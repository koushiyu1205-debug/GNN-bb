"""Residual-GAT V4 selector models and censor-aware loss.

V4 deliberately has exactly two learned arms: QD1 and QGR1.  Q0 remains an
external fallback and QB1 has no output neuron, so a malformed manifest cannot
revive the arm that the V4 freeze permanently vetoes.
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


V4_ARMS = ("QGR1", "QD1")
V4_ACTION_UNIVERSE = ("Q0", *V4_ARMS)
INTERACTION_CHECKPOINT_SCHEMA_V3 = (
    "lunar_ice_bpc.p0v5_interaction_gat_checkpoint.v3"
)
INTERACTION_DATASET_SCHEMA_V4 = (
    "lunar_ice_bpc.p0v5_interaction_gat_training_dataset.v4"
)
INTERACTION_CORPUS_SCHEMA_V4 = (
    "lunar_ice_bpc.p0v5_interaction_gat_corpus_freeze.v4"
)
INTERACTION_MANIFEST_SCHEMA_V3 = (
    "lunar_ice_bpc.p0v5_root_interaction_gat_runtime_manifest.v3"
)
INTERACTION_RUNTIME_POLICY_V4 = "P0V5_ROOT_INTERACTION_GAT_SELECTOR_V4"
INTERACTION_HIDDEN_DIM_V4 = 16
INTERACTION_HEADS_V4 = 2
INTERACTION_DROPOUT_V4 = 0.1
INTERACTION_PARAMETER_CAP_V4 = 20_000
V4_MODEL_KINDS = (
    "gat", "mlp", "linear", "no_message", "shuffled_topology",
)


class _V4ArmHeads(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.head = nn.Linear(hidden_dim * 6, len(V4_ARMS) * 4)

    def forward(self, node, edge, context, attention_pool):
        values = self.head(torch.cat((
            node.mean(0), node.max(0).values, attention_pool,
            edge.mean(0), edge.max(0).values, context,
        ), dim=-1)).reshape(1, len(V4_ARMS), 4)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
            "resource_censor_probability": torch.sigmoid(values[..., 3]),
        }


class InteractionGATSelectorV4(nn.Module):
    model_kind = "gat"
    message_passing_required = True
    independently_trained_control = False

    def __init__(
        self,
        normalization,
        *,
        hidden_dim: int = INTERACTION_HIDDEN_DIM_V4,
        heads: int = INTERACTION_HEADS_V4,
        dropout: float = INTERACTION_DROPOUT_V4,
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
        self.layer_norms = nn.ModuleList(nn.LayerNorm(hidden_dim) for _ in range(2))
        self.pool_gate = nn.Linear(hidden_dim, 1)
        self.arm_heads = _V4ArmHeads(hidden_dim)

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
                message = F.dropout(message, p=self.dropout, training=self.training)
                node = normalization(node + message)
        weights = torch.softmax(self.pool_gate(node).squeeze(-1), dim=0)
        return self.arm_heads(
            node,
            edge,
            self.context_encoder(context),
            (weights[:, None] * node).sum(0),
        )


class InteractionNoMessageControlV4(InteractionGATSelectorV4):
    model_kind = "no_message"
    message_passing_required = False
    independently_trained_control = True

    def forward(self, **kwargs):
        kwargs["disable_message_passing"] = True
        return super().forward(**kwargs)


class InteractionShuffledTopologyControlV4(InteractionGATSelectorV4):
    model_kind = "shuffled_topology"
    message_passing_required = False
    independently_trained_control = True


class InteractionMLPControlV4(nn.Module):
    model_kind = "mlp"
    message_passing_required = False
    independently_trained_control = True

    def __init__(self, normalization, *, hidden_dim=INTERACTION_HIDDEN_DIM_V4):
        super().__init__()
        dropout = INTERACTION_DROPOUT_V4
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
        self.arm_heads = _V4ArmHeads(hidden_dim)

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        node = self.node_encoder(node)
        edge = self.edge_encoder(edge)
        weights = torch.softmax(self.pool_gate(node).squeeze(-1), dim=0)
        return self.arm_heads(
            node, edge, self.context_encoder(context),
            (weights[:, None] * node).sum(0),
        )


class InteractionLinearControlV4(nn.Module):
    model_kind = "linear"
    message_passing_required = False
    independently_trained_control = True

    def __init__(self, normalization):
        super().__init__()
        self.normalizer = _InteractionNormalizer(normalization)
        self.head = nn.Linear(
            INTERACTION_NODE_DIM * 2 + INTERACTION_EDGE_DIM * 2
            + INTERACTION_CONTEXT_DIM,
            len(V4_ARMS) * 4,
        )

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node, edge, context = self.normalizer(
            node_features, edge_features, context_features
        )
        values = self.head(torch.cat((
            node.mean(0), node.max(0).values,
            edge.mean(0), edge.max(0).values, context,
        ), dim=-1)).reshape(1, len(V4_ARMS), 4)
        return {
            "benefit_probability": torch.sigmoid(values[..., 0]),
            "conditional_positive_gain": F.softplus(values[..., 1]),
            "adverse_probability": torch.sigmoid(values[..., 2]),
            "resource_censor_probability": torch.sigmoid(values[..., 3]),
        }


MODEL_CLASSES_V4 = {
    "gat": InteractionGATSelectorV4,
    "mlp": InteractionMLPControlV4,
    "linear": InteractionLinearControlV4,
    "no_message": InteractionNoMessageControlV4,
    "shuffled_topology": InteractionShuffledTopologyControlV4,
}


def features_for_model_kind_v4(
    features: InteractionGraphFeatures, *, model_kind: str, state_hash: str
) -> InteractionGraphFeatures:
    if model_kind == "shuffled_topology":
        return shuffled_topology_features(features, state_hash=state_hash)
    return features


def build_model_v4(model_kind: str, normalization):
    try:
        model = MODEL_CLASSES_V4[str(model_kind)](normalization)
    except KeyError as exc:
        raise ValueError(f"unsupported V4 model kind:{model_kind}") from exc
    count = interaction_parameter_count(model)
    if count >= INTERACTION_PARAMETER_CAP_V4:
        raise ValueError(f"V4 model exceeds parameter cap:{model_kind}:{count}")
    return model


def interaction_training_loss_v4(
    output,
    *,
    benefit_target: torch.Tensor,
    positive_gain_target: torch.Tensor,
    adverse_target: torch.Tensor,
    resource_censor_target: torch.Tensor,
    determined_mask: torch.Tensor,
    positive_mask: torch.Tensor,
    resource_mask: torch.Tensor,
    pairwise_preferences: Sequence[tuple[int, int, float]] = (),
):
    benefit = output["benefit_probability"].reshape(-1)
    gain = output["conditional_positive_gain"].reshape(-1)
    adverse = output["adverse_probability"].reshape(-1)
    resource = output["resource_censor_probability"].reshape(-1)
    targets = tuple(value.reshape(-1).to(benefit.dtype) for value in (
        benefit_target, positive_gain_target, adverse_target,
        resource_censor_target, determined_mask, positive_mask, resource_mask,
    ))
    if any(value.numel() != len(V4_ARMS) for value in targets):
        raise ValueError("V4 selector loss target dimension mismatch")
    (benefit_target, positive_gain_target, adverse_target, resource_target,
     determined, positive, resource_observed) = targets
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
    resource_bce = (
        F.binary_cross_entropy(resource, resource_target, reduction="none")
        * resource_observed
    ).sum() / resource_observed.sum().clamp_min(1.0)
    utility = benefit * gain - adverse - resource
    pair_losses = []
    pair_weight = 0.0
    for preferred, other, weight in pairwise_preferences:
        if preferred < -1 or preferred >= len(V4_ARMS):
            raise ValueError("V4 preferred arm index is invalid")
        if other < -1 or other >= len(V4_ARMS) or other == preferred:
            raise ValueError("V4 other arm index is invalid")
        weight = max(0.0, float(weight))
        preferred_value = utility.new_zeros(()) if preferred == -1 else utility[preferred]
        other_value = utility.new_zeros(()) if other == -1 else utility[other]
        pair_losses.append(weight * F.softplus(-(preferred_value - other_value)))
        pair_weight += weight
    pairwise_rank = (
        torch.stack(pair_losses).sum() / max(1.0, pair_weight)
        if pair_losses else utility.new_zeros(())
    )
    total = (
        benefit_bce + 0.5 * positive_gain_huber + adverse_bce
        + 0.5 * resource_bce + 0.25 * pairwise_rank
    )
    return {
        "loss": total,
        "benefit_bce": benefit_bce,
        "positive_gain_huber": positive_gain_huber,
        "adverse_bce": adverse_bce,
        "resource_censor_bce": resource_bce,
        "pairwise_rank": pairwise_rank,
    }


def interaction_v4_model_source_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


__all__ = [
    "INTERACTION_CHECKPOINT_SCHEMA_V3", "INTERACTION_CORPUS_SCHEMA_V4",
    "INTERACTION_DATASET_SCHEMA_V4", "INTERACTION_MANIFEST_SCHEMA_V3",
    "INTERACTION_RUNTIME_POLICY_V4", "InteractionGATSelectorV4",
    "InteractionGraphFeatures", "MODEL_CLASSES_V4", "V4_ACTION_UNIVERSE",
    "V4_ARMS", "V4_MODEL_KINDS", "build_interaction_graph", "build_model_v4",
    "features_for_model_kind_v4", "fit_interaction_envelope",
    "fit_interaction_normalization", "interaction_graph_builder_hash",
    "interaction_is_ood", "interaction_parameter_count",
    "interaction_training_loss_v4", "interaction_v4_model_source_hash",
]
