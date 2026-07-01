"""Build deterministic water-ice graph features for future GAT models."""

from __future__ import annotations

from typing import Any


NODE_FEATURES: tuple[str, ...] = (
    "is_depot",
    "is_task",
    "x_norm",
    "y_norm",
    "expected_ice_norm",
    "ice_confidence",
    "science_weight",
    "local_shadow_score",
    "local_thermal_risk",
    "local_slope_risk",
    "demand",
    "service_time_norm",
    "service_energy_norm",
    "time_window_start_norm",
    "time_window_end_norm",
    "time_window_width_norm",
    "mode_detect",
    "mode_sample",
    "mode_drill",
)

EDGE_FEATURES: tuple[str, ...] = (
    "source_is_depot",
    "target_is_depot",
    "dx_norm",
    "dy_norm",
    "pair_distance_norm",
    "same_sector",
    "travel_time_norm",
    "energy_norm",
    "risk_norm",
    "distance_norm",
    "shadow_exposure_norm",
    "is_low_time",
    "is_low_energy",
    "is_low_risk",
)


def build_guidance_graph(instance: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic feature arrays without importing ML frameworks."""

    extent = float(instance["resource_map"]["extent_km"])
    horizon = float(instance["scheduling"]["horizon_min"])
    tasks = instance["tasks"]
    max_expected_ice = max((float(task["expected_ice_kg"]) for task in tasks.values()), default=1.0) or 1.0
    max_service_time = max((float(task["sigma"]) for task in tasks.values()), default=1.0) or 1.0
    max_service_energy = max((float(task["g"]) for task in tasks.values()), default=1.0) or 1.0
    max_window_width = max((float(task["D"]) - float(task["r"]) for task in tasks.values()), default=1.0) or 1.0
    location_by_id = {"depot": tuple(float(value) for value in instance["depot"]["xy_km"])}
    nodes = []
    nodes.append(
        {
            "id": "depot",
            "kind": str(instance["depot"].get("kind") or "depot"),
            "features": [
                1.0,
                0.0,
                float(instance["depot"]["xy_km"][0]) / extent,
                float(instance["depot"]["xy_km"][1]) / extent,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ],
        }
    )
    for task_id, task in sorted(tasks.items()):
        mode = str(task["operation_mode"])
        window_start = float(task["r"])
        window_end = float(task["D"])
        location_by_id[str(task_id)] = tuple(float(value) for value in task["xy_km"])
        nodes.append(
            {
                "id": task_id,
                "kind": str(task.get("kind") or "task"),
                "features": [
                    0.0,
                    1.0,
                    float(task["xy_km"][0]) / extent,
                    float(task["xy_km"][1]) / extent,
                    float(task["expected_ice_kg"]) / max_expected_ice,
                    float(task["ice_confidence"]),
                    float(task["science_weight"]),
                    float(task["local_shadow_score"]),
                    float(task["local_thermal_risk"]),
                    float(task["local_slope_risk"]),
                    float(task["d"]),
                    float(task["sigma"]) / max_service_time,
                    float(task["g"]) / max_service_energy,
                    window_start / horizon,
                    window_end / horizon,
                    (window_end - window_start) / max_window_width,
                    1.0 if mode == "detect" else 0.0,
                    1.0 if mode == "sample" else 0.0,
                    1.0 if mode == "drill" else 0.0,
                ],
            }
        )

    options = [option for edge in instance["logical_graph"]["edges"] for option in edge["path_options"]]
    max_time = max((float(option["travel_time_min"]) for option in options), default=1.0) or 1.0
    max_energy = max((float(option["energy_proxy"]) for option in options), default=1.0) or 1.0
    max_risk = max((float(option["risk_integral"]) for option in options), default=1.0) or 1.0
    max_distance = max((float(option["path_distance_km"]) for option in options), default=1.0) or 1.0
    max_shadow = max((float(option["shadow_exposure_min"]) for option in options), default=1.0) or 1.0
    edges = []
    for edge in instance["logical_graph"]["edges"]:
        source = edge["from"]
        target = edge["to"]
        source_xy = location_by_id[str(source)]
        target_xy = location_by_id[str(target)]
        dx = float(target_xy[0]) - float(source_xy[0])
        dy = float(target_xy[1]) - float(source_xy[1])
        source_sector = _sector(source_xy, location_by_id["depot"])
        target_sector = _sector(target_xy, location_by_id["depot"])
        for option in edge["path_options"]:
            path_type = str(option["path_type"])
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "path_type": path_type,
                    "features": [
                        1.0 if source == "depot" else 0.0,
                        1.0 if target == "depot" else 0.0,
                        dx / extent,
                        dy / extent,
                        float(option["path_distance_km"]) / max_distance,
                        1.0 if source_sector == target_sector else 0.0,
                        float(option["travel_time_min"]) / max_time,
                        float(option["energy_proxy"]) / max_energy,
                        float(option["risk_integral"]) / max_risk,
                        float(option["path_distance_km"]) / max_distance,
                        float(option["shadow_exposure_min"]) / max_shadow,
                        1.0 if path_type == "low_time" else 0.0,
                        1.0 if path_type == "low_energy" else 0.0,
                        1.0 if path_type == "low_risk" else 0.0,
                    ],
                }
            )
    return {
        "schema_version": "lunar_ice_bpc.guidance_graph.v1",
        "instance_id": instance["instance_id"],
        "node_feature_schema": list(NODE_FEATURES),
        "edge_feature_schema": list(EDGE_FEATURES),
        "nodes": nodes,
        "edges": edges,
        "task_node_count": len(tasks),
        "depot_node_count": 1,
        "directed_edge_count": len(instance["logical_graph"]["edges"]),
        "path_option_edge_count": len(edges),
    }


def _sector(point: tuple[float, float], origin: tuple[float, float]) -> int:
    dx = float(point[0]) - float(origin[0])
    dy = float(point[1]) - float(origin[1])
    if abs(dx) <= 1.0e-12 and abs(dy) <= 1.0e-12:
        return -1
    if dx >= 0.0 and dy >= 0.0:
        return 0
    if dx < 0.0 <= dy:
        return 1
    if dx < 0.0 and dy < 0.0:
        return 2
    return 3
