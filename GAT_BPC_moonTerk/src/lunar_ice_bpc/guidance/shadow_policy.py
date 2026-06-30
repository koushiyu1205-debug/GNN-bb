"""Shadow-only guidance policy for diagnostics."""

from __future__ import annotations

from typing import Any

from lunar_ice_bpc.guidance.graph_builder import build_guidance_graph


def build_shadow_report(instance: dict[str, Any]) -> dict[str, Any]:
    graph = build_guidance_graph(instance)
    node_schema = graph["node_feature_schema"]
    idx_science = node_schema.index("science_weight")
    idx_shadow = node_schema.index("local_shadow_score")
    idx_thermal = node_schema.index("local_thermal_risk")
    idx_drill = node_schema.index("mode_drill")
    scored_nodes = []
    for node in graph["nodes"]:
        features = node["features"]
        score = (
            0.45 * float(features[idx_science])
            + 0.25 * float(features[idx_shadow])
            + 0.20 * float(features[idx_thermal])
            + 0.10 * float(features[idx_drill])
        )
        scored_nodes.append({"id": node["id"], "shadow_priority_score": round(score, 9)})
    scored_nodes.sort(key=lambda item: (-float(item["shadow_priority_score"]), str(item["id"])))
    return {
        "schema_version": "lunar_ice_bpc.gat_shadow_report.v1",
        "guidance_graph_schema_version": graph["schema_version"],
        "instance_id": graph["instance_id"],
        "mode": "shadow_only",
        "mutates_solver": False,
        "can_certify": False,
        "exact_status_effect": "none",
        "node_feature_schema": graph["node_feature_schema"],
        "edge_feature_schema": graph["edge_feature_schema"],
        "task_priority": scored_nodes,
        "edge_count": len(graph["edges"]),
        "node_count": len(graph["nodes"]),
        "note": "Diagnostic shadow guidance only; not a pricing oracle, lower bound, or certificate.",
    }
