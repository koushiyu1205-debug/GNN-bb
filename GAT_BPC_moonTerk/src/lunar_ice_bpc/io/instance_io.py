"""Instance read/write and validation helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lunar_ice_bpc.domain.scenario import (
    ACTIVE_FOOTPRINT_BY_SCALE,
    DISALLOWED_LINK_KEYS,
    FLEET_BY_SCALE,
    HORIZON_BY_SCALE,
    LunarIceConfig,
    PATH_TYPES,
    SERVICE_TIMING_POLICY_ID,
    SHADOW_CAP_BY_SCALE,
)


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _scan_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lower = str(key).lower()
            if any(token.lower() in lower for token in DISALLOWED_LINK_KEYS):
                issues.append(f"{path}.{key}")
            issues.extend(_scan_forbidden_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_forbidden_keys(child, f"{path}[{index}]"))
    return issues


def validate_instance(instance: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    config = LunarIceConfig()
    if instance.get("schema_version") != "lunar_ice_bpc.instance.v1":
        issues.append("schema_version must be lunar_ice_bpc.instance.v1")
    scale = _safe_int(instance.get("scale"))
    if scale not in ACTIVE_FOOTPRINT_BY_SCALE:
        issues.append(f"unsupported scale {instance.get('scale')!r}")
        scale = None
    if scale is not None:
        issues.extend(_scenario_parameter_issues(instance, scale, config))
    if "tasks" not in instance or not isinstance(instance["tasks"], dict) or not instance["tasks"]:
        issues.append("tasks must be a non-empty object")
    for task_id, task in sorted((instance.get("tasks") or {}).items()):
        mode = task.get("operation_mode")
        if mode not in {"detect", "sample", "drill"}:
            issues.append(f"{task_id}: unsupported operation_mode {mode!r}")
        if float(task.get("r", 0.0)) > float(task.get("D", 0.0)):
            issues.append(f"{task_id}: invalid time window")
        if scale is not None and not _inside_active_footprint(instance, task):
            issues.append(f"{task_id}: xy_km is outside active footprint")
    edge_count = 0
    for edge in instance.get("logical_graph", {}).get("edges", []):
        edge_count += 1
        options = edge.get("path_options", [])
        types = tuple(option.get("path_type") for option in options)
        if types != PATH_TYPES:
            issues.append(f"edge {edge.get('from')}->{edge.get('to')}: expected path types {PATH_TYPES}, got {types}")
    if edge_count == 0:
        issues.append("logical_graph.edges must be non-empty")
    forbidden = _scan_forbidden_keys(instance)
    if forbidden:
        issues.append("disallowed legacy link-planning keys found: " + ", ".join(forbidden[:10]))
    if scale is not None:
        issues.extend(_reference_solution_issues(instance, scale))
    return issues


def _scenario_parameter_issues(instance: dict[str, Any], scale: int, config: LunarIceConfig) -> list[str]:
    issues: list[str] = []
    resource = instance.get("resource_map") or {}
    vehicle = instance.get("vehicle") or {}
    scheduling = instance.get("scheduling") or {}
    explicit_service_timing_policy = scheduling.get(
        "service_timing_policy_id"
    )
    if (
        explicit_service_timing_policy is not None
        and explicit_service_timing_policy != SERVICE_TIMING_POLICY_ID
    ):
        issues.append(
            "scheduling.service_timing_policy_id must be "
            f"{SERVICE_TIMING_POLICY_ID!r}, got "
            f"{explicit_service_timing_policy!r}"
        )
    expected_shape = int(round(config.resource_map_extent_km * 1000.0 / config.synthetic_grid_resolution_m))
    checks = (
        ("resource_map.extent_km", resource.get("extent_km"), config.resource_map_extent_km),
        ("resource_map.resolution_m", resource.get("resolution_m"), config.synthetic_grid_resolution_m),
        ("resource_map.active_footprint_km", resource.get("active_footprint_km"), ACTIVE_FOOTPRINT_BY_SCALE[scale]),
        ("vehicle.fleet_size", vehicle.get("fleet_size"), FLEET_BY_SCALE[scale]),
        ("vehicle.Q_ice", vehicle.get("Q_ice"), config.q_ice),
        ("vehicle.B_use", vehicle.get("B_use"), config.b_use),
        ("vehicle.max_tasks_per_trip", vehicle.get("max_tasks_per_trip"), config.max_tasks_per_trip),
        ("vehicle.max_shadow_exposure_per_sortie", vehicle.get("max_shadow_exposure_per_sortie"), SHADOW_CAP_BY_SCALE[scale]),
        ("scheduling.horizon_min", scheduling.get("horizon_min"), HORIZON_BY_SCALE[scale]),
        ("scheduling.time_bucket_size", scheduling.get("time_bucket_size"), config.time_bucket_size),
    )
    for name, actual, expected in checks:
        if not _numeric_equal(actual, expected):
            issues.append(f"{name} must be {expected}, got {actual!r}")
    if list(resource.get("grid_shape") or []) != [expected_shape, expected_shape]:
        issues.append(f"resource_map.grid_shape must be [{expected_shape}, {expected_shape}]")
    if vehicle.get("energy_unit") != config.energy_unit:
        issues.append(f"vehicle.energy_unit must be {config.energy_unit!r}")
    if vehicle.get("depot_chargers") != config.depot_chargers:
        issues.append(f"vehicle.depot_chargers must be {config.depot_chargers!r}")
    return issues


def _reference_solution_issues(instance: dict[str, Any], scale: int) -> list[str]:
    issues: list[str] = []
    vehicle = instance.get("vehicle") or {}
    horizon = float((instance.get("scheduling") or {}).get("horizon_min", HORIZON_BY_SCALE[scale]))
    shadow_cap = float(vehicle.get("max_shadow_exposure_per_sortie", SHADOW_CAP_BY_SCALE[scale]))
    energy_cap = float(vehicle.get("B_use", LunarIceConfig().b_use))
    capacity = float(vehicle.get("Q_ice", LunarIceConfig().q_ice))
    max_tasks = int(vehicle.get("max_tasks_per_trip", LunarIceConfig().max_tasks_per_trip))
    for journey_index, journey in enumerate((instance.get("reference_solution") or {}).get("journeys", []) or [], start=1):
        for sortie_index, sortie in enumerate(journey.get("sorties", []) or [], start=1):
            prefix = f"reference_solution.journeys[{journey_index}].sorties[{sortie_index}]"
            if len(sortie.get("tasks", []) or []) > max_tasks:
                issues.append(f"{prefix}: exceeds max_tasks_per_trip")
            if float(sortie.get("shadow_exposure_min", 0.0)) > shadow_cap + 1.0e-9:
                issues.append(f"{prefix}: exceeds max_shadow_exposure_per_sortie")
            if float(sortie.get("energy_proxy", 0.0)) > energy_cap + 1.0e-9:
                issues.append(f"{prefix}: exceeds B_use")
            if float(sortie.get("demand", 0.0)) > capacity + 1.0e-9:
                issues.append(f"{prefix}: exceeds Q_ice")
            if float(sortie.get("end_time", 0.0)) > horizon + 1.0e-9:
                issues.append(f"{prefix}: exceeds horizon_min")
    return issues


def _inside_active_footprint(instance: dict[str, Any], task: dict[str, Any]) -> bool:
    try:
        depot = instance["depot"]["xy_km"]
        xy = task["xy_km"]
        footprint = float((instance.get("resource_map") or {})["active_footprint_km"])
        half = footprint / 2.0 + 1.0e-9
        return abs(float(xy[0]) - float(depot[0])) <= half and abs(float(xy[1]) - float(depot[1])) <= half
    except (KeyError, TypeError, ValueError):
        return False


def _numeric_equal(actual: object, expected: float | int) -> bool:
    try:
        return abs(float(actual) - float(expected)) <= 1.0e-9
    except (TypeError, ValueError):
        return False


def _safe_int(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
