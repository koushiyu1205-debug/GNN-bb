"""中文摘要：本文件显式控制 clean BPC 搜索树。SCIP 在这里仅作为每个节点 RMP LP 的求解器。"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from itertools import permutations
import math
import time
from typing import Any

from .branching import BranchConstraint, choose_branch
from .columns import RouteColumn, RoutePool, evaluate_route, route_to_json
from .cuts import ScheduleNoGoodCut, make_no_good_cuts_for_all_vehicles
from .data import BPCData
from .logger import BPCLogger
from .node import BPCNode, BPCStats
from .pricing import exact_pricing
from .rmp import RMPSolution, solve_rmp_lp
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
    cuts: list[ScheduleNoGoodCut]
    incumbent: Incumbent | None


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
        self.pool = RoutePool()
        self.cuts: list[ScheduleNoGoodCut] = []
        self.cut_keys: set[tuple[int, tuple[tuple[int, ...], ...]]] = set()
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
            self.stats.fathomed_integral += 1
            self.logger.log("fathom", node_id=node.id, reason="integral", bound=round(node.lower_bound, 6))
            return []

        branch = choose_branch(
            self.data,
            last_solution.route_values,
            last_solution.y_values,
            node.branch_constraints,
            tol=self.integer_tol,
        )
        if branch is None:
            self.abort_status = "BRANCH_FAILED"
            self.logger.log("fathom", node_id=node.id, reason="no_branch_candidate", bound=round(node.lower_bound, 6))
            return []

        left, right = branch
        left_node = self._make_child(node, left)
        right_node = self._make_child(node, right)
        self.logger.log("branch", node_id=node.id, left=left.name(), right=right.name(), lower_bound=round(node.lower_bound, 6))
        return [left_node, right_node]

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
            new_cuts = make_no_good_cuts_for_all_vehicles(
                self.data.vehicles,
                conflict,
                len(self.cuts),
                source_vehicle=vehicle,
                kind="schedule_infeasible_route_set",
            )
            added = 0
            for cut in new_cuts:
                if cut.key in self.cut_keys:
                    continue
                self.cut_keys.add(cut.key)
                self.cuts.append(cut)
                added += 1
            self.stats.cuts_added += added
            self.logger.log(
                "cut_added",
                node_id=node.id,
                source_vehicle=vehicle,
                added=added,
                signatures=[list(route.signature) for route in conflict],
            )
            return added

        objective = float(solution.objective or 0.0)
        if self.incumbent is None or objective < self.incumbent.objective - self.integer_tol:
            self.incumbent = Incumbent(objective=objective, route_values=selected, y_values=solution.y_values, node_id=node.id)
            self.logger.log("incumbent", node_id=node.id, objective=round(objective, 6), source="certified_integral")
        return 0


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
