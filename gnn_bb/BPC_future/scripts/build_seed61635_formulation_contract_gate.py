#!/usr/bin/env python3
"""Build the C-2 seed61635 formulation/cut contract gate.

This is the step after the V799 readiness audit. It does not run BPC, pricing,
or RMP. It reads the V799 rows and turns them into a candidate-level contract
matrix for the next implementation step.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any, Iterable


DEFAULT_READINESS_DIR = Path("BPC_future/results/20260629_v799_seed61635_formulation_cut_readiness")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/20260629_v800_seed61635_formulation_contract_gate")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260629_bpc_future_v800_seed61635_formulation_contract_gate_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


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


def _readiness_by_family(readiness_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("family") or ""): row
        for row in _iter_jsonl(readiness_dir / "readiness_rows.jsonl")
        if isinstance(row, dict) and row.get("family")
    }


def _gate(name: str, status: str, evidence: Any, required_for_live: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "required_for_live": bool(required_for_live),
        "evidence": evidence,
    }


def _live_ready(gates: list[dict[str, Any]]) -> bool:
    return all(str(gate["status"]) == "pass" for gate in gates if bool(gate.get("required_for_live", True)))


def _route_order_candidate(row: dict[str, Any]) -> dict[str, Any]:
    partition_count = int(row.get("partition_row_count") or 0)
    partition_holding = int(row.get("partition_contract_holding_row_count") or 0)
    child_pricing_negative = int(row.get("child_pricing_found_negative_row_count") or 0)
    direct_supported = bool(row.get("exact_pricing_supported", False))
    gates = [
        _gate("observed_seed61635_signal", "pass" if bool(row.get("observed_signal")) else "fail", bool(row.get("observed_signal"))),
        _gate(
            "state_scoped_partition_contract",
            "pass" if partition_count > 0 and partition_holding == partition_count else "fail",
            {"partition_row_count": partition_count, "holding": partition_holding},
        ),
        _gate(
            "finite_pool_child_rmp_lift_signal",
            "pass" if float(row.get("max_child_rmp_objective_gain") or 0.0) > 0.0 else "fail",
            row.get("max_child_rmp_objective_gain"),
            required_for_live=False,
        ),
        _gate(
            "child_pricing_pressure_cleared",
            "pass" if child_pricing_negative == 0 else "fail",
            {
                "child_pricing_found_negative_row_count": child_pricing_negative,
                "min_child_pricing_best_reduced_cost": row.get("min_child_pricing_best_reduced_cost"),
            },
        ),
        _gate(
            "direct_certificate_support",
            "pass" if direct_supported else "fail_closed",
            {"exact_pricing_supported": direct_supported},
        ),
        _gate(
            "completion_bound_certificate_path",
            "pass" if direct_supported else "fail_closed",
            {"completion_bound_fail_closed": bool(row.get("completion_bound_fail_closed", False))},
        ),
        _gate(
            "task_set_dominance_safety",
            "fail_closed",
            "route-order depends on materialized route signature, not only task set",
        ),
    ]
    return {
        "schema_version": "seed61635_formulation_contract_candidate_v1",
        "candidate": "state_scoped_route_order_partition_branch",
        "source_family": "route_order_partition_formulation",
        "selected_for_next_design": True,
        "live_ready": _live_ready(gates),
        "contract_status": "design_only_not_live",
        "gates": gates,
        "next_step": "write opt-in state-scoped branch controller contract tests; no direct certificate use until supported",
    }


def _route_resource_candidate(row: dict[str, Any]) -> dict[str, Any]:
    global_valid = int(row.get("max_global_valid_candidate_count") or 0)
    pricing_supported = int(row.get("max_pricing_supported_candidate_count") or 0)
    gates = [
        _gate("observed_seed61635_signal", "pass" if bool(row.get("observed_signal")) else "fail", bool(row.get("observed_signal"))),
        _gate("global_valid_row_family", "pass" if global_valid > 0 else "fail", global_valid),
        _gate("rmp_coefficient_defined", "fail", "no route-resource FutureCut contract is defined"),
        _gate("manual_reduced_cost_coefficient_defined", "fail", "manual_journey_reduced_cost has no route-resource coefficient"),
        _gate("pricing_reduced_cost_coefficient_defined", "pass" if pricing_supported > 0 else "fail", pricing_supported),
        _gate(
            "completion_bound_certificate_path",
            "pass" if pricing_supported > 0 else "fail_closed",
            {"completion_bound_fail_closed": bool(row.get("completion_bound_fail_closed", False))},
        ),
        _gate("integer_validity_test_defined", "fail", "no integer validity test for a route-resource row yet"),
    ]
    return {
        "schema_version": "seed61635_formulation_contract_candidate_v1",
        "candidate": "pricing_compatible_route_resource_row",
        "source_family": "route_resource_cut_audit",
        "selected_for_next_design": False,
        "live_ready": _live_ready(gates),
        "contract_status": "blocked_before_design",
        "gates": gates,
        "next_step": "do not implement live row until a globally valid or state-scoped row family is specified",
    }


def _weighted_candidate(row: dict[str, Any]) -> dict[str, Any]:
    moved = bool(row.get("dual_moved_from_seed61635_plateau", False))
    gates = [
        _gate("observed_seed61635_signal", "pass" if bool(row.get("observed_signal")) else "fail", bool(row.get("observed_signal"))),
        _gate(
            "coefficient_and_pricing_contract",
            "pass",
            "weighted subset row has RMP/manual/pricing coefficient support from V760",
            required_for_live=False,
        ),
        _gate("seed61635_dual_moved", "pass" if moved else "fail", moved),
    ]
    return {
        "schema_version": "seed61635_formulation_contract_candidate_v1",
        "candidate": "weighted_rank1_task_subset_row",
        "source_family": "weighted_rank1_task_subset",
        "selected_for_next_design": False,
        "live_ready": _live_ready(gates),
        "contract_status": "deprioritized_by_seed61635_efficacy_gate",
        "gates": gates,
        "next_step": "do not spend C-2 on expanding task-subset weighted rows",
    }


def build_seed61635_formulation_contract_gate(
    readiness_dir: Path,
    output_dir: Path,
    report: Path,
) -> dict[str, Any]:
    readiness_summary = _read_json(readiness_dir / "summary.json")
    families = _readiness_by_family(readiness_dir)
    candidates = [
        _route_order_candidate(families.get("route_order_partition_formulation", {})),
        _route_resource_candidate(families.get("route_resource_cut_audit", {})),
        _weighted_candidate(families.get("weighted_rank1_task_subset", {})),
    ]
    live_ready = [row for row in candidates if bool(row.get("live_ready"))]
    selected = [row for row in candidates if bool(row.get("selected_for_next_design"))]
    summary = {
        "schema_version": "seed61635_formulation_contract_gate_summary_v1",
        "date": date.today().isoformat(),
        "readiness_dir": str(readiness_dir),
        "output_dir": str(output_dir),
        "report_path": str(report),
        "candidate_count": len(candidates),
        "live_ready_candidate_count": len(live_ready),
        "selected_next_candidate": selected[0]["candidate"] if selected else None,
        "decision": "continue_C2_design_only; no_live_cut_or_live_branch",
        "readiness_decision": readiness_summary.get("decision"),
        "diagnostic_only": True,
        "production_ready": False,
        "official_bound_effect": False,
        "certificate_effect": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_path = output_dir / "contract_gate_rows.jsonl"
    rows_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in candidates) + "\n",
        encoding="utf-8",
    )
    summary["rows_path"] = str(rows_path)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary, candidates)
    return summary


def _write_report(report: Path, summary: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# V800 Seed61635 Formulation Contract Gate",
        "",
        "该报告把 V799 readiness audit 转成 C-2 contract gate。它只读已有 JSON/JSONL，不运行 BPC / pricing / RMP，不产生 official bound 或 certificate。",
        "",
        "## Summary",
        "",
        f"- candidate_count: `{summary['candidate_count']}`",
        f"- live_ready_candidate_count: `{summary['live_ready_candidate_count']}`",
        f"- selected_next_candidate: `{summary['selected_next_candidate']}`",
        f"- decision: `{summary['decision']}`",
        "",
        "## Candidate Gates",
        "",
    ]
    for candidate in candidates:
        lines.extend(
            [
                f"### {candidate['candidate']}",
                "",
                f"- selected_for_next_design: `{candidate['selected_for_next_design']}`",
                f"- live_ready: `{candidate['live_ready']}`",
                f"- contract_status: `{candidate['contract_status']}`",
                f"- next_step: `{candidate['next_step']}`",
                "",
            ]
        )
        for gate in candidate["gates"]:
            lines.append(
                f"- `{gate['name']}`: `{gate['status']}`"
                f" (required_for_live=`{gate['required_for_live']}`)"
            )
        lines.append("")
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    summary = build_seed61635_formulation_contract_gate(
        readiness_dir=args.readiness_dir,
        output_dir=args.output_dir,
        report=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
