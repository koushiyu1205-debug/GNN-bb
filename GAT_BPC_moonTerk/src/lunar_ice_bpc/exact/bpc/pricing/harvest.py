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
) -> tuple[tuple[JourneyColumn, ...], dict]:
    """Select true-RC negative candidates that can actually enter the master."""

    counter = profiling or PruningCounter()
    start = perf_counter()
    reports: list[HarvestCandidateReport] = []
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
        if signature in seen_signatures:
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
        if report.would_enter_master:
            addable.append((report.would_change_active_support, float(true_rc), task_set, column))
        reports.append(
            HarvestCandidateReport(
                signature=signature,
                true_reduced_cost=round(float(true_rc), 9),
                task_set=task_set,
                is_negative=True,
                would_enter_master=report.would_enter_master,
                addability_reason=report.reason,
                reject_reason=report.reject_reason,
                pool_contains_signature=report.pool_contains_signature,
                current_master_contains_signature=report.current_master_contains_signature,
                is_forbidden_signature=report.is_forbidden_signature,
                is_allowed_by_branch=report.is_allowed_by_branch,
                is_allowed_by_cut_context=report.is_allowed_by_cut_context,
                would_change_active_support=report.would_change_active_support,
            )
        )
    addable.sort(key=lambda item: (not item[0], item[1], item[2]))
    selected = tuple(row[3] for row in addable[: max(0, int(max_selected))])
    counter.candidate_addability_time += perf_counter() - start
    counter.candidate_duplicate_count += int(duplicate_signature_count)
    counter.candidate_addable_count += len(addable)
    payload = {
        "schema_version": "lunar_ice_bpc.b2_harvest.v1",
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
