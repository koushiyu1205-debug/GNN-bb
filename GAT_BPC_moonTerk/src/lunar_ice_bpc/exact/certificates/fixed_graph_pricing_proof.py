"""Fixed-logical-graph exhaustive pricing proof artifact.

This binds restricted RMP duals to exhaustive direct-label pricing over the
current three-path logical graph. It is useful proof evidence for the small
fixed-graph baseline, but it is not the official true-dual BPC certificate.
"""

from __future__ import annotations

from typing import Any

from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals
from lunar_ice_bpc.exact.pricing.journey_pricing import (
    DirectPricingCache,
    price_exhaustive_direct_journey_columns,
)


def build_fixed_graph_pricing_proof(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    max_direct_tasks: int = 5,
    negative_eps: float = 1.0e-6,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> dict[str, Any]:
    """Return fail-closed fixed-graph exhaustive pricing evidence."""

    cut_context = cut_context or CutContext()
    branch_context = branch_context or BranchContext()
    pricing, columns = price_exhaustive_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=int(max_direct_tasks),
        cache=DirectPricingCache(),
        completion_bound_enabled=True,
        cut_context=cut_context,
        branch_context=branch_context,
    )
    complete = bool(pricing.get("pricing_complete_for_all_task_subsets"))
    min_rc = _float_or_none(pricing.get("best_reduced_cost"))
    no_negative = bool(complete and min_rc is not None and min_rc >= -abs(float(negative_eps)))
    negative_found = bool(pricing.get("negative_found") or (min_rc is not None and min_rc < -abs(float(negative_eps))))
    if not complete:
        status = "FIXED_GRAPH_PRICING_INCOMPLETE"
    elif negative_found:
        status = "FIXED_GRAPH_NEGATIVE_REDUCED_COST_FOUND"
    elif no_negative:
        status = "FIXED_GRAPH_NO_NEGATIVE_PROVED"
    else:
        status = "FIXED_GRAPH_PRICING_FAIL_CLOSED"
    return {
        "schema_version": "lunar_ice_bpc.fixed_graph_pricing_proof.v1",
        "status": status,
        "exact_status": "NOT_BPC_CERTIFIED",
        "certificate_scope": "fixed_logical_graph_exhaustive_direct_pricing",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "exhaustive_candidate_set_count": pricing.get("exhaustive_candidate_set_count"),
        "pricing_status": pricing.get("status"),
        "pricing_complete_for_all_task_subsets": complete,
        "priced_column_count": len(columns),
        "min_reduced_cost": min_rc,
        "negative_found": negative_found,
        "fixed_graph_no_negative_proved": bool(no_negative),
        "uses_true_dual_bpc_certificate": False,
        "lower_bound_official": False,
        "can_certify_no_negative": False,
        "cut_context_active": not cut_context.empty,
        "cut_count": len(cut_context.cuts),
        "branch_context_active": not branch_context.empty,
        "branch_decision_count": len(branch_context.pair_decisions),
        "branch_filtered_column_count": pricing.get("branch_filtered_column_count"),
        "completion_bound_enabled": (pricing.get("completion_bound") or {}).get("enabled"),
        "completion_bound_pruned_label_count": (pricing.get("completion_bound") or {}).get("pruned_label_count"),
        "exact_status_effect": "none",
        "mutates_solver": False,
        "note": _note(status),
    }


def _note(status: str) -> str:
    if status == "FIXED_GRAPH_NO_NEGATIVE_PROVED":
        return (
            "Exhaustive direct-label pricing found no negative reduced-cost column on the fixed logical graph; "
            "this is fixed-graph evidence only, not a true-dual BPC certificate."
        )
    if status == "FIXED_GRAPH_NEGATIVE_REDUCED_COST_FOUND":
        return "A negative reduced-cost fixed-graph journey exists; add columns or continue pricing."
    if status == "FIXED_GRAPH_PRICING_INCOMPLETE":
        return "Fixed-graph exhaustive pricing did not cover all task subsets; fail closed."
    return "Fixed-graph pricing evidence is insufficient; fail closed."


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 9)
    except (TypeError, ValueError):
        return None
