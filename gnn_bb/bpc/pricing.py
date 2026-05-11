"""中文摘要：本文件实现 clean BPC 的 exact RCSP pricing。它只用 true dual 定价，不做 heuristic pricing。"""

from __future__ import annotations

from dataclasses import dataclass
import heapq
from typing import Any

from .branching import BranchConstraint, partial_sequence_allowed, route_allowed_by_branch, route_branch_coefficient
from .columns import RouteColumn, evaluate_route, route_work_time_lower_bound
from .cuts import ScheduleNoGoodCut
from .data import BPCData
from .rmp import RMPDuals


@dataclass(order=True)
class Label:
    priority: float
    node: int
    sequence: tuple[int, ...]
    time: float
    load: float
    energy: float
    travel_time: float
    cost: float


@dataclass
class PricingResult:
    routes: list[RouteColumn]
    exhausted: bool
    best_reduced_cost: float | None
    label_pops: int
    generated_labels: int
    negative_routes: int


def reduced_cost(
    data: BPCData,
    route: RouteColumn,
    vehicle: int,
    duals: RMPDuals,
    cuts: list[ScheduleNoGoodCut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    phase: str,
) -> float:
    route_cost = 0.0 if phase == "phase1" else float(route.cost)
    value = (
        route_cost
        - sum(float(duals.cover[task]) for task in route.task_set)
        - float(duals.sortie_count[vehicle])
        - float(duals.vehicle_time[vehicle]) * route_work_time_lower_bound(data, route)
    )
    for cut in cuts:
        coeff = cut.coefficient(route, vehicle)
        if coeff:
            value -= float(duals.cuts.get(cut.id, 0.0)) * coeff
    for index, constraint in enumerate(branch_constraints):
        coeff = route_branch_coefficient(route, vehicle, constraint)
        if coeff:
            value -= float(duals.branches.get(index, 0.0)) * coeff
    return value


def _label_priority(sequence: tuple[int, ...], cost: float, duals: RMPDuals, phase: str) -> float:
    # 中文注释：priority 只影响遍历顺序；最终证明依赖完整枚举，不依赖这个启发式。
    base = 0.0 if phase == "phase1" else cost
    return base - sum(float(duals.cover[task]) for task in sequence)


def exact_pricing(
    data: BPCData,
    routes: list[RouteColumn],
    duals: RMPDuals,
    cuts: list[ScheduleNoGoodCut],
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    phase: str,
    eps: float,
    max_routes_to_return: int,
    max_labels: int = 0,
) -> PricingResult:
    existing_signatures = {route.signature for route in routes}
    candidate_by_signature: dict[tuple[int, ...], tuple[float, RouteColumn]] = {}
    best_reduced_cost: float | None = None
    label_pops = 0
    generated_labels = 0
    exhausted = True

    for vehicle in data.vehicles:
        queue: list[Label] = [Label(0.0, 0, tuple(), 0.0, 0.0, 0.0, 0.0, 0.0)]
        while queue:
            if max_labels > 0 and label_pops >= max_labels:
                exhausted = False
                break
            label = heapq.heappop(queue)
            label_pops += 1
            for task in data.tasks:
                if task in label.sequence:
                    continue
                next_sequence = (*label.sequence, int(task))
                if not partial_sequence_allowed(next_sequence, vehicle, branch_constraints):
                    continue

                segment = data.arc(label.node, task)
                arrival = label.time + float(segment["tau"])
                start = max(data.task_value(task, "r"), arrival)
                finish = start + data.task_value(task, "sigma")
                if finish > data.task_value(task, "D") + 1.0e-9:
                    continue
                next_load = label.load + data.task_value(task, "d")
                if next_load > data.capacity + 1.0e-9:
                    continue
                next_energy = label.energy + float(segment["energy"]) + data.task_value(task, "g")
                if next_energy > data.energy_limit + 1.0e-9:
                    continue
                return_segment = data.arc(task, 0)
                return_time = finish + float(return_segment["tau"])
                total_energy = next_energy + float(return_segment["energy"])
                if return_time > data.horizon + 1.0e-9 or total_energy > data.energy_limit + 1.0e-9:
                    continue

                next_cost = label.cost + float(segment["cost"]) + data.task_value(task, "c_srv")
                next_label = Label(
                    priority=_label_priority(next_sequence, next_cost, duals, phase),
                    node=int(task),
                    sequence=next_sequence,
                    time=finish,
                    load=next_load,
                    energy=next_energy,
                    travel_time=label.travel_time + float(segment["tau"]),
                    cost=next_cost,
                )
                generated_labels += 1

                if next_sequence not in existing_signatures:
                    route = evaluate_route(data, next_sequence)
                    if route is not None and route_allowed_by_branch(route, vehicle, branch_constraints):
                        rc = reduced_cost(data, route, vehicle, duals, cuts, branch_constraints, phase=phase)
                        best_reduced_cost = rc if best_reduced_cost is None else min(best_reduced_cost, rc)
                        if rc < -eps:
                            current = candidate_by_signature.get(route.signature)
                            if current is None or rc < current[0]:
                                candidate_by_signature[route.signature] = (rc, route)
                heapq.heappush(queue, next_label)
        if not exhausted:
            break

    candidates = sorted(candidate_by_signature.values(), key=lambda item: item[0])
    if max_routes_to_return > 0:
        candidates = candidates[:max_routes_to_return]
    return PricingResult(
        routes=[route for _rc, route in candidates],
        exhausted=exhausted,
        best_reduced_cost=best_reduced_cost,
        label_pops=label_pops,
        generated_labels=generated_labels,
        negative_routes=len(candidate_by_signature),
    )
