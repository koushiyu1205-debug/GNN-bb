#!/usr/bin/env python3
"""中文摘要：本脚本运行根目录 bpc/ 下的 clean Branch-Price-and-Cut 主线，并输出 CSV、JSONL 日志和解文件。"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bpc.data import load_bpc_data
from bpc.solver import BPCResult, solve_bpc_clean
from gnn_bb.baseline.config import load_config
from gnn_bb.data.io_utils import ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="运行根目录 bpc/ clean Branch-Price-and-Cut。")
    parser.add_argument("--config", default="configs/bpc_clean.yaml")
    parser.add_argument("--instances", nargs="*", help="覆盖配置中的实例列表")
    parser.add_argument("--time-limit", type=float, help="覆盖配置时间限制")
    parser.add_argument("--max-nodes", type=int, help="覆盖最大处理节点数")
    parser.add_argument("--results-csv", default="results/bpc_clean.csv")
    parser.add_argument("--log-dir", default="results/logs/bpc_clean")
    parser.add_argument("--solution-dir", default="results/solutions/bpc_clean")
    parser.add_argument("--quiet", action="store_true", help="关闭 clean BPC 控制台进度")
    return parser.parse_args()


def _write_rows(path: Path, rows: list[dict]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(BPCResult.__dataclass_fields__.keys()))
        writer.writeheader()
        writer.writerows(rows)


def _bool_config(config: dict, name: str, default: bool) -> bool:
    value = config.get(name, default)
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off", ""}
    return bool(value)


def _int_tuple_config(config: dict, name: str, default: tuple[int, ...]) -> tuple[int, ...]:
    value = config.get(name, default)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            text = text[1:-1]
        items = [item.strip() for item in text.split(",") if item.strip()]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        items = [value]
    parsed = tuple(sorted({int(item) for item in items if int(item) >= 2}))
    return parsed or tuple(default)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    instances = args.instances or config.get("instances", ["very_small"])
    time_limit = float(args.time_limit if args.time_limit is not None else config.get("time_limit", 3600))
    max_nodes = int(args.max_nodes if args.max_nodes is not None else config.get("max_nodes", 100000))
    rows = []
    for name in instances:
        data = load_bpc_data(str(name), instance_dir=config.get("instance_dir", "json/instances"))
        log_path = ROOT / args.log_dir / f"{data.name}.jsonl"
        solution_path = ROOT / args.solution_dir / f"solution_{data.name}.json"
        print(
            f"开始 clean BPC: instance={data.name}, tasks={len(data.tasks)}, vehicles={len(data.vehicles)}, "
            f"time_limit={time_limit:g}s, max_nodes={max_nodes}, log={log_path}",
            flush=True,
        )
        result = solve_bpc_clean(
            data,
            time_limit=time_limit,
            max_nodes=max_nodes,
            pricing_eps=float(config.get("pricing_eps", 1.0e-6)),
            integer_tol=float(config.get("integer_tol", 1.0e-6)),
            max_routes_per_pricing=int(config.get("max_routes_per_pricing", 200)),
            max_labels_per_pricing=int(config.get("max_labels_per_pricing", 0) or 0),
            root_max_routes_per_pricing=int(config.get("root_max_routes_per_pricing", 0) or 0),
            heuristic_pricing_enabled=_bool_config(config, "heuristic_pricing_enabled", False),
            heuristic_pricing_max_labels=int(config.get("heuristic_pricing_max_labels", 100000)),
            heuristic_pricing_routes_per_round=int(config.get("heuristic_pricing_routes_per_round", 500)),
            heuristic_pricing_selection_mode=str(config.get("heuristic_pricing_selection_mode", "diverse")),
            exact_pricing_selection_mode=str(config.get("exact_pricing_selection_mode", "reduced_cost")),
            branch_node_heuristic_boost_enabled=_bool_config(config, "branch_node_heuristic_boost_enabled", False),
            branch_node_heuristic_boost_max_labels=int(config.get("branch_node_heuristic_boost_max_labels", 800000)),
            branch_node_heuristic_boost_routes_per_round=int(config.get("branch_node_heuristic_boost_routes_per_round", 1000)),
            branch_node_heuristic_boost_min_depth=int(config.get("branch_node_heuristic_boost_min_depth", 1)),
            exact_pricing_dominance_enabled=_bool_config(
                config,
                "exact_pricing_dominance_enabled",
                _bool_config(config, "exact_pricing_enable_dominance", False),
            ),
            pricing_completion_bound_enabled=_bool_config(config, "pricing_completion_bound_enabled", False),
            ng_dssr_pricing_enabled=_bool_config(config, "ng_dssr_pricing_enabled", False),
            ng_dssr_memory_size=int(config.get("ng_dssr_memory_size", 6)),
            exact_dssr_pricing_enabled=_bool_config(config, "exact_dssr_pricing_enabled", False),
            exact_dssr_initial_memory_size=int(config.get("exact_dssr_initial_memory_size", 6)),
            exact_dssr_max_iterations=int(config.get("exact_dssr_max_iterations", 4)),
            exact_dssr_max_labels=int(config.get("exact_dssr_max_labels", 0)),
            route_enumeration_enabled=_bool_config(config, "route_enumeration_enabled", False),
            route_enumeration_rc_threshold=float(config.get("route_enumeration_rc_threshold", 0.0)),
            route_enumeration_max_routes=int(config.get("route_enumeration_max_routes", 0)),
            restricted_master_heuristic_enabled=_bool_config(config, "restricted_master_heuristic_enabled", False),
            restricted_master_time_limit=float(config.get("restricted_master_time_limit", 20.0)),
            restricted_master_max_routes=int(config.get("restricted_master_max_routes", 4000)),
            restricted_master_max_calls=int(config.get("restricted_master_max_calls", 20)),
            restricted_master_max_depth=int(config.get("restricted_master_max_depth", 3)),
            restricted_master_schedule_aware=_bool_config(config, "restricted_master_schedule_aware", True),
            restricted_master_max_no_good_rounds=int(config.get("restricted_master_max_no_good_rounds", 20)),
            restricted_master_route_pack_conflict_max_events=int(
                config.get("restricted_master_route_pack_conflict_max_events", 2)
            ),
            restricted_master_repair_enabled=_bool_config(config, "restricted_master_repair_enabled", True),
            restricted_master_repair_max_attempts=int(config.get("restricted_master_repair_max_attempts", 3)),
            restricted_master_repair_max_states=int(config.get("restricted_master_repair_max_states", 50000)),
            rmp_params=dict(config.get("rmp_params", {})),
            log_path=log_path,
            solution_path=solution_path,
            seed=int(config["random_seed"]) if config.get("random_seed") is not None else None,
            quiet=bool(args.quiet or config.get("log_level", "progress") == "quiet"),
            branching_strategy=str(config.get("branching_strategy", "3pb")),
            three_pb_pseudocost_candidates=int(config.get("three_pb_pseudocost_candidates", 6)),
            three_pb_fractional_candidates=int(config.get("three_pb_fractional_candidates", 6)),
            three_pb_lp_candidates=int(config.get("three_pb_lp_candidates", 3)),
            three_pb_heuristic_cg_iterations=int(config.get("three_pb_heuristic_cg_iterations", 3)),
            three_pb_heuristic_routes_per_iter=int(config.get("three_pb_heuristic_routes_per_iter", 50)),
            three_pb_heuristic_max_labels=int(config.get("three_pb_heuristic_max_labels", 800)),
            task_vehicle_linking_enabled=_bool_config(config, "task_vehicle_linking_enabled", True),
            robust_capacity_cuts_enabled=_bool_config(config, "robust_capacity_cuts_enabled", True),
            robust_capacity_cut_max_depth=int(config.get("robust_capacity_cut_max_depth", 0)),
            robust_capacity_cut_max_subset_size=int(config.get("robust_capacity_cut_max_subset_size", 5)),
            robust_capacity_cut_max_per_round=int(config.get("robust_capacity_cut_max_per_round", 20)),
            robust_capacity_cut_min_violation=float(config.get("robust_capacity_cut_min_violation", 1.0e-5)),
            robust_capacity_cut_max_rounds_per_node=int(config.get("robust_capacity_cut_max_rounds_per_node", 3)),
            resource_lower_bound_cuts_enabled=_bool_config(config, "resource_lower_bound_cuts_enabled", True),
            resource_cut_max_depth=int(config.get("resource_cut_max_depth", 0)),
            resource_cut_max_subset_size=int(config.get("resource_cut_max_subset_size", 6)),
            resource_cut_max_per_round=int(config.get("resource_cut_max_per_round", 20)),
            resource_cut_min_violation=float(config.get("resource_cut_min_violation", 1.0e-5)),
            resource_cut_max_rounds_per_node=int(config.get("resource_cut_max_rounds_per_node", 3)),
            subset_row_cuts_enabled=_bool_config(config, "subset_row_cuts_enabled", True),
            subset_row_cut_max_depth=int(config.get("subset_row_cut_max_depth", 0)),
            subset_row_cut_max_subset_size=int(config.get("subset_row_cut_max_subset_size", 8)),
            subset_row_cut_max_per_round=int(config.get("subset_row_cut_max_per_round", 20)),
            subset_row_cut_min_violation=float(config.get("subset_row_cut_min_violation", 1.0e-5)),
            subset_row_cut_max_rounds_per_node=int(config.get("subset_row_cut_max_rounds_per_node", 3)),
            subset_row_candidate_top_routes=int(config.get("subset_row_candidate_top_routes", 80)),
            subset_row_candidate_max_sets=int(config.get("subset_row_candidate_max_sets", 500)),
            subset_row_k_values=_int_tuple_config(config, "subset_row_k_values", (2, 3)),
            lm_rank1_cuts_enabled=_bool_config(config, "lm_rank1_cuts_enabled", True),
            lm_rank1_cut_max_depth=int(config.get("lm_rank1_cut_max_depth", 0)),
            lm_rank1_cut_max_subset_size=int(config.get("lm_rank1_cut_max_subset_size", 8)),
            lm_rank1_cut_max_per_round=int(config.get("lm_rank1_cut_max_per_round", 20)),
            lm_rank1_cut_min_violation=float(config.get("lm_rank1_cut_min_violation", 1.0e-5)),
            lm_rank1_cut_max_rounds_per_node=int(config.get("lm_rank1_cut_max_rounds_per_node", 3)),
            lm_rank1_candidate_top_routes=int(config.get("lm_rank1_candidate_top_routes", 100)),
            lm_rank1_candidate_max_sets=int(config.get("lm_rank1_candidate_max_sets", 700)),
            lm_rank1_denominators=_int_tuple_config(config, "lm_rank1_denominators", (3, 4)),
            lm_rank1_memory_size=int(config.get("lm_rank1_memory_size", 4)),
            lm_rank1_max_patterns_per_set=int(config.get("lm_rank1_max_patterns_per_set", 12)),
            schedule_subset_cost_cuts_enabled=_bool_config(config, "schedule_subset_cost_cuts_enabled", False),
            schedule_subset_cost_cut_max_depth=int(config.get("schedule_subset_cost_cut_max_depth", 0)),
            schedule_subset_cost_cut_max_subset_size=int(config.get("schedule_subset_cost_cut_max_subset_size", 8)),
            schedule_subset_cost_cut_max_per_round=int(config.get("schedule_subset_cost_cut_max_per_round", 10)),
            schedule_subset_cost_cut_min_violation=float(config.get("schedule_subset_cost_cut_min_violation", 1.0e-4)),
            schedule_subset_cost_cut_max_rounds_per_node=int(config.get("schedule_subset_cost_cut_max_rounds_per_node", 2)),
            schedule_subset_cost_oracle_max_states=int(config.get("schedule_subset_cost_oracle_max_states", 200000)),
            schedule_subset_cost_candidate_top_tasks=int(config.get("schedule_subset_cost_candidate_top_tasks", 12)),
            schedule_subset_cost_candidate_max_combinations=int(config.get("schedule_subset_cost_candidate_max_combinations", 200)),
            schedule_subset_cost_route_union_top_routes=int(config.get("schedule_subset_cost_route_union_top_routes", 10)),
            schedule_subset_cost_route_union_max_routes=int(config.get("schedule_subset_cost_route_union_max_routes", 4)),
            schedule_capacity_cuts_enabled=_bool_config(config, "schedule_capacity_cuts_enabled", True),
            schedule_capacity_separation_enabled=_bool_config(config, "schedule_capacity_separation_enabled", False),
            schedule_capacity_cut_max_depth=int(config.get("schedule_capacity_cut_max_depth", 0)),
            schedule_capacity_cut_max_subset_size=int(config.get("schedule_capacity_cut_max_subset_size", 10)),
            schedule_capacity_cut_max_per_round=int(config.get("schedule_capacity_cut_max_per_round", 20)),
            schedule_capacity_cut_min_violation=float(config.get("schedule_capacity_cut_min_violation", 1.0e-5)),
            schedule_capacity_cut_max_rounds_per_node=int(config.get("schedule_capacity_cut_max_rounds_per_node", 3)),
            schedule_capacity_oracle_max_states=int(config.get("schedule_capacity_oracle_max_states", 200000)),
            schedule_capacity_candidate_top_tasks=int(config.get("schedule_capacity_candidate_top_tasks", 12)),
            schedule_capacity_candidate_max_combinations=int(config.get("schedule_capacity_candidate_max_combinations", 300)),
            schedule_capacity_route_union_top_routes=int(config.get("schedule_capacity_route_union_top_routes", 8)),
            schedule_capacity_route_union_max_routes=int(config.get("schedule_capacity_route_union_max_routes", 4)),
            root_schedule_capacity_cuts_enabled=_bool_config(config, "root_schedule_capacity_cuts_enabled", False),
            root_schedule_capacity_max_depth=int(config.get("root_schedule_capacity_max_depth", 0)),
            root_schedule_capacity_pair_budget=int(config.get("root_schedule_capacity_pair_budget", 100)),
            root_schedule_capacity_triple_budget=int(config.get("root_schedule_capacity_triple_budget", 50)),
            root_schedule_capacity_oracle_max_states=int(config.get("root_schedule_capacity_oracle_max_states", 200000)),
            root_schedule_capacity_time_budget=float(config.get("root_schedule_capacity_time_budget", 5.0)),
            root_schedule_capacity_min_violation=float(config.get("root_schedule_capacity_min_violation", 1.0e-5)),
            root_schedule_capacity_stop_after_no_add_rounds=int(
                config.get("root_schedule_capacity_stop_after_no_add_rounds", 1)
            ),
            schedule_incompatibility_cuts_enabled=_bool_config(config, "schedule_incompatibility_cuts_enabled", True),
            schedule_incompatibility_cut_max_depth=int(config.get("schedule_incompatibility_cut_max_depth", 2)),
            schedule_incompatibility_cut_max_rounds_per_node=int(
                config.get("schedule_incompatibility_cut_max_rounds_per_node", 2)
            ),
            schedule_incompatibility_cut_max_support_routes=int(
                config.get("schedule_incompatibility_cut_max_support_routes", 80)
            ),
            schedule_incompatibility_cut_max_per_round=int(config.get("schedule_incompatibility_cut_max_per_round", 10)),
            schedule_incompatibility_cut_min_violation=float(config.get("schedule_incompatibility_cut_min_violation", 5.0e-2)),
            schedule_incompatibility_clique_min_size=int(config.get("schedule_incompatibility_clique_min_size", 3)),
            schedule_incompatibility_clique_seed_count=int(config.get("schedule_incompatibility_clique_seed_count", 24)),
            route_set_schedule_packing_cuts_enabled=_bool_config(config, "route_set_schedule_packing_cuts_enabled", True),
            route_set_schedule_packing_cut_max_depth=int(config.get("route_set_schedule_packing_cut_max_depth", 2)),
            route_set_schedule_packing_cut_max_rounds_per_node=int(
                config.get("route_set_schedule_packing_cut_max_rounds_per_node", 2)
            ),
            route_set_schedule_packing_cut_max_support_routes=int(
                config.get("route_set_schedule_packing_cut_max_support_routes", 40)
            ),
            route_set_schedule_packing_cut_max_routes=int(config.get("route_set_schedule_packing_cut_max_routes", 16)),
            route_set_schedule_packing_cut_max_per_round=int(config.get("route_set_schedule_packing_cut_max_per_round", 5)),
            route_set_schedule_packing_cut_min_violation=float(config.get("route_set_schedule_packing_cut_min_violation", 5.0e-2)),
            route_set_schedule_packing_oracle_max_states=int(config.get("route_set_schedule_packing_oracle_max_states", 200000)),
            route_set_schedule_packing_roi_guard_enabled=_bool_config(
                config, "route_set_schedule_packing_roi_guard_enabled", True
            ),
            route_set_schedule_packing_stop_after_no_add_rounds=int(
                config.get("route_set_schedule_packing_stop_after_no_add_rounds", 1)
            ),
            route_set_schedule_packing_min_objective_improvement=float(
                config.get("route_set_schedule_packing_min_objective_improvement", 1.0e-7)
            ),
            route_set_schedule_packing_stop_after_no_improve_rounds=int(
                config.get("route_set_schedule_packing_stop_after_no_improve_rounds", 2)
            ),
            route_set_schedule_packing_global_time_limit_ratio=float(
                config.get("route_set_schedule_packing_global_time_limit_ratio", 0.10)
            ),
            fleet_lower_bound_cuts_enabled=_bool_config(config, "fleet_lower_bound_cuts_enabled", False),
            fleet_lower_bound_oracle_max_states=int(config.get("fleet_lower_bound_oracle_max_states", 500000)),
            schedule_pack_diagnostic_enabled=_bool_config(config, "schedule_pack_diagnostic_enabled", False),
            schedule_pack_diagnostic_max_candidate_routes=int(
                config.get("schedule_pack_diagnostic_max_candidate_routes", 180)
            ),
            schedule_pack_diagnostic_max_columns=int(config.get("schedule_pack_diagnostic_max_columns", 8000)),
            schedule_pack_diagnostic_beam_width=int(config.get("schedule_pack_diagnostic_beam_width", 800)),
            schedule_pack_diagnostic_max_sorties=int(config.get("schedule_pack_diagnostic_max_sorties", 0)),
            schedule_pack_diagnostic_time_limit=float(config.get("schedule_pack_diagnostic_time_limit", 60.0)),
            schedule_pack_pricing_batch_size=int(config.get("schedule_pack_pricing_batch_size", 32)),
            schedule_pack_relaxation_enabled=_bool_config(config, "schedule_pack_relaxation_enabled", False),
            schedule_pack_relaxation_max_depth=int(config.get("schedule_pack_relaxation_max_depth", 2)),
            schedule_pack_relaxation_time_limit=float(config.get("schedule_pack_relaxation_time_limit", 30.0)),
            schedule_pack_relaxation_use_for_priority=_bool_config(
                config,
                "schedule_pack_relaxation_use_for_priority",
                True,
            ),
            schedule_pack_full_pricing_enabled=_bool_config(config, "schedule_pack_full_pricing_enabled", False),
            schedule_pack_full_pricing_max_depth=int(config.get("schedule_pack_full_pricing_max_depth", 0)),
            schedule_pack_full_pricing_max_states=int(config.get("schedule_pack_full_pricing_max_states", 0)),
            schedule_pack_adaptive_enabled=_bool_config(config, "schedule_pack_adaptive_enabled", False),
            schedule_pack_adaptive_gap_abs=float(config.get("schedule_pack_adaptive_gap_abs", 10.0)),
            schedule_pack_adaptive_gap_ratio=float(config.get("schedule_pack_adaptive_gap_ratio", 3.0e-2)),
            schedule_pack_adaptive_skip_if_fathomable=_bool_config(
                config,
                "schedule_pack_adaptive_skip_if_fathomable",
                True,
            ),
            route_enumeration_adaptive_enabled=_bool_config(config, "route_enumeration_adaptive_enabled", False),
            route_enumeration_adaptive_gap_abs=float(config.get("route_enumeration_adaptive_gap_abs", 10.0)),
            route_enumeration_adaptive_gap_ratio=float(config.get("route_enumeration_adaptive_gap_ratio", 3.0e-2)),
            three_pb_candidate_budget_enabled=_bool_config(config, "three_pb_candidate_budget_enabled", False),
            three_pb_root_pseudocost_candidates=int(config.get("three_pb_root_pseudocost_candidates", 6)),
            three_pb_root_fractional_candidates=int(config.get("three_pb_root_fractional_candidates", 6)),
            three_pb_root_lp_candidates=int(config.get("three_pb_root_lp_candidates", 3)),
            three_pb_nonroot_pseudocost_candidates=int(config.get("three_pb_nonroot_pseudocost_candidates", 4)),
            three_pb_nonroot_fractional_candidates=int(config.get("three_pb_nonroot_fractional_candidates", 4)),
            three_pb_nonroot_lp_candidates=int(config.get("three_pb_nonroot_lp_candidates", 2)),
            three_pb_deep_depth=int(config.get("three_pb_deep_depth", 3)),
            three_pb_deep_pseudocost_candidates=int(config.get("three_pb_deep_pseudocost_candidates", 3)),
            three_pb_deep_fractional_candidates=int(config.get("three_pb_deep_fractional_candidates", 3)),
            three_pb_deep_lp_candidates=int(config.get("three_pb_deep_lp_candidates", 1)),
            cut_purge_age=int(config.get("cut_purge_age", 20)),
            cut_purge_slack=float(config.get("cut_purge_slack", 1.0e-5)),
            cut_purge_dual=float(config.get("cut_purge_dual", 1.0e-8)),
            schedule_nogood_purge_enabled=_bool_config(config, "schedule_nogood_purge_enabled", True),
            schedule_nogood_purge_age=int(config.get("schedule_nogood_purge_age", 8)),
            schedule_nogood_purge_slack=float(config.get("schedule_nogood_purge_slack", 1.0e-4)),
            schedule_nogood_purge_dual=float(config.get("schedule_nogood_purge_dual", 1.0e-8)),
        )
        rows.append(result.to_row())
        print(
            f"{result.instance}: status={result.status}, primal={result.primal_bound}, dual={result.dual_bound}, "
            f"gap={result.gap}, diag_dual={result.diagnostic_dual_bound}, diag_gap={result.diagnostic_gap}, "
            f"time={result.solving_time}s, nodes={result.node_count}, "
            f"rmp={result.rmp_solves}, pricing={result.pricing_calls}, routes={result.generated_routes}, "
            f"cuts={result.cuts_added}, crossing={result.crossing_cuts_added}, "
            f"crossing_upgraded={result.crossing_cuts_upgraded}, rci={result.robust_capacity_cuts_added}, "
            f"kpath={result.resource_lower_bound_cuts_added}, pair={result.schedule_pair_conflict_cuts_added}, "
            f"subset_row={result.subset_row_cuts_added}, lm_rank1={result.lm_rank1_cuts_added}, "
            f"sched_cost={result.schedule_subset_cost_cuts_added}, "
            f"clique={result.schedule_clique_conflict_cuts_added}, "
            f"route_pack={result.schedule_route_set_packing_cuts_added}, "
            f"nogood={result.schedule_nogood_cuts_added}, "
            f"sched_cap={result.schedule_capacity_cuts_added}, "
            f"fleet_lb={result.fleet_lower_bound_cuts_added}/{result.fleet_lower_bound_value}, "
            f"fleet_oracle_U={result.fleet_lower_bound_oracle_upper_bound}, "
            f"fleet_oracle_states={result.fleet_lower_bound_oracle_states}, "
            f"fleet_oracle_exact={result.fleet_lower_bound_oracle_exact}, "
            f"rim_calls={result.restricted_master_integer_calls}, rim_feasible={result.restricted_master_integer_feasible}, "
            f"rim_rejected={result.restricted_master_integer_rejected}, "
            f"rim_pair={result.restricted_master_integer_pair_conflict_cuts}, "
            f"rim_route_pack={result.restricted_master_integer_route_set_packing_cuts}, "
            f"rim_ng={result.restricted_master_integer_no_good_cuts}, "
            f"rim_sched_cap={result.restricted_master_integer_schedule_capacity_cuts}, "
            f"rim_repair={result.restricted_master_integer_repair_successes}/{result.restricted_master_integer_repair_attempts}, "
            f"rim_repair_best={result.restricted_master_integer_repair_best_objective}, "
            f"sched_pack_status={result.schedule_pack_diagnostic_status}, "
            f"sched_pack_obj={result.schedule_pack_diagnostic_objective}, "
            f"sched_pack_gap_root={result.schedule_pack_diagnostic_gap_vs_root}, "
            f"sched_pack_cols={result.schedule_pack_diagnostic_columns}, "
            f"sched_pack_relax_calls={result.schedule_pack_relaxation_calls}, "
            f"sched_pack_relax_best={result.schedule_pack_relaxation_best_objective}, "
            f"sched_pack_full_exact={result.schedule_pack_relaxation_full_exact}, "
            f"sched_pack_adapt={result.schedule_pack_adaptive_runs}/{result.schedule_pack_adaptive_decisions}, "
            f"sched_pack_adapt_skip={result.schedule_pack_adaptive_skips}, "
            f"route_enum_adapt={result.route_enumeration_adaptive_runs}/{result.route_enumeration_adaptive_decisions}, "
            f"route_enum_adapt_skip={result.route_enumeration_adaptive_skips}, "
            f"cuts_purged={result.cuts_purged}, branch_test_time={result.branch_testing_time}s",
            flush=True,
        )
    output = ROOT / args.results_csv
    _write_rows(output, rows)
    print(f"clean BPC CSV 已写入：{output}", flush=True)


if __name__ == "__main__":
    main()
