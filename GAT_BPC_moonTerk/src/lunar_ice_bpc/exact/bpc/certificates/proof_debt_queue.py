"""Proof-debt guard for delayed true reduced-cost negatives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProofDebtCandidate:
    candidate_id: str
    true_reduced_cost: float | None = None
    payload: Any = None


@dataclass
class ProofDebtQueue:
    unreleased: list[ProofDebtCandidate] = field(default_factory=list)

    def add(self, candidate: ProofDebtCandidate | dict | str) -> None:
        if isinstance(candidate, ProofDebtCandidate):
            self.unreleased.append(candidate)
            return
        if isinstance(candidate, dict):
            self.unreleased.append(
                ProofDebtCandidate(
                    candidate_id=str(candidate.get("candidate_id") or candidate.get("id") or len(self.unreleased)),
                    true_reduced_cost=(
                        None
                        if candidate.get("true_reduced_cost") is None
                        else float(candidate["true_reduced_cost"])
                    ),
                    payload=dict(candidate),
                )
            )
            return
        self.unreleased.append(ProofDebtCandidate(candidate_id=str(candidate)))

    def release_all_before_certificate(self) -> tuple[ProofDebtCandidate, ...]:
        released = tuple(self.unreleased)
        self.unreleased.clear()
        return released

    def block_certificate_if_unreleased(self) -> bool:
        return any(
            candidate.true_reduced_cost is None or float(candidate.true_reduced_cost) < -1.0e-9
            for candidate in self.unreleased
        )

    def audit(self) -> dict:
        blocking = self.block_certificate_if_unreleased()
        return {
            "unreleased_count": len(self.unreleased),
            "blocking_true_rc_negative_count": sum(
                1
                for candidate in self.unreleased
                if candidate.true_reduced_cost is None or float(candidate.true_reduced_cost) < -1.0e-9
            ),
            "blocks_certificate": blocking,
            "candidate_ids": [candidate.candidate_id for candidate in self.unreleased],
        }

