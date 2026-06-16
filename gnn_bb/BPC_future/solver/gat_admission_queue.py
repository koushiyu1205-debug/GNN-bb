"""Exact-safe GAT admission scheduling helpers.

This module is intentionally solver-adjacent but not solver-integrated.  It
models the Stage 4 target-mode semantics for already true-RC-verified
candidates: learned signals may prioritize or delay negative columns, but they
cannot reject negative columns or certify no-negative closure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


GAT_HIGH_PRIORITY = "HIGH_PRIORITY"
GAT_DELAY_QUEUE = "DELAY_QUEUE"
GAT_REJECT_NONNEGATIVE_ONLY = "REJECT_NONNEGATIVE_ONLY"


@dataclass(frozen=True)
class GATAdmissionCandidate:
    """A candidate whose reduced cost was already checked with true RMP duals."""

    candidate_id: str
    true_reduced_cost: float
    safe_and_in_distribution: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GATAdmissionDecision:
    candidate_id: str
    decision: str
    reason: str
    true_reduced_cost: float
    is_true_rc_negative: bool


@dataclass(frozen=True)
class GATDelayQueueEntry:
    candidate: GATAdmissionCandidate
    first_delayed_round: int
    last_seen_round: int


@dataclass(frozen=True)
class GATCertificatePreflight:
    """Certificate-facing state for delayed candidates.

    ``selector_can_certificate`` is permanently false: even an empty or
    nonnegative delay queue only means the exact pricing final judge may run.
    """

    selector_can_certificate: bool
    requires_exact_pricing_full_scan: bool
    delayed_negative_ids: tuple[str, ...]
    delayed_nonnegative_ids: tuple[str, ...]
    certificate_blocked_by_delayed_negative: bool


class GATAdmissionQueue:
    """Finite-delay queue for true-RC negative candidates.

    The queue never owns proof semantics.  A delayed negative must eventually be
    re-exposed or repriced; before certificate, any currently negative delayed
    candidate blocks learned closure and must be handled by the exact path.
    """

    def __init__(
        self,
        *,
        reduced_cost_tolerance: float = 1.0e-9,
        max_delay_rounds: int = 1,
        max_queue_size: int = 0,
    ) -> None:
        self.reduced_cost_tolerance = max(0.0, float(reduced_cost_tolerance))
        self.max_delay_rounds = max(0, int(max_delay_rounds))
        self.max_queue_size = max(0, int(max_queue_size))
        self._entries: dict[str, GATDelayQueueEntry] = {}

    def decide(
        self,
        candidate: GATAdmissionCandidate,
        *,
        current_round: int,
    ) -> GATAdmissionDecision:
        """Schedule a true-RC-verified candidate without discarding negatives."""

        is_negative = self._is_negative(candidate.true_reduced_cost)
        if not is_negative:
            self._entries.pop(candidate.candidate_id, None)
            return GATAdmissionDecision(
                candidate_id=candidate.candidate_id,
                decision=GAT_REJECT_NONNEGATIVE_ONLY,
                reason="true_reduced_cost_nonnegative",
                true_reduced_cost=float(candidate.true_reduced_cost),
                is_true_rc_negative=False,
            )
        if bool(candidate.safe_and_in_distribution):
            self._entries.pop(candidate.candidate_id, None)
            return GATAdmissionDecision(
                candidate_id=candidate.candidate_id,
                decision=GAT_HIGH_PRIORITY,
                reason="true_rc_negative_safe_in_distribution",
                true_reduced_cost=float(candidate.true_reduced_cost),
                is_true_rc_negative=True,
            )
        self._delay(candidate, current_round=int(current_round))
        return GATAdmissionDecision(
            candidate_id=candidate.candidate_id,
            decision=GAT_DELAY_QUEUE,
            reason="true_rc_negative_delayed_not_rejected",
            true_reduced_cost=float(candidate.true_reduced_cost),
            is_true_rc_negative=True,
        )

    def decide_many(
        self,
        candidates: Iterable[GATAdmissionCandidate],
        *,
        current_round: int,
    ) -> list[GATAdmissionDecision]:
        return [self.decide(candidate, current_round=current_round) for candidate in candidates]

    def due_for_release(self, *, current_round: int, before_certificate: bool = False) -> list[GATDelayQueueEntry]:
        """Return delayed entries that must be re-exposed to the exact path."""

        if before_certificate:
            return list(self._entries.values())
        release: dict[str, GATDelayQueueEntry] = {}
        if self.max_delay_rounds <= 0:
            release.update(self._entries)
        else:
            release.update(
                {
                    entry.candidate.candidate_id: entry
                    for entry in self._entries.values()
                    if int(current_round) - int(entry.first_delayed_round) >= self.max_delay_rounds
                }
            )
        if self.max_queue_size > 0 and len(self._entries) > self.max_queue_size:
            overflow_count = len(self._entries) - self.max_queue_size
            oldest = sorted(
                self._entries.values(),
                key=lambda entry: (
                    entry.first_delayed_round,
                    entry.candidate.candidate_id,
                ),
            )[:overflow_count]
            release.update({entry.candidate.candidate_id: entry for entry in oldest})
        return list(release.values())

    def pop_released(self, entries: Iterable[GATDelayQueueEntry]) -> list[GATAdmissionCandidate]:
        released: list[GATAdmissionCandidate] = []
        for entry in entries:
            stored = self._entries.pop(entry.candidate.candidate_id, None)
            if stored is not None:
                released.append(stored.candidate)
        return released

    def certificate_preflight(
        self,
        *,
        current_true_reduced_costs: dict[str, float] | None = None,
    ) -> GATCertificatePreflight:
        """Report whether delayed candidates block learned certificate closure."""

        rc_by_id = current_true_reduced_costs or {}
        delayed_negative: list[str] = []
        delayed_nonnegative: list[str] = []
        for candidate_id, entry in sorted(self._entries.items()):
            rc = float(rc_by_id.get(candidate_id, entry.candidate.true_reduced_cost))
            if self._is_negative(rc):
                delayed_negative.append(candidate_id)
            else:
                delayed_nonnegative.append(candidate_id)
        return GATCertificatePreflight(
            selector_can_certificate=False,
            requires_exact_pricing_full_scan=True,
            delayed_negative_ids=tuple(delayed_negative),
            delayed_nonnegative_ids=tuple(delayed_nonnegative),
            certificate_blocked_by_delayed_negative=bool(delayed_negative),
        )

    def __len__(self) -> int:
        return len(self._entries)

    def _delay(self, candidate: GATAdmissionCandidate, *, current_round: int) -> None:
        existing = self._entries.get(candidate.candidate_id)
        first_round = int(current_round) if existing is None else int(existing.first_delayed_round)
        self._entries[candidate.candidate_id] = GATDelayQueueEntry(
            candidate=candidate,
            first_delayed_round=first_round,
            last_seen_round=int(current_round),
        )

    def _is_negative(self, reduced_cost: float) -> bool:
        return float(reduced_cost) < -self.reduced_cost_tolerance
