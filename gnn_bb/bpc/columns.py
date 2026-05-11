"""中文摘要：本文件定义 route column，并提供单条 sortie route 的资源可行性评价。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .data import BPCData


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


@dataclass(frozen=True)
class RouteColumn:
    id: int
    tasks: tuple[int, ...]
    task_set: frozenset[int]
    load: float
    travel_time: float
    return_time: float
    energy: float
    cost: float
    cycle_time: float
    service_start: dict[str, float]
    physical_paths: tuple[dict[str, Any], ...]

    @property
    def signature(self) -> tuple[int, ...]:
        return self.tasks


class RoutePool:
    """中文注释：只保存已经生成的 route 签名，RMP 中的 route-vehicle 变量每次按节点重建。"""

    def __init__(self) -> None:
        self.routes: list[RouteColumn] = []
        self.by_signature: dict[tuple[int, ...], RouteColumn] = {}

    def add(self, route: RouteColumn) -> RouteColumn:
        existing = self.by_signature.get(route.signature)
        if existing is not None:
            return existing
        stored = replace(route, id=len(self.routes))
        self.routes.append(stored)
        self.by_signature[stored.signature] = stored
        return stored

    def contains(self, signature: tuple[int, ...]) -> bool:
        return tuple(signature) in self.by_signature


def route_work_time_lower_bound(data: BPCData, route: RouteColumn) -> float:
    # 中文注释：这是任意排程下该 sortie 至少占用车辆的时间；等待时间不放入 master，避免误删真实可行解。
    service_time = sum(data.task_value(task, "sigma") for task in route.tasks)
    return float(route.travel_time) + service_time + float(route.energy) / data.rho


def evaluate_route(data: BPCData, sequence: tuple[int, ...] | list[int]) -> RouteColumn | None:
    sequence = tuple(int(task) for task in sequence)
    load = sum(data.task_value(task, "d") for task in sequence)
    if load > data.capacity + 1.0e-9:
        return None

    current = 0
    current_time = 0.0
    travel_time = 0.0
    travel_energy = 0.0
    travel_cost = 0.0
    service_energy = 0.0
    service_cost = 0.0
    service_start: dict[str, float] = {}
    physical_paths: list[dict[str, Any]] = []

    for task_id in sequence:
        segment = data.arc(current, task_id)
        travel_time += float(segment["tau"])
        travel_energy += float(segment["energy"])
        travel_cost += float(segment["cost"])
        physical_paths.append({"from": current, "to": task_id, "path": segment.get("path", [])})

        arrival = current_time + float(segment["tau"])
        start = max(data.task_value(task_id, "r"), arrival)
        finish = start + data.task_value(task_id, "sigma")
        if finish > data.task_value(task_id, "D") + 1.0e-9:
            return None

        service_start[str(task_id)] = _round(start)
        current_time = finish
        service_energy += data.task_value(task_id, "g")
        service_cost += data.task_value(task_id, "c_srv")
        current = task_id

    back = data.arc(current, 0)
    travel_time += float(back["tau"])
    travel_energy += float(back["energy"])
    travel_cost += float(back["cost"])
    physical_paths.append({"from": current, "to": 0, "path": back.get("path", [])})

    return_time = current_time + float(back["tau"])
    total_energy = travel_energy + service_energy
    total_cost = travel_cost + service_cost
    if total_energy > data.energy_limit + 1.0e-9 or return_time > data.horizon + 1.0e-9:
        return None

    return RouteColumn(
        id=-1,
        tasks=sequence,
        task_set=frozenset(sequence),
        load=_round(load),
        travel_time=_round(travel_time),
        return_time=_round(return_time),
        energy=_round(total_energy),
        cost=_round(total_cost),
        cycle_time=_round(return_time + total_energy / data.rho),
        service_start=service_start,
        physical_paths=tuple(physical_paths),
    )


def route_to_json(route: RouteColumn) -> dict[str, Any]:
    return {
        "id": int(route.id),
        "tasks": list(route.tasks),
        "task_set": sorted(route.task_set),
        "load": route.load,
        "travel_time": route.travel_time,
        "return_time": route.return_time,
        "energy": route.energy,
        "cost": route.cost,
        "cycle_time": route.cycle_time,
        "service_start": route.service_start,
        "physical_paths": list(route.physical_paths),
    }
