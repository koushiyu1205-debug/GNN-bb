"""Q0-anchored label-state guidance for the P0V5 proof tail.

The networks run once per pricing request.  Their outputs are immutable node,
arc, and label-state coefficients consumed by Native QG2 solely as an
in-bucket queue ordering key.  Nothing in this module filters labels, changes
dominance, supplies a bound, or has certificate authority.
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


QG2_FEATURE_SCHEMA_V1 = "lunar_ice_bpc.p0v5_qg2_features.v1"
QG2_CHECKPOINT_SCHEMA_V1 = "lunar_ice_bpc.p0v5_qg2_checkpoint.v1"
QG2_LABEL_STATE_SCHEMA_V1 = "lunar_spprc.qg2_label_state.v1"
QG2_LABEL_STATE_FEATURE_COUNT = 15
QG2_MODEL_IDS = {
    "linear": "proof_queue_label_state_linear_v1",
    "mlp": "proof_queue_label_state_mlp2x32_v1",
    "gat": "proof_queue_label_state_gat2x32x2_v1",
}

QG2_NODE_DYNAMIC_FEATURES = (
    "cover_dual",
    "cover_dual_z_within_request",
    "cover_dual_over_maxabs_within_request",
    "cover_dual_rank_within_request",
    "cover_dual_positive",
)

# Optional trajectory values are accompanied by presence masks.  Missing live
# values are never silently represented as genuine zeros.
QG2_CONTEXT_FEATURES = (
    "log1p_scale",
    "fleet_dual",
    "cover_dual_mean",
    "cover_dual_std",
    "cover_dual_min",
    "cover_dual_max",
    "log1p_active_column_count",
    "active_column_count_present",
    "log1p_active_task_set_count",
    "active_task_sets_present",
    "active_task_coverage_fraction",
    "active_task_set_mean_cardinality_fraction",
    "log1p_round",
    "round_present",
    "log1p_previous_proof_wall",
    "previous_proof_wall_present",
    "log1p_previous_processed_labels",
    "previous_processed_labels_present",
    "dual_l1_delta_from_previous",
    "dual_l1_delta_present",
    "branch_decision_count",
    "same_journey_branch_fraction",
    "active_cut_count",
    "active_cut_dual_abs_sum",
    "log1p_v5_midpoint_wall",
    "v5_midpoint_wall_present",
    "root_lifecycle_scope",
)


@dataclass(frozen=True)
class QG2Features:
    instance_content_hash: str
    task_ids: tuple[str, ...]
    arc_candidate_ids: tuple[str, ...]
    node_features: tuple[tuple[float, ...], ...]
    edge_index: tuple[tuple[int, ...], tuple[int, ...]]
    edge_features: tuple[tuple[float, ...], ...]
    context_features: tuple[float, ...]
    schema_version: str = QG2_FEATURE_SCHEMA_V1

    def to_tensors(self) -> dict[str, torch.Tensor]:
        return {
            "node_features": torch.tensor(
                self.node_features, dtype=torch.float32
            ),
            "edge_index": torch.tensor(self.edge_index, dtype=torch.long),
            "edge_features": torch.tensor(
                self.edge_features, dtype=torch.float32
            ),
            "context_features": torch.tensor(
                self.context_features, dtype=torch.float32
            ),
        }


def _optional_log(value: int | float | None) -> tuple[float, float]:
    if value is None:
        return 0.0, 0.0
    numeric = float(value)
    if not isfinite(numeric) or numeric < 0.0:
        raise ValueError("QG2 optional trajectory value is invalid")
    return log1p(numeric), 1.0


def _optional_raw(value: float | None) -> tuple[float, float]:
    if value is None:
        return 0.0, 0.0
    numeric = float(value)
    if not isfinite(numeric) or numeric < 0.0:
        raise ValueError("QG2 optional trajectory value is invalid")
    return numeric, 1.0


def build_qg2_features(
    data: LunarIceData,
    *,
    cover_duals: Mapping[str, float],
    fleet_dual: float,
    active_column_count: int | None,
    active_task_sets: tuple[tuple[str, ...], ...] | None,
    round_index: int | None,
    previous_proof_wall_sec: float | None,
    previous_processed_labels: int | None,
    dual_l1_delta_from_previous: float | None,
    branch_decisions: tuple[object, ...],
    cut_duals: Mapping[str, float],
    v5_midpoint_wall_sec: float | None,
    root_lifecycle_scope: bool,
) -> QG2Features:
    duals = {str(key): float(value) for key, value in cover_duals.items()}
    if set(duals) != set(data.task_ids):
        raise ValueError("QG2 task-dual universe mismatch")
    values = [duals[task_id] for task_id in data.task_ids]
    if any(not isfinite(value) for value in values):
        raise ValueError("QG2 task dual is non-finite")
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
    active_value, active_present = _optional_log(active_column_count)
    if active_task_sets is None:
        active_set_count = 0.0
        active_sets_present = 0.0
        active_task_coverage = 0.0
        active_mean_cardinality = 0.0
    else:
        legal_tasks = set(data.task_ids)
        normalized_active_sets = tuple(
            frozenset(str(task_id) for task_id in task_set)
            for task_set in active_task_sets
        )
        if any(
            not task_set or not task_set.issubset(legal_tasks)
            for task_set in normalized_active_sets
        ):
            raise ValueError("QG2 active task-set incidence is invalid")
        active_set_count = log1p(float(len(normalized_active_sets)))
        active_sets_present = 1.0
        active_task_coverage = len(
            set().union(*normalized_active_sets)
            if normalized_active_sets else set()
        ) / max(1, len(data.task_ids))
        active_mean_cardinality = (
            sum(len(task_set) for task_set in normalized_active_sets)
            / max(1, len(normalized_active_sets))
            / max(1, len(data.task_ids))
        )
    round_value, round_present = _optional_log(round_index)
    previous_wall, previous_wall_present = _optional_log(
        previous_proof_wall_sec
    )
    previous_labels, previous_labels_present = _optional_log(
        previous_processed_labels
    )
    dual_delta, dual_delta_present = _optional_raw(
        dual_l1_delta_from_previous
    )
    branch_count = len(branch_decisions)
    same_count = sum(
        str(getattr(decision, "sense", "")) == "same_journey"
        for decision in branch_decisions
    )
    cut_values = tuple(float(value) for value in cut_duals.values())
    if any(not isfinite(value) for value in cut_values):
        raise ValueError("QG2 cut dual is non-finite")
    midpoint_wall, midpoint_wall_present = _optional_log(
        v5_midpoint_wall_sec
    )
    context = (
        log1p(float(data.scale)),
        float(fleet_dual),
        mean,
        std,
        min(values, default=0.0),
        max(values, default=0.0),
        active_value,
        active_present,
        active_set_count,
        active_sets_present,
        active_task_coverage,
        active_mean_cardinality,
        round_value,
        round_present,
        previous_wall,
        previous_wall_present,
        previous_labels,
        previous_labels_present,
        dual_delta,
        dual_delta_present,
        float(branch_count),
        float(same_count) / max(1, branch_count),
        float(len(cut_values)),
        sum(abs(value) for value in cut_values),
        midpoint_wall,
        midpoint_wall_present,
        1.0 if root_lifecycle_scope else 0.0,
    )
    flat = (*context, *(value for row in node_rows for value in row))
    if any(not isfinite(float(value)) for value in flat):
        raise ValueError("QG2 features are non-finite")
    return QG2Features(
        instance_content_hash=data.instance_content_hash,
        task_ids=tuple(data.task_ids),
        arc_candidate_ids=static.arc_candidate_ids,
        node_features=node_rows,
        edge_index=(static.arc_sources, static.arc_targets),
        edge_features=static.arc_features,
        context_features=context,
    )


class _QG2Heads(nn.Module):
    def __init__(self, hidden_dim: int) -> None:
        super().__init__()
        self.node_head = nn.Linear(hidden_dim, 1)
        self.arc_head = nn.Sequential(
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )
        self.state_head = nn.Linear(hidden_dim * 2, QG2_LABEL_STATE_FEATURE_COUNT)
        self.benefit_head = nn.Linear(hidden_dim * 2, 1)
        self.positive_gain_head = nn.Linear(hidden_dim * 2, 1)

    def emit(
        self,
        node_embedding: torch.Tensor,
        edge_embedding: torch.Tensor,
        edge_index: torch.Tensor,
        context_embedding: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
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
            "node_scores": self.node_head(node_embedding).squeeze(-1),
            "arc_scores": self.arc_head(arc_inputs).squeeze(-1),
            "label_state_coefficients": torch.tanh(
                self.state_head(global_input)
            ),
            "benefit_probability": torch.sigmoid(
                self.benefit_head(global_input).squeeze(-1)
            ),
            "conditional_positive_gain": F.softplus(
                self.positive_gain_head(global_input).squeeze(-1)
            ),
        }


class _QG2LinearHeads(_QG2Heads):
    """Generalized-linear heads for the non-neural ranking baseline."""

    def __init__(self, hidden_dim: int) -> None:
        super().__init__(hidden_dim)
        self.arc_head = nn.Linear(hidden_dim * 4, 1)


class QG2TinyGAT(nn.Module):
    model_kind = "gat"

    def __init__(self, *, hidden_dim: int = 32, heads: int = 2) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.heads = int(heads)
        node_dim = len(NODE_STATIC_FEATURES) + len(QG2_NODE_DYNAMIC_FEATURES)
        self.node_encoder = nn.Sequential(nn.Linear(node_dim, hidden_dim), nn.ReLU())
        self.edge_encoder = nn.Sequential(
            nn.Linear(len(EDGE_STATIC_FEATURES), hidden_dim), nn.ReLU()
        )
        self.context_encoder = nn.Sequential(
            nn.Linear(len(QG2_CONTEXT_FEATURES), hidden_dim), nn.ReLU()
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(hidden_dim, hidden_dim, heads)
            for _ in range(2)
        )
        self.heads_module = _QG2Heads(hidden_dim)

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node_embedding = self.node_encoder(node_features)
        edge_embedding = self.edge_encoder(edge_features)
        for layer in self.attention_layers:
            node_embedding = layer(node_embedding, edge_index, edge_embedding)
        context_embedding = self.context_encoder(context_features)
        return self.heads_module.emit(
            node_embedding, edge_embedding, edge_index, context_embedding
        )


class QG2MLP(QG2TinyGAT):
    model_kind = "mlp"

    def __init__(self, *, hidden_dim: int = 32, heads: int = 1) -> None:
        super().__init__(hidden_dim=hidden_dim, heads=heads)
        self.attention_layers = nn.ModuleList(
            nn.Sequential(nn.Linear(hidden_dim, hidden_dim), nn.ReLU())
            for _ in range(1)
        )

    def forward(self, *, node_features, edge_index, edge_features, context_features):
        node_embedding = self.node_encoder(node_features)
        for layer in self.attention_layers:
            node_embedding = layer(node_embedding)
        edge_embedding = self.edge_encoder(edge_features)
        context_embedding = self.context_encoder(context_features)
        return self.heads_module.emit(
            node_embedding, edge_embedding, edge_index, context_embedding
        )


class QG2Linear(QG2TinyGAT):
    model_kind = "linear"

    def __init__(self, *, hidden_dim: int = 32, heads: int = 1) -> None:
        super().__init__(hidden_dim=hidden_dim, heads=heads)
        self.node_encoder = nn.Linear(self.node_encoder[0].in_features, hidden_dim)
        self.edge_encoder = nn.Linear(self.edge_encoder[0].in_features, hidden_dim)
        self.context_encoder = nn.Linear(
            self.context_encoder[0].in_features, hidden_dim
        )
        self.attention_layers = nn.ModuleList()
        self.heads_module = _QG2LinearHeads(hidden_dim)


def normalized_potentials(scores: torch.Tensor) -> torch.Tensor:
    if scores.ndim != 1 or scores.numel() == 0:
        raise ValueError("QG2 potential vector must be nonempty")
    if not bool(torch.isfinite(scores).all()):
        raise ValueError("QG2 emitted NaN/Inf")
    maximum = scores.abs().max()
    if float(maximum.detach().item()) <= 1.0e-12:
        return torch.zeros_like(scores)
    return scores / maximum


def normalize_qg2_potential_groups(
    node_scores: torch.Tensor,
    arc_scores: torch.Tensor,
    state_coefficients: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Apply one positive scale so the learned label order is unchanged."""

    groups = (node_scores, arc_scores, state_coefficients)
    if any(value.ndim != 1 for value in groups):
        raise ValueError("QG2 potential groups must be one-dimensional")
    if any(not bool(torch.isfinite(value).all()) for value in groups):
        raise ValueError("QG2 emitted NaN/Inf")
    maximum = torch.cat(groups).abs().max()
    if float(maximum.detach().item()) <= 1.0e-12:
        return tuple(torch.zeros_like(value) for value in groups)
    return tuple(value / maximum for value in groups)


