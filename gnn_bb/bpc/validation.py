"""中文摘要：本文件验证整数解是否是原问题真实可行解，重点检查同一车辆多条 sortie 的时间顺序。"""

from __future__ import annotations

from dataclasses import dataclass

from .columns import RouteColumn
from .data import BPCData


CHECK_TOL = 1.0e-9


@dataclass(frozen=True)
class ScheduleCheckResult:
    feasible: bool
    order: tuple[int, ...]
    ready_time: float | None


@dataclass(frozen=True)
class RoutePairScheduleConflict:
    """中文注释：两条 sortie route 无论先后顺序都不能排在同一辆车上。"""

    left: RouteColumn
    right: RouteColumn
    left_ready_time: float | None
    right_ready_time: float | None
    left_then_right_ready_time: float | None
    right_then_left_ready_time: float | None

    @property
    def signatures(self) -> tuple[tuple[int, ...], tuple[int, ...]]:
        return tuple(sorted((self.left.signature, self.right.signature)))


@dataclass(frozen=True)
class ScheduleInfeasibilityWitness:
    """中文注释：用于解释整数 route 集合为什么不能形成真实车辆 schedule。"""

    routes: tuple[RouteColumn, ...]
    pair_conflicts: tuple[RoutePairScheduleConflict, ...]
    reason: str
    deletion_minimal: bool


@dataclass(frozen=True)
class RouteSetSchedulePackingResult:
    """中文注释：一组 route 在同一辆车上最多可排程多少条的 exact 证书。"""

    upper_bound: int
    states_explored: int
    exact: bool


def evaluate_route_at_start(data: BPCData, route: RouteColumn, start_time: float) -> dict | None:
    current = 0
    current_time = float(start_time)
    load = 0.0
    energy = 0.0
    cost = 0.0
    travel_time = 0.0
    service_start: dict[str, float] = {}

    for task_id in route.tasks:
        segment = data.arc(current, task_id)
        arrival = current_time + float(segment["tau"])
        start = max(data.task_value(task_id, "r"), arrival)
        finish = start + data.task_value(task_id, "sigma")
        if finish > data.task_value(task_id, "D") + CHECK_TOL:
            return None
        load += data.task_value(task_id, "d")
        energy += float(segment["energy"]) + data.task_value(task_id, "g")
        cost += float(segment["cost"]) + data.task_value(task_id, "c_srv")
        travel_time += float(segment["tau"])
        if load > data.capacity + CHECK_TOL or energy > data.energy_limit + CHECK_TOL:
            return None
        service_start[str(task_id)] = round(start, 6)
        current = task_id
        current_time = finish

    back = data.arc(current, 0)
    return_time = current_time + float(back["tau"])
    energy += float(back["energy"])
    cost += float(back["cost"])
    travel_time += float(back["tau"])
    if energy > data.energy_limit + CHECK_TOL:
        return None
    ready_time = return_time + energy / data.rho
    if ready_time > data.horizon + CHECK_TOL:
        return None
    return {
        "start_time": round(float(start_time), 6),
        "return_time": round(return_time, 6),
        "ready_time": round(ready_time, 6),
        "energy": round(energy, 6),
        "cost": round(cost, 6),
        "travel_time": round(travel_time, 6),
        "service_start": service_start,
    }


def check_route_set_schedule_feasible(data: BPCData, routes: list[RouteColumn]) -> ScheduleCheckResult:
    if not routes:
        return ScheduleCheckResult(True, tuple(), 0.0)

    count = len(routes)
    full_mask = (1 << count) - 1
    best_ready: dict[tuple[int, int], float] = {}
    parent: dict[tuple[int, int], tuple[int, int] | None] = {}

    for index, route in enumerate(routes):
        evaluated = evaluate_route_at_start(data, route, 0.0)
        if evaluated is None:
            continue
        key = (1 << index, index)
        best_ready[key] = float(evaluated["ready_time"])
        parent[key] = None

    for _ in range(count):
        items = sorted(best_ready.items(), key=lambda item: (bin(item[0][0]).count("1"), item[1]))
        for (mask, last), ready in items:
            for nxt, route in enumerate(routes):
                if mask & (1 << nxt):
                    continue
                evaluated = evaluate_route_at_start(data, route, ready)
                if evaluated is None:
                    continue
                next_key = (mask | (1 << nxt), nxt)
                next_ready = float(evaluated["ready_time"])
                if next_ready + CHECK_TOL < best_ready.get(next_key, float("inf")):
                    best_ready[next_key] = next_ready
                    parent[next_key] = (mask, last)

    best_last = None
    best_value = float("inf")
    for (mask, last), ready in best_ready.items():
        if mask == full_mask and ready <= data.horizon + CHECK_TOL and ready < best_value:
            best_last = last
            best_value = ready
    if best_last is None:
        return ScheduleCheckResult(False, tuple(), None)

    order = []
    cursor: tuple[int, int] | None = (full_mask, best_last)
    while cursor is not None:
        order.append(cursor[1])
        cursor = parent[cursor]
    order.reverse()
    return ScheduleCheckResult(True, tuple(order), round(best_value, 6))


