"""Production separator and policy state for Native Live SRI BPC V1.

Only divisor-two SRI-3/SRI-5 rows are live-capable.  The separator evaluates
the complete configured family against the current restricted-master primal;
the capacity limit affects only which violated rows are returned, never which
rows are inspected.
"""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappush, heapreplace
from itertools import combinations
from math import comb
from typing import Iterable, Mapping

from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    CutDefinition,
    CutLineage,
    CutLineageEntry,
    LIVE_SRI_DIVISOR,
    MAX_NATIVE_ACTIVE_CUTS,
    canonical_subset_row_cut,
    stable_payload_hash,
    validate_live_sri_context,
)


LIVE_SRI_POLICY_VERSION = "native_live_sri_bpc_v1"
LIVE_SRI_SEPARATOR_VERSION = "native_live_sri_complete_enumeration_v1"
LIVE_SRI_VIOLATION_EPS = 1.0e-6


@dataclass(frozen=True)
class LiveSriPolicy:
    """Frozen policy parameters for P0/P1/P2 and the no-cut rollback."""

    name: str = "no_cut"
    root_subset_sizes: tuple[int, ...] = tuple()
    node_subset_sizes: tuple[int, ...] = tuple()
    global_cap: int = 4
    lineage_local_cap: int = 4
    active_cap: int = 8
    violation_eps: float = LIVE_SRI_VIOLATION_EPS
    max_separation_rounds: int = 8
    min_restricted_rmp_gain: float = 1.0e-4
    version: str = LIVE_SRI_POLICY_VERSION

    def __post_init__(self) -> None:
        root_sizes = tuple(sorted({int(size) for size in self.root_subset_sizes}))
        node_sizes = tuple(sorted({int(size) for size in self.node_subset_sizes}))
        if any(size not in {3, 5} for size in (*root_sizes, *node_sizes)):
            raise ValueError("Live SRI V1 supports only subset sizes 3 and 5")
        if int(self.global_cap) < 0 or int(self.lineage_local_cap) < 0:
            raise ValueError("cut caps must be nonnegative")
        if not 0 <= int(self.active_cap) <= MAX_NATIVE_ACTIVE_CUTS:
            raise ValueError("active_cap must be between 0 and 16")
        if float(self.violation_eps) != LIVE_SRI_VIOLATION_EPS:
            raise ValueError("Live SRI V1 violation_eps is frozen at 1e-6")
        if float(self.min_restricted_rmp_gain) < 0.0:
            raise ValueError("min_restricted_rmp_gain must be nonnegative")
        object.__setattr__(self, "name", str(self.name))
        object.__setattr__(self, "root_subset_sizes", root_sizes)
        object.__setattr__(self, "node_subset_sizes", node_sizes)

    @property
    def enabled(self) -> bool:
        return bool(self.root_subset_sizes or self.node_subset_sizes)

    @property
    def policy_hash(self) -> str:
        return stable_payload_hash(self.to_payload())

    def subset_sizes_for_depth(self, depth: int) -> tuple[int, ...]:
        return self.root_subset_sizes if int(depth) == 0 else self.node_subset_sizes

    def to_payload(self) -> dict:
        return {
            "version": self.version,
            "name": self.name,
            "root_subset_sizes": list(self.root_subset_sizes),
            "node_subset_sizes": list(self.node_subset_sizes),
            "global_cap": int(self.global_cap),
            "lineage_local_cap": int(self.lineage_local_cap),
            "active_cap": int(self.active_cap),
            "violation_eps": float(self.violation_eps),
            "max_separation_rounds": int(self.max_separation_rounds),
            "min_restricted_rmp_gain": float(self.min_restricted_rmp_gain),
            "completion_bound_with_active_cuts": False,
        }

    @classmethod
    def named(cls, name: str) -> "LiveSriPolicy":
        normalized = str(name).strip().upper().replace("-", "_")
        if normalized in {"", "NO_CUT", "NONE", "OFF"}:
            return cls(name="no_cut")
        if normalized == "P0":
            return cls(name="P0", root_subset_sizes=(3,))
        if normalized == "P1":
            return cls(name="P1", root_subset_sizes=(3, 5))
        if normalized == "P2":
            return cls(name="P2", root_subset_sizes=(3, 5), node_subset_sizes=(3,))
        raise ValueError(f"unknown Native Live SRI policy {name!r}")


