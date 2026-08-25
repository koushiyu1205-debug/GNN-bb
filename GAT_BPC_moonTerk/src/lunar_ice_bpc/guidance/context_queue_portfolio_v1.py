"""Models and pre-action features for Context Queue Portfolio V1.

The selector chooses at most one exact-safe queue ordering.  Q0 remains an
external fallback.  This module deliberately has a new schema so historical
QG2 checkpoints cannot be loaded as portfolio candidates by accident.
"""

from __future__ import annotations

from dataclasses import replace
from math import isfinite, log1p, sqrt
from typing import Iterable, Mapping, Sequence

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.models import EdgeAttentionLayer
from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
    QG2_CONTEXT_FEATURES,
    QG2_NODE_DYNAMIC_FEATURES,
    QG2Features,
    build_qg2_features,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
    normalize_qg2_v3_features,
)
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
)


PORTFOLIO_ARMS = ("QGR1", "QD1", "QB1")
PORTFOLIO_FALLBACK = "Q0"
PORTFOLIO_ACTION_UNIVERSE = (PORTFOLIO_FALLBACK, *PORTFOLIO_ARMS)
PORTFOLIO_FEATURE_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_context_queue_portfolio_features.v1"
)
PORTFOLIO_NORMALIZATION_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_context_queue_portfolio_normalization.v1"
)
PORTFOLIO_ENVELOPE_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_context_queue_portfolio_envelope.v1"
)
PORTFOLIO_CHECKPOINT_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_context_queue_portfolio_checkpoint.v1"
)
PORTFOLIO_INPUT_PARITY_CONTRACT_V1 = (
    "node_edge_context_identical_gat_topology_only_difference.v1"
)
PORTFOLIO_EXTRA_CONTEXT_FEATURES = (
    "log1p_previous_dominance_candidate_checks",
    "previous_dominance_candidate_checks_present",
    "log1p_previous_dominance_wall_sec",
    "previous_dominance_wall_sec_present",
    "log1p_previous_max_visited_bucket_size",
    "previous_max_visited_bucket_size_present",
)
PORTFOLIO_CONTEXT_FEATURES = (
    *QG2_CONTEXT_FEATURES,
    *PORTFOLIO_EXTRA_CONTEXT_FEATURES,
)
PORTFOLIO_NODE_FEATURES = (*NODE_STATIC_FEATURES, *QG2_NODE_DYNAMIC_FEATURES)
PORTFOLIO_EDGE_FEATURES = tuple(
    "risk_over_objective_reference" if name == "risk" else name
    for name in EDGE_STATIC_FEATURES
)
PORTFOLIO_NODE_DIM = len(NODE_STATIC_FEATURES) + len(QG2_NODE_DYNAMIC_FEATURES)
PORTFOLIO_EDGE_DIM = len(EDGE_STATIC_FEATURES)


def build_portfolio_features(request) -> QG2Features:
    """Build action-reachable features before any queue policy is selected."""

    previous_is_literal_q0 = (
        str(request.proof_tail_previous_queue_policy_id) == "Q0"
    )
    base = normalize_qg2_v3_features(request.data, build_qg2_features(
        request.data,
        cover_duals=request.true_duals.cover,
        fleet_dual=float(request.true_duals.fleet_limit),
        active_column_count=request.proof_tail_active_column_count,
        active_task_sets=request.proof_tail_active_task_sets,
        round_index=request.proof_tail_round_index,
        previous_proof_wall_sec=(
            request.proof_tail_previous_proof_wall_sec
            if previous_is_literal_q0 else None
        ),
        previous_processed_labels=(
            request.proof_tail_previous_processed_labels
            if previous_is_literal_q0 else None
        ),
        dual_l1_delta_from_previous=request.proof_tail_dual_delta_l1,
        branch_decisions=tuple(request.branch_context.pair_decisions),
        cut_duals=dict(request.true_duals.cuts or {}),
        v5_midpoint_wall_sec=request.proof_tail_v5_midpoint_wall_sec,
        root_lifecycle_scope=(request.pricing_lifecycle_scope == "root_cg"),
    ))
    extras = (
        *_optional_log(
            request.proof_tail_previous_dominance_candidate_checks
            if previous_is_literal_q0 else None
        ),
        *_optional_log(
            request.proof_tail_previous_dominance_wall_sec
            if previous_is_literal_q0 else None
        ),
        *_optional_log(
            request.proof_tail_previous_max_visited_bucket_size
            if previous_is_literal_q0 else None
        ),
    )
    return replace(
        base,
        context_features=(*base.context_features, *extras),
        schema_version=PORTFOLIO_FEATURE_SCHEMA_V1,
    )


