"""Benchmark acceptance audit for lunar-ice runs."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from lunar_ice_bpc.io.instance_io import write_json


@dataclass(frozen=True)
class ScaleAcceptanceGoal:
    exact_min_count: int
    mean_optimal_time_lt: float | None = None
    require_all_exact: bool = False
    require_valid_gap: bool = False
    require_scalable_report: bool = False


ACCEPTANCE_GOALS: dict[int, ScaleAcceptanceGoal] = {
    5: ScaleAcceptanceGoal(exact_min_count=20, mean_optimal_time_lt=5.0, require_all_exact=True),
    10: ScaleAcceptanceGoal(exact_min_count=20, mean_optimal_time_lt=10.0, require_all_exact=True),
    20: ScaleAcceptanceGoal(exact_min_count=20, mean_optimal_time_lt=100.0, require_all_exact=True),
    30: ScaleAcceptanceGoal(exact_min_count=15, mean_optimal_time_lt=250.0),
    50: ScaleAcceptanceGoal(exact_min_count=3, require_valid_gap=True),
    100: ScaleAcceptanceGoal(exact_min_count=0, require_valid_gap=True, require_scalable_report=True),
}

EXACT_OPTIMAL_STATUSES = {"EXACT_BASELINE_OPTIMAL", "BPC_CERTIFIED_OPTIMAL", "OPTIMAL"}


def audit_benchmark_csv(
    results_csv: str | Path,
    *,
    output_json: str | Path | None = None,
    scales: Iterable[int | str] | None = None,
    expected_per_scale: int = 20,
) -> dict:
    """Audit benchmark CSV rows against the refactor-plan acceptance matrix."""

    csv_path = Path(results_csv)
    rows = _read_rows(csv_path)
    requested_scales = _requested_scales(rows, scales)
    scale_payloads: dict[str, dict] = {}
    for scale in requested_scales:
        scale_rows = [row for row in rows if _row_scale(row) == int(scale)]
        scale_payloads[f"{int(scale):03d}"] = _audit_scale(int(scale), scale_rows, expected_per_scale=int(expected_per_scale))
    passed = all(payload["status"] == "PASS" for payload in scale_payloads.values())
    payload = {
        "schema_version": "lunar_ice_bpc.benchmark_audit.v1",
        "results_csv": str(csv_path),
        "expected_per_scale": int(expected_per_scale),
        "scale_labels": list(scale_payloads),
        "overall_status": "PASS" if passed else "FAIL",
        "scales": scale_payloads,
        "note": (
            "Audits current benchmark evidence against the planned scale acceptance targets. "
            "Fixed-graph baselines are tracked separately from future true-dual BPC certificates."
        ),
    }
    if output_json is not None:
        write_json(output_json, payload)
    return payload


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _requested_scales(rows: list[dict[str, str]], scales: Iterable[int | str] | None) -> tuple[int, ...]:
    if scales is not None:
        return tuple(sorted({int(str(scale).strip()) for scale in scales if str(scale).strip()}))
    return tuple(sorted({_row_scale(row) for row in rows if _row_scale(row) > 0}))


def _audit_scale(scale: int, rows: list[dict[str, str]], *, expected_per_scale: int) -> dict:
    goal = ACCEPTANCE_GOALS.get(scale, ScaleAcceptanceGoal(exact_min_count=int(expected_per_scale)))
    run_count = len(rows)
    exact_rows = [row for row in rows if str(row.get("exact_status") or "") in EXACT_OPTIMAL_STATUSES]
    exact_count = len(exact_rows)
    wall_times = [_optimal_time_or_none(row) for row in exact_rows]
    wall_times = [value for value in wall_times if value is not None]
    mean_optimal_time = round(sum(wall_times) / len(wall_times), 6) if wall_times else None
    valid_gap_rows = [row for row in rows if _has_float(row.get("objective")) and _has_float(row.get("lower_bound")) and _has_float(row.get("relaxation_gap"))]
    incumbent_rows = [row for row in rows if _has_float(row.get("objective"))]
    pricing_rows = [row for row in rows if _has_pricing_workload(row)]
    node_rows = [row for row in rows if _has_float(row.get("node_count"))]
    incomplete_rows = [row for row in rows if str(row.get("incomplete_reason") or "").strip()]
    timeout_rows = [row for row in rows if str(row.get("time_limit_exceeded") or "") == "True"]
    timeout_reason_rows = [row for row in timeout_rows if str(row.get("timeout_reason") or "").strip()]
    exact_scope_counts = _count_values(rows, "exact_claim_scope")
    bpc_certificate_status_counts = _count_values(rows, "bpc_certificate_status")
    direct_baseline_status_counts = _count_values(rows, "direct_baseline_status")
    pricing_certificate_status_counts = _count_values(rows, "pricing_certificate_status")
    pricing_certificate_selected_source_counts = _count_values(rows, "pricing_certificate_selected_source")
    fixed_graph_closure_status_counts = _count_values(rows, "fixed_graph_pricing_closure_status")
    completion_bound_consistency_status_counts = _count_values(rows, "completion_bound_consistency_status")
    true_dual_tail_status_counts = _count_values(rows, "true_dual_pricing_tail_status")
    true_dual_readiness_status_counts = _count_values(rows, "true_dual_readiness_status")
    true_dual_certificate_count = sum(1 for row in rows if str(row.get("uses_true_dual_bpc_certificate") or "") == "True")
    no_negative_certificate_count = sum(
        1 for row in rows if str(row.get("pricing_certificate_can_certify_no_negative") or "") == "True"
    )
    fixed_graph_closure_closed_count = sum(
        1
        for row in rows
        if str(row.get("fixed_graph_pricing_closure_status") or "") == "FIXED_GRAPH_PRICING_CLOSED"
        and str(row.get("fixed_graph_pricing_closure_no_negative_proved") or "") == "True"
    )
    fixed_graph_closure_diagnostic_only_count = sum(
        1
        for row in rows
        if str(row.get("fixed_graph_pricing_closure_status") or "").strip()
        and str(row.get("fixed_graph_pricing_closure_uses_true_dual_bpc_certificate") or "") == "False"
        and str(row.get("fixed_graph_pricing_closure_lower_bound_official") or "") == "False"
        and str(row.get("fixed_graph_pricing_closure_can_certify_no_negative") or "") == "False"
    )
    readiness_fixed_graph_closure_complete_count = sum(
        1
        for row in rows
        if str(row.get("true_dual_readiness_diagnostic_fixed_graph_closure_complete") or "") == "True"
    )
    readiness_waiting_true_dual_count = sum(
        1
        for row in rows
        if str(row.get("true_dual_readiness_status") or "") == "WAITING_TRUE_DUAL_PRICING_PROOF"
    )
    true_dual_tail_certified_count = sum(
        1 for row in rows if str(row.get("true_dual_pricing_tail_can_certify_no_negative") or "") == "True"
    )
    true_dual_tail_not_ported_count = sum(
        1 for row in rows if str(row.get("true_dual_pricing_tail_status") or "") == "TRUE_DUAL_PRICING_TAIL_NOT_PORTED"
    )
    true_dual_tail_dual_bound_count = sum(
        1 for row in rows if str(row.get("true_dual_pricing_tail_dual_vector_bound_to_rmp") or "") == "True"
    )
    completion_bound_consistency_pass_count = sum(
        1 for row in rows if str(row.get("completion_bound_consistency_consistent") or "") == "True"
    )

    required_exact = _required_exact_count(goal, expected_per_scale=int(expected_per_scale))
    checks = {
        "run_count_matches_expected": run_count == int(expected_per_scale),
        "time_limit_not_exceeded": not timeout_rows,
        "exact_count_target_met": exact_count >= required_exact,
        "mean_optimal_time_target_met": (
            True
            if goal.mean_optimal_time_lt is None
            else mean_optimal_time is not None and mean_optimal_time < float(goal.mean_optimal_time_lt)
        ),
        "valid_gap_reported": (not goal.require_valid_gap) or len(valid_gap_rows) == run_count,
        "scalable_report_complete": (
            not goal.require_scalable_report
            or (
                len(incumbent_rows) == run_count
                and len(valid_gap_rows) == run_count
                and len(pricing_rows) == run_count
                and len(node_rows) == run_count
                and len(incomplete_rows) == run_count
            )
        ),
        "timeout_reason_reported_when_needed": len(timeout_reason_rows) == len(timeout_rows),
    }
    if goal.require_all_exact:
        checks["all_instances_exact"] = exact_count == run_count == int(expected_per_scale)
    status = "PASS" if rows and all(checks.values()) else "FAIL"
    return {
        "scale": scale,
        "scale_label": f"{scale:03d}",
        "status": status,
        "run_count": run_count,
        "expected_run_count": int(expected_per_scale),
        "exact_optimal_count": exact_count,
        "required_exact_optimal_count": required_exact,
        "mean_optimal_wall_time_sec": mean_optimal_time,
        "mean_optimal_wall_time_metric": "exact_baseline_wall_time_sec_or_wall_time_sec",
        "mean_optimal_wall_time_target_sec": goal.mean_optimal_time_lt,
        "valid_gap_count": len(valid_gap_rows),
        "incumbent_count": len(incumbent_rows),
        "pricing_workload_reported_count": len(pricing_rows),
        "node_count_reported_count": len(node_rows),
        "incomplete_reason_reported_count": len(incomplete_rows),
        "exact_claim_scope_counts": exact_scope_counts,
        "bpc_certificate_status_counts": bpc_certificate_status_counts,
        "direct_baseline_status_counts": direct_baseline_status_counts,
        "pricing_certificate_status_counts": pricing_certificate_status_counts,
        "pricing_certificate_selected_source_counts": pricing_certificate_selected_source_counts,
        "fixed_graph_pricing_closure_status_counts": fixed_graph_closure_status_counts,
        "fixed_graph_pricing_closure_closed_count": fixed_graph_closure_closed_count,
        "fixed_graph_pricing_closure_diagnostic_only_count": fixed_graph_closure_diagnostic_only_count,
        "completion_bound_consistency_status_counts": completion_bound_consistency_status_counts,
        "completion_bound_consistency_pass_count": completion_bound_consistency_pass_count,
        "true_dual_pricing_tail_status_counts": true_dual_tail_status_counts,
        "true_dual_pricing_tail_certified_count": true_dual_tail_certified_count,
        "true_dual_pricing_tail_not_ported_count": true_dual_tail_not_ported_count,
        "true_dual_pricing_tail_dual_vector_bound_count": true_dual_tail_dual_bound_count,
        "true_dual_readiness_status_counts": true_dual_readiness_status_counts,
        "true_dual_readiness_fixed_graph_closure_complete_count": readiness_fixed_graph_closure_complete_count,
        "true_dual_readiness_waiting_true_dual_count": readiness_waiting_true_dual_count,
        "true_dual_bpc_certificate_count": true_dual_certificate_count,
        "no_negative_certificate_count": no_negative_certificate_count,
        "time_limit_exceeded_count": len(timeout_rows),
        "timeout_reason_reported_count": len(timeout_reason_rows),
        "checks": checks,
    }


def _required_exact_count(goal: ScaleAcceptanceGoal, *, expected_per_scale: int) -> int:
    if goal.require_all_exact:
        return int(expected_per_scale)
    return min(int(goal.exact_min_count), int(expected_per_scale))


def _row_scale(row: dict[str, str]) -> int:
    if _has_float(row.get("task_count")):
        return int(float(str(row.get("task_count"))))
    text = str(row.get("instance_id") or row.get("instance_path") or "")
    for scale in (5, 10, 20, 30, 50, 100):
        if f"{scale:03d}" in text:
            return scale
    return 0


def _has_pricing_workload(row: dict[str, str]) -> bool:
    workload_keys = (
        "direct_pricing_status",
        "direct_cg_status",
        "generated_sortie_count",
        "route_template_count",
        "restricted_rmp_status",
    )
    return any(str(row.get(key) or "").strip() for key in workload_keys)


def _optimal_time_or_none(row: dict[str, str]) -> float | None:
    exact_baseline_time = _float_or_none(row.get("exact_baseline_wall_time_sec"))
    if exact_baseline_time is not None:
        return exact_baseline_time
    return _float_or_none(row.get("wall_time_sec"))


def _count_values(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "missing")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _has_float(value: object) -> bool:
    return _float_or_none(value) is not None


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None
