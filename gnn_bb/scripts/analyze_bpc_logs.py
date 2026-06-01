#!/usr/bin/env python3
"""中文摘要：汇总 clean BPC JSONL/CSV 日志，输出 hardness summary。"""

from __future__ import annotations

import argparse
import csv
import glob
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bpc.perf_stats import HARDNESS_HELP, analyze_logs  # noqa: E402


CSV_FIELDS = [
    "instance",
    "status",
    "hardness_tags",
    "primal_bound",
    "dual_bound",
    "diagnostic_dual_bound",
    "gap",
    "diagnostic_gap",
    "root_relaxation",
    "initial_incumbent",
    "root_gap",
    "time_to_first_incumbent",
    "time_to_best_incumbent",
    "rmp_solves",
    "pricing_calls",
    "exact_pricing_calls",
    "label_pops",
    "generated_labels",
    "best_reduced_cost",
    "added_routes",
    "certified_pricing_calls",
    "restricted_master_rejected",
    "restricted_master_pair_conflict_cuts",
    "restricted_master_route_set_packing_cuts",
    "restricted_master_schedule_capacity_cuts",
    "restricted_master_no_good_cuts",
    "restricted_master_adaptive_skips",
    "restricted_master_adaptive_time_limit_reductions",
    "restricted_master_adaptive_failure_streak_max",
    "restricted_master_adaptive_unproductive_streak_max",
    "restricted_master_adaptive_probe_forced",
    "restricted_master_adaptive_gap_skips",
    "restricted_master_adaptive_gap_forced_probes",
    "restricted_master_adaptive_raw_stall_skips",
    "restricted_master_adaptive_raw_stall_max",
    "pricing_tailing_events",
    "pricing_tailing_negative_search_slow",
    "pricing_tailing_certificate_slow",
    "pricing_tailing_degenerate",
    "pricing_tailing_branch_test_dominated",
    "pricing_tailing_exact_label_pops",
    "pricing_tailing_duplicate_task_sets",
    "selective_pricing_heuristic_attempts",
    "selective_pricing_true_negative_routes",
    "selective_pricing_false_candidate_routes",
    "selective_pricing_exact_calls_avoided",
    "selective_pricing_exact_calls_required",
    "pricing_stabilization_attempts",
    "pricing_stabilization_true_negative_routes",
    "pricing_stabilization_false_candidate_routes",
    "pricing_stabilization_exact_calls_required",
    "task_schedule_capacity_cuts_added",
    "task_schedule_capacity_candidates_generated",
    "task_schedule_capacity_candidates_after_precheck",
    "task_schedule_capacity_pair_candidates",
    "task_schedule_capacity_triple_candidates",
    "task_schedule_capacity_small_set_candidates",
    "task_schedule_capacity_candidates_by_source",
    "task_schedule_capacity_prechecked_by_source",
    "task_schedule_capacity_oracle_requests",
    "task_schedule_capacity_oracle_computations",
    "task_schedule_capacity_cache_hits",
    "task_schedule_capacity_oracle_incomplete",
    "task_schedule_capacity_exact_not_tight",
    "task_schedule_capacity_exact_tight_not_violated",
    "task_schedule_capacity_violated_candidates",
    "task_schedule_capacity_best_violation",
    "task_schedule_capacity_oracle_time",
    "task_schedule_capacity_oracle_states_total",
    "task_schedule_capacity_oracle_states_max",
    "task_schedule_capacity_cuts_copied_to_all_vehicles",
    "task_schedule_capacity_stopped_by_no_add",
    "task_schedule_capacity_stopped_by_no_improvement",
    "task_schedule_capacity_stopped_by_node_time_budget",
    "task_schedule_capacity_stopped_by_global_time_budget",
    "task_schedule_capacity_branch_signal_candidates",
    "task_schedule_capacity_branch_signal_applied",
    "witness_rank1_cuts_added",
    "witness_rank1_subset_row_cuts_added",
    "witness_rank1_lm_rank1_cuts_added",
    "witness_rank1_candidates_generated",
    "witness_rank1_candidates_after_precheck",
    "witness_rank1_violated_candidates",
    "witness_rank1_duplicate_skips",
    "witness_rank1_best_violation",
    "witness_rank1_candidates_by_source",
    "weighted_route_schedule_packing_cuts_added",
    "weighted_route_schedule_packing_candidates_generated",
    "weighted_route_schedule_packing_candidates_after_precheck",
    "weighted_route_schedule_packing_candidates_by_source",
    "weighted_route_schedule_packing_candidates_by_alpha",
    "weighted_route_schedule_packing_oracle_requests",
    "weighted_route_schedule_packing_oracle_computations",
    "weighted_route_schedule_packing_cache_hits",
    "weighted_route_schedule_packing_oracle_incomplete",
    "weighted_route_schedule_packing_exact_not_violated",
    "weighted_route_schedule_packing_violated_candidates",
    "weighted_route_schedule_packing_best_violation",
    "weighted_route_schedule_packing_oracle_time",
    "weighted_route_schedule_packing_oracle_states_total",
    "weighted_route_schedule_packing_oracle_states_max",
    "weighted_route_schedule_packing_added_but_no_bound_improvement",
    "weighted_route_schedule_packing_stopped_by_budget",
    "weighted_route_schedule_packing_duplicate_skips",
    "schedule_variant_route_pack_cuts_added",
    "schedule_variant_route_pack_candidates",
    "schedule_variant_route_pack_expanded_candidates",
    "schedule_variant_route_pack_oracle_queries",
    "schedule_variant_route_pack_cache_hits",
    "schedule_variant_route_pack_oracle_incomplete",
    "schedule_variant_route_pack_exact_not_tight",
    "schedule_variant_route_pack_exact_not_violated",
    "schedule_variant_route_pack_violated_candidates",
    "schedule_variant_route_pack_duplicate_skips",
    "schedule_variant_route_pack_best_violation",
    "schedule_variant_route_pack_oracle_time",
    "schedule_variant_route_pack_oracle_states_total",
    "schedule_variant_route_pack_oracle_states_max",
    "route_pack_roi_classifications",
    "route_pack_roi_same_pool_degeneracy",
    "route_pack_roi_pricing_mousehole",
    "route_pack_roi_objective_degeneracy_no_support_change",
    "route_pack_roi_mixed",
    "route_pool_restart_nodes",
    "route_pool_restart_rounds",
    "route_pool_restart_routes_omitted_total",
    "route_pool_restart_routes_omitted_max",
    "route_pool_restart_pricing_recovered_routes",
    "route_pool_restart_protected_routes_max",
    "route_pool_hygiene_diagnostic_events",
    "route_pool_hygiene_task_set_groups_max",
    "route_pool_hygiene_multi_route_groups_max",
    "route_pool_hygiene_near_duplicate_groups_max",
    "route_pool_hygiene_near_duplicate_routes_max",
    "route_pool_hygiene_max_group_size",
    "route_pool_hygiene_admission_evaluated",
    "route_pool_hygiene_admission_admitted",
    "route_pool_hygiene_admission_filtered",
    "route_pool_hygiene_admission_protected",
    "route_pool_hygiene_admission_forced_exact",
    "branch_candidate_count",
    "branch_lp_testing",
    "branch_heuristic_testing",
    "branch_testing_time",
    "open_nodes_remaining",
    "timeout_pending_node_certified",
    "official_bound_available",
    "source",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze clean BPC JSONL/CSV logs and classify instance hardness.",
        epilog=HARDNESS_HELP,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="JSONL/CSV paths or glob patterns.")
    parser.add_argument("--csv", dest="csv_path", help="Write summary CSV to this path.")
    parser.add_argument("--json", dest="json_path", help="Write full summary JSON to this path.")
    parser.add_argument("--pretty", action="store_true", help="Print a compact table to stdout.")
    args = parser.parse_args()

    paths = _expand_paths(args.paths)
    if not paths:
        parser.error("no input logs matched")

    summaries = analyze_logs(paths)
    if args.csv_path:
        _write_csv(Path(args.csv_path), summaries)
    if args.json_path:
        Path(args.json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_path).write_text(json.dumps(summaries, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if args.pretty or (not args.csv_path and not args.json_path):
        _print_pretty(summaries)
    return 0


def _expand_paths(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            paths.extend(Path(match) for match in matches)
        else:
            paths.append(Path(pattern))
    return [path for path in paths if path.exists()]


def _write_csv(path: Path, summaries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for summary in summaries:
            row = {field: _cell(summary.get(field)) for field in CSV_FIELDS}
            row["hardness_tags"] = "|".join(summary.get("hardness_tags") or [])
            writer.writerow(row)


def _print_pretty(summaries: list[dict[str, Any]]) -> None:
    rows = []
    for summary in summaries:
        rows.append(
            [
                str(summary.get("instance")),
                str(summary.get("status")),
                ",".join(summary.get("hardness_tags") or []),
                _fmt(summary.get("root_relaxation")),
                _fmt(summary.get("primal_bound")),
                _fmt(summary.get("dual_bound")),
                _fmt(summary.get("diagnostic_gap")),
                str(summary.get("label_pops") or 0),
                str(summary.get("open_nodes_remaining") or 0),
                str(summary.get("timeout_pending_node_certified")),
            ]
        )
    headers = ["instance", "status", "tags", "root_lb", "primal", "dual", "diag_gap", "labels", "open", "pending_cert"]
    widths = [len(header) for header in headers]
    for row in rows:
        widths = [max(width, len(cell)) for width, cell in zip(widths, row)]
    print("  ".join(header.ljust(width) for header, width in zip(headers, widths)))
    print("  ".join("-" * width for width in widths))
    for row in rows:
        print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)))


def _cell(value: Any) -> Any:
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return value


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.6g}"
    except (TypeError, ValueError):
        return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
