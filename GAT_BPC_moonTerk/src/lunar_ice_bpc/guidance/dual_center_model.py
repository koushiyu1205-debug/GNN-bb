"""Independent root dual-center model ladder.

Torch is intentionally imported in this leaf module only.  Framework-free
deployment eligibility must be checked before importing it, especially for
scale 5/10 pre-import bypass.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn

from lunar_ice_bpc.guidance.models import EdgeAttentionLayer


ROOT_DUAL_CENTER_MODEL_KINDS = (
    "linear",
    "mlp2x32",
    "gat1x32x1",
    "gat2x32x2",
)
ROOT_DUAL_CENTER_ARCHITECTURE_VERSION = (
    "lunar_ice_bpc.root_dual_center.trajectory_rc.v1"
)
ROOT_DUAL_CENTER_CHECKPOINT_SCHEMA = (
    "lunar_ice_bpc.root_dual_center_checkpoint.v1"
)


@dataclass(frozen=True)
class RootDualCenterDimensions:
    node_input_dim: int
    edge_input_dim: int
    resource_context_dim: int = 4


class RootDualCenterModel(nn.Module):
    """Predict a normalized task-dual residual and aleatoric uncertainty."""

    def __init__(
        self,
        dimensions: RootDualCenterDimensions,
        *,
        kind: str,
    ) -> None:
        super().__init__()
        if kind not in ROOT_DUAL_CENTER_MODEL_KINDS:
            raise ValueError(f"unsupported root dual-center kind {kind!r}")
        self.kind = str(kind)
        self.node_input_dim = int(dimensions.node_input_dim)
        self.edge_input_dim = int(dimensions.edge_input_dim)
        self.resource_context_dim = int(
            dimensions.resource_context_dim
        )
        hidden_dim, layer_count, head_count = _shape(self.kind)
        if self.kind == "linear":
            self.node_encoder = nn.Identity()
            self.edge_encoder = nn.Identity()
            encoded_dim = self.node_input_dim
            encoded_edge_dim = self.edge_input_dim
        else:
            self.node_encoder = nn.Sequential(
                nn.Linear(self.node_input_dim, hidden_dim),
                nn.ReLU(),
            )
            self.edge_encoder = nn.Sequential(
                nn.Linear(self.edge_input_dim, hidden_dim),
                nn.ReLU(),
            )
            encoded_dim = hidden_dim
            encoded_edge_dim = hidden_dim
        self.attention_layers = nn.ModuleList(
            EdgeAttentionLayer(
                encoded_dim,
                encoded_edge_dim,
                head_count,
            )
            for _ in range(layer_count)
        )
        task_input_dim = (
            2 * encoded_dim + self.resource_context_dim
        )
        if self.kind == "linear":
            self.center_head = nn.Linear(task_input_dim, 1)
            self.log_variance_head = nn.Linear(task_input_dim, 1)
        else:
            self.center_head = nn.Sequential(
                nn.Linear(task_input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1),
            )
            self.log_variance_head = nn.Sequential(
                nn.Linear(task_input_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, 1),
            )

    def forward(
        self,
        *,
        node_features: torch.Tensor,
        edge_index: torch.Tensor,
        edge_features: torch.Tensor,
        task_node_indices: torch.Tensor,
        resource_context: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        node_embedding = self.node_encoder(node_features)
        edge_embedding = self.edge_encoder(edge_features)
        for layer in self.attention_layers:
            node_embedding = layer(
                node_embedding, edge_index, edge_embedding
            )
        global_embedding = node_embedding.mean(dim=0)
        task_count = int(task_node_indices.shape[0])
        task_inputs = torch.cat(
            (
                node_embedding[task_node_indices],
                global_embedding.expand(task_count, -1),
                resource_context.expand(task_count, -1),
            ),
            dim=-1,
        )
        normalized_residual = self.center_head(task_inputs).squeeze(-1)
        log_variance = self.log_variance_head(task_inputs).squeeze(-1)
        return {
            "normalized_residual": normalized_residual,
            "log_variance": torch.clamp(
                log_variance, min=-8.0, max=6.0
            ),
            "node_embedding": node_embedding,
            "global_embedding": global_embedding,
        }


def build_root_dual_center_model(
    kind: str,
    *,
    node_input_dim: int,
    edge_input_dim: int,
    resource_context_dim: int = 4,
) -> RootDualCenterModel:
    return RootDualCenterModel(
        RootDualCenterDimensions(
            node_input_dim=int(node_input_dim),
            edge_input_dim=int(edge_input_dim),
            resource_context_dim=int(resource_context_dim),
        ),
        kind=str(kind),
    )


def root_dual_center_checkpoint_payload(
    model: RootDualCenterModel,
    *,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": ROOT_DUAL_CENTER_CHECKPOINT_SCHEMA,
        "model_architecture_version": (
            ROOT_DUAL_CENTER_ARCHITECTURE_VERSION
        ),
        "model_kind": model.kind,
        "node_input_dim": model.node_input_dim,
        "edge_input_dim": model.edge_input_dim,
        "resource_context_dim": model.resource_context_dim,
        "metadata": dict(metadata),
        "state_dict": model.state_dict(),
    }


def load_root_dual_center_checkpoint(
    path: str,
    *,
    map_location: str = "cpu",
) -> tuple[RootDualCenterModel, dict[str, Any]]:
    payload = torch.load(
        path, map_location=map_location, weights_only=False
    )
    if str(payload.get("schema_version") or "") != (
        ROOT_DUAL_CENTER_CHECKPOINT_SCHEMA
    ):
        raise ValueError("root dual-center checkpoint schema mismatch")
    if str(payload.get("model_architecture_version") or "") != (
        ROOT_DUAL_CENTER_ARCHITECTURE_VERSION
    ):
        raise ValueError(
            "root dual-center checkpoint architecture mismatch"
        )
    model = build_root_dual_center_model(
        str(payload["model_kind"]),
        node_input_dim=int(payload["node_input_dim"]),
        edge_input_dim=int(payload["edge_input_dim"]),
        resource_context_dim=int(payload["resource_context_dim"]),
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, dict(payload.get("metadata") or {})


def _shape(kind: str) -> tuple[int, int, int]:
    return {
        "linear": (0, 0, 0),
        "mlp2x32": (32, 0, 0),
        "gat1x32x1": (32, 1, 1),
        "gat2x32x2": (32, 2, 2),
    }[kind]
