"""Synthetic instance generation and reference schedule construction."""

from __future__ import annotations

import math
import random
from typing import Any

from lunar_ice_bpc.domain.polar_resources import SyntheticPolarField, build_edge_options, path_option
from lunar_ice_bpc.domain.scenario import (
    ACTIVE_FOOTPRINT_BY_SCALE,
    FLEET_BY_SCALE,
    HORIZON_BY_SCALE,
    MEAN_WINDOW_WIDTH_CAP_BY_SCALE,
    OPERATION_MODE_SPECS,
    PATH_OPTION_POLICY_ID,
    RISK_SCHEMA_VERSION,
    SHADOW_CAP_BY_SCALE,
    SYNTHETIC_GENERATOR_ID,
    TIME_WINDOW_POLICY_ID,
    WINDOW_WIDTH_CAP_BY_SCALE,
    LunarIceConfig,
    scale_label,
    snap_down,
    snap_up,
)


def _edge_key(source: str, target: str) -> str:
    return f"{source}->{target}"


def _mode_sequence(scale: int, rng: random.Random) -> list[str]:
    counts = {
        "detect": int(round(scale * OPERATION_MODE_SPECS["detect"].ratio)),
        "sample": int(round(scale * OPERATION_MODE_SPECS["sample"].ratio)),
    }
    counts["drill"] = max(0, int(scale) - counts["detect"] - counts["sample"])
    while sum(counts.values()) < int(scale):
        counts["detect"] += 1
    while sum(counts.values()) > int(scale):
        counts["detect"] -= 1
    modes = [mode for mode, count in counts.items() for _ in range(max(0, count))]
    rng.shuffle(modes)
    return modes


def _sample_target_xy(field: SyntheticPolarField, footprint_km: float, rng: random.Random) -> tuple[float, float]:
    center_x, center_y = field.depot_xy_km
    half = min(float(footprint_km), float(field.extent_km)) / 2.0
    low_x = max(0.5, center_x - half)
    high_x = min(field.extent_km - 0.5, center_x + half)
    low_y = max(0.5, center_y - half)
    high_y = min(field.extent_km - 0.5, center_y + half)
    best: tuple[float, float] | None = None
    best_score = -1.0
    for _ in range(100):
        x = rng.uniform(low_x, high_x)
        y = rng.uniform(low_y, high_y)
        if math.dist((x, y), field.depot_xy_km) < 1.5:
            continue
        fields = field.fields_at(x, y)
        score = 0.65 * fields["ice_confidence"] + 0.35 * fields["shadow"]
        if score > best_score:
            best = (x, y)
            best_score = score
        if fields["ice_confidence"] >= 0.50 and fields["shadow"] >= 0.35:
            return (x, y)
    if best is None:
        return (rng.uniform(low_x, high_x), rng.uniform(low_y, high_y))
    return best


def _task_payloads(scale: int, field: SyntheticPolarField, config: LunarIceConfig, rng: random.Random) -> dict[str, dict[str, Any]]:
    modes = _mode_sequence(scale, rng)
    raw_tasks: list[dict[str, Any]] = []
    footprint = ACTIVE_FOOTPRINT_BY_SCALE[int(scale)]
    for index in range(int(scale)):
        mode = modes[index]
        spec = OPERATION_MODE_SPECS[mode]
        x, y = _sample_target_xy(field, footprint, rng)
        fields = field.fields_at(x, y)
        service_time = rng.uniform(*spec.service_time_min)
        service_energy = rng.uniform(*spec.service_energy_proxy)
        expected_ice = 5.0 + 45.0 * fields["ice_confidence"] * rng.uniform(0.75, 1.25)
        task = {
            "id": f"ice_site_{index + 1:03d}",
            "kind": "psr_water_ice_target",
            "xy_km": [round(x, 6), round(y, 6)],
            "expected_ice_kg": round(expected_ice, 6),
            "ice_confidence": round(fields["ice_confidence"], 6),
            "science_weight": 1.0,
            "operation_mode": mode,
            "planned_depth_m": round(0.0 if mode == "detect" else rng.uniform(0.15, 1.0 if mode == "sample" else 2.0), 6),
            "planned_sample_mass_kg": round(0.0 if mode == "detect" else rng.uniform(0.25, 2.0 if mode == "sample" else 4.0), 6),
            "local_shadow_score": round(fields["shadow"], 6),
            "local_thermal_risk": round(fields["thermal_risk"], 6),
            "local_slope_risk": round(fields["slope_risk"], 6),
            "d": float(spec.demand),
            "sigma": round(service_time, 6),
            "g": round(service_energy, 6),
            "c_srv": round(0.02 * service_time + 0.10 * service_energy, 6),
            "r": 0.0,
            "D": 0.0,
        }
        raw_tasks.append(task)
    max_ice = max(task["expected_ice_kg"] for task in raw_tasks) or 1.0
    for task in raw_tasks:
        norm_ice = float(task["expected_ice_kg"]) / max_ice
        task["science_weight"] = round(0.6 * float(task["ice_confidence"]) + 0.4 * norm_ice, 6)
    return {task["id"]: task for task in raw_tasks}