@dataclass(frozen=True)
class SriCandidate:
    cut: CutDefinition
    activity: float
    violation: float
    support_column_count: int

    @property
    def ranking_key(self) -> tuple:
        return (-float(self.violation), -int(self.support_column_count), tuple(self.cut.tasks))

    def to_payload(self) -> dict:
        return {
            "cut": self.cut.to_payload(),
            "cut_id": self.cut.cut_id,
            "tasks": list(self.cut.tasks),
            "subset_size": len(self.cut.tasks),
            "activity": round(float(self.activity), 12),
            "rhs": float(self.cut.rhs),
            "violation": round(float(self.violation), 12),
            "support_column_count": int(self.support_column_count),
            "violated": True,
        }


@dataclass(frozen=True)
class _HeapEntry:
    """A min-heap entry whose root is the least desirable retained cut."""

    candidate: SriCandidate

    def __lt__(self, other: "_HeapEntry") -> bool:
        left = self.candidate
        right = other.candidate
        if abs(left.violation - right.violation) > 1.0e-15:
            return left.violation < right.violation
        if left.support_column_count != right.support_column_count:
            return left.support_column_count < right.support_column_count
        # For ties, lexicographically smaller task IDs are preferable, hence
        # a lexicographically larger tuple is the worse/min-heap entry.
        return tuple(left.cut.tasks) > tuple(right.cut.tasks)


@dataclass(frozen=True)
class SriSeparationResult:
    selected: tuple[SriCandidate, ...]
    subset_sizes: tuple[int, ...]
    enumerated_candidate_count: int
    expected_candidate_count: int
    violated_candidate_count: int
    selection_capacity: int
    max_violation: float | None
    positive_primal_column_count: int
    full_enumeration_completed: bool = True

    @property
    def selected_cuts(self) -> tuple[CutDefinition, ...]:
        return tuple(row.cut for row in self.selected)

    @property
    def unselected_violated_count(self) -> int:
        return max(0, int(self.violated_candidate_count) - len(self.selected))

    def to_payload(self) -> dict:
        return {
            "schema_version": "lunar_ice_bpc.live_sri_separation.v1",
            "separator_policy_version": LIVE_SRI_SEPARATOR_VERSION,
            "divisor": LIVE_SRI_DIVISOR,
            "subset_sizes": list(self.subset_sizes),
            "enumerated_candidate_count": int(self.enumerated_candidate_count),
            "expected_candidate_count": int(self.expected_candidate_count),
            "full_enumeration_completed": bool(self.full_enumeration_completed),
            "family_no_violated_sri_certified": bool(
                self.full_enumeration_completed and self.violated_candidate_count == 0
            ),
            "violated_candidate_count": int(self.violated_candidate_count),
            "selected_candidate_count": len(self.selected),
            "selection_capacity": int(self.selection_capacity),
            "selection_cap_reached": bool(
                self.selection_capacity > 0 and len(self.selected) >= self.selection_capacity
            ),
            "unselected_violated_count": int(self.unselected_violated_count),
            "max_violation": self.max_violation,
            "positive_primal_column_count": int(self.positive_primal_column_count),
            "violation_eps": LIVE_SRI_VIOLATION_EPS,
            "selected": [row.to_payload() for row in self.selected],
        }


