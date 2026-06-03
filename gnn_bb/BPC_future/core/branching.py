"""Pricing-compatible branch constraints for the trip-time master."""

from __future__ import annotations

from dataclasses import dataclass

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
        if self.kind == "task_vehicle_on":
            return f"task_vehicle({self.task_i},{self.vehicle})=on"
        if self.kind == "task_vehicle_off":
            return f"task_vehicle({self.task_i},{self.vehicle})=off"
        return f"{self.kind}({self.task_i},{self.task_j},{self.vehicle})"


def trip_allowed_by_branch(trip: TimedTrip, vehicle: int, constraints: tuple[BranchConstraint, ...]) -> bool:
    task_set = trip.task_set
    for constraint in constraints:
        if constraint.kind == "separate_vehicle":
            assert constraint.task_j is not None
            if int(constraint.task_i) in task_set and int(constraint.task_j) in task_set:
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

