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
    restricted_master_integer_schedule_capacity_cuts: int
    crossing_cuts_added: int
    crossing_cuts_upgraded: int
    robust_capacity_cuts_added: int
    resource_lower_bound_cuts_added: int
    schedule_pair_conflict_cuts_added: int
    schedule_nogood_cuts_added: int
    schedule_capacity_cuts_added: int
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
    restricted_master_heuristic_enabled: bool = False,
    restricted_master_time_limit: float = 20.0,
    restricted_master_max_routes: int = 4000,
    restricted_master_max_calls: int = 20,
    restricted_master_max_depth: int = 3,
    restricted_master_schedule_aware: bool = True,
    restricted_master_max_no_good_rounds: int = 20,
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
    schedule_capacity_cuts_enabled: bool = True,
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
    cut_purge_age: int = 20,
    cut_purge_slack: float = 1.0e-5,
    cut_purge_dual: float = 1.0e-8,
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
            restricted_master_heuristic_enabled=restricted_master_heuristic_enabled,
            restricted_master_time_limit=restricted_master_time_limit,
            restricted_master_max_routes=restricted_master_max_routes,
            restricted_master_max_calls=restricted_master_max_calls,
            restricted_master_max_depth=restricted_master_max_depth,
            restricted_master_schedule_aware=restricted_master_schedule_aware,
            restricted_master_max_no_good_rounds=restricted_master_max_no_good_rounds,
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
            schedule_capacity_cuts_enabled=schedule_capacity_cuts_enabled,
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
            cut_purge_age=cut_purge_age,
            cut_purge_slack=cut_purge_slack,
            cut_purge_dual=cut_purge_dual,
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
        restricted_master_integer_schedule_capacity_cuts=tree_result.stats.restricted_master_integer_schedule_capacity_cuts,
        crossing_cuts_added=tree_result.stats.crossing_cuts_added,
        crossing_cuts_upgraded=tree_result.stats.crossing_cuts_upgraded,
        robust_capacity_cuts_added=tree_result.stats.robust_capacity_cuts_added,
        resource_lower_bound_cuts_added=tree_result.stats.resource_lower_bound_cuts_added,
        schedule_pair_conflict_cuts_added=tree_result.stats.schedule_pair_conflict_cuts_added,
        schedule_nogood_cuts_added=tree_result.stats.schedule_nogood_cuts_added,
        schedule_capacity_cuts_added=tree_result.stats.schedule_capacity_cuts_added,
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
                    "tasks": list(getattr(cut, "tasks", ())),
                    "sense": cut.sense,
                    "rhs": cut.rhs,
                    "k_bound": getattr(cut, "k_bound", None),
                    "capacity_bound": getattr(cut, "capacity_bound", None),
                    "resource_bound": getattr(cut, "resource_bound", None),
                    "demand": getattr(cut, "demand", None),
                    "capacity": getattr(cut, "capacity", None),
                    "upper_bound": getattr(cut, "upper_bound", None),
                    "oracle_states": getattr(cut, "oracle_states", None),
                    "source": getattr(cut, "source", None),
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
