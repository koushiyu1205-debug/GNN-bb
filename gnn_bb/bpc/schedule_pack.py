"""中文摘要：本文件提供 candidate-pool schedule-pack 诊断和浅层节点 relaxation。

schedule-pack 默认只用于判断当前 route pool 能否形成更强的完整车辆 schedule master。
候选池收敛、超时或状态上限触发时，生成的 schedule columns 只作为诊断和节点排序信号；
只有当 full route-space schedule pricing 完整结束并返回 exact_over_full_route_space=True 时，
对应 LP 值才允许接入 clean BPC 的正式节点下界、剪枝和最优性证明。
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import Any

from .branching import BranchConstraint, partial_sequence_allowed, route_allowed_by_branch, route_branch_coefficient
from .columns import RouteColumn, evaluate_route
from .cuts import Cut
from .data import BPCData
from .validation import check_route_set_schedule_feasible, evaluate_route_at_start


_DUAL_ABS_LIMIT = 1.0e12


@dataclass(frozen=True)
class SchedulePackColumn:
    id: int
    route_signatures: tuple[tuple[int, ...], ...]
    tasks: tuple[int, ...]
    route_count: int
    variable_cost: float
    fixed_cost: float
    cost: float
    ready_time: float


@dataclass(frozen=True)
class SchedulePackDiagnosticResult:
    status: str
    objective: float | None
    column_count: int
    candidate_route_count: int
    generated_state_count: int
    skipped_duplicate_columns: int
    skipped_infeasible_extensions: int
    single_route_columns: int
    multi_route_columns: int
    max_route_count: int
    max_task_count: int
    solving_time: float
    pricing_iterations: int = 0
    generated_pricing_columns: int = 0
    best_reduced_cost: float | None = None
    exact_over_candidate_routes: bool = False
    seed_columns: int = 0
    exact_over_full_route_space: bool = False
    full_pricing_generated_states: int = 0
    full_pricing_route_count: int = 0
    full_pricing_time: float = 0.0


@dataclass(frozen=True)
class _ScheduleState:
    route_indices: tuple[int, ...]
    tasks: frozenset[int]
    ready_time: float
    variable_cost: float


@dataclass(frozen=True)
class _ScheduleLPResult:
    objective: float | None
    status: str
    cover_duals: dict[int, float]
    fleet_dual: float


@dataclass(frozen=True)
class _VehicleScheduleLPResult:
    objective: float | None
    status: str
    cover_duals: dict[int, float]
    schedule_duals: dict[int, float]
    cut_duals: dict[int, float]
    branch_duals: dict[int, float]


@dataclass(frozen=True)
class _PricingResult:
    state: _ScheduleState | None
    best_reduced_cost: float | None
    generated_states: int
    skipped_infeasible_extensions: int
    exact: bool


@dataclass(frozen=True)
class _BatchPricingResult:
    states: tuple[tuple[_ScheduleState, float], ...]
    best_reduced_cost: float | None
    generated_states: int
    skipped_infeasible_extensions: int
    exact: bool


@dataclass(frozen=True)
class _FullPricingResult:
    routes: tuple[RouteColumn, ...] | None
    best_reduced_cost: float | None
    generated_states: int
    skipped_infeasible_extensions: int
    route_count: int
    exact: bool
    solving_time: float


@dataclass(frozen=True)
class _FullScheduleLabel:
    routes: tuple[RouteColumn, ...]
    tasks: frozenset[int]
    used_mask: int
    ready_time: float
    variable_cost: float
    reduced_component: float


class _SchedulePackCoefficientCache:
    def __init__(self, data: BPCData) -> None:
        self.task_to_bit = {int(task): 1 << index for index, task in enumerate(data.tasks)}
        self.route_masks: dict[tuple[int, ...], int] = {}
        self.route_cut_coefficients: dict[tuple[tuple[int, ...], int, int], float] = {}
        self.route_branch_coefficients: dict[tuple[tuple[int, ...], int, int], float] = {}

    def route_mask(self, route: RouteColumn) -> int:
        cached = self.route_masks.get(route.signature)
        if cached is not None:
            return cached
        mask = 0
        for task in route.task_set:
            mask |= self.task_to_bit[int(task)]
        self.route_masks[route.signature] = mask
        return mask

    def cut_coefficient(self, route: RouteColumn, vehicle: int, cut: Cut) -> float:
        key = (route.signature, int(vehicle), int(cut.id))
        cached = self.route_cut_coefficients.get(key)
        if cached is not None:
            return cached
        coefficient = float(cut.coefficient(route, int(vehicle)))
        self.route_cut_coefficients[key] = coefficient
        return coefficient

    def branch_coefficient(
        self,
        route: RouteColumn,
        vehicle: int,
        constraint_index: int,
        constraint: BranchConstraint,
    ) -> float:
        key = (route.signature, int(vehicle), int(constraint_index))
        cached = self.route_branch_coefficients.get(key)
        if cached is not None:
            return cached
        coefficient = float(route_branch_coefficient(route, int(vehicle), constraint))
        self.route_branch_coefficients[key] = coefficient
        return coefficient


def solve_schedule_pack_restricted_lp(
    data: BPCData,
    routes: list[RouteColumn],
    *,
    support_values: dict[tuple[int, ...], float] | None = None,
    seed_schedules: list[list[RouteColumn]] | tuple[tuple[RouteColumn, ...], ...] | None = None,
    max_candidate_routes: int = 180,
    max_columns: int = 8000,
    beam_width: int = 800,
    max_sorties: int = 0,
    time_limit: float = 60.0,
    rmp_params: dict[str, Any] | None = None,
) -> SchedulePackDiagnosticResult:
    """解一个 restricted schedule-pack LP 诊断。

    中文注释：该 LP 只使用候选 route 集合生成完整车辆 schedule columns，并在该
    候选集合内做 reduced-cost schedule pricing。由于候选 route 仍可被截断，它不是
    原问题的有效 lower bound，只能作为判断 schedule-pack master 是否值得继续开发
    的诊断值。
    """

    started = time.perf_counter()
    support = support_values or {}
    seed_route_map: dict[tuple[int, ...], RouteColumn] = {}
    for schedule in seed_schedules or []:
        for route in schedule:
            seed_route_map[route.signature] = route
    candidate_routes = _select_candidate_routes(data, routes, support, max_candidate_routes, seed_route_map)
    deadline = started + max(0.0, float(time_limit)) if time_limit > 0 else None
    columns, generated_states, skipped_duplicate, skipped_infeasible, seed_columns = _generate_schedule_columns(
        data,
        candidate_routes,
        seed_schedules=seed_schedules,
        max_columns=max_columns,
        beam_width=beam_width,
        max_sorties=max_sorties,
        deadline=deadline,
    )
    if not columns:
        return SchedulePackDiagnosticResult(
            status="NO_COLUMNS",
            objective=None,
            column_count=0,
            candidate_route_count=len(candidate_routes),
            generated_state_count=generated_states,
            skipped_duplicate_columns=skipped_duplicate,
            skipped_infeasible_extensions=skipped_infeasible,
            single_route_columns=0,
            multi_route_columns=0,
            max_route_count=0,
            max_task_count=0,
            solving_time=time.perf_counter() - started,
            seed_columns=seed_columns,
        )

    covered_tasks = set().union(*(set(column.tasks) for column in columns))
    if any(int(task) not in covered_tasks for task in data.tasks):
        return _result_without_objective(
            "NO_COVER",
            columns,
            len(candidate_routes),
            generated_states,
            skipped_duplicate,
            skipped_infeasible,
            started,
        )

    lp_result = _solve_lp(data, columns, max(0.001, _remaining(deadline)), rmp_params or {})
    pricing_iterations = 0
    generated_pricing_columns = 0
    best_reduced_cost: float | None = None
    exact_over_candidate_routes = False
    status = lp_result.status
    objective = lp_result.objective

    column_keys = {_column_key(column.route_signatures) for column in columns}
    while (
        status == "OPTIMAL"
        and objective is not None
        and not _expired(deadline)
        and len(columns) < max(1, int(max_columns))
    ):
        pricing_iterations += 1
        priced = _price_best_schedule_column(
            data,
            candidate_routes,
            cover_duals=lp_result.cover_duals,
            fleet_dual=lp_result.fleet_dual,
            existing_keys=column_keys,
            max_sorties=max_sorties,
            deadline=deadline,
        )
        generated_states += priced.generated_states
        skipped_infeasible += priced.skipped_infeasible_extensions
        best_reduced_cost = priced.best_reduced_cost
        if not priced.exact:
            status = "PRICING_TIME_LIMIT"
            break
        if priced.state is None or priced.best_reduced_cost is None or priced.best_reduced_cost >= -1.0e-7:
            exact_over_candidate_routes = True
            break

        column = _column_from_state(data, candidate_routes, priced.state, len(columns))
        key = _column_key(column.route_signatures)
        if key in column_keys:
            exact_over_candidate_routes = True
            break
        columns.append(column)
        column_keys.add(key)
        generated_pricing_columns += 1
        lp_result = _solve_lp(data, columns, max(0.001, _remaining(deadline)), rmp_params or {})
        status = lp_result.status
        objective = lp_result.objective

    if len(columns) >= max(1, int(max_columns)) and not exact_over_candidate_routes and status == "OPTIMAL":
        status = "COLUMN_LIMIT"

    return SchedulePackDiagnosticResult(
        status=status,
        objective=objective,
        column_count=len(columns),
        candidate_route_count=len(candidate_routes),
        generated_state_count=generated_states,
        skipped_duplicate_columns=skipped_duplicate,
        skipped_infeasible_extensions=skipped_infeasible,
        single_route_columns=sum(1 for column in columns if column.route_count == 1),
        multi_route_columns=sum(1 for column in columns if column.route_count > 1),
        max_route_count=max(column.route_count for column in columns),
        max_task_count=max(len(column.tasks) for column in columns),
        solving_time=time.perf_counter() - started,
        pricing_iterations=pricing_iterations,
        generated_pricing_columns=generated_pricing_columns,
        best_reduced_cost=best_reduced_cost,
        exact_over_candidate_routes=exact_over_candidate_routes,
        seed_columns=seed_columns,
    )


def solve_schedule_pack_node_relaxation(
    data: BPCData,
    routes: list[RouteColumn],
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    support_values: dict[tuple[int, ...], float] | None = None,
    seed_schedules: list[list[RouteColumn]] | tuple[tuple[RouteColumn, ...], ...] | None = None,
    max_candidate_routes: int = 180,
    max_columns: int = 8000,
    beam_width: int = 800,
    max_sorties: int = 0,
    time_limit: float = 60.0,
    pricing_batch_size: int = 32,
    full_route_space_pricing: bool = False,
    full_pricing_max_states: int = 0,
    rmp_params: dict[str, Any] | None = None,
) -> SchedulePackDiagnosticResult:
    """解当前节点上的 candidate-pool schedule-pack relaxation。

    中文注释：该模型使用 vehicle-indexed schedule columns，尊重当前节点分支约束
    和已有 valid cuts。它只在候选 route 集合内做 pricing；因此可作为候选池松弛
    诊断和节点排序信号，但不是原问题 exact lower bound。
    """

    started = time.perf_counter()
    support = support_values or {}
    seed_route_map: dict[tuple[int, ...], RouteColumn] = {}
    for schedule in seed_schedules or []:
        for route in schedule:
            seed_route_map[route.signature] = route
    candidate_routes = _select_candidate_routes(data, routes, support, max_candidate_routes, seed_route_map)
    deadline = started + max(0.0, float(time_limit)) if time_limit > 0 else None
    columns, generated_states, skipped_duplicate, skipped_infeasible, seed_columns = _generate_schedule_columns(
        data,
        candidate_routes,
        seed_schedules=seed_schedules,
        max_columns=max_columns,
        beam_width=beam_width,
        max_sorties=max_sorties,
        deadline=deadline,
    )
    if not columns:
        return SchedulePackDiagnosticResult(
            status="NO_COLUMNS",
            objective=None,
            column_count=0,
            candidate_route_count=len(candidate_routes),
            generated_state_count=generated_states,
            skipped_duplicate_columns=skipped_duplicate,
            skipped_infeasible_extensions=skipped_infeasible,
            single_route_columns=0,
            multi_route_columns=0,
            max_route_count=0,
            max_task_count=0,
            solving_time=time.perf_counter() - started,
            seed_columns=seed_columns,
        )

    covered_tasks = set().union(*(set(column.tasks) for column in columns))
    if any(int(task) not in covered_tasks for task in data.tasks):
        return _result_without_objective(
            "NO_COVER",
            columns,
            len(candidate_routes),
            generated_states,
            skipped_duplicate,
            skipped_infeasible,
            started,
        )

    coefficient_cache = _SchedulePackCoefficientCache(data)
    rmp_config = rmp_params or {}

    def build_rmp() -> _VehicleIndexedSchedulePackRMP:
        return _VehicleIndexedSchedulePackRMP(
            data,
            candidate_routes,
            columns,
            cuts,
            branch_constraints,
            rmp_config,
            coefficient_cache=coefficient_cache,
        )

    rmp = build_rmp()

    def solve_current_rmp(time_limit: float) -> _VehicleScheduleLPResult:
        nonlocal rmp
        result = rmp.solve(time_limit)
        if result.status == "DUAL_UNAVAILABLE" and not _expired(deadline):
            rmp = build_rmp()
            result = rmp.solve(time_limit)
        return result

    lp_result = solve_current_rmp(max(0.001, _remaining(deadline)))
    pricing_iterations = 0
    generated_pricing_columns = 0
    best_reduced_cost: float | None = None
    exact_over_candidate_routes = False
    exact_over_full_route_space = False
    full_pricing_generated_states = 0
    full_pricing_route_count = 0
    full_pricing_time = 0.0
    status = lp_result.status
    objective = lp_result.objective

    column_keys = {_column_key(column.route_signatures) for column in columns}
    while (
        status == "OPTIMAL"
        and objective is not None
        and not _expired(deadline)
        and len(columns) < max(1, int(max_columns))
    ):
        pricing_iterations += 1
        priced_columns: list[tuple[float, _ScheduleState]] = []
        batch_limit = max(1, int(pricing_batch_size))
        round_best_reduced_cost: float | None = None
        for vehicle in data.vehicles:
            priced = _price_vehicle_schedule_columns_batch(
                data,
                candidate_routes,
                int(vehicle),
                cuts,
                branch_constraints,
                cover_duals=lp_result.cover_duals,
                schedule_dual=float(lp_result.schedule_duals.get(int(vehicle), 0.0)),
                cut_duals=lp_result.cut_duals,
                branch_duals=lp_result.branch_duals,
                existing_keys=column_keys,
                max_sorties=max_sorties,
                deadline=deadline,
                batch_size=batch_limit,
                coefficient_cache=coefficient_cache,
            )
            generated_states += priced.generated_states
            skipped_infeasible += priced.skipped_infeasible_extensions
            if priced.best_reduced_cost is not None:
                if round_best_reduced_cost is None or priced.best_reduced_cost < round_best_reduced_cost:
                    round_best_reduced_cost = priced.best_reduced_cost
            if not priced.exact:
                status = "PRICING_TIME_LIMIT"
                break
            priced_columns.extend((float(reduced_cost), state) for state, reduced_cost in priced.states)
        best_reduced_cost = round_best_reduced_cost
        if status == "PRICING_TIME_LIMIT":
            break
        priced_columns.sort(key=lambda item: (item[0], _state_rank(item[1])))
        new_columns: list[SchedulePackColumn] = []
        added_this_round = 0
        for _reduced_cost, state in priced_columns[:batch_limit]:
            if len(columns) + len(new_columns) >= max(1, int(max_columns)):
                break
            column = _column_from_state(data, candidate_routes, state, len(columns) + len(new_columns))
            key = _column_key(column.route_signatures)
            if key in column_keys:
                continue
            new_columns.append(column)
            column_keys.add(key)
            added_this_round += 1
        if added_this_round > 0:
            columns.extend(new_columns)
            rmp.add_columns(new_columns)
            generated_pricing_columns += added_this_round
            lp_result = solve_current_rmp(max(0.001, _remaining(deadline)))
            status = lp_result.status
            objective = lp_result.objective
            continue

        if round_best_reduced_cost is None or round_best_reduced_cost >= -1.0e-7:
            exact_over_candidate_routes = True
            if not full_route_space_pricing:
                break
            best_full_pricing: _FullPricingResult | None = None
            full_pricing_incomplete = False
            for vehicle in data.vehicles:
                full_priced = _price_best_vehicle_schedule_column_full_route_space(
                    data,
                    int(vehicle),
                    cuts,
                    branch_constraints,
                    cover_duals=lp_result.cover_duals,
                    schedule_dual=float(lp_result.schedule_duals.get(int(vehicle), 0.0)),
                    cut_duals=lp_result.cut_duals,
                    branch_duals=lp_result.branch_duals,
                    existing_keys=column_keys,
                    max_sorties=max_sorties,
                    deadline=deadline,
                    max_states=full_pricing_max_states,
                    coefficient_cache=coefficient_cache,
                )
                full_pricing_generated_states += full_priced.generated_states
                generated_states += full_priced.generated_states
                skipped_infeasible += full_priced.skipped_infeasible_extensions
                full_pricing_route_count = max(full_pricing_route_count, full_priced.route_count)
                full_pricing_time += full_priced.solving_time
                if best_full_pricing is None or (
                    full_priced.best_reduced_cost is not None
                    and (
                        best_full_pricing.best_reduced_cost is None
                        or full_priced.best_reduced_cost < best_full_pricing.best_reduced_cost
                    )
                ):
                    best_full_pricing = full_priced
                if not full_priced.exact:
                    full_pricing_incomplete = True
                    if (
                        full_priced.routes is None
                        or full_priced.best_reduced_cost is None
                        or full_priced.best_reduced_cost >= -1.0e-7
                    ):
                        status = "FULL_PRICING_TIME_LIMIT"
                    break
            if best_full_pricing is None:
                exact_over_full_route_space = True
                break
            best_reduced_cost = best_full_pricing.best_reduced_cost
            if (
                best_full_pricing.routes is None
                or best_full_pricing.best_reduced_cost is None
                or best_full_pricing.best_reduced_cost >= -1.0e-7
            ):
                if full_pricing_incomplete or status == "FULL_PRICING_TIME_LIMIT":
                    status = "FULL_PRICING_TIME_LIMIT"
                    break
                exact_over_full_route_space = True
                break
            _append_missing_routes(candidate_routes, best_full_pricing.routes)
            rmp.sync_routes(candidate_routes)
            column = _column_from_routes(data, best_full_pricing.routes, len(columns))
            key = _column_key(column.route_signatures)
            if key in column_keys:
                if full_pricing_incomplete or status == "FULL_PRICING_TIME_LIMIT":
                    status = "FULL_PRICING_TIME_LIMIT"
                    break
                exact_over_full_route_space = True
                break
            columns.append(column)
            column_keys.add(key)
            rmp.add_columns([column])
            generated_pricing_columns += 1
            exact_over_candidate_routes = False
            lp_result = solve_current_rmp(max(0.001, _remaining(deadline)))
            status = lp_result.status
            objective = lp_result.objective
            continue
        exact_over_candidate_routes = True
        break

    if len(columns) >= max(1, int(max_columns)) and not exact_over_candidate_routes and status == "OPTIMAL":
        status = "COLUMN_LIMIT"

    return SchedulePackDiagnosticResult(
        status=status,
        objective=objective,
        column_count=len(columns),
        candidate_route_count=len(candidate_routes),
        generated_state_count=generated_states,
        skipped_duplicate_columns=skipped_duplicate,
        skipped_infeasible_extensions=skipped_infeasible,
        single_route_columns=sum(1 for column in columns if column.route_count == 1),
        multi_route_columns=sum(1 for column in columns if column.route_count > 1),
        max_route_count=max(column.route_count for column in columns),
        max_task_count=max(len(column.tasks) for column in columns),
        solving_time=time.perf_counter() - started,
        pricing_iterations=pricing_iterations,
        generated_pricing_columns=generated_pricing_columns,
        best_reduced_cost=best_reduced_cost,
        exact_over_candidate_routes=exact_over_candidate_routes,
        seed_columns=seed_columns,
        exact_over_full_route_space=exact_over_full_route_space,
        full_pricing_generated_states=full_pricing_generated_states,
        full_pricing_route_count=full_pricing_route_count,
        full_pricing_time=full_pricing_time,
    )


def _select_candidate_routes(
    data: BPCData,
    routes: list[RouteColumn],
    support_values: dict[tuple[int, ...], float],
    max_candidate_routes: int,
    required_routes: dict[tuple[int, ...], RouteColumn] | None = None,
) -> list[RouteColumn]:
    by_signature = {route.signature: route for route in routes}
    selected: dict[tuple[int, ...], RouteColumn] = {}

    def add(route: RouteColumn | None) -> None:
        if route is None:
            return
        selected.setdefault(route.signature, route)

    for route in (required_routes or {}).values():
        add(by_signature.get(route.signature, route))

    sorted_routes = sorted(
        by_signature.values(),
        key=lambda route: (
            -float(support_values.get(route.signature, 0.0)),
            float(route.cost) / max(1, len(route.task_set)),
            float(route.cycle_time),
            -len(route.task_set),
            route.signature,
        ),
    )
    limit = len(sorted_routes) if max_candidate_routes <= 0 else max(0, max_candidate_routes)
    for route in sorted_routes[:limit]:
        add(route)

    for task in data.tasks:
        task_routes = [
            route
            for route in by_signature.values()
            if int(task) in route.task_set
        ]
        task_routes.sort(
            key=lambda route: (
                len(route.task_set) != 1,
                float(route.cost) / max(1, len(route.task_set)),
                float(route.cycle_time),
                route.signature,
            )
        )
        for route in task_routes[:3]:
            add(route)

    if max_candidate_routes <= 0 or len(selected) <= max_candidate_routes:
        return list(selected.values())
    required_signatures = set((required_routes or {}).keys())
    required = [route for signature, route in selected.items() if signature in required_signatures]
    optional = [route for signature, route in selected.items() if signature not in required_signatures]
    optional_limit = max(0, int(max_candidate_routes) - len(required))
    return required + sorted(
        optional,
        key=lambda route: (
            -float(support_values.get(route.signature, 0.0)),
            float(route.cost) / max(1, len(route.task_set)),
            float(route.cycle_time),
            route.signature,
        ),
    )[:optional_limit]


def _generate_schedule_columns(
    data: BPCData,
    routes: list[RouteColumn],
    *,
    seed_schedules: list[list[RouteColumn]] | tuple[tuple[RouteColumn, ...], ...] | None,
    max_columns: int,
    beam_width: int,
    max_sorties: int,
    deadline: float | None,
) -> tuple[list[SchedulePackColumn], int, int, int, int]:
    max_route_count = int(max_sorties) if max_sorties and max_sorties > 0 else int(data.sortie_limit)
    max_route_count = max(1, min(max_route_count, int(data.sortie_limit)))
    column_by_key: dict[tuple[tuple[int, ...], ...], SchedulePackColumn] = {}
    generated_states = 0
    skipped_duplicate = 0
    skipped_infeasible = 0
    seed_columns = 0

    def add_column(state: _ScheduleState) -> None:
        nonlocal skipped_duplicate
        key = _state_key(routes, state)
        if key in column_by_key:
            skipped_duplicate += 1
            return
        column_by_key[key] = _column_from_state(data, routes, state, len(column_by_key))

    signature_to_index = {route.signature: index for index, route in enumerate(routes)}
    for schedule in seed_schedules or []:
        if _expired(deadline) or len(column_by_key) >= max_columns:
            break
        route_indices: list[int] = []
        schedule_routes: list[RouteColumn] = []
        for route in schedule:
            index = signature_to_index.get(route.signature)
            if index is None:
                continue
            route_indices.append(index)
            schedule_routes.append(routes[index])
        if not route_indices:
            continue
        checked = check_route_set_schedule_feasible(data, schedule_routes)
        generated_states += max(1, len(schedule_routes))
        if not checked.feasible or checked.ready_time is None:
            skipped_infeasible += 1
            continue
        ordered_indices = tuple(route_indices[index] for index in checked.order)
        state = _ScheduleState(
            route_indices=ordered_indices,
            tasks=frozenset(task for index in ordered_indices for task in routes[index].task_set),
            ready_time=float(checked.ready_time),
            variable_cost=sum(float(routes[index].cost) for index in ordered_indices),
        )
        before = len(column_by_key)
        add_column(state)
        if len(column_by_key) > before:
            seed_columns += 1

    beam: list[_ScheduleState] = []
    for index, route in enumerate(routes):
        if _expired(deadline) or len(column_by_key) >= max_columns:
            break
        evaluated = evaluate_route_at_start(data, route, 0.0)
        generated_states += 1
        if evaluated is None:
            skipped_infeasible += 1
            continue
        state = _ScheduleState(
            route_indices=(index,),
            tasks=frozenset(int(task) for task in route.task_set),
            ready_time=float(evaluated["ready_time"]),
            variable_cost=float(route.cost),
        )
        add_column(state)
        beam.append(state)

    depth = 1
    while beam and depth < max_route_count and len(column_by_key) < max_columns and not _expired(deadline):
        next_states: list[_ScheduleState] = []
        for state in beam:
            used = set(state.route_indices)
            for index, route in enumerate(routes):
                if _expired(deadline) or len(column_by_key) >= max_columns:
                    break
                if index in used or state.tasks.intersection(route.task_set):
                    continue
                evaluated = evaluate_route_at_start(data, route, state.ready_time)
                generated_states += 1
                if evaluated is None:
                    skipped_infeasible += 1
                    continue
                next_state = _ScheduleState(
                    route_indices=(*state.route_indices, index),
                    tasks=frozenset((*state.tasks, *(int(task) for task in route.task_set))),
                    ready_time=float(evaluated["ready_time"]),
                    variable_cost=float(state.variable_cost) + float(route.cost),
                )
                add_column(next_state)
                next_states.append(next_state)
        next_states.sort(key=_state_rank)
        beam = next_states[: max(1, int(beam_width))]
        depth += 1

    columns = sorted(column_by_key.values(), key=lambda column: (column.cost / max(1, len(column.tasks)), column.cost, column.route_signatures))
    return columns[: max(1, int(max_columns))], generated_states, skipped_duplicate, skipped_infeasible, seed_columns


def _state_key(routes: list[RouteColumn], state: _ScheduleState) -> tuple[tuple[int, ...], ...]:
    return _column_key(tuple(routes[index].signature for index in state.route_indices))


def _column_key(signatures: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(int(task) for task in signature) for signature in signatures))


def _column_from_state(
    data: BPCData,
    routes: list[RouteColumn],
    state: _ScheduleState,
    column_id: int,
) -> SchedulePackColumn:
    signatures = tuple(routes[index].signature for index in state.route_indices)
    return SchedulePackColumn(
        id=int(column_id),
        route_signatures=signatures,
        tasks=tuple(sorted(state.tasks)),
        route_count=len(state.route_indices),
        variable_cost=float(state.variable_cost),
        fixed_cost=float(data.fixed_vehicle_cost),
        cost=float(data.fixed_vehicle_cost) + float(state.variable_cost),
        ready_time=float(state.ready_time),
    )


def _state_rank(state: _ScheduleState) -> tuple[float, float, int, tuple[int, ...]]:
    return (
        float(state.variable_cost) / max(1, len(state.tasks)),
        float(state.ready_time),
        -len(state.tasks),
        state.route_indices,
    )


def _price_best_schedule_column(
    data: BPCData,
    routes: list[RouteColumn],
    *,
    cover_duals: dict[int, float],
    fleet_dual: float,
    existing_keys: set[tuple[tuple[int, ...], ...]],
    max_sorties: int,
    deadline: float | None,
) -> _PricingResult:
    task_to_bit = {int(task): 1 << index for index, task in enumerate(data.tasks)}
    route_infos: list[tuple[int, int, float, RouteColumn]] = []
    for index, route in enumerate(routes):
        mask = 0
        dual_sum = 0.0
        for task in route.task_set:
            mask |= task_to_bit[int(task)]
            dual_sum += float(cover_duals.get(int(task), 0.0))
        profit = dual_sum - float(route.cost)
        route_infos.append((index, mask, profit, route))
    route_infos.sort(key=lambda item: (-item[2], item[3].cycle_time, item[3].signature))

    max_route_count = int(max_sorties) if max_sorties and max_sorties > 0 else int(data.sortie_limit)
    max_route_count = max(1, min(max_route_count, int(data.sortie_limit)))
    labels_by_key: dict[tuple[int, int], list[_ScheduleState]] = {}
    frontier: list[_ScheduleState] = []
    generated_states = 0
    skipped_infeasible = 0
    best_state: _ScheduleState | None = None
    best_reduced_cost: float | None = None

    def consider_state(state: _ScheduleState) -> None:
        nonlocal best_state, best_reduced_cost
        key = _state_key(routes, state)
        if key in existing_keys:
            return
        reduced_cost = float(data.fixed_vehicle_cost) + float(state.variable_cost)
        reduced_cost -= sum(float(cover_duals.get(int(task), 0.0)) for task in state.tasks)
        reduced_cost -= float(fleet_dual)
        if best_reduced_cost is None or reduced_cost < best_reduced_cost:
            best_reduced_cost = reduced_cost
            best_state = state

    def add_label(state: _ScheduleState) -> bool:
        key = (sum(task_to_bit[int(task)] for task in state.tasks), len(state.route_indices))
        labels = labels_by_key.setdefault(key, [])
        for old in labels:
            if old.ready_time <= state.ready_time + 1.0e-9 and old.variable_cost <= state.variable_cost + 1.0e-9:
                old_dual = sum(float(cover_duals.get(int(task), 0.0)) for task in old.tasks)
                new_dual = sum(float(cover_duals.get(int(task), 0.0)) for task in state.tasks)
                if old_dual - old.variable_cost >= new_dual - state.variable_cost - 1.0e-9:
                    return False
        labels[:] = [
            old
            for old in labels
            if not (
                state.ready_time <= old.ready_time + 1.0e-9
                and state.variable_cost <= old.variable_cost + 1.0e-9
                and sum(float(cover_duals.get(int(task), 0.0)) for task in state.tasks) - state.variable_cost
                >= sum(float(cover_duals.get(int(task), 0.0)) for task in old.tasks) - old.variable_cost - 1.0e-9
            )
        ]
        labels.append(state)
        return True

    for index, mask, _profit, route in route_infos:
        if _expired(deadline):
            return _PricingResult(best_state, best_reduced_cost, generated_states, skipped_infeasible, False)
        evaluated = evaluate_route_at_start(data, route, 0.0)
        generated_states += 1
        if evaluated is None:
            skipped_infeasible += 1
            continue
        state = _ScheduleState(
            route_indices=(index,),
            tasks=frozenset(int(task) for task in route.task_set),
            ready_time=float(evaluated["ready_time"]),
            variable_cost=float(route.cost),
        )
        if add_label(state):
            frontier.append(state)
            consider_state(state)

    for _depth in range(1, max_route_count):
        if not frontier:
            break
        next_frontier: list[_ScheduleState] = []
        for state in sorted(frontier, key=_state_rank):
            if _expired(deadline):
                return _PricingResult(best_state, best_reduced_cost, generated_states, skipped_infeasible, False)
            used_mask = sum(task_to_bit[int(task)] for task in state.tasks)
            for index, mask, _profit, route in route_infos:
                if used_mask & mask:
                    continue
                evaluated = evaluate_route_at_start(data, route, state.ready_time)
                generated_states += 1
                if evaluated is None:
                    skipped_infeasible += 1
                    continue
                next_state = _ScheduleState(
                    route_indices=(*state.route_indices, index),
                    tasks=frozenset((*state.tasks, *(int(task) for task in route.task_set))),
                    ready_time=float(evaluated["ready_time"]),
                    variable_cost=float(state.variable_cost) + float(route.cost),
                )
                if add_label(next_state):
                    next_frontier.append(next_state)
                    consider_state(next_state)
        frontier = next_frontier

    return _PricingResult(best_state, best_reduced_cost, generated_states, skipped_infeasible, True)


def _price_vehicle_schedule_columns_batch(
    data: BPCData,
    routes: list[RouteColumn],
    vehicle: int,
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    cover_duals: dict[int, float],
    schedule_dual: float,
    cut_duals: dict[int, float],
    branch_duals: dict[int, float],
    existing_keys: set[tuple[tuple[int, ...], ...]],
    max_sorties: int,
    deadline: float | None,
    batch_size: int,
    coefficient_cache: _SchedulePackCoefficientCache,
) -> _BatchPricingResult:
    route_infos: list[tuple[int, int, float, RouteColumn]] = []
    for index, route in enumerate(routes):
        if not route_allowed_by_branch(route, int(vehicle), branch_constraints):
            continue
        mask = coefficient_cache.route_mask(route)
        contribution = float(route.cost)
        for task in route.task_set:
            contribution -= float(cover_duals.get(int(task), 0.0))
        for cut in cuts:
            dual = float(cut_duals.get(int(cut.id), 0.0))
            if dual == 0.0:
                continue
            coefficient = coefficient_cache.cut_coefficient(route, int(vehicle), cut)
            if coefficient:
                contribution -= dual * coefficient
        for index_bc, constraint in enumerate(branch_constraints):
            if constraint.kind != "arc_on":
                continue
            dual = float(branch_duals.get(index_bc, 0.0))
            if dual:
                contribution -= dual * coefficient_cache.branch_coefficient(route, int(vehicle), index_bc, constraint)
        route_infos.append((index, mask, contribution, route))
    route_infos.sort(key=lambda item: (item[2], item[3].cycle_time, item[3].signature))

    max_route_count = int(max_sorties) if max_sorties and max_sorties > 0 else int(data.sortie_limit)
    max_route_count = max(1, min(max_route_count, int(data.sortie_limit)))
    labels_by_key: dict[tuple[int, int], list[tuple[_ScheduleState, float]]] = {}
    frontier: list[tuple[_ScheduleState, float]] = []
    generated_states = 0
    skipped_infeasible = 0
    negative_states: dict[tuple[tuple[int, ...], ...], tuple[_ScheduleState, float]] = {}
    best_reduced_cost: float | None = None

    def consider_state(state: _ScheduleState, reduced_component: float) -> None:
        nonlocal best_reduced_cost
        key = _state_key(routes, state)
        if key in existing_keys:
            return
        reduced_cost = float(reduced_component) - float(schedule_dual)
        if best_reduced_cost is None or reduced_cost < best_reduced_cost:
            best_reduced_cost = reduced_cost
        if reduced_cost >= -1.0e-7:
            return
        old = negative_states.get(key)
        if old is None or reduced_cost < old[1]:
            negative_states[key] = (state, reduced_cost)

    def add_label(state: _ScheduleState, reduced_component: float) -> bool:
        mask = 0
        for task in state.tasks:
            mask |= coefficient_cache.task_to_bit[int(task)]
        key = (mask, len(state.route_indices))
        labels = labels_by_key.setdefault(key, [])
        for old, old_component in labels:
            if old.ready_time <= state.ready_time + 1.0e-9 and old_component <= reduced_component + 1.0e-9:
                return False
        labels[:] = [
            (old, old_component)
            for old, old_component in labels
            if not (state.ready_time <= old.ready_time + 1.0e-9 and reduced_component <= old_component + 1.0e-9)
        ]
        labels.append((state, reduced_component))
        return True

    for index, mask, contribution, route in route_infos:
        if _expired(deadline):
            states = _top_priced_states(negative_states, batch_size)
            return _BatchPricingResult(states, best_reduced_cost, generated_states, skipped_infeasible, False)
        evaluated = evaluate_route_at_start(data, route, 0.0)
        generated_states += 1
        if evaluated is None:
            skipped_infeasible += 1
            continue
        state = _ScheduleState(
            route_indices=(index,),
            tasks=frozenset(int(task) for task in route.task_set),
            ready_time=float(evaluated["ready_time"]),
            variable_cost=float(route.cost),
        )
        if add_label(state, float(contribution)):
            frontier.append((state, float(contribution)))
            consider_state(state, float(contribution))

    for _depth in range(1, max_route_count):
        if not frontier:
            break
        next_frontier: list[tuple[_ScheduleState, float]] = []
        for state, reduced_component in sorted(frontier, key=lambda item: (_state_rank(item[0]), item[1])):
            if _expired(deadline):
                states = _top_priced_states(negative_states, batch_size)
                return _BatchPricingResult(states, best_reduced_cost, generated_states, skipped_infeasible, False)
            used_mask = 0
            for task in state.tasks:
                used_mask |= coefficient_cache.task_to_bit[int(task)]
            for index, mask, contribution, route in route_infos:
                if used_mask & mask:
                    continue
                evaluated = evaluate_route_at_start(data, route, state.ready_time)
                generated_states += 1
                if evaluated is None:
                    skipped_infeasible += 1
                    continue
                next_state = _ScheduleState(
                    route_indices=(*state.route_indices, index),
                    tasks=frozenset((*state.tasks, *(int(task) for task in route.task_set))),
                    ready_time=float(evaluated["ready_time"]),
                    variable_cost=float(state.variable_cost) + float(route.cost),
                )
                next_component = float(reduced_component) + float(contribution)
                if add_label(next_state, next_component):
                    next_frontier.append((next_state, next_component))
                    consider_state(next_state, next_component)
        frontier = next_frontier

    return _BatchPricingResult(
        _top_priced_states(negative_states, batch_size),
        best_reduced_cost,
        generated_states,
        skipped_infeasible,
        True,
    )


def _top_priced_states(
    candidates: dict[tuple[tuple[int, ...], ...], tuple[_ScheduleState, float]],
    batch_size: int,
) -> tuple[tuple[_ScheduleState, float], ...]:
    ordered = sorted(candidates.values(), key=lambda item: (item[1], _state_rank(item[0])))
    return tuple(ordered[: max(1, int(batch_size))])


def _route_reduced_component(
    route: RouteColumn,
    vehicle: int,
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    cover_duals: dict[int, float],
    cut_duals: dict[int, float],
    branch_duals: dict[int, float],
    coefficient_cache: _SchedulePackCoefficientCache,
) -> float:
    contribution = float(route.cost)
    for task in route.task_set:
        contribution -= float(cover_duals.get(int(task), 0.0))
    for cut in cuts:
        dual = float(cut_duals.get(int(cut.id), 0.0))
        if dual == 0.0:
            continue
        coefficient = coefficient_cache.cut_coefficient(route, int(vehicle), cut)
        if coefficient:
            contribution -= dual * coefficient
    for index_bc, constraint in enumerate(branch_constraints):
        if constraint.kind != "arc_on":
            continue
        dual = float(branch_duals.get(index_bc, 0.0))
        if dual:
            contribution -= dual * coefficient_cache.branch_coefficient(route, int(vehicle), index_bc, constraint)
    return float(contribution)


def _partial_route_prefix_feasible_at_start(data: BPCData, sequence: tuple[int, ...], start_time: float) -> bool:
    current = 0
    current_time = float(start_time)
    load = 0.0
    energy = 0.0
    for task_id in sequence:
        task = int(task_id)
        segment = data.arc(current, task)
        arrival = current_time + float(segment["tau"])
        start = max(data.task_value(task, "r"), arrival)
        finish = start + data.task_value(task, "sigma")
        if finish > data.task_value(task, "D") + 1.0e-9:
            return False
        load += data.task_value(task, "d")
        energy += float(segment["energy"]) + data.task_value(task, "g")
        if load > data.capacity + 1.0e-9 or energy > data.energy_limit + 1.0e-9:
            return False
        if finish > data.horizon + 1.0e-9:
            return False
        current = task
        current_time = finish
    return True


def _price_best_vehicle_schedule_column_full_route_space(
    data: BPCData,
    vehicle: int,
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    cover_duals: dict[int, float],
    schedule_dual: float,
    cut_duals: dict[int, float],
    branch_duals: dict[int, float],
    existing_keys: set[tuple[tuple[int, ...], ...]],
    max_sorties: int,
    deadline: float | None,
    max_states: int,
    coefficient_cache: _SchedulePackCoefficientCache | None = None,
) -> _FullPricingResult:
    """在全 route space 上为某辆车做 exact schedule-column pricing。

    中文注释：该过程把单 sortie route 生成和完整车辆 schedule pricing 合在同一
    个 label search 中。每个 schedule label 延伸时，只枚举当前剩余任务下可作为
    下一条 sortie 的 route；一旦发现负 reduced-cost schedule column，立即返回
    该合法列供 RMP 回流，但不声明 exact。只有完整搜索结束且没有负列时才给出
    exact 证书。
    """

    started = time.perf_counter()
    generated_states = 0
    skipped_infeasible = 0
    generated_route_signatures: set[tuple[int, ...]] = set()

    if any(
        constraint.kind == "vehicle_use_off" and int(constraint.vehicle) == int(vehicle)
        for constraint in branch_constraints
    ):
        return _FullPricingResult(None, None, 0, 0, 0, True, time.perf_counter() - started)

    if coefficient_cache is None:
        coefficient_cache = _SchedulePackCoefficientCache(data)

    max_route_count = int(max_sorties) if max_sorties and max_sorties > 0 else int(data.sortie_limit)
    max_route_count = max(1, min(max_route_count, int(data.sortie_limit)))
    task_order = tuple(
        sorted(
            (int(task) for task in data.tasks),
            key=lambda task: (
                -float(cover_duals.get(int(task), 0.0)),
                float(data.task_value(int(task), "r")),
                int(task),
            ),
        )
    )
    labels_by_key: dict[tuple[int, int], list[_FullScheduleLabel]] = {}
    frontier: list[_FullScheduleLabel] = [
        _FullScheduleLabel(
            routes=tuple(),
            tasks=frozenset(),
            used_mask=0,
            ready_time=0.0,
            variable_cost=0.0,
            reduced_component=0.0,
        )
    ]
    best_routes: tuple[RouteColumn, ...] | None = None
    best_reduced_cost: float | None = None

    def check_budget() -> bool:
        return not _expired(deadline) and (int(max_states) <= 0 or generated_states <= int(max_states))

    def schedule_key(schedule_routes: tuple[RouteColumn, ...]) -> tuple[tuple[int, ...], ...]:
        return _column_key(tuple(route.signature for route in schedule_routes))

    def consider(label: _FullScheduleLabel) -> bool:
        nonlocal best_routes, best_reduced_cost
        if not label.routes or schedule_key(label.routes) in existing_keys:
            return False
        reduced_cost = float(label.reduced_component) - float(schedule_dual)
        if best_reduced_cost is None or reduced_cost < best_reduced_cost:
            best_reduced_cost = reduced_cost
            best_routes = label.routes
        return reduced_cost < -1.0e-7

    def add_label(label: _FullScheduleLabel) -> bool:
        if not label.routes:
            return True
        key = (int(label.used_mask), len(label.routes))
        labels = labels_by_key.setdefault(key, [])
        for old in labels:
            if old.ready_time <= label.ready_time + 1.0e-9 and old.reduced_component <= label.reduced_component + 1.0e-9:
                return False
        labels[:] = [
            old
            for old in labels
            if not (
                label.ready_time <= old.ready_time + 1.0e-9
                and label.reduced_component <= old.reduced_component + 1.0e-9
            )
        ]
        labels.append(label)
        return True

    def result(exact: bool) -> _FullPricingResult:
        return _FullPricingResult(
            best_routes,
            best_reduced_cost,
            generated_states,
            skipped_infeasible,
            len(generated_route_signatures),
            bool(exact),
            time.perf_counter() - started,
        )

    def next_routes(label: _FullScheduleLabel):
        nonlocal generated_states, skipped_infeasible
        stack: list[tuple[int, ...]] = [tuple()]
        while stack:
            if not check_budget():
                return
            prefix = stack.pop()
            used_in_route = set(prefix)
            for task in task_order:
                bit = coefficient_cache.task_to_bit[int(task)]
                if label.used_mask & bit or int(task) in used_in_route:
                    continue
                sequence = (*prefix, int(task))
                generated_states += 1
                if not check_budget():
                    return
                if not partial_sequence_allowed(sequence, int(vehicle), branch_constraints):
                    continue
                if not _partial_route_prefix_feasible_at_start(data, sequence, label.ready_time):
                    skipped_infeasible += 1
                    continue
                stack.append(sequence)
                route = evaluate_route(data, sequence)
                if route is None:
                    continue
                evaluated = evaluate_route_at_start(data, route, label.ready_time)
                if evaluated is None:
                    continue
                if not route_allowed_by_branch(route, int(vehicle), branch_constraints):
                    continue
                generated_route_signatures.add(route.signature)
                yield route, int(coefficient_cache.route_mask(route)), float(evaluated["ready_time"])

    depth = 0
    while frontier and depth < max_route_count:
        next_frontier: list[_FullScheduleLabel] = []
        for label in sorted(
            frontier,
            key=lambda item: (
                item.reduced_component,
                item.ready_time,
                item.variable_cost,
                tuple(route.signature for route in item.routes),
            ),
        ):
            if not check_budget():
                return result(False)
            for route, route_mask, next_ready in next_routes(label):
                contribution = _route_reduced_component(
                    route,
                    int(vehicle),
                    cuts,
                    branch_constraints,
                    cover_duals=cover_duals,
                    cut_duals=cut_duals,
                    branch_duals=branch_duals,
                    coefficient_cache=coefficient_cache,
                )
                new_label = _FullScheduleLabel(
                    routes=(*label.routes, route),
                    tasks=frozenset((*label.tasks, *(int(task) for task in route.task_set))),
                    used_mask=int(label.used_mask | route_mask),
                    ready_time=float(next_ready),
                    variable_cost=float(label.variable_cost) + float(route.cost),
                    reduced_component=float(label.reduced_component) + float(contribution),
                )
                if not add_label(new_label):
                    continue
                if consider(new_label):
                    return result(False)
                if len(new_label.routes) < max_route_count:
                    next_frontier.append(new_label)
            if not check_budget():
                return result(False)
        frontier = next_frontier
        depth += 1

    return result(True)


def _enumerate_full_vehicle_routes(
    data: BPCData,
    vehicle: int,
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    deadline: float | None,
    max_states: int,
) -> tuple[list[RouteColumn], int, bool]:
    routes: dict[tuple[int, ...], RouteColumn] = {}
    generated_states = 0
    stack: list[tuple[int, ...]] = [()]
    task_order = tuple(int(task) for task in data.tasks)

    def over_budget() -> bool:
        return _expired(deadline) or (int(max_states) > 0 and generated_states > int(max_states))

    while stack:
        if over_budget():
            return list(routes.values()), generated_states, False
        prefix = stack.pop()
        used = set(prefix)
        for task in task_order:
            if task in used:
                continue
            sequence = (*prefix, int(task))
            generated_states += 1
            if over_budget():
                return list(routes.values()), generated_states, False
            if not partial_sequence_allowed(sequence, int(vehicle), branch_constraints):
                continue
            route = evaluate_route(data, sequence)
            if route is None:
                continue
            stack.append(sequence)
            if route_allowed_by_branch(route, int(vehicle), branch_constraints):
                routes.setdefault(route.signature, route)

    ordered = sorted(routes.values(), key=lambda route: (len(route.tasks), route.cost / max(1, len(route.tasks)), route.cycle_time, route.signature))
    return ordered, generated_states, True


def _append_missing_routes(routes: list[RouteColumn], new_routes: tuple[RouteColumn, ...]) -> None:
    by_signature = {route.signature: route for route in routes}
    for route in new_routes:
        if route.signature in by_signature:
            continue
        routes.append(route)
        by_signature[route.signature] = route


def _column_from_routes(
    data: BPCData,
    routes: tuple[RouteColumn, ...],
    column_id: int,
) -> SchedulePackColumn:
    ready_time = 0.0
    for route in routes:
        evaluated = evaluate_route_at_start(data, route, ready_time)
        if evaluated is None:
            ready_time = float("inf")
            break
        ready_time = float(evaluated["ready_time"])
    tasks = frozenset(task for route in routes for task in route.task_set)
    variable_cost = sum(float(route.cost) for route in routes)
    return SchedulePackColumn(
        id=int(column_id),
        route_signatures=tuple(route.signature for route in routes),
        tasks=tuple(sorted(tasks)),
        route_count=len(routes),
        variable_cost=float(variable_cost),
        fixed_cost=float(data.fixed_vehicle_cost),
        cost=float(data.fixed_vehicle_cost) + float(variable_cost),
        ready_time=float(ready_time),
    )


def _column_allowed_for_vehicle(
    routes_by_signature: dict[tuple[int, ...], RouteColumn],
    column: SchedulePackColumn,
    vehicle: int,
    branch_constraints: tuple[BranchConstraint, ...],
) -> bool:
    if any(signature not in routes_by_signature for signature in column.route_signatures):
        return False
    return all(
        route_allowed_by_branch(routes_by_signature[signature], int(vehicle), branch_constraints)
        for signature in column.route_signatures
    )


def _column_route_coefficient(
    routes_by_signature: dict[tuple[int, ...], RouteColumn],
    column: SchedulePackColumn,
    vehicle: int,
    cut: Cut,
    coefficient_cache: _SchedulePackCoefficientCache | None = None,
) -> float:
    if coefficient_cache is None:
        return sum(float(cut.coefficient(routes_by_signature[signature], int(vehicle))) for signature in column.route_signatures)
    return sum(
        coefficient_cache.cut_coefficient(routes_by_signature[signature], int(vehicle), cut)
        for signature in column.route_signatures
    )


def _column_branch_coefficient(
    routes_by_signature: dict[tuple[int, ...], RouteColumn],
    column: SchedulePackColumn,
    vehicle: int,
    constraint: BranchConstraint,
    constraint_index: int = -1,
    coefficient_cache: _SchedulePackCoefficientCache | None = None,
) -> float:
    if coefficient_cache is None or int(constraint_index) < 0:
        return sum(
            route_branch_coefficient(routes_by_signature[signature], int(vehicle), constraint)
            for signature in column.route_signatures
        )
    return sum(
        coefficient_cache.branch_coefficient(routes_by_signature[signature], int(vehicle), int(constraint_index), constraint)
        for signature in column.route_signatures
    )


def _solve_lp(
    data: BPCData,
    columns: list[SchedulePackColumn],
    time_limit: float,
    rmp_params: dict[str, Any],
) -> _ScheduleLPResult:
    from pyscipopt import Model, quicksum

    model = Model(f"schedule_pack_diag_{data.name}")
    _try_set_param(model, "display/verblevel", 0)
    _try_set_param(model, "presolving/maxrounds", 0)
    _try_set_param(model, "separating/maxrounds", 0)
    _try_set_param(model, "parallel/maxnthreads", 1)
    _try_set_param(model, "limits/time", float(time_limit))
    for name, value in rmp_params.items():
        if str(name).startswith("display/"):
            continue
        _try_set_param(model, name, value)

    z = {
        column.id: model.addVar(vtype="C", lb=0.0, ub=1.0, obj=float(column.cost), name=f"z[{column.id}]")
        for column in columns
    }
    cover_cons = {}
    for task in data.tasks:
        cover_cons[int(task)] = model.addCons(
            quicksum(z[column.id] for column in columns if int(task) in set(column.tasks)) == 1.0,
            name=f"cover[{task}]",
        )
    fleet_cons = model.addCons(quicksum(z.values()) <= float(len(data.vehicles)), name="fleet")
    model.optimize()
    status = _status_name(model.getStatus())
    if model.getNSols() <= 0:
        return _ScheduleLPResult(None, status, {}, 0.0)
    objective = float(model.getObjVal())
    if status != "OPTIMAL":
        return _ScheduleLPResult(objective, status, {}, 0.0)
    cover_duals: dict[int, float] = {}
    for task, cons in cover_cons.items():
        dual = _dual_value(model, cons)
        if dual is None:
            return _ScheduleLPResult(objective, "DUAL_UNAVAILABLE", {}, 0.0)
        cover_duals[task] = dual
    fleet_dual = _dual_value(model, fleet_cons)
    if fleet_dual is None:
        return _ScheduleLPResult(objective, "DUAL_UNAVAILABLE", {}, 0.0)
    return _ScheduleLPResult(objective, status, cover_duals, fleet_dual)


class _VehicleIndexedSchedulePackRMP:
    """持久化 vehicle-indexed schedule-pack LP。

    中文注释：该类只增量加入新的 schedule column 变量和各约束系数，不在每轮
    pricing 后重建整个 PySCIPOpt 模型。新增列的每个系数与原 `_solve_vehicle_indexed_lp`
    重建版一致，因此只改变求解实现，不改变 LP 数学模型。
    """

    def __init__(
        self,
        data: BPCData,
        routes: list[RouteColumn],
        columns: list[SchedulePackColumn],
        cuts: list[Cut],
        branch_constraints: tuple[BranchConstraint, ...],
        rmp_params: dict[str, Any],
        *,
        coefficient_cache: _SchedulePackCoefficientCache,
    ) -> None:
        from pyscipopt import Model, quicksum

        self.data = data
        self.cuts = cuts
        self.branch_constraints = branch_constraints
        self.coefficient_cache = coefficient_cache
        self.route_by_signature: dict[tuple[int, ...], RouteColumn] = {}
        self.column_by_id: dict[int, SchedulePackColumn] = {}
        self.y: dict[int, Any] = {}
        self.z: dict[tuple[int, int], Any] = {}
        self.cover_cons: dict[int, Any] = {}
        self.schedule_cons: dict[int, Any] = {}
        self.cut_cons: dict[int, Any] = {}
        self.branch_cons: dict[int, Any] = {}
        self.cut_term_counts: dict[int, int] = {}
        self.branch_term_counts: dict[int, int] = {}
        self.solved = False

        self.sync_routes(routes)
        self.model = Model(f"schedule_pack_node_relax_{data.name}")
        _try_set_param(self.model, "display/verblevel", 0)
        _try_set_param(self.model, "presolving/maxrounds", 0)
        _try_set_param(self.model, "separating/maxrounds", 0)
        _try_set_param(self.model, "parallel/maxnthreads", 1)
        for name, value in rmp_params.items():
            if str(name).startswith("display/"):
                continue
            _try_set_param(self.model, name, value)

        for vehicle in data.vehicles:
            lb = 0.0
            ub = 1.0
            for constraint in branch_constraints:
                if constraint.kind == "vehicle_use_on" and int(constraint.vehicle) == int(vehicle):
                    lb = 1.0
                elif constraint.kind == "vehicle_use_off" and int(constraint.vehicle) == int(vehicle):
                    ub = 0.0
            self.y[int(vehicle)] = self.model.addVar(
                vtype="C",
                lb=lb,
                ub=ub,
                obj=float(data.fixed_vehicle_cost),
                name=f"y[{vehicle}]",
            )

        for task in data.tasks:
            self.cover_cons[int(task)] = self.model.addCons(
                quicksum([]) == 1.0,
                name=f"cover[{task}]",
            )

        for vehicle in data.vehicles:
            self.schedule_cons[int(vehicle)] = self.model.addCons(
                -self.y[int(vehicle)] <= 0.0,
                name=f"schedule_use[{vehicle}]",
            )

        for left, right in zip(data.vehicles[:-1], data.vehicles[1:]):
            self.model.addCons(self.y[int(right)] <= self.y[int(left)], name=f"vehicle_order[{left}]")

        for cut in cuts:
            y_terms = []
            y_term_count = 0
            for vehicle, var in self.y.items():
                coefficient = cut.y_coefficient(vehicle) if hasattr(cut, "y_coefficient") else 0.0
                if coefficient != 0.0:
                    y_terms.append(float(coefficient) * var)
                    y_term_count += 1
            expr = quicksum(y_terms)
            if cut.sense == "<=":
                self.cut_cons[int(cut.id)] = self.model.addCons(expr <= cut.rhs, name=f"cut[{cut.id}]")
            elif cut.sense == ">=":
                self.cut_cons[int(cut.id)] = self.model.addCons(expr >= cut.rhs, name=f"cut[{cut.id}]")
            else:
                raise ValueError(f"未知 cut sense: {cut.sense}")
            self.cut_term_counts[int(cut.id)] = y_term_count

        for index, constraint in enumerate(branch_constraints):
            if constraint.kind != "arc_on":
                continue
            self.branch_cons[int(index)] = self.model.addCons(
                quicksum([]) >= 1.0,
                name=f"branch_arc_on[{index}]",
            )
            self.branch_term_counts[int(index)] = 0

        self.add_columns(columns)

    def sync_routes(self, routes: list[RouteColumn]) -> None:
        for route in routes:
            self.route_by_signature[route.signature] = route

    def add_columns(self, columns: list[SchedulePackColumn]) -> None:
        if not columns:
            return
        if self.solved:
            self.model.freeTransform()
            self.solved = False
        for column in columns:
            if int(column.id) in self.column_by_id:
                continue
            self.column_by_id[int(column.id)] = column
            missing = [signature for signature in column.route_signatures if signature not in self.route_by_signature]
            if missing:
                raise ValueError(f"schedule-pack column 引用了缺失 route: {missing[0]}")
            for vehicle in self.data.vehicles:
                vehicle_id = int(vehicle)
                if not _column_allowed_for_vehicle(self.route_by_signature, column, vehicle_id, self.branch_constraints):
                    continue
                var = self.model.addVar(
                    vtype="C",
                    lb=0.0,
                    ub=1.0,
                    obj=float(column.variable_cost),
                    name=f"z[{column.id},{vehicle_id}]",
                )
                self.z[(int(column.id), vehicle_id)] = var
                for task in column.tasks:
                    self.model.addConsCoeff(self.cover_cons[int(task)], var, 1.0)
                self.model.addConsCoeff(self.schedule_cons[vehicle_id], var, 1.0)
                for cut in self.cuts:
                    coefficient = _column_route_coefficient(
                        self.route_by_signature,
                        column,
                        vehicle_id,
                        cut,
                        self.coefficient_cache,
                    )
                    if coefficient != 0.0:
                        self.model.addConsCoeff(self.cut_cons[int(cut.id)], var, coefficient)
                        self.cut_term_counts[int(cut.id)] = self.cut_term_counts.get(int(cut.id), 0) + 1
                for index, constraint in enumerate(self.branch_constraints):
                    if constraint.kind != "arc_on":
                        continue
                    coefficient = _column_branch_coefficient(
                        self.route_by_signature,
                        column,
                        vehicle_id,
                        constraint,
                        index,
                        self.coefficient_cache,
                    )
                    if coefficient != 0.0:
                        self.model.addConsCoeff(self.branch_cons[int(index)], var, coefficient)
                        self.branch_term_counts[int(index)] = self.branch_term_counts.get(int(index), 0) + 1

    def solve(self, time_limit: float) -> _VehicleScheduleLPResult:
        _try_set_param(self.model, "limits/time", float(time_limit))
        self.model.optimize()
        self.solved = True
        status = _status_name(self.model.getStatus())
        if self.model.getNSols() <= 0:
            return _VehicleScheduleLPResult(None, status, {}, {}, {}, {})

        objective = float(self.model.getObjVal())
        if status != "OPTIMAL":
            return _VehicleScheduleLPResult(objective, status, {}, {}, {}, {})

        cover_duals: dict[int, float] = {}
        for task, cons in self.cover_cons.items():
            dual = _dual_value(self.model, cons)
            if dual is None:
                return _VehicleScheduleLPResult(objective, "DUAL_UNAVAILABLE", {}, {}, {}, {})
            cover_duals[task] = dual

        schedule_duals: dict[int, float] = {}
        for vehicle, cons in self.schedule_cons.items():
            dual = _dual_value(self.model, cons)
            if dual is None:
                return _VehicleScheduleLPResult(objective, "DUAL_UNAVAILABLE", {}, {}, {}, {})
            schedule_duals[vehicle] = dual

        cut_duals: dict[int, float] = {}
        for cut_id, cons in self.cut_cons.items():
            if self.cut_term_counts.get(int(cut_id), 0) == 0:
                cut_duals[int(cut_id)] = 0.0
                continue
            dual = _dual_value(self.model, cons)
            if dual is None:
                return _VehicleScheduleLPResult(objective, "DUAL_UNAVAILABLE", {}, {}, {}, {})
            cut_duals[int(cut_id)] = dual

        branch_duals: dict[int, float] = {}
        for index, cons in self.branch_cons.items():
            if self.branch_term_counts.get(int(index), 0) == 0:
                branch_duals[int(index)] = 0.0
                continue
            dual = _dual_value(self.model, cons)
            if dual is None:
                return _VehicleScheduleLPResult(objective, "DUAL_UNAVAILABLE", {}, {}, {}, {})
            branch_duals[int(index)] = dual

        return _VehicleScheduleLPResult(
            objective=objective,
            status=status,
            cover_duals=cover_duals,
            schedule_duals=schedule_duals,
            cut_duals=cut_duals,
            branch_duals=branch_duals,
        )


def _solve_vehicle_indexed_lp(
    data: BPCData,
    routes: list[RouteColumn],
    columns: list[SchedulePackColumn],
    cuts: list[Cut],
    branch_constraints: tuple[BranchConstraint, ...],
    time_limit: float,
    rmp_params: dict[str, Any],
    *,
    coefficient_cache: _SchedulePackCoefficientCache | None = None,
) -> _VehicleScheduleLPResult:
    cache = coefficient_cache or _SchedulePackCoefficientCache(data)
    rmp = _VehicleIndexedSchedulePackRMP(
        data,
        routes,
        columns,
        cuts,
        branch_constraints,
        rmp_params,
        coefficient_cache=cache,
    )
    return rmp.solve(time_limit)


def _result_without_objective(
    status: str,
    columns: list[SchedulePackColumn],
    candidate_route_count: int,
    generated_states: int,
    skipped_duplicate: int,
    skipped_infeasible: int,
    started: float,
) -> SchedulePackDiagnosticResult:
    return SchedulePackDiagnosticResult(
        status=status,
        objective=None,
        column_count=len(columns),
        candidate_route_count=candidate_route_count,
        generated_state_count=generated_states,
        skipped_duplicate_columns=skipped_duplicate,
        skipped_infeasible_extensions=skipped_infeasible,
        single_route_columns=sum(1 for column in columns if column.route_count == 1),
        multi_route_columns=sum(1 for column in columns if column.route_count > 1),
        max_route_count=max((column.route_count for column in columns), default=0),
        max_task_count=max((len(column.tasks) for column in columns), default=0),
        solving_time=time.perf_counter() - started,
    )


def _dual_value(model, cons) -> float | None:
    def clean(value: Any) -> float | None:
        try:
            dual = float(value)
        except Exception:
            return None
        if not math.isfinite(dual):
            return None
        if abs(dual) > _DUAL_ABS_LIMIT:
            return None
        return dual

    transformed = None
    try:
        transformed = model.getTransformedCons(cons)
    except Exception:
        transformed = None
    if transformed is not None:
        try:
            dual = clean(model.getDualsolLinear(transformed))
            if dual is not None:
                return dual
        except Exception:
            pass
    try:
        return clean(model.getDualsolLinear(cons))
    except Exception:
        return None


def _empty_linear_constraint_satisfied(sense: str, rhs: float) -> bool:
    if sense == "<=":
        return 0.0 <= float(rhs) + 1.0e-9
    if sense == ">=":
        return 0.0 >= float(rhs) - 1.0e-9
    raise ValueError(f"未知 cut sense: {sense}")


def _expired(deadline: float | None) -> bool:
    return deadline is not None and time.perf_counter() >= deadline


def _remaining(deadline: float | None) -> float:
    if deadline is None:
        return 1.0e20
    return max(0.001, deadline - time.perf_counter())


def _try_set_param(model, name: str, value: Any) -> None:
    try:
        model.setParam(name, value)
    except Exception:
        pass


def _status_name(status: Any) -> str:
    text = str(status).lower()
    mapping = {
        "optimal": "OPTIMAL",
        "infeasible": "INFEASIBLE",
        "unbounded": "UNBOUNDED",
        "inforunbd": "INF_OR_UNBD",
        "timelimit": "TIME_LIMIT",
        "memlimit": "MEMORY_LIMIT",
        "userinterrupt": "INTERRUPTED",
    }
    return mapping.get(text, text.upper())
