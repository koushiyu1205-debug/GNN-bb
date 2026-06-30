"""Bound-on/bound-off audit for direct-label completion bounds."""

from __future__ import annotations

from typing import Any

from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.pricing.journey_pricing import price_exhaustive_direct_journey_columns


def build_completion_bound_consistency_audit(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    max_direct_tasks: int = 5,
    negative_eps: float = 1.0e-6,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> dict[str, Any]:
    """Compare exhaustive direct pricing with completion-bound on and off."""

    if len(data.task_ids) > int(max_direct_tasks):
        return {
            "schema_version": "lunar_ice_bpc.completion_bound_consistency.v1",
            "status": "SKIPPED_TOO_LARGE_FOR_COMPLETION_BOUND_AUDIT",
            "task_count": len(data.task_ids),
            "max_direct_tasks": int(max_direct_tasks),
            "consistent": False,
            "can_certify_no_negative": False,
            "exact_status_effect": "none",
            "mutates_solver": False,
            "note": f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}",
        }
    context = cut_context or CutContext()
    branch = branch_context or BranchContext()
    with_bound, _ = price_exhaustive_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=int(max_direct_tasks),
        completion_bound_enabled=True,
        cut_context=context,
        branch_context=branch,
    )
    without_bound, _ = price_exhaustive_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=int(max_direct_tasks),
        completion_bound_enabled=False,
        cut_context=context,
        branch_context=branch,
    )
    with_completion = with_bound.get("completion_bound") or {}
    without_completion = without_bound.get("completion_bound") or {}
    consistent = _same_float(with_bound.get("best_reduced_cost"), without_bound.get("best_reduced_cost")) and bool(
        with_bound.get("negative_found")
    ) == bool(without_bound.get("negative_found"))
    return {
        "schema_version": "lunar_ice_bpc.completion_bound_consistency.v1",
        "status": "COMPLETION_BOUND_CONSISTENT" if consistent else "COMPLETION_BOUND_MISMATCH",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "consistent": consistent,
        "with_bound_status": with_bound.get("status"),
        "without_bound_status": without_bound.get("status"),
        "with_bound_best_reduced_cost": _float_or_none(with_bound.get("best_reduced_cost")),
        "without_bound_best_reduced_cost": _float_or_none(without_bound.get("best_reduced_cost")),
        "with_bound_negative_found": bool(with_bound.get("negative_found")),
        "without_bound_negative_found": bool(without_bound.get("negative_found")),
        "with_bound_enabled": bool(with_completion.get("enabled")),
        "without_bound_enabled": bool(without_completion.get("enabled")),
        "with_bound_pruned_label_count": int(with_completion.get("pruned_label_count") or 0),
        "with_bound_evaluated_label_count": int(with_completion.get("evaluated_label_count") or 0),
        "without_bound_evaluated_label_count": int(without_completion.get("evaluated_label_count") or 0),
        "cut_context_active": not context.empty,
        "branch_context_active": not branch.empty,
        "can_certify_no_negative": False,
        "exact_status_effect": "none",
        "mutates_solver": False,
        "note": (
            "Completion-bound pruning preserves exhaustive direct-label pricing output."
            if consistent
            else "Completion-bound pruning changed exhaustive direct-label pricing output; fail closed."
        ),
    }


def _same_float(left: object, right: object, *, eps: float = 1.0e-9) -> bool:
    left_value = _float_or_none(left)
    right_value = _float_or_none(right)
    if left_value is None or right_value is None:
        return left_value is right_value
    return abs(left_value - right_value) <= float(eps)


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 9)
    except (TypeError, ValueError):
        return None
