"""中文摘要：生成 Layer 1 portfolio sortie route pool，并计算 route reduced contribution。"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import heapq
from typing import Any

from .branching import BranchConstraint, same_components
from .columns import Sortie
from .data import InstanceData
from .rmp import RMPDuals


@dataclass(frozen=True)
class SortieRoute:
    tasks: tuple[int, ...]
    task_set: frozenset[int]
    cost: float
    ready_time_at_zero: float
    load: float
    energy: float
    service_start_at_zero: dict[str, float]
    same_component_hits: tuple[tuple[int, tuple[int, ...]], ...] = field(default_factory=tuple, compare=False)

    @property
    def signature(self) -> tuple[int, ...]:
        return self.tasks


@dataclass
class RoutePoolStats:
    route_pool_size: int = 0
    low_cbar_routes_kept: int = 0
    per_task_routes_kept: int = 0
    route_size_bucket_routes_kept: int = 0
    time_flexible_routes_kept: int = 0
    micro_routes_kept: int = 0
    branch_relevant_routes_kept: int = 0
    historical_routes_kept: int = 0
    diverse_routes_kept: int = 0
    generated_route_count: int = 0


@dataclass
class RoutePoolResult:
    routes: list[SortieRoute]
    stats: RoutePoolStats


@dataclass(order=True)
class _RouteLabel:
    priority: float
    node: int = field(compare=False)
    tasks: tuple[int, ...] = field(compare=False)
    time: float = field(compare=False)
    load: float = field(compare=False)
    energy: float = field(compare=False)
    cost: float = field(compare=False)
    service_start: dict[str, float] = field(compare=False)


def route_reduced_contribution(route: SortieRoute, duals: RMPDuals, phase: str) -> float:
    base = 0.0 if phase == "phase1" else float(route.cost)
    return base - sum(float(duals.cover[task]) for task in route.task_set)


def evaluate_sortie_route(data: InstanceData, tasks: tuple[int, ...], start_time: float) -> Sortie | None:
    current = 0
    current_time = float(start_time)
    load = 0.0
    energy = 0.0
    cost = 0.0
    service_start: dict[str, float] = {}
    for task in tasks:
        segment = data.arc(current, task)
        arrival = current_time + float(segment["tau"])
        start = max(data.task_value(task, "r"), arrival)
        finish = start + data.task_value(task, "sigma")
        if finish > data.task_value(task, "D") + 1.0e-9:
            return None
        load += data.task_value(task, "d")
        energy += float(segment["energy"]) + data.task_value(task, "g")
        cost += float(segment["cost"]) + data.task_value(task, "c_srv")
        if load > data.capacity + 1.0e-9 or energy > data.energy_limit + 1.0e-9:
            return None
        service_start[str(task)] = round(start, 6)
        current = int(task)
        current_time = finish
    back = data.arc(current, 0)
    return_time = current_time + float(back["tau"])
    energy += float(back["energy"])
    cost += float(back["cost"])
    ready_time = return_time + energy / data.rho
    if energy > data.energy_limit + 1.0e-9 or ready_time > data.horizon + 1.0e-9:
        return None
    return Sortie(
        tasks=tuple(tasks),
        start_time=round(float(start_time), 6),
        return_time=round(return_time, 6),
        ready_time=round(ready_time, 6),
        load=round(load, 6),
        energy=round(energy, 6),
        cost=round(cost, 6),
        service_start=service_start,
    )


def sortie_from_zero(data: InstanceData, tasks: tuple[int, ...]) -> SortieRoute | None:
    sortie = evaluate_sortie_route(data, tasks, 0.0)
    if sortie is None:
        return None
    return SortieRoute(
        tasks=tuple(tasks),
        task_set=frozenset(tasks),
        cost=float(sortie.cost),
        ready_time_at_zero=float(sortie.ready_time),
        load=float(sortie.load),
        energy=float(sortie.energy),
        service_start_at_zero=dict(sortie.service_start),
    )


def route_allowed_by_branch(route: SortieRoute, constraints: tuple[BranchConstraint, ...]) -> bool:
    _components, separates = same_components(constraints)
    for left, right in separates:
        if route.task_set & left and route.task_set & right:
            return False
    return True


def route_same_component_hits(route: SortieRoute, constraints: tuple[BranchConstraint, ...]) -> tuple[tuple[int, tuple[int, ...]], ...]:
    components, _separates = same_components(constraints)
    hits = []
    for index, component in enumerate(components):
        covered = tuple(sorted(route.task_set & component))
        if covered:
            hits.append((index, covered))
    return tuple(hits)


def annotate_route_for_branch(route: SortieRoute, constraints: tuple[BranchConstraint, ...]) -> SortieRoute:
    return replace(route, same_component_hits=route_same_component_hits(route, constraints))


def generate_raw_routes(
    data: InstanceData,
    duals: RMPDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    *,
    phase: str,
    label_limit: int,
) -> list[SortieRoute]:
    routes: dict[tuple[int, ...], SortieRoute] = {}
    queue: list[_RouteLabel] = [_RouteLabel(0.0, 0, tuple(), 0.0, 0.0, 0.0, 0.0, {})]
    pops = 0
    while queue and (label_limit <= 0 or pops < label_limit):
        label = heapq.heappop(queue)
        pops += 1
        for task in data.tasks:
            if task in label.tasks:
                continue
            tasks = (*label.tasks, int(task))
            segment = data.arc(label.node, task)
            arrival = label.time + float(segment["tau"])
            start = max(data.task_value(task, "r"), arrival)
            finish = start + data.task_value(task, "sigma")
            if finish > data.task_value(task, "D") + 1.0e-9:
                continue
            load = label.load + data.task_value(task, "d")
            if load > data.capacity + 1.0e-9:
                continue
            energy = label.energy + float(segment["energy"]) + data.task_value(task, "g")
            if energy > data.energy_limit + 1.0e-9:
                continue
            back = data.arc(task, 0)
            if finish + float(back["tau"]) > data.horizon + 1.0e-9:
                continue
            if energy + float(back["energy"]) > data.energy_limit + 1.0e-9:
                continue
            route = sortie_from_zero(data, tasks)
            if route is not None and route_allowed_by_branch(route, branch_constraints):
                routes.setdefault(route.signature, annotate_route_for_branch(route, branch_constraints))
            service_start = dict(label.service_start)
            service_start[str(task)] = round(start, 6)
            cost = label.cost + float(segment["cost"]) + data.task_value(task, "c_srv")
            priority = (0.0 if phase == "phase1" else cost) - sum(float(duals.cover[t]) for t in tasks)
            heapq.heappush(queue, _RouteLabel(priority, int(task), tasks, finish, load, energy, cost, service_start))
    return list(routes.values())


def build_portfolio_routes(
    data: InstanceData,
    duals: RMPDuals,
    branch_constraints: tuple[BranchConstraint, ...],
    historical_routes: list[SortieRoute],
    config: dict[str, Any],
    *,
    phase: str,
) -> RoutePoolResult:
    label_limit = max(100, int(config.get("max_new_routes_per_pricing_round", 1000)) * 20)
    raw = generate_raw_routes(data, duals, branch_constraints, phase=phase, label_limit=label_limit)
    by_signature: dict[tuple[int, ...], SortieRoute] = {}
    stats = RoutePoolStats(generated_route_count=len(raw))

    def add(route: SortieRoute, counter: str) -> None:
        if route.signature in by_signature:
            setattr(stats, counter, getattr(stats, counter) + 1)
            return
        if len(by_signature) >= int(config.get("max_routes_in_pricing_pool", 2000)):
            return
        by_signature[route.signature] = route
        setattr(stats, counter, getattr(stats, counter) + 1)

    scored = sorted(raw, key=lambda route: route_reduced_contribution(route, duals, phase))
    for route in scored[: int(config.get("low_cbar_route_quota", 500))]:
        add(route, "low_cbar_routes_kept")

    per_task_quota = int(config.get("per_task_route_quota", 20))
    for task in data.tasks:
        task_routes = [route for route in scored if task in route.task_set]
        for route in task_routes[:per_task_quota]:
            add(route, "per_task_routes_kept")

    route_size_quota = int(config.get("route_size_bucket_quota", 100))
    for size_group in (1, 2, 3, 4):
        if size_group < 4:
            bucket = [route for route in scored if len(route.tasks) == size_group]
        else:
            bucket = [route for route in scored if len(route.tasks) >= size_group]
        for route in bucket[:route_size_quota]:
            add(route, "route_size_bucket_routes_kept")

    def route_slack(route: SortieRoute) -> float:
        return min(
            data.task_value(task, "D") - float(route.service_start_at_zero.get(str(task), 0.0))
            for task in route.task_set
        )

    flexible = sorted(raw, key=lambda route: (route.ready_time_at_zero, -route_slack(route), len(route.tasks), route.cost))
    for route in flexible[: int(config.get("time_flexible_route_quota", 200))]:
        add(route, "time_flexible_routes_kept")

    micro = sorted(raw, key=lambda route: (route.ready_time_at_zero, len(route.tasks), route.cost))
    for route in micro[: int(config.get("micro_route_quota", 200))]:
        add(route, "micro_routes_kept")

    same_components_list, _separates = same_components(branch_constraints)
    same_component_tasks = set().union(*same_components_list) if same_components_list else set()
    branch_tasks = {constraint.i for constraint in branch_constraints} | {constraint.j for constraint in branch_constraints}
    if same_component_tasks:
        branch_relevant = [
            route
            for route in scored
            if any(route.task_set & component for component in same_components_list)
        ]
    else:
        branch_relevant = [route for route in scored if route.task_set & branch_tasks]
    for route in branch_relevant[: int(config.get("branch_relevant_route_quota", 300))]:
        add(route, "branch_relevant_routes_kept")

    for route in historical_routes[: int(config.get("historical_route_quota", 300))]:
        if route_allowed_by_branch(route, branch_constraints):
            add(annotate_route_for_branch(route, branch_constraints), "historical_routes_kept")

    def diversity_key(route: SortieRoute) -> tuple[frozenset[int], int, int]:
        first_release = min(data.task_value(task, "r") for task in route.task_set)
        cluster_size = max(1.0, float(config.get("diverse_time_cluster_size", 30)))
        return (route.task_set, len(route.tasks), int(first_release // cluster_size))

    seen_diverse_keys: set[tuple[frozenset[int], int, int]] = set()
    for route in scored:
        key = diversity_key(route)
        if key in seen_diverse_keys:
            continue
        seen_diverse_keys.add(key)
        add(route, "diverse_routes_kept")
        if stats.diverse_routes_kept >= int(config.get("diverse_route_quota", 300)):
            break

    stats.route_pool_size = len(by_signature)
    return RoutePoolResult(list(by_signature.values()), stats)
