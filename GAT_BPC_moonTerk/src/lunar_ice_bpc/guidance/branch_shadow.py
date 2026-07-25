"""Safe shortlist-only branch ranking and offline all-pairs controls."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from lunar_ice_bpc.exact.bpc.guidance.contracts import canonical_universe_hash


@dataclass(frozen=True)
class BranchPairCandidate:
    task_a: str
    task_b: str
    deterministic_rank: int
    fractionality: float = 0.0
    context: tuple[float, ...] = tuple()

    @property
    def candidate_id(self) -> str:
        left, right = sorted((str(self.task_a), str(self.task_b)))
        return f"branch_pair:{left}|{right}"


def rank_p0_shortlist(
    candidates: Iterable[BranchPairCandidate],
    *,
    scores: Mapping[str, float],
    enabled: bool,
) -> tuple[tuple[BranchPairCandidate, ...], dict[str, Any]]:
    rows = tuple(candidates)
    ids = tuple(row.candidate_id for row in rows)
    if len(ids) != len(set(ids)):
        raise ValueError("branch shortlist contains duplicate pairs")
    universe_hash = canonical_universe_hash(
        ids, universe_kind="p0_branch_shortlist"
    )
    if enabled:
        ordered = tuple(
            sorted(
                rows,
                key=lambda row: (
                    -float(scores.get(row.candidate_id, float("-inf"))),
                    int(row.deterministic_rank),
                    row.candidate_id,
                ),
            )
        )
    else:
        ordered = tuple(
            sorted(
                rows,
                key=lambda row: (
                    int(row.deterministic_rank),
                    row.candidate_id,
                ),
            )
        )
    after_hash = canonical_universe_hash(
        (row.candidate_id for row in ordered),
        universe_kind="p0_branch_shortlist",
    )
    if after_hash != universe_hash:
        raise RuntimeError("branch guidance changed the P0 shortlist universe")
    return ordered, {
        "mode": "shadow_shortlist_ranking",
        "legal_branch_shortlist_hash_before_sort": universe_hash,
        "legal_branch_shortlist_hash_after_sort": after_hash,
        "guidance_branch_pair_drop_count": 0,
        "missing_score_fallback_count": sum(
            1 for candidate_id in ids if candidate_id not in scores
        ),
        "same_and_different_children_required": True,
        "mutates_solver": False,
    }


def offline_all_pairs_control(
    candidates: Iterable[BranchPairCandidate],
    *,
    scores: Mapping[str, float],
) -> dict[str, tuple[str, ...]]:
    rows = tuple(candidates)
    deterministic = tuple(
        row.candidate_id
        for row in sorted(
            rows,
            key=lambda row: (row.deterministic_rank, row.candidate_id),
        )
    )
    learned = tuple(
        row.candidate_id
        for row in sorted(
            rows,
            key=lambda row: (
                -float(scores.get(row.candidate_id, float("-inf"))),
                row.deterministic_rank,
                row.candidate_id,
            ),
        )
    )
    return {"U0_deterministic": deterministic, "U1_learned": learned}