def exact_route_set_schedule_capacity(
    data: BPCData,
    routes: list[RouteColumn] | tuple[RouteColumn, ...],
    *,
    max_states: int = 200000,
) -> RouteSetSchedulePackingResult | None:
    """精确计算同一辆车最多能从给定 route 集合中排程多少条。

    中文注释：候选 route 集合来自启发式分离，但这里的 DP 是证明环节。
    若状态数超过上限则返回 None，调用方不得加 cut。
    """

    route_list = list(routes)
    count = len(route_list)
    if count == 0:
        return RouteSetSchedulePackingResult(0, 0, True)

    max_count = min(count, int(data.sortie_limit))
    best_ready: dict[tuple[int, int], float] = {}
    states_explored = 0
    best_cardinality = 0

    for index, route in enumerate(route_list):
        evaluated = evaluate_route_at_start(data, route, 0.0)
        states_explored += 1
        if max_states > 0 and states_explored > max_states:
            return None
        if evaluated is None:
            continue
        key = (1 << index, index)
        best_ready[key] = float(evaluated["ready_time"])
        best_cardinality = max(best_cardinality, 1)

    for cardinality in range(1, max_count):
        items = [
            (state, ready)
            for state, ready in best_ready.items()
            if state[0].bit_count() == cardinality
        ]
        if not items:
            continue
        for (mask, _last), ready in sorted(items, key=lambda item: (item[1], item[0])):
            for nxt, route in enumerate(route_list):
                if mask & (1 << nxt):
                    continue
                evaluated = evaluate_route_at_start(data, route, ready)
                states_explored += 1
                if max_states > 0 and states_explored > max_states:
                    return None
                if evaluated is None:
                    continue
                next_mask = mask | (1 << nxt)
                next_key = (next_mask, nxt)
                next_ready = float(evaluated["ready_time"])
                if next_ready + CHECK_TOL < best_ready.get(next_key, float("inf")):
                    best_ready[next_key] = next_ready
                    best_cardinality = max(best_cardinality, next_mask.bit_count())
                    if best_cardinality >= max_count:
                        return RouteSetSchedulePackingResult(max_count, states_explored, True)

    return RouteSetSchedulePackingResult(best_cardinality, states_explored, True)


def route_transition_ready_time(
    data: BPCData,
    first: RouteColumn,
    second: RouteColumn,
    *,
    start_time: float = 0.0,
) -> float | None:
    """返回 first 后接 second 的车辆 ready time；不可行则返回 None。"""

    first_eval = evaluate_route_at_start(data, first, start_time)
    if first_eval is None:
        return None
    second_eval = evaluate_route_at_start(data, second, float(first_eval["ready_time"]))
    if second_eval is None:
        return None
    return float(second_eval["ready_time"])


def find_route_pair_schedule_conflicts(
    data: BPCData,
    routes: list[RouteColumn] | tuple[RouteColumn, ...],
    *,
    max_pairs: int = 0,
) -> tuple[RoutePairScheduleConflict, ...]:
    """找出无论 p->q 还是 q->p 都不可行的 route pair。

    中文注释：如果一对 route 从时间 0 开始的任一先后顺序都不可行，那么在任何更晚
    的部分 schedule 中也不可行，因此可安全加入 lambda[p,r]+lambda[q,r]<=y[r]。
    """

    conflicts: list[RoutePairScheduleConflict] = []
    route_list = list(routes)
    for left_index, left in enumerate(route_list):
        left_eval = evaluate_route_at_start(data, left, 0.0)
        left_ready = None if left_eval is None else float(left_eval["ready_time"])
        for right in route_list[left_index + 1 :]:
            right_eval = evaluate_route_at_start(data, right, 0.0)
            right_ready = None if right_eval is None else float(right_eval["ready_time"])
            left_then_right = route_transition_ready_time(data, left, right)
            right_then_left = route_transition_ready_time(data, right, left)
            if left_then_right is not None or right_then_left is not None:
                continue
            conflicts.append(
                RoutePairScheduleConflict(
                    left=left,
                    right=right,
                    left_ready_time=left_ready,
                    right_ready_time=right_ready,
                    left_then_right_ready_time=left_then_right,
                    right_then_left_ready_time=right_then_left,
                )
            )
            if max_pairs > 0 and len(conflicts) >= max_pairs:
                return tuple(conflicts)
    return tuple(conflicts)


def diagnose_route_set_schedule(
    data: BPCData,
    routes: list[RouteColumn] | tuple[RouteColumn, ...],
    *,
    max_pair_conflicts: int = 8,
) -> ScheduleInfeasibilityWitness | None:
    """对不可排程 route 集合返回可用于 cut 的结构化 witness。"""

    route_list = list(routes)
    if check_route_set_schedule_feasible(data, route_list).feasible:
        return None
    core = tuple(shrink_infeasible_route_set(data, route_list))
    pair_conflicts = find_route_pair_schedule_conflicts(data, core, max_pairs=max_pair_conflicts)
    return ScheduleInfeasibilityWitness(
        routes=core,
        pair_conflicts=pair_conflicts,
        reason="pair_transition" if pair_conflicts else "set_order",
        deletion_minimal=True,
    )


def shrink_infeasible_route_set(data: BPCData, routes: list[RouteColumn]) -> list[RouteColumn]:
    conflict = list(routes)
    changed = True
    while changed and len(conflict) > 1:
        changed = False
        for route in list(conflict):
            candidate = [item for item in conflict if item is not route]
            if candidate and not check_route_set_schedule_feasible(data, candidate).feasible:
                conflict = candidate
                changed = True
                break
    return conflict
