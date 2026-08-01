"""GAT policy for running or skipping the V5 midpoint prepass.

Skipping calls the unchanged P0V4 exact backend.  Running preserves V5.  The
policy therefore chooses between two exact-safe execution paths and has no
authority over reduced costs, bounds, pruning, or certificates.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import log1p
from typing import Mapping

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.guidance.models import EdgeAttentionLayer
from lunar_ice_bpc.guidance.proof_queue_gat import (
    ProofQueueGatFeatures,
    build_proof_queue_gat_features,
)
from lunar_ice_bpc.guidance.tensorization import EDGE_STATIC_FEATURES


BIDIRECTIONAL_GATE_GAT_CHECKPOINT_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_bidirectional_gate_gat_checkpoint.v1"
)
BIDIRECTIONAL_GATE_GAT_MODEL_ID = "bidirectional_prepass_gat2x32x2_v1"
BIDIRECTIONAL_GATE_GAT_POLICY_ID = (
    "v5_midpoint_run_or_exact_p0v4_fallback_v1"
)
BIDIRECTIONAL_GATE_DYNAMIC_CONTEXT_FEATURES = (
    "previous_midpoint_outcome_observed",
    "previous_midpoint_failed",
    "previous_midpoint_accepted",
    "log1p_consecutive_observed_failures",
)


@dataclass(frozen=True)
class BidirectionalGateFeatures:
    graph: ProofQueueGatFeatures
    context_features: tuple[float, ...]

    @property
    def node_features(self):
        return self.graph.node_features

    @property
    def edge_features(self):
        return self.graph.edge_features

    def to_tensors(self) -> dict[str, torch.Tensor]:
        tensors = self.graph.to_tensors()
        tensors["context_features"] = torch.tensor(
            self.context_features, dtype=torch.float32
        )
        return tensors


def build_bidirectional_gate_features(
    data,
    *,
    cover_duals: Mapping[str, float],
    fleet_dual: float = 0.0,
    round_index: int = 0,
    previous_midpoint_outcome: str = "NONE",
    consecutive_observed_failures: int = 0,
) -> BidirectionalGateFeatures:
    graph = build_proof_queue_gat_features(
        data,
        cover_duals=cover_duals,
        fleet_dual=fleet_dual,
        round_index=round_index,
    )
    previous = str(previous_midpoint_outcome).upper()
    if previous not in {"NONE", "FAILED", "ACCEPTED"}:
        raise ValueError("invalid previous midpoint outcome")
    context = (
        *graph.context_features,
        0.0 if previous == "NONE" else 1.0,
        1.0 if previous == "FAILED" else 0.0,
        1.0 if previous == "ACCEPTED" else 0.0,
        log1p(max(0, int(consecutive_observed_failures))),
    )
    return BidirectionalGateFeatures(graph=graph, context_features=context)


class BidirectionalPrepassGAT(nn.Module):
    """Graph classifier with failure-probability and wasted-time heads."""

    def __init__(self, *, node_input_dim: int, context_input_dim: int) -> None:
        super().__init__()
        self.node_input_dim = int(node_input_dim)
        self.context_input_dim = int(context_input_dim)
        hidden = 32
        self.node_encoder = nn.Sequential(
            nn.Linear(self.node_input_dim, hidden), nn.ReLU()
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(len(EDGE_STATIC_FEATURES), hidden), nn.ReLU()
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(self.context_input_dim, hidden), nn.ReLU()
        )
        self.layers = nn.ModuleList(
            EdgeAttentionLayer(hidden, hidden, 2) for _ in range(2)
        )
        self.failure_head = nn.Sequential(
            nn.Linear(hidden * 2, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1),
        )
        self.waste_head = nn.Sequential(
            nn.Linear(hidden * 2, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(
        self,
        *,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        context_features: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        nodes = self.node_encoder(node_features)
        edges = self.edge_encoder(edge_features)
        for layer in self.layers:
            nodes = layer(nodes, edge_index, edges)
        context = self.context_encoder(context_features)
        pooled = torch.cat((nodes.mean(dim=0), context), dim=-1)
        return {
            "failure_probability": torch.sigmoid(
                self.failure_head(pooled).squeeze(-1)
            ),
            "conditional_wasted_time_sec": F.softplus(
                self.waste_head(pooled).squeeze(-1)
            ),
        }


def model_for_features(features: ProofQueueGatFeatures):
    return BidirectionalPrepassGAT(
        node_input_dim=len(features.node_features[0]),
        context_input_dim=len(features.context_features),
    )


def checkpoint_payload(
    model: BidirectionalPrepassGAT,
    *,
    metadata: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": BIDIRECTIONAL_GATE_GAT_CHECKPOINT_SCHEMA_V1,
        "model_id": BIDIRECTIONAL_GATE_GAT_MODEL_ID,
        "node_input_dim": model.node_input_dim,
        "context_input_dim": model.context_input_dim,
        "metadata": dict(metadata),
        "state_dict": model.state_dict(),
    }


def load_checkpoint(path: str, *, map_location: str = "cpu"):
    payload = torch.load(path, map_location=map_location, weights_only=False)
    if str(payload.get("schema_version") or "") != (
        BIDIRECTIONAL_GATE_GAT_CHECKPOINT_SCHEMA_V1
    ):
        raise ValueError("bidirectional gate checkpoint schema mismatch")
    if str(payload.get("model_id") or "") != BIDIRECTIONAL_GATE_GAT_MODEL_ID:
        raise ValueError("bidirectional gate model id mismatch")
    model = BidirectionalPrepassGAT(
        node_input_dim=int(payload["node_input_dim"]),
        context_input_dim=int(payload["context_input_dim"]),
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, dict(payload.get("metadata") or {})
