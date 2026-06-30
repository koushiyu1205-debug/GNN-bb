"""Readiness artifact for the future true-dual BPC certificate path."""

from __future__ import annotations

from typing import Any


def build_true_dual_certificate_readiness(
    *,
    pricing_certificate: dict[str, Any],
    restricted_rmp: dict[str, Any] | None = None,
    node_bound_certificate: dict[str, Any] | None = None,
    negative_eps: float = 1.0e-6,
) -> dict[str, Any]:
    """Report which true-dual certificate prerequisites are already present.

    This artifact is deliberately diagnostic. It does not upgrade direct,
    fixed-graph, or restricted-pool evidence into a BPC certificate. It only
    makes the missing proof inputs explicit for the future true-dual path.
    """

    restricted_rmp = restricted_rmp or {}
    node_bound_certificate = node_bound_certificate or {}
    direct_pricing = restricted_rmp.get("direct_pricing") or {}
    direct_cg = restricted_rmp.get("direct_column_generation") or {}
    fixed_graph_closure = restricted_rmp.get("fixed_graph_pricing_closure") or {}
    frontier = pricing_certificate.get("frontier_ledger") or {}

    fixed_graph_closure_complete = bool(
        fixed_graph_closure.get("status") == "FIXED_GRAPH_PRICING_CLOSED"
        and fixed_graph_closure.get("fixed_graph_no_negative_proved")
    )
    min_rc = _first_float(
        fixed_graph_closure.get("last_best_reduced_cost") if fixed_graph_closure_complete else None,
        pricing_certificate.get("min_reduced_cost"),
        frontier.get("min_reduced_cost"),
        direct_pricing.get("best_reduced_cost"),
        restricted_rmp.get("min_reduced_cost"),
    )
    no_negative = bool(min_rc is not None and min_rc >= -abs(float(negative_eps)))
    direct_pricing_complete = bool(
        direct_pricing.get("status") == "DIRECT_LABEL_PRICED"
        and direct_pricing.get("pricing_complete_for_all_tasks")
    )
    diagnostic_complete = direct_pricing_complete or fixed_graph_closure_complete
    rmp_optimal = bool(
        restricted_rmp.get("status") == "RESTRICTED_RMP_OPTIMAL"
        and restricted_rmp.get("min_reduced_cost") is not None
    )
    true_dual_used = bool(pricing_certificate.get("uses_true_dual_bpc_certificate"))
    pricing_complete = bool(pricing_certificate.get("pricing_complete"))
    coverage_complete = bool(pricing_certificate.get("coverage_complete"))
    pricing_can_certify = bool(pricing_certificate.get("can_certify_no_negative"))
    node_bound_official = bool(node_bound_certificate.get("lower_bound_official"))

    missing = _missing_inputs(
        rmp_optimal=rmp_optimal,
        true_dual_used=true_dual_used,
        pricing_complete=pricing_complete,
        coverage_complete=coverage_complete,
        min_rc=min_rc,
        no_negative=no_negative,
        node_bound_official=node_bound_official,
    )
    status = _readiness_status(
        pricing_can_certify=pricing_can_certify,
        true_dual_used=true_dual_used,
        rmp_optimal=rmp_optimal,
        diagnostic_complete=diagnostic_complete,
        min_rc=min_rc,
        no_negative=no_negative,
    )
    return {
        "schema_version": "lunar_ice_bpc.true_dual_certificate_readiness.v1",
        "status": status,
        "evaluation_scope": "certificate_prerequisite_audit",
        "exact_status_effect": "none",
        "mutates_solver": False,
        "can_certify": bool(pricing_can_certify and true_dual_used),
        "pricing_certificate_status": pricing_certificate.get("status"),
        "pricing_certificate_can_certify_no_negative": pricing_can_certify,
        "true_dual_pricing_used": true_dual_used,
        "pricing_complete": pricing_complete,
        "coverage_complete": coverage_complete,
        "restricted_rmp_optimal": rmp_optimal,
        "diagnostic_direct_pricing_complete": direct_pricing_complete,
        "diagnostic_fixed_graph_closure_complete": fixed_graph_closure_complete,
        "fixed_graph_closure_status": fixed_graph_closure.get("status"),
        "fixed_graph_closure_no_negative_proved": bool(fixed_graph_closure.get("fixed_graph_no_negative_proved")),
        "diagnostic_no_negative": no_negative,
        "min_reduced_cost": min_rc,
        "node_bound_official": node_bound_official,
        "missing_input_count": len(missing),
        "missing_inputs": missing,
        "pricing_certificate_issues": list(pricing_certificate.get("issues") or []),
        "frontier_issues": list(frontier.get("issues") or []),
        "direct_pricing_status": direct_pricing.get("status"),
        "direct_cg_status": direct_cg.get("status"),
        "lower_bound_official": False,
        "note": _note(status),
    }


def _missing_inputs(
    *,
    rmp_optimal: bool,
    true_dual_used: bool,
    pricing_complete: bool,
    coverage_complete: bool,
    min_rc: float | None,
    no_negative: bool,
    node_bound_official: bool,
) -> list[str]:
    missing: list[str] = []
    if not rmp_optimal:
        missing.append("restricted_or_node_rmp_not_optimal")
    if not true_dual_used:
        missing.append("true_dual_pricing_proof_not_used")
    if not pricing_complete:
        missing.append("pricing_not_complete")
    if not coverage_complete:
        missing.append("pricing_coverage_not_complete")
    if min_rc is None:
        missing.append("min_reduced_cost_missing")
    elif not no_negative:
        missing.append("negative_reduced_cost_column_exists")
    if not node_bound_official:
        missing.append("official_bpc_node_bound_missing")
    return missing


def _readiness_status(
    *,
    pricing_can_certify: bool,
    true_dual_used: bool,
    rmp_optimal: bool,
    diagnostic_complete: bool,
    min_rc: float | None,
    no_negative: bool,
) -> str:
    if pricing_can_certify and true_dual_used:
        return "TRUE_DUAL_CERTIFICATE_READY"
    if min_rc is not None and not no_negative:
        return "BLOCKED_BY_NEGATIVE_REDUCED_COST"
    if not rmp_optimal:
        return "BLOCKED_BY_RMP_STATUS"
    if diagnostic_complete and no_negative:
        return "WAITING_TRUE_DUAL_PRICING_PROOF"
    return "BLOCKED_BY_INCOMPLETE_PRICING"


def _note(status: str) -> str:
    if status == "TRUE_DUAL_CERTIFICATE_READY":
        return "A true-dual pricing certificate is present; downstream node-bound checks may use it."
    if status == "WAITING_TRUE_DUAL_PRICING_PROOF":
        return "Diagnostic pricing found no negative column, but true-dual pricing proof is still missing."
    if status == "BLOCKED_BY_NEGATIVE_REDUCED_COST":
        return "A negative reduced-cost column was found; add it or continue pricing before certification."
    if status == "BLOCKED_BY_RMP_STATUS":
        return "The restricted or node RMP prerequisite is not optimal, so certificate readiness cannot advance."
    return "Pricing coverage is incomplete; fail closed until the true-dual pricing path is complete."


def _first_float(*values: object) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            return round(float(value), 9)
        except (TypeError, ValueError):
            continue
    return None
