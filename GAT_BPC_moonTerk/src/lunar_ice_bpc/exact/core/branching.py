"""Exact branch-context helpers for journey columns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from lunar_ice_bpc.exact.core.journey import JourneyColumn


SAME_JOURNEY = "same_journey"
DIFFERENT_JOURNEY = "different_journey"
BRANCH_SENSES = (SAME_JOURNEY, DIFFERENT_JOURNEY)


@dataclass(frozen=True)
class PairBranchDecision:
    """Ryan-Foster-style decision on whether two tasks share one journey."""

    task_a: str
    task_b: str
    sense: str

    def __post_init__(self) -> None:
        if str(self.task_a) == str(self.task_b):
            raise ValueError("branch task pair must contain two distinct tasks")
        if str(self.sense) not in BRANCH_SENSES:
            raise ValueError(f"unsupported branch sense {self.sense!r}")

    @property
    def key(self) -> tuple[str, str, str]:
        a, b = sorted((str(self.task_a), str(self.task_b)))
        return a, b, str(self.sense)

    def to_payload(self) -> dict:
        a, b, sense = self.key
        return {"task_a": a, "task_b": b, "sense": sense}


@dataclass(frozen=True)
class BranchContext:
    """Immutable exact branch context carried by a future BPC node."""

    pair_decisions: tuple[PairBranchDecision, ...] = tuple()

    def __post_init__(self) -> None:
        seen: dict[tuple[str, str], str] = {}
        for decision in self.pair_decisions:
            a, b, sense = decision.key
            old = seen.get((a, b))
            if old is not None and old != sense:
                raise ValueError(f"conflicting branch decisions for pair {(a, b)}")
            seen[(a, b)] = sense

    @property
    def empty(self) -> bool:
        return not self.pair_decisions

    def to_payload(self) -> dict:
        return {
            "schema_version": "lunar_ice_bpc.branch_context.v1",
            "pair_decision_count": len(self.pair_decisions),
            "pair_decisions": [decision.to_payload() for decision in self.pair_decisions],
            "note": "Exact branch feasibility context; guidance may rank candidates but cannot change these decisions.",
        }


def pair_same_journey_indicator(column: JourneyColumn, task_a: str, task_b: str) -> int:
    task_set = {str(task_id) for task_id in column.task_set}
    return int(str(task_a) in task_set and str(task_b) in task_set)


def journey_violates_pair_decision(column: JourneyColumn, decision: PairBranchDecision) -> bool:
    task_set = {str(task_id) for task_id in column.task_set}
    has_a = str(decision.task_a) in task_set
    has_b = str(decision.task_b) in task_set
    if decision.sense == SAME_JOURNEY:
        return has_a != has_b
    if decision.sense == DIFFERENT_JOURNEY:
        return has_a and has_b
    raise ValueError(f"unsupported branch sense {decision.sense!r}")


def journey_branch_violations(column: JourneyColumn, context: BranchContext) -> tuple[dict, ...]:
    violations: list[dict] = []
    for decision in context.pair_decisions:
        if journey_violates_pair_decision(column, decision):
            violations.append(decision.to_payload())
    return tuple(violations)


def journey_satisfies_branch_context(column: JourneyColumn, context: BranchContext | None) -> bool:
    if context is None or context.empty:
        return True
    return not journey_branch_violations(column, context)


def filter_journey_columns_by_branch_context(
    columns: Iterable[JourneyColumn],
    context: BranchContext | None,
) -> tuple[JourneyColumn, ...]:
    return tuple(column for column in columns if journey_satisfies_branch_context(column, context))


def branch_context_from_payload(payload: dict | None) -> BranchContext:
    if not payload:
        return BranchContext()
    decisions = []
    for row in payload.get("pair_decisions", []) or []:
        decisions.append(
            PairBranchDecision(
                task_a=str(row["task_a"]),
                task_b=str(row["task_b"]),
                sense=str(row["sense"]),
            )
        )
    return BranchContext(pair_decisions=tuple(decisions))
