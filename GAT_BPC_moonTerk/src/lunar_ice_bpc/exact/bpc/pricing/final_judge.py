"""B1 true-dual fixed-graph pricing final judge."""

from __future__ import annotations

from dataclasses import dataclass
import os
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
from lunar_ice_bpc.exact.solver.gurobi_compact import solve_highs_compact_single_journey_pricing


TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS = "best_task_subset_representative_fixed_graph_columns"
COMPACT_SINGLE_JOURNEY_PRICING_MIN_TASKS = 25
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_SEC = 60.0
COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET = 3
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_CAP_SEC"
COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET"
COMPACT_SINGLE_JOURNEY_NEGATIVE_NO_GOOD_SCOPE_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_NO_GOOD_SCOPE"
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_MTZ_CONNECTIVITY = False
COMPACT_SINGLE_JOURNEY_PROOF_MTZ_CONNECTIVITY = True


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
    """Run exhaustive fixed-graph pricing with completion-bound pruning disabled.

    ``complete_universe_columns`` is a legacy name for the compressed fixed-graph
    universe: one objective-best representative journey per nonempty task subset.
    It is not the set of all route variants.
    """

    active_branch_context = branch_context or _branch_context_from_reduced_cost_context(context)
    active_cut_context = cut_context or _cut_context_from_reduced_cost_context(context)
    duals = JourneyDuals(
        cover=context.task_duals,
        fleet_limit=context.fleet_dual,
        cuts=context.cut_duals,
    )
    if active_cut_context.empty and (active_branch_context.empty or complete_universe_columns is not None):
        if (
            active_branch_context.empty
            and complete_universe_columns is None
            and len(data.task_ids) >= COMPACT_SINGLE_JOURNEY_PRICING_MIN_TASKS
        ):
            return _run_compact_single_journey_pricing_final_judge(
                data,
                duals,
                context=context,
                branch_context=active_branch_context,
                cut_context=active_cut_context,
                negative_eps=negative_eps,
                wall_time_limit_sec=wall_time_limit_sec,
            )
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


