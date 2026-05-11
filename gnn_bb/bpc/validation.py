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
