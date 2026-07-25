"""Content-addressed static graph features for ranking models.

The cache stores immutable Python tuples rather than framework tensors.  This
keeps cache identity independent of a device and allows the deployment gate to
bypass before importing torch.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from math import isfinite, log1p
from threading import RLock
from typing import Any

from lunar_ice_bpc.domain.scenario import PATH_TYPES
from lunar_ice_bpc.exact.bpc.guidance.contracts import canonical_arc_candidate_id
from lunar_ice_bpc.exact.core.data import LunarIceData


STATIC_FEATURE_SCHEMA_V2 = "lunar_ice_bpc.gat_static_features.v2"
COMPOSITE_FEATURE_SCHEMA_V3 = "lunar_ice_bpc.gat_features.v3"
HARVEST_MODEL_CONTEXT_SCHEMA_V2 = (
    "lunar_ice_bpc.gat_harvest_model_context."
    "v2_without_selector_facts"
)
NODE_STATIC_FEATURES = (
    "is_depot",
    "is_task",
    "x_over_extent",
    "y_over_extent",
    "science_weight",
    "demand",
    "service_time_over_horizon",
    "service_energy_over_limit",
    "service_cost",
    "ready_over_horizon",
    "due_over_horizon",
    "window_width_over_horizon",
    "local_shadow_score",
    "local_thermal_risk",
    "mode_detect",
    "mode_sample",
    "mode_drill",
)
EDGE_STATIC_FEATURES = (
    "travel_time_over_horizon",
    "energy_over_limit",
    "risk",
    "distance",
    "shadow_over_limit",
    "is_low_time",
    "is_low_energy",
    "is_low_risk",
)
DYNAMIC_NODE_FEATURES = (
    "cover_dual",
    "log1p_scale",
    "log1p_memory_limit_bytes",
    "log1p_wall_time_budget_sec",
    "pricing_mode_exact",
    "pricing_mode_harvest",
)

QUEUE_POLICY_ENCODING = {
    "Q0": 0.0,
    "Q1": 0.25,
    "Q2": 0.50,
    "Q3": 0.75,
    "Q4": 1.0,
}


def learned_harvest_context(values) -> tuple[float, float, float, float]:
    """Remove facts already consumed by the deterministic harvest selector.

    ``would_change_active_support`` directly defines the current grade-4
    label, and ``is_new_task_set`` is already applied by P0's mandatory
    new-row-before-replacement partition.  Exposing either value to the
    learned head creates target leakage or duplicates deterministic policy.
    The raw values remain in telemetry/replay; only model input is masked.
    """

    context = tuple(float(value) for value in values)
    if len(context) != 4:
        raise ValueError("harvest candidate context must have four values")
    if any(not isfinite(value) for value in context):
        raise ValueError("harvest candidate context must be finite")
    return (context[0], 0.0, 0.0, context[3])


@dataclass(frozen=True)
class StaticGraphFeatures:
    instance_content_hash: str
    node_ids: tuple[str, ...]
    node_features: tuple[tuple[float, ...], ...]
    arc_candidate_ids: tuple[str, ...]
    arc_sources: tuple[int, ...]
    arc_targets: tuple[int, ...]
    arc_features: tuple[tuple[float, ...], ...]
    schema_version: str = STATIC_FEATURE_SCHEMA_V2


_CACHE_LOCK = RLock()
_STATIC_CACHE: OrderedDict[str, StaticGraphFeatures] = OrderedDict()
_STATIC_CACHE_MAX_ENTRIES = 32


def build_static_graph_features(data: LunarIceData) -> StaticGraphFeatures:
    cache_key = data.instance_content_hash
    with _CACHE_LOCK:
        cached = _STATIC_CACHE.get(cache_key)
        if cached is not None:
            _STATIC_CACHE.move_to_end(cache_key)
            return cached

    node_ids = ("depot", *data.task_ids)
    node_index = {node_id: index for index, node_id in enumerate(node_ids)}
    coordinates = [data.depot_xy_km] + [
        data.tasks[task_id].xy_km for task_id in data.task_ids
    ]
    extent = max(
        1.0,
        max(abs(float(value)) for point in coordinates for value in point),
    )
    horizon = max(1.0, float(data.horizon))
    energy_limit = max(1.0, float(data.energy_limit))
    shadow_limit = max(1.0, float(data.max_shadow_exposure_per_sortie))
    rows: list[tuple[float, ...]] = [
        (
            1.0,
            0.0,
            float(data.depot_xy_km[0]) / extent,
            float(data.depot_xy_km[1]) / extent,
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
        )
    ]
    for task_id in data.task_ids:
        task = data.tasks[task_id]
        mode = str(task.operation_mode)
        rows.append(
            (
                0.0,
                1.0,
                float(task.xy_km[0]) / extent,
                float(task.xy_km[1]) / extent,
                float(task.science_weight),
                float(task.demand),
                float(task.service_time) / horizon,
                float(task.service_energy) / energy_limit,
                float(task.service_cost),
                float(task.ready_time) / horizon,
                float(task.due_time) / horizon,
                float(task.due_time - task.ready_time) / horizon,
                float(task.local_shadow_score),
                float(task.local_thermal_risk),
                1.0 if mode == "detect" else 0.0,
                1.0 if mode == "sample" else 0.0,
                1.0 if mode == "drill" else 0.0,
            )
        )

    arc_ids: list[str] = []
    sources: list[int] = []
    targets: list[int] = []
    edge_rows: list[tuple[float, ...]] = []
    for (source, target), by_type in sorted(data.arcs.items()):
        for path_type in PATH_TYPES:
            option = by_type[path_type]
            arc_ids.append(canonical_arc_candidate_id(source, target, path_type))
            sources.append(node_index[source])
            targets.append(node_index[target])
            edge_rows.append(
                (
                    float(option.travel_time_min) / horizon,
                    float(option.energy_proxy) / energy_limit,
                    float(option.risk_integral),
                    float(option.distance_km) / extent,
                    float(option.shadow_exposure_min) / shadow_limit,
                    1.0 if path_type == "low_time" else 0.0,
                    1.0 if path_type == "low_energy" else 0.0,
                    1.0 if path_type == "low_risk" else 0.0,
                )
            )
    value = StaticGraphFeatures(
        instance_content_hash=cache_key,
        node_ids=tuple(node_ids),
        node_features=tuple(rows),
        arc_candidate_ids=tuple(arc_ids),
        arc_sources=tuple(sources),
        arc_targets=tuple(targets),
        arc_features=tuple(edge_rows),
    )
    with _CACHE_LOCK:
        old = _STATIC_CACHE.get(cache_key)
        if old is not None:
            return old
        _STATIC_CACHE[cache_key] = value
        while len(_STATIC_CACHE) > _STATIC_CACHE_MAX_ENTRIES:
            _STATIC_CACHE.popitem(last=False)
    return value


def dynamic_node_features(request: Any) -> tuple[tuple[float, ...], ...]:
    data = request.data
    memory_bytes = max(0.0, float(request.memory_limit_gb)) * (1024.0**3)
    wall = (
        0.0
        if request.wall_time_limit_sec is None
        else max(0.0, float(request.wall_time_limit_sec))
    )
    exact = 1.0 if str(request.mode) == "exact_proof" else 0.0
    harvest = 1.0 - exact
    common = (
        log1p(float(data.scale)),
        log1p(memory_bytes),
        log1p(wall),
        exact,
        harvest,
    )
    return (
        (0.0, *common),
        *(
            (
                float(request.true_duals.cover.get(task_id, 0.0)),
                *common,
            )
            for task_id in data.task_ids
        ),
    )


def encode_queue_policy_id(policy_id: str) -> float:
    try:
        return QUEUE_POLICY_ENCODING[str(policy_id)]
    except KeyError as exc:
        raise ValueError(f"unsupported queue policy {policy_id!r}") from exc


def clear_static_feature_cache() -> None:
    with _CACHE_LOCK:
        _STATIC_CACHE.clear()
