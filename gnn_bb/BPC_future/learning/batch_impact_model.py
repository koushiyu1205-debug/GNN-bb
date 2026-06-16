"""Offline GAT batch-impact model for RMP-trajectory admission studies.

This module is diagnostic/audit-only.  It predicts whether a true-RC-verified
candidate journey batch looks useful for RMP trajectory improvement, but it is
not a pricing oracle, certificate source, official bound source, or permission
to permanently discard true-RC negative columns.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:  # pragma: no cover - import failure path is environment-dependent.
    import torch
    from torch import Tensor, nn
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "BPC_future.learning.batch_impact_model requires torch. "
        "Install the learning stack before using the batch-impact model."
    ) from exc

from BPC_future.learning.gnn_model import HierarchicalOptionGAT


BATCH_IMPACT_EXACTNESS_CONTRACT: Dict[str, bool] = {
    "production_ready": False,
    "pricing_oracle": False,
    "certificate_source": False,
    "official_bound_effect": False,
    "can_permanently_discard_true_rc_negative": False,
    "delay_queue_replaces_exact_pricing": False,
}

BATCH_IMPACT_HEAD_NAMES: tuple[str, ...] = (
    "candidate_high_priority",
    "candidate_delay_risk",
    "batch_roi_positive",
    "objective_progress",
    "tail_improved",
    "bad_mode_switch",
    "support_changed_good",
    "predicted_delta_v",
    "predicted_barrier_slack",
    "predicted_accepted_batch_roi",
)


class JourneyCandidateEncoder(nn.Module):
    """Encode ordered journey candidates from task embeddings and local features.

    ``candidate_task_membership`` captures the set of covered tasks, while
    ``candidate_sequence_positions`` captures their order inside the candidate
    journey.  Two candidates with the same task set but reversed sequence can
    therefore receive different embeddings.
    """

    def __init__(
        self,
        *,
        graph_hidden_dim: int,
        candidate_feature_dim: int,
        candidate_hidden_dim: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        if int(graph_hidden_dim) <= 0:
            raise ValueError("graph_hidden_dim must be positive")
        if int(candidate_feature_dim) <= 0:
            raise ValueError("candidate_feature_dim must be positive")
        if int(candidate_hidden_dim) <= 0:
            raise ValueError("candidate_hidden_dim must be positive")

        self.graph_hidden_dim = int(graph_hidden_dim)
        self.candidate_feature_dim = int(candidate_feature_dim)
        self.candidate_hidden_dim = int(candidate_hidden_dim)

        task_context_dim = 2 * self.graph_hidden_dim
        input_dim = 4 * task_context_dim + self.candidate_feature_dim + 2
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, self.candidate_hidden_dim),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(self.candidate_hidden_dim, self.candidate_hidden_dim),
            nn.ReLU(),
        )

    def forward(
        self,
        task_h: Tensor,
        initial_task_h: Tensor,
        candidate_task_membership: Tensor,
        candidate_sequence_positions: Tensor,
        candidate_features: Tensor,
    ) -> Dict[str, Tensor]:
        self._validate_inputs(
            task_h=task_h,
            initial_task_h=initial_task_h,
            candidate_task_membership=candidate_task_membership,
            candidate_sequence_positions=candidate_sequence_positions,
            candidate_features=candidate_features,
        )
        membership = candidate_task_membership.to(device=task_h.device, dtype=task_h.dtype)
        positions = candidate_sequence_positions.to(device=task_h.device, dtype=task_h.dtype)
        candidate_features = candidate_features.to(device=task_h.device, dtype=task_h.dtype)

        present = membership > 0
        task_counts = membership.sum(dim=1, keepdim=True)
        if bool(torch.any(task_counts <= 0)):
            raise ValueError("each candidate must cover at least one task")

        if bool(torch.any(positions[present] <= 0)):
            raise ValueError("present tasks must have positive sequence positions")
        if bool(torch.any(positions[~present] != 0)):
            raise ValueError("absent tasks must have zero sequence position")

        max_order = positions.max(dim=1, keepdim=True).values.clamp_min(1.0)
        normalized_order = positions / max_order

        large = torch.full_like(positions, torch.finfo(positions.dtype).max)
        min_present_order = torch.where(present, positions, large).min(dim=1, keepdim=True).values
        max_present_order = torch.where(present, positions, torch.zeros_like(positions)).max(dim=1, keepdim=True).values
        first_mask = (present & (positions == min_present_order)).to(dtype=task_h.dtype)
        last_mask = (present & (positions == max_present_order)).to(dtype=task_h.dtype)

        task_context = torch.cat([task_h, initial_task_h], dim=-1)
        set_pool = membership @ task_context / task_counts
        order_pool = normalized_order @ task_context / task_counts
        first_pool = first_mask @ task_context / first_mask.sum(dim=1, keepdim=True).clamp_min(1.0)
        last_pool = last_mask @ task_context / last_mask.sum(dim=1, keepdim=True).clamp_min(1.0)
        order_span = (max_present_order - min_present_order).clamp_min(0.0)

        encoder_input = torch.cat(
            [
                set_pool,
                order_pool,
                first_pool,
                last_pool,
                candidate_features,
                task_counts,
                order_span,
            ],
            dim=-1,
        )
        _assert_finite(encoder_input, "candidate encoder input")
        embedding = self.encoder(encoder_input)
        _assert_finite(embedding, "candidate embedding")
        return {
            "candidate_embedding": embedding,
            "task_counts": task_counts.squeeze(-1),
            "order_span": order_span.squeeze(-1),
            "set_pool": set_pool,
            "order_pool": order_pool,
            "first_pool": first_pool,
            "last_pool": last_pool,
        }

    def _validate_inputs(
        self,
        *,
        task_h: Tensor,
        initial_task_h: Tensor,
        candidate_task_membership: Tensor,
        candidate_sequence_positions: Tensor,
        candidate_features: Tensor,
    ) -> None:
        if task_h.dim() != 2 or task_h.size(1) != self.graph_hidden_dim:
            raise ValueError(f"task_h must have shape [num_tasks, {self.graph_hidden_dim}]")
        if initial_task_h.shape != task_h.shape:
            raise ValueError("initial_task_h must have the same shape as task_h")
        if candidate_task_membership.dim() != 2:
            raise ValueError("candidate_task_membership must have shape [num_candidates, num_tasks]")
        if candidate_sequence_positions.shape != candidate_task_membership.shape:
            raise ValueError("candidate_sequence_positions must match candidate_task_membership shape")
        if candidate_features.dim() != 2 or candidate_features.size(1) != self.candidate_feature_dim:
            raise ValueError(
                "candidate_features must have shape "
                f"[num_candidates, {self.candidate_feature_dim}]"
            )
        if candidate_features.size(0) != candidate_task_membership.size(0):
            raise ValueError("candidate_features and candidate_task_membership must have the same row count")
        if candidate_task_membership.size(1) != task_h.size(0):
            raise ValueError("candidate_task_membership width must equal the number of task embeddings")
        _assert_finite(task_h, "task_h")
        _assert_finite(initial_task_h, "initial_task_h")
        _assert_finite(candidate_task_membership, "candidate_task_membership")
        _assert_finite(candidate_sequence_positions, "candidate_sequence_positions")
        _assert_finite(candidate_features, "candidate_features")


class RMPContextEncoder(nn.Module):
    """Encode one shared RMP/dual/basis/tail-retry context vector."""

    def __init__(
        self,
        *,
        context_feature_dim: int,
        context_hidden_dim: int = 64,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        if int(context_feature_dim) <= 0:
            raise ValueError("context_feature_dim must be positive")
        if int(context_hidden_dim) <= 0:
            raise ValueError("context_hidden_dim must be positive")
        self.context_feature_dim = int(context_feature_dim)
        self.context_hidden_dim = int(context_hidden_dim)
        self.encoder = nn.Sequential(
            nn.Linear(self.context_feature_dim, self.context_hidden_dim),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(self.context_hidden_dim, self.context_hidden_dim),
            nn.ReLU(),
        )

    def forward(self, context_features: Tensor, *, device: torch.device, dtype: torch.dtype) -> Tensor:
        if context_features.dim() == 1:
            if context_features.numel() != self.context_feature_dim:
                raise ValueError(
                    f"context_features length must be {self.context_feature_dim}, got {context_features.numel()}"
                )
            features = context_features.unsqueeze(0)
        elif context_features.dim() == 2 and context_features.size(0) == 1:
            if context_features.size(1) != self.context_feature_dim:
                raise ValueError(
                    "context_features second dimension does not match "
                    f"context_feature_dim={self.context_feature_dim}"
                )
            features = context_features
        else:
            raise ValueError("context_features must have shape [context_dim] or [1, context_dim]")
        features = features.to(device=device, dtype=dtype)
        _assert_finite(features, "context_features")
        embedding = self.encoder(features).squeeze(0)
        _assert_finite(embedding, "context embedding")
        return embedding


class BatchImpactEncoder(nn.Module):
    """Pool candidate embeddings into a batch-level representation."""

    def __init__(
        self,
        *,
        candidate_hidden_dim: int,
        batch_feature_dim: int = 0,
        batch_hidden_dim: int = 128,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        if int(candidate_hidden_dim) <= 0:
            raise ValueError("candidate_hidden_dim must be positive")
        if int(batch_feature_dim) < 0:
            raise ValueError("batch_feature_dim must be non-negative")
        if int(batch_hidden_dim) <= 0:
            raise ValueError("batch_hidden_dim must be positive")
        self.candidate_hidden_dim = int(candidate_hidden_dim)
        self.batch_feature_dim = int(batch_feature_dim)
        self.batch_hidden_dim = int(batch_hidden_dim)
        input_dim = 3 * self.candidate_hidden_dim + self.batch_feature_dim + 1
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, self.batch_hidden_dim),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(self.batch_hidden_dim, self.batch_hidden_dim),
            nn.ReLU(),
        )

    def forward(
        self,
        candidate_embeddings: Tensor,
        *,
        candidate_mask: Optional[Tensor] = None,
        batch_features: Optional[Tensor] = None,
    ) -> Dict[str, Tensor]:
        if candidate_embeddings.dim() != 2 or candidate_embeddings.size(1) != self.candidate_hidden_dim:
            raise ValueError(
                "candidate_embeddings must have shape "
                f"[num_candidates, {self.candidate_hidden_dim}]"
            )
        _assert_finite(candidate_embeddings, "candidate_embeddings")
        if candidate_mask is None:
            mask = torch.ones(
                candidate_embeddings.size(0),
                dtype=torch.bool,
                device=candidate_embeddings.device,
            )
        else:
            if candidate_mask.dim() != 1 or candidate_mask.size(0) != candidate_embeddings.size(0):
                raise ValueError("candidate_mask must have one value per candidate")
            mask = candidate_mask.to(device=candidate_embeddings.device, dtype=torch.bool)
        if not bool(torch.any(mask)):
            raise ValueError("candidate_mask must select at least one candidate")

        selected = candidate_embeddings[mask]
        mean_pool = selected.mean(dim=0)
        max_pool = selected.max(dim=0).values
        std_pool = _safe_sqrt_zero_forward(((selected - mean_pool) ** 2).mean(dim=0))
        selected_count = candidate_embeddings.new_tensor([float(selected.size(0))])
        feature_row = _batch_feature_row(
            batch_features=batch_features,
            batch_feature_dim=self.batch_feature_dim,
            device=candidate_embeddings.device,
            dtype=candidate_embeddings.dtype,
        )
        encoder_input = torch.cat([mean_pool, max_pool, std_pool, feature_row, selected_count], dim=0)
        _assert_finite(encoder_input, "batch encoder input")
        embedding = self.encoder(encoder_input.unsqueeze(0)).squeeze(0)
        _assert_finite(embedding, "batch embedding")
        return {
            "batch_embedding": embedding,
            "batch_candidate_count": selected_count.squeeze(0),
            "batch_mean_pool": mean_pool,
            "batch_max_pool": max_pool,
            "batch_std_pool": std_pool,
        }


class GATBatchImpactModel(nn.Module):
    """Predict candidate admission and batch-level RMP trajectory impact."""

    def __init__(
        self,
        *,
        node_dim: int,
        option_dim: int,
        candidate_feature_dim: int,
        context_feature_dim: int,
        batch_feature_dim: int = 0,
        hidden_dim: int = 128,
        option_hidden_dim: int = 128,
        pair_edge_dim: int = 128,
        num_gnn_layers: int = 2,
        heads: int = 4,
        dropout: float = 0.1,
        candidate_hidden_dim: int = 128,
        context_hidden_dim: int = 64,
        batch_hidden_dim: int = 128,
        impact_hidden_dim: int = 128,
        use_layer_norm: bool = True,
    ) -> None:
        super().__init__()
        if int(impact_hidden_dim) <= 0:
            raise ValueError("impact_hidden_dim must be positive")
        self.candidate_feature_dim = int(candidate_feature_dim)
        self.context_feature_dim = int(context_feature_dim)
        self.batch_feature_dim = int(batch_feature_dim)
        self.candidate_hidden_dim = int(candidate_hidden_dim)
        self.context_hidden_dim = int(context_hidden_dim)
        self.batch_hidden_dim = int(batch_hidden_dim)
        self.impact_hidden_dim = int(impact_hidden_dim)
        self.exactness_contract = dict(BATCH_IMPACT_EXACTNESS_CONTRACT)

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
        self.candidate_encoder = JourneyCandidateEncoder(
            graph_hidden_dim=int(hidden_dim),
            candidate_feature_dim=self.candidate_feature_dim,
            candidate_hidden_dim=self.candidate_hidden_dim,
            dropout=float(dropout),
        )
        self.context_encoder = RMPContextEncoder(
            context_feature_dim=self.context_feature_dim,
            context_hidden_dim=self.context_hidden_dim,
            dropout=float(dropout),
        )
        self.batch_encoder = BatchImpactEncoder(
            candidate_hidden_dim=self.candidate_hidden_dim,
            batch_feature_dim=self.batch_feature_dim,
            batch_hidden_dim=self.batch_hidden_dim,
            dropout=float(dropout),
        )

        candidate_decision_dim = self.candidate_hidden_dim + self.batch_hidden_dim + self.context_hidden_dim
        batch_decision_dim = self.batch_hidden_dim + self.context_hidden_dim
        self.high_priority_head = _mlp_head(candidate_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.delay_risk_head = _mlp_head(candidate_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.batch_roi_positive_head = _mlp_head(batch_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.objective_progress_head = _mlp_head(batch_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.tail_improved_head = _mlp_head(batch_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.bad_mode_switch_head = _mlp_head(batch_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.support_changed_good_head = _mlp_head(batch_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.delta_v_head = _mlp_head(batch_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.barrier_slack_head = _mlp_head(batch_decision_dim, self.impact_hidden_dim, dropout=float(dropout))
        self.accepted_batch_roi_head = _mlp_head(batch_decision_dim, self.impact_hidden_dim, dropout=float(dropout))

    def forward(
        self,
        data: Any,
        candidate_task_membership: Tensor,
        candidate_sequence_positions: Tensor,
        candidate_features: Tensor,
        context_features: Tensor,
        *,
        candidate_mask: Optional[Tensor] = None,
        batch_features: Optional[Tensor] = None,
    ) -> Dict[str, Tensor]:
        encoded = self.graph_encoder.encode(data)
        task_h = encoded["task_h"]
        initial_task_h = encoded["initial_task_h"]
        candidate_output = self.candidate_encoder(
            task_h=task_h,
            initial_task_h=initial_task_h,
            candidate_task_membership=candidate_task_membership,
            candidate_sequence_positions=candidate_sequence_positions,
            candidate_features=candidate_features,
        )
        candidate_embedding = candidate_output["candidate_embedding"]
        context_embedding = self.context_encoder(
            context_features,
            device=candidate_embedding.device,
            dtype=candidate_embedding.dtype,
        )
        batch_output = self.batch_encoder(
            candidate_embedding,
            candidate_mask=candidate_mask,
            batch_features=batch_features,
        )
        batch_embedding = batch_output["batch_embedding"]

        context_for_candidates = context_embedding.unsqueeze(0).expand(candidate_embedding.size(0), -1)
        batch_for_candidates = batch_embedding.unsqueeze(0).expand(candidate_embedding.size(0), -1)
        candidate_decision_input = torch.cat(
            [candidate_embedding, batch_for_candidates, context_for_candidates],
            dim=-1,
        )
        batch_decision_input = torch.cat([batch_embedding, context_embedding], dim=-1).unsqueeze(0)

        high_priority_logit = self.high_priority_head(candidate_decision_input).squeeze(-1)
        delay_risk_logit = self.delay_risk_head(candidate_decision_input).squeeze(-1)
        batch_roi_positive_logit = self.batch_roi_positive_head(batch_decision_input).squeeze(-1)
        objective_progress_logit = self.objective_progress_head(batch_decision_input).squeeze(-1)
        tail_improved_logit = self.tail_improved_head(batch_decision_input).squeeze(-1)
        bad_mode_switch_logit = self.bad_mode_switch_head(batch_decision_input).squeeze(-1)
        support_changed_good_logit = self.support_changed_good_head(batch_decision_input).squeeze(-1)
        predicted_delta_v = self.delta_v_head(batch_decision_input).squeeze(-1)
        predicted_barrier_slack = self.barrier_slack_head(batch_decision_input).squeeze(-1)
        predicted_accepted_batch_roi = self.accepted_batch_roi_head(batch_decision_input).squeeze(-1)

        outputs: Dict[str, Tensor] = {
            "candidate_embedding": candidate_embedding,
            "batch_embedding": batch_embedding,
            "context_embedding": context_embedding,
            "task_counts": candidate_output["task_counts"],
            "order_span": candidate_output["order_span"],
            "batch_candidate_count": batch_output["batch_candidate_count"],
            "high_priority_logit": high_priority_logit,
            "high_priority_probability": torch.sigmoid(high_priority_logit),
            "delay_risk_logit": delay_risk_logit,
            "delay_risk_probability": torch.sigmoid(delay_risk_logit),
            "batch_roi_positive_logit": batch_roi_positive_logit,
            "batch_roi_positive_probability": torch.sigmoid(batch_roi_positive_logit),
            "objective_progress_logit": objective_progress_logit,
            "objective_progress_probability": torch.sigmoid(objective_progress_logit),
            "tail_improved_logit": tail_improved_logit,
            "tail_improved_probability": torch.sigmoid(tail_improved_logit),
            "bad_mode_switch_logit": bad_mode_switch_logit,
            "bad_mode_switch_probability": torch.sigmoid(bad_mode_switch_logit),
            "support_changed_good_logit": support_changed_good_logit,
            "support_changed_good_probability": torch.sigmoid(support_changed_good_logit),
            "predicted_delta_v": predicted_delta_v,
            "predicted_barrier_slack": predicted_barrier_slack,
            "predicted_accepted_batch_roi": predicted_accepted_batch_roi,
        }
        for name, value in outputs.items():
            _assert_finite(value, name)
        return outputs


def batch_impact_exactness_contract() -> Dict[str, bool]:
    """Return a copy of the exactness contract for checkpoint metadata."""

    return dict(BATCH_IMPACT_EXACTNESS_CONTRACT)


def _mlp_head(input_dim: int, hidden_dim: int, *, dropout: float) -> nn.Sequential:
    return nn.Sequential(
        nn.Linear(int(input_dim), int(hidden_dim)),
        nn.ReLU(),
        nn.Dropout(float(dropout)),
        nn.Linear(int(hidden_dim), 1),
    )


def _batch_feature_row(
    *,
    batch_features: Optional[Tensor],
    batch_feature_dim: int,
    device: torch.device,
    dtype: torch.dtype,
) -> Tensor:
    if int(batch_feature_dim) == 0:
        if batch_features is not None and batch_features.numel() != 0:
            raise ValueError("batch_features must be omitted or empty when batch_feature_dim=0")
        return torch.empty(0, device=device, dtype=dtype)
    if batch_features is None:
        raise ValueError("batch_features are required when batch_feature_dim > 0")
    if batch_features.dim() == 1:
        if batch_features.numel() != int(batch_feature_dim):
            raise ValueError(f"batch_features length must be {batch_feature_dim}")
        row = batch_features
    elif batch_features.dim() == 2 and batch_features.size(0) == 1:
        if batch_features.size(1) != int(batch_feature_dim):
            raise ValueError(f"batch_features second dimension must be {batch_feature_dim}")
        row = batch_features.squeeze(0)
    else:
        raise ValueError("batch_features must have shape [batch_feature_dim] or [1, batch_feature_dim]")
    row = row.to(device=device, dtype=dtype)
    _assert_finite(row, "batch_features")
    return row


def _assert_finite(tensor: Tensor, name: str) -> None:
    if not bool(torch.all(torch.isfinite(tensor))):
        raise ValueError(f"{name} contains NaN or Inf")


def _safe_sqrt_zero_forward(var: Tensor, *, eps: float = 1.0e-8) -> Tensor:
    """Return sqrt(var) while keeping the zero-variance backward finite."""

    return torch.sqrt(torch.clamp(var, min=0.0) + float(eps)) - float(eps) ** 0.5
