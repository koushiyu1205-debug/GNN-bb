"""No-leakage pre-call arc features for proof-queue potential ranking."""

from __future__ import annotations

from dataclasses import dataclass
from math import log1p, sqrt

from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
    build_static_graph_features,
)


PROOF_QUEUE_ARC_FEATURE_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v3_proof_queue_arc_features.v1"
)


@dataclass(frozen=True)
class ProofQueueArcFeatures:
    instance_content_hash: str
    source_state_hash: str
    arc_candidate_ids: tuple[str, ...]
    rows: tuple[tuple[float, ...], ...]
    feature_names: tuple[str, ...]
    schema_version: str = PROOF_QUEUE_ARC_FEATURE_SCHEMA_V1


def build_proof_queue_arc_features(
    data: LunarIceData,
    snapshot: dict,
) -> ProofQueueArcFeatures:
    """Build features available before the exact Native proof call.

    No completed-route, dominance-trace, queue-outcome, or future-RMP field is
    consumed here.  Dual ranks and normalizations are computed within the
    current request, so fold-held-out states do not leak training statistics.
    """

    if str(snapshot.get("instance_content_hash") or "") != (
        data.instance_content_hash
    ):
        raise ValueError("snapshot/data content hash mismatch")
    task_duals = {
        str(key): float(value)
        for key, value in dict(
            (snapshot.get("true_duals") or {}).get("task_duals") or {}
        ).items()
    }
    if set(task_duals) != set(data.task_ids):
        raise ValueError("snapshot task-dual universe mismatch")
    dual_values = [task_duals[task_id] for task_id in data.task_ids]
    dual_mean = sum(dual_values) / max(1, len(dual_values))
    dual_variance = sum(
        (value - dual_mean) ** 2 for value in dual_values
    ) / max(1, len(dual_values))
    dual_std = max(1.0e-12, sqrt(dual_variance))
    dual_maxabs = max(1.0e-12, *(abs(value) for value in dual_values))
    sorted_pairs = sorted(
        (value, task_id) for task_id, value in task_duals.items()
    )
    rank_by_task = {
        task_id: index / max(1, len(sorted_pairs) - 1)
        for index, (_, task_id) in enumerate(sorted_pairs)
    }

    static = build_static_graph_features(data)
    node_dynamic = [(0.0, 0.0, 0.0, 0.0, 0.0)]
    for task_id in data.task_ids:
        value = task_duals[task_id]
        node_dynamic.append(
            (
                value,
                (value - dual_mean) / dual_std,
                value / dual_maxabs,
                rank_by_task[task_id],
                1.0 if value > 0.0 else 0.0,
            )
        )
    node_rows = tuple(
        tuple(static_row) + tuple(dynamic_row)
        for static_row, dynamic_row in zip(
            static.node_features, node_dynamic
        )
    )
    trajectory = dict(snapshot.get("trajectory_features") or {})
    global_features = (
        log1p(float(data.scale)),
        float(
            (snapshot.get("true_duals") or {}).get("fleet_dual") or 0.0
        ),
        dual_mean,
        dual_std,
        min(dual_values, default=0.0),
        max(dual_values, default=0.0),
        log1p(float(snapshot.get("active_column_count") or 0.0)),
        log1p(float(snapshot.get("round") or 0.0)),
        log1p(
            max(
                0.0,
                float(
                    trajectory.get("previous_proof_pass_wall_time")
                    or 0.0
                ),
            )
        ),
        log1p(
            max(
                0.0,
                float(
                    trajectory.get("previous_harvest_processed_labels")
                    or 0.0
                ),
            )
        ),
        float(
            trajectory.get("dual_l1_delta_from_previous") or 0.0
        ),
        float(
            trajectory.get("dual_linf_delta_from_previous") or 0.0
        ),
    )
    rows = []
    for source, target, edge in zip(
        static.arc_sources,
        static.arc_targets,
        static.arc_features,
    ):
        source_row = node_rows[source]
        target_row = node_rows[target]
        target_dual_z = target_row[len(NODE_STATIC_FEATURES) + 1]
        rows.append(
            (
                *source_row,
                *target_row,
                *edge,
                *(target_dual_z * value for value in edge),
                *global_features,
            )
        )
    node_names = (
        *NODE_STATIC_FEATURES,
        "cover_dual",
        "cover_dual_z_within_request",
        "cover_dual_over_maxabs_within_request",
        "cover_dual_rank_within_request",
        "cover_dual_positive",
    )
    feature_names = (
        *(f"source_{name}" for name in node_names),
        *(f"target_{name}" for name in node_names),
        *EDGE_STATIC_FEATURES,
        *(f"target_dual_z_x_{name}" for name in EDGE_STATIC_FEATURES),
        "log1p_scale",
        "fleet_dual",
        "cover_dual_mean",
        "cover_dual_std",
        "cover_dual_min",
        "cover_dual_max",
        "log1p_active_column_count",
        "log1p_round",
        "log1p_previous_proof_wall",
        "log1p_previous_harvest_processed_labels",
        "dual_l1_delta_from_previous",
        "dual_linf_delta_from_previous",
    )
    if any(len(row) != len(feature_names) for row in rows):
        raise AssertionError("proof queue arc feature dimension mismatch")
    return ProofQueueArcFeatures(
        instance_content_hash=data.instance_content_hash,
        source_state_hash=str(snapshot.get("state_hash") or ""),
        arc_candidate_ids=static.arc_candidate_ids,
        rows=tuple(rows),
        feature_names=tuple(feature_names),
    )
