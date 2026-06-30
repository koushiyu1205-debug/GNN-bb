"""Completion-bound helpers for direct-label journey pricing.

The bound here is deliberately narrow: it only uses task-cover dual rewards.
Fleet, cut, and branch duals are applied outside this bound so the artifact can
later be reused in the true-dual pricing tail without mixing proof terms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class PositiveCoverCompletionBound:
    task_ids: tuple[str, ...]
    positive_cover_duals: Mapping[str, float]
    dual_source: str = "task_cover_duals"

    def remaining_lower_bound(self, remaining_task_ids: Iterable[str]) -> float:
        """Return an optimistic lower bound for future non-fleet RC terms."""

        value = -sum(
            max(0.0, float(self.positive_cover_duals.get(str(task_id), 0.0)))
            for task_id in remaining_task_ids
        )
        return round(value, 9)

    def optimistic_label_bound(
        self,
        *,
        current_reduced_base: float,
        current_end_time: float,
        beta_journey_end_time: float,
        remaining_task_ids: Iterable[str],
    ) -> float:
        """Bound any extension of a label, excluding the fleet dual term."""

        return round(
            float(current_reduced_base)
            + float(beta_journey_end_time) * max(0.0, float(current_end_time))
            + self.remaining_lower_bound(remaining_task_ids),
            9,
        )

    def to_payload(self) -> dict:
        return {
            "schema_version": "lunar_ice_bpc.completion_bound.v1",
            "bound_type": "positive_cover_dual_optimistic_tail",
            "dual_source": self.dual_source,
            "task_count": len(self.task_ids),
            "positive_cover_dual_sum": round(sum(self.positive_cover_duals.values()), 9),
            "includes_fleet_dual": False,
            "includes_cut_duals": False,
            "includes_branch_duals": False,
            "pruning_is_exact_safe": True,
            "can_certify_no_negative": False,
            "note": (
                "Optimistic completion bound for label pruning only; official "
                "no-negative certificates still require complete true-dual pricing."
            ),
        }


def build_positive_cover_completion_bound(
    task_ids: Iterable[str],
    cover_duals: Mapping[str, float],
    *,
    dual_source: str = "task_cover_duals",
) -> PositiveCoverCompletionBound:
    ordered = tuple(sorted(str(task_id) for task_id in task_ids))
    positive = {
        task_id: max(0.0, float(cover_duals.get(task_id, 0.0)))
        for task_id in ordered
    }
    return PositiveCoverCompletionBound(
        task_ids=ordered,
        positive_cover_duals=positive,
        dual_source=str(dual_source),
    )
