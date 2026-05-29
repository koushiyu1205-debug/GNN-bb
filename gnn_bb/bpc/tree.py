"""中文摘要：本文件显式控制 clean BPC 搜索树。SCIP 在这里仅作为每个节点 RMP LP 的求解器。"""

from __future__ import annotations

from dataclasses import dataclass, replace
import heapq
from itertools import combinations
from itertools import product
from itertools import permutations
import math
import time
from typing import Any

from .branching import (
    BranchCandidate,
    BranchConstraint,
    choose_branch,
    generate_branch_candidates,
    route_allowed_by_branch,
    route_branch_coefficient,
)
from .columns import RouteColumn, RoutePool, evaluate_route, route_to_json
from .cuts import (
    Cut,
    CrossingCut,
    FleetLowerBoundCut,
    LimitedMemoryRank1Cut,
    ScheduleCapacityCut,
    ScheduleSubsetCostLowerBoundCut,
    ScheduleNoGoodCut,
    SubsetRowCut,
    WeightedScheduleRouteSetPackingCut,
    capacity_route_lower_bound,
    make_no_good_cuts_for_all_vehicles,
    make_schedule_capacity_cuts_for_all_vehicles,
    normalize_signatures,
)
from .data import BPCData
from .logger import BPCLogger
from .node import BPCNode, BPCStats
from .persistent_rmp import PersistentRMP, PersistentRMPRequiresRebuild
from .pricing import PricingResult, exact_pricing
from .rmp import RMPSolution, RestrictedIntegerResult, solve_restricted_integer_master, solve_rmp_lp
from .schedule_capacity import ScheduleCapacityResult, exact_schedule_task_capacity, find_schedule_capacity_conflict
from .schedule_cost import ScheduleSubsetCostResult, exact_schedule_subset_cost
from .schedule_pack import solve_schedule_pack_node_relaxation
from .task_schedule_capacity import (
    TaskScheduleCapacityCacheEntry,
    TaskScheduleCapacityCandidate,
    TaskScheduleCapacityWitness,
    generate_task_schedule_capacity_candidates,
    witness_from_routes,
)
from .validation import (
    RoutePairScheduleConflict,
    check_route_set_schedule_feasible,
    diagnose_route_set_schedule,
    evaluate_route_at_start,
    exact_route_set_schedule_capacity,
    exact_weighted_route_set_schedule_capacity,
    route_transition_ready_time,
)


@dataclass
class Incumbent:
    objective: float
    route_values: list[tuple[RouteColumn, int, float]]
    y_values: dict[int, float]
    node_id: int


@dataclass
class TreeResult:
    status: str
    primal_bound: float | None
    dual_bound: float | None
    gap: float | None
    solving_time: float
    node_count: int
    stats: BPCStats
    routes: list[RouteColumn]
    cuts: list[Cut]
    incumbent: Incumbent | None


@dataclass
class PseudoCostRecord:
    count: int = 0
    score_sum: float = 0.0

    @property
    def initialized(self) -> bool:
        return self.count > 0

    @property
    def average_score(self) -> float:
        return self.score_sum / self.count if self.count else 0.0

    def update(self, score: float) -> None:
        self.count += 1
        self.score_sum += float(score)


@dataclass
class BranchTestResult:
    candidate: BranchCandidate
    lp_score: float
    heuristic_score: float
    left_lp_status: str
    right_lp_status: str
    left_lp_gain: float
    right_lp_gain: float
    left_heuristic_gain: float
    right_heuristic_gain: float
    left_best_reduced_cost: float | None
    right_best_reduced_cost: float | None
    left_heuristic_iterations: int
    right_heuristic_iterations: int
    left_heuristic_added_routes: int
    right_heuristic_added_routes: int
    left_heuristic_exhausted: bool | None
    right_heuristic_exhausted: bool | None
    selected_by: str


@dataclass
class HeuristicChildResult:
    gain: float
    best_reduced_cost: float | None
    iterations: int
    added_routes: int
    exhausted: bool | None


class CleanBPCTree:
    def __init__(
        self,
        data: BPCData,
        *,
        time_limit: float,
        max_nodes: int,
        eps: float,
        integer_tol: float,
        max_routes_per_pricing: int,
        max_labels_per_pricing: int,
        rmp_params: dict[str, Any] | None,
        logger: BPCLogger,
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
        restricted_master_scan_solution_pool_enabled: bool = False,
        restricted_master_scan_solution_pool_limit: int = 20,
        restricted_master_adaptive_enabled: bool = False,
        restricted_master_adaptive_min_depth: int = 1,
        restricted_master_adaptive_after_failures: int = 2,
        restricted_master_adaptive_reduced_time_limit: float = 5.0,
        restricted_master_adaptive_skip_after_failures: int = 4,
        restricted_master_adaptive_productivity_guard_enabled: bool = False,
        restricted_master_adaptive_productive_after_failures: int = 2,
        restricted_master_adaptive_productive_max_consecutive_skips: int = 2,
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
        witness_rank1_cuts_enabled: bool = False,
        witness_rank1_max_depth: int = 1,
        witness_rank1_max_rounds_per_node: int = 1,
        witness_rank1_max_candidates: int = 40,
        witness_rank1_max_cuts_per_round: int = 8,
        witness_rank1_max_subset_size: int = 8,
        witness_rank1_min_violation: float = 1.0e-5,
        witness_rank1_use_route_pack_roi: bool = True,
        witness_rank1_use_rim_witness: bool = True,
        witness_rank1_use_incompatibility_witness: bool = True,
        witness_rank1_use_subset_row: bool = True,
        witness_rank1_use_lm_rank1: bool = True,
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
        schedule_variant_route_pack_cuts_enabled: bool = False,
        schedule_variant_route_pack_max_depth: int = 2,
        schedule_variant_route_pack_max_core_routes: int = 4,
        schedule_variant_route_pack_max_variants_per_task_set: int = 4,
        schedule_variant_route_pack_max_routes: int = 16,
        schedule_variant_route_pack_min_violation: float = 1.0e-5,
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
        route_pool_restart_node_start_enabled: bool = True,
        route_pool_restart_min_depth: int = 0,
        route_pool_restart_max_depth: int = -1,
        route_pool_restart_max_routes: int = 0,
        route_pool_restart_min_global_routes: int = 0,
        route_pool_restart_keep_recent_rounds: int = 2,
        route_pool_restart_max_routes_per_task_set: int = 6,
        route_pool_restart_active_value_tol: float = 1.0e-8,
        route_pool_restart_keep_cut_signatures: bool = False,
        route_pool_restart_cleanup_enabled: bool = False,
        route_pool_restart_branch_with_global_solution: bool = False,
        route_pool_task_set_compaction_enabled: bool = False,
        route_pool_task_set_compaction_min_depth: int = 1,
        route_pool_task_set_compaction_max_depth: int = -1,
        route_pool_task_set_compaction_max_routes_per_task_set: int = 3,
        route_pool_task_set_compaction_min_group_size: int = 4,
        route_pool_task_set_compaction_keep_recent_rounds: int = 2,
        route_pack_branch_signal_enabled: bool = False,
        route_pack_branch_signal_apply_enabled: bool = False,
        route_pack_branch_signal_apply_min_depth: int = 0,
        route_pack_branch_signal_boost: float = 0.02,
        early_bound_fathom_before_cuts_enabled: bool = False,
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
    ) -> None:
        self.data = data
        self.time_limit = float(time_limit)
        self.max_nodes = int(max_nodes)
        self.eps = float(eps)
        self.integer_tol = float(integer_tol)
        self.max_routes_per_pricing = int(max_routes_per_pricing)
        self.max_labels_per_pricing = int(max_labels_per_pricing)
        self.root_max_routes_per_pricing = int(root_max_routes_per_pricing)
        self.heuristic_pricing_enabled = bool(heuristic_pricing_enabled)
        self.heuristic_pricing_max_labels = int(heuristic_pricing_max_labels)
        self.heuristic_pricing_routes_per_round = int(heuristic_pricing_routes_per_round)
        self.heuristic_pricing_selection_mode = str(heuristic_pricing_selection_mode)
        self.exact_pricing_selection_mode = str(exact_pricing_selection_mode)
        self.branch_node_heuristic_boost_enabled = bool(branch_node_heuristic_boost_enabled)
        self.branch_node_heuristic_boost_max_labels = int(branch_node_heuristic_boost_max_labels)
        self.branch_node_heuristic_boost_routes_per_round = int(branch_node_heuristic_boost_routes_per_round)
        self.branch_node_heuristic_boost_min_depth = int(branch_node_heuristic_boost_min_depth)
        self.exact_pricing_dominance_enabled = bool(exact_pricing_dominance_enabled)
        self.pricing_completion_bound_enabled = bool(pricing_completion_bound_enabled)
        self.ng_dssr_pricing_enabled = bool(ng_dssr_pricing_enabled)
        self.ng_dssr_memory_size = int(ng_dssr_memory_size)
        self.exact_dssr_pricing_enabled = bool(exact_dssr_pricing_enabled)
        self.exact_dssr_initial_memory_size = int(exact_dssr_initial_memory_size)
        self.exact_dssr_max_iterations = int(exact_dssr_max_iterations)
        self.exact_dssr_max_labels = int(exact_dssr_max_labels)
        self.route_enumeration_enabled = bool(route_enumeration_enabled)
        self.route_enumeration_rc_threshold = float(route_enumeration_rc_threshold)
        self.route_enumeration_max_routes = int(route_enumeration_max_routes)
        self.persistent_rmp_enabled = bool(persistent_rmp_enabled)
        self.restricted_master_heuristic_enabled = bool(restricted_master_heuristic_enabled)
        self.restricted_master_time_limit = float(restricted_master_time_limit)
        self.restricted_master_max_routes = int(restricted_master_max_routes)
        self.restricted_master_max_calls = int(restricted_master_max_calls)
        self.restricted_master_max_depth = int(restricted_master_max_depth)
        self.restricted_master_schedule_aware = bool(restricted_master_schedule_aware)
        self.restricted_master_max_no_good_rounds = int(restricted_master_max_no_good_rounds)
        self.restricted_master_route_pack_conflict_max_events = int(restricted_master_route_pack_conflict_max_events)
        self.restricted_master_repair_enabled = bool(restricted_master_repair_enabled)
        self.restricted_master_repair_max_attempts = int(restricted_master_repair_max_attempts)
        self.restricted_master_repair_max_states = int(restricted_master_repair_max_states)
        self.restricted_master_scan_solution_pool_enabled = bool(restricted_master_scan_solution_pool_enabled)
        self.restricted_master_scan_solution_pool_limit = int(restricted_master_scan_solution_pool_limit)
        self.restricted_master_adaptive_enabled = bool(restricted_master_adaptive_enabled)
        self.restricted_master_adaptive_min_depth = int(restricted_master_adaptive_min_depth)
        self.restricted_master_adaptive_after_failures = int(restricted_master_adaptive_after_failures)
        self.restricted_master_adaptive_reduced_time_limit = float(restricted_master_adaptive_reduced_time_limit)
        self.restricted_master_adaptive_skip_after_failures = int(restricted_master_adaptive_skip_after_failures)
        self.restricted_master_adaptive_productivity_guard_enabled = bool(
            restricted_master_adaptive_productivity_guard_enabled
        )
        self.restricted_master_adaptive_productive_after_failures = int(
            restricted_master_adaptive_productive_after_failures
        )
        self.restricted_master_adaptive_productive_max_consecutive_skips = int(
            restricted_master_adaptive_productive_max_consecutive_skips
        )
        self._restricted_master_adaptive_failure_streak = 0
        self._restricted_master_adaptive_unproductive_streak = 0
        self._restricted_master_adaptive_productive_skip_streak = 0
        self.rmp_params = dict(rmp_params or {})
        self.logger = logger
        self.branching_strategy = str(branching_strategy)
        self.three_pb_pseudocost_candidates = int(three_pb_pseudocost_candidates)
        self.three_pb_fractional_candidates = int(three_pb_fractional_candidates)
        self.three_pb_lp_candidates = int(three_pb_lp_candidates)
        self.three_pb_heuristic_cg_iterations = int(three_pb_heuristic_cg_iterations)
        self.three_pb_heuristic_routes_per_iter = int(three_pb_heuristic_routes_per_iter)
        self.three_pb_heuristic_max_labels = int(three_pb_heuristic_max_labels)
        self.task_vehicle_linking_enabled = bool(task_vehicle_linking_enabled)
        self.robust_capacity_cuts_enabled = bool(robust_capacity_cuts_enabled)
        self.robust_capacity_cut_max_depth = int(robust_capacity_cut_max_depth)
        self.robust_capacity_cut_max_subset_size = int(robust_capacity_cut_max_subset_size)
        self.robust_capacity_cut_max_per_round = int(robust_capacity_cut_max_per_round)
        self.robust_capacity_cut_min_violation = float(robust_capacity_cut_min_violation)
        self.robust_capacity_cut_max_rounds_per_node = int(robust_capacity_cut_max_rounds_per_node)
        self.resource_lower_bound_cuts_enabled = bool(resource_lower_bound_cuts_enabled)
        self.resource_cut_max_depth = int(resource_cut_max_depth)
        self.resource_cut_max_subset_size = int(resource_cut_max_subset_size)
        self.resource_cut_max_per_round = int(resource_cut_max_per_round)
        self.resource_cut_min_violation = float(resource_cut_min_violation)
        self.resource_cut_max_rounds_per_node = int(resource_cut_max_rounds_per_node)
        self.crossing_cuts_enabled = self.robust_capacity_cuts_enabled or self.resource_lower_bound_cuts_enabled
        self.crossing_cut_max_depth = max(self.robust_capacity_cut_max_depth, self.resource_cut_max_depth)
        self.crossing_cut_max_subset_size = max(self.robust_capacity_cut_max_subset_size, self.resource_cut_max_subset_size)
        self.crossing_cut_max_per_round = max(self.robust_capacity_cut_max_per_round, self.resource_cut_max_per_round)
        self.crossing_cut_min_violation = min(self.robust_capacity_cut_min_violation, self.resource_cut_min_violation)
        self.crossing_cut_max_rounds_per_node = max(
            self.robust_capacity_cut_max_rounds_per_node,
            self.resource_cut_max_rounds_per_node,
        )
        self.subset_row_cuts_enabled = bool(subset_row_cuts_enabled)
        self.subset_row_cut_max_depth = int(subset_row_cut_max_depth)
        self.subset_row_cut_max_subset_size = int(subset_row_cut_max_subset_size)
        self.subset_row_cut_max_per_round = int(subset_row_cut_max_per_round)
        self.subset_row_cut_min_violation = float(subset_row_cut_min_violation)
        self.subset_row_cut_max_rounds_per_node = int(subset_row_cut_max_rounds_per_node)
        self.subset_row_candidate_top_routes = int(subset_row_candidate_top_routes)
        self.subset_row_candidate_max_sets = int(subset_row_candidate_max_sets)
        raw_k_values = subset_row_k_values if isinstance(subset_row_k_values, (list, tuple, set)) else (subset_row_k_values,)
        parsed_k_values = tuple(sorted({int(value) for value in raw_k_values if int(value) >= 2}))
        self.subset_row_k_values = parsed_k_values or (2,)
        self.lm_rank1_cuts_enabled = bool(lm_rank1_cuts_enabled)
        self.lm_rank1_cut_max_depth = int(lm_rank1_cut_max_depth)
        self.lm_rank1_cut_max_subset_size = int(lm_rank1_cut_max_subset_size)
        self.lm_rank1_cut_max_per_round = int(lm_rank1_cut_max_per_round)
        self.lm_rank1_cut_min_violation = float(lm_rank1_cut_min_violation)
        self.lm_rank1_cut_max_rounds_per_node = int(lm_rank1_cut_max_rounds_per_node)
        self.lm_rank1_candidate_top_routes = int(lm_rank1_candidate_top_routes)
        self.lm_rank1_candidate_max_sets = int(lm_rank1_candidate_max_sets)
        raw_denominators = lm_rank1_denominators if isinstance(lm_rank1_denominators, (list, tuple, set)) else (lm_rank1_denominators,)
        parsed_denominators = tuple(sorted({int(value) for value in raw_denominators if int(value) >= 3}))
        self.lm_rank1_denominators = parsed_denominators or (3,)
        self.lm_rank1_memory_size = int(lm_rank1_memory_size)
        self.lm_rank1_max_patterns_per_set = int(lm_rank1_max_patterns_per_set)
        self.witness_rank1_cuts_enabled = bool(witness_rank1_cuts_enabled)
        self.witness_rank1_max_depth = int(witness_rank1_max_depth)
        self.witness_rank1_max_rounds_per_node = int(witness_rank1_max_rounds_per_node)
        self.witness_rank1_max_candidates = int(witness_rank1_max_candidates)
        self.witness_rank1_max_cuts_per_round = int(witness_rank1_max_cuts_per_round)
        self.witness_rank1_max_subset_size = int(witness_rank1_max_subset_size)
        self.witness_rank1_min_violation = float(witness_rank1_min_violation)
        self.witness_rank1_use_route_pack_roi = bool(witness_rank1_use_route_pack_roi)
        self.witness_rank1_use_rim_witness = bool(witness_rank1_use_rim_witness)
        self.witness_rank1_use_incompatibility_witness = bool(witness_rank1_use_incompatibility_witness)
        self.witness_rank1_use_subset_row = bool(witness_rank1_use_subset_row)
        self.witness_rank1_use_lm_rank1 = bool(witness_rank1_use_lm_rank1)
        self.schedule_subset_cost_cuts_enabled = bool(schedule_subset_cost_cuts_enabled)
        self.schedule_subset_cost_cut_max_depth = int(schedule_subset_cost_cut_max_depth)
        self.schedule_subset_cost_cut_max_subset_size = int(schedule_subset_cost_cut_max_subset_size)
        self.schedule_subset_cost_cut_max_per_round = int(schedule_subset_cost_cut_max_per_round)
        self.schedule_subset_cost_cut_min_violation = float(schedule_subset_cost_cut_min_violation)
        self.schedule_subset_cost_cut_max_rounds_per_node = int(schedule_subset_cost_cut_max_rounds_per_node)
        self.schedule_subset_cost_oracle_max_states = int(schedule_subset_cost_oracle_max_states)
        self.schedule_subset_cost_candidate_top_tasks = int(schedule_subset_cost_candidate_top_tasks)
        self.schedule_subset_cost_candidate_max_combinations = int(schedule_subset_cost_candidate_max_combinations)
        self.schedule_subset_cost_route_union_top_routes = int(schedule_subset_cost_route_union_top_routes)
        self.schedule_subset_cost_route_union_max_routes = int(schedule_subset_cost_route_union_max_routes)
        self.schedule_capacity_cuts_enabled = bool(schedule_capacity_cuts_enabled)
        self.schedule_capacity_separation_enabled = bool(schedule_capacity_separation_enabled)
        self.schedule_capacity_cut_max_depth = int(schedule_capacity_cut_max_depth)
        self.schedule_capacity_cut_max_subset_size = int(schedule_capacity_cut_max_subset_size)
        self.schedule_capacity_cut_max_per_round = int(schedule_capacity_cut_max_per_round)
        self.schedule_capacity_cut_min_violation = float(schedule_capacity_cut_min_violation)
        self.schedule_capacity_cut_max_rounds_per_node = int(schedule_capacity_cut_max_rounds_per_node)
        self.schedule_capacity_oracle_max_states = int(schedule_capacity_oracle_max_states)
        self.schedule_capacity_candidate_top_tasks = int(schedule_capacity_candidate_top_tasks)
        self.schedule_capacity_candidate_max_combinations = int(schedule_capacity_candidate_max_combinations)
        self.schedule_capacity_route_union_top_routes = int(schedule_capacity_route_union_top_routes)
        self.schedule_capacity_route_union_max_routes = int(schedule_capacity_route_union_max_routes)
        self.root_schedule_capacity_cuts_enabled = bool(root_schedule_capacity_cuts_enabled)
        self.root_schedule_capacity_max_depth = int(root_schedule_capacity_max_depth)
        self.root_schedule_capacity_pair_budget = int(root_schedule_capacity_pair_budget)
        self.root_schedule_capacity_triple_budget = int(root_schedule_capacity_triple_budget)
        self.root_schedule_capacity_oracle_max_states = int(root_schedule_capacity_oracle_max_states)
        self.root_schedule_capacity_time_budget = float(root_schedule_capacity_time_budget)
        self.root_schedule_capacity_min_violation = float(root_schedule_capacity_min_violation)
        self.root_schedule_capacity_stop_after_no_add_rounds = int(root_schedule_capacity_stop_after_no_add_rounds)
        self.task_schedule_capacity_legacy_alias_mode = task_schedule_capacity_cuts_enabled is None
        self.task_schedule_capacity_cuts_enabled = (
            bool(root_schedule_capacity_cuts_enabled)
            if task_schedule_capacity_cuts_enabled is None
            else bool(task_schedule_capacity_cuts_enabled)
        )
        self.task_schedule_capacity_max_depth = (
            int(root_schedule_capacity_max_depth)
            if task_schedule_capacity_max_depth is None
            else int(task_schedule_capacity_max_depth)
        )
        self.task_schedule_capacity_pair_budget = (
            int(root_schedule_capacity_pair_budget)
            if task_schedule_capacity_pair_budget is None
            else int(task_schedule_capacity_pair_budget)
        )
        self.task_schedule_capacity_triple_budget = (
            int(root_schedule_capacity_triple_budget)
            if task_schedule_capacity_triple_budget is None
            else int(task_schedule_capacity_triple_budget)
        )
        self.task_schedule_capacity_small_set_budget = int(task_schedule_capacity_small_set_budget)
        self.task_schedule_capacity_max_subset_size = int(task_schedule_capacity_max_subset_size)
        self.task_schedule_capacity_max_cuts_per_round = int(task_schedule_capacity_max_cuts_per_round)
        self.task_schedule_capacity_oracle_max_states = (
            int(root_schedule_capacity_oracle_max_states)
            if task_schedule_capacity_oracle_max_states is None
            else int(task_schedule_capacity_oracle_max_states)
        )
        self.task_schedule_capacity_node_time_budget = (
            float(root_schedule_capacity_time_budget)
            if task_schedule_capacity_node_time_budget is None
            else float(task_schedule_capacity_node_time_budget)
        )
        self.task_schedule_capacity_global_time_ratio = float(task_schedule_capacity_global_time_ratio)
        self.task_schedule_capacity_min_violation = (
            float(root_schedule_capacity_min_violation)
            if task_schedule_capacity_min_violation is None
            else float(task_schedule_capacity_min_violation)
        )
        self.task_schedule_capacity_copy_to_all_vehicles = bool(task_schedule_capacity_copy_to_all_vehicles)
        self.task_schedule_capacity_use_rim_witness = bool(task_schedule_capacity_use_rim_witness)
        self.task_schedule_capacity_use_route_pack_witness = bool(task_schedule_capacity_use_route_pack_witness)
        self.task_schedule_capacity_use_incompatibility_witness = bool(task_schedule_capacity_use_incompatibility_witness)
        self.task_schedule_capacity_use_top_z_mass = bool(task_schedule_capacity_use_top_z_mass)
        self.task_schedule_capacity_use_support_route_union = bool(task_schedule_capacity_use_support_route_union)
        self.task_schedule_capacity_use_time_window_clusters = bool(task_schedule_capacity_use_time_window_clusters)
        self.task_schedule_capacity_stop_after_no_add_rounds = (
            int(root_schedule_capacity_stop_after_no_add_rounds)
            if task_schedule_capacity_stop_after_no_add_rounds is None
            else int(task_schedule_capacity_stop_after_no_add_rounds)
        )
        self.task_schedule_capacity_stop_after_no_improve_rounds = int(task_schedule_capacity_stop_after_no_improve_rounds)
        self.task_schedule_capacity_cache_incomplete = bool(task_schedule_capacity_cache_incomplete)
        self.task_schedule_capacity_cache_not_tight = bool(task_schedule_capacity_cache_not_tight)
        self.task_schedule_capacity_cache_exact_upper_bound = bool(task_schedule_capacity_cache_exact_upper_bound)
        self.task_schedule_capacity_branch_signal_enabled = bool(task_schedule_capacity_branch_signal_enabled)
        self.task_schedule_capacity_branch_signal_apply_enabled = bool(task_schedule_capacity_branch_signal_apply_enabled)
        self.schedule_incompatibility_cuts_enabled = bool(schedule_incompatibility_cuts_enabled)
        self.schedule_incompatibility_cut_max_depth = int(schedule_incompatibility_cut_max_depth)
        self.schedule_incompatibility_cut_max_rounds_per_node = int(schedule_incompatibility_cut_max_rounds_per_node)
        self.schedule_incompatibility_cut_max_support_routes = int(schedule_incompatibility_cut_max_support_routes)
        self.schedule_incompatibility_cut_max_per_round = int(schedule_incompatibility_cut_max_per_round)
        self.schedule_incompatibility_cut_min_violation = float(schedule_incompatibility_cut_min_violation)
        self.schedule_incompatibility_clique_min_size = int(schedule_incompatibility_clique_min_size)
        self.schedule_incompatibility_clique_seed_count = int(schedule_incompatibility_clique_seed_count)
        self.route_set_schedule_packing_cuts_enabled = bool(route_set_schedule_packing_cuts_enabled)
        self.route_set_schedule_packing_cut_max_depth = int(route_set_schedule_packing_cut_max_depth)
        self.route_set_schedule_packing_cut_max_rounds_per_node = int(route_set_schedule_packing_cut_max_rounds_per_node)
        self.route_set_schedule_packing_cut_max_support_routes = int(route_set_schedule_packing_cut_max_support_routes)
        self.route_set_schedule_packing_cut_max_routes = int(route_set_schedule_packing_cut_max_routes)
        self.route_set_schedule_packing_cut_max_per_round = int(route_set_schedule_packing_cut_max_per_round)
        self.route_set_schedule_packing_cut_min_violation = float(route_set_schedule_packing_cut_min_violation)
        self.route_set_schedule_packing_oracle_max_states = int(route_set_schedule_packing_oracle_max_states)
        self.route_set_schedule_packing_roi_guard_enabled = bool(route_set_schedule_packing_roi_guard_enabled)
        self.route_set_schedule_packing_stop_after_no_add_rounds = int(route_set_schedule_packing_stop_after_no_add_rounds)
        self.route_set_schedule_packing_min_objective_improvement = float(route_set_schedule_packing_min_objective_improvement)
        self.route_set_schedule_packing_stop_after_no_improve_rounds = int(
            route_set_schedule_packing_stop_after_no_improve_rounds
        )
        self.route_set_schedule_packing_global_time_limit_ratio = float(route_set_schedule_packing_global_time_limit_ratio)
        self.schedule_variant_route_pack_cuts_enabled = bool(schedule_variant_route_pack_cuts_enabled)
        self.schedule_variant_route_pack_max_depth = int(schedule_variant_route_pack_max_depth)
        self.schedule_variant_route_pack_max_core_routes = int(schedule_variant_route_pack_max_core_routes)
        self.schedule_variant_route_pack_max_variants_per_task_set = int(
            schedule_variant_route_pack_max_variants_per_task_set
        )
        self.schedule_variant_route_pack_max_routes = int(schedule_variant_route_pack_max_routes)
        self.schedule_variant_route_pack_min_violation = float(schedule_variant_route_pack_min_violation)
        self.weighted_route_schedule_packing_cuts_enabled = bool(weighted_route_schedule_packing_cuts_enabled)
        self.weighted_route_schedule_packing_max_depth = int(weighted_route_schedule_packing_max_depth)
        self.weighted_route_schedule_packing_max_rounds_per_node = int(weighted_route_schedule_packing_max_rounds_per_node)
        self.weighted_route_schedule_packing_max_candidates = int(weighted_route_schedule_packing_max_candidates)
        self.weighted_route_schedule_packing_max_cuts_per_round = int(weighted_route_schedule_packing_max_cuts_per_round)
        self.weighted_route_schedule_packing_max_routes = int(weighted_route_schedule_packing_max_routes)
        self.weighted_route_schedule_packing_oracle_max_states = int(weighted_route_schedule_packing_oracle_max_states)
        self.weighted_route_schedule_packing_min_violation = float(weighted_route_schedule_packing_min_violation)
        self.weighted_route_schedule_packing_node_time_budget = float(weighted_route_schedule_packing_node_time_budget)
        self.weighted_route_schedule_packing_global_time_ratio = float(weighted_route_schedule_packing_global_time_ratio)
        self.fleet_lower_bound_cuts_enabled = bool(fleet_lower_bound_cuts_enabled)
        self.fleet_lower_bound_oracle_max_states = int(fleet_lower_bound_oracle_max_states)
        self.schedule_pack_diagnostic_enabled = bool(schedule_pack_diagnostic_enabled)
        self.schedule_pack_diagnostic_max_candidate_routes = int(schedule_pack_diagnostic_max_candidate_routes)
        self.schedule_pack_diagnostic_max_columns = int(schedule_pack_diagnostic_max_columns)
        self.schedule_pack_diagnostic_beam_width = int(schedule_pack_diagnostic_beam_width)
        self.schedule_pack_diagnostic_max_sorties = int(schedule_pack_diagnostic_max_sorties)
        self.schedule_pack_diagnostic_time_limit = float(schedule_pack_diagnostic_time_limit)
        self.schedule_pack_pricing_batch_size = int(schedule_pack_pricing_batch_size)
        self.schedule_pack_relaxation_enabled = bool(schedule_pack_relaxation_enabled)
        self.schedule_pack_relaxation_max_depth = int(schedule_pack_relaxation_max_depth)
        self.schedule_pack_relaxation_time_limit = float(schedule_pack_relaxation_time_limit)
        self.schedule_pack_relaxation_use_for_priority = bool(schedule_pack_relaxation_use_for_priority)
        self.schedule_pack_full_pricing_enabled = bool(schedule_pack_full_pricing_enabled)
        self.schedule_pack_full_pricing_max_depth = int(schedule_pack_full_pricing_max_depth)
        self.schedule_pack_full_pricing_max_states = int(schedule_pack_full_pricing_max_states)
        self.schedule_pack_adaptive_enabled = bool(schedule_pack_adaptive_enabled)
        self.schedule_pack_adaptive_gap_abs = float(schedule_pack_adaptive_gap_abs)
        self.schedule_pack_adaptive_gap_ratio = float(schedule_pack_adaptive_gap_ratio)
        self.schedule_pack_adaptive_skip_if_fathomable = bool(schedule_pack_adaptive_skip_if_fathomable)
        self.route_enumeration_adaptive_enabled = bool(route_enumeration_adaptive_enabled)
        self.route_enumeration_adaptive_gap_abs = float(route_enumeration_adaptive_gap_abs)
        self.route_enumeration_adaptive_gap_ratio = float(route_enumeration_adaptive_gap_ratio)
        self.route_pool_hygiene_diagnostics_enabled = bool(route_pool_hygiene_diagnostics_enabled)
        self.route_pool_hygiene_diagnostics_min_routes = int(route_pool_hygiene_diagnostics_min_routes)
        self.route_pool_hygiene_near_duplicate_abs_tol = float(route_pool_hygiene_near_duplicate_abs_tol)
        self.route_pool_hygiene_near_duplicate_rel_tol = float(route_pool_hygiene_near_duplicate_rel_tol)
        self.route_pool_hygiene_sample_groups = int(route_pool_hygiene_sample_groups)
        self.route_pool_hygiene_admission_enabled = bool(route_pool_hygiene_admission_enabled)
        self.route_pool_hygiene_admission_max_per_task_set = int(route_pool_hygiene_admission_max_per_task_set)
        self.route_pool_hygiene_admission_min_depth = int(route_pool_hygiene_admission_min_depth)
        self.route_pool_hygiene_admission_protect_active_task_sets = bool(
            route_pool_hygiene_admission_protect_active_task_sets
        )
        self.route_pool_hygiene_admission_protect_cut_task_sets = bool(
            route_pool_hygiene_admission_protect_cut_task_sets
        )
        self.route_pool_hygiene_admission_protect_incumbent_task_sets = bool(
            route_pool_hygiene_admission_protect_incumbent_task_sets
        )
        self.route_pool_hygiene_admission_protect_branch_task_sets = bool(
            route_pool_hygiene_admission_protect_branch_task_sets
        )
        self.route_pool_restart_enabled = bool(route_pool_restart_enabled)
        self.route_pool_restart_node_start_enabled = bool(route_pool_restart_node_start_enabled)
        self.route_pool_restart_min_depth = int(route_pool_restart_min_depth)
        self.route_pool_restart_max_depth = int(route_pool_restart_max_depth)
        self.route_pool_restart_max_routes = int(route_pool_restart_max_routes)
        self.route_pool_restart_min_global_routes = int(route_pool_restart_min_global_routes)
        self.route_pool_restart_keep_recent_rounds = int(route_pool_restart_keep_recent_rounds)
        self.route_pool_restart_max_routes_per_task_set = int(route_pool_restart_max_routes_per_task_set)
        self.route_pool_restart_active_value_tol = float(route_pool_restart_active_value_tol)
        self.route_pool_restart_keep_cut_signatures = bool(route_pool_restart_keep_cut_signatures)
        self.route_pool_restart_cleanup_enabled = bool(route_pool_restart_cleanup_enabled)
        self.route_pool_restart_branch_with_global_solution = bool(route_pool_restart_branch_with_global_solution)
        self.route_pool_task_set_compaction_enabled = bool(route_pool_task_set_compaction_enabled)
        self.route_pool_task_set_compaction_min_depth = int(route_pool_task_set_compaction_min_depth)
        self.route_pool_task_set_compaction_max_depth = int(route_pool_task_set_compaction_max_depth)
        self.route_pool_task_set_compaction_max_routes_per_task_set = int(route_pool_task_set_compaction_max_routes_per_task_set)
        self.route_pool_task_set_compaction_min_group_size = int(route_pool_task_set_compaction_min_group_size)
        self.route_pool_task_set_compaction_keep_recent_rounds = int(route_pool_task_set_compaction_keep_recent_rounds)
        self.route_pack_branch_signal_enabled = bool(route_pack_branch_signal_enabled)
        self.route_pack_branch_signal_apply_enabled = bool(route_pack_branch_signal_apply_enabled)
        self.route_pack_branch_signal_apply_min_depth = int(route_pack_branch_signal_apply_min_depth)
        self.route_pack_branch_signal_boost = float(route_pack_branch_signal_boost)
        self.early_bound_fathom_before_cuts_enabled = bool(early_bound_fathom_before_cuts_enabled)
        self.three_pb_candidate_budget_enabled = bool(three_pb_candidate_budget_enabled)
        self.three_pb_root_pseudocost_candidates = int(three_pb_root_pseudocost_candidates)
        self.three_pb_root_fractional_candidates = int(three_pb_root_fractional_candidates)
        self.three_pb_root_lp_candidates = int(three_pb_root_lp_candidates)
        self.three_pb_nonroot_pseudocost_candidates = int(three_pb_nonroot_pseudocost_candidates)
        self.three_pb_nonroot_fractional_candidates = int(three_pb_nonroot_fractional_candidates)
        self.three_pb_nonroot_lp_candidates = int(three_pb_nonroot_lp_candidates)
        self.three_pb_deep_depth = int(three_pb_deep_depth)
        self.three_pb_deep_pseudocost_candidates = int(three_pb_deep_pseudocost_candidates)
        self.three_pb_deep_fractional_candidates = int(three_pb_deep_fractional_candidates)
        self.three_pb_deep_lp_candidates = int(three_pb_deep_lp_candidates)
        self.cut_purge_age = int(cut_purge_age)
        self.cut_purge_slack = float(cut_purge_slack)
        self.cut_purge_dual = float(cut_purge_dual)
        self.schedule_nogood_purge_enabled = bool(schedule_nogood_purge_enabled)
        self.schedule_nogood_purge_age = int(schedule_nogood_purge_age)
        self.schedule_nogood_purge_slack = float(schedule_nogood_purge_slack)
        self.schedule_nogood_purge_dual = float(schedule_nogood_purge_dual)
        self.pseudocosts: dict[str, PseudoCostRecord] = {}
        self.pool = RoutePool()
        self.cuts: list[Cut] = []
        self.cut_keys: set[tuple] = set()
        self.cut_inactive_age: dict[tuple, int] = {}
        self.cut_rounds_by_node: dict[int, int] = {}
        self.resource_cut_rounds_by_node: dict[int, int] = {}
        self.subset_row_cut_rounds_by_node: dict[int, int] = {}
        self.lm_rank1_cut_rounds_by_node: dict[int, int] = {}
        self.witness_rank1_cut_rounds_by_node: dict[int, int] = {}
        self.witness_rank1_memory: dict[tuple[int, ...], dict[str, Any]] = {}
        self.route_pack_branch_arc_scores: dict[tuple[int, int], float] = {}
        self.schedule_subset_cost_cut_rounds_by_node: dict[int, int] = {}
        self.schedule_capacity_cut_rounds_by_node: dict[int, int] = {}
        self.root_schedule_capacity_no_add_rounds_by_node: dict[int, int] = {}
        self.task_schedule_capacity_cut_rounds_by_node: dict[int, int] = {}
        self.task_schedule_capacity_no_add_rounds_by_node: dict[int, int] = {}
        self.task_schedule_capacity_no_improve_rounds_by_node: dict[int, int] = {}
        self.schedule_incompatibility_cut_rounds_by_node: dict[int, int] = {}
        self.route_set_schedule_packing_cut_rounds_by_node: dict[int, int] = {}
        self.route_set_schedule_packing_no_add_rounds_by_node: dict[int, int] = {}
        self.route_set_schedule_packing_no_improve_rounds_by_node: dict[int, int] = {}
        self.route_set_schedule_packing_oracle_time_total = 0.0
        self.weighted_route_schedule_packing_cut_rounds_by_node: dict[int, int] = {}
        self.weighted_route_schedule_packing_oracle_time_total = 0.0
        self.task_schedule_capacity_oracle_time_total = 0.0
        self.pending_cut_roi: list[dict[str, Any]] = []
        self.route_pack_roi_pricing_watch: list[dict[str, Any]] = []
        self.route_set_schedule_packing_cache: dict[tuple[tuple[int, ...], ...], tuple[int, int] | None] = {}
        self.weighted_route_schedule_packing_cache: dict[
            tuple[tuple[tuple[int, ...], ...], tuple[float, ...]],
            tuple[float, int] | None,
        ] = {}
        self.weighted_route_schedule_packing_witness_memory: dict[tuple[tuple[int, ...], ...], dict[str, Any]] = {}
        self.weighted_route_schedule_packing_successful_sets: set[tuple[tuple[int, ...], ...]] = set()
        self.schedule_conflict_witness_cache: dict[tuple[tuple[int, ...], ...], Any] = {}
        self.schedule_conflict_route_pack_cache: dict[tuple[tuple[int, ...], ...], tuple[int | None, int | None, bool]] = {}
        self.schedule_capacity_cache: dict[tuple[int, ...], ScheduleCapacityResult | None] = {}
        self.root_schedule_capacity_cache: dict[tuple[int, ...], ScheduleCapacityResult | None] = {}
        self.task_schedule_capacity_cache: dict[tuple[int, ...], TaskScheduleCapacityCacheEntry] = {}
        self.task_schedule_capacity_witness_memory: dict[tuple[int, ...], TaskScheduleCapacityWitness] = {}
        self.task_schedule_capacity_successful_sets: set[tuple[int, ...]] = set()
        self.task_schedule_capacity_branch_witnesses: list[dict[str, Any]] = []
        self.task_schedule_capacity_explained_route_sets: set[tuple[int, ...]] = set()
        self.schedule_subset_cost_cache: dict[tuple[int, ...], ScheduleSubsetCostResult | None] = {}
        self.schedule_pair_incompatibility_cache: dict[tuple[tuple[int, ...], tuple[int, ...]], bool] = {}
        self.resource_pair_incompatible: set[tuple[int, int]] | None = None
        self.resource_chromatic_cache: dict[tuple[int, ...], int] = {}
        self.next_cut_id = 0
        self.stats = BPCStats()
        self.incumbent: Incumbent | None = None
        self.next_node_id = 1
        self.start_time = time.perf_counter()
        self.abort_status: str | None = None
        self.pending_node_bound: float | None = None
        self.timeout_pending_node_certified: bool | None = None

    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time

    def _time_left(self) -> bool:
        return self.elapsed() <= self.time_limit + 1.0e-9

    def _record_incumbent(self, objective: float) -> None:
        elapsed = self.elapsed()
        if self.stats.time_to_first_incumbent is None:
            self.stats.time_to_first_incumbent = elapsed
        if self.stats.best_incumbent_value is None or objective < self.stats.best_incumbent_value - self.integer_tol:
            self.stats.best_incumbent_value = float(objective)
            self.stats.time_to_best_incumbent = elapsed

    def _log_fathom(self, *, node_id: int, reason: str, bound: float | None) -> None:
        self.stats.fathom_reasons[reason] = self.stats.fathom_reasons.get(reason, 0) + 1
        self.logger.log("fathom", node_id=node_id, reason=reason, bound=None if bound is None else round(bound, 6))

    def _register_cut_roi(
        self,
        node: BPCNode,
        family: str,
        added: int,
        before_objective: float | None,
        *,
        roi_context: dict[str, Any] | None = None,
    ) -> None:
        if added <= 0 or before_objective is None:
            return
        self.pending_cut_roi.append(
            {
                "node_id": int(node.id),
                "family": str(family),
                "added": int(added),
                "before_objective": float(before_objective),
                "roi_context": roi_context,
            }
        )

    def _complete_pending_cut_roi(self, node: BPCNode, solution: RMPSolution) -> int:
        if not self.pending_cut_roi or solution.objective is None:
            return 0
        added_from_roi = 0
        remaining: list[dict[str, Any]] = []
        for item in self.pending_cut_roi:
            if int(item["node_id"]) != int(node.id):
                remaining.append(item)
                continue
            before = float(item["before_objective"])
            after = float(solution.objective)
            improvement = after - before
            family = str(item["family"])
            added = int(item["added"])
            low_improvement = improvement < self.route_set_schedule_packing_min_objective_improvement
            roi_context = item.get("roi_context")
            if family == "schedule_route_set_packing":
                if low_improvement:
                    self.route_set_schedule_packing_no_improve_rounds_by_node[node.id] = (
                        self.route_set_schedule_packing_no_improve_rounds_by_node.get(node.id, 0) + 1
                    )
                    self.stats.route_set_schedule_packing_added_but_no_bound_improvement += added
                else:
                    self.route_set_schedule_packing_no_improve_rounds_by_node[node.id] = 0
            elif family == "weighted_schedule_route_set_packing":
                if low_improvement:
                    self.stats.weighted_route_schedule_packing_added_but_no_bound_improvement += added
            elif family == "task_schedule_capacity":
                if low_improvement:
                    self.task_schedule_capacity_no_improve_rounds_by_node[node.id] = (
                        self.task_schedule_capacity_no_improve_rounds_by_node.get(node.id, 0) + 1
                    )
                    self.stats.task_schedule_capacity_added_but_no_bound_improvement += added
                else:
                    self.task_schedule_capacity_no_improve_rounds_by_node[node.id] = 0
            self.logger.log(
                "cut_roi",
                node_id=node.id,
                family=family,
                added=added,
                before_objective=round(before, 9),
                after_objective=round(after, 9),
                objective_improvement=round(improvement, 9),
                low_improvement=bool(low_improvement),
            )
            if family in {"schedule_route_set_packing", "weighted_schedule_route_set_packing"} and roi_context:
                post_support = self._route_pack_roi_support_signatures(solution, roi_context.get("vehicles"))
                diagnostics = self._route_pack_roi_diagnostics_payload(
                    roi_context,
                    stage="post_rmp",
                    post_rmp_support_signatures=post_support,
                    new_pricing_signatures=tuple(),
                    before_objective=before,
                    after_objective=after,
                    objective_improvement=improvement,
                    low_improvement=bool(low_improvement),
                )
                self.logger.log("route_pack_roi_diagnostics", node_id=node.id, family=family, **diagnostics)
                self._record_witness_rank1_route_pack_roi(node.id, diagnostics)
                self._record_route_pack_branch_signal(diagnostics)
                added_from_roi += self._add_schedule_variant_route_pack_roi_cuts(
                    node,
                    solution,
                    diagnostics,
                    source=f"roi_{diagnostics.get('classification', 'unknown')}",
                )
                self.route_pack_roi_pricing_watch.append(
                    {
                        "node_id": int(node.id),
                        "family": family,
                        "roi_context": roi_context,
                        "post_rmp_support_signatures": post_support,
                        "before_objective": before,
                        "after_objective": after,
                        "objective_improvement": improvement,
                        "low_improvement": bool(low_improvement),
                    }
                )
        self.pending_cut_roi = remaining
        return added_from_roi

    def _route_pack_roi_support_signatures(
        self,
        solution: RMPSolution,
        vehicles: Any = None,
    ) -> tuple[tuple[int, ...], ...]:
        vehicle_filter = None if vehicles is None else {int(vehicle) for vehicle in vehicles}
        signatures = {
            route.signature
            for route, vehicle, value in solution.route_values
            if float(value) > self.integer_tol and (vehicle_filter is None or int(vehicle) in vehicle_filter)
        }
        return normalize_signatures(tuple(signatures))

    def _route_pack_roi_task_union(self, signatures: tuple[tuple[int, ...], ...]) -> tuple[int, ...]:
        return tuple(sorted({int(task) for signature in signatures for task in signature}))

    def _route_pack_roi_context(
        self,
        *,
        solution: RMPSolution,
        vehicles: list[int] | tuple[int, ...],
        cut_signatures: tuple[tuple[int, ...], ...],
        alpha_patterns: list[str] | tuple[str, ...] = (),
    ) -> dict[str, Any]:
        normalized = normalize_signatures(cut_signatures)
        vehicle_tuple = tuple(sorted({int(vehicle) for vehicle in vehicles}))
        return {
            "vehicles": vehicle_tuple,
            "cut_core_signatures": normalized,
            "cut_core_task_union": self._route_pack_roi_task_union(normalized),
            "pre_support_signatures": self._route_pack_roi_support_signatures(solution, vehicle_tuple),
            "pre_pool_signatures": normalize_signatures(tuple(self.pool.by_signature)),
            "pre_pool_size": len(self.pool.routes),
            "alpha_patterns": tuple(str(pattern) for pattern in alpha_patterns if str(pattern)),
        }

    def _route_pack_roi_overlap(self, signature: tuple[int, ...], core_tasks: set[int]) -> float:
        task_set = {int(task) for task in signature}
        if not task_set or not core_tasks:
            return 0.0
        return len(task_set & core_tasks) / float(max(1, min(len(task_set), len(core_tasks))))

    def _route_pack_roi_replacement_metrics(
        self,
        *,
        context: dict[str, Any],
        candidate_signatures: tuple[tuple[int, ...], ...],
        require_old_pool: bool,
        exclude_pre_support: bool,
    ) -> tuple[int, float, tuple[tuple[int, ...], ...]]:
        core_tasks = {int(task) for task in context.get("cut_core_task_union", ())}
        pre_support = {tuple(signature) for signature in context.get("pre_support_signatures", ())}
        old_pool = {tuple(signature) for signature in context.get("pre_pool_signatures", ())}
        core_signatures = {tuple(signature) for signature in context.get("cut_core_signatures", ())}
        replacements: list[tuple[int, ...]] = []
        max_overlap = 0.0
        for signature in candidate_signatures:
            signature = tuple(int(task) for task in signature)
            if signature in core_signatures:
                continue
            if exclude_pre_support and signature in pre_support:
                continue
            if require_old_pool and signature not in old_pool:
                continue
            overlap = self._route_pack_roi_overlap(signature, core_tasks)
            max_overlap = max(max_overlap, overlap)
            if overlap >= 0.5:
                replacements.append(signature)
        return len(replacements), max_overlap, normalize_signatures(tuple(replacements))

    def _route_pack_roi_classification(
        self,
        *,
        low_improvement: bool,
        pre_support_signatures: tuple[tuple[int, ...], ...],
        post_rmp_support_signatures: tuple[tuple[int, ...], ...],
        same_pool_replacement_count: int,
        pricing_replacement_count: int,
    ) -> str:
        if pricing_replacement_count > 0 and same_pool_replacement_count > 0:
            return "mixed"
        if pricing_replacement_count > 0:
            return "pricing_mousehole"
        if same_pool_replacement_count > 0:
            return "same_pool_degeneracy"
        if low_improvement:
            pre_set = set(pre_support_signatures)
            post_set = set(post_rmp_support_signatures)
            overlap = len(pre_set & post_set) / float(max(1, len(pre_set | post_set)))
            if overlap >= 0.8:
                return "objective_degeneracy_no_support_change"
        return "mixed"

    def _route_pack_roi_diagnostics_payload(
        self,
        context: dict[str, Any],
        *,
        stage: str,
        post_rmp_support_signatures: tuple[tuple[int, ...], ...],
        new_pricing_signatures: tuple[tuple[int, ...], ...],
        before_objective: float,
        after_objective: float,
        objective_improvement: float,
        low_improvement: bool,
    ) -> dict[str, Any]:
        pre_support = normalize_signatures(tuple(context.get("pre_support_signatures", ())))
        post_support = normalize_signatures(post_rmp_support_signatures)
        new_pricing = normalize_signatures(new_pricing_signatures)
        same_pool_count, max_old_overlap, same_pool_signatures = self._route_pack_roi_replacement_metrics(
            context=context,
            candidate_signatures=post_support,
            require_old_pool=True,
            exclude_pre_support=True,
        )
        pricing_count, max_new_overlap, pricing_signatures = self._route_pack_roi_replacement_metrics(
            context=context,
            candidate_signatures=new_pricing,
            require_old_pool=False,
            exclude_pre_support=True,
        )
        classification = self._route_pack_roi_classification(
            low_improvement=bool(low_improvement),
            pre_support_signatures=pre_support,
            post_rmp_support_signatures=post_support,
            same_pool_replacement_count=same_pool_count,
            pricing_replacement_count=pricing_count,
        )
        return {
            "stage": str(stage),
            "classification": classification,
            "vehicles": list(context.get("vehicles", ())),
            "cut_core_signature_count": len(context.get("cut_core_signatures", ())),
            "cut_core_signatures": [list(signature) for signature in context.get("cut_core_signatures", ())],
            "cut_core_task_union": list(context.get("cut_core_task_union", ())),
            "alpha_patterns": list(context.get("alpha_patterns", ())),
            "pre_pool_size": int(context.get("pre_pool_size", 0) or 0),
            "pre_support_signatures": [list(signature) for signature in pre_support],
            "post_rmp_support_signatures": [list(signature) for signature in post_support],
            "new_pricing_signatures": [list(signature) for signature in new_pricing],
            "same_pool_replacement_count": int(same_pool_count),
            "same_pool_replacement_signatures": [list(signature) for signature in same_pool_signatures],
            "pricing_replacement_count": int(pricing_count),
            "pricing_replacement_signatures": [list(signature) for signature in pricing_signatures],
            "max_task_overlap_old_pool": round(float(max_old_overlap), 6),
            "max_task_overlap_new_pricing": round(float(max_new_overlap), 6),
            "before_objective": round(float(before_objective), 9),
            "after_objective": round(float(after_objective), 9),
            "objective_improvement": round(float(objective_improvement), 9),
            "low_improvement": bool(low_improvement),
        }

    def _complete_route_pack_roi_pricing_watch(
        self,
        node: BPCNode,
        *,
        new_routes: list[RouteColumn],
    ) -> None:
        if not self.route_pack_roi_pricing_watch:
            return
        new_signatures = normalize_signatures(tuple(route.signature for route in new_routes))
        remaining: list[dict[str, Any]] = []
        for item in self.route_pack_roi_pricing_watch:
            if int(item.get("node_id", -1)) != int(node.id):
                remaining.append(item)
                continue
            context = item["roi_context"]
            diagnostics = self._route_pack_roi_diagnostics_payload(
                context,
                stage="post_pricing",
                post_rmp_support_signatures=item.get("post_rmp_support_signatures", ()),
                new_pricing_signatures=new_signatures,
                before_objective=float(item.get("before_objective", 0.0)),
                after_objective=float(item.get("after_objective", 0.0)),
                objective_improvement=float(item.get("objective_improvement", 0.0)),
                low_improvement=bool(item.get("low_improvement", False)),
            )
            self.logger.log(
                "route_pack_roi_diagnostics",
                node_id=node.id,
                family=str(item.get("family", "route_pack")),
                **diagnostics,
            )
            self._record_witness_rank1_route_pack_roi(node.id, diagnostics)
            self._record_route_pack_branch_signal(diagnostics)
        self.route_pack_roi_pricing_watch = remaining

    def initialize(self) -> None:
        for task in self.data.tasks:
            route = evaluate_route(self.data, (task,))
            if route is not None:
                self.pool.add(route)
        self._build_serial_schedule_incumbent()
        self._build_greedy_incumbent()
        self._add_exact_fleet_lower_bound_cut()

    def _allocate_cut_id(self) -> int:
        cut_id = self.next_cut_id
        self.next_cut_id += 1
        return cut_id

    def _allocate_cut_ids(self, count: int) -> int:
        first_id = self.next_cut_id
        self.next_cut_id += int(count)
        return first_id

    def _add_exact_fleet_lower_bound_cut(self) -> int:
        if not self.fleet_lower_bound_cuts_enabled:
            self.logger.log(
                "fleet_lower_bound",
                status="DISABLED",
                added=0,
                lower_bound=0,
                tasks=len(self.data.tasks),
            )
            return 0
        tasks = tuple(sorted(int(task) for task in self.data.tasks))
        if len(tasks) <= 1:
            self.logger.log(
                "fleet_lower_bound",
                status="TRIVIAL",
                added=0,
                lower_bound=1 if tasks else 0,
                tasks=len(tasks),
            )
            return 0
        started = time.perf_counter()
        oracle = exact_schedule_task_capacity(
            self.data,
            tasks,
            max_states=max(1, self.fleet_lower_bound_oracle_max_states),
        )
        elapsed = time.perf_counter() - started
        if oracle is None or not oracle.exact:
            self.stats.fleet_lower_bound_oracle_exact = False
            states = 0 if oracle is None else int(oracle.states_explored)
            self.logger.log(
                "fleet_lower_bound",
                status="ORACLE_INCOMPLETE",
                added=0,
                lower_bound=0,
                tasks=len(tasks),
                oracle_upper_bound=None,
                oracle_states=states,
                max_states=self.fleet_lower_bound_oracle_max_states,
                time=round(elapsed, 6),
            )
            return 0

        upper_bound = int(oracle.upper_bound)
        states = int(oracle.states_explored)
        self.stats.fleet_lower_bound_oracle_upper_bound = upper_bound
        self.stats.fleet_lower_bound_oracle_states = states
        self.stats.fleet_lower_bound_oracle_exact = True
        if upper_bound >= len(tasks):
            self.logger.log(
                "fleet_lower_bound",
                status="NO_CUT",
                added=0,
                lower_bound=1,
                tasks=len(tasks),
                oracle_upper_bound=upper_bound,
                oracle_states=states,
                max_states=self.fleet_lower_bound_oracle_max_states,
                time=round(elapsed, 6),
            )
            return 0
        if upper_bound <= 0:
            lower_bound = len(tasks) + 1
        else:
            lower_bound = int(math.ceil(len(tasks) / float(upper_bound)))
        lower_bound = max(2, lower_bound)
        cut = FleetLowerBoundCut(
            id=self._allocate_cut_id(),
            lower_bound=lower_bound,
            tasks=tasks,
            oracle_upper_bound=upper_bound,
            oracle_states=states,
        )
        if cut.key in self.cut_keys:
            self.logger.log(
                "fleet_lower_bound",
                status="DUPLICATE",
                added=0,
                lower_bound=lower_bound,
                tasks=len(tasks),
                oracle_upper_bound=upper_bound,
                oracle_states=states,
                max_states=self.fleet_lower_bound_oracle_max_states,
                time=round(elapsed, 6),
            )
            return 0
        self.cuts.append(cut)
        self.cut_keys.add(cut.key)
        self.stats.fleet_lower_bound_cuts_added += 1
        self.stats.fleet_lower_bound_value = lower_bound
        self.stats.cuts_added += 1
        self.logger.log(
            "fleet_lower_bound",
            status="ADDED",
            added=1,
            lower_bound=lower_bound,
            tasks=len(tasks),
            oracle_upper_bound=upper_bound,
            oracle_states=states,
            max_states=self.fleet_lower_bound_oracle_max_states,
            time=round(elapsed, 6),
        )
        return 1

    def _build_greedy_incumbent(self) -> None:
        # 中文注释：这个启发式只给 UB，不参与 lower bound 或最优性证明。
        # 356 秒主线先用 raw greedy objective 过滤，只有 raw 已经优于当前 UB 的
        # 构造才进入局部改进。对所有构造都做 improve 会给出过强初始 UB，
        # 改变早期 RMP dual 并缩窄 root route pool。
        best_assigned: dict[int, list[RouteColumn]] | None = None
        best_objective = float("inf") if self.incumbent is None else float(self.incumbent.objective)
        for order in self._construction_orders():
            assigned = self._construct_assignment(order)
            if assigned is None:
                continue
            raw_objective = self._assignment_objective(assigned)
            if raw_objective >= best_objective - self.integer_tol:
                continue
            improved = self._improve_assignment(assigned)
            objective = self._assignment_objective(improved)
            if objective < best_objective - self.integer_tol:
                best_assigned = improved
                best_objective = objective
        if best_assigned is None:
            return
        self._set_incumbent_from_assignment(best_assigned, node_id=0, source="greedy_schedule")

    def _build_serial_schedule_incumbent(self) -> None:
        """中文注释：快速构造单车串行 schedule，用于补足 route pool 和早期 UB。"""

        if not self.data.vehicles:
            return
        first_vehicle = int(self.data.vehicles[0])
        for order in self._construction_orders():
            routes = self._serial_routes_for_order(order)
            if routes is None:
                continue
            assigned = {vehicle: [] for vehicle in self.data.vehicles}
            assigned[first_vehicle] = routes
            self._set_incumbent_from_assignment(assigned, node_id=0, source="serial_schedule")

    def _serial_routes_for_order(self, order: tuple[int, ...]) -> list[RouteColumn] | None:
        if not order:
            return []

        routes: list[RouteColumn] = []
        current: list[int] = []
        ready_time = 0.0

        def close_current() -> bool:
            nonlocal ready_time, current
            if not current:
                return True
            route = evaluate_route(self.data, tuple(current))
            if route is None:
                return False
            evaluated = evaluate_route_at_start(self.data, route, ready_time)
            if evaluated is None:
                return False
            routes.append(route)
            ready_time = float(evaluated["ready_time"])
            current = []
            return True

        for task in order:
            candidate_sequence = tuple([*current, int(task)])
            candidate_route = evaluate_route(self.data, candidate_sequence)
            candidate_eval = (
                None if candidate_route is None else evaluate_route_at_start(self.data, candidate_route, ready_time)
            )
            if candidate_eval is not None:
                current = list(candidate_sequence)
                continue

            if not close_current():
                return None
            singleton = evaluate_route(self.data, (int(task),))
            singleton_eval = None if singleton is None else evaluate_route_at_start(self.data, singleton, ready_time)
            if singleton_eval is None:
                return None
            current = [int(task)]

        if not close_current():
            return None
        if len(routes) > self.data.sortie_limit:
            return None
        if not check_route_set_schedule_feasible(self.data, routes).feasible:
            return None
        return routes

    def _construction_orders(self) -> list[tuple[int, ...]]:
        singleton_cost = {}
        for task in self.data.tasks:
            route = evaluate_route(self.data, (task,))
            singleton_cost[int(task)] = float("inf") if route is None else float(route.cost)
        tasks = list(self.data.tasks)
        orders = [
            tuple(sorted(tasks, key=lambda item: (self.data.task_value(item, "D"), self.data.task_value(item, "r"), item))),
            tuple(sorted(tasks, key=lambda item: (self.data.task_value(item, "r"), self.data.task_value(item, "D"), item))),
            tuple(sorted(tasks, key=lambda item: (-self.data.task_value(item, "d"), self.data.task_value(item, "D"), item))),
            tuple(sorted(tasks, key=lambda item: (-self.data.task_value(item, "g"), self.data.task_value(item, "D"), item))),
            tuple(sorted(tasks, key=lambda item: (-singleton_cost[int(item)], self.data.task_value(item, "D"), item))),
            tuple(sorted(tasks, key=lambda item: (singleton_cost[int(item)], self.data.task_value(item, "D"), item))),
        ]
        unique: list[tuple[int, ...]] = []
        seen = set()
        for order in orders:
            if order in seen:
                continue
            seen.add(order)
            unique.append(order)
        return unique

    def _construct_assignment(self, order: tuple[int, ...]) -> dict[int, list[RouteColumn]] | None:
        assigned: dict[int, list[RouteColumn]] = {vehicle: [] for vehicle in self.data.vehicles}
        assigned_tasks: set[int] = set()
        for task in order:
            best = self._best_greedy_insertion(assigned, task)
            if best is None:
                return None
            _score, vehicle, routes = best
            assigned[vehicle] = list(routes)
            assigned_tasks.add(int(task))
        if assigned_tasks != set(self.data.tasks):
            return None
        return assigned

    def _best_greedy_insertion(self, assigned: dict[int, list[RouteColumn]], task: int):
        best = None
        for vehicle in self.data.vehicles:
            current_routes = assigned[vehicle]
            current_cost = sum(route.cost for route in current_routes)

            if len(current_routes) < self.data.sortie_limit:
                route = evaluate_route(self.data, (task,))
                if route is not None:
                    candidate_routes = [*current_routes, route]
                    checked = check_route_set_schedule_feasible(self.data, candidate_routes)
                    if checked.feasible:
                        fixed_delta = self.data.fixed_vehicle_cost if not current_routes else 0.0
                        score = (
                            float(route.cost) + fixed_delta,
                            int(not current_routes),
                            float(checked.ready_time or 0.0),
                            vehicle,
                            len(current_routes),
                            route.signature,
                        )
                        if best is None or score < best[0]:
                            best = (score, vehicle, candidate_routes)

            for route_index, old_route in enumerate(current_routes):
                old_sequence = list(old_route.tasks)
                for position in range(len(old_sequence) + 1):
                    sequence = tuple([*old_sequence[:position], int(task), *old_sequence[position:]])
                    route = evaluate_route(self.data, sequence)
                    if route is None:
                        continue
                    candidate_routes = [*current_routes[:route_index], route, *current_routes[route_index + 1 :]]
                    checked = check_route_set_schedule_feasible(self.data, candidate_routes)
                    if not checked.feasible:
                        continue
                    delta_cost = sum(item.cost for item in candidate_routes) - current_cost
                    score = (
                        float(delta_cost),
                        0,
                        float(checked.ready_time or 0.0),
                        vehicle,
                        route_index,
                        route.signature,
                    )
                    if best is None or score < best[0]:
                        best = (score, vehicle, candidate_routes)
        return best

    def _assignment_objective(self, assigned: dict[int, list[RouteColumn]]) -> float:
        used = sum(1 for routes in assigned.values() if routes)
        return sum(route.cost for routes in assigned.values() for route in routes) + used * self.data.fixed_vehicle_cost

    def _assignment_feasible(self, assigned: dict[int, list[RouteColumn]]) -> bool:
        covered: list[int] = []
        for routes in assigned.values():
            if len(routes) > self.data.sortie_limit:
                return False
            checked = check_route_set_schedule_feasible(self.data, routes)
            if not checked.feasible:
                return False
            for route in routes:
                covered.extend(route.tasks)
        return sorted(covered) == sorted(self.data.tasks) and len(covered) == len(set(covered))

    def _set_incumbent_from_assignment(self, assigned: dict[int, list[RouteColumn]], *, node_id: int, source: str) -> bool:
        if not self._assignment_feasible(assigned):
            return False
        stored_assigned = {
            vehicle: [self.pool.add(route) for route in routes]
            for vehicle, routes in assigned.items()
        }
        objective = self._assignment_objective(stored_assigned)
        if self.incumbent is not None and objective >= self.incumbent.objective - self.integer_tol:
            return False
        selected = [
            (route, vehicle, 1.0)
            for vehicle, routes in stored_assigned.items()
            for route in routes
        ]
        used = {vehicle for _route, vehicle, _value in selected}
        self.incumbent = Incumbent(
            objective=objective,
            route_values=selected,
            y_values={vehicle: float(vehicle in used) for vehicle in self.data.vehicles},
            node_id=node_id,
        )
        self._record_incumbent(objective)
        self.logger.log("incumbent", node_id=node_id, objective=round(objective, 6), source=source)
        return True

    def _improve_assignment(self, assigned: dict[int, list[RouteColumn]]) -> dict[int, list[RouteColumn]]:
        current = {vehicle: list(routes) for vehicle, routes in assigned.items()}
        current = self._improve_route_sequences(current)
        for _round in range(200):
            improved = self._best_relocate_move(current)
            if improved is None:
                break
            current = self._improve_route_sequences(improved)
        return current

    def _improve_route_sequences(self, assigned: dict[int, list[RouteColumn]]) -> dict[int, list[RouteColumn]]:
        improved = {vehicle: list(routes) for vehicle, routes in assigned.items()}
        for vehicle, routes in list(improved.items()):
            changed_routes = list(routes)
            for index, route in enumerate(routes):
                better = self._best_sequence_for_task_set(route.tasks)
                if better is not None and better.cost < route.cost - self.integer_tol:
                    candidate_routes = [*changed_routes[:index], better, *changed_routes[index + 1 :]]
                    if check_route_set_schedule_feasible(self.data, candidate_routes).feasible:
                        changed_routes = candidate_routes
            improved[vehicle] = changed_routes
        return improved

    def _best_sequence_for_task_set(self, tasks: tuple[int, ...]) -> RouteColumn | None:
        if len(tasks) <= 1 or len(tasks) > 7:
            return evaluate_route(self.data, tasks)
        best: RouteColumn | None = None
        for sequence in permutations(tasks):
            route = evaluate_route(self.data, sequence)
            if route is None:
                continue
            if best is None or route.cost < best.cost - self.integer_tol:
                best = route
        return best

    def _best_relocate_move(self, assigned: dict[int, list[RouteColumn]]) -> dict[int, list[RouteColumn]] | None:
        current_objective = self._assignment_objective(assigned)
        best_objective = current_objective
        best_assigned: dict[int, list[RouteColumn]] | None = None

        for source_vehicle, source_routes in assigned.items():
            for source_index, source_route in enumerate(source_routes):
                base = {vehicle: list(routes) for vehicle, routes in assigned.items()}
                del base[source_vehicle][source_index]
                for dest_vehicle in self.data.vehicles:
                    if dest_vehicle == source_vehicle:
                        continue
                    if len(base[dest_vehicle]) >= self.data.sortie_limit:
                        continue
                    candidate = {vehicle: list(routes) for vehicle, routes in base.items()}
                    candidate[dest_vehicle] = [*candidate[dest_vehicle], source_route]
                    if not self._assignment_feasible(candidate):
                        continue
                    objective = self._assignment_objective(candidate)
                    if objective < best_objective - self.integer_tol:
                        best_objective = objective
                        best_assigned = candidate

        for source_vehicle, source_routes in assigned.items():
            for source_index, source_route in enumerate(source_routes):
                for task in source_route.tasks:
                    base = {vehicle: list(routes) for vehicle, routes in assigned.items()}
                    remaining_sequence = tuple(item for item in source_route.tasks if item != task)
                    del base[source_vehicle][source_index]
                    if remaining_sequence:
                        remaining_route = self._best_sequence_for_task_set(remaining_sequence)
                        if remaining_route is None:
                            continue
                        base[source_vehicle].insert(source_index, remaining_route)

                    for dest_vehicle in self.data.vehicles:
                        candidate = self._best_insert_task_into_vehicle(base, dest_vehicle, int(task))
                        if candidate is None:
                            continue
                        objective = self._assignment_objective(candidate)
                        if objective < best_objective - self.integer_tol and self._assignment_feasible(candidate):
                            best_objective = objective
                            best_assigned = candidate
        return best_assigned

    def _best_insert_task_into_vehicle(
        self,
        base: dict[int, list[RouteColumn]],
        dest_vehicle: int,
        task: int,
    ) -> dict[int, list[RouteColumn]] | None:
        current_routes = base[dest_vehicle]
        best_score = float("inf")
        best_routes: list[RouteColumn] | None = None

        if len(current_routes) < self.data.sortie_limit:
            route = evaluate_route(self.data, (task,))
            if route is not None:
                candidate_routes = [*current_routes, route]
                checked = check_route_set_schedule_feasible(self.data, candidate_routes)
                if checked.feasible:
                    best_score = self._vehicle_routes_cost(candidate_routes)
                    best_routes = candidate_routes

        for route_index, old_route in enumerate(current_routes):
            old_sequence = list(old_route.tasks)
            for position in range(len(old_sequence) + 1):
                sequence = tuple([*old_sequence[:position], int(task), *old_sequence[position:]])
                route = self._best_sequence_for_task_set(sequence)
                if route is None:
                    continue
                candidate_routes = [*current_routes[:route_index], route, *current_routes[route_index + 1 :]]
                checked = check_route_set_schedule_feasible(self.data, candidate_routes)
                if not checked.feasible:
                    continue
                score = self._vehicle_routes_cost(candidate_routes)
                if score < best_score - self.integer_tol:
                    best_score = score
                    best_routes = candidate_routes

        if best_routes is None:
            return None
        candidate = {vehicle: list(routes) for vehicle, routes in base.items()}
        candidate[dest_vehicle] = best_routes
        return candidate

    def _vehicle_routes_cost(self, routes: list[RouteColumn]) -> float:
        return sum(route.cost for route in routes) + (self.data.fixed_vehicle_cost if routes else 0.0)

    def _repair_route_assignment(self, routes: list[RouteColumn]) -> dict[int, list[RouteColumn]] | None:
        ordered_routes = sorted(routes, key=lambda route: (-len(route.tasks), -route.cycle_time, route.signature))
        assigned: dict[int, list[RouteColumn]] = {vehicle: [] for vehicle in self.data.vehicles}
        best: dict[int, list[RouteColumn]] | None = None
        best_objective = float("inf")
        visited = 0
        max_states = 50000

        def search(index: int) -> None:
            nonlocal best, best_objective, visited
            visited += 1
            if visited > max_states:
                return
            partial_objective = self._assignment_objective(assigned)
            if partial_objective >= best_objective - self.integer_tol:
                return
            if index == len(ordered_routes):
                candidate = {vehicle: list(items) for vehicle, items in assigned.items()}
                if not self._assignment_feasible(candidate):
                    return
                objective = self._assignment_objective(candidate)
                if objective < best_objective - self.integer_tol:
                    best_objective = objective
                    best = candidate
                return

            route = ordered_routes[index]
            tried_empty_vehicle = False
            vehicles = sorted(self.data.vehicles, key=lambda vehicle: (len(assigned[vehicle]) == 0, len(assigned[vehicle]), vehicle))
            for vehicle in vehicles:
                if len(assigned[vehicle]) >= self.data.sortie_limit:
                    continue
                if not assigned[vehicle]:
                    if tried_empty_vehicle:
                        continue
                    tried_empty_vehicle = True
                candidate_routes = [*assigned[vehicle], route]
                if not check_route_set_schedule_feasible(self.data, candidate_routes).feasible:
                    continue
                assigned[vehicle].append(route)
                search(index + 1)
                assigned[vehicle].pop()

        search(0)
        return best

    def solve(self) -> TreeResult:
        self.initialize()
        open_nodes: list[BPCNode] = [BPCNode(priority=0.0, id=0, depth=0, lower_bound=0.0)]
        self.logger.log(
            "start",
            instance=self.data.name,
            tasks=len(self.data.tasks),
            vehicles=len(self.data.vehicles),
            initial_routes=len(self.pool.routes),
            initial_incumbent=None if self.incumbent is None else round(self.incumbent.objective, 6),
            task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
            schedule_capacity_cuts_enabled=self.schedule_capacity_cuts_enabled,
            schedule_capacity_separation_enabled=self.schedule_capacity_separation_enabled,
            root_schedule_capacity_cuts_enabled=self.root_schedule_capacity_cuts_enabled,
            root_schedule_capacity_max_depth=self.root_schedule_capacity_max_depth,
            task_schedule_capacity_cuts_enabled=self.task_schedule_capacity_cuts_enabled,
            task_schedule_capacity_max_depth=self.task_schedule_capacity_max_depth,
            task_schedule_capacity_pair_budget=self.task_schedule_capacity_pair_budget,
            task_schedule_capacity_triple_budget=self.task_schedule_capacity_triple_budget,
            task_schedule_capacity_small_set_budget=self.task_schedule_capacity_small_set_budget,
            weighted_route_schedule_packing_cuts_enabled=self.weighted_route_schedule_packing_cuts_enabled,
            weighted_route_schedule_packing_max_depth=self.weighted_route_schedule_packing_max_depth,
            weighted_route_schedule_packing_max_candidates=self.weighted_route_schedule_packing_max_candidates,
            fleet_lower_bound_cuts_enabled=self.fleet_lower_bound_cuts_enabled,
            fleet_lower_bound_oracle_max_states=self.fleet_lower_bound_oracle_max_states,
            route_set_schedule_packing_roi_guard_enabled=self.route_set_schedule_packing_roi_guard_enabled,
            schedule_pack_diagnostic_enabled=self.schedule_pack_diagnostic_enabled,
            schedule_pack_relaxation_enabled=self.schedule_pack_relaxation_enabled,
            schedule_pack_full_pricing_enabled=self.schedule_pack_full_pricing_enabled,
            schedule_pack_adaptive_enabled=self.schedule_pack_adaptive_enabled,
            route_enumeration_adaptive_enabled=self.route_enumeration_adaptive_enabled,
            route_pool_hygiene_diagnostics_enabled=self.route_pool_hygiene_diagnostics_enabled,
            route_pool_hygiene_diagnostics_min_routes=self.route_pool_hygiene_diagnostics_min_routes,
            route_pool_hygiene_admission_enabled=self.route_pool_hygiene_admission_enabled,
            route_pool_hygiene_admission_max_per_task_set=self.route_pool_hygiene_admission_max_per_task_set,
            route_pool_hygiene_admission_min_depth=self.route_pool_hygiene_admission_min_depth,
            route_pool_hygiene_admission_protect_active_task_sets=(
                self.route_pool_hygiene_admission_protect_active_task_sets
            ),
            route_pool_hygiene_admission_protect_cut_task_sets=(
                self.route_pool_hygiene_admission_protect_cut_task_sets
            ),
            route_pool_hygiene_admission_protect_incumbent_task_sets=(
                self.route_pool_hygiene_admission_protect_incumbent_task_sets
            ),
            route_pool_hygiene_admission_protect_branch_task_sets=(
                self.route_pool_hygiene_admission_protect_branch_task_sets
            ),
            restricted_master_adaptive_enabled=self.restricted_master_adaptive_enabled,
            restricted_master_adaptive_min_depth=self.restricted_master_adaptive_min_depth,
            restricted_master_adaptive_after_failures=self.restricted_master_adaptive_after_failures,
            restricted_master_adaptive_reduced_time_limit=self.restricted_master_adaptive_reduced_time_limit,
            restricted_master_adaptive_skip_after_failures=self.restricted_master_adaptive_skip_after_failures,
            restricted_master_adaptive_productivity_guard_enabled=(
                self.restricted_master_adaptive_productivity_guard_enabled
            ),
            restricted_master_adaptive_productive_after_failures=(
                self.restricted_master_adaptive_productive_after_failures
            ),
            restricted_master_adaptive_productive_max_consecutive_skips=(
                self.restricted_master_adaptive_productive_max_consecutive_skips
            ),
            restricted_master_scan_solution_pool_enabled=self.restricted_master_scan_solution_pool_enabled,
            restricted_master_scan_solution_pool_limit=self.restricted_master_scan_solution_pool_limit,
            route_pool_restart_enabled=self.route_pool_restart_enabled,
            route_pool_restart_node_start_enabled=self.route_pool_restart_node_start_enabled,
            route_pool_restart_min_depth=self.route_pool_restart_min_depth,
            route_pool_restart_max_depth=self.route_pool_restart_max_depth,
            route_pool_restart_max_routes=self.route_pool_restart_max_routes,
            route_pool_restart_min_global_routes=self.route_pool_restart_min_global_routes,
            route_pool_restart_keep_recent_rounds=self.route_pool_restart_keep_recent_rounds,
            route_pool_restart_max_routes_per_task_set=self.route_pool_restart_max_routes_per_task_set,
            route_pool_restart_cleanup_enabled=self.route_pool_restart_cleanup_enabled,
            route_pool_restart_branch_with_global_solution=self.route_pool_restart_branch_with_global_solution,
            early_bound_fathom_before_cuts_enabled=self.early_bound_fathom_before_cuts_enabled,
            persistent_rmp_enabled=self.persistent_rmp_enabled,
        )

        status = "UNKNOWN"
        while open_nodes and self._time_left() and self.stats.nodes_processed < self.max_nodes and self.abort_status is None:
            node = heapq.heappop(open_nodes)
            if self.incumbent is not None and node.lower_bound >= self.incumbent.objective - self.integer_tol:
                self.stats.fathomed_bound += 1
                self._log_fathom(node_id=node.id, reason="bound_before_process", bound=node.lower_bound)
                continue
            self.logger.log("node_start", node_id=node.id, depth=node.depth, node_lb=round(node.lower_bound, 6), open_nodes=len(open_nodes))
            children = self._process_node(node)
            self.stats.nodes_processed += 1
            for child in children:
                heapq.heappush(open_nodes, child)
            if children:
                self.stats.branch_nodes += 1
            self.logger.log(
                "node_end",
                node_id=node.id,
                depth=node.depth,
                children=len(children),
                open_nodes=len(open_nodes),
                nodes_processed=self.stats.nodes_processed,
                certified_lower_bound=round(node.lower_bound, 6),
                incumbent=None if self.incumbent is None else round(self.incumbent.objective, 6),
            )

        if self.abort_status is not None:
            status = self.abort_status
        elif open_nodes and not self._time_left():
            status = "TIME_LIMIT"
        elif open_nodes and self.stats.nodes_processed >= self.max_nodes:
            status = "NODE_LIMIT"
        elif self.incumbent is None:
            status = "INFEASIBLE"
        else:
            status = "OPTIMAL"

        dual = self._global_lower_bound(open_nodes, status)
        diagnostic_dual = self._diagnostic_lower_bound(open_nodes)
        primal = None if self.incumbent is None else self.incumbent.objective
        gap = None
        if primal is not None and dual is not None and abs(primal) > 1.0e-12:
            gap = max(0.0, (primal - dual) / abs(primal))
        diagnostic_gap = None
        if primal is not None and diagnostic_dual is not None and abs(primal) > 1.0e-12:
            diagnostic_gap = max(0.0, (primal - diagnostic_dual) / abs(primal))
        self.stats.diagnostic_dual_bound = diagnostic_dual
        self.stats.diagnostic_gap = diagnostic_gap
        self.stats.best_open_node_bound = min([node.lower_bound for node in open_nodes], default=None)
        self.stats.pending_node_bound = self.pending_node_bound
        self.stats.open_nodes_remaining = len(open_nodes)
        self.stats.timeout_pending_node_certified = self.timeout_pending_node_certified
        self.stats.official_bound_available = dual is not None
        result = TreeResult(
            status=status,
            primal_bound=primal,
            dual_bound=dual,
            gap=gap,
            solving_time=self.elapsed(),
            node_count=self.stats.nodes_processed,
            stats=self.stats,
            routes=self.pool.routes,
            cuts=self.cuts,
            incumbent=self.incumbent,
        )
        self.logger.log(
            "finish",
            status=status,
            primal_bound=None if primal is None else round(primal, 6),
            dual_bound=None if dual is None else round(dual, 6),
            gap=None if gap is None else round(gap, 6),
            diagnostic_dual_bound=None if diagnostic_dual is None else round(diagnostic_dual, 6),
            diagnostic_gap=None if diagnostic_gap is None else round(diagnostic_gap, 6),
            best_open_node_bound=None if self.stats.best_open_node_bound is None else round(self.stats.best_open_node_bound, 6),
            pending_node_bound=None if self.pending_node_bound is None else round(self.pending_node_bound, 6),
            last_certified_node_bound=None
            if self.stats.last_certified_node_bound is None
            else round(self.stats.last_certified_node_bound, 6),
            root_relaxation=None if self.stats.root_relaxation is None else round(self.stats.root_relaxation, 6),
            nodes=self.stats.nodes_processed,
            routes=len(self.pool.routes),
            cuts=len(self.cuts),
            crossing_cuts_added=self.stats.crossing_cuts_added,
            crossing_cuts_upgraded=self.stats.crossing_cuts_upgraded,
            subset_row_cuts_added=self.stats.subset_row_cuts_added,
            lm_rank1_cuts_added=self.stats.lm_rank1_cuts_added,
            robust_capacity_cuts_added=self.stats.robust_capacity_cuts_added,
            resource_lower_bound_cuts_added=self.stats.resource_lower_bound_cuts_added,
            schedule_subset_cost_cuts_added=self.stats.schedule_subset_cost_cuts_added,
            schedule_pair_conflict_cuts_added=self.stats.schedule_pair_conflict_cuts_added,
            schedule_nogood_cuts_added=self.stats.schedule_nogood_cuts_added,
            schedule_capacity_cuts_added=self.stats.schedule_capacity_cuts_added,
            root_schedule_capacity_cuts_added=self.stats.root_schedule_capacity_cuts_added,
            root_schedule_capacity_oracle_queries=self.stats.root_schedule_capacity_oracle_queries,
            root_schedule_capacity_oracle_incomplete=self.stats.root_schedule_capacity_oracle_incomplete,
            root_schedule_capacity_oracle_time=round(self.stats.root_schedule_capacity_oracle_time, 6),
            root_schedule_capacity_cache_hits=self.stats.root_schedule_capacity_cache_hits,
            root_schedule_capacity_candidates_generated=self.stats.root_schedule_capacity_candidates_generated,
            root_schedule_capacity_candidates_after_precheck=self.stats.root_schedule_capacity_candidates_after_precheck,
            root_schedule_capacity_best_violation=round(self.stats.root_schedule_capacity_best_violation, 9),
            task_schedule_capacity_cuts_added=self.stats.task_schedule_capacity_cuts_added,
            task_schedule_capacity_candidates_generated=self.stats.task_schedule_capacity_candidates_generated,
            task_schedule_capacity_candidates_after_precheck=self.stats.task_schedule_capacity_candidates_after_precheck,
            task_schedule_capacity_pair_candidates=self.stats.task_schedule_capacity_pair_candidates,
            task_schedule_capacity_triple_candidates=self.stats.task_schedule_capacity_triple_candidates,
            task_schedule_capacity_small_set_candidates=self.stats.task_schedule_capacity_small_set_candidates,
            task_schedule_capacity_candidates_by_source=self.stats.task_schedule_capacity_candidates_by_source,
            task_schedule_capacity_prechecked_by_source=self.stats.task_schedule_capacity_prechecked_by_source,
            task_schedule_capacity_oracle_requests=self.stats.task_schedule_capacity_oracle_requests,
            task_schedule_capacity_oracle_computations=self.stats.task_schedule_capacity_oracle_computations,
            task_schedule_capacity_cache_hits=self.stats.task_schedule_capacity_cache_hits,
            task_schedule_capacity_oracle_incomplete=self.stats.task_schedule_capacity_oracle_incomplete,
            task_schedule_capacity_exact_not_tight=self.stats.task_schedule_capacity_exact_not_tight,
            task_schedule_capacity_exact_tight_not_violated=self.stats.task_schedule_capacity_exact_tight_not_violated,
            task_schedule_capacity_violated_candidates=self.stats.task_schedule_capacity_violated_candidates,
            task_schedule_capacity_best_violation=round(self.stats.task_schedule_capacity_best_violation, 9),
            task_schedule_capacity_oracle_time=round(self.stats.task_schedule_capacity_oracle_time, 6),
            task_schedule_capacity_oracle_states_total=self.stats.task_schedule_capacity_oracle_states_total,
            task_schedule_capacity_oracle_states_max=self.stats.task_schedule_capacity_oracle_states_max,
            task_schedule_capacity_cuts_copied_to_all_vehicles=self.stats.task_schedule_capacity_cuts_copied_to_all_vehicles,
            task_schedule_capacity_stopped_by_no_add=self.stats.task_schedule_capacity_stopped_by_no_add,
            task_schedule_capacity_stopped_by_no_improvement=self.stats.task_schedule_capacity_stopped_by_no_improvement,
            task_schedule_capacity_stopped_by_node_time_budget=self.stats.task_schedule_capacity_stopped_by_node_time_budget,
            task_schedule_capacity_stopped_by_global_time_budget=self.stats.task_schedule_capacity_stopped_by_global_time_budget,
            task_schedule_capacity_branch_signal_candidates=self.stats.task_schedule_capacity_branch_signal_candidates,
            task_schedule_capacity_branch_signal_applied=self.stats.task_schedule_capacity_branch_signal_applied,
            schedule_clique_conflict_cuts_added=self.stats.schedule_clique_conflict_cuts_added,
            schedule_route_set_packing_cuts_added=self.stats.schedule_route_set_packing_cuts_added,
            schedule_variant_route_pack_cuts_added=self.stats.schedule_variant_route_pack_cuts_added,
            schedule_variant_route_pack_candidates=self.stats.schedule_variant_route_pack_candidates,
            schedule_variant_route_pack_expanded_candidates=self.stats.schedule_variant_route_pack_expanded_candidates,
            schedule_variant_route_pack_oracle_queries=self.stats.schedule_variant_route_pack_oracle_queries,
            schedule_variant_route_pack_cache_hits=self.stats.schedule_variant_route_pack_cache_hits,
            schedule_variant_route_pack_oracle_incomplete=self.stats.schedule_variant_route_pack_oracle_incomplete,
            schedule_variant_route_pack_exact_not_tight=self.stats.schedule_variant_route_pack_exact_not_tight,
            schedule_variant_route_pack_exact_not_violated=self.stats.schedule_variant_route_pack_exact_not_violated,
            schedule_variant_route_pack_violated_candidates=self.stats.schedule_variant_route_pack_violated_candidates,
            schedule_variant_route_pack_duplicate_skips=self.stats.schedule_variant_route_pack_duplicate_skips,
            schedule_variant_route_pack_best_violation=round(self.stats.schedule_variant_route_pack_best_violation, 9),
            schedule_variant_route_pack_oracle_time=round(self.stats.schedule_variant_route_pack_oracle_time, 6),
            schedule_variant_route_pack_oracle_states_total=self.stats.schedule_variant_route_pack_oracle_states_total,
            schedule_variant_route_pack_oracle_states_max=self.stats.schedule_variant_route_pack_oracle_states_max,
            route_set_schedule_packing_oracle_queries=self.stats.route_set_schedule_packing_oracle_queries,
            route_set_schedule_packing_oracle_time=round(self.stats.route_set_schedule_packing_oracle_time, 6),
            route_set_schedule_packing_cache_hits=self.stats.route_set_schedule_packing_cache_hits,
            route_set_schedule_packing_added_but_no_bound_improvement=(
                self.stats.route_set_schedule_packing_added_but_no_bound_improvement
            ),
            witness_rank1_cuts_added=self.stats.witness_rank1_cuts_added,
            witness_rank1_subset_row_cuts_added=self.stats.witness_rank1_subset_row_cuts_added,
            witness_rank1_lm_rank1_cuts_added=self.stats.witness_rank1_lm_rank1_cuts_added,
            witness_rank1_candidates_generated=self.stats.witness_rank1_candidates_generated,
            witness_rank1_candidates_after_precheck=self.stats.witness_rank1_candidates_after_precheck,
            witness_rank1_violated_candidates=self.stats.witness_rank1_violated_candidates,
            witness_rank1_duplicate_skips=self.stats.witness_rank1_duplicate_skips,
            witness_rank1_best_violation=round(self.stats.witness_rank1_best_violation, 9),
            witness_rank1_candidates_by_source=self.stats.witness_rank1_candidates_by_source,
            weighted_route_schedule_packing_cuts_added=self.stats.weighted_route_schedule_packing_cuts_added,
            weighted_route_schedule_packing_candidates_generated=(
                self.stats.weighted_route_schedule_packing_candidates_generated
            ),
            weighted_route_schedule_packing_candidates_after_precheck=(
                self.stats.weighted_route_schedule_packing_candidates_after_precheck
            ),
            weighted_route_schedule_packing_candidates_by_source=(
                self.stats.weighted_route_schedule_packing_candidates_by_source
            ),
            weighted_route_schedule_packing_candidates_by_alpha=(
                self.stats.weighted_route_schedule_packing_candidates_by_alpha
            ),
            weighted_route_schedule_packing_oracle_requests=self.stats.weighted_route_schedule_packing_oracle_requests,
            weighted_route_schedule_packing_oracle_computations=(
                self.stats.weighted_route_schedule_packing_oracle_computations
            ),
            weighted_route_schedule_packing_cache_hits=self.stats.weighted_route_schedule_packing_cache_hits,
            weighted_route_schedule_packing_oracle_incomplete=self.stats.weighted_route_schedule_packing_oracle_incomplete,
            weighted_route_schedule_packing_exact_not_violated=(
                self.stats.weighted_route_schedule_packing_exact_not_violated
            ),
            weighted_route_schedule_packing_violated_candidates=(
                self.stats.weighted_route_schedule_packing_violated_candidates
            ),
            weighted_route_schedule_packing_best_violation=round(
                self.stats.weighted_route_schedule_packing_best_violation,
                9,
            ),
            weighted_route_schedule_packing_oracle_time=round(self.stats.weighted_route_schedule_packing_oracle_time, 6),
            weighted_route_schedule_packing_oracle_states_total=(
                self.stats.weighted_route_schedule_packing_oracle_states_total
            ),
            weighted_route_schedule_packing_oracle_states_max=self.stats.weighted_route_schedule_packing_oracle_states_max,
            weighted_route_schedule_packing_added_but_no_bound_improvement=(
                self.stats.weighted_route_schedule_packing_added_but_no_bound_improvement
            ),
            weighted_route_schedule_packing_stopped_by_budget=self.stats.weighted_route_schedule_packing_stopped_by_budget,
            weighted_route_schedule_packing_duplicate_skips=self.stats.weighted_route_schedule_packing_duplicate_skips,
            fleet_lower_bound_cuts_added=self.stats.fleet_lower_bound_cuts_added,
            fleet_lower_bound_value=self.stats.fleet_lower_bound_value,
            fleet_lower_bound_oracle_upper_bound=self.stats.fleet_lower_bound_oracle_upper_bound,
            fleet_lower_bound_oracle_states=self.stats.fleet_lower_bound_oracle_states,
            fleet_lower_bound_oracle_exact=self.stats.fleet_lower_bound_oracle_exact,
            cuts_purged=self.stats.cuts_purged,
            schedule_pack_diagnostic_status=self.stats.schedule_pack_diagnostic_status,
            schedule_pack_diagnostic_objective=None
            if self.stats.schedule_pack_diagnostic_objective is None
            else round(self.stats.schedule_pack_diagnostic_objective, 6),
            schedule_pack_diagnostic_gap_vs_root=None
            if self.stats.schedule_pack_diagnostic_gap_vs_root is None
            else round(self.stats.schedule_pack_diagnostic_gap_vs_root, 6),
            schedule_pack_diagnostic_columns=self.stats.schedule_pack_diagnostic_columns,
            schedule_pack_diagnostic_time=round(self.stats.schedule_pack_diagnostic_time, 6),
            schedule_pack_relaxation_calls=self.stats.schedule_pack_relaxation_calls,
            schedule_pack_relaxation_root_objective=None
            if self.stats.schedule_pack_relaxation_root_objective is None
            else round(self.stats.schedule_pack_relaxation_root_objective, 6),
            schedule_pack_relaxation_best_objective=None
            if self.stats.schedule_pack_relaxation_best_objective is None
            else round(self.stats.schedule_pack_relaxation_best_objective, 6),
            schedule_pack_relaxation_time=round(self.stats.schedule_pack_relaxation_time, 6),
            schedule_pack_relaxation_full_exact=self.stats.schedule_pack_relaxation_full_exact,
            schedule_pack_relaxation_full_pricing_states=self.stats.schedule_pack_relaxation_full_pricing_states,
            schedule_pack_relaxation_full_pricing_time=round(self.stats.schedule_pack_relaxation_full_pricing_time, 6),
            schedule_pack_adaptive_decisions=self.stats.schedule_pack_adaptive_decisions,
            schedule_pack_adaptive_runs=self.stats.schedule_pack_adaptive_runs,
            schedule_pack_adaptive_skips=self.stats.schedule_pack_adaptive_skips,
            schedule_pack_adaptive_easy_skips=self.stats.schedule_pack_adaptive_easy_skips,
            schedule_pack_adaptive_bound_skips=self.stats.schedule_pack_adaptive_bound_skips,
            route_enumeration_adaptive_decisions=self.stats.route_enumeration_adaptive_decisions,
            route_enumeration_adaptive_runs=self.stats.route_enumeration_adaptive_runs,
            route_enumeration_adaptive_skips=self.stats.route_enumeration_adaptive_skips,
            route_enumeration_adaptive_easy_skips=self.stats.route_enumeration_adaptive_easy_skips,
            route_pool_restart_nodes=self.stats.route_pool_restart_nodes,
            route_pool_restart_rounds=self.stats.route_pool_restart_rounds,
            route_pool_restart_routes_omitted_total=self.stats.route_pool_restart_routes_omitted_total,
            route_pool_restart_routes_omitted_max=self.stats.route_pool_restart_routes_omitted_max,
            route_pool_restart_pricing_recovered_routes=self.stats.route_pool_restart_pricing_recovered_routes,
            route_pool_restart_protected_routes_max=self.stats.route_pool_restart_protected_routes_max,
            route_pool_hygiene_diagnostic_events=self.stats.route_pool_hygiene_diagnostic_events,
            route_pool_hygiene_task_set_groups_max=self.stats.route_pool_hygiene_task_set_groups_max,
            route_pool_hygiene_multi_route_groups_max=self.stats.route_pool_hygiene_multi_route_groups_max,
            route_pool_hygiene_near_duplicate_groups_max=self.stats.route_pool_hygiene_near_duplicate_groups_max,
            route_pool_hygiene_near_duplicate_routes_max=self.stats.route_pool_hygiene_near_duplicate_routes_max,
            route_pool_hygiene_max_group_size=self.stats.route_pool_hygiene_max_group_size,
            route_pool_hygiene_admission_evaluated=self.stats.route_pool_hygiene_admission_evaluated,
            route_pool_hygiene_admission_admitted=self.stats.route_pool_hygiene_admission_admitted,
            route_pool_hygiene_admission_filtered=self.stats.route_pool_hygiene_admission_filtered,
            route_pool_hygiene_admission_protected=self.stats.route_pool_hygiene_admission_protected,
            route_pool_hygiene_admission_forced_exact=self.stats.route_pool_hygiene_admission_forced_exact,
            restricted_master_adaptive_skips=self.stats.restricted_master_adaptive_skips,
            restricted_master_adaptive_time_limit_reductions=(
                self.stats.restricted_master_adaptive_time_limit_reductions
            ),
            restricted_master_adaptive_failure_streak_max=self.stats.restricted_master_adaptive_failure_streak_max,
            restricted_master_adaptive_unproductive_streak_max=(
                self.stats.restricted_master_adaptive_unproductive_streak_max
            ),
            restricted_master_adaptive_probe_forced=self.stats.restricted_master_adaptive_probe_forced,
            rmp_solves=self.stats.rmp_solves,
            pricing_calls=self.stats.pricing_calls,
            exact_pricing_calls=self.stats.exact_pricing_calls,
            label_pops=self.stats.label_pops,
            generated_labels=self.stats.generated_labels,
            branch_testing_time=round(self.stats.branch_testing_time, 6),
            branch_lp_candidates_tested=self.stats.branch_lp_candidates_tested,
            branch_heuristic_candidates_tested=self.stats.branch_heuristic_candidates_tested,
            time_to_first_incumbent=None
            if self.stats.time_to_first_incumbent is None
            else round(self.stats.time_to_first_incumbent, 6),
            time_to_best_incumbent=None
            if self.stats.time_to_best_incumbent is None
            else round(self.stats.time_to_best_incumbent, 6),
            open_nodes_remaining=len(open_nodes),
            fathom_reasons=dict(self.stats.fathom_reasons),
            timeout_pending_node_certified=self.timeout_pending_node_certified,
            official_bound_available=dual is not None,
        )
        if status == "TIME_LIMIT":
            self.logger.log(
                "timeout_diagnostics",
                pending_node_bound=None if self.pending_node_bound is None else round(self.pending_node_bound, 6),
                timeout_pending_node_certified=self.timeout_pending_node_certified,
                official_bound_available=dual is not None,
                official_bound=None if dual is None else round(dual, 6),
                diagnostic_bound=None if diagnostic_dual is None else round(diagnostic_dual, 6),
            )
        return result

    def _global_lower_bound(self, open_nodes: list[BPCNode], status: str) -> float | None:
        if self.abort_status is not None:
            return None
        if status == "OPTIMAL" and self.incumbent is not None and not open_nodes:
            return self.incumbent.objective
        values = [node.lower_bound for node in open_nodes]
        if values:
            return min(values)
        return None

    def _diagnostic_lower_bound(self, open_nodes: list[BPCNode]) -> float | None:
        values = [float(node.lower_bound) for node in open_nodes]
        if self.pending_node_bound is not None:
            values.append(float(self.pending_node_bound))
        if values:
            return min(values)
        if self.abort_status is None and self.incumbent is not None:
            return self.incumbent.objective
        return None

    def _exact_routes_per_pricing(self, node: BPCNode) -> int:
        if node.depth == 0 and self.root_max_routes_per_pricing > 0:
            return self.root_max_routes_per_pricing
        return self.max_routes_per_pricing

    def _add_pricing_routes(
        self,
        pricing: PricingResult,
        *,
        route_pool: RoutePool | None = None,
        route_birth_iter: dict[tuple[int, ...], int] | None = None,
        birth_iter: int = 0,
    ) -> tuple[int, int]:
        pool = self.pool if route_pool is None else route_pool
        local_added = 0
        global_added = 0
        for route in pricing.routes:
            global_before = len(self.pool.routes)
            stored = self.pool.add(route)
            if len(self.pool.routes) > global_before:
                global_added += 1
            if pool is self.pool:
                if len(self.pool.routes) > global_before:
                    local_added += 1
                    if route_birth_iter is not None:
                        route_birth_iter[stored.signature] = int(birth_iter)
            else:
                local_before = len(pool.routes)
                pool.add(stored)
                if len(pool.routes) > local_before:
                    local_added += 1
                    if route_birth_iter is not None:
                        route_birth_iter[stored.signature] = int(birth_iter)
        self.stats.generated_routes = len(self.pool.routes)
        if route_pool is not None and route_pool is not self.pool and local_added > global_added:
            self.stats.route_pool_restart_pricing_recovered_routes += local_added - global_added
        return local_added, global_added

    def _new_route_pool_from(self, routes: list[RouteColumn] | tuple[RouteColumn, ...]) -> RoutePool:
        pool = RoutePool()
        for route in routes:
            pool.add(route)
        return pool

    def _route_pool_restart_active(self, node: BPCNode | None = None) -> bool:
        min_depth = int(self.route_pool_restart_min_depth)
        max_depth = int(self.route_pool_restart_max_depth)
        return (
            self.route_pool_restart_enabled
            and (node is None or int(node.depth) >= min_depth)
            and (node is None or max_depth < 0 or int(node.depth) <= max_depth)
            and self.route_pool_restart_max_routes > 0
            and len(self.pool.routes) > max(0, self.route_pool_restart_min_global_routes)
        )

    def _route_allowed_for_any_vehicle(self, route: RouteColumn, node: BPCNode) -> bool:
        return any(route_allowed_by_branch(route, int(vehicle), node.branch_constraints) for vehicle in self.data.vehicles)

    def _route_pool_restart_reasons(
        self,
        node: BPCNode,
        solution: RMPSolution | None,
        route_birth_iter: dict[tuple[int, ...], int] | None,
        cg_iter: int,
    ) -> dict[tuple[int, ...], set[str]]:
        reasons: dict[tuple[int, ...], set[str]] = {}

        def mark(route: RouteColumn, reason: str) -> None:
            reasons.setdefault(route.signature, set()).add(reason)

        for route in self.pool.routes:
            if len(route.tasks) == 1:
                mark(route, "singleton")
        if self.incumbent is not None:
            for route, _vehicle, value in self.incumbent.route_values:
                if value > 0.5:
                    mark(route, "incumbent")
        if solution is not None:
            for route, _vehicle, value in solution.route_values:
                if abs(float(value)) > self.route_pool_restart_active_value_tol:
                    mark(route, "active")
        if route_birth_iter is not None and self.route_pool_restart_keep_recent_rounds >= 0:
            keep_recent = int(self.route_pool_restart_keep_recent_rounds)
            for route in self.pool.routes:
                born = route_birth_iter.get(route.signature)
                if born is not None and int(cg_iter) - int(born) <= keep_recent:
                    mark(route, "recent")

        arc_on_constraints = [constraint for constraint in node.branch_constraints if constraint.kind == "arc_on"]
        if arc_on_constraints:
            for constraint in arc_on_constraints:
                matches = [
                    route
                    for route in self.pool.routes
                    if self._route_allowed_for_any_vehicle(route, node)
                    and any(
                        route_branch_coefficient(route, int(vehicle), constraint) != 0.0
                        for vehicle in self.data.vehicles
                    )
                ]
                for route in sorted(matches, key=lambda item: (item.cost, len(item.tasks), item.signature))[:20]:
                    mark(route, "branch_arc_on")

        for cut in self.cuts:
            if isinstance(cut, WeightedScheduleRouteSetPackingCut) or self.route_pool_restart_keep_cut_signatures:
                for signature in getattr(cut, "signatures", ()):
                    route = self.pool.by_signature.get(tuple(signature))
                    if route is not None:
                        mark(route, "cut_signature")
        return reasons

    def _select_route_pool_restart_routes(
        self,
        node: BPCNode,
        solution: RMPSolution | None,
        route_birth_iter: dict[tuple[int, ...], int] | None,
        cg_iter: int,
    ) -> tuple[list[RouteColumn], dict[str, int]]:
        max_routes = max(1, int(self.route_pool_restart_max_routes))
        reasons = self._route_pool_restart_reasons(node, solution, route_birth_iter, cg_iter)
        active_value: dict[tuple[int, ...], float] = {}
        if solution is not None:
            for route, _vehicle, value in solution.route_values:
                active_value[route.signature] = max(active_value.get(route.signature, 0.0), abs(float(value)))

        selected: list[RouteColumn] = []
        seen: set[tuple[int, ...]] = set()

        def add(route: RouteColumn) -> None:
            if route.signature in seen:
                return
            selected.append(route)
            seen.add(route.signature)

        protected_routes = [
            route
            for route in self.pool.routes
            if route.signature in reasons and self._route_allowed_for_any_vehicle(route, node)
        ]
        for route in sorted(protected_routes, key=lambda item: (item.id, item.signature)):
            add(route)

        max_per_task_set = max(0, int(self.route_pool_restart_max_routes_per_task_set))
        task_set_count: dict[frozenset[int], int] = {}
        for route in selected:
            task_set_count[route.task_set] = task_set_count.get(route.task_set, 0) + 1

        def score(route: RouteColumn) -> tuple:
            born = -1 if route_birth_iter is None else route_birth_iter.get(route.signature, -1)
            return (
                -active_value.get(route.signature, 0.0),
                -int(born),
                -len(route.tasks),
                float(route.cost),
                route.signature,
            )

        for route in sorted(self.pool.routes, key=score):
            if len(selected) >= max_routes:
                break
            if route.signature in seen:
                continue
            if not self._route_allowed_for_any_vehicle(route, node):
                continue
            if max_per_task_set > 0 and task_set_count.get(route.task_set, 0) >= max_per_task_set:
                continue
            add(route)
            task_set_count[route.task_set] = task_set_count.get(route.task_set, 0) + 1

        reason_counts: dict[str, int] = {}
        for signature in seen:
            for reason in reasons.get(signature, ()):
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        reason_counts["selected"] = len(selected)
        reason_counts["protected"] = len([signature for signature in seen if signature in reasons])
        return selected, reason_counts

    def _initial_node_route_pool(self, node: BPCNode) -> tuple[RoutePool | None, dict[tuple[int, ...], int] | None]:
        if not self.route_pool_restart_node_start_enabled:
            return None, None
        if not self._route_pool_restart_active(node) or len(self.pool.routes) <= self.route_pool_restart_max_routes:
            return None, None
        selected, reason_counts = self._select_route_pool_restart_routes(node, None, None, 0)
        local_pool = self._new_route_pool_from(selected)
        birth_iter = {route.signature: 0 for route in local_pool.routes}
        omitted = max(0, len(self.pool.routes) - len(local_pool.routes))
        self.stats.route_pool_restart_nodes += 1
        self.stats.route_pool_restart_rounds += 1
        self.stats.route_pool_restart_routes_omitted_total += omitted
        self.stats.route_pool_restart_routes_omitted_max = max(self.stats.route_pool_restart_routes_omitted_max, omitted)
        self.stats.route_pool_restart_protected_routes_max = max(
            self.stats.route_pool_restart_protected_routes_max,
            int(reason_counts.get("protected", 0)),
        )
        self.logger.log(
            "route_pool_restart",
            node_id=node.id,
            depth=node.depth,
            stage="node_start",
            global_routes=len(self.pool.routes),
            local_routes=len(local_pool.routes),
            omitted_routes=omitted,
            max_routes=self.route_pool_restart_max_routes,
            reason_counts=reason_counts,
        )
        return local_pool, birth_iter

    def _cleanup_node_route_pool(
        self,
        node: BPCNode,
        route_pool: RoutePool | None,
        solution: RMPSolution,
        route_birth_iter: dict[tuple[int, ...], int] | None,
        cg_iter: int,
    ) -> bool:
        if route_pool is None or route_birth_iter is None:
            return False
        if len(route_pool.routes) <= self.route_pool_restart_max_routes:
            return False
        selected, reason_counts = self._select_route_pool_restart_routes(node, solution, route_birth_iter, cg_iter)
        selected_signatures = {route.signature for route in selected}
        if len(selected_signatures) >= len(route_pool.routes):
            return False
        before = len(route_pool.routes)
        replacement = self._new_route_pool_from(selected)
        route_pool.routes = replacement.routes
        route_pool.by_signature = replacement.by_signature
        for signature in list(route_birth_iter):
            if signature not in route_pool.by_signature:
                route_birth_iter.pop(signature, None)
        omitted = max(0, len(self.pool.routes) - len(route_pool.routes))
        removed_local = before - len(route_pool.routes)
        self.stats.route_pool_restart_rounds += 1
        self.stats.route_pool_restart_routes_omitted_total += omitted
        self.stats.route_pool_restart_routes_omitted_max = max(self.stats.route_pool_restart_routes_omitted_max, omitted)
        self.stats.route_pool_restart_protected_routes_max = max(
            self.stats.route_pool_restart_protected_routes_max,
            int(reason_counts.get("protected", 0)),
        )
        self.logger.log(
            "route_pool_restart",
            node_id=node.id,
            depth=node.depth,
            stage="cleanup",
            cg_iter=cg_iter,
            global_routes=len(self.pool.routes),
            local_before=before,
            local_routes=len(route_pool.routes),
            removed_local_routes=removed_local,
            omitted_routes=omitted,
            max_routes=self.route_pool_restart_max_routes,
            reason_counts=reason_counts,
        )
        return True

    def _create_node_route_pool_from_solution(
        self,
        node: BPCNode,
        solution: RMPSolution,
        route_birth_iter: dict[tuple[int, ...], int] | None,
        cg_iter: int,
    ) -> tuple[RoutePool, dict[tuple[int, ...], int]] | None:
        """Create a local node route pool after the global pool has become large.

        This is exact-safe for the same reason as node-start restart: the global
        pool is not deleted, and exact pricing runs against the local pool so any
        omitted route with negative reduced cost can be recovered as a column.
        """

        if not self.route_pool_restart_cleanup_enabled:
            return None
        if not self._route_pool_restart_active(node) or len(self.pool.routes) <= self.route_pool_restart_max_routes:
            return None
        birth_iter = route_birth_iter
        if birth_iter is None:
            birth_iter = {route.signature: 0 for route in self.pool.routes}
        selected, reason_counts = self._select_route_pool_restart_routes(node, solution, birth_iter, cg_iter)
        if len(selected) >= len(self.pool.routes):
            return None
        local_pool = self._new_route_pool_from(selected)
        local_birth_iter = {
            route.signature: int(birth_iter.get(route.signature, cg_iter))
            for route in local_pool.routes
        }
        omitted = max(0, len(self.pool.routes) - len(local_pool.routes))
        self.stats.route_pool_restart_nodes += 1
        self.stats.route_pool_restart_rounds += 1
        self.stats.route_pool_restart_routes_omitted_total += omitted
        self.stats.route_pool_restart_routes_omitted_max = max(self.stats.route_pool_restart_routes_omitted_max, omitted)
        self.stats.route_pool_restart_protected_routes_max = max(
            self.stats.route_pool_restart_protected_routes_max,
            int(reason_counts.get("protected", 0)),
        )
        self.logger.log(
            "route_pool_restart",
            node_id=node.id,
            depth=node.depth,
            stage="mid_node_create",
            cg_iter=cg_iter,
            global_routes=len(self.pool.routes),
            local_routes=len(local_pool.routes),
            omitted_routes=omitted,
            max_routes=self.route_pool_restart_max_routes,
            reason_counts=reason_counts,
        )
        return local_pool, local_birth_iter

    def _route_pool_task_set_compaction_active(self, node: BPCNode) -> bool:
        max_per_task_set = int(self.route_pool_task_set_compaction_max_routes_per_task_set)
        if not self.route_pool_task_set_compaction_enabled or max_per_task_set <= 0:
            return False
        if int(node.depth) < int(self.route_pool_task_set_compaction_min_depth):
            return False
        max_depth = int(self.route_pool_task_set_compaction_max_depth)
        if max_depth >= 0 and int(node.depth) > max_depth:
            return False
        return True

    def _signature_cut_signatures(self) -> set[tuple[int, ...]]:
        signatures: set[tuple[int, ...]] = set()
        for cut in self.cuts:
            for signature in getattr(cut, "signatures", ()) or ():
                signatures.add(tuple(int(task) for task in signature))
        return signatures

    def _compact_node_route_pool_by_task_set(
        self,
        node: BPCNode,
        solution: RMPSolution,
        route_pool: RoutePool | None,
        route_birth_iter: dict[tuple[int, ...], int] | None,
        cg_iter: int,
    ) -> tuple[RoutePool, dict[tuple[int, ...], int]] | None:
        """Locally cap inactive same-task-set route variants.

        The global route pool is not deleted. If an omitted route has negative
        reduced cost for the current node, exact pricing can recover it.
        """

        if not self._route_pool_task_set_compaction_active(node):
            return None
        current_routes = list(self.pool.routes if route_pool is None else route_pool.routes)
        if not current_routes:
            return None
        max_per_task_set = max(1, int(self.route_pool_task_set_compaction_max_routes_per_task_set))
        min_group_size = max(max_per_task_set + 1, int(self.route_pool_task_set_compaction_min_group_size))

        local_birth = route_birth_iter or {route.signature: 0 for route in current_routes}
        restart_keep_recent = self.route_pool_restart_keep_recent_rounds
        self.route_pool_restart_keep_recent_rounds = int(self.route_pool_task_set_compaction_keep_recent_rounds)
        try:
            reasons = self._route_pool_restart_reasons(node, solution, local_birth, cg_iter)
        finally:
            self.route_pool_restart_keep_recent_rounds = restart_keep_recent
        for signature in self._signature_cut_signatures():
            reasons.setdefault(signature, set()).add("cut_signature")

        active_value: dict[tuple[int, ...], float] = {}
        for route, _vehicle, value in solution.route_values:
            active_value[route.signature] = max(active_value.get(route.signature, 0.0), abs(float(value)))

        grouped: dict[frozenset[int], list[RouteColumn]] = {}
        for route in current_routes:
            if self._route_allowed_for_any_vehicle(route, node):
                grouped.setdefault(route.task_set, []).append(route)

        selected: list[RouteColumn] = []
        compacted_groups = 0
        protected_count = 0
        removed = 0

        def route_order(route: RouteColumn) -> tuple:
            born = int(local_birth.get(route.signature, 0))
            return (
                -active_value.get(route.signature, 0.0),
                -born,
                float(route.cost),
                float(route.cycle_time),
                float(route.return_time),
                route.signature,
            )

        for routes in grouped.values():
            if len(routes) < min_group_size:
                selected.extend(sorted(routes, key=lambda item: item.id))
                continue
            protected = [route for route in routes if route.signature in reasons]
            unprotected = [route for route in routes if route.signature not in reasons]
            keep = list(sorted(protected, key=lambda item: item.id))
            protected_count += len(keep)
            spare = max(0, max_per_task_set - len(keep))
            keep.extend(sorted(unprotected, key=route_order)[:spare])
            if len(keep) < len(routes):
                compacted_groups += 1
                removed += len(routes) - len(keep)
            selected.extend(keep)

        if removed <= 0:
            return None
        if len({route.signature for route in selected}) >= len(current_routes):
            return None

        local_pool = self._new_route_pool_from(sorted(selected, key=lambda item: item.id))
        local_birth_iter = {
            route.signature: int(local_birth.get(route.signature, cg_iter))
            for route in local_pool.routes
        }
        omitted = max(0, len(self.pool.routes) - len(local_pool.routes))
        if route_pool is None:
            self.stats.route_pool_restart_nodes += 1
        self.stats.route_pool_restart_rounds += 1
        self.stats.route_pool_restart_routes_omitted_total += omitted
        self.stats.route_pool_restart_routes_omitted_max = max(self.stats.route_pool_restart_routes_omitted_max, omitted)
        self.stats.route_pool_restart_protected_routes_max = max(
            self.stats.route_pool_restart_protected_routes_max,
            protected_count,
        )
        self.logger.log(
            "route_pool_task_set_compaction",
            node_id=node.id,
            depth=node.depth,
            cg_iter=cg_iter,
            global_routes=len(self.pool.routes),
            local_before=len(current_routes),
            local_routes=len(local_pool.routes),
            removed_local_routes=removed,
            omitted_routes=omitted,
            compacted_groups=compacted_groups,
            max_routes_per_task_set=max_per_task_set,
            protected_routes=protected_count,
        )
        return local_pool, local_birth_iter

    def _resolve_global_solution_for_branching(
        self,
        node: BPCNode,
        certified_solution: RMPSolution,
    ) -> RMPSolution:
        if not self.route_pool_restart_branch_with_global_solution:
            return certified_solution
        if certified_solution.objective is None:
            return certified_solution
        global_solution = solve_rmp_lp(
            self.data,
            self.pool.routes,
            self.cuts,
            node.branch_constraints,
            phase="phase2",
            rmp_params=self.rmp_params,
            verbose=False,
            task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
        )
        self.stats.rmp_solves += 1
        objective_delta = None
        if global_solution.objective is not None:
            objective_delta = float(global_solution.objective) - float(certified_solution.objective)
        accepted = (
            global_solution.optimal
            and global_solution.duals is not None
            and global_solution.objective is not None
            and abs(float(objective_delta or 0.0)) <= max(1.0e-6, 10.0 * self.integer_tol)
            and global_solution.artificial_sum <= self.integer_tol
        )
        self.logger.log(
            "route_pool_restart_global_branch_solution",
            node_id=node.id,
            depth=node.depth,
            status=global_solution.status,
            accepted=bool(accepted),
            local_objective=round(float(certified_solution.objective), 6),
            global_objective=None if global_solution.objective is None else round(float(global_solution.objective), 6),
            objective_delta=None if objective_delta is None else round(float(objective_delta), 9),
            global_route_count=len(self.pool.routes),
            local_variable_count=certified_solution.variable_count,
            global_variable_count=global_solution.variable_count,
        )
        if accepted:
            return global_solution
        return certified_solution

    def _route_pool_hygiene_profile(
        self,
        routes: list[RouteColumn] | tuple[RouteColumn, ...],
    ) -> dict[str, Any]:
        by_task_set: dict[tuple[int, ...], list[RouteColumn]] = {}
        for route in routes:
            key = tuple(sorted(int(task) for task in route.task_set))
            by_task_set.setdefault(key, []).append(route)

        multi_groups = [items for items in by_task_set.values() if len(items) > 1]
        near_duplicate_groups = 0
        near_duplicate_routes = 0
        max_group_size = 0
        max_near_duplicate_group_size = 0
        max_cost_spread = 0.0
        samples: list[dict[str, Any]] = []
        sample_limit = max(0, int(self.route_pool_hygiene_sample_groups))
        for task_set, items in sorted(
            by_task_set.items(),
            key=lambda pair: (-len(pair[1]), pair[0]),
        ):
            if len(items) <= 1:
                continue
            ordered = sorted(items, key=lambda route: (float(route.cost), route.signature))
            min_cost = float(ordered[0].cost)
            max_cost = max(float(route.cost) for route in ordered)
            threshold = (
                min_cost
                + max(0.0, float(self.route_pool_hygiene_near_duplicate_abs_tol))
                + max(0.0, float(self.route_pool_hygiene_near_duplicate_rel_tol)) * max(1.0, abs(min_cost))
            )
            near = [route for route in ordered if float(route.cost) <= threshold + 1.0e-12]
            max_group_size = max(max_group_size, len(items))
            max_cost_spread = max(max_cost_spread, max_cost - min_cost)
            if len(near) > 1:
                near_duplicate_groups += 1
                near_duplicate_routes += len(near) - 1
                max_near_duplicate_group_size = max(max_near_duplicate_group_size, len(near))
            if len(samples) < sample_limit:
                samples.append(
                    {
                        "task_set": list(task_set),
                        "group_size": len(items),
                        "near_duplicate_count": len(near),
                        "min_cost": round(min_cost, 6),
                        "max_cost": round(max_cost, 6),
                        "cost_spread": round(max_cost - min_cost, 6),
                        "best_signatures": [list(route.signature) for route in ordered[: min(5, len(ordered))]],
                    }
                )

        return {
            "route_count": len(routes),
            "task_set_groups": len(by_task_set),
            "multi_route_groups": len(multi_groups),
            "near_duplicate_groups": int(near_duplicate_groups),
            "near_duplicate_routes": int(near_duplicate_routes),
            "max_group_size": int(max_group_size),
            "max_near_duplicate_group_size": int(max_near_duplicate_group_size),
            "max_cost_spread": round(float(max_cost_spread), 6),
            "samples": samples,
        }

    def _log_route_pool_hygiene_diagnostics(
        self,
        node: BPCNode | None,
        *,
        stage: str,
        routes: list[RouteColumn] | tuple[RouteColumn, ...] | None = None,
    ) -> None:
        if not self.route_pool_hygiene_diagnostics_enabled:
            return
        route_list = self.pool.routes if routes is None else list(routes)
        if len(route_list) < max(0, int(self.route_pool_hygiene_diagnostics_min_routes)):
            return
        payload = self._route_pool_hygiene_profile(route_list)
        self.stats.route_pool_hygiene_diagnostic_events += 1
        self.stats.route_pool_hygiene_task_set_groups_max = max(
            self.stats.route_pool_hygiene_task_set_groups_max,
            int(payload["task_set_groups"]),
        )
        self.stats.route_pool_hygiene_multi_route_groups_max = max(
            self.stats.route_pool_hygiene_multi_route_groups_max,
            int(payload["multi_route_groups"]),
        )
        self.stats.route_pool_hygiene_near_duplicate_groups_max = max(
            self.stats.route_pool_hygiene_near_duplicate_groups_max,
            int(payload["near_duplicate_groups"]),
        )
        self.stats.route_pool_hygiene_near_duplicate_routes_max = max(
            self.stats.route_pool_hygiene_near_duplicate_routes_max,
            int(payload["near_duplicate_routes"]),
        )
        self.stats.route_pool_hygiene_max_group_size = max(
            self.stats.route_pool_hygiene_max_group_size,
            int(payload["max_group_size"]),
        )
        self.logger.log(
            "route_pool_hygiene_diagnostics",
            node_id=None if node is None else int(node.id),
            depth=None if node is None else int(node.depth),
            stage=str(stage),
            **payload,
        )

    def _apply_route_pool_hygiene_admission(
        self,
        pricing: PricingResult,
        *,
        pricing_kind: str,
        node: BPCNode | None = None,
        solution: RMPSolution | None = None,
    ) -> tuple[PricingResult, dict[str, Any] | None]:
        if (
            not self.route_pool_hygiene_admission_enabled
            or pricing_kind not in {"heuristic", "heuristic_boost"}
            or self.route_pool_hygiene_admission_max_per_task_set <= 0
            or not pricing.routes
        ):
            return pricing, None
        if node is not None and int(node.depth) < max(0, int(self.route_pool_hygiene_admission_min_depth)):
            return pricing, None

        max_per_task_set = max(1, int(self.route_pool_hygiene_admission_max_per_task_set))
        protected_task_sets = self._route_pool_hygiene_admission_protected_task_sets(node, solution)
        counts: dict[tuple[int, ...], int] = {}
        admitted: list[RouteColumn] = []
        filtered: list[RouteColumn] = []
        capped_groups: set[tuple[int, ...]] = set()
        protected_routes = 0
        for route in pricing.routes:
            task_set = tuple(sorted(int(task) for task in route.task_set))
            if len(task_set) <= 1:
                admitted.append(route)
                continue
            if task_set in protected_task_sets:
                admitted.append(route)
                protected_routes += 1
                continue
            count = counts.get(task_set, 0)
            if count < max_per_task_set:
                admitted.append(route)
                counts[task_set] = count + 1
            else:
                filtered.append(route)
                capped_groups.add(task_set)

        self.stats.route_pool_hygiene_admission_evaluated += len(pricing.routes)
        self.stats.route_pool_hygiene_admission_admitted += len(admitted)
        self.stats.route_pool_hygiene_admission_filtered += len(filtered)
        self.stats.route_pool_hygiene_admission_protected += protected_routes
        if not filtered:
            return pricing, None

        # 中文注释：过滤过 heuristic 负列后，不能把该 heuristic 调用当作完整证书使用。
        filtered_pricing = replace(pricing, routes=admitted, exhausted=False, negative_routes=len(admitted))
        self.stats.route_pool_hygiene_admission_forced_exact += int(bool(pricing.exhausted))
        return filtered_pricing, {
            "evaluated_routes": len(pricing.routes),
            "admitted_routes": len(admitted),
            "filtered_routes": len(filtered),
            "protected_routes": int(protected_routes),
            "protected_task_set_count": len(protected_task_sets),
            "capped_group_count": len(capped_groups),
            "max_per_task_set": max_per_task_set,
            "min_depth": max(0, int(self.route_pool_hygiene_admission_min_depth)),
            "forced_exact_certificate": bool(pricing.exhausted),
            "sample_filtered_signatures": [list(route.signature) for route in filtered[:10]],
        }

    def _route_pool_hygiene_admission_protected_task_sets(
        self,
        node: BPCNode | None,
        solution: RMPSolution | None,
    ) -> set[tuple[int, ...]]:
        protected: set[tuple[int, ...]] = set()

        def mark(route: RouteColumn) -> None:
            if len(route.task_set) > 1:
                protected.add(tuple(sorted(int(task) for task in route.task_set)))

        if self.route_pool_hygiene_admission_protect_incumbent_task_sets and self.incumbent is not None:
            for route, _vehicle, value in self.incumbent.route_values:
                if float(value) > 0.5:
                    mark(route)

        if self.route_pool_hygiene_admission_protect_active_task_sets and solution is not None:
            for route, _vehicle, value in solution.route_values:
                if abs(float(value)) > self.route_pool_restart_active_value_tol:
                    mark(route)

        if self.route_pool_hygiene_admission_protect_cut_task_sets:
            for cut in self.cuts:
                for signature in getattr(cut, "signatures", ()):
                    if len(signature) > 1:
                        protected.add(tuple(sorted(int(task) for task in signature)))

        if self.route_pool_hygiene_admission_protect_branch_task_sets and node is not None and node.branch_constraints:
            branch_tasks: set[int] = set()
            for constraint in node.branch_constraints:
                if constraint.task_i is not None:
                    branch_tasks.add(int(constraint.task_i))
                if constraint.task_j is not None:
                    branch_tasks.add(int(constraint.task_j))
            if branch_tasks:
                for route in self.pool.routes:
                    if route.task_set & branch_tasks:
                        mark(route)

        return protected

    def _schedule_pack_seed_schedules(self) -> list[list[RouteColumn]]:
        if self.incumbent is None:
            return []
        by_vehicle: dict[int, list[RouteColumn]] = {int(vehicle): [] for vehicle in self.data.vehicles}
        for route, vehicle, value in self.incumbent.route_values:
            if float(value) > 0.5:
                by_vehicle[int(vehicle)].append(route)
        return [routes for routes in by_vehicle.values() if routes]

    def _schedule_pack_support_values(self, solution: RMPSolution) -> dict[tuple[int, ...], float]:
        support_values: dict[tuple[int, ...], float] = {}
        for route, _vehicle, value in solution.route_values:
            support_values[route.signature] = support_values.get(route.signature, 0.0) + float(value)
        return support_values

    def _adaptive_gap_snapshot(
        self,
        bound: float,
        *,
        abs_threshold: float,
        ratio_threshold: float,
    ) -> tuple[float | None, float | None, float | None, float]:
        threshold = max(float(abs_threshold), float(ratio_threshold) * max(1.0, abs(float(bound))))
        if self.incumbent is None:
            return None, None, None, threshold
        incumbent = float(self.incumbent.objective)
        gap = incumbent - float(bound)
        ratio = gap / max(1.0, abs(float(bound)))
        return incumbent, gap, ratio, threshold

    def _schedule_pack_adaptive_allows(
        self,
        node: BPCNode,
        *,
        root_diagnostic: bool,
        node_relaxation: bool,
        node_bound: float,
    ) -> bool:
        if not self.schedule_pack_adaptive_enabled:
            return True
        self.stats.schedule_pack_adaptive_decisions += 1
        incumbent, gap, gap_ratio, threshold = self._adaptive_gap_snapshot(
            node_bound,
            abs_threshold=self.schedule_pack_adaptive_gap_abs,
            ratio_threshold=self.schedule_pack_adaptive_gap_ratio,
        )
        action = "run"
        reason = "no_incumbent"
        if incumbent is not None:
            if (
                self.schedule_pack_adaptive_skip_if_fathomable
                and float(node_bound) >= incumbent - self.integer_tol
            ):
                action = "skip"
                reason = "already_fathomable"
                self.stats.schedule_pack_adaptive_bound_skips += 1
            elif float(gap or 0.0) <= threshold + self.integer_tol:
                action = "skip"
                reason = "easy_gap"
                self.stats.schedule_pack_adaptive_easy_skips += 1
            else:
                reason = "hard_gap"

        if action == "run":
            self.stats.schedule_pack_adaptive_runs += 1
        else:
            self.stats.schedule_pack_adaptive_skips += 1
        self.logger.log(
            "schedule_pack_adaptive",
            node_id=node.id,
            depth=node.depth,
            action=action,
            reason=reason,
            root_diagnostic=root_diagnostic,
            node_relaxation=node_relaxation,
            node_bound=round(float(node_bound), 6),
            incumbent=None if incumbent is None else round(incumbent, 6),
            gap=None if gap is None else round(gap, 6),
            gap_ratio=None if gap_ratio is None else round(gap_ratio, 6),
            threshold=round(threshold, 6),
            threshold_abs=round(self.schedule_pack_adaptive_gap_abs, 6),
            threshold_ratio=round(self.schedule_pack_adaptive_gap_ratio, 6),
        )
        return action == "run"

    def _route_enumeration_adaptive_allows(self, node: BPCNode, solution: RMPSolution) -> bool:
        if not self.route_enumeration_adaptive_enabled:
            return True
        node_bound = float(solution.objective if solution.objective is not None else node.lower_bound)
        self.stats.route_enumeration_adaptive_decisions += 1
        incumbent, gap, gap_ratio, threshold = self._adaptive_gap_snapshot(
            node_bound,
            abs_threshold=self.route_enumeration_adaptive_gap_abs,
            ratio_threshold=self.route_enumeration_adaptive_gap_ratio,
        )
        action = "run"
        reason = "no_incumbent"
        if incumbent is not None:
            if float(gap or 0.0) <= threshold + self.integer_tol:
                action = "skip"
                reason = "easy_gap"
                self.stats.route_enumeration_adaptive_easy_skips += 1
            else:
                reason = "hard_gap"
        if action == "run":
            self.stats.route_enumeration_adaptive_runs += 1
        else:
            self.stats.route_enumeration_adaptive_skips += 1
        self.logger.log(
            "route_enumeration_adaptive",
            node_id=node.id,
            depth=node.depth,
            action=action,
            reason=reason,
            node_bound=round(node_bound, 6),
            incumbent=None if incumbent is None else round(incumbent, 6),
            gap=None if gap is None else round(gap, 6),
            gap_ratio=None if gap_ratio is None else round(gap_ratio, 6),
            threshold=round(threshold, 6),
            threshold_abs=round(self.route_enumeration_adaptive_gap_abs, 6),
            threshold_ratio=round(self.route_enumeration_adaptive_gap_ratio, 6),
        )
        return action == "run"

    def _run_schedule_pack_relaxation(self, node: BPCNode, solution: RMPSolution) -> None:
        root_diagnostic = bool(
            self.schedule_pack_diagnostic_enabled
            and node.id == 0
            and self.stats.schedule_pack_diagnostic_status is None
        )
        node_relaxation = bool(
            self.schedule_pack_relaxation_enabled
            and node.depth <= self.schedule_pack_relaxation_max_depth
        )
        if not root_diagnostic and not node_relaxation:
            return
        node_bound_for_adaptive = float(solution.objective if solution.objective is not None else node.lower_bound)
        if not self._schedule_pack_adaptive_allows(
            node,
            root_diagnostic=root_diagnostic,
            node_relaxation=node_relaxation,
            node_bound=node_bound_for_adaptive,
        ):
            if root_diagnostic:
                self.stats.schedule_pack_diagnostic_status = "SKIPPED_ADAPTIVE"
                self.logger.log(
                    "schedule_pack_diagnostic",
                    node_id=node.id,
                    status="SKIPPED_ADAPTIVE",
                    root_route_vehicle_bound=round(node_bound_for_adaptive, 6),
                    objective=None,
                    gap_vs_root=None,
                    columns=0,
                    candidate_routes=0,
                    generated_states=0,
                    solving_time=0.0,
                    exact_bound=False,
                )
            return
        remaining = max(0.0, self.time_limit - self.elapsed() - 1.0)
        requested_time_limit = 0.0
        if root_diagnostic:
            requested_time_limit = max(requested_time_limit, self.schedule_pack_diagnostic_time_limit)
        if node_relaxation:
            requested_time_limit = max(requested_time_limit, self.schedule_pack_relaxation_time_limit)
        time_limit = min(requested_time_limit, remaining)
        if time_limit < 1.0:
            if root_diagnostic:
                self.stats.schedule_pack_diagnostic_status = "SKIPPED_TIME"
                self.logger.log(
                    "schedule_pack_diagnostic",
                    node_id=node.id,
                    status="SKIPPED_TIME",
                    root_route_vehicle_bound=round(float(solution.objective or 0.0), 6),
                    objective=None,
                    columns=0,
                    candidate_routes=0,
                    generated_states=0,
                    solving_time=0.0,
                )
            return

        result = solve_schedule_pack_node_relaxation(
            self.data,
            self.pool.routes,
            self.cuts,
            node.branch_constraints,
            support_values=self._schedule_pack_support_values(solution),
            seed_schedules=self._schedule_pack_seed_schedules(),
            max_candidate_routes=self.schedule_pack_diagnostic_max_candidate_routes,
            max_columns=self.schedule_pack_diagnostic_max_columns,
            beam_width=self.schedule_pack_diagnostic_beam_width,
            max_sorties=self.schedule_pack_diagnostic_max_sorties,
            time_limit=time_limit,
            pricing_batch_size=self.schedule_pack_pricing_batch_size,
            rmp_params=self.rmp_params,
            full_route_space_pricing=bool(
                self.schedule_pack_full_pricing_enabled
                and node.depth <= self.schedule_pack_full_pricing_max_depth
            ),
            full_pricing_max_states=self.schedule_pack_full_pricing_max_states,
        )
        node_bound = float(solution.objective or 0.0)
        gap_vs_node = None
        exact_bound_applied = False
        official_bound = float(node.lower_bound)
        if result.objective is not None:
            gap_vs_node = float(result.objective) - node_bound
            if node_relaxation:
                node.schedule_pack_relaxation_bound = float(result.objective)
                current_best = self.stats.schedule_pack_relaxation_best_objective
                if current_best is None or float(result.objective) > current_best + self.integer_tol:
                    self.stats.schedule_pack_relaxation_best_objective = float(result.objective)
                    self.stats.schedule_pack_relaxation_best_gap_vs_node = gap_vs_node
                if result.exact_over_full_route_space and float(result.objective) > node.lower_bound + self.integer_tol:
                    node.lower_bound = float(result.objective)
                    official_bound = node.lower_bound
                    exact_bound_applied = True
                    self.stats.last_certified_node_bound = max(
                        float(self.stats.last_certified_node_bound or node_bound),
                        node.lower_bound,
                    )
                    if node.id == 0:
                        self.stats.root_relaxation = max(float(self.stats.root_relaxation or node_bound), node.lower_bound)
        if node_relaxation:
            self.stats.schedule_pack_relaxation_calls += 1
            self.stats.schedule_pack_relaxation_time += result.solving_time
            self.stats.schedule_pack_relaxation_columns += result.column_count
            if result.exact_over_candidate_routes:
                self.stats.schedule_pack_relaxation_candidate_exact += 1
            if result.exact_over_full_route_space:
                self.stats.schedule_pack_relaxation_full_exact += 1
            self.stats.schedule_pack_relaxation_full_pricing_states += result.full_pricing_generated_states
            self.stats.schedule_pack_relaxation_full_pricing_time += result.full_pricing_time
            if node.id == 0 and self.stats.schedule_pack_relaxation_root_objective is None:
                self.stats.schedule_pack_relaxation_root_objective = result.objective
            self.logger.log(
                "schedule_pack_relaxation",
                node_id=node.id,
                depth=node.depth,
                status=result.status,
                node_route_vehicle_bound=round(node_bound, 6),
                objective=None if result.objective is None else round(result.objective, 6),
                gap_vs_node=None if gap_vs_node is None else round(gap_vs_node, 6),
                columns=result.column_count,
                candidate_routes=result.candidate_route_count,
                generated_states=result.generated_state_count,
                duplicate_columns=result.skipped_duplicate_columns,
                infeasible_extensions=result.skipped_infeasible_extensions,
                single_route_columns=result.single_route_columns,
                multi_route_columns=result.multi_route_columns,
                max_route_count=result.max_route_count,
                max_task_count=result.max_task_count,
                pricing_iterations=result.pricing_iterations,
                generated_pricing_columns=result.generated_pricing_columns,
                best_reduced_cost=None if result.best_reduced_cost is None else round(result.best_reduced_cost, 9),
                exact_over_candidate_routes=result.exact_over_candidate_routes,
                exact_over_full_route_space=result.exact_over_full_route_space,
                full_pricing_generated_states=result.full_pricing_generated_states,
                full_pricing_route_count=result.full_pricing_route_count,
                full_pricing_time=round(result.full_pricing_time, 6),
                seed_columns=result.seed_columns,
                solving_time=round(result.solving_time, 6),
                exact_bound=result.exact_over_full_route_space,
                exact_bound_applied=exact_bound_applied,
                official_node_bound=round(official_bound, 6),
                used_for_priority=bool(self.schedule_pack_relaxation_use_for_priority and result.objective is not None),
            )
            if result.objective is not None and self.schedule_pack_relaxation_use_for_priority:
                node.priority = max(float(node.priority), float(result.objective))
        if root_diagnostic:
            self.stats.schedule_pack_diagnostic_status = result.status
            self.stats.schedule_pack_diagnostic_objective = result.objective
            self.stats.schedule_pack_diagnostic_gap_vs_root = gap_vs_node
            self.stats.schedule_pack_diagnostic_columns = result.column_count
            self.stats.schedule_pack_diagnostic_candidate_routes = result.candidate_route_count
            self.stats.schedule_pack_diagnostic_generated_states = result.generated_state_count
            self.stats.schedule_pack_diagnostic_time = result.solving_time
            self.logger.log(
                "schedule_pack_diagnostic",
                node_id=node.id,
                status=result.status,
                root_route_vehicle_bound=round(node_bound, 6),
                objective=None if result.objective is None else round(result.objective, 6),
                gap_vs_root=None if gap_vs_node is None else round(gap_vs_node, 6),
                columns=result.column_count,
                candidate_routes=result.candidate_route_count,
                generated_states=result.generated_state_count,
                duplicate_columns=result.skipped_duplicate_columns,
                infeasible_extensions=result.skipped_infeasible_extensions,
                single_route_columns=result.single_route_columns,
                multi_route_columns=result.multi_route_columns,
                max_route_count=result.max_route_count,
                max_task_count=result.max_task_count,
                pricing_iterations=result.pricing_iterations,
                generated_pricing_columns=result.generated_pricing_columns,
                best_reduced_cost=None if result.best_reduced_cost is None else round(result.best_reduced_cost, 9),
                exact_over_candidate_routes=result.exact_over_candidate_routes,
                exact_over_full_route_space=result.exact_over_full_route_space,
                full_pricing_generated_states=result.full_pricing_generated_states,
                full_pricing_route_count=result.full_pricing_route_count,
                full_pricing_time=round(result.full_pricing_time, 6),
                seed_columns=result.seed_columns,
                solving_time=round(result.solving_time, 6),
                exact_bound=result.exact_over_full_route_space,
            )

    def _run_pricing(
        self,
        node: BPCNode,
        solution: RMPSolution,
        *,
        cg_iter: int,
        phase: str,
        pricing_kind: str,
        max_routes_to_return: int,
        max_labels: int,
        selection_mode: str,
        route_pool: RoutePool | None = None,
        route_birth_iter: dict[tuple[int, ...], int] | None = None,
    ) -> tuple[PricingResult, int]:
        pricing_pool = self.pool if route_pool is None else route_pool
        ng_enabled = (
            bool(self.ng_dssr_pricing_enabled)
            and pricing_kind in {"heuristic", "heuristic_boost"}
            and int(max_labels) > 0
        )
        enumeration_threshold = None
        enumeration_limit = 0
        if self.route_enumeration_enabled and pricing_kind == "exact":
            if self._route_enumeration_adaptive_allows(node, solution):
                enumeration_threshold = self.route_enumeration_rc_threshold
                enumeration_limit = self.route_enumeration_max_routes
        pricing = exact_pricing(
            self.data,
            pricing_pool.routes,
            solution.duals,
            self.cuts,
            node.branch_constraints,
            phase=phase,
            eps=self.eps,
            max_routes_to_return=max_routes_to_return,
            max_labels=max_labels,
            selection_mode=selection_mode,
            dominance_enabled=self.exact_pricing_dominance_enabled,
            completion_bound_enabled=self.pricing_completion_bound_enabled,
            ng_relaxation_enabled=ng_enabled,
            ng_memory_size=self.ng_dssr_memory_size,
            exact_dssr_pricing_enabled=(
                bool(self.exact_dssr_pricing_enabled)
                and pricing_kind == "exact"
                and phase == "phase2"
            ),
            exact_dssr_initial_memory_size=self.exact_dssr_initial_memory_size,
            exact_dssr_max_iterations=self.exact_dssr_max_iterations,
            exact_dssr_max_labels=self.exact_dssr_max_labels,
            route_enumeration_rc_threshold=enumeration_threshold,
            route_enumeration_max_routes=enumeration_limit,
        )
        self.stats.pricing_calls += 1
        if pricing_kind == "exact":
            self.stats.exact_pricing_calls += 1
        self.stats.label_pops += pricing.label_pops
        self.stats.generated_labels += pricing.generated_labels
        pricing, admission_payload = self._apply_route_pool_hygiene_admission(
            pricing,
            pricing_kind=pricing_kind,
            node=node,
            solution=solution,
        )
        before_signatures = set(pricing_pool.by_signature)
        added, global_added = self._add_pricing_routes(
            pricing,
            route_pool=pricing_pool,
            route_birth_iter=route_birth_iter,
            birth_iter=cg_iter,
        )
        new_routes = [
            pricing_pool.by_signature[signature]
            for signature in sorted(set(pricing_pool.by_signature) - before_signatures)
        ]
        self._complete_route_pack_roi_pricing_watch(node, new_routes=new_routes)
        if added > 0:
            self._log_route_pool_hygiene_diagnostics(
                node,
                stage=f"after_{pricing_kind}_pricing",
                routes=pricing_pool.routes,
            )
        if admission_payload is not None:
            self.logger.log(
                "route_pool_hygiene_admission",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                phase=phase,
                pricing_kind=pricing_kind,
                added_routes=added,
                global_added_routes=global_added,
                **admission_payload,
            )
        self.logger.log(
            "pricing",
            node_id=node.id,
            depth=node.depth,
            cg_iter=cg_iter,
            phase=phase,
            pricing_kind=pricing_kind,
            selection_mode=selection_mode,
            max_labels=max_labels,
            certificate=pricing.exhausted,
            best_reduced_cost=None if pricing.best_reduced_cost is None else round(pricing.best_reduced_cost, 9),
            negative_routes=pricing.negative_routes,
            added_routes=added,
            global_added_routes=global_added,
            hygiene_admission_filtered=0 if admission_payload is None else admission_payload["filtered_routes"],
            hygiene_admission_forced_exact=(
                False if admission_payload is None else admission_payload["forced_exact_certificate"]
            ),
            exhausted=pricing.exhausted,
            route_count=len(pricing_pool.routes),
            global_route_count=len(self.pool.routes),
            label_pops=pricing.label_pops,
            generated_labels=pricing.generated_labels,
            dominance_enabled=pricing.dominance_enabled,
            dominance_pruned=pricing.dominance_pruned,
            completion_bound_enabled=pricing.completion_bound_enabled,
            completion_pruned=pricing.completion_pruned,
            ng_relaxation_enabled=pricing.ng_relaxation_enabled,
            ng_memory_size=pricing.ng_memory_size,
            dssr_pricing_enabled=pricing.dssr_pricing_enabled,
            dssr_iterations=pricing.dssr_iterations,
            dssr_memory_expansions=pricing.dssr_memory_expansions,
            dssr_fallback=pricing.dssr_fallback,
            enumerated_routes=pricing.enumerated_routes,
            route_enumeration_threshold=pricing.route_enumeration_threshold,
        )
        return pricing, added

    def _restricted_master_routes(self, solution: RMPSolution) -> list[RouteColumn]:
        if self.restricted_master_max_routes <= 0 or len(self.pool.routes) <= self.restricted_master_max_routes:
            return list(self.pool.routes)

        support: dict[tuple[int, ...], float] = {}
        for route, _vehicle, value in solution.route_values:
            support[route.signature] = max(support.get(route.signature, 0.0), float(value))

        selected: list[RouteColumn] = []
        seen: set[tuple[int, ...]] = set()

        def add(route: RouteColumn) -> None:
            if len(selected) >= self.restricted_master_max_routes:
                return
            if route.signature in seen:
                return
            selected.append(route)
            seen.add(route.signature)

        for route, _vehicle, value in sorted(solution.route_values, key=lambda item: (-float(item[2]), item[0].cost, item[0].signature)):
            if value > self.integer_tol:
                add(route)
        for task in self.data.tasks:
            for route in self.pool.routes:
                if route.signature == (int(task),):
                    add(route)
                    break

        remaining = sorted(
            self.pool.routes,
            key=lambda route: (
                -support.get(route.signature, 0.0),
                -len(route.tasks),
                route.cost,
                route.signature,
            ),
        )
        for route in remaining:
            add(route)
            if len(selected) >= self.restricted_master_max_routes:
                break
        return selected

    def _add_restricted_master_conflict_cuts(
        self,
        node: BPCNode,
        result: RestrictedIntegerResult,
        solution: RMPSolution,
    ) -> int:
        added = 0
        skipped_weak = 0
        diagnostics = {
            "conflicts_checked": 0,
            "skipped_without_witness": 0,
            "pair_conflict_events": 0,
            "pair_cuts_added": 0,
            "route_set_packing_events": 0,
            "route_set_packing_cuts_added": 0,
            "route_set_packing_cache_hits": 0,
            "route_set_packing_oracle_states_max": 0,
            "route_set_packing_budget_skips": 0,
            "variant_route_pack_cuts_added": 0,
            "schedule_capacity_events": 0,
            "schedule_capacity_cuts_added": 0,
            "nogood_violated_conflicts": 0,
            "nogood_cuts_added": 0,
            "weak_nogood_not_violated": 0,
        }
        route_pack_attempt_events = 0
        route_pack_attempt_budget = max(0, self.restricted_master_route_pack_conflict_max_events)
        for source_vehicle, conflict_routes in result.rejected_conflicts:
            diagnostics["conflicts_checked"] += 1
            if not conflict_routes:
                diagnostics["skipped_without_witness"] += 1
                continue
            self._record_task_schedule_capacity_witness(
                list(conflict_routes),
                source="rim_witness",
                vehicle=int(source_vehicle),
                node_id=node.id,
            )
            self._record_weighted_route_schedule_packing_witness(
                list(conflict_routes),
                source="rim_witness",
                vehicle=int(source_vehicle),
                node_id=node.id,
            )
            witness = self._diagnose_schedule_conflict(conflict_routes)
            if witness is None:
                diagnostics["skipped_without_witness"] += 1
                continue
            pair_added = self._add_schedule_pair_conflict_cuts(
                node,
                int(source_vehicle),
                witness.pair_conflicts,
            )
            if pair_added:
                diagnostics["pair_conflict_events"] += 1
                diagnostics["pair_cuts_added"] += pair_added
                added += pair_added
                continue
            if route_pack_attempt_events < route_pack_attempt_budget:
                route_pack_attempt_events += 1
                route_pack_added, route_pack_cache_hit, route_pack_states = self._add_schedule_route_set_packing_conflict_cuts(
                    node,
                    int(source_vehicle),
                    list(conflict_routes),
                )
                diagnostics["route_set_packing_events"] += 1
                diagnostics["route_set_packing_cache_hits"] += int(route_pack_cache_hit)
                diagnostics["route_set_packing_oracle_states_max"] = max(
                    int(diagnostics["route_set_packing_oracle_states_max"]),
                    int(route_pack_states or 0),
                )
                if route_pack_added:
                    diagnostics["route_set_packing_cuts_added"] += route_pack_added
                    added += route_pack_added
                    continue
                variant_added = self._add_schedule_variant_route_pack_conflict_cuts(
                    node,
                    int(source_vehicle),
                    list(witness.routes),
                    solution,
                    source="rim_conflict",
                )
                if variant_added:
                    diagnostics["variant_route_pack_cuts_added"] += variant_added
                    added += variant_added
                    continue
            else:
                diagnostics["route_set_packing_budget_skips"] += 1
            structural_added = self._add_schedule_capacity_conflict_cuts(
                node,
                int(source_vehicle),
                list(witness.routes),
            )
            if structural_added:
                diagnostics["schedule_capacity_events"] += 1
                diagnostics["schedule_capacity_cuts_added"] += structural_added
                added += structural_added
                continue
            violated_vehicles = self._violated_schedule_conflict_vehicles(solution, witness.routes)
            if not violated_vehicles:
                skipped_weak += 1
                diagnostics["weak_nogood_not_violated"] += 1
                continue
            nogood_added = self._add_schedule_conflict_cuts(
                node,
                int(source_vehicle),
                list(witness.routes),
                kind="schedule_nogood_core",
                vehicles=violated_vehicles,
            )
            if nogood_added:
                diagnostics["nogood_violated_conflicts"] += 1
                diagnostics["nogood_cuts_added"] += nogood_added
                added += nogood_added
        if skipped_weak:
            self.logger.log(
                "rim_conflict_skipped",
                node_id=node.id,
                skipped=skipped_weak,
                reason="weak_nogood_not_violated_by_current_lp",
            )
        if diagnostics["conflicts_checked"]:
            self.logger.log(
                "rim_conflict_diagnostics",
                node_id=node.id,
                **diagnostics,
            )
        return added

    def _try_restricted_master_heuristic(self, node: BPCNode, solution: RMPSolution) -> int:
        if not self.restricted_master_heuristic_enabled:
            return 0
        if node.depth > self.restricted_master_max_depth:
            return 0
        if self.stats.restricted_master_integer_calls >= self.restricted_master_max_calls:
            return 0
        if solution.objective is None:
            return 0
        if self.incumbent is not None and solution.objective >= self.incumbent.objective - self.integer_tol:
            return 0
        adaptive_active = (
            self.restricted_master_adaptive_enabled
            and int(node.depth) >= max(0, int(self.restricted_master_adaptive_min_depth))
        )
        productivity_guard_active = (
            adaptive_active and self.restricted_master_adaptive_productivity_guard_enabled
        )
        failure_streak = int(self._restricted_master_adaptive_failure_streak)
        unproductive_streak = int(self._restricted_master_adaptive_unproductive_streak)
        productive_skip_streak = int(self._restricted_master_adaptive_productive_skip_streak)
        adaptive_probe_forced = False
        if productivity_guard_active:
            skip_after = int(self.restricted_master_adaptive_productive_after_failures)
            max_consecutive_skips = int(self.restricted_master_adaptive_productive_max_consecutive_skips)
            if (
                skip_after > 0
                and max_consecutive_skips > 0
                and unproductive_streak >= skip_after
                and productive_skip_streak < max_consecutive_skips
            ):
                self._restricted_master_adaptive_productive_skip_streak += 1
                self.stats.restricted_master_adaptive_skips += 1
                self.logger.log(
                    "restricted_integer_master_adaptive_skip",
                    node_id=node.id,
                    depth=node.depth,
                    reason="productivity_guard",
                    failure_streak=failure_streak,
                    unproductive_streak=unproductive_streak,
                    skip_after=skip_after,
                    productive_skip_streak=self._restricted_master_adaptive_productive_skip_streak,
                    max_consecutive_skips=max_consecutive_skips,
                )
                return 0
            if (
                skip_after > 0
                and max_consecutive_skips > 0
                and unproductive_streak >= skip_after
                and productive_skip_streak >= max_consecutive_skips
            ):
                adaptive_probe_forced = True
                self.stats.restricted_master_adaptive_probe_forced += 1
        else:
            skip_after = int(self.restricted_master_adaptive_skip_after_failures)
            if adaptive_active and skip_after > 0 and failure_streak >= skip_after:
                self.stats.restricted_master_adaptive_skips += 1
                self.logger.log(
                    "restricted_integer_master_adaptive_skip",
                    node_id=node.id,
                    depth=node.depth,
                    reason="failure_streak",
                    failure_streak=failure_streak,
                    skip_after=skip_after,
                )
                return 0
        time_limit = min(self.restricted_master_time_limit, max(0.0, self.time_limit - self.elapsed() - 1.0))
        adaptive_reduced = False
        reduce_after = int(self.restricted_master_adaptive_after_failures)
        reduced_time_limit = float(self.restricted_master_adaptive_reduced_time_limit)
        adaptive_pressure = unproductive_streak if productivity_guard_active else failure_streak
        if (
            adaptive_active
            and reduce_after > 0
            and adaptive_pressure >= reduce_after
            and reduced_time_limit > 0.0
            and reduced_time_limit < time_limit
        ):
            time_limit = reduced_time_limit
            adaptive_reduced = True
            self.stats.restricted_master_adaptive_time_limit_reductions += 1
        if time_limit < 1.0:
            return 0

        routes = self._restricted_master_routes(solution)
        previous_repair_best = self.stats.restricted_master_integer_repair_best_objective
        previous_raw_best = self.stats.restricted_master_integer_raw_best_objective
        result = solve_restricted_integer_master(
            self.data,
            routes,
            self.cuts,
            node.branch_constraints,
            rmp_params=self.rmp_params,
            time_limit=time_limit,
            task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
            incumbent_bound=None if self.incumbent is None else self.incumbent.objective,
            schedule_aware=self.restricted_master_schedule_aware,
            max_no_good_rounds=self.restricted_master_max_no_good_rounds,
            schedule_capacity_oracle_max_states=self.schedule_capacity_oracle_max_states,
            schedule_capacity_conflict_max_subset_size=self.schedule_capacity_cut_max_subset_size,
            repair_enabled=self.restricted_master_repair_enabled,
            repair_max_attempts=self.restricted_master_repair_max_attempts,
            repair_max_states=self.restricted_master_repair_max_states,
            scan_solution_pool=self.restricted_master_scan_solution_pool_enabled,
            solution_pool_scan_limit=self.restricted_master_scan_solution_pool_limit,
        )
        self.stats.restricted_master_integer_calls += 1
        self.stats.restricted_master_integer_time += result.solving_time
        self.stats.restricted_master_integer_rejected += result.rejected_solutions
        self.stats.restricted_master_integer_no_good_cuts += result.no_good_cuts
        self.stats.restricted_master_integer_pair_conflict_cuts += result.pair_conflict_cuts
        self.stats.restricted_master_integer_route_set_packing_cuts += result.route_set_packing_cuts
        self.stats.restricted_master_integer_schedule_capacity_cuts += result.schedule_capacity_cuts
        self.stats.restricted_master_integer_repair_attempts += result.repair_attempts
        self.stats.restricted_master_integer_repair_successes += result.repair_successes
        self.stats.restricted_master_integer_repair_time += result.repair_time
        self.stats.restricted_master_integer_repair_states += result.repair_states
        repair_improved = False
        if result.repair_best_objective is not None:
            current_repair = previous_repair_best
            if current_repair is None or result.repair_best_objective < current_repair - self.integer_tol:
                self.stats.restricted_master_integer_repair_best_objective = result.repair_best_objective
                repair_improved = True
        raw_improved = False
        if result.raw_objective is not None:
            current_raw = previous_raw_best
            if current_raw is None or result.raw_objective < current_raw - self.integer_tol:
                self.stats.restricted_master_integer_raw_best_objective = result.raw_objective
                raw_improved = True
        added_conflict_cuts = self._add_restricted_master_conflict_cuts(node, result, solution)
        accepted = False
        if result.objective is not None:
            accepted = self._set_incumbent_from_assignment(result.assigned_routes, node_id=node.id, source=result.source)
            if accepted:
                self.stats.restricted_master_integer_feasible += 1
                current = self.stats.restricted_master_integer_best_objective
                if current is None or result.objective < current - self.integer_tol:
                    self.stats.restricted_master_integer_best_objective = result.objective
        productivity_reasons: list[str] = []
        if accepted:
            productivity_reasons.append("accepted")
        if added_conflict_cuts > 0:
            productivity_reasons.append("conflict_cuts")
        if raw_improved:
            productivity_reasons.append("raw_improved")
        if repair_improved:
            productivity_reasons.append("repair_improved")
        adaptive_productive_call = bool(productivity_reasons)
        if adaptive_active:
            status = str(result.status).upper()
            failed = (not accepted) and status == "TIME_LIMIT"
            if failed:
                self._restricted_master_adaptive_failure_streak += 1
            else:
                self._restricted_master_adaptive_failure_streak = 0
            self.stats.restricted_master_adaptive_failure_streak_max = max(
                self.stats.restricted_master_adaptive_failure_streak_max,
                int(self._restricted_master_adaptive_failure_streak),
            )
            if productivity_guard_active:
                if adaptive_productive_call:
                    self._restricted_master_adaptive_unproductive_streak = 0
                    self._restricted_master_adaptive_productive_skip_streak = 0
                else:
                    self._restricted_master_adaptive_unproductive_streak += 1
                    if adaptive_probe_forced:
                        self._restricted_master_adaptive_productive_skip_streak = 0
                self.stats.restricted_master_adaptive_unproductive_streak_max = max(
                    self.stats.restricted_master_adaptive_unproductive_streak_max,
                    int(self._restricted_master_adaptive_unproductive_streak),
                )
        self.logger.log(
            "restricted_integer_master",
            node_id=node.id,
            depth=node.depth,
            status=result.status,
            objective=None if result.objective is None else round(result.objective, 6),
            raw_objective=None if result.raw_objective is None else round(result.raw_objective, 6),
            accepted=accepted,
            selected_routes=result.selected_routes,
            route_pool=len(routes),
            schedule_aware=self.restricted_master_schedule_aware,
            rejected_solutions=result.rejected_solutions,
            no_good_cuts=result.no_good_cuts,
            pair_conflict_cuts=result.pair_conflict_cuts,
            route_set_packing_cuts=result.route_set_packing_cuts,
            schedule_capacity_cuts=result.schedule_capacity_cuts,
            repair_attempts=result.repair_attempts,
            repair_successes=result.repair_successes,
            repair_time=round(result.repair_time, 6),
            repair_states=result.repair_states,
            repair_best_objective=None if result.repair_best_objective is None else round(result.repair_best_objective, 6),
            solution_pool_scanned=result.solution_pool_scanned,
            solution_pool_accepted_rank=result.solution_pool_accepted_rank,
            added_schedule_cuts=added_conflict_cuts,
            time=round(result.solving_time, 6),
            adaptive_enabled=adaptive_active,
            adaptive_time_limit=round(time_limit, 6),
            adaptive_reduced=adaptive_reduced,
            adaptive_failure_streak=self._restricted_master_adaptive_failure_streak,
            adaptive_productivity_guard_enabled=productivity_guard_active,
            adaptive_productive_call=adaptive_productive_call,
            adaptive_productive_reasons=productivity_reasons,
            adaptive_unproductive_streak=self._restricted_master_adaptive_unproductive_streak,
            adaptive_productive_skip_streak=self._restricted_master_adaptive_productive_skip_streak,
            adaptive_probe_forced=adaptive_probe_forced,
        )
        return added_conflict_cuts

    def _process_node(self, node: BPCNode) -> list[BPCNode]:
        cg_iter = 0
        phase = "phase1"
        last_solution: RMPSolution | None = None
        node_certified = False
        persistent_rmp: PersistentRMP | None = None
        persistent_rmp_disabled = False
        node_route_pool, route_birth_iter = self._initial_node_route_pool(node)
        if route_birth_iter is None and self.route_pool_restart_enabled:
            route_birth_iter = {route.signature: 0 for route in self.pool.routes}
        self._log_route_pool_hygiene_diagnostics(node, stage="node_start")

        def solve_current_rmp() -> tuple[RMPSolution, str]:
            nonlocal persistent_rmp, persistent_rmp_disabled
            rmp_routes = self.pool.routes if node_route_pool is None else node_route_pool.routes
            if node_route_pool is not None:
                persistent_rmp_disabled = True
            if not self.persistent_rmp_enabled or persistent_rmp_disabled:
                return (
                    solve_rmp_lp(
                        self.data,
                        rmp_routes,
                        self.cuts,
                        node.branch_constraints,
                        phase=phase,
                        rmp_params=self.rmp_params,
                        verbose=False,
                        task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
                    ),
                    "rebuild",
                )
            try:
                if persistent_rmp is None or persistent_rmp.phase != phase:
                    persistent_rmp = PersistentRMP(
                        self.data,
                        rmp_routes,
                        self.cuts,
                        node.branch_constraints,
                        phase=phase,
                        rmp_params=self.rmp_params,
                        verbose=False,
                        task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
                    )
                    return (persistent_rmp.solve(), "persistent_rebuild")
                persistent_rmp.sync(rmp_routes, self.cuts)
                return (persistent_rmp.solve(), "persistent")
            except PersistentRMPRequiresRebuild:
                try:
                    persistent_rmp = PersistentRMP(
                        self.data,
                        rmp_routes,
                        self.cuts,
                        node.branch_constraints,
                        phase=phase,
                        rmp_params=self.rmp_params,
                        verbose=False,
                        task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
                    )
                    return (persistent_rmp.solve(), "persistent_rebuild")
                except Exception as exc:
                    self.logger.log(
                        "persistent_rmp_fallback",
                        node_id=node.id,
                        depth=node.depth,
                        phase=phase,
                        reason=type(exc).__name__,
                        message=str(exc),
                    )
                    persistent_rmp = None
                    persistent_rmp_disabled = True
            except Exception as exc:
                self.logger.log(
                    "persistent_rmp_fallback",
                    node_id=node.id,
                    depth=node.depth,
                    phase=phase,
                    reason=type(exc).__name__,
                    message=str(exc),
                )
                persistent_rmp = None
                persistent_rmp_disabled = True
            return (
                solve_rmp_lp(
                    self.data,
                    rmp_routes,
                    self.cuts,
                    node.branch_constraints,
                    phase=phase,
                    rmp_params=self.rmp_params,
                    verbose=False,
                    task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
                ),
                "rebuild_fallback",
            )

        while self._time_left():
            cg_iter += 1
            solution, rmp_backend = solve_current_rmp()
            self.stats.rmp_solves += 1
            last_solution = solution
            self.logger.log(
                "rmp",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                phase=phase,
                status=solution.status,
                objective=None if solution.objective is None else round(solution.objective, 6),
                artificial_sum=round(solution.artificial_sum, 6),
                route_count=len(self.pool.routes),
                local_route_count=len(self.pool.routes) if node_route_pool is None else len(node_route_pool.routes),
                route_pool_restart_enabled=node_route_pool is not None,
                cut_count=len(self.cuts),
                variable_count=solution.variable_count,
                constraint_count=solution.constraint_count,
                backend=rmp_backend,
            )
            roi_added = self._complete_pending_cut_roi(node, solution)
            if roi_added:
                continue

            if not solution.optimal or solution.duals is None:
                self.stats.fathomed_infeasible += 1
                self._log_fathom(node_id=node.id, reason=f"rmp_{solution.status.lower()}", bound=None)
                return []

            if phase == "phase2":
                if self.route_pool_restart_cleanup_enabled:
                    if node_route_pool is None:
                        created_pool = self._create_node_route_pool_from_solution(
                            node,
                            solution,
                            route_birth_iter,
                            cg_iter,
                        )
                        if created_pool is not None:
                            node_route_pool, route_birth_iter = created_pool
                            persistent_rmp = None
                            continue
                    elif self._cleanup_node_route_pool(
                        node,
                        node_route_pool,
                        solution,
                        route_birth_iter,
                        cg_iter,
                    ):
                        persistent_rmp = None
                        continue
                compacted_pool = self._compact_node_route_pool_by_task_set(
                    node,
                    solution,
                    node_route_pool,
                    route_birth_iter,
                    cg_iter,
                )
                if compacted_pool is not None:
                    node_route_pool, route_birth_iter = compacted_pool
                    persistent_rmp = None
                    continue
                purged_by_kind = self._purge_inactive_cuts(solution)
                purged = sum(purged_by_kind.values())
                if purged:
                    self.logger.log(
                        "cut_purged",
                        node_id=node.id,
                        removed=purged,
                        removed_by_kind=purged_by_kind,
                        remaining=len(self.cuts),
                    )
                    persistent_rmp = None
                    continue

            if phase == "phase1" and solution.artificial_sum <= self.integer_tol:
                phase = "phase2"
                persistent_rmp = None
                continue

            pricing: PricingResult | None = None
            added = 0
            if self.heuristic_pricing_enabled and self.heuristic_pricing_max_labels > 0:
                heuristic_pricing, heuristic_added = self._run_pricing(
                    node,
                    solution,
                    cg_iter=cg_iter,
                    phase=phase,
                    pricing_kind="heuristic",
                    max_routes_to_return=self.heuristic_pricing_routes_per_round,
                    max_labels=self.heuristic_pricing_max_labels,
                    selection_mode=self.heuristic_pricing_selection_mode,
                    route_pool=node_route_pool,
                    route_birth_iter=route_birth_iter,
                )
                if heuristic_added > 0:
                    continue
                if heuristic_pricing.exhausted:
                    # 中文注释：label 上限未触发时，该轮启发式调用已经完成完整枚举，可直接作为证明。
                    pricing = heuristic_pricing
                    self.stats.exact_pricing_calls += 1

                if (
                    pricing is None
                    and phase == "phase2"
                    and node.depth >= self.branch_node_heuristic_boost_min_depth
                    and self.branch_node_heuristic_boost_enabled
                    and self.branch_node_heuristic_boost_max_labels > self.heuristic_pricing_max_labels
                ):
                    boosted_pricing, boosted_added = self._run_pricing(
                        node,
                        solution,
                        cg_iter=cg_iter,
                        phase=phase,
                        pricing_kind="heuristic_boost",
                        max_routes_to_return=self.branch_node_heuristic_boost_routes_per_round,
                        max_labels=self.branch_node_heuristic_boost_max_labels,
                        selection_mode=self.heuristic_pricing_selection_mode,
                        route_pool=node_route_pool,
                        route_birth_iter=route_birth_iter,
                    )
                    if boosted_added > 0:
                        continue
                    if boosted_pricing.exhausted:
                        # 中文注释：boost 未触发 label 上限时同样给出完整枚举证明。
                        pricing = boosted_pricing
                        self.stats.exact_pricing_calls += 1

            if pricing is None:
                pricing, added = self._run_pricing(
                    node,
                    solution,
                    cg_iter=cg_iter,
                    phase=phase,
                    pricing_kind="exact",
                    max_routes_to_return=self._exact_routes_per_pricing(node),
                    max_labels=self.max_labels_per_pricing,
                    selection_mode=self.exact_pricing_selection_mode,
                    route_pool=node_route_pool,
                    route_birth_iter=route_birth_iter,
                )
            if added > 0:
                continue
            if not pricing.exhausted:
                self.abort_status = "PRICING_INCOMPLETE"
                self._log_fathom(node_id=node.id, reason="pricing_incomplete", bound=None)
                return []
            if phase == "phase1":
                self.stats.fathomed_infeasible += 1
                self._log_fathom(node_id=node.id, reason="phase1_infeasible", bound=None)
                return []
            if (
                self.early_bound_fathom_before_cuts_enabled
                and solution.objective is not None
                and self.incumbent is not None
                and float(solution.objective) >= float(self.incumbent.objective) - self.integer_tol
            ):
                last_solution = solution
                node_certified = True
                break
            separated = self._separate_crossing_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_subset_row_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_lm_rank1_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_witness_rank1_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_schedule_subset_cost_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_root_schedule_capacity_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_route_set_schedule_packing_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_weighted_route_schedule_packing_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_schedule_incompatibility_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_schedule_capacity_cuts(node, solution)
            if separated:
                continue
            node_certified = True
            break

        if not node_certified:
            if self.abort_status is None and not self._time_left():
                self.abort_status = "TIME_LIMIT"
                self.pending_node_bound = node.lower_bound
                self.timeout_pending_node_certified = False
                self._log_fathom(node_id=node.id, reason="time_limit_before_node_certificate", bound=None)
            return []
        if last_solution is None or not last_solution.optimal or last_solution.objective is None:
            return []

        node.lower_bound = float(last_solution.objective)
        self.stats.last_certified_node_bound = node.lower_bound
        if self.stats.root_relaxation is None and node.id == 0:
            self.stats.root_relaxation = node.lower_bound
        self._run_schedule_pack_relaxation(node, last_solution)

        if not self._time_left():
            self.abort_status = "TIME_LIMIT"
            self.pending_node_bound = node.lower_bound
            self.timeout_pending_node_certified = True
            self._log_fathom(node_id=node.id, reason="time_limit_after_node_certificate", bound=node.lower_bound)
            return []

        if self.incumbent is not None and node.lower_bound >= self.incumbent.objective - self.integer_tol:
            self.stats.fathomed_bound += 1
            self._log_fathom(node_id=node.id, reason="bound_after_schedule_pack", bound=node.lower_bound)
            return []

        decision_solution = last_solution
        if node_route_pool is not None:
            decision_solution = self._resolve_global_solution_for_branching(node, last_solution)

        if self._try_restricted_master_heuristic(node, decision_solution):
            return [
                BPCNode(
                    priority=max(node.lower_bound, node.schedule_pack_relaxation_bound or node.lower_bound),
                    id=node.id,
                    depth=node.depth,
                    branch_constraints=node.branch_constraints,
                    parent_id=node.parent_id,
                    description=node.description,
                    lower_bound=node.lower_bound,
                    schedule_pack_relaxation_bound=node.schedule_pack_relaxation_bound,
                )
            ]

        if not self._time_left():
            self.abort_status = "TIME_LIMIT"
            self.pending_node_bound = node.lower_bound
            self.timeout_pending_node_certified = True
            self._log_fathom(node_id=node.id, reason="time_limit_after_restricted_master", bound=node.lower_bound)
            return []

        if self.incumbent is not None and node.lower_bound >= self.incumbent.objective - self.integer_tol:
            self.stats.fathomed_bound += 1
            self._log_fathom(node_id=node.id, reason="bound", bound=node.lower_bound)
            return []

        integral = self._is_integral(decision_solution)
        if integral:
            cuts_added = self._validate_integral_or_cut(node, decision_solution)
            if cuts_added:
                return [
                    BPCNode(
                        priority=max(node.lower_bound, node.schedule_pack_relaxation_bound or node.lower_bound),
                        id=node.id,
                        depth=node.depth,
                        branch_constraints=node.branch_constraints,
                        parent_id=node.parent_id,
                        description=node.description,
                        lower_bound=node.lower_bound,
                        schedule_pack_relaxation_bound=node.schedule_pack_relaxation_bound,
                    )
                ]
            if self.abort_status is not None:
                return []
            self.stats.fathomed_integral += 1
            self._log_fathom(node_id=node.id, reason="integral", bound=node.lower_bound)
            return []

        branch = self._choose_branch(node, decision_solution)
        if branch is None:
            self.abort_status = "BRANCH_FAILED"
            self._log_fathom(node_id=node.id, reason="no_branch_candidate", bound=node.lower_bound)
            return []

        left, right = branch
        left_node = self._make_child(node, left)
        right_node = self._make_child(node, right)
        self.logger.log("branch", node_id=node.id, left=left.name(), right=right.name(), lower_bound=round(node.lower_bound, 6))
        return [left_node, right_node]

    def _cut_activity(self, cut: Cut, solution: RMPSolution) -> float:
        activity = sum(cut.coefficient(route, vehicle) * value for route, vehicle, value in solution.route_values)
        if hasattr(cut, "y_coefficient"):
            activity += sum(cut.y_coefficient(vehicle) * value for vehicle, value in solution.y_values.items())
        return activity

    def _cut_slack(self, cut: Cut, solution: RMPSolution) -> float:
        activity = self._cut_activity(cut, solution)
        if cut.sense == "<=":
            return float(cut.rhs) - activity
        if cut.sense == ">=":
            return activity - float(cut.rhs)
        raise ValueError(f"未知 cut sense: {cut.sense}")

    def _purge_inactive_cuts(self, solution: RMPSolution) -> dict[str, int]:
        if solution.duals is None:
            return {}
        kept: list[Cut] = []
        removed_by_kind: dict[str, int] = {}
        purgeable_nogood_kinds = {"schedule_nogood", "schedule_nogood_core", "schedule_nogood_full"}
        for cut in self.cuts:
            if (
                isinstance(
                    cut,
                    (
                        CrossingCut,
                        ScheduleCapacityCut,
                        ScheduleSubsetCostLowerBoundCut,
                        SubsetRowCut,
                        LimitedMemoryRank1Cut,
                    ),
                )
                and self.cut_purge_age > 0
            ):
                age_limit = self.cut_purge_age
                slack_limit = self.cut_purge_slack
                dual_limit = self.cut_purge_dual
            elif (
                self.schedule_nogood_purge_enabled
                and isinstance(cut, ScheduleNoGoodCut)
                and cut.kind in purgeable_nogood_kinds
                and self.schedule_nogood_purge_age > 0
            ):
                age_limit = self.schedule_nogood_purge_age
                slack_limit = self.schedule_nogood_purge_slack
                dual_limit = self.schedule_nogood_purge_dual
            else:
                kept.append(cut)
                continue
            key = cut.key
            slack = self._cut_slack(cut, solution)
            dual_abs = abs(float(solution.duals.cuts.get(cut.id, 0.0)))
            if slack > slack_limit and dual_abs <= dual_limit:
                self.cut_inactive_age[key] = self.cut_inactive_age.get(key, 0) + 1
            else:
                self.cut_inactive_age[key] = 0
            if self.cut_inactive_age.get(key, 0) >= age_limit:
                removed_by_kind[cut.kind] = removed_by_kind.get(cut.kind, 0) + 1
                self.cut_keys.discard(key)
                self.cut_inactive_age.pop(key, None)
            else:
                kept.append(cut)
        if removed_by_kind:
            self.cuts = kept
            self.stats.cuts_purged += sum(removed_by_kind.values())
        return removed_by_kind

    def _separate_crossing_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        # 中文注释：统一处理 RCI 和 k-path/resource cut，同一 S 只保留 RHS 最大的一条 crossing cut。
        if not self.crossing_cuts_enabled:
            return 0
        if node.depth > self.crossing_cut_max_depth:
            return 0
        rounds = self.cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.crossing_cut_max_rounds_per_node:
            return 0

        max_size = min(self.crossing_cut_max_subset_size, len(self.data.tasks))
        candidates: list[tuple[float, tuple[int, ...], int, int, int, float, float, str, int | None]] = []
        for size in range(2, max_size + 1):
            for subset in combinations(self.data.tasks, size):
                tasks = tuple(sorted(int(task) for task in subset))
                demand = sum(self.data.task_value(task, "d") for task in tasks)
                capacity_bound = capacity_route_lower_bound(self.data, tasks) if self.robust_capacity_cuts_enabled else 0
                resource_bound = self._resource_chromatic_bound(tasks) if self.resource_lower_bound_cuts_enabled else 0
                k_bound = max(capacity_bound, resource_bound)
                if k_bound <= 1:
                    continue
                rhs = float(2 * k_bound)
                existing_index = self._find_crossing_cut_index(tasks)
                if existing_index is not None and float(getattr(self.cuts[existing_index], "rhs", 0.0)) >= rhs - self.integer_tol:
                    continue
                temp_cut = CrossingCut(
                    id=-1,
                    tasks=tasks,
                    rhs=rhs,
                    k_bound=k_bound,
                    capacity_bound=capacity_bound,
                    resource_bound=resource_bound,
                    demand=demand,
                    capacity=self.data.capacity,
                )
                activity = self._cut_activity(temp_cut, solution)
                violation = rhs - activity
                if violation > self.crossing_cut_min_violation:
                    source = "resource" if resource_bound > capacity_bound else "capacity"
                    candidates.append((violation, tasks, k_bound, capacity_bound, resource_bound, demand, rhs, source, existing_index))

        if not candidates:
            return 0
        candidates.sort(key=lambda item: (-item[0], -item[2], len(item[1]), item[1]))
        added = 0
        upgraded = 0
        added_payload = []
        for violation, tasks, k_bound, capacity_bound, resource_bound, demand, rhs, source, existing_index in candidates[
            : max(1, self.crossing_cut_max_per_round)
        ]:
            cut = CrossingCut(
                id=self._allocate_cut_id(),
                tasks=tasks,
                rhs=rhs,
                k_bound=k_bound,
                capacity_bound=capacity_bound,
                resource_bound=resource_bound,
                demand=demand,
                capacity=self.data.capacity,
            )
            if existing_index is not None:
                old_cut = self.cuts[existing_index]
                if float(getattr(old_cut, "rhs", 0.0)) >= rhs - self.integer_tol:
                    continue
                self.cuts[existing_index] = cut
                self.cut_inactive_age[cut.key] = 0
                upgraded += 1
            else:
                if cut.key in self.cut_keys:
                    continue
                self.cuts.append(cut)
                self.cut_keys.add(cut.key)
                self.cut_inactive_age[cut.key] = 0
                added += 1

            if source == "resource":
                self.stats.resource_lower_bound_cuts_added += 1
            else:
                self.stats.robust_capacity_cuts_added += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "tasks": list(tasks),
                    "demand": round(demand, 6),
                    "capacity_bound": capacity_bound,
                    "resource_bound": resource_bound,
                    "k_bound": k_bound,
                    "rhs": round(rhs, 6),
                    "source": source,
                    "violation": round(violation, 9),
                    "action": "upgrade" if existing_index is not None else "add",
                }
            )
        changed = added + upgraded
        if changed:
            self.cut_rounds_by_node[node.id] = rounds + 1
            self.stats.cuts_added += added
            self.stats.crossing_cuts_added += added
            self.stats.crossing_cuts_upgraded += upgraded
            self.logger.log(
                "cut_added",
                node_id=node.id,
                family="crossing_cut",
                added=added,
                upgraded=upgraded,
                cuts=added_payload,
            )
        return changed

    def _find_crossing_cut_index(self, tasks: tuple[int, ...]) -> int | None:
        key = ("crossing_cut", frozenset(int(task) for task in tasks))
        for index, cut in enumerate(self.cuts):
            if isinstance(cut, CrossingCut) and cut.key == key:
                return index
        return None

    def _separate_subset_row_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        """分离经典 subset-row cuts，补强 route set-partitioning 下界。"""

        if not self.subset_row_cuts_enabled:
            return 0
        if node.depth > self.subset_row_cut_max_depth:
            return 0
        rounds = self.subset_row_cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.subset_row_cut_max_rounds_per_node:
            return 0
        self.subset_row_cut_rounds_by_node[node.id] = rounds + 1

        subsets = self._subset_row_candidate_subsets(solution)
        diagnostics: dict[str, float | int] = {
            "candidate_subsets": len(subsets),
            "candidate_size_max": max((len(tasks) for tasks in subsets), default=0),
            "k_values": len(self.subset_row_k_values),
            "skipped_duplicate": 0,
            "skipped_invalid_rhs": 0,
            "skipped_not_violated": 0,
            "violated_candidates": 0,
            "max_violation": 0.0,
            "added": 0,
        }
        candidates: list[tuple[float, tuple[int, ...], int, float, float]] = []
        seen: set[tuple] = set()
        for tasks in subsets:
            for divisor in self.subset_row_k_values:
                rhs = math.floor(len(tasks) / int(divisor))
                if rhs <= 0:
                    diagnostics["skipped_invalid_rhs"] = int(diagnostics["skipped_invalid_rhs"]) + 1
                    continue
                key = ("subset_row", tasks, int(divisor))
                if key in self.cut_keys or key in seen:
                    diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                    continue
                seen.add(key)
                activity = self._subset_row_activity(solution, tasks, int(divisor))
                violation = activity - float(rhs)
                if violation <= self.subset_row_cut_min_violation:
                    diagnostics["skipped_not_violated"] = int(diagnostics["skipped_not_violated"]) + 1
                    continue
                diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
                diagnostics["max_violation"] = max(float(diagnostics["max_violation"]), float(violation))
                candidates.append((violation, tasks, int(divisor), activity, float(rhs)))

        if not candidates:
            self.logger.log("subset_row_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
            return 0

        candidates.sort(key=lambda item: (-item[0], -len(item[1]), item[2], item[1]))
        added = 0
        added_payload = []
        for violation, tasks, divisor, activity, rhs in candidates[: max(1, self.subset_row_cut_max_per_round)]:
            cut = SubsetRowCut(id=self._allocate_cut_id(), tasks=tasks, divisor=divisor)
            if cut.key in self.cut_keys:
                continue
            self.cuts.append(cut)
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            added += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "tasks": list(tasks),
                    "divisor": divisor,
                    "activity": round(activity, 9),
                    "rhs": round(rhs, 9),
                    "activity_minus_rhs": round(violation, 9),
                }
            )

        diagnostics["added"] = int(added)
        self.logger.log("subset_row_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
        if not added:
            return 0
        self.stats.cuts_added += added
        self.stats.subset_row_cuts_added += added
        self.logger.log("cut_added", node_id=node.id, family="subset_row", added=added, cuts=added_payload)
        return added

    def _subset_row_candidate_subsets(self, solution: RMPSolution) -> list[tuple[int, ...]]:
        max_size = min(self.subset_row_cut_max_subset_size, len(self.data.tasks))
        if max_size < 2:
            return []
        candidates: set[tuple[int, ...]] = set()
        all_tasks = tuple(sorted(int(task) for task in self.data.tasks))
        if len(all_tasks) <= max_size:
            candidates.add(all_tasks)

        support = [
            (float(value), route)
            for route, _vehicle, value in solution.route_values
            if value > self.integer_tol and len(route.task_set) >= 2
        ]
        support.sort(key=lambda item: (-item[0] * len(item[1].task_set), -item[0], -len(item[1].task_set), item[1].signature))
        top_routes = [route for _value, route in support[: max(0, self.subset_row_candidate_top_routes)]]

        def add_tasks(tasks_iterable) -> None:
            if len(candidates) >= self.subset_row_candidate_max_sets:
                return
            tasks = tuple(sorted({int(task) for task in tasks_iterable}))
            if 2 <= len(tasks) <= max_size:
                candidates.add(tasks)

        for route in top_routes:
            route_tasks = tuple(sorted(int(task) for task in route.task_set))
            add_tasks(route_tasks)
            if len(route_tasks) > max_size:
                add_tasks(route_tasks[:max_size])
            for size in range(3, min(max_size, len(route_tasks)) + 1):
                for tasks in combinations(route_tasks, size):
                    add_tasks(tasks)
                    if len(candidates) >= self.subset_row_candidate_max_sets:
                        break
                if len(candidates) >= self.subset_row_candidate_max_sets:
                    break
            if len(candidates) >= self.subset_row_candidate_max_sets:
                break

        max_combo_routes = min(3, len(top_routes))
        for size in range(2, max_combo_routes + 1):
            for combo in combinations(top_routes, size):
                add_tasks(task for route in combo for task in route.task_set)
                if len(candidates) >= self.subset_row_candidate_max_sets:
                    break
            if len(candidates) >= self.subset_row_candidate_max_sets:
                break

        return sorted(candidates, key=lambda item: (len(item), item))[: max(0, self.subset_row_candidate_max_sets)]

    def _subset_row_activity(self, solution: RMPSolution, tasks: tuple[int, ...], divisor: int) -> float:
        subset = set(int(task) for task in tasks)
        return sum(
            math.floor(sum(1 for task in route.task_set if int(task) in subset) / int(divisor)) * float(value)
            for route, _vehicle, value in solution.route_values
        )

    def _separate_lm_rank1_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        """分离第一版 limited-memory rank-1 cut。"""

        if not self.lm_rank1_cuts_enabled:
            return 0
        if node.depth > self.lm_rank1_cut_max_depth:
            return 0
        rounds = self.lm_rank1_cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.lm_rank1_cut_max_rounds_per_node:
            return 0
        self.lm_rank1_cut_rounds_by_node[node.id] = rounds + 1

        subsets = self._lm_rank1_candidate_subsets(solution)
        diagnostics: dict[str, float | int | str] = {
            "candidate_subsets": len(subsets),
            "candidate_size_max": max((len(tasks) for tasks in subsets), default=0),
            "denominators": len(self.lm_rank1_denominators),
            "patterns": 0,
            "skipped_duplicate": 0,
            "skipped_invalid_rhs": 0,
            "skipped_not_violated": 0,
            "violated_candidates": 0,
            "max_violation": 0.0,
            "added": 0,
        }
        candidates: list[tuple[float, tuple[int, ...], tuple[int, ...], int, float, float, tuple[int, ...]]] = []
        seen: set[tuple] = set()
        for tasks in subsets:
            for denominator in self.lm_rank1_denominators:
                for multipliers, memory_tasks in self._lm_rank1_multiplier_patterns(solution, tasks, int(denominator)):
                    diagnostics["patterns"] = int(diagnostics["patterns"]) + 1
                    rhs = math.floor(sum(multipliers) / int(denominator))
                    if rhs <= 0:
                        diagnostics["skipped_invalid_rhs"] = int(diagnostics["skipped_invalid_rhs"]) + 1
                        continue
                    key = ("limited_memory_rank1", tasks, multipliers, int(denominator))
                    if key in self.cut_keys or key in seen:
                        diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                        continue
                    seen.add(key)
                    activity = self._lm_rank1_activity(solution, tasks, multipliers, int(denominator))
                    violation = activity - float(rhs)
                    if violation <= self.lm_rank1_cut_min_violation:
                        diagnostics["skipped_not_violated"] = int(diagnostics["skipped_not_violated"]) + 1
                        continue
                    diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
                    diagnostics["max_violation"] = max(float(diagnostics["max_violation"]), float(violation))
                    candidates.append((violation, tasks, multipliers, int(denominator), activity, float(rhs), memory_tasks))

        if not candidates:
            self.logger.log("lm_rank1_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
            return 0

        candidates.sort(key=lambda item: (-item[0], -sum(item[2]), -len(item[1]), item[3], item[1], item[2]))
        added = 0
        added_payload = []
        for violation, tasks, multipliers, denominator, activity, rhs, memory_tasks in candidates[
            : max(1, self.lm_rank1_cut_max_per_round)
        ]:
            cut = LimitedMemoryRank1Cut(
                id=self._allocate_cut_id(),
                tasks=tasks,
                multipliers=multipliers,
                denominator=denominator,
                memory_tasks=memory_tasks,
            )
            if cut.key in self.cut_keys:
                continue
            self.cuts.append(cut)
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            added += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "tasks": list(tasks),
                    "multipliers": list(multipliers),
                    "denominator": denominator,
                    "memory_tasks": list(memory_tasks),
                    "activity": round(activity, 9),
                    "rhs": round(rhs, 9),
                    "activity_minus_rhs": round(violation, 9),
                }
            )

        diagnostics["added"] = int(added)
        self.logger.log("lm_rank1_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
        if not added:
            return 0
        self.stats.cuts_added += added
        self.stats.lm_rank1_cuts_added += added
        self.logger.log("cut_added", node_id=node.id, family="limited_memory_rank1", added=added, cuts=added_payload)
        return added

    def _witness_rank1_source_enabled(self, source: str) -> bool:
        source = str(source)
        if source.startswith("route_pack") or source.startswith("weighted_route_pack"):
            return bool(self.witness_rank1_use_route_pack_roi)
        if source.startswith("rim"):
            return bool(self.witness_rank1_use_rim_witness)
        if source.startswith("incompatibility") or source.startswith("schedule_incompatibility"):
            return bool(self.witness_rank1_use_incompatibility_witness)
        return True

    def _witness_rank1_source_strength(self, source: str) -> float:
        source = str(source)
        if source.startswith("route_pack_roi"):
            return 6.0
        if source.startswith("rim"):
            return 5.0
        if source.startswith("incompatibility") or source.startswith("schedule_incompatibility"):
            return 4.0
        if source.startswith("route_pack"):
            return 3.0
        return 1.0

    def _record_witness_rank1_tasks(
        self,
        tasks: tuple[int, ...] | list[int] | set[int],
        *,
        source: str,
        node_id: int | None,
        vehicle: int | None = None,
        score: float = 0.0,
    ) -> None:
        if not self._witness_rank1_source_enabled(source):
            return
        normalized = tuple(sorted({int(task) for task in tasks}))
        if len(normalized) < 2:
            return
        entry = self.witness_rank1_memory.get(normalized)
        if entry is None:
            entry = {
                "tasks": normalized,
                "source_count": {},
                "score": 0.0,
                "hits": 0,
                "vehicles": set(),
                "last_node": None,
            }
            self.witness_rank1_memory[normalized] = entry
        source_count = entry["source_count"]
        source_count[str(source)] = int(source_count.get(str(source), 0)) + 1
        entry["score"] = float(entry.get("score", 0.0)) + float(score) + self._witness_rank1_source_strength(source)
        entry["hits"] = int(entry.get("hits", 0)) + 1
        entry["last_node"] = None if node_id is None else int(node_id)
        if vehicle is not None:
            entry["vehicles"].add(int(vehicle))

    def _record_witness_rank1_route_pack_roi(self, node_id: int, diagnostics: dict[str, Any]) -> None:
        if (
            not self.witness_rank1_cuts_enabled
            or not self.witness_rank1_use_route_pack_roi
            or not bool(diagnostics.get("low_improvement", False))
        ):
            return
        classification = str(diagnostics.get("classification", ""))
        if classification not in {"same_pool_degeneracy", "pricing_mousehole", "mixed", "objective_degeneracy_no_support_change"}:
            return
        core_signatures = [
            tuple(sorted({int(task) for task in signature}))
            for signature in diagnostics.get("cut_core_signatures", ()) or ()
            if len(signature) >= 2
        ]
        tasks = tuple(int(task) for task in diagnostics.get("cut_core_task_union", ()) or ())
        replacement_count = int(diagnostics.get("same_pool_replacement_count", 0) or 0) + int(
            diagnostics.get("pricing_replacement_count", 0) or 0
        )
        score = 1.0 + float(replacement_count) + float(diagnostics.get("max_task_overlap_old_pool", 0.0) or 0.0)
        self._record_witness_rank1_tasks(
            tasks,
            source=f"route_pack_roi_{classification}",
            node_id=node_id,
            vehicle=None,
            score=score,
        )
        if classification == "objective_degeneracy_no_support_change":
            return

        def normalized_signatures(name: str) -> list[tuple[int, ...]]:
            signatures: list[tuple[int, ...]] = []
            for signature in diagnostics.get(name, ()) or ():
                normalized = tuple(sorted({int(task) for task in signature}))
                if len(normalized) >= 2:
                    signatures.append(normalized)
            signatures = list(dict.fromkeys(signatures))
            core_tasks = set(tasks)
            signatures.sort(
                key=lambda signature: (
                    -self._route_pack_roi_overlap(signature, core_tasks),
                    len(signature),
                    signature,
                )
            )
            return signatures[:8]

        def record_replacements(signatures: list[tuple[int, ...]], source_prefix: str, base_score: float) -> None:
            if not signatures:
                return
            replacement_union = tuple(sorted({task for signature in signatures for task in signature}))
            self._record_witness_rank1_tasks(
                replacement_union,
                source=f"{source_prefix}_union_{classification}",
                node_id=node_id,
                vehicle=None,
                score=base_score + float(len(signatures)),
            )
            paired = 0
            for signature in signatures:
                overlap = self._route_pack_roi_overlap(signature, set(tasks))
                self._record_witness_rank1_tasks(
                    signature,
                    source=f"{source_prefix}_signature_{classification}",
                    node_id=node_id,
                    vehicle=None,
                    score=base_score + 2.0 * float(overlap),
                )
                for core in core_signatures:
                    if paired >= 12:
                        return
                    pair_tasks = tuple(sorted(set(signature) | set(core)))
                    if len(pair_tasks) < 3:
                        continue
                    pair_overlap = min(
                        self._route_pack_roi_overlap(signature, set(core)),
                        self._route_pack_roi_overlap(core, set(signature)),
                    )
                    if pair_overlap < 0.5:
                        continue
                    self._record_witness_rank1_tasks(
                        pair_tasks,
                        source=f"{source_prefix}_core_pair_{classification}",
                        node_id=node_id,
                        vehicle=None,
                        score=base_score + 3.0 + 2.0 * float(pair_overlap),
                    )
                    paired += 1

        same_pool_signatures = normalized_signatures("same_pool_replacement_signatures")
        pricing_signatures = normalized_signatures("pricing_replacement_signatures")
        record_replacements(same_pool_signatures, "route_pack_roi_same_pool_replacement", 8.0)
        record_replacements(pricing_signatures, "route_pack_roi_pricing_replacement", 7.0)

    def _record_route_pack_branch_signal(self, diagnostics: dict[str, Any]) -> None:
        if not self.route_pack_branch_signal_enabled or not bool(diagnostics.get("low_improvement", False)):
            return
        classification = str(diagnostics.get("classification", ""))
        if classification not in {"same_pool_degeneracy", "mixed", "objective_degeneracy_no_support_change"}:
            return

        def norm_signatures(value: Any) -> list[tuple[int, ...]]:
            signatures: list[tuple[int, ...]] = []
            for signature in value or ():
                normalized = tuple(int(task) for task in signature)
                if len(normalized) >= 2:
                    signatures.append(normalized)
            return signatures

        pre_support = norm_signatures(diagnostics.get("pre_support_signatures"))
        replacements = norm_signatures(diagnostics.get("same_pool_replacement_signatures"))
        if not pre_support or not replacements:
            return

        pre_by_task_set: dict[frozenset[int], list[tuple[int, ...]]] = {}
        for signature in pre_support:
            pre_by_task_set.setdefault(frozenset(signature), []).append(signature)

        updates = 0
        for replacement in replacements:
            base_signatures = pre_by_task_set.get(frozenset(replacement), [])
            for base in base_signatures:
                if base == replacement:
                    continue
                base_arcs = {(int(left), int(right)) for left, right in zip(base[:-1], base[1:])}
                replacement_arcs = {
                    (int(left), int(right))
                    for left, right in zip(replacement[:-1], replacement[1:])
                }
                for arc in sorted(base_arcs.symmetric_difference(replacement_arcs)):
                    self.route_pack_branch_arc_scores[arc] = self.route_pack_branch_arc_scores.get(arc, 0.0) + 1.0
                    updates += 1
        if updates:
            self.stats.task_schedule_capacity_branch_signal_candidates += updates

    def _route_pack_branch_boost(self, candidate: BranchCandidate, node: BPCNode | None = None) -> float:
        if not self.route_pack_branch_signal_apply_enabled or candidate.kind != "arc":
            return 0.0
        if node is not None and int(node.depth) < int(self.route_pack_branch_signal_apply_min_depth):
            return 0.0
        arc = (int(candidate.left.task_i), int(candidate.left.task_j or 0))
        score = float(self.route_pack_branch_arc_scores.get(arc, 0.0))
        if score <= 0.0:
            return 0.0
        return min(0.25, float(self.route_pack_branch_signal_boost) * score)

    def _route_pack_branch_summary(self) -> dict[str, Any]:
        if not self.route_pack_branch_arc_scores:
            return {"arc_count": 0, "top_arcs": []}
        top = sorted(self.route_pack_branch_arc_scores.items(), key=lambda item: (-item[1], item[0]))[:10]
        return {
            "arc_count": len(self.route_pack_branch_arc_scores),
            "apply_enabled": bool(self.route_pack_branch_signal_apply_enabled),
            "apply_min_depth": int(self.route_pack_branch_signal_apply_min_depth),
            "top_arcs": [
                {"arc": [int(left), int(right)], "score": round(float(score), 6)}
                for (left, right), score in top
            ],
        }

    def _witness_rank1_candidate_subsets(self, solution: RMPSolution) -> list[tuple[tuple[int, ...], str, float]]:
        max_size = min(max(2, int(self.witness_rank1_max_subset_size)), len(self.data.tasks))
        if max_size < 2 or not self.witness_rank1_memory:
            return []
        pressure = {int(task): 0.0 for task in self.data.tasks}
        for route, _vehicle, value in solution.route_values:
            if float(value) <= self.integer_tol:
                continue
            for task in route.task_set:
                if int(task) in pressure:
                    pressure[int(task)] += float(value)

        candidates: dict[tuple[int, ...], tuple[str, float]] = {}

        def add_candidate(tasks: tuple[int, ...], source: str, score: float) -> None:
            tasks = tuple(sorted({int(task) for task in tasks}))
            if len(tasks) < 2:
                return
            if len(tasks) > max_size:
                ordered = sorted(tasks, key=lambda task: (-pressure.get(int(task), 0.0), int(task)))
                tasks = tuple(sorted(ordered[:max_size]))
            old = candidates.get(tasks)
            if old is None or float(score) > float(old[1]):
                candidates[tasks] = (source, float(score))

        for tasks, entry in self.witness_rank1_memory.items():
            source_count = entry.get("source_count", {})
            if source_count:
                source = max(source_count, key=lambda key: int(source_count[key]))
            else:
                source = "witness"
            if not self._witness_rank1_source_enabled(source):
                continue
            score = float(entry.get("score", 0.0)) + float(entry.get("hits", 0))
            add_candidate(tuple(tasks), str(source), score)
            if len(tasks) > max_size:
                ordered = sorted(tasks, key=lambda task: (-pressure.get(int(task), 0.0), int(task)))
                for size in range(3, max_size + 1):
                    add_candidate(tuple(ordered[:size]), str(source), score - 0.01 * float(max_size - size))

        ranked = sorted(candidates.items(), key=lambda item: (-item[1][1], len(item[0]), item[0]))
        return [(tasks, source, score) for tasks, (source, score) in ranked[: max(0, int(self.witness_rank1_max_candidates))]]

    def _separate_witness_rank1_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        if not self.witness_rank1_cuts_enabled:
            return 0
        if node.depth > self.witness_rank1_max_depth:
            return 0
        rounds = self.witness_rank1_cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.witness_rank1_max_rounds_per_node:
            return 0
        if not (self.witness_rank1_use_subset_row or self.witness_rank1_use_lm_rank1):
            return 0

        subsets = self._witness_rank1_candidate_subsets(solution)
        diagnostics: dict[str, Any] = {
            "candidate_subsets": len(subsets),
            "candidate_size_max": max((len(tasks) for tasks, _source, _score in subsets), default=0),
            "candidate_sources": {},
            "patterns": 0,
            "skipped_duplicate": 0,
            "skipped_invalid_rhs": 0,
            "skipped_not_violated": 0,
            "violated_candidates": 0,
            "max_violation": 0.0,
            "added": 0,
            "subset_row_added": 0,
            "lm_rank1_added": 0,
        }
        self.stats.witness_rank1_candidates_generated += len(subsets)
        for _tasks, source, _score in subsets:
            diagnostics["candidate_sources"][source] = int(diagnostics["candidate_sources"].get(source, 0)) + 1
            self.stats.witness_rank1_candidates_by_source[source] = (
                self.stats.witness_rank1_candidates_by_source.get(source, 0) + 1
            )

        if not subsets:
            # Do not spend the per-node budget before route-pack/RIM witnesses
            # have had a chance to populate the memory later in the same node.
            self.logger.log("witness_rank1_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
            return 0

        self.witness_rank1_cut_rounds_by_node[node.id] = rounds + 1

        candidates: list[tuple[float, float, str, tuple[int, ...], tuple[int, ...] | None, int, float, float, str]] = []
        seen: set[tuple] = set()
        for tasks, source, score in subsets:
            if self.witness_rank1_use_subset_row:
                for divisor in self.subset_row_k_values:
                    rhs = math.floor(len(tasks) / int(divisor))
                    if rhs <= 0:
                        diagnostics["skipped_invalid_rhs"] = int(diagnostics["skipped_invalid_rhs"]) + 1
                        continue
                    key = ("subset_row", tasks, int(divisor))
                    if key in self.cut_keys or key in seen:
                        diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                        continue
                    seen.add(key)
                    activity = self._subset_row_activity(solution, tasks, int(divisor))
                    violation = activity - float(rhs)
                    if violation <= self.witness_rank1_min_violation:
                        diagnostics["skipped_not_violated"] = int(diagnostics["skipped_not_violated"]) + 1
                        continue
                    diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
                    diagnostics["max_violation"] = max(float(diagnostics["max_violation"]), float(violation))
                    candidates.append((violation, score, "subset_row", tasks, None, int(divisor), activity, float(rhs), source))
            if self.witness_rank1_use_lm_rank1:
                for denominator in self.lm_rank1_denominators:
                    for multipliers, memory_tasks in self._lm_rank1_multiplier_patterns(solution, tasks, int(denominator)):
                        diagnostics["patterns"] = int(diagnostics["patterns"]) + 1
                        rhs = math.floor(sum(multipliers) / int(denominator))
                        if rhs <= 0:
                            diagnostics["skipped_invalid_rhs"] = int(diagnostics["skipped_invalid_rhs"]) + 1
                            continue
                        key = ("limited_memory_rank1", tasks, multipliers, int(denominator))
                        if key in self.cut_keys or key in seen:
                            diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                            continue
                        seen.add(key)
                        activity = self._lm_rank1_activity(solution, tasks, multipliers, int(denominator))
                        violation = activity - float(rhs)
                        if violation <= self.witness_rank1_min_violation:
                            diagnostics["skipped_not_violated"] = int(diagnostics["skipped_not_violated"]) + 1
                            continue
                        diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
                        diagnostics["max_violation"] = max(float(diagnostics["max_violation"]), float(violation))
                        candidates.append(
                            (violation, score, "limited_memory_rank1", tasks, multipliers, int(denominator), activity, float(rhs), source)
                        )

        self.stats.witness_rank1_candidates_after_precheck += int(diagnostics["violated_candidates"])
        self.stats.witness_rank1_violated_candidates += int(diagnostics["violated_candidates"])
        self.stats.witness_rank1_duplicate_skips += int(diagnostics["skipped_duplicate"])
        self.stats.witness_rank1_best_violation = max(
            float(self.stats.witness_rank1_best_violation),
            float(diagnostics["max_violation"]),
        )
        if not candidates:
            self.logger.log("witness_rank1_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
            return 0

        candidates.sort(key=lambda item: (-item[0], -item[1], 0 if item[2] == "subset_row" else 1, -len(item[3]), item[3], item[4] or ()))
        added = 0
        added_payload: list[dict[str, Any]] = []
        for violation, score, cut_kind, tasks, multipliers, divisor_or_denominator, activity, rhs, source in candidates[
            : max(1, int(self.witness_rank1_max_cuts_per_round))
        ]:
            if cut_kind == "subset_row":
                cut = SubsetRowCut(id=self._allocate_cut_id(), tasks=tasks, divisor=divisor_or_denominator)
            else:
                assert multipliers is not None
                memory_tasks = tuple(sorted(int(task) for task, multiplier in zip(tasks, multipliers) if int(multiplier) > 1))
                cut = LimitedMemoryRank1Cut(
                    id=self._allocate_cut_id(),
                    tasks=tasks,
                    multipliers=multipliers,
                    denominator=divisor_or_denominator,
                    memory_tasks=memory_tasks,
                )
            if cut.key in self.cut_keys:
                diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                continue
            self.cuts.append(cut)
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            added += 1
            if cut_kind == "subset_row":
                diagnostics["subset_row_added"] = int(diagnostics["subset_row_added"]) + 1
                self.stats.subset_row_cuts_added += 1
                self.stats.witness_rank1_subset_row_cuts_added += 1
            else:
                diagnostics["lm_rank1_added"] = int(diagnostics["lm_rank1_added"]) + 1
                self.stats.lm_rank1_cuts_added += 1
                self.stats.witness_rank1_lm_rank1_cuts_added += 1
            payload = {
                "id": cut.id,
                "cut_kind": cut_kind,
                "tasks": list(tasks),
                "source": source,
                "witness_score": round(float(score), 6),
                "activity": round(float(activity), 9),
                "rhs": round(float(rhs), 9),
                "activity_minus_rhs": round(float(violation), 9),
            }
            if cut_kind == "subset_row":
                payload["divisor"] = int(divisor_or_denominator)
            else:
                payload["denominator"] = int(divisor_or_denominator)
                payload["multipliers"] = list(multipliers or ())
            added_payload.append(payload)

        diagnostics["added"] = int(added)
        self.logger.log("witness_rank1_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
        if not added:
            return 0
        self.stats.cuts_added += added
        self.stats.witness_rank1_cuts_added += added
        self.logger.log("cut_added", node_id=node.id, family="witness_rank1", added=added, cuts=added_payload)
        return added

    def _lm_rank1_candidate_subsets(self, solution: RMPSolution) -> list[tuple[int, ...]]:
        max_size = min(self.lm_rank1_cut_max_subset_size, len(self.data.tasks))
        if max_size < 2:
            return []
        candidates: set[tuple[int, ...]] = set()
        support = [
            (float(value), route)
            for route, _vehicle, value in solution.route_values
            if value > self.integer_tol and len(route.task_set) >= 2
        ]
        support.sort(key=lambda item: (-item[0] * len(item[1].task_set), -item[0], -len(item[1].task_set), item[1].signature))
        top_routes = [route for _value, route in support[: max(0, self.lm_rank1_candidate_top_routes)]]

        def add_tasks(tasks_iterable) -> None:
            if len(candidates) >= self.lm_rank1_candidate_max_sets:
                return
            tasks = tuple(sorted({int(task) for task in tasks_iterable}))
            if 2 <= len(tasks) <= max_size:
                candidates.add(tasks)

        for route in top_routes:
            route_tasks = tuple(sorted(int(task) for task in route.task_set))
            add_tasks(route_tasks)
            for size in range(3, min(max_size, len(route_tasks)) + 1):
                for tasks in combinations(route_tasks, size):
                    add_tasks(tasks)
                    if len(candidates) >= self.lm_rank1_candidate_max_sets:
                        break
                if len(candidates) >= self.lm_rank1_candidate_max_sets:
                    break
            if len(candidates) >= self.lm_rank1_candidate_max_sets:
                break

        max_combo_routes = min(4, len(top_routes))
        for size in range(2, max_combo_routes + 1):
            for combo in combinations(top_routes, size):
                add_tasks(task for route in combo for task in route.task_set)
                if len(candidates) >= self.lm_rank1_candidate_max_sets:
                    break
            if len(candidates) >= self.lm_rank1_candidate_max_sets:
                break

        return sorted(candidates, key=lambda item: (len(item), item))[: max(0, self.lm_rank1_candidate_max_sets)]

    def _lm_rank1_multiplier_patterns(
        self,
        solution: RMPSolution,
        tasks: tuple[int, ...],
        denominator: int,
    ) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
        denominator = max(3, int(denominator))
        memory_size = max(1, min(int(self.lm_rank1_memory_size), len(tasks)))
        subset = set(int(task) for task in tasks)
        pressure = {int(task): 0.0 for task in tasks}
        for route, _vehicle, value in solution.route_values:
            hits = [int(task) for task in route.task_set if int(task) in subset]
            if len(hits) < 2:
                continue
            increment = float(value) * float(len(hits) - 1)
            for task in hits:
                pressure[task] += increment
        ordered = sorted(tasks, key=lambda task: (-pressure[int(task)], int(task)))
        memory_tasks = tuple(sorted(int(task) for task in ordered[:memory_size]))
        patterns: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
        seen: set[tuple[int, ...]] = set()

        def add_pattern(weight_by_task: dict[int, int]) -> None:
            if len(patterns) >= max(1, self.lm_rank1_max_patterns_per_set):
                return
            multipliers = tuple(max(1, min(denominator - 1, int(weight_by_task.get(int(task), 1)))) for task in tasks)
            if multipliers in seen:
                return
            if all(value == 1 for value in multipliers) and denominator in self.subset_row_k_values:
                return
            seen.add(multipliers)
            heavy_memory = tuple(sorted(int(task) for task, value in zip(tasks, multipliers) if value > 1))
            patterns.append((multipliers, heavy_memory or memory_tasks))

        # 中文注释：uniform denominator 不在普通 subset-row 中时也可作为 rank-1 候选。
        add_pattern({})
        for task in ordered[:memory_size]:
            add_pattern({int(task): denominator - 1})
            if denominator > 3:
                add_pattern({int(task): 2})
        for left, right in combinations(ordered[:memory_size], 2):
            add_pattern({int(left): min(2, denominator - 1), int(right): min(2, denominator - 1)})
            if denominator > 3:
                add_pattern({int(left): denominator - 1, int(right): 2})
                add_pattern({int(left): 2, int(right): denominator - 1})
            if len(patterns) >= max(1, self.lm_rank1_max_patterns_per_set):
                break
        if len(patterns) < max(1, self.lm_rank1_max_patterns_per_set):
            # 中文注释：规范化的 limited-memory R1C 候选。只在 memory 任务上枚举非均匀
            # multiplier，并按当前 LP pressure 排序；非 memory 任务保持 multiplier=1。
            # 这仍是普通 rank-1 CG cut，memory 只限制候选搜索规模，不影响有效性。
            memory_order = [int(task) for task in ordered[:memory_size]]
            values = tuple(range(1, denominator))
            scored_patterns: list[tuple[float, dict[int, int]]] = []
            for weights in product(values, repeat=len(memory_order)):
                if all(weight == 1 for weight in weights):
                    continue
                weight_by_task = {task: int(weight) for task, weight in zip(memory_order, weights)}
                multiplier_sum = len(tasks) + sum(int(weight) - 1 for weight in weights)
                rhs = multiplier_sum // denominator
                if rhs <= 0:
                    continue
                score = sum(float(pressure[task]) * float(int(weight) - 1) for task, weight in zip(memory_order, weights))
                scored_patterns.append((score, weight_by_task))
            scored_patterns.sort(
                key=lambda item: (
                    -item[0],
                    -sum(item[1].values()),
                    tuple(-item[1][task] for task in memory_order),
                )
            )
            for _score, weight_by_task in scored_patterns:
                add_pattern(weight_by_task)
                if len(patterns) >= max(1, self.lm_rank1_max_patterns_per_set):
                    break
        return patterns

    def _lm_rank1_activity(
        self,
        solution: RMPSolution,
        tasks: tuple[int, ...],
        multipliers: tuple[int, ...],
        denominator: int,
    ) -> float:
        weight_by_task = {int(task): int(multiplier) for task, multiplier in zip(tasks, multipliers)}
        return sum(
            math.floor(sum(weight_by_task.get(int(task), 0) for task in route.task_set) / int(denominator)) * float(value)
            for route, _vehicle, value in solution.route_values
        )

    def _separate_schedule_subset_cost_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        """分离成本型单车 schedule lower-bound cut。"""

        if not self.schedule_subset_cost_cuts_enabled:
            return 0
        if node.depth > self.schedule_subset_cost_cut_max_depth:
            return 0
        rounds = self.schedule_subset_cost_cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.schedule_subset_cost_cut_max_rounds_per_node:
            return 0

        candidate_subsets_by_vehicle = self._schedule_subset_cost_candidate_subsets_by_vehicle(solution)
        diagnostics: dict[str, float | int] = {
            "vehicles_checked": 0,
            "vehicles_active": 0,
            "candidate_subsets": 0,
            "candidate_size_max": 0,
            "skipped_vehicle_inactive": 0,
            "skipped_duplicate": 0,
            "oracle_queries": 0,
            "skipped_oracle_incomplete": 0,
            "skipped_oracle_infeasible": 0,
            "skipped_nonpositive_bound": 0,
            "skipped_not_violated": 0,
            "violated_candidates": 0,
            "oracle_states_total": 0,
            "oracle_states_max": 0,
            "max_violation": 0.0,
            "added": 0,
        }
        candidates: list[tuple[float, int, tuple[int, ...], float, int, float, float, float]] = []
        seen: set[tuple] = set()
        for vehicle in self.data.vehicles:
            diagnostics["vehicles_checked"] = int(diagnostics["vehicles_checked"]) + 1
            y_value = float(solution.y_values.get(vehicle, 0.0))
            if y_value <= self.integer_tol:
                diagnostics["skipped_vehicle_inactive"] = int(diagnostics["skipped_vehicle_inactive"]) + 1
                continue
            diagnostics["vehicles_active"] = int(diagnostics["vehicles_active"]) + 1
            vehicle_cost = self._vehicle_route_cost(solution, int(vehicle))
            for tasks in candidate_subsets_by_vehicle.get(int(vehicle), []):
                diagnostics["candidate_subsets"] = int(diagnostics["candidate_subsets"]) + 1
                diagnostics["candidate_size_max"] = max(int(diagnostics["candidate_size_max"]), len(tasks))
                preliminary_key = ("schedule_subset_cost_lb", int(vehicle), tasks)
                if preliminary_key in seen:
                    diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                    continue
                seen.add(preliminary_key)
                diagnostics["oracle_queries"] = int(diagnostics["oracle_queries"]) + 1
                oracle = self._schedule_subset_cost_bound(tasks)
                if oracle is None or not oracle.exact:
                    diagnostics["skipped_oracle_incomplete"] = int(diagnostics["skipped_oracle_incomplete"]) + 1
                    continue
                diagnostics["oracle_states_total"] = int(diagnostics["oracle_states_total"]) + int(oracle.states_explored)
                diagnostics["oracle_states_max"] = max(int(diagnostics["oracle_states_max"]), int(oracle.states_explored))
                if not oracle.feasible or oracle.lower_bound is None:
                    diagnostics["skipped_oracle_infeasible"] = int(diagnostics["skipped_oracle_infeasible"]) + 1
                    continue
                lower_bound = float(oracle.lower_bound)
                if lower_bound <= self.integer_tol:
                    diagnostics["skipped_nonpositive_bound"] = int(diagnostics["skipped_nonpositive_bound"]) + 1
                    continue
                key = ("schedule_subset_cost_lb", int(vehicle), tasks, round(lower_bound, 9))
                if key in self.cut_keys:
                    diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                    continue
                task_mass = self._task_vehicle_mass(solution, tasks, int(vehicle))
                activity = vehicle_cost - lower_bound * task_mass + lower_bound * float(len(tasks) - 1) * y_value
                violation = -activity
                if violation <= self.schedule_subset_cost_cut_min_violation:
                    diagnostics["skipped_not_violated"] = int(diagnostics["skipped_not_violated"]) + 1
                    continue
                diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
                diagnostics["max_violation"] = max(float(diagnostics["max_violation"]), float(violation))
                candidates.append(
                    (
                        violation,
                        int(vehicle),
                        tasks,
                        lower_bound,
                        int(oracle.states_explored),
                        y_value,
                        vehicle_cost,
                        task_mass,
                    )
                )

        if not candidates:
            self.logger.log(
                "schedule_subset_cost_diagnostics",
                node_id=node.id,
                depth=node.depth,
                round=rounds + 1,
                **diagnostics,
            )
            return 0

        candidates.sort(key=lambda item: (-item[0], -len(item[2]), item[1], item[2]))
        added = 0
        added_payload = []
        for violation, vehicle, tasks, lower_bound, states, y_value, vehicle_cost, task_mass in candidates[
            : max(1, self.schedule_subset_cost_cut_max_per_round)
        ]:
            cut = ScheduleSubsetCostLowerBoundCut(
                id=self._allocate_cut_id(),
                vehicle=vehicle,
                tasks=tasks,
                lower_bound=lower_bound,
                oracle_states=states,
            )
            if cut.key in self.cut_keys:
                continue
            self.cuts.append(cut)
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            added += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": vehicle,
                    "tasks": list(tasks),
                    "lower_bound": round(lower_bound, 9),
                    "y": round(y_value, 9),
                    "vehicle_route_cost": round(vehicle_cost, 9),
                    "task_mass": round(task_mass, 9),
                    "activity_minus_rhs": round(-violation, 9),
                    "violation": round(violation, 9),
                    "oracle_states": states,
                }
            )

        diagnostics["added"] = int(added)
        self.logger.log(
            "schedule_subset_cost_diagnostics",
            node_id=node.id,
            depth=node.depth,
            round=rounds + 1,
            **diagnostics,
        )
        if not added:
            return 0
        self.schedule_subset_cost_cut_rounds_by_node[node.id] = rounds + 1
        self.stats.cuts_added += added
        self.stats.schedule_subset_cost_cuts_added += added
        self.logger.log("cut_added", node_id=node.id, family="schedule_subset_cost_lb", added=added, cuts=added_payload)
        return added

    def _schedule_subset_cost_candidate_subsets_by_vehicle(self, solution: RMPSolution) -> dict[int, list[tuple[int, ...]]]:
        max_size = min(self.schedule_subset_cost_cut_max_subset_size, len(self.data.tasks))
        if max_size < 2:
            return {int(vehicle): [] for vehicle in self.data.vehicles}
        all_tasks = tuple(sorted(int(task) for task in self.data.tasks))
        by_vehicle: dict[int, list[tuple[int, ...]]] = {}
        for vehicle in self.data.vehicles:
            candidates: set[tuple[int, ...]] = set()
            if len(all_tasks) <= max_size:
                candidates.add(all_tasks)
            task_values = self._vehicle_task_values(solution, int(vehicle))
            value_by_task = {task: value for value, task in task_values}
            y_value = float(solution.y_values.get(vehicle, 0.0))
            ordered = [task for _value, task in task_values[:max_size]]
            for size in range(2, len(ordered) + 1):
                candidates.add(tuple(sorted(ordered[:size])))

            top_count = max(max_size, self.schedule_subset_cost_candidate_top_tasks)
            top_tasks = [task for _value, task in task_values[:top_count]]
            scored: list[tuple[float, tuple[int, ...]]] = []
            for size in range(2, min(max_size, len(top_tasks)) + 1):
                for tasks in combinations(top_tasks, size):
                    mass = sum(value_by_task.get(task, 0.0) for task in tasks)
                    score = mass - (size - 1) * y_value
                    if score > -0.5 * max(1.0, y_value):
                        scored.append((score, tuple(sorted(int(task) for task in tasks))))
            scored.sort(key=lambda item: (-item[0], -len(item[1]), item[1]))
            for _score, tasks in scored[: max(0, self.schedule_subset_cost_candidate_max_combinations)]:
                candidates.add(tasks)

            self._add_schedule_subset_cost_route_union_candidates(solution, int(vehicle), max_size, candidates)
            by_vehicle[int(vehicle)] = sorted(candidates, key=lambda item: (len(item), item))
        return by_vehicle

    def _add_schedule_subset_cost_route_union_candidates(
        self,
        solution: RMPSolution,
        vehicle: int,
        max_size: int,
        candidates: set[tuple[int, ...]],
    ) -> None:
        support = [
            (float(value), route)
            for route, route_vehicle, value in solution.route_values
            if int(route_vehicle) == int(vehicle) and value > self.integer_tol
        ]
        support.sort(key=lambda item: (-item[0] * len(item[1].task_set), -item[0], item[1].cost, item[1].signature))
        top_routes = [route for _value, route in support[: max(0, self.schedule_subset_cost_route_union_top_routes)]]
        max_routes = min(max(2, self.schedule_subset_cost_route_union_max_routes), len(top_routes))
        for size in range(2, max_routes + 1):
            for combo in combinations(top_routes, size):
                tasks = tuple(sorted({int(task) for route in combo for task in route.task_set}))
                if 2 <= len(tasks) <= max_size:
                    candidates.add(tasks)

    def _schedule_subset_cost_bound(self, tasks: tuple[int, ...]) -> ScheduleSubsetCostResult | None:
        tasks = tuple(sorted(int(task) for task in tasks))
        if tasks not in self.schedule_subset_cost_cache:
            self.schedule_subset_cost_cache[tasks] = exact_schedule_subset_cost(
                self.data,
                tasks,
                max_states=self.schedule_subset_cost_oracle_max_states,
            )
        return self.schedule_subset_cost_cache[tasks]

    def _ensure_resource_pair_incompatibilities(self) -> set[tuple[int, int]]:
        if self.resource_pair_incompatible is not None:
            return self.resource_pair_incompatible
        incompatible: set[tuple[int, int]] = set()
        tasks = tuple(self.data.tasks)
        for left_index, left in enumerate(tasks):
            for right in tasks[left_index + 1 :]:
                if not self._pair_route_compatible(int(left), int(right)):
                    incompatible.add((int(left), int(right)))
        self.resource_pair_incompatible = incompatible
        self.logger.log(
            "resource_pair_graph",
            incompatible_edges=len(incompatible),
            possible_edges=len(tasks) * (len(tasks) - 1) // 2,
        )
        return incompatible

    def _pair_route_compatible(self, left: int, right: int) -> bool:
        # 中文注释：两任务只要存在任一顺序能放进同一条 sortie route，就不能在 incompatibility graph 中连边。
        return evaluate_route(self.data, (left, right)) is not None or evaluate_route(self.data, (right, left)) is not None

    def _resource_chromatic_bound(self, tasks: tuple[int, ...]) -> int:
        tasks = tuple(sorted(int(task) for task in tasks))
        cached = self.resource_chromatic_cache.get(tasks)
        if cached is not None:
            return cached
        incompatible = self._ensure_resource_pair_incompatibilities()
        index_of = {task: index for index, task in enumerate(tasks)}
        n = len(tasks)
        adjacency = [0 for _ in range(n)]
        for left, right in incompatible:
            if left not in index_of or right not in index_of:
                continue
            i = index_of[left]
            j = index_of[right]
            adjacency[i] |= 1 << j
            adjacency[j] |= 1 << i
        degrees = [adjacency[index].bit_count() for index in range(n)]
        order = sorted(range(n), key=lambda index: (-degrees[index], tasks[index]))

        lower = self._resource_clique_lower_bound(adjacency)
        lower = max(1, lower)
        for color_count in range(lower, n + 1):
            if self._resource_can_color(order, adjacency, color_count):
                self.resource_chromatic_cache[tasks] = color_count
                return color_count
        self.resource_chromatic_cache[tasks] = n
        return n

    def _resource_clique_lower_bound(self, adjacency: list[int]) -> int:
        # 中文注释：子集规模很小，直接枚举 clique 下界即可；后续 exact coloring 仍负责证明 chromatic number。
        n = len(adjacency)
        best = 1 if n else 0
        for mask in range(1, 1 << n):
            size = mask.bit_count()
            if size <= best:
                continue
            clique = True
            for i in range(n):
                if not (mask & (1 << i)):
                    continue
                others = mask & ~(1 << i)
                if others & ~adjacency[i]:
                    clique = False
                    break
            if clique:
                best = size
        return best

    def _resource_can_color(self, order: list[int], adjacency: list[int], color_count: int) -> bool:
        color_masks = [0 for _ in range(color_count)]

        def search(position: int) -> bool:
            if position == len(order):
                return True
            vertex = order[position]
            tried_empty = False
            for color in range(color_count):
                if color_masks[color] == 0:
                    if tried_empty:
                        continue
                    tried_empty = True
                if adjacency[vertex] & color_masks[color]:
                    continue
                color_masks[color] |= 1 << vertex
                if search(position + 1):
                    return True
                color_masks[color] &= ~(1 << vertex)
            return False

        return search(0)

    def _separate_task_schedule_capacity_cuts(
        self,
        node: BPCNode,
        solution: RMPSolution,
        *,
        legacy_family: str,
    ) -> int:
        if not self.task_schedule_capacity_cuts_enabled and legacy_family == "task_schedule_capacity":
            return 0
        if node.depth > self.task_schedule_capacity_max_depth:
            return 0
        rounds = self.task_schedule_capacity_cut_rounds_by_node.get(node.id, 0)
        if rounds >= max(1, self.schedule_capacity_cut_max_rounds_per_node):
            return 0
        no_add_rounds = self.task_schedule_capacity_no_add_rounds_by_node.get(node.id, 0)
        if (
            self.task_schedule_capacity_stop_after_no_add_rounds >= 0
            and no_add_rounds >= self.task_schedule_capacity_stop_after_no_add_rounds
        ):
            self.stats.task_schedule_capacity_stopped_by_no_add += 1
            self.logger.log(
                "task_schedule_capacity_diagnostics",
                node_id=node.id,
                depth=node.depth,
                round=rounds + 1,
                stopped_by="no_add_rounds",
                added=0,
            )
            return 0
        no_improve_rounds = self.task_schedule_capacity_no_improve_rounds_by_node.get(node.id, 0)
        if (
            self.task_schedule_capacity_stop_after_no_improve_rounds >= 0
            and no_improve_rounds >= self.task_schedule_capacity_stop_after_no_improve_rounds
        ):
            self.stats.task_schedule_capacity_stopped_by_no_improvement += 1
            self.logger.log(
                "task_schedule_capacity_diagnostics",
                node_id=node.id,
                depth=node.depth,
                round=rounds + 1,
                stopped_by="no_improvement_rounds",
                added=0,
            )
            return 0
        global_budget = max(0.0, self.time_limit * self.task_schedule_capacity_global_time_ratio)
        if global_budget > 0.0 and self.task_schedule_capacity_oracle_time_total >= global_budget:
            self.stats.task_schedule_capacity_stopped_by_global_time_budget += 1
            self.logger.log(
                "task_schedule_capacity_diagnostics",
                node_id=node.id,
                depth=node.depth,
                round=rounds + 1,
                stopped_by="global_time_budget",
                added=0,
            )
            return 0

        min_violation = max(self.integer_tol, self.task_schedule_capacity_min_violation)
        started = time.perf_counter()
        task_values_by_vehicle = {
            int(vehicle): self._vehicle_task_values(solution, int(vehicle))
            for vehicle in self.data.vehicles
        }
        support_routes_by_vehicle = {
            int(vehicle): self._schedule_support_routes(
                solution,
                int(vehicle),
                max_routes=max(
                    self.route_set_schedule_packing_cut_max_support_routes,
                    self.schedule_incompatibility_cut_max_support_routes,
                    self.schedule_capacity_route_union_top_routes,
                ),
            )
            for vehicle in self.data.vehicles
        }
        generation = generate_task_schedule_capacity_candidates(
            self.data,
            vehicles=tuple(int(vehicle) for vehicle in self.data.vehicles),
            y_values={int(vehicle): float(value) for vehicle, value in solution.y_values.items()},
            task_values_by_vehicle=task_values_by_vehicle,
            support_routes_by_vehicle=support_routes_by_vehicle,
            witness_memory=self.task_schedule_capacity_witness_memory,
            min_violation=min_violation,
            pair_budget=self.task_schedule_capacity_pair_budget,
            triple_budget=self.task_schedule_capacity_triple_budget,
            small_set_budget=self.task_schedule_capacity_small_set_budget,
            max_subset_size=self.task_schedule_capacity_max_subset_size,
            use_rim_witness=self.task_schedule_capacity_use_rim_witness,
            use_route_pack_witness=self.task_schedule_capacity_use_route_pack_witness,
            use_incompatibility_witness=self.task_schedule_capacity_use_incompatibility_witness,
            use_top_z_mass=self.task_schedule_capacity_use_top_z_mass,
            use_support_route_union=self.task_schedule_capacity_use_support_route_union,
            use_time_window_clusters=self.task_schedule_capacity_use_time_window_clusters,
            successful_task_sets=self.task_schedule_capacity_successful_sets,
        )
        diagnostics: dict[str, Any] = {
            **generation.diagnostics,
            "oracle_requests": 0,
            "oracle_computations": 0,
            "cache_hits": 0,
            "oracle_incomplete": 0,
            "exact_not_tight": 0,
            "exact_tight_not_violated": 0,
            "duplicate": 0,
            "violated_candidates": 0,
            "cuts_added": 0,
            "cuts_copied_to_all_vehicles": 0,
            "oracle_time": 0.0,
            "oracle_states_total": 0,
            "oracle_states_max": 0,
            "best_violation": 0.0,
            "max_oracle_states": self.task_schedule_capacity_oracle_max_states,
            "node_time_budget": self.task_schedule_capacity_node_time_budget,
            "global_time_budget": global_budget,
            "stopped_by": None,
            "branch_signal_candidates": 0,
            "branch_signal_applied": 0,
        }
        self._accumulate_task_schedule_capacity_generation_stats(diagnostics)
        if legacy_family == "root_schedule_capacity":
            self.stats.root_schedule_capacity_candidates_generated += int(diagnostics["candidates_generated"])
            self.stats.root_schedule_capacity_candidates_after_precheck += int(diagnostics["candidates_after_precheck"])
        if not generation.candidates:
            self.task_schedule_capacity_no_add_rounds_by_node[node.id] = no_add_rounds + 1
            if legacy_family == "root_schedule_capacity":
                self.root_schedule_capacity_no_add_rounds_by_node[node.id] = no_add_rounds + 1
            self.logger.log("task_schedule_capacity_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
            if legacy_family == "root_schedule_capacity":
                self.logger.log("root_schedule_capacity_diagnostics", node_id=node.id, depth=node.depth, **self._legacy_root_schedcap_diagnostics(diagnostics))
            return 0

        self.task_schedule_capacity_cut_rounds_by_node[node.id] = rounds + 1
        cuts_added = 0
        added_payload: list[dict[str, Any]] = []
        for candidate in generation.candidates:
            if global_budget > 0.0 and self.task_schedule_capacity_oracle_time_total >= global_budget:
                diagnostics["stopped_by"] = "global_time_budget"
                self.stats.task_schedule_capacity_stopped_by_global_time_budget += 1
                break
            if (
                self.task_schedule_capacity_node_time_budget > 0.0
                and time.perf_counter() - started > self.task_schedule_capacity_node_time_budget
            ):
                diagnostics["stopped_by"] = "node_time_budget"
                self.stats.task_schedule_capacity_stopped_by_node_time_budget += 1
                break
            if cuts_added >= max(1, self.task_schedule_capacity_max_cuts_per_round):
                break
            cut_key = ("schedule_capacity", int(candidate.vehicle), candidate.tasks)
            if cut_key in self.cut_keys:
                diagnostics["duplicate"] = int(diagnostics["duplicate"]) + 1
                continue
            diagnostics["oracle_requests"] = int(diagnostics["oracle_requests"]) + 1
            oracle_entry, cache_hit = self._task_schedule_capacity_bound(candidate.tasks, node_id=node.id, source=candidate.source)
            if cache_hit:
                diagnostics["cache_hits"] = int(diagnostics["cache_hits"]) + 1
            else:
                diagnostics["oracle_computations"] = int(diagnostics["oracle_computations"]) + 1
                diagnostics["oracle_time"] = float(diagnostics["oracle_time"]) + float(oracle_entry.oracle_time)
                self.task_schedule_capacity_oracle_time_total += float(oracle_entry.oracle_time)
                diagnostics["oracle_states_total"] = int(diagnostics["oracle_states_total"]) + int(oracle_entry.states_explored)
                diagnostics["oracle_states_max"] = max(int(diagnostics["oracle_states_max"]), int(oracle_entry.states_explored))
            if oracle_entry.incomplete or not oracle_entry.exact or oracle_entry.upper_bound is None:
                diagnostics["oracle_incomplete"] = int(diagnostics["oracle_incomplete"]) + 1
                continue
            upper_bound = int(oracle_entry.upper_bound)
            if upper_bound >= len(candidate.tasks):
                diagnostics["exact_not_tight"] = int(diagnostics["exact_not_tight"]) + 1
                continue
            y_value = float(solution.y_values.get(int(candidate.vehicle), 0.0))
            activity = self._task_vehicle_mass(solution, candidate.tasks, int(candidate.vehicle))
            violation = activity - float(upper_bound) * y_value
            diagnostics["best_violation"] = max(float(diagnostics["best_violation"]), float(violation))
            self.stats.task_schedule_capacity_best_violation = max(
                float(self.stats.task_schedule_capacity_best_violation),
                float(violation),
            )
            if legacy_family == "root_schedule_capacity":
                self.stats.root_schedule_capacity_best_violation = max(
                    float(self.stats.root_schedule_capacity_best_violation),
                    float(violation),
                )
            if violation <= min_violation:
                diagnostics["exact_tight_not_violated"] = int(diagnostics["exact_tight_not_violated"]) + 1
                continue
            diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
            vehicles_to_add = (
                [int(vehicle) for vehicle in self.data.vehicles]
                if self.task_schedule_capacity_copy_to_all_vehicles
                else [int(candidate.vehicle)]
            )
            added_for_candidate = 0
            for add_vehicle in vehicles_to_add:
                cut = ScheduleCapacityCut(
                    id=self._allocate_cut_id(),
                    vehicle=int(add_vehicle),
                    tasks=candidate.tasks,
                    upper_bound=upper_bound,
                    oracle_states=int(oracle_entry.states_explored),
                    source_vehicle=int(candidate.vehicle),
                    source="task_schedule_capacity" if legacy_family != "root_schedule_capacity" else "root_schedule_capacity",
                )
                if cut.key in self.cut_keys:
                    diagnostics["duplicate"] = int(diagnostics["duplicate"]) + 1
                    continue
                self.cuts.append(cut)
                self.cut_keys.add(cut.key)
                self.cut_inactive_age[cut.key] = 0
                added_for_candidate += 1
                cuts_added += 1
                add_y = float(solution.y_values.get(int(add_vehicle), 0.0))
                add_activity = self._task_vehicle_mass(solution, candidate.tasks, int(add_vehicle))
                added_payload.append(
                    {
                        "id": cut.id,
                        "vehicle": int(add_vehicle),
                        "source_vehicle": int(candidate.vehicle),
                        "tasks": list(candidate.tasks),
                        "upper_bound": upper_bound,
                        "activity": round(add_activity, 9),
                        "y": round(add_y, 9),
                        "activity_minus_rhs": round(add_activity - float(upper_bound) * add_y, 9),
                        "oracle_states": int(oracle_entry.states_explored),
                        "oracle_time": round(float(oracle_entry.oracle_time), 6),
                        "source": candidate.source,
                        "cache_hit": bool(cache_hit),
                    }
                )
            if added_for_candidate:
                if self.task_schedule_capacity_copy_to_all_vehicles:
                    copied = max(0, added_for_candidate - 1)
                    diagnostics["cuts_copied_to_all_vehicles"] = int(diagnostics["cuts_copied_to_all_vehicles"]) + copied
                self.task_schedule_capacity_successful_sets.add(candidate.tasks)
                self.task_schedule_capacity_explained_route_sets.add(candidate.tasks)
                branch_signal_count_before = len(self.task_schedule_capacity_branch_witnesses)
                self._record_task_schedule_capacity_branch_signal(candidate, upper_bound, violation, node.id)
                if len(self.task_schedule_capacity_branch_witnesses) > branch_signal_count_before:
                    diagnostics["branch_signal_candidates"] = int(diagnostics["branch_signal_candidates"]) + 1

        diagnostics["cuts_added"] = cuts_added
        diagnostics["oracle_time"] = round(float(diagnostics["oracle_time"]), 6)
        self._accumulate_task_schedule_capacity_oracle_stats(diagnostics)
        if legacy_family == "root_schedule_capacity":
            self.stats.root_schedule_capacity_oracle_queries += int(diagnostics.get("oracle_computations", 0) or 0)
            self.stats.root_schedule_capacity_oracle_incomplete += int(diagnostics.get("oracle_incomplete", 0) or 0)
            self.stats.root_schedule_capacity_oracle_time += float(diagnostics.get("oracle_time", 0.0) or 0.0)
            self.stats.root_schedule_capacity_cache_hits += int(diagnostics.get("cache_hits", 0) or 0)
        if cuts_added:
            self.task_schedule_capacity_no_add_rounds_by_node[node.id] = 0
            if legacy_family == "root_schedule_capacity":
                self.root_schedule_capacity_no_add_rounds_by_node[node.id] = 0
            self.stats.cuts_added += cuts_added
            self.stats.schedule_capacity_cuts_added += cuts_added
            self.stats.task_schedule_capacity_cuts_added += cuts_added
            if legacy_family == "root_schedule_capacity":
                self.stats.root_schedule_capacity_cuts_added += cuts_added
            self.logger.log(
                "cut_added",
                node_id=node.id,
                family="task_schedule_capacity" if legacy_family != "root_schedule_capacity" else "root_schedule_capacity",
                added=cuts_added,
                copied_to_all_vehicles=int(diagnostics["cuts_copied_to_all_vehicles"]),
                cuts=added_payload,
            )
            self._register_cut_roi(node, "task_schedule_capacity", cuts_added, solution.objective)
        else:
            self.task_schedule_capacity_no_add_rounds_by_node[node.id] = no_add_rounds + 1
            if legacy_family == "root_schedule_capacity":
                self.root_schedule_capacity_no_add_rounds_by_node[node.id] = no_add_rounds + 1
        self.logger.log("task_schedule_capacity_diagnostics", node_id=node.id, depth=node.depth, round=rounds + 1, **diagnostics)
        if legacy_family == "root_schedule_capacity":
            self.logger.log("root_schedule_capacity_diagnostics", node_id=node.id, depth=node.depth, **self._legacy_root_schedcap_diagnostics(diagnostics))
        return cuts_added

    def _legacy_root_schedcap_diagnostics(self, diagnostics: dict[str, Any]) -> dict[str, Any]:
        return {
            "vehicles_checked": int(diagnostics.get("vehicles_checked", 0) or 0),
            "vehicles_active": int(diagnostics.get("vehicles_active", 0) or 0),
            "candidates_generated": int(diagnostics.get("candidates_generated", 0) or 0),
            "candidates_after_precheck": int(diagnostics.get("candidates_after_precheck", 0) or 0),
            "pair_candidates": int(diagnostics.get("pair_candidates", 0) or 0),
            "triple_candidates": int(diagnostics.get("triple_candidates", 0) or 0),
            "oracle_queries": int(diagnostics.get("oracle_computations", 0) or 0),
            "oracle_incomplete": int(diagnostics.get("oracle_incomplete", 0) or 0),
            "cache_hits": int(diagnostics.get("cache_hits", 0) or 0),
            "tight_not_violated": int(diagnostics.get("exact_tight_not_violated", 0) or 0),
            "not_tight": int(diagnostics.get("exact_not_tight", 0) or 0),
            "duplicate": int(diagnostics.get("duplicate", 0) or 0),
            "violated": int(diagnostics.get("violated_candidates", 0) or 0),
            "cuts_added": int(diagnostics.get("cuts_added", 0) or 0),
            "oracle_time": diagnostics.get("oracle_time", 0.0),
            "oracle_states_total": int(diagnostics.get("oracle_states_total", 0) or 0),
            "oracle_states_max": int(diagnostics.get("oracle_states_max", 0) or 0),
            "max_oracle_states": self.task_schedule_capacity_oracle_max_states,
            "best_violation": float(diagnostics.get("best_violation", 0.0) or 0.0),
        }

    def _separate_root_schedule_capacity_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        if not (self.task_schedule_capacity_cuts_enabled or self.root_schedule_capacity_cuts_enabled):
            return 0
        if self.task_schedule_capacity_legacy_alias_mode:
            self.task_schedule_capacity_cuts_enabled = bool(self.root_schedule_capacity_cuts_enabled)
            self.task_schedule_capacity_max_depth = int(self.root_schedule_capacity_max_depth)
            self.task_schedule_capacity_pair_budget = int(self.root_schedule_capacity_pair_budget)
            self.task_schedule_capacity_triple_budget = int(self.root_schedule_capacity_triple_budget)
            self.task_schedule_capacity_oracle_max_states = int(self.root_schedule_capacity_oracle_max_states)
            self.task_schedule_capacity_node_time_budget = float(self.root_schedule_capacity_time_budget)
            self.task_schedule_capacity_min_violation = float(self.root_schedule_capacity_min_violation)
            self.task_schedule_capacity_stop_after_no_add_rounds = int(self.root_schedule_capacity_stop_after_no_add_rounds)
        return self._separate_task_schedule_capacity_cuts(
            node,
            solution,
            legacy_family="root_schedule_capacity",
        )

    def _task_schedule_capacity_bound(
        self,
        tasks: tuple[int, ...],
        *,
        node_id: int,
        source: str,
    ) -> tuple[TaskScheduleCapacityCacheEntry, bool]:
        tasks = tuple(sorted(int(task) for task in tasks))
        cached = self.task_schedule_capacity_cache.get(tasks)
        if cached is not None:
            cached.record_use(node_id=node_id, source=source, cache_hit=True)
            return cached, True

        started = time.perf_counter()
        result = exact_schedule_task_capacity(
            self.data,
            tasks,
            max_states=max(0, self.task_schedule_capacity_oracle_max_states),
        )
        elapsed = time.perf_counter() - started
        if result is None or not result.exact:
            states_explored = 0 if result is None else int(result.states_explored)
            feasible = bool(result is not None and int(result.upper_bound) > 0)
            entry = TaskScheduleCapacityCacheEntry(
                tasks=tasks,
                upper_bound=None,
                states_explored=states_explored,
                exact=False,
                incomplete=True,
                infeasible=False,
                feasible=feasible,
                oracle_time=elapsed,
                last_used_node=int(node_id),
                source_count={source: 1},
            )
            if self.task_schedule_capacity_cache_incomplete:
                self.task_schedule_capacity_cache[tasks] = entry
                self.root_schedule_capacity_cache[tasks] = None
            return entry, False

        upper_bound = int(result.upper_bound)
        entry = TaskScheduleCapacityCacheEntry(
            tasks=tasks,
            upper_bound=upper_bound,
            states_explored=int(result.states_explored),
            exact=True,
            incomplete=False,
            infeasible=upper_bound <= 0,
            feasible=upper_bound > 0,
            oracle_time=elapsed,
            last_used_node=int(node_id),
            source_count={source: 1},
        )
        should_cache = self.task_schedule_capacity_cache_exact_upper_bound
        if upper_bound >= len(tasks) and not self.task_schedule_capacity_cache_not_tight:
            should_cache = False
        if should_cache:
            self.task_schedule_capacity_cache[tasks] = entry
            self.root_schedule_capacity_cache[tasks] = ScheduleCapacityResult(upper_bound, int(result.states_explored), True)
        return entry, False

    def _record_task_schedule_capacity_witness(
        self,
        routes: list[RouteColumn] | tuple[RouteColumn, ...],
        *,
        source: str,
        vehicle: int | None,
        node_id: int | None,
        violation: float = 0.0,
    ) -> None:
        witness = witness_from_routes(
            routes,
            source=source,
            vehicle=vehicle,
            node_id=node_id,
            violation=violation,
        )
        if witness is None:
            return
        existing = self.task_schedule_capacity_witness_memory.get(witness.tasks)
        if existing is None:
            self.task_schedule_capacity_witness_memory[witness.tasks] = witness
        else:
            existing.merge(witness)
        self._record_witness_rank1_tasks(
            witness.tasks,
            source=source,
            node_id=node_id,
            vehicle=vehicle,
            score=float(violation),
        )

    def _record_task_schedule_capacity_branch_signal(
        self,
        candidate: TaskScheduleCapacityCandidate,
        upper_bound: int,
        violation: float,
        node_id: int,
    ) -> None:
        if not self.task_schedule_capacity_branch_signal_enabled:
            return
        payload = {
            "node_id": int(node_id),
            "vehicle": int(candidate.vehicle),
            "tasks": list(candidate.tasks),
            "size": candidate.size,
            "upper_bound": int(upper_bound),
            "violation": round(float(violation), 9),
            "source": candidate.source,
        }
        self.task_schedule_capacity_branch_witnesses.append(payload)
        self.task_schedule_capacity_branch_witnesses = self.task_schedule_capacity_branch_witnesses[-100:]
        self.stats.task_schedule_capacity_branch_signal_candidates += 1

    def _task_schedule_capacity_branch_summary(self) -> dict[str, Any]:
        if not self.task_schedule_capacity_branch_signal_enabled:
            return {"enabled": False, "candidates": 0, "recent": []}
        recent = self.task_schedule_capacity_branch_witnesses[-10:]
        return {
            "enabled": True,
            "apply_enabled": self.task_schedule_capacity_branch_signal_apply_enabled,
            "candidates": len(self.task_schedule_capacity_branch_witnesses),
            "applied": int(self.stats.task_schedule_capacity_branch_signal_applied),
            "recent": recent,
        }

    def _task_schedule_capacity_branch_boost(self, candidate: BranchCandidate) -> float:
        if not self.task_schedule_capacity_branch_signal_apply_enabled:
            return 0.0
        score = 0.0
        for witness in self.task_schedule_capacity_branch_witnesses[-30:]:
            tasks = set(int(task) for task in witness.get("tasks", []))
            if candidate.kind == "ryan_foster" and candidate.left.task_j is not None:
                pair = {int(candidate.left.task_i), int(candidate.left.task_j)}
                if pair.issubset(tasks):
                    score = max(score, 1.0e-6)
            elif candidate.kind == "task_vehicle":
                if int(candidate.left.task_i) in tasks and int(candidate.left.vehicle) == int(witness.get("vehicle")):
                    score = max(score, 5.0e-7)
        if score > 0.0:
            self.stats.task_schedule_capacity_branch_signal_applied += 1
        return score

    def _accumulate_task_schedule_capacity_generation_stats(self, diagnostics: dict[str, Any]) -> None:
        self.stats.task_schedule_capacity_candidates_generated += int(diagnostics.get("candidates_generated", 0) or 0)
        self.stats.task_schedule_capacity_candidates_after_precheck += int(diagnostics.get("candidates_after_precheck", 0) or 0)
        self.stats.task_schedule_capacity_pair_candidates += int(diagnostics.get("pair_candidates", 0) or 0)
        self.stats.task_schedule_capacity_triple_candidates += int(diagnostics.get("triple_candidates", 0) or 0)
        self.stats.task_schedule_capacity_small_set_candidates += int(diagnostics.get("small_set_candidates", 0) or 0)
        for key, value in (diagnostics.get("candidates_by_source") or {}).items():
            self.stats.task_schedule_capacity_candidates_by_source[str(key)] = (
                self.stats.task_schedule_capacity_candidates_by_source.get(str(key), 0) + int(value)
            )
        for key, value in (diagnostics.get("prechecked_by_source") or {}).items():
            self.stats.task_schedule_capacity_prechecked_by_source[str(key)] = (
                self.stats.task_schedule_capacity_prechecked_by_source.get(str(key), 0) + int(value)
            )

    def _accumulate_task_schedule_capacity_oracle_stats(self, diagnostics: dict[str, Any]) -> None:
        self.stats.task_schedule_capacity_oracle_requests += int(diagnostics.get("oracle_requests", 0) or 0)
        self.stats.task_schedule_capacity_oracle_computations += int(diagnostics.get("oracle_computations", 0) or 0)
        self.stats.task_schedule_capacity_cache_hits += int(diagnostics.get("cache_hits", 0) or 0)
        self.stats.task_schedule_capacity_oracle_incomplete += int(diagnostics.get("oracle_incomplete", 0) or 0)
        self.stats.task_schedule_capacity_exact_not_tight += int(diagnostics.get("exact_not_tight", 0) or 0)
        self.stats.task_schedule_capacity_exact_tight_not_violated += int(diagnostics.get("exact_tight_not_violated", 0) or 0)
        self.stats.task_schedule_capacity_violated_candidates += int(diagnostics.get("violated_candidates", 0) or 0)
        self.stats.task_schedule_capacity_oracle_time += float(diagnostics.get("oracle_time", 0.0) or 0.0)
        self.stats.task_schedule_capacity_oracle_states_total += int(diagnostics.get("oracle_states_total", 0) or 0)
        self.stats.task_schedule_capacity_oracle_states_max = max(
            int(self.stats.task_schedule_capacity_oracle_states_max),
            int(diagnostics.get("oracle_states_max", 0) or 0),
        )
        self.stats.task_schedule_capacity_cuts_copied_to_all_vehicles += int(
            diagnostics.get("cuts_copied_to_all_vehicles", 0) or 0
        )

    def _record_weighted_route_schedule_packing_witness(
        self,
        routes: list[RouteColumn] | tuple[RouteColumn, ...],
        *,
        source: str,
        vehicle: int | None,
        node_id: int | None,
        violation: float = 0.0,
    ) -> None:
        signatures, ordered_routes = self._weighted_route_signature_routes(routes)
        if len(signatures) < 2:
            return
        existing = self.weighted_route_schedule_packing_witness_memory.get(signatures)
        if existing is None:
            self.weighted_route_schedule_packing_witness_memory[signatures] = {
                "routes": ordered_routes,
                "source_count": {str(source): 1},
                "vehicles": set() if vehicle is None else {int(vehicle)},
                "last_node": None if node_id is None else int(node_id),
                "max_violation": float(violation),
            }
            return
        existing["routes"] = ordered_routes
        source_count = existing.setdefault("source_count", {})
        source_count[str(source)] = int(source_count.get(str(source), 0)) + 1
        if vehicle is not None:
            existing.setdefault("vehicles", set()).add(int(vehicle))
        if node_id is not None:
            existing["last_node"] = int(node_id)
        existing["max_violation"] = max(float(existing.get("max_violation", 0.0)), float(violation))

    def _weighted_route_signature_routes(
        self,
        routes: list[RouteColumn] | tuple[RouteColumn, ...],
    ) -> tuple[tuple[tuple[int, ...], ...], list[RouteColumn]]:
        route_by_signature: dict[tuple[int, ...], RouteColumn] = {}
        for route in routes:
            route_by_signature.setdefault(route.signature, route)
        signatures = normalize_signatures(tuple(route_by_signature))
        return signatures, [route_by_signature[signature] for signature in signatures]

    def _normalized_weighted_route_weights(
        self,
        signatures: tuple[tuple[int, ...], ...],
        weight_by_signature: dict[tuple[int, ...], float],
    ) -> tuple[float, ...]:
        raw = [max(0.0, float(weight_by_signature.get(signature, 0.0))) for signature in signatures]
        peak = max(raw, default=0.0)
        if peak <= 1.0e-12:
            return tuple(0.0 for _signature in signatures)
        normalized = []
        for weight in raw:
            value = 0.0 if weight <= 1.0e-12 else weight / peak
            normalized.append(round(float(value), 9))
        return tuple(normalized)

    def _weighted_route_schedule_packing_bound_with_cache_status(
        self,
        routes: list[RouteColumn] | tuple[RouteColumn, ...],
        weights: tuple[float, ...],
    ) -> tuple[float | None, int | None, bool]:
        weight_by_original_signature = {
            route.signature: float(weight)
            for route, weight in zip(routes, weights)
        }
        signatures, ordered_routes = self._weighted_route_signature_routes(routes)
        normalized_weights = self._normalized_weighted_route_weights(
            signatures,
            weight_by_original_signature,
        )
        key = (signatures, normalized_weights)
        cached = self.weighted_route_schedule_packing_cache.get(key)
        if cached is not None:
            return (cached[0], cached[1], True)
        if key in self.weighted_route_schedule_packing_cache and cached is None:
            return (None, None, True)
        result = exact_weighted_route_set_schedule_capacity(
            self.data,
            ordered_routes,
            normalized_weights,
            max_states=self.weighted_route_schedule_packing_oracle_max_states,
        )
        if not result.exact:
            self.weighted_route_schedule_packing_cache[key] = None
            return (None, int(result.states_explored), False)
        value = (float(result.upper_bound), int(result.states_explored))
        self.weighted_route_schedule_packing_cache[key] = value
        return (value[0], value[1], False)

    def _weighted_route_conflict_frequency(self) -> dict[tuple[int, ...], int]:
        frequency: dict[tuple[int, ...], int] = {}
        for signatures, payload in self.weighted_route_schedule_packing_witness_memory.items():
            count = sum(int(value) for value in (payload.get("source_count") or {}).values())
            count = max(1, count)
            for signature in signatures:
                frequency[signature] = frequency.get(signature, 0) + count
        return frequency

    def _discrete_weighted_route_scores(
        self,
        signatures: tuple[tuple[int, ...], ...],
        score_by_signature: dict[tuple[int, ...], float],
    ) -> tuple[float, ...]:
        scores = [max(0.0, float(score_by_signature.get(signature, 0.0))) for signature in signatures]
        peak = max(scores, default=0.0)
        if peak <= 1.0e-12:
            return tuple(1.0 for _signature in signatures)
        weights = []
        for score in scores:
            ratio = score / peak if peak > 0.0 else 0.0
            if ratio >= 2.0 / 3.0:
                weights.append(3.0)
            elif ratio >= 1.0 / 3.0:
                weights.append(2.0)
            else:
                weights.append(1.0)
        return tuple(weights)

    def _weighted_route_incompatibility_scores(
        self,
        routes: list[RouteColumn],
        value_by_signature: dict[tuple[int, ...], float],
    ) -> dict[tuple[int, ...], float]:
        scores = {route.signature: 0.0 for route in routes}
        for left_index, left in enumerate(routes):
            for right in routes[left_index + 1 :]:
                left_right = route_transition_ready_time(self.data, left, right, start_time=0.0)
                right_left = route_transition_ready_time(self.data, right, left, start_time=0.0)
                if left_right is not None or right_left is not None:
                    continue
                scores[left.signature] += 1.0 + float(value_by_signature.get(right.signature, 0.0))
                scores[right.signature] += 1.0 + float(value_by_signature.get(left.signature, 0.0))
        return scores

    def _expand_weighted_route_core_with_pool(
        self,
        routes: list[RouteColumn],
        value_by_signature: dict[tuple[int, ...], float],
    ) -> list[RouteColumn]:
        if len(routes) >= max(2, self.weighted_route_schedule_packing_max_routes):
            return list(routes[: max(2, self.weighted_route_schedule_packing_max_routes)])
        core_tasks = {int(task) for route in routes for task in route.task_set}
        if not core_tasks:
            return list(routes)
        existing = {route.signature for route in routes}
        expanded = list(routes)
        candidates = []
        for route in self.pool.routes:
            if route.signature in existing:
                continue
            overlap = len(set(route.task_set) & core_tasks) / float(max(1, min(len(route.task_set), len(core_tasks))))
            if overlap < 0.5:
                continue
            candidates.append((overlap, float(value_by_signature.get(route.signature, 0.0)), -len(route.task_set), route.signature, route))
        for _overlap, _value, _size, _signature, route in sorted(
            candidates,
            key=lambda item: (-item[0], -item[1], item[2], item[3]),
        ):
            if len(expanded) >= max(2, self.weighted_route_schedule_packing_max_routes):
                break
            expanded.append(route)
            existing.add(route.signature)
        return expanded

    def _weighted_route_schedule_packing_candidate_patterns(
        self,
        routes: list[RouteColumn],
        value_by_signature: dict[tuple[int, ...], float],
        conflict_frequency: dict[tuple[int, ...], int],
        *,
        source: str,
    ) -> list[tuple[str, tuple[float, ...]]]:
        signatures = normalize_signatures(tuple(route.signature for route in routes))
        patterns: list[tuple[str, tuple[float, ...]]] = []
        core_weights = tuple(1.0 for _signature in signatures)
        patterns.append(("conflict_core", core_weights))

        conflict_score = self._discrete_weighted_route_scores(
            signatures,
            {signature: float(conflict_frequency.get(signature, 0)) for signature in signatures},
        )
        if any(weight != 1.0 for weight in conflict_score):
            patterns.append(("conflict_score_discrete", conflict_score))

        incompat_score = self._discrete_weighted_route_scores(
            signatures,
            self._weighted_route_incompatibility_scores(routes, value_by_signature),
        )
        if any(weight != 1.0 for weight in incompat_score):
            patterns.append(("incompat_degree_discrete", incompat_score))

        lp_x_conflict = self._discrete_weighted_route_scores(
            signatures,
            {
                signature: float(value_by_signature.get(signature, 0.0)) * float(conflict_frequency.get(signature, 0))
                for signature in signatures
            },
        )
        if any(conflict_frequency.get(signature, 0) > 0 for signature in signatures) and any(
            weight != 1.0 for weight in lp_x_conflict
        ):
            patterns.append(("lp_x_conflict_discrete", lp_x_conflict))

        seen: set[tuple[float, ...]] = set()
        unique: list[tuple[str, tuple[float, ...]]] = []
        for pattern, weights in patterns:
            if weights in seen:
                continue
            seen.add(weights)
            unique.append((pattern, weights))
        return unique

    def _separate_weighted_route_schedule_packing_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        """分离有限 support 上的 weighted route-schedule packing cut。"""

        if not self.weighted_route_schedule_packing_cuts_enabled:
            return 0
        if node.depth > self.weighted_route_schedule_packing_max_depth:
            return 0
        rounds = self.weighted_route_schedule_packing_cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.weighted_route_schedule_packing_max_rounds_per_node:
            return 0

        min_violation = max(self.integer_tol, self.weighted_route_schedule_packing_min_violation)
        global_budget = max(0.0, self.time_limit * self.weighted_route_schedule_packing_global_time_ratio)
        if global_budget > 0.0 and self.weighted_route_schedule_packing_oracle_time_total >= global_budget:
            self.stats.weighted_route_schedule_packing_stopped_by_budget += 1
            self.logger.log(
                "weighted_route_schedule_packing_diagnostics",
                node_id=node.id,
                depth=node.depth,
                round=rounds + 1,
                stopped_by="global_time_budget",
                added=0,
            )
            return 0

        diagnostics: dict[str, Any] = {
            "vehicles_checked": 0,
            "vehicles_with_support": 0,
            "candidate_sets": 0,
            "candidates_after_precheck": 0,
            "candidates_by_source": {},
            "candidates_by_alpha": {},
            "oracle_requests": 0,
            "oracle_computations": 0,
            "cache_hits": 0,
            "oracle_incomplete": 0,
            "exact_not_violated": 0,
            "duplicate": 0,
            "violated_candidates": 0,
            "cuts_added": 0,
            "best_violation": 0.0,
            "oracle_time": 0.0,
            "oracle_states_total": 0,
            "oracle_states_max": 0,
            "stopped_by": None,
        }
        started = time.perf_counter()
        self.weighted_route_schedule_packing_cut_rounds_by_node[node.id] = rounds + 1

        support_by_vehicle = {
            int(vehicle): self._schedule_support_routes(
                solution,
                int(vehicle),
                max_routes=max(self.route_set_schedule_packing_cut_max_support_routes, self.weighted_route_schedule_packing_max_routes),
            )
            for vehicle in self.data.vehicles
        }
        support_values_by_vehicle = {
            vehicle: {route.signature: float(value) for value, route in support}
            for vehicle, support in support_by_vehicle.items()
        }
        route_by_signature = {route.signature: route for route in self.pool.routes}
        for support in support_by_vehicle.values():
            for _value, route in support:
                route_by_signature.setdefault(route.signature, route)
        for signatures, payload in self.weighted_route_schedule_packing_witness_memory.items():
            for route in payload.get("routes") or []:
                if route.signature in signatures:
                    route_by_signature.setdefault(route.signature, route)
        conflict_frequency = self._weighted_route_conflict_frequency()

        raw_candidates: list[tuple[float, float, int, str, str, tuple[tuple[int, ...], ...], list[RouteColumn], tuple[float, ...], float, float]] = []
        seen_precheck: set[tuple] = set()

        def count_by(mapping_name: str, key: str) -> None:
            bucket = diagnostics[mapping_name]
            bucket[key] = int(bucket.get(key, 0)) + 1

        def consider(
            *,
            vehicle: int,
            routes: list[RouteColumn],
            source: str,
            source_strength: float,
        ) -> None:
            signatures, ordered_routes = self._weighted_route_signature_routes(routes)
            if len(signatures) < 2:
                return
            if len(signatures) > max(2, self.weighted_route_schedule_packing_max_routes):
                signatures = signatures[: max(2, self.weighted_route_schedule_packing_max_routes)]
                ordered_routes = [route_by_signature[signature] for signature in signatures if signature in route_by_signature]
            if any(signature not in route_by_signature for signature in signatures):
                return
            value_by_signature = support_values_by_vehicle.get(int(vehicle), {})
            if source != "support_top":
                ordered_routes = self._expand_weighted_route_core_with_pool(ordered_routes, value_by_signature)
                signatures, ordered_routes = self._weighted_route_signature_routes(ordered_routes)
            y_value = float(solution.y_values.get(int(vehicle), 0.0))
            for alpha_pattern, weights in self._weighted_route_schedule_packing_candidate_patterns(
                ordered_routes,
                value_by_signature,
                conflict_frequency,
                source=source,
            ):
                diagnostics["candidate_sets"] = int(diagnostics["candidate_sets"]) + 1
                count_by("candidates_by_source", source)
                count_by("candidates_by_alpha", alpha_pattern)
                normalized_weights = self._normalized_weighted_route_weights(
                    signatures,
                    {signature: float(weight) for signature, weight in zip(signatures, weights)},
                )
                if not any(weight > 0.0 for weight in normalized_weights):
                    continue
                activity = sum(
                    float(weight) * float(value_by_signature.get(signature, 0.0))
                    for signature, weight in zip(signatures, normalized_weights)
                )
                cheap_lower_beta = max(normalized_weights, default=0.0)
                potential = activity - cheap_lower_beta * y_value
                if potential <= min_violation:
                    continue
                key = (int(vehicle), signatures, normalized_weights)
                if key in seen_precheck:
                    diagnostics["duplicate"] = int(diagnostics["duplicate"]) + 1
                    continue
                seen_precheck.add(key)
                diagnostics["candidates_after_precheck"] = int(diagnostics["candidates_after_precheck"]) + 1
                score = potential + source_strength - 0.001 * float(len(signatures))
                raw_candidates.append(
                    (
                        score,
                        potential,
                        int(vehicle),
                        source,
                        alpha_pattern,
                        signatures,
                        ordered_routes,
                        normalized_weights,
                        activity,
                        y_value,
                    )
                )

        for vehicle in self.data.vehicles:
            vehicle = int(vehicle)
            diagnostics["vehicles_checked"] = int(diagnostics["vehicles_checked"]) + 1
            support = support_by_vehicle[vehicle]
            if len(support) >= 2:
                diagnostics["vehicles_with_support"] = int(diagnostics["vehicles_with_support"]) + 1
                for routes in self._route_set_schedule_packing_candidates(support):
                    consider(vehicle=vehicle, routes=list(routes), source="support_top", source_strength=0.0)

        for signatures, payload in self.weighted_route_schedule_packing_witness_memory.items():
            routes = [route_by_signature[signature] for signature in signatures if signature in route_by_signature]
            if len(routes) < 2:
                continue
            source_count = payload.get("source_count") or {}
            source = max(source_count, key=lambda key: int(source_count[key])) if source_count else "witness"
            strength = 10.0 + 0.1 * sum(int(value) for value in source_count.values())
            vehicles = payload.get("vehicles") or set(int(vehicle) for vehicle in self.data.vehicles)
            for vehicle in sorted(int(item) for item in vehicles):
                if vehicle not in support_values_by_vehicle:
                    continue
                consider(vehicle=vehicle, routes=routes, source=str(source), source_strength=strength)

        self.stats.weighted_route_schedule_packing_candidates_generated += int(diagnostics["candidate_sets"])
        self.stats.weighted_route_schedule_packing_candidates_after_precheck += int(diagnostics["candidates_after_precheck"])
        for key, value in diagnostics["candidates_by_source"].items():
            self.stats.weighted_route_schedule_packing_candidates_by_source[str(key)] = (
                self.stats.weighted_route_schedule_packing_candidates_by_source.get(str(key), 0) + int(value)
            )
        for key, value in diagnostics["candidates_by_alpha"].items():
            self.stats.weighted_route_schedule_packing_candidates_by_alpha[str(key)] = (
                self.stats.weighted_route_schedule_packing_candidates_by_alpha.get(str(key), 0) + int(value)
            )

        raw_candidates.sort(key=lambda item: (-item[0], -item[1], item[2], item[3], item[4], item[5]))
        added = 0
        added_payload: list[dict[str, Any]] = []
        for _score, _potential, vehicle, source, alpha_pattern, signatures, routes, weights, activity, y_value in raw_candidates[
            : max(0, self.weighted_route_schedule_packing_max_candidates)
        ]:
            if added >= max(1, self.weighted_route_schedule_packing_max_cuts_per_round):
                break
            if (
                self.weighted_route_schedule_packing_node_time_budget > 0.0
                and time.perf_counter() - started > self.weighted_route_schedule_packing_node_time_budget
            ):
                diagnostics["stopped_by"] = "node_time_budget"
                self.stats.weighted_route_schedule_packing_stopped_by_budget += 1
                break
            if global_budget > 0.0 and self.weighted_route_schedule_packing_oracle_time_total >= global_budget:
                diagnostics["stopped_by"] = "global_time_budget"
                self.stats.weighted_route_schedule_packing_stopped_by_budget += 1
                break

            diagnostics["oracle_requests"] = int(diagnostics["oracle_requests"]) + 1
            oracle_started = time.perf_counter()
            beta, states, cache_hit = self._weighted_route_schedule_packing_bound_with_cache_status(routes, weights)
            oracle_time = time.perf_counter() - oracle_started
            if cache_hit:
                diagnostics["cache_hits"] = int(diagnostics["cache_hits"]) + 1
                self.stats.weighted_route_schedule_packing_cache_hits += 1
            else:
                diagnostics["oracle_computations"] = int(diagnostics["oracle_computations"]) + 1
                diagnostics["oracle_time"] = float(diagnostics["oracle_time"]) + oracle_time
                self.weighted_route_schedule_packing_oracle_time_total += oracle_time
                self.stats.weighted_route_schedule_packing_oracle_time += oracle_time
            self.stats.weighted_route_schedule_packing_oracle_requests += 1
            if beta is None or states is None:
                diagnostics["oracle_incomplete"] = int(diagnostics["oracle_incomplete"]) + 1
                self.stats.weighted_route_schedule_packing_oracle_incomplete += 1
                continue
            diagnostics["oracle_states_total"] = int(diagnostics["oracle_states_total"]) + int(states)
            diagnostics["oracle_states_max"] = max(int(diagnostics["oracle_states_max"]), int(states))
            self.stats.weighted_route_schedule_packing_oracle_states_total += int(states)
            self.stats.weighted_route_schedule_packing_oracle_states_max = max(
                int(self.stats.weighted_route_schedule_packing_oracle_states_max),
                int(states),
            )
            violation = activity - float(beta) * y_value
            diagnostics["best_violation"] = max(float(diagnostics["best_violation"]), float(violation))
            self.stats.weighted_route_schedule_packing_best_violation = max(
                float(self.stats.weighted_route_schedule_packing_best_violation),
                float(violation),
            )
            if violation <= min_violation:
                diagnostics["exact_not_violated"] = int(diagnostics["exact_not_violated"]) + 1
                self.stats.weighted_route_schedule_packing_exact_not_violated += 1
                continue
            cut = WeightedScheduleRouteSetPackingCut(
                id=self._allocate_cut_id(),
                vehicle=int(vehicle),
                signatures=signatures,
                weights=weights,
                upper_bound=float(beta),
                oracle_states=int(states),
                source_vehicle=int(vehicle),
                source=str(source),
                alpha_pattern=str(alpha_pattern),
            )
            if cut.key in self.cut_keys:
                diagnostics["duplicate"] = int(diagnostics["duplicate"]) + 1
                self.stats.weighted_route_schedule_packing_duplicate_skips += 1
                continue
            self.cuts.append(cut)
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            added += 1
            diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
            self.stats.weighted_route_schedule_packing_violated_candidates += 1
            self.weighted_route_schedule_packing_successful_sets.add(signatures)
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": int(vehicle),
                    "route_count": len(signatures),
                    "signatures": [list(signature) for signature in signatures],
                    "weights": [round(float(weight), 9) for weight in weights],
                    "upper_bound": round(float(beta), 9),
                    "activity": round(float(activity), 9),
                    "y": round(float(y_value), 9),
                    "activity_minus_rhs": round(float(violation), 9),
                    "oracle_states": int(states),
                    "oracle_time": round(float(oracle_time), 6),
                    "source": str(source),
                    "alpha_pattern": str(alpha_pattern),
                    "cache_hit": bool(cache_hit),
                }
            )

        diagnostics["cuts_added"] = added
        diagnostics["oracle_time"] = round(float(diagnostics["oracle_time"]), 6)
        self.stats.weighted_route_schedule_packing_oracle_computations += int(diagnostics["oracle_computations"])
        if added:
            self.stats.cuts_added += added
            self.stats.weighted_route_schedule_packing_cuts_added += added
            roi_signatures = normalize_signatures(
                tuple(
                    tuple(signature)
                    for payload in added_payload
                    for signature in payload.get("signatures", ())
                )
            )
            roi_vehicles = [int(payload["vehicle"]) for payload in added_payload]
            roi_patterns = tuple(str(payload.get("alpha_pattern", "")) for payload in added_payload)
            self._register_cut_roi(
                node,
                "weighted_schedule_route_set_packing",
                added,
                solution.objective,
                roi_context=self._route_pack_roi_context(
                    solution=solution,
                    vehicles=roi_vehicles,
                    cut_signatures=roi_signatures,
                    alpha_patterns=roi_patterns,
                ),
            )
            self.logger.log(
                "cut_added",
                node_id=node.id,
                family="weighted_schedule_route_set_packing",
                added=added,
                cuts=added_payload,
            )
        self.logger.log(
            "weighted_route_schedule_packing_diagnostics",
            node_id=node.id,
            depth=node.depth,
            round=rounds + 1,
            **diagnostics,
        )
        return added

    def _separate_route_set_schedule_packing_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        """分离高阶 route-set schedule packing cut。

        中文注释：对候选 route 集 C，用 exact DP 证明同一辆车最多能排 U(C) 条，
        只在当前 LP 违反 sum_{p in C} lambda[p,r] <= U(C)y[r] 时加 cut。
        """

        if not self.route_set_schedule_packing_cuts_enabled:
            return 0
        if node.depth > self.route_set_schedule_packing_cut_max_depth:
            return 0
        rounds = self.route_set_schedule_packing_cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.route_set_schedule_packing_cut_max_rounds_per_node:
            return 0

        min_violation = max(self.integer_tol, self.route_set_schedule_packing_cut_min_violation)
        candidates: list[tuple[float, int, int, tuple[tuple[int, ...], ...], list[RouteColumn], float, int, int, float]] = []
        seen_candidate_keys: set[tuple] = set()
        diagnostics: dict[str, float | int] = {
            "vehicles_checked": 0,
            "vehicles_with_support": 0,
            "support_routes_total": 0,
            "support_routes_max": 0,
            "candidate_sets": 0,
            "candidate_routes_max": 0,
            "skipped_support_too_small": 0,
            "skipped_signature_too_small": 0,
            "oracle_queries": 0,
            "skipped_oracle_incomplete": 0,
            "skipped_not_tight": 0,
            "skipped_not_violated": 0,
            "skipped_duplicate": 0,
            "violated_candidates": 0,
            "cache_hits": 0,
            "oracle_time": 0.0,
            "oracle_states_total": 0,
            "oracle_states_max": 0,
            "max_violation": 0.0,
            "post_cut_objective_improvement": 0.0,
            "added_but_no_bound_improvement": 0,
            "disabled_by_roi_guard": 0,
            "added": 0,
        }

        def log_diagnostics(added: int, disabled_by_roi_guard: str | None = None) -> None:
            diagnostics["added"] = int(added)
            if disabled_by_roi_guard:
                diagnostics["disabled_by_roi_guard"] = disabled_by_roi_guard
            if int(diagnostics["vehicles_checked"]) == 0:
                if disabled_by_roi_guard:
                    self.logger.log(
                        "route_set_schedule_packing_diagnostics",
                        node_id=node.id,
                        depth=node.depth,
                        round=rounds + 1,
                        **diagnostics,
                    )
                return
            self.logger.log(
                "route_set_schedule_packing_diagnostics",
                node_id=node.id,
                depth=node.depth,
                round=rounds + 1,
                **diagnostics,
            )

        if self.route_set_schedule_packing_roi_guard_enabled:
            no_add_rounds = self.route_set_schedule_packing_no_add_rounds_by_node.get(node.id, 0)
            no_improve_rounds = self.route_set_schedule_packing_no_improve_rounds_by_node.get(node.id, 0)
            global_budget = max(0.0, self.time_limit * self.route_set_schedule_packing_global_time_limit_ratio)
            if (
                self.route_set_schedule_packing_stop_after_no_add_rounds >= 0
                and no_add_rounds >= self.route_set_schedule_packing_stop_after_no_add_rounds
            ):
                log_diagnostics(0, "no_add_rounds")
                return 0
            if (
                self.route_set_schedule_packing_stop_after_no_improve_rounds >= 0
                and no_improve_rounds >= self.route_set_schedule_packing_stop_after_no_improve_rounds
            ):
                log_diagnostics(0, "no_bound_improvement")
                return 0
            if global_budget > 0.0 and self.route_set_schedule_packing_oracle_time_total >= global_budget:
                log_diagnostics(0, "global_oracle_time")
                return 0

        self.route_set_schedule_packing_cut_rounds_by_node[node.id] = rounds + 1

        for vehicle in self.data.vehicles:
            diagnostics["vehicles_checked"] = int(diagnostics["vehicles_checked"]) + 1
            support = self._schedule_support_routes(
                solution,
                int(vehicle),
                max_routes=self.route_set_schedule_packing_cut_max_support_routes,
            )
            diagnostics["support_routes_total"] = int(diagnostics["support_routes_total"]) + len(support)
            diagnostics["support_routes_max"] = max(int(diagnostics["support_routes_max"]), len(support))
            if len(support) < 2:
                diagnostics["skipped_support_too_small"] = int(diagnostics["skipped_support_too_small"]) + 1
                continue
            diagnostics["vehicles_with_support"] = int(diagnostics["vehicles_with_support"]) + 1
            y_value = float(solution.y_values.get(int(vehicle), 0.0))
            value_by_signature = {route.signature: float(value) for value, route in support}
            route_set_candidates = self._route_set_schedule_packing_candidates(support)
            diagnostics["candidate_sets"] = int(diagnostics["candidate_sets"]) + len(route_set_candidates)
            for routes in route_set_candidates:
                diagnostics["candidate_routes_max"] = max(int(diagnostics["candidate_routes_max"]), len(routes))
                signatures = normalize_signatures(tuple(route.signature for route in routes))
                if len(signatures) < 2:
                    diagnostics["skipped_signature_too_small"] = int(diagnostics["skipped_signature_too_small"]) + 1
                    continue
                diagnostics["oracle_queries"] = int(diagnostics["oracle_queries"]) + 1
                oracle_started = time.perf_counter()
                upper_bound, states, cache_hit = self._route_set_schedule_packing_bound_with_cache_status(routes)
                oracle_time = time.perf_counter() - oracle_started
                diagnostics["oracle_time"] = float(diagnostics["oracle_time"]) + oracle_time
                self.route_set_schedule_packing_oracle_time_total += oracle_time
                self.stats.route_set_schedule_packing_oracle_time += oracle_time
                self.stats.route_set_schedule_packing_oracle_queries += 1
                if cache_hit:
                    diagnostics["cache_hits"] = int(diagnostics["cache_hits"]) + 1
                    self.stats.route_set_schedule_packing_cache_hits += 1
                if upper_bound is None or states is None:
                    diagnostics["skipped_oracle_incomplete"] = int(diagnostics["skipped_oracle_incomplete"]) + 1
                    continue
                diagnostics["oracle_states_total"] = int(diagnostics["oracle_states_total"]) + int(states)
                diagnostics["oracle_states_max"] = max(int(diagnostics["oracle_states_max"]), int(states))
                if upper_bound >= len(signatures):
                    diagnostics["skipped_not_tight"] = int(diagnostics["skipped_not_tight"]) + 1
                    continue
                activity = sum(value_by_signature.get(signature, 0.0) for signature in signatures)
                violation = activity - float(upper_bound) * y_value
                if violation <= min_violation:
                    diagnostics["skipped_not_violated"] = int(diagnostics["skipped_not_violated"]) + 1
                    continue
                key = ("schedule_route_set_packing", int(vehicle), signatures, float(upper_bound), True)
                if key in self.cut_keys or key in seen_candidate_keys:
                    diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                    continue
                seen_candidate_keys.add(key)
                diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
                diagnostics["max_violation"] = max(float(diagnostics["max_violation"]), float(violation))
                self._record_task_schedule_capacity_witness(
                    list(routes),
                    source="route_pack_witness",
                    vehicle=int(vehicle),
                    node_id=node.id,
                    violation=float(violation),
                )
                self._record_weighted_route_schedule_packing_witness(
                    list(routes),
                    source="route_pack_witness",
                    vehicle=int(vehicle),
                    node_id=node.id,
                    violation=float(violation),
                )
                candidates.append((violation, len(signatures), int(vehicle), signatures, list(routes), activity, upper_bound, states, y_value))

        if not candidates:
            if self.route_set_schedule_packing_roi_guard_enabled:
                self.route_set_schedule_packing_no_add_rounds_by_node[node.id] = (
                    self.route_set_schedule_packing_no_add_rounds_by_node.get(node.id, 0) + 1
                )
            diagnostics["oracle_time"] = round(float(diagnostics["oracle_time"]), 6)
            log_diagnostics(0)
            return 0

        candidates.sort(key=lambda item: (-item[0], -item[1], item[2], item[3]))
        added = 0
        added_payload = []
        for violation, size, vehicle, signatures, routes, activity, upper_bound, states, y_value in candidates[
            : max(1, self.route_set_schedule_packing_cut_max_per_round)
        ]:
            cut = ScheduleNoGoodCut(
                id=self._allocate_cut_id(),
                vehicle=vehicle,
                signatures=signatures,
                kind="schedule_route_set_packing",
                source_vehicle=vehicle,
                rhs_value=float(upper_bound),
                scale_by_vehicle_use=True,
            )
            if cut.key in self.cut_keys:
                continue
            self.cuts.append(cut)
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            added += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": vehicle,
                    "route_count": size,
                    "upper_bound": int(upper_bound),
                    "signatures": [list(signature) for signature in signatures],
                    "y": round(y_value, 9),
                    "activity": round(activity, 9),
                    "rhs": round(cut.rhs, 9),
                    "activity_minus_rhs": round(violation, 9),
                    "oracle_states": states,
                }
            )

        if not added:
            if self.route_set_schedule_packing_roi_guard_enabled:
                self.route_set_schedule_packing_no_add_rounds_by_node[node.id] = (
                    self.route_set_schedule_packing_no_add_rounds_by_node.get(node.id, 0) + 1
                )
            diagnostics["oracle_time"] = round(float(diagnostics["oracle_time"]), 6)
            log_diagnostics(0)
            return 0

        if self.route_set_schedule_packing_roi_guard_enabled:
            self.route_set_schedule_packing_no_add_rounds_by_node[node.id] = 0
        self.stats.cuts_added += added
        self.stats.schedule_route_set_packing_cuts_added += added
        diagnostics["oracle_time"] = round(float(diagnostics["oracle_time"]), 6)
        log_diagnostics(added)
        roi_signatures = normalize_signatures(
            tuple(
                tuple(signature)
                for payload in added_payload
                for signature in payload.get("signatures", ())
            )
        )
        roi_vehicles = [int(payload["vehicle"]) for payload in added_payload]
        self._register_cut_roi(
            node,
            "schedule_route_set_packing",
            added,
            solution.objective,
            roi_context=self._route_pack_roi_context(
                solution=solution,
                vehicles=roi_vehicles,
                cut_signatures=roi_signatures,
                alpha_patterns=("uniform",),
            ),
        )
        self.logger.log(
            "cut_added",
            node_id=node.id,
            family="schedule_route_set_packing",
            added=added,
            cuts=added_payload,
        )
        return added

    def _route_set_schedule_packing_candidates(
        self,
        support: list[tuple[float, RouteColumn]],
    ) -> list[list[RouteColumn]]:
        max_routes = min(max(2, self.route_set_schedule_packing_cut_max_routes), len(support))
        if max_routes < 2:
            return []
        candidates: list[list[RouteColumn]] = []
        seen: set[tuple[tuple[int, ...], ...]] = set()
        sorted_support = sorted(support, key=lambda item: (-item[0], -len(item[1].task_set), item[1].cycle_time, item[1].signature))

        def add_candidate(routes: list[RouteColumn]) -> None:
            signatures = normalize_signatures(tuple(route.signature for route in routes))
            if len(signatures) < 2 or signatures in seen:
                return
            seen.add(signatures)
            candidates.append(list(routes))

        prefix_routes = [route for _value, route in sorted_support[:max_routes]]
        for size in range(2, len(prefix_routes) + 1):
            add_candidate(prefix_routes[:size])

        tight_routes = [
            route
            for _value, route in sorted(
                support,
                key=lambda item: (item[1].cycle_time, item[1].return_time, -item[0], item[1].signature),
            )[:max_routes]
        ]
        for size in range(2, len(tight_routes) + 1):
            add_candidate(tight_routes[:size])

        dense_routes = [
            route
            for _value, route in sorted(
                support,
                key=lambda item: (-item[0] * max(1, len(item[1].task_set)), item[1].cycle_time, item[1].signature),
            )[:max_routes]
        ]
        for size in range(2, len(dense_routes) + 1):
            add_candidate(dense_routes[:size])

        def explained_penalty(routes: list[RouteColumn]) -> int:
            task_union = {int(task) for route in routes for task in route.task_set}
            signatures = set(normalize_signatures(tuple(route.signature for route in routes)))
            task_explained = any(set(tasks).issubset(task_union) for tasks in self.task_schedule_capacity_successful_sets)
            route_explained = any(set(weighted).issubset(signatures) for weighted in self.weighted_route_schedule_packing_successful_sets)
            return int(task_explained or route_explained)

        candidates.sort(key=lambda routes: (explained_penalty(routes), len(routes), normalize_signatures(tuple(route.signature for route in routes))))
        return candidates

    def _route_set_schedule_packing_bound_with_cache_status(
        self,
        routes: list[RouteColumn] | tuple[RouteColumn, ...],
    ) -> tuple[int | None, int | None, bool]:
        signatures = normalize_signatures(tuple(route.signature for route in routes))
        cached = self.route_set_schedule_packing_cache.get(signatures)
        if cached is not None:
            return (cached[0], cached[1], True)
        if signatures in self.route_set_schedule_packing_cache and cached is None:
            return (None, None, True)
        result = exact_route_set_schedule_capacity(
            self.data,
            routes,
            max_states=self.route_set_schedule_packing_oracle_max_states,
        )
        if result is None or not result.exact:
            self.route_set_schedule_packing_cache[signatures] = None
            return (None, None, False)
        value = (int(result.upper_bound), int(result.states_explored))
        self.route_set_schedule_packing_cache[signatures] = value
        return (value[0], value[1], False)

    def _route_set_schedule_packing_bound(self, routes: list[RouteColumn]) -> tuple[int | None, int | None]:
        upper_bound, states, _cache_hit = self._route_set_schedule_packing_bound_with_cache_status(routes)
        return (upper_bound, states)

    def _separate_schedule_incompatibility_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        """分离 LP 违背的单车 schedule incompatibility pair/clique cut。

        中文注释：若两条 route 从时间 0 开始任一先后顺序都不可行，则在任意更晚的
        部分 schedule 中也不可行。pairwise clique 中最多只能选一条 route，因此
        sum lambda[p,r] <= y[r] 是有效 cut。
        """

        if not self.schedule_incompatibility_cuts_enabled:
            return 0
        if node.depth > self.schedule_incompatibility_cut_max_depth:
            return 0
        rounds = self.schedule_incompatibility_cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.schedule_incompatibility_cut_max_rounds_per_node:
            return 0

        min_violation = max(self.integer_tol, self.schedule_incompatibility_cut_min_violation)
        candidates: list[tuple[float, int, int, tuple[tuple[int, ...], ...], str, list[RouteColumn], float, float]] = []
        seen_candidate_keys: set[tuple] = set()

        for vehicle in self.data.vehicles:
            support = self._schedule_support_routes(solution, int(vehicle))
            if len(support) < 2:
                continue
            y_value = float(solution.y_values.get(int(vehicle), 0.0))
            adjacency = self._schedule_incompatibility_adjacency([route for _value, route in support])
            values = [value for value, _route in support]
            routes = [route for _value, route in support]

            for left_index in range(len(routes)):
                for right_index in range(left_index + 1, len(routes)):
                    if right_index not in adjacency[left_index]:
                        continue
                    activity = values[left_index] + values[right_index]
                    violation = activity - y_value
                    if violation <= min_violation:
                        continue
                    pair_routes = [routes[left_index], routes[right_index]]
                    signatures = normalize_signatures(tuple(route.signature for route in pair_routes))
                    key = ("schedule_pair_conflict", int(vehicle), signatures, 1.0, True)
                    if key in self.cut_keys or key in seen_candidate_keys:
                        continue
                    seen_candidate_keys.add(key)
                    self._record_task_schedule_capacity_witness(
                        pair_routes,
                        source="incompatibility_witness",
                        vehicle=int(vehicle),
                        node_id=node.id,
                        violation=float(violation),
                    )
                    self._record_weighted_route_schedule_packing_witness(
                        pair_routes,
                        source="incompatibility_witness",
                        vehicle=int(vehicle),
                        node_id=node.id,
                        violation=float(violation),
                    )
                    candidates.append((violation, 2, int(vehicle), signatures, "schedule_pair_conflict", pair_routes, activity, y_value))

            for clique_indices in self._greedy_schedule_incompatibility_cliques(values, adjacency):
                if len(clique_indices) < max(2, self.schedule_incompatibility_clique_min_size):
                    continue
                clique_routes = [routes[index] for index in clique_indices]
                activity = sum(values[index] for index in clique_indices)
                violation = activity - y_value
                if violation <= min_violation:
                    continue
                signatures = normalize_signatures(tuple(route.signature for route in clique_routes))
                key = ("schedule_clique_conflict", int(vehicle), signatures, 1.0, True)
                if key in self.cut_keys or key in seen_candidate_keys:
                    continue
                seen_candidate_keys.add(key)
                self._record_task_schedule_capacity_witness(
                    clique_routes,
                    source="incompatibility_witness",
                    vehicle=int(vehicle),
                    node_id=node.id,
                    violation=float(violation),
                )
                self._record_weighted_route_schedule_packing_witness(
                    clique_routes,
                    source="incompatibility_witness",
                    vehicle=int(vehicle),
                    node_id=node.id,
                    violation=float(violation),
                )
                candidates.append(
                    (
                        violation,
                        len(clique_indices),
                        int(vehicle),
                        signatures,
                        "schedule_clique_conflict",
                        clique_routes,
                        activity,
                        y_value,
                    )
                )

        if not candidates:
            return 0

        candidates.sort(key=lambda item: (-item[0], -item[1], item[2], item[3]))
        added_pair = 0
        added_clique = 0
        added_payload = []
        for violation, size, vehicle, signatures, kind, routes, activity, y_value in candidates[
            : max(1, self.schedule_incompatibility_cut_max_per_round)
        ]:
            cut = ScheduleNoGoodCut(
                id=self._allocate_cut_id(),
                vehicle=vehicle,
                signatures=signatures,
                kind=kind,
                source_vehicle=vehicle,
                rhs_value=1.0 if kind == "schedule_clique_conflict" else None,
                scale_by_vehicle_use=True,
            )
            if cut.key in self.cut_keys:
                continue
            self.cuts.append(cut)
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            if kind == "schedule_clique_conflict":
                added_clique += 1
            else:
                added_pair += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": vehicle,
                    "kind": kind,
                    "route_count": size,
                    "upper_bound": round(cut.upper_bound, 9),
                    "signatures": [list(signature) for signature in signatures],
                    "y": round(y_value, 9),
                    "activity": round(activity, 9),
                    "rhs": round(cut.rhs, 9),
                    "activity_minus_rhs": round(violation, 9),
                }
            )

        added = added_pair + added_clique
        if not added:
            return 0

        self.schedule_incompatibility_cut_rounds_by_node[node.id] = rounds + 1
        self.stats.cuts_added += added
        self.stats.schedule_pair_conflict_cuts_added += added_pair
        self.stats.schedule_clique_conflict_cuts_added += added_clique
        self.logger.log(
            "cut_added",
            node_id=node.id,
            family="schedule_incompatibility",
            added=added,
            pair_added=added_pair,
            clique_added=added_clique,
            cuts=added_payload,
        )
        return added

    def _schedule_support_routes(
        self,
        solution: RMPSolution,
        vehicle: int,
        *,
        max_routes: int | None = None,
    ) -> list[tuple[float, RouteColumn]]:
        by_signature: dict[tuple[int, ...], tuple[float, RouteColumn]] = {}
        for route, route_vehicle, value in solution.route_values:
            if int(route_vehicle) != int(vehicle) or value <= self.integer_tol:
                continue
            current_value, _current_route = by_signature.get(route.signature, (0.0, route))
            by_signature[route.signature] = (current_value + float(value), route)
        support = list(by_signature.values())
        support.sort(key=lambda item: (-item[0], -len(item[1].task_set), item[1].cost, item[1].signature))
        limit = self.schedule_incompatibility_cut_max_support_routes if max_routes is None else int(max_routes)
        limit = max(0, limit)
        return support[:limit] if limit else support

    def _schedule_incompatibility_adjacency(self, routes: list[RouteColumn]) -> list[set[int]]:
        adjacency = [set() for _route in routes]
        for left_index, left in enumerate(routes):
            for right_index in range(left_index + 1, len(routes)):
                right = routes[right_index]
                if not self._routes_schedule_pair_incompatible(left, right):
                    continue
                adjacency[left_index].add(right_index)
                adjacency[right_index].add(left_index)
        return adjacency

    def _routes_schedule_pair_incompatible(self, left: RouteColumn, right: RouteColumn) -> bool:
        signatures = normalize_signatures((left.signature, right.signature))
        key = (signatures[0], signatures[1])
        cached = self.schedule_pair_incompatibility_cache.get(key)
        if cached is not None:
            return cached
        incompatible = (
            route_transition_ready_time(self.data, left, right) is None
            and route_transition_ready_time(self.data, right, left) is None
        )
        self.schedule_pair_incompatibility_cache[key] = incompatible
        return incompatible

    def _greedy_schedule_incompatibility_cliques(
        self,
        values: list[float],
        adjacency: list[set[int]],
    ) -> list[tuple[int, ...]]:
        seed_count = min(max(0, self.schedule_incompatibility_clique_seed_count), len(values))
        if seed_count == 0:
            return []
        order = sorted(range(len(values)), key=lambda index: (-values[index], -len(adjacency[index]), index))
        cliques: list[tuple[int, ...]] = []
        seen: set[tuple[int, ...]] = set()
        for seed in order[:seed_count]:
            clique = [seed]
            for candidate in order:
                if candidate == seed:
                    continue
                if all(candidate in adjacency[item] for item in clique):
                    clique.append(candidate)
            clique_tuple = tuple(sorted(clique))
            if clique_tuple in seen:
                continue
            seen.add(clique_tuple)
            cliques.append(clique_tuple)
        return cliques

    def _separate_schedule_capacity_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        if self.task_schedule_capacity_cuts_enabled:
            return 0
        if self.schedule_capacity_separation_enabled:
            return self._separate_task_schedule_capacity_cuts(
                node,
                solution,
                legacy_family="schedule_capacity",
            )
        if not self.schedule_capacity_separation_enabled:
            return 0
        if node.depth > self.schedule_capacity_cut_max_depth:
            return 0
        rounds = self.schedule_capacity_cut_rounds_by_node.get(node.id, 0)
        if rounds >= self.schedule_capacity_cut_max_rounds_per_node:
            return 0

        candidate_subsets_by_vehicle = self._schedule_capacity_candidate_subsets_by_vehicle(solution)
        self.logger.log(
            "schedule_capacity_candidates",
            node_id=node.id,
            by_vehicle={str(vehicle): len(subsets) for vehicle, subsets in candidate_subsets_by_vehicle.items()},
        )
        candidates: list[tuple[float, int, tuple[int, ...], int, int, float]] = []
        diagnostics: dict[str, float | int] = {
            "vehicles_checked": 0,
            "vehicles_active": 0,
            "candidate_subsets": 0,
            "candidate_size_max": 0,
            "skipped_vehicle_inactive": 0,
            "skipped_duplicate": 0,
            "oracle_queries": 0,
            "skipped_oracle_incomplete": 0,
            "skipped_not_tight": 0,
            "skipped_not_violated": 0,
            "violated_candidates": 0,
            "oracle_states_total": 0,
            "oracle_states_max": 0,
            "max_violation": 0.0,
            "added": 0,
        }

        def log_diagnostics(added: int) -> None:
            diagnostics["added"] = int(added)
            self.logger.log(
                "schedule_capacity_diagnostics",
                node_id=node.id,
                depth=node.depth,
                round=rounds + 1,
                **diagnostics,
            )

        for vehicle in self.data.vehicles:
            diagnostics["vehicles_checked"] = int(diagnostics["vehicles_checked"]) + 1
            y_value = float(solution.y_values.get(vehicle, 0.0))
            if y_value <= self.integer_tol:
                diagnostics["skipped_vehicle_inactive"] = int(diagnostics["skipped_vehicle_inactive"]) + 1
                continue
            diagnostics["vehicles_active"] = int(diagnostics["vehicles_active"]) + 1
            for tasks in candidate_subsets_by_vehicle.get(int(vehicle), []):
                diagnostics["candidate_subsets"] = int(diagnostics["candidate_subsets"]) + 1
                diagnostics["candidate_size_max"] = max(int(diagnostics["candidate_size_max"]), len(tasks))
                key = ("schedule_capacity", int(vehicle), tasks)
                if key in self.cut_keys:
                    diagnostics["skipped_duplicate"] = int(diagnostics["skipped_duplicate"]) + 1
                    continue
                diagnostics["oracle_queries"] = int(diagnostics["oracle_queries"]) + 1
                oracle = self._schedule_capacity_bound(tasks)
                if oracle is None:
                    diagnostics["skipped_oracle_incomplete"] = int(diagnostics["skipped_oracle_incomplete"]) + 1
                    continue
                diagnostics["oracle_states_total"] = int(diagnostics["oracle_states_total"]) + int(oracle.states_explored)
                diagnostics["oracle_states_max"] = max(
                    int(diagnostics["oracle_states_max"]),
                    int(oracle.states_explored),
                )
                upper_bound = int(oracle.upper_bound)
                if upper_bound >= len(tasks):
                    diagnostics["skipped_not_tight"] = int(diagnostics["skipped_not_tight"]) + 1
                    continue
                activity = self._task_vehicle_mass(solution, tasks, int(vehicle)) - upper_bound * y_value
                if activity > self.schedule_capacity_cut_min_violation:
                    diagnostics["violated_candidates"] = int(diagnostics["violated_candidates"]) + 1
                    diagnostics["max_violation"] = max(float(diagnostics["max_violation"]), float(activity))
                    candidates.append((activity, int(vehicle), tasks, upper_bound, oracle.states_explored, y_value))
                else:
                    diagnostics["skipped_not_violated"] = int(diagnostics["skipped_not_violated"]) + 1

        if not candidates:
            log_diagnostics(0)
            return 0
        candidates.sort(key=lambda item: (-item[0], item[1], len(item[2]), item[2]))
        added = 0
        added_payload = []
        for violation, vehicle, tasks, upper_bound, states, y_value in candidates[: max(1, self.schedule_capacity_cut_max_per_round)]:
            cut = ScheduleCapacityCut(
                id=self._allocate_cut_id(),
                vehicle=vehicle,
                tasks=tasks,
                upper_bound=upper_bound,
                oracle_states=states,
            )
            if cut.key in self.cut_keys:
                continue
            self.cuts.append(cut)
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            added += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": vehicle,
                    "tasks": list(tasks),
                    "upper_bound": upper_bound,
                    "y": round(y_value, 9),
                    "activity_minus_rhs": round(violation, 9),
                    "oracle_states": states,
                }
            )
        if added:
            self.schedule_capacity_cut_rounds_by_node[node.id] = rounds + 1
            self.stats.cuts_added += added
            self.stats.schedule_capacity_cuts_added += added
            self.logger.log(
                "cut_added",
                node_id=node.id,
                family="schedule_capacity",
                added=added,
                cuts=added_payload,
            )
        log_diagnostics(added)
        return added

    def _schedule_capacity_candidate_subsets_by_vehicle(self, solution: RMPSolution) -> dict[int, list[tuple[int, ...]]]:
        max_size = min(self.schedule_capacity_cut_max_subset_size, len(self.data.tasks))
        all_tasks = tuple(sorted(int(task) for task in self.data.tasks))
        by_vehicle: dict[int, list[tuple[int, ...]]] = {}

        for vehicle in self.data.vehicles:
            candidates: set[tuple[int, ...]] = set()
            if len(all_tasks) <= max_size:
                candidates.add(all_tasks)

            task_values = self._vehicle_task_values(solution, int(vehicle))
            value_by_task = {task: value for value, task in task_values}
            ordered = [task for _value, task in task_values[:max_size]]
            for size in range(2, len(ordered) + 1):
                candidates.add(tuple(sorted(ordered[:size])))

            # 中文注释：也加入接近 y 的任务，专门捕捉某辆车 fractional 承担过多任务的结构。
            y_value = float(solution.y_values.get(vehicle, 0.0))
            near_y = [task for value, task in task_values if value >= max(self.integer_tol, 0.8 * y_value)]
            near_y = near_y[:max_size]
            for size in range(2, len(near_y) + 1):
                candidates.add(tuple(sorted(near_y[:size])))

            self._add_schedule_capacity_route_union_candidates(solution, int(vehicle), max_size, candidates)
            self._add_schedule_capacity_scored_task_combinations(value_by_task, y_value, max_size, candidates)
            by_vehicle[int(vehicle)] = sorted(candidates, key=lambda item: (len(item), item))

        return by_vehicle

    def _vehicle_task_values(self, solution: RMPSolution, vehicle: int) -> list[tuple[float, int]]:
        task_values = []
        for task in self.data.tasks:
            value = self._task_vehicle_mass(solution, (int(task),), int(vehicle))
            if value > self.integer_tol:
                task_values.append((value, int(task)))
        task_values.sort(key=lambda item: (-item[0], item[1]))
        return task_values

    def _add_schedule_capacity_route_union_candidates(
        self,
        solution: RMPSolution,
        vehicle: int,
        max_size: int,
        candidates: set[tuple[int, ...]],
    ) -> None:
        support = [
            (float(value), route)
            for route, route_vehicle, value in solution.route_values
            if int(route_vehicle) == int(vehicle) and value > self.integer_tol
        ]
        support.sort(key=lambda item: (-item[0] * len(item[1].task_set), -item[0], item[1].signature))
        top_routes = [route for _value, route in support[: max(0, self.schedule_capacity_route_union_top_routes)]]
        max_routes = min(max(2, self.schedule_capacity_route_union_max_routes), len(top_routes))
        for size in range(2, max_routes + 1):
            for route_combo in combinations(top_routes, size):
                tasks = tuple(sorted({int(task) for route in route_combo for task in route.task_set}))
                if 2 <= len(tasks) <= max_size:
                    candidates.add(tasks)

    def _add_schedule_capacity_scored_task_combinations(
        self,
        value_by_task: dict[int, float],
        y_value: float,
        max_size: int,
        candidates: set[tuple[int, ...]],
    ) -> None:
        if y_value <= self.integer_tol:
            return
        top_count = max(max_size, self.schedule_capacity_candidate_top_tasks)
        ordered = sorted(value_by_task, key=lambda task: (-value_by_task[task], task))[:top_count]
        scored: list[tuple[float, tuple[int, ...]]] = []
        for size in range(2, min(max_size, len(ordered)) + 1):
            for tasks in combinations(ordered, size):
                mass = sum(value_by_task[task] for task in tasks)
                # 中文注释：若 U(S) 至少比 |S| 小 1，这个分数就是潜在 violation；只用于排序，不参与证明。
                score = mass - (size - 1) * y_value
                if score > -0.25 * max(1.0, y_value):
                    scored.append((score, tuple(sorted(int(task) for task in tasks))))
        scored.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
        for _score, tasks in scored[: max(0, self.schedule_capacity_candidate_max_combinations)]:
            candidates.add(tasks)

    def _task_vehicle_mass(self, solution: RMPSolution, tasks: tuple[int, ...], vehicle: int) -> float:
        subset = set(int(task) for task in tasks)
        return sum(
            sum(1 for task in route.task_set if int(task) in subset) * value
            for route, route_vehicle, value in solution.route_values
            if int(route_vehicle) == int(vehicle)
        )

    def _vehicle_route_cost(self, solution: RMPSolution, vehicle: int) -> float:
        return sum(
            float(route.cost) * float(value)
            for route, route_vehicle, value in solution.route_values
            if int(route_vehicle) == int(vehicle)
        )

    def _schedule_capacity_bound(self, tasks: tuple[int, ...]) -> ScheduleCapacityResult | None:
        tasks = tuple(sorted(int(task) for task in tasks))
        if tasks not in self.schedule_capacity_cache:
            result = exact_schedule_task_capacity(
                self.data,
                tasks,
                max_states=self.schedule_capacity_oracle_max_states,
            )
            self.schedule_capacity_cache[tasks] = result if result is not None and result.exact else None
        return self.schedule_capacity_cache[tasks]

    def _choose_branch(self, node: BPCNode, solution: RMPSolution) -> tuple[BranchConstraint, BranchConstraint] | None:
        if self.branching_strategy.lower() != "3pb":
            return choose_branch(
                self.data,
                solution.route_values,
                solution.y_values,
                node.branch_constraints,
                tol=self.integer_tol,
            )
        return self._choose_branch_three_phase(node, solution)

    def _choose_branch_three_phase(self, node: BPCNode, solution: RMPSolution) -> tuple[BranchConstraint, BranchConstraint] | None:
        candidates = generate_branch_candidates(
            self.data,
            solution.route_values,
            solution.y_values,
            node.branch_constraints,
            tol=self.integer_tol,
        )
        if not candidates:
            self.logger.log("branch_candidates", node_id=node.id, count=0, strategy="3pb")
            return None

        initialized: list[BranchCandidate] = []
        uninitialized: list[BranchCandidate] = []
        for candidate in candidates:
            record = self.pseudocosts.get(candidate.key)
            if record is not None and record.initialized:
                initialized.append(candidate)
            else:
                uninitialized.append(candidate)

        initialized.sort(
            key=lambda item: (
                -(
                    self.pseudocosts[item.key].average_score
                    + self._task_schedule_capacity_branch_boost(item)
                    + self._route_pack_branch_boost(item, node)
                ),
                -item.fractionality,
                item.key,
            )
        )
        uninitialized.sort(
            key=lambda item: (
                -(
                    item.fractionality
                    + self._task_schedule_capacity_branch_boost(item)
                    + self._route_pack_branch_boost(item, node)
                ),
                item.key,
            )
        )
        pseudocost_budget, fractional_budget, lp_budget = self._three_pb_candidate_budgets(node)
        screened = [
            *initialized[: max(0, pseudocost_budget)],
            *uninitialized[: max(0, fractional_budget)],
        ]
        if not screened:
            screened = sorted(candidates, key=lambda item: (-item.fractionality, item.key))[:1]

        self.logger.log(
            "branch_candidates",
            node_id=node.id,
            strategy="3pb",
            count=len(candidates),
            initialized=len(initialized),
            uninitialized=len(uninitialized),
            screened=len(screened),
            budget_enabled=self.three_pb_candidate_budget_enabled,
            pseudocost_budget=pseudocost_budget,
            fractional_budget=fractional_budget,
            lp_budget=lp_budget,
            by_kind=self._candidate_kind_counts(candidates),
            screened_by_kind=self._candidate_kind_counts(screened),
            screened_candidates=[candidate.compact() for candidate in screened[:20]],
            schedule_capacity_witness_summary=self._task_schedule_capacity_branch_summary(),
            route_pack_branch_signal_summary=self._route_pack_branch_summary(),
        )

        testing_started = time.perf_counter()
        lp_results: list[BranchTestResult] = []
        for candidate in screened:
            lp_results.append(self._lp_test_candidate(node, solution, candidate))
        self.stats.branch_lp_candidates_tested += len(lp_results)

        lp_results.sort(key=lambda item: (-item.lp_score, item.candidate.key))
        lp_top = lp_results[: max(1, min(lp_budget, len(lp_results)))]

        heuristic_results: list[BranchTestResult] = []
        for item in lp_top:
            heuristic_results.append(self._heuristic_test_candidate(node, solution, item))
        self.stats.branch_heuristic_candidates_tested += len(heuristic_results)
        testing_time = time.perf_counter() - testing_started
        self.stats.branch_testing_time += testing_time

        selected = max(
            heuristic_results,
            key=lambda item: (
                item.heuristic_score
                + self._task_schedule_capacity_branch_boost(item.candidate)
                + self._route_pack_branch_boost(item.candidate, node),
                item.lp_score,
                item.candidate.fractionality,
                item.candidate.key,
            ),
        )
        for result in lp_results:
            self.pseudocosts.setdefault(result.candidate.key, PseudoCostRecord()).update(result.lp_score)

        self.logger.log(
            "branch_selection",
            node_id=node.id,
            strategy="3pb",
            selected=selected.candidate.compact(),
            selected_by=selected.selected_by,
            lp_tested=len(lp_results),
            heuristic_tested=len(heuristic_results),
            testing_time=round(testing_time, 6),
            lp_results_by_kind=self._branch_test_summary_by_kind(lp_results),
            heuristic_results_by_kind=self._branch_test_summary_by_kind(heuristic_results),
            top_results=[self._branch_test_to_log(item) for item in heuristic_results[:20]],
            schedule_capacity_witness_summary=self._task_schedule_capacity_branch_summary(),
            route_pack_branch_signal_summary=self._route_pack_branch_summary(),
        )
        return selected.candidate.left, selected.candidate.right

    def _three_pb_candidate_budgets(self, node: BPCNode) -> tuple[int, int, int]:
        if not self.three_pb_candidate_budget_enabled:
            return (
                self.three_pb_pseudocost_candidates,
                self.three_pb_fractional_candidates,
                self.three_pb_lp_candidates,
            )
        if node.depth <= 0:
            return (
                self.three_pb_root_pseudocost_candidates,
                self.three_pb_root_fractional_candidates,
                self.three_pb_root_lp_candidates,
            )
        if node.depth >= self.three_pb_deep_depth:
            return (
                self.three_pb_deep_pseudocost_candidates,
                self.three_pb_deep_fractional_candidates,
                self.three_pb_deep_lp_candidates,
            )
        return (
            self.three_pb_nonroot_pseudocost_candidates,
            self.three_pb_nonroot_fractional_candidates,
            self.three_pb_nonroot_lp_candidates,
        )

    def _candidate_kind_counts(self, candidates: list[BranchCandidate]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for candidate in candidates:
            counts[candidate.kind] = counts.get(candidate.kind, 0) + 1
        return dict(sorted(counts.items()))

    def _branch_test_summary_by_kind(self, results: list[BranchTestResult]) -> dict[str, dict[str, float | int | None]]:
        summary: dict[str, dict[str, float | int | None]] = {}
        for result in results:
            item = summary.setdefault(
                result.candidate.kind,
                {
                    "count": 0,
                    "best_lp_score": None,
                    "best_heuristic_score": None,
                    "added_routes": 0,
                    "pricing_calls": 0,
                },
            )
            item["count"] = int(item["count"] or 0) + 1
            best_lp = item["best_lp_score"]
            if best_lp is None or result.lp_score > float(best_lp):
                item["best_lp_score"] = round(result.lp_score, 9)
            best_heuristic = item["best_heuristic_score"]
            if best_heuristic is None or result.heuristic_score > float(best_heuristic):
                item["best_heuristic_score"] = round(result.heuristic_score, 9)
            item["added_routes"] = (
                int(item["added_routes"] or 0)
                + result.left_heuristic_added_routes
                + result.right_heuristic_added_routes
            )
            item["pricing_calls"] = (
                int(item["pricing_calls"] or 0)
                + result.left_heuristic_iterations
                + result.right_heuristic_iterations
            )
        return dict(sorted(summary.items()))

    def _branch_test_to_log(self, result: BranchTestResult) -> dict[str, Any]:
        return {
            **result.candidate.compact(),
            "lp_score": round(result.lp_score, 9),
            "heuristic_score": round(result.heuristic_score, 9),
            "left_lp_status": result.left_lp_status,
            "right_lp_status": result.right_lp_status,
            "left_lp_gain": round(result.left_lp_gain, 9),
            "right_lp_gain": round(result.right_lp_gain, 9),
            "left_heuristic_gain": round(result.left_heuristic_gain, 9),
            "right_heuristic_gain": round(result.right_heuristic_gain, 9),
            "left_best_reduced_cost": None if result.left_best_reduced_cost is None else round(result.left_best_reduced_cost, 9),
            "right_best_reduced_cost": None if result.right_best_reduced_cost is None else round(result.right_best_reduced_cost, 9),
            "left_heuristic_iterations": result.left_heuristic_iterations,
            "right_heuristic_iterations": result.right_heuristic_iterations,
            "left_heuristic_added_routes": result.left_heuristic_added_routes,
            "right_heuristic_added_routes": result.right_heuristic_added_routes,
            "left_heuristic_exhausted": result.left_heuristic_exhausted,
            "right_heuristic_exhausted": result.right_heuristic_exhausted,
            "selected_by": result.selected_by,
        }

    def _lp_test_candidate(self, node: BPCNode, solution: RMPSolution, candidate: BranchCandidate) -> BranchTestResult:
        left_status, left_gain = self._restricted_child_lp_gain(node, solution, candidate.left)
        right_status, right_gain = self._restricted_child_lp_gain(node, solution, candidate.right)
        lp_score = self._branch_score(left_gain, right_gain)
        return BranchTestResult(
            candidate=candidate,
            lp_score=lp_score,
            heuristic_score=lp_score,
            left_lp_status=left_status,
            right_lp_status=right_status,
            left_lp_gain=left_gain,
            right_lp_gain=right_gain,
            left_heuristic_gain=left_gain,
            right_heuristic_gain=right_gain,
            left_best_reduced_cost=None,
            right_best_reduced_cost=None,
            left_heuristic_iterations=0,
            right_heuristic_iterations=0,
            left_heuristic_added_routes=0,
            right_heuristic_added_routes=0,
            left_heuristic_exhausted=None,
            right_heuristic_exhausted=None,
            selected_by="lp",
        )

    def _heuristic_test_candidate(self, node: BPCNode, solution: RMPSolution, result: BranchTestResult) -> BranchTestResult:
        left = self._heuristic_child_gain(node, solution, result.candidate.left)
        right = self._heuristic_child_gain(node, solution, result.candidate.right)
        heuristic_score = self._branch_score(left.gain, right.gain)
        return BranchTestResult(
            candidate=result.candidate,
            lp_score=result.lp_score,
            heuristic_score=heuristic_score,
            left_lp_status=result.left_lp_status,
            right_lp_status=result.right_lp_status,
            left_lp_gain=result.left_lp_gain,
            right_lp_gain=result.right_lp_gain,
            left_heuristic_gain=left.gain,
            right_heuristic_gain=right.gain,
            left_best_reduced_cost=left.best_reduced_cost,
            right_best_reduced_cost=right.best_reduced_cost,
            left_heuristic_iterations=left.iterations,
            right_heuristic_iterations=right.iterations,
            left_heuristic_added_routes=left.added_routes,
            right_heuristic_added_routes=right.added_routes,
            left_heuristic_exhausted=left.exhausted,
            right_heuristic_exhausted=right.exhausted,
            selected_by="heuristic",
        )

    def _restricted_child_lp_gain(self, node: BPCNode, solution: RMPSolution, constraint: BranchConstraint) -> tuple[str, float]:
        child_constraints = (*node.branch_constraints, constraint)
        child = solve_rmp_lp(
            self.data,
            self.pool.routes,
            self.cuts,
            child_constraints,
            phase="phase2",
            rmp_params=self.rmp_params,
            verbose=False,
            task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
        )
        self.stats.branch_lp_test_rmp_solves += 1
        parent = float(solution.objective or 0.0)
        if child.optimal and child.objective is not None:
            return child.status, max(0.0, float(child.objective) - parent)
        return child.status, self._testing_infeasible_gain(parent)

    def _heuristic_child_gain(self, node: BPCNode, solution: RMPSolution, constraint: BranchConstraint) -> HeuristicChildResult:
        child_constraints = (*node.branch_constraints, constraint)
        parent = float(solution.objective or 0.0)
        local_pool = RoutePool()
        for route in self.pool.routes:
            local_pool.add(route)

        iterations = 0
        added_total = 0
        best_rc: float | None = None
        all_pricing_exhausted = True
        last_objective: float | None = None
        added_after_last_solve = False

        max_iterations = max(1, self.three_pb_heuristic_cg_iterations)
        routes_per_iter = max(1, self.three_pb_heuristic_routes_per_iter)
        max_labels = max(0, self.three_pb_heuristic_max_labels)

        for _round in range(max_iterations):
            if not self._time_left():
                break
            child = solve_rmp_lp(
                self.data,
                local_pool.routes,
                self.cuts,
                child_constraints,
                phase="phase2",
                rmp_params=self.rmp_params,
                verbose=False,
                task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
            )
            self.stats.branch_heuristic_test_rmp_solves += 1
            added_after_last_solve = False
            if not child.optimal or child.objective is None or child.duals is None:
                return HeuristicChildResult(
                    gain=self._testing_infeasible_gain(parent),
                    best_reduced_cost=best_rc,
                    iterations=iterations,
                    added_routes=added_total,
                    exhausted=None if iterations == 0 else all_pricing_exhausted,
                )
            last_objective = float(child.objective)
            pricing = exact_pricing(
                self.data,
                local_pool.routes,
                child.duals,
                self.cuts,
                child_constraints,
                phase="phase2",
                eps=self.eps,
                max_routes_to_return=routes_per_iter,
                max_labels=max_labels,
                dominance_enabled=self.exact_pricing_dominance_enabled,
                completion_bound_enabled=self.pricing_completion_bound_enabled,
                ng_relaxation_enabled=bool(self.ng_dssr_pricing_enabled) and max_labels > 0,
                ng_memory_size=self.ng_dssr_memory_size,
            )
            self.stats.branch_heuristic_test_pricing_calls += 1
            iterations += 1
            all_pricing_exhausted = all_pricing_exhausted and pricing.exhausted
            current_rc = pricing.best_reduced_cost
            if best_rc is None:
                best_rc = current_rc
            elif current_rc is not None:
                best_rc = min(best_rc, current_rc)
            added = 0
            for route in pricing.routes:
                before = len(local_pool.routes)
                local_pool.add(route)
                if len(local_pool.routes) > before:
                    added += 1
            added_total += added
            if added == 0:
                break
            added_after_last_solve = True

        if added_after_last_solve and self._time_left():
            child = solve_rmp_lp(
                self.data,
                local_pool.routes,
                self.cuts,
                child_constraints,
                phase="phase2",
                rmp_params=self.rmp_params,
                verbose=False,
                task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
            )
            self.stats.branch_heuristic_test_rmp_solves += 1
            if child.optimal and child.objective is not None:
                last_objective = float(child.objective)

        if last_objective is None:
            return HeuristicChildResult(
                gain=self._testing_infeasible_gain(parent),
                best_reduced_cost=best_rc,
                iterations=iterations,
                added_routes=added_total,
                exhausted=None if iterations == 0 else all_pricing_exhausted,
            )
        return HeuristicChildResult(
            gain=max(0.0, last_objective - parent),
            best_reduced_cost=best_rc,
            iterations=iterations,
            added_routes=added_total,
            exhausted=all_pricing_exhausted,
        )

    def _testing_infeasible_gain(self, parent_bound: float) -> float:
        return max(1.0, abs(float(parent_bound)) * 0.05)

    def _branch_score(self, left_gain: float, right_gain: float) -> float:
        eps = max(self.integer_tol, 1.0e-6)
        left = max(float(left_gain), eps)
        right = max(float(right_gain), eps)
        return min(left, right) + 0.1 * max(left, right) + 0.01 * left * right

    def _make_child(self, parent: BPCNode, constraint: BranchConstraint) -> BPCNode:
        node = BPCNode(
            priority=parent.lower_bound,
            id=self.next_node_id,
            depth=parent.depth + 1,
            branch_constraints=(*parent.branch_constraints, constraint),
            parent_id=parent.id,
            description=constraint.name(),
            lower_bound=parent.lower_bound,
        )
        self.next_node_id += 1
        return node

    def _is_integral(self, solution: RMPSolution) -> bool:
        for _route, _vehicle, value in solution.route_values:
            if self.integer_tol < value < 1.0 - self.integer_tol:
                return False
        for value in solution.y_values.values():
            if self.integer_tol < value < 1.0 - self.integer_tol:
                return False
        return True

    def _validate_integral_or_cut(self, node: BPCNode, solution: RMPSolution) -> int:
        grouped: dict[int, list[RouteColumn]] = {vehicle: [] for vehicle in self.data.vehicles}
        selected: list[tuple[RouteColumn, int, float]] = []
        for route, vehicle, value in solution.route_values:
            if value > 1.0 - self.integer_tol:
                grouped[vehicle].append(route)
                selected.append((route, vehicle, 1.0))

        # 中文注释：如果 route 集合本身可重新排到车辆上，先记录一个真实可行 incumbent；
        # 当前节点的原 assignment 若不可行，仍会继续加 cut，不能直接 fathom。
        selected_routes = [route for route, _vehicle, _value in selected]
        repaired = self._repair_route_assignment(selected_routes)
        if repaired is not None:
            self._set_incumbent_from_assignment(repaired, node_id=node.id, source="route_assignment_repair")

        for vehicle, routes in grouped.items():
            witness = self._diagnose_schedule_conflict(routes)
            if witness is None:
                continue
            self._record_task_schedule_capacity_witness(
                list(routes),
                source="rim_witness",
                vehicle=int(vehicle),
                node_id=node.id,
            )
            self._record_weighted_route_schedule_packing_witness(
                list(routes),
                source="rim_witness",
                vehicle=int(vehicle),
                node_id=node.id,
            )

            pair_added = self._add_schedule_pair_conflict_cuts(
                node,
                int(vehicle),
                witness.pair_conflicts,
            )
            if pair_added:
                return pair_added

            route_pack_added, _cache_hit, _states = self._add_schedule_route_set_packing_conflict_cuts(
                node,
                int(vehicle),
                list(routes),
            )
            if route_pack_added:
                return route_pack_added

            variant_added = self._add_schedule_variant_route_pack_conflict_cuts(
                node,
                int(vehicle),
                list(witness.routes),
                solution,
                source="integral_validation",
            )
            if variant_added:
                return variant_added

            structural_added = self._add_schedule_capacity_conflict_cuts(
                node,
                int(vehicle),
                list(witness.routes),
            )
            if structural_added:
                return structural_added

            core_added = self._add_schedule_conflict_cuts(
                node,
                int(vehicle),
                list(witness.routes),
                kind="schedule_nogood_core",
            )
            if core_added:
                return core_added

            full_added = self._add_schedule_conflict_cuts(
                node,
                int(vehicle),
                routes,
                kind="schedule_nogood_full",
            )
            if full_added:
                return full_added

            self.abort_status = "SCHEDULE_CUT_DUPLICATE"
            self.logger.log(
                "fathom",
                node_id=node.id,
                reason="schedule_infeasible_but_no_new_cut",
                bound=None,
            )
            return 0

        objective = float(solution.objective or 0.0)
        if self.incumbent is None or objective < self.incumbent.objective - self.integer_tol:
            self.incumbent = Incumbent(objective=objective, route_values=selected, y_values=solution.y_values, node_id=node.id)
            self._record_incumbent(objective)
            self.logger.log("incumbent", node_id=node.id, objective=round(objective, 6), source="certified_integral")
        return 0

    def _diagnose_schedule_conflict(self, routes: list[RouteColumn] | tuple[RouteColumn, ...]):
        signatures = normalize_signatures(tuple(route.signature for route in routes))
        if signatures not in self.schedule_conflict_witness_cache:
            self.schedule_conflict_witness_cache[signatures] = diagnose_route_set_schedule(self.data, routes)
        return self.schedule_conflict_witness_cache[signatures]

    def _schedule_variant_route_pack_closure(
        self,
        core_routes: list[RouteColumn] | tuple[RouteColumn, ...],
        solution: RMPSolution,
        vehicle: int,
    ) -> list[RouteColumn]:
        """Return concrete same-task-set route variants already present in the pool.

        The returned set is finite support only. It deliberately does not claim
        anything about future priced routes with the same task set.
        """

        core_signatures = {route.signature for route in core_routes}
        if len(core_signatures) < 2:
            return []
        if (
            self.schedule_variant_route_pack_max_core_routes > 0
            and len(core_signatures) > self.schedule_variant_route_pack_max_core_routes
        ):
            return []

        value_by_signature: dict[tuple[int, ...], float] = {}
        for route, route_vehicle, value in solution.route_values:
            if int(route_vehicle) != int(vehicle) or value <= self.integer_tol:
                continue
            value_by_signature[route.signature] = value_by_signature.get(route.signature, 0.0) + float(value)

        by_task_set: dict[frozenset[int], dict[tuple[int, ...], RouteColumn]] = {}
        for route in self.pool.routes:
            by_task_set.setdefault(frozenset(route.task_set), {})[route.signature] = route
        for route in core_routes:
            by_task_set.setdefault(frozenset(route.task_set), {})[route.signature] = route

        closure_by_signature: dict[tuple[int, ...], RouteColumn] = {}
        variants_per_group = max(1, self.schedule_variant_route_pack_max_variants_per_task_set)
        for core in sorted(core_routes, key=lambda route: (tuple(sorted(route.task_set)), route.signature)):
            group = list(by_task_set.get(frozenset(core.task_set), {}).values())
            if not group:
                continue
            group.sort(
                key=lambda route: (
                    0 if route.signature == core.signature else 1,
                    -float(value_by_signature.get(route.signature, 0.0)),
                    float(route.cost),
                    float(route.cycle_time),
                    route.signature,
                )
            )
            for route in group[:variants_per_group]:
                closure_by_signature.setdefault(route.signature, route)

        if len(closure_by_signature) <= len(core_signatures):
            return []
        max_routes = max(2, self.schedule_variant_route_pack_max_routes)
        ordered = sorted(
            closure_by_signature.values(),
            key=lambda route: (
                0 if route.signature in core_signatures else 1,
                -float(value_by_signature.get(route.signature, 0.0)),
                tuple(sorted(route.task_set)),
                float(route.cost),
                route.signature,
            ),
        )
        return ordered[:max_routes]

    def _add_schedule_variant_route_pack_conflict_cuts(
        self,
        node: BPCNode,
        source_vehicle: int,
        routes: list[RouteColumn],
        solution: RMPSolution,
        *,
        source: str,
    ) -> int:
        if not self.schedule_variant_route_pack_cuts_enabled:
            return 0
        if node.depth > self.schedule_variant_route_pack_max_depth:
            return 0

        self.stats.schedule_variant_route_pack_candidates += 1
        closure_routes = self._schedule_variant_route_pack_closure(routes, solution, source_vehicle)
        core_signatures = normalize_signatures(tuple(route.signature for route in routes))
        closure_signatures = normalize_signatures(tuple(route.signature for route in closure_routes))
        if len(closure_signatures) < 2:
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                source_vehicle=source_vehicle,
                core_route_count=len(core_signatures),
                expanded=False,
                added=0,
            )
            return 0
        self.stats.schedule_variant_route_pack_expanded_candidates += 1

        self.stats.schedule_variant_route_pack_oracle_queries += 1
        oracle_started = time.perf_counter()
        upper_bound, states, cache_hit = self._route_set_schedule_packing_bound_with_cache_status(closure_routes)
        oracle_time = time.perf_counter() - oracle_started
        self.stats.schedule_variant_route_pack_oracle_time += oracle_time
        if cache_hit:
            self.stats.schedule_variant_route_pack_cache_hits += 1
        if upper_bound is None or states is None:
            self.stats.schedule_variant_route_pack_oracle_incomplete += 1
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                source_vehicle=source_vehicle,
                core_route_count=len(core_signatures),
                closure_route_count=len(closure_signatures),
                cache_hit=cache_hit,
                oracle_complete=False,
                oracle_states=states,
                upper_bound=upper_bound,
                added=0,
            )
            return 0

        self.stats.schedule_variant_route_pack_oracle_states_total += int(states)
        self.stats.schedule_variant_route_pack_oracle_states_max = max(
            self.stats.schedule_variant_route_pack_oracle_states_max,
            int(states),
        )
        if int(upper_bound) >= len(closure_signatures):
            self.stats.schedule_variant_route_pack_exact_not_tight += 1
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                source_vehicle=source_vehicle,
                core_route_count=len(core_signatures),
                closure_route_count=len(closure_signatures),
                cache_hit=cache_hit,
                oracle_complete=True,
                oracle_states=states,
                upper_bound=int(upper_bound),
                skipped_not_tight=True,
                added=0,
            )
            return 0

        min_violation = max(self.integer_tol, self.schedule_variant_route_pack_min_violation)
        values_by_vehicle: dict[int, dict[tuple[int, ...], float]] = {}
        for route, route_vehicle, value in solution.route_values:
            if value <= self.integer_tol:
                continue
            vehicle_values = values_by_vehicle.setdefault(int(route_vehicle), {})
            vehicle_values[route.signature] = vehicle_values.get(route.signature, 0.0) + float(value)

        violated: list[tuple[float, int, float, float]] = []
        for vehicle in self.data.vehicles:
            vehicle = int(vehicle)
            y_value = float(solution.y_values.get(vehicle, 0.0))
            value_by_signature = values_by_vehicle.get(vehicle, {})
            activity = sum(value_by_signature.get(signature, 0.0) for signature in closure_signatures)
            violation = activity - float(upper_bound) * y_value
            if violation > min_violation:
                violated.append((float(violation), vehicle, float(activity), y_value))

        if not violated:
            self.stats.schedule_variant_route_pack_exact_not_violated += 1
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                source_vehicle=source_vehicle,
                core_route_count=len(core_signatures),
                closure_route_count=len(closure_signatures),
                cache_hit=cache_hit,
                oracle_complete=True,
                oracle_states=states,
                upper_bound=int(upper_bound),
                exact_not_violated=True,
                added=0,
            )
            return 0

        violated.sort(key=lambda item: (-item[0], item[1]))
        self.stats.schedule_variant_route_pack_violated_candidates += len(violated)
        self.stats.schedule_variant_route_pack_best_violation = max(
            self.stats.schedule_variant_route_pack_best_violation,
            violated[0][0],
        )
        target_vehicles = tuple(vehicle for _violation, vehicle, _activity, _y_value in violated)
        cuts = make_no_good_cuts_for_all_vehicles(
            target_vehicles,
            closure_routes,
            self._allocate_cut_ids(len(target_vehicles)),
            source_vehicle=source_vehicle,
            kind="schedule_route_set_packing",
            rhs_value=float(upper_bound),
            scale_by_vehicle_use=True,
        )
        added = 0
        duplicate = 0
        added_payload = []
        violation_by_vehicle = {vehicle: (violation, activity, y_value) for violation, vehicle, activity, y_value in violated}
        for cut in cuts:
            if cut.key in self.cut_keys:
                duplicate += 1
                continue
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            self.cuts.append(cut)
            added += 1
            violation, activity, y_value = violation_by_vehicle[int(cut.vehicle)]
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": cut.vehicle,
                    "upper_bound": int(upper_bound),
                    "activity": round(activity, 9),
                    "y": round(y_value, 9),
                    "activity_minus_rhs": round(violation, 9),
                    "route_count": len(closure_signatures),
                    "core_signatures": [list(signature) for signature in core_signatures],
                    "signatures": [list(signature) for signature in closure_signatures],
                    "source_vehicle": source_vehicle,
                    "source": source,
                    "cache_hit": cache_hit,
                    "oracle_states": states,
                }
            )

        self.stats.schedule_variant_route_pack_duplicate_skips += duplicate
        if not added:
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                source_vehicle=source_vehicle,
                core_route_count=len(core_signatures),
                closure_route_count=len(closure_signatures),
                cache_hit=cache_hit,
                oracle_complete=True,
                oracle_states=states,
                upper_bound=int(upper_bound),
                duplicate=True,
                added=0,
            )
            return 0

        self.stats.cuts_added += added
        self.stats.schedule_route_set_packing_cuts_added += added
        self.stats.schedule_variant_route_pack_cuts_added += added
        self.logger.log(
            "schedule_variant_route_pack_diagnostics",
            node_id=node.id,
            source=source,
            source_vehicle=source_vehicle,
            core_route_count=len(core_signatures),
            closure_route_count=len(closure_signatures),
            cache_hit=cache_hit,
            oracle_complete=True,
            oracle_states=states,
            oracle_time=round(oracle_time, 6),
            upper_bound=int(upper_bound),
            violated_candidates=len(violated),
            duplicate=duplicate,
            added=added,
            best_violation=round(violated[0][0], 9),
        )
        self.logger.log(
            "cut_added",
            node_id=node.id,
            family="schedule_route_set_packing",
            source="variant_closure",
            source_vehicle=source_vehicle,
            added=added,
            route_count=len(closure_signatures),
            upper_bound=int(upper_bound),
            oracle_states=states,
            cache_hit=cache_hit,
            core_signatures=[list(signature) for signature in core_signatures],
            signatures=[list(signature) for signature in closure_signatures],
            cuts=added_payload,
        )
        return added

    def _add_schedule_variant_route_pack_roi_cuts(
        self,
        node: BPCNode,
        solution: RMPSolution,
        diagnostics: dict[str, Any],
        *,
        source: str,
    ) -> int:
        if not self.schedule_variant_route_pack_cuts_enabled:
            return 0
        if node.depth > self.schedule_variant_route_pack_max_depth:
            return 0
        if not bool(diagnostics.get("low_improvement", False)):
            return 0
        if str(diagnostics.get("classification") or "") not in {"same_pool_degeneracy", "mixed"}:
            return 0

        replacement_signatures = normalize_signatures(
            tuple(tuple(int(task) for task in signature) for signature in diagnostics.get("same_pool_replacement_signatures", ()))
        )
        if not replacement_signatures:
            return 0

        route_by_signature = {route.signature: route for route in self.pool.routes}
        replacement_routes = [route_by_signature[signature] for signature in replacement_signatures if signature in route_by_signature]
        if not replacement_routes:
            return 0

        replacement_task_union = {int(task) for route in replacement_routes for task in route.task_set}
        core_signatures = normalize_signatures(
            tuple(tuple(int(task) for task in signature) for signature in diagnostics.get("cut_core_signatures", ()))
        )
        core_routes = [route_by_signature[signature] for signature in core_signatures if signature in route_by_signature]
        core_routes.sort(
            key=lambda route: (
                -len(set(route.task_set) & replacement_task_union),
                -self._route_pack_roi_overlap(route.signature, replacement_task_union),
                len(route.task_set),
                route.cost,
                route.signature,
            )
        )

        max_routes = max(2, self.schedule_variant_route_pack_max_routes)
        candidate_by_signature: dict[tuple[int, ...], RouteColumn] = {
            route.signature: route for route in replacement_routes[:max_routes]
        }
        for route in core_routes:
            if len(candidate_by_signature) >= max_routes:
                break
            if not (set(route.task_set) & replacement_task_union):
                continue
            candidate_by_signature.setdefault(route.signature, route)

        routes = list(candidate_by_signature.values())
        signatures = normalize_signatures(tuple(route.signature for route in routes))
        self.stats.schedule_variant_route_pack_candidates += 1
        if len(signatures) <= len(replacement_signatures):
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                core_route_count=len(core_signatures),
                closure_route_count=len(signatures),
                expanded=False,
                added=0,
            )
            return 0
        self.stats.schedule_variant_route_pack_expanded_candidates += 1

        self.stats.schedule_variant_route_pack_oracle_queries += 1
        oracle_started = time.perf_counter()
        upper_bound, states, cache_hit = self._route_set_schedule_packing_bound_with_cache_status(routes)
        oracle_time = time.perf_counter() - oracle_started
        self.stats.schedule_variant_route_pack_oracle_time += oracle_time
        if cache_hit:
            self.stats.schedule_variant_route_pack_cache_hits += 1
        if upper_bound is None or states is None:
            self.stats.schedule_variant_route_pack_oracle_incomplete += 1
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                core_route_count=len(core_signatures),
                closure_route_count=len(signatures),
                cache_hit=cache_hit,
                oracle_complete=False,
                oracle_states=states,
                upper_bound=upper_bound,
                added=0,
            )
            return 0

        self.stats.schedule_variant_route_pack_oracle_states_total += int(states)
        self.stats.schedule_variant_route_pack_oracle_states_max = max(
            self.stats.schedule_variant_route_pack_oracle_states_max,
            int(states),
        )
        if int(upper_bound) >= len(signatures):
            self.stats.schedule_variant_route_pack_exact_not_tight += 1
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                core_route_count=len(core_signatures),
                closure_route_count=len(signatures),
                cache_hit=cache_hit,
                oracle_complete=True,
                oracle_states=states,
                upper_bound=int(upper_bound),
                skipped_not_tight=True,
                added=0,
            )
            return 0

        values_by_vehicle: dict[int, dict[tuple[int, ...], float]] = {}
        for route, route_vehicle, value in solution.route_values:
            if value <= self.integer_tol:
                continue
            bucket = values_by_vehicle.setdefault(int(route_vehicle), {})
            bucket[route.signature] = bucket.get(route.signature, 0.0) + float(value)

        vehicles = tuple(sorted({int(vehicle) for vehicle in diagnostics.get("vehicles", ())})) or self.data.vehicles
        min_violation = max(self.integer_tol, self.schedule_variant_route_pack_min_violation)
        violated: list[tuple[float, int, float, float]] = []
        for vehicle in vehicles:
            y_value = float(solution.y_values.get(int(vehicle), 0.0))
            value_by_signature = values_by_vehicle.get(int(vehicle), {})
            activity = sum(value_by_signature.get(signature, 0.0) for signature in signatures)
            violation = activity - float(upper_bound) * y_value
            if violation > min_violation:
                violated.append((float(violation), int(vehicle), float(activity), y_value))
        if not violated:
            self.stats.schedule_variant_route_pack_exact_not_violated += 1
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                core_route_count=len(core_signatures),
                closure_route_count=len(signatures),
                cache_hit=cache_hit,
                oracle_complete=True,
                oracle_states=states,
                upper_bound=int(upper_bound),
                exact_not_violated=True,
                added=0,
            )
            return 0

        violated.sort(key=lambda item: (-item[0], item[1]))
        self.stats.schedule_variant_route_pack_violated_candidates += len(violated)
        self.stats.schedule_variant_route_pack_best_violation = max(
            self.stats.schedule_variant_route_pack_best_violation,
            violated[0][0],
        )
        target_vehicles = tuple(vehicle for _violation, vehicle, _activity, _y_value in violated)
        cuts = make_no_good_cuts_for_all_vehicles(
            target_vehicles,
            routes,
            self._allocate_cut_ids(len(target_vehicles)),
            source_vehicle=target_vehicles[0],
            kind="schedule_route_set_packing",
            rhs_value=float(upper_bound),
            scale_by_vehicle_use=True,
        )
        violation_by_vehicle = {vehicle: (violation, activity, y_value) for violation, vehicle, activity, y_value in violated}
        added = 0
        duplicate = 0
        added_payload = []
        for cut in cuts:
            if cut.key in self.cut_keys:
                duplicate += 1
                continue
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            self.cuts.append(cut)
            added += 1
            violation, activity, y_value = violation_by_vehicle[int(cut.vehicle)]
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": cut.vehicle,
                    "upper_bound": int(upper_bound),
                    "activity": round(activity, 9),
                    "y": round(y_value, 9),
                    "activity_minus_rhs": round(violation, 9),
                    "route_count": len(signatures),
                    "replacement_signatures": [list(signature) for signature in replacement_signatures],
                    "signatures": [list(signature) for signature in signatures],
                    "source": source,
                    "cache_hit": cache_hit,
                    "oracle_states": states,
                }
            )

        self.stats.schedule_variant_route_pack_duplicate_skips += duplicate
        if not added:
            self.logger.log(
                "schedule_variant_route_pack_diagnostics",
                node_id=node.id,
                source=source,
                core_route_count=len(core_signatures),
                closure_route_count=len(signatures),
                cache_hit=cache_hit,
                oracle_complete=True,
                oracle_states=states,
                upper_bound=int(upper_bound),
                duplicate=True,
                added=0,
            )
            return 0

        self.stats.cuts_added += added
        self.stats.schedule_route_set_packing_cuts_added += added
        self.stats.schedule_variant_route_pack_cuts_added += added
        self.logger.log(
            "schedule_variant_route_pack_diagnostics",
            node_id=node.id,
            source=source,
            core_route_count=len(core_signatures),
            closure_route_count=len(signatures),
            cache_hit=cache_hit,
            oracle_complete=True,
            oracle_states=states,
            oracle_time=round(oracle_time, 6),
            upper_bound=int(upper_bound),
            violated_candidates=len(violated),
            duplicate=duplicate,
            added=added,
            best_violation=round(violated[0][0], 9),
        )
        self.logger.log(
            "cut_added",
            node_id=node.id,
            family="schedule_route_set_packing",
            source="variant_roi",
            added=added,
            route_count=len(signatures),
            upper_bound=int(upper_bound),
            oracle_states=states,
            cache_hit=cache_hit,
            replacement_signatures=[list(signature) for signature in replacement_signatures],
            signatures=[list(signature) for signature in signatures],
            cuts=added_payload,
        )
        return added

    def _add_schedule_route_set_packing_conflict_cuts(
        self,
        node: BPCNode,
        source_vehicle: int,
        routes: list[RouteColumn],
    ) -> tuple[int, bool, int | None]:
        if not self.route_set_schedule_packing_cuts_enabled:
            return (0, False, None)
        signatures = normalize_signatures(tuple(route.signature for route in routes))
        if len(signatures) < 2:
            return (0, False, None)
        self._record_task_schedule_capacity_witness(
            routes,
            source="route_pack_witness",
            vehicle=source_vehicle,
            node_id=node.id,
        )
        self._record_weighted_route_schedule_packing_witness(
            routes,
            source="route_pack_witness",
            vehicle=source_vehicle,
            node_id=node.id,
        )

        upper_bound, states, cache_hit = self._route_set_schedule_packing_bound_with_cache_status(routes)
        self.schedule_conflict_route_pack_cache[signatures] = (upper_bound, states, cache_hit)
        if upper_bound is None or states is None:
            self.logger.log(
                "schedule_route_set_packing_conflict_diagnostics",
                node_id=node.id,
                source_vehicle=source_vehicle,
                route_count=len(signatures),
                cache_hit=cache_hit,
                oracle_complete=False,
                oracle_states=states,
                upper_bound=upper_bound,
                added=0,
            )
            return (0, cache_hit, states)
        if int(upper_bound) >= len(signatures):
            self.logger.log(
                "schedule_route_set_packing_conflict_diagnostics",
                node_id=node.id,
                source_vehicle=source_vehicle,
                route_count=len(signatures),
                cache_hit=cache_hit,
                oracle_complete=True,
                oracle_states=states,
                upper_bound=int(upper_bound),
                skipped_not_tight=True,
                added=0,
            )
            return (0, cache_hit, states)
        if int(upper_bound) >= len(signatures) - 1:
            self.logger.log(
                "schedule_route_set_packing_conflict_diagnostics",
                node_id=node.id,
                source_vehicle=source_vehicle,
                route_count=len(signatures),
                cache_hit=cache_hit,
                oracle_complete=True,
                oracle_states=states,
                upper_bound=int(upper_bound),
                skipped_nogood_equivalent=True,
                added=0,
            )
            return (0, cache_hit, states)

        cuts = make_no_good_cuts_for_all_vehicles(
            self.data.vehicles,
            routes,
            self._allocate_cut_ids(len(self.data.vehicles)),
            source_vehicle=source_vehicle,
            kind="schedule_route_set_packing",
            rhs_value=float(upper_bound),
            scale_by_vehicle_use=True,
        )
        added = 0
        added_payload = []
        for cut in cuts:
            if cut.key in self.cut_keys:
                continue
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            self.cuts.append(cut)
            added += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": cut.vehicle,
                    "route_count": len(signatures),
                    "upper_bound": int(upper_bound),
                    "signatures": [list(signature) for signature in signatures],
                    "source_vehicle": source_vehicle,
                    "source": "schedule_conflict",
                    "cache_hit": cache_hit,
                    "oracle_states": states,
                }
            )

        self.logger.log(
            "schedule_route_set_packing_conflict_diagnostics",
            node_id=node.id,
            source_vehicle=source_vehicle,
            route_count=len(signatures),
            cache_hit=cache_hit,
            oracle_complete=True,
            oracle_states=states,
            upper_bound=int(upper_bound),
            duplicate=added == 0,
            added=added,
        )
        if not added:
            return (0, cache_hit, states)

        self.stats.cuts_added += added
        self.stats.schedule_route_set_packing_cuts_added += added
        self.logger.log(
            "cut_added",
            node_id=node.id,
            family="schedule_route_set_packing",
            source="schedule_conflict",
            source_vehicle=source_vehicle,
            added=added,
            route_count=len(signatures),
            upper_bound=int(upper_bound),
            oracle_states=states,
            cache_hit=cache_hit,
            signatures=[list(signature) for signature in signatures],
            cuts=added_payload,
        )
        return (added, cache_hit, states)

    def _add_schedule_capacity_conflict_cuts(
        self,
        node: BPCNode,
        source_vehicle: int,
        routes: list[RouteColumn],
    ) -> int:
        if not self.schedule_capacity_cuts_enabled:
            return 0
        structural = find_schedule_capacity_conflict(
            self.data,
            routes,
            max_subset_size=self.schedule_capacity_cut_max_subset_size,
            max_states=self.schedule_capacity_oracle_max_states,
        )
        if structural is None:
            return 0
        new_cuts = make_schedule_capacity_cuts_for_all_vehicles(
            self.data.vehicles,
            structural.tasks,
            structural.upper_bound,
            structural.states_explored,
            self._allocate_cut_ids(len(self.data.vehicles)),
            source_vehicle=source_vehicle,
            source="schedule_conflict",
        )
        added = 0
        added_payload = []
        for cut in new_cuts:
            if cut.key in self.cut_keys:
                continue
            self.cut_keys.add(cut.key)
            self.cut_inactive_age[cut.key] = 0
            self.cuts.append(cut)
            added += 1
            added_payload.append(
                {
                    "id": cut.id,
                    "vehicle": cut.vehicle,
                    "tasks": list(cut.tasks),
                    "upper_bound": cut.upper_bound,
                    "source_vehicle": source_vehicle,
                    "activity_minus_rhs": len(cut.tasks) - cut.upper_bound,
                    "oracle_states": cut.oracle_states,
                    "source": cut.source,
                }
            )
        if added:
            self.stats.cuts_added += added
            self.stats.schedule_capacity_cuts_added += added
            self.logger.log(
                "cut_added",
                node_id=node.id,
                family="schedule_capacity_conflict",
                source_vehicle=source_vehicle,
                added=added,
                route_count=len(routes),
                cuts=added_payload,
            )
        return added

    def _add_schedule_pair_conflict_cuts(
        self,
        node: BPCNode,
        source_vehicle: int,
        pair_conflicts: tuple[RoutePairScheduleConflict, ...],
    ) -> int:
        for pair in pair_conflicts:
            routes = [pair.left, pair.right]
            new_cuts = make_no_good_cuts_for_all_vehicles(
                self.data.vehicles,
                routes,
                self._allocate_cut_ids(len(self.data.vehicles)),
                source_vehicle=source_vehicle,
                kind="schedule_pair_conflict",
            )
            added = 0
            added_payload = []
            for cut in new_cuts:
                if cut.key in self.cut_keys:
                    continue
                self.cut_keys.add(cut.key)
                self.cuts.append(cut)
                added += 1
                added_payload.append(
                    {
                        "id": cut.id,
                        "vehicle": cut.vehicle,
                        "signatures": [list(signature) for signature in cut.signatures],
                        "source_vehicle": source_vehicle,
                        "left_ready_time": pair.left_ready_time,
                        "right_ready_time": pair.right_ready_time,
                    }
                )
            if not added:
                continue
            self.stats.cuts_added += added
            self.stats.schedule_pair_conflict_cuts_added += added
            self.logger.log(
                "cut_added",
                node_id=node.id,
                family="schedule_pair_conflict",
                source_vehicle=source_vehicle,
                added=added,
                route_count=2,
                signatures=[list(pair.left.signature), list(pair.right.signature)],
                cuts=added_payload,
            )
            return added
        return 0

    def _violated_schedule_conflict_vehicles(
        self,
        solution: RMPSolution,
        routes: tuple[RouteColumn, ...] | list[RouteColumn],
    ) -> tuple[int, ...]:
        signatures = {route.signature for route in routes}
        if not signatures:
            return tuple()
        rhs = max(0, len(signatures) - 1)
        violated = []
        for vehicle in self.data.vehicles:
            y_value = float(solution.y_values.get(int(vehicle), 0.0))
            activity = sum(
                float(value)
                for route, route_vehicle, value in solution.route_values
                if int(route_vehicle) == int(vehicle) and route.signature in signatures
            )
            if activity > rhs * y_value + max(self.integer_tol, 1.0e-6):
                violated.append(int(vehicle))
        return tuple(violated)

    def _add_schedule_conflict_cuts(
        self,
        node: BPCNode,
        source_vehicle: int,
        routes: list[RouteColumn],
        *,
        kind: str,
        vehicles: tuple[int, ...] | None = None,
    ) -> int:
        vehicles = tuple(int(vehicle) for vehicle in (self.data.vehicles if vehicles is None else vehicles))
        if not vehicles:
            return 0
        new_cuts = make_no_good_cuts_for_all_vehicles(
            vehicles,
            routes,
            self._allocate_cut_ids(len(vehicles)),
            source_vehicle=source_vehicle,
            kind=kind,
        )
        added = 0
        for cut in new_cuts:
            if cut.key in self.cut_keys:
                continue
            self.cut_keys.add(cut.key)
            self.cuts.append(cut)
            added += 1
        if added:
            self.stats.cuts_added += added
            self.stats.schedule_nogood_cuts_added += added
            self.logger.log(
                "cut_added",
                node_id=node.id,
                family=kind,
                source_vehicle=source_vehicle,
                added=added,
                route_count=len(routes),
                signatures=[list(route.signature) for route in routes],
            )
        return added


def incumbent_to_solution(data: BPCData, incumbent: Incumbent | None) -> dict[str, Any]:
    solution: dict[str, Any] = {"vehicles": {}, "sorties": [], "selected_route_ids": [], "schedule_checks": {}}
    if incumbent is None:
        return solution
    for vehicle, value in incumbent.y_values.items():
        solution["vehicles"][str(vehicle)] = round(float(value), 6)
    sortie_index = {vehicle: 0 for vehicle in data.vehicles}
    grouped: dict[int, list[RouteColumn]] = {vehicle: [] for vehicle in data.vehicles}
    for route, vehicle, _value in incumbent.route_values:
        grouped[vehicle].append(route)
        sortie_index[vehicle] += 1
        solution["selected_route_ids"].append(int(route.id))
        route_data = route_to_json(route)
        solution["sorties"].append(
            {
                "vehicle": int(vehicle),
                "sortie": sortie_index[vehicle],
                "route_id": int(route.id),
                "tasks": route_data["tasks"],
                "cost": route_data["cost"],
                "load": route_data["load"],
                "energy": route_data["energy"],
                "return_time": route_data["return_time"],
                "cycle_time": route_data["cycle_time"],
                "service_start": route_data["service_start"],
            }
        )
    for vehicle, routes in grouped.items():
        checked = check_route_set_schedule_feasible(data, routes)
        order_route_ids = [int(routes[index].id) for index in checked.order] if checked.feasible else []
        solution["schedule_checks"][str(vehicle)] = {
            "feasible": bool(checked.feasible),
            "route_order": order_route_ids,
            "ready_time": checked.ready_time,
        }
    return solution