def _optional_log(value: int | float | None) -> tuple[float, float]:
    if value is None:
        return 0.0, 0.0
    numeric = float(value)
    if not isfinite(numeric) or numeric < 0.0:
        raise ValueError("portfolio trajectory value is invalid")
    return log1p(numeric), 1.0


def fit_portfolio_normalization(
    rows: Sequence[QG2Features],
) -> dict[str, object]:
    if not rows or any(
        row.schema_version != PORTFOLIO_FEATURE_SCHEMA_V1 for row in rows
    ):
        raise ValueError("portfolio normalization requires V1 training rows")
    payload = {
        "schema_version": PORTFOLIO_NORMALIZATION_SCHEMA_V1,
        "fit_partition": "train_instances_only",
        "node": _statistics(
            (value for row in rows for value in row.node_features),
            PORTFOLIO_NODE_DIM,
        ),
        "edge": _statistics(
            (value for row in rows for value in row.edge_features),
            PORTFOLIO_EDGE_DIM,
        ),
        "context": _statistics(
            (row.context_features for row in rows),
            len(PORTFOLIO_CONTEXT_FEATURES),
        ),
    }
    validate_portfolio_normalization(payload)
    return payload


def _statistics(
    rows: Iterable[Sequence[float]], dimension: int
) -> dict[str, list[float]]:
    materialized = [tuple(float(value) for value in row) for row in rows]
    if not materialized or any(len(row) != dimension for row in materialized):
        raise ValueError("portfolio normalization dimension mismatch")
    if any(not isfinite(value) for row in materialized for value in row):
        raise ValueError("portfolio normalization contains NaN/Inf")
    means = [
        sum(row[index] for row in materialized) / len(materialized)
        for index in range(dimension)
    ]
    stds = []
    for index, mean in enumerate(means):
        variance = sum(
            (row[index] - mean) ** 2 for row in materialized
        ) / len(materialized)
        stds.append(max(1.0e-6, sqrt(variance)))
    return {"mean": means, "std": stds}


def validate_portfolio_normalization(payload: Mapping[str, object]) -> None:
    if payload.get("schema_version") != PORTFOLIO_NORMALIZATION_SCHEMA_V1:
        raise ValueError("portfolio normalization schema mismatch")
    if payload.get("fit_partition") != "train_instances_only":
        raise ValueError("portfolio normalization is not train-only")
    for group, dimension in (
        ("node", PORTFOLIO_NODE_DIM),
        ("edge", PORTFOLIO_EDGE_DIM),
        ("context", len(PORTFOLIO_CONTEXT_FEATURES)),
    ):
        values = dict(payload.get(group) or {})
        means = tuple(float(value) for value in values.get("mean") or ())
        stds = tuple(float(value) for value in values.get("std") or ())
        if (
            len(means) != dimension
            or len(stds) != dimension
            or any(not isfinite(value) for value in (*means, *stds))
            or any(value <= 0.0 for value in stds)
        ):
            raise ValueError(f"portfolio {group} normalization invalid")


def fit_portfolio_feature_envelope(
    rows: Sequence[QG2Features], *, relative_margin: float = 0.05
) -> dict[str, object]:
    if not rows or any(
        row.schema_version != PORTFOLIO_FEATURE_SCHEMA_V1 for row in rows
    ):
        raise ValueError("portfolio envelope requires V1 training rows")
    margin = float(relative_margin)
    if not isfinite(margin) or margin != 0.05:
        raise ValueError("portfolio V1 envelope margin is frozen at 5 percent")
    groups = {
        "node": [value for row in rows for value in row.node_features],
        "edge": [value for row in rows for value in row.edge_features],
        "context": [row.context_features for row in rows],
    }
    payload: dict[str, object] = {
        "schema_version": PORTFOLIO_ENVELOPE_SCHEMA_V1,
        "fit_partition": "train_instances_only",
        "relative_margin": margin,
    }
    for name, values in groups.items():
        dimension = len(values[0])
        payload[f"{name}_min"] = [
            min(float(row[index]) for row in values)
            for index in range(dimension)
        ]
        payload[f"{name}_max"] = [
            max(float(row[index]) for row in values)
            for index in range(dimension)
        ]
    return payload