def separate_live_sri(
    task_ids: Iterable[str],
    primal_columns: Iterable[Mapping[str, object]],
    *,
    subset_sizes: Iterable[int],
    selection_capacity: int,
    existing_cut_context: CutContext | None = None,
    violation_eps: float = LIVE_SRI_VIOLATION_EPS,
) -> SriSeparationResult:
    """Completely enumerate the requested V1 family and retain top violations."""

    if float(violation_eps) != LIVE_SRI_VIOLATION_EPS:
        raise ValueError("Live SRI V1 violation_eps is frozen at 1e-6")
    ordered_tasks = tuple(sorted({str(task_id) for task_id in task_ids}))
    ordered_sizes = tuple(sorted({int(size) for size in subset_sizes}))
    if any(size not in {3, 5} for size in ordered_sizes):
        raise ValueError("Live SRI V1 separator supports only SRI-3/SRI-5")
    capacity = max(0, int(selection_capacity))
    task_bits = {task_id: 1 << index for index, task_id in enumerate(ordered_tasks)}
    active_rows: list[tuple[int, float]] = []
    for row in primal_columns:
        value = float(row.get("lambda_value") or 0.0)
        if value <= 1.0e-12:
            continue
        mask = 0
        for task_id in row.get("tasks", []) or []:
            mask |= task_bits.get(str(task_id), 0)
        if mask:
            active_rows.append((mask, value))

    existing_math = {
        cut.mathematical_key for cut in (existing_cut_context or CutContext()).cuts
    }
    heap: list[_HeapEntry] = []
    enumerated = 0
    violated = 0
    max_violation: float | None = None
    for subset_size in ordered_sizes:
        for subset in combinations(ordered_tasks, subset_size):
            enumerated += 1
            cut = canonical_subset_row_cut(subset)
            if cut.mathematical_key in existing_math:
                continue
            subset_mask = 0
            for task_id in subset:
                subset_mask |= task_bits[task_id]
            activity = 0.0
            support = 0
            for column_mask, value in active_rows:
                coefficient = (column_mask & subset_mask).bit_count() // LIVE_SRI_DIVISOR
                if coefficient:
                    support += 1
                    activity += float(coefficient) * value
            violation = float(activity) - float(cut.rhs)
            if violation <= LIVE_SRI_VIOLATION_EPS:
                continue
            violated += 1
            max_violation = violation if max_violation is None else max(max_violation, violation)
            candidate = SriCandidate(
                cut=cut,
                activity=activity,
                violation=violation,
                support_column_count=support,
            )
            if capacity <= 0:
                continue
            entry = _HeapEntry(candidate)
            if len(heap) < capacity:
                heappush(heap, entry)
            elif heap[0] < entry:
                heapreplace(heap, entry)

    selected = tuple(sorted((entry.candidate for entry in heap), key=lambda row: row.ranking_key))
    expected = sum(comb(len(ordered_tasks), size) for size in ordered_sizes if len(ordered_tasks) >= size)
    return SriSeparationResult(
        selected=selected,
        subset_sizes=ordered_sizes,
        enumerated_candidate_count=enumerated,
        expected_candidate_count=expected,
        violated_candidate_count=violated,
        selection_capacity=capacity,
        max_violation=None if max_violation is None else round(max_violation, 12),
        positive_primal_column_count=len(active_rows),
        full_enumeration_completed=enumerated == expected,
    )


def activate_separated_cuts(
    context: CutContext,
    lineage: CutLineage,
    result: SriSeparationResult,
    *,
    policy: LiveSriPolicy,
    node_id: str,
    depth: int,
    ancestor_path: Iterable[str] = tuple(),
) -> tuple[CutContext, CutLineage, dict]:
    """Apply policy caps and return immutable context/lineage descendants."""

    lineage_issues = lineage.validate_context(context)
    if lineage_issues:
        raise ValueError(",".join(lineage_issues))
    scope = "global" if int(depth) == 0 else "local"
    global_count = sum(1 for row in lineage.entries if row.scope == "global")
    local_count = sum(1 for row in lineage.entries if row.scope == "local")
    scope_remaining = (
        int(policy.global_cap) - global_count
        if scope == "global"
        else int(policy.lineage_local_cap) - local_count
    )
    active_remaining = int(policy.active_cap) - len(context.cuts)
    addition_cap = max(0, min(scope_remaining, active_remaining))
    chosen = tuple(row.cut for row in result.selected[:addition_cap])
    entries = tuple(
        CutLineageEntry(
            cut_id=cut.cut_id,
            scope=scope,
            origin_node_id=str(node_id),
            ancestor_path=tuple(str(item) for item in ancestor_path),
            policy_version=policy.version,
        )
        for cut in chosen
    )
    next_context = CutContext(cuts=(*context.cuts, *chosen))
    next_lineage = CutLineage(
        entries=(*lineage.entries, *entries),
        policy_version=policy.version,
    )
    issues = (*validate_live_sri_context(next_context), *next_lineage.validate_context(next_context))
    if issues:
        raise ValueError(",".join(issues))
    report = {
        "scope": scope,
        "requested_selected_count": len(result.selected),
        "addition_cap": addition_cap,
        "added_cut_count": len(chosen),
        "added_cut_ids": [cut.cut_id for cut in chosen],
        "active_cut_count": len(next_context.cuts),
        "global_cut_count": global_count + (len(chosen) if scope == "global" else 0),
        "lineage_local_cut_count": local_count + (len(chosen) if scope == "local" else 0),
        "active_cut_context_hash": next_context.active_cut_context_hash,
        "cut_lineage_hash": next_lineage.cut_lineage_hash,
        "live_cut_policy_hash": policy.policy_hash,
    }
    return next_context, next_lineage, report
