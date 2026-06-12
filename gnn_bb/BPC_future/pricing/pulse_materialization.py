"""Pulse leaf materialization helpers.

Phase 3A deliberately contains no Pulse DFS.  These helpers define the leaf
contract that a future Pulse search must use when turning a completed trace into
the same TimedTrip/JourneyColumn objects used by the existing pricing code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from BPC_future.core.columns import TimedTrip, evaluate_timed_trip
from BPC_future.core.cuts import FutureCut
from BPC_future.core.data import ArcOption, FutureData
from BPC_future.core.journey import JourneyColumn, make_journey
from BPC_future.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost


@dataclass(frozen=True)
class PulseSortieTrace:
    sequence: tuple[int, ...]
    start_time: float
    arc_options: tuple[ArcOption, ...] | None = None


@dataclass(frozen=True)
class PulseLeafCandidate:
    trips: tuple[TimedTrip, ...]
    journey: JourneyColumn
    true_reduced_cost: float
    is_negative: bool


def materialize_pulse_sortie(
    data: FutureData,
    sequence: tuple[int, ...] | list[int],
    start_time: float,
    *,
    arc_options: tuple[ArcOption, ...] | list[ArcOption] | None = None,
    time_bucket_size: float,
    include_physical_paths: bool = True,
) -> TimedTrip | None:
    """Replay a completed Pulse sortie trace through ``evaluate_timed_trip``."""

    return evaluate_timed_trip(
        data,
        tuple(int(task) for task in sequence),
        float(start_time),
        time_bucket_size=float(time_bucket_size),
        arc_options=None if arc_options is None else tuple(arc_options),
        include_physical_paths=bool(include_physical_paths),
    )


def materialize_pulse_journey(
    data: FutureData,
    trips: Iterable[TimedTrip],
    *,
    tolerance: float = 1.0e-9,
) -> JourneyColumn | None:
    """Build a journey with the existing ``make_journey`` semantics."""

    return make_journey(data, tuple(trips), tolerance=float(tolerance))


def materialize_pulse_leaf_candidate(
    data: FutureData,
    sortie_traces: Iterable[PulseSortieTrace],
    duals: JourneyDuals,
    *,
    cuts: tuple[FutureCut, ...] = tuple(),
    time_bucket_size: float,
    eps: float = 1.0e-6,
    include_physical_paths: bool = True,
    tolerance: float = 1.0e-9,
) -> PulseLeafCandidate | None:
    """Materialize a completed Pulse leaf and compute its true reduced cost."""

    trips: list[TimedTrip] = []
    for trace in tuple(sortie_traces):
        trip = materialize_pulse_sortie(
            data,
            trace.sequence,
            trace.start_time,
            arc_options=trace.arc_options,
            time_bucket_size=float(time_bucket_size),
            include_physical_paths=bool(include_physical_paths),
        )
        if trip is None:
            return None
        trips.append(trip)
    journey = materialize_pulse_journey(data, trips, tolerance=float(tolerance))
    if journey is None:
        return None
    true_reduced_cost = float(manual_journey_reduced_cost(journey, duals, cuts=cuts))
    return PulseLeafCandidate(
        trips=tuple(trips),
        journey=journey,
        true_reduced_cost=true_reduced_cost,
        is_negative=true_reduced_cost < -float(eps),
    )


def materialize_negative_pulse_leaf(
    data: FutureData,
    sortie_traces: Iterable[PulseSortieTrace],
    duals: JourneyDuals,
    *,
    cuts: tuple[FutureCut, ...] = tuple(),
    time_bucket_size: float,
    eps: float = 1.0e-6,
    include_physical_paths: bool = True,
    tolerance: float = 1.0e-9,
) -> PulseLeafCandidate | None:
    """Return only leaves that are negative under true RMP reduced cost."""

    candidate = materialize_pulse_leaf_candidate(
        data,
        sortie_traces,
        duals,
        cuts=cuts,
        time_bucket_size=float(time_bucket_size),
        eps=float(eps),
        include_physical_paths=bool(include_physical_paths),
        tolerance=float(tolerance),
    )
    if candidate is None or not bool(candidate.is_negative):
        return None
    return candidate


__all__ = [
    "PulseLeafCandidate",
    "PulseSortieTrace",
    "materialize_negative_pulse_leaf",
    "materialize_pulse_journey",
    "materialize_pulse_leaf_candidate",
    "materialize_pulse_sortie",
]