def _run_compact_single_journey_pricing_final_judge(
    data: LunarIceData,
    duals: JourneyDuals,
    *,
    context: ReducedCostContext,
    branch_context: BranchContext,
    cut_context: CutContext,
    negative_eps: float,
    wall_time_limit_sec: float | None,
) -> FinalJudgeResult:
    start = perf_counter()
    phase_payloads: dict[str, dict] = {}
    forbidden_patterns: list[tuple[tuple[int, str, str, str], ...]] = []
    forbidden_task_sets: list[tuple[str, ...]] = []
    seen_patterns: set[tuple[tuple[int, str, str, str], ...]] = set()
    seen_task_sets: set[tuple[str, ...]] = set()
    batch_negative_columns: list[JourneyColumn] = []
    last_negative_result: dict | None = None
    batch_target = _env_int(
        COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET_ENV,
        default=COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET,
        minimum=1,
        maximum=32,
    )
    negative_search_cap = _env_float(
        COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_ENV,
        default=COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_SEC,
        minimum=0.001,
        maximum=3600.0,
    )
    no_good_scope = _env_choice(
        COMPACT_SINGLE_JOURNEY_NEGATIVE_NO_GOOD_SCOPE_ENV,
        default="arc",
        choices={"arc", "task_set", "arc_and_task_set"},
    )
    for batch_index in range(1, batch_target + 1):
        remaining_for_search = _remaining_compact_time(wall_time_limit_sec, started_at=start)
        if remaining_for_search is not None and remaining_for_search <= 0.25:
            break
        negative_budget = (
            negative_search_cap
            if remaining_for_search is None
            else min(
                max(0.001, float(remaining_for_search)),
                negative_search_cap,
            )
        )
        negative_result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=negative_budget,
            threads=1,
            mip_gap=0.0,
            negative_eps=negative_eps,
            mtz_connectivity=COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_MTZ_CONNECTIVITY,
            negative_feasibility_search=True,
            forbidden_arc_patterns=tuple(forbidden_patterns),
            forbidden_task_sets=tuple(forbidden_task_sets),
        )
        last_negative_result = negative_result
        phase_payloads[f"negative_feasibility_search_{batch_index}"] = _compact_phase_summary(negative_result)
        negative_state, negative_columns, negative_can_certify = _compact_result_state(
            negative_result,
            duals,
            cut_context,
            negative_eps=negative_eps,
        )
        if negative_state == PricingState.FOUND_NEGATIVE:
            added_new = False
            for column in negative_columns:
                pattern = _journey_forbidden_arc_pattern(column)
                task_set = _journey_forbidden_task_set(column)
                pattern_added = False
                task_set_added = False
                if no_good_scope in {"arc", "arc_and_task_set"} and pattern and pattern not in seen_patterns:
                    seen_patterns.add(pattern)
                    forbidden_patterns.append(pattern)
                    pattern_added = True
                if no_good_scope in {"task_set", "arc_and_task_set"} and task_set and task_set not in seen_task_sets:
                    seen_task_sets.add(task_set)
                    forbidden_task_sets.append(task_set)
                    task_set_added = True
                if not (pattern_added or task_set_added):
                    continue
                batch_negative_columns.append(column)
                added_new = True
            if added_new:
                continue
            break
        if negative_state == PricingState.CERTIFIED_NO_NEGATIVE and not batch_negative_columns:
            return _compact_final_judge_result(
                data,
                context=context,
                branch_context=branch_context,
                cut_context=cut_context,
                result=negative_result,
                state=negative_state,
                negative_columns=tuple(),
                can_certify=negative_can_certify,
                started_at=start,
                phase="negative_feasibility_search",
                phase_payloads=phase_payloads,
            )
        break

    if batch_negative_columns:
        manual_best = min(_manual_reduced_cost(column, duals, cut_context) for column in batch_negative_columns)
        result = dict(last_negative_result or {})
        result.update(
            {
                "status": "COMPACT_HIGHS_PRICING_BATCH_FOUND_NEGATIVE",
                "algorithm_status": "COMPACT_HIGHS_PRICING_BATCH_FOUND_NEGATIVE",
                "exact_status": "NOT_SOLVED",
                "pricing_state": PricingState.FOUND_NEGATIVE.value,
                "best_reduced_cost": round(float(manual_best), 9),
                "manual_best_reduced_cost": round(float(manual_best), 9),
                "pricing_best_reduced_cost": round(float(manual_best), 9),
                "negative_found": True,
                "negative_column_count": len(batch_negative_columns),
                "can_certify_no_negative": False,
                "uses_true_dual_bpc_certificate": False,
                "pricing_rc_audit_pass": True,
                "journeys": tuple(batch_negative_columns),
                "journey_count": len(batch_negative_columns),
                "has_feasible_incumbent": True,
                "compact_negative_batch_enabled": True,
                "compact_negative_batch_target": batch_target,
                "compact_negative_no_good_scope": no_good_scope,
                "compact_negative_search_cap_sec": negative_search_cap,
                "compact_negative_batch_found_count": len(batch_negative_columns),
                "compact_negative_batch_search_call_count": len(phase_payloads),
                "forbidden_arc_pattern_count": len(forbidden_patterns),
                "forbidden_arc_patterns_can_certify_full_space": False,
                "forbidden_task_set_count": len(forbidden_task_sets),
                "forbidden_task_sets_can_certify_full_space": False,
                "wall_time_sec": round(perf_counter() - start, 6),
                "note": (
                    "Compact final judge used restricted negative-feasibility discovery to return "
                    "multiple audited negative columns. Restricted discovery is not a no-negative "
                    "certificate; a later unrestricted proof phase is still required for closure."
                ),
            }
        )
        return _compact_final_judge_result(
            data,
            context=context,
            branch_context=branch_context,
            cut_context=cut_context,
            result=result,
            state=PricingState.FOUND_NEGATIVE,
            negative_columns=tuple(batch_negative_columns),
            can_certify=False,
            started_at=start,
            phase="negative_feasibility_batch",
            phase_payloads=phase_payloads,
        )

    remaining = _remaining_compact_time(wall_time_limit_sec, started_at=start)
    if remaining is None or remaining > 0.25:
        result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=remaining,
            threads=1,
            mip_gap=0.0,
            negative_eps=negative_eps,
            mtz_connectivity=COMPACT_SINGLE_JOURNEY_PROOF_MTZ_CONNECTIVITY,
            pair_adjacency_cuts=True,
        )
        state, negative_columns, can_certify = _compact_result_state(
            result,
            duals,
            cut_context,
            negative_eps=negative_eps,
        )
        return _compact_final_judge_result(
            data,
            context=context,
            branch_context=branch_context,
            cut_context=cut_context,
            result=result,
            state=state,
            negative_columns=negative_columns,
            can_certify=can_certify,
            started_at=start,
            phase="optimization_proof",
            phase_payloads={
                **phase_payloads,
                "optimization_proof": _compact_phase_summary(result),
            },
        )

    return _compact_final_judge_result(
        data,
        context=context,
        branch_context=branch_context,
        cut_context=cut_context,
        result=last_negative_result or {},
        state=PricingState.INCOMPLETE_LIMIT,
        negative_columns=tuple(),
        can_certify=False,
        started_at=start,
        phase="negative_feasibility_search",
        phase_payloads=phase_payloads,
    )