def _edge_lookup(edges: list[dict]) -> dict[str, dict[str, dict]]:
    lookup: dict[str, dict[str, dict]] = {}
    for edge in edges:
        lookup[_edge_key(edge["from"], edge["to"])] = {option["path_type"]: option for option in edge["path_options"]}
    return lookup


class _LazyReferenceEdgeLookup:
    """Build only the path options needed by constructive reference scheduling."""

    def __init__(self, field: SyntheticPolarField, nodes: dict[str, tuple[float, float]], config: LunarIceConfig) -> None:
        self._field = field
        self._nodes = nodes
        self._config = config
        self._cache: dict[str, dict[str, dict]] = {}

    def __getitem__(self, key: str) -> dict[str, dict]:
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        source, target = key.split("->", 1)
        source_xy = self._nodes[source]
        target_xy = self._nodes[target]
        value = {
            "low_risk": path_option(self._field, source_xy, target_xy, "low_risk", self._config),
            "low_energy": path_option(self._field, source_xy, target_xy, "low_energy", self._config),
        }
        self._cache[key] = value
        return value


def _sortie_profile(sequence: list[str], tasks: dict[str, dict], edges: dict[str, dict[str, dict]], config: LunarIceConfig, *, start_time: float) -> dict:
    current = "depot"
    elapsed = float(start_time)
    travel_time = 0.0
    path_energy = 0.0
    service_energy = 0.0
    risk = 0.0
    shadow = 0.0
    distance = 0.0
    demand = 0.0
    service_starts: dict[str, float] = {}
    legs: list[dict] = []
    for task_id in sequence:
        option = edges[_edge_key(current, task_id)]["low_risk"]
        elapsed += float(option["travel_time_min"])
        travel_time += float(option["travel_time_min"])
        path_energy += float(option["energy_proxy"])
        risk += float(option["risk_integral"])
        shadow += float(option["shadow_exposure_min"])
        distance += float(option["path_distance_km"])
        task = tasks[task_id]
        service_starts[task_id] = elapsed
        elapsed += float(task["sigma"])
        service_energy += float(task["g"])
        shadow += float(task["sigma"]) * float(task["local_shadow_score"])
        risk += float(task["local_thermal_risk"]) * float(task["sigma"]) * 0.01
        demand += float(task["d"])
        legs.append({"from": current, "to": task_id, "path_type": "low_risk"})
        current = task_id
    back = edges[_edge_key(current, "depot")]["low_energy"]
    elapsed += float(back["travel_time_min"])
    travel_time += float(back["travel_time_min"])
    path_energy += float(back["energy_proxy"])
    risk += float(back["risk_integral"])
    shadow += float(back["shadow_exposure_min"])
    distance += float(back["path_distance_km"])
    legs.append({"from": current, "to": "depot", "path_type": "low_energy"})
    energy = path_energy + service_energy
    return_time = elapsed
    recharge_time = float(config.dock_overhead_min) + energy / max(1.0e-9, float(config.recharge_power_proxy_per_min))
    end_time = return_time + recharge_time
    return {
        "tasks": list(sequence),
        "legs": legs,
        "start_time": round(start_time, 6),
        "service_starts": {key: round(value, 6) for key, value in service_starts.items()},
        "return_time": round(return_time, 6),
        "recharge_time": round(recharge_time, 6),
        "end_time": round(end_time, 6),
        "travel_time": round(travel_time, 6),
        "distance_km": round(distance, 6),
        "energy_proxy": round(energy, 6),
        "risk_integral": round(risk, 6),
        "shadow_exposure_min": round(shadow, 6),
        "demand": round(demand, 6),
        "feasible": bool(
            demand <= config.q_ice + 1.0e-9
            and energy <= config.b_use + 1.0e-9
        ),
    }


def _route_feasible(sequence: list[str], tasks: dict[str, dict], edges: dict[str, dict[str, dict]], config: LunarIceConfig, scale: int) -> bool:
    if len(sequence) > int(config.max_tasks_per_trip):
        return False
    profile = _sortie_profile(sequence, tasks, edges, config, start_time=0.0)
    return bool(
        profile["feasible"]
        and float(profile["shadow_exposure_min"]) <= SHADOW_CAP_BY_SCALE[int(scale)] + 1.0e-9
    )


