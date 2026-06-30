"""Timed sortie construction for lunar-ice journey columns."""

from __future__ import annotations

from dataclasses import dataclass

from lunar_ice_bpc.exact.core.data import LunarIceData


@dataclass(frozen=True)
class SortieLeg:
    source: str
    target: str
    path_type: str


@dataclass(frozen=True)
class TimedSortie:
    tasks: tuple[str, ...]
    legs: tuple[SortieLeg, ...]
    start_time: float
    service_starts: dict[str, float]
    return_time: float
    recharge_time: float
    end_time: float
    travel_time: float
    distance_km: float
    energy_proxy: float
    risk_integral: float
    shadow_exposure_min: float
    demand: float
    discovery_completion_term: float
    feasible: bool
    infeasible_reason: str = ""

    @property
    def task_set(self) -> frozenset[str]:
        return frozenset(self.tasks)


def build_timed_sortie(
    data: LunarIceData,
    sequence: tuple[str, ...],
    path_types: tuple[str, ...],
    *,
    start_time: float,
) -> TimedSortie:
    """Build the earliest feasible timed sortie for a fixed sequence and path choices."""

    if len(path_types) != len(sequence) + 1:
        raise ValueError("path_types must have one entry per sortie leg including return")
    if len(sequence) > data.max_tasks_per_trip:
        return _infeasible(sequence, path_types, start_time, "max_tasks_per_trip")

    current = "depot"
    elapsed = float(start_time)
    travel_time = 0.0
    distance = 0.0
    energy = 0.0
    risk = 0.0
    shadow = 0.0
    demand = 0.0
    completion_term = 0.0
    service_starts: dict[str, float] = {}
    legs: list[SortieLeg] = []

    for index, task_id in enumerate(sequence):
        option = data.option(current, task_id, path_types[index])
        elapsed += option.travel_time_min
        travel_time += option.travel_time_min
        distance += option.distance_km
        energy += option.energy_proxy
        risk += option.risk_integral
        shadow += option.shadow_exposure_min
        task = data.tasks[task_id]
        service_start = max(elapsed, task.ready_time)
        if service_start > task.due_time - task.service_time + 1.0e-9:
            return _infeasible(sequence, path_types, start_time, "time_window")
        service_starts[task_id] = service_start
        elapsed = service_start + task.service_time
        energy += task.service_energy
        risk += task.local_thermal_risk * task.service_time * 0.01
        shadow += task.local_shadow_score * task.service_time
        demand += task.demand
        completion_term += task.science_weight * elapsed
        legs.append(SortieLeg(source=current, target=task_id, path_type=path_types[index]))
        current = task_id

    back = data.option(current, "depot", path_types[-1])
    elapsed += back.travel_time_min
    travel_time += back.travel_time_min
    distance += back.distance_km
    energy += back.energy_proxy
    risk += back.risk_integral
    shadow += back.shadow_exposure_min
    legs.append(SortieLeg(source=current, target="depot", path_type=path_types[-1]))
    return_time = elapsed
    recharge = data.dock_overhead_min + energy / max(1.0e-9, data.recharge_power_proxy_per_min)
    end_time = return_time + recharge

    if demand > data.capacity + 1.0e-9:
        return _infeasible(sequence, path_types, start_time, "capacity")
    if energy > data.energy_limit + 1.0e-9:
        return _infeasible(sequence, path_types, start_time, "energy")
    if shadow > data.max_shadow_exposure_per_sortie + 1.0e-9:
        return _infeasible(sequence, path_types, start_time, "shadow_exposure")
    if end_time > data.horizon + 1.0e-9:
        return _infeasible(sequence, path_types, start_time, "horizon")

    return TimedSortie(
        tasks=tuple(sequence),
        legs=tuple(legs),
        start_time=round(start_time, 6),
        service_starts={key: round(value, 6) for key, value in service_starts.items()},
        return_time=round(return_time, 6),
        recharge_time=round(recharge, 6),
        end_time=round(end_time, 6),
        travel_time=round(travel_time, 6),
        distance_km=round(distance, 6),
        energy_proxy=round(energy, 6),
        risk_integral=round(risk, 6),
        shadow_exposure_min=round(shadow, 6),
        demand=round(demand, 6),
        discovery_completion_term=round(completion_term, 6),
        feasible=True,
    )


def _infeasible(sequence: tuple[str, ...], path_types: tuple[str, ...], start_time: float, reason: str) -> TimedSortie:
    current = "depot"
    legs: list[SortieLeg] = []
    for index, task_id in enumerate(sequence):
        path_type = path_types[index] if index < len(path_types) else "low_risk"
        legs.append(SortieLeg(source=current, target=task_id, path_type=path_type))
        current = task_id
    if path_types:
        legs.append(SortieLeg(source=current, target="depot", path_type=path_types[-1]))
    return TimedSortie(
        tasks=tuple(sequence),
        legs=tuple(legs),
        start_time=round(start_time, 6),
        service_starts={},
        return_time=round(start_time, 6),
        recharge_time=0.0,
        end_time=round(start_time, 6),
        travel_time=0.0,
        distance_km=0.0,
        energy_proxy=0.0,
        risk_integral=0.0,
        shadow_exposure_min=0.0,
        demand=0.0,
        discovery_completion_term=0.0,
        feasible=False,
        infeasible_reason=reason,
    )

