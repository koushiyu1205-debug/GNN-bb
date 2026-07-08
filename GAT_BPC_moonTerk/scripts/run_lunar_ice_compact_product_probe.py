#!/usr/bin/env python3
"""Run resumable compact fixed-graph product-oracle probes."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import shutil
import sys
from time import perf_counter
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.exact.core.objective import flatten_objective_payload, objective_metadata  # noqa: E402
from lunar_ice_bpc.exact.solver.gurobi_compact import (  # noqa: E402
    estimate_gurobi_compact_size,
    solve_highs_compact_fixed_graph,
)


DEFAULT_OUTPUT_DIR = "runs/objective_normalized_cost_risk_completion_full"
DEFAULT_MANIFEST = "data/manifests/lunar_ice_sp50_real_benchmark_manifest.json"

CSV_COLUMNS = (
    "matrix_group",
    "scale",
    "instance_id",
    "solver_backend",
    "certificate_family",
    "algorithm_status",
    "certificate_scope",
    "product_oracle_exact_optimal",
    "has_feasible_incumbent",
    "objective",
    "model_objective",
    "bound",
    "gap",
    "solver_info_valid",
    "solver_info_objective_function_value",
    "solver_info_mip_dual_bound",
    "solver_info_mip_gap",
    "solver_info_mip_node_count",
    "solver_info_simplex_iteration_count",
    "solver_info_ipm_iteration_count",
    "solver_info_pdlp_iteration_count",
    "solver_info_primal_solution_status",
    "solver_info_dual_solution_status",
    "solver_info_max_primal_infeasibility",
    "solver_info_max_dual_infeasibility",
    "solver_info_max_integrality_violation",
    "solver_info_primal_dual_integral",
    "journey_count",
    "wall_time_sec",
    "row_elapsed_sec",
    "time_limit_sec",
    "threads",
    "mip_gap",
    "use_reference_warm_start",
    "mip_start_enabled",
    "mip_start_status",
    "mip_start_source",
    "mip_start_objective",
    "mip_start_sortie_count",
    "mip_start_entry_count",
    "mip_start_note",
    "variable_count",
    "constraint_count",
    "binary_arc_var_count",
    "task_assignment_var_count",
    "vehicle_count",
    "sortie_slots_per_vehicle",
    "sortie_slot_bound_source",
    "sortie_slot_min_duration_lower_bound",
    "sortie_slot_min_return_duration_lower_bound",
    "path_option_policy",
    "note",
    "fail_closed_reason",
    "attempted_exception_type",
    "objective_schema_version",
    "objective_mode",
    "objective_reference_cost",
    "objective_reference_risk",
    "objective_reference_completion",
    "objective_reference_makespan_metric",
    "objective_makespan_enters_pricing_objective",
    "solution_raw_operating_cost",
    "solution_raw_risk",
    "solution_raw_weighted_completion_time",
    "solution_raw_makespan",
    "solution_raw_objective_unscaled_weighted_sum",
    "solution_normalized_operating_cost",
    "solution_normalized_risk",
    "solution_normalized_weighted_completion_time",
    "solution_normalized_makespan_metric",
    "solution_normalized_objective",
    "solution_official_objective",
    "solution_makespan_enters_pricing_objective",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scale", type=int, default=30)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--time-limit-sec", type=float, default=300.0)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--mip-gap", type=float, default=0.0)
    parser.add_argument("--no-reference-warm-start", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--instance-id",
        action="append",
        default=[],
        help="Run only matching instance_id values. Can be passed more than once.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="When --instance-id is used, remove matching existing rows before rerunning them.",
    )
    parser.add_argument("--min-mem-available-gb", type=float, default=2.0)
    parser.add_argument("--min-disk-free-gb", type=float, default=20.0)
    args = parser.parse_args()

    output_dir = _resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scale = int(args.scale)
    prefix = output_dir / f"compact_product_scale{scale:03d}"
    rows_json = prefix.with_name(f"{prefix.name}_resume_rows.json")
    rows_csv = prefix.with_name(f"{prefix.name}_rows.csv")
    summary_json = prefix.with_name(f"{prefix.name}_summary.json")
    report_md = prefix.with_name(f"{prefix.name}_report_zh.md")

    requested_instance_ids = {str(value) for value in args.instance_id}
    rows = [] if args.force else _read_rows(rows_json)
    if requested_instance_ids and args.replace_existing and not args.force:
        rows = [row for row in rows if str(row.get("instance_id")) not in requested_instance_ids]
    completed = {str(row.get("instance_id")) for row in rows if row.get("instance_id")}
    instance_paths = _instance_paths_for_scale(_load_manifest(_resolve_path(args.manifest)), scale=scale, limit=int(args.limit))
    if requested_instance_ids:
        instance_paths = tuple(
            path
            for path in instance_paths
            if _instance_id_from_path(path) in requested_instance_ids
        )
    matrix_group = f"{scale}-scale compact product oracle probe"

    for instance_path in instance_paths:
        raw = json.loads(instance_path.read_text(encoding="utf-8"))
        instance_id = str(raw.get("instance_id") or instance_path.stem)
        if instance_id in completed:
            continue
        _assert_resource_guard(output_dir, args)
        start = perf_counter()
        try:
            data = load_lunar_ice_data(raw)
            result = solve_highs_compact_fixed_graph(
                data,
                time_limit_sec=float(args.time_limit_sec),
                threads=int(args.threads),
                mip_gap=float(args.mip_gap),
                reference_solution=None if args.no_reference_warm_start else raw.get("reference_solution"),
            )
            row = _row_from_result(
                data=data,
                result=result,
                matrix_group=matrix_group,
                args=args,
                elapsed=perf_counter() - start,
            )
        except Exception as exc:
            data = load_lunar_ice_data(raw)
            size = estimate_gurobi_compact_size(data)
            row = _exception_row(
                data=data,
                size=size,
                matrix_group=matrix_group,
                args=args,
                elapsed=perf_counter() - start,
                exc=exc,
            )
        rows.append(row)
        completed.add(instance_id)
        _write_artifacts(rows, rows_json=rows_json, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)

    _write_artifacts(rows, rows_json=rows_json, rows_csv=rows_csv, summary_json=summary_json, report_md=report_md)
    print(f"compact product probe report written to {report_md}")
    return 0


def _row_from_result(*, data, result: dict, matrix_group: str, args, elapsed: float) -> dict:
    mip_start = result.get("mip_start") if isinstance(result.get("mip_start"), dict) else {}
    objective_breakdown = result.get("objective_breakdown")
    solver_info = result.get("solver_info") if isinstance(result.get("solver_info"), dict) else {}
    row = {
        "matrix_group": matrix_group,
        "scale": len(data.task_ids),
        "instance_id": data.instance_id,
        "solver_backend": "HiGHS compact MILP",
        "certificate_family": "PRODUCT_ORACLE_NOT_BPC",
        "algorithm_status": result.get("algorithm_status"),
        "certificate_scope": result.get("certificate_scope"),
        "product_oracle_exact_optimal": result.get("certificate_scope") == "DIRECT_DP_FIXED_GRAPH_OPTIMAL",
        "has_feasible_incumbent": bool(result.get("has_feasible_incumbent")),
        "objective": result.get("objective"),
        "model_objective": result.get("model_objective"),
        "bound": result.get("bound"),
        "gap": result.get("gap"),
        "solver_info_valid": solver_info.get("valid"),
        "solver_info_objective_function_value": solver_info.get("objective_function_value"),
        "solver_info_mip_dual_bound": solver_info.get("mip_dual_bound"),
        "solver_info_mip_gap": solver_info.get("mip_gap"),
        "solver_info_mip_node_count": solver_info.get("mip_node_count"),
        "solver_info_simplex_iteration_count": solver_info.get("simplex_iteration_count"),
        "solver_info_ipm_iteration_count": solver_info.get("ipm_iteration_count"),
        "solver_info_pdlp_iteration_count": solver_info.get("pdlp_iteration_count"),
        "solver_info_primal_solution_status": solver_info.get("primal_solution_status"),
        "solver_info_dual_solution_status": solver_info.get("dual_solution_status"),
        "solver_info_max_primal_infeasibility": solver_info.get("max_primal_infeasibility"),
        "solver_info_max_dual_infeasibility": solver_info.get("max_dual_infeasibility"),
        "solver_info_max_integrality_violation": solver_info.get("max_integrality_violation"),
        "solver_info_primal_dual_integral": solver_info.get("primal_dual_integral"),
        "journey_count": int(result.get("journey_count") or 0),
        "wall_time_sec": result.get("wall_time_sec"),
        "row_elapsed_sec": round(float(elapsed), 6),
        "time_limit_sec": float(args.time_limit_sec),
        "threads": int(args.threads),
        "mip_gap": float(args.mip_gap),
        "use_reference_warm_start": not bool(args.no_reference_warm_start),
        "mip_start_enabled": bool(mip_start.get("enabled")),
        "mip_start_status": mip_start.get("status") or "",
        "mip_start_source": mip_start.get("source") or "",
        "mip_start_objective": mip_start.get("objective"),
        "mip_start_sortie_count": int(mip_start.get("sortie_count") or 0),
        "mip_start_entry_count": int(mip_start.get("entry_count") or 0),
        "mip_start_note": mip_start.get("note") or "",
        "variable_count": int(result.get("variable_count") or result.get("estimated_variable_count") or 0),
        "constraint_count": int(result.get("constraint_count") or result.get("estimated_constraint_count") or 0),
        "binary_arc_var_count": int(result.get("binary_arc_var_count") or 0),
        "task_assignment_var_count": int(result.get("task_assignment_var_count") or 0),
        "vehicle_count": int(result.get("vehicle_count") or data.fleet_size),
        "sortie_slots_per_vehicle": int(result.get("sortie_slots_per_vehicle") or len(data.task_ids)),
        "sortie_slot_bound_source": result.get("sortie_slot_bound_source") or "",
        "sortie_slot_min_duration_lower_bound": result.get("sortie_slot_min_duration_lower_bound"),
        "sortie_slot_min_return_duration_lower_bound": result.get("sortie_slot_min_return_duration_lower_bound"),
        "path_option_policy": result.get("path_option_policy") or str(data.path_option_policy_id),
        "note": result.get("note") or "",
        "fail_closed_reason": "" if result.get("certificate_scope") == "DIRECT_DP_FIXED_GRAPH_OPTIMAL" else (result.get("note") or ""),
        "attempted_exception_type": "",
    }
    row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
    row.update(flatten_objective_payload(objective_breakdown, prefix="solution"))
    return row


def _exception_row(*, data, size: dict, matrix_group: str, args, elapsed: float, exc: Exception) -> dict:
    row = {
        "matrix_group": matrix_group,
        "scale": len(data.task_ids),
        "instance_id": data.instance_id,
        "solver_backend": "HiGHS compact MILP",
        "certificate_family": "PRODUCT_ORACLE_NOT_BPC",
        "algorithm_status": "HIGHS_COMPACT_EXCEPTION",
        "certificate_scope": "FEASIBLE_INCUMBENT_ONLY",
        "product_oracle_exact_optimal": False,
        "has_feasible_incumbent": False,
        "objective": None,
        "model_objective": None,
        "bound": None,
        "gap": None,
        "solver_info_valid": None,
        "solver_info_objective_function_value": None,
        "solver_info_mip_dual_bound": None,
        "solver_info_mip_gap": None,
        "solver_info_mip_node_count": None,
        "solver_info_simplex_iteration_count": None,
        "solver_info_ipm_iteration_count": None,
        "solver_info_pdlp_iteration_count": None,
        "solver_info_primal_solution_status": None,
        "solver_info_dual_solution_status": None,
        "solver_info_max_primal_infeasibility": None,
        "solver_info_max_dual_infeasibility": None,
        "solver_info_max_integrality_violation": None,
        "solver_info_primal_dual_integral": None,
        "journey_count": 0,
        "wall_time_sec": None,
        "row_elapsed_sec": round(float(elapsed), 6),
        "time_limit_sec": float(args.time_limit_sec),
        "threads": int(args.threads),
        "mip_gap": float(args.mip_gap),
        "use_reference_warm_start": not bool(args.no_reference_warm_start),
        "mip_start_enabled": False,
        "mip_start_status": "",
        "mip_start_source": "",
        "mip_start_objective": None,
        "mip_start_sortie_count": 0,
        "mip_start_entry_count": 0,
        "mip_start_note": "",
        "variable_count": int(size.get("estimated_variable_count") or 0),
        "constraint_count": int(size.get("estimated_constraint_count") or 0),
        "binary_arc_var_count": int(size.get("binary_arc_var_count") or 0),
        "task_assignment_var_count": int(size.get("task_assignment_var_count") or 0),
        "vehicle_count": int(size.get("vehicle_count") or data.fleet_size),
        "sortie_slots_per_vehicle": int(size.get("sortie_slots_per_vehicle") or len(data.task_ids)),
        "sortie_slot_bound_source": size.get("sortie_slot_bound_source") or "",
        "sortie_slot_min_duration_lower_bound": size.get("sortie_slot_min_duration_lower_bound"),
        "sortie_slot_min_return_duration_lower_bound": size.get("sortie_slot_min_return_duration_lower_bound"),
        "path_option_policy": str(size.get("path_option_policy") or data.path_option_policy_id),
        "note": f"{type(exc).__name__}: {exc}",
        "fail_closed_reason": f"{type(exc).__name__}: {exc}",
        "attempted_exception_type": type(exc).__name__,
    }
    row.update(flatten_objective_payload(objective_metadata(data), prefix="objective"))
    return row


def _write_artifacts(rows: list[dict], *, rows_json: Path, rows_csv: Path, summary_json: Path, report_md: Path) -> None:
    rows_json.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    with rows_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    summary = _summary_from_rows(rows)
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    report_md.write_text(_report_from_summary(summary, rows), encoding="utf-8")


def _summary_from_rows(rows: list[dict]) -> dict:
    solved = [row for row in rows if row.get("certificate_scope") == "DIRECT_DP_FIXED_GRAPH_OPTIMAL"]
    incumbents = [row for row in rows if bool(row.get("has_feasible_incumbent"))]
    gaps = [float(row["gap"]) for row in rows if row.get("gap") not in {None, ""}]
    times = [float(row["row_elapsed_sec"]) for row in rows if row.get("row_elapsed_sec") not in {None, ""}]
    objectives = [float(row["objective"]) for row in incumbents if row.get("objective") not in {None, ""}]
    bounds = [float(row["bound"]) for row in rows if row.get("bound") not in {None, ""}]
    node_counts = [float(row["solver_info_mip_node_count"]) for row in rows if row.get("solver_info_mip_node_count") not in {None, ""}]
    simplex_iterations = [
        float(row["solver_info_simplex_iteration_count"])
        for row in rows
        if row.get("solver_info_simplex_iteration_count") not in {None, ""}
    ]
    statuses: dict[str, int] = {}
    for row in rows:
        status = str(row.get("algorithm_status") or "")
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "schema_version": "lunar_ice_bpc.compact_product_probe_summary.v1",
        "row_count": len(rows),
        "instance_count": len({row.get("instance_id") for row in rows}),
        "product_optimal_count": len(solved),
        "feasible_incumbent_count": len(incumbents),
        "status_counts": statuses,
        "mean_row_elapsed_sec": _mean(times),
        "mean_objective": _mean(objectives),
        "mean_bound": _mean(bounds),
        "mean_gap": _mean(gaps),
        "max_gap": max(gaps) if gaps else None,
        "rows_with_bound_count": len(bounds),
        "mean_mip_node_count": _mean(node_counts),
        "max_mip_node_count": max(node_counts) if node_counts else None,
        "mean_simplex_iteration_count": _mean(simplex_iterations),
        "rows": rows,
    }


def _report_from_summary(summary: dict, rows: list[dict]) -> str:
    lines = [
        "# Compact Fixed-Graph Product Oracle Probe Report",
        "",
        "## 结论",
        "",
        "- 该报告是 fixed-graph product oracle 诊断，不是 BPC root/tree certificate。",
        "- `DIRECT_DP_FIXED_GRAPH_OPTIMAL` 才表示 product oracle 证明最优；有 incumbent 但 time limit 只表示可行上界。",
        "",
        "## 汇总",
        "",
        f"- rows: {summary['row_count']}",
        f"- product optimal: {summary['product_optimal_count']}/{summary['row_count']}",
        f"- feasible incumbent: {summary['feasible_incumbent_count']}/{summary['row_count']}",
        f"- mean row elapsed: {_fmt(summary['mean_row_elapsed_sec'])}s",
        f"- mean objective among incumbents: {_fmt(summary['mean_objective'])}",
        f"- mean bound: {_fmt(summary['mean_bound'])}",
        f"- mean gap: {_fmt(summary['mean_gap'])}",
        f"- max gap: {_fmt(summary['max_gap'])}",
        f"- rows with finite bound: {summary.get('rows_with_bound_count', 0)}/{summary['row_count']}",
        f"- mean/max MIP nodes: {_fmt(summary.get('mean_mip_node_count'))}/{_fmt(summary.get('max_mip_node_count'))}",
        f"- mean simplex iterations: {_fmt(summary.get('mean_simplex_iteration_count'))}",
        f"- status counts: {summary['status_counts']}",
        "",
        "## Rows",
        "",
        "| instance | status | incumbent | objective | bound | gap | elapsed_s | mip_start |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('instance_id')} | `{row.get('algorithm_status')}` | "
            f"{str(bool(row.get('has_feasible_incumbent'))).lower()} | {_fmt(row.get('objective'))} | "
            f"{_fmt(row.get('bound'))} | {_fmt(row.get('gap'))} | {_fmt(row.get('row_elapsed_sec'))} | "
            f"{row.get('mip_start_status') or ''}/{row.get('mip_start_source') or ''} |"
        )
    lines.append("")
    return "\n".join(lines)


def _instance_paths_for_scale(manifest: dict, *, scale: int, limit: int) -> tuple[Path, ...]:
    rows = [
        row for row in manifest.get("instances", [])
        if int(row.get("scale") or row.get("task_count") or -1) == int(scale) and row.get("path")
    ]
    rows.sort(key=lambda row: (int(row.get("attempt_index") or 0), str(row.get("instance_id") or "")))
    return tuple(_resolve_path(row["path"]) for row in rows[: max(0, int(limit))])


def _instance_id_from_path(path: Path) -> str:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return path.stem
    return str(raw.get("instance_id") or path.stem)


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


def _read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [dict(row) for row in rows if isinstance(row, dict)]


def _load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else ROOT / candidate


def _mean(values: Iterable[float]) -> float | None:
    values = tuple(float(value) for value in values)
    return None if not values else round(sum(values) / len(values), 6)


def _fmt(value) -> str:
    if value in {None, ""}:
        return ""
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
