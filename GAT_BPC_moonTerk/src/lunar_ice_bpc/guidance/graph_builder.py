"""Build deterministic water-ice graph features for future GAT models."""

from __future__ import annotations

from typing import Any


NODE_FEATURES: tuple[str, ...] = (
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
    "mode_detect",
    "mode_sample",
    "mode_drill",
)

EDGE_FEATURES: tuple[str, ...] = (
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
    tasks = instance["tasks"]
    max_expected_ice = max((float(task["expected_ice_kg"]) for task in tasks.values()), default=1.0) or 1.0
    max_service_time = max((float(task["sigma"]) for task in tasks.values()), default=1.0) or 1.0
    max_service_energy = max((float(task["g"]) for task in tasks.values()), default=1.0) or 1.0
    nodes = []
    for task_id, task in sorted(tasks.items()):
        mode = str(task["operation_mode"])
        nodes.append(
            {
                "id": task_id,
                "features": [
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
        if source == "depot" or target == "depot":
            continue
        for option in edge["path_options"]:
            path_type = str(option["path_type"])
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "path_type": path_type,
                    "features": [
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
    }

