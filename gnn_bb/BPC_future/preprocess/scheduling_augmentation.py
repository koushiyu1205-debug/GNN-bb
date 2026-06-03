"""Deterministic scheduling-field augmentation for Moon Trek scenarios."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SchedulingAugmentationConfig:
    horizon_min: float = 720.0
    fleet_size: int = 3
    vehicle_capacity_task_units: float = 6.0
    max_sorties_per_vehicle: int = 8
    usable_battery_capacity_proxy: float = 80.0
    survival_energy_reserve_proxy: float = 10.0
    max_roundtrip_energy_proxy: float = 70.0
    recharge_power_proxy_per_min: float = 2.0
    service_energy_proxy_per_min: float = 0.04
    survival_energy_proxy_per_min: float = 0.01
    fixed_vehicle_cost: float = 50.0
    travel_cost_weight: float = 1.0
    risk_cost_weight: float = 8.0
    energy_cost_weight: float = 0.25
    task_window_length_min: float = 480.0
    task_window_bucket_min: float = 30.0


def augment_scenario_for_multisortie_cvrptw(
    scenario: dict[str, Any],
    *,
    config: SchedulingAugmentationConfig = SchedulingAugmentationConfig(),
) -> dict[str, Any]:
    """Return a scenario with deterministic multi-sortie CVRPTW fields."""

    augmented = deepcopy(scenario)
    tasks = augmented.get("tasks", [])
    depot_xy = tuple(float(value) for value in augmented["depot"]["xy_km"])
    augmented["problem_type"] = "multi_sortie_cvrptw"
    augmented["units"] = {
        "time": "minute",
        "distance": "kilometer",
        "energy": "terrain_energy_proxy",
        "demand": "task_unit",
    }
    augmented["scheduling"] = _scheduling_policy_payload(config)
    vehicle = augmented.setdefault("vehicle", {})
    vehicle.update(_vehicle_payload(config, len(tasks)))

    for index, task in enumerate(tasks, start=1):
        task.update(_task_payload(task, index, depot_xy, config))
    return augmented


def augment_logical_graph_for_multisortie_cvrptw(
    payload: dict[str, Any],
    scenario: dict[str, Any],
    *,
    config: SchedulingAugmentationConfig = SchedulingAugmentationConfig(),
) -> dict[str, Any]:
    augmented = deepcopy(payload)
    augmented["scenario"]["problem_type"] = "multi_sortie_cvrptw"
    augmented["scenario"]["scheduling"] = _scheduling_policy_payload(config)
    augmented["scenario"]["vehicle"] = deepcopy(scenario["vehicle"])
    augmented["scenario"]["task_summary"] = {
        "task_count": len(scenario.get("tasks", [])),
        "demand_total": round(sum(float(task["demand"]) for task in scenario.get("tasks", [])), 6),
        "time_window_model": "deterministic terrain/sector windows; no task waiting allowed",
    }
    return augmented


def augment_manifest_dataset(
    manifest_path: str | Path,
    *,
    config: SchedulingAugmentationConfig = SchedulingAugmentationConfig(),
) -> dict[str, Any]:
    manifest_file = Path(manifest_path)
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest["scheduling_augmentation"] = asdict(config)
    manifest["sortie_policy"] = _scheduling_policy_payload(config)["sortie_policy"]
    for entry in manifest.get("instances", []):
        scenario_path = Path(entry["scenario"])
        graph_path = Path(entry["logical_graph"])
        scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
        roundtrip_check = (
            entry.get("physical_roundtrip_check")
            or graph.get("scenario", {}).get("vehicle", {}).get("physical_roundtrip_check")
            or scenario.get("vehicle", {}).get("physical_roundtrip_check")
        )
        if roundtrip_check is not None:
            scenario.setdefault("vehicle", {})["physical_roundtrip_check"] = roundtrip_check
        scenario = augment_scenario_for_multisortie_cvrptw(scenario, config=config)
        graph = augment_logical_graph_for_multisortie_cvrptw(graph, scenario, config=config)
        scenario_path.write_text(json.dumps(scenario, indent=2, sort_keys=True), encoding="utf-8")
        graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True), encoding="utf-8")
        entry["problem_type"] = "multi_sortie_cvrptw"
        entry["vehicle"] = scenario["vehicle"]
        entry["scheduling"] = scenario["scheduling"]
    manifest_file.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def _scheduling_policy_payload(config: SchedulingAugmentationConfig) -> dict[str, Any]:
    return {
        "horizon_min": float(config.horizon_min),
        "task_service_starts_on_arrival": True,
        "task_waiting_allowed": False,
        "depot_waiting_allowed": True,
        "sortie_policy": {
            "start_location": "depot",
            "end_location": "depot",
            "full_recharge_after_each_sortie": True,
            "depot_chargers": "unlimited",
            "next_sortie_starts_full": True,
            "usable_battery_capacity_proxy": float(config.usable_battery_capacity_proxy),
            "survival_energy_reserve_proxy": float(config.survival_energy_reserve_proxy),
            "max_roundtrip_energy_proxy": float(config.max_roundtrip_energy_proxy),
            "recharge_time_formula": "recharge_time_min = energy_used_proxy / recharge_power_proxy_per_min",
            "energy_used_formula": (
                "travel_energy_proxy + service_energy_proxy + "
                "survival_energy_proxy_per_min * sortie_elapsed_before_recharge_min"
            ),
            "en_route_waiting_allowed": False,
        },
        "objective": {
            "sense": "minimize",
            "formula": (
                "fixed_vehicle_cost * used_vehicles + travel_cost_weight * path_distance_km + "
                "risk_cost_weight * risk_integral + energy_cost_weight * energy_proxy + service_cost"
            ),
            "travel_cost_weight": float(config.travel_cost_weight),
            "risk_cost_weight": float(config.risk_cost_weight),
            "energy_cost_weight": float(config.energy_cost_weight),
        },
    }


def _vehicle_payload(config: SchedulingAugmentationConfig, task_count: int) -> dict[str, Any]:
    fleet_size = max(1, min(int(config.fleet_size), max(1, math.ceil(max(task_count, 1) / 6))))
    return {
        "fleet_size": fleet_size,
        "capacity_task_units": float(config.vehicle_capacity_task_units),
        "max_sorties_per_vehicle": int(config.max_sorties_per_vehicle),
        "usable_battery_capacity_proxy": float(config.usable_battery_capacity_proxy),
        "survival_energy_reserve_proxy": float(config.survival_energy_reserve_proxy),
        "max_roundtrip_energy_proxy": float(config.max_roundtrip_energy_proxy),
        "sortie_energy_capacity_proxy": float(config.max_roundtrip_energy_proxy),
        "recharge_power_proxy_per_min": float(config.recharge_power_proxy_per_min),
        "service_energy_proxy_per_min": float(config.service_energy_proxy_per_min),
        "survival_energy_proxy_per_min": float(config.survival_energy_proxy_per_min),
        "fixed_vehicle_cost": float(config.fixed_vehicle_cost),
        "recharge_policy": "full_after_each_sortie",
        "depot_chargers": "unlimited",
        "task_waiting_allowed": False,
        "depot_waiting_allowed": True,
        # BPC_future aliases used by the current timed-trip prototype.
        "R_bar": fleet_size,
        "Q": float(config.vehicle_capacity_task_units),
        "S_bar": int(config.max_sorties_per_vehicle),
        "B_use": float(config.max_roundtrip_energy_proxy),
        "rho": float(config.recharge_power_proxy_per_min),
        "F": float(config.fixed_vehicle_cost),
        "H": float(config.horizon_min),
    }


def _task_payload(
    task: dict[str, Any],
    index: int,
    depot_xy: tuple[float, float],
    config: SchedulingAugmentationConfig,
) -> dict[str, Any]:
    risk = float(task.get("risk", 0.0))
    slope = float(task.get("slope_deg", 0.0))
    roughness = float(task.get("roughness_m", 0.0))
    service_time = round(18.0 + 8.0 * risk + 0.25 * slope + 0.20 * roughness, 3)
    service_energy = round(service_time * float(config.service_energy_proxy_per_min), 6)
    service_cost = round(0.15 * service_time + 2.0 * risk + 0.05 * slope, 6)
    ready = _deterministic_ready_time(task, index, depot_xy, config)
    due = min(float(config.horizon_min), ready + float(config.task_window_length_min))
    demand = 1.0
    return {
        "demand": demand,
        "demand_units": "task_unit",
        "service_time_min": service_time,
        "service_energy_proxy": service_energy,
        "service_cost": service_cost,
        "ready_time_min": ready,
        "due_time_min": round(due, 6),
        "time_window_min": [ready, round(due, 6)],
        "service_start_rule": "arrival_time_must_be_inside_time_window; no waiting at task",
        # BPC_future aliases used by the current timed-trip prototype.
        "d": demand,
        "sigma": service_time,
        "g": service_energy,
        "c_srv": service_cost,
        "r": ready,
        "D": round(due, 6),
    }


def _deterministic_ready_time(
    task: dict[str, Any],
    index: int,
    depot_xy: tuple[float, float],
    config: SchedulingAugmentationConfig,
) -> float:
    x, y = (float(value) for value in task["xy_km"])
    angle = math.atan2(y - depot_xy[1], x - depot_xy[0])
    sector = int(math.floor(((angle + math.pi) / (2.0 * math.pi)) * 8.0)) % 8
    risk_bucket = int(round(float(task.get("risk", 0.0)) * 10.0)) % 3
    bucket = (sector + index + risk_bucket) % 8
    return round(float(config.task_window_bucket_min) * bucket, 6)
