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
    crossing_cuts_added: int = 0
    crossing_cuts_upgraded: int = 0
    robust_capacity_cuts_added: int = 0
    resource_lower_bound_cuts_added: int = 0
    schedule_nogood_cuts_added: int = 0
    schedule_capacity_cuts_added: int = 0
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