def qg2_training_loss(
    *,
    preferred_scores: torch.Tensor,
    other_scores: torch.Tensor,
    benefit_probability: torch.Tensor,
    benefit_target: torch.Tensor,
    conditional_positive_gain: torch.Tensor,
    positive_gain_target: torch.Tensor,
    outcome_mask: torch.Tensor,
    positive_mask: torch.Tensor,
) -> torch.Tensor:
    """Fixed V2 loss: label rank + 0.1 benefit + 0.1 positive gain."""

    rank_loss = F.softplus(-(preferred_scores - other_scores)).mean()
    if bool(outcome_mask.any()):
        benefit_loss = F.binary_cross_entropy(
            benefit_probability[outcome_mask], benefit_target[outcome_mask]
        )
    else:
        benefit_loss = rank_loss.new_zeros(())
    if bool(positive_mask.any()):
        gain_loss = F.smooth_l1_loss(
            conditional_positive_gain[positive_mask],
            positive_gain_target[positive_mask],
        )
    else:
        gain_loss = rank_loss.new_zeros(())
    return rank_loss + 0.1 * benefit_loss + 0.1 * gain_loss


def checkpoint_payload(model: nn.Module, *, metadata: Mapping[str, object]):
    kind = str(getattr(model, "model_kind", ""))
    if kind not in QG2_MODEL_IDS:
        raise ValueError("unsupported QG2 model kind")
    return {
        "schema_version": QG2_CHECKPOINT_SCHEMA_V1,
        "feature_schema_version": QG2_FEATURE_SCHEMA_V1,
        "label_state_schema_version": QG2_LABEL_STATE_SCHEMA_V1,
        "model_kind": kind,
        "model_id": QG2_MODEL_IDS[kind],
        "hidden_dim": int(getattr(model, "hidden_dim", 32)),
        "heads": int(getattr(model, "heads", 1)),
        "metadata": dict(metadata),
        "state_dict": model.state_dict(),
    }


def load_checkpoint(path: str, *, map_location: str = "cpu"):
    payload = torch.load(path, map_location=map_location, weights_only=False)
    if str(payload.get("schema_version") or "") != QG2_CHECKPOINT_SCHEMA_V1:
        raise ValueError("QG2 checkpoint schema mismatch")
    if str(payload.get("feature_schema_version") or "") != QG2_FEATURE_SCHEMA_V1:
        raise ValueError("QG2 feature schema mismatch")
    if str(payload.get("label_state_schema_version") or "") != QG2_LABEL_STATE_SCHEMA_V1:
        raise ValueError("QG2 label-state schema mismatch")
    kind = str(payload.get("model_kind") or "")
    model_class = {"linear": QG2Linear, "mlp": QG2MLP, "gat": QG2TinyGAT}.get(kind)
    if model_class is None or str(payload.get("model_id") or "") != QG2_MODEL_IDS.get(kind):
        raise ValueError("QG2 model identity mismatch")
    model = model_class(
        hidden_dim=int(payload.get("hidden_dim") or 32),
        heads=int(payload.get("heads") or 1),
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, dict(payload.get("metadata") or {})