def _remaining_compact_time(wall_time_limit_sec: float | None, *, started_at: float) -> float | None:
    if wall_time_limit_sec is None:
        return None
    return max(0.001, float(wall_time_limit_sec) - (perf_counter() - float(started_at)))


def _env_int(name: str, *, default: int, minimum: int, maximum: int) -> int:
    raw = os.environ.get(str(name))
    try:
        value = int(raw) if raw not in {None, ""} else int(default)
    except (TypeError, ValueError):
        value = int(default)
    return max(int(minimum), min(int(maximum), int(value)))


def _env_float(name: str, *, default: float, minimum: float, maximum: float) -> float:
    raw = os.environ.get(str(name))
    try:
        value = float(raw) if raw not in {None, ""} else float(default)
    except (TypeError, ValueError):
        value = float(default)
    return max(float(minimum), min(float(maximum), float(value)))


def _env_choice(name: str, *, default: str, choices: set[str]) -> str:
    raw = os.environ.get(str(name))
    value = str(raw).strip().lower() if raw not in {None, ""} else str(default)
    return value if value in choices else str(default)


def _compact_result_state(
    result: dict,
    duals: JourneyDuals,
    cut_context: CutContext,
    *,
    negative_eps: float,
) -> tuple[PricingState, tuple[JourneyColumn, ...], bool]:
    state = PricingState(str(result.get("pricing_state") or PricingState.INCOMPLETE_LIMIT.value))
    columns = tuple(result.get("journeys") or tuple())
    negative_columns = tuple(
        column
        for column in columns
        if _manual_reduced_cost(column, duals, cut_context) < -abs(float(negative_eps))
    )
    if negative_columns:
        state = PricingState.FOUND_NEGATIVE
    can_certify = bool(
        state == PricingState.CERTIFIED_NO_NEGATIVE
        and result.get("can_certify_no_negative") is True
        and result.get("pricing_rc_audit_pass") is True
    )
    if can_certify:
        state = PricingState.CERTIFIED_NO_NEGATIVE
    elif state == PricingState.CERTIFIED_NO_NEGATIVE:
        state = PricingState.INCOMPLETE_LIMIT
    return state, negative_columns, bool(can_certify)


