"""中文摘要：显式控制 vehicle-schedule BPC 搜索树。"""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import math
import time
from typing import Any

from .branching import BranchConstraint, generate_rf_candidates
from .columns import ScheduleColumn, SchedulePool, Sortie
from .data import InstanceData
from .logger import BPCLogger
from .pricing import exact_schedule_pricing
from .rmp import RMPSolution, solve_rmp_lp


@dataclass(order=True)
class SearchNode:
    priority: float
    id: int = field(compare=False)
    depth: int = field(compare=False)
    branch_constraints: tuple[BranchConstraint, ...] = field(compare=False, default_factory=tuple)
    lower_bound: float = field(compare=False, default=0.0)


@dataclass
class TreeStats:
    nodes: int = 0
    rmp_solves: int = 0
    pricing_calls: int = 0
    generated_columns: int = 0
    label_pops: int = 0
    generated_labels: int = 0
    pricing_queue_peak: int = 0
    branch_nodes: int = 0
    root_relaxation: float | None = None


@dataclass
class Incumbent:
    objective: float
    columns: list[ScheduleColumn]
    node_id: int


@dataclass
class TreeResult:
    status: str
    primal_bound: float | None
    dual_bound: float | None
    gap: float | None
    elapsed: float
    stats: TreeStats
    columns: list[ScheduleColumn]
    incumbent: Incumbent | None


