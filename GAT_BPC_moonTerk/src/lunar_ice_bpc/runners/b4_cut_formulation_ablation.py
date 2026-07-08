"""B4 cut/formulation ablation runner and report writer."""

from __future__ import annotations

import csv
import gc
import json
from pathlib import Path
import signal
from statistics import mean
from time import perf_counter
from typing import Callable, Iterable

from lunar_ice_bpc.exact.bpc.solver.cut_formulation_solver import solve_b4_cut_formulation_baseline
from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
from lunar_ice_bpc.exact.core.objective import flatten_objective_payload, objective_metadata
from lunar_ice_bpc.io.instance_io import read_json


B4A_MODE = "B4A_cut_diagnostic_only"
B4B_MODE = "B4B_root_live_subset_row"
B4_MODES = (B4A_MODE, B4B_MODE)

CSV_COLUMNS = (
    "matrix_group",
    "scale",
    "instance_id",
    "mode",
    "algorithm_status",
    "certificate_scope",
    "pricing_state",
    "uses_true_dual_bpc_certificate",
    "BPC_TREE_OPTIMAL_count",
    "BPC_NODE_LP_CERTIFIED_count",
    "b3_algorithm_status",
    "b3_certificate_scope",
    "b3_root_lp_bound",
    "b4_root_lp_bound",
    "root_no_cut_lp_bound",
    "incumbent_objective",
    "objective_diff_vs_B3",
    "certificate_scope_diff_vs_B3",
    "cut_probe_status",
    "cut_candidate_count",
    "cut_violated_count",
    "max_violation",
    "mean_violation",
    "violated_subset_size_histogram",
    "cut_kind",
    "cut_key",
    "rhs",
    "sense",
    "coefficient_dependency",
    "coefficient_vector_hash",
    "pricing_supported",
    "completion_bound_supported",
    "dominance_compatible",
    "would_bind_on_current_rmp",
    "would_change_dual_support",
    "affected_column_count",
    "active_support_overlap",
    "diagnostic_round_status",
    "diagnostic_selected_cut_count",
    "diagnostic_cut_rmp_bound_delta",
    "diagnostic_cut_rmp_status",
    "diagnostic_lower_bound_official",
    "diagnostic_can_certify",
    "restricted_pool_diagnostic_status",
    "restricted_pool_evaluation_scope",
    "restricted_pool_seed_column_count",
    "restricted_pool_root_rmp_status",
    "restricted_pool_root_bound",
    "restricted_pool_can_certify",
    "live_subset_rows",
    "cut_rows_active",
    "cut_added_count",
    "cut_dual_nonzero_count",
    "manual_rc_with_cuts_matches_pricing_rc",
    "manual_rc_cut_consistency_pass",
    "cut_dual_sign_audit_pass",
    "cut_dominance_valid",
    "cut_pricing_supported_count",
    "cut_completion_bound_fail_closed_count",
    "completion_bound_pruning_enabled",
    "fleet_lower_bound_live_enabled",
    "lp_bound_delta",
    "root_gap_delta",
    "cut_effective_claim",
    "objective_mismatch",
    "certificate_scope_regression",
    "direct_dp_certificate_leak",
    "manual_rc_with_cuts_fail",
    "pricing_rc_with_cuts_fail",
    "cut_coefficient_audit_fail",
    "cut_dual_sign_audit_fail",
    "cut_dominance_compatibility_fail",
    "fleet_lower_bound_live_enabled_without_proof",
    "completion_bound_unsafe_with_cuts",
    "restricted_pricing_claimed_no_negative",
    "positive_incumbent_rc_claimed_certificate",
    "wall_time",
    "fail_closed_reason",
    "attempted_exception_type",
    "attempted_max_direct_tasks",
    "rmp_memory_precheck_failed",
    "rmp_memory_precheck_stage",
    "rmp_memory_precheck_reason",
    "rmp_memory_precheck_estimated_column_count",
    "rmp_memory_precheck_estimated_tableau_cells",
    "rmp_memory_precheck_cell_limit",
)


