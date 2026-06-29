#!/usr/bin/env python3
"""Summarize seed61635 formulation/cut readiness from existing logs.

This helper is read-only. It joins three diagnostic lines that have already
been run for seed61635:

* weighted rank-1 task-subset rows,
* route/resource cut audit rows,
* route-order partition child RMP/pricing probes.

The output is a gate matrix for deciding whether the next step is a live cut,
state-scoped branch/formulation work, or more evidence. It does not run BPC,
pricing, RMP, or create official bounds/certificates.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_WEIGHTED_RUN = Path("BPC_future/results/20260629_v760_weighted_rank1_live_seed61635_45")
DEFAULT_ROUTE_RESOURCE_RUN = Path("BPC_future/results/20260629_v765_route_resource_cut_audit_seed61635_45")
DEFAULT_ROUTE_ORDER_RUN = Path("BPC_future/results/20260629_v772_route_order_child_pricing_seed61635_45")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/20260629_v799_seed61635_formulation_cut_readiness")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260629_bpc_future_v799_seed61635_formulation_cut_readiness_zh.md"
)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload


def _iter_events(run_dir: Path) -> Iterable[dict[str, Any]]:
    if not run_dir.exists():
        return
    for path in sorted(run_dir.rglob("*.jsonl")):
        yield from _iter_jsonl(path)


def _read_result_row(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "results.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return dict(rows[0]) if rows else {}


def _float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed:
        return default
    return float(parsed)


def _int(value: Any, default: int = 0) -> int:
    parsed = _float(value)
    if parsed is None:
        return int(default)
    return int(parsed)


def _min_optional(values: Iterable[float | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    return min(present) if present else None


def _round_optional(value: float | None) -> float | None:
    return None if value is None else round(float(value), 9)


def _result_summary(run_dir: Path) -> dict[str, Any]:
    row = _read_result_row(run_dir)
    return {
        "run_dir": str(run_dir),
        "result_available": bool(row),
        "status": row.get("status"),
        "primal_bound": _float(row.get("primal_bound")),
        "dual_bound": _float(row.get("dual_bound")),
        "gap": _float(row.get("gap")),
        "columns": _int(row.get("columns")),
        "node_count": _int(row.get("node_count")),
        "pricing_calls": _int(row.get("pricing_calls")),
        "exact_pricing_calls": _int(row.get("exact_pricing_calls")),
        "cuts_added": _int(row.get("cuts_added")),
        "subset_row_cuts_added": _int(row.get("subset_row_cuts_added")),
    }


def _weighted_rank1_row(run_dir: Path) -> dict[str, Any]:
    events = list(_iter_events(run_dir))
    separations = [row for row in events if row.get("event") == "journey_weighted_rank1_cut_separation"]
    added = [row for row in events if row.get("event") == "journey_weighted_rank1_cut_added"]
    audits = [row for row in events if row.get("event") == "journey_weighted_rank1_cut_audit"]
    dual_events = [row for row in events if row.get("event") == "journey_cut_dual_diagnostics"]
    weighted_dual_events = 0
    max_weighted_abs_dual = 0.0
    for event in dual_events:
        weighted_seen = False
        for cut in event.get("top_cuts") or []:
            if str(cut.get("kind") or "") != "weighted_subset_row":
                continue
            weighted_seen = True
            max_weighted_abs_dual = max(max_weighted_abs_dual, abs(float(cut.get("dual") or 0.0)))
        if weighted_seen:
            weighted_dual_events += 1
    result = _result_summary(run_dir)
    moved_dual = (_float(result.get("dual_bound"), 0.0) or 0.0) > 526.651393 + 1.0e-6
    return {
        "schema_version": "seed61635_formulation_cut_readiness_row_v1",
        "family": "weighted_rank1_task_subset",
        "run_dir": str(run_dir),
        "diagnostic_only": True,
        "production_ready": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "observed_signal": bool(separations or audits or added),
        "event_count": len(events),
        "audit_event_count": len(audits),
        "separation_event_count": len(separations),
        "added_event_count": len(added),
        "max_best_violation": max([_float(row.get("best_violation"), 0.0) or 0.0 for row in separations] or [0.0]),
        "weighted_dual_event_count": int(weighted_dual_events),
        "max_weighted_abs_dual": round(float(max_weighted_abs_dual), 9),
        "result": result,
        "dual_moved_from_seed61635_plateau": bool(moved_dual),
        "live_ready": False,
        "primary_blocker": "task_subset_family_did_not_move_seed61635_dual",
        "next_gate": "stop_expanding_task_subset_rows_unless_longer_probe_moves_dual",
    }


def _route_resource_row(run_dir: Path) -> dict[str, Any]:
    audits = [row for row in _iter_events(run_dir) if row.get("event") == "journey_route_resource_cut_audit"]
    max_order = max([_int(row.get("order_direction_candidate_count")) for row in audits] or [0])
    max_adjacent = max([_int(row.get("adjacent_direction_candidate_count")) for row in audits] or [0])
    max_multi_route = max([_int(row.get("same_task_set_multi_route_candidate_count")) for row in audits] or [0])
    max_global_valid = max([_int(row.get("route_resource_global_valid_candidate_count")) for row in audits] or [0])
    max_pricing_supported = max(
        [_int(row.get("route_resource_pricing_supported_candidate_count")) for row in audits] or [0]
    )
    top_rows: list[dict[str, Any]] = []
    for event in audits:
        for key in ("top_order_direction_rows", "top_adjacent_direction_rows", "top_same_task_set_multi_route_rows"):
            for item in event.get(key) or []:
                if isinstance(item, dict):
                    top_rows.append(item)
    top_rows = sorted(
        top_rows,
        key=lambda item: (
            -float(item.get("total_mass", item.get("mass", 0.0)) or 0.0),
            str(item.get("row_type") or ""),
            str(item.get("tasks") or ""),
        ),
    )[:8]
    return {
        "schema_version": "seed61635_formulation_cut_readiness_row_v1",
        "family": "route_resource_cut_audit",
        "run_dir": str(run_dir),
        "diagnostic_only": True,
        "production_ready": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "observed_signal": bool(max_order or max_adjacent or max_multi_route),
        "event_count": len(audits),
        "max_order_direction_candidate_count": int(max_order),
        "max_adjacent_direction_candidate_count": int(max_adjacent),
        "max_same_task_set_multi_route_candidate_count": int(max_multi_route),
        "max_global_valid_candidate_count": int(max_global_valid),
        "max_pricing_supported_candidate_count": int(max_pricing_supported),
        "completion_bound_fail_closed": all(bool(row.get("completion_bound_fail_closed", False)) for row in audits) if audits else False,
        "top_candidate_rows": top_rows,
        "result": _result_summary(run_dir),
        "live_ready": False,
        "primary_blocker": "no_global_valid_or_pricing_supported_route_resource_row",
        "next_gate": "design_state_scoped_order_resource_branch_or_pricing_compatible_row",
    }


def _route_order_partition_row(run_dir: Path) -> dict[str, Any]:
    audits = [row for row in _iter_events(run_dir) if row.get("event") == "journey_route_order_partition_audit"]
    partition_rows: list[dict[str, Any]] = []
    pricing_rows: list[dict[str, Any]] = []
    rmp_rows: list[dict[str, Any]] = []
    for event in audits:
        for row in event.get("top_partition_rows") or []:
            if not isinstance(row, dict):
                continue
            partition_rows.append(row)
            for child_row in row.get("child_pricing_probe_rows") or []:
                if isinstance(child_row, dict):
                    pricing_rows.append(child_row)
            for child_row in row.get("child_rmp_probe_rows") or []:
                if isinstance(child_row, dict):
                    rmp_rows.append(child_row)
    found_negative_rows = [
        row for row in pricing_rows if _int(row.get("negative_journey_count")) > 0 or (_float(row.get("best_reduced_cost")) or 0.0) < -1.0e-9
    ]
    best_rc = _min_optional(_float(row.get("best_reduced_cost")) for row in pricing_rows)
    max_rmp_gain = max([_float(row.get("objective_gain"), 0.0) or 0.0 for row in rmp_rows] or [0.0])
    rows_with_complete_partition = sum(1 for row in partition_rows if bool(row.get("exact_safe_partition_contract_holds")))
    return {
        "schema_version": "seed61635_formulation_cut_readiness_row_v1",
        "family": "route_order_partition_formulation",
        "run_dir": str(run_dir),
        "diagnostic_only": True,
        "production_ready": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "observed_signal": bool(partition_rows),
        "event_count": len(audits),
        "partition_row_count": len(partition_rows),
        "partition_contract_holding_row_count": int(rows_with_complete_partition),
        "child_rmp_probe_row_count": len(rmp_rows),
        "max_child_rmp_objective_gain": round(float(max_rmp_gain), 9),
        "child_pricing_probe_row_count": len(pricing_rows),
        "child_pricing_found_negative_row_count": len(found_negative_rows),
        "min_child_pricing_best_reduced_cost": _round_optional(best_rc),
        "exact_pricing_supported": all(bool(row.get("exact_pricing_supported", False)) for row in audits) if audits else False,
        "completion_bound_fail_closed": all(bool(row.get("completion_bound_fail_closed", False)) for row in audits) if audits else False,
        "result": _result_summary(run_dir),
        "live_ready": False,
        "primary_blocker": "child_pricing_pressure_and_no_direct_certificate_support",
        "next_gate": "convert_to_state_scoped_formulation_or_pricing_compatible_route_resource_row",
    }


def summarize_seed61635_formulation_cut_readiness(
    *,
    weighted_run: Path,
    route_resource_run: Path,
    route_order_run: Path,
    output_dir: Path,
    report: Path,
) -> dict[str, Any]:
    rows = [
        _weighted_rank1_row(weighted_run),
        _route_resource_row(route_resource_run),
        _route_order_partition_row(route_order_run),
    ]
    live_ready_rows = [row for row in rows if bool(row.get("live_ready"))]
    observed_rows = [row for row in rows if bool(row.get("observed_signal"))]
    result_duals = [
        _float((row.get("result") or {}).get("dual_bound"))
        for row in rows
        if _float((row.get("result") or {}).get("dual_bound")) is not None
    ]
    plateau_dual = 526.651393
    dual_plateau_holds = all(abs(float(value) - plateau_dual) <= 1.0e-6 for value in result_duals)
    summary = {
        "schema_version": "seed61635_formulation_cut_readiness_summary_v1",
        "date": date.today().isoformat(),
        "output_dir": str(output_dir),
        "report_path": str(report),
        "row_count": len(rows),
        "observed_signal_family_count": len(observed_rows),
        "live_ready_family_count": len(live_ready_rows),
        "dual_plateau_reference": plateau_dual,
        "dual_plateau_holds_for_inputs": bool(dual_plateau_holds),
        "diagnostic_only": True,
        "production_ready": False,
        "official_bound_effect": False,
        "certificate_effect": False,
        "decision": "do_not_enter_live_cut; pursue state-scoped formulation/pricing-compatible row design",
        "hard_gates_before_live_cut": [
            "global_valid_or_state_scoped_partition_proven",
            "rmp_coefficient_and_manual_reduced_cost_match",
            "pricing_reduced_cost_matches_rmp_coefficient",
            "completion_bound_and_certificate_paths_fail_closed_or_supported",
            "seed61635_probe_moves_dual_or_reduces_child_pricing_pressure",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / "readiness_rows.jsonl"
    rows_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    summary["rows_path"] = str(rows_path)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary, rows)
    return summary


def _write_report(report: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# V799 Seed61635 Formulation/Cut Readiness Audit",
        "",
        "该报告只读已有 seed61635 诊断日志，汇总 weighted rank-1、route/resource cut audit、route-order partition child pricing 三条线的 live-readiness gate；它不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## Summary",
        "",
        f"- observed_signal_family_count: `{summary['observed_signal_family_count']}`",
        f"- live_ready_family_count: `{summary['live_ready_family_count']}`",
        f"- dual_plateau_holds_for_inputs: `{summary['dual_plateau_holds_for_inputs']}`",
        f"- decision: `{summary['decision']}`",
        "",
        "## Family Rows",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['family']}",
                "",
                f"- observed_signal: `{row['observed_signal']}`",
                f"- live_ready: `{row['live_ready']}`",
                f"- primary_blocker: `{row['primary_blocker']}`",
                f"- next_gate: `{row['next_gate']}`",
            ]
        )
        result = row.get("result") or {}
        if result:
            lines.append(f"- status/dual/gap: `{result.get('status')}` / `{result.get('dual_bound')}` / `{result.get('gap')}`")
        if row["family"] == "route_order_partition_formulation":
            lines.extend(
                [
                    f"- max_child_rmp_objective_gain: `{row.get('max_child_rmp_objective_gain')}`",
                    f"- child_pricing_found_negative_row_count: `{row.get('child_pricing_found_negative_row_count')}`",
                    f"- min_child_pricing_best_reduced_cost: `{row.get('min_child_pricing_best_reduced_cost')}`",
                ]
            )
        if row["family"] == "route_resource_cut_audit":
            lines.extend(
                [
                    f"- max_global_valid_candidate_count: `{row.get('max_global_valid_candidate_count')}`",
                    f"- max_pricing_supported_candidate_count: `{row.get('max_pricing_supported_candidate_count')}`",
                    f"- max_order_direction_candidate_count: `{row.get('max_order_direction_candidate_count')}`",
                ]
            )
        lines.append("")
    lines.extend(
        [
            "## Hard Gates Before Live Cut",
            "",
            *[f"- `{gate}`" for gate in summary["hard_gates_before_live_cut"]],
            "",
        ]
    )
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weighted-run", type=Path, default=DEFAULT_WEIGHTED_RUN)
    parser.add_argument("--route-resource-run", type=Path, default=DEFAULT_ROUTE_RESOURCE_RUN)
    parser.add_argument("--route-order-run", type=Path, default=DEFAULT_ROUTE_ORDER_RUN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    summary = summarize_seed61635_formulation_cut_readiness(
        weighted_run=args.weighted_run,
        route_resource_run=args.route_resource_run,
        route_order_run=args.route_order_run,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
