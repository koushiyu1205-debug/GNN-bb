"""B1 true-dual fixed-graph pricing final judge."""

from __future__ import annotations

from dataclasses import dataclass
import os
from time import perf_counter

from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.bpc.master.reduced_cost import ReducedCostContext
from lunar_ice_bpc.exact.bpc.pricing.status import PricingState
from lunar_ice_bpc.exact.core.branching import BranchContext, branch_context_from_payload, journey_satisfies_branch_context
from lunar_ice_bpc.exact.core.cuts import CutContext, cut_coefficients_for_journey, cut_context_from_payload
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
COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET = 5
COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_TARGET = 5
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_CAP_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_SEARCH_CAP_SEC"
COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_BATCH_TARGET"
COMPACT_SINGLE_JOURNEY_NEGATIVE_NO_GOOD_SCOPE_ENV = "LUNAR_ICE_COMPACT_NEGATIVE_NO_GOOD_SCOPE"
COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_TARGET_ENV = (
    "LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_TARGET"
)
COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE_ENV = (
    "LUNAR_ICE_COMPACT_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE"
)
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILE_ENV = "LUNAR_ICE_COMPACT_FINAL_JUDGE_PROFILE"
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_ENV = "LUNAR_ICE_COMPACT_FINAL_JUDGE_PHASE_MODE"
COMPACT_SINGLE_JOURNEY_SERVICE_START_DEPOT_TRAVEL_LB_ENV = "LUNAR_ICE_COMPACT_SERVICE_START_DEPOT_TRAVEL_LB"
COMPACT_SINGLE_JOURNEY_TASK_TO_DEPOT_RETURN_TRAVEL_LB_ENV = (
    "LUNAR_ICE_COMPACT_TASK_TO_DEPOT_RETURN_TRAVEL_LB"
)
COMPACT_SINGLE_JOURNEY_PAIR_ROUTE_DURATION_LB_ENV = "LUNAR_ICE_COMPACT_PAIR_ROUTE_DURATION_LB"
COMPACT_SINGLE_JOURNEY_PAIR_WEIGHTED_COMPLETION_LB_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_WEIGHTED_COMPLETION_LB"
)
COMPACT_SINGLE_JOURNEY_SORTIE_SLOT_POSITION_BOUNDS_ENV = (
    "LUNAR_ICE_COMPACT_SORTIE_SLOT_POSITION_BOUNDS"
)
COMPACT_SINGLE_JOURNEY_DEMAND_COVER_CUT_ENV = "LUNAR_ICE_COMPACT_DEMAND_COVER_CUT"
COMPACT_SINGLE_JOURNEY_SINGLE_TASK_ENERGY_LB_ENV = "LUNAR_ICE_COMPACT_SINGLE_TASK_ENERGY_LB"
COMPACT_SINGLE_JOURNEY_SINGLE_TASK_SHADOW_LB_ENV = "LUNAR_ICE_COMPACT_SINGLE_TASK_SHADOW_LB"
COMPACT_SINGLE_JOURNEY_PAIR_ENERGY_LB_ENV = "LUNAR_ICE_COMPACT_PAIR_ENERGY_LB"
COMPACT_SINGLE_JOURNEY_PAIR_SHADOW_LB_ENV = "LUNAR_ICE_COMPACT_PAIR_SHADOW_LB"
COMPACT_SINGLE_JOURNEY_PAIR_ENERGY_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_ENERGY_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_PAIR_TIME_WINDOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_PAIR_TIME_WINDOW_PRECEDENCE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_TIME_WINDOW_PRECEDENCE_CUT"
)
COMPACT_SINGLE_JOURNEY_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_QUAD_TIME_WINDOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_QUAD_TIME_WINDOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_PAIR_SHADOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_PAIR_SHADOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_TRIPLE_SHADOW_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_TRIPLE_SHADOW_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_TRIPLE_ENERGY_INFEASIBLE_CUT_ENV = (
    "LUNAR_ICE_COMPACT_TRIPLE_ENERGY_INFEASIBLE_CUT"
)
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT = "harvest_then_proof"
COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_MTZ_CONNECTIVITY = False
COMPACT_SINGLE_JOURNEY_PROOF_MTZ_CONNECTIVITY = True
COMPACT_SINGLE_JOURNEY_B4V2_MTZ_ENDPOINT_ORDER_CUTS = False
COMPACT_SINGLE_JOURNEY_B4V2_PAIR_ADJACENCY_CUTS = False
COMPACT_SINGLE_JOURNEY_B4V2_LATEST_SERVICE_START_SLOT_BOUND = True
COMPACT_SINGLE_JOURNEY_B4V2_TIME_WINDOW_ARC_PRUNING = False
COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILES = {
    "B4V2": {
        "name": "B4V2",
        "formulation_profile": "B4V2_latest_start_only",
        "negative_mtz_connectivity": COMPACT_SINGLE_JOURNEY_NEGATIVE_SEARCH_MTZ_CONNECTIVITY,
        "proof_mtz_connectivity": COMPACT_SINGLE_JOURNEY_PROOF_MTZ_CONNECTIVITY,
        "mtz_endpoint_order_cuts": COMPACT_SINGLE_JOURNEY_B4V2_MTZ_ENDPOINT_ORDER_CUTS,
        "pair_adjacency_cuts": COMPACT_SINGLE_JOURNEY_B4V2_PAIR_ADJACENCY_CUTS,
        "latest_service_start_slot_bound": COMPACT_SINGLE_JOURNEY_B4V2_LATEST_SERVICE_START_SLOT_BOUND,
        "time_window_arc_pruning": COMPACT_SINGLE_JOURNEY_B4V2_TIME_WINDOW_ARC_PRUNING,
        "official_default": True,
    },
    "V4": {
        "name": "V4",
        "formulation_profile": "B4V4_endpoint_pair_latest_start_time_window",
        "negative_mtz_connectivity": True,
        "proof_mtz_connectivity": True,
        "mtz_endpoint_order_cuts": True,
        "pair_adjacency_cuts": True,
        "latest_service_start_slot_bound": True,
        "time_window_arc_pruning": True,
        "official_default": False,
    },
}


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
    column_pool: ColumnPool | None = None,
    master_view: MasterColumnView | None = None,
    node_id: str = "root",
    active_task_sets: set[frozenset[str]] | None = None,
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
                column_pool=column_pool,
                master_view=master_view,
                node_id=node_id,
                active_task_sets=active_task_sets,
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
    column_pool: ColumnPool | None = None,
    master_view: MasterColumnView | None = None,
    node_id: str = "root",
    active_task_sets: set[frozenset[str]] | None = None,
) -> FinalJudgeResult:
    start = perf_counter()
    phase_payloads: dict[str, dict] = {}
    forbidden_patterns: list[tuple[tuple[int, str, str, str], ...]] = []
    forbidden_task_sets: list[tuple[str, ...]] = []
    seen_patterns: set[tuple[tuple[int, str, str, str], ...]] = set()
    seen_task_sets: set[tuple[str, ...]] = set()
    batch_negative_columns: list[JourneyColumn] = []
    batch_pricing_rc_by_signature: dict[object, float] = {}
    last_negative_result: dict | None = None
    profile = _compact_final_judge_profile_from_env()
    phase_mode = _compact_final_judge_phase_mode_from_env()
    service_start_depot_travel_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_SERVICE_START_DEPOT_TRAVEL_LB_ENV,
        default=False,
    )
    task_to_depot_return_travel_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_TASK_TO_DEPOT_RETURN_TRAVEL_LB_ENV,
        default=False,
    )
    pair_route_duration_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_ROUTE_DURATION_LB_ENV,
        default=False,
    )
    pair_weighted_completion_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_WEIGHTED_COMPLETION_LB_ENV,
        default=False,
    )
    sortie_slot_position_bounds = _env_bool(
        COMPACT_SINGLE_JOURNEY_SORTIE_SLOT_POSITION_BOUNDS_ENV,
        default=False,
    )
    demand_cover_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_DEMAND_COVER_CUT_ENV,
        default=False,
    )
    single_task_energy_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_SINGLE_TASK_ENERGY_LB_ENV,
        default=False,
    )
    single_task_shadow_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_SINGLE_TASK_SHADOW_LB_ENV,
        default=False,
    )
    pair_energy_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_ENERGY_LB_ENV,
        default=False,
    )
    pair_shadow_lb = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_SHADOW_LB_ENV,
        default=False,
    )
    pair_energy_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_ENERGY_INFEASIBLE_CUT_ENV,
        default=False,
    )
    pair_time_window_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_TIME_WINDOW_INFEASIBLE_CUT_ENV,
        default=False,
    )
    pair_time_window_precedence_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_TIME_WINDOW_PRECEDENCE_CUT_ENV,
        default=False,
    )
    triple_time_window_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_TRIPLE_TIME_WINDOW_INFEASIBLE_CUT_ENV,
        default=False,
    )
    quad_time_window_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_QUAD_TIME_WINDOW_INFEASIBLE_CUT_ENV,
        default=False,
    )
    pair_shadow_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_PAIR_SHADOW_INFEASIBLE_CUT_ENV,
        default=False,
    )
    triple_shadow_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_TRIPLE_SHADOW_INFEASIBLE_CUT_ENV,
        default=False,
    )
    triple_energy_infeasible_cut = _env_bool(
        COMPACT_SINGLE_JOURNEY_TRIPLE_ENERGY_INFEASIBLE_CUT_ENV,
        default=False,
    )
    batch_target = _env_int(
        COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET_ENV,
        default=COMPACT_SINGLE_JOURNEY_NEGATIVE_BATCH_TARGET,
        minimum=1,
        maximum=32,
    )
    optimization_harvest_target = _env_int(
        COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_TARGET_ENV,
        default=COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_TARGET,
        minimum=1,
        maximum=16,
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
    optimization_harvest_no_good_scope = _env_choice(
        COMPACT_SINGLE_JOURNEY_OPTIMIZATION_HARVEST_NO_GOOD_SCOPE_ENV,
        default="task_set",
        choices={"arc", "task_set", "arc_and_task_set"},
    )
    if phase_mode == "feasibility_proof_only":
        remaining = _remaining_compact_time(wall_time_limit_sec, started_at=start)
        result = solve_highs_compact_single_journey_pricing(
            data,
            duals,
            time_limit_sec=remaining,
            threads=1,
            mip_gap=0.0,
            negative_eps=negative_eps,
            mtz_connectivity=bool(profile["proof_mtz_connectivity"]),
            mtz_endpoint_order_cuts=bool(profile["mtz_endpoint_order_cuts"]),
            pair_adjacency_cuts=bool(profile["pair_adjacency_cuts"]),
            latest_service_start_slot_bound=bool(profile["latest_service_start_slot_bound"]),
            time_window_arc_pruning=bool(profile["time_window_arc_pruning"]),
            sortie_slot_position_bounds=sortie_slot_position_bounds,
            service_start_depot_travel_lb=service_start_depot_travel_lb,
            task_to_depot_return_travel_lb=task_to_depot_return_travel_lb,
            pair_route_duration_lb=pair_route_duration_lb,
            pair_weighted_completion_lb=pair_weighted_completion_lb,
            demand_cover_cut=demand_cover_cut,
            single_task_energy_lb=single_task_energy_lb,
            single_task_shadow_lb=single_task_shadow_lb,
            pair_energy_lb=pair_energy_lb,
            pair_shadow_lb=pair_shadow_lb,
            pair_energy_infeasible_cut=pair_energy_infeasible_cut,
            pair_time_window_infeasible_cut=pair_time_window_infeasible_cut,
            pair_time_window_precedence_cut=pair_time_window_precedence_cut,
            triple_time_window_infeasible_cut=triple_time_window_infeasible_cut,
            quad_time_window_infeasible_cut=quad_time_window_infeasible_cut,
            pair_shadow_infeasible_cut=pair_shadow_infeasible_cut,
            triple_shadow_infeasible_cut=triple_shadow_infeasible_cut,
            triple_energy_infeasible_cut=triple_energy_infeasible_cut,
            negative_feasibility_search=True,
        )
        result = _with_compact_profile_payload(result, profile)
        result["negative_feasibility_full_space_proof_attempted"] = True
        result["negative_feasibility_full_space_proof_can_certify"] = bool(
            result.get("can_certify_no_negative")
            and not result.get("forbidden_arc_pattern_count")
            and not result.get("forbidden_task_set_count")
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
            phase="negative_feasibility_proof",
            phase_payloads={"negative_feasibility_proof": _compact_phase_summary(result)},
            profile=profile,
            phase_mode=phase_mode,
        )

    negative_batch_range = range(1, batch_target + 1) if phase_mode != "proof_only" else ()
    for batch_index in negative_batch_range:
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
            mtz_connectivity=bool(profile["negative_mtz_connectivity"]),
            mtz_endpoint_order_cuts=bool(profile["mtz_endpoint_order_cuts"]),
            pair_adjacency_cuts=bool(profile["pair_adjacency_cuts"]),
            latest_service_start_slot_bound=bool(profile["latest_service_start_slot_bound"]),
            time_window_arc_pruning=bool(profile["time_window_arc_pruning"]),
            sortie_slot_position_bounds=sortie_slot_position_bounds,
            service_start_depot_travel_lb=service_start_depot_travel_lb,
            task_to_depot_return_travel_lb=task_to_depot_return_travel_lb,
            pair_route_duration_lb=pair_route_duration_lb,
            pair_weighted_completion_lb=pair_weighted_completion_lb,
            demand_cover_cut=demand_cover_cut,
            single_task_energy_lb=single_task_energy_lb,
            single_task_shadow_lb=single_task_shadow_lb,
            pair_energy_lb=pair_energy_lb,
            pair_shadow_lb=pair_shadow_lb,
            pair_energy_infeasible_cut=pair_energy_infeasible_cut,
            pair_time_window_infeasible_cut=pair_time_window_infeasible_cut,
            pair_time_window_precedence_cut=pair_time_window_precedence_cut,
            triple_time_window_infeasible_cut=triple_time_window_infeasible_cut,
            quad_time_window_infeasible_cut=quad_time_window_infeasible_cut,
            pair_shadow_infeasible_cut=pair_shadow_infeasible_cut,
            triple_shadow_infeasible_cut=triple_shadow_infeasible_cut,
            triple_energy_infeasible_cut=triple_energy_infeasible_cut,
            negative_feasibility_search=True,
            forbidden_arc_patterns=tuple(forbidden_patterns),
            forbidden_task_sets=tuple(forbidden_task_sets),
        )
        negative_result = _with_compact_profile_payload(negative_result, profile)
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
                signature = column_signature_from_journey(column)
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
                pricing_rc = _compact_result_pricing_rc_for_column(negative_result, column_count=len(negative_columns))
                if pricing_rc is not None:
                    batch_pricing_rc_by_signature[signature] = pricing_rc
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
                profile=profile,
                phase_mode=phase_mode,
            )
        break

    if batch_negative_columns:
        harvest_payload = _compact_negative_harvest_payload(
            batch_negative_columns,
            duals,
            cut_context,
            negative_eps=negative_eps,
            candidate_negative_count=len(batch_negative_columns),
            max_selected=batch_target,
            pricing_rc_by_signature=batch_pricing_rc_by_signature,
            column_pool=column_pool,
            master_view=master_view,
            node_id=node_id,
            active_task_sets=active_task_sets,
            branch_context=branch_context,
        )
        selected_columns = tuple(harvest_payload.pop("_selected_columns"))
        manual_rc_values = tuple(_manual_reduced_cost(column, duals, cut_context) for column in selected_columns)
        manual_best = min(manual_rc_values) if manual_rc_values else None
        result = dict(last_negative_result or {})
        if not selected_columns:
            result.update(
                {
                    "status": "COMPACT_HIGHS_PRICING_BATCH_NO_ADDABLE_NEGATIVE",
                    "algorithm_status": "COMPACT_HIGHS_PRICING_BATCH_NO_ADDABLE_NEGATIVE",
                    "exact_status": "NOT_SOLVED",
                    "pricing_state": PricingState.INCOMPLETE_LIMIT.value,
                    "negative_found": True,
                    "negative_column_count": 0,
                    "can_certify_no_negative": False,
                    "uses_true_dual_bpc_certificate": False,
                    "pricing_rc_audit_pass": True,
                    "journeys": tuple(),
                    "journey_count": 0,
                    "compact_negative_batch_enabled": True,
                    "compact_negative_batch_target": batch_target,
                    "compact_negative_no_good_scope": no_good_scope,
                    "compact_negative_search_cap_sec": negative_search_cap,
                    "compact_negative_batch_found_count": 0,
                    "compact_negative_batch_search_call_count": len(phase_payloads),
                    "forbidden_arc_pattern_count": len(forbidden_patterns),
                    "forbidden_arc_patterns_can_certify_full_space": False,
                    "forbidden_task_set_count": len(forbidden_task_sets),
                    "forbidden_task_sets_can_certify_full_space": False,
                    "wall_time_sec": round(perf_counter() - start, 6),
                    "note": (
                        "Compact final judge found true negative candidates, but harvesting "
                        "rejected all of them as non-addable. This cannot advance the master "
                        "and cannot certify no-negative, so the runner falls through to the "
                        "unrestricted proof phase when time remains."
                    ),
                    **harvest_payload,
                }
            )
            last_negative_result = result
        else:
            result.update(
                {
                    "status": "COMPACT_HIGHS_PRICING_BATCH_FOUND_NEGATIVE",
                    "algorithm_status": "COMPACT_HIGHS_PRICING_BATCH_FOUND_NEGATIVE",
                    "exact_status": "NOT_SOLVED",
                    "pricing_state": PricingState.FOUND_NEGATIVE.value,
                    "best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
                    "manual_best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
                    "pricing_best_reduced_cost": None if manual_best is None else round(float(manual_best), 9),
                    "negative_found": True,
                    "negative_column_count": len(selected_columns),
                    "can_certify_no_negative": False,
                    "uses_true_dual_bpc_certificate": False,
                    "pricing_rc_audit_pass": True,
                    "journeys": selected_columns,
                    "journey_count": len(selected_columns),
                    "has_feasible_incumbent": True,
                    "compact_negative_batch_enabled": True,
                    "compact_negative_batch_target": batch_target,
                    "compact_negative_no_good_scope": no_good_scope,
                    "compact_negative_search_cap_sec": negative_search_cap,
                    "compact_negative_batch_found_count": len(selected_columns),
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
                    **harvest_payload,
                }
            )
            return _compact_final_judge_result(
                data,
                context=context,
                branch_context=branch_context,
                cut_context=cut_context,
                result=result,
                state=PricingState.FOUND_NEGATIVE,
                negative_columns=selected_columns,
                can_certify=False,
                started_at=start,
                phase="negative_feasibility_batch",
                phase_payloads=phase_payloads,
                profile=profile,
                phase_mode=phase_mode,
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
            mtz_connectivity=bool(profile["proof_mtz_connectivity"]),
            mtz_endpoint_order_cuts=bool(profile["mtz_endpoint_order_cuts"]),
            pair_adjacency_cuts=bool(profile["pair_adjacency_cuts"]),
            latest_service_start_slot_bound=bool(profile["latest_service_start_slot_bound"]),
            time_window_arc_pruning=bool(profile["time_window_arc_pruning"]),
            sortie_slot_position_bounds=sortie_slot_position_bounds,
        service_start_depot_travel_lb=service_start_depot_travel_lb,
        task_to_depot_return_travel_lb=task_to_depot_return_travel_lb,
        pair_route_duration_lb=pair_route_duration_lb,
        pair_weighted_completion_lb=pair_weighted_completion_lb,
        demand_cover_cut=demand_cover_cut,
            single_task_energy_lb=single_task_energy_lb,
            single_task_shadow_lb=single_task_shadow_lb,
            pair_energy_lb=pair_energy_lb,
            pair_shadow_lb=pair_shadow_lb,
            pair_energy_infeasible_cut=pair_energy_infeasible_cut,
            pair_time_window_infeasible_cut=pair_time_window_infeasible_cut,
            pair_time_window_precedence_cut=pair_time_window_precedence_cut,
            triple_time_window_infeasible_cut=triple_time_window_infeasible_cut,
            quad_time_window_infeasible_cut=quad_time_window_infeasible_cut,
            pair_shadow_infeasible_cut=pair_shadow_infeasible_cut,
            triple_shadow_infeasible_cut=triple_shadow_infeasible_cut,
            triple_energy_infeasible_cut=triple_energy_infeasible_cut,
        )
        result = _with_compact_profile_payload(result, profile)
        state, negative_columns, can_certify = _compact_result_state(
            result,
            duals,
            cut_context,
            negative_eps=negative_eps,
        )
        if state == PricingState.FOUND_NEGATIVE and optimization_harvest_target > 1:
            optimization_columns: list[JourneyColumn] = list(negative_columns)
            optimization_pricing_rc_by_signature: dict[object, float] = {}
            for column in negative_columns:
                signature = column_signature_from_journey(column)
                pricing_rc = _compact_result_pricing_rc_for_column(result, column_count=len(negative_columns))
                if pricing_rc is not None:
                    optimization_pricing_rc_by_signature[signature] = pricing_rc
                pattern = _journey_forbidden_arc_pattern(column)
                task_set = _journey_forbidden_task_set(column)
                if (
                    optimization_harvest_no_good_scope in {"arc", "arc_and_task_set"}
                    and pattern
                    and pattern not in seen_patterns
                ):
                    seen_patterns.add(pattern)
                    forbidden_patterns.append(pattern)
                if (
                    optimization_harvest_no_good_scope in {"task_set", "arc_and_task_set"}
                    and task_set
                    and task_set not in seen_task_sets
                ):
                    seen_task_sets.add(task_set)
                    forbidden_task_sets.append(task_set)
            optimization_phase_payloads = {
                **phase_payloads,
                "optimization_proof": _compact_phase_summary(result),
            }
            for harvest_index in range(2, optimization_harvest_target + 1):
                remaining_for_harvest = _remaining_compact_time(wall_time_limit_sec, started_at=start)
                if remaining_for_harvest is not None and remaining_for_harvest <= 0.25:
                    break
                restricted_result = solve_highs_compact_single_journey_pricing(
                    data,
                    duals,
                    time_limit_sec=remaining_for_harvest,
                    threads=1,
                    mip_gap=0.0,
                    negative_eps=negative_eps,
                    mtz_connectivity=bool(profile["proof_mtz_connectivity"]),
                    mtz_endpoint_order_cuts=bool(profile["mtz_endpoint_order_cuts"]),
                    pair_adjacency_cuts=bool(profile["pair_adjacency_cuts"]),
                    latest_service_start_slot_bound=bool(profile["latest_service_start_slot_bound"]),
                    time_window_arc_pruning=bool(profile["time_window_arc_pruning"]),
                    sortie_slot_position_bounds=sortie_slot_position_bounds,
                    service_start_depot_travel_lb=service_start_depot_travel_lb,
                    task_to_depot_return_travel_lb=task_to_depot_return_travel_lb,
                    pair_route_duration_lb=pair_route_duration_lb,
                    pair_weighted_completion_lb=pair_weighted_completion_lb,
                    demand_cover_cut=demand_cover_cut,
                    single_task_energy_lb=single_task_energy_lb,
                    single_task_shadow_lb=single_task_shadow_lb,
                    pair_energy_lb=pair_energy_lb,
                    pair_shadow_lb=pair_shadow_lb,
                    pair_energy_infeasible_cut=pair_energy_infeasible_cut,
                    pair_time_window_infeasible_cut=pair_time_window_infeasible_cut,
                    pair_time_window_precedence_cut=pair_time_window_precedence_cut,
                    triple_time_window_infeasible_cut=triple_time_window_infeasible_cut,
                    quad_time_window_infeasible_cut=quad_time_window_infeasible_cut,
                    pair_shadow_infeasible_cut=pair_shadow_infeasible_cut,
                    triple_shadow_infeasible_cut=triple_shadow_infeasible_cut,
                    triple_energy_infeasible_cut=triple_energy_infeasible_cut,
                    forbidden_arc_patterns=tuple(forbidden_patterns),
                    forbidden_task_sets=tuple(forbidden_task_sets),
                )
                restricted_result = _with_compact_profile_payload(restricted_result, profile)
                optimization_phase_payloads[f"optimization_harvest_{harvest_index}"] = _compact_phase_summary(
                    restricted_result
                )
                restricted_state, restricted_negative_columns, _restricted_can_certify = _compact_result_state(
                    restricted_result,
                    duals,
                    cut_context,
                    negative_eps=negative_eps,
                )
                if restricted_state != PricingState.FOUND_NEGATIVE:
                    break
                added_new = False
                for column in restricted_negative_columns:
                    signature = column_signature_from_journey(column)
                    pattern = _journey_forbidden_arc_pattern(column)
                    task_set = _journey_forbidden_task_set(column)
                    pattern_added = False
                    task_set_added = False
                    if (
                        optimization_harvest_no_good_scope in {"arc", "arc_and_task_set"}
                        and pattern
                        and pattern not in seen_patterns
                    ):
                        seen_patterns.add(pattern)
                        forbidden_patterns.append(pattern)
                        pattern_added = True
                    if (
                        optimization_harvest_no_good_scope in {"task_set", "arc_and_task_set"}
                        and task_set
                        and task_set not in seen_task_sets
                    ):
                        seen_task_sets.add(task_set)
                        forbidden_task_sets.append(task_set)
                        task_set_added = True
                    if not (pattern_added or task_set_added):
                        continue
                    optimization_columns.append(column)
                    pricing_rc = _compact_result_pricing_rc_for_column(
                        restricted_result,
                        column_count=len(restricted_negative_columns),
                    )
                    if pricing_rc is not None:
                        optimization_pricing_rc_by_signature[signature] = pricing_rc
                    added_new = True
                if not added_new:
                    break
            harvest_payload = _compact_negative_harvest_payload(
                optimization_columns,
                duals,
                cut_context,
                negative_eps=negative_eps,
                candidate_negative_count=len(optimization_columns),
                max_selected=optimization_harvest_target,
                source_phase="compact_final_judge_optimization_harvest",
                pricing_rc_by_signature=optimization_pricing_rc_by_signature,
                column_pool=column_pool,
                master_view=master_view,
                node_id=node_id,
                active_task_sets=active_task_sets,
                branch_context=branch_context,
            )
            selected_columns = tuple(harvest_payload.pop("_selected_columns"))
            if selected_columns:
                manual_rc_values = tuple(_manual_reduced_cost(column, duals, cut_context) for column in selected_columns)
                manual_best = min(manual_rc_values)
                result = dict(result)
                result.update(
                    {
                        "status": "COMPACT_HIGHS_PRICING_OPTIMIZATION_HARVEST_FOUND_NEGATIVE",
                        "algorithm_status": "COMPACT_HIGHS_PRICING_OPTIMIZATION_HARVEST_FOUND_NEGATIVE",
                        "exact_status": "NOT_SOLVED",
                        "pricing_state": PricingState.FOUND_NEGATIVE.value,
                        "best_reduced_cost": round(float(manual_best), 9),
                        "manual_best_reduced_cost": round(float(manual_best), 9),
                        "pricing_best_reduced_cost": round(float(manual_best), 9),
                        "negative_found": True,
                        "negative_column_count": len(selected_columns),
                        "can_certify_no_negative": False,
                        "uses_true_dual_bpc_certificate": False,
                        "pricing_rc_audit_pass": bool(harvest_payload.get("harvest_pricing_rc_audit_pass")),
                        "journeys": selected_columns,
                        "journey_count": len(selected_columns),
                        "has_feasible_incumbent": True,
                        "compact_optimization_harvest_enabled": True,
                        "compact_optimization_harvest_target": int(optimization_harvest_target),
                        "compact_optimization_harvest_no_good_scope": optimization_harvest_no_good_scope,
                        "compact_optimization_harvest_found_count": len(selected_columns),
                        "compact_optimization_harvest_search_call_count": len(
                            [key for key in optimization_phase_payloads if str(key).startswith("optimization")]
                        ),
                        "compact_negative_no_good_scope": no_good_scope,
                        "restricted_harvest_can_certify_no_negative": False,
                        "forbidden_arc_pattern_count": len(forbidden_patterns),
                        "forbidden_arc_patterns_can_certify_full_space": False,
                        "forbidden_task_set_count": len(forbidden_task_sets),
                        "forbidden_task_sets_can_certify_full_space": False,
                        "wall_time_sec": round(perf_counter() - start, 6),
                        "note": (
                            "Compact final judge used unrestricted optimization proof followed by "
                            "restricted no-good optimization harvest. Restricted harvest rows are "
                            "candidate discovery only and cannot certify no-negative."
                        ),
                        **harvest_payload,
                    }
                )
                return _compact_final_judge_result(
                    data,
                    context=context,
                    branch_context=branch_context,
                    cut_context=cut_context,
                    result=result,
                    state=PricingState.FOUND_NEGATIVE,
                    negative_columns=selected_columns,
                    can_certify=False,
                    started_at=start,
                    phase="optimization_harvest",
                    phase_payloads=optimization_phase_payloads,
                    profile=profile,
                    phase_mode=phase_mode,
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
            profile=profile,
            phase_mode=phase_mode,
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
        profile=profile,
        phase_mode=phase_mode,
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


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(str(name))
    if raw in {None, ""}:
        return bool(default)
    value = str(raw).strip().lower()
    if value in {"1", "true", "yes", "on", "enabled", "enable"}:
        return True
    if value in {"0", "false", "no", "off", "disabled", "disable"}:
        return False
    return bool(default)


def _compact_final_judge_profile_from_env() -> dict:
    raw = os.environ.get(COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILE_ENV)
    value = str(raw or "B4V2").strip().upper()
    aliases = {
        "": "B4V2",
        "DEFAULT": "B4V2",
        "V2": "B4V2",
        "B4V2": "B4V2",
        "LATEST_START": "B4V2",
        "LATEST_START_ONLY": "B4V2",
        "V4": "V4",
        "B4V4": "V4",
        "COMBINED": "V4",
        "B4V4_COMBINED": "V4",
    }
    key = aliases.get(value, "B4V2")
    return dict(COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILES[key])


def _compact_final_judge_phase_mode_from_env() -> str:
    raw = os.environ.get(COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_ENV)
    value = str(raw or COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT).strip().lower()
    aliases = {
        "": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "default": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "harvest": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "harvest_then_proof": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "negative_then_proof": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
        "proof": "proof_only",
        "proof_only": "proof_only",
        "optimization_proof": "proof_only",
        "feasibility_proof": "feasibility_proof_only",
        "feasibility_proof_only": "feasibility_proof_only",
        "negative_feasibility_proof": "feasibility_proof_only",
        "negative_feasibility_proof_only": "feasibility_proof_only",
    }
    return aliases.get(value, COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT)


def _compact_profile_payload(profile: dict) -> dict:
    return {
        "compact_final_judge_profile": str(profile["name"]),
        "compact_final_judge_formulation_profile": str(profile["formulation_profile"]),
        "compact_final_judge_profile_env": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PROFILE_ENV,
        "compact_final_judge_profile_official_default": bool(profile["official_default"]),
    }


def _with_compact_profile_payload(result: dict, profile: dict) -> dict:
    merged = dict(result)
    merged.update(_compact_profile_payload(profile))
    return merged


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
    profile: dict | None = None,
    phase_mode: str = COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_DEFAULT,
) -> FinalJudgeResult:
    columns = tuple(result.get("journeys") or tuple())
    pricing_proof_kind = _compact_pricing_proof_kind(result, can_certify=can_certify)
    profile_payload = _compact_profile_payload(profile or _compact_final_judge_profile_from_env())
    global_remaining_rc_lb = _first_float(
        result.get("global_remaining_rc_lb"),
        result.get("global_remaining_rc_lower_bound"),
        result.get("dual_bound"),
        result.get("bound"),
    )
    unsupported_region_count = _compact_frontier_unsupported_region_count(result, pricing_proof_kind=pricing_proof_kind)
    payload = {
        **{key: value for key, value in result.items() if key != "journeys"},
        **profile_payload,
        "status": str(result.get("status") or "COMPACT_HIGHS_SINGLE_JOURNEY_PRICING"),
        "exact_status": str(result.get("exact_status") or "NOT_SOLVED"),
        "compact_pricing_phase": str(phase),
        "compact_pricing_phase_payloads": dict(phase_payloads),
        "compact_final_judge_phase_mode": str(phase_mode),
        "compact_final_judge_phase_mode_env": COMPACT_SINGLE_JOURNEY_FINAL_JUDGE_PHASE_MODE_ENV,
        "negative_feasibility_skipped_for_proof_only": bool(str(phase_mode) == "proof_only"),
        "negative_feasibility_full_space_proof_attempted": bool(
            result.get("negative_feasibility_full_space_proof_attempted")
        ),
        "negative_feasibility_full_space_proof_can_certify": bool(
            result.get("negative_feasibility_full_space_proof_can_certify")
        ),
        "task_count": len(data.task_ids),
        "max_direct_tasks": len(data.task_ids),
        "candidate_round_count": int(result.get("candidate_round_count") or result.get("compact_negative_batch_search_call_count") or 1),
        "candidate_round_limit": int(result.get("candidate_round_limit") or result.get("compact_negative_batch_target") or 1),
        "candidate_task_count": len(data.task_ids),
        "candidate_task_ids": list(data.task_ids),
        "pricing_state": state.value,
        "can_certify_no_negative": bool(can_certify),
        "uses_true_dual_bpc_certificate": bool(can_certify),
        "negative_found": bool(negative_columns) or bool(result.get("negative_found")) or state == PricingState.FOUND_NEGATIVE,
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
        "global_remaining_rc_lb": global_remaining_rc_lb,
        "global_remaining_rc_lb_valid": bool(global_remaining_rc_lb is not None),
        "global_remaining_rc_lb_coverage_complete": bool(can_certify),
        "frontier_region_count": int(result.get("frontier_region_count") or (1 if global_remaining_rc_lb is not None else 0)),
        "frontier_unsupported_region_count": int(unsupported_region_count),
        "pending_complete_min_rc": _first_float(
            result.get("pending_complete_min_rc"),
            result.get("best_reduced_cost"),
            result.get("manual_best_reduced_cost"),
        ),
        "pricing_proof_kind": pricing_proof_kind,
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


def _compact_negative_harvest_payload(
    columns: list[JourneyColumn],
    duals: JourneyDuals,
    cut_context: CutContext,
    *,
    negative_eps: float,
    candidate_negative_count: int,
    max_selected: int | None = None,
    source_phase: str = "compact_final_judge_negative_feasibility_batch",
    pricing_rc_by_signature: dict[object, float] | None = None,
    column_pool: ColumnPool | None = None,
    master_view: MasterColumnView | None = None,
    node_id: str = "root",
    active_task_sets: set[frozenset[str]] | None = None,
    branch_context: BranchContext | None = None,
) -> dict:
    audited: list[tuple[float, tuple[str, ...], JourneyColumn]] = []
    not_addable_count = 0
    for column in columns:
        true_rc = _manual_reduced_cost(column, duals, cut_context)
        if true_rc < -abs(float(negative_eps)):
            audited.append((float(true_rc), _journey_forbidden_task_set(column), column))
        else:
            not_addable_count += 1
    audited.sort(key=lambda row: (row[0], row[1]))
    active_task_set_lookup = {
        tuple(sorted(str(task_id) for task_id in row))
        for row in (active_task_sets or set())
    }
    new_rows: list[tuple[float, tuple[str, ...], JourneyColumn]] = []
    replacement_rows: list[tuple[float, tuple[str, ...], JourneyColumn]] = []
    selected_new_task_sets: set[tuple[str, ...]] = set()
    seen_task_sets: set[tuple[str, ...]] = set()
    for row in audited:
        _true_rc, task_set, _column = row
        seen_before = task_set in seen_task_sets
        seen_task_sets.add(task_set)
        if (
            task_set not in active_task_set_lookup
            and not seen_before
            and task_set not in selected_new_task_sets
        ):
            new_rows.append(row)
            selected_new_task_sets.add(task_set)
        else:
            replacement_rows.append(row)
    limit = len(audited) if max_selected is None else max(0, int(max_selected))
    selected: list[JourneyColumn] = []
    selected_task_set_rows: list[tuple[tuple[str, ...], bool]] = []
    addability_reports: list[dict] = []
    addability_audit_available = bool(column_pool is not None and master_view is not None)
    addability_rejected_count = 0
    addability_reject_reasons: dict[str, int] = {}
    pricing_lookup = pricing_rc_by_signature or {}
    for true_rc, task_set, column in new_rows + replacement_rows:
        pricing_rc = _optional_float(pricing_lookup.get(column_signature_from_journey(column)))
        addability_report = _compact_harvest_addability_report(
            column,
            true_rc=true_rc,
            pricing_rc=pricing_rc,
            column_pool=column_pool,
            master_view=master_view,
            node_id=node_id,
            active_task_sets=active_task_sets,
            branch_context=branch_context,
            cut_context=cut_context,
        )
        addability_reports.append(addability_report)
        if not addability_report["would_enter_master"]:
            addability_rejected_count += 1
            reason = str(addability_report.get("reject_reason") or addability_report.get("addability_reason") or "not_addable")
            addability_reject_reasons[reason] = int(addability_reject_reasons.get(reason, 0)) + 1
            continue
        selected.append(column)
        selected_task_set_rows.append((task_set, task_set not in active_task_set_lookup))
        if len(selected) >= limit:
            break
    selected_new_task_sets_count, replacement_task_set_count = _compact_selected_task_set_counts(
        selected_task_set_rows,
        active_task_set_lookup=active_task_set_lookup,
    )
    duplicate_count = max(0, len(audited) - len(seen_task_sets))
    selected_rc_values = tuple(_manual_reduced_cost(column, duals, cut_context) for column in selected)
    selected_pricing_rc_values = tuple(
        _optional_float(pricing_lookup.get(column_signature_from_journey(column)))
        for column in selected
    )
    selected_pricing_rc_available = bool(selected) and all(value is not None for value in selected_pricing_rc_values)
    selected_pricing_diffs = tuple(
        abs(float(manual_rc) - float(pricing_rc))
        for manual_rc, pricing_rc in zip(selected_rc_values, selected_pricing_rc_values)
        if pricing_rc is not None
    )
    pricing_rc_audit_pass = bool(
        selected_pricing_rc_available
        and len(selected_pricing_diffs) == len(selected_rc_values)
        and all(diff <= 1.0e-6 for diff in selected_pricing_diffs)
    )
    selected_task_set_tuples = tuple(_journey_forbidden_task_set(column) for column in selected)
    selected_addability_reports = tuple(
        row for row in addability_reports if row.get("selected_after_addability_audit")
    )
    return {
        "_selected_columns": tuple(selected),
        "harvest_schema_version": "lunar_ice_bpc.b4_1_final_judge_harvest.v1",
        "harvest_source_phase": str(source_phase),
        "harvest_target": None if max_selected is None else int(max_selected),
        "harvest_candidate_negative_count": int(candidate_negative_count),
        "harvest_selected_count": len(selected),
        "harvest_selected_new_task_set_count": int(selected_new_task_sets_count),
        "harvest_selected_replacement_task_set_count": int(replacement_task_set_count),
        "harvest_rejected_duplicate_count": int(duplicate_count),
        "harvest_rejected_not_addable_count": int(not_addable_count + addability_rejected_count),
        "harvest_addability_audit_available": addability_audit_available,
        "harvest_selected_all_addability_audited": addability_audit_available,
        "harvest_selected_all_would_enter_master": all(
            bool(row.get("would_enter_master")) for row in addability_reports if row.get("selected_after_addability_audit")
        ),
        "harvest_addability_reject_reasons": dict(sorted(addability_reject_reasons.items())),
        "harvest_manual_rc_audit_pass": all(value < -abs(float(negative_eps)) for value in selected_rc_values),
        "harvest_pricing_rc_audit_available": selected_pricing_rc_available,
        "harvest_pricing_rc_audit_pass": pricing_rc_audit_pass,
        "harvest_pricing_rc_max_abs_diff": (
            None if not selected_pricing_diffs else round(float(max(selected_pricing_diffs)), 9)
        ),
        "harvest_branch_context_audit_pass": all(
            bool(row.get("is_allowed_by_branch")) for row in selected_addability_reports
        ),
        "harvest_cut_context_audit_pass": all(
            bool(row.get("is_allowed_by_cut_context")) for row in selected_addability_reports
        ),
        "harvest_addability_audit_pass": (
            all(bool(row.get("would_enter_master")) for row in selected_addability_reports)
            if addability_audit_available
            else None
        ),
        "harvest_best_true_rc": None if not selected_rc_values else round(float(min(selected_rc_values)), 9),
        "harvest_worst_selected_true_rc": None if not selected_rc_values else round(float(max(selected_rc_values)), 9),
        "harvest_avg_pairwise_jaccard": _avg_pairwise_jaccard(selected_task_set_tuples),
        "harvest_priority": "prefer_new_task_set_then_true_rc_then_replacements",
        "restricted_harvest_can_certify_no_negative": False,
        "harvest_reports": addability_reports,
    }


def _compact_harvest_addability_report(
    column: JourneyColumn,
    *,
    true_rc: float,
    pricing_rc: float | None = None,
    column_pool: ColumnPool | None,
    master_view: MasterColumnView | None,
    node_id: str,
    active_task_sets: set[frozenset[str]] | None,
    branch_context: BranchContext | None,
    cut_context: CutContext,
) -> dict:
    signature = column_signature_from_journey(column)
    branch_allowed = journey_satisfies_branch_context(column, branch_context)
    cut_coefficients = cut_coefficients_for_journey(column, cut_context)
    cut_allowed = True
    if column_pool is None or master_view is None:
        return {
            "task_set": list(signature.task_set),
            "true_reduced_cost": round(float(true_rc), 9),
            "pricing_reduced_cost": None if pricing_rc is None else round(float(pricing_rc), 9),
            "manual_pricing_rc_abs_diff": None
            if pricing_rc is None
            else round(abs(float(true_rc) - float(pricing_rc)), 9),
            "would_enter_master": True,
            "selected_after_addability_audit": True,
            "addability_audit_available": False,
            "addability_reason": "addability_audit_not_available",
            "reject_reason": "",
            "pool_contains_signature": False,
            "current_master_contains_signature": False,
            "is_allowed_by_branch": bool(branch_allowed),
            "is_allowed_by_cut_context": bool(cut_allowed),
            "would_change_active_support": True,
        }
    bpc_column = BpcColumn(signature=signature, objective=column.objective, payload=column)
    report = column_pool.addability_check(
        bpc_column,
        {
            "master_view": master_view,
            "node_id": str(node_id),
            "active_task_sets": active_task_sets or set(),
            "is_allowed_by_branch": branch_allowed,
            "is_allowed_by_cut_context": cut_allowed,
            "cut_coefficients": cut_coefficients,
        },
    )
    return {
        "task_set": list(signature.task_set),
        "true_reduced_cost": round(float(true_rc), 9),
        "pricing_reduced_cost": None if pricing_rc is None else round(float(pricing_rc), 9),
        "manual_pricing_rc_abs_diff": None
        if pricing_rc is None
        else round(abs(float(true_rc) - float(pricing_rc)), 9),
        "would_enter_master": bool(report.would_enter_master),
        "selected_after_addability_audit": bool(report.would_enter_master),
        "addability_audit_available": True,
        "addability_reason": report.reason,
        "reject_reason": report.reject_reason,
        "pool_contains_signature": report.pool_contains_signature,
        "current_master_contains_signature": report.current_master_contains_signature,
        "is_allowed_by_branch": report.is_allowed_by_branch,
        "is_allowed_by_cut_context": report.is_allowed_by_cut_context,
        "would_change_active_support": report.would_change_active_support,
    }


def _compact_selected_task_set_counts(
    rows: list[tuple[tuple[str, ...], bool]],
    *,
    active_task_set_lookup: set[tuple[str, ...]],
) -> tuple[int, int]:
    selected_new_task_sets: set[tuple[str, ...]] = set()
    new_count = 0
    replacement_count = 0
    for task_set, candidate_is_new in rows:
        if candidate_is_new and task_set not in active_task_set_lookup and task_set not in selected_new_task_sets:
            new_count += 1
            selected_new_task_sets.add(task_set)
        else:
            replacement_count += 1
    return new_count, replacement_count


def _compact_result_pricing_rc_for_column(result: dict, *, column_count: int) -> float | None:
    if int(column_count) != 1:
        return None
    return _optional_float(
        result.get("pricing_model_reduced_cost"),
        result.get("model_objective"),
        result.get("pricing_best_reduced_cost"),
        result.get("best_reduced_cost"),
    )


def _optional_float(*values: object) -> float | None:
    for value in values:
        if value is None or value == "":
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


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


def _compact_pricing_proof_kind(result: dict, *, can_certify: bool) -> str:
    if can_certify:
        return "EXHAUSTIVE_NO_NEGATIVE"
    explicit = result.get("pricing_proof_kind")
    if explicit in {
        "NONE",
        "EXHAUSTIVE_NO_NEGATIVE",
        "FRONTIER_BOUND_INCOMPLETE",
        "FRONTIER_BOUND_NO_NEGATIVE",
    }:
        if explicit in {"EXHAUSTIVE_NO_NEGATIVE", "FRONTIER_BOUND_NO_NEGATIVE"}:
            return "FRONTIER_BOUND_INCOMPLETE"
        return str(explicit)
    if result.get("negative_feasibility_search_enabled") or result.get("compact_negative_batch_enabled"):
        return "FRONTIER_BOUND_INCOMPLETE"
    if result.get("pricing_complete_by_compact_milp") and result.get("can_certify_no_negative") is True:
        return "EXHAUSTIVE_NO_NEGATIVE"
    return "FRONTIER_BOUND_INCOMPLETE"


def _compact_frontier_unsupported_region_count(result: dict, *, pricing_proof_kind: str) -> int:
    if pricing_proof_kind in {"EXHAUSTIVE_NO_NEGATIVE", "FRONTIER_BOUND_NO_NEGATIVE"}:
        return 0
    explicit = result.get("frontier_unsupported_region_count")
    if explicit is not None:
        try:
            explicit_count = max(0, int(explicit))
            if pricing_proof_kind == "FRONTIER_BOUND_INCOMPLETE":
                return max(1, explicit_count)
            return explicit_count
        except (TypeError, ValueError):
            pass
    forbidden_count = int(result.get("forbidden_arc_pattern_count") or 0) + int(result.get("forbidden_task_set_count") or 0)
    return max(1, forbidden_count)


def _first_float(*values: object) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            return round(float(value), 9)
        except (TypeError, ValueError):
            continue
    return None


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
        "compact_final_judge_profile": result.get("compact_final_judge_profile"),
        "compact_final_judge_formulation_profile": result.get("compact_final_judge_formulation_profile"),
        "compact_final_judge_profile_official_default": result.get("compact_final_judge_profile_official_default"),
        "compact_final_judge_phase_mode": result.get("compact_final_judge_phase_mode"),
        "compact_optimization_harvest_enabled": result.get("compact_optimization_harvest_enabled"),
        "compact_optimization_harvest_target": result.get("compact_optimization_harvest_target"),
        "compact_optimization_harvest_no_good_scope": result.get(
            "compact_optimization_harvest_no_good_scope"
        ),
        "compact_optimization_harvest_found_count": result.get("compact_optimization_harvest_found_count"),
        "compact_optimization_harvest_search_call_count": result.get(
            "compact_optimization_harvest_search_call_count"
        ),
        "negative_feasibility_skipped_for_proof_only": result.get("negative_feasibility_skipped_for_proof_only"),
        "negative_feasibility_full_space_proof_attempted": result.get(
            "negative_feasibility_full_space_proof_attempted"
        ),
        "negative_feasibility_full_space_proof_can_certify": result.get(
            "negative_feasibility_full_space_proof_can_certify"
        ),
        "mtz_connectivity_enabled": result.get("mtz_connectivity_enabled"),
        "mtz_endpoint_order_cuts_enabled": result.get("mtz_endpoint_order_cuts_enabled"),
        "mtz_endpoint_order_cut_count": result.get("mtz_endpoint_order_cut_count"),
        "pair_adjacency_cuts_enabled": result.get("pair_adjacency_cuts_enabled"),
        "pair_adjacency_cut_count": result.get("pair_adjacency_cut_count"),
        "sortie_slots_per_journey": result.get("sortie_slots_per_journey"),
        "sortie_slot_bound_source": result.get("sortie_slot_bound_source"),
        "sortie_slot_horizon_count_bound": result.get("sortie_slot_horizon_count_bound"),
        "latest_service_start_slot_bound_enabled": result.get("latest_service_start_slot_bound_enabled"),
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
        "sortie_slot_position_bounds_enabled": result.get("sortie_slot_position_bounds_enabled"),
        "sortie_slot_position_bound_count": result.get("sortie_slot_position_bound_count"),
        "sortie_slot_latest_start_upper_bound": result.get("sortie_slot_latest_start_upper_bound"),
        "service_start_depot_travel_lb_enabled": result.get("service_start_depot_travel_lb_enabled"),
        "service_start_depot_travel_lb_count": result.get("service_start_depot_travel_lb_count"),
        "service_start_depot_travel_lb_min": result.get("service_start_depot_travel_lb_min"),
        "service_start_depot_travel_lb_max": result.get("service_start_depot_travel_lb_max"),
        "task_to_depot_return_travel_lb_enabled": result.get("task_to_depot_return_travel_lb_enabled"),
        "task_to_depot_return_travel_lb_count": result.get("task_to_depot_return_travel_lb_count"),
        "task_to_depot_return_travel_lb_min": result.get("task_to_depot_return_travel_lb_min"),
        "task_to_depot_return_travel_lb_max": result.get("task_to_depot_return_travel_lb_max"),
        "pair_route_duration_lb_enabled": result.get("pair_route_duration_lb_enabled"),
        "pair_route_duration_lb_count": result.get("pair_route_duration_lb_count"),
        "pair_route_duration_lb_min": result.get("pair_route_duration_lb_min"),
        "pair_route_duration_lb_max": result.get("pair_route_duration_lb_max"),
        "pair_weighted_completion_lb_enabled": result.get("pair_weighted_completion_lb_enabled"),
        "pair_weighted_completion_lb_count": result.get("pair_weighted_completion_lb_count"),
        "pair_weighted_completion_lb_min": result.get("pair_weighted_completion_lb_min"),
        "pair_weighted_completion_lb_max": result.get("pair_weighted_completion_lb_max"),
        "demand_cover_cut_enabled": result.get("demand_cover_cut_enabled"),
        "demand_cover_cut_count": result.get("demand_cover_cut_count"),
        "demand_cover_subset_count": result.get("demand_cover_subset_count"),
        "demand_cover_max_size": result.get("demand_cover_max_size"),
        "demand_cover_min_demand": result.get("demand_cover_min_demand"),
        "demand_cover_max_demand": result.get("demand_cover_max_demand"),
        "single_task_energy_lb_enabled": result.get("single_task_energy_lb_enabled"),
        "single_task_energy_lb_count": result.get("single_task_energy_lb_count"),
        "single_task_energy_lb_min": result.get("single_task_energy_lb_min"),
        "single_task_energy_lb_max": result.get("single_task_energy_lb_max"),
        "single_task_shadow_lb_enabled": result.get("single_task_shadow_lb_enabled"),
        "single_task_shadow_lb_count": result.get("single_task_shadow_lb_count"),
        "single_task_shadow_lb_min": result.get("single_task_shadow_lb_min"),
        "single_task_shadow_lb_max": result.get("single_task_shadow_lb_max"),
        "pair_energy_lb_enabled": result.get("pair_energy_lb_enabled"),
        "pair_energy_lb_count": result.get("pair_energy_lb_count"),
        "pair_energy_lb_min": result.get("pair_energy_lb_min"),
        "pair_energy_lb_max": result.get("pair_energy_lb_max"),
        "pair_energy_lb_exceeds_limit_count": result.get("pair_energy_lb_exceeds_limit_count"),
        "pair_shadow_lb_enabled": result.get("pair_shadow_lb_enabled"),
        "pair_shadow_lb_count": result.get("pair_shadow_lb_count"),
        "pair_shadow_lb_min": result.get("pair_shadow_lb_min"),
        "pair_shadow_lb_max": result.get("pair_shadow_lb_max"),
        "pair_shadow_lb_exceeds_limit_count": result.get("pair_shadow_lb_exceeds_limit_count"),
        "pair_energy_infeasible_cut_enabled": result.get("pair_energy_infeasible_cut_enabled"),
        "pair_energy_infeasible_cut_count": result.get("pair_energy_infeasible_cut_count"),
        "pair_energy_infeasible_pair_count": result.get("pair_energy_infeasible_pair_count"),
        "pair_time_window_infeasible_cut_enabled": result.get("pair_time_window_infeasible_cut_enabled"),
        "pair_time_window_infeasible_cut_count": result.get("pair_time_window_infeasible_cut_count"),
        "pair_time_window_infeasible_pair_count": result.get("pair_time_window_infeasible_pair_count"),
        "pair_time_window_infeasible_margin_min": result.get("pair_time_window_infeasible_margin_min"),
        "pair_time_window_infeasible_margin_max": result.get("pair_time_window_infeasible_margin_max"),
        "pair_time_window_precedence_cut_enabled": result.get("pair_time_window_precedence_cut_enabled"),
        "pair_time_window_precedence_cut_count": result.get("pair_time_window_precedence_cut_count"),
        "pair_time_window_precedence_pair_count": result.get("pair_time_window_precedence_pair_count"),
        "pair_time_window_precedence_margin_min": result.get("pair_time_window_precedence_margin_min"),
        "pair_time_window_precedence_margin_max": result.get("pair_time_window_precedence_margin_max"),
        "triple_time_window_infeasible_cut_enabled": result.get("triple_time_window_infeasible_cut_enabled"),
        "triple_time_window_infeasible_cut_count": result.get("triple_time_window_infeasible_cut_count"),
        "triple_time_window_infeasible_triple_count": result.get("triple_time_window_infeasible_triple_count"),
        "triple_time_window_infeasible_margin_min": result.get("triple_time_window_infeasible_margin_min"),
        "triple_time_window_infeasible_margin_max": result.get("triple_time_window_infeasible_margin_max"),
        "quad_time_window_infeasible_cut_enabled": result.get("quad_time_window_infeasible_cut_enabled"),
        "quad_time_window_infeasible_cut_count": result.get("quad_time_window_infeasible_cut_count"),
        "quad_time_window_infeasible_quad_count": result.get("quad_time_window_infeasible_quad_count"),
        "quad_time_window_infeasible_margin_min": result.get("quad_time_window_infeasible_margin_min"),
        "quad_time_window_infeasible_margin_max": result.get("quad_time_window_infeasible_margin_max"),
        "pair_shadow_infeasible_cut_enabled": result.get("pair_shadow_infeasible_cut_enabled"),
        "pair_shadow_infeasible_cut_count": result.get("pair_shadow_infeasible_cut_count"),
        "pair_shadow_infeasible_pair_count": result.get("pair_shadow_infeasible_pair_count"),
        "pair_shadow_infeasible_lb_min": result.get("pair_shadow_infeasible_lb_min"),
        "pair_shadow_infeasible_lb_max": result.get("pair_shadow_infeasible_lb_max"),
        "triple_shadow_infeasible_cut_enabled": result.get("triple_shadow_infeasible_cut_enabled"),
        "triple_shadow_infeasible_cut_count": result.get("triple_shadow_infeasible_cut_count"),
        "triple_shadow_infeasible_triple_count": result.get("triple_shadow_infeasible_triple_count"),
        "triple_shadow_infeasible_lb_min": result.get("triple_shadow_infeasible_lb_min"),
        "triple_shadow_infeasible_lb_max": result.get("triple_shadow_infeasible_lb_max"),
        "triple_energy_infeasible_cut_enabled": result.get("triple_energy_infeasible_cut_enabled"),
        "triple_energy_infeasible_cut_count": result.get("triple_energy_infeasible_cut_count"),
        "triple_energy_infeasible_triple_count": result.get("triple_energy_infeasible_triple_count"),
        "triple_energy_infeasible_lb_min": result.get("triple_energy_infeasible_lb_min"),
        "triple_energy_infeasible_lb_max": result.get("triple_energy_infeasible_lb_max"),
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
