"""Fail-closed inference helpers for the optional QG2 context-arm selector.

The selector is deliberately subordinate to QG2.  It may choose ``QD1`` or
``QB1`` only after the QG2 activation gate declines the label-state action;
if neither selector arm is eligible, the only fallback is literal ``Q0``.
This module predicts scores only.  It has no authority to start pricing,
filter labels, change dominance, alter bounds, or issue certificates.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch
from torch import nn

from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
    PRICING_LIFECYCLE_SCOPE_ROOT_CG,
)
from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
    QG2_CONTEXT_FEATURES,
    build_qg2_features,
)


QG2_CONTEXT_ARM_SELECTOR_CHECKPOINT_V1 = (
    "lunar_ice_bpc.p0v5_qg2_context_arm_selector_checkpoint.v1"
)
QG2_CONTEXT_ARM_SELECTOR_PREDICTION_V1 = (
    "lunar_ice_bpc.p0v5_qg2_context_arm_selector_prediction.v1"
)
QG2_CONTEXT_ARM_SELECTOR_ARMS = ("QD1", "QB1")
QG2_CONTEXT_ARM_SELECTOR_FALLBACK = "Q0"


class QG2ContextArmSelector(nn.Module):
    """The frozen two-head linear selector used by the feasibility study."""

    def __init__(self, dimension: int) -> None:
        super().__init__()
        self.head = nn.Linear(int(dimension), len(QG2_CONTEXT_ARM_SELECTOR_ARMS) * 2)

    def forward(self, features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        values = self.head(features).reshape(
            -1, len(QG2_CONTEXT_ARM_SELECTOR_ARMS), 2
        )
        return values[..., 0], torch.nn.functional.softplus(values[..., 1])


@dataclass(frozen=True)
class QG2ContextArmPrediction:
    benefit_probability: float
    conditional_positive_gain: float

    @property
    def expected_gain(self) -> float:
        return self.benefit_probability * self.conditional_positive_gain


def load_qg2_context_arm_selector(
    checkpoint_path: str | Path,
) -> tuple[QG2ContextArmSelector, dict[str, Any]]:
    """Load a development checkpoint and independently validate its contract."""

    path = Path(checkpoint_path).resolve()
    payload = torch.load(path, map_location="cpu", weights_only=False)
    if not isinstance(payload, Mapping):
        raise ValueError("QG2 context-arm checkpoint payload is invalid")
    payload = dict(payload)
    errors: list[str] = []
    if str(payload.get("schema_version") or "") != (
        QG2_CONTEXT_ARM_SELECTOR_CHECKPOINT_V1
    ):
        errors.append("checkpoint_schema_mismatch")
    if tuple(payload.get("arms") or ()) != QG2_CONTEXT_ARM_SELECTOR_ARMS:
        errors.append("checkpoint_arm_universe_mismatch")
    dimension = int(payload.get("feature_dimension") or 0)
    if dimension != len(QG2_CONTEXT_FEATURES):
        errors.append("checkpoint_feature_dimension_mismatch")
    if str(payload.get("fallback_action") or "") != (
        QG2_CONTEXT_ARM_SELECTOR_FALLBACK
    ):
        errors.append("checkpoint_literal_q0_fallback_missing")
    if bool(payload.get("deployment_authorized")):
        errors.append("development_checkpoint_claims_deployment")
    normalization = dict(payload.get("normalization") or {})
    means = list(normalization.get("mean") or ())
    stds = list(normalization.get("std") or ())
    if (
        len(means) != dimension
        or len(stds) != dimension
        or any(not isfinite(float(value)) for value in (*means, *stds))
        or any(float(value) <= 0.0 for value in stds)
        or str(normalization.get("fit_partition") or "")
        != "train_instances_only"
    ):
        errors.append("checkpoint_normalization_invalid")
    if not isinstance(payload.get("state_dict"), Mapping):
        errors.append("checkpoint_state_dict_missing")
    if errors:
        raise ValueError(
            "QG2 context-arm checkpoint validation failed:"
            + ",".join(sorted(set(errors)))
        )
    model = QG2ContextArmSelector(dimension)
    model.load_state_dict(payload["state_dict"], strict=True)
    model.eval()
    return model, payload


def predict_qg2_context_arms(
    model: QG2ContextArmSelector,
    checkpoint: Mapping[str, Any],
    context_features: Sequence[float],
) -> dict[str, QG2ContextArmPrediction]:
    """Predict both legal secondary arms from pre-action context features."""

    dimension = int(checkpoint.get("feature_dimension") or 0)
    values = tuple(float(value) for value in context_features)
    if len(values) != dimension or any(not isfinite(value) for value in values):
        raise ValueError("QG2 context-arm inference feature vector is invalid")
    normalization = dict(checkpoint.get("normalization") or {})
    normalized = [
        (value - float(mean)) / float(std)
        for value, mean, std in zip(
            values,
            normalization.get("mean") or (),
            normalization.get("std") or (),
            strict=True,
        )
    ]
    tensor = torch.tensor([normalized], dtype=torch.float32)
    with torch.inference_mode():
        logits, magnitudes = model(tensor)
        probabilities = torch.sigmoid(logits)
    outputs = (*probabilities.reshape(-1), *magnitudes.reshape(-1))
    if any(not bool(torch.isfinite(value).all()) for value in outputs):
        raise ValueError("QG2 context-arm selector emitted NaN/Inf")
    result: dict[str, QG2ContextArmPrediction] = {}
    for index, arm in enumerate(QG2_CONTEXT_ARM_SELECTOR_ARMS):
        result[arm] = QG2ContextArmPrediction(
            benefit_probability=float(probabilities[0, index]),
            conditional_positive_gain=float(magnitudes[0, index]),
        )
    return result


def qg2_features_from_snapshot(data: Any, snapshot: Mapping[str, Any]):
    """Recreate the complete pre-action QG2 feature object."""

    true_duals = dict(snapshot.get("true_duals") or {})
    trajectory = dict(snapshot.get("trajectory_features") or {})
    features = build_qg2_features(
        data,
        cover_duals=dict(
            true_duals.get("task_duals") or true_duals.get("cover") or {}
        ),
        fleet_dual=float(
            true_duals.get("fleet_dual")
            if true_duals.get("fleet_dual") is not None
            else true_duals.get("fleet_limit") or 0.0
        ),
        active_column_count=_optional_int(snapshot.get("active_column_count")),
        active_task_sets=_active_task_sets(snapshot.get("active_task_sets")),
        round_index=_optional_int(snapshot.get("round")),
        previous_proof_wall_sec=_optional_float(
            trajectory.get("previous_proof_pass_wall_time")
        ),
        previous_processed_labels=_optional_int(
            trajectory.get("previous_proof_processed_labels")
            if trajectory.get("previous_proof_processed_labels") is not None
            else trajectory.get("previous_harvest_processed_labels")
        ),
        dual_l1_delta_from_previous=_optional_float(
            trajectory.get("dual_l1_delta_from_previous")
        ),
        branch_decisions=tuple(
            branch_context_from_payload(
                snapshot.get("branch_context") or {}
            ).pair_decisions
        ),
        cut_duals=dict(
            true_duals.get("cut_duals") or true_duals.get("cuts") or {}
        ),
        v5_midpoint_wall_sec=_optional_float(
            snapshot.get("bidirectional_midpoint_prepass_wall_sec")
            if snapshot.get("bidirectional_midpoint_prepass_wall_sec")
            is not None
            else trajectory.get("v5_midpoint_wall_sec")
        ),
        root_lifecycle_scope=(
            str(
                snapshot.get("pricing_lifecycle_scope")
                or PRICING_LIFECYCLE_SCOPE_ROOT_CG
            )
            == PRICING_LIFECYCLE_SCOPE_ROOT_CG
        ),
    )
    return features


def qg2_context_features_from_snapshot(data: Any, snapshot: Mapping[str, Any]) -> tuple[float, ...]:
    """Recreate exactly the pre-action context vector used by selector fitting."""

    features = qg2_features_from_snapshot(data, snapshot)
    result = tuple(float(value) for value in features.context_features)
    if len(result) != len(QG2_CONTEXT_FEATURES) or any(
        not isfinite(value) for value in result
    ):
        raise ValueError("QG2 context-arm pre-action features are invalid")
    return result


def qg2_context_arm_is_ood(
    context_features: Sequence[float],
    feature_envelope: Mapping[str, Any],
) -> bool:
    """Apply the same train-only context envelope used by QG2 runtime vetoes."""

    minimum = tuple(float(value) for value in feature_envelope.get("context_min") or ())
    maximum = tuple(float(value) for value in feature_envelope.get("context_max") or ())
    relative_margin = float(feature_envelope.get("relative_margin") or 0.0)
    values = tuple(float(value) for value in context_features)
    if len(values) != len(minimum) or len(values) != len(maximum):
        return True
    for value, low, high in zip(values, minimum, maximum, strict=True):
        span = max(abs(low), abs(high), abs(high - low), 1.0)
        margin = max(0.0, relative_margin) * span
        if value < low - margin or value > high + margin:
            return True
    return False


def choose_qg2_secondary_arm(
    predictions: Mapping[str, QG2ContextArmPrediction],
    *,
    benefit_probability_threshold: float,
    expected_gain_threshold: float,
    qg2_declined: bool,
    ood: bool = False,
) -> str:
    """Choose QD1/QB1 only after QG2 declines; otherwise return literal Q0."""

    if not qg2_declined or ood:
        return QG2_CONTEXT_ARM_SELECTOR_FALLBACK
    eligible = [
        (prediction.expected_gain, arm)
        for arm, prediction in predictions.items()
        if arm in QG2_CONTEXT_ARM_SELECTOR_ARMS
        and prediction.benefit_probability
        >= float(benefit_probability_threshold)
        and prediction.expected_gain >= float(expected_gain_threshold)
    ]
    if not eligible:
        return QG2_CONTEXT_ARM_SELECTOR_FALLBACK
    return max(eligible, key=lambda row: (row[0], row[1]))[1]


def _optional_int(value: Any) -> int | None:
    return None if value is None else max(0, int(value))


def _optional_float(value: Any) -> float | None:
    return None if value is None else max(0.0, float(value))


def _active_task_sets(value: Any) -> tuple[tuple[str, ...], ...] | None:
    if value is None:
        return None
    return tuple(tuple(str(task_id) for task_id in row) for row in value)
