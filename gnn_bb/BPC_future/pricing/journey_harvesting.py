"""Exact-safe journey harvesting utilities.

This module is deliberately narrower than the full pricing oracle.  It can
batch already feasible candidate journeys after an expensive true-dual judge,
but it never proves that no negative journey exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from BPC_future.core.cuts import FutureCut
from BPC_future.core.journey import JourneyColumn
from BPC_future.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost


def _journey_column_task_set(journey: JourneyColumn) -> frozenset[int]:
    return frozenset(int(task) for task in getattr(journey, "task_set", tuple()))


def _journey_task_jaccard(left: JourneyColumn, right: JourneyColumn) -> float:
    left_tasks = _journey_column_task_set(left)
    right_tasks = _journey_column_task_set(right)
    union = left_tasks | right_tasks
    if not union:
        return 0.0
    return float(len(left_tasks & right_tasks)) / float(len(union))


def _journey_task_containment(left: JourneyColumn, right: JourneyColumn) -> float:
    left_tasks = _journey_column_task_set(left)
    right_tasks = _journey_column_task_set(right)
    if not left_tasks or not right_tasks:
        return 0.0
    return float(len(left_tasks & right_tasks)) / float(min(len(left_tasks), len(right_tasks)))


def _task_set_jaccard(left: frozenset[int], right: frozenset[int]) -> float:
    union = left | right
    if not union:
        return 0.0
    return float(len(left & right)) / float(len(union))


def _avg_pairwise_journey_task_jaccard(journeys: list[JourneyColumn]) -> float | None:
    if len(journeys) < 2:
        return None
    total = 0.0
    pairs = 0
    for left_index, left in enumerate(journeys):
        for right in journeys[left_index + 1 :]:
            total += _journey_task_jaccard(left, right)
            pairs += 1
    return None if pairs <= 0 else float(total) / float(pairs)


@dataclass(frozen=True)
class DiverseJourneySelection:
    journeys: list[JourneyColumn]
    candidate_negative_count: int
    selected_count: int
    task_set_dominance_enabled: bool
    task_set_dominance_collapsed_count: int
    rejected_overlap_count: int
    rejected_duplicate_task_set_count: int
    fallback_fill_count: int
    fallback_fill_new_mask_count: int
    fallback_fill_replacement_count: int
    fallback_fill_support_changing_count: int
    fallback_fill_weak_replacement_count: int
    candidate_new_task_set_count: int
    selected_new_task_set_count: int
    selected_replacement_task_set_count: int
    candidate_priority_task_set_count: int
    selected_priority_task_set_count: int
    candidate_support_changing_count: int
    selected_support_changing_count: int
    selected_strong_replacement_count: int
    selected_weak_replacement_count: int
    mask_closure_candidate_task_set_count: int
    mask_closure_selected_count: int
    mask_closure_selected_task_set_count: int
    best_true_rc: float | None
    worst_selected_true_rc: float | None
    avg_pairwise_jaccard: float | None


_DiverseJourneySelection = DiverseJourneySelection


@dataclass(frozen=True)
class SupportAwareJourneyHarvestResult:
    selected: list[JourneyColumn]
    diagnostics: dict[str, Any]
    true_reduced_costs_by_signature: dict[tuple, float]


def _select_diverse_journey_candidates(
    candidates: list[tuple[float, JourneyColumn]],
    *,
    max_returned: int,
    top_k_strongest: int = 5,
    min_fill: int = 20,
    min_new_task_sets: int = 0,
    min_priority_task_sets: int = 0,
    max_jaccard: float = 0.5,
    max_containment: float = 0.8,
    overlap_threshold: float | None = None,
    dominant_task_set_costs: dict[frozenset[int], float] | None = None,
    existing_task_sets: set[frozenset[int]] | None = None,
    priority_task_sets: set[frozenset[int]] | None = None,
    priority_overlap_threshold: float = 1.0,
    support_aware_enabled: bool = False,
    support_task_sets: set[frozenset[int]] | None = None,
    support_overlap_threshold: float = 0.6,
    replacement_cap: int = 8,
    strong_replacement_threshold: float = -1.0e-4,
    mask_closure_enabled: bool = False,
    mask_closure_max_masks: int = 8,
    mask_closure_max_columns_per_mask: int = 6,
    prefer_new_task_sets: bool = True,
    allow_duplicate_task_sets: bool = False,
) -> DiverseJourneySelection:
    """Harvest exact true-RC negative journeys by strength and orthogonality.

    The input candidates have already passed the exact reduced-cost filter.
    This selector only ranks and batches useful directions for the RMP after an
    expensive exact-pricing probe; it never changes certificate validity.
    """

    limit = max(1, int(max_returned))
    if overlap_threshold is not None:
        max_jaccard = float(overlap_threshold)
    jaccard_limit = min(1.0, max(0.0, float(max_jaccard)))
    containment_limit = min(1.0, max(0.0, float(max_containment)))
    strongest_limit = max(0, min(limit, int(top_k_strongest)))
    fill_limit = max(0, min(limit, int(min_fill)))
    new_task_set_quota = max(0, min(limit, int(min_new_task_sets)))
    priority_task_set_quota = max(0, min(limit, int(min_priority_task_sets)))

    best_by_signature: dict[tuple, tuple[float, JourneyColumn]] = {}
    for objective, journey in candidates:
        signature = tuple(getattr(journey, "signature", tuple()))
        old = best_by_signature.get(signature)
        if old is None or (float(objective), signature) < (float(old[0]), signature):
            best_by_signature[signature] = (float(objective), journey)

    dominant_costs = {
        frozenset(int(task) for task in task_set): float(cost)
        for task_set, cost in (dominant_task_set_costs or {}).items()
    }
    task_set_dominance_active = bool(dominant_costs)
    existing_keys = set(dominant_costs.keys()) if task_set_dominance_active else set(existing_task_sets or set())
    priority_keys = {frozenset(int(task) for task in task_set) for task_set in (priority_task_sets or set())}
    priority_overlap = min(1.0, max(0.0, float(priority_overlap_threshold)))
    support_aware = bool(support_aware_enabled)
    support_keys = {frozenset(int(task) for task in task_set) for task_set in (support_task_sets or set())}
    support_overlap = min(1.0, max(0.0, float(support_overlap_threshold)))
    weak_replacement_limit = max(0, min(limit, int(replacement_cap)))
    strong_replacement_cutoff = float(strong_replacement_threshold)
    closure_enabled = bool(mask_closure_enabled) and not task_set_dominance_active
    closure_max_masks = max(0, int(mask_closure_max_masks))
    closure_max_columns_per_mask = max(0, int(mask_closure_max_columns_per_mask))

    scored_source = list(best_by_signature.values())
    raw_candidate_negative_count = len(scored_source)
    if task_set_dominance_active:
        best_by_task_set: dict[frozenset[int], tuple[float, JourneyColumn]] = {}
        for objective, journey in scored_source:
            task_set = _journey_column_task_set(journey)
            incumbent_cost = dominant_costs.get(task_set)
            if incumbent_cost is not None and float(journey.cost) >= float(incumbent_cost) - 1.0e-9:
                continue
            old = best_by_task_set.get(task_set)
            candidate_key = (
                round(float(journey.cost), 9),
                round(float(objective), 9),
                tuple(getattr(journey, "signature", tuple())),
            )
            if old is None:
                best_by_task_set[task_set] = (float(objective), journey)
                continue
            old_objective, old_journey = old
            old_key = (
                round(float(old_journey.cost), 9),
                round(float(old_objective), 9),
                tuple(getattr(old_journey, "signature", tuple())),
            )
            if candidate_key < old_key:
                best_by_task_set[task_set] = (float(objective), journey)
        scored_source = list(best_by_task_set.values())

    def is_priority_task_set(task_set: frozenset[int]) -> bool:
        normalized = frozenset(int(task) for task in task_set)
        if normalized in priority_keys:
            return True
        return any(_task_set_jaccard(normalized, priority) >= priority_overlap for priority in priority_keys)

    def max_support_jaccard(task_set: frozenset[int]) -> float:
        normalized = frozenset(int(task) for task in task_set)
        if not support_keys:
            return 0.0
        return max(_task_set_jaccard(normalized, support) for support in support_keys)

    def support_bucket(objective: float, journey: JourneyColumn) -> str:
        task_set = _journey_column_task_set(journey)
        if task_set not in existing_keys:
            return "new"
        if support_keys and max_support_jaccard(task_set) <= support_overlap:
            return "support"
        if float(objective) <= strong_replacement_cutoff:
            return "strong_replacement"
        return "weak_replacement"

    scored = sorted(
        scored_source,
        key=lambda item: (round(float(item[0]), 9), item[1].signature),
    )
    task_set_dominance_collapsed_count = max(0, len(best_by_signature) - len(scored))
    candidate_new_task_set_count = sum(
        1 for _objective, journey in scored if _journey_column_task_set(journey) not in existing_keys
    )
    candidate_priority_task_set_count = sum(
        1 for _objective, journey in scored if is_priority_task_set(_journey_column_task_set(journey))
    )
    candidate_support_changing_count = sum(
        1
        for objective, journey in scored
        if support_bucket(float(objective), journey) in {"new", "support"}
    )
    diverse_selection_order = scored
    if prefer_new_task_sets and existing_keys and candidate_new_task_set_count > 0:
        diverse_selection_order = sorted(
            scored,
            key=lambda item: (
                0 if _journey_column_task_set(item[1]) not in existing_keys else 1,
                round(float(item[0]), 9),
                item[1].signature,
            ),
        )
    if support_aware:
        bucket_rank = {
            "new": 0,
            "support": 1,
            "strong_replacement": 2,
            "weak_replacement": 3,
        }
        diverse_selection_order = sorted(
            scored,
            key=lambda item: (
                bucket_rank.get(support_bucket(float(item[0]), item[1]), 4),
                round(float(item[0]), 9),
                item[1].signature,
            ),
        )

    selected: list[tuple[float, JourneyColumn]] = []
    selected_signatures: set[tuple] = set()
    selected_task_sets: set[frozenset[int]] = set()
    rejected_duplicate_signatures: set[tuple] = set()
    rejected_overlap = 0
    rejected_duplicate_task_set = 0
    selected_bucket_counts = {
        "new": 0,
        "support": 0,
        "strong_replacement": 0,
        "weak_replacement": 0,
    }
    selected_closure_signatures: set[tuple] = set()
    fallback_fill_signatures: set[tuple] = set()

    def selected_weak_replacements() -> int:
        return int(selected_bucket_counts.get("weak_replacement", 0))

    def add_selected(objective: float, journey: JourneyColumn, *, from_closure: bool = False) -> None:
        signature = tuple(getattr(journey, "signature", tuple()))
        selected.append((float(objective), journey))
        selected_signatures.add(signature)
        selected_task_sets.add(_journey_column_task_set(journey))
        if from_closure:
            selected_closure_signatures.add(signature)
        if support_aware:
            bucket = support_bucket(float(objective), journey)
            selected_bucket_counts[bucket] = int(selected_bucket_counts.get(bucket, 0)) + 1

    def weak_replacement_cap_reached(objective: float, journey: JourneyColumn) -> bool:
        if not support_aware:
            return False
        if support_bucket(float(objective), journey) != "weak_replacement":
            return False
        return selected_weak_replacements() >= weak_replacement_limit

    def weak_replacement_cap_reached_for_fill(objective: float, journey: JourneyColumn) -> bool:
        if not weak_replacement_cap_reached(float(objective), journey):
            return False
        return not (fill_limit > weak_replacement_limit and len(selected) < fill_limit)

    if priority_task_set_quota > 0 and priority_keys:
        for objective, journey in scored:
            selected_priority_so_far = sum(
                1 for _selected_objective, selected_journey in selected
                if is_priority_task_set(_journey_column_task_set(selected_journey))
            )
            if selected_priority_so_far >= min(priority_task_set_quota, candidate_priority_task_set_count):
                break
            signature = tuple(getattr(journey, "signature", tuple()))
            if signature in selected_signatures:
                continue
            task_set = _journey_column_task_set(journey)
            if not is_priority_task_set(task_set):
                continue
            if weak_replacement_cap_reached(float(objective), journey):
                continue
            if not allow_duplicate_task_sets and task_set in selected_task_sets:
                if signature not in rejected_duplicate_signatures:
                    rejected_duplicate_signatures.add(signature)
                    rejected_duplicate_task_set += 1
                continue
            add_selected(float(objective), journey)

    if prefer_new_task_sets and existing_keys and new_task_set_quota > 0:
        for objective, journey in diverse_selection_order:
            selected_new_so_far = sum(
                1 for _selected_objective, selected_journey in selected
                if _journey_column_task_set(selected_journey) not in existing_keys
            )
            if selected_new_so_far >= min(new_task_set_quota, candidate_new_task_set_count):
                break
            signature = tuple(getattr(journey, "signature", tuple()))
            if signature in selected_signatures:
                continue
            task_set = _journey_column_task_set(journey)
            if task_set in existing_keys:
                continue
            if weak_replacement_cap_reached(float(objective), journey):
                continue
            if not allow_duplicate_task_sets and task_set in selected_task_sets:
                if signature not in rejected_duplicate_signatures:
                    rejected_duplicate_signatures.add(signature)
                    rejected_duplicate_task_set += 1
                continue
            add_selected(float(objective), journey)

    for objective, journey in scored:
        if len(selected) >= strongest_limit:
            break
        signature = tuple(getattr(journey, "signature", tuple()))
        if signature in selected_signatures:
            continue
        task_set = _journey_column_task_set(journey)
        if weak_replacement_cap_reached(float(objective), journey):
            continue
        if not allow_duplicate_task_sets and task_set in selected_task_sets:
            if signature not in rejected_duplicate_signatures:
                rejected_duplicate_signatures.add(signature)
                rejected_duplicate_task_set += 1
            continue
        add_selected(float(objective), journey)

    for objective, journey in diverse_selection_order:
        if len(selected) >= limit:
            break
        signature = tuple(getattr(journey, "signature", tuple()))
        if signature in selected_signatures:
            continue
        task_set = _journey_column_task_set(journey)
        if weak_replacement_cap_reached(float(objective), journey):
            continue
        if not allow_duplicate_task_sets and task_set in selected_task_sets:
            if signature not in rejected_duplicate_signatures:
                rejected_duplicate_signatures.add(signature)
                rejected_duplicate_task_set += 1
            continue
        diverse = True
        for _selected_objective, selected_journey in selected:
            if (
                _journey_task_jaccard(journey, selected_journey) > jaccard_limit
                or _journey_task_containment(journey, selected_journey) > containment_limit
            ):
                diverse = False
                break
        if diverse:
            add_selected(float(objective), journey)
        else:
            rejected_overlap += 1

    closure_candidate_task_sets: set[frozenset[int]] = set()
    if closure_enabled and closure_max_masks > 0 and closure_max_columns_per_mask > 0 and len(selected) < limit:
        by_task_set: dict[frozenset[int], list[tuple[float, JourneyColumn]]] = {}
        for objective, journey in scored:
            task_set = _journey_column_task_set(journey)
            by_task_set.setdefault(task_set, []).append((float(objective), journey))

        def closure_task_set_allowed(task_set: frozenset[int], grouped: list[tuple[float, JourneyColumn]]) -> bool:
            if task_set not in existing_keys:
                return False
            if support_keys and task_set in support_keys:
                return True
            return len(grouped) > 1

        closure_groups = [
            (task_set, grouped)
            for task_set, grouped in by_task_set.items()
            if closure_task_set_allowed(task_set, grouped)
        ]
        closure_candidate_task_sets = {task_set for task_set, _grouped in closure_groups}
        closure_groups.sort(
            key=lambda item: (
                0 if item[0] in support_keys else 1,
                round(float(item[1][0][0]), 9),
                tuple(sorted(item[0])),
            )
        )
        closed_masks = 0
        for task_set, grouped in closure_groups:
            if len(selected) >= limit or closed_masks >= closure_max_masks:
                break
            grouped = sorted(grouped, key=lambda item: (round(float(item[0]), 9), item[1].signature))
            added_for_mask = sum(
                1
                for _objective, selected_journey in selected
                if _journey_column_task_set(selected_journey) == task_set
            )
            added_any_for_mask = False
            for objective, journey in grouped:
                if len(selected) >= limit or added_for_mask >= closure_max_columns_per_mask:
                    break
                signature = tuple(getattr(journey, "signature", tuple()))
                if signature in selected_signatures:
                    continue
                add_selected(float(objective), journey, from_closure=True)
                added_for_mask += 1
                added_any_for_mask = True
            if added_any_for_mask:
                closed_masks += 1

    fallback_fill = 0
    if len(selected) < fill_limit:
        for objective, journey in diverse_selection_order:
            if len(selected) >= fill_limit:
                break
            signature = tuple(getattr(journey, "signature", tuple()))
            if signature in selected_signatures:
                continue
            task_set = _journey_column_task_set(journey)
            if weak_replacement_cap_reached_for_fill(float(objective), journey):
                continue
            if not allow_duplicate_task_sets and task_set in selected_task_sets:
                if signature not in rejected_duplicate_signatures:
                    rejected_duplicate_signatures.add(signature)
                    rejected_duplicate_task_set += 1
                continue
            add_selected(float(objective), journey)
            fallback_fill_signatures.add(signature)
            fallback_fill += 1

    selected.sort(key=lambda item: (round(float(item[0]), 9), item[1].signature))
    selected = selected[:limit]
    selected_journeys = [journey for _objective, journey in selected]
    selected_rcs = [float(objective) for objective, _journey in selected]
    selected_bucket_counts = {
        "new": 0,
        "support": 0,
        "strong_replacement": 0,
        "weak_replacement": 0,
    }
    if support_aware:
        for objective, journey in selected:
            bucket = support_bucket(float(objective), journey)
            selected_bucket_counts[bucket] = int(selected_bucket_counts.get(bucket, 0)) + 1
    selected_closure_signatures = {
        signature
        for signature in selected_closure_signatures
        if any(tuple(getattr(journey, "signature", tuple())) == signature for _objective, journey in selected)
    }
    selected_closure_task_sets = {
        _journey_column_task_set(journey)
        for _objective, journey in selected
        if tuple(getattr(journey, "signature", tuple())) in selected_closure_signatures
    }
    selected_fallback = [
        (float(objective), journey)
        for objective, journey in selected
        if tuple(getattr(journey, "signature", tuple())) in fallback_fill_signatures
    ]
    fallback_fill_new_mask_count = sum(
        1 for _objective, journey in selected_fallback if _journey_column_task_set(journey) not in existing_keys
    )
    fallback_fill_support_changing_count = sum(
        1
        for objective, journey in selected_fallback
        if support_bucket(float(objective), journey) in {"new", "support"}
    )
    fallback_fill_weak_replacement_count = sum(
        1
        for objective, journey in selected_fallback
        if support_bucket(float(objective), journey) == "weak_replacement"
    )
    selected_new_task_set_count = sum(
        1 for journey in selected_journeys if _journey_column_task_set(journey) not in existing_keys
    )
    selected_priority_task_set_count = sum(
        1 for journey in selected_journeys if is_priority_task_set(_journey_column_task_set(journey))
    )
    selected_support_changing_count = sum(
        1
        for objective, journey in selected
        if support_bucket(float(objective), journey) in {"new", "support"}
    )
    return DiverseJourneySelection(
        journeys=selected_journeys,
        candidate_negative_count=int(raw_candidate_negative_count),
        selected_count=len(selected_journeys),
        task_set_dominance_enabled=bool(task_set_dominance_active),
        task_set_dominance_collapsed_count=int(task_set_dominance_collapsed_count),
        rejected_overlap_count=int(rejected_overlap),
        rejected_duplicate_task_set_count=int(rejected_duplicate_task_set),
        fallback_fill_count=int(fallback_fill),
        fallback_fill_new_mask_count=int(fallback_fill_new_mask_count),
        fallback_fill_replacement_count=int(len(selected_fallback) - fallback_fill_new_mask_count),
        fallback_fill_support_changing_count=int(fallback_fill_support_changing_count),
        fallback_fill_weak_replacement_count=int(fallback_fill_weak_replacement_count),
        candidate_new_task_set_count=int(candidate_new_task_set_count),
        selected_new_task_set_count=int(selected_new_task_set_count),
        selected_replacement_task_set_count=int(len(selected_journeys) - selected_new_task_set_count),
        candidate_priority_task_set_count=int(candidate_priority_task_set_count),
        selected_priority_task_set_count=int(selected_priority_task_set_count),
        candidate_support_changing_count=int(candidate_support_changing_count),
        selected_support_changing_count=int(selected_support_changing_count),
        selected_strong_replacement_count=int(selected_bucket_counts.get("strong_replacement", 0)),
        selected_weak_replacement_count=int(selected_bucket_counts.get("weak_replacement", 0)),
        mask_closure_candidate_task_set_count=int(len(closure_candidate_task_sets)),
        mask_closure_selected_count=int(len(selected_closure_signatures)),
        mask_closure_selected_task_set_count=int(len(selected_closure_task_sets)),
        best_true_rc=None if not scored else float(scored[0][0]),
        worst_selected_true_rc=None if not selected_rcs else max(selected_rcs),
        avg_pairwise_jaccard=_avg_pairwise_journey_task_jaccard(selected_journeys),
    )


def _task_set_from_mask_key(mask: Any) -> frozenset[int]:
    if mask is None:
        return frozenset()
    if isinstance(mask, int):
        bits: set[int] = set()
        value = int(mask)
        bit = 0
        while value:
            if value & 1:
                bits.add(bit)
            value >>= 1
            bit += 1
        return frozenset(bits)
    if hasattr(mask, "task_set"):
        return _journey_column_task_set(mask)
    return frozenset(int(task) for task in mask)


def _task_sets_from_masks(masks: Iterable[Any] | None) -> set[frozenset[int]]:
    return {
        task_set
        for task_set in (_task_set_from_mask_key(mask) for mask in (masks or ()))
        if task_set
    }


def _signature_key(signature: Any) -> tuple:
    if signature is None:
        return tuple()
    if isinstance(signature, tuple):
        return signature
    if isinstance(signature, list):
        return tuple(signature)
    return (signature,)


def _empty_harvest_diagnostics() -> dict[str, Any]:
    return {
        "candidate_negative_count": 0,
        "selected_count": 0,
        "selected_new_mask_count": 0,
        "selected_support_changing_count": 0,
        "selected_strong_replacement_count": 0,
        "selected_weak_replacement_count": 0,
        "rejected_overlap_count": 0,
        "fallback_fill_count": 0,
        "fallback_fill_new_mask_count": 0,
        "fallback_fill_replacement_count": 0,
        "fallback_fill_support_changing_count": 0,
        "fallback_fill_weak_replacement_count": 0,
        "best_true_rc": None,
        "worst_selected_true_rc": None,
        "avg_pairwise_jaccard": None,
    }


def harvest_support_aware_negative_journeys(
    candidate_journeys: Iterable[JourneyColumn],
    *,
    true_duals: JourneyDuals,
    cuts: tuple[FutureCut, ...],
    active_masks: Iterable[Any],
    pool_masks: Iterable[Any],
    forbidden_signatures: Iterable[Any],
    eps: float,
    max_columns: int,
    min_new_masks: int,
    replacement_cap: int,
    top_k_strongest: int,
    max_jaccard_selected: float,
    max_jaccard_active: float,
    max_containment: float,
) -> SupportAwareJourneyHarvestResult:
    """Return a diverse batch of true-dual negative journeys.

    This helper filters with the official manual journey reduced-cost formula
    first.  An empty result is only an empty harvest result; it is not a pricing
    certificate.
    """

    forbidden = {_signature_key(signature) for signature in (forbidden_signatures or ())}
    negative_candidates: list[tuple[float, JourneyColumn]] = []
    true_rc_by_signature: dict[tuple, float] = {}
    for journey in candidate_journeys:
        signature = _signature_key(getattr(journey, "signature", tuple()))
        if signature in forbidden:
            continue
        true_rc = float(manual_journey_reduced_cost(journey, true_duals, cuts))
        if true_rc >= -float(eps):
            continue
        negative_candidates.append((true_rc, journey))
        old = true_rc_by_signature.get(signature)
        if old is None or true_rc < old:
            true_rc_by_signature[signature] = true_rc

    if not negative_candidates or int(max_columns) <= 0:
        return SupportAwareJourneyHarvestResult(
            selected=[],
            diagnostics=_empty_harvest_diagnostics(),
            true_reduced_costs_by_signature=true_rc_by_signature,
        )

    existing_task_sets = _task_sets_from_masks(pool_masks)
    support_task_sets = _task_sets_from_masks(active_masks)
    selection = _select_diverse_journey_candidates(
        negative_candidates,
        max_returned=max(1, int(max_columns)),
        top_k_strongest=int(top_k_strongest),
        min_fill=max(1, int(max_columns)),
        min_new_task_sets=int(min_new_masks),
        max_jaccard=float(max_jaccard_selected),
        max_containment=float(max_containment),
        existing_task_sets=existing_task_sets,
        support_aware_enabled=True,
        support_task_sets=support_task_sets,
        support_overlap_threshold=float(max_jaccard_active),
        replacement_cap=int(replacement_cap),
        strong_replacement_threshold=float("-inf"),
        prefer_new_task_sets=True,
    )
    diagnostics = {
        "candidate_negative_count": int(selection.candidate_negative_count),
        "selected_count": int(selection.selected_count),
        "selected_new_mask_count": int(selection.selected_new_task_set_count),
        "selected_support_changing_count": int(selection.selected_support_changing_count),
        "selected_strong_replacement_count": int(selection.selected_strong_replacement_count),
        "selected_weak_replacement_count": int(selection.selected_weak_replacement_count),
        "rejected_overlap_count": int(selection.rejected_overlap_count),
        "fallback_fill_count": int(selection.fallback_fill_count),
        "fallback_fill_new_mask_count": int(selection.fallback_fill_new_mask_count),
        "fallback_fill_replacement_count": int(selection.fallback_fill_replacement_count),
        "fallback_fill_support_changing_count": int(selection.fallback_fill_support_changing_count),
        "fallback_fill_weak_replacement_count": int(selection.fallback_fill_weak_replacement_count),
        "best_true_rc": selection.best_true_rc,
        "worst_selected_true_rc": selection.worst_selected_true_rc,
        "avg_pairwise_jaccard": selection.avg_pairwise_jaccard,
        "selected_new_task_set_count": int(selection.selected_new_task_set_count),
        "selected_replacement_task_set_count": int(selection.selected_replacement_task_set_count),
        "rejected_duplicate_task_set_count": int(selection.rejected_duplicate_task_set_count),
    }
    return SupportAwareJourneyHarvestResult(
        selected=selection.journeys,
        diagnostics=diagnostics,
        true_reduced_costs_by_signature=true_rc_by_signature,
    )
