"""Minimal Q0/QD1 Interaction-GAT selector used by the P0V5 V6 chain.

V6 intentionally has one learned arm.  Q0 is an external fallback, while
QB1 and QGR1 have neither output neurons nor runtime installation authority.
The graph and scalar feature definitions are reused byte-for-byte from V2.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Sequence

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
    INTERACTION_CONTEXT_DIM,
    INTERACTION_EDGE_DIM,
    INTERACTION_FEATURE_SCHEMA_V2,
    INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_INPUT_PARITY_CONTRACT_V1,
    INTERACTION_NODE_DIM,
    InteractionGraphFeatures,
    _InteractionNormalizer,
    build_interaction_graph,
    fit_interaction_envelope,
    fit_interaction_normalization,
    interaction_graph_builder_hash,
    interaction_is_ood,
    interaction_parameter_count,
)
from lunar_ice_bpc.guidance.interaction_gat_queue_v3 import (
    shuffled_topology_features,
)
from lunar_ice_bpc.guidance.models import EdgeAttentionLayer


V6_ARMS = ("QD1",)
V6_ACTION_UNIVERSE = ("Q0", "QD1")
V6_MODEL_KINDS = (
    "gat", "mlp", "linear", "no_message", "shuffled_topology",
)
INTERACTION_CHECKPOINT_SCHEMA_V6 = (
    "lunar_ice_bpc.p0v5_interaction_gat_qd1_checkpoint.v1"
)
INTERACTION_DATASET_SCHEMA_V6 = (
    "lunar_ice_bpc.p0v5_interaction_gat_qd1_training_dataset.v1"
)
INTERACTION_MANIFEST_SCHEMA_V6 = (
    "lunar_ice_bpc.p0v5_root_interaction_gat_qd1_runtime_manifest.v1"
)
INTERACTION_RUNTIME_POLICY_V6 = "P0V5_ROOT_INTERACTION_GAT_QD1_SELECTOR_V6"
INTERACTION_HIDDEN_DIM_V6 = 16
INTERACTION_HEADS_V6 = 2
INTERACTION_DROPOUT_V6 = 0.1
INTERACTION_PARAMETER_CAP_V6 = 20_000


class _V6QD1Head(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.head = nn.Linear(hidden_dim * 6, 3)

    def forward(self, node, edge, context, attention_pool):
        values = self.head(torch.cat((
            node.mean(0), node.max(0).values, attention_pool,
            edge.mean(0), edge.max(0).values, context,
        ), dim=-1)).reshape(1, 1, 3)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


class InteractionGATQD1SelectorV6(nn.Module):
    model_kind = "gat"
    message_passing_required = True
    independently_trained_control = False

    def __init__(
        self,
        normalization,
        *,
        hidden_dim: int = INTERACTION_HIDDEN_DIM_V6,
        heads: int = INTERACTION_HEADS_V6,
        dropout: float = INTERACTION_DROPOUT_V6,
    ) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.heads = int(heads)
        self.dropout = float(dropout)
        self.normalizer = _InteractionNormalizer(normalization)
        self.node_encoder = nn.Sequential(
            nn.Linear(INTERACTION_NODE_DIM, hidden_dim), nn.ReLU()
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(INTERACTION_EDGE_DIM, hidden_dim), nn.ReLU()
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(INTERACTION_CONTEXT_DIM, hidden_dim), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(hidden_dim, hidden_dim, heads) for _ in range(2)
        )
        self.layer_norms = nn.ModuleList(
            nn.LayerNorm(hidden_dim) for _ in range(2)
        )
        self.pool_gate = nn.Linear(hidden_dim, 1)
        self.qd1_head = _V6QD1Head(hidden_dim)

    def forward(
        self,
        *,
        node_features,
        edge_index,
        edge_features,
        context_features,
        message_edge_index=None,
        disable_message_passing: bool = False,
    ):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        node = self.node_encoder(node)
        edge = self.edge_encoder(edge)
        topology = edge_index if message_edge_index is None else message_edge_index
        if not disable_message_passing:
            for layer, normalization in zip(
                self.attention_layers, self.layer_norms, strict=True
            ):
                message = F.relu(layer(node, topology, edge))
                message = F.dropout(
                    message, p=self.dropout, training=self.training
                )
                node = normalization(node + message)
        weights = torch.softmax(self.pool_gate(node).squeeze(-1), dim=0)
        return self.qd1_head(
            node,
            edge,
            self.context_encoder(context),
            (weights[:, None] * node).sum(0),
        )


class InteractionNoMessageControlV6(InteractionGATQD1SelectorV6):
    model_kind = "no_message"
    message_passing_required = False
    independently_trained_control = True

    def forward(self, **kwargs):
        kwargs["disable_message_passing"] = True
        return super().forward(**kwargs)


class InteractionShuffledTopologyControlV6(InteractionGATQD1SelectorV6):
    model_kind = "shuffled_topology"
    message_passing_required = False
    independently_trained_control = True


class InteractionMLPControlV6(nn.Module):
    model_kind = "mlp"
    message_passing_required = False
    independently_trained_control = True

    def __init__(self, normalization, *, hidden_dim=INTERACTION_HIDDEN_DIM_V6):
        super().__init__()
        dropout = INTERACTION_DROPOUT_V6
        self.normalizer = _InteractionNormalizer(normalization)
        self.node_encoder = nn.Sequential(
            nn.Linear(INTERACTION_NODE_DIM, hidden_dim), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(INTERACTION_EDGE_DIM, hidden_dim), nn.ReLU(),
            nn.Dropout(dropout),
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(INTERACTION_CONTEXT_DIM, hidden_dim), nn.ReLU(),
            nn.Dropout(dropout), nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.pool_gate = nn.Linear(hidden_dim, 1)
        self.qd1_head = _V6QD1Head(hidden_dim)

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        node = self.node_encoder(node)
        edge = self.edge_encoder(edge)
        weights = torch.softmax(self.pool_gate(node).squeeze(-1), dim=0)
        return self.qd1_head(
            node, edge, self.context_encoder(context),
            (weights[:, None] * node).sum(0),
        )


class InteractionLinearControlV6(nn.Module):
    model_kind = "linear"
    message_passing_required = False
    independently_trained_control = True

    def __init__(self, normalization):
        super().__init__()
        self.normalizer = _InteractionNormalizer(normalization)
        self.head = nn.Linear(
            INTERACTION_NODE_DIM * 2 + INTERACTION_EDGE_DIM * 2
            + INTERACTION_CONTEXT_DIM,
            3,
        )

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        values = self.head(torch.cat((
            node.mean(0), node.max(0).values,
            edge.mean(0), edge.max(0).values, context,
        ), dim=-1)).reshape(1, 1, 3)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
        }


MODEL_CLASSES_V6 = {
    "gat": InteractionGATQD1SelectorV6,
    "mlp": InteractionMLPControlV6,
    "linear": InteractionLinearControlV6,
    "no_message": InteractionNoMessageControlV6,
    "shuffled_topology": InteractionShuffledTopologyControlV6,
}


def features_for_model_kind_v6(
    features: InteractionGraphFeatures, *, model_kind: str, state_hash: str
) -> InteractionGraphFeatures:
    if model_kind == "shuffled_topology":
        return shuffled_topology_features(features, state_hash=state_hash)
    return features


def build_model_v6(model_kind: str, normalization):
    try:
        model = MODEL_CLASSES_V6[str(model_kind)](normalization)
    except KeyError as exc:
        raise ValueError(f"unsupported V6 model kind:{model_kind}") from exc
    count = interaction_parameter_count(model)
    if count >= INTERACTION_PARAMETER_CAP_V6:
        raise ValueError(f"V6 model exceeds parameter cap:{model_kind}:{count}")
    return model


def interaction_training_loss_v6(
    output,
    *,
    benefit_target: torch.Tensor,
    positive_gain_target: torch.Tensor,
    adverse_target: torch.Tensor,
    determined_mask: torch.Tensor,
    positive_mask: torch.Tensor,
    rank_direction: torch.Tensor,
    rank_mask: torch.Tensor,
):
    benefit = output["benefit_probability"].reshape(-1)
    gain = output["conditional_positive_gain"].reshape(-1)
    adverse = output["adverse_probability"].reshape(-1)
    targets = tuple(value.reshape(-1).to(benefit.dtype) for value in (
        benefit_target, positive_gain_target, adverse_target,
        determined_mask, positive_mask, rank_direction, rank_mask,
    ))
    if any(value.numel() != 1 for value in targets):
        raise ValueError("V6 selector loss target dimension mismatch")
    (benefit_target, positive_gain_target, adverse_target,
     determined, positive, direction, rank_observed) = targets
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
        F.huber_loss(gain, positive_gain_target, reduction="none") * gain_mask
    ).sum() / gain_mask.sum().clamp_min(1.0)
    utility = benefit * gain - adverse
    pairwise_rank = (
        F.softplus(-(direction * utility)) * rank_observed
    ).sum() / rank_observed.sum().clamp_min(1.0)
    total = (
        benefit_bce + 0.5 * positive_gain_huber
        + adverse_bce + 0.25 * pairwise_rank
    )
    return {
        "loss": total,
        "benefit_bce": benefit_bce,
        "positive_gain_huber": positive_gain_huber,
        "adverse_bce": adverse_bce,
        "pairwise_rank": pairwise_rank,
    }


def interaction_v6_model_source_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


__all__ = [
    "INTERACTION_CHECKPOINT_SCHEMA_V6", "INTERACTION_DATASET_SCHEMA_V6",
    "INTERACTION_MANIFEST_SCHEMA_V6", "INTERACTION_RUNTIME_POLICY_V6",
    "InteractionGATQD1SelectorV6", "InteractionGraphFeatures",
    "MODEL_CLASSES_V6", "V6_ACTION_UNIVERSE", "V6_ARMS", "V6_MODEL_KINDS",
    "build_interaction_graph", "build_model_v6", "features_for_model_kind_v6",
    "fit_interaction_envelope", "fit_interaction_normalization",
    "interaction_graph_builder_hash", "interaction_is_ood",
    "interaction_parameter_count", "interaction_training_loss_v6",
    "interaction_v6_model_source_hash",
]
