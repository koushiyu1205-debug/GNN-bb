"""B1 true-dual fixed-graph pricing final judge."""

from __future__ import annotations

from dataclasses import dataclass

from lunar_ice_bpc.exact.bpc.master.reduced_cost import ReducedCostContext
from lunar_ice_bpc.exact.bpc.pricing.status import PricingState
from lunar_ice_bpc.exact.core.branching import BranchContext, branch_context_from_payload, journey_satisfies_branch_context
from lunar_ice_bpc.exact.core.cuts import CutContext, cut_context_from_payload
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost
from lunar_ice_bpc.exact.pricing.journey_pricing import (
    DirectPricingCache,
    price_exhaustive_direct_journey_columns,
)


@dataclass(frozen=True)
class FinalJudgeResult:
    pricing_state: PricingState
    pricing_payload: dict
    negative_columns: tuple[JourneyColumn, ...]
    all_priced_columns: tuple[JourneyColumn, ...]


def run_true_dual_root_final_judge(
    data: LunarIceData,
    context: ReducedCostContext,
    *,
    max_direct_tasks: int = 5,
    negative_eps: float = 1.0e-6,
    cache: DirectPricingCache | None = None,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> FinalJudgeResult:
    """Run exhaustive fixed-graph pricing with completion-bound pruning disabled."""

    active_branch_context = branch_context or _branch_context_from_reduced_cost_context(context)
    active_cut_context = cut_context or _cut_context_from_reduced_cost_context(context)
    duals = JourneyDuals(
        cover=context.task_duals,
        fleet_limit=context.fleet_dual,
        cuts=context.cut_duals,
    )
    pricing, columns = price_exhaustive_direct_journey_columns(
        data,
        duals,
        negative_eps=negative_eps,
        max_direct_tasks=int(max_direct_tasks),
        cache=cache,
        completion_bound_enabled=False,
        branch_context=active_branch_context,
        cut_context=active_cut_context,
    )
    negative_columns = tuple(
        column
        for column in columns
        if _manual_reduced_cost(column, duals, active_cut_context) < -abs(float(negative_eps))
    )
    manual_rc_values = tuple(_manual_reduced_cost(column, duals, active_cut_context) for column in columns)
    manual_best_reduced_cost = min(manual_rc_values) if manual_rc_values else None
    complete = bool(pricing.get("pricing_complete_for_all_task_subsets"))
    min_reduced_cost = pricing.get("best_reduced_cost")
    pricing_rc_audit_pass = bool(
        min_reduced_cost is None
        and manual_best_reduced_cost is None
        or (
            min_reduced_cost is not None
            and manual_best_reduced_cost is not None
            and abs(float(min_reduced_cost) - float(manual_best_reduced_cost)) <= 1.0e-6
        )
    )
    certified = bool(
        complete
        and min_reduced_cost is not None
        and float(min_reduced_cost) >= -abs(float(negative_eps))
        and not negative_columns
        and pricing_rc_audit_pass
    )
    if negative_columns:
        state = PricingState.FOUND_NEGATIVE
    elif certified:
        state = PricingState.CERTIFIED_NO_NEGATIVE
    else:
        state = PricingState.INCOMPLETE_LIMIT
    payload = dict(pricing)
    payload["pricing_state"] = state.value
    payload["completion_bound_pruning_enabled"] = False
    payload["can_certify_no_negative"] = bool(certified)
    payload["uses_true_dual_bpc_certificate"] = bool(certified)
    payload["dual_fingerprint"] = context.dual_fingerprint
    payload["branch_context"] = active_branch_context.to_payload()
    payload["cut_context"] = active_cut_context.to_payload()
    payload["manual_best_reduced_cost"] = manual_best_reduced_cost
    payload["pricing_best_reduced_cost"] = min_reduced_cost
    payload["pricing_rc_audit_pass"] = pricing_rc_audit_pass
    payload["manual_priced_column_count"] = len(manual_rc_values)
    payload["all_priced_columns_satisfy_branch_context"] = all(
        journey_satisfies_branch_context(column, active_branch_context)
        for column in columns
    )
    return FinalJudgeResult(
        pricing_state=state,
        pricing_payload=payload,
        negative_columns=negative_columns,
        all_priced_columns=tuple(columns),
    )


def _branch_context_from_reduced_cost_context(context: ReducedCostContext) -> BranchContext:
    if isinstance(context.branch_context, BranchContext):
        return context.branch_context
    if isinstance(context.branch_context, dict):
        return branch_context_from_payload(context.branch_context)
    return BranchContext()


def _cut_context_from_reduced_cost_context(context: ReducedCostContext) -> CutContext:
    if isinstance(context.cut_context, CutContext):
        return context.cut_context
    if isinstance(context.cut_context, dict):
        return cut_context_from_payload(context.cut_context)
    return CutContext()


def _manual_reduced_cost(column: JourneyColumn, duals: JourneyDuals, cut_context: CutContext) -> float:
    return manual_journey_reduced_cost(
        column,
        duals,
        cut_coefficients=cut_context.coefficients_for(column),
    )
