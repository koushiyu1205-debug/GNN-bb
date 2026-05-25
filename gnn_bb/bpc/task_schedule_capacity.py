"""Task-level schedule-capacity candidate generation and oracle cache records.

This module is intentionally solver-agnostic: it ranks candidate task sets for
the route-vehicle master, but every cut still needs an exact oracle certificate
from :mod:`bpc.schedule_capacity` before it is valid.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import Any

from .columns import RouteColumn
from .data import BPCData


STRONG_WITNESS_SOURCES = frozenset({"rim_witness", "route_pack_witness", "incompatibility_witness"})


@dataclass
class TaskScheduleCapacityCandidate:
    tasks: tuple[int, ...]
    vehicle: int
    source: str
    activity: float
    y_value: float
    potential_violation_u1: float
    score: float
    from_rim_conflict: bool = False
    from_route_pack_witness: bool = False
    from_incompatibility_witness: bool = False
    from_top_z_mass: bool = False
    from_time_window_cluster: bool = False
    from_support_route_union: bool = False
    source_count: int = 1

    @property
    def size(self) -> int:
        return len(self.tasks)

    @property
    def has_strong_witness(self) -> bool:
        return self.from_rim_conflict or self.from_route_pack_witness or self.from_incompatibility_witness

    def merge(self, other: "TaskScheduleCapacityCandidate") -> None:
        self.source = _merge_sources(self.source, other.source)
        self.score = max(float(self.score), float(other.score))
        self.activity = max(float(self.activity), float(other.activity))
        self.potential_violation_u1 = max(float(self.potential_violation_u1), float(other.potential_violation_u1))
        self.from_rim_conflict = self.from_rim_conflict or other.from_rim_conflict
        self.from_route_pack_witness = self.from_route_pack_witness or other.from_route_pack_witness
        self.from_incompatibility_witness = self.from_incompatibility_witness or other.from_incompatibility_witness
        self.from_top_z_mass = self.from_top_z_mass or other.from_top_z_mass
        self.from_time_window_cluster = self.from_time_window_cluster or other.from_time_window_cluster
        self.from_support_route_union = self.from_support_route_union or other.from_support_route_union
        self.source_count += int(other.source_count)

    def compact(self) -> dict[str, Any]:
        return {
            "vehicle": int(self.vehicle),
            "tasks": list(self.tasks),
            "size": self.size,
            "source": self.source,
            "activity": round(float(self.activity), 9),
            "y": round(float(self.y_value), 9),
            "potential_violation_u1": round(float(self.potential_violation_u1), 9),
            "score": round(float(self.score), 9),
            "rim": bool(self.from_rim_conflict),
            "route_pack": bool(self.from_route_pack_witness),
            "incompatibility": bool(self.from_incompatibility_witness),
            "top_z": bool(self.from_top_z_mass),
            "time_window_cluster": bool(self.from_time_window_cluster),
            "support_route_union": bool(self.from_support_route_union),
        }


@dataclass
class TaskScheduleCapacityCacheEntry:
    tasks: tuple[int, ...]
    upper_bound: int | None
    states_explored: int
    exact: bool
    incomplete: bool
    infeasible: bool
    feasible: bool
    oracle_time: float
    hit_count: int = 0
    last_used_node: int | None = None
    source_count: dict[str, int] = field(default_factory=dict)

    def record_use(self, *, node_id: int, source: str, cache_hit: bool) -> None:
        if cache_hit:
            self.hit_count += 1
        self.last_used_node = int(node_id)
        self.source_count[source] = self.source_count.get(source, 0) + 1


@dataclass
class TaskScheduleCapacityWitness:
    tasks: tuple[int, ...]
    source: str
    vehicle: int | None = None
    node_id: int | None = None
    count: int = 1
    route_count: int = 0
    last_violation: float = 0.0

    @property
    def is_strong(self) -> bool:
        return any(part in STRONG_WITNESS_SOURCES for part in self.source.split("+"))

    def merge(self, other: "TaskScheduleCapacityWitness") -> None:
        self.source = _merge_sources(self.source, other.source)
        self.count += int(other.count)
        self.route_count = max(int(self.route_count), int(other.route_count))
        self.last_violation = max(float(self.last_violation), float(other.last_violation))
        if other.node_id is not None:
            self.node_id = int(other.node_id)

    def compact(self) -> dict[str, Any]:
        return {
            "tasks": list(self.tasks),
            "size": len(self.tasks),
            "source": self.source,
            "vehicle": self.vehicle,
            "node_id": self.node_id,
            "count": self.count,
            "route_count": self.route_count,
            "last_violation": round(float(self.last_violation), 9),
        }


@dataclass
class TaskScheduleCapacityGenerationResult:
    candidates: list[TaskScheduleCapacityCandidate]
    diagnostics: dict[str, Any]


def generate_task_schedule_capacity_candidates(
    data: BPCData,
    *,
    vehicles: tuple[int, ...],
    y_values: dict[int, float],
    task_values_by_vehicle: dict[int, list[tuple[float, int]]],
    support_routes_by_vehicle: dict[int, list[tuple[float, RouteColumn]]],
    witness_memory: dict[tuple[int, ...], TaskScheduleCapacityWitness],
    min_violation: float,
    pair_budget: int,
    triple_budget: int,
    small_set_budget: int,
    max_subset_size: int,
    use_rim_witness: bool,
    use_route_pack_witness: bool,
    use_incompatibility_witness: bool,
    use_top_z_mass: bool = True,
    use_support_route_union: bool = True,
    use_time_window_clusters: bool = False,
    successful_task_sets: set[tuple[int, ...]] | None = None,
) -> TaskScheduleCapacityGenerationResult:
    """Generate sorted, budgeted candidates that pass the U=1 cheap precheck."""

    successful_task_sets = successful_task_sets or set()
    max_subset_size = max(2, min(int(max_subset_size), len(data.tasks)))
    pair_budget = max(0, int(pair_budget))
    triple_budget = max(0, int(triple_budget))
    small_set_budget = max(0, int(small_set_budget))
    candidate_by_key: dict[tuple[int, tuple[int, ...]], TaskScheduleCapacityCandidate] = {}
    raw_source_counts: dict[str, int] = {}
    precheck_source_counts: dict[str, int] = {}
    diagnostics: dict[str, Any] = {
        "vehicles_checked": 0,
        "vehicles_active": 0,
        "candidates_generated": 0,
        "candidates_after_precheck": 0,
        "pair_candidates": 0,
        "triple_candidates": 0,
        "small_set_candidates": 0,
        "candidates_by_source": raw_source_counts,
        "prechecked_by_source": precheck_source_counts,
        "candidate_size_max": 0,
        "best_precheck_violation": 0.0,
    }

    def activity_for(tasks: tuple[int, ...], value_by_task: dict[int, float]) -> float:
        return float(sum(value_by_task.get(int(task), 0.0) for task in tasks))

    def add_candidate(
        vehicle: int,
        tasks_raw: tuple[int, ...] | list[int] | set[int],
        source: str,
        value_by_task: dict[int, float],
        *,
        from_rim: bool = False,
        from_route_pack: bool = False,
        from_incompatibility: bool = False,
        from_top_z: bool = False,
        from_time_window: bool = False,
        from_support_route_union: bool = False,
    ) -> None:
        tasks = tuple(sorted({int(task) for task in tasks_raw}))
        size = len(tasks)
        if size < 2 or size > max_subset_size:
            return
        if size > 3 and not (from_rim or from_route_pack or from_incompatibility):
            return
        diagnostics["candidates_generated"] = int(diagnostics["candidates_generated"]) + 1
        raw_source_counts[source] = raw_source_counts.get(source, 0) + 1
        y_value = float(y_values.get(int(vehicle), 0.0))
        if y_value <= 0.0:
            return
        activity = activity_for(tasks, value_by_task)
        potential = activity - y_value
        if potential <= min_violation:
            return
        diagnostics["candidates_after_precheck"] = int(diagnostics["candidates_after_precheck"]) + 1
        diagnostics["candidate_size_max"] = max(int(diagnostics["candidate_size_max"]), size)
        diagnostics["best_precheck_violation"] = max(float(diagnostics["best_precheck_violation"]), float(potential))
        precheck_source_counts[source] = precheck_source_counts.get(source, 0) + 1
        if size == 2:
            diagnostics["pair_candidates"] = int(diagnostics["pair_candidates"]) + 1
        elif size == 3:
            diagnostics["triple_candidates"] = int(diagnostics["triple_candidates"]) + 1
        else:
            diagnostics["small_set_candidates"] = int(diagnostics["small_set_candidates"]) + 1

        strong = 3.0 if (from_rim or from_route_pack or from_incompatibility) else 0.0
        history = 1.0 if tasks in successful_task_sets else 0.0
        cost_estimate = 0.01 * size
        score = float(potential) + strong + history - cost_estimate
        candidate = TaskScheduleCapacityCandidate(
            tasks=tasks,
            vehicle=int(vehicle),
            source=source,
            activity=activity,
            y_value=y_value,
            potential_violation_u1=potential,
            score=score,
            from_rim_conflict=from_rim,
            from_route_pack_witness=from_route_pack,
            from_incompatibility_witness=from_incompatibility,
            from_top_z_mass=from_top_z,
            from_time_window_cluster=from_time_window,
            from_support_route_union=from_support_route_union,
        )
        key = (int(vehicle), tasks)
        existing = candidate_by_key.get(key)
        if existing is None:
            candidate_by_key[key] = candidate
        else:
            existing.merge(candidate)

    for vehicle_raw in vehicles:
        vehicle = int(vehicle_raw)
        diagnostics["vehicles_checked"] = int(diagnostics["vehicles_checked"]) + 1
        y_value = float(y_values.get(vehicle, 0.0))
        if y_value <= min_violation:
            continue
        diagnostics["vehicles_active"] = int(diagnostics["vehicles_active"]) + 1
        task_values = list(task_values_by_vehicle.get(vehicle, []))
        value_by_task = {int(task): float(value) for value, task in task_values}
        ordered_tasks = [int(task) for _value, task in task_values]

        if use_top_z_mass:
            pair_scan = min(len(ordered_tasks), max(2, int((2 * max(1, pair_budget)) ** 0.5) + 6))
            for tasks in combinations(ordered_tasks[:pair_scan], 2):
                add_candidate(vehicle, tasks, "top_z_pair", value_by_task, from_top_z=True)

            triple_scan = min(len(ordered_tasks), max(3, int((6 * max(1, triple_budget)) ** (1.0 / 3.0)) + 6))
            for tasks in combinations(ordered_tasks[:triple_scan], 3):
                add_candidate(vehicle, tasks, "top_z_triple", value_by_task, from_top_z=True)

        if use_support_route_union:
            for _route_value, route in support_routes_by_vehicle.get(vehicle, []):
                if len(route.task_set) in (2, 3):
                    add_candidate(vehicle, tuple(route.task_set), "support_route_union", value_by_task, from_support_route_union=True)
            support_routes = [route for _value, route in support_routes_by_vehicle.get(vehicle, [])]
            for left, right in combinations(support_routes[:8], 2):
                tasks = tuple(sorted(set(left.task_set) | set(right.task_set)))
                if len(tasks) in (2, 3):
                    add_candidate(vehicle, tasks, "support_route_union", value_by_task, from_support_route_union=True)

        if use_time_window_clusters:
            tw_tasks = sorted(
                ordered_tasks[: max(6, min(len(ordered_tasks), 12))],
                key=lambda task: (data.task_value(task, "D") - data.task_value(task, "r"), data.task_value(task, "D"), task),
            )
            for size in (2, 3):
                for start in range(0, max(0, len(tw_tasks) - size + 1)):
                    add_candidate(
                        vehicle,
                        tuple(tw_tasks[start : start + size]),
                        "time_window_cluster",
                        value_by_task,
                        from_time_window=True,
                    )

        for witness in witness_memory.values():
            source_parts = {part.strip() for part in witness.source.split("+") if part.strip()}
            has_rim = "rim_witness" in source_parts
            has_route_pack = "route_pack_witness" in source_parts
            has_incompatibility = "incompatibility_witness" in source_parts
            if not (
                (has_rim and use_rim_witness)
                or (has_route_pack and use_route_pack_witness)
                or (has_incompatibility and use_incompatibility_witness)
            ):
                continue
            tasks = tuple(int(task) for task in witness.tasks)
            source = witness.source
            flags = {
                "from_rim": has_rim and use_rim_witness,
                "from_route_pack": has_route_pack and use_route_pack_witness,
                "from_incompatibility": has_incompatibility and use_incompatibility_witness,
            }
            if 2 <= len(tasks) <= max_subset_size:
                add_candidate(vehicle, tasks, source, value_by_task, **flags)
            # Strong witnesses often contain a route union that is too large for
            # the oracle budget. Keep deterministic high-mass subsets only.
            ordered_witness_tasks = sorted(tasks, key=lambda task: (-value_by_task.get(int(task), 0.0), int(task)))
            for size in range(2, min(max_subset_size, len(ordered_witness_tasks)) + 1):
                if size > 3 and small_set_budget <= 0:
                    continue
                for subset in combinations(ordered_witness_tasks[: min(len(ordered_witness_tasks), max(6, size))], size):
                    add_candidate(vehicle, subset, source, value_by_task, **flags)

    candidates = list(candidate_by_key.values())
    candidates.sort(
        key=lambda item: (
            -float(item.potential_violation_u1),
            -_source_strength(item),
            item.size,
            0 if item.tasks in successful_task_sets else 1,
            item.size,
            int(item.vehicle),
            item.tasks,
        )
    )
    kept: list[TaskScheduleCapacityCandidate] = []
    counts = {2: 0, 3: 0, "small": 0}
    for candidate in candidates:
        if candidate.size == 2:
            if counts[2] >= pair_budget:
                continue
            counts[2] += 1
        elif candidate.size == 3:
            if counts[3] >= triple_budget:
                continue
            counts[3] += 1
        else:
            if counts["small"] >= small_set_budget:
                continue
            counts["small"] += 1
        kept.append(candidate)
    return TaskScheduleCapacityGenerationResult(candidates=kept, diagnostics=diagnostics)


def witness_from_routes(
    routes: list[RouteColumn] | tuple[RouteColumn, ...],
    *,
    source: str,
    vehicle: int | None,
    node_id: int | None,
    violation: float = 0.0,
) -> TaskScheduleCapacityWitness | None:
    tasks = tuple(sorted({int(task) for route in routes for task in route.task_set}))
    if len(tasks) < 2:
        return None
    return TaskScheduleCapacityWitness(
        tasks=tasks,
        source=str(source),
        vehicle=None if vehicle is None else int(vehicle),
        node_id=None if node_id is None else int(node_id),
        route_count=len(routes),
        last_violation=float(violation),
    )


def _source_strength(candidate: TaskScheduleCapacityCandidate) -> int:
    if candidate.from_rim_conflict:
        return 5
    if candidate.from_route_pack_witness:
        return 4
    if candidate.from_incompatibility_witness:
        return 3
    if candidate.from_support_route_union:
        return 2
    if candidate.from_time_window_cluster:
        return 1
    return 0


def _merge_sources(left: str, right: str) -> str:
    parts = []
    for item in [*left.split("+"), *right.split("+")]:
        text = item.strip()
        if text and text not in parts:
            parts.append(text)
    return "+".join(parts) if parts else left or right
