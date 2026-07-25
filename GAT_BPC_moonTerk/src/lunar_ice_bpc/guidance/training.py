"""Losses, censored labels, sampling order, and model promotion rules."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import isfinite, log1p
from typing import Any, Iterable, Iterator, Mapping

import torch
from torch.nn import functional as F


PRICING_GRADES = {
    "useful_negative": 4.0,
    "addable_negative": 3.0,
    "duplicate_negative": 1.0,
    "nonnegative_or_invalid": 0.0,
}
HEAD_SCALE_WEIGHTS = {
    "exact_pricing": {5: 1.0, 10: 1.0, 20: 1.0, 30: 1.0},
    "harvest": {5: 1.0, 10: 1.0, 20: 1.0, 30: 1.0, 50: 0.05, 100: 0.05},
    "proof_risk": {5: 1.0, 10: 1.0, 20: 1.0, 30: 1.0, 50: 1.0, 100: 1.0},
    "branch": {5: 1.0, 10: 1.0, 20: 1.0, 30: 1.0},
    "ood": {5: 1.0, 10: 1.0, 20: 1.0, 30: 1.0, 50: 1.0, 100: 1.0},
}


def pricing_grade(
    label: str, *, hidden_negative: bool = False
) -> float:
    grade = float(PRICING_GRADES[str(label)])
    return min(4.0, grade + (1.0 if hidden_negative else 0.0))


def graded_listwise_loss(
    scores: torch.Tensor,
    grades: torch.Tensor,
    group_ids: torch.Tensor,
) -> torch.Tensor:
    """ListNet-style loss computed only within the same RMP context."""

    losses = []
    for group_id in torch.unique(group_ids):
        mask = group_ids == group_id
        if int(mask.sum()) < 2:
            continue
        target = F.softmax(grades[mask], dim=0)
        prediction = F.log_softmax(scores[mask], dim=0)
        losses.append(-(target * prediction).sum())
    if not losses:
        return scores.sum() * 0.0
    return torch.stack(losses).mean()


def counterfactual_soft_listwise_loss(
    scores: torch.Tensor,
    target_probabilities: torch.Tensor,
    probe_mask: torch.Tensor,
) -> torch.Tensor:
    """Cross entropy against conservative paired action-value probabilities.

    Only actions that were actually run against the same P0 control enter the
    denominator.  The explicit P0_KEEP_ORDER action is always included; an
    unprobed legal candidate is never converted into a negative example.
    """

    flattened_scores = scores.reshape(-1)
    probabilities = target_probabilities.reshape(-1)
    mask = probe_mask.reshape(-1).bool()
    if not (
        flattened_scores.numel()
        == probabilities.numel()
        == mask.numel()
    ):
        raise ValueError("counterfactual listwise tensor length mismatch")
    if int(mask.sum()) < 2:
        return flattened_scores.sum() * 0.0
    selected_probabilities = probabilities[mask]
    if not bool(torch.isfinite(selected_probabilities).all()):
        raise ValueError("counterfactual targets must be finite")
    if bool((selected_probabilities < 0.0).any()):
        raise ValueError("counterfactual targets cannot be negative")
    probability_sum = selected_probabilities.sum()
    if not bool(torch.isfinite(probability_sum)) or float(
        probability_sum.detach()
    ) <= 0.0:
        raise ValueError("counterfactual target mass must be positive")
    selected_probabilities = selected_probabilities / probability_sum
    return -(
        selected_probabilities
        * F.log_softmax(flattened_scores[mask], dim=0)
    ).sum()


def masked_trajectory_regression_loss(
    predicted_advantage: torch.Tensor,
    observed_advantage: torch.Tensor,
    probe_mask: torch.Tensor,
) -> torch.Tensor:
    """Calibrate action scores to paired P0-relative trajectory advantage."""

    predicted = predicted_advantage.reshape(-1)
    observed = observed_advantage.reshape(-1)
    mask = probe_mask.reshape(-1).bool()
    if not (predicted.numel() == observed.numel() == mask.numel()):
        raise ValueError("trajectory regression tensor length mismatch")
    if not bool(mask.any()):
        return predicted.sum() * 0.0
    return F.smooth_l1_loss(predicted[mask], observed[mask])


def discrete_time_survival_nll(
    hazard_logits: torch.Tensor,
    candidate_indices: torch.Tensor,
    observed_time_fraction: torch.Tensor,
    event_observed: torch.Tensor,
) -> torch.Tensor:
    """Right-censored discrete hazard likelihood for first useful discovery.

    ``observed_time_fraction`` is measured on ``(0, 1]`` relative to the
    matched budget.  For an event, the event interval contributes a hazard
    term; for a timeout/incomplete observation, only the observed survival
    intervals contribute.  No fabricated timeout cost is introduced.
    """

    if hazard_logits.ndim != 2:
        raise ValueError("hazard logits must have shape [candidate, bin]")
    indices = candidate_indices.reshape(-1).long()
    fractions = observed_time_fraction.reshape(-1)
    observed = event_observed.reshape(-1).bool()
    if not (indices.numel() == fractions.numel() == observed.numel()):
        raise ValueError("survival observation tensor length mismatch")
    if indices.numel() == 0:
        return hazard_logits.sum() * 0.0
    if int(indices.min()) < 0 or int(indices.max()) >= hazard_logits.shape[0]:
        raise ValueError("survival candidate index is out of range")
    if not bool(torch.isfinite(fractions).all()) or bool(
        ((fractions <= 0.0) | (fractions > 1.0)).any()
    ):
        raise ValueError("survival time fractions must lie in (0, 1]")

    selected = hazard_logits[indices]
    bin_count = int(selected.shape[1])
    bins = torch.clamp(
        torch.ceil(fractions * float(bin_count)).long() - 1,
        min=0,
        max=bin_count - 1,
    )
    interval_ids = torch.arange(
        bin_count, device=selected.device
    ).expand(selected.shape[0], -1)
    before_event = interval_ids < bins[:, None]
    through_censor = interval_ids <= bins[:, None]
    survival_mask = torch.where(
        observed[:, None], before_event, through_censor
    )
    survival_loss = (
        F.softplus(selected) * survival_mask.to(selected.dtype)
    ).sum(dim=1)
    event_loss = torch.where(
        observed,
        F.softplus(-selected.gather(1, bins[:, None]).squeeze(1)),
        torch.zeros_like(fractions),
    )
    return (survival_loss + event_loss).mean()


def survival_concordance_loss(
    hazard_logits: torch.Tensor,
    candidate_indices: torch.Tensor,
    observed_time_fraction: torch.Tensor,
    event_observed: torch.Tensor,
) -> torch.Tensor:
    """Rank only survival pairs whose observation intervals are comparable."""

    if hazard_logits.ndim != 2:
        raise ValueError("hazard logits must have shape [candidate, bin]")
    indices = candidate_indices.reshape(-1).long()
    fractions = observed_time_fraction.reshape(-1)
    observed = event_observed.reshape(-1).bool()
    if indices.numel() < 2:
        return hazard_logits.sum() * 0.0
    selected = hazard_logits[indices]
    # Higher cumulative hazard means earlier predicted discovery.
    risk = F.softplus(selected).sum(dim=1)
    losses = []
    for left in range(indices.numel()):
        if not bool(observed[left]):
            continue
        for right in range(indices.numel()):
            if left == right:
                continue
            if int(indices[left]) == int(indices[right]):
                continue
            if float(fractions[left]) < float(fractions[right]):
                losses.append(F.softplus(-(risk[left] - risk[right])))
    if not losses:
        return hazard_logits.sum() * 0.0
    return torch.stack(losses).mean()


def branch_cost(
    left_work: float,
    right_work: float,
    normalized_imbalance: float,
) -> float:
    left = max(0.0, float(left_work))
    right = max(0.0, float(right_work))
    imbalance = max(0.0, float(normalized_imbalance))
    return (
        log1p(left + right)
        + 0.5 * log1p(max(left, right))
        + 0.25 * imbalance
    )


@dataclass(frozen=True)
class CensoredBranchObservation:
    observed_work_lower_bound: float
    censoring_time_sec: float
    censoring_memory_bytes: int
    left_status: str
    right_status: str
    exact: bool
    exact_branch_cost: float | None = None

    def __post_init__(self) -> None:
        if self.exact and self.exact_branch_cost is None:
            raise ValueError("exact branch observation requires exact_branch_cost")
        if not self.exact and self.exact_branch_cost is not None:
            raise ValueError("censored observation cannot carry a fabricated cost")


def strong_pairwise_branch_label(
    left: CensoredBranchObservation,
    right: CensoredBranchObservation,
) -> int | None:
    """Return -1/1 only when the observed intervals are actually separable."""

    if left.exact and right.exact:
        assert left.exact_branch_cost is not None
        assert right.exact_branch_cost is not None
        if left.exact_branch_cost == right.exact_branch_cost:
            return None
        return -1 if left.exact_branch_cost < right.exact_branch_cost else 1
    if left.exact and left.exact_branch_cost is not None:
        if left.exact_branch_cost < right.observed_work_lower_bound:
            return -1
    if right.exact and right.exact_branch_cost is not None:
        if right.exact_branch_cost < left.observed_work_lower_bound:
            return 1
    return None


def survival_ranking_loss(
    predicted_cost: torch.Tensor,
    observed_lower_bound: torch.Tensor,
    exact_mask: torch.Tensor,
) -> torch.Tensor:
    exact_loss = (
        F.smooth_l1_loss(
            predicted_cost[exact_mask],
            observed_lower_bound[exact_mask],
        )
        if bool(exact_mask.any())
        else predicted_cost.sum() * 0.0
    )
    censored_mask = ~exact_mask
    censored_loss = (
        F.relu(observed_lower_bound[censored_mask] - predicted_cost[censored_mask]).mean()
        if bool(censored_mask.any())
        else predicted_cost.sum() * 0.0
    )
    return exact_loss + 0.5 * censored_loss


class EMALossNormalizer:
    def __init__(self, decay: float = 0.95) -> None:
        self.decay = float(decay)
        self.scales: dict[str, float] = {}

    def normalized_sum(
        self, losses: Mapping[str, torch.Tensor]
    ) -> torch.Tensor:
        values = []
        for name, loss in losses.items():
            observed = max(1.0e-12, float(loss.detach().abs().cpu()))
            old = self.scales.get(name, observed)
            self.scales[name] = self.decay * old + (1.0 - self.decay) * observed
            values.append(loss / max(1.0e-12, self.scales[name]))
        if not values:
            raise ValueError("at least one head loss is required")
        return torch.stack(values).sum()


def gradient_cosine(left: torch.Tensor, right: torch.Tensor) -> float:
    denominator = float(left.norm() * right.norm())
    if denominator <= 0.0:
        return 0.0
    return float(torch.dot(left.flatten(), right.flatten()) / denominator)


def should_enable_pcgrad(
    validation_cosines: Iterable[float],
    *,
    threshold: float = -0.2,
    consecutive: int = 3,
) -> bool:
    values = tuple(float(value) for value in validation_cosines)
    return len(values) >= consecutive and all(
        value < threshold for value in values[-consecutive:]
    )


def pcgrad_project(gradients: list[torch.Tensor]) -> list[torch.Tensor]:
    projected = [gradient.clone() for gradient in gradients]
    for left_index, left in enumerate(projected):
        for right_index, right in enumerate(gradients):
            if left_index == right_index:
                continue
            dot = torch.dot(left.flatten(), right.flatten())
            if float(dot) < 0.0:
                denominator = torch.dot(right.flatten(), right.flatten()).clamp_min(
                    1.0e-12
                )
                left = left - dot / denominator * right
        projected[left_index] = left
    return projected


def iter_head_scale_groups(
    rows: Iterable[Mapping[str, Any]],
) -> Iterator[tuple[str, int, tuple[Mapping[str, Any], ...]]]:
    """Enforce head -> scale -> instance -> context -> candidate sampling."""

    grouped: dict[
        tuple[str, int, str, str, str, str], list[Mapping[str, Any]]
    ] = defaultdict(list)
    for row in rows:
        key = (
            str(row["head"]),
            int(row["scale"]),
            str(row["instance_content_hash"]),
            str(row.get("node_phase") or ""),
            str(row.get("rmp_context_hash") or ""),
            str(row.get("candidate_id") or ""),
        )
        grouped[key].append(row)
    by_head_scale: dict[tuple[str, int], list[Mapping[str, Any]]] = defaultdict(list)
    for key in sorted(grouped):
        head, scale, *_ = key
        # Multiple raw observations of one candidate remain one sampling unit.
        by_head_scale[(head, scale)].append(grouped[key][0])
    for head, scale in sorted(by_head_scale):
        yield head, scale, tuple(by_head_scale[(head, scale)])


def model_selection_key(metrics: Mapping[str, Any]) -> tuple:
    """Lexicographic key; lower tuples are preferred."""

    safety_pass = bool(metrics.get("safety_gate_pass", False))
    small_scale_pass = bool(metrics.get("scale5_10_non_degradation", False))
    worst_lcb = float(metrics.get("worst_scale_bootstrap_lcb", float("-inf")))
    medium_gain = float(metrics.get("scale20_30_end_to_end_gain", float("-inf")))
    overhead = float(metrics.get("guidance_total_wall_sec", float("inf")))
    parameter_count = int(metrics.get("parameter_count", 2**63 - 1))
    return (
        0 if safety_pass else 1,
        0 if small_scale_pass else 1,
        -worst_lcb if isfinite(worst_lcb) else float("inf"),
        -medium_gain if isfinite(medium_gain) else float("inf"),
        overhead,
        parameter_count,
    )