def _compact_final_judge_result(
    data: LunarIceData,
    *,
    context: ReducedCostContext,
    branch_context: BranchContext,
    cut_context: CutContext,
    result: dict,
    state: PricingState,
    negative_columns: tuple[JourneyColumn, ...],
    can_certify: bool,
    started_at: float,
    phase: str,
    phase_payloads: dict,
) -> FinalJudgeResult:
    columns = tuple(result.get("journeys") or tuple())
    payload = {
        **{key: value for key, value in result.items() if key != "journeys"},
        "status": str(result.get("status") or "COMPACT_HIGHS_SINGLE_JOURNEY_PRICING"),
        "exact_status": str(result.get("exact_status") or "NOT_SOLVED"),
        "compact_pricing_phase": str(phase),
        "compact_pricing_phase_payloads": dict(phase_payloads),
        "task_count": len(data.task_ids),
        "max_direct_tasks": len(data.task_ids),
        "candidate_round_count": int(result.get("candidate_round_count") or result.get("compact_negative_batch_search_call_count") or 1),
        "candidate_round_limit": int(result.get("candidate_round_limit") or result.get("compact_negative_batch_target") or 1),
        "candidate_task_count": len(data.task_ids),
        "candidate_task_ids": list(data.task_ids),
        "pricing_state": state.value,
        "can_certify_no_negative": bool(can_certify),
        "uses_true_dual_bpc_certificate": bool(can_certify),
        "negative_found": bool(negative_columns),
        "negative_column_count": len(negative_columns),
        "cut_context_active": not cut_context.empty,
        "cut_count": len(cut_context.cuts),
        "branch_context_active": not branch_context.empty,
        "branch_decision_count": len(branch_context.pair_decisions),
        "branch_filtered_column_count": 0,
        "completion_bound": _disabled_completion_bound_payload(),
        "completion_bound_pruning_enabled": False,
        "sortie_template_cache": {"enabled": False, "entry_count": 0, "hit_count": 0, "miss_count": 0},
        "dual_fingerprint": context.dual_fingerprint,
        "branch_context": branch_context.to_payload(),
        "cut_context": cut_context.to_payload(),
        "manual_best_reduced_cost": result.get("manual_best_reduced_cost"),
        "pricing_best_reduced_cost": result.get("pricing_best_reduced_cost", result.get("best_reduced_cost")),
        "pricing_rc_audit_pass": bool(result.get("pricing_rc_audit_pass") is True),
        "manual_priced_column_count": len(columns),
        "all_priced_columns_satisfy_branch_context": True,
        "final_judge_wall_time": round(perf_counter() - started_at, 6),
        "column_universe_semantics": "compact_single_journey_pricing_fixed_graph_all_task_subsets",
        "compact_pricing_contains_all_route_variants": True,
        "complete_universe_contains_all_route_variants": False,
        "representative_universe_total_count": _representative_universe_total_count(data),
        "representative_universe_audited_count": 0,
        "representative_universe_completion_ratio": 0.0,
        "representative_universe_remaining_count": _representative_universe_total_count(data),
        "note": (
            "Final judge used compact HiGHS single-journey reduced-cost pricing instead of "
            "enumerating every task-subset representative. It can certify no-negative only "
            "when the compact pricing MILP is exact and nonnegative; negative-feasibility "
            "phase may still return audited negative columns before exact closure."
        ),
    }
    return FinalJudgeResult(
        pricing_state=state,
        pricing_payload=payload,
        negative_columns=negative_columns,
        all_priced_columns=columns,
    )


