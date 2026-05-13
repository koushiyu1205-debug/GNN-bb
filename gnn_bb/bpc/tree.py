"""中文摘要：本文件显式控制 clean BPC 搜索树。SCIP 在这里仅作为每个节点 RMP LP 的求解器。"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from itertools import combinations
from itertools import permutations
import math
import time
from typing import Any

from .branching import BranchCandidate, BranchConstraint, choose_branch, generate_branch_candidates
from .columns import RouteColumn, RoutePool, evaluate_route, route_to_json
from .cuts import (
    Cut,
    CrossingCut,
    ScheduleCapacityCut,
    ScheduleNoGoodCut,
    capacity_route_lower_bound,
    make_no_good_cuts_for_all_vehicles,
)
from .data import BPCData
from .logger import BPCLogger
from .node import BPCNode, BPCStats
from .pricing import exact_pricing
from .rmp import RMPSolution, solve_rmp_lp
from .schedule_capacity import ScheduleCapacityResult, exact_schedule_task_capacity
from .validation import check_route_set_schedule_feasible, shrink_infeasible_route_set


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
    ) -> None:
        self.data = data
        self.time_limit = float(time_limit)
        self.max_nodes = int(max_nodes)
        self.eps = float(eps)
        self.integer_tol = float(integer_tol)
        self.max_routes_per_pricing = int(max_routes_per_pricing)
        self.max_labels_per_pricing = int(max_labels_per_pricing)
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
        self.schedule_capacity_cuts_enabled = bool(schedule_capacity_cuts_enabled)
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
        self.cut_purge_age = int(cut_purge_age)
        self.cut_purge_slack = float(cut_purge_slack)
        self.cut_purge_dual = float(cut_purge_dual)
        self.pseudocosts: dict[str, PseudoCostRecord] = {}
        self.pool = RoutePool()
        self.cuts: list[Cut] = []
        self.cut_keys: set[tuple] = set()
        self.cut_inactive_age: dict[tuple, int] = {}
        self.cut_rounds_by_node: dict[int, int] = {}
        self.resource_cut_rounds_by_node: dict[int, int] = {}
        self.schedule_capacity_cut_rounds_by_node: dict[int, int] = {}
        self.schedule_capacity_cache: dict[tuple[int, ...], ScheduleCapacityResult | None] = {}
        self.resource_pair_incompatible: set[tuple[int, int]] | None = None
        self.resource_chromatic_cache: dict[tuple[int, ...], int] = {}
        self.next_cut_id = 0
        self.stats = BPCStats()
        self.incumbent: Incumbent | None = None
        self.next_node_id = 1
        self.start_time = time.perf_counter()
        self.abort_status: str | None = None

    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time

    def _time_left(self) -> bool:
        return self.elapsed() <= self.time_limit + 1.0e-9

    def initialize(self) -> None:
        for task in self.data.tasks:
            route = evaluate_route(self.data, (task,))
            if route is not None:
                self.pool.add(route)
        self._build_greedy_incumbent()

    def _allocate_cut_id(self) -> int:
        cut_id = self.next_cut_id
        self.next_cut_id += 1
        return cut_id

    def _allocate_cut_ids(self, count: int) -> int:
        first_id = self.next_cut_id
        self.next_cut_id += int(count)
        return first_id

    def _build_greedy_incumbent(self) -> None:
        # 中文注释：这个启发式只给 UB，不参与 lower bound 或最优性证明。
        best_assigned: dict[int, list[RouteColumn]] | None = None
        best_objective = float("inf")
        for order in self._construction_orders():
            assigned = self._construct_assignment(order)
            if assigned is None:
                continue
            assigned = self._improve_assignment(assigned)
            objective = self._assignment_objective(assigned)
            if objective < best_objective - self.integer_tol:
                best_assigned = assigned
                best_objective = objective
        if best_assigned is None:
            return
        self._set_incumbent_from_assignment(best_assigned, node_id=0, source="greedy_schedule")

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
                        score = (
                            1,
                            float(route.cost),
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
                        0,
                        float(delta_cost),
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
        )

        status = "UNKNOWN"
        while open_nodes and self._time_left() and self.stats.nodes_processed < self.max_nodes and self.abort_status is None:
            node = heapq.heappop(open_nodes)
            if self.incumbent is not None and node.lower_bound >= self.incumbent.objective - self.integer_tol:
                self.stats.fathomed_bound += 1
                self.logger.log("fathom", node_id=node.id, reason="bound_before_process", bound=round(node.lower_bound, 6))
                continue
            self.logger.log("node_start", node_id=node.id, depth=node.depth, node_lb=round(node.lower_bound, 6), open_nodes=len(open_nodes))
            children = self._process_node(node)
            self.stats.nodes_processed += 1
            for child in children:
                heapq.heappush(open_nodes, child)
            if children:
                self.stats.branch_nodes += 1

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
        primal = None if self.incumbent is None else self.incumbent.objective
        gap = None
        if primal is not None and dual is not None and abs(primal) > 1.0e-12:
            gap = max(0.0, (primal - dual) / abs(primal))
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
            nodes=self.stats.nodes_processed,
            routes=len(self.pool.routes),
            cuts=len(self.cuts),
            crossing_cuts_added=self.stats.crossing_cuts_added,
            crossing_cuts_upgraded=self.stats.crossing_cuts_upgraded,
            robust_capacity_cuts_added=self.stats.robust_capacity_cuts_added,
            resource_lower_bound_cuts_added=self.stats.resource_lower_bound_cuts_added,
            schedule_nogood_cuts_added=self.stats.schedule_nogood_cuts_added,
            schedule_capacity_cuts_added=self.stats.schedule_capacity_cuts_added,
            cuts_purged=self.stats.cuts_purged,
            rmp_solves=self.stats.rmp_solves,
            pricing_calls=self.stats.pricing_calls,
            branch_testing_time=round(self.stats.branch_testing_time, 6),
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

    def _process_node(self, node: BPCNode) -> list[BPCNode]:
        cg_iter = 0
        phase = "phase1"
        last_solution: RMPSolution | None = None

        while self._time_left():
            cg_iter += 1
            solution = solve_rmp_lp(
                self.data,
                self.pool.routes,
                self.cuts,
                node.branch_constraints,
                phase=phase,
                rmp_params=self.rmp_params,
                verbose=False,
                task_vehicle_linking_enabled=self.task_vehicle_linking_enabled,
            )
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
                cut_count=len(self.cuts),
                variable_count=solution.variable_count,
                constraint_count=solution.constraint_count,
            )

            if not solution.optimal or solution.duals is None:
                self.stats.fathomed_infeasible += 1
                self.logger.log("fathom", node_id=node.id, reason=f"rmp_{solution.status.lower()}", bound=None)
                return []

            if phase == "phase2":
                purged = self._purge_inactive_capacity_cuts(solution)
                if purged:
                    self.logger.log("cut_purged", node_id=node.id, removed=purged, remaining=len(self.cuts))
                    continue

            if phase == "phase1" and solution.artificial_sum <= self.integer_tol:
                phase = "phase2"
                continue

            pricing = exact_pricing(
                self.data,
                self.pool.routes,
                solution.duals,
                self.cuts,
                node.branch_constraints,
                phase=phase,
                eps=self.eps,
                max_routes_to_return=self.max_routes_per_pricing,
                max_labels=self.max_labels_per_pricing,
            )
            self.stats.pricing_calls += 1
            self.stats.exact_pricing_calls += 1
            added = 0
            for route in pricing.routes:
                before = len(self.pool.routes)
                self.pool.add(route)
                if len(self.pool.routes) > before:
                    added += 1
            self.stats.generated_routes = len(self.pool.routes)
            self.logger.log(
                "pricing",
                node_id=node.id,
                depth=node.depth,
                cg_iter=cg_iter,
                phase=phase,
                best_reduced_cost=None if pricing.best_reduced_cost is None else round(pricing.best_reduced_cost, 9),
                negative_routes=pricing.negative_routes,
                added_routes=added,
                exhausted=pricing.exhausted,
                label_pops=pricing.label_pops,
                generated_labels=pricing.generated_labels,
            )
            if added > 0:
                continue
            if not pricing.exhausted:
                self.abort_status = "PRICING_INCOMPLETE"
                self.logger.log("fathom", node_id=node.id, reason="pricing_incomplete", bound=None)
                return []
            if phase == "phase1":
                self.stats.fathomed_infeasible += 1
                self.logger.log("fathom", node_id=node.id, reason="phase1_infeasible", bound=None)
                return []
            separated = self._separate_crossing_cuts(node, solution)
            if separated:
                continue
            separated = self._separate_schedule_capacity_cuts(node, solution)
            if separated:
                continue
            break

        if last_solution is None or not last_solution.optimal or last_solution.objective is None:
            return []

        node.lower_bound = float(last_solution.objective)
        if self.stats.root_relaxation is None and node.id == 0:
            self.stats.root_relaxation = node.lower_bound

        if self.incumbent is not None and node.lower_bound >= self.incumbent.objective - self.integer_tol:
            self.stats.fathomed_bound += 1
            self.logger.log("fathom", node_id=node.id, reason="bound", bound=round(node.lower_bound, 6))
            return []

        integral = self._is_integral(last_solution)
        if integral:
            cuts_added = self._validate_integral_or_cut(node, last_solution)
            if cuts_added:
                return [BPCNode(priority=node.lower_bound, id=node.id, depth=node.depth, branch_constraints=node.branch_constraints, parent_id=node.parent_id, description=node.description, lower_bound=node.lower_bound)]
            if self.abort_status is not None:
                return []
            self.stats.fathomed_integral += 1
            self.logger.log("fathom", node_id=node.id, reason="integral", bound=round(node.lower_bound, 6))
            return []

        branch = self._choose_branch(node, last_solution)
        if branch is None:
            self.abort_status = "BRANCH_FAILED"
            self.logger.log("fathom", node_id=node.id, reason="no_branch_candidate", bound=round(node.lower_bound, 6))
            return []

        left, right = branch
        left_node = self._make_child(node, left)
        right_node = self._make_child(node, right)
        self.logger.log("branch", node_id=node.id, left=left.name(), right=right.name(), lower_bound=round(node.lower_bound, 6))
        return [left_node, right_node]

    def _cut_activity(self, cut: Cut, solution: RMPSolution) -> float:
        return sum(cut.coefficient(route, vehicle) * value for route, vehicle, value in solution.route_values)

    def _cut_slack(self, cut: Cut, solution: RMPSolution) -> float:
        activity = self._cut_activity(cut, solution)
        if cut.sense == "<=":
            return float(cut.rhs) - activity
        if cut.sense == ">=":
            return activity - float(cut.rhs)
        raise ValueError(f"未知 cut sense: {cut.sense}")

    def _purge_inactive_capacity_cuts(self, solution: RMPSolution) -> int:
        if self.cut_purge_age <= 0 or solution.duals is None:
            return 0
        kept: list[Cut] = []
        removed = 0
        for cut in self.cuts:
            if not isinstance(cut, (CrossingCut, ScheduleCapacityCut)):
                kept.append(cut)
                continue
            key = cut.key
            slack = self._cut_slack(cut, solution)
            dual_abs = abs(float(solution.duals.cuts.get(cut.id, 0.0)))
            if slack > self.cut_purge_slack and dual_abs <= self.cut_purge_dual:
                self.cut_inactive_age[key] = self.cut_inactive_age.get(key, 0) + 1
            else:
                self.cut_inactive_age[key] = 0
            if self.cut_inactive_age.get(key, 0) >= self.cut_purge_age:
                removed += 1
                self.cut_keys.discard(key)
                self.cut_inactive_age.pop(key, None)
            else:
                kept.append(cut)
        if removed:
            self.cuts = kept
            self.stats.cuts_purged += removed
        return removed

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

    def _separate_schedule_capacity_cuts(self, node: BPCNode, solution: RMPSolution) -> int:
        if not self.schedule_capacity_cuts_enabled:
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
        for vehicle in self.data.vehicles:
            y_value = float(solution.y_values.get(vehicle, 0.0))
            if y_value <= self.integer_tol:
                continue
            for tasks in candidate_subsets_by_vehicle.get(int(vehicle), []):
                key = ("schedule_capacity", int(vehicle), tasks)
                if key in self.cut_keys:
                    continue
                oracle = self._schedule_capacity_bound(tasks)
                if oracle is None:
                    continue
                upper_bound = int(oracle.upper_bound)
                if upper_bound >= len(tasks):
                    continue
                activity = self._task_vehicle_mass(solution, tasks, int(vehicle)) - upper_bound * y_value
                if activity > self.schedule_capacity_cut_min_violation:
                    candidates.append((activity, int(vehicle), tasks, upper_bound, oracle.states_explored, y_value))

        if not candidates:
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

    def _schedule_capacity_bound(self, tasks: tuple[int, ...]) -> ScheduleCapacityResult | None:
        tasks = tuple(sorted(int(task) for task in tasks))
        if tasks not in self.schedule_capacity_cache:
            self.schedule_capacity_cache[tasks] = exact_schedule_task_capacity(
                self.data,
                tasks,
                max_states=self.schedule_capacity_oracle_max_states,
            )
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

        initialized.sort(key=lambda item: (-self.pseudocosts[item.key].average_score, -item.fractionality, item.key))
        uninitialized.sort(key=lambda item: (-item.fractionality, item.key))
        screened = [
            *initialized[: max(0, self.three_pb_pseudocost_candidates)],
            *uninitialized[: max(0, self.three_pb_fractional_candidates)],
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
            by_kind=self._candidate_kind_counts(candidates),
            screened_candidates=[candidate.compact() for candidate in screened[:20]],
        )

        testing_started = time.perf_counter()
        lp_results: list[BranchTestResult] = []
        for candidate in screened:
            lp_results.append(self._lp_test_candidate(node, solution, candidate))
        self.stats.branch_lp_candidates_tested += len(lp_results)

        lp_results.sort(key=lambda item: (-item.lp_score, item.candidate.key))
        lp_top = lp_results[: max(1, min(self.three_pb_lp_candidates, len(lp_results)))]

        heuristic_results: list[BranchTestResult] = []
        for item in lp_top:
            heuristic_results.append(self._heuristic_test_candidate(node, solution, item))
        self.stats.branch_heuristic_candidates_tested += len(heuristic_results)
        testing_time = time.perf_counter() - testing_started
        self.stats.branch_testing_time += testing_time

        selected = max(heuristic_results, key=lambda item: (item.heuristic_score, item.lp_score, item.candidate.fractionality, item.candidate.key))
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
            top_results=[self._branch_test_to_log(item) for item in heuristic_results[:20]],
        )
        return selected.candidate.left, selected.candidate.right

    def _candidate_kind_counts(self, candidates: list[BranchCandidate]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for candidate in candidates:
            counts[candidate.kind] = counts.get(candidate.kind, 0) + 1
        return dict(sorted(counts.items()))

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
            checked = check_route_set_schedule_feasible(self.data, routes)
            if checked.feasible:
                continue

            conflict = shrink_infeasible_route_set(self.data, routes)
            core_added = self._add_schedule_conflict_cuts(
                node,
                int(vehicle),
                conflict,
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
            self.logger.log("incumbent", node_id=node.id, objective=round(objective, 6), source="certified_integral")
        return 0

    def _add_schedule_conflict_cuts(
        self,
        node: BPCNode,
        source_vehicle: int,
        routes: list[RouteColumn],
        *,
        kind: str,
    ) -> int:
        new_cuts = make_no_good_cuts_for_all_vehicles(
            self.data.vehicles,
            routes,
            self._allocate_cut_ids(len(self.data.vehicles)),
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
    solution: dict[str, Any] = {"vehicles": {}, "sorties": [], "selected_route_ids": []}
    if incumbent is None:
        return solution
    for vehicle, value in incumbent.y_values.items():
        solution["vehicles"][str(vehicle)] = round(float(value), 6)
    sortie_index = {vehicle: 0 for vehicle in data.vehicles}
    for route, vehicle, _value in incumbent.route_values:
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
    return solution
