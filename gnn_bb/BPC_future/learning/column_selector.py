"""Context-aware GNN column impact scheduler.

This module is learning-side only.  It can rank or schedule candidate journeys
before they are offered to the RMP, but it is not a pricing oracle and must not
participate in official lower bounds, no-negative certificates, or branch
decisions.  In exact-safe use, true-RC negative candidates that are not
prioritized must remain in a delay queue rather than being discarded.  Every
selected candidate still has to pass the existing TimedTrip/JourneyColumn
materialization and true reduced-cost checks.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:  # pragma: no cover - import failure path is environment-dependent.
    import torch
    from torch import Tensor, nn
    import torch.nn.functional as F
except Exception as exc:  # pragma: no cover
    raise ImportError(
        "BPC_future.learning.column_selector requires torch. "
        "Install the learning stack before using the selector."
    ) from exc

from BPC_future.learning.gnn_model import HierarchicalOptionGAT


SELECTOR_CLASS_SKIP = 0
SELECTOR_CLASS_ADD = 1
SELECTOR_CLASS_ABSTAIN = 2
SELECTOR_CLASS_NAMES: tuple[str, str, str] = ("skip", "add", "abstain")

# Production-facing scheduler names.  The legacy class ids are kept for
# checkpoint compatibility, but the exact-safe integration must not interpret
# "skip" as permission to discard a true-RC negative column.
SELECTOR_CLASS_REJECT_NONNEGATIVE_ONLY = SELECTOR_CLASS_SKIP
SELECTOR_CLASS_HIGH_PRIORITY = SELECTOR_CLASS_ADD
SELECTOR_CLASS_DELAY_QUEUE = SELECTOR_CLASS_ABSTAIN
SCHEDULER_DECISION_NAMES: tuple[str, str, str] = (
    "REJECT_NONNEGATIVE_ONLY",
    "HIGH_PRIORITY",
    "DELAY_QUEUE",
)


class ContextAwareColumnSelector(nn.Module):
    """Predict add/skip/abstain logits for candidate journey columns.

    The model reuses the existing logical-graph GNN encoder, then pools task
    embeddings for each candidate by its task-membership mask.  Candidate-local
    features and RMP/context features are concatenated with the pooled embedding.

    Expected inputs:
    - ``data``: the same PyG graph accepted by ``HierarchicalOptionGAT``;
    - ``candidate_task_membership``: ``[num_candidates, num_tasks]`` bool/float
      matrix over ``data.task_mask`` task order;
    - ``candidate_features``: ``[num_candidates, candidate_feature_dim]``;
    - ``context_features``: either ``[context_feature_dim]`` for one shared RMP
      context or ``[num_candidates, context_feature_dim]``.
    """

    def __init__(
        self,
        *,
        node_dim: int,
        option_dim: int,
        candidate_feature_dim: int,
        context_feature_dim: int,
        hidden_dim: int = 128,
        option_hidden_dim: int = 128,
        pair_edge_dim: int = 128,
        num_gnn_layers: int = 2,
        heads: int = 4,
        dropout: float = 0.1,
        selector_hidden_dim: int = 128,
        use_layer_norm: bool = True,
    ) -> None:
        super().__init__()
        if int(candidate_feature_dim) <= 0:
            raise ValueError("candidate_feature_dim must be positive")
        if int(context_feature_dim) <= 0:
            raise ValueError("context_feature_dim must be positive")
        if int(selector_hidden_dim) <= 0:
            raise ValueError("selector_hidden_dim must be positive")

        self.candidate_feature_dim = int(candidate_feature_dim)
        self.context_feature_dim = int(context_feature_dim)
        self.hidden_dim = int(hidden_dim)
        self.selector_hidden_dim = int(selector_hidden_dim)
        self.encoder = HierarchicalOptionGAT(
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
        selector_input_dim = (
            2 * int(hidden_dim)
            + int(candidate_feature_dim)
            + int(context_feature_dim)
            + 1
        )
        self.selector_mlp = nn.Sequential(
            nn.Linear(selector_input_dim, int(selector_hidden_dim)),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(selector_hidden_dim), int(selector_hidden_dim)),
            nn.ReLU(),
            nn.Dropout(float(dropout)),
            nn.Linear(int(selector_hidden_dim), len(SELECTOR_CLASS_NAMES)),
        )

    def forward(
        self,
        data: Any,
        candidate_task_membership: Tensor,
        candidate_features: Tensor,
        context_features: Tensor,
    ) -> Dict[str, Tensor]:
        self._validate_candidate_inputs(
            data=data,
            candidate_task_membership=candidate_task_membership,
            candidate_features=candidate_features,
            context_features=context_features,
        )
        encoded = self.encoder.encode(data)
        task_h = encoded["task_h"]
        initial_task_h = encoded["initial_task_h"]

        membership = candidate_task_membership.to(
            device=task_h.device,
            dtype=task_h.dtype,
        )
        candidate_features = candidate_features.to(
            device=task_h.device,
            dtype=task_h.dtype,
        )
        context = _broadcast_context_features(
            context_features.to(device=task_h.device, dtype=task_h.dtype),
            num_candidates=int(membership.size(0)),
            context_feature_dim=self.context_feature_dim,
        )

        task_counts = membership.sum(dim=1, keepdim=True)
        if bool(torch.any(task_counts <= 0)):
            raise ValueError("each candidate must cover at least one task")
        pooled_task = membership @ task_h / task_counts
        pooled_initial_task = membership @ initial_task_h / task_counts

        selector_input = torch.cat(
            [
                pooled_task,
                pooled_initial_task,
                candidate_features,
                context,
                task_counts,
            ],
            dim=-1,
        )
        _assert_finite(selector_input, "selector input")
        logits = self.selector_mlp(selector_input)
        _assert_finite(logits, "selector logits")
        probabilities = F.softmax(logits, dim=-1)
        return {
            "logits": logits,
            "probabilities": probabilities,
            "add_probability": probabilities[:, SELECTOR_CLASS_ADD],
            "skip_probability": probabilities[:, SELECTOR_CLASS_SKIP],
            "abstain_probability": probabilities[:, SELECTOR_CLASS_ABSTAIN],
            "high_priority_probability": probabilities[:, SELECTOR_CLASS_HIGH_PRIORITY],
            "trajectory_impact_probability": probabilities[:, SELECTOR_CLASS_HIGH_PRIORITY],
            "reject_nonnegative_probability": probabilities[
                :, SELECTOR_CLASS_REJECT_NONNEGATIVE_ONLY
            ],
            "delay_queue_probability": probabilities[:, SELECTOR_CLASS_DELAY_QUEUE],
            "candidate_embedding": pooled_task,
            "task_counts": task_counts.squeeze(-1),
        }

    def _validate_candidate_inputs(
        self,
        *,
        data: Any,
        candidate_task_membership: Tensor,
        candidate_features: Tensor,
        context_features: Tensor,
    ) -> None:
        task_mask = getattr(data, "task_mask")
        if candidate_task_membership.dim() != 2:
            raise ValueError("candidate_task_membership must have shape [num_candidates, num_tasks]")
        if candidate_features.dim() != 2:
            raise ValueError("candidate_features must have shape [num_candidates, candidate_feature_dim]")
        if candidate_features.size(1) != self.candidate_feature_dim:
            raise ValueError(
                "candidate_features second dimension does not match "
                f"candidate_feature_dim={self.candidate_feature_dim}"
            )
        if candidate_features.size(0) != candidate_task_membership.size(0):
            raise ValueError("candidate_features and candidate_task_membership must have the same row count")
        if int(candidate_task_membership.size(1)) != int(task_mask.sum().item()):
            raise ValueError("candidate_task_membership width must equal the number of task nodes")
        if context_features.dim() not in {1, 2}:
            raise ValueError("context_features must have shape [context_dim] or [num_candidates, context_dim]")
        _assert_finite(candidate_task_membership, "candidate_task_membership")
        _assert_finite(candidate_features, "candidate_features")
        _assert_finite(context_features, "context_features")


def column_selector_loss(
    logits: Tensor,
    labels: Tensor,
    class_weights: Optional[Tensor] = None,
) -> Tensor:
    """Cross-entropy loss for skip/add/abstain selector targets."""

    if logits.dim() != 2 or logits.size(1) != len(SELECTOR_CLASS_NAMES):
        raise ValueError("logits must have shape [num_candidates, 3]")
    if labels.dim() != 1 or labels.size(0) != logits.size(0):
        raise ValueError("labels must have shape [num_candidates]")
    if labels.dtype != torch.long:
        labels = labels.long()
    if bool(torch.any(labels < 0)) or bool(torch.any(labels >= len(SELECTOR_CLASS_NAMES))):
        raise ValueError("labels contain class ids outside selector class range")
    _assert_finite(logits, "selector logits")
    return F.cross_entropy(logits, labels, weight=class_weights)


def conservative_add_decisions(
    probabilities: Tensor,
    *,
    add_threshold: float = 0.9,
    add_margin: float = 0.0,
) -> Tensor:
    """Return ADD or ABSTAIN decisions from selector probabilities.

    This helper is intended for exact-safe integration: the learned model may
    nominate candidates for addition, but every non-nominated candidate remains
    ``ABSTAIN`` so the solver can continue through its existing exact path.
    It never certifies no-column and never forces a candidate to be discarded.
    """

    if probabilities.dim() != 2 or probabilities.size(1) != len(SELECTOR_CLASS_NAMES):
        raise ValueError("probabilities must have shape [num_candidates, 3]")
    _assert_finite(probabilities, "selector probabilities")
    threshold = float(add_threshold)
    margin = max(0.0, float(add_margin))
    add_prob = probabilities[:, SELECTOR_CLASS_ADD]
    non_add = torch.stack(
        [
            probabilities[:, SELECTOR_CLASS_SKIP],
            probabilities[:, SELECTOR_CLASS_ABSTAIN],
        ],
        dim=1,
    ).max(dim=1).values
    should_add = (add_prob >= threshold) & ((add_prob - non_add) >= margin)
    decisions = torch.full(
        (probabilities.size(0),),
        SELECTOR_CLASS_ABSTAIN,
        dtype=torch.long,
        device=probabilities.device,
    )
    decisions[should_add] = SELECTOR_CLASS_ADD
    return decisions


def conservative_high_priority_decisions(
    probabilities: Tensor,
    *,
    high_priority_threshold: float = 0.9,
    high_priority_margin: float = 0.0,
) -> Tensor:
    """Return HIGH_PRIORITY or DELAY_QUEUE for true-RC negative candidates.

    This is the exact-safe scheduler view of ``conservative_add_decisions``:
    candidates that do not clear the stability threshold are delayed, not
    discarded.  Callers must separately verify true reduced cost.
    """

    return conservative_add_decisions(
        probabilities,
        add_threshold=float(high_priority_threshold),
        add_margin=float(high_priority_margin),
    )


def exact_safe_negative_scheduler_decisions(
    probabilities: Tensor,
    true_rc_negative_mask: Tensor,
    *,
    high_priority_threshold: float = 0.9,
    high_priority_margin: float = 0.0,
) -> Tensor:
    """Map candidates to HIGH_PRIORITY / DELAY_QUEUE / REJECT_NONNEGATIVE_ONLY.

    True-RC negative candidates are never permanently rejected by this helper:
    they either become HIGH_PRIORITY or remain in DELAY_QUEUE.  Only candidates
    that fail the true-RC-negative mask can be assigned
    REJECT_NONNEGATIVE_ONLY.
    """

    if true_rc_negative_mask.dim() != 1 or true_rc_negative_mask.size(0) != probabilities.size(0):
        raise ValueError("true_rc_negative_mask must have one value per candidate")
    high_or_delay = conservative_high_priority_decisions(
        probabilities,
        high_priority_threshold=float(high_priority_threshold),
        high_priority_margin=float(high_priority_margin),
    )
    negative_mask = true_rc_negative_mask.to(
        device=probabilities.device,
        dtype=torch.bool,
    )
    decisions = torch.full(
        (probabilities.size(0),),
        SELECTOR_CLASS_REJECT_NONNEGATIVE_ONLY,
        dtype=torch.long,
        device=probabilities.device,
    )
    decisions[negative_mask] = SELECTOR_CLASS_DELAY_QUEUE
    decisions[negative_mask & (high_or_delay == SELECTOR_CLASS_HIGH_PRIORITY)] = (
        SELECTOR_CLASS_HIGH_PRIORITY
    )
    return decisions


def _broadcast_context_features(
    context_features: Tensor,
    *,
    num_candidates: int,
    context_feature_dim: int,
) -> Tensor:
    if context_features.dim() == 1:
        if context_features.numel() != int(context_feature_dim):
            raise ValueError(
                f"context_features length must be {context_feature_dim}, got {context_features.numel()}"
            )
        return context_features.unsqueeze(0).expand(int(num_candidates), -1)
    if context_features.size(1) != int(context_feature_dim):
        raise ValueError(
            "context_features second dimension does not match "
            f"context_feature_dim={context_feature_dim}"
        )
    if context_features.size(0) != int(num_candidates):
        raise ValueError("batched context_features must have one row per candidate")
    return context_features


def _assert_finite(tensor: Tensor, name: str) -> None:
    if not bool(torch.all(torch.isfinite(tensor))):
        raise ValueError(f"{name} contains NaN or Inf")
