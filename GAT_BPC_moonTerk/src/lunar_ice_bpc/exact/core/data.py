"""Typed instance adapter for lunar-ice exact routines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskData:
    id: str
    xy_km: tuple[float, float]
    science_weight: float
    operation_mode: str
    demand: float
    service_time: float
    service_energy: float
    service_cost: float
    ready_time: float
    due_time: float
    local_shadow_score: float
    local_thermal_risk: float


@dataclass(frozen=True)
class ArcOptionData:
    path_type: str
    travel_time_min: float
    energy_proxy: float
    risk_integral: float
    distance_km: float
    shadow_exposure_min: float
    thermal_survival_energy_proxy: float
    path_xy: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class ObjectiveWeights:
    alpha_discovery_completion: float
    beta_journey_end_time: float
    gamma_lunar_ice_risk: float
    delta_energy: float


@dataclass(frozen=True)
class LunarIceData:
    instance_id: str
    scale: int
    tasks: dict[str, TaskData]
    depot_xy_km: tuple[float, float]
    arcs: dict[tuple[str, str], dict[str, ArcOptionData]]
    fleet_size: int
    max_tasks_per_trip: int
    capacity: float
    energy_limit: float
    horizon: float
    dock_overhead_min: float
    recharge_power_proxy_per_min: float
    max_shadow_exposure_per_sortie: float
    objective: ObjectiveWeights

    @property
    def task_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.tasks))

    def option(self, source: str, target: str, path_type: str) -> ArcOptionData:
        return self.arcs[(str(source), str(target))][str(path_type)]


def load_lunar_ice_data(instance: dict[str, Any]) -> LunarIceData:
    tasks: dict[str, TaskData] = {}
    for task_id, payload in sorted(instance["tasks"].items()):
        tasks[str(task_id)] = TaskData(
            id=str(task_id),
            xy_km=(float(payload["xy_km"][0]), float(payload["xy_km"][1])),
            science_weight=float(payload["science_weight"]),
            operation_mode=str(payload["operation_mode"]),
            demand=float(payload["d"]),
            service_time=float(payload["sigma"]),
            service_energy=float(payload["g"]),
            service_cost=float(payload["c_srv"]),
            ready_time=float(payload["r"]),
            due_time=float(payload["D"]),
            local_shadow_score=float(payload["local_shadow_score"]),
            local_thermal_risk=float(payload["local_thermal_risk"]),
        )

    arcs: dict[tuple[str, str], dict[str, ArcOptionData]] = {}
    for edge in instance["logical_graph"]["edges"]:
        source = str(edge["from"])
        target = str(edge["to"])
        by_type: dict[str, ArcOptionData] = {}
        for option in edge["path_options"]:
            by_type[str(option["path_type"])] = ArcOptionData(
                path_type=str(option["path_type"]),
                travel_time_min=float(option["travel_time_min"]),
                energy_proxy=float(option["energy_proxy"]),
                risk_integral=float(option["risk_integral"]),
                distance_km=float(option["path_distance_km"]),
                shadow_exposure_min=float(option["shadow_exposure_min"]),
                thermal_survival_energy_proxy=float(option["thermal_survival_energy_proxy"]),
                path_xy=tuple((float(x), float(y)) for x, y in option.get("path_xy", [])),
            )
        arcs[(source, target)] = by_type

    vehicle = instance["vehicle"]
    objective_payload = instance["scheduling"]["objective"]
    return LunarIceData(
        instance_id=str(instance["instance_id"]),
        scale=int(instance["scale"]),
        tasks=tasks,
        depot_xy_km=(float(instance["depot"]["xy_km"][0]), float(instance["depot"]["xy_km"][1])),
        arcs=arcs,
        fleet_size=int(vehicle["fleet_size"]),
        max_tasks_per_trip=int(vehicle["max_tasks_per_trip"]),
        capacity=float(vehicle["Q_ice"]),
        energy_limit=float(vehicle["B_use"]),
        horizon=float(instance["scheduling"]["horizon_min"]),
        dock_overhead_min=float(vehicle["dock_overhead_min"]),
        recharge_power_proxy_per_min=float(vehicle["recharge_power_proxy_per_min"]),
        max_shadow_exposure_per_sortie=float(vehicle["max_shadow_exposure_per_sortie"]),
        objective=ObjectiveWeights(
            alpha_discovery_completion=float(objective_payload["alpha_discovery_completion"]),
            beta_journey_end_time=float(objective_payload["beta_journey_end_time"]),
            gamma_lunar_ice_risk=float(objective_payload["gamma_lunar_ice_risk"]),
            delta_energy=float(objective_payload["delta_energy"]),
        ),
    )

