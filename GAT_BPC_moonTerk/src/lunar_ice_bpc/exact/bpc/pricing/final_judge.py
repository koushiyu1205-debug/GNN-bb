"""B1 true-dual fixed-graph pricing final judge."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

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
from lunar_ice_bpc.exact.solver.journey_driver import (
    DirectBaselineTimeLimitExceeded,
    enumerate_direct_journey_columns,
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
    wall_time_limit_sec: float | None = None,
    complete_universe_columns: tuple[JourneyColumn, ...] | None = None,
    complete_universe_counts: dict | None = None,
) -> FinalJudgeResult:
    """Run exhaustive fixed-graph pricing with completion-bound pruning disabled."""

    active_branch_context = branch_context or _branch_context_from_reduced_cost_context(context)
    active_cut_context = cut_context or _cut_context_from_reduced_cost_context(context)
    duals = JourneyDuals(
        cover=context.task_duals,
        fleet_limit=context.fleet_dual,
        cuts=context.cut_duals,
    )
    if active_cut_context.empty and (active_branch_context.empty or complete_universe_columns is not None):
        return _run_complete_universe_rc_final_judge(
            data,
            duals,
            context=context,
            branch_context=active_branch_context,
            cut_context=active_cut_context,
            max_direct_tasks=max_direct_tasks,
            negative_eps=negative_eps,
            cache=cache,
            wall_time_limit_sec=wall_time_limit_sec,
            complete_universe_columns=complete_universe_columns,
            complete_universe_counts=complete_universe_counts,
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


def _run_complete_universe_rc_final_judge(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    context: ReducedCostContext,
    branch_context: BranchContext,
    cut_context: CutContext,
    max_direct_tasks: int,
    negative_eps: float,
    cache: DirectPricingCache | None,
    wall_time_limit_sec: float | None,
    complete_universe_columns: tuple[JourneyColumn, ...] | None,
    complete_universe_counts: dict | None,
) -> FinalJudgeResult:
    """Price root columns by complete fixed-universe enumeration plus manual RC audit.

    At the root without branch/cut context, reduced cost differs across columns
    only by the fixed journey objective for a given task set. The direct journey
    universe enumerator already returns the objective-best fixed-graph column
    for every nonempty task subset, so a manual RC audit over that complete
    universe is an exact no-negative proof path without re-pricing every subset.
    """

    if len(data.task_ids) > int(max_direct_tasks):
        payload = _incomplete_universe_payload(
            data,
            max_direct_tasks=max_direct_tasks,
            status="SKIPPED_TOO_LARGE_FOR_COMPLETE_UNIVERSE_RC_AUDIT",
            note=f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}",
            cache=cache,
        )
        payload["dual_fingerprint"] = context.dual_fingerprint
        payload["branch_context"] = branch_context.to_payload()
        payload["cut_context"] = cut_context.to_payload()
        return FinalJudgeResult(
            pricing_state=PricingState.INCOMPLETE_LIMIT,
            pricing_payload=payload,
            negative_columns=tuple(),
            all_priced_columns=tuple(),
        )

    start = perf_counter()
    complete_universe_counts = complete_universe_counts or {}
    if complete_universe_columns is None:
        deadline = None
        if wall_time_limit_sec is not None:
            deadline = start + max(0.001, float(wall_time_limit_sec))
        try:
            universe = enumerate_direct_journey_columns(
                data,
                max_exact_tasks=int(max_direct_tasks),
                deadline=deadline,
            )
        except DirectBaselineTimeLimitExceeded as exc:
            payload = _incomplete_universe_payload(
                data,
                max_direct_tasks=max_direct_tasks,
                status="COMPLETE_UNIVERSE_RC_AUDIT_TIME_LIMIT",
                note=(
                    f"Complete fixed-universe RC audit exceeded wall_time_limit_sec={wall_time_limit_sec} "
                    f"during {exc.stage}; partial counts are diagnostic only."
                ),
                cache=cache,
                generated_journey_count=exc.generated_journey_count,
                generated_sortie_count=exc.generated_sortie_count,
                route_template_count=exc.route_template_count,
                pareto_label_count=exc.pareto_label_count,
            )
            payload["dual_fingerprint"] = context.dual_fingerprint
            payload["branch_context"] = branch_context.to_payload()
            payload["cut_context"] = cut_context.to_payload()
            return FinalJudgeResult(
                pricing_state=PricingState.INCOMPLETE_LIMIT,
                pricing_payload=payload,
                negative_columns=tuple(),
                all_priced_columns=tuple(),
            )
        raw_columns = tuple(universe.columns)
        generated_sortie_count = int(universe.generated_sortie_count)
        route_template_count = int(universe.route_template_count)
        pareto_label_count = int(universe.pareto_label_count)
        universe_source = "enumerated"
    else:
        raw_columns = tuple(complete_universe_columns)
        generated_sortie_count = int(complete_universe_counts.get("generated_sortie_count") or 0)
        route_template_count = int(complete_universe_counts.get("route_template_count") or 0)
        pareto_label_count = int(complete_universe_counts.get("pareto_label_count") or 0)
        universe_source = "provided_complete_universe_cache"
    columns = tuple(column for column in raw_columns if journey_satisfies_branch_context(column, branch_context))
    branch_filtered_column_count = len(raw_columns) - len(columns)
    rc_values = tuple(_manual_reduced_cost(column, duals, cut_context) for column in columns)
    min_reduced_cost = min(rc_values) if rc_values else None
    negative_pairs = tuple(
        sorted(
            (
                (rc, column)
                for rc, column in zip(rc_values, columns)
                if rc < -abs(float(negative_eps))
            ),
            key=lambda item: (item[0], tuple(sorted(item[1].task_set)), item[1].objective),
        )
    )
    negative_columns = tuple(column for _, column in negative_pairs)
    pricing_rc_audit_pass = bool(
        (min_reduced_cost is None and not columns)
        or (min_reduced_cost is not None and min_reduced_cost == min(rc_values))
    )
    certified = bool(
        columns
        and min_reduced_cost is not None
        and float(min_reduced_cost) >= -abs(float(negative_eps))
        and not negative_columns
        and pricing_rc_audit_pass
    )
    state = (
        PricingState.FOUND_NEGATIVE
        if negative_columns
        else PricingState.CERTIFIED_NO_NEGATIVE
        if certified
        else PricingState.INCOMPLETE_LIMIT
    )
    payload = {
        "status": "COMPLETE_DIRECT_UNIVERSE_RC_AUDITED",
        "exact_status": "NOT_BPC_CERTIFIED",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": len(columns),
        "candidate_round_limit": None,
        "candidate_task_count": len(data.task_ids),
        "candidate_task_ids": list(data.task_ids),
        "pricing_complete_for_all_tasks": True,
        "pricing_complete_for_all_task_subsets": True,
        "exhaustive_candidate_set_count": len(columns),
        "generated_journey_count": len(columns),
        "complete_universe_raw_column_count": len(raw_columns),
        "sortie_attempt_count": int(route_template_count),
        "feasible_sortie_template_count": int(generated_sortie_count),
        "route_template_count": int(route_template_count),
        "pareto_label_count": int(pareto_label_count),
        "best_reduced_cost": min_reduced_cost,
        "negative_found": bool(negative_columns),
        "negative_column_count": len(negative_columns),
        "cut_context_active": not cut_context.empty,
        "cut_count": len(cut_context.cuts),
        "branch_context_active": not branch_context.empty,
        "branch_decision_count": len(branch_context.pair_decisions),
        "branch_filtered_column_count": branch_filtered_column_count,
        "completion_bound": _disabled_completion_bound_payload(),
        "completion_bound_pruning_enabled": False,
        "sortie_template_cache": _cache_payload(cache),
        "pricing_state": state.value,
        "can_certify_no_negative": bool(certified),
        "uses_true_dual_bpc_certificate": bool(certified),
        "dual_fingerprint": context.dual_fingerprint,
        "branch_context": branch_context.to_payload(),
        "cut_context": cut_context.to_payload(),
        "manual_best_reduced_cost": min_reduced_cost,
        "pricing_best_reduced_cost": min_reduced_cost,
        "pricing_rc_audit_pass": pricing_rc_audit_pass,
        "manual_priced_column_count": len(rc_values),
        "all_priced_columns_satisfy_branch_context": all(
            journey_satisfies_branch_context(column, branch_context)
            for column in columns
        ),
        "final_judge_wall_time": round(perf_counter() - start, 6),
        "complete_universe_source": universe_source,
        "note": (
            "Root final judge used complete fixed-universe enumeration plus manual reduced-cost audit; "
            "certificate authority is granted only when all audited RC values are nonnegative."
        ),
    }
    return FinalJudgeResult(
        pricing_state=state,
        pricing_payload=payload,
        negative_columns=negative_columns,
        all_priced_columns=columns,
    )


def _incomplete_universe_payload(
    data: LunarIceData,
    *,
    max_direct_tasks: int,
    status: str,
    note: str,
    cache: DirectPricingCache | None,
    generated_journey_count: int = 0,
    generated_sortie_count: int = 0,
    route_template_count: int = 0,
    pareto_label_count: int = 0,
) -> dict:
    return {
        "status": status,
        "exact_status": "NOT_SOLVED",
        "task_count": len(data.task_ids),
        "max_direct_tasks": int(max_direct_tasks),
        "candidate_round_count": int(generated_journey_count),
        "candidate_round_limit": None,
        "candidate_task_count": 0,
        "candidate_task_ids": [],
        "pricing_complete_for_all_tasks": False,
        "pricing_complete_for_all_task_subsets": False,
        "exhaustive_candidate_set_count": int(generated_journey_count),
        "generated_journey_count": int(generated_journey_count),
        "sortie_attempt_count": int(route_template_count),
        "feasible_sortie_template_count": int(generated_sortie_count),
        "route_template_count": int(route_template_count),
        "pareto_label_count": int(pareto_label_count),
        "best_reduced_cost": None,
        "negative_found": False,
        "negative_column_count": 0,
        "cut_context_active": False,
        "cut_count": 0,
        "branch_context_active": False,
        "branch_decision_count": 0,
        "branch_filtered_column_count": 0,
        "completion_bound": _disabled_completion_bound_payload(),
        "completion_bound_pruning_enabled": False,
        "sortie_template_cache": _cache_payload(cache),
        "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
        "can_certify_no_negative": False,
        "uses_true_dual_bpc_certificate": False,
        "manual_best_reduced_cost": None,
        "pricing_best_reduced_cost": None,
        "pricing_rc_audit_pass": False,
        "manual_priced_column_count": 0,
        "all_priced_columns_satisfy_branch_context": True,
        "note": note,
    }


def _disabled_completion_bound_payload() -> dict:
    return {
        "enabled": False,
        "pruning_enabled": False,
        "evaluated_label_count": 0,
        "pruned_label_count": 0,
    }


def _cache_payload(cache: DirectPricingCache | None) -> dict:
    if cache is None:
        return {"enabled": False, "entry_count": 0, "hit_count": 0, "miss_count": 0}
    return cache.stats()


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
