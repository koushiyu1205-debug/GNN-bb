"""Smallest-first ranking model ladder for P0 V2 guidance.

This module imports torch and therefore must only be imported after the
framework-free deployment gate has admitted the current scale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F


MODEL_LADDER = (
    "linear",
    "mlp2x32",
    "gat1x32x1",
    "gat2x32x2",
    "gat3x64x4",
)
MODEL_ARCHITECTURE_VERSION = (
    "lunar_ice_bpc.gat_ranker.counterfactual_trajectory.v2"
)
SURVIVAL_HAZARD_BINS = 4


@dataclass(frozen=True)
class ModelDimensions:
    node_input_dim: int
    edge_input_dim: int


def symmetric_pair_features(
    left: torch.Tensor,
    right: torch.Tensor,
    global_embedding: torch.Tensor,
    pair_context: torch.Tensor,
) -> torch.Tensor:
    """Features invariant to exchanging a Ryan--Foster pair."""

    return torch.cat(
        (
            left + right,
            torch.abs(left - right),
            left * right,
            global_embedding,
            pair_context,
        ),
        dim=-1,
    )


class EdgeAttentionLayer(nn.Module):
    def __init__(self, hidden_dim: int, edge_dim: int, heads: int) -> None:
        super().__init__()
        self.hidden_dim = int(hidden_dim)
        self.heads = int(heads)
        self.query = nn.Linear(hidden_dim, hidden_dim * heads, bias=False)
        self.key = nn.Linear(hidden_dim, hidden_dim * heads, bias=False)
        self.value = nn.Linear(hidden_dim, hidden_dim * heads, bias=False)
        self.edge_bias = nn.Linear(edge_dim, heads, bias=False)
        self.self_projection = nn.Linear(hidden_dim, hidden_dim)
        self.output = nn.Linear(hidden_dim, hidden_dim)
        self.norm = nn.LayerNorm(hidden_dim)

    def forward(
        self,
        node_embedding: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
    ) -> torch.Tensor:
        node_count = int(node_embedding.shape[0])
        if edge_index.numel() == 0:
            return self.norm(
                node_embedding + self.output(self.self_projection(node_embedding))
            )
        sources = edge_index[0]
        targets = edge_index[1]
        q = self.query(node_embedding).reshape(
            node_count, self.heads, self.hidden_dim
        )
        k = self.key(node_embedding).reshape(
            node_count, self.heads, self.hidden_dim
        )
        v = self.value(node_embedding).reshape(
            node_count, self.heads, self.hidden_dim
        )
        logits = (
            (q[targets] * k[sources]).sum(dim=-1)
            / float(self.hidden_dim) ** 0.5
            + self.edge_bias(edge_features)
        )
        logits = F.leaky_relu(logits, negative_slope=0.2)
        target_index = targets[:, None].expand(-1, self.heads)
        maxima = torch.full(
            (node_count, self.heads),
            -torch.inf,
            dtype=logits.dtype,
            device=logits.device,
        )
        maxima.scatter_reduce_(
            0, target_index, logits, reduce="amax", include_self=True
        )
        weights = torch.exp(logits - maxima[targets])
        denominators = torch.zeros_like(maxima)
        denominators.scatter_add_(0, target_index, weights)
        weights = weights / denominators[targets].clamp_min(1.0e-12)
        messages = weights[..., None] * v[sources]
        aggregated = torch.zeros(
            (node_count, self.heads, self.hidden_dim),
            dtype=messages.dtype,
            device=messages.device,
        )
        aggregated.scatter_add_(
            0,
            targets[:, None, None].expand_as(messages),
            messages,
        )
        combined = aggregated.mean(dim=1)
        return self.norm(
            node_embedding
            + self.output(F.elu(combined))
            + self.self_projection(node_embedding)
        )


class GuidanceRanker(nn.Module):
    """Shared encoder with pricing heads and shadow proof/branch heads."""

    def __init__(
        self,
        dimensions: ModelDimensions,
        *,
        kind: str,
    ) -> None:
        super().__init__()
        if kind not in MODEL_LADDER:
            raise ValueError(f"unsupported model kind {kind!r}")
        self.kind = kind
        hidden_dim, layers, heads = _model_shape(kind)
        self.hidden_dim = hidden_dim
        self.node_input_dim = dimensions.node_input_dim
        self.edge_input_dim = dimensions.edge_input_dim
        if kind == "linear":
            self.node_encoder = nn.Identity()
            encoded_dim = dimensions.node_input_dim
        elif kind == "mlp2x32":
            self.node_encoder = nn.Sequential(
                nn.Linear(dimensions.node_input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
            )
            encoded_dim = hidden_dim
        else:
            self.node_encoder = nn.Sequential(
                nn.Linear(dimensions.node_input_dim, hidden_dim),
                nn.ReLU(),
            )
            encoded_dim = hidden_dim
        self.edge_encoder = (
            nn.Identity()
            if kind == "linear"
            else nn.Sequential(
                nn.Linear(dimensions.edge_input_dim, hidden_dim),
                nn.ReLU(),
            )
        )
        encoded_edge_dim = (
            dimensions.edge_input_dim if kind == "linear" else hidden_dim
        )
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(encoded_dim, encoded_edge_dim, heads)
            for _ in range(layers)
        )
        head_factory = (
            (lambda input_dim: nn.Linear(input_dim, 1))
            if kind == "linear"
            else (
                lambda input_dim: nn.Sequential(
                    nn.Linear(input_dim, hidden_dim),
                    nn.ReLU(),
                    nn.Linear(hidden_dim, 1),
                )
            )
        )
        task_input_dim = encoded_dim + 4
        arc_input_dim = encoded_dim * 2 + encoded_edge_dim + 4
        harvest_input_dim = encoded_dim + 8
        noop_input_dim = encoded_dim + 4
        self.task_head = head_factory(task_input_dim)
        self.arc_head = head_factory(arc_input_dim)
        self.harvest_head = head_factory(harvest_input_dim)
        self.task_advantage_head = head_factory(task_input_dim)
        self.arc_advantage_head = head_factory(arc_input_dim)
        self.harvest_advantage_head = head_factory(harvest_input_dim)
        self.task_hazard_head = _multi_output_head(
            kind, task_input_dim, hidden_dim, SURVIVAL_HAZARD_BINS
        )
        self.arc_hazard_head = _multi_output_head(
            kind, arc_input_dim, hidden_dim, SURVIVAL_HAZARD_BINS
        )
        self.harvest_hazard_head = _multi_output_head(
            kind, harvest_input_dim, hidden_dim, SURVIVAL_HAZARD_BINS
        )
        self.task_noop_head = head_factory(noop_input_dim)
        self.arc_noop_head = head_factory(noop_input_dim)
        self.harvest_noop_head = head_factory(noop_input_dim)
        self.task_noop_hazard_head = _multi_output_head(
            kind, noop_input_dim, hidden_dim, SURVIVAL_HAZARD_BINS
        )
        self.arc_noop_hazard_head = _multi_output_head(
            kind, noop_input_dim, hidden_dim, SURVIVAL_HAZARD_BINS
        )
        self.harvest_noop_hazard_head = _multi_output_head(
            kind, noop_input_dim, hidden_dim, SURVIVAL_HAZARD_BINS
        )
        self.proof_risk_head = head_factory(encoded_dim + 4)
        self.branch_head = head_factory(encoded_dim * 4 + 4)

    def encode(
        self,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        node_embedding = self.node_encoder(node_features)
        edge_embedding = self.edge_encoder(edge_features)
        for layer in self.attention_layers:
            node_embedding = layer(
                node_embedding, edge_index, edge_embedding
            )
        return node_embedding, edge_embedding

    def forward(
        self,
        *,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        task_node_indices: torch.Tensor,
        resource_context: torch.Tensor,
        harvest_task_masks: torch.Tensor | None = None,
        harvest_context: torch.Tensor | None = None,
        branch_pairs: torch.Tensor | None = None,
        branch_context: torch.Tensor | None = None,
        detach_auxiliary_encoder: bool = False,
    ) -> dict[str, torch.Tensor]:
        node_embedding, edge_embedding = self.encode(
            node_features, edge_index, edge_features
        )
        global_embedding = node_embedding.mean(dim=0)
        noop_inputs = torch.cat(
            (global_embedding, resource_context), dim=-1
        )
        task_resource = resource_context.expand(
            task_node_indices.shape[0], -1
        )
        task_inputs = torch.cat(
            (node_embedding[task_node_indices], task_resource), dim=-1
        )
        task_scores = self.task_head(task_inputs).squeeze(-1)
        arc_resource = resource_context.expand(edge_index.shape[1], -1)
        arc_inputs = torch.cat(
            (
                node_embedding[edge_index[0]],
                node_embedding[edge_index[1]],
                edge_embedding,
                arc_resource,
            ),
            dim=-1,
        )
        output = {
            "task_scores": task_scores,
            "arc_scores": self.arc_head(arc_inputs).squeeze(-1),
            "task_advantages": self.task_advantage_head(
                task_inputs.detach()
                if detach_auxiliary_encoder
                else task_inputs
            ).squeeze(-1),
            "arc_advantages": self.arc_advantage_head(
                arc_inputs.detach()
                if detach_auxiliary_encoder
                else arc_inputs
            ).squeeze(-1),
            "task_hazard_logits": self.task_hazard_head(
                task_inputs.detach()
                if detach_auxiliary_encoder
                else task_inputs
            ),
            "arc_hazard_logits": self.arc_hazard_head(
                arc_inputs.detach()
                if detach_auxiliary_encoder
                else arc_inputs
            ),
            "task_noop_score": self.task_noop_head(noop_inputs).squeeze(-1),
            "arc_noop_score": self.arc_noop_head(noop_inputs).squeeze(-1),
            "harvest_noop_score": self.harvest_noop_head(
                noop_inputs
            ).squeeze(-1),
            "task_noop_hazard_logits": self.task_noop_hazard_head(
                noop_inputs.detach()
                if detach_auxiliary_encoder
                else noop_inputs
            ),
            "arc_noop_hazard_logits": self.arc_noop_hazard_head(
                noop_inputs.detach()
                if detach_auxiliary_encoder
                else noop_inputs
            ),
            "harvest_noop_hazard_logits": self.harvest_noop_hazard_head(
                noop_inputs.detach()
                if detach_auxiliary_encoder
                else noop_inputs
            ),
            "proof_tail_risk": self.proof_risk_head(
                torch.cat((global_embedding, resource_context), dim=-1)
            ).squeeze(-1),
            "node_embedding": node_embedding,
            "global_embedding": global_embedding,
        }
        if harvest_task_masks is not None:
            denominators = harvest_task_masks.sum(dim=-1, keepdim=True).clamp_min(
                1.0
            )
            candidate_embedding = (
                harvest_task_masks @ node_embedding
            ) / denominators
            context = (
                torch.zeros(
                    (candidate_embedding.shape[0], 4),
                    dtype=candidate_embedding.dtype,
                    device=candidate_embedding.device,
                )
                if harvest_context is None
                else harvest_context
            )
            harvest_resource = resource_context.expand(
                candidate_embedding.shape[0], -1
            )
            harvest_inputs = torch.cat(
                (candidate_embedding, context, harvest_resource), dim=-1
            )
            output["harvest_scores"] = self.harvest_head(
                harvest_inputs
            ).squeeze(-1)
            output["harvest_advantages"] = self.harvest_advantage_head(
                harvest_inputs.detach()
                if detach_auxiliary_encoder
                else harvest_inputs
            ).squeeze(-1)
            output["harvest_hazard_logits"] = self.harvest_hazard_head(
                harvest_inputs.detach()
                if detach_auxiliary_encoder
                else harvest_inputs
            )
        if branch_pairs is not None:
            context = (
                torch.zeros(
                    (branch_pairs.shape[0], 4),
                    dtype=node_embedding.dtype,
                    device=node_embedding.device,
                )
                if branch_context is None
                else branch_context
            )
            global_rows = global_embedding.expand(branch_pairs.shape[0], -1)
            features = symmetric_pair_features(
                node_embedding[branch_pairs[:, 0]],
                node_embedding[branch_pairs[:, 1]],
                global_rows,
                context,
            )
            # Larger ranking score means lower predicted branch cost.
            output["branch_scores"] = self.branch_head(features).squeeze(-1)
        return output


def build_model(
    kind: str,
    *,
    node_input_dim: int,
    edge_input_dim: int,
) -> GuidanceRanker:
    return GuidanceRanker(
        ModelDimensions(
            node_input_dim=int(node_input_dim),
            edge_input_dim=int(edge_input_dim),
        ),
        kind=str(kind),
    )


def checkpoint_payload(
    model: GuidanceRanker,
    *,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "lunar_ice_bpc.gat_checkpoint.v2",
        "model_architecture_version": MODEL_ARCHITECTURE_VERSION,
        "model_kind": model.kind,
        "node_input_dim": model.node_input_dim,
        "edge_input_dim": model.edge_input_dim,
        "metadata": dict(metadata),
        "state_dict": model.state_dict(),
    }


def load_checkpoint(path: str, *, map_location: str = "cpu"):
    payload = torch.load(
        path, map_location=map_location, weights_only=False
    )
    if str(payload.get("schema_version") or "") != (
        "lunar_ice_bpc.gat_checkpoint.v2"
    ):
        raise ValueError(
            "legacy grade-objective checkpoint rejected; retrain the "
            "counterfactual trajectory architecture"
        )
    if str(payload.get("model_architecture_version") or "") != (
        MODEL_ARCHITECTURE_VERSION
    ):
        raise ValueError("GAT checkpoint architecture version mismatch")
    model = build_model(
        str(payload["model_kind"]),
        node_input_dim=int(payload["node_input_dim"]),
        edge_input_dim=int(payload["edge_input_dim"]),
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, dict(payload.get("metadata") or {})


def _model_shape(kind: str) -> tuple[int, int, int]:
    return {
        "linear": (0, 0, 0),
        "mlp2x32": (32, 0, 0),
        "gat1x32x1": (32, 1, 1),
        "gat2x32x2": (32, 2, 2),
        "gat3x64x4": (64, 3, 4),
    }[kind]


def _multi_output_head(
    kind: str,
    input_dim: int,
    hidden_dim: int,
    output_dim: int,
) -> nn.Module:
    if kind == "linear":
        return nn.Linear(input_dim, output_dim)
    return nn.Sequential(
        nn.Linear(input_dim, hidden_dim),
        nn.ReLU(),
        nn.Linear(hidden_dim, output_dim),
    )
