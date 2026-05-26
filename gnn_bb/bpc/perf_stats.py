"""中文摘要：聚合 clean BPC JSONL/CSV 日志，生成性能与 hardness 诊断摘要。"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


HARDNESS_HELP = """Hardness tags:
- primal-hard: no incumbent, no first-incumbent time, or best incumbent appears after half of the run time.
- proof-hard: incumbent exists but optimality is not proved, official bound is unavailable, diagnostic gap remains positive, or pricing labels are very high.
- branch-hard: branch testing consumes at least 5% of time, many nodes are processed, or branch candidate testing is large.
- schedule-conflict-hard: RIM rejects schedule-infeasible integer solutions or schedule/no-good/route-pack/capacity cuts are active.
"""


def analyze_logs(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for path in paths:
        path = Path(path)
        if path.suffix.lower() == ".csv":
            summaries.extend(analyze_csv(path))
        else:
            summaries.append(analyze_jsonl(path))
    return summaries


def analyze_csv(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    summaries: list[dict[str, Any]] = []
    for row in rows:
        summary = {
            "source": str(path),
            "instance": row.get("instance") or path.stem,
            "status": row.get("status"),
            "primal_bound": _number(row.get("primal_bound")),
            "dual_bound": _number(row.get("dual_bound")),
            "diagnostic_dual_bound": _number(row.get("diagnostic_dual_bound")),
            "gap": _number(row.get("gap")),
            "diagnostic_gap": _number(row.get("diagnostic_gap")),
            "root_relaxation": _number(row.get("root_relaxation")),
            "initial_incumbent": None,
            "time_to_first_incumbent": _number(row.get("time_to_first_incumbent")),
            "time_to_best_incumbent": _number(row.get("time_to_best_incumbent")),
            "root_gap": None,
            "rmp_solves": _int(row.get("rmp_solves")),
            "pricing_calls": _int(row.get("pricing_calls")),
            "exact_pricing_calls": _int(row.get("exact_pricing_calls")),
            "label_pops": _int(row.get("label_pops")),
            "generated_labels": _int(row.get("generated_labels")),
            "branch_nodes": _int(row.get("branch_nodes")),
            "branch_lp_candidates_tested": _int(row.get("branch_lp_candidates_tested")),
            "branch_heuristic_candidates_tested": _int(row.get("branch_heuristic_candidates_tested")),
            "branch_testing_time": _number(row.get("branch_testing_time")) or 0.0,
            "restricted_master_rejected": _int(row.get("restricted_master_integer_rejected")),
            "restricted_master_pair_conflict_cuts": _int(row.get("restricted_master_integer_pair_conflict_cuts")),
            "restricted_master_route_set_packing_cuts": _int(row.get("restricted_master_integer_route_set_packing_cuts")),
            "restricted_master_schedule_capacity_cuts": _int(row.get("restricted_master_integer_schedule_capacity_cuts")),
            "restricted_master_no_good_cuts": _int(row.get("restricted_master_integer_no_good_cuts")),
            "restricted_master_adaptive_skips": _int(row.get("restricted_master_adaptive_skips")),
            "restricted_master_adaptive_time_limit_reductions": _int(
                row.get("restricted_master_adaptive_time_limit_reductions")
            ),
            "restricted_master_adaptive_failure_streak_max": _int(
                row.get("restricted_master_adaptive_failure_streak_max")
            ),
            "task_schedule_capacity_cuts_added": _int(row.get("task_schedule_capacity_cuts_added")),
            "task_schedule_capacity_candidates_generated": _int(row.get("task_schedule_capacity_candidates_generated")),
            "task_schedule_capacity_candidates_after_precheck": _int(row.get("task_schedule_capacity_candidates_after_precheck")),
            "task_schedule_capacity_pair_candidates": _int(row.get("task_schedule_capacity_pair_candidates")),
            "task_schedule_capacity_triple_candidates": _int(row.get("task_schedule_capacity_triple_candidates")),
            "task_schedule_capacity_small_set_candidates": _int(row.get("task_schedule_capacity_small_set_candidates")),
            "task_schedule_capacity_candidates_by_source": row.get("task_schedule_capacity_candidates_by_source"),
            "task_schedule_capacity_prechecked_by_source": row.get("task_schedule_capacity_prechecked_by_source"),
            "task_schedule_capacity_oracle_requests": _int(row.get("task_schedule_capacity_oracle_requests")),
            "task_schedule_capacity_oracle_computations": _int(row.get("task_schedule_capacity_oracle_computations")),
            "task_schedule_capacity_cache_hits": _int(row.get("task_schedule_capacity_cache_hits")),
            "task_schedule_capacity_oracle_time": _number(row.get("task_schedule_capacity_oracle_time")) or 0.0,
            "task_schedule_capacity_oracle_incomplete": _int(row.get("task_schedule_capacity_oracle_incomplete")),
            "task_schedule_capacity_exact_not_tight": _int(row.get("task_schedule_capacity_exact_not_tight")),
            "task_schedule_capacity_exact_tight_not_violated": _int(row.get("task_schedule_capacity_exact_tight_not_violated")),
            "task_schedule_capacity_violated_candidates": _int(row.get("task_schedule_capacity_violated_candidates")),
            "task_schedule_capacity_best_violation": _number(row.get("task_schedule_capacity_best_violation")) or 0.0,
            "task_schedule_capacity_oracle_states_total": _int(row.get("task_schedule_capacity_oracle_states_total")),
            "task_schedule_capacity_oracle_states_max": _int(row.get("task_schedule_capacity_oracle_states_max")),
            "task_schedule_capacity_cuts_copied_to_all_vehicles": _int(row.get("task_schedule_capacity_cuts_copied_to_all_vehicles")),
            "task_schedule_capacity_stopped_by_no_add": _int(row.get("task_schedule_capacity_stopped_by_no_add")),
            "task_schedule_capacity_stopped_by_no_improvement": _int(row.get("task_schedule_capacity_stopped_by_no_improvement")),
            "task_schedule_capacity_stopped_by_node_time_budget": _int(row.get("task_schedule_capacity_stopped_by_node_time_budget")),
            "task_schedule_capacity_stopped_by_global_time_budget": _int(row.get("task_schedule_capacity_stopped_by_global_time_budget")),
            "task_schedule_capacity_branch_signal_candidates": _int(row.get("task_schedule_capacity_branch_signal_candidates")),
            "task_schedule_capacity_branch_signal_applied": _int(row.get("task_schedule_capacity_branch_signal_applied")),
            "weighted_route_schedule_packing_cuts_added": _int(row.get("weighted_route_schedule_packing_cuts_added")),
            "weighted_route_schedule_packing_candidates_generated": _int(
                row.get("weighted_route_schedule_packing_candidates_generated")
            ),
            "weighted_route_schedule_packing_candidates_after_precheck": _int(
                row.get("weighted_route_schedule_packing_candidates_after_precheck")
            ),
            "weighted_route_schedule_packing_candidates_by_source": row.get(
                "weighted_route_schedule_packing_candidates_by_source"
            ),
            "weighted_route_schedule_packing_candidates_by_alpha": row.get(
                "weighted_route_schedule_packing_candidates_by_alpha"
            ),
            "weighted_route_schedule_packing_oracle_requests": _int(
                row.get("weighted_route_schedule_packing_oracle_requests")
            ),
            "weighted_route_schedule_packing_oracle_computations": _int(
                row.get("weighted_route_schedule_packing_oracle_computations")
            ),
            "weighted_route_schedule_packing_cache_hits": _int(row.get("weighted_route_schedule_packing_cache_hits")),
            "weighted_route_schedule_packing_oracle_incomplete": _int(
                row.get("weighted_route_schedule_packing_oracle_incomplete")
            ),
            "weighted_route_schedule_packing_exact_not_violated": _int(
                row.get("weighted_route_schedule_packing_exact_not_violated")
            ),
            "weighted_route_schedule_packing_violated_candidates": _int(
                row.get("weighted_route_schedule_packing_violated_candidates")
            ),
            "weighted_route_schedule_packing_best_violation": _number(
                row.get("weighted_route_schedule_packing_best_violation")
            )
            or 0.0,
            "weighted_route_schedule_packing_oracle_time": _number(row.get("weighted_route_schedule_packing_oracle_time"))
            or 0.0,
            "weighted_route_schedule_packing_oracle_states_total": _int(
                row.get("weighted_route_schedule_packing_oracle_states_total")
            ),
            "weighted_route_schedule_packing_oracle_states_max": _int(
                row.get("weighted_route_schedule_packing_oracle_states_max")
            ),
            "weighted_route_schedule_packing_added_but_no_bound_improvement": _int(
                row.get("weighted_route_schedule_packing_added_but_no_bound_improvement")
            ),
            "weighted_route_schedule_packing_stopped_by_budget": _int(
                row.get("weighted_route_schedule_packing_stopped_by_budget")
            ),
            "weighted_route_schedule_packing_duplicate_skips": _int(row.get("weighted_route_schedule_packing_duplicate_skips")),
            "route_pack_roi_classifications": row.get("route_pack_roi_classifications"),
            "route_pack_roi_same_pool_degeneracy": _int(row.get("route_pack_roi_same_pool_degeneracy")),
            "route_pack_roi_pricing_mousehole": _int(row.get("route_pack_roi_pricing_mousehole")),
            "route_pack_roi_objective_degeneracy_no_support_change": _int(
                row.get("route_pack_roi_objective_degeneracy_no_support_change")
            ),
            "route_pack_roi_mixed": _int(row.get("route_pack_roi_mixed")),
            "route_pool_restart_nodes": _int(row.get("route_pool_restart_nodes")),
            "route_pool_restart_rounds": _int(row.get("route_pool_restart_rounds")),
            "route_pool_restart_routes_omitted_total": _int(row.get("route_pool_restart_routes_omitted_total")),
            "route_pool_restart_routes_omitted_max": _int(row.get("route_pool_restart_routes_omitted_max")),
            "route_pool_restart_pricing_recovered_routes": _int(row.get("route_pool_restart_pricing_recovered_routes")),
            "route_pool_restart_protected_routes_max": _int(row.get("route_pool_restart_protected_routes_max")),
            "route_pool_hygiene_diagnostic_events": _int(row.get("route_pool_hygiene_diagnostic_events")),
            "route_pool_hygiene_task_set_groups_max": _int(row.get("route_pool_hygiene_task_set_groups_max")),
            "route_pool_hygiene_multi_route_groups_max": _int(row.get("route_pool_hygiene_multi_route_groups_max")),
            "route_pool_hygiene_near_duplicate_groups_max": _int(row.get("route_pool_hygiene_near_duplicate_groups_max")),
            "route_pool_hygiene_near_duplicate_routes_max": _int(row.get("route_pool_hygiene_near_duplicate_routes_max")),
            "route_pool_hygiene_max_group_size": _int(row.get("route_pool_hygiene_max_group_size")),
            "route_pool_hygiene_admission_evaluated": _int(row.get("route_pool_hygiene_admission_evaluated")),
            "route_pool_hygiene_admission_admitted": _int(row.get("route_pool_hygiene_admission_admitted")),
            "route_pool_hygiene_admission_filtered": _int(row.get("route_pool_hygiene_admission_filtered")),
            "route_pool_hygiene_admission_protected": _int(row.get("route_pool_hygiene_admission_protected")),
            "route_pool_hygiene_admission_forced_exact": _int(row.get("route_pool_hygiene_admission_forced_exact")),
            "open_nodes_remaining": _int(row.get("open_nodes_remaining")),
            "timeout_pending_node_certified": _bool_or_none(row.get("timeout_pending_node_certified")),
            "official_bound_available": _bool_or_none(row.get("official_bound_available")),
            "fathom_reasons": {},
            "cut_families": {},
            "node_metrics": {},
            "pricing_by_node": {},
            "finish_time": _number(row.get("solving_time")) or 0.0,
        }
        summary["root_gap"] = _root_gap(summary.get("initial_incumbent"), summary.get("root_relaxation"))
        summary["hardness_tags"] = hardness_tags(summary)
        summaries.append(summary)
    return summaries


def analyze_jsonl(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    records = _load_jsonl(path)
    start = next((record for record in records if record.get("event") == "start"), {})
    finish = next((record for record in reversed(records) if record.get("event") == "finish"), {})
    timeout = next((record for record in reversed(records) if record.get("event") == "timeout_diagnostics"), {})
    incumbents = [record for record in records if record.get("event") == "incumbent"]
    pricing_events = [record for record in records if record.get("event") == "pricing"]
    rmp_events = [record for record in records if record.get("event") == "rmp"]
    finish_time = _number(finish.get("time")) or (max((_number(record.get("time")) or 0.0 for record in records), default=0.0))
    initial_incumbent = _number(start.get("initial_incumbent"))
    time_to_first_incumbent = _number(finish.get("time_to_first_incumbent"))
    time_to_best_incumbent = _number(finish.get("time_to_best_incumbent"))
    if time_to_first_incumbent is None and incumbents:
        time_to_first_incumbent = _number(incumbents[0].get("time"))
    if time_to_best_incumbent is None and incumbents:
        best = min(incumbents, key=lambda record: (_number(record.get("objective")) or float("inf")))
        time_to_best_incumbent = _number(best.get("time"))

    node_metrics: dict[str, dict[str, Any]] = defaultdict(lambda: _empty_node_metrics())
    pricing_by_node: dict[str, dict[str, Any]] = defaultdict(lambda: _empty_pricing_metrics())
    cut_families: dict[str, Counter[str]] = defaultdict(Counter)
    cut_roi: dict[str, dict[str, float | int]] = defaultdict(lambda: {"events": 0, "added": 0, "improvement": 0.0, "low_improvement": 0})
    fathom_reasons: Counter[str] = Counter()
    open_nodes_timeline: list[dict[str, Any]] = []
    branch_candidate_count = 0
    branch_lp_testing = 0
    branch_heuristic_testing = 0
    branch_testing_time = _number(finish.get("branch_testing_time")) or 0.0
    rim = Counter()
    task_schedcap = Counter()
    task_schedcap_by_source: Counter[str] = Counter()
    task_schedcap_prechecked_by_source: Counter[str] = Counter()
    task_schedcap_time = 0.0
    task_schedcap_best_violation = 0.0
    weighted_route_pack = Counter()
    weighted_route_pack_by_source: Counter[str] = Counter()
    weighted_route_pack_by_alpha: Counter[str] = Counter()
    weighted_route_pack_time = 0.0
    weighted_route_pack_best_violation = 0.0
    route_pack_roi_classifications: Counter[str] = Counter()
    route_pool_restart = Counter()
    route_pool_hygiene = Counter()

    for record in records:
        event = str(record.get("event", ""))
        node_id = record.get("node_id")
        node_key = "" if node_id is None else str(node_id)
        if event == "rmp" and node_key:
            item = node_metrics[node_key]
            item["rmp_solves"] += 1
            item["last_rmp_objective"] = _number(record.get("objective"))
            item["depth"] = record.get("depth")
            if node_id == 0 and str(record.get("phase")) == "phase2" and item.get("root_phase2_objective") is None:
                item["root_phase2_objective"] = _number(record.get("objective"))
        elif event == "pricing" and node_key:
            node_metrics[node_key]["pricing_calls"] += 1
            if str(record.get("pricing_kind")) == "exact":
                node_metrics[node_key]["exact_pricing_calls"] += 1
            pricing = pricing_by_node[node_key]
            pricing["calls"] += 1
            pricing["exact_calls"] += int(str(record.get("pricing_kind")) == "exact")
            pricing["label_pops"] += _int(record.get("label_pops"))
            pricing["generated_labels"] += _int(record.get("generated_labels"))
            pricing["added_routes"] += _int(record.get("added_routes"))
            pricing["certificates"] += int(bool(record.get("certificate")))
            best_rc = _number(record.get("best_reduced_cost"))
            if best_rc is not None:
                current = pricing.get("best_reduced_cost")
                pricing["best_reduced_cost"] = best_rc if current is None else min(float(current), best_rc)
        elif event == "cut_added":
            family = str(record.get("family") or "unknown")
            cut_families[family]["added"] += _int(record.get("added"))
        elif event.endswith("_diagnostics"):
            family = _diagnostic_family(event)
            cut_families[family]["attempts"] += 1
            cut_families[family]["oracle_queries"] += _int(record.get("oracle_queries"))
            cut_families[family]["oracle_requests"] += _int(record.get("oracle_requests"))
            cut_families[family]["oracle_computations"] += _int(record.get("oracle_computations"))
            cut_families[family]["oracle_time_us"] += int(round((_number(record.get("oracle_time")) or 0.0) * 1_000_000))
            cut_families[family]["incomplete"] += _int(record.get("skipped_oracle_incomplete")) + _int(record.get("oracle_incomplete"))
            cut_families[family]["duplicate"] += _int(record.get("skipped_duplicate")) + _int(record.get("duplicate"))
            cut_families[family]["added"] += _int(record.get("added")) + _int(record.get("cuts_added"))
            if event == "task_schedule_capacity_diagnostics":
                task_schedcap["generated"] += _int(record.get("candidates_generated"))
                task_schedcap["prechecked"] += _int(record.get("candidates_after_precheck"))
                task_schedcap["pair"] += _int(record.get("pair_candidates"))
                task_schedcap["triple"] += _int(record.get("triple_candidates"))
                task_schedcap["small"] += _int(record.get("small_set_candidates"))
                task_schedcap["oracle_requests"] += _int(record.get("oracle_requests"))
                task_schedcap["oracle_computations"] += _int(record.get("oracle_computations"))
                task_schedcap["cache_hits"] += _int(record.get("cache_hits"))
                task_schedcap["incomplete"] += _int(record.get("oracle_incomplete"))
                task_schedcap["not_tight"] += _int(record.get("exact_not_tight"))
                task_schedcap["not_violated"] += _int(record.get("exact_tight_not_violated"))
                task_schedcap["violated"] += _int(record.get("violated_candidates"))
                task_schedcap["added"] += _int(record.get("cuts_added"))
                task_schedcap["states_total"] += _int(record.get("oracle_states_total"))
                task_schedcap["states_max"] = max(int(task_schedcap["states_max"]), _int(record.get("oracle_states_max")))
                task_schedcap["copied"] += _int(record.get("cuts_copied_to_all_vehicles"))
                stopped_by = str(record.get("stopped_by") or "")
                task_schedcap["stopped_by_no_add"] += int(stopped_by == "no_add_rounds")
                task_schedcap["stopped_by_no_improvement"] += int(stopped_by == "no_improvement_rounds")
                task_schedcap["stopped_by_node_time_budget"] += int(stopped_by == "node_time_budget")
                task_schedcap["stopped_by_global_time_budget"] += int(stopped_by == "global_time_budget")
                task_schedcap["branch_signal_candidates"] += _int(record.get("branch_signal_candidates"))
                task_schedcap["branch_signal_applied"] += _int(record.get("branch_signal_applied"))
                task_schedcap_best_violation = max(
                    task_schedcap_best_violation,
                    _number(record.get("best_violation")) or 0.0,
                )
                for key, value in (record.get("candidates_by_source") or {}).items():
                    task_schedcap_by_source[str(key)] += _int(value)
                for key, value in (record.get("prechecked_by_source") or {}).items():
                    task_schedcap_prechecked_by_source[str(key)] += _int(value)
                task_schedcap_time += _number(record.get("oracle_time")) or 0.0
            elif event == "weighted_route_schedule_packing_diagnostics":
                weighted_route_pack["generated"] += _int(record.get("candidate_sets"))
                weighted_route_pack["prechecked"] += _int(record.get("candidates_after_precheck"))
                weighted_route_pack["oracle_requests"] += _int(record.get("oracle_requests"))
                weighted_route_pack["oracle_computations"] += _int(record.get("oracle_computations"))
                weighted_route_pack["cache_hits"] += _int(record.get("cache_hits"))
                weighted_route_pack["incomplete"] += _int(record.get("oracle_incomplete"))
                weighted_route_pack["not_violated"] += _int(record.get("exact_not_violated"))
                weighted_route_pack["violated"] += _int(record.get("violated_candidates"))
                weighted_route_pack["added"] += _int(record.get("cuts_added")) + _int(record.get("added"))
                weighted_route_pack["states_total"] += _int(record.get("oracle_states_total"))
                weighted_route_pack["states_max"] = max(
                    int(weighted_route_pack["states_max"]),
                    _int(record.get("oracle_states_max")),
                )
                weighted_route_pack["stopped_by_budget"] += int(
                    str(record.get("stopped_by") or "") in {"node_time_budget", "global_time_budget"}
                )
                weighted_route_pack["duplicate"] += _int(record.get("duplicate"))
                weighted_route_pack_best_violation = max(
                    weighted_route_pack_best_violation,
                    _number(record.get("best_violation")) or 0.0,
                )
                weighted_route_pack_time += _number(record.get("oracle_time")) or 0.0
                for key, value in (record.get("candidates_by_source") or {}).items():
                    weighted_route_pack_by_source[str(key)] += _int(value)
                for key, value in (record.get("candidates_by_alpha") or {}).items():
                    weighted_route_pack_by_alpha[str(key)] += _int(value)
            elif event == "route_pack_roi_diagnostics":
                route_pack_roi_classifications[str(record.get("classification") or "unknown")] += 1
        elif event == "cut_roi":
            family = str(record.get("family") or "unknown")
            cut_roi[family]["events"] = int(cut_roi[family]["events"]) + 1
            cut_roi[family]["added"] = int(cut_roi[family]["added"]) + _int(record.get("added"))
            cut_roi[family]["improvement"] = float(cut_roi[family]["improvement"]) + (_number(record.get("objective_improvement")) or 0.0)
            cut_roi[family]["low_improvement"] = int(cut_roi[family]["low_improvement"]) + int(bool(record.get("low_improvement")))
        elif event == "restricted_integer_master":
            rim["rejected_solutions"] += _int(record.get("rejected_solutions"))
            rim["pair_conflict_cuts"] += _int(record.get("pair_conflict_cuts"))
            rim["route_set_packing_cuts"] += _int(record.get("route_set_packing_cuts"))
            rim["schedule_capacity_cuts"] += _int(record.get("schedule_capacity_cuts"))
            rim["no_good_cuts"] += _int(record.get("no_good_cuts"))
            rim["adaptive_time_limit_reductions"] += int(bool(record.get("adaptive_reduced")))
            rim["adaptive_failure_streak_max"] = max(
                int(rim["adaptive_failure_streak_max"]),
                _int(record.get("adaptive_failure_streak")),
            )
        elif event == "restricted_integer_master_adaptive_skip":
            rim["adaptive_skips"] += 1
        elif event == "rim_conflict_diagnostics":
            rim["conflicts_checked"] += _int(record.get("conflicts_checked"))
            rim["route_set_packing_events"] += _int(record.get("route_set_packing_events"))
            rim["schedule_capacity_events"] += _int(record.get("schedule_capacity_events"))
        elif event == "branch_candidates":
            branch_candidate_count += _int(record.get("count"))
        elif event == "branch_selection":
            branch_lp_testing += _int(record.get("lp_tested"))
            branch_heuristic_testing += _int(record.get("heuristic_tested"))
            branch_testing_time += _number(record.get("testing_time")) or 0.0
        elif event == "fathom":
            fathom_reasons[str(record.get("reason") or "unknown")] += 1
        elif event == "route_pool_restart":
            route_pool_restart["rounds"] += 1
            route_pool_restart["omitted_total"] += _int(record.get("omitted_routes"))
            route_pool_restart["omitted_max"] = max(
                int(route_pool_restart["omitted_max"]),
                _int(record.get("omitted_routes")),
            )
            route_pool_restart["protected_max"] = max(
                int(route_pool_restart["protected_max"]),
                _int((record.get("reason_counts") or {}).get("protected")),
            )
            if str(record.get("stage")) == "node_start":
                route_pool_restart["nodes"] += 1
        elif event == "route_pool_hygiene_diagnostics":
            route_pool_hygiene["diagnostic_events"] += 1
            route_pool_hygiene["task_set_groups_max"] = max(
                int(route_pool_hygiene["task_set_groups_max"]),
                _int(record.get("task_set_groups")),
            )
            route_pool_hygiene["multi_route_groups_max"] = max(
                int(route_pool_hygiene["multi_route_groups_max"]),
                _int(record.get("multi_route_groups")),
            )
            route_pool_hygiene["near_duplicate_groups_max"] = max(
                int(route_pool_hygiene["near_duplicate_groups_max"]),
                _int(record.get("near_duplicate_groups")),
            )
            route_pool_hygiene["near_duplicate_routes_max"] = max(
                int(route_pool_hygiene["near_duplicate_routes_max"]),
                _int(record.get("near_duplicate_routes")),
            )
            route_pool_hygiene["max_group_size"] = max(
                int(route_pool_hygiene["max_group_size"]),
                _int(record.get("max_group_size")),
            )
        elif event == "route_pool_hygiene_admission":
            route_pool_hygiene["admission_evaluated"] += _int(record.get("evaluated_routes"))
            route_pool_hygiene["admission_admitted"] += _int(record.get("admitted_routes"))
            route_pool_hygiene["admission_filtered"] += _int(record.get("filtered_routes"))
            route_pool_hygiene["admission_protected"] += _int(record.get("protected_routes"))
            route_pool_hygiene["admission_forced_exact"] += int(bool(record.get("forced_exact_certificate")))
        elif event in {"node_start", "node_end"}:
            open_nodes_timeline.append(
                {
                    "time": _number(record.get("time")),
                    "node_id": record.get("node_id"),
                    "event": event,
                    "open_nodes": _int(record.get("open_nodes")),
                }
            )

    root_relaxation = _number(finish.get("root_relaxation"))
    if root_relaxation is None:
        root_relaxation = node_metrics.get("0", {}).get("root_phase2_objective")

    summary = {
        "source": str(path),
        "instance": start.get("instance") or finish.get("instance") or path.stem,
        "status": finish.get("status"),
        "primal_bound": _number(finish.get("primal_bound")),
        "dual_bound": _number(finish.get("dual_bound")),
        "diagnostic_dual_bound": _number(finish.get("diagnostic_dual_bound")) or _number(timeout.get("diagnostic_bound")),
        "gap": _number(finish.get("gap")),
        "diagnostic_gap": _number(finish.get("diagnostic_gap")),
        "root_relaxation": root_relaxation,
        "initial_incumbent": initial_incumbent,
        "time_to_first_incumbent": time_to_first_incumbent,
        "time_to_best_incumbent": time_to_best_incumbent,
        "root_gap": _root_gap(initial_incumbent, root_relaxation),
        "rmp_solves": len(rmp_events),
        "pricing_calls": len(pricing_events),
        "exact_pricing_calls": sum(1 for record in pricing_events if str(record.get("pricing_kind")) == "exact"),
        "label_pops": sum(_int(record.get("label_pops")) for record in pricing_events),
        "generated_labels": sum(_int(record.get("generated_labels")) for record in pricing_events),
        "best_reduced_cost": _min_number(record.get("best_reduced_cost") for record in pricing_events),
        "added_routes": sum(_int(record.get("added_routes")) for record in pricing_events),
        "certified_pricing_calls": sum(1 for record in pricing_events if bool(record.get("certificate"))),
        "node_metrics": dict(node_metrics),
        "pricing_by_node": dict(pricing_by_node),
        "cut_families": _finalize_cut_families(cut_families),
        "cut_roi": dict(cut_roi),
        "restricted_master_rejected": int(rim["rejected_solutions"]),
        "restricted_master_pair_conflict_cuts": int(rim["pair_conflict_cuts"]),
        "restricted_master_route_set_packing_cuts": int(rim["route_set_packing_cuts"]),
        "restricted_master_schedule_capacity_cuts": int(rim["schedule_capacity_cuts"]),
        "restricted_master_no_good_cuts": int(rim["no_good_cuts"]),
        "restricted_master_adaptive_skips": int(rim["adaptive_skips"])
        or _int(finish.get("restricted_master_adaptive_skips")),
        "restricted_master_adaptive_time_limit_reductions": int(rim["adaptive_time_limit_reductions"])
        or _int(finish.get("restricted_master_adaptive_time_limit_reductions")),
        "restricted_master_adaptive_failure_streak_max": int(rim["adaptive_failure_streak_max"])
        or _int(finish.get("restricted_master_adaptive_failure_streak_max")),
        "rim_conflicts_checked": int(rim["conflicts_checked"]),
        "task_schedule_capacity_cuts_added": int(task_schedcap["added"]) or _int(finish.get("task_schedule_capacity_cuts_added")),
        "task_schedule_capacity_candidates_generated": int(task_schedcap["generated"])
        or _int(finish.get("task_schedule_capacity_candidates_generated")),
        "task_schedule_capacity_candidates_after_precheck": int(task_schedcap["prechecked"])
        or _int(finish.get("task_schedule_capacity_candidates_after_precheck")),
        "task_schedule_capacity_pair_candidates": int(task_schedcap["pair"])
        or _int(finish.get("task_schedule_capacity_pair_candidates")),
        "task_schedule_capacity_triple_candidates": int(task_schedcap["triple"])
        or _int(finish.get("task_schedule_capacity_triple_candidates")),
        "task_schedule_capacity_small_set_candidates": int(task_schedcap["small"])
        or _int(finish.get("task_schedule_capacity_small_set_candidates")),
        "task_schedule_capacity_candidates_by_source": dict(task_schedcap_by_source)
        or finish.get("task_schedule_capacity_candidates_by_source"),
        "task_schedule_capacity_prechecked_by_source": dict(task_schedcap_prechecked_by_source)
        or finish.get("task_schedule_capacity_prechecked_by_source"),
        "task_schedule_capacity_oracle_requests": int(task_schedcap["oracle_requests"])
        or _int(finish.get("task_schedule_capacity_oracle_requests")),
        "task_schedule_capacity_oracle_computations": int(task_schedcap["oracle_computations"])
        or _int(finish.get("task_schedule_capacity_oracle_computations")),
        "task_schedule_capacity_cache_hits": int(task_schedcap["cache_hits"]) or _int(finish.get("task_schedule_capacity_cache_hits")),
        "task_schedule_capacity_oracle_incomplete": int(task_schedcap["incomplete"])
        or _int(finish.get("task_schedule_capacity_oracle_incomplete")),
        "task_schedule_capacity_exact_not_tight": int(task_schedcap["not_tight"])
        or _int(finish.get("task_schedule_capacity_exact_not_tight")),
        "task_schedule_capacity_exact_tight_not_violated": int(task_schedcap["not_violated"])
        or _int(finish.get("task_schedule_capacity_exact_tight_not_violated")),
        "task_schedule_capacity_violated_candidates": int(task_schedcap["violated"])
        or _int(finish.get("task_schedule_capacity_violated_candidates")),
        "task_schedule_capacity_best_violation": task_schedcap_best_violation
        or (_number(finish.get("task_schedule_capacity_best_violation")) or 0.0),
        "task_schedule_capacity_oracle_time": task_schedcap_time or (_number(finish.get("task_schedule_capacity_oracle_time")) or 0.0),
        "task_schedule_capacity_oracle_states_total": int(task_schedcap["states_total"])
        or _int(finish.get("task_schedule_capacity_oracle_states_total")),
        "task_schedule_capacity_oracle_states_max": int(task_schedcap["states_max"])
        or _int(finish.get("task_schedule_capacity_oracle_states_max")),
        "task_schedule_capacity_cuts_copied_to_all_vehicles": int(task_schedcap["copied"])
        or _int(finish.get("task_schedule_capacity_cuts_copied_to_all_vehicles")),
        "task_schedule_capacity_stopped_by_no_add": int(task_schedcap["stopped_by_no_add"])
        or _int(finish.get("task_schedule_capacity_stopped_by_no_add")),
        "task_schedule_capacity_stopped_by_no_improvement": int(task_schedcap["stopped_by_no_improvement"])
        or _int(finish.get("task_schedule_capacity_stopped_by_no_improvement")),
        "task_schedule_capacity_stopped_by_node_time_budget": int(task_schedcap["stopped_by_node_time_budget"])
        or _int(finish.get("task_schedule_capacity_stopped_by_node_time_budget")),
        "task_schedule_capacity_stopped_by_global_time_budget": int(task_schedcap["stopped_by_global_time_budget"])
        or _int(finish.get("task_schedule_capacity_stopped_by_global_time_budget")),
        "task_schedule_capacity_branch_signal_candidates": int(task_schedcap["branch_signal_candidates"])
        or _int(finish.get("task_schedule_capacity_branch_signal_candidates")),
        "task_schedule_capacity_branch_signal_applied": int(task_schedcap["branch_signal_applied"])
        or _int(finish.get("task_schedule_capacity_branch_signal_applied")),
        "weighted_route_schedule_packing_cuts_added": int(weighted_route_pack["added"])
        or _int(finish.get("weighted_route_schedule_packing_cuts_added")),
        "weighted_route_schedule_packing_candidates_generated": int(weighted_route_pack["generated"])
        or _int(finish.get("weighted_route_schedule_packing_candidates_generated")),
        "weighted_route_schedule_packing_candidates_after_precheck": int(weighted_route_pack["prechecked"])
        or _int(finish.get("weighted_route_schedule_packing_candidates_after_precheck")),
        "weighted_route_schedule_packing_candidates_by_source": dict(weighted_route_pack_by_source)
        or finish.get("weighted_route_schedule_packing_candidates_by_source"),
        "weighted_route_schedule_packing_candidates_by_alpha": dict(weighted_route_pack_by_alpha)
        or finish.get("weighted_route_schedule_packing_candidates_by_alpha"),
        "weighted_route_schedule_packing_oracle_requests": int(weighted_route_pack["oracle_requests"])
        or _int(finish.get("weighted_route_schedule_packing_oracle_requests")),
        "weighted_route_schedule_packing_oracle_computations": int(weighted_route_pack["oracle_computations"])
        or _int(finish.get("weighted_route_schedule_packing_oracle_computations")),
        "weighted_route_schedule_packing_cache_hits": int(weighted_route_pack["cache_hits"])
        or _int(finish.get("weighted_route_schedule_packing_cache_hits")),
        "weighted_route_schedule_packing_oracle_incomplete": int(weighted_route_pack["incomplete"])
        or _int(finish.get("weighted_route_schedule_packing_oracle_incomplete")),
        "weighted_route_schedule_packing_exact_not_violated": int(weighted_route_pack["not_violated"])
        or _int(finish.get("weighted_route_schedule_packing_exact_not_violated")),
        "weighted_route_schedule_packing_violated_candidates": int(weighted_route_pack["violated"])
        or _int(finish.get("weighted_route_schedule_packing_violated_candidates")),
        "weighted_route_schedule_packing_best_violation": weighted_route_pack_best_violation
        or (_number(finish.get("weighted_route_schedule_packing_best_violation")) or 0.0),
        "weighted_route_schedule_packing_oracle_time": weighted_route_pack_time
        or (_number(finish.get("weighted_route_schedule_packing_oracle_time")) or 0.0),
        "weighted_route_schedule_packing_oracle_states_total": int(weighted_route_pack["states_total"])
        or _int(finish.get("weighted_route_schedule_packing_oracle_states_total")),
        "weighted_route_schedule_packing_oracle_states_max": int(weighted_route_pack["states_max"])
        or _int(finish.get("weighted_route_schedule_packing_oracle_states_max")),
        "weighted_route_schedule_packing_added_but_no_bound_improvement": _int(
            finish.get("weighted_route_schedule_packing_added_but_no_bound_improvement")
        ),
        "weighted_route_schedule_packing_stopped_by_budget": int(weighted_route_pack["stopped_by_budget"])
        or _int(finish.get("weighted_route_schedule_packing_stopped_by_budget")),
        "weighted_route_schedule_packing_duplicate_skips": int(weighted_route_pack["duplicate"])
        or _int(finish.get("weighted_route_schedule_packing_duplicate_skips")),
        "route_pack_roi_classifications": dict(route_pack_roi_classifications),
        "route_pack_roi_same_pool_degeneracy": int(route_pack_roi_classifications["same_pool_degeneracy"]),
        "route_pack_roi_pricing_mousehole": int(route_pack_roi_classifications["pricing_mousehole"]),
        "route_pack_roi_objective_degeneracy_no_support_change": int(
            route_pack_roi_classifications["objective_degeneracy_no_support_change"]
        ),
        "route_pack_roi_mixed": int(route_pack_roi_classifications["mixed"]),
        "route_pool_restart_nodes": int(route_pool_restart["nodes"]) or _int(finish.get("route_pool_restart_nodes")),
        "route_pool_restart_rounds": int(route_pool_restart["rounds"]) or _int(finish.get("route_pool_restart_rounds")),
        "route_pool_restart_routes_omitted_total": int(route_pool_restart["omitted_total"])
        or _int(finish.get("route_pool_restart_routes_omitted_total")),
        "route_pool_restart_routes_omitted_max": int(route_pool_restart["omitted_max"])
        or _int(finish.get("route_pool_restart_routes_omitted_max")),
        "route_pool_restart_pricing_recovered_routes": _int(
            finish.get("route_pool_restart_pricing_recovered_routes")
        ),
        "route_pool_restart_protected_routes_max": int(route_pool_restart["protected_max"])
        or _int(finish.get("route_pool_restart_protected_routes_max")),
        "route_pool_hygiene_diagnostic_events": int(route_pool_hygiene["diagnostic_events"])
        or _int(finish.get("route_pool_hygiene_diagnostic_events")),
        "route_pool_hygiene_task_set_groups_max": int(route_pool_hygiene["task_set_groups_max"])
        or _int(finish.get("route_pool_hygiene_task_set_groups_max")),
        "route_pool_hygiene_multi_route_groups_max": int(route_pool_hygiene["multi_route_groups_max"])
        or _int(finish.get("route_pool_hygiene_multi_route_groups_max")),
        "route_pool_hygiene_near_duplicate_groups_max": int(route_pool_hygiene["near_duplicate_groups_max"])
        or _int(finish.get("route_pool_hygiene_near_duplicate_groups_max")),
        "route_pool_hygiene_near_duplicate_routes_max": int(route_pool_hygiene["near_duplicate_routes_max"])
        or _int(finish.get("route_pool_hygiene_near_duplicate_routes_max")),
        "route_pool_hygiene_max_group_size": int(route_pool_hygiene["max_group_size"])
        or _int(finish.get("route_pool_hygiene_max_group_size")),
        "route_pool_hygiene_admission_evaluated": int(route_pool_hygiene["admission_evaluated"])
        or _int(finish.get("route_pool_hygiene_admission_evaluated")),
        "route_pool_hygiene_admission_admitted": int(route_pool_hygiene["admission_admitted"])
        or _int(finish.get("route_pool_hygiene_admission_admitted")),
        "route_pool_hygiene_admission_filtered": int(route_pool_hygiene["admission_filtered"])
        or _int(finish.get("route_pool_hygiene_admission_filtered")),
        "route_pool_hygiene_admission_protected": int(route_pool_hygiene["admission_protected"])
        or _int(finish.get("route_pool_hygiene_admission_protected")),
        "route_pool_hygiene_admission_forced_exact": int(route_pool_hygiene["admission_forced_exact"])
        or _int(finish.get("route_pool_hygiene_admission_forced_exact")),
        "branch_candidate_count": branch_candidate_count,
        "branch_lp_testing": branch_lp_testing or _int(finish.get("branch_lp_candidates_tested")),
        "branch_heuristic_testing": branch_heuristic_testing or _int(finish.get("branch_heuristic_candidates_tested")),
        "branch_testing_time": branch_testing_time,
        "fathom_reasons": dict(fathom_reasons or Counter(finish.get("fathom_reasons") or {})),
        "open_nodes_remaining": _int(finish.get("open_nodes_remaining")),
        "open_nodes_timeline": open_nodes_timeline,
        "timeout_pending_node_certified": _bool_or_none(
            timeout.get("timeout_pending_node_certified", finish.get("timeout_pending_node_certified"))
        ),
        "official_bound_available": _bool_or_none(
            timeout.get("official_bound_available", finish.get("official_bound_available"))
        ),
        "finish_time": finish_time,
    }
    summary["hardness_tags"] = hardness_tags(summary)
    return summary


def hardness_tags(summary: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    status = str(summary.get("status") or "")
    finish_time = float(summary.get("finish_time") or 0.0)
    time_to_first = summary.get("time_to_first_incumbent")
    time_to_best = summary.get("time_to_best_incumbent")
    primal = summary.get("primal_bound")
    diagnostic_gap = summary.get("diagnostic_gap")
    label_pops = int(summary.get("label_pops") or 0)
    node_count = sum(1 for _key in (summary.get("node_metrics") or {})) or int(summary.get("node_count") or 0)
    branch_testing_time = float(summary.get("branch_testing_time") or 0.0)
    branch_tests = int(summary.get("branch_lp_testing") or 0) + int(summary.get("branch_heuristic_testing") or 0)
    schedule_signal = (
        int(summary.get("restricted_master_rejected") or 0)
        + int(summary.get("restricted_master_pair_conflict_cuts") or 0)
        + int(summary.get("restricted_master_route_set_packing_cuts") or 0)
        + int(summary.get("restricted_master_schedule_capacity_cuts") or 0)
        + int(summary.get("restricted_master_no_good_cuts") or 0)
        + int(summary.get("rim_conflicts_checked") or 0)
    )
    for family, values in (summary.get("cut_families") or {}).items():
        if "schedule" in str(family) or "nogood" in str(family):
            schedule_signal += int(values.get("added") or 0) + int(values.get("incomplete") or 0)

    if primal is None or time_to_first is None or (finish_time > 0.0 and time_to_best is not None and time_to_best > 0.5 * finish_time):
        tags.append("primal-hard")
    if (
        status not in {"OPTIMAL", "INFEASIBLE"}
        and primal is not None
        and (
            summary.get("official_bound_available") is False
            or (diagnostic_gap is not None and float(diagnostic_gap) > 1.0e-4)
            or label_pops >= 10_000_000
        )
    ):
        tags.append("proof-hard")
    if (finish_time > 0.0 and branch_testing_time >= 0.05 * finish_time) or branch_tests >= 100 or node_count >= 100:
        tags.append("branch-hard")
    if schedule_signal > 0:
        tags.append("schedule-conflict-hard")
    return tags or ["easy-or-mixed"]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
    return records


def _empty_node_metrics() -> dict[str, Any]:
    return {
        "rmp_solves": 0,
        "pricing_calls": 0,
        "exact_pricing_calls": 0,
        "last_rmp_objective": None,
        "root_phase2_objective": None,
        "depth": None,
    }


def _empty_pricing_metrics() -> dict[str, Any]:
    return {
        "calls": 0,
        "exact_calls": 0,
        "label_pops": 0,
        "generated_labels": 0,
        "best_reduced_cost": None,
        "added_routes": 0,
        "certificates": 0,
    }


def _diagnostic_family(event: str) -> str:
    return event.removesuffix("_diagnostics").replace("_diag", "")


def _finalize_cut_families(families: dict[str, Counter[str]]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for family, counter in families.items():
        item = dict(counter)
        if "oracle_time_us" in item:
            item["oracle_time"] = round(float(item.pop("oracle_time_us")) / 1_000_000.0, 6)
        output[family] = item
    return output


def _root_gap(incumbent: Any, root_relaxation: Any) -> float | None:
    incumbent = _number(incumbent)
    root_relaxation = _number(root_relaxation)
    if incumbent is None or root_relaxation is None or abs(incumbent) <= 1.0e-12:
        return None
    return max(0.0, (incumbent - root_relaxation) / abs(incumbent))


def _min_number(values: Iterable[Any]) -> float | None:
    parsed = [_number(value) for value in values]
    parsed = [value for value in parsed if value is not None]
    return min(parsed, default=None)


def _number(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int:
    number = _number(value)
    if number is None:
        return 0
    return int(number)


def _bool_or_none(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None
