#!/usr/bin/env python3
"""Run resource-guarded B0-B3 experiments for the normalized additive objective."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.objective import (  # noqa: E402
    aggregate_journey_objective_breakdown,
    flatten_objective_payload,
    objective_metadata,
)
from lunar_ice_bpc.exact.solver.journey_driver import _reference_solution_upper_bound  # noqa: E402
from lunar_ice_bpc.runners.b0_b1_ablation import (  # noqa: E402
    B0_MODE,
    B1A_MODE,
    B1B_MODE,
    run_b0_b1_ablation,
    write_b0_b1_ablation_artifacts,
    _report_from_rows as _b0b1_report_from_rows,
)
from lunar_ice_bpc.runners.b2_pricing_tail_ablation import (  # noqa: E402
    B2A_MODE,
    B2B_MODE,
    B2B_R2_MODE,
    B2B_R3_MODE,
    B2C_MODE,
    B2D_MODE,
    B2_MODES,
    B2_PRODUCT_MODE,
    run_b2_pricing_tail_ablation,
    write_b2_pricing_tail_ablation_artifacts,
    _report_from_rows as _b2_report_from_rows,
)
from lunar_ice_bpc.runners.b3_branch_tree_ablation import (  # noqa: E402
    B3A_MODE,
    B3B_MODE,
    B3_MODES,
    run_b3_branch_tree_ablation,
    write_b3_branch_tree_ablation_artifacts,
    _report_from_rows as _b3_report_from_rows,
)


DEFAULT_OUTPUT_DIR = "runs/objective_normalized_cost_risk_completion_full"
DEFAULT_MANIFEST = "data/manifests/lunar_ice_sp50_real_benchmark_manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--families", default="b0b1,b2,b3")
    parser.add_argument("--scales", default="5,10,20,30")
    parser.add_argument("--limit-per-scale", type=int, default=20)
    parser.add_argument("--smoke", action="store_true", help="Run only 1 instance at 5-scale for all requested families.")
    parser.add_argument("--force", action="store_true", help="Overwrite completed family/scale artifacts.")
    parser.add_argument(
        "--rerun-guard-rows",
        action="store_true",
        help=(
            "Treat instances containing resource-guard rows as incomplete and replace that instance/family block. "
            "Use with --run-heavy-full-universe-modes and/or --run-heavy-direct-modes to make strict progress."
        ),
    )
    parser.add_argument(
        "--max-rerun-instances-per-family-scale",
        type=int,
        default=0,
        help=(
            "When --rerun-guard-rows is set, cap newly rerun instances per family/scale. "
            "0 means no cap."
        ),
    )
    parser.add_argument("--min-mem-available-gb", type=float, default=2.0)
    parser.add_argument("--min-disk-free-gb", type=float, default=20.0)
    parser.add_argument("--heavy-full-universe-scale-guard", type=int, default=20)
    parser.add_argument(
        "--direct-exact-scale-guard",
        type=int,
        default=30,
        help=(
            "At this scale or above, direct-exact-dependent modes are written as fail-closed "
            "resource-guard rows unless --run-heavy-direct-modes is set."
        ),
    )
    parser.add_argument(
        "--run-heavy-direct-modes",
        action="store_true",
        help="Run direct-exact-dependent modes at or above --direct-exact-scale-guard.",
    )
    parser.add_argument(
        "--run-heavy-full-universe-modes",
        action="store_true",
        help="Run B1A/B2A/B3A full-universe modes even at or above the heavy scale guard.",
    )
    parser.add_argument("--max-workers", type=int, default=1, help="Only B0/B1 uses process workers; keep at 1 for low memory.")
    parser.add_argument("--b1-max-rounds", type=int, default=8)
    parser.add_argument(
        "--b1-reference-seed-without-b0",
        action="store_true",
        help=(
            "For B1 rows, skip the preliminary B0 direct-DP run and seed B1B from the "
            "instance reference feasible incumbent when B0 exact incumbent is unavailable. "
            "This is diagnostic only; it never creates a certificate."
        ),
    )
    parser.add_argument("--b2-max-rounds", type=int, default=8)
    parser.add_argument("--b3-max-rounds-per-node", type=int, default=16)
    parser.add_argument("--max-tree-nodes", type=int, default=31)
    parser.add_argument("--max-branch-depth", type=int, default=4)
    parser.add_argument(
        "--scale30-row-time-limit",
        type=float,
        default=None,
        help="Override the default 3600s row limit for 30-scale resource probes.",
    )
    parser.add_argument(
        "--skip-b3a-full-universe",
        action="store_true",
        help="Skip B3A full-universe branch audit. The full experiment default is to run it.",
    )
    args = parser.parse_args()

    output_dir = _resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = _load_manifest(_resolve_path(args.manifest))
    families = _parse_csv(args.families)
    scales = (5,) if args.smoke else tuple(int(value) for value in _parse_csv(args.scales))
    limit = 1 if args.smoke else int(args.limit_per_scale)
    requested_pairs = {(family, int(scale)) for family in families for scale in scales}

    index = {
        "schema_version": "lunar_ice_bpc.normalized_objective_full_ablation_index.v1",
        "objective_mode": "normalized_operating_cost_risk_weighted_completion",
        "makespan_enters_pricing_objective": False,
        "output_dir": str(output_dir),
        "manifest": str(_resolve_path(args.manifest)),
        "families_requested": list(families),
        "scales_requested": list(scales),
        "limit_per_scale": limit,
        "entries": _preserved_index_entries(output_dir / "index.json", requested_pairs=requested_pairs),
    }

    for scale in scales:
        instance_paths = _instance_paths_for_scale(manifest, scale=scale, limit=limit)
        if not instance_paths:
            index["entries"].append({"scale": scale, "status": "NO_INSTANCES_FOUND"})
            continue
        row_time_limit = _row_time_limit(scale, args=args)
        for family in families:
            artifact_prefix = output_dir / f"{family}_scale{scale:03d}"
            summary_json = artifact_prefix.with_name(f"{artifact_prefix.name}_summary.json")
            rows_csv = artifact_prefix.with_name(f"{artifact_prefix.name}_rows.csv")
            report_md = artifact_prefix.with_name(f"{artifact_prefix.name}_report_zh.md")
            resume_rows_json = artifact_prefix.with_name(f"{artifact_prefix.name}_resume_rows.json")
            matrix_group = f"{scale}-scale full normalized objective"
            rows = [] if args.force else _existing_rows(resume_rows_json, summary_json)
            expected_modes = _expected_mode_count(family)
            completed = _completed_instance_ids(rows, matrix_group=matrix_group, expected_mode_count=expected_modes)
            guard_instances = _guarded_instance_ids(rows, matrix_group=matrix_group)
            if args.rerun_guard_rows:
                completed -= guard_instances
            entry = {
                "family": family,
                "scale": scale,
                "status": "RUNNING",
                "expected_instance_count": len(instance_paths),
                "completed_instance_count": len(completed),
                "guard_instance_count": len(guard_instances),
                "row_time_limit_sec": row_time_limit,
                "rows_csv": str(rows_csv),
                "summary_json": str(summary_json),
                "report_md": str(report_md),
                "resume_rows_json": str(resume_rows_json),
            }
            index["entries"].append(entry)
            _write_index(output_dir, index)

            if len(completed) >= len(instance_paths):
                if rows:
                    report = _report_from_rows_for_family(family, rows)
                    _write_family_artifacts(family, report, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
                    rows = list(report.get("rows") or rows)
                    _write_resume_rows(resume_rows_json, rows)
                    entry.update(
                        {
                            "completed_instance_count": len(completed),
                            "row_count": report.get("row_count"),
                            "wall_time_sec": 0.0,
                        }
                    )
                entry["status"] = "SKIPPED_COMPLETE"
                _write_index(output_dir, index)
                continue

            start = perf_counter()
            rerun_count = 0
            for instance_path in instance_paths:
                instance_id = _instance_id_from_path(instance_path)
                if instance_id in completed:
                    continue
                if (
                    args.rerun_guard_rows
                    and int(args.max_rerun_instances_per_family_scale) > 0
                    and rerun_count >= int(args.max_rerun_instances_per_family_scale)
                ):
                    break
                _assert_resource_guard(output_dir, args)
                partial = _run_family(
                    family,
                    instance_paths=(instance_path,),
                    scale=scale,
                    row_time_limit=row_time_limit,
                    args=args,
                )
                if args.rerun_guard_rows:
                    rows = [
                        row for row in rows
                        if not (
                            str(row.get("matrix_group") or "") == str(matrix_group)
                            and str(row.get("instance_id") or "") == str(instance_id)
                        )
                    ]
                rows.extend(partial.get("rows", []))
                completed.add(instance_id)
                rerun_count += 1
                report = _report_from_rows_for_family(family, rows)
                _write_family_artifacts(family, report, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
                rows = list(report.get("rows") or rows)
                _write_resume_rows(resume_rows_json, rows)
                entry.update(
                    {
                        "status": "RUNNING",
                        "completed_instance_count": len(completed),
                        "row_count": report.get("row_count"),
                        "wall_time_sec": round(perf_counter() - start, 6),
                    }
                )
                _write_index(output_dir, index)
            entry["status"] = (
                "PARTIAL_RERUN_LIMIT"
                if (
                    args.rerun_guard_rows
                    and int(args.max_rerun_instances_per_family_scale) > 0
                    and rerun_count >= int(args.max_rerun_instances_per_family_scale)
                    and len(completed) < len(instance_paths)
                )
                else "DONE"
            )
            entry["wall_time_sec"] = round(perf_counter() - start, 6)
            _write_resume_rows(resume_rows_json, rows)
            _write_index(output_dir, index)

    _write_index(output_dir, index)
    _write_master_report(output_dir)
    print(f"normalized objective ablation index written to {output_dir / 'index.json'}")
    return 0


def _run_family(family: str, *, instance_paths: tuple[Path, ...], scale: int, row_time_limit: float, args) -> dict:
    matrix_group = f"{scale}-scale full normalized objective"
    max_direct_tasks = int(scale)
    guarded_heavy_universe = (
        int(scale) >= int(args.heavy_full_universe_scale_guard)
        and not bool(args.run_heavy_full_universe_modes)
    )
    guarded_direct_exact = (
        int(scale) >= int(args.direct_exact_scale_guard)
        and not bool(args.run_heavy_direct_modes)
    )
    if guarded_direct_exact:
        if family == "b0b1":
            skipped_modes = (B0_MODE, B1A_MODE, B1B_MODE)
        elif family == "b2":
            skipped_modes = B2_MODES
        elif family == "b3":
            skipped_modes = B3_MODES
        else:
            raise ValueError(f"unsupported family={family!r}; expected b0b1,b2,b3")
        return _append_resource_guard_rows(
            family,
            {"rows": []},
            instance_paths=instance_paths,
            skipped_modes=tuple(skipped_modes),
            matrix_group=matrix_group,
            reason=(
                f"direct-exact-dependent mode skipped at scale={scale} by resource guard; "
                "latest 30-scale B0 probe timed out after 300s during sortie_candidate_generation "
                "before fleet_set_partition"
            ),
        )
    if family == "b0b1":
        modes = (B0_MODE, B1A_MODE, B1B_MODE)
        skipped_modes: tuple[str, ...] = tuple()
        if guarded_heavy_universe:
            modes = (B0_MODE, B1B_MODE)
            skipped_modes = (B1A_MODE,)
        report = run_b0_b1_ablation(
            instance_paths,
            modes=modes,
            max_direct_tasks=max_direct_tasks,
            b1_max_rounds=int(args.b1_max_rounds),
            matrix_group=matrix_group,
            row_time_limit_sec=row_time_limit,
            max_workers=int(args.max_workers),
            b1_solve_b0_direct_first=not bool(args.b1_reference_seed_without_b0),
        )
        return _append_resource_guard_rows(
            family,
            report,
            instance_paths=instance_paths,
            skipped_modes=skipped_modes,
            matrix_group=matrix_group,
            reason=f"heavy full-universe mode skipped at scale={scale} by resource guard",
        )
    if family == "b2":
        modes = B2_MODES
        skipped_modes = tuple()
        if guarded_heavy_universe:
            skipped_modes = (B1A_MODE, B2A_MODE, B2B_MODE, B2B_R2_MODE, B2B_R3_MODE, B2C_MODE, B2D_MODE)
            modes = tuple(mode for mode in B2_MODES if mode not in set(skipped_modes))
        report = run_b2_pricing_tail_ablation(
            instance_paths,
            modes=modes,
            max_direct_tasks=max_direct_tasks,
            b1_max_rounds=int(args.b1_max_rounds),
            b2_max_rounds=int(args.b2_max_rounds),
            matrix_group=matrix_group,
            row_time_limit_sec=row_time_limit,
        )
        return _append_resource_guard_rows(
            family,
            report,
            instance_paths=instance_paths,
            skipped_modes=skipped_modes,
            matrix_group=matrix_group,
            reason=f"heavy full-universe mode skipped at scale={scale} by resource guard",
        )
    if family == "b3":
        modes = B3_MODES
        skipped_modes = tuple()
        if guarded_heavy_universe:
            skipped_modes = (B2B_R3_MODE, B3A_MODE)
            modes = tuple(mode for mode in B3_MODES if mode not in set(skipped_modes))
        report = run_b3_branch_tree_ablation(
            instance_paths,
            modes=modes,
            max_direct_tasks=max_direct_tasks,
            b2_max_rounds=int(args.b2_max_rounds),
            b3_max_rounds_per_node=int(args.b3_max_rounds_per_node),
            max_tree_nodes=int(args.max_tree_nodes),
            max_branch_depth=int(args.max_branch_depth),
            matrix_group=matrix_group,
            row_time_limit_sec=row_time_limit,
            allow_b3a_full_universe=not bool(args.skip_b3a_full_universe),
        )
        return _append_resource_guard_rows(
            family,
            report,
            instance_paths=instance_paths,
            skipped_modes=skipped_modes,
            matrix_group=matrix_group,
            reason=f"heavy full-universe mode skipped at scale={scale} by resource guard",
        )
    raise ValueError(f"unsupported family={family!r}; expected b0b1,b2,b3")


def _append_resource_guard_rows(
    family: str,
    report: dict,
    *,
    instance_paths: tuple[Path, ...],
    skipped_modes: tuple[str, ...],
    matrix_group: str,
    reason: str,
) -> dict:
    if not skipped_modes:
        return report
    rows = list(report.get("rows") or [])
    source_by_instance = {
        str(row.get("instance_id") or ""): row
        for row in rows
        if row.get("solution_raw_operating_cost") not in {None, ""}
    }
    for instance_path in instance_paths:
        instance = json.loads(Path(instance_path).read_text(encoding="utf-8"))
        data = load_lunar_ice_data(instance)
        source = source_by_instance.get(data.instance_id)
        for mode in skipped_modes:
            rows.append(_resource_guard_row(family, mode=mode, data=data, matrix_group=matrix_group, reason=reason, source=source))
    return _report_from_rows_for_family(family, rows)


def _resource_guard_row(family: str, *, mode: str, data, matrix_group: str, reason: str, source: dict | None) -> dict:
    direct_like = mode in {B0_MODE, B2_PRODUCT_MODE}
    reference_incumbent = None if source is not None else _reference_solution_upper_bound(data)
    reference_objective = None if reference_incumbent is None else float(reference_incumbent.objective)
    reference_source = "" if reference_incumbent is None else str(reference_incumbent.source)
    row = {
        "matrix_group": matrix_group,
        "scale": len(data.task_ids),
        "instance_id": data.instance_id,
        "algorithm_status": "DIRECT_DP_TIME_LIMIT" if direct_like else "BPC_INCOMPLETE_PRICING",
        "certificate_scope": "FEASIBLE_INCUMBENT_ONLY" if family == "b0b1" or direct_like else "DIAGNOSTIC_PRICING_FRONTIER",
        "pricing_state": "" if direct_like else "INCOMPLETE_LIMIT",
        "uses_true_dual_bpc_certificate": False,
        "root_lp_bound_official": False,
        "fail_closed_reason": reason,
        "wall_time": 0.0,
        "B0_direct_objective": None if source is None else source.get("B0_direct_objective"),
        "reference_solution_upper_bound": (
            reference_objective if source is None else source.get("reference_solution_upper_bound")
        ),
        "reference_solution_upper_bound_source": (
            reference_source if source is None else str(source.get("reference_solution_upper_bound_source") or "")
        ),
        "feasible_incumbent_source": (
            "" if reference_incumbent is None else f"REFERENCE_FEASIBLE_INCUMBENT:{reference_source}"
        ),
        "feasible_incumbent_objective": reference_objective,
        "feasible_incumbent_journey_count": 0 if reference_incumbent is None else len(reference_incumbent.journeys),
        "feasible_incumbent_used_as_bpc_certificate": False,
        "journey_label_bound_pruned_count": 0
        if source is None
        else int(source.get("journey_label_bound_pruned_count") or 0),
    }
    row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
    if source is not None:
        row.update({key: value for key, value in source.items() if str(key).startswith("solution_")})
    elif reference_incumbent is not None:
        row.update(
            flatten_objective_payload(
                aggregate_journey_objective_breakdown(data, reference_incumbent.journeys),
                prefix="solution",
            )
        )
    if family == "b0b1":
        row.update(
            {
                "mode": mode,
                "bpc_certificate_status": "NOT_PORTED_TRUE_DUAL_BPC",
                "pricing_round_count": 0,
                "added_column_count": 0,
                "manual_rc_audit_pass": None,
                "pricing_rc_audit_pass": None,
                "proof_debt_unreleased_count": 0,
                "direct_root_official_leak": False,
                "b1_mode": mode,
                "seed_mode": "full_universe" if mode == B1A_MODE else "",
                "initial_column_count": 0,
                "full_universe_column_count": None,
                "full_universe_preloaded": False,
            }
        )
    elif family == "b2":
        row.update(
            {
                "mode": mode,
                "baseline_name": _baseline_for_b2_mode(mode),
                "candidate_name": mode,
                "seed_builder": "resource_guard",
                "initial_column_count": 0,
                "full_universe_column_count": None,
                "full_universe_preloaded": False,
                "root_lp_bound": None,
                "root_bound_le_B0_objective": None,
                "pricing_round_count": 0,
                "final_judge_call_count": 0,
                "candidate_negative_count": 0,
                "addable_negative_count": 0,
                "selected_count": 0,
                "added_to_master_count": 0,
                "added_column_count": 0,
                "manual_rc_audit_pass": None,
                "pricing_rc_audit_pass": None,
                "proof_debt_unreleased_count": 0,
                "certificate_scope_regression": False,
                "objective_mismatch": False,
                "improvement_reason": "resource_guard_fail_closed",
            }
        )
    elif family == "b3":
        row.update(
            {
                "mode": mode,
                "B2B_R3_root_lp_bound": None,
                "B3_global_lb": None,
                "B3_global_ub": reference_objective,
                "B3_global_gap": None,
                "objective_diff_vs_B0": None,
                "B3_tree_closed": False,
                "BPC_TREE_OPTIMAL_count": 0,
                "BPC_NODE_LP_CERTIFIED_count": 0,
                "node_count": 0,
                "evaluated_node_count": 0,
                "open_node_count": 0,
                "incomplete_node_count": 1,
                "manual_rc_audit_pass": None,
                "pricing_rc_audit_pass": None,
                "branch_pricing_audit_pass": None,
                "proof_debt_unreleased_count": 0,
                "all_node_ledgers_valid": False,
                "direct_dp_used_as_bpc_certificate": False,
                "direct_dp_certificate_leak": 0,
            }
        )
    else:
        raise ValueError(f"unsupported family={family!r}")
    return row


def _baseline_for_b2_mode(mode: str) -> str:
    if mode == B1A_MODE:
        return "accepted_B1"
    if mode == B2A_MODE:
        return B1A_MODE
    return B1B_MODE


def _write_family_artifacts(family: str, report: dict, *, rows_csv: Path, summary_json: Path, report_md: Path) -> None:
    if family == "b0b1":
        write_b0_b1_ablation_artifacts(report, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
    elif family == "b2":
        write_b2_pricing_tail_ablation_artifacts(report, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
    elif family == "b3":
        write_b3_branch_tree_ablation_artifacts(report, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
    else:
        raise ValueError(f"unsupported family={family!r}")


def _report_from_rows_for_family(family: str, rows: list[dict]) -> dict:
    if family == "b0b1":
        return _b0b1_report_from_rows(rows)
    if family == "b2":
        return _b2_report_from_rows(rows)
    if family == "b3":
        return _b3_report_from_rows(rows)
    raise ValueError(f"unsupported family={family!r}")


def _existing_rows(resume_rows_json: Path, summary_json: Path) -> list[dict]:
    if resume_rows_json.exists():
        rows = json.loads(resume_rows_json.read_text(encoding="utf-8"))
        return [dict(row) for row in rows if isinstance(row, dict)]
    if not summary_json.exists():
        return []
    payload = json.loads(summary_json.read_text(encoding="utf-8"))
    rows = payload.get("rows") or []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _write_resume_rows(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def _completed_instance_ids(rows: list[dict], *, matrix_group: str, expected_mode_count: int) -> set[str]:
    modes_by_instance: dict[str, set[str]] = {}
    mode_key = "mode"
    for row in rows:
        if str(row.get("matrix_group") or "") != str(matrix_group):
            continue
        instance_id = str(row.get("instance_id") or "")
        if not instance_id:
            continue
        mode = row.get("mode")
        if mode is None:
            mode = row.get("candidate_name")
        if mode is None:
            continue
        modes_by_instance.setdefault(instance_id, set()).add(str(mode))
    return {
        instance_id
        for instance_id, modes in modes_by_instance.items()
        if len(modes) >= int(expected_mode_count)
    }


def _guarded_instance_ids(rows: list[dict], *, matrix_group: str) -> set[str]:
    guarded: set[str] = set()
    for row in rows:
        if str(row.get("matrix_group") or "") != str(matrix_group):
            continue
        if not _row_is_resource_guard(row):
            continue
        instance_id = str(row.get("instance_id") or "")
        if instance_id:
            guarded.add(instance_id)
    return guarded


def _row_is_resource_guard(row: dict) -> bool:
    reason = str(row.get("fail_closed_reason") or "").lower()
    if not reason:
        return False
    if "resource guard" not in reason and "resource_guard" not in reason and "skipped at scale" not in reason:
        return False
    wall_time = row.get("wall_time")
    try:
        return float(wall_time or 0.0) == 0.0
    except (TypeError, ValueError):
        return True


def _expected_mode_count(family: str) -> int:
    if family == "b0b1":
        return 3
    if family == "b2":
        return len(B2_MODES)
    if family == "b3":
        return len(B3_MODES)
    raise ValueError(f"unsupported family={family!r}")


def _instance_paths_for_scale(manifest: dict, *, scale: int, limit: int) -> tuple[Path, ...]:
    rows = [
        row for row in manifest.get("instances", [])
        if int(row.get("scale") or -1) == int(scale) and row.get("path")
    ]
    rows.sort(key=lambda row: (int(row.get("attempt_index") or 0), str(row.get("instance_id") or "")))
    return tuple(_resolve_path(row["path"]) for row in rows[: max(0, int(limit))])


def _instance_id_from_path(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get("instance_id") or path.stem)


def _assert_resource_guard(output_dir: Path, args) -> None:
    mem_available = _mem_available_gb()
    if mem_available is not None and mem_available < float(args.min_mem_available_gb):
        raise RuntimeError(
            f"resource guard stopped: MemAvailable={mem_available:.2f}GiB "
            f"< min_mem_available_gb={args.min_mem_available_gb}"
        )
    disk_free = shutil.disk_usage(output_dir).free / (1024 ** 3)
    if disk_free < float(args.min_disk_free_gb):
        raise RuntimeError(
            f"resource guard stopped: disk_free={disk_free:.2f}GiB "
            f"< min_disk_free_gb={args.min_disk_free_gb}"
        )


def _mem_available_gb() -> float | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    for line in meminfo.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            parts = line.split()
            if len(parts) >= 2:
                return float(parts[1]) / (1024 ** 2)
    return None


def _row_time_limit(scale: int, *, args=None) -> float:
    if int(scale) == 30 and args is not None and args.scale30_row_time_limit is not None:
        return float(args.scale30_row_time_limit)
    return 3600.0 if int(scale) == 30 else 600.0


def _load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in str(value).split(",") if part.strip())


def _write_index(output_dir: Path, index: dict) -> None:
    (output_dir / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_master_report(output_dir: Path) -> None:
    lines = [
        "# 归一化成本-风险-完成时间目标 B0-B3 全量实验总报告",
        "",
        "## 目标函数边界",
        "",
        "- official objective: `normalized_operating_cost + normalized_risk + 0.4 * normalized_weighted_completion_time`。",
        "- 所有 normalization references 均按 instance 写入 `objective_*` 字段。",
        "- `solution_normalized_objective` / `solution_official_objective` 是本轮 official objective。",
        "- `solution_raw_objective_unscaled_weighted_sum` 只用于尺度诊断，不参与 reduced cost 或证书判定。",
        "- makespan 只作为 `solution_raw_makespan` / `solution_normalized_makespan_metric` 报告指标，不进入 pricing objective。",
        "",
        "## 完成度边界",
        "",
        "- 5/10/20-scale official objective/certificate 结果来自 distance-corrected full runs；30-scale candidate-pruning 优化后已做 5-scale B0 objective spot-check，目标值保持一致。",
        "- 代码当前已修复 path-option dominance：distance 现在参与支配判断；若某个 scale/family 尚未在该修复后重跑，以 `completion_audit_zh.md` 的刷新边界为准。",
        "- 20-scale B2/B3 的 diagnostic frontier rows 是实际 solver run 的诊断结果；它们不构成 official certificate，也不应解释为 B3B tree optimality gap。",
        "- 20-scale 已补跑的 B1A/B2A/B3A full-universe active-RMP rows 会在 dense tableau memory precheck 超限时 fail-closed；这不是证书，而是避免重复触发 MemoryError 的安全边界。",
        "- 30-scale rows 是 resource-guard fail-closed rows，不是实际跑满 3600s 的 solver rows，也不是 30-scale exact solve。",
        "- 30-scale rows 的 `solution_*` 字段来自可行上界 incumbent，用于记录 objective 分解；它不表示对应 B0/B1/B2/B3 mode 已证明 optimal。",
        "- 严格完成度审计见 `completion_audit_zh.md`。",
        "",
        "## 覆盖汇总",
        "",
        "| scale | family | rows | instances | solved/certified scopes | fail-closed rows | missing solution objective |",
        "|---:|---|---:|---:|---|---:|---:|",
    ]
    for scale in (5, 10, 20, 30):
        for family in ("b0b1", "b2", "b3"):
            rows = _read_rows(output_dir / f"{family}_scale{scale:03d}_resume_rows.json")
            if not rows:
                lines.append(f"| {scale} | {family} | 0 | 0 | missing | 0 | 0 |")
                continue
            scopes: dict[str, int] = {}
            fail_closed = 0
            missing_solution = 0
            for row in rows:
                scope = str(row.get("certificate_scope") or "")
                scopes[scope] = scopes.get(scope, 0) + 1
                if row.get("fail_closed_reason"):
                    fail_closed += 1
                if row.get("solution_official_objective") in {None, ""}:
                    missing_solution += 1
            scope_text = ", ".join(f"{key}:{value}" for key, value in sorted(scopes.items()))
            lines.append(
                f"| {scale} | {family} | {len(rows)} | {len({row.get('instance_id') for row in rows})} | "
                f"{scope_text} | {fail_closed} | {missing_solution} |"
            )

    lines.extend(
        [
            "",
            "## 逐模式证书与耗时汇总",
            "",
            "| scale | family | mode | rows | mean wall time (s) | certificate scopes | missing solution objective |",
            "|---:|---|---|---:|---:|---|---:|",
        ]
    )
    for scale in (5, 10, 20, 30):
        for family in ("b0b1", "b2", "b3"):
            rows = _read_rows(output_dir / f"{family}_scale{scale:03d}_resume_rows.json")
            rows_by_mode: dict[str, list[dict]] = {}
            for row in rows:
                rows_by_mode.setdefault(_row_mode(row), []).append(row)
            for mode, mode_rows in sorted(rows_by_mode.items()):
                scopes: dict[str, int] = {}
                missing_solution = 0
                times: list[float] = []
                for row in mode_rows:
                    scope = str(row.get("certificate_scope") or "")
                    scopes[scope] = scopes.get(scope, 0) + 1
                    if row.get("solution_official_objective") in {None, ""}:
                        missing_solution += 1
                    wall_time = _row_wall_time(row)
                    if wall_time is not None:
                        times.append(wall_time)
                scope_text = ", ".join(f"{key}:{value}" for key, value in sorted(scopes.items()))
                mean_wall = "" if not times else f"{(sum(times) / len(times)):.6g}"
                lines.append(
                    f"| {scale} | {family} | `{mode}` | {len(mode_rows)} | {mean_wall} | "
                    f"{scope_text} | {missing_solution} |"
                )

    lines.extend(
        [
            "",
            "## B0 与 B3B 对齐",
            "",
            "| scale | compared instances | max abs(B3 global UB - B0 objective) | B3B tree optimal rows |",
            "|---:|---:|---:|---:|",
        ]
    )
    for scale in (5, 10, 20, 30):
        b0_rows = _read_rows(output_dir / f"b0b1_scale{scale:03d}_resume_rows.json")
        b3_rows = _read_rows(output_dir / f"b3_scale{scale:03d}_resume_rows.json")
        b0_by_instance = {
            str(row.get("instance_id")): row
            for row in b0_rows
            if row.get("mode") == B0_MODE and row.get("B0_direct_objective") not in {None, ""}
        }
        b3b = [row for row in b3_rows if row.get("mode") == B3B_MODE]
        diffs = []
        for row in b3b:
            instance_id = str(row.get("instance_id"))
            if instance_id not in b0_by_instance or row.get("B3_global_ub") in {None, ""}:
                continue
            diffs.append(abs(float(row["B3_global_ub"]) - float(b0_by_instance[instance_id]["B0_direct_objective"])))
        max_diff = "" if not diffs else f"{max(diffs):.9g}"
        tree_optimal = sum(1 for row in b3b if row.get("certificate_scope") == "BPC_TREE_OPTIMAL")
        lines.append(f"| {scale} | {len(diffs)} | {max_diff} | {tree_optimal}/{len(b3b)} |")

    compact_summary_path = output_dir / "compact_product_scale030_summary.json"
    if compact_summary_path.exists():
        compact_summary = json.loads(compact_summary_path.read_text(encoding="utf-8"))
        compact_rows = int(compact_summary.get("row_count") or 0)
        compact_feasible = int(compact_summary.get("feasible_incumbent_count") or 0)
        compact_optimal = int(compact_summary.get("product_optimal_count") or 0)
        compact_mean_objective = compact_summary.get("mean_objective")
        compact_mean_elapsed = compact_summary.get("mean_row_elapsed_sec")
        compact_objective_text = (
            ""
            if compact_mean_objective in {None, ""}
            else f"，mean objective among incumbents 约 {float(compact_mean_objective):.6g}"
        )
        compact_elapsed_text = (
            ""
            if compact_mean_elapsed in {None, ""}
            else f"，mean row elapsed 约 {float(compact_mean_elapsed):.4g}s"
        )
        compact_probe_line = (
            f"- 新增可恢复 compact product probe runner；30-scale 前 {compact_rows} 个实例以 60s/row 跑通，"
            f"{compact_feasible}/{compact_rows} 有 feasible incumbent，{compact_optimal}/{compact_rows} product optimal"
            f"{compact_objective_text}{compact_elapsed_text}。"
        )
    else:
        compact_probe_line = (
            "- 新增可恢复 compact product probe runner；尚未发现 `compact_product_scale030_summary.json`，"
            "因此总报告未纳入 compact product row 统计。"
        )
    compact_bound_summary_path = (
        output_dir
        / "compact_bound_probe_scale030_300s"
        / "compact_product_scale030_summary.json"
    )
    compact_bound_probe_line = ""
    if compact_bound_summary_path.exists():
        bound_summary = json.loads(compact_bound_summary_path.read_text(encoding="utf-8"))
        bound_rows = int(bound_summary.get("row_count") or 0)
        bound_rows_with_bound = int(bound_summary.get("rows_with_bound_count") or 0)
        mean_bound = bound_summary.get("mean_bound")
        mean_gap = bound_summary.get("mean_gap")
        mean_nodes = bound_summary.get("mean_mip_node_count")
        mean_simplex = bound_summary.get("mean_simplex_iteration_count")
        def value_text(value) -> str:
            return "" if value in {None, ""} else f"{float(value):.7g}"

        compact_bound_probe_line = (
            f"- 30-scale 首实例 compact 300s bound probe 已写入独立目录：{bound_rows_with_bound}/{bound_rows} rows "
            f"有 finite bound，mean bound `{value_text(mean_bound)}`，mean gap `{value_text(mean_gap)}`，"
            f"mean MIP nodes `{value_text(mean_nodes)}`，mean simplex iterations `{value_text(mean_simplex)}`。"
        )
    duration_lb_summary_path = (
        output_dir
        / "compact_duration_lb_probe_scale030_60s"
        / "compact_product_scale030_summary.json"
    )
    compact_duration_lb_probe_line = ""
    if duration_lb_summary_path.exists():
        duration_summary = json.loads(duration_lb_summary_path.read_text(encoding="utf-8"))
        duration_rows = int(duration_summary.get("row_count") or 0)
        duration_rows_with_bound = int(duration_summary.get("rows_with_bound_count") or 0)
        duration_mean_objective = duration_summary.get("mean_objective")
        duration_mean_elapsed = duration_summary.get("mean_row_elapsed_sec")

        def duration_value_text(value) -> str:
            return "" if value in {None, ""} else f"{float(value):.7g}"

        compact_duration_lb_probe_line = (
            f"- duration-lower-bound compact 60s probe 已写入独立目录：{duration_rows_with_bound}/{duration_rows} rows "
            f"有 finite bound，mean objective `{duration_value_text(duration_mean_objective)}`，"
            f"mean elapsed `{duration_value_text(duration_mean_elapsed)}`s；该安全紧化未在 60s 内产生 product bound。"
        )
    tight_m_summary_path = (
        output_dir
        / "compact_tight_m_probe_scale030_300s"
        / "compact_product_scale030_summary.json"
    )
    compact_tight_m_probe_line = ""
    if tight_m_summary_path.exists():
        tight_m_summary = json.loads(tight_m_summary_path.read_text(encoding="utf-8"))
        tight_rows = int(tight_m_summary.get("row_count") or 0)
        tight_rows_with_bound = int(tight_m_summary.get("rows_with_bound_count") or 0)
        tight_bound = tight_m_summary.get("mean_bound")
        tight_gap = tight_m_summary.get("mean_gap")
        tight_nodes = tight_m_summary.get("mean_mip_node_count")
        tight_simplex = tight_m_summary.get("mean_simplex_iteration_count")

        def tight_value_text(value) -> str:
            return "" if value in {None, ""} else f"{float(value):.7g}"

        compact_tight_m_probe_line = (
            f"- tight big-M compact 300s probe 已写入独立目录：{tight_rows_with_bound}/{tight_rows} rows "
            f"有 finite bound，mean bound `{tight_value_text(tight_bound)}`，mean gap `{tight_value_text(tight_gap)}`，"
            f"mean MIP nodes `{tight_value_text(tight_nodes)}`，mean simplex iterations `{tight_value_text(tight_simplex)}`；"
            "该 probe 未改变 30-scale 首实例 bound/gap，说明仅收紧 time big-M 不是闭合 30-scale 的主要突破口。"
        )
    bound_gap_path = output_dir / "scale30_bound_gap_diagnostic.json"
    bound_gap_line = ""
    if bound_gap_path.exists():
        bound_gap = json.loads(bound_gap_path.read_text(encoding="utf-8"))
        reference_ub = bound_gap.get("reference_upper_bound")
        future_tail = (bound_gap.get("future_tail_lower_bound") or {}).get("function_value")
        bounds_by_name = {str(row.get("name")): row for row in bound_gap.get("bounds") or []}
        compact_bound = None
        compact_ratio = None
        for name, row in bounds_by_name.items():
            if name.startswith("compact_product_bound:"):
                compact_bound = row.get("bound")
                compact_ratio = row.get("ratio_to_reference_upper_bound")
                break

        def gap_value_text(value) -> str:
            return "" if value in {None, ""} else f"{float(value):.9g}"

        bound_gap_line = (
            "- 30-scale bound-gap diagnostic：首实例 reference feasible UB "
            f"`{gap_value_text(reference_ub)}`，direct-DP root pruning bound `{gap_value_text(future_tail)}`，"
            f"compact product bound `{gap_value_text(compact_bound)}`，compact/ref ratio `{gap_value_text(compact_ratio)}`。"
        )
    threshold_probe_line = ""
    threshold_probe_path = output_dir / "scale30_direct_bound_pruning_threshold_probe_20s_zh.md"
    if threshold_probe_path.exists():
        threshold_probe_line = (
            "- direct-DP bound-pruning threshold 20s probe 显示：把激活门槛临时从 `0.5` 降到 `0.4` "
            "会使 pruning active，但首实例 20s 内 `journey_label_bound_pruned_count=0`；"
            "当前瓶颈不是阈值过高，而是 lower bound 强度不足。"
        )
    strict_b0b1_probe_line = ""
    strict_b0b1_rows_path = (
        output_dir
        / "strict_progress_probe_scale030_b0b1_60s"
        / "b0b1_scale030_resume_rows.json"
    )
    if strict_b0b1_rows_path.exists():
        strict_rows = _read_rows(strict_b0b1_rows_path)
        by_mode = {_row_mode(row): row for row in strict_rows}
        b0_row = by_mode.get(B0_MODE, {})
        b1b_row = by_mode.get(B1B_MODE, {})

        def strict_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        strict_b0b1_probe_line = (
            "- strict-progress 30-scale B0/B1 runner probe 已在单实例、60s row setting 下真实运行："
            f"B0 status `{strict_value(b0_row, 'algorithm_status')}`、wall `{strict_value(b0_row, 'wall_time')}`s，"
            f"B1B status `{strict_value(b1b_row, 'algorithm_status')}`、scope `{strict_value(b1b_row, 'certificate_scope')}`、"
            f"wall `{strict_value(b1b_row, 'wall_time')}`s；仍无 B0 exact objective 或 B1 root certificate。"
        )
    reference_seed_no_b0_probe_line = ""
    reference_seed_no_b0_rows_path = (
        output_dir
        / "strict_progress_probe_scale030_b0b1_60s_reference_seed_no_b0"
        / "b0b1_scale030_resume_rows.json"
    )
    if reference_seed_no_b0_rows_path.exists():
        no_b0_rows = _read_rows(reference_seed_no_b0_rows_path)
        by_mode = {_row_mode(row): row for row in no_b0_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def no_b0_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        reference_seed_no_b0_probe_line = (
            "- reference-seed-without-B0 30-scale B1B probe 显示："
            f"`solve_b0_direct_first={no_b0_value(b1b_row, 'solve_b0_direct_first')}`，"
            f"`initial_column_count={no_b0_value(b1b_row, 'initial_column_count')}`，"
            f"`feasible_incumbent_seed_column_count={no_b0_value(b1b_row, 'feasible_incumbent_seed_column_count')}`，"
            f"`feasible_incumbent_seed_used_as_certificate={no_b0_value(b1b_row, 'feasible_incumbent_seed_used_as_certificate')}`；"
            "60s 内仍未得到 B1 root certificate，瓶颈转向 true-dual pricing/final-judge tail。"
        )
    final_judge_deadline_probe_line = ""
    final_judge_deadline_rows_path = (
        output_dir
        / "strict_progress_probe_scale030_b1b_reference_seed_deadline_60s"
        / "b0b1_scale030_resume_rows.json"
    )
    if final_judge_deadline_rows_path.exists():
        deadline_rows = _read_rows(final_judge_deadline_rows_path)
        by_mode = {_row_mode(row): row for row in deadline_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def deadline_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        final_judge_deadline_probe_line = (
            "- B1B final-judge deadline telemetry probe 显示："
            f"status `{deadline_value(b1b_row, 'final_judge_status')}`，"
            f"final judge wall `{deadline_value(b1b_row, 'final_judge_wall_time')}`s，"
            f"generated journeys `{deadline_value(b1b_row, 'final_judge_generated_journey_count')}`，"
            f"route templates `{deadline_value(b1b_row, 'final_judge_route_template_count')}`，"
            f"sortie templates `{deadline_value(b1b_row, 'final_judge_generated_sortie_count')}`，"
            f"pareto labels `{deadline_value(b1b_row, 'final_judge_pareto_label_count')}`，"
            f"representative universe audited `{_final_judge_universe_value(b1b_row, 'audited')}`/"
            f"`{_final_judge_universe_value(b1b_row, 'total')}`，"
            f"completion ratio `{_final_judge_universe_value(b1b_row, 'ratio')}`，"
            f"remaining `{_final_judge_universe_value(b1b_row, 'remaining')}`；"
            "现在能定位为 complete-universe RC audit/pricing tail 超时，而不是外层 row timeout 黑盒截断。"
        )
    compact_pricing_probe_line = ""
    compact_pricing_rows_path = (
        output_dir
        / "compact_pricing_probe_scale030_b1b_reference_seed_60s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_rows_path.exists():
        compact_rows = _read_rows(compact_pricing_rows_path)
        by_mode = {_row_mode(row): row for row in compact_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def compact_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_probe_line = (
            "- compact single-journey pricing optimization-mode historical probe 显示："
            f"backend `{compact_value(b1b_row, 'final_judge_solver_backend')}`，"
            f"status `{compact_value(b1b_row, 'final_judge_status')}`，"
            f"wall `{compact_value(b1b_row, 'final_judge_wall_time')}`s，"
            f"best RC `{compact_value(b1b_row, 'final_judge_best_reduced_cost')}`，"
            f"dual bound `{compact_value(b1b_row, 'final_judge_dual_bound')}`，"
            f"MIP gap `{compact_value(b1b_row, 'final_judge_mip_gap')}`，"
            f"vars `{compact_value(b1b_row, 'final_judge_variable_count')}`，"
            f"rows `{compact_value(b1b_row, 'final_judge_constraint_count')}`；"
            "它避免了 2^30 representative enumeration，但 60s 内 bound 仍不能排除负 reduced-cost column。"
        )
    compact_pricing_default_telemetry_line = ""
    compact_pricing_default_telemetry_rows_path = (
        output_dir
        / "compact_pricing_default_telemetry_probe_scale030_b1b_reference_seed_60s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_default_telemetry_rows_path.exists():
        telemetry_rows = _read_rows(compact_pricing_default_telemetry_rows_path)
        by_mode = {_row_mode(row): row for row in telemetry_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def telemetry_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_default_telemetry_line = (
            "- optimization-only compact-pricing telemetry probe 显示："
            f"pricing rounds `{telemetry_value(b1b_row, 'pricing_round_count')}`，"
            f"added columns `{telemetry_value(b1b_row, 'added_column_count')}`，"
            f"final judge calls `{telemetry_value(b1b_row, 'final_judge_call_count')}`，"
            f"total final judge wall `{telemetry_value(b1b_row, 'final_judge_total_wall_time')}`s，"
            f"best RC `{telemetry_value(b1b_row, 'final_judge_best_reduced_cost')}`，"
            f"dual bound `{telemetry_value(b1b_row, 'final_judge_dual_bound')}`；"
            "该历史 probe 未发现负列且未加列，说明单纯 minimization 更偏向 bound 诊断，不适合作为找负列阶段。"
        )
    compact_pricing_negative_feasibility_line = ""
    compact_pricing_negative_feasibility_rows_path = (
        output_dir
        / "compact_pricing_neg_feas_probe_scale030_b1b_reference_seed_60s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_negative_feasibility_rows_path.exists():
        neg_feas_rows = _read_rows(compact_pricing_negative_feasibility_rows_path)
        by_mode = {_row_mode(row): row for row in neg_feas_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def neg_feas_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_negative_feasibility_line = (
            "- compact single-journey pricing negative-feasibility probe 显示："
            f"status `{neg_feas_value(b1b_row, 'final_judge_status')}`，"
            f"exact status `{neg_feas_value(b1b_row, 'final_judge_exact_status')}`，"
            f"wall `{neg_feas_value(b1b_row, 'final_judge_wall_time')}`s，"
            f"vars `{neg_feas_value(b1b_row, 'final_judge_variable_count')}`，"
            f"rows `{neg_feas_value(b1b_row, 'final_judge_constraint_count')}`，"
            f"enabled `{neg_feas_value(b1b_row, 'final_judge_negative_feasibility_search_enabled')}`；"
            "该 negative-only row 的最后一次 final judge 仍在 60s 内超时，没有证明 no-negative，也没有返回新的负列；"
            "是否能找负列以 hybrid 累计 telemetry 为准。"
        )
    compact_pricing_hybrid_line = ""
    compact_pricing_hybrid_rows_path = (
        output_dir
        / "compact_pricing_hybrid_probe_scale030_b1b_reference_seed_60s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_hybrid_rows_path.exists():
        hybrid_rows = _read_rows(compact_pricing_hybrid_rows_path)
        by_mode = {_row_mode(row): row for row in hybrid_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def hybrid_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_hybrid_line = (
            "- compact-pricing hybrid final-judge probe 显示："
            f"pricing rounds `{hybrid_value(b1b_row, 'pricing_round_count')}`，"
            f"added columns `{hybrid_value(b1b_row, 'added_column_count')}`，"
            f"final judge calls `{hybrid_value(b1b_row, 'final_judge_call_count')}`，"
            f"found-negative calls `{hybrid_value(b1b_row, 'final_judge_found_negative_count')}`，"
            f"best negative RC `{hybrid_value(b1b_row, 'final_judge_best_negative_reduced_cost')}`，"
            f"incomplete calls `{hybrid_value(b1b_row, 'final_judge_incomplete_count')}`；"
            "hybrid 能找到真实负列并推进 root CG，但 60s 内仍未形成 no-negative proof。"
        )
    compact_pricing_hybrid_300s_line = ""
    compact_pricing_hybrid_300s_rows_path = (
        output_dir
        / "compact_pricing_hybrid_probe_scale030_b1b_reference_seed_300s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_hybrid_300s_rows_path.exists():
        hybrid_300s_rows = _read_rows(compact_pricing_hybrid_300s_rows_path)
        by_mode = {_row_mode(row): row for row in hybrid_300s_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def hybrid_300s_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_hybrid_300s_line = (
            "- compact-pricing hybrid 300s probe 显示："
            f"pricing rounds `{hybrid_300s_value(b1b_row, 'pricing_round_count')}`，"
            f"added columns `{hybrid_300s_value(b1b_row, 'added_column_count')}`，"
            f"final judge calls `{hybrid_300s_value(b1b_row, 'final_judge_call_count')}`，"
            f"found-negative calls `{hybrid_300s_value(b1b_row, 'final_judge_found_negative_count')}`，"
            f"best negative RC `{hybrid_300s_value(b1b_row, 'final_judge_best_negative_reduced_cost')}`，"
            f"incomplete calls `{hybrid_300s_value(b1b_row, 'final_judge_incomplete_count')}`；"
            "hybrid 在更长预算下持续产生有效列，但仍未完成最终 no-negative proof。"
        )
    compact_pricing_hybrid_3600s_line = ""
    compact_pricing_hybrid_3600s_rows_path = (
        output_dir
        / "compact_pricing_hybrid_probe_scale030_b1b_reference_seed_3600s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_hybrid_3600s_rows_path.exists():
        hybrid_3600s_rows = _read_rows(compact_pricing_hybrid_3600s_rows_path)
        by_mode = {_row_mode(row): row for row in hybrid_3600s_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def hybrid_3600s_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_hybrid_3600s_line = (
            "- compact-pricing hybrid 3600s probe 显示："
            f"pricing rounds `{hybrid_3600s_value(b1b_row, 'pricing_round_count')}`，"
            f"added columns `{hybrid_3600s_value(b1b_row, 'added_column_count')}`，"
            f"found-negative calls `{hybrid_3600s_value(b1b_row, 'final_judge_found_negative_count')}`，"
            f"best negative RC `{hybrid_3600s_value(b1b_row, 'final_judge_best_negative_reduced_cost')}`，"
            f"last best RC `{hybrid_3600s_value(b1b_row, 'final_judge_best_reduced_cost')}`，"
            f"last dual bound `{hybrid_3600s_value(b1b_row, 'final_judge_dual_bound')}`；"
            "3600s 内已消除多轮负列，但最终 no-negative proof 仍未闭合。"
        )
    compact_pricing_batch_probe_line = ""
    compact_pricing_batch_probe_json_path = (
        output_dir
        / "compact_pricing_batch_probe_scale030_b1b_reference_seed_120s"
        / "probe.json"
    )
    if compact_pricing_batch_probe_json_path.exists():
        batch_probe = json.loads(compact_pricing_batch_probe_json_path.read_text(encoding="utf-8"))
        final_judge = batch_probe.get("final_judge") or {}
        compact_pricing_batch_probe_line = (
            "- compact-pricing batch negative discovery 已加入 final judge："
            "restricted negative-feasibility 子问题只用于发现多条人工 RC 审计过的负列，不能证明 no-negative；"
            "证书仍必须来自后续 unrestricted proof。"
            "30-scale 首实例 120s probe 显示："
            f"单个 B1B root pricing round 内 batch search calls `{final_judge.get('compact_negative_batch_search_call_count')}`，"
            f"返回并加入 `{batch_probe.get('added_column_count')}` 条负列，"
            f"best RC `{final_judge.get('best_reduced_cost')}`，"
            f"final judge phase `{final_judge.get('compact_pricing_phase')}`，"
            f"`can_certify_no_negative={final_judge.get('can_certify_no_negative')}`，"
            f"scope 仍为 `{batch_probe.get('certificate_scope')}`。"
        )
    compact_pricing_batch_300s_probe_line = ""
    compact_pricing_batch_300s_probe_json_path = (
        output_dir
        / "compact_pricing_batch_probe_scale030_b1b_reference_seed_300s"
        / "probe.json"
    )
    if compact_pricing_batch_300s_probe_json_path.exists():
        batch_probe = json.loads(compact_pricing_batch_300s_probe_json_path.read_text(encoding="utf-8"))
        history = list(batch_probe.get("history") or [])
        first = history[0] if history else {}
        last = history[-1] if history else {}
        compact_pricing_batch_300s_probe_line = (
            "- compact-pricing batch 300s probe 显示："
            f"30-scale 首实例 `{batch_probe.get('pricing_round_count')}` 个 B1B root pricing rounds 内加入 "
            f"`{batch_probe.get('added_column_count')}` 条负列，"
            f"best RC 从第 1 轮 `{first.get('best_reduced_cost')}` 到第 "
            f"`{last.get('round')}` 轮 `{last.get('best_reduced_cost')}`；"
            "对比旧 hybrid 300s 的 `6` rounds / `5` columns，batch 明显减少外层 RMP/final-judge rounds，"
            f"但总 wall time 仍约 `{batch_probe.get('elapsed_sec')}`s，说明当前主要收益是减少 RMP 重解次数，"
            "最终 no-negative proof 仍未闭合。"
        )
    compact_pricing_batch_target5_probe_line = ""
    compact_pricing_batch_target5_probe_json_path = (
        output_dir
        / "compact_pricing_batch_target5_probe_scale030_b1b_reference_seed_300s"
        / "probe.json"
    )
    if compact_pricing_batch_target5_probe_json_path.exists():
        batch_probe = json.loads(compact_pricing_batch_target5_probe_json_path.read_text(encoding="utf-8"))
        final_judge = batch_probe.get("final_judge") or {}
        compact_pricing_batch_target5_probe_line = (
            "- compact-pricing batch target=5 300s probe 显示："
            "通过 `LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET=5`，"
            f"30-scale 首实例单个 B1B root pricing round 内加入 `{batch_probe.get('added_column_count')}` 条负列，"
            f"batch search calls `{final_judge.get('compact_negative_batch_search_call_count')}`，"
            f"wall `{batch_probe.get('elapsed_sec')}s`，"
            f"best RC `{final_judge.get('best_reduced_cost')}`；"
            "相比 target=3 的 `2` rounds / `5` columns，target=5 进一步减少 RMP 重解，"
            f"但仍为 `{batch_probe.get('certificate_scope')}`，不能证明 no-negative。"
        )
    compact_pricing_batch_target5_3600s_probe_line = ""
    compact_pricing_batch_target5_3600s_probe_json_path = (
        output_dir
        / "compact_pricing_batch_target5_probe_scale030_b1b_reference_seed_3600s"
        / "probe.json"
    )
    if compact_pricing_batch_target5_3600s_probe_json_path.exists():
        batch_probe = json.loads(
            compact_pricing_batch_target5_3600s_probe_json_path.read_text(encoding="utf-8")
        )
        history = list(batch_probe.get("history") or [])
        best_rc_values = [
            row.get("best_reduced_cost")
            for row in history
            if isinstance(row.get("best_reduced_cost"), (int, float))
        ]
        best_negative_rc = min(best_rc_values) if best_rc_values else None
        compact_pricing_batch_target5_3600s_probe_line = (
            "- compact-pricing batch target=5 3600s probe 显示："
            f"30-scale 首实例在 `{batch_probe.get('elapsed_sec')}`s 内完成 "
            f"`{batch_probe.get('pricing_round_count')}` 个 B1B root pricing rounds、加入 "
            f"`{batch_probe.get('added_column_count')}` 条负列，"
            f"found-negative calls `{batch_probe.get('final_judge_found_negative_count')}`，"
            f"best negative RC `{best_negative_rc}`；"
            "相比旧 hybrid 3600s 的 `36` rounds / `35` columns，batch target=5 明显提高单轮加列效率，"
            f"但最后一轮仍为 `{batch_probe.get('pricing_state')}` / `{batch_probe.get('certificate_scope')}`，"
            "没有形成 no-negative proof，因此不是 BPC certificate。"
        )
    compact_pricing_resume_probe_line = ""
    compact_pricing_resume_stage1_json_path = (
        output_dir
        / "compact_pricing_batch_resume_stage1_scale030_b1b_reference_seed_120s"
        / "probe.json"
    )
    compact_pricing_resume_stage2_json_path = (
        output_dir
        / "compact_pricing_batch_resume_stage2_scale030_b1b_reference_seed_120s"
        / "probe.json"
    )
    if compact_pricing_resume_stage1_json_path.exists() and compact_pricing_resume_stage2_json_path.exists():
        stage1 = json.loads(compact_pricing_resume_stage1_json_path.read_text(encoding="utf-8"))
        stage2 = json.loads(compact_pricing_resume_stage2_json_path.read_text(encoding="utf-8"))
        compact_pricing_resume_probe_line = (
            "- compact-pricing staged resume smoke 显示："
            f"stage1 在 `{stage1.get('elapsed_sec')}`s 内从 reference seed 加入 "
            f"`{stage1.get('added_column_count')}` 条负列并保存 `{len(stage1.get('active_columns') or [])}` 个 active columns；"
            f"stage2 从这 `{stage2.get('config', {}).get('resume_initial_column_count')}` 列恢复，"
            f"重新解 RMP/final judge 后在 `{stage2.get('elapsed_sec')}`s 内再加入 "
            f"`{stage2.get('added_column_count')}` 条负列，保存 `{len(stage2.get('active_columns') or [])}` 个 active columns。"
            "该机制只复用列池，不复用 dual/certificate；"
            f"结果仍为 `{stage2.get('certificate_scope')}`，但后续 30-scale 长跑可以从 staged state 继续。"
        )
    compact_pricing_staged_runner_line = ""
    compact_pricing_staged_runner_manifest_path = (
        output_dir
        / "compact_pricing_staged_resume_scale030_b1b_reference_seed_120s"
        / "staged_resume_manifest.json"
    )
    if compact_pricing_staged_runner_manifest_path.exists():
        manifest = json.loads(compact_pricing_staged_runner_manifest_path.read_text(encoding="utf-8"))
        rows = list(manifest.get("stages") or [])
        latest = rows[-1] if rows else {}
        first = rows[0] if rows else {}
        total_added = sum(int(row.get("added_column_count") or 0) for row in rows)
        stage_bits = []
        for row in rows:
            config_note = (
                f" / batch `{row.get('batch_target')}`"
                if row.get("batch_target") not in {None, ""}
                else ""
            )
            stage_bits.append(
                f"stage{row.get('stage_index')} 为 `{row.get('elapsed_sec')}`s{config_note} / "
                f"best RC `{row.get('best_negative_reduced_cost')}`"
            )
        compact_pricing_staged_runner_line = (
            "- compact-pricing staged runner continuation 显示："
            f"从 staged smoke 的 `{first.get('resume_initial_column_count')}` 个 active columns 继续，"
            f"`{len(rows)}` 个 staged runner stages 合计加入 `{total_added}` 条负列并保存 "
            f"`{latest.get('active_column_count')}` 个 active columns；"
            f"{'，'.join(stage_bits)}。"
            f"当前仍为 `{latest.get('certificate_scope')}`，但证明 staged runner 可以在真实 30-scale 上持续累积列池。"
        )
    compact_pricing_mtz_probe_line = ""
    compact_pricing_mtz_rows_path = (
        output_dir
        / "compact_pricing_mtz_probe_scale030_b1b_reference_seed_120s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_mtz_rows_path.exists():
        mtz_rows = _read_rows(compact_pricing_mtz_rows_path)
        by_mode = {_row_mode(row): row for row in mtz_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def mtz_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_mtz_probe_line = (
            "- compact-pricing MTZ-only 120s probe 显示："
            f"pricing rounds `{mtz_value(b1b_row, 'pricing_round_count')}`，"
            f"added columns `{mtz_value(b1b_row, 'added_column_count')}`，"
            f"best negative RC `{mtz_value(b1b_row, 'final_judge_best_negative_reduced_cost')}`，"
            f"vars `{mtz_value(b1b_row, 'final_judge_variable_count')}`，"
            f"rows `{mtz_value(b1b_row, 'final_judge_constraint_count')}`；"
            "MTZ 去掉不连通 task 子环，但短时找负列阶段约束数几乎翻倍，因此不作为 negative-search 默认。"
        )
    compact_pricing_hybrid_mtz_proof_line = ""
    compact_pricing_hybrid_mtz_proof_rows_path = (
        output_dir
        / "compact_pricing_hybrid_mtz_proof_probe_scale030_b1b_reference_seed_120s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_hybrid_mtz_proof_rows_path.exists():
        mtz_proof_rows = _read_rows(compact_pricing_hybrid_mtz_proof_rows_path)
        by_mode = {_row_mode(row): row for row in mtz_proof_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def mtz_proof_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_hybrid_mtz_proof_line = (
            "- compact-pricing hybrid MTZ-proof 120s probe 显示："
            f"pricing rounds `{mtz_proof_value(b1b_row, 'pricing_round_count')}`，"
            f"added columns `{mtz_proof_value(b1b_row, 'added_column_count')}`，"
            f"best negative RC `{mtz_proof_value(b1b_row, 'final_judge_best_negative_reduced_cost')}`，"
            f"last vars `{mtz_proof_value(b1b_row, 'final_judge_variable_count')}`，"
            f"last rows `{mtz_proof_value(b1b_row, 'final_judge_constraint_count')}`，"
            f"last MTZ `{mtz_proof_value(b1b_row, 'final_judge_mtz_connectivity_enabled')}`；"
            "当前默认策略保持 negative-search 轻模型找列，MTZ 只保留给后续 optimization proof phase。"
        )
    compact_pricing_hybrid_tight_m_line = ""
    compact_pricing_hybrid_tight_m_rows_path = (
        output_dir
        / "compact_pricing_hybrid_tight_m_mtz_proof_probe_scale030_b1b_reference_seed_120s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_hybrid_tight_m_rows_path.exists():
        tight_m_rows = _read_rows(compact_pricing_hybrid_tight_m_rows_path)
        by_mode = {_row_mode(row): row for row in tight_m_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def tight_m_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_hybrid_tight_m_line = (
            "- compact-pricing hybrid tight-M 120s probe 显示："
            f"pricing rounds `{tight_m_value(b1b_row, 'pricing_round_count')}`，"
            f"added columns `{tight_m_value(b1b_row, 'added_column_count')}`，"
            f"best negative RC `{tight_m_value(b1b_row, 'final_judge_best_negative_reduced_cost')}`，"
            f"last vars `{tight_m_value(b1b_row, 'final_judge_variable_count')}`，"
            f"last rows `{tight_m_value(b1b_row, 'final_judge_constraint_count')}`；"
            "task-source time big-M 已按 source latest-start 收紧，短时找列结果仍未进入最终 proof phase。"
        )
    compact_pricing_hybrid_duration_lb_line = ""
    compact_pricing_hybrid_duration_lb_rows_path = (
        output_dir
        / "compact_pricing_hybrid_duration_lb_probe_scale030_b1b_reference_seed_120s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_hybrid_duration_lb_rows_path.exists():
        duration_lb_rows = _read_rows(compact_pricing_hybrid_duration_lb_rows_path)
        by_mode = {_row_mode(row): row for row in duration_lb_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def duration_lb_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_hybrid_duration_lb_line = (
            "- compact-pricing hybrid duration-lb 120s probe 显示："
            f"pricing rounds `{duration_lb_value(b1b_row, 'pricing_round_count')}`，"
            f"added columns `{duration_lb_value(b1b_row, 'added_column_count')}`，"
            f"best negative RC `{duration_lb_value(b1b_row, 'final_judge_best_negative_reduced_cost')}`，"
            f"last vars `{duration_lb_value(b1b_row, 'final_judge_variable_count')}`，"
            f"last rows `{duration_lb_value(b1b_row, 'final_judge_constraint_count')}`；"
            "sortie return-start 已加入 service-duration + min depot out/return travel 下界，短时仍未进入最终 proof phase。"
        )
    compact_pricing_replay_line = ""
    compact_pricing_replay_json_path = (
        output_dir / "compact_pricing_replay_round3_mtz_proof_120s" / "replay.json"
    )
    if compact_pricing_replay_json_path.exists():
        try:
            replay = json.loads(compact_pricing_replay_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            replay = {}
        replay_result = replay.get("result") if isinstance(replay.get("result"), dict) else {}
        compact_pricing_replay_line = (
            "- compact-pricing dual replay 显示："
            f"source round `{replay.get('selected_history_round', '')}`，"
            f"replay status `{replay_result.get('status', '')}`，"
            f"pricing state `{replay_result.get('pricing_state', '')}`，"
            f"best RC `{replay_result.get('best_reduced_cost', '')}`，"
            f"dual bound `{replay_result.get('dual_bound', '')}`，"
            f"wall `{replay_result.get('wall_time_sec', '')}`s；"
            "短 120s B1B probe 的最后一轮单独重放后仍能找到负列，说明该短 probe 主要是剩余 row budget 不足，而不是已经进入 no-negative proof。"
        )
    compact_pricing_negative_replay_line = ""
    compact_pricing_negative_replay_json_path = (
        output_dir / "compact_pricing_replay_round3_negative_feas_120s" / "replay.json"
    )
    if compact_pricing_negative_replay_json_path.exists():
        try:
            replay = json.loads(compact_pricing_negative_replay_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            replay = {}
        replay_result = replay.get("result") if isinstance(replay.get("result"), dict) else {}
        compact_pricing_negative_replay_line = (
            "- compact-pricing negative-feasibility replay 显示："
            f"source round `{replay.get('selected_history_round', '')}`，"
            f"pricing state `{replay_result.get('pricing_state', '')}`，"
            f"best RC `{replay_result.get('best_reduced_cost', '')}`，"
            f"dual bound `{replay_result.get('dual_bound', '')}`，"
            f"wall `{replay_result.get('wall_time_sec', '')}`s；"
            "同一轮 dual 用 negative-feasibility formulation 也能找到负列，进一步确认短 probe 的限制来自剩余时间不足。"
        )
    compact_pricing_hybrid_history_line = ""
    compact_pricing_hybrid_history_rows_path = (
        output_dir
        / "compact_pricing_hybrid_history_probe_scale030_b1b_reference_seed_60s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_hybrid_history_rows_path.exists():
        history_rows = _read_rows(compact_pricing_hybrid_history_rows_path)
        by_mode = {_row_mode(row): row for row in history_rows}
        b1b_row = by_mode.get(B1B_MODE, {})
        history = []
        try:
            history = json.loads(str(b1b_row.get("pricing_history_json") or "[]"))
        except json.JSONDecodeError:
            history = []
        first = history[0] if history else {}
        last = history[-1] if history else {}
        compact_pricing_hybrid_history_line = (
            "- B1 pricing history telemetry probe 显示："
            f"history rows `{len(history)}`，"
            f"first state `{first.get('pricing_state', '')}` / RC `{first.get('best_reduced_cost', '')}`，"
            f"last state `{last.get('pricing_state', '')}`；"
            "`pricing_history_json` 已可用于逐轮审计 300s/3600s rows。"
        )
    compact_pricing_flow_probe_line = ""
    compact_pricing_flow_rows_path = (
        output_dir
        / "compact_pricing_flow_probe_scale030_b1b_reference_seed_60s"
        / "b0b1_scale030_resume_rows.json"
    )
    if compact_pricing_flow_rows_path.exists():
        flow_rows = _read_rows(compact_pricing_flow_rows_path)
        by_mode = {_row_mode(row): row for row in flow_rows}
        b1b_row = by_mode.get(B1B_MODE, {})

        def flow_value(row: dict, key: str) -> str:
            value = row.get(key)
            return "" if value in {None, ""} else str(value)

        compact_pricing_flow_probe_line = (
            "- compact single-journey pricing flow-connectivity probe 显示："
            f"status `{flow_value(b1b_row, 'final_judge_status')}`，"
            f"model status `{flow_value(b1b_row, 'final_judge_model_status_name')}`，"
            f"wall `{flow_value(b1b_row, 'final_judge_wall_time')}`s，"
            f"vars `{flow_value(b1b_row, 'final_judge_variable_count')}`，"
            f"rows `{flow_value(b1b_row, 'final_judge_constraint_count')}`；"
            "该 exact-safe tightening 使模型规模接近翻倍，60s 内没有返回可用 best RC/dual bound，"
            "因此保留为可选诊断，不作为默认 30-scale final judge path。"
        )

    lines.extend(
        [
            "",
            "## 30-scale 说明",
            "",
            "- 30-scale rows 是 fail-closed resource-guard rows，不表示 B0/BPC 已求得 30-scale 精确解。",
            "- 优化前 300s probe 结果为 `DIRECT_DP_TIME_LIMIT`：在 `sortie_candidate_generation` 阶段超时，尚未进入 `fleet_set_partition`；`generated_sortie_count=417,487,274`，最大 RSS 约 4.7GB。",
            "- 新增 exact-safe candidate pruning 与 30-scale bounded sortie cache 后，60s probe 仍在 `sortie_candidate_generation` 超时，但 `generated_sortie_count` 从同限时优化前的 90,643,490 降到 8,067,440，最大 RSS 约 0.6GB。",
            "- 新增 reference-solution best-path upper bound、time-aware task-visit lower bound、endpoint path lower bound 与 outgoing/start future-tail lower bound 诊断；5/10/20 首实例 direct-DP objective 与无 reference 上界版本一致。30-scale 首实例 20s probe 得到 repaired reference upper bound `1.919465`，direct-DP root pruning bound `0.841965885`，active bound pruning 因下界太弱而关闭，`journey_label_bound_pruned_count=0`；当前仍不足以切掉 early candidate generation。",
            "- B0/B1/B2/B3 runners 已把 row timeout 传入内部 direct-DP；B3B 在 B0 direct-DP 未给出 incumbent 时会先 fail-closed，不再继续枚举 representative universe。",
            "- B3B fail-closed payload 现在会记录 instance `reference_solution` 修复得到的 feasible upper bound，但仍保持 `FEASIBLE_INCUMBENT_ONLY`，不会把 reference incumbent 当作 BPC certificate。30-scale reference incumbent audit 显示 20/20 实例可重建 feasible upper bound，mean objective `1.8890827`。",
            "- Compact fixed-graph MILP 的 HiGHS backend 已在 5/10-scale 首实例与 B0 direct-DP 对齐；Gurobi backend 在本机从 10-scale 起被 size-limited license 拒绝。",
            "- 30-scale 首实例 HiGHS compact 300s 探针已运行：无 warm-start 时没有 feasible incumbent；reference warm-start 后得到 incumbent `objective=1.9146`，lower bound `1.259623395`，gap 约 34.21%，RSS 峰值约 2.48GB。",
            compact_probe_line,
            *([compact_bound_probe_line] if compact_bound_probe_line else []),
            *([compact_duration_lb_probe_line] if compact_duration_lb_probe_line else []),
            *([compact_tight_m_probe_line] if compact_tight_m_probe_line else []),
            *([bound_gap_line] if bound_gap_line else []),
            *([threshold_probe_line] if threshold_probe_line else []),
            *([strict_b0b1_probe_line] if strict_b0b1_probe_line else []),
            *([reference_seed_no_b0_probe_line] if reference_seed_no_b0_probe_line else []),
            *([final_judge_deadline_probe_line] if final_judge_deadline_probe_line else []),
            *([compact_pricing_probe_line] if compact_pricing_probe_line else []),
            *([compact_pricing_default_telemetry_line] if compact_pricing_default_telemetry_line else []),
            *([compact_pricing_negative_feasibility_line] if compact_pricing_negative_feasibility_line else []),
            *([compact_pricing_hybrid_line] if compact_pricing_hybrid_line else []),
            *([compact_pricing_hybrid_300s_line] if compact_pricing_hybrid_300s_line else []),
            *([compact_pricing_hybrid_3600s_line] if compact_pricing_hybrid_3600s_line else []),
            *([compact_pricing_batch_probe_line] if compact_pricing_batch_probe_line else []),
            *([compact_pricing_batch_300s_probe_line] if compact_pricing_batch_300s_probe_line else []),
            *([compact_pricing_batch_target5_probe_line] if compact_pricing_batch_target5_probe_line else []),
            *(
                [compact_pricing_batch_target5_3600s_probe_line]
                if compact_pricing_batch_target5_3600s_probe_line
                else []
            ),
            *([compact_pricing_resume_probe_line] if compact_pricing_resume_probe_line else []),
            *([compact_pricing_staged_runner_line] if compact_pricing_staged_runner_line else []),
            *([compact_pricing_mtz_probe_line] if compact_pricing_mtz_probe_line else []),
            *([compact_pricing_hybrid_mtz_proof_line] if compact_pricing_hybrid_mtz_proof_line else []),
            *([compact_pricing_hybrid_tight_m_line] if compact_pricing_hybrid_tight_m_line else []),
            *([compact_pricing_hybrid_duration_lb_line] if compact_pricing_hybrid_duration_lb_line else []),
            *([compact_pricing_replay_line] if compact_pricing_replay_line else []),
            *([compact_pricing_negative_replay_line] if compact_pricing_negative_replay_line else []),
            *([compact_pricing_hybrid_history_line] if compact_pricing_hybrid_history_line else []),
            *([compact_pricing_flow_probe_line] if compact_pricing_flow_probe_line else []),
            "- compact product MILP 是 fixed-graph product exact oracle，不是 BPC root/tree certificate；"
            "compact pricing MILP 只有在 exact pricing optimal 且 no-negative 时才能进入 BPC final judge 证书。"
            "当前 30-scale 仍未实际闭合，且未跑 3600s full compact/product/pricing 证明实验。",
            "- 因此当前 official BPC certificate 结果可用于 5/10/20；30-scale 需要后续设计新的 exact-safe pricing/certificate path，不能只依赖现有 direct universe 枚举。",
            "",
            "## Artifact 路径",
            "",
            f"- index: `{output_dir / 'index.json'}`",
            "- per-family CSV/summary/report: `b0b1_*`, `b2_*`, `b3_*`。",
            f"- 30-scale B0 probe: `{output_dir / 'scale30_b0_direct_dp_probe_300s_zh.md'}`",
            f"- 30-scale B0 post-pruning probe: `{output_dir / 'scale30_b0_direct_dp_probe_60s_after_candidate_pruning_zh.md'}`",
            f"- 30-scale B0 reference-bound probe: `{output_dir / 'scale30_b0_direct_dp_probe_20s_reference_bound_pruning_zh.md'}`",
            f"- 30-scale B3B safe-fail probe: `{output_dir / 'scale30_b3b_safe_fail_probe_20s_zh.md'}`",
            f"- 30-scale reference incumbent audit: `{output_dir / 'scale030_reference_incumbent_audit.md'}`",
            f"- 30-scale HiGHS compact probe: `{output_dir / 'scale30_highs_compact_probe_300s_zh.md'}`",
            f"- 30-scale resumable compact product rows: `{output_dir / 'compact_product_scale030_report_zh.md'}`",
            f"- 30-scale compact bound probe: `{output_dir / 'compact_bound_probe_scale030_300s' / 'compact_product_scale030_report_zh.md'}`",
            f"- 30-scale duration-lower-bound compact probe: `{output_dir / 'compact_duration_lb_probe_scale030_60s' / 'compact_product_scale030_report_zh.md'}`",
            f"- 30-scale tight big-M compact probe: `{output_dir / 'compact_tight_m_probe_scale030_300s' / 'compact_product_scale030_report_zh.md'}`",
            f"- 30-scale bound-gap diagnostic: `{output_dir / 'scale30_bound_gap_diagnostic_zh.md'}`",
            f"- 30-scale direct bound-pruning threshold probe: `{output_dir / 'scale30_direct_bound_pruning_threshold_probe_20s_zh.md'}`",
            f"- 30-scale B0/B1 strict-progress probe: `{output_dir / 'scale30_b0b1_strict_progress_probe_60s_zh.md'}`",
            f"- 30-scale B1B reference-seed-without-B0 probe: `{output_dir / 'scale30_b1b_reference_seed_without_b0_probe_60s_zh.md'}`",
            f"- 30-scale B1B final-judge deadline telemetry probe: `{output_dir / 'scale30_b1b_final_judge_deadline_telemetry_probe_60s_zh.md'}`",
            f"- 30-scale B1B compact-pricing optimization-mode final-judge probe: `{output_dir / 'scale30_b1b_compact_pricing_final_judge_probe_60s_zh.md'}`",
            f"- 30-scale B1B compact-pricing optimization-only telemetry probe: `{output_dir / 'scale30_b1b_compact_pricing_default_telemetry_probe_60s_zh.md'}`",
            f"- 30-scale B1B compact-pricing negative-feasibility probe: `{output_dir / 'scale30_b1b_compact_pricing_negative_feasibility_probe_60s_zh.md'}`",
            f"- 30-scale B1B compact-pricing hybrid final-judge probe: `{output_dir / 'scale30_b1b_compact_pricing_hybrid_probe_60s_zh.md'}`",
            f"- 30-scale B1B compact-pricing hybrid 300s probe: `{output_dir / 'scale30_b1b_compact_pricing_hybrid_probe_300s_zh.md'}`",
            f"- 30-scale B1B compact-pricing hybrid 3600s probe: `{output_dir / 'scale30_b1b_compact_pricing_hybrid_probe_3600s_zh.md'}`",
            f"- 30-scale B1B compact-pricing batch negative discovery 120s probe: `{output_dir / 'compact_pricing_batch_probe_scale030_b1b_reference_seed_120s' / 'probe_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing batch negative discovery 300s probe: `{output_dir / 'compact_pricing_batch_probe_scale030_b1b_reference_seed_300s' / 'probe_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing batch target=5 300s probe: `{output_dir / 'compact_pricing_batch_target5_probe_scale030_b1b_reference_seed_300s' / 'probe_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing batch target=5 3600s probe: `{output_dir / 'compact_pricing_batch_target5_probe_scale030_b1b_reference_seed_3600s' / 'probe_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing staged resume stage1: `{output_dir / 'compact_pricing_batch_resume_stage1_scale030_b1b_reference_seed_120s' / 'probe_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing staged resume stage2: `{output_dir / 'compact_pricing_batch_resume_stage2_scale030_b1b_reference_seed_120s' / 'probe_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing staged runner continuation: `{output_dir / 'compact_pricing_staged_resume_scale030_b1b_reference_seed_120s' / 'staged_resume_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing MTZ-only 120s probe: `{output_dir / 'compact_pricing_mtz_probe_scale030_b1b_reference_seed_120s' / 'b0b1_scale030_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing hybrid MTZ-proof 120s probe: `{output_dir / 'compact_pricing_hybrid_mtz_proof_probe_scale030_b1b_reference_seed_120s' / 'b0b1_scale030_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing hybrid tight-M 120s probe: `{output_dir / 'compact_pricing_hybrid_tight_m_mtz_proof_probe_scale030_b1b_reference_seed_120s' / 'b0b1_scale030_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing hybrid duration-lb 120s probe: `{output_dir / 'compact_pricing_hybrid_duration_lb_probe_scale030_b1b_reference_seed_120s' / 'b0b1_scale030_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing dual replay: `{output_dir / 'compact_pricing_replay_round3_mtz_proof_120s' / 'replay_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing negative-feasibility replay: `{output_dir / 'compact_pricing_replay_round3_negative_feas_120s' / 'replay_report_zh.md'}`",
            f"- 30-scale B1B compact-pricing hybrid history probe: `{output_dir / 'scale30_b1b_compact_pricing_hybrid_history_probe_60s_zh.md'}`",
            f"- 30-scale B1B compact-pricing flow-connectivity probe: `{output_dir / 'scale30_b1b_compact_pricing_flow_probe_60s_zh.md'}`",
            f"- compact oracle probe: `{output_dir / 'gurobi_compact_oracle_probe_zh.md'}`",
            f"- completion audit: `{output_dir / 'completion_audit_zh.md'}`",
        ]
    )
    (output_dir / "normalized_objective_full_report_zh.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _row_mode(row: dict) -> str:
    for key in ("mode", "candidate_name", "b1_mode"):
        value = row.get(key)
        if value not in {None, ""}:
            return str(value)
    return "UNKNOWN"


def _row_wall_time(row: dict) -> float | None:
    for key in ("wall_time", "wall_time_s", "elapsed_s", "row_elapsed_s", "solve_time_s"):
        value = row.get(key)
        if value in {None, ""}:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def _final_judge_universe_value(row: dict, key: str) -> str:
    total = _int_or_none(row.get("final_judge_representative_universe_total_count"))
    if total is None:
        scale = _int_or_none(row.get("scale"))
        total = (1 << scale) - 1 if scale is not None and scale >= 0 else None
    audited = _int_or_none(row.get("final_judge_representative_universe_audited_count"))
    if audited is None:
        audited = _int_or_none(row.get("final_judge_generated_journey_count"))
    remaining = _int_or_none(row.get("final_judge_representative_universe_remaining_count"))
    if remaining is None and total is not None and audited is not None:
        remaining = max(0, total - audited)
    ratio_value = row.get("final_judge_representative_universe_completion_ratio")
    ratio = _float_or_none(ratio_value)
    if ratio is None and total not in {None, 0} and audited is not None:
        ratio = round(float(audited) / float(total), 12)
    values = {
        "total": _format_int(total),
        "audited": _format_int(audited),
        "remaining": _format_int(remaining),
        "ratio": "" if ratio is None else f"{ratio:.12g}",
    }
    return values[key]


def _int_or_none(value) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float_or_none(value) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_int(value: int | None) -> str:
    return "" if value is None else f"{int(value):,}"


def _preserved_index_entries(index_json: Path, *, requested_pairs: set[tuple[str, int]]) -> list[dict]:
    if not index_json.exists():
        return []
    try:
        payload = json.loads(index_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    entries = []
    for entry in payload.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        pair = (str(entry.get("family") or ""), int(entry.get("scale") or -1))
        if pair in requested_pairs:
            continue
        entries.append(dict(entry))
    return entries


if __name__ == "__main__":
    raise SystemExit(main())
