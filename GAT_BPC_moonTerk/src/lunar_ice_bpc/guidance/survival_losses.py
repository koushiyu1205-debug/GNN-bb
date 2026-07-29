"""Right-censored likelihoods shared by exact-safe guidance experiments.

This module contains no scalar branch-cost construction.  In particular, it
does not expose the historical four-coefficient P0 V2 branch target.  The P0
V3 branch experiment imports its child-survival auxiliary loss from here so
that its end-to-end ranking target cannot be confused with that legacy cost.
"""

from __future__ import annotations

import torch
from torch.nn import functional as F


def discrete_time_survival_nll(
    hazard_logits: torch.Tensor,
    candidate_indices: torch.Tensor,
    observed_time_fraction: torch.Tensor,
    event_observed: torch.Tensor,
) -> torch.Tensor:
    """Right-censored discrete hazard likelihood for an observed event.

    ``observed_time_fraction`` is measured on ``(0, 1]`` relative to the
    matched budget. For an event, the event interval contributes a hazard
    term; for an incomplete observation, only the observed survival intervals
    contribute. No timeout penalty or fabricated terminal cost is introduced.
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
