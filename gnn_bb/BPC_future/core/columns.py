"""Timed trip columns and resource evaluation."""

from __future__ import annotations

from dataclasses import dataclass, replace
import math
from typing import Any

from .data import ArcOption, FutureData


def rounded(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


@dataclass(frozen=True)
class TimedTrip:
    id: int
    tasks: tuple[int, ...]
    task_set: frozenset[int]
    start_time: float
    end_time: float
    load: float
    travel_time: float
    energy: float
    distance: float
    risk: float
    cost: float
    recharge_time: float
    survival_energy: float
    arc_option_ids: tuple[str, ...]
    service_start: dict[str, float]
    occupancy: dict[int, float]
    physical_paths: tuple[dict[str, Any], ...]

    @property
    def signature(self) -> tuple[tuple[int, ...], tuple[str, ...], float]:
        return (self.tasks, self.arc_option_ids, self.start_time)


class TripPool:
    def __init__(self) -> None:
        self.trips: list[TimedTrip] = []
        self.by_signature: dict[tuple[tuple[int, ...], tuple[str, ...], float], TimedTrip] = {}

    def add(self, trip: TimedTrip) -> TimedTrip:
        existing = self.by_signature.get(trip.signature)
        if existing is not None:
            return existing
        stored = replace(trip, id=len(self.trips))
        self.trips.append(stored)
        self.by_signature[stored.signature] = stored
        return stored

    def rebuild(self, trips: list[TimedTrip]) -> None:
        self.trips = []
        self.by_signature = {}
        for trip in trips:
            self.add(trip)


def evaluate_timed_trip(
    data: FutureData,
    sequence: tuple[int, ...] | list[int],
    start_time: float,
    *,
    time_bucket_size: float,
    arc_options: tuple[ArcOption, ...] | list[ArcOption] | None = None,
    include_physical_paths: bool = True,
) -> TimedTrip | None:
    sequence = tuple(int(task) for task in sequence)
    start_time = rounded(start_time)
    if start_time < -1.0e-9:
        return None
    selected_options = _selected_arc_options(data, sequence, arc_options)
    if selected_options is None:
        return None
    task_waiting_allowed = bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    load = sum(data.task_value(task, "d") for task in sequence)
    if load > data.capacity + 1.0e-9:
        return None

    current = 0
    current_time = float(start_time)
    travel_time = 0.0
    travel_energy = 0.0
    travel_cost = 0.0
    travel_distance = 0.0
    travel_risk = 0.0
    service_energy = 0.0
    service_cost = 0.0
    service_start: dict[str, float] = {}
    physical_paths: list[dict[str, Any]] = []

    for leg_index, task_id in enumerate(sequence):
        option = selected_options[leg_index]
        travel_time += option.tau
        travel_energy += option.energy
        travel_cost += option.cost
        travel_distance += option.distance
        travel_risk += option.risk
        if include_physical_paths:
            physical_paths.append(_path_payload(current, task_id, option))
        arrival = current_time + option.tau
        ready_time = data.task_value(task_id, "r")
        if task_waiting_allowed:
            start_service = max(ready_time, arrival)
        else:
            if arrival < ready_time - 1.0e-9:
                return None
            start_service = arrival
        finish_service = start_service + data.task_value(task_id, "sigma")
        if finish_service > data.task_value(task_id, "D") + 1.0e-9:
            return None
        service_start[str(task_id)] = rounded(start_service)
        current_time = finish_service
        service_energy += data.task_value(task_id, "g")
        service_cost += data.task_value(task_id, "c_srv")
        current = task_id

    back = selected_options[-1]
    travel_time += back.tau
    travel_energy += back.energy
    travel_cost += back.cost
    travel_distance += back.distance
    travel_risk += back.risk
    if include_physical_paths:
        physical_paths.append(_path_payload(current, 0, back))
    return_time = current_time + back.tau
    elapsed_before_recharge = max(0.0, return_time - float(start_time))
    survival_energy = float(data.survival_energy_rate) * elapsed_before_recharge
    total_energy = travel_energy + service_energy + survival_energy
    if total_energy > data.energy_limit + 1.0e-9:
        return None
    recharge_time = total_energy / data.rho
    end_time = return_time + recharge_time
    if end_time > data.horizon + 1.0e-9:
        return None
    occupancy = time_bucket_occupancy(start_time, end_time, time_bucket_size, data.horizon)
    return TimedTrip(
        id=-1,
        tasks=sequence,
        task_set=frozenset(sequence),
        start_time=rounded(start_time),
        end_time=rounded(end_time),
        load=rounded(load),
        travel_time=rounded(travel_time),
        energy=rounded(total_energy),
        distance=rounded(travel_distance),
        risk=rounded(travel_risk),
        cost=rounded(travel_cost + service_cost),
        recharge_time=rounded(recharge_time),
        survival_energy=rounded(survival_energy),
        arc_option_ids=tuple(option.option_id for option in selected_options),
        service_start=service_start,
        occupancy=occupancy,
        physical_paths=tuple(physical_paths),
    )


def selected_arc_options_by_default(data: FutureData, sequence: tuple[int, ...] | list[int]) -> tuple[ArcOption, ...] | None:
    return _selected_arc_options(data, tuple(int(task) for task in sequence), None)


def candidate_start_times_for_trip(
    data: FutureData,
    sequence: tuple[int, ...] | list[int],
    arc_options: tuple[ArcOption, ...] | list[ArcOption] | None,
    *,
    start_step: float,
) -> tuple[float, ...]:
    """Return event/bucket start candidates for one fixed sequence/path-choice.

    This avoids full 1-minute horizon enumeration. For the common strict
    no-waiting Moon Trek policy, the feasible interval is computed directly
    from task arrival offsets. We then sample interval endpoints and coarser
    bucket boundaries so time-occupation duals still have useful placement
    options.
    """

    sequence = tuple(int(task) for task in sequence)
    selected_options = _selected_arc_options(data, sequence, arc_options)
    if selected_options is None:
        return tuple()
    step = max(1.0e-9, float(start_step))
    task_waiting_allowed = bool(data.instance.get("scheduling", {}).get("task_waiting_allowed", True))
    if task_waiting_allowed:
        candidates = {0.0, float(data.horizon)}
        current = 0.0
        while current <= data.horizon + 1.0e-9:
            candidates.add(rounded(current))
            current += step
        return tuple(sorted(candidates))
    lower = 0.0
    upper = float(data.horizon)
    offset = 0.0
    service_energy = 0.0
    for leg_index, task in enumerate(sequence):
        option = selected_options[leg_index]
        arrival_offset = offset + option.tau
        ready = data.task_value(task, "r")
        due = data.task_value(task, "D")
        service = data.task_value(task, "sigma")
        if not task_waiting_allowed:
            lower = max(lower, ready - arrival_offset)
        upper = min(upper, due - service - arrival_offset)
        offset = arrival_offset + service
        service_energy += data.task_value(task, "g")
    return_offset = offset + selected_options[-1].tau
    travel_energy = sum(option.energy for option in selected_options)
    survival_energy = float(data.survival_energy_rate) * return_offset
    total_energy = travel_energy + service_energy + survival_energy
    if total_energy > data.energy_limit + 1.0e-9:
        return tuple()
    end_offset = return_offset + total_energy / data.rho
    upper = min(upper, float(data.horizon) - end_offset)
    if upper < lower - 1.0e-9:
        return tuple()
    candidates = {rounded(lower), rounded(upper), rounded((lower + upper) / 2.0)}
    first_boundary = math.ceil(lower / step) * step
    current = first_boundary
    while current <= upper + 1.0e-9:
        candidates.add(rounded(current))
        current += step
    return tuple(sorted(start for start in candidates if lower - 1.0e-9 <= start <= upper + 1.0e-9))


def time_bucket_occupancy(start: float, end: float, bucket_size: float, horizon: float) -> dict[int, float]:
    if bucket_size <= 0:
        raise ValueError("time_bucket_size must be positive")
    if end <= start + 1.0e-12:
        return {}
    first = max(0, int(math.floor(start / bucket_size)))
    last = min(int(math.ceil(horizon / bucket_size)) - 1, int(math.floor((end - 1.0e-12) / bucket_size)))
    occupancy: dict[int, float] = {}
    for bucket in range(first, last + 1):
        left = bucket * bucket_size
        right = min(horizon, (bucket + 1) * bucket_size)
        overlap = max(0.0, min(end, right) - max(start, left))
        if overlap > 1.0e-9:
            occupancy[bucket] = rounded(overlap / bucket_size)
    return occupancy


def trip_to_json(trip: TimedTrip) -> dict[str, Any]:
    return {
        "id": int(trip.id),
        "tasks": list(trip.tasks),
        "start_time": trip.start_time,
        "end_time": trip.end_time,
        "load": trip.load,
        "travel_time": trip.travel_time,
        "energy": trip.energy,
        "distance": trip.distance,
        "risk": trip.risk,
        "cost": trip.cost,
        "recharge_time": trip.recharge_time,
        "survival_energy": trip.survival_energy,
        "arc_option_ids": list(trip.arc_option_ids),
        "service_start": trip.service_start,
        "occupancy": {str(k): v for k, v in sorted(trip.occupancy.items())},
        "physical_paths": list(trip.physical_paths),
    }


def _selected_arc_options(
    data: FutureData,
    sequence: tuple[int, ...],
    arc_options: tuple[ArcOption, ...] | list[ArcOption] | None,
) -> tuple[ArcOption, ...] | None:
    if arc_options is not None:
        selected = tuple(arc_options)
        if len(selected) != len(sequence) + 1:
            raise ValueError("arc_options length must equal len(sequence) + 1")
        return selected
    selected: list[ArcOption] = []
    current = 0
    for task in sequence:
        options = data.options(current, task)
        if not options:
            return None
        selected.append(options[0])
        current = task
    options = data.options(current, 0)
    if not options:
        return None
    selected.append(options[0])
    return tuple(selected)


def _path_payload(source: int, target: int, option: ArcOption) -> dict[str, Any]:
    return {
        "from": int(source),
        "to": int(target),
        "option_id": option.option_id,
        "path_type": option.path_type,
        "aliases": list(option.aliases),
        "travel_time_min": option.tau,
        "energy_proxy": option.energy,
        "distance_km": option.distance,
        "risk_integral": option.risk,
        "cost": option.cost,
        "path_cells": [list(cell) for cell in option.path_cells],
        "path_xy": [list(xy) for xy in option.path_xy],
        "path": [f"{row},{col}" for row, col in option.path_cells],
    }
