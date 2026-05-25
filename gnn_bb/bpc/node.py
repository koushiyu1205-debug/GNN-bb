"""中文摘要：本文件定义 clean BPC 搜索树节点和求解统计对象。"""

from __future__ import annotations

from dataclasses import dataclass, field

from .branching import BranchConstraint


@dataclass(order=True)
class BPCNode:
    priority: float
    id: int = field(compare=False)
    depth: int = field(compare=False)
    branch_constraints: tuple[BranchConstraint, ...] = field(compare=False, default_factory=tuple)
    parent_id: int | None = field(compare=False, default=None)
    description: str = field(compare=False, default="root")
    lower_bound: float = field(compare=False, default=0.0)
    schedule_pack_relaxation_bound: float | None = field(compare=False, default=None)


@dataclass
class BPCStats:
    rmp_solves: int = 0
    pricing_calls: int = 0
    exact_pricing_calls: int = 0
    branch_lp_test_rmp_solves: int = 0
    branch_heuristic_test_rmp_solves: int = 0
    branch_heuristic_test_pricing_calls: int = 0
    branch_lp_candidates_tested: int = 0
    branch_heuristic_candidates_tested: int = 0
    branch_testing_time: float = 0.0
    restricted_master_integer_calls: int = 0
    restricted_master_integer_feasible: int = 0
    restricted_master_integer_time: float = 0.0
    restricted_master_integer_best_objective: float | None = None
    restricted_master_integer_raw_best_objective: float | None = None
    restricted_master_integer_rejected: int = 0
    restricted_master_integer_no_good_cuts: int = 0
    restricted_master_integer_pair_conflict_cuts: int = 0
    restricted_master_integer_route_set_packing_cuts: int = 0
    restricted_master_integer_schedule_capacity_cuts: int = 0
    restricted_master_integer_repair_attempts: int = 0
    restricted_master_integer_repair_successes: int = 0
    restricted_master_integer_repair_time: float = 0.0
    restricted_master_integer_repair_states: int = 0
    restricted_master_integer_repair_best_objective: float | None = None
    time_to_first_incumbent: float | None = None
    time_to_best_incumbent: float | None = None
    best_incumbent_value: float | None = None
    open_nodes_remaining: int = 0
    timeout_pending_node_certified: bool | None = None
    official_bound_available: bool = True
    fathom_reasons: dict[str, int] = field(default_factory=dict)
    crossing_cuts_added: int = 0
    crossing_cuts_upgraded: int = 0
    subset_row_cuts_added: int = 0
    lm_rank1_cuts_added: int = 0
    robust_capacity_cuts_added: int = 0
    resource_lower_bound_cuts_added: int = 0
    schedule_subset_cost_cuts_added: int = 0
    schedule_pair_conflict_cuts_added: int = 0
    schedule_clique_conflict_cuts_added: int = 0
    schedule_route_set_packing_cuts_added: int = 0
    schedule_nogood_cuts_added: int = 0
    schedule_capacity_cuts_added: int = 0
    root_schedule_capacity_cuts_added: int = 0
    root_schedule_capacity_oracle_queries: int = 0
    root_schedule_capacity_oracle_incomplete: int = 0
    root_schedule_capacity_oracle_time: float = 0.0
    root_schedule_capacity_cache_hits: int = 0
    root_schedule_capacity_candidates_generated: int = 0
    root_schedule_capacity_candidates_after_precheck: int = 0
    root_schedule_capacity_best_violation: float = 0.0
    route_set_schedule_packing_oracle_queries: int = 0
    route_set_schedule_packing_oracle_time: float = 0.0
    route_set_schedule_packing_cache_hits: int = 0
    route_set_schedule_packing_added_but_no_bound_improvement: int = 0
    fleet_lower_bound_cuts_added: int = 0
    fleet_lower_bound_value: int = 0
    fleet_lower_bound_oracle_upper_bound: int | None = None
    fleet_lower_bound_oracle_states: int = 0
    fleet_lower_bound_oracle_exact: bool = False
    schedule_pack_diagnostic_status: str | None = None
    schedule_pack_diagnostic_objective: float | None = None
    schedule_pack_diagnostic_gap_vs_root: float | None = None
    schedule_pack_diagnostic_columns: int = 0
    schedule_pack_diagnostic_candidate_routes: int = 0
    schedule_pack_diagnostic_generated_states: int = 0
    schedule_pack_diagnostic_time: float = 0.0
    schedule_pack_relaxation_calls: int = 0
    schedule_pack_relaxation_time: float = 0.0
    schedule_pack_relaxation_root_objective: float | None = None
    schedule_pack_relaxation_best_objective: float | None = None
    schedule_pack_relaxation_best_gap_vs_node: float | None = None
    schedule_pack_relaxation_candidate_exact: int = 0
    schedule_pack_relaxation_full_exact: int = 0
    schedule_pack_relaxation_full_pricing_states: int = 0
    schedule_pack_relaxation_full_pricing_time: float = 0.0
    schedule_pack_relaxation_columns: int = 0
    schedule_pack_adaptive_decisions: int = 0
    schedule_pack_adaptive_runs: int = 0
    schedule_pack_adaptive_skips: int = 0
    schedule_pack_adaptive_easy_skips: int = 0
    schedule_pack_adaptive_bound_skips: int = 0
    route_enumeration_adaptive_decisions: int = 0
    route_enumeration_adaptive_runs: int = 0
    route_enumeration_adaptive_skips: int = 0
    route_enumeration_adaptive_easy_skips: int = 0
    cuts_purged: int = 0
    generated_routes: int = 0
    generated_columns: int = 0
    label_pops: int = 0
    generated_labels: int = 0
    cuts_added: int = 0
    branch_nodes: int = 0
    fathomed_infeasible: int = 0
    fathomed_bound: int = 0
    fathomed_integral: int = 0
    nodes_processed: int = 0
    root_relaxation: float | None = None
    diagnostic_dual_bound: float | None = None
    diagnostic_gap: float | None = None
    best_open_node_bound: float | None = None
    pending_node_bound: float | None = None
    last_certified_node_bound: float | None = None
