"""Offline GAT branch-impact model for Journey branch scheduling studies.

This module is diagnostic/audit-only.  It scores Ryan-Foster branch candidates
with task graph embeddings, branch-pair features, and current RMP/branch
context.  It is not a branching oracle, pricing oracle, certificate source, or
official bound source.
"""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - import failure path is environment-dependent.
    import torch
    from torch import Tensor, nn
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "BPC_future.learning.branch_impact_model requires torch. "
        "Install the learning stack before using the branch-impact model."
    ) from exc

from BPC_future.learning.batch_impact_model import RMPContextEncoder
from BPC_future.learning.gnn_model import HierarchicalOptionGAT


BRANCH_IMPACT_EXACTNESS_CONTRACT: Dict[str, bool] = {
    "production_ready": False,
    "pricing_oracle": False,
    "branching_oracle": False,
    "certificate_source": False,
    "official_bound_effect": False,
    "can_prune_branch_candidates": False,
    "can_permanently_discard_true_rc_negative": False,
    "default_solver_effect": False,
}

BRANCH_IMPACT_HEAD_NAMES: tuple[str, ...] = (
    "branch_priority",
    "tail_improved",
    "completion_bound_tail",
    "early_branch_continues",
    "negative_chain_continues",
    "active_touch",
    "inactive_only",
    "predicted_child_negative_pricing_events",
    "predicted_child_completion_bound_retries",
    "predicted_child_early_branch_triggers",
    "predicted_walltime_gain",
    "predicted_child_proof_cpu",
    "predicted_time_to_certificate",
    "predicted_gap_improvement",
    "predicted_primal_improvement",
    "predicted_dual_bound_gain",
    "predicted_fathom_gain",
    "predicted_branch_count_delta",
    "predicted_completion_bound_retry_gain",
    "tree_policy",
)


