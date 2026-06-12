"""Exact-safe structural archive for Pulse proof search.

The archive is deliberately conservative: a state is pruned only when an older
record with the same structural key is no worse in every tracked resource and
the comparison is valid for the scheduling mode.  Capacity overflow is
fail-open; old records may be dropped, but the current state is never rejected
just because the archive is full.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PulseStructuralKey:
    phase: str
    last_node: int
    visited_task_mask: int
    current_sortie_task_mask: int
    sorties_used: int
    branch_state_key: tuple[Any, ...] = tuple()


@dataclass(frozen=True)
class PulseArchiveRecord:
    partial_reduced_cost_lb: float
    energy_used: float
    load_used: float
    current_time: float | None = None
    start_interval: tuple[float, float] | None = None
    exact_prefix_cost: float | None = None
    trace_summary: tuple[Any, ...] = tuple()
    insertion_serial: int = 0
    proof_mode: bool = True


@dataclass(frozen=True)
class PulseArchiveDecision:
    dominated: bool
    inserted: bool
    dropped_old_record: bool = False


class StructuralKeyDominanceArchive:
    """Small exact-safe dominance archive keyed by Pulse structural state."""

    def __init__(self, *, max_records_per_key: int = 32) -> None:
        self.max_records_per_key = max(1, int(max_records_per_key))
        self._records: dict[PulseStructuralKey, list[PulseArchiveRecord]] = {}
        self._serial = 0

    def consider(
        self,
        key: PulseStructuralKey,
        record: PulseArchiveRecord,
        *,
        waiting_allowed: bool,
    ) -> PulseArchiveDecision:
        if not bool(record.proof_mode):
            return PulseArchiveDecision(dominated=False, inserted=False)
        records = self._records.setdefault(key, [])
        for old in records:
            if _archive_record_dominates(old, record, key=key, waiting_allowed=bool(waiting_allowed)):
                return PulseArchiveDecision(dominated=True, inserted=False)

        self._serial += 1
        stored = PulseArchiveRecord(
            partial_reduced_cost_lb=float(record.partial_reduced_cost_lb),
            energy_used=float(record.energy_used),
            load_used=float(record.load_used),
            current_time=None if record.current_time is None else float(record.current_time),
            start_interval=None
            if record.start_interval is None
            else (float(record.start_interval[0]), float(record.start_interval[1])),
            exact_prefix_cost=record.exact_prefix_cost,
            trace_summary=tuple(record.trace_summary),
            insertion_serial=int(self._serial),
            proof_mode=True,
        )
        records.append(stored)
        dropped = False
        if len(records) > self.max_records_per_key:
            records.sort(key=lambda item: int(item.insertion_serial))
            del records[0]
            dropped = True
        return PulseArchiveDecision(dominated=False, inserted=True, dropped_old_record=dropped)

    def record_count(self, key: PulseStructuralKey | None = None) -> int:
        if key is None:
            return sum(len(records) for records in self._records.values())
        return len(self._records.get(key, []))


def _archive_record_dominates(
    old: PulseArchiveRecord,
    new: PulseArchiveRecord,
    *,
    key: PulseStructuralKey,
    waiting_allowed: bool,
) -> bool:
    if not bool(old.proof_mode) or not bool(new.proof_mode):
        return False
    if float(old.partial_reduced_cost_lb) > float(new.partial_reduced_cost_lb) + 1.0e-9:
        return False
    if float(old.energy_used) > float(new.energy_used) + 1.0e-9:
        return False
    if float(old.load_used) > float(new.load_used) + 1.0e-9:
        return False

    phase = str(key.phase)
    if bool(waiting_allowed) or phase == "depot_ready":
        if old.current_time is None or new.current_time is None:
            return False
        return float(old.current_time) <= float(new.current_time) + 1.0e-9

    if old.start_interval is None or new.start_interval is None:
        return False
    old_left, old_right = old.start_interval
    new_left, new_right = new.start_interval
    return float(old_left) <= float(new_left) + 1.0e-9 and float(old_right) >= float(new_right) - 1.0e-9


__all__ = [
    "PulseArchiveDecision",
    "PulseArchiveRecord",
    "PulseStructuralKey",
    "StructuralKeyDominanceArchive",
]
