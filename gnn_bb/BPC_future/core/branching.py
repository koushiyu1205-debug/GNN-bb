"""Pricing-compatible branch constraints for the trip-time master."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .columns import TimedTrip


@dataclass(frozen=True)
class BranchConstraint:
    kind: str
    task_i: int
    task_j: int | None = None
    vehicle: int | None = None

    def name(self) -> str:
        if self.kind == "same_vehicle":
            return f"RF({self.task_i},{self.task_j})=same_vehicle"
        if self.kind == "separate_vehicle":
            return f"RF({self.task_i},{self.task_j})=separate_vehicle"
        if self.kind == "same_route_order_before":
            return f"route_order({self.task_i},{self.task_j})=before"
        if self.kind == "same_route_order_after":
            return f"route_order({self.task_i},{self.task_j})=after"
        if self.kind == "same_route_order_before_strict":
            return f"route_order({self.task_i},{self.task_j})=same_route_before"
        if self.kind == "same_route_order_after_strict":
            return f"route_order({self.task_i},{self.task_j})=same_route_after"
        if self.kind == "not_same_route":
            return f"route_order({self.task_i},{self.task_j})=not_same_route"
        if self.kind == "task_vehicle_on":
            return f"task_vehicle({self.task_i},{self.vehicle})=on"
        if self.kind == "task_vehicle_off":
            return f"task_vehicle({self.task_i},{self.vehicle})=off"
        return f"{self.kind}({self.task_i},{self.task_j},{self.vehicle})"


def _sequence_order_relation(sequence: tuple[int, ...], task_i: int, task_j: int) -> int:
    positions = {int(task): index for index, task in enumerate(sequence)}
    if int(task_i) not in positions or int(task_j) not in positions:
        return 0
    return -1 if positions[int(task_i)] < positions[int(task_j)] else 1


def _single_sequence_order_branch_allowed(
    sequence: tuple[int, ...],
    constraint: BranchConstraint,
) -> bool:
    assert constraint.task_j is not None
    task_set = {int(task) for task in sequence}
    left = int(constraint.task_i) in task_set
    right = int(constraint.task_j) in task_set
    relation = _sequence_order_relation(sequence, constraint.task_i, constraint.task_j)
    if constraint.kind == "same_route_order_before":
        return relation <= 0
    if constraint.kind == "same_route_order_after":
        return relation >= 0
    if constraint.kind == "same_route_order_before_strict":
        return (not left and not right) or relation < 0
    if constraint.kind == "same_route_order_after_strict":
        return (not left and not right) or relation > 0
    if constraint.kind == "not_same_route":
        return relation == 0
    return True


def journey_route_order_signature(journey: Any) -> tuple[tuple[int, ...], ...]:
    trips = tuple(getattr(journey, "trips", tuple()) or tuple())
    if trips:
        signatures: list[tuple[int, ...]] = []
        for trip in trips:
            sequence = tuple(int(task) for task in getattr(trip, "tasks", tuple()) or tuple())
            if sequence:
                signatures.append(sequence)
        if signatures:
            return tuple(signatures)
    raw_signature = tuple(getattr(journey, "signature", tuple()) or tuple())
    signatures = []
    for part in raw_signature:
        if isinstance(part, (tuple, list)) and part:
            sequence = part[0]
            if isinstance(sequence, (tuple, list)):
                seq_tuple = tuple(int(task) for task in sequence)
                if seq_tuple:
                    signatures.append(seq_tuple)
    if signatures:
        return tuple(signatures)
    task_tuple = tuple(sorted(int(task) for task in getattr(journey, "task_set", frozenset())))
    return (task_tuple,) if task_tuple else tuple()


def journey_same_route_order_relation(journey: Any, task_i: int, task_j: int) -> int:
    """Return -1 for i-before-j, +1 for j-before-i, and 0 when not same sortie."""

    i = int(task_i)
    j = int(task_j)
    for sequence in journey_route_order_signature(journey):
        relation = _sequence_order_relation(sequence, i, j)
        if relation != 0:
            return int(relation)
    return 0


def journey_allowed_by_branch(journey: Any, constraints: tuple[BranchConstraint, ...]) -> bool:
    task_set = {int(task) for task in getattr(journey, "task_set", frozenset())}
    for constraint in constraints:
        if constraint.task_j is None:
            return False
        left = int(constraint.task_i) in task_set
        right = int(constraint.task_j) in task_set
        if constraint.kind == "same_vehicle" and left != right:
            return False
        if constraint.kind == "separate_vehicle" and left and right:
            return False
        if constraint.kind == "same_route_order_before":
            if journey_same_route_order_relation(journey, int(constraint.task_i), int(constraint.task_j)) > 0:
                return False
            continue
        if constraint.kind == "same_route_order_after":
            if journey_same_route_order_relation(journey, int(constraint.task_i), int(constraint.task_j)) < 0:
                return False
            continue
        if constraint.kind == "same_route_order_before_strict":
            if not left and not right:
                continue
            if journey_same_route_order_relation(journey, int(constraint.task_i), int(constraint.task_j)) >= 0:
                return False
            continue
        if constraint.kind == "same_route_order_after_strict":
            if not left and not right:
                continue
            if journey_same_route_order_relation(journey, int(constraint.task_i), int(constraint.task_j)) <= 0:
                return False
            continue
        if constraint.kind == "not_same_route":
            if journey_same_route_order_relation(journey, int(constraint.task_i), int(constraint.task_j)) != 0:
                return False
            continue
        if constraint.kind not in {
            "same_vehicle",
            "separate_vehicle",
            "same_route_order_before",
            "same_route_order_after",
            "same_route_order_before_strict",
            "same_route_order_after_strict",
            "not_same_route",
        }:
            return False
    return True


def trip_allowed_by_branch(trip: TimedTrip, vehicle: int, constraints: tuple[BranchConstraint, ...]) -> bool:
    task_set = trip.task_set
    for constraint in constraints:
        if constraint.kind == "separate_vehicle":
            assert constraint.task_j is not None
            if int(constraint.task_i) in task_set and int(constraint.task_j) in task_set:
                return False
        elif constraint.kind == "same_route_order_before":
            assert constraint.task_j is not None
            if not _single_sequence_order_branch_allowed(tuple(int(task) for task in trip.tasks), constraint):
                return False
        elif constraint.kind == "same_route_order_after":
            assert constraint.task_j is not None
            if not _single_sequence_order_branch_allowed(tuple(int(task) for task in trip.tasks), constraint):
                return False
        elif constraint.kind in {
            "same_route_order_before_strict",
            "same_route_order_after_strict",
            "not_same_route",
        }:
            assert constraint.task_j is not None
            if not _single_sequence_order_branch_allowed(tuple(int(task) for task in trip.tasks), constraint):
                return False
        elif constraint.kind == "task_vehicle_on":
            if int(constraint.task_i) in task_set and int(vehicle) != int(constraint.vehicle):
                return False
        elif constraint.kind == "task_vehicle_off":
            if int(constraint.task_i) in task_set and int(vehicle) == int(constraint.vehicle):
                return False
    return True


def partial_sequence_allowed(sequence: tuple[int, ...], vehicle: int, constraints: tuple[BranchConstraint, ...]) -> bool:
    task_set = set(sequence)
    for constraint in constraints:
        if constraint.kind == "separate_vehicle":
            assert constraint.task_j is not None
            if int(constraint.task_i) in task_set and int(constraint.task_j) in task_set:
                return False
        elif constraint.kind == "same_route_order_before":
            assert constraint.task_j is not None
            if not _single_sequence_order_branch_allowed(sequence, constraint):
                return False
        elif constraint.kind == "same_route_order_after":
            assert constraint.task_j is not None
            if not _single_sequence_order_branch_allowed(sequence, constraint):
                return False
        elif constraint.kind in {
            "same_route_order_before_strict",
            "same_route_order_after_strict",
            "not_same_route",
        }:
            assert constraint.task_j is not None
            if not _single_sequence_order_branch_allowed(sequence, constraint):
                return False
        elif constraint.kind == "task_vehicle_on":
            if int(constraint.task_i) in task_set and int(vehicle) != int(constraint.vehicle):
                return False
        elif constraint.kind == "task_vehicle_off":
            if int(constraint.task_i) in task_set and int(vehicle) == int(constraint.vehicle):
                return False
    return True


def branch_coefficient(trip: TimedTrip, vehicle: int, constraint: BranchConstraint) -> float:
    if constraint.kind == "same_vehicle":
        assert constraint.task_j is not None
        return float(int(constraint.task_i in trip.task_set) - int(constraint.task_j in trip.task_set))
    if constraint.kind == "separate_vehicle":
        assert constraint.task_j is not None
        return float(int(constraint.task_i in trip.task_set) + int(constraint.task_j in trip.task_set))
    if constraint.kind == "task_vehicle_on":
        return 1.0 if int(constraint.task_i) in trip.task_set and int(vehicle) == int(constraint.vehicle) else 0.0
    if constraint.kind == "task_vehicle_off":
        return 1.0 if int(constraint.task_i) in trip.task_set and int(vehicle) == int(constraint.vehicle) else 0.0
    return 0.0
