"""中文摘要：显式控制 vehicle-schedule BPC 搜索树。"""

from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import math
import time
from typing import Any

from .branching import BranchConstraint, generate_rf_candidates, schedule_allowed_by_branch
from .columns import ScheduleColumn, SchedulePool, Sortie
from .data import InstanceData
from .logger import BPCLogger
from .pricing import DSSRSchedulePricing
from .rmp import (
    RMPSolution,
    check_schedule_reduced_cost_consistency,
    manual_reduced_cost,
    solve_restricted_master_integer,
    solve_rmp_lp,
)
from .route_pool import SortieRoute, build_portfolio_routes, evaluate_sortie_route
from .schedule_dp import compose_schedules_heuristic


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
    phase_switch_count: int = 0
    pool_scan_columns_found: int = 0
    pool_scan_time: float = 0.0
    route_pool_size: int = 0
    low_cbar_routes_kept: int = 0
    per_task_routes_kept: int = 0
    route_size_bucket_routes_kept: int = 0
    time_flexible_routes_kept: int = 0
    micro_routes_kept: int = 0
    branch_relevant_routes_kept: int = 0
    historical_routes_kept: int = 0
    diverse_routes_kept: int = 0
    schedule_dp_labels_created: int = 0
    schedule_dp_labels_pruned_by_subset_dominance: int = 0
    schedule_dp_labels_pruned_by_beam: int = 0
    schedule_dp_negative_schedules_found: int = 0
    schedule_dp_calls: int = 0
    schedule_dp_exhausted: bool = True
    schedule_dp_best_rc: float | None = None
    schedule_dp_time: float = 0.0
    heuristic_degradation_skips: int = 0
    restricted_master_integer_calls: int = 0
    restricted_master_integer_feasible: int = 0
    restricted_master_integer_time: float = 0.0
    restricted_master_integer_best_objective: float | None = None
    exact_pricing_calls: int = 0
    exact_pricing_called: int = 0
    exact_pricing_exhausted: int = 0
    exact_pricing_best_rc: float | None = None
    exact_pricing_time: float = 0.0
    ng_dssr_max_ng_size: int = 0
    dssr_iterations: int = 0
    dssr_memory_size: int = 0
    dssr_non_elementary_negative: int = 0
    dssr_certificate_from_relaxation: int = 0
    full_memory_fallback_called: int = 0
    manual_rc_check_max_error: float = 0.0
    vehicle_lb_dual_effective_value: float = 0.0
    pricing_certificate_layer: str | None = None


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
        master_cover_mode: str,
        vehicle_lower_bound_cut_enabled: bool,
        schedule_column_pool_enabled: bool,
        max_schedule_pool_size: int,
        route_pool_pricing_enabled: bool,
        exact_pricing_fallback_enabled: bool,
        exact_pricing_required_for_certificate: bool,
        config: dict[str, Any],
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
        self.master_cover_mode = str(master_cover_mode)
        self.vehicle_lower_bound_cut_enabled = bool(vehicle_lower_bound_cut_enabled)
        self.schedule_column_pool_enabled = bool(schedule_column_pool_enabled)
        self.max_schedule_pool_size = int(max_schedule_pool_size)
        self.route_pool_pricing_enabled = bool(route_pool_pricing_enabled)
        self.exact_pricing_fallback_enabled = bool(exact_pricing_fallback_enabled)
        self.exact_pricing_required_for_certificate = bool(exact_pricing_required_for_certificate)
        self.config = dict(config)
        self.rmp_params = dict(rmp_params or {})
        self.logger = logger
        self.pool = SchedulePool()
        self.active_signatures: set[tuple[tuple[int, ...], ...]] = set()
        self.historical_routes: list[SortieRoute] = []
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
                self._add_to_pool_and_active(column)
        greedy = self._greedy_schedule_columns()
        if greedy is not None:
            for column in greedy:
                self._add_to_pool_and_active(column)
            self.incumbent = Incumbent(sum(column.cost for column in greedy), greedy, 0)
            self.logger.log("incumbent", node=0, objective=round(self.incumbent.objective, 6), source="greedy")

    def _current_columns(self) -> list[ScheduleColumn]:
        return [column for column in self.pool.columns if column.signature in self.active_signatures]

    def _add_to_pool(self, column: ScheduleColumn) -> ScheduleColumn | None:
        if len(self.pool.columns) >= self.max_schedule_pool_size and not self.pool.contains(column.signature):
            return None
        return self.pool.add(column)

    def _add_to_pool_and_active(self, column: ScheduleColumn, *, remember_history: bool = False) -> int:
        stored = self._add_to_pool(column)
        if stored is None:
            return 0
        if stored.signature in self.active_signatures:
            return 0
        self.active_signatures.add(stored.signature)
        if remember_history:
            self._remember_routes(stored)
        return 1

    def _remember_routes(self, column: ScheduleColumn) -> None:
        for sortie in column.sorties:
            route = SortieRoute(
                tasks=tuple(sortie.tasks),
                task_set=frozenset(sortie.tasks),
                cost=float(sortie.cost),
                ready_time_at_zero=float(sortie.ready_time),
                load=float(sortie.load),
                energy=float(sortie.energy),
                service_start_at_zero=dict(sortie.service_start),
            )
            if all(route.signature != old.signature for old in self.historical_routes):
                self.historical_routes.insert(0, route)
        limit = int(self.config.get("historical_route_quota", 300))
        if len(self.historical_routes) > limit:
            del self.historical_routes[limit:]

    def solve(self) -> TreeResult:
        self.initialize()
        self.logger.log(
            "start",
            instance=self.data.name,
            tasks=len(self.data.tasks),
            initial_columns=len(self._current_columns()),
            master_cover_mode=self.master_cover_mode,
        )
        root = SearchNode(priority=0.0, id=0, depth=0, lower_bound=0.0)
        open_nodes: list[SearchNode] = [root]
        heapq.heapify(open_nodes)
        best_dual: float | None = None
        status = "SEARCHING"

        while open_nodes and self._time_left() and self.stats.nodes < self.max_nodes:
            node = heapq.heappop(open_nodes)
            self.stats.nodes += 1
            self.logger.log("node", node=node.id, depth=node.depth, lower_bound=round(node.lower_bound, 6), open_nodes=len(open_nodes))
            solution, certified = self._solve_node_lp(node)
            if not certified:
                status = "TIME_LIMIT" if not self._time_left() else "PRICING_LIMIT"
                break
            if solution is None or not solution.optimal:
                self.logger.log("fathom", node=node.id, reason="infeasible_or_no_lp")
                continue
            node.lower_bound = float(solution.objective or 0.0)
            if node.id == 0:
                self.stats.root_relaxation = node.lower_bound
            best_dual = node.lower_bound if best_dual is None else min(best_dual, node.lower_bound)
            self._try_restricted_master_incumbent(node, self._current_columns(), source="node_certified")
            if self.incumbent is not None and node.lower_bound >= self.incumbent.objective - self.integer_tol:
                self.logger.log("fathom", node=node.id, reason="bound")
                continue
            if self._is_integral(solution):
                incumbent = self._incumbent_from_integral_solution(solution, node)
                if incumbent is None:
                    status = "COVERING_POSTPROCESS_FAILED"
                    self.logger.log("fathom", node=node.id, reason="covering_postprocess_failed")
                    break
                if self.incumbent is None or incumbent.objective < self.incumbent.objective - self.integer_tol:
                    self.incumbent = incumbent
                    self.logger.log("incumbent", node=node.id, objective=round(incumbent.objective, 6), source="integral_master")
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

        if not open_nodes and status == "SEARCHING":
            status = "OPTIMAL" if self.incumbent is not None else "INFEASIBLE"
        elif self.stats.nodes >= self.max_nodes:
            status = "NODE_LIMIT"
        elif status == "SEARCHING":
            status = "TIME_LIMIT"

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
            previous_objective: float | None = None
            previous_added_by_heuristic = False
            heuristic_stagnant_rounds = 0
            heuristic_degradation_enabled = bool(self.config.get("heuristic_degradation_detection_enabled", True))
            heuristic_degradation_max_stagnant = max(1, int(self.config.get("heuristic_degradation_max_stagnant_rounds", 2)))
            heuristic_degradation_min_improvement = float(self.config.get("heuristic_degradation_min_obj_improvement", 1.0e-6))
            while self._time_left():
                cg_iter += 1
                current_columns = self._current_columns()
                solution = solve_rmp_lp(
                    self.data,
                    current_columns,
                    node.branch_constraints,
                    phase=phase,
                    master_cover_mode=self.master_cover_mode,
                    vehicle_lower_bound_cut_enabled=self.vehicle_lower_bound_cut_enabled,
                    rmp_params=self.rmp_params,
                )
                self.stats.rmp_solves += 1
                if solution.max_reduced_cost_error is not None:
                    self.stats.manual_rc_check_max_error = max(
                        self.stats.manual_rc_check_max_error,
                        float(solution.max_reduced_cost_error),
                    )
                if solution.duals is not None:
                    self.stats.vehicle_lb_dual_effective_value = float(solution.duals.vehicle_lb)
                self.logger.log(
                    "rmp",
                    node=node.id,
                    phase=phase,
                    cg_iter=cg_iter,
                    objective=None if solution.objective is None else round(solution.objective, 6),
                    artificial=round(solution.artificial_sum, 6),
                    columns=len(current_columns),
                    master_cover_mode=self.master_cover_mode,
                    phase_switch_count=self.stats.phase_switch_count,
                    vehicle_lb_cut_enabled=self.vehicle_lower_bound_cut_enabled,
                    vehicle_lb_value=solution.vehicle_lower_bound_value,
                    vehicle_lb_dual_effective_value=None if solution.duals is None else round(solution.duals.vehicle_lb, 10),
                    manual_rc_check_max_error=None
                    if solution.max_reduced_cost_error is None
                    else round(solution.max_reduced_cost_error, 10),
                )
                if not solution.optimal:
                    return solution, True
                if solution.duals is None:
                    return solution, False
                current_objective = None if solution.objective is None else float(solution.objective)
                if (
                    heuristic_degradation_enabled
                    and phase == "phase2"
                    and previous_added_by_heuristic
                    and previous_objective is not None
                    and current_objective is not None
                ):
                    objective_improvement = previous_objective - current_objective
                    if objective_improvement <= heuristic_degradation_min_improvement:
                        heuristic_stagnant_rounds += 1
                    else:
                        heuristic_stagnant_rounds = 0
                previous_added_by_heuristic = False
                previous_objective = current_objective
                try:
                    check_schedule_reduced_cost_consistency(
                        solution,
                        tolerance=float(self.config.get("manual_rc_tolerance", 1.0e-6)),
                    )
                except AssertionError as exc:
                    self.logger.log("reduced_cost_check_failed", node=node.id, phase=phase, error=str(exc))
                    return solution, False

                if phase == "phase1" and solution.artificial_sum <= self.integer_tol:
                    self.stats.phase_switch_count += 1
                    self.logger.log(
                        "phase_switch",
                        node=node.id,
                        from_phase="phase1",
                        to_phase="phase2",
                        artificial=round(solution.artificial_sum, 10),
                        phase_switch_count=self.stats.phase_switch_count,
                        reason="phase1_artificial_zero",
                    )
                    break

                integer_interval = int(self.config.get("restricted_master_integer_cg_interval", 10) or 0)
                if phase == "phase2" and integer_interval > 0 and cg_iter % integer_interval == 0:
                    self._try_restricted_master_incumbent(node, current_columns, source=f"phase2_cg_{cg_iter}")

                pool_added = self._pool_scan(node, solution.duals, phase, current_columns)
                if pool_added:
                    if not self._time_left():
                        return solution, False
                    continue

                heuristic_added = 0
                heuristic_blocked = (
                    heuristic_degradation_enabled
                    and phase == "phase2"
                    and heuristic_stagnant_rounds >= heuristic_degradation_max_stagnant
                )
                if self.route_pool_pricing_enabled and heuristic_blocked:
                    self.stats.heuristic_degradation_skips += 1
                    self.logger.log(
                        "heuristic_degradation",
                        node=node.id,
                        phase=phase,
                        cg_iter=cg_iter,
                        objective=None if solution.objective is None else round(float(solution.objective), 6),
                        stagnant_rounds=heuristic_stagnant_rounds,
                        max_stagnant_rounds=heuristic_degradation_max_stagnant,
                        min_obj_improvement=heuristic_degradation_min_improvement,
                        action="skip_layer1_layer2_to_exact",
                    )
                if self.route_pool_pricing_enabled and not heuristic_blocked:
                    heuristic_added = self._heuristic_layers(node, solution.duals, node.branch_constraints, phase)
                    if heuristic_added:
                        previous_added_by_heuristic = True
                        if not self._time_left():
                            return solution, False
                        continue

                if not self.exact_pricing_fallback_enabled:
                    if self.exact_pricing_required_for_certificate:
                        return solution, False
                    self.stats.pricing_certificate_layer = "heuristic_only_nonexact"
                    return solution, True
                result, exact_added = self._exact_layer(node, solution.duals, node.branch_constraints, phase, cg_iter)
                if exact_added > 0:
                    heuristic_stagnant_rounds = 0
                    previous_added_by_heuristic = False
                    if bool(self.config.get("restricted_master_integer_after_exact_added", True)):
                        self._try_restricted_master_incumbent(node, self._current_columns(), source="after_exact_added")
                    continue
                if result.columns:
                    self.logger.log(
                        "exact_pricing_column_add_failed",
                        node=node.id,
                        phase=phase,
                        found=len(result.columns),
                        best_rc=None if result.best_reduced_cost is None else round(result.best_reduced_cost, 6),
                    )
                    return solution, False
                if not result.exhausted:
                    return solution, False
                if not result.certificate:
                    self.logger.log(
                        "exact_pricing_certificate_failed",
                        node=node.id,
                        phase=phase,
                        best_rc=None if result.best_reduced_cost is None else round(result.best_reduced_cost, 6),
                    )
                    return solution, False
                self.stats.pricing_certificate_layer = result.algorithm
                if phase == "phase1":
                    return None, True
                return solution, True
        return None, False

    def _pool_scan(self, node: SearchNode, duals, phase: str, current_columns: list[ScheduleColumn]) -> int:
        if not self.schedule_column_pool_enabled:
            return 0
        started = time.perf_counter()
        added = 0
        current_signatures = {column.signature for column in current_columns if schedule_allowed_by_branch(column, node.branch_constraints)}
        for column in self.pool.columns:
            if column.signature in current_signatures:
                continue
            if not schedule_allowed_by_branch(column, node.branch_constraints):
                continue
            rc = manual_reduced_cost(column, duals, phase)
            if rc < -self.eps:
                added += self._add_to_pool_and_active(column, remember_history=True)
                if added >= self.max_columns_per_pricing:
                    break
        elapsed = time.perf_counter() - started
        self.stats.pool_scan_columns_found += added
        self.stats.pool_scan_time += elapsed
        self.logger.log(
            "pool_scan",
            node=node.id,
            phase=phase,
            found=added,
            pool_scan_columns_found=added,
            pool_scan_time=round(elapsed, 6),
            elapsed=round(elapsed, 6),
        )
        return added

    def _heuristic_layers(
        self,
        node: SearchNode,
        duals,
        branch_constraints: tuple[BranchConstraint, ...],
        phase: str,
    ) -> int:
        route_result = build_portfolio_routes(
            self.data,
            duals,
            branch_constraints,
            self.historical_routes,
            self.config,
            phase=phase,
        )
        stats = route_result.stats
        self.stats.route_pool_size = max(self.stats.route_pool_size, stats.route_pool_size)
        self.stats.low_cbar_routes_kept += stats.low_cbar_routes_kept
        self.stats.per_task_routes_kept += stats.per_task_routes_kept
        self.stats.route_size_bucket_routes_kept += stats.route_size_bucket_routes_kept
        self.stats.time_flexible_routes_kept += stats.time_flexible_routes_kept
        self.stats.micro_routes_kept += stats.micro_routes_kept
        self.stats.branch_relevant_routes_kept += stats.branch_relevant_routes_kept
        self.stats.historical_routes_kept += stats.historical_routes_kept
        self.stats.diverse_routes_kept += stats.diverse_routes_kept
        self.logger.log(
            "route_pool",
            node=node.id,
            phase=phase,
            route_pool_size=stats.route_pool_size,
            low_cbar=stats.low_cbar_routes_kept,
            low_cbar_routes_kept=stats.low_cbar_routes_kept,
            per_task=stats.per_task_routes_kept,
            per_task_routes_kept=stats.per_task_routes_kept,
            route_size_bucket=stats.route_size_bucket_routes_kept,
            route_size_bucket_routes_kept=stats.route_size_bucket_routes_kept,
            time_flexible=stats.time_flexible_routes_kept,
            time_flexible_routes_kept=stats.time_flexible_routes_kept,
            micro=stats.micro_routes_kept,
            micro_routes_kept=stats.micro_routes_kept,
            branch_relevant=stats.branch_relevant_routes_kept,
            branch_relevant_routes_kept=stats.branch_relevant_routes_kept,
            historical=stats.historical_routes_kept,
            historical_routes_kept=stats.historical_routes_kept,
            diverse=stats.diverse_routes_kept,
            diverse_routes_kept=stats.diverse_routes_kept,
        )
        dp_seconds = float(self.config.get("schedule_dp_max_seconds", 0.0) or 0.0)
        pricing_seconds = self.max_pricing_seconds if self.max_pricing_seconds > 0 else self._remaining_time()
        if dp_seconds > 0:
            pricing_seconds = min(pricing_seconds, dp_seconds)
        dp_result = compose_schedules_heuristic(
            self.data,
            route_result.routes,
            duals,
            branch_constraints,
            self.config,
            phase=phase,
            eps=self.eps,
            max_seconds=min(pricing_seconds, self._remaining_time()),
        )
        dp = dp_result.stats
        self.stats.schedule_dp_calls += 1
        self.stats.schedule_dp_labels_created += dp.labels_created
        self.stats.schedule_dp_labels_pruned_by_subset_dominance += dp.labels_pruned_by_subset_dominance
        self.stats.schedule_dp_labels_pruned_by_beam += dp.labels_pruned_by_beam
        self.stats.schedule_dp_negative_schedules_found += dp.negative_schedules_found
        self.stats.schedule_dp_exhausted = self.stats.schedule_dp_exhausted and bool(dp.exhausted)
        self.stats.schedule_dp_time += float(dp.elapsed)
        if dp.best_rc is not None:
            self.stats.schedule_dp_best_rc = dp.best_rc if self.stats.schedule_dp_best_rc is None else min(self.stats.schedule_dp_best_rc, dp.best_rc)
        added = 0
        for column in dp_result.columns:
            rc = manual_reduced_cost(column, duals, phase)
            if rc < -self.eps and schedule_allowed_by_branch(column, branch_constraints):
                added += self._add_to_pool_and_active(column, remember_history=True)
        self.stats.generated_columns += added
        self.logger.log(
            "schedule_dp",
            node=node.id,
            phase=phase,
            labels=dp.labels_created,
            schedule_dp_labels_created=dp.labels_created,
            pruned_subset=dp.labels_pruned_by_subset_dominance,
            schedule_dp_labels_pruned_by_subset_dominance=dp.labels_pruned_by_subset_dominance,
            pruned_beam=dp.labels_pruned_by_beam,
            schedule_dp_labels_pruned_by_beam=dp.labels_pruned_by_beam,
            exhausted=dp.exhausted,
            schedule_dp_exhausted=dp.exhausted,
            early_stopped=dp.early_stopped,
            schedule_dp_early_stopped=dp.early_stopped,
            found=dp.negative_schedules_found,
            schedule_dp_negative_schedules_found=dp.negative_schedules_found,
            added=added,
            best_rc=None if dp.best_rc is None else round(dp.best_rc, 6),
            schedule_dp_best_rc=None if dp.best_rc is None else round(dp.best_rc, 6),
            schedule_dp_time=round(dp.elapsed, 6),
            elapsed=round(dp.elapsed, 6),
        )
        return added

    def _exact_layer(
        self,
        node: SearchNode,
        duals,
        branch_constraints: tuple[BranchConstraint, ...],
        phase: str,
        cg_iter: int,
    ):
        started = time.perf_counter()

        def progress_callback(payload: dict[str, object]) -> None:
            algorithm = str(payload.pop("algorithm", "dssr_full_memory_exact"))
            self.logger.log(
                "exact_pricing_progress",
                node=node.id,
                phase=phase,
                cg_iter=cg_iter,
                algorithm=algorithm,
                **payload,
            )

        pricing = DSSRSchedulePricing(
            self.data,
            self.pool.columns,
            eps=self.eps,
            max_columns_to_return=self.max_columns_per_pricing,
            max_labels=int(self.config.get("max_labels_per_exact_pricing", self.max_labels_per_pricing) or 0),
            max_generated_labels=self.max_generated_labels_per_pricing,
            max_queue_size=self.max_queue_size_per_pricing,
            max_candidate_pool=self.max_candidate_pool_per_pricing,
            max_seconds=min(self.max_pricing_seconds, self._remaining_time()) if self.max_pricing_seconds > 0 else self._remaining_time(),
            max_memory_mb=float(self.config.get("max_pricing_memory_mb", 0.0) or 0.0),
            memory_check_interval=int(self.config.get("pricing_memory_check_interval", 4096) or 4096),
            enable_dominance=bool(self.config.get("exact_pricing_enable_dominance", True)),
            relaxed_memory_enabled=bool(self.config.get("dssr_relaxed_memory_enabled", True)),
            relaxed_initial_memory_size=int(self.config.get("dssr_initial_memory_size", 0) or 0),
            relaxed_max_iterations=int(self.config.get("dssr_max_iterations", 4) or 4),
            relaxed_memory_growth=int(self.config.get("dssr_memory_growth", 4) or 4),
            relaxed_iteration_seconds=float(self.config.get("dssr_relaxed_iteration_seconds", 30.0) or 0.0),
            relaxed_max_labels=int(self.config.get("dssr_relaxed_max_labels", 500000) or 0),
            progress_callback=progress_callback,
            progress_interval_seconds=float(self.config.get("exact_pricing_progress_interval_seconds", 30.0) or 0.0),
            progress_label_interval=int(self.config.get("exact_pricing_progress_label_interval", 500000) or 0),
            exact_pricing_algorithm=str(self.config.get("exact_pricing_algorithm", "ng_dssr")),
            full_memory_fallback_enabled=bool(self.config.get("full_memory_fallback_enabled", False)),
            ng_neighborhood_size=int(self.config.get("ng_neighborhood_size", 8) or 8),
            ng_include_time_compatible=bool(self.config.get("ng_include_time_compatible", True)),
            ng_include_branch_components=bool(self.config.get("ng_include_branch_components", True)),
            dssr_certificate_without_full_memory=bool(self.config.get("dssr_certificate_without_full_memory", True)),
        )
        result = pricing.run(duals, branch_constraints, phase=phase)
        elapsed = time.perf_counter() - started
        self.stats.pricing_calls += 1
        self.stats.exact_pricing_calls += 1
        self.stats.exact_pricing_called += 1
        self.stats.exact_pricing_time += elapsed
        self.stats.label_pops += result.label_pops
        self.stats.generated_labels += result.generated_labels
        self.stats.pricing_queue_peak = max(self.stats.pricing_queue_peak, result.queue_peak)
        self.stats.ng_dssr_max_ng_size = max(self.stats.ng_dssr_max_ng_size, result.ng_size)
        self.stats.dssr_iterations += result.dssr_iterations
        self.stats.dssr_memory_size = max(self.stats.dssr_memory_size, result.dssr_memory_size)
        self.stats.dssr_non_elementary_negative += result.dssr_non_elementary_negative
        self.stats.dssr_certificate_from_relaxation += int(result.certificate_from_relaxation)
        self.stats.full_memory_fallback_called += int(result.full_memory_fallback_called)
        if result.exhausted:
            self.stats.exact_pricing_exhausted += 1
        if result.best_reduced_cost is not None:
            self.stats.exact_pricing_best_rc = result.best_reduced_cost if self.stats.exact_pricing_best_rc is None else min(self.stats.exact_pricing_best_rc, result.best_reduced_cost)
        added = 0
        for column in result.columns:
            if manual_reduced_cost(column, duals, phase) < -self.eps and schedule_allowed_by_branch(column, branch_constraints):
                added += self._add_to_pool_and_active(column, remember_history=True)
        self.stats.generated_columns += added
        self.logger.log(
            "exact_pricing",
            node=node.id,
            phase=phase,
            cg_iter=cg_iter,
            best_rc=None if result.best_reduced_cost is None else round(result.best_reduced_cost, 6),
            found=len(result.columns),
            added=added,
            exact_pricing_called=True,
            exhausted=result.exhausted,
            exact_pricing_exhausted=result.exhausted,
            labels=result.label_pops,
            generated_labels=result.generated_labels,
            queue_peak=result.queue_peak,
            stop_reason=result.stop_reason,
            certificate=result.certificate,
            algorithm=result.algorithm,
            ng_size=result.ng_size,
            dssr_iterations=result.dssr_iterations,
            dssr_memory_size=result.dssr_memory_size,
            dssr_non_elementary_negative=result.dssr_non_elementary_negative,
            non_elementary_negative_count=result.dssr_non_elementary_negative,
            certificate_from_relaxation=result.certificate_from_relaxation,
            full_memory_fallback_called=result.full_memory_fallback_called,
            labels_pruned_by_dominance=result.labels_pruned_by_dominance,
            memory_peak_mb=result.memory_peak_mb,
            exact_pricing_best_rc=None if result.best_reduced_cost is None else round(result.best_reduced_cost, 6),
            exact_pricing_time=round(elapsed, 6),
            elapsed=round(elapsed, 6),
        )
        return result, added

    def _try_restricted_master_incumbent(
        self,
        node: SearchNode,
        columns: list[ScheduleColumn],
        *,
        source: str,
    ) -> Incumbent | None:
        if not bool(self.config.get("restricted_master_integer_enabled", True)):
            return None
        if not self._time_left():
            return None
        time_limit = float(self.config.get("restricted_master_integer_time_limit", 5.0) or 0.0)
        if time_limit > 0.0:
            time_limit = min(time_limit, self._remaining_time())
            if time_limit <= 1.0e-6:
                return None

        started = time.perf_counter()
        solution = solve_restricted_master_integer(
            self.data,
            columns,
            node.branch_constraints,
            master_cover_mode=self.master_cover_mode,
            vehicle_lower_bound_cut_enabled=self.vehicle_lower_bound_cut_enabled,
            time_limit=time_limit,
            rmp_params=self.rmp_params,
        )
        elapsed = time.perf_counter() - started
        self.stats.restricted_master_integer_calls += 1
        self.stats.restricted_master_integer_time += elapsed
        if solution.feasible:
            self.stats.restricted_master_integer_feasible += 1
            objective = float(solution.objective or sum(column.cost for column in solution.selected_columns))
            self.stats.restricted_master_integer_best_objective = (
                objective
                if self.stats.restricted_master_integer_best_objective is None
                else min(self.stats.restricted_master_integer_best_objective, objective)
            )
        self.logger.log(
            "restricted_master_integer",
            node=node.id,
            source=source,
            status=solution.status,
            feasible=solution.feasible,
            objective=None if solution.objective is None else round(float(solution.objective), 6),
            selected=len(solution.selected_columns),
            variables=solution.variable_count,
            constraints=solution.constraint_count,
            elapsed=round(elapsed, 6),
        )
        if not solution.feasible:
            return None

        incumbent = self._incumbent_from_selected_columns(
            solution.selected_columns,
            node,
            objective=float(solution.objective or sum(column.cost for column in solution.selected_columns)),
        )
        if incumbent is None:
            self.logger.log("restricted_master_integer_rejected", node=node.id, source=source, reason="postprocess_failed")
            return None
        if self.incumbent is None or incumbent.objective < self.incumbent.objective - self.integer_tol:
            self.incumbent = incumbent
            self.logger.log(
                "incumbent",
                node=node.id,
                objective=round(incumbent.objective, 6),
                source=f"restricted_master_integer:{source}",
            )
        return incumbent

    def _incumbent_from_integral_solution(self, solution: RMPSolution, node: SearchNode) -> Incumbent | None:
        selected = [column for column, value in solution.schedule_values if value > 1.0 - self.integer_tol]
        return self._incumbent_from_selected_columns(
            selected,
            node,
            objective=float(solution.objective or sum(column.cost for column in selected)),
        )

    def _incumbent_from_selected_columns(
        self,
        selected: list[ScheduleColumn],
        node: SearchNode,
        *,
        objective: float,
    ) -> Incumbent | None:
        if self.master_cover_mode == "covering":
            return self._postprocess_covering_incumbent(selected, node)
        if len(selected) > self.data.vehicle_count:
            return None
        if not all(schedule_allowed_by_branch(column, node.branch_constraints) for column in selected):
            return None
        counts = {int(task): 0 for task in self.data.tasks}
        for column in selected:
            for task in column.task_set:
                if int(task) in counts:
                    counts[int(task)] += 1
        if any(value != 1 for value in counts.values()):
            return None
        return Incumbent(float(objective), selected, node.id)

    def _postprocess_covering_incumbent(self, selected: list[ScheduleColumn], node: SearchNode) -> Incumbent | None:
        if not self._covering_shortcut_assumptions_hold():
            self.logger.log("covering_postprocess", node=node.id, accepted=False, reason="shortcut_assumption_failed")
            return None
        served: set[int] = set()
        rebuilt: list[ScheduleColumn] = []
        for column in selected:
            new_sorties: list[Sortie] = []
            task_set: set[int] = set()
            variable_cost = 0.0
            ready_time = 0.0
            for sortie in column.sorties:
                tasks = tuple(int(task) for task in sortie.tasks if int(task) not in served and int(task) not in task_set)
                if not tasks:
                    continue
                rebuilt_sortie = evaluate_sortie_route(self.data, tasks, ready_time)
                if rebuilt_sortie is None:
                    return None
                new_sorties.append(rebuilt_sortie)
                task_set.update(tasks)
                variable_cost += float(rebuilt_sortie.cost)
                ready_time = float(rebuilt_sortie.ready_time)
            if not new_sorties:
                continue
            rebuilt_column = ScheduleColumn(
                id=-1,
                sorties=tuple(new_sorties),
                task_set=frozenset(task_set),
                cost=round(self.data.fixed_vehicle_cost + variable_cost, 6),
                variable_cost=round(variable_cost, 6),
                ready_time=round(ready_time, 6),
            )
            if not schedule_allowed_by_branch(rebuilt_column, node.branch_constraints):
                return None
            rebuilt.append(rebuilt_column)
            served.update(task_set)

        if served != set(self.data.tasks) or len(rebuilt) > self.data.vehicle_count:
            return None
        counts = {task: 0 for task in self.data.tasks}
        for column in rebuilt:
            for task in column.task_set:
                counts[int(task)] = counts.get(int(task), 0) + 1
        if any(value != 1 for value in counts.values()):
            return None

        stored_columns: list[ScheduleColumn] = []
        for column in rebuilt:
            self._add_to_pool_and_active(column)
            stored_columns.append(self.pool.by_signature.get(column.signature, column))
        self.logger.log(
            "covering_postprocess",
            node=node.id,
            accepted=True,
            schedules=len(stored_columns),
            objective=round(sum(float(column.cost) for column in stored_columns), 6),
        )
        return Incumbent(sum(float(column.cost) for column in stored_columns), stored_columns, node.id)

    def _covering_shortcut_assumptions_hold(self) -> bool:
        tol = 1.0e-9
        if any(self.data.task_value(task, "c_srv") < -tol for task in self.data.tasks):
            return False
        nodes = (0, *self.data.tasks)
        for i in nodes:
            for k in self.data.tasks:
                if k == i:
                    continue
                for j in nodes:
                    if j == i or j == k:
                        continue
                    direct = self.data.arc(i, j)
                    left = self.data.arc(i, k)
                    right = self.data.arc(k, j)
                    if float(direct["cost"]) > float(left["cost"]) + float(right["cost"]) + tol:
                        return False
                    if float(direct["tau"]) > float(left["tau"]) + float(right["tau"]) + tol:
                        return False
                    if float(direct["energy"]) > float(left["energy"]) + float(right["energy"]) + tol:
                        return False
        return True

    def _is_integral(self, solution: RMPSolution) -> bool:
        return all(
            value <= self.integer_tol or value >= 1.0 - self.integer_tol
            for _column, value in solution.schedule_values
        )

    def _choose_branch(self, solution: RMPSolution):
        candidates = generate_rf_candidates(self.data.tasks, solution.schedule_values, self.integer_tol)
        if not candidates:
            return None
        same_sortie_score: dict[tuple[int, int], float] = {}
        cross_sortie_score: dict[tuple[int, int], float] = {}
        for column, value in solution.schedule_values:
            if value <= self.integer_tol:
                continue
            for sortie in column.sorties:
                tasks = sorted(int(task) for task in sortie.tasks)
                for left_index, i in enumerate(tasks):
                    for j in tasks[left_index + 1 :]:
                        same_sortie_score[(i, j)] = same_sortie_score.get((i, j), 0.0) + float(value)
            ordered = sorted(column.task_set)
            for left_index, i in enumerate(ordered):
                for j in ordered[left_index + 1 :]:
                    cross_sortie_score[(int(i), int(j))] = cross_sortie_score.get((int(i), int(j)), 0.0) + float(value)

        return max(
            candidates,
            key=lambda item: (
                item.fractionality,
                same_sortie_score.get((item.i, item.j), 0.0),
                cross_sortie_score.get((item.i, item.j), 0.0),
                -item.i,
                -item.j,
            ),
        )

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
