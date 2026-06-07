"""Vehicle journey columns built from timed trip columns.

A journey is a feasible sequence of timed sorties for one rover.  The current
BPC_future journey master prices these columns exactly when the configured
Python oracle exhausts, so the pool is an RMP column set rather than a
diagnostic-only finite model.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import heapq
from typing import Iterable

from BPC_future.core.columns import TimedTrip, rounded
from BPC_future.core.data import FutureData


@dataclass(frozen=True)
class JourneyColumn:
    id: int
    trips: tuple[TimedTrip, ...]
    task_set: frozenset[int]
    start_time: float
    end_time: float
    travel_cost: float
    fixed_vehicle_cost: float
    cost: float
    signature: tuple[tuple[tuple[int, ...], tuple[str, ...], float], ...]

    @property
    def trip_ids(self) -> tuple[int, ...]:
        return tuple(int(trip.id) for trip in self.trips)


class JourneyPool:
    def __init__(self, *, task_set_dominance_enabled: bool = True) -> None:
        self.task_set_dominance_enabled = bool(task_set_dominance_enabled)
        self.journeys: list[JourneyColumn] = []
        self.by_signature: dict[tuple[tuple[tuple[int, ...], tuple[str, ...], float], ...], JourneyColumn] = {}
        self.by_task_set: dict[frozenset[int], JourneyColumn] = {}

    def add(self, journey: JourneyColumn) -> JourneyColumn:
        existing = self.by_signature.get(journey.signature)
        if existing is not None:
            return existing
        task_key = frozenset(int(task) for task in journey.task_set)
        incumbent = self.by_task_set.get(task_key)
        if not self.task_set_dominance_enabled:
            stored = replace(journey, id=len(self.journeys), task_set=task_key)
            self.journeys.append(stored)
            self.by_signature[stored.signature] = stored
            if incumbent is None or float(stored.cost) < float(incumbent.cost) - 1.0e-9:
                self.by_task_set[task_key] = stored
            return stored
        if incumbent is not None:
            if float(incumbent.cost) <= float(journey.cost) + 1.0e-9:
                return incumbent
            stored = replace(journey, id=int(incumbent.id), task_set=task_key)
            self.journeys[int(incumbent.id)] = stored
            self.by_task_set[task_key] = stored
            self.by_signature.pop(incumbent.signature, None)
            self.by_signature[stored.signature] = stored
            return stored
        stored = replace(journey, id=len(self.journeys))
        self.journeys.append(stored)
        self.by_signature[stored.signature] = stored
        self.by_task_set[task_key] = stored
        return stored


def make_journey(data: FutureData, trips: Iterable[TimedTrip], *, tolerance: float = 1.0e-9) -> JourneyColumn | None:
    ordered = tuple(sorted(tuple(trips), key=lambda trip: (trip.start_time, trip.end_time, trip.tasks, trip.arc_option_ids)))
    if not ordered:
        return None
    task_set: set[int] = set()
    previous_end: float | None = None
    for trip in ordered:
        if previous_end is not None and trip.start_time < previous_end - tolerance:
            return None
        if task_set.intersection(trip.task_set):
            return None
        task_set.update(int(task) for task in trip.task_set)
        previous_end = float(trip.end_time)
    travel_cost = rounded(sum(float(trip.cost) for trip in ordered))
    fixed = float(data.fixed_vehicle_cost)
    return JourneyColumn(
        id=-1,
        trips=ordered,
        task_set=frozenset(task_set),
        start_time=rounded(ordered[0].start_time),
        end_time=rounded(ordered[-1].end_time),
        travel_cost=travel_cost,
        fixed_vehicle_cost=rounded(fixed),
        cost=rounded(fixed + travel_cost),
        signature=tuple(trip.signature for trip in ordered),
    )


def trips_compatible(left: TimedTrip, right: TimedTrip, *, tolerance: float = 1.0e-9) -> bool:
    return (
        float(left.end_time) <= float(right.start_time) + tolerance
        and not left.task_set.intersection(right.task_set)
    )


def build_journey_pool(
    data: FutureData,
    trips: list[TimedTrip],
    *,
    max_trips_per_journey: int = 6,
    max_columns: int = 5000,
    max_extensions_per_prefix: int = 80,
    task_set_dominance_enabled: bool = True,
    tolerance: float = 1.0e-9,
) -> JourneyPool:
    """Build deterministic feasible journey columns from a finite trip pool."""

    pool = JourneyPool(task_set_dominance_enabled=bool(task_set_dominance_enabled))
    if max_columns <= 0 or not trips:
        return pool
    max_trips = max(1, int(max_trips_per_journey))
    extension_limit = max(1, int(max_extensions_per_prefix))
    ordered = sorted(
        trips,
        key=lambda trip: (
            len(trip.task_set),
            trip.start_time,
            trip.end_time,
            trip.cost,
            trip.tasks,
            trip.arc_option_ids,
            trip.id,
        ),
    )

    # Single-trip journeys are important for feasibility and for a fair pool
    # comparison against the current timed-trip master.
    for trip in ordered:
        if len(pool.journeys) >= max_columns:
            return pool
        journey = make_journey(data, (trip,), tolerance=tolerance)
        if journey is not None:
            pool.add(journey)

    successors: dict[tuple[tuple[int, ...], tuple[str, ...], float], list[TimedTrip]] = {}
    for left in ordered:
        candidates = [
            right
            for right in ordered
            if trips_compatible(left, right, tolerance=tolerance)
        ]
        candidates.sort(key=lambda trip: (trip.start_time, trip.end_time, trip.cost, trip.tasks, trip.arc_option_ids, trip.id))
        successors[left.signature] = candidates[:extension_limit]

    heap: list[tuple[tuple, tuple[TimedTrip, ...]]] = []
    for trip in ordered:
        key = _prefix_key((trip,))
        heapq.heappush(heap, (key, (trip,)))

    seen_prefixes: set[tuple[tuple[tuple[int, ...], tuple[str, ...], float], ...]] = set()
    while heap and len(pool.journeys) < max_columns:
        _key, prefix = heapq.heappop(heap)
        signature = tuple(trip.signature for trip in prefix)
        if signature in seen_prefixes:
            continue
        seen_prefixes.add(signature)
        if len(prefix) >= max_trips:
            continue
        used_tasks = set().union(*(trip.task_set for trip in prefix))
        tail = prefix[-1]
        for nxt in successors.get(tail.signature, ()):
            if used_tasks.intersection(nxt.task_set):
                continue
            extended = (*prefix, nxt)
            journey = make_journey(data, extended, tolerance=tolerance)
            if journey is None:
                continue
            before = len(pool.journeys)
            pool.add(journey)
            if len(pool.journeys) >= max_columns:
                break
            if len(pool.journeys) > before and len(extended) < max_trips:
                heapq.heappush(heap, (_prefix_key(extended), extended))
    return pool


def _prefix_key(trips: tuple[TimedTrip, ...]) -> tuple:
    task_count = sum(len(trip.task_set) for trip in trips)
    return (
        len(trips),
        -task_count,
        round(sum(float(trip.cost) for trip in trips), 6),
        round(trips[-1].end_time, 6),
        tuple(trip.signature for trip in trips),
    )
