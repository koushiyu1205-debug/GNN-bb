"""Diagnostic exact branch-candidate probing for journey-column pools."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping

from lunar_ice_bpc.exact.core.branching import (
    DIFFERENT_JOURNEY,
    SAME_JOURNEY,
    BranchContext,
    PairBranchDecision,
    filter_journey_columns_by_branch_context,
)
from lunar_ice_bpc.exact.core.journey import JourneyColumn


@dataclass(frozen=True)
class BranchPairCandidate:
    task_a: str
    task_b: str
    together_column_count: int
    a_without_b_column_count: int
    b_without_a_column_count: int
    separated_column_count: int
    same_child_column_count: int
    different_child_column_count: int
    balance_score: int

    def to_payload(self) -> dict:
        same_context = BranchContext((PairBranchDecision(self.task_a, self.task_b, SAME_JOURNEY),))
        different_context = BranchContext((PairBranchDecision(self.task_a, self.task_b, DIFFERENT_JOURNEY),))
        return {
            "task_a": self.task_a,
            "task_b": self.task_b,
            "together_column_count": self.together_column_count,
            "a_without_b_column_count": self.a_without_b_column_count,
            "b_without_a_column_count": self.b_without_a_column_count,
            "separated_column_count": self.separated_column_count,
            "same_child_column_count": self.same_child_column_count,
            "different_child_column_count": self.different_child_column_count,
            "balance_score": self.balance_score,
            "same_child_context": same_context.to_payload(),
            "different_child_context": different_context.to_payload(),
        }


def build_branch_probe(
    task_ids: Iterable[str],
    columns: Iterable[JourneyColumn],
    *,
    max_candidates: int = 10,
) -> dict:
    """Return deterministic branch-pair diagnostics for a supplied column pool.

    This is not a fractional Ryan-Foster branch selector because the current
    restricted RMP scaffold does not expose primal fractional values. It only
    reports exact support in the supplied column pool and child contexts that a
    future branch-and-price node can apply.
    """

    ordered_tasks = tuple(sorted(str(task_id) for task_id in task_ids))
    pool = tuple(columns)
    candidates: list[BranchPairCandidate] = []
    for task_a, task_b in combinations(ordered_tasks, 2):
        together = 0
        a_without_b = 0
        b_without_a = 0
        for column in pool:
            tasks = {str(task_id) for task_id in column.task_set}
            has_a = task_a in tasks
            has_b = task_b in tasks
            if has_a and has_b:
                together += 1
            elif has_a:
                a_without_b += 1
            elif has_b:
                b_without_a += 1
        separated = a_without_b + b_without_a
        if together == 0 or separated == 0:
            continue
        same_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        different_context = BranchContext((PairBranchDecision(task_a, task_b, DIFFERENT_JOURNEY),))
        same_child_count = len(filter_journey_columns_by_branch_context(pool, same_context))
        different_child_count = len(filter_journey_columns_by_branch_context(pool, different_context))
        candidates.append(
            BranchPairCandidate(
                task_a=task_a,
                task_b=task_b,
                together_column_count=together,
                a_without_b_column_count=a_without_b,
                b_without_a_column_count=b_without_a,
                separated_column_count=separated,
                same_child_column_count=same_child_count,
                different_child_column_count=different_child_count,
                balance_score=min(together, separated),
            )
        )
    candidates.sort(
        key=lambda row: (
            -row.balance_score,
            abs(row.same_child_column_count - row.different_child_column_count),
            row.task_a,
            row.task_b,
        )
    )
    selected = candidates[: max(0, int(max_candidates))]
    return {
        "schema_version": "lunar_ice_bpc.branch_probe.v1",
        "status": "BRANCH_PROBE_READY" if selected else "NO_BRANCH_CANDIDATE",
        "candidate_count": len(candidates),
        "reported_candidate_count": len(selected),
        "column_pool_size": len(pool),
        "task_count": len(ordered_tasks),
        "candidates": [candidate.to_payload() for candidate in selected],
        "exact_status_effect": "none",
        "mutates_solver": False,
        "can_certify": False,
        "note": (
            "Diagnostic support-based branch probe over the supplied column pool. "
            "It does not use fractional primal values, mutate the solver, or certify bounds."
        ),
    }


def build_fractional_branch_probe(
    task_ids: Iterable[str],
    primal_columns: Iterable[Mapping[str, object]],
    columns: Iterable[JourneyColumn],
    *,
    max_candidates: int = 10,
    integer_eps: float = 1.0e-6,
) -> dict:
    """Return Ryan-Foster-style fractional pair diagnostics from RMP lambdas.

    The input lambdas come from the current restricted RMP diagnostic simplex.
    This can rank branch candidates for the supplied pool, but it is not an
    exact BPC proof artifact and cannot certify bounds.
    """

    ordered_tasks = tuple(sorted(str(task_id) for task_id in task_ids))
    pool = tuple(columns)
    lambda_rows = tuple(primal_columns)
    candidates: list[dict] = []
    for task_a, task_b in combinations(ordered_tasks, 2):
        same_fraction = 0.0
        support_column_count = 0
        for row in lambda_rows:
            tasks = {str(task_id) for task_id in row.get("tasks", []) or []}
            if task_a in tasks and task_b in tasks:
                same_fraction += float(row.get("lambda_value") or 0.0)
                support_column_count += 1
        if same_fraction <= abs(float(integer_eps)) or same_fraction >= 1.0 - abs(float(integer_eps)):
            continue
        same_context = BranchContext((PairBranchDecision(task_a, task_b, SAME_JOURNEY),))
        different_context = BranchContext((PairBranchDecision(task_a, task_b, DIFFERENT_JOURNEY),))
        candidates.append(
            {
                "task_a": task_a,
                "task_b": task_b,
                "same_fraction": round(float(same_fraction), 9),
                "fractionality": round(min(float(same_fraction), 1.0 - float(same_fraction)), 9),
                "support_column_count": support_column_count,
                "same_child_column_count": len(filter_journey_columns_by_branch_context(pool, same_context)),
                "different_child_column_count": len(filter_journey_columns_by_branch_context(pool, different_context)),
                "same_child_context": same_context.to_payload(),
                "different_child_context": different_context.to_payload(),
            }
        )
    candidates.sort(
        key=lambda row: (
            -float(row["fractionality"]),
            abs(int(row["same_child_column_count"]) - int(row["different_child_column_count"])),
            str(row["task_a"]),
            str(row["task_b"]),
        )
    )
    selected = candidates[: max(0, int(max_candidates))]
    return {
        "schema_version": "lunar_ice_bpc.fractional_branch_probe.v1",
        "status": "FRACTIONAL_BRANCH_PROBE_READY" if selected else "NO_FRACTIONAL_BRANCH_CANDIDATE",
        "candidate_count": len(candidates),
        "reported_candidate_count": len(selected),
        "column_pool_size": len(pool),
        "primal_column_count": len(lambda_rows),
        "task_count": len(ordered_tasks),
        "integer_eps": float(integer_eps),
        "candidates": selected,
        "exact_status_effect": "none",
        "mutates_solver": False,
        "can_certify": False,
        "note": (
            "Diagnostic Ryan-Foster fractional pair probe over restricted RMP primal lambdas. "
            "It ranks branch candidates but cannot certify bounds or no-negative pricing."
        ),
    }