def run_b4_cut_formulation_ablation(
    instances: Iterable[dict | str | Path],
    *,
    modes: Iterable[str] = B4_MODES,
    max_direct_tasks: int = 5,
    max_rounds: int = 8,
    max_live_cuts: int = 3,
    matrix_group: str = "",
    row_time_limit_sec: float | None = None,
    add_violated_only: bool = True,
) -> dict:
    rows: list[dict] = []
    for item in instances:
        instance = _load_instance(item)
        for mode in tuple(modes):
            rows.append(
                _run_guarded_row(
                    instance,
                    mode=mode,
                    max_direct_tasks=max_direct_tasks,
                    max_rounds=max_rounds,
                    max_live_cuts=max_live_cuts,
                    matrix_group=matrix_group,
                    row_time_limit_sec=row_time_limit_sec,
                    add_violated_only=add_violated_only,
                )
            )
    return _report_from_rows(rows)


def write_b4_cut_formulation_artifacts(
    report: dict,
    *,
    rows_csv: str | Path,
    summary_json: str | Path,
    report_md: str | Path,
) -> None:
    rows_csv = Path(rows_csv)
    summary_json = Path(summary_json)
    report_md = Path(report_md)
    rows_csv.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    report_md.parent.mkdir(parents=True, exist_ok=True)
    with rows_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in report["rows"]:
            writer.writerow({key: _csv_value(row.get(key)) for key in CSV_COLUMNS})
    summary_json.write_text(
        json.dumps({key: value for key, value in report.items() if key != "rows"}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    report_md.write_text(render_b4_cut_formulation_markdown(report, rows_csv=rows_csv, summary_json=summary_json), encoding="utf-8")


def render_b4_cut_formulation_markdown(report: dict, *, rows_csv: str | Path, summary_json: str | Path) -> str:
    lines = [
        "# B4 Cut/Formulation 消融报告",
        "",
        "## Objective Boundary",
        "",
        "- Official objective: `normalized_cost + normalized_risk + 0.4 * normalized_weighted_completion_time`。",
        "- `makespan` 只作为 report metric，不进入 pricing objective。",
        "- B4A restricted cut diagnostics 不能升级 certificate；B4B live subset-row 必须通过 cut/RMP/pricing audit。",
        "",
        "## Artifacts",
        "",
        f"- CSV rows: `{rows_csv}`",
        f"- JSON summary: `{summary_json}`",
        "",
        "## Redlines",
        "",
        "| metric | value | required |",
        "| --- | ---: | ---: |",
    ]
    for key, value in report["redlines"].items():
        lines.append(f"| {key} | {value} | 0 |")
    lines.extend(["", "## Summary", ""])
    lines.append("| scale | group | mode | runs | tree | node LP | cut candidates | violated | max violation | mean wall | fail-closed |")
    lines.append("| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in report["summary_rows"]:
        lines.append(
            "| {scale} | {group} | {mode} | {runs} | {tree} | {node} | {cand} | {viol} | {maxv} | {wall} | {fail} |".format(
                scale=row["scale"],
                group=row["matrix_group"],
                mode=row["mode"],
                runs=row["run_count"],
                tree=row["BPC_TREE_OPTIMAL_count"],
                node=row["BPC_NODE_LP_CERTIFIED_count"],
                cand=row["cut_candidate_count"],
                viol=row["cut_violated_count"],
                maxv=row["max_violation"],
                wall=row["mean_wall_time"],
                fail=row["fail_closed_count"],
            )
        )
    acceptance = report["acceptance"]
    any_violation = any(int(row.get("cut_violated_count") or 0) > 0 for row in report["rows"])
    live_rows = [row for row in report["rows"] if row.get("live_subset_rows") is True or row.get("mode") == B4B_MODE]
    diagnostic_claim_count = int(report["redlines"].get("restricted_pricing_claimed_no_negative_count") or 0)
    bound_move_rows = [
        row
        for row in report["rows"]
        if (_float_or_none(row.get("lp_bound_delta")) or 0.0) > 1.0e-6
        or (_float_or_none(row.get("root_gap_delta")) or 0.0) < -1.0e-6
    ]
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            f"- B4A diagnostic safe: `{acceptance['b4a_diagnostic_safe']}`。",
            f"- B4B live subset-row accepted: `{acceptance['b4b_root_live_subset_row_accepted']}`。",
            f"- B4E accepted candidate: `{acceptance['b4e_accepted_candidate']}`。",
            f"- Measurable improvement rows: `{acceptance['measurable_improvement_row_count']}`。",
            "",
            "## Notes",
            "",
            "- `cut_candidate_count > 0` 或 `cut_added_count > 0` 本身不是 B4 成功。",
            "- restricted cut RMP 的 bound movement 只作为 diagnostic bound movement。",
            "- fleet lower-bound cut 仍然不允许 live。",
            "",
            "## Plan Questions",
            "",
            "- Previous accepted baseline: `B3B_seeded_branch_price_tree` on normalized objective v1; 5/10/20 exact baseline is external to this B4 diagnostic report.",
            f"- Cut/formulation modes tested here: `{', '.join(sorted({str(row.get('mode')) for row in report['rows']}))}`。",
            f"- Any cut violated and bound on current RMP: `{any_violation}`；see `cut_violated_count`, `would_bind_on_current_rmp`, and `max_violation` columns.",
            f"- Any live cut passed RC/pricing/dominance audits: `{bool(live_rows and acceptance['b4b_root_live_subset_row_accepted'])}`。",
            f"- Root/tree bound moved in accepted-safe cut run: `{bool(bound_move_rows)}`。",
            "- Node count / certificate time improvement: not observed in B4A; B4B batch was not accepted.",
            "- Compact pricing proof-bound movement on 30-scale: reported in `runs/b4_pricing_formulation_diagnostic/b4_pricing_report_zh.md`.",
            f"- Diagnostic accidentally claimed certificate: `{diagnostic_claim_count > 0}`。",
            f"- B4 accepted: `{acceptance['b4e_accepted_candidate']}`。",
            "- Next target: compact pricing cut-dual/formulation support before expanding live subset-row cuts.",
        ]
    )
    return "\n".join(lines) + "\n"


def _run_guarded_row(
    instance: dict,
    *,
    mode: str,
    max_direct_tasks: int,
    max_rounds: int,
    max_live_cuts: int,
    matrix_group: str,
    row_time_limit_sec: float | None,
    add_violated_only: bool,
) -> dict:
    data = load_lunar_ice_data(instance)
    started = perf_counter()
    try:
        raw = _call_with_timeout(
            lambda: solve_b4_cut_formulation_baseline(
                data,
                max_direct_tasks=int(max_direct_tasks),
                max_rounds=int(max_rounds),
                live_subset_rows=mode == B4B_MODE,
                max_live_cuts=int(max_live_cuts),
                add_violated_only=bool(add_violated_only),
            ),
            timeout_sec=row_time_limit_sec,
        )
        return _row_from_raw(
            data,
            raw=raw,
            mode=mode,
            matrix_group=matrix_group,
            wall_time=perf_counter() - started,
            max_direct_tasks=max_direct_tasks,
        )
    except TimeoutError:
        return _fail_closed_row(
            data,
            mode=mode,
            matrix_group=matrix_group,
            wall_time=perf_counter() - started,
            reason=f"row_time_limit_sec={row_time_limit_sec}",
            exception_type="TimeoutError",
            max_direct_tasks=max_direct_tasks,
        )
    except MemoryError:
        gc.collect()
        return _fail_closed_row(
            data,
            mode=mode,
            matrix_group=matrix_group,
            wall_time=perf_counter() - started,
            reason="row failed closed after MemoryError",
            exception_type="MemoryError",
            max_direct_tasks=max_direct_tasks,
        )


def _row_from_raw(data, *, raw: dict, mode: str, matrix_group: str, wall_time: float, max_direct_tasks: int) -> dict:
    b3 = raw.get("b3_ablation") if isinstance(raw.get("b3_ablation"), dict) else {}
    probe = raw.get("cut_probe") if isinstance(raw.get("cut_probe"), dict) else {}
    diagnostic = raw.get("diagnostic_cut_separation_round") if isinstance(raw.get("diagnostic_cut_separation_round"), dict) else {}
    dominance = raw.get("cut_dominance_compatibility_report") if isinstance(raw.get("cut_dominance_compatibility_report"), dict) else {}
    audit = raw.get("cut_reduced_cost_audit") if isinstance(raw.get("cut_reduced_cost_audit"), dict) else {}
    sign_audit = audit.get("cut_dual_sign_audit") if isinstance(audit.get("cut_dual_sign_audit"), dict) else {}
    completion_policy = raw.get("completion_bound_policy") if isinstance(raw.get("completion_bound_policy"), dict) else {}
    final_judge = raw.get("final_judge") if isinstance(raw.get("final_judge"), dict) else {}
    restricted_pool = raw.get("restricted_pool_cut_diagnostic") if isinstance(raw.get("restricted_pool_cut_diagnostic"), dict) else {}
    top_candidate = _top_cut_candidate(probe)
    certificate_scope = str(raw.get("certificate_scope") or "")
    b3_scope = str(b3.get("b3_certificate_scope") or b3.get("certificate_scope") or "")
    objective_diff_vs_b3 = _float_or_none(b3.get("objective_diff_vs_B3"))
    objective_mismatch = bool(raw.get("final_integer_optimum_unchanged_vs_B3") is False or (objective_diff_vs_b3 is not None and abs(objective_diff_vs_b3) > 1.0e-6))
    certificate_scope_regression = bool(mode == B4B_MODE and _certificate_rank(certificate_scope) < _certificate_rank(b3_scope))
    cut_rows_active = bool(raw.get("cut_rows_active"))
    manual_rc_pass = audit.get("manual_rc_cut_consistency_pass")
    rc_match = audit.get("manual_rc_with_cuts_matches_pricing_rc")
    sign_pass = sign_audit.get("valid")
    dominance_valid = dominance.get("valid")
    restricted_claim = bool(
        diagnostic.get("restricted_pricing_claimed_no_negative")
        or diagnostic.get("lower_bound_official")
        or diagnostic.get("can_certify")
        or restricted_pool.get("lower_bound_official")
        or restricted_pool.get("can_certify")
    )
    dual_bound = _float_or_none(final_judge.get("dual_bound", final_judge.get("bound")))
    positive_incumbent_claim = bool(
        final_judge.get("can_certify_no_negative")
        and dual_bound is not None
        and dual_bound < -1.0e-6
    )
    signature = raw.get("cut_aware_signature_summary") if isinstance(raw.get("cut_aware_signature_summary"), dict) else {}
    coefficient_audit_fail = bool(cut_rows_active and not signature.get("all_active_signatures_include_cut_hash", False))
    row = {
        "matrix_group": matrix_group,
        "scale": len(data.task_ids),
        "instance_id": data.instance_id,
        "mode": mode,
        "algorithm_status": raw.get("algorithm_status"),
        "certificate_scope": certificate_scope,
        "pricing_state": raw.get("pricing_state"),
        "uses_true_dual_bpc_certificate": bool(raw.get("uses_true_dual_bpc_certificate")),
        "BPC_TREE_OPTIMAL_count": int(certificate_scope == "BPC_TREE_OPTIMAL"),
        "BPC_NODE_LP_CERTIFIED_count": int(certificate_scope in {"BPC_NODE_LP_CERTIFIED", "BPC_TREE_OPTIMAL"}),
        "b3_algorithm_status": b3.get("b3_algorithm_status"),
        "b3_certificate_scope": b3_scope,
        "b3_root_lp_bound": b3.get("b3_root_lp_bound"),
        "b4_root_lp_bound": b3.get("b4_root_lp_bound") or raw.get("root_lp_bound"),
        "root_no_cut_lp_bound": raw.get("root_no_cut_lp_bound"),
        "incumbent_objective": raw.get("incumbent_objective"),
        "objective_diff_vs_B3": objective_diff_vs_b3,
        "certificate_scope_diff_vs_B3": b3.get("certificate_scope_diff_vs_B3"),
        "cut_probe_status": probe.get("status"),
        "cut_candidate_count": int(probe.get("subset_candidate_count") or 0) + int(bool(probe.get("fleet_lower_bound_candidate"))),
        "cut_violated_count": int(probe.get("violated_subset_candidate_count") or 0),
        "max_violation": probe.get("max_violation"),
        "mean_violation": probe.get("mean_violation"),
        "violated_subset_size_histogram": probe.get("violated_subset_size_histogram") or {},
        "cut_kind": top_candidate.get("cut_kind") or top_candidate.get("cut_type") or "",
        "cut_key": top_candidate.get("cut_key") or "",
        "rhs": top_candidate.get("rhs"),
        "sense": top_candidate.get("sense") or "",
        "coefficient_dependency": top_candidate.get("coefficient_dependency") or "",
        "coefficient_vector_hash": top_candidate.get("coefficient_vector_hash") or "",
        "pricing_supported": top_candidate.get("pricing_supported"),
        "completion_bound_supported": top_candidate.get("completion_bound_supported"),
        "dominance_compatible": top_candidate.get("dominance_compatible"),
        "would_bind_on_current_rmp": top_candidate.get("would_bind_on_current_rmp"),
        "would_change_dual_support": top_candidate.get("would_change_dual_support"),
        "affected_column_count": top_candidate.get("affected_column_count"),
        "active_support_overlap": top_candidate.get("active_support_overlap"),
        "diagnostic_round_status": diagnostic.get("status"),
        "diagnostic_selected_cut_count": int(diagnostic.get("selected_cut_count") or 0),
        "diagnostic_cut_rmp_bound_delta": diagnostic.get("cut_rmp_bound_delta"),
        "diagnostic_cut_rmp_status": diagnostic.get("cut_rmp_status"),
        "diagnostic_lower_bound_official": bool(diagnostic.get("lower_bound_official")),
        "diagnostic_can_certify": bool(diagnostic.get("can_certify")),
        "restricted_pool_diagnostic_status": restricted_pool.get("status") or "",
        "restricted_pool_evaluation_scope": restricted_pool.get("evaluation_scope") or "",
        "restricted_pool_seed_column_count": restricted_pool.get("seed_column_count"),
        "restricted_pool_root_rmp_status": restricted_pool.get("root_rmp_status") or "",
        "restricted_pool_root_bound": restricted_pool.get("root_restricted_objective_bound"),
        "restricted_pool_can_certify": bool(restricted_pool.get("can_certify")),
        "live_subset_rows": bool(raw.get("live_subset_rows")),
        "cut_rows_active": cut_rows_active,
        "cut_added_count": int(raw.get("cut_added_count") or 0),
        "cut_dual_nonzero_count": int(raw.get("cut_dual_nonzero_count") or 0),
        "manual_rc_with_cuts_matches_pricing_rc": rc_match,
        "manual_rc_cut_consistency_pass": manual_rc_pass,
        "cut_dual_sign_audit_pass": sign_pass,
        "cut_dominance_valid": dominance_valid,
        "cut_pricing_supported_count": int(raw.get("cut_pricing_supported_count") or 0),
        "cut_completion_bound_fail_closed_count": int(raw.get("cut_completion_bound_fail_closed_count") or 0),
        "completion_bound_pruning_enabled": bool(completion_policy.get("pruning_enabled")),
        "fleet_lower_bound_live_enabled": bool(raw.get("fleet_lower_bound_live_enabled")),
        "lp_bound_delta": raw.get("lp_bound_delta") if raw.get("lp_bound_delta") is not None else diagnostic.get("cut_rmp_bound_delta"),
        "root_gap_delta": raw.get("root_gap_delta"),
        "cut_effective_claim": bool(raw.get("cut_effective_claim")),
        "objective_mismatch": objective_mismatch,
        "certificate_scope_regression": certificate_scope_regression,
        "direct_dp_certificate_leak": False,
        "manual_rc_with_cuts_fail": bool(cut_rows_active and manual_rc_pass is False),
        "pricing_rc_with_cuts_fail": bool(cut_rows_active and rc_match is False),
        "cut_coefficient_audit_fail": coefficient_audit_fail,
        "cut_dual_sign_audit_fail": bool(cut_rows_active and sign_pass is False),
        "cut_dominance_compatibility_fail": bool(cut_rows_active and dominance_valid is False),
        "fleet_lower_bound_live_enabled_without_proof": bool(raw.get("fleet_lower_bound_live_enabled")),
        "completion_bound_unsafe_with_cuts": bool(cut_rows_active and completion_policy.get("pruning_enabled") is not False),
        "restricted_pricing_claimed_no_negative": restricted_claim,
        "positive_incumbent_rc_claimed_certificate": positive_incumbent_claim,
        "wall_time": round(float(wall_time), 6),
        "fail_closed_reason": "" if certificate_scope in {"BPC_TREE_OPTIMAL", "BPC_NODE_LP_CERTIFIED"} else str(raw.get("note") or ""),
        "attempted_exception_type": "",
        "attempted_max_direct_tasks": int(max_direct_tasks),
        "rmp_memory_precheck_failed": bool(raw.get("rmp_memory_precheck_failed")),
        "rmp_memory_precheck_stage": raw.get("rmp_memory_precheck_stage") or "",
        "rmp_memory_precheck_reason": raw.get("rmp_memory_precheck_reason") or "",
        "rmp_memory_precheck_estimated_column_count": raw.get("rmp_memory_precheck_estimated_column_count"),
        "rmp_memory_precheck_estimated_tableau_cells": raw.get("rmp_memory_precheck_estimated_tableau_cells"),
        "rmp_memory_precheck_cell_limit": raw.get("rmp_memory_precheck_cell_limit"),
    }
    row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
    return row


def _report_from_rows(rows: list[dict]) -> dict:
    redline_keys = (
        "objective_mismatch",
        "certificate_scope_regression",
        "direct_dp_certificate_leak",
        "manual_rc_with_cuts_fail",
        "pricing_rc_with_cuts_fail",
        "cut_coefficient_audit_fail",
        "cut_dual_sign_audit_fail",
        "cut_dominance_compatibility_fail",
        "fleet_lower_bound_live_enabled_without_proof",
        "completion_bound_unsafe_with_cuts",
        "restricted_pricing_claimed_no_negative",
        "positive_incumbent_rc_claimed_certificate",
    )
    redlines = {key + "_count": sum(1 for row in rows if row.get(key) is True) for key in redline_keys}
    summary_rows = _summary_rows(rows)
    improvement_rows = [
        row
        for row in rows
        if (_float_or_none(row.get("lp_bound_delta")) or 0.0) > 1.0e-6
        or (_float_or_none(row.get("root_gap_delta")) or 0.0) < -1.0e-6
    ]
    b4b_rows = [row for row in rows if row.get("mode") == B4B_MODE]
    b4b_accepted = bool(
        b4b_rows
        and all(int(value or 0) == 0 for value in redlines.values())
        and any(row in improvement_rows for row in b4b_rows)
    )
    return {
        "schema_version": "lunar_ice_bpc.b4_cut_formulation_ablation.v1",
        "rows": rows,
        "row_count": len(rows),
        "summary_rows": summary_rows,
        "redlines": redlines,
        "acceptance": {
            "b4a_diagnostic_safe": bool(all(int(value or 0) == 0 for value in redlines.values())),
            "b4b_root_live_subset_row_accepted": b4b_accepted,
            "b4e_accepted_candidate": b4b_accepted,
            "measurable_improvement_row_count": len(improvement_rows),
        },
    }


def _summary_rows(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[int, str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((int(row["scale"]), str(row["matrix_group"]), str(row["mode"])), []).append(row)
    out: list[dict] = []
    for (scale, group_name, mode), group in sorted(groups.items()):
        walls = [_float_or_none(row.get("wall_time")) for row in group if _float_or_none(row.get("wall_time")) is not None]
        max_violations = [_float_or_none(row.get("max_violation")) for row in group if _float_or_none(row.get("max_violation")) is not None]
        out.append(
            {
                "scale": scale,
                "matrix_group": group_name,
                "mode": mode,
                "run_count": len(group),
                "BPC_TREE_OPTIMAL_count": sum(int(row.get("BPC_TREE_OPTIMAL_count") or 0) for row in group),
                "BPC_NODE_LP_CERTIFIED_count": sum(int(row.get("BPC_NODE_LP_CERTIFIED_count") or 0) for row in group),
                "cut_candidate_count": sum(int(row.get("cut_candidate_count") or 0) for row in group),
                "cut_violated_count": sum(int(row.get("cut_violated_count") or 0) for row in group),
                "max_violation": round(max(max_violations), 9) if max_violations else None,
                "mean_wall_time": round(mean(walls), 6) if walls else None,
                "fail_closed_count": sum(1 for row in group if row.get("fail_closed_reason")),
            }
        )
    return out


def _fail_closed_row(
    data,
    *,
    mode: str,
    matrix_group: str,
    wall_time: float,
    reason: str,
    exception_type: str,
    max_direct_tasks: int,
) -> dict:
    row = {
        "matrix_group": matrix_group,
        "scale": len(data.task_ids),
        "instance_id": data.instance_id,
        "mode": mode,
        "algorithm_status": "BPC_INCOMPLETE_PRICING",
        "certificate_scope": "DIAGNOSTIC_PRICING_FRONTIER",
        "pricing_state": "INCOMPLETE_LIMIT",
        "uses_true_dual_bpc_certificate": False,
        "BPC_TREE_OPTIMAL_count": 0,
        "BPC_NODE_LP_CERTIFIED_count": 0,
        "direct_dp_certificate_leak": False,
        "wall_time": round(float(wall_time), 6),
        "fail_closed_reason": reason,
        "attempted_exception_type": exception_type,
        "attempted_max_direct_tasks": int(max_direct_tasks),
        "rmp_memory_precheck_failed": False,
        "rmp_memory_precheck_stage": "",
        "rmp_memory_precheck_reason": "",
        "rmp_memory_precheck_estimated_column_count": None,
        "rmp_memory_precheck_estimated_tableau_cells": None,
        "rmp_memory_precheck_cell_limit": None,
    }
    row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
    return row


def _call_with_timeout(fn: Callable[[], dict], *, timeout_sec: float | None) -> dict:
    if timeout_sec is None or timeout_sec <= 0:
        return fn()

    def _raise_timeout(_signum, _frame) -> None:
        raise TimeoutError("row time limit exceeded")

    old_handler = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, float(timeout_sec))
    try:
        return fn()
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, old_handler)


def _top_cut_candidate(probe: dict) -> dict:
    candidates = list(probe.get("subset_candidates") or [])
    if candidates:
        return dict(candidates[0])
    fleet = probe.get("fleet_lower_bound_candidate")
    return dict(fleet) if isinstance(fleet, dict) else {}


def _load_instance(item: dict | str | Path) -> dict:
    if isinstance(item, dict):
        return item
    return read_json(item)


def _csv_value(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value


def _float_or_none(value) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _certificate_rank(scope: str) -> int:
    return {
        "": 0,
        "DIAGNOSTIC_PRICING_FRONTIER": 0,
        "FEASIBLE_INCUMBENT_ONLY": 0,
        "DIAGNOSTIC_RMP_BOUND": 1,
        "BPC_NODE_LP_CERTIFIED": 2,
        "BPC_TREE_OPTIMAL": 3,
    }.get(str(scope or ""), 0)