def _build_reference_solution(
    tasks: dict[str, dict],
    edges: dict[str, dict[str, dict]],
    config: LunarIceConfig,
    scale: int,
    *,
    task_order: list[str] | None = None,
) -> dict:
    depot = (float(config.resource_map_extent_km) / 2.0, float(config.resource_map_extent_km) / 2.0)
    ordered = list(task_order) if task_order is not None else sorted(
        tasks.keys(),
        key=lambda task_id: (
            math.atan2(float(tasks[task_id]["xy_km"][1]) - depot[1], float(tasks[task_id]["xy_km"][0]) - depot[0]),
            math.dist(tuple(tasks[task_id]["xy_km"]), depot),
        ),
    )
    routes: list[list[str]] = []
    current: list[str] = []
    for task_id in ordered:
        candidate = [*current, task_id]
        if current and not _route_feasible(candidate, tasks, edges, config, scale):
            routes.append(current)
            current = [task_id]
        else:
            current = candidate
    if current:
        routes.append(current)

    fleet_size = FLEET_BY_SCALE[int(scale)]
    availability = [0.0 for _ in range(fleet_size)]
    journeys: list[dict] = [{"vehicle_id": f"rover_{idx + 1:02d}", "sorties": []} for idx in range(fleet_size)]
    task_sortie_duration: dict[str, float] = {}
    for route in routes:
        vehicle_idx = min(range(fleet_size), key=lambda idx: availability[idx])
        start = availability[vehicle_idx]
        profile = _sortie_profile(route, tasks, edges, config, start_time=start)
        if float(profile["shadow_exposure_min"]) > SHADOW_CAP_BY_SCALE[int(scale)] + 1.0e-9:
            profile["feasible"] = False
        journeys[vehicle_idx]["sorties"].append(profile)
        availability[vehicle_idx] = float(profile["end_time"])
        duration = float(profile["end_time"]) - float(profile["start_time"])
        for task_id in route:
            task_sortie_duration[task_id] = duration

    journeys = [journey for journey in journeys if journey["sorties"]]
    makespan = max((float(sortie["end_time"]) for journey in journeys for sortie in journey["sorties"]), default=0.0)
    covered = [task_id for journey in journeys for sortie in journey["sorties"] for task_id in sortie["tasks"]]
    feasible = (
        sorted(covered) == sorted(tasks.keys())
        and all(bool(sortie["feasible"]) for journey in journeys for sortie in journey["sorties"])
        and makespan <= HORIZON_BY_SCALE[int(scale)] + 1.0e-9
    )
    return {
        "status": "FEASIBLE_REFERENCE" if feasible else "INFEASIBLE_REFERENCE",
        "exact_status": "NOT_SOLVED",
        "note": "Constructive reference schedule only; not an exact BPC certificate.",
        "journeys": journeys,
        "makespan_min": round(makespan, 6),
        "covered_task_count": len(set(covered)),
        "task_sortie_duration": {key: round(value, 6) for key, value in task_sortie_duration.items()},
    }


def _apply_time_windows(instance: dict, config: LunarIceConfig) -> None:
    scale = int(instance["scale"])
    tasks = instance["tasks"]
    horizon = HORIZON_BY_SCALE[scale]
    starts: dict[str, float] = {}
    durations = instance["reference_solution"].get("task_sortie_duration", {})
    for journey in instance["reference_solution"]["journeys"]:
        for sortie in journey["sorties"]:
            starts.update({task_id: float(value) for task_id, value in sortie["service_starts"].items()})
    for task_id, task in tasks.items():
        start = starts[task_id]
        sigma = float(task["sigma"])
        local_duration = float(durations.get(task_id, sigma + 2.0 * config.time_bucket_size))
        left_slack = max(2.0 * config.time_bucket_size, 0.10 * local_duration)
        right_slack = max(3.0 * config.time_bucket_size, 0.15 * local_duration)
        raw_r = start - left_slack
        raw_d = start + sigma + right_slack
        r_value = snap_down(max(0.0, raw_r), config.time_bucket_size)
        d_value = snap_up(min(horizon, raw_d), config.time_bucket_size)
        cap = WINDOW_WIDTH_CAP_BY_SCALE[scale]
        if d_value - r_value > cap:
            r_value, d_value = _tight_bucket_window(
                start=start,
                service_time=sigma,
                horizon=horizon,
                cap=cap,
                bucket=config.time_bucket_size,
            )
        min_width = sigma + 2.0 * config.time_bucket_size
        if d_value - r_value < min_width:
            d_value = min(horizon, snap_up(r_value + min_width, config.time_bucket_size))
        effective_cap = max(cap, snap_up(min_width, config.time_bucket_size))
        if d_value - r_value > effective_cap + 1.0e-9:
            r_value, d_value = _tight_bucket_window(
                start=start,
                service_time=sigma,
                horizon=horizon,
                cap=effective_cap,
                bucket=config.time_bucket_size,
            )
        task["r"] = round(r_value, 6)
        task["D"] = round(d_value, 6)