def _compact_phase_summary(result: dict) -> dict:
    return {
        "status": result.get("status"),
        "exact_status": result.get("exact_status"),
        "pricing_state": result.get("pricing_state"),
        "best_reduced_cost": result.get("best_reduced_cost"),
        "manual_best_reduced_cost": result.get("manual_best_reduced_cost"),
        "dual_bound": result.get("dual_bound", result.get("bound")),
        "gap": result.get("gap"),
        "wall_time_sec": result.get("wall_time_sec"),
        "negative_found": result.get("negative_found"),
        "negative_feasibility_search_enabled": result.get("negative_feasibility_search_enabled"),
        "mtz_connectivity_enabled": result.get("mtz_connectivity_enabled"),
        "mtz_endpoint_order_cuts_enabled": result.get("mtz_endpoint_order_cuts_enabled"),
        "mtz_endpoint_order_cut_count": result.get("mtz_endpoint_order_cut_count"),
        "pair_adjacency_cuts_enabled": result.get("pair_adjacency_cuts_enabled"),
        "pair_adjacency_cut_count": result.get("pair_adjacency_cut_count"),
        "sortie_slots_per_journey": result.get("sortie_slots_per_journey"),
        "sortie_slot_bound_source": result.get("sortie_slot_bound_source"),
        "sortie_slot_horizon_count_bound": result.get("sortie_slot_horizon_count_bound"),
        "sortie_slot_latest_start_count_bound": result.get("sortie_slot_latest_start_count_bound"),
        "sortie_slot_latest_service_start_upper_bound": result.get("sortie_slot_latest_service_start_upper_bound"),
        "sortie_slot_min_depot_outbound_travel_lower_bound": result.get(
            "sortie_slot_min_depot_outbound_travel_lower_bound"
        ),
        "sortie_slot_min_duration_lower_bound": result.get("sortie_slot_min_duration_lower_bound"),
        "sortie_slot_min_return_duration_lower_bound": result.get("sortie_slot_min_return_duration_lower_bound"),
        "sortie_slot_min_out_return_travel_lower_bound": result.get(
            "sortie_slot_min_out_return_travel_lower_bound"
        ),
        "time_window_arc_pruning_enabled": result.get("time_window_arc_pruning_enabled"),
        "time_window_arc_option_count": result.get("time_window_arc_option_count"),
        "time_window_impossible_arc_option_count": result.get("time_window_impossible_arc_option_count"),
        "compact_negative_no_good_scope": result.get("compact_negative_no_good_scope"),
        "forbidden_arc_pattern_count": result.get("forbidden_arc_pattern_count"),
        "forbidden_arc_patterns_can_certify_full_space": result.get("forbidden_arc_patterns_can_certify_full_space"),
        "forbidden_task_set_count": result.get("forbidden_task_set_count"),
        "forbidden_task_sets_can_certify_full_space": result.get("forbidden_task_sets_can_certify_full_space"),
        "variable_count": result.get("variable_count"),
        "constraint_count": result.get("constraint_count"),
        "model_status_name": result.get("model_status_name"),
    }


def _journey_forbidden_arc_pattern(column: JourneyColumn) -> tuple[tuple[int, str, str, str], ...]:
    pattern: list[tuple[int, str, str, str]] = []
    for slot, sortie in enumerate(column.sorties):
        for leg in sortie.legs:
            pattern.append((int(slot), str(leg.source), str(leg.target), str(leg.path_type)))
    return tuple(pattern)


def _journey_forbidden_task_set(column: JourneyColumn) -> tuple[str, ...]:
    return tuple(sorted(str(task_id) for task_id in column.task_set))


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
    """Price columns by task-subset representative enumeration plus manual RC audit.

    At the root without branch/cut context, reduced cost differs across columns
    only by the fixed journey objective for a given task set. The direct journey
    universe enumerator already returns the objective-best fixed-graph column
    for every nonempty task subset. Under Ryan-Foster task-set branching and no
    cuts, a manual RC audit over these representatives is an exact no-negative
    proof path without re-pricing every route variant.
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
            payload["final_judge_wall_time"] = round(perf_counter() - start, 6)
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
        "representative_universe_total_count": _representative_universe_total_count(data),
        "representative_universe_audited_count": len(columns),
        "representative_universe_completion_ratio": _completion_ratio(
            len(columns),
            _representative_universe_total_count(data),
        ),
        "representative_universe_remaining_count": max(
            0,
            _representative_universe_total_count(data) - len(columns),
        ),
        "generated_journey_count": len(columns),
        "complete_universe_raw_column_count": len(raw_columns),
        "column_universe_semantics": TASK_SUBSET_REPRESENTATIVE_UNIVERSE_SEMANTICS,
        "complete_universe_contains_all_route_variants": False,
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
            "Final judge used the objective-best fixed-graph representative for each task subset "
            "plus manual reduced-cost audit; certificate authority is granted only when all audited "
            "RC values are nonnegative. This is not an all-route-variant universe."
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
    representative_total = _representative_universe_total_count(data)
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
        "representative_universe_total_count": representative_total,
        "representative_universe_audited_count": int(generated_journey_count),
        "representative_universe_completion_ratio": _completion_ratio(
            int(generated_journey_count),
            representative_total,
        ),
        "representative_universe_remaining_count": max(
            0,
            representative_total - int(generated_journey_count),
        ),
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


def _representative_universe_total_count(data: LunarIceData) -> int:
    return (1 << len(data.task_ids)) - 1


def _completion_ratio(count: int, total: int) -> float:
    if int(total) <= 0:
        return 0.0
    return round(float(count) / float(total), 12)


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
