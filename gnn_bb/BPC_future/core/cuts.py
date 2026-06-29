"""Pricing-compatible cuts for the BPC_future trip-time master."""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
from typing import Protocol

from BPC_future.core.columns import TimedTrip
from BPC_future.core.data import FutureData


class FutureCut(Protocol):
    kind: str
    key: tuple
    sense: str
    rhs: float

    def coefficient(self, trip: TimedTrip, vehicle: int) -> float:
        ...

    def y_coefficient(self, vehicle: int) -> float:
        ...

    def payload(self) -> dict:
        ...


@dataclass(frozen=True)
class FleetLowerBoundCut:
    lb: int
    kind: str = "fleet_lower_bound"
    sense: str = ">="

    @property
    def rhs(self) -> float:
        return float(self.lb)

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.lb))

    def coefficient(self, trip: TimedTrip, vehicle: int) -> float:
        return 0.0

    def y_coefficient(self, vehicle: int) -> float:
        return 1.0

    def payload(self) -> dict:
        return {"kind": self.kind, "lb": int(self.lb), "rhs": self.rhs}


@dataclass(frozen=True)
class FleetUpperBoundCut:
    ub: int
    incumbent: float
    unavoidable_cost_lb: float
    kind: str = "fleet_upper_bound"
    sense: str = "<="

    @property
    def rhs(self) -> float:
        return float(self.ub)

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.ub))

    def coefficient(self, trip: TimedTrip, vehicle: int) -> float:
        return 0.0

    def y_coefficient(self, vehicle: int) -> float:
        return 1.0

    def payload(self) -> dict:
        return {
            "kind": self.kind,
            "ub": int(self.ub),
            "rhs": self.rhs,
            "incumbent": round(float(self.incumbent), 6),
            "unavoidable_cost_lb": round(float(self.unavoidable_cost_lb), 6),
        }


@dataclass(frozen=True)
class FleetPrefixDisableCut:
    max_vehicle: int
    kind: str = "fleet_prefix_disable"
    sense: str = "<="

    @property
    def rhs(self) -> float:
        return 0.0

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.max_vehicle))

    def coefficient(self, trip: TimedTrip, vehicle: int) -> float:
        return 0.0

    def y_coefficient(self, vehicle: int) -> float:
        return 1.0 if int(vehicle) > int(self.max_vehicle) else 0.0

    def payload(self) -> dict:
        return {"kind": self.kind, "max_vehicle": int(self.max_vehicle), "rhs": self.rhs}


@dataclass(frozen=True)
class SortieLowerBoundCut:
    lb: int
    kind: str = "sortie_lower_bound"
    sense: str = "<="

    @property
    def rhs(self) -> float:
        return -float(self.lb)

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.lb))

    def coefficient(self, trip: TimedTrip, vehicle: int) -> float:
        return -1.0

    def y_coefficient(self, vehicle: int) -> float:
        return 0.0

    def payload(self) -> dict:
        return {"kind": self.kind, "lb": int(self.lb), "rhs": self.rhs}


