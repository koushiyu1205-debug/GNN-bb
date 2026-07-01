"""Fail-closed fixed-graph exhaustive pricing closure loop."""

from __future__ import annotations

from typing import Iterable

from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.certificates.completion_bound_consistency import (
    build_completion_bound_consistency_audit,
)
from lunar_ice_bpc.exact.certificates.dual_binding import build_rmp_dual_binding_from_result
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost, solve_restricted_journey_rmp
from lunar_ice_bpc.exact.pricing.journey_pricing import DirectPricingCache, price_exhaustive_direct_journey_columns


def run_fixed_graph_pricing_closure(
    data: LunarIceData,
    initial_columns: Iterable[JourneyColumn],
    *,
    max_direct_tasks: int = 5,
    max_rounds: int = 3,
    negative_eps: float = 1.0e-6,
    max_columns_per_round: int = 64,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> dict:
    """Run a fail-closed exhaustive fixed-graph pricing closure loop.

    The loop is diagnostic until every true-dual closure gate passes. Once
    pricing completeness, RMP optimality, dual binding, completion-bound
    consistency, and nonnegative reduced cost are all verified, it certifies a
    scoped fixed-logical-graph BPC node LP bound. It never certifies a full BPC
    tree optimum.
    """

    cut_context = cut_context or CutContext()
    branch_context = branch_context or BranchContext()
    if len(data.task_ids) > int(max_direct_tasks):
        return {
            "schema_version": "lunar_ice_bpc.fixed_graph_pricing_closure.v1",
            "status": "SKIPPED_TOO_LARGE_FOR_FIXED_GRAPH_CLOSURE",
            "exact_status": "NOT_SOLVED",
            "task_count": len(data.task_ids),
            "max_direct_tasks": int(max_direct_tasks),
            "round_count": 0,
            "added_column_count": 0,
            "fixed_graph_no_negative_proved": False,
            "uses_true_dual_bpc_certificate": False,
            "lower_bound_official": False,
            "can_certify_no_negative": False,
            "note": f"task_count={len(data.task_ids)} exceeds max_direct_tasks={max_direct_tasks}",
        }

    columns = list(initial_columns)
    seen = {_column_signature(column) for column in columns}
    cache = DirectPricingCache()
    history: list[dict] = []
    added_total = 0
    last_rmp = None
    last_pricing = None
    for round_index in range(1, int(max_rounds) + 1):
        rmp = solve_restricted_journey_rmp(
            data.task_ids,
            columns,
            fleet_size=data.fleet_size,
            cut_context=cut_context,
            branch_context=branch_context,
        )
        last_rmp = rmp
        if rmp.status != "RESTRICTED_RMP_OPTIMAL":
            return _payload(
                status="FIXED_GRAPH_CLOSURE_RMP_NOT_OPTIMAL",
                round_count=round_index,
                added_column_count=added_total,
                rmp=rmp,
                pricing=last_pricing,
                history=history,
                data=data,
                max_direct_tasks=max_direct_tasks,
                negative_eps=negative_eps,
                cut_context=cut_context,
                branch_context=branch_context,
                note="Stopped because the restricted RMP did not solve to OPTIMAL.",
            )
        pricing, priced_columns = price_exhaustive_direct_journey_columns(
            data,
            rmp.duals,
            negative_eps=negative_eps,
            max_direct_tasks=int(max_direct_tasks),
            cache=cache,
            completion_bound_enabled=True,
            cut_context=cut_context,
            branch_context=branch_context,
        )
        last_pricing = pricing
        negative_columns = [
            column
            for column in priced_columns
            if manual_journey_reduced_cost(column, rmp.duals, cut_coefficients=cut_context.coefficients_for(column))
            < -abs(float(negative_eps))
        ]
        added_columns: list[JourneyColumn] = []
        for column in negative_columns:
            signature = _column_signature(column)
            if signature in seen:
                continue
            seen.add(signature)
            columns.append(column)
            added_columns.append(column)
            if len(added_columns) >= max(1, int(max_columns_per_round)):
                break
        added_total += len(added_columns)
        history.append(
            {
                "round": round_index,
                "rmp_status": rmp.status,
                "rmp_bound": rmp.objective_bound,
                "rmp_min_reduced_cost": rmp.min_reduced_cost,
                "pricing_status": pricing.get("status"),
                "pricing_complete_for_all_task_subsets": pricing.get("pricing_complete_for_all_task_subsets"),
                "best_reduced_cost": pricing.get("best_reduced_cost"),
                "negative_column_count": len(negative_columns),
                "added_column_count": len(added_columns),
                "active_column_count": rmp.active_column_count,
                "candidate_column_count": len(priced_columns),
            }
        )
        if not negative_columns:
            return _payload(
                status="FIXED_GRAPH_PRICING_CLOSED",
                round_count=round_index,
                added_column_count=added_total,
                rmp=rmp,
                pricing=pricing,
                history=history,
                data=data,
                max_direct_tasks=max_direct_tasks,
                negative_eps=negative_eps,
                cut_context=cut_context,
                branch_context=branch_context,
                fixed_graph_no_negative_proved=True,
                note=(
                    "Exhaustive direct-label pricing found no negative fixed-graph column; the result "
                    "certifies only if the true-dual closure gates pass."
                ),
            )
        if not added_columns:
            return _payload(
                status="FIXED_GRAPH_CLOSURE_STALLED_ON_DUPLICATE_NEGATIVE",
                round_count=round_index,
                added_column_count=added_total,
                rmp=rmp,
                pricing=pricing,
                history=history,
                data=data,
                max_direct_tasks=max_direct_tasks,
                negative_eps=negative_eps,
                cut_context=cut_context,
                branch_context=branch_context,
                note="Exhaustive fixed-graph pricing found only duplicate negative columns; fail closed.",
            )

    final_rmp = solve_restricted_journey_rmp(
        data.task_ids,
        columns,
        fleet_size=data.fleet_size,
        cut_context=cut_context,
        branch_context=branch_context,
    )
    return _payload(
        status="FIXED_GRAPH_CLOSURE_ROUND_LIMIT",
        round_count=int(max_rounds),
        added_column_count=added_total,
        rmp=final_rmp,
        pricing=last_pricing,
        history=history,
        data=data,
        max_direct_tasks=max_direct_tasks,
        negative_eps=negative_eps,
        cut_context=cut_context,
        branch_context=branch_context,
        note=f"Stopped after max_rounds={max_rounds}; fixed-graph pricing may still find negative columns.",
    )


def _payload(
    *,
    status: str,
    round_count: int,
    added_column_count: int,
    rmp,
    pricing: dict | None,
    history: list[dict],
    data: LunarIceData,
    max_direct_tasks: int,
    negative_eps: float,
    cut_context: CutContext,
    branch_context: BranchContext,
    fixed_graph_no_negative_proved: bool = False,
    note: str,
) -> dict:
    pricing = pricing or {}
    dual_binding = (
        build_rmp_dual_binding_from_result(
            rmp,
            source="fixed_graph_pricing_closure",
            binding_scope="fixed_logical_graph_exhaustive_pricing_closure",
            pricing_source=str(pricing.get("status") or ""),
        )
        if rmp is not None
        else {
            "schema_version": "lunar_ice_bpc.rmp_dual_binding.v1",
            "status": "RMP_DUAL_VECTOR_UNBOUND",
            "dual_vector_bound_to_rmp": False,
            "missing_inputs": ["rmp_missing"],
        }
    )
    completion_bound_audit = (
        build_completion_bound_consistency_audit(
            data,
            rmp.duals,
            max_direct_tasks=int(max_direct_tasks),
            negative_eps=negative_eps,
            cut_context=cut_context,
            branch_context=branch_context,
        )
        if rmp is not None
        else {
            "schema_version": "lunar_ice_bpc.completion_bound_consistency.v1",
            "status": "COMPLETION_BOUND_AUDIT_SKIPPED_RMP_MISSING",
            "consistent": False,
            "can_certify_no_negative": False,
            "exact_status_effect": "none",
            "mutates_solver": False,
        }
    )
    closure_certifies = _closure_can_certify(
        status=status,
        fixed_graph_no_negative_proved=fixed_graph_no_negative_proved,
        pricing=pricing,
        rmp=rmp,
        dual_binding=dual_binding,
        completion_bound_audit=completion_bound_audit,
        negative_eps=negative_eps,
    )
    return {
        "schema_version": "lunar_ice_bpc.fixed_graph_pricing_closure.v1",
        "status": status,
        "exact_status": (
            "BPC_NO_NEGATIVE_CERTIFIED"
            if closure_certifies
            else ("NOT_BPC_CERTIFIED" if fixed_graph_no_negative_proved else "NOT_SOLVED")
        ),
        "evaluation_scope": "fixed_logical_graph_exhaustive_direct_pricing",
        "round_count": int(round_count),
        "added_column_count": int(added_column_count),
        "final_rmp_status": rmp.status if rmp is not None else None,
        "final_bound": rmp.objective_bound if rmp is not None else None,
        "final_min_reduced_cost": rmp.min_reduced_cost if rmp is not None else None,
        "final_active_column_count": rmp.active_column_count if rmp is not None else None,
        "last_pricing_status": pricing.get("status"),
        "last_best_reduced_cost": pricing.get("best_reduced_cost"),
        "last_negative_found": pricing.get("negative_found"),
        "last_pricing_complete_for_all_task_subsets": pricing.get("pricing_complete_for_all_task_subsets"),
        "dual_vector_binding": dual_binding,
        "completion_bound_consistency": completion_bound_audit,
        "fixed_graph_no_negative_proved": bool(fixed_graph_no_negative_proved),
        "uses_true_dual_bpc_certificate": bool(closure_certifies),
        "lower_bound_official": bool(closure_certifies),
        "can_certify_no_negative": bool(closure_certifies),
        "history": list(history),
        "exact_status_effect": "pricing_certificate" if closure_certifies else "none",
        "mutates_solver": False,
        "note": (
            "Exact true-dual pricing closed the fixed three-path logical graph node; "
            "the certificate is scoped to this logical graph."
            if closure_certifies
            else note
        ),
    }


def _column_signature(column: JourneyColumn) -> tuple:
    return tuple(
        tuple((leg.source, leg.target, leg.path_type) for leg in sortie.legs)
        for sortie in column.sorties
    )


def _closure_can_certify(
    *,
    status: str,
    fixed_graph_no_negative_proved: bool,
    pricing: dict,
    rmp,
    dual_binding: dict,
    completion_bound_audit: dict,
    negative_eps: float,
) -> bool:
    min_reduced_cost = _float_or_none(pricing.get("best_reduced_cost"))
    return bool(
        status == "FIXED_GRAPH_PRICING_CLOSED"
        and fixed_graph_no_negative_proved
        and pricing.get("pricing_complete_for_all_task_subsets") is True
        and rmp is not None
        and getattr(rmp, "status", None) == "RESTRICTED_RMP_OPTIMAL"
        and dual_binding.get("dual_vector_bound_to_rmp") is True
        and completion_bound_audit.get("consistent") is True
        and min_reduced_cost is not None
        and min_reduced_cost >= -abs(float(negative_eps))
    )


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 9)
    except (TypeError, ValueError):
        return None