class BranchPairImpactEncoder(nn.Module):
    """Encode candidate Ryan-Foster task pairs from graph/task embeddings."""

    def __init__(
        self,
        *,
        graph_hidden_dim: int,
        branch_feature_dim: int,
        context_hidden_dim: int,
        branch_hidden_dim: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        if int(graph_hidden_dim) <= 0:
            raise ValueError("graph_hidden_dim must be positive")
        if int(branch_feature_dim) <= 0:
            raise ValueError("branch_feature_dim must be positive")
        if int(context_hidden_dim) <= 0:
            raise ValueError("context_hidden_dim must be positive")
        if int(branch_hidden_dim) <= 0:
            raise ValueError("branch_hidden_dim must be positive")
        self.graph_hidden_dim = int(graph_hidden_dim)
        self.branch_feature_dim = int(branch_feature_dim)
        self.context_hidden_dim = int(context_hidden_dim)
        self.branch_hidden_dim = int(branch_hidden_dim)
        task_context_dim = 2 * self.graph_hidden_dim
        input_dim = (
            2 * task_context_dim
            + task_context_dim
            + task_context_dim
            + self.branch_feature_dim
            + self.context_hidden_dim
        )
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, self.branch_hidden_dim),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(self.branch_hidden_dim, self.branch_hidden_dim),
            nn.ReLU(),
        )

    def forward(
        self,
        task_h: Tensor,
        initial_task_h: Tensor,
        branch_pair_indices: Tensor,
        branch_pair_features: Tensor,
        context_embedding: Tensor,
    ) -> Dict[str, Tensor]:
        self._validate_inputs(
            task_h=task_h,
            initial_task_h=initial_task_h,
            branch_pair_indices=branch_pair_indices,
            branch_pair_features=branch_pair_features,
            context_embedding=context_embedding,
        )
        pair_indices = branch_pair_indices.to(device=task_h.device, dtype=torch.long)
        features = branch_pair_features.to(device=task_h.device, dtype=task_h.dtype)
        context = context_embedding.to(device=task_h.device, dtype=task_h.dtype)
        task_context = torch.cat([task_h, initial_task_h], dim=-1)
        left = task_context[pair_indices[:, 0]]
        right = task_context[pair_indices[:, 1]]
        context_rows = context.unsqueeze(0).expand(left.size(0), -1)
        pair_input = torch.cat(
            [
                left,
                right,
                torch.abs(left - right),
                left * right,
                features,
                context_rows,
            ],
            dim=-1,
        )
        _assert_finite(pair_input, "branch pair encoder input")
        embedding = self.encoder(pair_input)
        _assert_finite(embedding, "branch pair embedding")
        return {
            "branch_pair_embedding": embedding,
            "left_task_embedding": left,
            "right_task_embedding": right,
        }

    def _validate_inputs(
        self,
        *,
        task_h: Tensor,
        initial_task_h: Tensor,
        branch_pair_indices: Tensor,
        branch_pair_features: Tensor,
        context_embedding: Tensor,
    ) -> None:
        if task_h.dim() != 2 or task_h.size(1) != self.graph_hidden_dim:
            raise ValueError(f"task_h must have shape [num_tasks, {self.graph_hidden_dim}]")
        if initial_task_h.shape != task_h.shape:
            raise ValueError("initial_task_h must match task_h shape")
        if branch_pair_indices.dim() != 2 or branch_pair_indices.size(1) != 2:
            raise ValueError("branch_pair_indices must have shape [num_branch_candidates, 2]")
        if branch_pair_features.dim() != 2 or branch_pair_features.size(1) != self.branch_feature_dim:
            raise ValueError(
                "branch_pair_features must have shape "
                f"[num_branch_candidates, {self.branch_feature_dim}]"
            )
        if branch_pair_features.size(0) != branch_pair_indices.size(0):
            raise ValueError("branch_pair_features must have one row per branch pair")
        if context_embedding.dim() != 1 or context_embedding.numel() != self.context_hidden_dim:
            raise ValueError(f"context_embedding must have length {self.context_hidden_dim}")
        if int(branch_pair_indices.numel()) == 0:
            raise ValueError("branch_pair_indices must not be empty")
        if bool(torch.any(branch_pair_indices < 0)) or bool(torch.any(branch_pair_indices >= task_h.size(0))):
            raise ValueError("branch_pair_indices contain task indices outside graph task range")
        if bool(torch.any(branch_pair_indices[:, 0] == branch_pair_indices[:, 1])):
            raise ValueError("branch pair must contain two distinct task indices")
        _assert_finite(task_h, "task_h")
        _assert_finite(initial_task_h, "initial_task_h")
        _assert_finite(branch_pair_features, "branch_pair_features")
        _assert_finite(context_embedding, "context_embedding")