def portfolio_is_ood(
    features: QG2Features, envelope: Mapping[str, object]
) -> tuple[bool, str]:
    if features.schema_version != PORTFOLIO_FEATURE_SCHEMA_V1:
        return True, "portfolio_feature_schema_mismatch"
    if envelope.get("schema_version") != PORTFOLIO_ENVELOPE_SCHEMA_V1:
        return True, "portfolio_envelope_schema_mismatch"
    if envelope.get("fit_partition") != "train_instances_only":
        return True, "portfolio_envelope_partition_mismatch"
    margin = float(envelope.get("relative_margin") or 0.0)
    if margin != 0.05:
        return True, "portfolio_envelope_margin_mismatch"
    groups = {
        "node": features.node_features,
        "edge": features.edge_features,
        "context": (features.context_features,),
    }
    for name, rows in groups.items():
        lower = tuple(float(v) for v in envelope.get(f"{name}_min") or ())
        upper = tuple(float(v) for v in envelope.get(f"{name}_max") or ())
        if not rows or len(lower) != len(rows[0]) or len(upper) != len(rows[0]):
            return True, f"portfolio_{name}_envelope_dimension_mismatch"
        for row in rows:
            for value, low, high in zip(row, lower, upper, strict=True):
                width = max(1.0e-9, high - low)
                if (
                    not all(isfinite(float(v)) for v in (value, low, high))
                    or low > high
                    or value < low - margin * width
                    or value > high + margin * width
                ):
                    return True, f"portfolio_{name}_feature_outside_envelope"
    return False, ""


class _PortfolioNormalizer(nn.Module):
    def __init__(self, normalization: Mapping[str, object]) -> None:
        super().__init__()
        validate_portfolio_normalization(normalization)
        for group in ("node", "edge", "context"):
            values = dict(normalization[group])
            self.register_buffer(
                f"{group}_mean",
                torch.tensor(values["mean"], dtype=torch.float32),
            )
            self.register_buffer(
                f"{group}_std",
                torch.tensor(values["std"], dtype=torch.float32),
            )

    def forward(self, node, edge, context):
        return (
            (node - self.node_mean) / self.node_std,
            (edge - self.edge_mean) / self.edge_std,
            (context - self.context_mean) / self.context_std,
        )


class _ArmHeads(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.head = nn.Linear(hidden_dim * 5, len(PORTFOLIO_ARMS) * 3)

    def forward(self, node, edge, context, *, use_max_pool: bool):
        node_mean = node.mean(dim=0)
        node_max = node.max(dim=0).values if use_max_pool else node_mean
        edge_mean = edge.mean(dim=0)
        edge_max = edge.max(dim=0).values if use_max_pool else edge_mean
        values = self.head(torch.cat(
            (node_mean, node_max, edge_mean, edge_max, context), dim=-1
        )).reshape(1, len(PORTFOLIO_ARMS), 3)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


class PortfolioGATSelector(nn.Module):
    model_kind = "gat"

    def __init__(
        self,
        normalization: Mapping[str, object],
        *,
        hidden_dim: int = 32,
        heads: int = 2,
    ) -> None:
        super().__init__()
        self.normalizer = _PortfolioNormalizer(normalization)
        self.node_encoder = nn.Sequential(
            nn.Linear(PORTFOLIO_NODE_DIM, hidden_dim), nn.ReLU()
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(PORTFOLIO_EDGE_DIM, hidden_dim), nn.ReLU()
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(len(PORTFOLIO_CONTEXT_FEATURES), hidden_dim), nn.ReLU()
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(hidden_dim, hidden_dim, heads) for _ in range(2)
        )
        self.arm_heads = _ArmHeads(hidden_dim)

    def forward(
        self, *, node_features, edge_index, edge_features, context_features,
        message_edge_index=None, disable_message_passing: bool = False,
    ):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        node_embedding = self.node_encoder(node)
        edge_embedding = self.edge_encoder(edge)
        message_index = edge_index if message_edge_index is None else message_edge_index
        if not disable_message_passing:
            for layer in self.attention_layers:
                node_embedding = layer(node_embedding, message_index, edge_embedding)
        return self.arm_heads(
            node_embedding,
            edge_embedding,
            self.context_encoder(context),
            use_max_pool=True,
        )


class PortfolioMLPSelector(PortfolioGATSelector):
    model_kind = "mlp"

    def __init__(self, normalization: Mapping[str, object], *, hidden_dim: int = 32):
        super().__init__(normalization, hidden_dim=hidden_dim, heads=1)
        self.node_mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU()
        )
        self.attention_layers = nn.ModuleList()

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        return self.arm_heads(
            self.node_mlp(self.node_encoder(node)),
            self.edge_encoder(edge),
            self.context_encoder(context),
            use_max_pool=True,
        )