@dataclass(frozen=True)
class SubsetRowCut:
    tasks: tuple[int, ...]
    k: int
    kind: str = "subset_row"
    sense: str = "<="

    def __post_init__(self) -> None:
        object.__setattr__(self, "tasks", tuple(sorted(int(task) for task in self.tasks)))
        if int(self.k) <= 1:
            raise ValueError("subset-row k must be greater than 1")

    @property
    def rhs(self) -> float:
        return float(len(self.tasks) // int(self.k))

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.k), self.tasks)

    def coefficient(self, trip: TimedTrip, vehicle: int) -> float:
        overlap = len(set(self.tasks).intersection(trip.task_set))
        return float(overlap // int(self.k))

    def y_coefficient(self, vehicle: int) -> float:
        return 0.0

    def payload(self) -> dict:
        return {
            "kind": self.kind,
            "tasks": list(self.tasks),
            "k": int(self.k),
            "rhs": self.rhs,
        }


@dataclass(frozen=True)
class WeightedSubsetRowCut:
    """Rank-1-like task subset row used first as an audit contract.

    This is the weighted generalization of ``SubsetRowCut``:

        coeff(column) = floor(sum_i weight_i * a_i(column) / denominator)
        rhs = floor(sum_i weight_i / denominator)

    With nonnegative fractional multipliers over the task-cover equalities, the
    row is valid for integer journey selections.  Live pricing support is kept
    separate; the current BPC_future solver only audits these rows unless a
    future pricing-compatible implementation explicitly enables them.
    """

    tasks: tuple[int, ...]
    weights: tuple[int, ...]
    denominator: int
    kind: str = "weighted_subset_row"
    sense: str = "<="

    def __post_init__(self) -> None:
        if len(self.tasks) != len(self.weights):
            raise ValueError("weighted subset row tasks and weights must have the same length")
        denominator = int(self.denominator)
        if denominator <= 1:
            raise ValueError("weighted subset row denominator must be greater than 1")
        pairs = sorted((int(task), int(weight)) for task, weight in zip(self.tasks, self.weights))
        if any(weight <= 0 for _task, weight in pairs):
            raise ValueError("weighted subset row weights must be positive")
        if any(weight >= denominator for _task, weight in pairs):
            raise ValueError("weighted subset row weights must be smaller than denominator")
        object.__setattr__(self, "tasks", tuple(task for task, _weight in pairs))
        object.__setattr__(self, "weights", tuple(weight for _task, weight in pairs))
        object.__setattr__(self, "denominator", denominator)

    @property
    def rhs(self) -> float:
        return float(sum(int(weight) for weight in self.weights) // int(self.denominator))

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.denominator), self.tasks, self.weights)

    def coefficient(self, trip: TimedTrip, vehicle: int) -> float:
        task_set = set(int(task) for task in trip.task_set)
        weighted_overlap = sum(
            int(weight)
            for task, weight in zip(self.tasks, self.weights)
            if int(task) in task_set
        )
        return float(weighted_overlap // int(self.denominator))

    def y_coefficient(self, vehicle: int) -> float:
        return 0.0

    def payload(self) -> dict:
        return {
            "kind": self.kind,
            "tasks": list(self.tasks),
            "weights": list(self.weights),
            "denominator": int(self.denominator),
            "rhs": self.rhs,
        }


@dataclass(frozen=True)
class TimePointCapacityCut:
    vehicle: int
    time_point: float
    kind: str = "time_point_capacity"
    sense: str = "<="

    def __post_init__(self) -> None:
        object.__setattr__(self, "vehicle", int(self.vehicle))
        object.__setattr__(self, "time_point", round(float(self.time_point), 6))

    @property
    def rhs(self) -> float:
        return 0.0

    @property
    def key(self) -> tuple:
        return (self.kind, int(self.vehicle), round(float(self.time_point), 6))

    def coefficient(self, trip: TimedTrip, vehicle: int) -> float:
        if int(vehicle) != int(self.vehicle):
            return 0.0
        point = float(self.time_point)
        return 1.0 if trip.start_time <= point + 1.0e-9 and point < trip.end_time - 1.0e-9 else 0.0

    def y_coefficient(self, vehicle: int) -> float:
        return -1.0 if int(vehicle) == int(self.vehicle) else 0.0

    def payload(self) -> dict:
        return {
            "kind": self.kind,
            "vehicle": int(self.vehicle),
            "time_point": round(float(self.time_point), 6),
            "rhs": self.rhs,
        }


@dataclass
class CutSeparationResult:
    generated: int = 0
    added: int = 0
    duplicate: int = 0
    best_violation: float = 0.0
    by_type: dict[str, int] | None = None
    added_cuts: list[FutureCut] | None = None

    def __post_init__(self) -> None:
        if self.by_type is None:
            self.by_type = {}
        if self.added_cuts is None:
            self.added_cuts = []


def add_cut_unique(cuts: list[FutureCut], cut_keys: set[tuple], cut: FutureCut) -> bool:
    if cut.key in cut_keys:
        return False
    cuts.append(cut)
    cut_keys.add(cut.key)
    return True


def fleet_lower_bound(data: FutureData) -> int:
    total_demand = sum(data.task_value(task, "d") for task in data.tasks)
    demand_lb = math.ceil(total_demand / max(1.0e-9, data.capacity * data.sortie_limit))
    service_energy = sum(data.task_value(task, "g") for task in data.tasks)
    service_time = sum(data.task_value(task, "sigma") for task in data.tasks)
    survival_energy = service_time * float(data.survival_energy_rate)
    recharge_time = (service_energy + survival_energy) / max(1.0e-9, data.rho)
    occupation_lb = math.ceil((service_time + recharge_time) / max(1.0e-9, data.horizon))
    return max(1, int(demand_lb), int(occupation_lb))


def sortie_lower_bound(data: FutureData) -> int:
    total_demand = sum(data.task_value(task, "d") for task in data.tasks)
    return max(1, int(math.ceil(total_demand / max(1.0e-9, data.capacity))))


def separate_pricing_compatible_cuts(
    data: FutureData,
    trip_values: list[tuple[TimedTrip, int, float]],
    y_values: dict[int, float],
    cover_duals: dict[int, float],
    cuts: list[FutureCut],
    cut_keys: set[tuple],
    *,
    config: dict,
    depth: int,
) -> CutSeparationResult:
    result = CutSeparationResult()
    if not bool(config.get("cuts_enabled", True)):
        return result

    if bool(config.get("time_point_capacity_cuts_enabled", False)):
        _separate_time_point_capacity_cuts(data, trip_values, y_values, cuts, cut_keys, config, depth, result)

    if bool(config.get("sortie_lower_bound_cut_enabled", True)):
        cut = SortieLowerBoundCut(sortie_lower_bound(data))
        result.generated += 1
        if add_cut_unique(cuts, cut_keys, cut):
            result.added += 1
            result.by_type[cut.kind] = result.by_type.get(cut.kind, 0) + 1
            result.added_cuts.append(cut)
        else:
            result.duplicate += 1

    if not bool(config.get("subset_row_cuts_enabled", True)):
        return result
    if int(depth) > int(config.get("subset_row_max_depth", 0)):
        return result

    candidates = _subset_row_candidates(data, trip_values, cover_duals, config)
    min_violation = float(config.get("subset_row_min_violation", 1.0e-6))
    max_added = int(config.get("subset_row_max_cuts_per_round", 20))
    for tasks, k in candidates:
        if result.added >= max_added:
            break
        cut = SubsetRowCut(tasks, k)
        if cut.key in cut_keys:
            result.duplicate += 1
            continue
        activity = _cut_activity(cut, trip_values)
        violation = activity - cut.rhs
        result.generated += 1
        result.best_violation = max(result.best_violation, violation)
        if violation <= min_violation:
            continue
        if add_cut_unique(cuts, cut_keys, cut):
            result.added += 1
            result.by_type[cut.kind] = result.by_type.get(cut.kind, 0) + 1
            result.added_cuts.append(cut)
    return result


def _separate_time_point_capacity_cuts(
    data: FutureData,
    trip_values: list[tuple[TimedTrip, int, float]],
    y_values: dict[int, float],
    cuts: list[FutureCut],
    cut_keys: set[tuple],
    config: dict,
    depth: int,
    result: CutSeparationResult,
) -> None:
    if int(depth) > int(config.get("time_point_capacity_max_depth", 0)):
        return
    max_added = int(config.get("time_point_capacity_max_cuts_per_round", 30))
    if max_added <= 0:
        return
    min_violation = float(config.get("time_point_capacity_min_violation", 1.0e-6))
    active_tol = float(config.get("time_point_capacity_active_tol", 1.0e-8))
    candidates: list[tuple[float, int, float, float]] = []
    by_vehicle: dict[int, list[tuple[TimedTrip, float]]] = {}
    for trip, vehicle, value in trip_values:
        if value > active_tol:
            by_vehicle.setdefault(int(vehicle), []).append((trip, float(value)))

    for vehicle, entries in by_vehicle.items():
        if not entries:
            continue
        endpoints = sorted({round(float(trip.start_time), 6) for trip, _value in entries} | {round(float(trip.end_time), 6) for trip, _value in entries})
        points: set[float] = set()
        for left, right in zip(endpoints[:-1], endpoints[1:]):
            if right > left + 1.0e-9:
                points.add(round((left + right) / 2.0, 6))
        points.update(endpoints[:-1])
        y_value = float(y_values.get(int(vehicle), 0.0))
        for point in points:
            activity = sum(value for trip, value in entries if trip.start_time <= point + 1.0e-9 and point < trip.end_time - 1.0e-9)
            violation = activity - y_value
            result.generated += 1
            result.best_violation = max(result.best_violation, violation)
            if violation > min_violation:
                candidates.append((violation, int(vehicle), float(point), activity))

    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    added_here = 0
    for violation, vehicle, point, _activity in candidates:
        if added_here >= max_added:
            break
        cut = TimePointCapacityCut(vehicle, point)
        if cut.key in cut_keys:
            result.duplicate += 1
            continue
        if add_cut_unique(cuts, cut_keys, cut):
            result.added += 1
            added_here += 1
            result.by_type[cut.kind] = result.by_type.get(cut.kind, 0) + 1
            result.added_cuts.append(cut)


def _subset_row_candidates(
    data: FutureData,
    trip_values: list[tuple[TimedTrip, int, float]],
    cover_duals: dict[int, float],
    config: dict,
) -> list[tuple[tuple[int, ...], int]]:
    max_subset = int(config.get("subset_row_max_subset_size", 6))
    budget = int(config.get("subset_row_candidate_budget", 200))
    tasks = list(data.tasks)
    mass = {int(task): 0.0 for task in tasks}
    pair_mass: dict[tuple[int, int], float] = {}
    for trip, _vehicle, value in trip_values:
        for task in trip.task_set:
            mass[int(task)] += float(value)
        for i, j in itertools.combinations(sorted(int(task) for task in trip.task_set), 2):
            pair_mass[(i, j)] = pair_mass.get((i, j), 0.0) + float(value)
    ranked = sorted(
        tasks,
        key=lambda task: (
            -mass[int(task)],
            -float(cover_duals.get(int(task), 0.0)),
            data.task_value(int(task), "D") - data.task_value(int(task), "r"),
            int(task),
        ),
    )
    top = ranked[: min(len(ranked), max(10, max_subset + 2))]
    candidates: set[tuple[tuple[int, ...], int]] = set()
    for size in (3, 4):
        if size <= max_subset:
            for combo in itertools.combinations(top, size):
                candidates.add((tuple(sorted(int(task) for task in combo)), 2))
                if len(candidates) >= budget:
                    break
        if len(candidates) >= budget:
            break
    for size in (4, 5, 6):
        if size <= max_subset:
            for combo in itertools.combinations(top, size):
                candidates.add((tuple(sorted(int(task) for task in combo)), 3))
                if len(candidates) >= budget:
                    break
        if len(candidates) >= budget:
            break
    pair_ranked = sorted(pair_mass, key=lambda pair: (-pair_mass[pair], pair))
    for pair in pair_ranked[:budget]:
        pool = set(pair)
        for task in top:
            pool.add(int(task))
            if len(pool) >= 3:
                candidate = tuple(sorted(pool))
                if len(candidate) <= max_subset:
                    candidates.add((candidate, 2))
            if len(pool) >= max_subset:
                break
        if len(candidates) >= budget:
            break
    return sorted(
        candidates,
        key=lambda item: (
            int(item[1]),
            len(item[0]),
            -sum(mass[task] for task in item[0]),
            item[0],
        ),
    )[:budget]


def _cut_activity(cut: FutureCut, trip_values: list[tuple[TimedTrip, int, float]]) -> float:
    return sum(cut.coefficient(trip, vehicle) * float(value) for trip, vehicle, value in trip_values)
