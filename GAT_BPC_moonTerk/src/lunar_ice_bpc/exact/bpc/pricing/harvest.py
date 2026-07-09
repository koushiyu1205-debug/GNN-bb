"""B2 addability-aware harvesting."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Iterable

from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.pricing.profiling import PruningCounter
from lunar_ice_bpc.exact.core.branching import BranchContext, journey_satisfies_branch_context
from lunar_ice_bpc.exact.core.journey import JourneyColumn


@dataclass(frozen=True)
class HarvestCandidateReport:
    signature: object
    true_reduced_cost: float
    task_set: tuple[str, ...]
    is_negative: bool
    would_enter_master: bool
    addability_reason: str
    reject_reason: str
    pool_contains_signature: bool
    current_master_contains_signature: bool
    is_forbidden_signature: bool
    is_allowed_by_branch: bool
    is_allowed_by_cut_context: bool
    would_change_active_support: bool


def harvest_addable_negative_columns(
    candidates: Iterable[tuple[float, JourneyColumn]],
    *,
    pool: ColumnPool,
    view: MasterColumnView,
    node_id: str = "root",
    negative_eps: float = 1.0e-6,
    max_selected: int = 64,
    forbidden_signatures: set | None = None,
    active_task_sets: set[frozenset[str]] | None = None,
    branch_context: BranchContext | None = None,
    profiling: PruningCounter | None = None,
    source_phase: str = "addability_harvest",
) -> tuple[tuple[JourneyColumn, ...], dict]:
    """Select true-RC negative candidates that can actually enter the master."""

    counter = profiling or PruningCounter()
    start = perf_counter()
    reports: list[HarvestCandidateReport] = []
    active_task_set_lookup = {
        frozenset(str(task_id) for task_id in row)
        for row in (active_task_sets or set())
    }
    addable: list[tuple[bool, float, tuple[str, ...], JourneyColumn]] = []
    seen_signatures: set[object] = set()
    duplicate_signature_count = 0
    forbidden_count = 0
    branch_filtered_count = 0
    cut_filtered_count = 0
    duplicate_in_current_master_count = 0
    in_pool_not_master_count = 0
    dominance_filtered_count = 0
    negative_count = 0
    for true_rc, column in candidates:
        signature = column_signature_from_journey(column)
        task_set = tuple(sorted(str(task_id) for task_id in column.task_set))
        is_negative = float(true_rc) < -abs(float(negative_eps))
        if not is_negative:
            continue
        negative_count += 1
        duplicate_candidate_signature = signature in seen_signatures
        if duplicate_candidate_signature:
            duplicate_signature_count += 1
        seen_signatures.add(signature)
        branch_allowed = journey_satisfies_branch_context(column, branch_context)
        bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
        report = pool.addability_check(
            bpc_column,
            {
                "master_view": view,
                "node_id": node_id,
                "forbidden_signatures": forbidden_signatures or set(),
                "active_task_sets": active_task_sets or set(),
                "is_allowed_by_branch": branch_allowed,
            },
        )
        if report.is_forbidden_signature:
            forbidden_count += 1
        if not report.is_allowed_by_branch:
            branch_filtered_count += 1
        if not report.is_allowed_by_cut_context:
            cut_filtered_count += 1
        if not report.would_change_active_support:
            dominance_filtered_count += 1
        if report.current_master_contains_signature:
            duplicate_in_current_master_count += 1
        if report.pool_contains_signature and not report.current_master_contains_signature:
            in_pool_not_master_count += 1
        if report.pool_contains_signature or report.current_master_contains_signature:
            duplicate_signature_count += 1
        would_enter_master = bool(report.would_enter_master and not duplicate_candidate_signature)
        if would_enter_master:
            addable.append((report.would_change_active_support, float(true_rc), task_set, column))
        reports.append(
            HarvestCandidateReport(
                signature=signature,
                true_reduced_cost=round(float(true_rc), 9),
                task_set=task_set,
                is_negative=True,
                would_enter_master=would_enter_master,
                addability_reason="duplicate_candidate_signature" if duplicate_candidate_signature else report.reason,
                reject_reason="duplicate_candidate_signature" if duplicate_candidate_signature else report.reject_reason,
                pool_contains_signature=report.pool_contains_signature,
                current_master_contains_signature=report.current_master_contains_signature,
                is_forbidden_signature=report.is_forbidden_signature,
                is_allowed_by_branch=report.is_allowed_by_branch,
                is_allowed_by_cut_context=report.is_allowed_by_cut_context,
                would_change_active_support=report.would_change_active_support,
            )
        )
    selected_rows = _select_harvest_rows(
        addable,
        active_task_set_lookup=active_task_set_lookup,
        max_selected=max_selected,
    )
    selected = tuple(row[3] for row in selected_rows)
    selected_task_sets = tuple(row[2] for row in selected_rows)
    selected_new_task_set_count, selected_replacement_task_set_count = _selected_task_set_counts(
        selected_rows,
        active_task_set_lookup=active_task_set_lookup,
    )
    selected_true_rc_values = tuple(float(row[1]) for row in selected_rows)
    counter.candidate_addability_time += perf_counter() - start
    counter.candidate_duplicate_count += int(duplicate_signature_count)
    counter.candidate_addable_count += len(addable)
    payload = {
        "schema_version": "lunar_ice_bpc.b2_harvest.v1",
        "harvest_source_phase": str(source_phase),
        "candidate_negative_count": int(negative_count),
        "addable_negative_count": len(addable),
        "duplicate_in_current_master_count": int(duplicate_in_current_master_count),
        "in_pool_not_master_count": int(in_pool_not_master_count),
        "forbidden_signature_count": int(forbidden_count),
        "branch_filtered_count": int(branch_filtered_count),
        "cut_filtered_count": int(cut_filtered_count),
        "selected_count": len(selected),
        "selected_would_enter_master_count": len(selected),
        "selected_all_would_enter_master": True,
        "harvest_candidate_negative_count": int(negative_count),
        "harvest_addable_candidate_count": len(addable),
        "harvest_selected_count": len(selected),
        "harvest_selected_new_task_set_count": int(selected_new_task_set_count),
        "harvest_selected_replacement_task_set_count": int(selected_replacement_task_set_count),
        "harvest_rejected_duplicate_count": int(duplicate_signature_count),
        "harvest_rejected_not_addable_count": max(0, int(negative_count) - len(addable)),
        "harvest_best_true_rc": None if not selected_true_rc_values else round(float(min(selected_true_rc_values)), 9),
        "harvest_worst_selected_true_rc": None if not selected_true_rc_values else round(float(max(selected_true_rc_values)), 9),
        "harvest_avg_pairwise_jaccard": _avg_pairwise_jaccard(selected_task_sets),
        "harvest_priority": "prefer_new_task_set_then_true_rc_then_replacements",
        "harvest_duplicate_signature_count": int(duplicate_signature_count),
        "harvest_forbidden_signature_count": int(forbidden_count),
        "harvest_branch_filtered_count": int(branch_filtered_count),
        "harvest_cut_filtered_count": int(cut_filtered_count),
        "harvest_duplicate_in_current_master_count": int(duplicate_in_current_master_count),
        "harvest_in_pool_not_master_count": int(in_pool_not_master_count),
        "harvest_dominance_filtered_count": int(dominance_filtered_count),
        "reports": [
            {
                "true_reduced_cost": report.true_reduced_cost,
                "task_set": list(report.task_set),
                "would_enter_master": report.would_enter_master,
                "addability_reason": report.addability_reason,
                "reject_reason": report.reject_reason,
                "pool_contains_signature": report.pool_contains_signature,
                "current_master_contains_signature": report.current_master_contains_signature,
                "is_forbidden_signature": report.is_forbidden_signature,
                "is_allowed_by_branch": report.is_allowed_by_branch,
                "is_allowed_by_cut_context": report.is_allowed_by_cut_context,
                "would_change_active_support": report.would_change_active_support,
            }
            for report in reports
        ],
        "profiling": counter.to_payload(),
    }
    return selected, payload


def _avg_pairwise_jaccard(task_sets: tuple[tuple[str, ...], ...]) -> float | None:
    if len(task_sets) < 2:
        return None
    total = 0.0
    count = 0
    for left_index, left in enumerate(task_sets):
        left_set = set(left)
        for right in task_sets[left_index + 1 :]:
            right_set = set(right)
            union = left_set | right_set
            total += 1.0 if not union else len(left_set & right_set) / len(union)
            count += 1
    return None if count == 0 else round(float(total / count), 9)


def _select_harvest_rows(
    rows: list[tuple[bool, float, tuple[str, ...], JourneyColumn]],
    *,
    active_task_set_lookup: set[frozenset[str]],
    max_selected: int,
) -> tuple[tuple[bool, float, tuple[str, ...], JourneyColumn], ...]:
    limit = max(0, int(max_selected))
    if limit <= 0:
        return tuple()
    ordered = sorted(rows, key=lambda item: (item[1], item[2]))
    new_rows: list[tuple[bool, float, tuple[str, ...], JourneyColumn]] = []
    replacement_rows: list[tuple[bool, float, tuple[str, ...], JourneyColumn]] = []
    selected_new_task_sets: set[frozenset[str]] = set()
    for row in ordered:
        would_change_support, _true_rc, task_set, _column = row
        key = frozenset(task_set)
        if would_change_support and key not in active_task_set_lookup and key not in selected_new_task_sets:
            new_rows.append(row)
            selected_new_task_sets.add(key)
        else:
            replacement_rows.append(row)
    return tuple((new_rows + replacement_rows)[:limit])


def _selected_task_set_counts(
    rows: tuple[tuple[bool, float, tuple[str, ...], JourneyColumn], ...],
    *,
    active_task_set_lookup: set[frozenset[str]],
) -> tuple[int, int]:
    selected_new_task_sets: set[frozenset[str]] = set()
    new_count = 0
    replacement_count = 0
    for would_change_support, _true_rc, task_set, _column in rows:
        key = frozenset(task_set)
        if would_change_support and key not in active_task_set_lookup and key not in selected_new_task_sets:
            new_count += 1
            selected_new_task_sets.add(key)
        else:
            replacement_count += 1
    return new_count, replacement_count
