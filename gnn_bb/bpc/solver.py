"""中文摘要：本文件是 clean BPC 对外入口。它读取数据、运行显式 BPC 树，并整理 CSV/JSON 输出字段。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .columns import route_to_json
from .data import BPCData
from .logger import BPCLogger
from .tree import CleanBPCTree, incumbent_to_solution


@dataclass
class BPCResult:
    instance: str
    task_count: int
    vehicle_count: int
    sortie_count: int
    status: str
    primal_bound: float | None
    dual_bound: float | None
    gap: float | None
    diagnostic_dual_bound: float | None
    diagnostic_gap: float | None
    best_open_node_bound: float | None
    pending_node_bound: float | None
    last_certified_node_bound: float | None
    time_to_first_incumbent: float | None
    time_to_best_incumbent: float | None
    open_nodes_remaining: int
    timeout_pending_node_certified: bool | None
    official_bound_available: bool
    solving_time: float
    node_count: int
    rmp_solves: int
    pricing_calls: int
    exact_pricing_calls: int
    branch_nodes: int
    branch_lp_test_rmp_solves: int
    branch_heuristic_test_rmp_solves: int
    branch_heuristic_test_pricing_calls: int
    branch_lp_candidates_tested: int
    branch_heuristic_candidates_tested: int
    branch_testing_time: float
    restricted_master_integer_calls: int
    restricted_master_integer_feasible: int
    restricted_master_integer_time: float
    restricted_master_integer_best_objective: float | None
    restricted_master_integer_raw_best_objective: float | None
    restricted_master_integer_rejected: int
    restricted_master_integer_no_good_cuts: int
    restricted_master_integer_pair_conflict_cuts: int
    restricted_master_integer_route_set_packing_cuts: int
    restricted_master_integer_schedule_capacity_cuts: int
    restricted_master_integer_repair_attempts: int
    restricted_master_integer_repair_successes: int
    restricted_master_integer_repair_time: float
    restricted_master_integer_repair_states: int
    restricted_master_integer_repair_best_objective: float | None
    restricted_master_adaptive_skips: int
    restricted_master_adaptive_time_limit_reductions: int
    restricted_master_adaptive_failure_streak_max: int
    crossing_cuts_added: int
    crossing_cuts_upgraded: int
    subset_row_cuts_added: int
    lm_rank1_cuts_added: int
    robust_capacity_cuts_added: int
    resource_lower_bound_cuts_added: int
    schedule_subset_cost_cuts_added: int
    schedule_pair_conflict_cuts_added: int
    schedule_clique_conflict_cuts_added: int
    schedule_route_set_packing_cuts_added: int
    schedule_nogood_cuts_added: int
    schedule_capacity_cuts_added: int
    root_schedule_capacity_cuts_added: int
    root_schedule_capacity_oracle_queries: int
    root_schedule_capacity_oracle_incomplete: int
    root_schedule_capacity_oracle_time: float
    root_schedule_capacity_cache_hits: int
    root_schedule_capacity_candidates_generated: int
    root_schedule_capacity_candidates_after_precheck: int
    root_schedule_capacity_best_violation: float
    task_schedule_capacity_cuts_added: int
    task_schedule_capacity_candidates_generated: int
    task_schedule_capacity_candidates_after_precheck: int
    task_schedule_capacity_pair_candidates: int
    task_schedule_capacity_triple_candidates: int
    task_schedule_capacity_small_set_candidates: int
    task_schedule_capacity_candidates_by_source: dict[str, int]
    task_schedule_capacity_prechecked_by_source: dict[str, int]
    task_schedule_capacity_oracle_requests: int
    task_schedule_capacity_oracle_computations: int
    task_schedule_capacity_cache_hits: int
    task_schedule_capacity_oracle_incomplete: int
    task_schedule_capacity_exact_not_tight: int
    task_schedule_capacity_exact_tight_not_violated: int
    task_schedule_capacity_violated_candidates: int
    task_schedule_capacity_best_violation: float
    task_schedule_capacity_oracle_time: float
    task_schedule_capacity_oracle_states_total: int
    task_schedule_capacity_oracle_states_max: int
    task_schedule_capacity_cuts_copied_to_all_vehicles: int
    task_schedule_capacity_stopped_by_no_add: int
    task_schedule_capacity_stopped_by_no_improvement: int
    task_schedule_capacity_stopped_by_node_time_budget: int
    task_schedule_capacity_stopped_by_global_time_budget: int
    task_schedule_capacity_branch_signal_candidates: int
    task_schedule_capacity_branch_signal_applied: int
    route_set_schedule_packing_oracle_queries: int
    route_set_schedule_packing_oracle_time: float
    route_set_schedule_packing_cache_hits: int
    route_set_schedule_packing_added_but_no_bound_improvement: int
    weighted_route_schedule_packing_cuts_added: int
    weighted_route_schedule_packing_candidates_generated: int
    weighted_route_schedule_packing_candidates_after_precheck: int
    weighted_route_schedule_packing_candidates_by_source: dict[str, int]
    weighted_route_schedule_packing_candidates_by_alpha: dict[str, int]
    weighted_route_schedule_packing_oracle_requests: int
    weighted_route_schedule_packing_oracle_computations: int
    weighted_route_schedule_packing_cache_hits: int
    weighted_route_schedule_packing_oracle_incomplete: int
    weighted_route_schedule_packing_exact_not_violated: int
    weighted_route_schedule_packing_violated_candidates: int
    weighted_route_schedule_packing_best_violation: float
    weighted_route_schedule_packing_oracle_time: float
    weighted_route_schedule_packing_oracle_states_total: int
    weighted_route_schedule_packing_oracle_states_max: int
    weighted_route_schedule_packing_added_but_no_bound_improvement: int
    weighted_route_schedule_packing_stopped_by_budget: int
    weighted_route_schedule_packing_duplicate_skips: int
    fleet_lower_bound_cuts_added: int
    fleet_lower_bound_value: int
    fleet_lower_bound_oracle_upper_bound: int | None
    fleet_lower_bound_oracle_states: int
    fleet_lower_bound_oracle_exact: bool
    schedule_pack_diagnostic_status: str | None
    schedule_pack_diagnostic_objective: float | None
    schedule_pack_diagnostic_gap_vs_root: float | None
    schedule_pack_diagnostic_columns: int
    schedule_pack_diagnostic_candidate_routes: int
    schedule_pack_diagnostic_generated_states: int
    schedule_pack_diagnostic_time: float
    schedule_pack_relaxation_calls: int
    schedule_pack_relaxation_time: float
    schedule_pack_relaxation_root_objective: float | None
    schedule_pack_relaxation_best_objective: float | None
    schedule_pack_relaxation_best_gap_vs_node: float | None
    schedule_pack_relaxation_candidate_exact: int
    schedule_pack_relaxation_full_exact: int
    schedule_pack_relaxation_full_pricing_states: int
    schedule_pack_relaxation_full_pricing_time: float
    schedule_pack_relaxation_columns: int
    schedule_pack_adaptive_decisions: int
    schedule_pack_adaptive_runs: int
    schedule_pack_adaptive_skips: int
    schedule_pack_adaptive_easy_skips: int
    schedule_pack_adaptive_bound_skips: int
    route_enumeration_adaptive_decisions: int
    route_enumeration_adaptive_runs: int
    route_enumeration_adaptive_skips: int
    route_enumeration_adaptive_easy_skips: int
    route_pool_restart_nodes: int
    route_pool_restart_rounds: int
    route_pool_restart_routes_omitted_total: int
    route_pool_restart_routes_omitted_max: int
    route_pool_restart_pricing_recovered_routes: int
    route_pool_restart_protected_routes_max: int
    route_pool_hygiene_diagnostic_events: int
    route_pool_hygiene_task_set_groups_max: int
    route_pool_hygiene_multi_route_groups_max: int
    route_pool_hygiene_near_duplicate_groups_max: int
    route_pool_hygiene_near_duplicate_routes_max: int
    route_pool_hygiene_max_group_size: int
    route_pool_hygiene_admission_evaluated: int
    route_pool_hygiene_admission_admitted: int
    route_pool_hygiene_admission_filtered: int
    route_pool_hygiene_admission_protected: int
    route_pool_hygiene_admission_forced_exact: int
    cuts_purged: int
    generated_routes: int
    generated_columns: int
    label_pops: int
    generated_labels: int
    cuts_added: int
    root_relaxation: float | None
    incumbent_node: int | None
    log_path: str
    instance_path: str
    seed: int | None

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


def _round(value: Any, digits: int = 6) -> Any:
    if value is None:
        return None
    if isinstance(value, float):
        return round(value, digits)
    return value


def solve_bpc_clean(
    data: BPCData,
    *,
    time_limit: float,
    max_nodes: int,
    pricing_eps: float,
    integer_tol: float,
    max_routes_per_pricing: int,
    max_labels_per_pricing: int,
    rmp_params: dict[str, Any] | None,
    log_path: str | Path | None,
    solution_path: str | Path | None,
    seed: int | None,
    quiet: bool,
    root_max_routes_per_pricing: int = 0,
    heuristic_pricing_enabled: bool = False,
    heuristic_pricing_max_labels: int = 100000,
    heuristic_pricing_routes_per_round: int = 500,
    heuristic_pricing_selection_mode: str = "diverse",
    exact_pricing_selection_mode: str = "reduced_cost",
    branch_node_heuristic_boost_enabled: bool = False,
    branch_node_heuristic_boost_max_labels: int = 800000,
    branch_node_heuristic_boost_routes_per_round: int = 1000,
    branch_node_heuristic_boost_min_depth: int = 1,
    exact_pricing_dominance_enabled: bool = False,
    pricing_completion_bound_enabled: bool = False,
    ng_dssr_pricing_enabled: bool = False,
    ng_dssr_memory_size: int = 6,
    exact_dssr_pricing_enabled: bool = False,
    exact_dssr_initial_memory_size: int = 6,
    exact_dssr_max_iterations: int = 4,
    exact_dssr_max_labels: int = 0,
    route_enumeration_enabled: bool = False,
    route_enumeration_rc_threshold: float = 0.0,
    route_enumeration_max_routes: int = 0,
    persistent_rmp_enabled: bool = False,
    restricted_master_heuristic_enabled: bool = False,
    restricted_master_time_limit: float = 20.0,
    restricted_master_max_routes: int = 4000,
    restricted_master_max_calls: int = 20,
    restricted_master_max_depth: int = 3,
    restricted_master_schedule_aware: bool = True,
    restricted_master_max_no_good_rounds: int = 20,
    restricted_master_route_pack_conflict_max_events: int = 2,
    restricted_master_repair_enabled: bool = True,
    restricted_master_repair_max_attempts: int = 3,
    restricted_master_repair_max_states: int = 50000,
    restricted_master_adaptive_enabled: bool = False,
    restricted_master_adaptive_min_depth: int = 1,
    restricted_master_adaptive_after_failures: int = 2,
    restricted_master_adaptive_reduced_time_limit: float = 5.0,
    restricted_master_adaptive_skip_after_failures: int = 4,
    branching_strategy: str = "3pb",
    three_pb_pseudocost_candidates: int = 6,
    three_pb_fractional_candidates: int = 6,
    three_pb_lp_candidates: int = 3,
    three_pb_heuristic_cg_iterations: int = 3,
    three_pb_heuristic_routes_per_iter: int = 50,
    three_pb_heuristic_max_labels: int = 800,
    task_vehicle_linking_enabled: bool = True,
    robust_capacity_cuts_enabled: bool = True,
    robust_capacity_cut_max_depth: int = 0,
    robust_capacity_cut_max_subset_size: int = 5,
    robust_capacity_cut_max_per_round: int = 20,
    robust_capacity_cut_min_violation: float = 1.0e-5,
    robust_capacity_cut_max_rounds_per_node: int = 3,
    resource_lower_bound_cuts_enabled: bool = True,
    resource_cut_max_depth: int = 0,
    resource_cut_max_subset_size: int = 6,
    resource_cut_max_per_round: int = 20,
    resource_cut_min_violation: float = 1.0e-5,
    resource_cut_max_rounds_per_node: int = 3,
    subset_row_cuts_enabled: bool = True,
    subset_row_cut_max_depth: int = 0,
    subset_row_cut_max_subset_size: int = 8,
    subset_row_cut_max_per_round: int = 20,
    subset_row_cut_min_violation: float = 1.0e-5,
    subset_row_cut_max_rounds_per_node: int = 3,
    subset_row_candidate_top_routes: int = 80,
    subset_row_candidate_max_sets: int = 500,
    subset_row_k_values: tuple[int, ...] | list[int] = (2, 3),
    lm_rank1_cuts_enabled: bool = True,
    lm_rank1_cut_max_depth: int = 0,
    lm_rank1_cut_max_subset_size: int = 8,
    lm_rank1_cut_max_per_round: int = 20,
    lm_rank1_cut_min_violation: float = 1.0e-5,
    lm_rank1_cut_max_rounds_per_node: int = 3,
    lm_rank1_candidate_top_routes: int = 100,
    lm_rank1_candidate_max_sets: int = 700,
    lm_rank1_denominators: tuple[int, ...] | list[int] = (3, 4),
    lm_rank1_memory_size: int = 4,
    lm_rank1_max_patterns_per_set: int = 12,
    schedule_subset_cost_cuts_enabled: bool = False,
    schedule_subset_cost_cut_max_depth: int = 0,
    schedule_subset_cost_cut_max_subset_size: int = 8,
    schedule_subset_cost_cut_max_per_round: int = 10,
    schedule_subset_cost_cut_min_violation: float = 1.0e-4,
    schedule_subset_cost_cut_max_rounds_per_node: int = 2,
    schedule_subset_cost_oracle_max_states: int = 200000,
    schedule_subset_cost_candidate_top_tasks: int = 12,
    schedule_subset_cost_candidate_max_combinations: int = 200,
    schedule_subset_cost_route_union_top_routes: int = 10,
    schedule_subset_cost_route_union_max_routes: int = 4,
    schedule_capacity_cuts_enabled: bool = True,
    schedule_capacity_separation_enabled: bool = False,
    schedule_capacity_cut_max_depth: int = 0,
    schedule_capacity_cut_max_subset_size: int = 10,
    schedule_capacity_cut_max_per_round: int = 20,
    schedule_capacity_cut_min_violation: float = 1.0e-5,
    schedule_capacity_cut_max_rounds_per_node: int = 3,
    schedule_capacity_oracle_max_states: int = 200000,
    schedule_capacity_candidate_top_tasks: int = 12,
    schedule_capacity_candidate_max_combinations: int = 300,
    schedule_capacity_route_union_top_routes: int = 8,
    schedule_capacity_route_union_max_routes: int = 4,
    root_schedule_capacity_cuts_enabled: bool = False,
    root_schedule_capacity_max_depth: int = 0,
    root_schedule_capacity_pair_budget: int = 100,
    root_schedule_capacity_triple_budget: int = 50,
    root_schedule_capacity_oracle_max_states: int = 200000,
    root_schedule_capacity_time_budget: float = 5.0,
    root_schedule_capacity_min_violation: float = 1.0e-5,
    root_schedule_capacity_stop_after_no_add_rounds: int = 1,
    task_schedule_capacity_cuts_enabled: bool | None = None,
    task_schedule_capacity_max_depth: int | None = None,
    task_schedule_capacity_pair_budget: int | None = None,
    task_schedule_capacity_triple_budget: int | None = None,
    task_schedule_capacity_small_set_budget: int = 0,
    task_schedule_capacity_max_subset_size: int = 6,
    task_schedule_capacity_max_cuts_per_round: int = 20,
    task_schedule_capacity_oracle_max_states: int | None = None,
    task_schedule_capacity_node_time_budget: float | None = None,
    task_schedule_capacity_global_time_ratio: float = 0.05,
    task_schedule_capacity_min_violation: float | None = None,
    task_schedule_capacity_copy_to_all_vehicles: bool = False,
    task_schedule_capacity_use_rim_witness: bool = True,
    task_schedule_capacity_use_route_pack_witness: bool = True,
    task_schedule_capacity_use_incompatibility_witness: bool = True,
    task_schedule_capacity_use_top_z_mass: bool = True,
    task_schedule_capacity_use_support_route_union: bool = True,
    task_schedule_capacity_use_time_window_clusters: bool = False,
    task_schedule_capacity_stop_after_no_add_rounds: int | None = None,
    task_schedule_capacity_stop_after_no_improve_rounds: int = 2,
    task_schedule_capacity_cache_incomplete: bool = True,
    task_schedule_capacity_cache_not_tight: bool = True,
    task_schedule_capacity_cache_exact_upper_bound: bool = True,
    task_schedule_capacity_branch_signal_enabled: bool = True,
    task_schedule_capacity_branch_signal_apply_enabled: bool = False,
    schedule_incompatibility_cuts_enabled: bool = True,
    schedule_incompatibility_cut_max_depth: int = 2,
    schedule_incompatibility_cut_max_rounds_per_node: int = 2,
    schedule_incompatibility_cut_max_support_routes: int = 80,
    schedule_incompatibility_cut_max_per_round: int = 10,
    schedule_incompatibility_cut_min_violation: float = 5.0e-2,
    schedule_incompatibility_clique_min_size: int = 3,
    schedule_incompatibility_clique_seed_count: int = 24,
    route_set_schedule_packing_cuts_enabled: bool = True,
    route_set_schedule_packing_cut_max_depth: int = 2,
    route_set_schedule_packing_cut_max_rounds_per_node: int = 2,
    route_set_schedule_packing_cut_max_support_routes: int = 40,
    route_set_schedule_packing_cut_max_routes: int = 16,
    route_set_schedule_packing_cut_max_per_round: int = 5,
    route_set_schedule_packing_cut_min_violation: float = 5.0e-2,
    route_set_schedule_packing_oracle_max_states: int = 200000,
    route_set_schedule_packing_roi_guard_enabled: bool = True,
    route_set_schedule_packing_stop_after_no_add_rounds: int = 1,
    route_set_schedule_packing_min_objective_improvement: float = 1.0e-7,
    route_set_schedule_packing_stop_after_no_improve_rounds: int = 2,
    route_set_schedule_packing_global_time_limit_ratio: float = 0.10,
    weighted_route_schedule_packing_cuts_enabled: bool = False,
    weighted_route_schedule_packing_max_depth: int = 1,
    weighted_route_schedule_packing_max_rounds_per_node: int = 1,
    weighted_route_schedule_packing_max_candidates: int = 20,
    weighted_route_schedule_packing_max_cuts_per_round: int = 5,
    weighted_route_schedule_packing_max_routes: int = 16,
    weighted_route_schedule_packing_oracle_max_states: int = 200000,
    weighted_route_schedule_packing_min_violation: float = 5.0e-2,
    weighted_route_schedule_packing_node_time_budget: float = 5.0,
    weighted_route_schedule_packing_global_time_ratio: float = 0.05,
    fleet_lower_bound_cuts_enabled: bool = False,
    fleet_lower_bound_oracle_max_states: int = 500000,
    schedule_pack_diagnostic_enabled: bool = False,
    schedule_pack_diagnostic_max_candidate_routes: int = 180,
    schedule_pack_diagnostic_max_columns: int = 8000,
    schedule_pack_diagnostic_beam_width: int = 800,
    schedule_pack_diagnostic_max_sorties: int = 0,
    schedule_pack_diagnostic_time_limit: float = 60.0,
    schedule_pack_pricing_batch_size: int = 32,
    schedule_pack_relaxation_enabled: bool = False,
    schedule_pack_relaxation_max_depth: int = 2,
    schedule_pack_relaxation_time_limit: float = 30.0,
    schedule_pack_relaxation_use_for_priority: bool = True,
    schedule_pack_full_pricing_enabled: bool = False,
    schedule_pack_full_pricing_max_depth: int = 0,
    schedule_pack_full_pricing_max_states: int = 0,
    schedule_pack_adaptive_enabled: bool = False,
    schedule_pack_adaptive_gap_abs: float = 10.0,
    schedule_pack_adaptive_gap_ratio: float = 3.0e-2,
    schedule_pack_adaptive_skip_if_fathomable: bool = True,
    route_enumeration_adaptive_enabled: bool = False,
    route_enumeration_adaptive_gap_abs: float = 10.0,
    route_enumeration_adaptive_gap_ratio: float = 3.0e-2,
    route_pool_hygiene_diagnostics_enabled: bool = False,
    route_pool_hygiene_diagnostics_min_routes: int = 0,
    route_pool_hygiene_near_duplicate_abs_tol: float = 1.0e-6,
    route_pool_hygiene_near_duplicate_rel_tol: float = 1.0e-4,
    route_pool_hygiene_sample_groups: int = 5,
    route_pool_hygiene_admission_enabled: bool = False,
    route_pool_hygiene_admission_max_per_task_set: int = 0,
    route_pool_hygiene_admission_min_depth: int = 0,
    route_pool_hygiene_admission_protect_active_task_sets: bool = True,
    route_pool_hygiene_admission_protect_cut_task_sets: bool = True,
    route_pool_hygiene_admission_protect_incumbent_task_sets: bool = True,
    route_pool_hygiene_admission_protect_branch_task_sets: bool = True,
    route_pool_restart_enabled: bool = False,
    route_pool_restart_max_routes: int = 0,
    route_pool_restart_min_global_routes: int = 0,
    route_pool_restart_keep_recent_rounds: int = 2,
    route_pool_restart_max_routes_per_task_set: int = 6,
    route_pool_restart_active_value_tol: float = 1.0e-8,
    route_pool_restart_keep_cut_signatures: bool = False,
    route_pool_restart_cleanup_enabled: bool = False,
    three_pb_candidate_budget_enabled: bool = False,
    three_pb_root_pseudocost_candidates: int = 6,
    three_pb_root_fractional_candidates: int = 6,
    three_pb_root_lp_candidates: int = 3,
    three_pb_nonroot_pseudocost_candidates: int = 4,
    three_pb_nonroot_fractional_candidates: int = 4,
    three_pb_nonroot_lp_candidates: int = 2,
    three_pb_deep_depth: int = 3,
    three_pb_deep_pseudocost_candidates: int = 3,
    three_pb_deep_fractional_candidates: int = 3,
    three_pb_deep_lp_candidates: int = 1,
    cut_purge_age: int = 20,
    cut_purge_slack: float = 1.0e-5,
    cut_purge_dual: float = 1.0e-8,
    schedule_nogood_purge_enabled: bool = True,
    schedule_nogood_purge_age: int = 8,
    schedule_nogood_purge_slack: float = 1.0e-4,
    schedule_nogood_purge_dual: float = 1.0e-8,
) -> BPCResult:
    logger = BPCLogger(log_path, console=not quiet)
    try:
        tree = CleanBPCTree(
            data,
            time_limit=time_limit,
            max_nodes=max_nodes,
            eps=pricing_eps,
            integer_tol=integer_tol,
            max_routes_per_pricing=max_routes_per_pricing,
            max_labels_per_pricing=max_labels_per_pricing,
            rmp_params=rmp_params,
            logger=logger,
            root_max_routes_per_pricing=root_max_routes_per_pricing,
            heuristic_pricing_enabled=heuristic_pricing_enabled,
            heuristic_pricing_max_labels=heuristic_pricing_max_labels,
            heuristic_pricing_routes_per_round=heuristic_pricing_routes_per_round,
            heuristic_pricing_selection_mode=heuristic_pricing_selection_mode,
            exact_pricing_selection_mode=exact_pricing_selection_mode,
            branch_node_heuristic_boost_enabled=branch_node_heuristic_boost_enabled,
            branch_node_heuristic_boost_max_labels=branch_node_heuristic_boost_max_labels,
            branch_node_heuristic_boost_routes_per_round=branch_node_heuristic_boost_routes_per_round,
            branch_node_heuristic_boost_min_depth=branch_node_heuristic_boost_min_depth,
            exact_pricing_dominance_enabled=exact_pricing_dominance_enabled,
            pricing_completion_bound_enabled=pricing_completion_bound_enabled,
            ng_dssr_pricing_enabled=ng_dssr_pricing_enabled,
            ng_dssr_memory_size=ng_dssr_memory_size,
            exact_dssr_pricing_enabled=exact_dssr_pricing_enabled,
            exact_dssr_initial_memory_size=exact_dssr_initial_memory_size,
            exact_dssr_max_iterations=exact_dssr_max_iterations,
            exact_dssr_max_labels=exact_dssr_max_labels,
            route_enumeration_enabled=route_enumeration_enabled,
            route_enumeration_rc_threshold=route_enumeration_rc_threshold,
            route_enumeration_max_routes=route_enumeration_max_routes,
            persistent_rmp_enabled=persistent_rmp_enabled,
            restricted_master_heuristic_enabled=restricted_master_heuristic_enabled,
            restricted_master_time_limit=restricted_master_time_limit,
            restricted_master_max_routes=restricted_master_max_routes,
            restricted_master_max_calls=restricted_master_max_calls,
            restricted_master_max_depth=restricted_master_max_depth,
            restricted_master_schedule_aware=restricted_master_schedule_aware,
            restricted_master_max_no_good_rounds=restricted_master_max_no_good_rounds,
            restricted_master_route_pack_conflict_max_events=restricted_master_route_pack_conflict_max_events,
            restricted_master_repair_enabled=restricted_master_repair_enabled,
            restricted_master_repair_max_attempts=restricted_master_repair_max_attempts,
            restricted_master_repair_max_states=restricted_master_repair_max_states,
            restricted_master_adaptive_enabled=restricted_master_adaptive_enabled,
            restricted_master_adaptive_min_depth=restricted_master_adaptive_min_depth,
            restricted_master_adaptive_after_failures=restricted_master_adaptive_after_failures,
            restricted_master_adaptive_reduced_time_limit=restricted_master_adaptive_reduced_time_limit,
            restricted_master_adaptive_skip_after_failures=restricted_master_adaptive_skip_after_failures,
            branching_strategy=branching_strategy,
            three_pb_pseudocost_candidates=three_pb_pseudocost_candidates,
            three_pb_fractional_candidates=three_pb_fractional_candidates,
            three_pb_lp_candidates=three_pb_lp_candidates,
            three_pb_heuristic_cg_iterations=three_pb_heuristic_cg_iterations,
            three_pb_heuristic_routes_per_iter=three_pb_heuristic_routes_per_iter,
            three_pb_heuristic_max_labels=three_pb_heuristic_max_labels,
            task_vehicle_linking_enabled=task_vehicle_linking_enabled,
            robust_capacity_cuts_enabled=robust_capacity_cuts_enabled,
            robust_capacity_cut_max_depth=robust_capacity_cut_max_depth,
            robust_capacity_cut_max_subset_size=robust_capacity_cut_max_subset_size,
            robust_capacity_cut_max_per_round=robust_capacity_cut_max_per_round,
            robust_capacity_cut_min_violation=robust_capacity_cut_min_violation,
            robust_capacity_cut_max_rounds_per_node=robust_capacity_cut_max_rounds_per_node,
            resource_lower_bound_cuts_enabled=resource_lower_bound_cuts_enabled,
            resource_cut_max_depth=resource_cut_max_depth,
            resource_cut_max_subset_size=resource_cut_max_subset_size,
            resource_cut_max_per_round=resource_cut_max_per_round,
            resource_cut_min_violation=resource_cut_min_violation,
            resource_cut_max_rounds_per_node=resource_cut_max_rounds_per_node,
            subset_row_cuts_enabled=subset_row_cuts_enabled,
            subset_row_cut_max_depth=subset_row_cut_max_depth,
            subset_row_cut_max_subset_size=subset_row_cut_max_subset_size,
            subset_row_cut_max_per_round=subset_row_cut_max_per_round,
            subset_row_cut_min_violation=subset_row_cut_min_violation,
            subset_row_cut_max_rounds_per_node=subset_row_cut_max_rounds_per_node,
            subset_row_candidate_top_routes=subset_row_candidate_top_routes,
            subset_row_candidate_max_sets=subset_row_candidate_max_sets,
            subset_row_k_values=subset_row_k_values,
            lm_rank1_cuts_enabled=lm_rank1_cuts_enabled,
            lm_rank1_cut_max_depth=lm_rank1_cut_max_depth,
            lm_rank1_cut_max_subset_size=lm_rank1_cut_max_subset_size,
            lm_rank1_cut_max_per_round=lm_rank1_cut_max_per_round,
            lm_rank1_cut_min_violation=lm_rank1_cut_min_violation,
            lm_rank1_cut_max_rounds_per_node=lm_rank1_cut_max_rounds_per_node,
            lm_rank1_candidate_top_routes=lm_rank1_candidate_top_routes,
            lm_rank1_candidate_max_sets=lm_rank1_candidate_max_sets,
            lm_rank1_denominators=lm_rank1_denominators,
            lm_rank1_memory_size=lm_rank1_memory_size,
            lm_rank1_max_patterns_per_set=lm_rank1_max_patterns_per_set,
            schedule_subset_cost_cuts_enabled=schedule_subset_cost_cuts_enabled,
            schedule_subset_cost_cut_max_depth=schedule_subset_cost_cut_max_depth,
            schedule_subset_cost_cut_max_subset_size=schedule_subset_cost_cut_max_subset_size,
            schedule_subset_cost_cut_max_per_round=schedule_subset_cost_cut_max_per_round,
            schedule_subset_cost_cut_min_violation=schedule_subset_cost_cut_min_violation,
            schedule_subset_cost_cut_max_rounds_per_node=schedule_subset_cost_cut_max_rounds_per_node,
            schedule_subset_cost_oracle_max_states=schedule_subset_cost_oracle_max_states,
            schedule_subset_cost_candidate_top_tasks=schedule_subset_cost_candidate_top_tasks,
            schedule_subset_cost_candidate_max_combinations=schedule_subset_cost_candidate_max_combinations,
            schedule_subset_cost_route_union_top_routes=schedule_subset_cost_route_union_top_routes,
            schedule_subset_cost_route_union_max_routes=schedule_subset_cost_route_union_max_routes,
            schedule_capacity_cuts_enabled=schedule_capacity_cuts_enabled,
            schedule_capacity_separation_enabled=schedule_capacity_separation_enabled,
            schedule_capacity_cut_max_depth=schedule_capacity_cut_max_depth,
            schedule_capacity_cut_max_subset_size=schedule_capacity_cut_max_subset_size,
            schedule_capacity_cut_max_per_round=schedule_capacity_cut_max_per_round,
            schedule_capacity_cut_min_violation=schedule_capacity_cut_min_violation,
            schedule_capacity_cut_max_rounds_per_node=schedule_capacity_cut_max_rounds_per_node,
            schedule_capacity_oracle_max_states=schedule_capacity_oracle_max_states,
            schedule_capacity_candidate_top_tasks=schedule_capacity_candidate_top_tasks,
            schedule_capacity_candidate_max_combinations=schedule_capacity_candidate_max_combinations,
            schedule_capacity_route_union_top_routes=schedule_capacity_route_union_top_routes,
            schedule_capacity_route_union_max_routes=schedule_capacity_route_union_max_routes,
            root_schedule_capacity_cuts_enabled=root_schedule_capacity_cuts_enabled,
            root_schedule_capacity_max_depth=root_schedule_capacity_max_depth,
            root_schedule_capacity_pair_budget=root_schedule_capacity_pair_budget,
            root_schedule_capacity_triple_budget=root_schedule_capacity_triple_budget,
            root_schedule_capacity_oracle_max_states=root_schedule_capacity_oracle_max_states,
            root_schedule_capacity_time_budget=root_schedule_capacity_time_budget,
            root_schedule_capacity_min_violation=root_schedule_capacity_min_violation,
            root_schedule_capacity_stop_after_no_add_rounds=root_schedule_capacity_stop_after_no_add_rounds,
            task_schedule_capacity_cuts_enabled=task_schedule_capacity_cuts_enabled,
            task_schedule_capacity_max_depth=task_schedule_capacity_max_depth,
            task_schedule_capacity_pair_budget=task_schedule_capacity_pair_budget,
            task_schedule_capacity_triple_budget=task_schedule_capacity_triple_budget,
            task_schedule_capacity_small_set_budget=task_schedule_capacity_small_set_budget,
            task_schedule_capacity_max_subset_size=task_schedule_capacity_max_subset_size,
            task_schedule_capacity_max_cuts_per_round=task_schedule_capacity_max_cuts_per_round,
            task_schedule_capacity_oracle_max_states=task_schedule_capacity_oracle_max_states,
            task_schedule_capacity_node_time_budget=task_schedule_capacity_node_time_budget,
            task_schedule_capacity_global_time_ratio=task_schedule_capacity_global_time_ratio,
            task_schedule_capacity_min_violation=task_schedule_capacity_min_violation,
            task_schedule_capacity_copy_to_all_vehicles=task_schedule_capacity_copy_to_all_vehicles,
            task_schedule_capacity_use_rim_witness=task_schedule_capacity_use_rim_witness,
            task_schedule_capacity_use_route_pack_witness=task_schedule_capacity_use_route_pack_witness,
            task_schedule_capacity_use_incompatibility_witness=task_schedule_capacity_use_incompatibility_witness,
            task_schedule_capacity_use_top_z_mass=task_schedule_capacity_use_top_z_mass,
            task_schedule_capacity_use_support_route_union=task_schedule_capacity_use_support_route_union,
            task_schedule_capacity_use_time_window_clusters=task_schedule_capacity_use_time_window_clusters,
            task_schedule_capacity_stop_after_no_add_rounds=task_schedule_capacity_stop_after_no_add_rounds,
            task_schedule_capacity_stop_after_no_improve_rounds=task_schedule_capacity_stop_after_no_improve_rounds,
            task_schedule_capacity_cache_incomplete=task_schedule_capacity_cache_incomplete,
            task_schedule_capacity_cache_not_tight=task_schedule_capacity_cache_not_tight,
            task_schedule_capacity_cache_exact_upper_bound=task_schedule_capacity_cache_exact_upper_bound,
            task_schedule_capacity_branch_signal_enabled=task_schedule_capacity_branch_signal_enabled,
            task_schedule_capacity_branch_signal_apply_enabled=task_schedule_capacity_branch_signal_apply_enabled,
            schedule_incompatibility_cuts_enabled=schedule_incompatibility_cuts_enabled,
            schedule_incompatibility_cut_max_depth=schedule_incompatibility_cut_max_depth,
            schedule_incompatibility_cut_max_rounds_per_node=schedule_incompatibility_cut_max_rounds_per_node,
            schedule_incompatibility_cut_max_support_routes=schedule_incompatibility_cut_max_support_routes,
            schedule_incompatibility_cut_max_per_round=schedule_incompatibility_cut_max_per_round,
            schedule_incompatibility_cut_min_violation=schedule_incompatibility_cut_min_violation,
            schedule_incompatibility_clique_min_size=schedule_incompatibility_clique_min_size,
            schedule_incompatibility_clique_seed_count=schedule_incompatibility_clique_seed_count,
            route_set_schedule_packing_cuts_enabled=route_set_schedule_packing_cuts_enabled,
            route_set_schedule_packing_cut_max_depth=route_set_schedule_packing_cut_max_depth,
            route_set_schedule_packing_cut_max_rounds_per_node=route_set_schedule_packing_cut_max_rounds_per_node,
            route_set_schedule_packing_cut_max_support_routes=route_set_schedule_packing_cut_max_support_routes,
            route_set_schedule_packing_cut_max_routes=route_set_schedule_packing_cut_max_routes,
            route_set_schedule_packing_cut_max_per_round=route_set_schedule_packing_cut_max_per_round,
            route_set_schedule_packing_cut_min_violation=route_set_schedule_packing_cut_min_violation,
            route_set_schedule_packing_oracle_max_states=route_set_schedule_packing_oracle_max_states,
            route_set_schedule_packing_roi_guard_enabled=route_set_schedule_packing_roi_guard_enabled,
            route_set_schedule_packing_stop_after_no_add_rounds=route_set_schedule_packing_stop_after_no_add_rounds,
            route_set_schedule_packing_min_objective_improvement=route_set_schedule_packing_min_objective_improvement,
            route_set_schedule_packing_stop_after_no_improve_rounds=route_set_schedule_packing_stop_after_no_improve_rounds,
            route_set_schedule_packing_global_time_limit_ratio=route_set_schedule_packing_global_time_limit_ratio,
            weighted_route_schedule_packing_cuts_enabled=weighted_route_schedule_packing_cuts_enabled,
            weighted_route_schedule_packing_max_depth=weighted_route_schedule_packing_max_depth,
            weighted_route_schedule_packing_max_rounds_per_node=weighted_route_schedule_packing_max_rounds_per_node,
            weighted_route_schedule_packing_max_candidates=weighted_route_schedule_packing_max_candidates,
            weighted_route_schedule_packing_max_cuts_per_round=weighted_route_schedule_packing_max_cuts_per_round,
            weighted_route_schedule_packing_max_routes=weighted_route_schedule_packing_max_routes,
            weighted_route_schedule_packing_oracle_max_states=weighted_route_schedule_packing_oracle_max_states,
            weighted_route_schedule_packing_min_violation=weighted_route_schedule_packing_min_violation,
            weighted_route_schedule_packing_node_time_budget=weighted_route_schedule_packing_node_time_budget,
            weighted_route_schedule_packing_global_time_ratio=weighted_route_schedule_packing_global_time_ratio,
            fleet_lower_bound_cuts_enabled=fleet_lower_bound_cuts_enabled,
            fleet_lower_bound_oracle_max_states=fleet_lower_bound_oracle_max_states,
            schedule_pack_diagnostic_enabled=schedule_pack_diagnostic_enabled,
            schedule_pack_diagnostic_max_candidate_routes=schedule_pack_diagnostic_max_candidate_routes,
            schedule_pack_diagnostic_max_columns=schedule_pack_diagnostic_max_columns,
            schedule_pack_diagnostic_beam_width=schedule_pack_diagnostic_beam_width,
            schedule_pack_diagnostic_max_sorties=schedule_pack_diagnostic_max_sorties,
            schedule_pack_diagnostic_time_limit=schedule_pack_diagnostic_time_limit,
            schedule_pack_pricing_batch_size=schedule_pack_pricing_batch_size,
            schedule_pack_relaxation_enabled=schedule_pack_relaxation_enabled,
            schedule_pack_relaxation_max_depth=schedule_pack_relaxation_max_depth,
            schedule_pack_relaxation_time_limit=schedule_pack_relaxation_time_limit,
            schedule_pack_relaxation_use_for_priority=schedule_pack_relaxation_use_for_priority,
            schedule_pack_full_pricing_enabled=schedule_pack_full_pricing_enabled,
            schedule_pack_full_pricing_max_depth=schedule_pack_full_pricing_max_depth,
            schedule_pack_full_pricing_max_states=schedule_pack_full_pricing_max_states,
            schedule_pack_adaptive_enabled=schedule_pack_adaptive_enabled,
            schedule_pack_adaptive_gap_abs=schedule_pack_adaptive_gap_abs,
            schedule_pack_adaptive_gap_ratio=schedule_pack_adaptive_gap_ratio,
            schedule_pack_adaptive_skip_if_fathomable=schedule_pack_adaptive_skip_if_fathomable,
            route_enumeration_adaptive_enabled=route_enumeration_adaptive_enabled,
            route_enumeration_adaptive_gap_abs=route_enumeration_adaptive_gap_abs,
            route_enumeration_adaptive_gap_ratio=route_enumeration_adaptive_gap_ratio,
            route_pool_hygiene_diagnostics_enabled=route_pool_hygiene_diagnostics_enabled,
            route_pool_hygiene_diagnostics_min_routes=route_pool_hygiene_diagnostics_min_routes,
            route_pool_hygiene_near_duplicate_abs_tol=route_pool_hygiene_near_duplicate_abs_tol,
            route_pool_hygiene_near_duplicate_rel_tol=route_pool_hygiene_near_duplicate_rel_tol,
            route_pool_hygiene_sample_groups=route_pool_hygiene_sample_groups,
            route_pool_hygiene_admission_enabled=route_pool_hygiene_admission_enabled,
            route_pool_hygiene_admission_max_per_task_set=route_pool_hygiene_admission_max_per_task_set,
            route_pool_hygiene_admission_min_depth=route_pool_hygiene_admission_min_depth,
            route_pool_hygiene_admission_protect_active_task_sets=(
                route_pool_hygiene_admission_protect_active_task_sets
            ),
            route_pool_hygiene_admission_protect_cut_task_sets=route_pool_hygiene_admission_protect_cut_task_sets,
            route_pool_hygiene_admission_protect_incumbent_task_sets=(
                route_pool_hygiene_admission_protect_incumbent_task_sets
            ),
            route_pool_hygiene_admission_protect_branch_task_sets=(
                route_pool_hygiene_admission_protect_branch_task_sets
            ),
            route_pool_restart_enabled=route_pool_restart_enabled,
            route_pool_restart_max_routes=route_pool_restart_max_routes,
            route_pool_restart_min_global_routes=route_pool_restart_min_global_routes,
            route_pool_restart_keep_recent_rounds=route_pool_restart_keep_recent_rounds,
            route_pool_restart_max_routes_per_task_set=route_pool_restart_max_routes_per_task_set,
            route_pool_restart_active_value_tol=route_pool_restart_active_value_tol,
            route_pool_restart_keep_cut_signatures=route_pool_restart_keep_cut_signatures,
            route_pool_restart_cleanup_enabled=route_pool_restart_cleanup_enabled,
            three_pb_candidate_budget_enabled=three_pb_candidate_budget_enabled,
            three_pb_root_pseudocost_candidates=three_pb_root_pseudocost_candidates,
            three_pb_root_fractional_candidates=three_pb_root_fractional_candidates,
            three_pb_root_lp_candidates=three_pb_root_lp_candidates,
            three_pb_nonroot_pseudocost_candidates=three_pb_nonroot_pseudocost_candidates,
            three_pb_nonroot_fractional_candidates=three_pb_nonroot_fractional_candidates,
            three_pb_nonroot_lp_candidates=three_pb_nonroot_lp_candidates,
            three_pb_deep_depth=three_pb_deep_depth,
            three_pb_deep_pseudocost_candidates=three_pb_deep_pseudocost_candidates,
            three_pb_deep_fractional_candidates=three_pb_deep_fractional_candidates,
            three_pb_deep_lp_candidates=three_pb_deep_lp_candidates,
            cut_purge_age=cut_purge_age,
            cut_purge_slack=cut_purge_slack,
            cut_purge_dual=cut_purge_dual,
            schedule_nogood_purge_enabled=schedule_nogood_purge_enabled,
            schedule_nogood_purge_age=schedule_nogood_purge_age,
            schedule_nogood_purge_slack=schedule_nogood_purge_slack,
            schedule_nogood_purge_dual=schedule_nogood_purge_dual,
        )
        tree_result = tree.solve()
    finally:
        logger.close()

    generated_columns = len(tree_result.routes) * len(data.vehicles)
    result = BPCResult(
        instance=data.name,
        task_count=len(data.tasks),
        vehicle_count=len(data.vehicles),
        sortie_count=data.sortie_limit,
        status=tree_result.status,
        primal_bound=_round(tree_result.primal_bound),
        dual_bound=_round(tree_result.dual_bound),
        gap=_round(tree_result.gap),
        diagnostic_dual_bound=_round(tree_result.stats.diagnostic_dual_bound),
        diagnostic_gap=_round(tree_result.stats.diagnostic_gap),
        best_open_node_bound=_round(tree_result.stats.best_open_node_bound),
        pending_node_bound=_round(tree_result.stats.pending_node_bound),
        last_certified_node_bound=_round(tree_result.stats.last_certified_node_bound),
        time_to_first_incumbent=_round(tree_result.stats.time_to_first_incumbent),
        time_to_best_incumbent=_round(tree_result.stats.time_to_best_incumbent),
        open_nodes_remaining=tree_result.stats.open_nodes_remaining,
        timeout_pending_node_certified=tree_result.stats.timeout_pending_node_certified,
        official_bound_available=tree_result.stats.official_bound_available,
        solving_time=_round(tree_result.solving_time),
        node_count=tree_result.node_count,
        rmp_solves=tree_result.stats.rmp_solves,
        pricing_calls=tree_result.stats.pricing_calls,
        exact_pricing_calls=tree_result.stats.exact_pricing_calls,
        branch_nodes=tree_result.stats.branch_nodes,
        branch_lp_test_rmp_solves=tree_result.stats.branch_lp_test_rmp_solves,
        branch_heuristic_test_rmp_solves=tree_result.stats.branch_heuristic_test_rmp_solves,
        branch_heuristic_test_pricing_calls=tree_result.stats.branch_heuristic_test_pricing_calls,
        branch_lp_candidates_tested=tree_result.stats.branch_lp_candidates_tested,
        branch_heuristic_candidates_tested=tree_result.stats.branch_heuristic_candidates_tested,
        branch_testing_time=_round(tree_result.stats.branch_testing_time),
        restricted_master_integer_calls=tree_result.stats.restricted_master_integer_calls,
        restricted_master_integer_feasible=tree_result.stats.restricted_master_integer_feasible,
        restricted_master_integer_time=_round(tree_result.stats.restricted_master_integer_time),
        restricted_master_integer_best_objective=_round(tree_result.stats.restricted_master_integer_best_objective),
        restricted_master_integer_raw_best_objective=_round(tree_result.stats.restricted_master_integer_raw_best_objective),
        restricted_master_integer_rejected=tree_result.stats.restricted_master_integer_rejected,
        restricted_master_integer_no_good_cuts=tree_result.stats.restricted_master_integer_no_good_cuts,
        restricted_master_integer_pair_conflict_cuts=tree_result.stats.restricted_master_integer_pair_conflict_cuts,
        restricted_master_integer_route_set_packing_cuts=tree_result.stats.restricted_master_integer_route_set_packing_cuts,
        restricted_master_integer_schedule_capacity_cuts=tree_result.stats.restricted_master_integer_schedule_capacity_cuts,
        restricted_master_integer_repair_attempts=tree_result.stats.restricted_master_integer_repair_attempts,
        restricted_master_integer_repair_successes=tree_result.stats.restricted_master_integer_repair_successes,
        restricted_master_integer_repair_time=_round(tree_result.stats.restricted_master_integer_repair_time),
        restricted_master_integer_repair_states=tree_result.stats.restricted_master_integer_repair_states,
        restricted_master_integer_repair_best_objective=_round(tree_result.stats.restricted_master_integer_repair_best_objective),
        restricted_master_adaptive_skips=tree_result.stats.restricted_master_adaptive_skips,
        restricted_master_adaptive_time_limit_reductions=(
            tree_result.stats.restricted_master_adaptive_time_limit_reductions
        ),
        restricted_master_adaptive_failure_streak_max=tree_result.stats.restricted_master_adaptive_failure_streak_max,
        crossing_cuts_added=tree_result.stats.crossing_cuts_added,
        crossing_cuts_upgraded=tree_result.stats.crossing_cuts_upgraded,
        subset_row_cuts_added=tree_result.stats.subset_row_cuts_added,
        lm_rank1_cuts_added=tree_result.stats.lm_rank1_cuts_added,
        robust_capacity_cuts_added=tree_result.stats.robust_capacity_cuts_added,
        resource_lower_bound_cuts_added=tree_result.stats.resource_lower_bound_cuts_added,
        schedule_subset_cost_cuts_added=tree_result.stats.schedule_subset_cost_cuts_added,
        schedule_pair_conflict_cuts_added=tree_result.stats.schedule_pair_conflict_cuts_added,
        schedule_clique_conflict_cuts_added=tree_result.stats.schedule_clique_conflict_cuts_added,
        schedule_route_set_packing_cuts_added=tree_result.stats.schedule_route_set_packing_cuts_added,
        schedule_nogood_cuts_added=tree_result.stats.schedule_nogood_cuts_added,
        schedule_capacity_cuts_added=tree_result.stats.schedule_capacity_cuts_added,
        root_schedule_capacity_cuts_added=tree_result.stats.root_schedule_capacity_cuts_added,
        root_schedule_capacity_oracle_queries=tree_result.stats.root_schedule_capacity_oracle_queries,
        root_schedule_capacity_oracle_incomplete=tree_result.stats.root_schedule_capacity_oracle_incomplete,
        root_schedule_capacity_oracle_time=_round(tree_result.stats.root_schedule_capacity_oracle_time),
        root_schedule_capacity_cache_hits=tree_result.stats.root_schedule_capacity_cache_hits,
        root_schedule_capacity_candidates_generated=tree_result.stats.root_schedule_capacity_candidates_generated,
        root_schedule_capacity_candidates_after_precheck=tree_result.stats.root_schedule_capacity_candidates_after_precheck,
        root_schedule_capacity_best_violation=_round(tree_result.stats.root_schedule_capacity_best_violation, 9),
        task_schedule_capacity_cuts_added=tree_result.stats.task_schedule_capacity_cuts_added,
        task_schedule_capacity_candidates_generated=tree_result.stats.task_schedule_capacity_candidates_generated,
        task_schedule_capacity_candidates_after_precheck=tree_result.stats.task_schedule_capacity_candidates_after_precheck,
        task_schedule_capacity_pair_candidates=tree_result.stats.task_schedule_capacity_pair_candidates,
        task_schedule_capacity_triple_candidates=tree_result.stats.task_schedule_capacity_triple_candidates,
        task_schedule_capacity_small_set_candidates=tree_result.stats.task_schedule_capacity_small_set_candidates,
        task_schedule_capacity_candidates_by_source=dict(tree_result.stats.task_schedule_capacity_candidates_by_source),
        task_schedule_capacity_prechecked_by_source=dict(tree_result.stats.task_schedule_capacity_prechecked_by_source),
        task_schedule_capacity_oracle_requests=tree_result.stats.task_schedule_capacity_oracle_requests,
        task_schedule_capacity_oracle_computations=tree_result.stats.task_schedule_capacity_oracle_computations,
        task_schedule_capacity_cache_hits=tree_result.stats.task_schedule_capacity_cache_hits,
        task_schedule_capacity_oracle_incomplete=tree_result.stats.task_schedule_capacity_oracle_incomplete,
        task_schedule_capacity_exact_not_tight=tree_result.stats.task_schedule_capacity_exact_not_tight,
        task_schedule_capacity_exact_tight_not_violated=tree_result.stats.task_schedule_capacity_exact_tight_not_violated,
        task_schedule_capacity_violated_candidates=tree_result.stats.task_schedule_capacity_violated_candidates,
        task_schedule_capacity_best_violation=_round(tree_result.stats.task_schedule_capacity_best_violation, 9),
        task_schedule_capacity_oracle_time=_round(tree_result.stats.task_schedule_capacity_oracle_time),
        task_schedule_capacity_oracle_states_total=tree_result.stats.task_schedule_capacity_oracle_states_total,
        task_schedule_capacity_oracle_states_max=tree_result.stats.task_schedule_capacity_oracle_states_max,
        task_schedule_capacity_cuts_copied_to_all_vehicles=tree_result.stats.task_schedule_capacity_cuts_copied_to_all_vehicles,
        task_schedule_capacity_stopped_by_no_add=tree_result.stats.task_schedule_capacity_stopped_by_no_add,
        task_schedule_capacity_stopped_by_no_improvement=tree_result.stats.task_schedule_capacity_stopped_by_no_improvement,
        task_schedule_capacity_stopped_by_node_time_budget=tree_result.stats.task_schedule_capacity_stopped_by_node_time_budget,
        task_schedule_capacity_stopped_by_global_time_budget=tree_result.stats.task_schedule_capacity_stopped_by_global_time_budget,
        task_schedule_capacity_branch_signal_candidates=tree_result.stats.task_schedule_capacity_branch_signal_candidates,
        task_schedule_capacity_branch_signal_applied=tree_result.stats.task_schedule_capacity_branch_signal_applied,
        route_set_schedule_packing_oracle_queries=tree_result.stats.route_set_schedule_packing_oracle_queries,
        route_set_schedule_packing_oracle_time=_round(tree_result.stats.route_set_schedule_packing_oracle_time),
        route_set_schedule_packing_cache_hits=tree_result.stats.route_set_schedule_packing_cache_hits,
        route_set_schedule_packing_added_but_no_bound_improvement=(
            tree_result.stats.route_set_schedule_packing_added_but_no_bound_improvement
        ),
        weighted_route_schedule_packing_cuts_added=tree_result.stats.weighted_route_schedule_packing_cuts_added,
        weighted_route_schedule_packing_candidates_generated=tree_result.stats.weighted_route_schedule_packing_candidates_generated,
        weighted_route_schedule_packing_candidates_after_precheck=(
            tree_result.stats.weighted_route_schedule_packing_candidates_after_precheck
        ),
        weighted_route_schedule_packing_candidates_by_source=dict(
            tree_result.stats.weighted_route_schedule_packing_candidates_by_source
        ),
        weighted_route_schedule_packing_candidates_by_alpha=dict(
            tree_result.stats.weighted_route_schedule_packing_candidates_by_alpha
        ),
        weighted_route_schedule_packing_oracle_requests=tree_result.stats.weighted_route_schedule_packing_oracle_requests,
        weighted_route_schedule_packing_oracle_computations=(
            tree_result.stats.weighted_route_schedule_packing_oracle_computations
        ),
        weighted_route_schedule_packing_cache_hits=tree_result.stats.weighted_route_schedule_packing_cache_hits,
        weighted_route_schedule_packing_oracle_incomplete=tree_result.stats.weighted_route_schedule_packing_oracle_incomplete,
        weighted_route_schedule_packing_exact_not_violated=(
            tree_result.stats.weighted_route_schedule_packing_exact_not_violated
        ),
        weighted_route_schedule_packing_violated_candidates=(
            tree_result.stats.weighted_route_schedule_packing_violated_candidates
        ),
        weighted_route_schedule_packing_best_violation=_round(
            tree_result.stats.weighted_route_schedule_packing_best_violation,
            9,
        ),
        weighted_route_schedule_packing_oracle_time=_round(tree_result.stats.weighted_route_schedule_packing_oracle_time),
        weighted_route_schedule_packing_oracle_states_total=(
            tree_result.stats.weighted_route_schedule_packing_oracle_states_total
        ),
        weighted_route_schedule_packing_oracle_states_max=tree_result.stats.weighted_route_schedule_packing_oracle_states_max,
        weighted_route_schedule_packing_added_but_no_bound_improvement=(
            tree_result.stats.weighted_route_schedule_packing_added_but_no_bound_improvement
        ),
        weighted_route_schedule_packing_stopped_by_budget=tree_result.stats.weighted_route_schedule_packing_stopped_by_budget,
        weighted_route_schedule_packing_duplicate_skips=tree_result.stats.weighted_route_schedule_packing_duplicate_skips,
        fleet_lower_bound_cuts_added=tree_result.stats.fleet_lower_bound_cuts_added,
        fleet_lower_bound_value=tree_result.stats.fleet_lower_bound_value,
        fleet_lower_bound_oracle_upper_bound=tree_result.stats.fleet_lower_bound_oracle_upper_bound,
        fleet_lower_bound_oracle_states=tree_result.stats.fleet_lower_bound_oracle_states,
        fleet_lower_bound_oracle_exact=tree_result.stats.fleet_lower_bound_oracle_exact,
        schedule_pack_diagnostic_status=tree_result.stats.schedule_pack_diagnostic_status,
        schedule_pack_diagnostic_objective=_round(tree_result.stats.schedule_pack_diagnostic_objective),
        schedule_pack_diagnostic_gap_vs_root=_round(tree_result.stats.schedule_pack_diagnostic_gap_vs_root),
        schedule_pack_diagnostic_columns=tree_result.stats.schedule_pack_diagnostic_columns,
        schedule_pack_diagnostic_candidate_routes=tree_result.stats.schedule_pack_diagnostic_candidate_routes,
        schedule_pack_diagnostic_generated_states=tree_result.stats.schedule_pack_diagnostic_generated_states,
        schedule_pack_diagnostic_time=_round(tree_result.stats.schedule_pack_diagnostic_time),
        schedule_pack_relaxation_calls=tree_result.stats.schedule_pack_relaxation_calls,
        schedule_pack_relaxation_time=_round(tree_result.stats.schedule_pack_relaxation_time),
        schedule_pack_relaxation_root_objective=_round(tree_result.stats.schedule_pack_relaxation_root_objective),
        schedule_pack_relaxation_best_objective=_round(tree_result.stats.schedule_pack_relaxation_best_objective),
        schedule_pack_relaxation_best_gap_vs_node=_round(tree_result.stats.schedule_pack_relaxation_best_gap_vs_node),
        schedule_pack_relaxation_candidate_exact=tree_result.stats.schedule_pack_relaxation_candidate_exact,
        schedule_pack_relaxation_full_exact=tree_result.stats.schedule_pack_relaxation_full_exact,
        schedule_pack_relaxation_full_pricing_states=tree_result.stats.schedule_pack_relaxation_full_pricing_states,
        schedule_pack_relaxation_full_pricing_time=_round(tree_result.stats.schedule_pack_relaxation_full_pricing_time),
        schedule_pack_relaxation_columns=tree_result.stats.schedule_pack_relaxation_columns,
        schedule_pack_adaptive_decisions=tree_result.stats.schedule_pack_adaptive_decisions,
        schedule_pack_adaptive_runs=tree_result.stats.schedule_pack_adaptive_runs,
        schedule_pack_adaptive_skips=tree_result.stats.schedule_pack_adaptive_skips,
        schedule_pack_adaptive_easy_skips=tree_result.stats.schedule_pack_adaptive_easy_skips,
        schedule_pack_adaptive_bound_skips=tree_result.stats.schedule_pack_adaptive_bound_skips,
        route_enumeration_adaptive_decisions=tree_result.stats.route_enumeration_adaptive_decisions,
        route_enumeration_adaptive_runs=tree_result.stats.route_enumeration_adaptive_runs,
        route_enumeration_adaptive_skips=tree_result.stats.route_enumeration_adaptive_skips,
        route_enumeration_adaptive_easy_skips=tree_result.stats.route_enumeration_adaptive_easy_skips,
        route_pool_restart_nodes=tree_result.stats.route_pool_restart_nodes,
        route_pool_restart_rounds=tree_result.stats.route_pool_restart_rounds,
        route_pool_restart_routes_omitted_total=tree_result.stats.route_pool_restart_routes_omitted_total,
        route_pool_restart_routes_omitted_max=tree_result.stats.route_pool_restart_routes_omitted_max,
        route_pool_restart_pricing_recovered_routes=tree_result.stats.route_pool_restart_pricing_recovered_routes,
        route_pool_restart_protected_routes_max=tree_result.stats.route_pool_restart_protected_routes_max,
        route_pool_hygiene_diagnostic_events=tree_result.stats.route_pool_hygiene_diagnostic_events,
        route_pool_hygiene_task_set_groups_max=tree_result.stats.route_pool_hygiene_task_set_groups_max,
        route_pool_hygiene_multi_route_groups_max=tree_result.stats.route_pool_hygiene_multi_route_groups_max,
        route_pool_hygiene_near_duplicate_groups_max=tree_result.stats.route_pool_hygiene_near_duplicate_groups_max,
        route_pool_hygiene_near_duplicate_routes_max=tree_result.stats.route_pool_hygiene_near_duplicate_routes_max,
        route_pool_hygiene_max_group_size=tree_result.stats.route_pool_hygiene_max_group_size,
        route_pool_hygiene_admission_evaluated=tree_result.stats.route_pool_hygiene_admission_evaluated,
        route_pool_hygiene_admission_admitted=tree_result.stats.route_pool_hygiene_admission_admitted,
        route_pool_hygiene_admission_filtered=tree_result.stats.route_pool_hygiene_admission_filtered,
        route_pool_hygiene_admission_protected=tree_result.stats.route_pool_hygiene_admission_protected,
        route_pool_hygiene_admission_forced_exact=tree_result.stats.route_pool_hygiene_admission_forced_exact,
        cuts_purged=tree_result.stats.cuts_purged,
        generated_routes=len(tree_result.routes),
        generated_columns=generated_columns,
        label_pops=tree_result.stats.label_pops,
        generated_labels=tree_result.stats.generated_labels,
        cuts_added=len(tree_result.cuts),
        root_relaxation=_round(tree_result.stats.root_relaxation),
        incumbent_node=None if tree_result.incumbent is None else tree_result.incumbent.node_id,
        log_path=str(log_path or ""),
        instance_path=str(data.instance_path),
        seed=seed,
    )

    if solution_path is not None:
        import json

        output = {
            "summary": result.to_row(),
            "solution": incumbent_to_solution(data, tree_result.incumbent),
            "routes": [route_to_json(route) for route in tree_result.routes],
            "cuts": [
                {
                    "id": cut.id,
                    "vehicle": getattr(cut, "vehicle", None),
                    "kind": cut.kind,
                    "source_vehicle": getattr(cut, "source_vehicle", None),
                    "signatures": [list(signature) for signature in getattr(cut, "signatures", ())],
                    "weights": list(getattr(cut, "weights", ())),
                    "tasks": list(getattr(cut, "tasks", ())),
                    "sense": cut.sense,
                    "rhs": cut.rhs,
                    "upper_bound": getattr(cut, "upper_bound", None),
                    "scale_by_vehicle_use": getattr(cut, "scale_by_vehicle_use", None),
                    "k_bound": getattr(cut, "k_bound", None),
                    "capacity_bound": getattr(cut, "capacity_bound", None),
                    "resource_bound": getattr(cut, "resource_bound", None),
                    "demand": getattr(cut, "demand", None),
                    "capacity": getattr(cut, "capacity", None),
                    "lower_bound": getattr(cut, "lower_bound", None),
                    "oracle_upper_bound": getattr(cut, "oracle_upper_bound", None),
                    "divisor": getattr(cut, "divisor", None),
                    "denominator": getattr(cut, "denominator", None),
                    "multipliers": list(getattr(cut, "multipliers", ())),
                    "memory_tasks": list(getattr(cut, "memory_tasks", ())),
                    "oracle_states": getattr(cut, "oracle_states", None),
                    "source": getattr(cut, "source", None),
                    "alpha_pattern": getattr(cut, "alpha_pattern", None),
                }
                for cut in tree_result.cuts
            ],
        }
        path = Path(solution_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(output, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    return result