def _tight_bucket_window(*, start: float, service_time: float, horizon: float, cap: float, bucket: float) -> tuple[float, float]:
    finish = float(start) + float(service_time)
    min_width = float(service_time) + 2.0 * float(bucket)
    effective_cap = max(float(cap), snap_up(min_width, bucket))
    latest_r = snap_down(min(float(start), float(horizon)), bucket)
    earliest_r = snap_down(max(0.0, finish - effective_cap), bucket)
    best: tuple[float, float] | None = None
    best_key: tuple[float, float, float] | None = None
    candidate = earliest_r
    center = start + 0.5 * service_time
    while candidate <= latest_r + 1.0e-9:
        r_value = candidate
        d_value = snap_up(max(finish, r_value + min_width), bucket)
        width = d_value - r_value
        if d_value <= horizon + 1.0e-9 and width <= effective_cap + 1.0e-9:
            key = (width, abs((r_value + d_value) * 0.5 - center), r_value)
            if best_key is None or key < best_key:
                best = (r_value, d_value)
                best_key = key
        candidate += float(bucket)
    if best is not None:
        return best
    r_value = snap_down(max(0.0, min(start, horizon - effective_cap)), bucket)
    d_value = min(horizon, snap_up(max(finish, r_value + min_width), bucket))
    return r_value, d_value


def _objective(instance: dict, config: LunarIceConfig) -> float:
    tasks = instance["tasks"]
    completion_term = 0.0
    end_term = 0.0
    risk = 0.0
    energy = 0.0
    for journey in instance["reference_solution"]["journeys"]:
        for sortie in journey["sorties"]:
            end_term = max(end_term, float(sortie["end_time"]))
            risk += float(sortie["risk_integral"])
            energy += float(sortie["energy_proxy"])
            for task_id, start in sortie["service_starts"].items():
                task = tasks[task_id]
                completion_term += float(task["science_weight"]) * (float(start) + float(task["sigma"]))
    value = (
        config.objective_alpha_discovery_completion * completion_term
        + config.objective_beta_journey_end_time * end_term
        + config.objective_gamma_lunar_ice_risk * risk
        + config.objective_delta_energy * energy
    )
    return round(value, 6)


