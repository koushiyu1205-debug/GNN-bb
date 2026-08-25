"""Risk-aware context selector over Q0/QG2/QD1/QB1 for QG2 V3.

The selector is intentionally separate from the admission ranker.  It may run
exactly one non-Q0 queue ordering arm, and literal Q0 is the mandatory action
when every arm is rejected, the context is OOD, or any input is invalid.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
    QG2_CONTEXT_FEATURES,
    QG2_NODE_DYNAMIC_FEATURES,
)
from lunar_ice_bpc.guidance.models import EdgeAttentionLayer
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
    _TrainOnlyNormalizer,
)
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
)


QG2_V3_SELECTOR_ARMS = ("QG2", "QD1", "QB1")
QG2_V3_SELECTOR_FALLBACK = "Q0"
QG2_V3_SELECTOR_CHECKPOINT_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_unified_arm_selector.v3"
)
QG2_V4_SELECTOR_CHECKPOINT_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_v4_arm_selector_checkpoint.v3"
)
QG2_V4_SELECTOR_RANK_LOSS_WEIGHT = 0.25


class QG2V3UnifiedArmSelector(nn.Module):
    """Small linear three-head selector suitable for the bounded dataset."""

    def __init__(self, dimension: int = len(QG2_CONTEXT_FEATURES)) -> None:
        super().__init__()
        self.dimension = int(dimension)
        self.head = nn.Linear(
            self.dimension, len(QG2_V3_SELECTOR_ARMS) * 3
        )

    def forward(self, features: torch.Tensor):
        values = self.head(features).reshape(
            -1, len(QG2_V3_SELECTOR_ARMS), 3
        )
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


class _GraphArmHeads(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.head = nn.Linear(
            hidden_dim * 5, len(QG2_V3_SELECTOR_ARMS) * 3
        )

    def forward(
        self,
        node_embedding: torch.Tensor,
        edge_embedding: torch.Tensor,
        context_embedding: torch.Tensor,
        *,
        use_max_pool: bool,
    ) -> dict[str, torch.Tensor]:
        mean_pool = node_embedding.mean(dim=0)
        max_pool = (
            node_embedding.max(dim=0).values if use_max_pool else mean_pool
        )
        edge_mean = edge_embedding.mean(dim=0)
        edge_max = (
            edge_embedding.max(dim=0).values if use_max_pool else edge_mean
        )
        values = self.head(torch.cat(
            (mean_pool, max_pool, edge_mean, edge_max, context_embedding),
            dim=-1,
        )).reshape(1, len(QG2_V3_SELECTOR_ARMS), 3)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


class QG2V3GraphArmSelector(nn.Module):
    """Primary graph selector; this is trained before MLP/Linear controls."""

    model_kind = "gat"

    def __init__(
        self,
        normalization: Mapping[str, object],
        *,
        hidden_dim: int = 32,
        heads: int = 2,
    ) -> None:
        super().__init__()
        self.normalizer = _TrainOnlyNormalizer(normalization)
        self.node_encoder = nn.Sequential(
            nn.Linear(
                len(NODE_STATIC_FEATURES) + len(QG2_NODE_DYNAMIC_FEATURES),
                hidden_dim,
            ),
            nn.ReLU(),
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(len(EDGE_STATIC_FEATURES), hidden_dim), nn.ReLU()
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(len(QG2_CONTEXT_FEATURES), hidden_dim), nn.ReLU()
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(hidden_dim, hidden_dim, heads) for _ in range(2)
        )
        self.arm_heads = _GraphArmHeads(hidden_dim)

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        node_embedding = self.node_encoder(node)
        edge_embedding = self.edge_encoder(edge)
        for layer in self.attention_layers:
            node_embedding = layer(node_embedding, edge_index, edge_embedding)
        return self.arm_heads(
            node_embedding,
            edge_embedding,
            self.context_encoder(context),
            use_max_pool=True,
        )


class QG2V3MLPArmSelector(QG2V3GraphArmSelector):
    model_kind = "mlp"

    def __init__(
        self,
        normalization: Mapping[str, object],
        *,
        hidden_dim: int = 32,
        heads: int = 1,
    ) -> None:
        super().__init__(normalization, hidden_dim=hidden_dim, heads=heads)
        self.node_mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU()
        )
        self.attention_layers = nn.ModuleList()

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        node_embedding = self.node_mlp(self.node_encoder(node))
        return self.arm_heads(
            node_embedding,
            self.edge_encoder(edge),
            self.context_encoder(context),
            use_max_pool=True,
        )


class QG2V3LinearGraphArmSelector(nn.Module):
    """Generalized-linear full-interface control without message passing.

    The control sees the same node, edge, and context tensors as the GAT.  It
    receives deterministic mean/max graph summaries so a comparison does not
    accidentally reward the GAT merely for seeing extrema that were hidden
    from the linear baseline.
    """

    model_kind = "linear"

    def __init__(self, normalization: Mapping[str, object]) -> None:
        super().__init__()
        self.normalizer = _TrainOnlyNormalizer(normalization)
        node_dim = len(NODE_STATIC_FEATURES) + len(QG2_NODE_DYNAMIC_FEATURES)
        edge_dim = len(EDGE_STATIC_FEATURES)
        self.head = nn.Linear(
            node_dim * 2 + edge_dim * 2 + len(QG2_CONTEXT_FEATURES),
            len(QG2_V3_SELECTOR_ARMS) * 3,
        )

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        node_mean = node.mean(dim=0)
        node_max = node.max(dim=0).values
        edge_mean = edge.mean(dim=0)
        edge_max = edge.max(dim=0).values
        values = self.head(torch.cat(
            (node_mean, node_max, edge_mean, edge_max, context), dim=-1
        )).reshape(1, len(QG2_V3_SELECTOR_ARMS), 3)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


@dataclass(frozen=True)
class QG2V3ArmPrediction:
    benefit_probability: float
    conditional_positive_gain: float
    adverse_probability: float

    @property
    def expected_gain(self) -> float:
        return self.benefit_probability * self.conditional_positive_gain

    def risk_adjusted_score(self, risk_penalty: float) -> float:
        return self.expected_gain - float(risk_penalty) * self.adverse_probability


@dataclass(frozen=True)
class QG2V3ArmThreshold:
    minimum_benefit_probability: float
    minimum_expected_gain: float
    maximum_adverse_probability: float


def qg2_v3_selector_loss(
    *,
    predictions: Mapping[str, torch.Tensor],
    benefit_target: torch.Tensor,
    positive_gain_target: torch.Tensor,
    adverse_target: torch.Tensor,
    outcome_mask: torch.Tensor,
    positive_mask: torch.Tensor,
    adverse_mask: torch.Tensor,
    utility_target: torch.Tensor | None = None,
    utility_mask: torch.Tensor | None = None,
    benefit_positive_weight: torch.Tensor | None = None,
    adverse_positive_weight: torch.Tensor | None = None,
) -> dict[str, torch.Tensor]:
    probability = predictions["benefit_probability"]
    gain = predictions["conditional_positive_gain"]
    adverse = predictions["adverse_probability"]
    expected_shape = probability.shape
    if any(
        value.shape != expected_shape
        for value in (
            gain, adverse, benefit_target, positive_gain_target,
            adverse_target, outcome_mask, positive_mask, adverse_mask,
        )
    ):
        raise ValueError("QG2 V3 selector loss shape mismatch")
    if (utility_target is None) != (utility_mask is None):
        raise ValueError("QG2 V4 selector utility target/mask mismatch")
    if utility_target is not None and (
        utility_target.shape != expected_shape
        or utility_mask.shape != expected_shape
    ):
        raise ValueError("QG2 V4 selector utility tensor shape mismatch")
    zero = probability.new_zeros(())
    benefit_weight = (
        torch.ones_like(benefit_target)
        if benefit_positive_weight is None else torch.where(
            benefit_target > 0.5,
            benefit_positive_weight.expand_as(benefit_target),
            torch.ones_like(benefit_target),
        )
    )
    adverse_weight = (
        torch.ones_like(adverse_target)
        if adverse_positive_weight is None else torch.where(
            adverse_target > 0.5,
            adverse_positive_weight.expand_as(adverse_target),
            torch.ones_like(adverse_target),
        )
    )
    benefit_loss = (
        F.binary_cross_entropy(
            probability[outcome_mask], benefit_target[outcome_mask],
            weight=benefit_weight[outcome_mask],
        )
        if bool(outcome_mask.any()) else zero
    )
    gain_loss = (
        F.smooth_l1_loss(
            gain[positive_mask], positive_gain_target[positive_mask]
        )
        if bool(positive_mask.any()) else zero
    )
    adverse_loss = (
        F.binary_cross_entropy(
            adverse[adverse_mask], adverse_target[adverse_mask],
            weight=adverse_weight[adverse_mask],
        )
        if bool(adverse_mask.any()) else zero
    )
    rank_loss = (
        _arm_utility_rank_loss(
            probability * gain - adverse,
            utility_target,
            utility_mask,
        )
        if utility_target is not None else zero
    )
    total = (
        benefit_loss + 0.5 * gain_loss + adverse_loss
        + QG2_V4_SELECTOR_RANK_LOSS_WEIGHT * rank_loss
    )
    return {
        "total_loss": total,
        "rank_loss": rank_loss,
        "benefit_loss": benefit_loss,
        "positive_gain_loss": gain_loss,
        "adverse_loss": adverse_loss,
    }


def _arm_utility_rank_loss(
    predicted_utility: torch.Tensor,
    observed_utility: torch.Tensor,
    observed_mask: torch.Tensor,
) -> torch.Tensor:
    """Rank uncensored matched arms against Q0 and one another."""

    losses = []
    flat_prediction = predicted_utility.reshape(-1)
    flat_observed = observed_utility.reshape(-1)
    flat_mask = observed_mask.reshape(-1)
    eligible = [
        index for index in range(flat_prediction.numel())
        if bool(flat_mask[index])
    ]
    for index in eligible:
        target = flat_observed[index]
        if abs(float(target)) > 1.0e-9:
            sign = 1.0 if float(target) > 0.0 else -1.0
            losses.append(F.softplus(-sign * flat_prediction[index]))
    for offset, left in enumerate(eligible):
        for right in eligible[offset + 1:]:
            difference = flat_observed[left] - flat_observed[right]
            if abs(float(difference)) <= 1.0e-9:
                continue
            sign = 1.0 if float(difference) > 0.0 else -1.0
            losses.append(F.softplus(
                -sign * (flat_prediction[left] - flat_prediction[right])
            ))
    return (
        torch.stack(losses).mean()
        if losses else predicted_utility.new_zeros(())
    )


def predict_qg2_v3_arms(
    model: QG2V3UnifiedArmSelector,
    context_features: Sequence[float],
    normalization: Mapping[str, Sequence[float]],
) -> dict[str, QG2V3ArmPrediction]:
    values = tuple(float(value) for value in context_features)
    means = tuple(float(value) for value in normalization.get("mean") or ())
    stds = tuple(float(value) for value in normalization.get("std") or ())
    if (
        len(values) != len(QG2_CONTEXT_FEATURES)
        or len(means) != len(values)
        or len(stds) != len(values)
        or any(not isfinite(value) for value in (*values, *means, *stds))
        or any(value <= 0.0 for value in stds)
    ):
        raise ValueError("QG2 V3 selector feature/normalization mismatch")
    normalized = torch.tensor(
        [[(value - mean) / std for value, mean, std in zip(
            values, means, stds, strict=True
        )]],
        dtype=torch.float32,
    )
    with torch.inference_mode():
        output = model(normalized)
    if any(not bool(value.isfinite().all()) for value in output.values()):
        raise ValueError("QG2 V3 selector emitted NaN/Inf")
    return {
        arm: QG2V3ArmPrediction(
            benefit_probability=float(output["benefit_probability"][0, index]),
            conditional_positive_gain=float(
                output["conditional_positive_gain"][0, index]
            ),
            adverse_probability=float(output["adverse_probability"][0, index]),
        )
        for index, arm in enumerate(QG2_V3_SELECTOR_ARMS)
    }


def choose_qg2_v3_arm(
    predictions: Mapping[str, QG2V3ArmPrediction],
    thresholds: Mapping[str, QG2V3ArmThreshold],
    *,
    risk_penalty: float,
    ood: bool = False,
) -> str:
    if ood or not isfinite(float(risk_penalty)) or risk_penalty < 0.0:
        return QG2_V3_SELECTOR_FALLBACK
    if set(predictions) != set(QG2_V3_SELECTOR_ARMS):
        return QG2_V3_SELECTOR_FALLBACK
    eligible = []
    for arm in QG2_V3_SELECTOR_ARMS:
        prediction = predictions[arm]
        threshold = thresholds.get(arm)
        values = (
            prediction.benefit_probability,
            prediction.conditional_positive_gain,
            prediction.adverse_probability,
        )
        if threshold is None or any(not isfinite(value) for value in values):
            continue
        if (
            prediction.benefit_probability
            < threshold.minimum_benefit_probability
            or prediction.expected_gain < threshold.minimum_expected_gain
            or prediction.adverse_probability
            > threshold.maximum_adverse_probability
        ):
            continue
        eligible.append((
            prediction.risk_adjusted_score(risk_penalty), arm
        ))
    if not eligible:
        return QG2_V3_SELECTOR_FALLBACK
    score, arm = max(eligible, key=lambda row: (row[0], row[1]))
    return arm if score > 0.0 else QG2_V3_SELECTOR_FALLBACK
