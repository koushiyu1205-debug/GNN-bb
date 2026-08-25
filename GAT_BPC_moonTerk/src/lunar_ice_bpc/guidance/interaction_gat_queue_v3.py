"""V3 Interaction-GAT models and topology-control transforms.

The pre-action graph is intentionally identical to V2.  V3 changes only the
small-sample training architecture and makes both topology ablations
independently trainable models.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.interaction_gat_queue_v2 import (
    INTERACTION_CHECKPOINT_SCHEMA_V1,
    INTERACTION_CONTEXT_DIM,
    INTERACTION_CONTEXT_FEATURES,
    INTERACTION_EDGE_DIM,
    INTERACTION_EDGE_FEATURES,
    INTERACTION_FEATURE_SCHEMA_V2,
    INTERACTION_GRAPH_SCHEMA_V1,
    INTERACTION_INPUT_PARITY_CONTRACT_V1,
    INTERACTION_NODE_DIM,
    INTERACTION_NODE_FEATURES,
    InteractionGraphFeatures,
    InteractionLinearControl,
    _InteractionArmHeads,
    _InteractionNormalizer,
    build_interaction_graph,
    fit_interaction_envelope,
    fit_interaction_normalization,
    interaction_graph_builder_hash,
    interaction_is_ood,
    interaction_parameter_count,
    interaction_training_loss,
)
from lunar_ice_bpc.guidance.models import EdgeAttentionLayer


INTERACTION_CHECKPOINT_SCHEMA_V2 = (
    "lunar_ice_bpc.p0v5_interaction_gat_checkpoint.v2"
)
INTERACTION_DATASET_SCHEMA_V3 = (
    "lunar_ice_bpc.p0v5_interaction_gat_training_dataset.v3"
)
INTERACTION_CORPUS_SCHEMA_V3 = (
    "lunar_ice_bpc.p0v5_interaction_gat_corpus_freeze.v3"
)
INTERACTION_MANIFEST_SCHEMA_V2 = (
    "lunar_ice_bpc.p0v5_root_interaction_gat_runtime_manifest.v2"
)
INTERACTION_RUNTIME_POLICY_V3 = "P0V5_ROOT_INTERACTION_GAT_SELECTOR_V3"
INTERACTION_HIDDEN_DIM_V3 = 16
INTERACTION_HEADS_V3 = 2
INTERACTION_DROPOUT_V3 = 0.1
INTERACTION_PARAMETER_CAP_V3 = 20_000
V3_MODEL_KINDS = (
    "gat", "mlp", "linear", "no_message", "shuffled_topology",
)


class InteractionGATSelectorV3(nn.Module):
    model_kind = "gat"
    message_passing_required = True
    independently_trained_control = False

    def __init__(
        self,
        normalization,
        *,
        hidden_dim: int = INTERACTION_HIDDEN_DIM_V3,
        heads: int = INTERACTION_HEADS_V3,
        dropout: float = INTERACTION_DROPOUT_V3,
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
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(hidden_dim, hidden_dim, heads) for _ in range(2)
        )
        self.pool_gate = nn.Linear(hidden_dim, 1)
        self.arm_heads = _InteractionArmHeads(hidden_dim)

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
            for layer in self.attention_layers:
                node = F.relu(layer(node, topology, edge))
                node = F.dropout(node, p=self.dropout, training=self.training)
        weights = torch.softmax(self.pool_gate(node).squeeze(-1), dim=0)
        attention_pool = (weights[:, None] * node).sum(0)
        return self.arm_heads(
            node, edge, self.context_encoder(context), attention_pool
        )


class InteractionNoMessageControlV3(InteractionGATSelectorV3):
    model_kind = "no_message"
    message_passing_required = False
    independently_trained_control = True

    def forward(self, **kwargs):
        kwargs["disable_message_passing"] = True
        return super().forward(**kwargs)


class InteractionShuffledTopologyControlV3(InteractionGATSelectorV3):
    model_kind = "shuffled_topology"
    message_passing_required = False
    independently_trained_control = True


class InteractionMLPControlV3(nn.Module):
    model_kind = "mlp"
    independently_trained_control = True
    message_passing_required = False

    def __init__(self, normalization, *, hidden_dim=INTERACTION_HIDDEN_DIM_V3):
        super().__init__()
        dropout = INTERACTION_DROPOUT_V3
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
        self.arm_heads = _InteractionArmHeads(hidden_dim)

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


class InteractionLinearControlV3(InteractionLinearControl):
    model_kind = "linear"
    independently_trained_control = True


MODEL_CLASSES_V3 = {
    "gat": InteractionGATSelectorV3,
    "mlp": InteractionMLPControlV3,
    "linear": InteractionLinearControlV3,
    "no_message": InteractionNoMessageControlV3,
    "shuffled_topology": InteractionShuffledTopologyControlV3,
}


def shuffled_topology_features(
    features: InteractionGraphFeatures, *, state_hash: str
) -> InteractionGraphFeatures:
    """Return the frozen endpoint-shuffle control for one context.

    Node/edge/context values and edge count are unchanged.  Only target
    endpoints are cyclically shifted by a stable non-zero offset.
    """

    edge_count = len(features.edge_index[0])
    if edge_count <= 1:
        return features
    digest = hashlib.sha256(
        f"interaction-gat-v3-shuffle:{state_hash}".encode("utf-8")
    ).digest()
    shift = 1 + int.from_bytes(digest[:8], "big") % (edge_count - 1)
    sources, targets = features.edge_index
    rolled = targets[-shift:] + targets[:-shift]
    return replace(
        features,
        edge_index=(tuple(int(value) for value in sources), rolled),
    )


def features_for_model_kind(
    features: InteractionGraphFeatures, *, model_kind: str, state_hash: str
) -> InteractionGraphFeatures:
    if model_kind == "shuffled_topology":
        return shuffled_topology_features(features, state_hash=state_hash)
    return features


def build_model_v3(model_kind: str, normalization):
    try:
        model = MODEL_CLASSES_V3[str(model_kind)](normalization)
    except KeyError as exc:
        raise ValueError(f"unsupported V3 model kind:{model_kind}") from exc
    count = interaction_parameter_count(model)
    if count >= INTERACTION_PARAMETER_CAP_V3:
        raise ValueError(f"V3 model exceeds parameter cap:{model_kind}:{count}")
    return model


def interaction_v3_model_source_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


__all__ = [
    "INTERACTION_CHECKPOINT_SCHEMA_V1",
    "INTERACTION_CHECKPOINT_SCHEMA_V2",
    "INTERACTION_CONTEXT_FEATURES",
    "INTERACTION_CORPUS_SCHEMA_V3",
    "INTERACTION_DATASET_SCHEMA_V3",
    "INTERACTION_EDGE_FEATURES",
    "INTERACTION_FEATURE_SCHEMA_V2",
    "INTERACTION_GRAPH_SCHEMA_V1",
    "INTERACTION_INPUT_PARITY_CONTRACT_V1",
    "INTERACTION_MANIFEST_SCHEMA_V2",
    "INTERACTION_NODE_FEATURES",
    "INTERACTION_RUNTIME_POLICY_V3",
    "InteractionGATSelectorV3",
    "InteractionGraphFeatures",
    "MODEL_CLASSES_V3",
    "V3_MODEL_KINDS",
    "build_interaction_graph",
    "build_model_v3",
    "features_for_model_kind",
    "fit_interaction_envelope",
    "fit_interaction_normalization",
    "interaction_graph_builder_hash",
    "interaction_is_ood",
    "interaction_parameter_count",
    "interaction_training_loss",
    "shuffled_topology_features",
]
