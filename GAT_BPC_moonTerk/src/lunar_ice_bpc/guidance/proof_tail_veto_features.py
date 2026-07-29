"""Framework-free features for the P0 V3 one-shot proof-tail veto gate."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log1p
from typing import Mapping

from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
    build_static_graph_features,
)


PROOF_TAIL_VETO_FEATURE_SCHEMA = (
    "lunar_ice_bpc.p0v3_proof_tail_veto_features.v2"
)
NODE_DYNAMIC_FEATURES = (
    "current_true_dual",
    "absolute_true_dual",
    "active_master_support_frequency",
    "rmp_primal_lambda_support",
    "rmp_primal_support",
    "rmp_fractional_support",
)
GLOBAL_FEATURES = (
    "log1p_scale",
    "round_over_100",
    "log1p_active_column_count",
    "previous_added_over_target",
    "previous_harvest_over_target",
    "penultimate_harvest_over_target",
    "harvest_count_delta_over_target",
    "log1p_previous_harvest_processed_labels",
    "log1p_penultimate_harvest_processed_labels",
    "previous_best_true_rc",
    "log1p_abs_previous_best_true_rc_micro",
    "penultimate_best_true_rc",
    "best_true_rc_delta",
    "dual_l1_delta_from_previous",
    "dual_linf_delta_from_previous",
    "dual_l1_delta_from_penultimate",
    "dual_linf_delta_from_penultimate",
    "node_lp_bound_delta",
    "node_lp_bound_delta_from_penultimate",
    "node_lp_bound",
    "rmp_primal_nonzero_over_scale",
    "rmp_primal_fractional_over_scale",
    "harvest_target_over_64",
    "sparse_harvest_strike_fraction",
)


@dataclass(frozen=True)
class ProofTailVetoFeatures:
    instance_content_hash: str
    state_hash: str
    scale: int
    node_features: tuple[tuple[float, ...], ...]
    edge_index: tuple[tuple[int, ...], tuple[int, ...]]
    edge_features: tuple[tuple[float, ...], ...]
    global_features: tuple[float, ...]
    schema_version: str = PROOF_TAIL_VETO_FEATURE_SCHEMA


def build_proof_tail_veto_features(
    data: LunarIceData,
    snapshot: Mapping[str, object],
    *,
    column_catalog: Mapping[str, object] | None = None,
) -> ProofTailVetoFeatures:
    """Build features available immediately before the one permitted call."""

    if str(snapshot.get("instance_content_hash") or "") != (
        data.instance_content_hash
    ):
        raise ValueError("proof-tail feature instance hash mismatch")
    if str(snapshot.get("source_pass_strategy") or "") != "proof_only":
        raise ValueError("proof-tail veto features require a proof-only trigger")
    required_strikes = int(
        snapshot.get("required_sparse_harvest_strikes") or 1
    )
    observed_strikes = int(
        snapshot.get("sparse_harvest_strike_count") or 0
    )
    if required_strikes < 2 or observed_strikes < required_strikes:
        raise ValueError("proof-tail veto features require a two-strike trigger")
    return _build_graph_state_features(
        data,
        snapshot,
        column_catalog=column_catalog,
    )


def build_harvest_dynamics_features(
    data: LunarIceData,
    snapshot: Mapping[str, object],
    *,
    column_catalog: Mapping[str, object] | None = None,
) -> ProofTailVetoFeatures:
    """Build offline features for an observed bounded-harvest state."""

    if str(snapshot.get("instance_content_hash") or "") != (
        data.instance_content_hash
    ):
        raise ValueError("harvest-dynamics feature instance hash mismatch")
    if str(snapshot.get("source_pass_strategy") or "") != (
        "harvest_then_proof"
    ):
        raise ValueError(
            "harvest-dynamics features require a harvest state"
        )
    return _build_graph_state_features(
        data,
        snapshot,
        column_catalog=column_catalog,
    )


def _build_graph_state_features(
    data: LunarIceData,
    snapshot: Mapping[str, object],
    *,
    column_catalog: Mapping[str, object] | None,
) -> ProofTailVetoFeatures:
    required_strikes = int(
        snapshot.get("required_sparse_harvest_strikes") or 1
    )
    observed_strikes = int(
        snapshot.get("sparse_harvest_strike_count") or 0
    )

    static = build_static_graph_features(data)
    trajectory = dict(snapshot.get("trajectory_features") or {})
    duals = dict(snapshot.get("true_duals") or {})
    task_duals = {
        str(key): float(value)
        for key, value in (duals.get("task_duals") or {}).items()
    }
    primal_lambda, primal_support, fractional_support = _primal_support(
        snapshot
    )
    active_support = _active_support_frequency(
        data,
        snapshot,
        column_catalog=column_catalog,
    )
    node_rows: list[tuple[float, ...]] = []
    for node_id, static_row in zip(
        static.node_ids,
        static.node_features,
        strict=True,
    ):
        dual = (
            float(duals.get("fleet_dual") or 0.0)
            if node_id == "depot"
            else float(task_duals.get(node_id, 0.0))
        )
        node_rows.append(
            (
                *static_row,
                dual,
                abs(dual),
                float(active_support.get(node_id, 0.0)),
                float(primal_lambda.get(node_id, 0.0)),
                float(primal_support.get(node_id, 0.0)),
                float(fractional_support.get(node_id, 0.0)),
            )
        )
    target = max(
        1.0,
        float(snapshot.get("effective_harvest_target") or 1.0),
    )
    scale = max(1, int(data.scale))
    previous_best_rc = float(
        trajectory.get("previous_best_true_rc") or 0.0
    )
    penultimate_best_rc = float(
        trajectory.get("penultimate_best_true_rc") or 0.0
    )
    previous_harvest_count = float(
        trajectory.get("previous_harvest_column_count") or 0.0
    )
    penultimate_harvest_count = float(
        trajectory.get("penultimate_harvest_column_count") or 0.0
    )
    global_features = (
        log1p(float(scale)),
        float(snapshot.get("round") or 0) / 100.0,
        log1p(float(snapshot.get("active_column_count") or 0)),
        float(trajectory.get("previous_added_column_count") or 0.0)
        / target,
        previous_harvest_count / target,
        penultimate_harvest_count / target,
        (previous_harvest_count - penultimate_harvest_count)
        / target,
        log1p(
            float(
                trajectory.get(
                    "previous_harvest_processed_labels"
                )
                or 0.0
            )
        ),
        log1p(
            float(
                trajectory.get(
                    "penultimate_harvest_processed_labels"
                )
                or 0.0
            )
        ),
        previous_best_rc,
        log1p(abs(previous_best_rc) * 1.0e6),
        penultimate_best_rc,
        previous_best_rc - penultimate_best_rc,
        float(
            trajectory.get("dual_l1_delta_from_previous") or 0.0
        ),
        float(
            trajectory.get("dual_linf_delta_from_previous") or 0.0
        ),
        float(
            trajectory.get(
                "dual_l1_delta_from_penultimate"
            )
            or 0.0
        ),
        float(
            trajectory.get(
                "dual_linf_delta_from_penultimate"
            )
            or 0.0
        ),
        float(trajectory.get("node_lp_bound_delta") or 0.0),
        float(
            trajectory.get(
                "node_lp_bound_delta_from_penultimate"
            )
            or 0.0
        ),
        float(snapshot.get("node_lp_bound") or 0.0),
        float(
            trajectory.get("rmp_primal_nonzero_count") or 0.0
        )
        / scale,
        float(
            trajectory.get("rmp_primal_fractional_count") or 0.0
        )
        / scale,
        target / 64.0,
        observed_strikes / max(1.0, float(required_strikes)),
    )
    _require_finite(node_rows, name="node")
    _require_finite(static.arc_features, name="edge")
    _require_finite((global_features,), name="global")
    return ProofTailVetoFeatures(
        instance_content_hash=data.instance_content_hash,
        state_hash=str(snapshot.get("state_hash") or ""),
        scale=int(data.scale),
        node_features=tuple(node_rows),
        edge_index=(
            tuple(int(value) for value in static.arc_sources),
            tuple(int(value) for value in static.arc_targets),
        ),
        edge_features=static.arc_features,
        global_features=tuple(global_features),
    )


def proof_tail_veto_feature_dimensions() -> tuple[int, int, int]:
    return (
        len(NODE_STATIC_FEATURES) + len(NODE_DYNAMIC_FEATURES),
        len(EDGE_STATIC_FEATURES),
        len(GLOBAL_FEATURES),
    )


def _primal_support(
    snapshot: Mapping[str, object],
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    lambda_support: dict[str, float] = {}
    support: dict[str, float] = {}
    fractional: dict[str, float] = {}
    for raw in snapshot.get("rmp_primal") or ():
        row = dict(raw)
        value = float(row.get("lambda_value") or 0.0)
        is_fractional = 1.0e-9 < value < 1.0 - 1.0e-9
        for task_id in row.get("tasks") or ():
            key = str(task_id)
            lambda_support[key] = lambda_support.get(key, 0.0) + value
            support[key] = 1.0
            if is_fractional:
                fractional[key] = 1.0
    return lambda_support, support, fractional


def _active_support_frequency(
    data: LunarIceData,
    snapshot: Mapping[str, object],
    *,
    column_catalog: Mapping[str, object] | None,
) -> dict[str, float]:
    if column_catalog is None:
        return {}
    if str(column_catalog.get("instance_content_hash") or "") != (
        data.instance_content_hash
    ):
        raise ValueError("proof-tail column catalog instance hash mismatch")
    columns = dict(column_catalog.get("columns") or {})
    active_ids = tuple(snapshot.get("active_column_ids") or ())
    denominator = max(1.0, float(len(active_ids)))
    counts: dict[str, int] = {}
    for column_id in active_ids:
        payload = dict(columns.get(str(column_id)) or {})
        if not payload:
            raise ValueError("proof-tail active column is missing from catalog")
        tasks = {
            str(task_id)
            for sortie in payload.get("sorties") or ()
            for task_id in (sortie.get("tasks") or ())
        }
        for task_id in tasks:
            counts[task_id] = counts.get(task_id, 0) + 1
    return {
        task_id: count / denominator
        for task_id, count in counts.items()
    }


def _require_finite(
    rows,
    *,
    name: str,
) -> None:
    if any(
        not isfinite(float(value))
        for row in rows
        for value in row
    ):
        raise ValueError(f"proof-tail {name} features must be finite")