class GATBranchImpactModel(nn.Module):
    """Predict branch-tail impact for Ryan-Foster branch candidates."""

    def __init__(
        self,
        *,
        node_dim: int,
        option_dim: int,
        branch_feature_dim: int,
        context_feature_dim: int,
        hidden_dim: int = 128,
        option_hidden_dim: int = 128,
        pair_edge_dim: int = 128,
        num_gnn_layers: int = 2,
        heads: int = 4,
        dropout: float = 0.1,
        branch_hidden_dim: int = 128,
        context_hidden_dim: int = 64,
        impact_hidden_dim: int = 128,
        use_layer_norm: bool = True,
    ) -> None:
        super().__init__()
        if int(branch_feature_dim) <= 0:
            raise ValueError("branch_feature_dim must be positive")
        if int(context_feature_dim) <= 0:
            raise ValueError("context_feature_dim must be positive")
        if int(impact_hidden_dim) <= 0:
            raise ValueError("impact_hidden_dim must be positive")
        self.branch_feature_dim = int(branch_feature_dim)
        self.context_feature_dim = int(context_feature_dim)
        self.branch_hidden_dim = int(branch_hidden_dim)
        self.context_hidden_dim = int(context_hidden_dim)
        self.impact_hidden_dim = int(impact_hidden_dim)
        self.exactness_contract = dict(BRANCH_IMPACT_EXACTNESS_CONTRACT)
        self.graph_encoder = HierarchicalOptionGAT(
            node_dim=int(node_dim),
            option_dim=int(option_dim),
            hidden_dim=int(hidden_dim),
            option_hidden_dim=int(option_hidden_dim),
            pair_edge_dim=int(pair_edge_dim),
            num_gnn_layers=int(num_gnn_layers),
            heads=int(heads),
            dropout=float(dropout),
            use_layer_norm=bool(use_layer_norm),
        )
        self.context_encoder = RMPContextEncoder(
            context_feature_dim=self.context_feature_dim,
            context_hidden_dim=self.context_hidden_dim,
            dropout=float(dropout),
        )
        self.branch_encoder = BranchPairImpactEncoder(
            graph_hidden_dim=int(hidden_dim),
            branch_feature_dim=self.branch_feature_dim,
            context_hidden_dim=self.context_hidden_dim,
            branch_hidden_dim=self.branch_hidden_dim,
            dropout=float(dropout),
        )
        decision_dim = self.branch_hidden_dim + self.context_hidden_dim
        self.branch_priority_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.tail_improved_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.completion_bound_tail_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.early_branch_continues_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.negative_chain_continues_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.active_touch_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.inactive_only_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.child_negative_pricing_events_head = _mlp_head(
            decision_dim,
            self.impact_hidden_dim,
            dropout=float(dropout),
        )
        self.child_completion_bound_retries_head = _mlp_head(
            decision_dim,
            self.impact_hidden_dim,
            dropout=float(dropout),
        )
        self.child_early_branch_triggers_head = _mlp_head(
            decision_dim,
            self.impact_hidden_dim,
            dropout=float(dropout),
        )
        self.walltime_gain_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.child_proof_cpu_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.time_to_certificate_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.gap_improvement_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.primal_improvement_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.dual_bound_gain_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.fathom_gain_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.branch_count_delta_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.completion_bound_retry_gain_head = _mlp_head(
            decision_dim,
            self.impact_hidden_dim,
            dropout=float(dropout),
        )
        self.tree_policy_head = _mlp_head(decision_dim, self.impact_hidden_dim, dropout=float(dropout))

    def forward(
        self,
        data: Any,
        branch_pair_indices: Tensor,
        branch_pair_features: Tensor,
        context_features: Tensor,
    ) -> Dict[str, Tensor]:
        encoded = self.graph_encoder.encode(data)
        context_embedding = self.context_encoder(
            context_features,
            device=encoded["task_h"].device,
            dtype=encoded["task_h"].dtype,
        )
        branch_output = self.branch_encoder(
            task_h=encoded["task_h"],
            initial_task_h=encoded["initial_task_h"],
            branch_pair_indices=branch_pair_indices,
            branch_pair_features=branch_pair_features,
            context_embedding=context_embedding,
        )
        branch_embedding = branch_output["branch_pair_embedding"]
        context_rows = context_embedding.unsqueeze(0).expand(branch_embedding.size(0), -1)
        decision_input = torch.cat([branch_embedding, context_rows], dim=-1)
        _assert_finite(decision_input, "branch impact decision input")

        branch_priority_logit = self.branch_priority_head(decision_input).squeeze(-1)
        tail_improved_logit = self.tail_improved_head(decision_input).squeeze(-1)
        completion_bound_tail_logit = self.completion_bound_tail_head(decision_input).squeeze(-1)
        early_branch_continues_logit = self.early_branch_continues_head(decision_input).squeeze(-1)
        negative_chain_continues_logit = self.negative_chain_continues_head(decision_input).squeeze(-1)
        active_touch_logit = self.active_touch_head(decision_input).squeeze(-1)
        inactive_only_logit = self.inactive_only_head(decision_input).squeeze(-1)
        predicted_child_negative_pricing_events = self.child_negative_pricing_events_head(decision_input).squeeze(-1)
        predicted_child_completion_bound_retries = self.child_completion_bound_retries_head(decision_input).squeeze(-1)
        predicted_child_early_branch_triggers = self.child_early_branch_triggers_head(decision_input).squeeze(-1)
        predicted_walltime_gain = self.walltime_gain_head(decision_input).squeeze(-1)
        predicted_child_proof_cpu = self.child_proof_cpu_head(decision_input).squeeze(-1)
        predicted_time_to_certificate = self.time_to_certificate_head(decision_input).squeeze(-1)
        predicted_gap_improvement = self.gap_improvement_head(decision_input).squeeze(-1)
        predicted_primal_improvement = self.primal_improvement_head(decision_input).squeeze(-1)
        predicted_dual_bound_gain = self.dual_bound_gain_head(decision_input).squeeze(-1)
        predicted_fathom_gain = self.fathom_gain_head(decision_input).squeeze(-1)
        predicted_branch_count_delta = self.branch_count_delta_head(decision_input).squeeze(-1)
        predicted_completion_bound_retry_gain = self.completion_bound_retry_gain_head(decision_input).squeeze(-1)
        tree_policy_logit = self.tree_policy_head(decision_input).squeeze(-1)
        outputs: Dict[str, Tensor] = {
            "branch_pair_embedding": branch_embedding,
            "context_embedding": context_embedding,
            "branch_decision_embedding": decision_input,
            "branch_priority_logit": branch_priority_logit,
            "branch_priority_probability": torch.sigmoid(branch_priority_logit),
            "tail_improved_logit": tail_improved_logit,
            "tail_improved_probability": torch.sigmoid(tail_improved_logit),
            "completion_bound_tail_logit": completion_bound_tail_logit,
            "completion_bound_tail_probability": torch.sigmoid(completion_bound_tail_logit),
            "early_branch_continues_logit": early_branch_continues_logit,
            "early_branch_continues_probability": torch.sigmoid(early_branch_continues_logit),
            "negative_chain_continues_logit": negative_chain_continues_logit,
            "negative_chain_continues_probability": torch.sigmoid(negative_chain_continues_logit),
            "active_touch_logit": active_touch_logit,
            "active_touch_probability": torch.sigmoid(active_touch_logit),
            "inactive_only_logit": inactive_only_logit,
            "inactive_only_probability": torch.sigmoid(inactive_only_logit),
            "predicted_child_negative_pricing_events": predicted_child_negative_pricing_events,
            "predicted_child_completion_bound_retries": predicted_child_completion_bound_retries,
            "predicted_child_early_branch_triggers": predicted_child_early_branch_triggers,
            "predicted_walltime_gain": predicted_walltime_gain,
            "predicted_child_proof_cpu": predicted_child_proof_cpu,
            "predicted_time_to_certificate": predicted_time_to_certificate,
            "predicted_gap_improvement": predicted_gap_improvement,
            "predicted_primal_improvement": predicted_primal_improvement,
            "predicted_dual_bound_gain": predicted_dual_bound_gain,
            "predicted_fathom_gain": predicted_fathom_gain,
            "predicted_branch_count_delta": predicted_branch_count_delta,
            "predicted_completion_bound_retry_gain": predicted_completion_bound_retry_gain,
            "tree_policy_logit": tree_policy_logit,
            "tree_policy_probability": torch.sigmoid(tree_policy_logit),
        }
        outputs.update(branch_output)
        for name, value in outputs.items():
            _assert_finite(value, name)
        return outputs


def branch_impact_exactness_contract() -> Dict[str, bool]:
    """Return a copy of the branch-impact exactness contract."""

    return dict(BRANCH_IMPACT_EXACTNESS_CONTRACT)


def _mlp_head(input_dim: int, hidden_dim: int, *, dropout: float) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(int(input_dim), int(hidden_dim)),
        nn.ReLU(),
        nn.Dropout(float(dropout)),
        nn.Linear(int(hidden_dim), 1),
    )


def _assert_finite(tensor: Tensor, name: str) -> None:
    if not bool(torch.all(torch.isfinite(tensor))):
        raise ValueError(f"{name} contains NaN or Inf")
