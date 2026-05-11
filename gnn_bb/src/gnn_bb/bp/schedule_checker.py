"""中文摘要：本文件提供 route-vehicle BPC 使用的日程可行性检查器。它只判断已选 sortie routes 是否能排成真实车辆执行顺序，并生成安全的不可行组合 cut。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from typing import Any

from gnn_bb.data.io_utils import round_float
from gnn_bb.data.terrain import arc_key


CHECK_TOL = 1.0e-9


@dataclass(frozen=True)
class ScheduleCheckResult:
    feasible: bool
    order: tuple[int, ...]
    ready_time: float | None


def _task_value(instance: dict[str, Any], task_id: int, field_name: str) -> float:
    return float(instance["tasks"][str(task_id)][field_name])


def route_signature(route: dict[str, Any]) -> tuple[int, ...]:
    return tuple(int(task) for task in route.get("tasks", route.get("sequence", tuple())))


def route_work_time_lower_bound(instance: dict[str, Any], route: dict[str, Any]) -> float:
    # 中文注释：这是任意执行顺序下该 sortie 至少占用的工作时间；等待时间不计入下界，避免过度收紧 master。
    service_time = sum(_task_value(instance, int(task), "sigma") for task in route_signature(route))
    return float(route["travel_time"]) + service_time + float(route["energy"]) / float(instance["vehicles"]["rho"])


def evaluate_route_at_start(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    route: dict[str, Any],
    start_time: float,
) -> dict[str, Any] | None:
    vehicles = instance["vehicles"]
    q_limit = float(vehicles["Q"])
    b_limit = float(vehicles["B_use"])
    horizon = float(vehicles["H"])
    rho = float(vehicles["rho"])

    current = 0
    current_time = float(start_time)
    load = 0.0
    energy = 0.0
    cost = 0.0
    travel_time = 0.0
    service_start: dict[str, float] = {}

    for task_id in route_signature(route):
        segment = pairwise[arc_key(current, task_id)]
        arrival = current_time + float(segment["tau"])
        start = max(_task_value(instance, task_id, "r"), arrival)
        finish = start + _task_value(instance, task_id, "sigma")
        if finish > _task_value(instance, task_id, "D") + CHECK_TOL:
            return None
        load += _task_value(instance, task_id, "d")
        if load > q_limit + CHECK_TOL:
            return None
        energy += float(segment["energy"]) + _task_value(instance, task_id, "g")
        if energy > b_limit + CHECK_TOL:
            return None
        cost += float(segment["cost"]) + _task_value(instance, task_id, "c_srv")
        travel_time += float(segment["tau"])
        service_start[str(task_id)] = round_float(start)
        current = task_id
        current_time = finish

    back = pairwise[arc_key(current, 0)]
    return_time = current_time + float(back["tau"])
    energy += float(back["energy"])
    cost += float(back["cost"])
    travel_time += float(back["tau"])
    if energy > b_limit + CHECK_TOL:
        return None
    ready_time = return_time + energy / rho
    if ready_time > horizon + CHECK_TOL:
        return None

    return {
        "tasks": list(route_signature(route)),
        "start_time": round_float(start_time),
        "return_time": round_float(return_time),
        "ready_time": round_float(ready_time),
        "energy": round_float(energy),
        "cost": round_float(cost),
        "travel_time": round_float(travel_time),
        "service_start": service_start,
    }


def check_route_set_schedule_feasible(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    routes: list[dict[str, Any]],
) -> ScheduleCheckResult:
    if not routes:
        return ScheduleCheckResult(True, tuple(), 0.0)
    horizon = float(instance["vehicles"]["H"])
    count = len(routes)
    full_mask = (1 << count) - 1
    parent: dict[tuple[int, int], tuple[int, int] | None] = {}
    best_ready: dict[tuple[int, int], float] = {}

    for index, route in enumerate(routes):
        evaluated = evaluate_route_at_start(instance, pairwise, route, 0.0)
        if evaluated is None:
            continue
        mask = 1 << index
        ready = float(evaluated["ready_time"])
        best_ready[(mask, index)] = ready
        parent[(mask, index)] = None

    for _ in range(count):
        items = sorted(best_ready.items(), key=lambda item: (bin(item[0][0]).count("1"), item[1]))
        for (mask, last), ready in items:
            for nxt, route in enumerate(routes):
                if mask & (1 << nxt):
                    continue
                evaluated = evaluate_route_at_start(instance, pairwise, route, ready)
                if evaluated is None:
                    continue
                next_mask = mask | (1 << nxt)
                next_ready = float(evaluated["ready_time"])
                key = (next_mask, nxt)
                if next_ready + CHECK_TOL < best_ready.get(key, float("inf")):
                    best_ready[key] = next_ready
                    parent[key] = (mask, last)

    best_last = None
    best_value = float("inf")
    for (mask, last), ready in best_ready.items():
        if mask == full_mask and ready <= horizon + CHECK_TOL and ready < best_value:
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
    return ScheduleCheckResult(True, tuple(order), round_float(best_value))


def routes_pairwise_compatible(instance: dict[str, Any], pairwise: dict[str, dict[str, Any]], left: dict[str, Any], right: dict[str, Any]) -> bool:
    first = evaluate_route_at_start(instance, pairwise, left, 0.0)
    if first is not None and evaluate_route_at_start(instance, pairwise, right, float(first["ready_time"])) is not None:
        return True
    second = evaluate_route_at_start(instance, pairwise, right, 0.0)
    return second is not None and evaluate_route_at_start(instance, pairwise, left, float(second["ready_time"])) is not None


def find_pairwise_incompatible_cuts(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    routes: list[dict[str, Any]],
) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    cuts = []
    for left, right in combinations(routes, 2):
        if not routes_pairwise_compatible(instance, pairwise, left, right):
            cuts.append(tuple(sorted((route_signature(left), route_signature(right)))))
    return cuts


def shrink_infeasible_route_set(
    instance: dict[str, Any],
    pairwise: dict[str, dict[str, Any]],
    routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    conflict = list(routes)
    changed = True
    while changed and len(conflict) > 1:
        changed = False
        for route in list(conflict):
            candidate = [item for item in conflict if item is not route]
            if candidate and not check_route_set_schedule_feasible(instance, pairwise, candidate).feasible:
                conflict = candidate
                changed = True
                break
    return conflict
