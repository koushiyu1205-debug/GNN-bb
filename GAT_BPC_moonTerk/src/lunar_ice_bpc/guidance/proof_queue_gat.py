"""Graph-attention guidance for exact SPPRC proof-queue ordering.

The model scores the already legal task-transition arcs of one pricing
request.  Scores may change only the QG1 queue tie-break.  They are never used
as a bound, a dominance rule, a filter, or a certificate input.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log1p, sqrt
from typing import Mapping

import torch
from torch import nn
from torch.nn import functional as F

from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.guidance.models import EdgeAttentionLayer
from lunar_ice_bpc.guidance.tensorization import (
    EDGE_STATIC_FEATURES,
    NODE_STATIC_FEATURES,
    build_static_graph_features,
)


PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_proof_queue_gat_features.v1"
)
PROOF_QUEUE_GAT_CHECKPOINT_SCHEMA_V1 = (
    "lunar_ice_bpc.p0v5_proof_queue_gat_checkpoint.v1"
)
PROOF_QUEUE_GAT_MODEL_ID = "proof_queue_arc_gat2x32x2_v1"

PROOF_QUEUE_GAT_NODE_DYNAMIC_FEATURES = (
    "cover_dual",
    "cover_dual_z_within_request",
    "cover_dual_over_maxabs_within_request",
    "cover_dual_rank_within_request",
    "cover_dual_positive",
)
PROOF_QUEUE_GAT_CONTEXT_FEATURES = (
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


@dataclass(frozen=True)
class ProofQueueGatFeatures:
    instance_content_hash: str
    arc_candidate_ids: tuple[str, ...]
    node_features: tuple[tuple[float, ...], ...]
    edge_index: tuple[tuple[int, ...], tuple[int, ...]]
    edge_features: tuple[tuple[float, ...], ...]
    context_features: tuple[float, ...]
    schema_version: str = PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1

    @property
    def node_feature_names(self) -> tuple[str, ...]:
        return (*NODE_STATIC_FEATURES, *PROOF_QUEUE_GAT_NODE_DYNAMIC_FEATURES)

    @property
    def edge_feature_names(self) -> tuple[str, ...]:
        return EDGE_STATIC_FEATURES

    @property
    def context_feature_names(self) -> tuple[str, ...]:
        return PROOF_QUEUE_GAT_CONTEXT_FEATURES

    def to_tensors(self) -> dict[str, torch.Tensor]:
        return {
            "node_features": torch.tensor(
                self.node_features, dtype=torch.float32
            ),
            "edge_index": torch.tensor(
                self.edge_index, dtype=torch.long
            ),
            "edge_features": torch.tensor(
                self.edge_features, dtype=torch.float32
            ),
            "context_features": torch.tensor(
                self.context_features, dtype=torch.float32
            ),
        }


def build_proof_queue_gat_features(
    data: LunarIceData,
    *,
    cover_duals: Mapping[str, float],
    fleet_dual: float = 0.0,
    active_column_count: int = 0,
    round_index: int = 0,
    previous_proof_wall_sec: float = 0.0,
    previous_harvest_processed_labels: int = 0,
    dual_l1_delta_from_previous: float = 0.0,
    dual_linf_delta_from_previous: float = 0.0,
) -> ProofQueueGatFeatures:
    """Build finite, pre-call-only graph features for one true-dual request."""

    duals = {str(key): float(value) for key, value in cover_duals.items()}
    if set(duals) != set(data.task_ids):
        raise ValueError("proof-queue GAT task-dual universe mismatch")
    values = [duals[task_id] for task_id in data.task_ids]
    if any(not isfinite(value) for value in values):
        raise ValueError("proof-queue GAT task dual is non-finite")
    mean = sum(values) / max(1, len(values))
    variance = sum((value - mean) ** 2 for value in values) / max(
        1, len(values)
    )
    std = max(1.0e-12, sqrt(variance))
    max_abs = max(1.0e-12, *(abs(value) for value in values))
    ranked = sorted((value, task_id) for task_id, value in duals.items())
    rank = {
        task_id: index / max(1, len(ranked) - 1)
        for index, (_value, task_id) in enumerate(ranked)
    }

    static = build_static_graph_features(data)
    dynamic_rows: list[tuple[float, ...]] = [(0.0,) * 5]
    for task_id in data.task_ids:
        value = duals[task_id]
        dynamic_rows.append(
            (
                value,
                (value - mean) / std,
                value / max_abs,
                rank[task_id],
                1.0 if value > 0.0 else 0.0,
            )
        )
    node_rows = tuple(
        (*static_row, *dynamic_row)
        for static_row, dynamic_row in zip(
            static.node_features, dynamic_rows, strict=True
        )
    )
    context = (
        log1p(float(data.scale)),
        float(fleet_dual),
        mean,
        std,
        min(values, default=0.0),
        max(values, default=0.0),
        log1p(max(0, int(active_column_count))),
        log1p(max(0, int(round_index))),
        log1p(max(0.0, float(previous_proof_wall_sec))),
        log1p(max(0, int(previous_harvest_processed_labels))),
        float(dual_l1_delta_from_previous),
        float(dual_linf_delta_from_previous),
    )
    flat = (*context, *(value for row in node_rows for value in row))
    if any(not isfinite(float(value)) for value in flat):
        raise ValueError("proof-queue GAT features are non-finite")
    return ProofQueueGatFeatures(
        instance_content_hash=data.instance_content_hash,
        arc_candidate_ids=static.arc_candidate_ids,
        node_features=node_rows,
        edge_index=(static.arc_sources, static.arc_targets),
        edge_features=static.arc_features,
        context_features=context,
    )


def proof_queue_gat_features_from_snapshot(
    data: LunarIceData,
    snapshot: Mapping[str, object],
) -> ProofQueueGatFeatures:
    """Accept both historical root-state and current pricing snapshots."""

    true_duals = dict(snapshot.get("true_duals") or {})
    cover = dict(
        true_duals.get("task_duals")
        or true_duals.get("cover")
        or {}
    )
    trajectory = dict(snapshot.get("trajectory_features") or {})
    return build_proof_queue_gat_features(
        data,
        cover_duals=cover,
        fleet_dual=float(
            true_duals.get("fleet_dual")
            if true_duals.get("fleet_dual") is not None
            else true_duals.get("fleet_limit") or 0.0
        ),
        active_column_count=int(snapshot.get("active_column_count") or 0),
        round_index=int(snapshot.get("round") or 0),
        previous_proof_wall_sec=float(
            trajectory.get("previous_proof_pass_wall_time") or 0.0
        ),
        previous_harvest_processed_labels=int(
            trajectory.get("previous_harvest_processed_labels") or 0
        ),
        dual_l1_delta_from_previous=float(
            trajectory.get("dual_l1_delta_from_previous") or 0.0
        ),
        dual_linf_delta_from_previous=float(
            trajectory.get("dual_linf_delta_from_previous") or 0.0
        ),
    )


class ProofQueuePotentialGAT(nn.Module):
    """Two-layer edge-aware GAT with arc-potential and safety-gate heads."""

    def __init__(self, *, hidden_dim: int = 32, heads: int = 2) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.heads = int(heads)
        self.node_input_dim = len(NODE_STATIC_FEATURES) + len(
            PROOF_QUEUE_GAT_NODE_DYNAMIC_FEATURES
        )
        self.edge_input_dim = len(EDGE_STATIC_FEATURES)
        self.context_input_dim = len(PROOF_QUEUE_GAT_CONTEXT_FEATURES)
        self.node_encoder = nn.Sequential(
            nn.Linear(self.node_input_dim, self.hidden_dim), nn.ReLU()
        )
        self.edge_encoder = nn.Sequential(
            nn.Linear(self.edge_input_dim, self.hidden_dim), nn.ReLU()
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(self.context_input_dim, self.hidden_dim), nn.ReLU()
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(self.hidden_dim, self.hidden_dim, self.heads)
            for _ in range(2)
        )
        self.arc_head = nn.Sequential(
            nn.Linear(self.hidden_dim * 4, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, 1),
        )
        self.benefit_head = nn.Sequential(
            nn.Linear(self.hidden_dim * 2, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, 1),
        )
        self.positive_gain_head = nn.Sequential(
            nn.Linear(self.hidden_dim * 2, self.hidden_dim),
            nn.ReLU(),
            nn.Linear(self.hidden_dim, 1),
        )

    def forward(
        self,
        *,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        context_features: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        node_embedding = self.node_encoder(node_features)
        edge_embedding = self.edge_encoder(edge_features)
        for layer in self.attention_layers:
            node_embedding = layer(
                node_embedding, edge_index, edge_embedding
            )
        context_embedding = self.context_encoder(context_features)
        context_rows = context_embedding.expand(edge_index.shape[1], -1)
        arc_inputs = torch.cat(
            (
                node_embedding[edge_index[0]],
                node_embedding[edge_index[1]],
                edge_embedding,
                context_rows,
            ),
            dim=-1,
        )
        global_input = torch.cat(
            (node_embedding.mean(dim=0), context_embedding), dim=-1
        )
        return {
            "arc_scores": self.arc_head(arc_inputs).squeeze(-1),
            "benefit_probability": torch.sigmoid(
                self.benefit_head(global_input).squeeze(-1)
            ),
            "conditional_positive_gain": F.softplus(
                self.positive_gain_head(global_input).squeeze(-1)
            ),
        }


def normalized_arc_potentials(scores: torch.Tensor) -> torch.Tensor:
    """Map arbitrary finite scores to the centered QG1 interval [-1, 1]."""

    if scores.ndim != 1 or scores.numel() == 0:
        raise ValueError("proof-queue GAT arc score vector must be nonempty")
    if not bool(torch.isfinite(scores).all()):
        raise ValueError("proof-queue GAT emitted NaN/Inf")
    centered = scores - scores.mean()
    maximum = centered.abs().max()
    if float(maximum.detach().item()) <= 1.0e-12:
        return torch.zeros_like(centered)
    return centered / maximum


def proof_queue_arc_ranking_loss(
    predicted_scores: torch.Tensor,
    target_potentials: torch.Tensor,
) -> torch.Tensor:
    """Dense regression plus a balanced top-vs-bottom ranking objective."""

    predicted = normalized_arc_potentials(predicted_scores)
    target = normalized_arc_potentials(target_potentials)
    mse = F.mse_loss(predicted, target)
    width = max(1, min(64, int(target.numel()) // 10))
    order = torch.argsort(target)
    low = order[:width]
    high = order[-width:]
    pairwise = F.softplus(
        -(predicted[high][:, None] - predicted[low][None, :])
    ).mean()
    cosine = 1.0 - F.cosine_similarity(
        predicted.reshape(1, -1), target.reshape(1, -1)
    ).mean()
    return mse + 0.25 * pairwise + 0.25 * cosine


def checkpoint_payload(
    model: ProofQueuePotentialGAT,
    *,
    metadata: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": PROOF_QUEUE_GAT_CHECKPOINT_SCHEMA_V1,
        "model_id": PROOF_QUEUE_GAT_MODEL_ID,
        "feature_schema_version": PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1,
        "hidden_dim": model.hidden_dim,
        "heads": model.heads,
        "metadata": dict(metadata),
        "state_dict": model.state_dict(),
    }


def load_checkpoint(path: str, *, map_location: str = "cpu"):
    payload = torch.load(path, map_location=map_location, weights_only=False)
    if str(payload.get("schema_version") or "") != (
        PROOF_QUEUE_GAT_CHECKPOINT_SCHEMA_V1
    ):
        raise ValueError("proof-queue GAT checkpoint schema mismatch")
    if str(payload.get("model_id") or "") != PROOF_QUEUE_GAT_MODEL_ID:
        raise ValueError("proof-queue GAT model id mismatch")
    if str(payload.get("feature_schema_version") or "") != (
        PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1
    ):
        raise ValueError("proof-queue GAT feature schema mismatch")
    model = ProofQueuePotentialGAT(
        hidden_dim=int(payload.get("hidden_dim") or 32),
        heads=int(payload.get("heads") or 2),
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, dict(payload.get("metadata") or {})