class VehicleScheduleBPCTree:
    def __init__(
        self,
        data: InstanceData,
        *,
        time_limit: float,
        max_nodes: int,
        eps: float,
        integer_tol: float,
        max_columns_per_pricing: int,
        max_labels_per_pricing: int,
        max_generated_labels_per_pricing: int,
        max_queue_size_per_pricing: int,
        max_candidate_pool_per_pricing: int,
        max_pricing_seconds: float,
        rmp_params: dict[str, Any] | None,
        logger: BPCLogger,
    ) -> None:
        self.data = data
        self.time_limit = float(time_limit)
        self.max_nodes = int(max_nodes)
        self.eps = float(eps)
        self.integer_tol = float(integer_tol)
        self.max_columns_per_pricing = int(max_columns_per_pricing)
        self.max_labels_per_pricing = int(max_labels_per_pricing)
        self.max_generated_labels_per_pricing = int(max_generated_labels_per_pricing)
        self.max_queue_size_per_pricing = int(max_queue_size_per_pricing)
        self.max_candidate_pool_per_pricing = int(max_candidate_pool_per_pricing)
        self.max_pricing_seconds = float(max_pricing_seconds)
        self.rmp_params = dict(rmp_params or {})
        self.logger = logger
        self.pool = SchedulePool()
        self.stats = TreeStats()
        self.incumbent: Incumbent | None = None
        self.next_node_id = 1
        self.start_time = time.perf_counter()

    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time

    def _time_left(self) -> bool:
        return self.elapsed() <= self.time_limit + 1.0e-9

    def _remaining_time(self) -> float:
        return max(0.0, self.time_limit - self.elapsed())

    def initialize(self) -> None:
        for task in self.data.tasks:
            column = self._single_task_schedule(task)
            if column is not None:
                self.pool.add(column)
        greedy = self._greedy_schedule_columns()
        if greedy is not None:
            for column in greedy:
                self.pool.add(column)
            self.incumbent = Incumbent(sum(column.cost for column in greedy), greedy, 0)
            self.logger.log("incumbent", node=0, objective=round(self.incumbent.objective, 6), source="greedy")

    def solve(self) -> TreeResult:
        self.initialize()
        self.logger.log("start", instance=self.data.name, tasks=len(self.data.tasks), initial_columns=len(self.pool.columns))
        root = SearchNode(priority=0.0, id=0, depth=0, lower_bound=0.0)
        open_nodes: list[SearchNode] = [root]
        heapq.heapify(open_nodes)
        best_dual: float | None = None
        status = "TIME_LIMIT"

        while open_nodes and self._time_left() and self.stats.nodes < self.max_nodes:
            node = heapq.heappop(open_nodes)
            self.stats.nodes += 1
            self.logger.log("node", node=node.id, depth=node.depth, lower_bound=round(node.lower_bound, 6), open_nodes=len(open_nodes))
            solution, certified = self._solve_node_lp(node)
            if not certified:
                status = "PRICING_LIMIT"
                break
            if solution is None or not solution.optimal:
                self.logger.log("fathom", node=node.id, reason="infeasible_or_no_lp")
                continue
            node.lower_bound = float(solution.objective or 0.0)
            if node.id == 0:
                self.stats.root_relaxation = node.lower_bound
            best_dual = node.lower_bound if best_dual is None else min(best_dual, node.lower_bound)
            if self.incumbent is not None and node.lower_bound >= self.incumbent.objective - self.integer_tol:
                self.logger.log("fathom", node=node.id, reason="bound")
                continue
            if self._is_integral(solution):
                columns = [column for column, value in solution.schedule_values if value > 1.0 - self.integer_tol]
                objective = float(solution.objective or 0.0)
                if self.incumbent is None or objective < self.incumbent.objective - self.integer_tol:
                    self.incumbent = Incumbent(objective, columns, node.id)
                    self.logger.log("incumbent", node=node.id, objective=round(objective, 6), source="integral_master")
                self.logger.log("fathom", node=node.id, reason="integral")
                continue

            candidate = self._choose_branch(solution)
            if candidate is None:
                status = "UNSUPPORTED_FRACTIONAL"
                self.logger.log("fathom", node=node.id, reason="no_pricing_compatible_branch")
                break
            self.stats.branch_nodes += 1
            left = self._child(node, BranchConstraint("separate", candidate.i, candidate.j))
            right = self._child(node, BranchConstraint("same", candidate.i, candidate.j))
            heapq.heappush(open_nodes, left)
            heapq.heappush(open_nodes, right)
            self.logger.log("branch", node=node.id, i=candidate.i, j=candidate.j, value=round(candidate.value, 6))

        if not open_nodes and status not in {"PRICING_LIMIT", "UNSUPPORTED_FRACTIONAL"}:
            status = "OPTIMAL"
        elif self.stats.nodes >= self.max_nodes:
            status = "NODE_LIMIT"

        primal = None if self.incumbent is None else self.incumbent.objective
        dual = self._global_lower_bound(open_nodes, best_dual, status)
        gap = None
        if primal is not None and dual is not None and abs(primal) > self.integer_tol:
            gap = max(0.0, (primal - dual) / abs(primal))
        self.logger.log(
            "finish",
            status=status,
            primal=None if primal is None else round(primal, 6),
            dual=None if dual is None else round(dual, 6),
            gap=None if gap is None else round(gap, 6),
            nodes=self.stats.nodes,
        )
        return TreeResult(status, primal, dual, gap, self.elapsed(), self.stats, self.pool.columns, self.incumbent)

    def _solve_node_lp(self, node: SearchNode) -> tuple[RMPSolution | None, bool]:
        for phase in ("phase1", "phase2"):
            cg_iter = 0
            while self._time_left():
                cg_iter += 1
                solution = solve_rmp_lp(
                    self.data,
                    self.pool.columns,
                    node.branch_constraints,
                    phase=phase,
                    rmp_params=self.rmp_params,
                )
                self.stats.rmp_solves += 1
                self.logger.log(
                    "rmp",
                    node=node.id,
                    phase=phase,
                    cg_iter=cg_iter,
                    objective=None if solution.objective is None else round(solution.objective, 6),
                    artificial=round(solution.artificial_sum, 6),
                    columns=len(self.pool.columns),
                )
                if not solution.optimal:
                    return solution, True
                if solution.duals is None:
                    return solution, False
                result = exact_schedule_pricing(
                    self.data,
                    self.pool.columns,
                    solution.duals,
                    node.branch_constraints,
                    phase=phase,
                    eps=self.eps,
                    max_columns_to_return=self.max_columns_per_pricing,
                    max_labels=self.max_labels_per_pricing,
                    max_generated_labels=self.max_generated_labels_per_pricing,
                    max_queue_size=self.max_queue_size_per_pricing,
                    max_candidate_pool=self.max_candidate_pool_per_pricing,
                    max_seconds=min(self.max_pricing_seconds, self._remaining_time()) if self.max_pricing_seconds > 0 else self._remaining_time(),
                )
                self.stats.pricing_calls += 1
                self.stats.label_pops += result.label_pops
                self.stats.generated_labels += result.generated_labels
                self.stats.pricing_queue_peak = max(self.stats.pricing_queue_peak, result.queue_peak)
                added = 0
                for column in result.columns:
                    before = len(self.pool.columns)
                    self.pool.add(column)
                    added += int(len(self.pool.columns) > before)
                self.stats.generated_columns += added
                self.logger.log(
                    "pricing",
                    node=node.id,
                    phase=phase,
                    cg_iter=cg_iter,
                    best_rc=None if result.best_reduced_cost is None else round(result.best_reduced_cost, 6),
                    found=len(result.columns),
                    added=added,
                    exhausted=result.exhausted,
                    labels=result.label_pops,
                    generated_labels=result.generated_labels,
                    queue_peak=result.queue_peak,
                    stop_reason=result.stop_reason,
                )
                if not result.exhausted:
                    return solution, False
                if added == 0:
                    if phase == "phase1" and solution.artificial_sum > self.integer_tol:
                        return None, True
                    if phase == "phase2":
                        return solution, True
                    break
        return None, True

    def _is_integral(self, solution: RMPSolution) -> bool:
        return all(
            value <= self.integer_tol or value >= 1.0 - self.integer_tol
            for _column, value in solution.schedule_values
        )

    def _choose_branch(self, solution: RMPSolution):
        candidates = generate_rf_candidates(self.data.tasks, solution.schedule_values, self.integer_tol)
        return candidates[0] if candidates else None

    def _child(self, parent: SearchNode, constraint: BranchConstraint) -> SearchNode:
        node = SearchNode(
            priority=parent.lower_bound,
            id=self.next_node_id,
            depth=parent.depth + 1,
            branch_constraints=(*parent.branch_constraints, constraint),
            lower_bound=parent.lower_bound,
        )
        self.next_node_id += 1
        return node

    def _global_lower_bound(self, open_nodes: list[SearchNode], best_dual: float | None, status: str) -> float | None:
        if status == "OPTIMAL" and self.incumbent is not None and not open_nodes:
            return self.incumbent.objective
        values = [node.lower_bound for node in open_nodes]
        if best_dual is not None:
            values.append(best_dual)
        return min(values) if values else best_dual

    def _single_task_schedule(self, task: int) -> ScheduleColumn | None:
        segment = self.data.arc(0, task)
        arrival = float(segment["tau"])
        start = max(self.data.task_value(task, "r"), arrival)
        finish = start + self.data.task_value(task, "sigma")
        if finish > self.data.task_value(task, "D") + 1.0e-9:
            return None
        back = self.data.arc(task, 0)
        load = self.data.task_value(task, "d")
        energy = float(segment["energy"]) + self.data.task_value(task, "g") + float(back["energy"])
        if load > self.data.capacity + 1.0e-9 or energy > self.data.energy_limit + 1.0e-9:
            return None
        return_time = finish + float(back["tau"])
        ready_time = return_time + energy / self.data.rho
        if ready_time > self.data.horizon + 1.0e-9:
            return None
        sortie = Sortie(
            tasks=(int(task),),
            start_time=0.0,
            return_time=round(return_time, 6),
            ready_time=round(ready_time, 6),
            load=round(load, 6),
            energy=round(energy, 6),
            cost=round(float(segment["cost"]) + self.data.task_value(task, "c_srv") + float(back["cost"]), 6),
            service_start={str(task): round(start, 6)},
        )
        variable_cost = float(sortie.cost)
        return ScheduleColumn(
            id=-1,
            sorties=(sortie,),
            task_set=frozenset({int(task)}),
            cost=round(self.data.fixed_vehicle_cost + variable_cost, 6),
            variable_cost=round(variable_cost, 6),
            ready_time=round(ready_time, 6),
        )

    def _greedy_schedule_columns(self) -> list[ScheduleColumn] | None:
        # 中文注释：只构造初始 UB；失败不会影响精确性。
        columns: list[ScheduleColumn] = []
        current: list[int] = []
        for task in self.data.tasks:
            trial = (*current, int(task))
            column = self._sequence_as_one_sortie_schedule(trial)
            if column is not None:
                current = list(trial)
                continue
            if current:
                stored = self._sequence_as_one_sortie_schedule(tuple(current))
                if stored is None:
                    return None
                columns.append(stored)
            current = [int(task)]
        if current:
            stored = self._sequence_as_one_sortie_schedule(tuple(current))
            if stored is None:
                return None
            columns.append(stored)
        if len(columns) > self.data.vehicle_count:
            return None
        return columns

    def _sequence_as_one_sortie_schedule(self, sequence: tuple[int, ...]) -> ScheduleColumn | None:
        label = self._single_task_schedule(sequence[0])
        if label is None or len(sequence) == 1:
            return label
        # 中文注释：复用 pricing 的直接资源推进逻辑，生成一个单 sortie schedule。
        current = 0
        current_time = 0.0
        load = 0.0
        energy = 0.0
        cost = 0.0
        service_start = {}
        for task in sequence:
            segment = self.data.arc(current, task)
            arrival = current_time + float(segment["tau"])
            start = max(self.data.task_value(task, "r"), arrival)
            finish = start + self.data.task_value(task, "sigma")
            if finish > self.data.task_value(task, "D") + 1.0e-9:
                return None
            load += self.data.task_value(task, "d")
            energy += float(segment["energy"]) + self.data.task_value(task, "g")
            cost += float(segment["cost"]) + self.data.task_value(task, "c_srv")
            if load > self.data.capacity + 1.0e-9 or energy > self.data.energy_limit + 1.0e-9:
                return None
            service_start[str(task)] = round(start, 6)
            current = int(task)
            current_time = finish
        back = self.data.arc(current, 0)
        return_time = current_time + float(back["tau"])
        energy += float(back["energy"])
        cost += float(back["cost"])
        ready_time = return_time + energy / self.data.rho
        if energy > self.data.energy_limit + 1.0e-9 or ready_time > self.data.horizon + 1.0e-9:
            return None
        sortie = Sortie(tuple(sequence), 0.0, round(return_time, 6), round(ready_time, 6), round(load, 6), round(energy, 6), round(cost, 6), service_start)
        return ScheduleColumn(-1, (sortie,), frozenset(sequence), round(self.data.fixed_vehicle_cost + cost, 6), round(cost, 6), round(ready_time, 6))
