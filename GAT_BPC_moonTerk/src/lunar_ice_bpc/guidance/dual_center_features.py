"""Framework-free root-state features for the dual-center head."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log1p

from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
    build_static_graph_features,
)


ROOT_DUAL_CENTER_FEATURE_SCHEMA = (
    "lunar_ice_bpc.root_dual_center_features.v1"
)
ROOT_DUAL_CENTER_DYNAMIC_NODE_FEATURES = (
    "initial_cover_dual",
    "initial_fleet_dual",
    "log1p_scale",
    "log1p_memory_limit_bytes",
    "log1p_wall_time_budget_sec",
    "is_root",
)
ROOT_DUAL_CENTER_RESOURCE_CONTEXT = (
    "log1p_scale",
    "log1p_memory_limit_bytes",
    "log1p_wall_time_budget_sec",
    "initial_fleet_dual",
)


@dataclass(frozen=True)
class RootDualCenterFeatures:
    instance_content_hash: str
    task_ids: tuple[str, ...]
    node_features: tuple[tuple[float, ...], ...]
    edge_sources: tuple[int, ...]
    edge_targets: tuple[int, ...]
    edge_features: tuple[tuple[float, ...], ...]
    task_node_indices: tuple[int, ...]
    resource_context: tuple[float, ...]
    schema_version: str = ROOT_DUAL_CENTER_FEATURE_SCHEMA


def build_root_dual_center_features(
    data: LunarIceData,
    initial_duals: JourneyDuals,
    *,
    memory_limit_bytes: int,
    wall_time_budget_sec: float,
) -> RootDualCenterFeatures:
    expected_tasks = set(data.task_ids)
    observed_tasks = {str(task_id) for task_id in initial_duals.cover}
    if observed_tasks != expected_tasks:
        raise ValueError("initial dual task universe mismatch")
    memory = max(0, int(memory_limit_bytes))
    wall = max(0.0, float(wall_time_budget_sec))
    common = (
        float(initial_duals.fleet_limit),
        log1p(float(data.scale)),
        log1p(float(memory)),
        log1p(wall),
        1.0,
    )
    static = build_static_graph_features(data)
    dynamic_rows = (
        (0.0, *common),
        *(
            (
                float(initial_duals.cover[task_id]),
                *common,
            )
            for task_id in data.task_ids
        ),
    )
    node_rows = tuple(
        tuple(float(value) for value in static_row + dynamic_row)
        for static_row, dynamic_row in zip(
            static.node_features, dynamic_rows
        )
    )
    resource_context = (
        log1p(float(data.scale)),
        log1p(float(memory)),
        log1p(wall),
        float(initial_duals.fleet_limit),
    )
    all_values = (
        value
        for row in (*node_rows, *static.arc_features)
        for value in row
    )
    if any(not isfinite(float(value)) for value in all_values):
        raise ValueError("root dual-center features contain NaN/Inf")
    if any(
        not isfinite(float(value)) for value in resource_context
    ):
        raise ValueError(
            "root dual-center resource context contains NaN/Inf"
        )
    return RootDualCenterFeatures(
        instance_content_hash=data.instance_content_hash,
        task_ids=tuple(data.task_ids),
        node_features=node_rows,
        edge_sources=static.arc_sources,
        edge_targets=static.arc_targets,
        edge_features=static.arc_features,
        task_node_indices=tuple(range(1, len(data.task_ids) + 1)),
        resource_context=resource_context,
    )


def root_dual_center_feature_dimensions() -> tuple[int, int, int]:
    return (
        len(NODE_STATIC_FEATURES)
        + len(ROOT_DUAL_CENTER_DYNAMIC_NODE_FEATURES),
        len(EDGE_STATIC_FEATURES),
        len(ROOT_DUAL_CENTER_RESOURCE_CONTEXT),
    )