def generate_instance(scale: int, *, seed: int, index: int = 1, config: LunarIceConfig | None = None) -> dict:
    config = config or LunarIceConfig()
    scale = int(scale)
    label = scale_label(scale)
    rng = random.Random(int(seed))
    field = SyntheticPolarField.build(seed=int(seed), extent_km=config.resource_map_extent_km, resolution_m=config.synthetic_grid_resolution_m)
    tasks = _task_payloads(scale, field, config, rng)
    nodes = {"depot": field.depot_xy_km}
    nodes.update({task_id: tuple(task["xy_km"]) for task_id, task in tasks.items()})
    reference_edges = _LazyReferenceEdgeLookup(field, nodes, config)
    reference = _build_reference_solution(tasks, reference_edges, config, scale)
    instance = {
        "schema_version": "lunar_ice_bpc.instance.v1",
        "instance_id": f"lunar_ice_{label}_{index:03d}_seed{int(seed)}",
        "scale": scale,
        "seed": int(seed),
        "resource_map": {
            **field.to_payload(),
            "generator": SYNTHETIC_GENERATOR_ID,
            "risk_schema_version": RISK_SCHEMA_VERSION,
            "active_footprint_km": ACTIVE_FOOTPRINT_BY_SCALE[scale],
            "preview": field.preview(cells=72),
        },
        "depot": {"id": "depot", "kind": "peak_of_eternal_light", "xy_km": list(field.depot_xy_km)},
        "vehicle": {
            "fleet_size": FLEET_BY_SCALE[scale],
            "Q_ice": config.q_ice,
            "B_use": config.b_use,
            "energy_unit": config.energy_unit,
            "max_tasks_per_trip": config.max_tasks_per_trip,
            "dock_overhead_min": config.dock_overhead_min,
            "recharge_power_proxy_per_min": config.recharge_power_proxy_per_min,
            "depot_chargers": config.depot_chargers,
            "max_shadow_exposure_per_sortie": SHADOW_CAP_BY_SCALE[scale],
        },
        "scheduling": {
            "horizon_min": HORIZON_BY_SCALE[scale],
            "time_bucket_size": config.time_bucket_size,
            "time_window_policy_id": TIME_WINDOW_POLICY_ID,
            "operation_modes": list(OPERATION_MODE_SPECS.keys()),
            "operation_mode_mix": {mode: spec.ratio for mode, spec in OPERATION_MODE_SPECS.items()},
            "objective": {
                "mode": "weighted_discovery_completion",
                "alpha_discovery_completion": config.objective_alpha_discovery_completion,
                "beta_journey_end_time": config.objective_beta_journey_end_time,
                "gamma_lunar_ice_risk": config.objective_gamma_lunar_ice_risk,
                "delta_energy": config.objective_delta_energy,
            },
        },
        "tasks": tasks,
        "logical_graph": {
            "path_option_policy_id": PATH_OPTION_POLICY_ID,
            "nodes": [{"id": node_id, "xy_km": [round(xy[0], 6), round(xy[1], 6)]} for node_id, xy in nodes.items()],
            "edges": [],
        },
        "reference_solution": reference,
    }
    if reference["status"] != "FEASIBLE_REFERENCE":
        instance["validation"] = {
            "accepted": False,
            "reason": "reference_solution_infeasible",
            "time_window_policy_id": TIME_WINDOW_POLICY_ID,
            "risk_schema_version": RISK_SCHEMA_VERSION,
        }
        return instance
    edges = build_edge_options(field, nodes, config)
    instance["logical_graph"]["edges"] = edges
    _apply_time_windows(instance, config)
    instance["reference_solution"]["objective"] = _objective(instance, config)
    widths = [float(task["D"]) - float(task["r"]) for task in instance["tasks"].values()]
    starts: dict[str, float] = {}
    for journey in instance["reference_solution"]["journeys"]:
        for sortie in journey["sorties"]:
            starts.update({task_id: float(value) for task_id, value in sortie["service_starts"].items()})
    cap = WINDOW_WIDTH_CAP_BY_SCALE[scale]
    effective_caps = {
        task_id: max(cap, snap_up(float(task["sigma"]) + 2.0 * config.time_bucket_size, config.time_bucket_size))
        for task_id, task in instance["tasks"].items()
    }
    forced_count = sum(1 for value in effective_caps.values() if value > cap + 1.0e-9)
    windows_contain_reference = all(
        float(task["r"]) <= starts[task_id] + 1.0e-9
        and starts[task_id] + float(task["sigma"]) <= float(task["D"]) + 1.0e-9
        for task_id, task in instance["tasks"].items()
    )
    windows_meet_min_width = all(
        float(task["D"]) - float(task["r"]) >= float(task["sigma"]) + 2.0 * config.time_bucket_size - 1.0e-9
        for task in instance["tasks"].values()
    )
    windows_within_effective_cap = all(
        float(task["D"]) - float(task["r"]) <= effective_caps[task_id] + 1.0e-9
        for task_id, task in instance["tasks"].items()
    )
    mean_width = sum(widths) / max(1, len(widths))
    accepted = (
        mean_width <= MEAN_WINDOW_WIDTH_CAP_BY_SCALE[scale] + 1.0e-9
        and windows_contain_reference
        and windows_meet_min_width
        and windows_within_effective_cap
    )
    if accepted:
        validation_reason = "accepted"
    elif not windows_contain_reference:
        validation_reason = "time_window_misses_reference_service"
    elif not windows_meet_min_width:
        validation_reason = "time_window_below_min_width"
    elif not windows_within_effective_cap:
        validation_reason = "time_window_exceeds_effective_cap"
    else:
        validation_reason = "mean_window_width_too_wide"
    instance["validation"] = {
        "accepted": bool(accepted),
        "reason": validation_reason,
        "mean_window_width": round(mean_width, 6),
        "max_window_width": round(max(widths), 6),
        "configured_window_width_cap": cap,
        "max_effective_window_width_cap": round(max(effective_caps.values()), 6),
        "forced_min_width_count": forced_count,
        "windows_contain_reference": bool(windows_contain_reference),
        "windows_meet_min_width": bool(windows_meet_min_width),
        "windows_within_effective_cap": bool(windows_within_effective_cap),
        "time_window_policy_id": TIME_WINDOW_POLICY_ID,
        "risk_schema_version": RISK_SCHEMA_VERSION,
    }
    return instance
