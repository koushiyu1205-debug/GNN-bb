"""Timed sortie construction for lunar-ice journey columns."""

from __future__ import annotations

from dataclasses import dataclass

from lunar_ice_bpc.domain.scenario import SERVICE_TIMING_POLICY_ID
from lunar_ice_bpc.exact.core.data import LunarIceData


_TIME_EPS = 1.0e-9


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
    service_cost: float
    shadow_exposure_min: float
    demand: float
    discovery_completion_term: float
    task_completion_times: dict[str, float]
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
    """Build the earliest feasible sortie with waiting allowed only at the depot.

    ``start_time`` is the earliest time at which the vehicle is available at
    the depot.  The actual departure may be delayed there.  Once the sortie
    leaves the depot, every task must start service exactly on arrival; a
    route that would require waiting at any task is feasible only when one
    common departure-time shift makes every task arrival fall inside its
    service-start window.
    """

    if len(path_types) != len(sequence) + 1:
        raise ValueError("path_types must have one entry per sortie leg including return")
    if len(sequence) > data.max_tasks_per_trip:
        return _infeasible(sequence, path_types, start_time, "max_tasks_per_trip")

    earliest_departure = max(0.0, float(start_time))
    latest_departure = float(data.horizon)
    current = "depot"
    elapsed_from_departure = 0.0
    travel_time = 0.0
    distance = 0.0
    energy = 0.0
    risk = 0.0
    shadow = 0.0
    demand = 0.0
    service_cost = 0.0
    completion_term = 0.0
    legs: list[SortieLeg] = []
    arrival_offsets: dict[str, float] = {}

    for index, task_id in enumerate(sequence):
        option = data.option(current, task_id, path_types[index])
        elapsed_from_departure += option.travel_time_min
        travel_time += option.travel_time_min
        distance += option.distance_km
        energy += option.energy_proxy
        risk += option.risk_integral
        shadow += option.shadow_exposure_min
        task = data.tasks[task_id]
        arrival_offsets[task_id] = elapsed_from_departure
        earliest_departure = max(
            earliest_departure,
            float(task.ready_time) - elapsed_from_departure,
        )
        latest_departure = min(
            latest_departure,
            float(task.due_time)
            - float(task.service_time)
            - elapsed_from_departure,
        )
        if earliest_departure > latest_departure + _TIME_EPS:
            return _infeasible(sequence, path_types, start_time, "time_window")
        elapsed_from_departure += task.service_time
        energy += task.service_energy
        risk += task.local_thermal_risk * task.service_time * 0.01
        shadow += task.local_shadow_score * task.service_time
        demand += task.demand
        service_cost += task.service_cost
        legs.append(SortieLeg(source=current, target=task_id, path_type=path_types[index]))
        current = task_id

    back = data.option(current, "depot", path_types[-1])
    elapsed_from_departure += back.travel_time_min
    travel_time += back.travel_time_min
    distance += back.distance_km
    energy += back.energy_proxy
    risk += back.risk_integral
    shadow += back.shadow_exposure_min
    legs.append(SortieLeg(source=current, target="depot", path_type=path_types[-1]))
    recharge = data.dock_overhead_min + energy / max(1.0e-9, data.recharge_power_proxy_per_min)
    latest_departure = min(
        latest_departure,
        float(data.horizon) - elapsed_from_departure - recharge,
    )

    if demand > data.capacity + 1.0e-9:
        return _infeasible(sequence, path_types, start_time, "capacity")
    if energy > data.energy_limit + 1.0e-9:
        return _infeasible(sequence, path_types, start_time, "energy")
    if shadow > data.max_shadow_exposure_per_sortie + 1.0e-9:
        return _infeasible(sequence, path_types, start_time, "shadow_exposure")
    if earliest_departure > latest_departure + _TIME_EPS:
        return _infeasible(sequence, path_types, start_time, "horizon")

    actual_departure = earliest_departure
    service_starts: dict[str, float] = {}
    task_completion_times: dict[str, float] = {}
    for task_id in sequence:
        task = data.tasks[task_id]
        service_start = actual_departure + arrival_offsets[task_id]
        completion = service_start + float(task.service_time)
        service_starts[task_id] = service_start
        task_completion_times[task_id] = completion
        completion_term += float(task.science_weight) * completion
    return_time = actual_departure + elapsed_from_departure
    end_time = return_time + recharge

    return TimedSortie(
        tasks=tuple(sequence),
        legs=tuple(legs),
        start_time=round(actual_departure, 6),
        service_starts={key: round(value, 6) for key, value in service_starts.items()},
        return_time=round(return_time, 6),
        recharge_time=round(recharge, 6),
        end_time=round(end_time, 6),
        travel_time=round(travel_time, 6),
        distance_km=round(distance, 6),
        energy_proxy=round(energy, 6),
        risk_integral=round(risk, 6),
        service_cost=round(service_cost, 6),
        shadow_exposure_min=round(shadow, 6),
        demand=round(demand, 6),
        discovery_completion_term=round(completion_term, 6),
        task_completion_times={key: round(value, 6) for key, value in task_completion_times.items()},
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
        service_cost=0.0,
        shadow_exposure_min=0.0,
        demand=0.0,
        discovery_completion_term=0.0,
        task_completion_times={},
        feasible=False,
        infeasible_reason=reason,
    )