class PortfolioLinearSelector(nn.Module):
    model_kind = "linear"

    def __init__(self, normalization: Mapping[str, object]) -> None:
        super().__init__()
        self.normalizer = _PortfolioNormalizer(normalization)
        self.head = nn.Linear(
            PORTFOLIO_NODE_DIM * 2
            + PORTFOLIO_EDGE_DIM * 2
            + len(PORTFOLIO_CONTEXT_FEATURES),
            len(PORTFOLIO_ARMS) * 3,
        )

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        values = self.head(torch.cat((
            node.mean(dim=0), node.max(dim=0).values,
            edge.mean(dim=0), edge.max(dim=0).values,
            context,
        ), dim=-1)).reshape(1, len(PORTFOLIO_ARMS), 3)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


def portfolio_parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


def portfolio_training_loss(
    output: Mapping[str, torch.Tensor],
    *,
    benefit_target: torch.Tensor,
    positive_gain_target: torch.Tensor,
    adverse_target: torch.Tensor,
    determined_mask: torch.Tensor,
    positive_mask: torch.Tensor,
    pairwise_preferences: Sequence[tuple[int, int, float]] = (),
) -> dict[str, torch.Tensor]:
    """Apply the frozen four-term selector loss to one context.

    Arm indices 0..2 denote QGR1/QD1/QB1; index -1 in a pair denotes Q0,
    whose predicted gain is fixed at zero.  Repeats must already have been
    collapsed to one median target before this function is called.
    """

    benefit = output["benefit_probability"].reshape(-1)
    gain = output["conditional_positive_gain"].reshape(-1)
    adverse = output["adverse_probability"].reshape(-1)
    targets = tuple(t.reshape(-1).to(dtype=benefit.dtype) for t in (
        benefit_target,
        positive_gain_target,
        adverse_target,
        determined_mask,
        positive_mask,
    ))
    benefit_target, positive_gain_target, adverse_target, determined, positive = targets
    if any(value.numel() != len(PORTFOLIO_ARMS) for value in targets):
        raise ValueError("portfolio loss target dimension mismatch")
    denominator = determined.sum().clamp_min(1.0)
    benefit_bce = (
        F.binary_cross_entropy(benefit, benefit_target, reduction="none")
        * determined
    ).sum() / denominator
    adverse_bce = (
        F.binary_cross_entropy(adverse, adverse_target, reduction="none")
        * determined
    ).sum() / denominator
    gain_mask = determined * positive
    positive_gain_huber = (
        F.huber_loss(gain, positive_gain_target, reduction="none")
        * gain_mask
    ).sum() / gain_mask.sum().clamp_min(1.0)
    utility = benefit * gain - adverse
    pair_losses = []
    for preferred, other, weight in pairwise_preferences:
        if preferred < -1 or preferred >= len(PORTFOLIO_ARMS):
            raise ValueError("portfolio preferred arm index is invalid")
        if other < -1 or other >= len(PORTFOLIO_ARMS) or other == preferred:
            raise ValueError("portfolio other arm index is invalid")
        preferred_value = utility.new_zeros(()) if preferred == -1 else utility[preferred]
        other_value = utility.new_zeros(()) if other == -1 else utility[other]
        pair_losses.append(
            max(0.0, float(weight)) * F.softplus(-(preferred_value - other_value))
        )
    pairwise_rank = (
        torch.stack(pair_losses).sum()
        / max(1.0, sum(max(0.0, float(row[2])) for row in pairwise_preferences))
        if pair_losses else utility.new_zeros(())
    )
    total = benefit_bce + 0.5 * positive_gain_huber + adverse_bce + 0.25 * pairwise_rank
    return {
        "loss": total,
        "benefit_bce": benefit_bce,
        "positive_gain_huber": positive_gain_huber,
        "adverse_bce": adverse_bce,
        "pairwise_rank": pairwise_rank,
    }
