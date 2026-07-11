"""Fail-closed true-dual pricing-tail artifact.

This module gives the future BPC certificate path a single entry point.  The
current lunar-ice runner can bind diagnostic pricing evidence here, but the
artifact only delegates to ``CERTIFIED_NO_NEGATIVE`` when the payload explicitly
comes from the true-dual BPC pricing path and has complete coverage.
"""

from __future__ import annotations

from typing import Any

from lunar_ice_bpc.exact.certificates.pricing_certificate import build_pricing_certificate


def build_true_dual_pricing_tail(
    *,
    source: str,
    pricing_payload: dict[str, Any] | None = None,
    rmp_payload: dict[str, Any] | None = None,
    certificate_scope: str = "branch_price_node",
    negative_eps: float = 1.0e-6,
) -> dict[str, Any]:
    """Build the pricing-tail certificate boundary without relaxing proof rules."""

    pricing_payload = pricing_payload or {}
    rmp_payload = rmp_payload or {}
    uses_true_dual = bool(pricing_payload.get("uses_true_dual_bpc_certificate"))
    pricing_complete = _pricing_complete(pricing_payload)
    coverage_complete = _coverage_complete(pricing_payload)
    min_rc = _first_float(
        pricing_payload.get("min_reduced_cost"),
        pricing_payload.get("best_reduced_cost"),
        pricing_payload.get("last_best_reduced_cost"),
        rmp_payload.get("min_reduced_cost"),
    )
    normalized_pricing_payload = dict(pricing_payload)
    if min_rc is not None:
        normalized_pricing_payload["best_reduced_cost"] = min_rc
    certificate = build_pricing_certificate(
        source=source,
        pricing_payload=normalized_pricing_payload,
        rmp_payload=rmp_payload,
        uses_true_dual_bpc_certificate=uses_true_dual,
        pricing_complete=pricing_complete,
        coverage_complete=coverage_complete,
        certificate_scope=certificate_scope,
        negative_eps=negative_eps,
    ).to_payload()
    missing = _missing_inputs(
        pricing_payload=pricing_payload,
        rmp_payload=rmp_payload,
        uses_true_dual=uses_true_dual,
        pricing_complete=pricing_complete,
        coverage_complete=coverage_complete,
        min_rc=min_rc,
        negative_eps=negative_eps,
    )
    tail_can_certify = bool(certificate.get("can_certify_no_negative") and not missing)
    status = _tail_status(tail_can_certify, missing)
    return {
        "schema_version": "lunar_ice_bpc.true_dual_pricing_tail.v1",
        "status": status,
        "source": str(source),
        "certificate_scope": str(certificate_scope),
        "uses_true_dual_bpc_certificate": uses_true_dual,
        "pricing_complete": pricing_complete,
        "coverage_complete": coverage_complete,
        "rmp_optimal": bool(rmp_payload.get("status") == "RESTRICTED_RMP_OPTIMAL"),
        "min_reduced_cost": min_rc,
        "dual_vector_bound_to_rmp": bool(pricing_payload.get("dual_vector_bound_to_rmp")),
        "dual_vector_fingerprint": pricing_payload.get("dual_vector_fingerprint"),
        "can_certify_no_negative": tail_can_certify,
        "pricing_certificate": certificate,
        "missing_input_count": len(missing),
        "missing_inputs": missing,
        "exact_status_effect": "none" if not tail_can_certify else "pricing_certificate",
        "mutates_solver": False,
        "lower_bound_official": tail_can_certify,
        "note": _note(status),
    }


def _pricing_complete(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("pricing_complete")
        or payload.get("pricing_complete_for_all_task_subsets")
        or payload.get("pricing_complete_for_all_tasks")
    )


def _coverage_complete(payload: dict[str, Any]) -> bool:
    return bool(payload.get("coverage_complete") or payload.get("pricing_complete_for_all_task_subsets"))


def _missing_inputs(
    *,
    pricing_payload: dict[str, Any],
    rmp_payload: dict[str, Any],
    uses_true_dual: bool,
    pricing_complete: bool,
    coverage_complete: bool,
    min_rc: float | None,
    negative_eps: float,
) -> list[str]:
    missing: list[str] = []
    if rmp_payload.get("status") != "RESTRICTED_RMP_OPTIMAL":
        missing.append("rmp_not_optimal")
    if not uses_true_dual:
        missing.append("true_dual_bpc_pricing_not_used")
    if not pricing_complete:
        missing.append("pricing_not_complete")
    if not coverage_complete:
        missing.append("pricing_coverage_not_complete")
    proof_kind = _pricing_proof_kind(pricing_payload)
    if proof_kind not in {"EXHAUSTIVE_NO_NEGATIVE", "FRONTIER_BOUND_NO_NEGATIVE"}:
        missing.append("pricing_proof_kind_not_certifying")
    if min_rc is None:
        missing.append("min_reduced_cost_missing")
    elif min_rc < -abs(float(negative_eps)):
        missing.append("negative_reduced_cost_column_exists")
    if not pricing_payload.get("dual_vector_bound_to_rmp"):
        missing.append("dual_vector_binding_missing")
    return missing


def _tail_status(tail_can_certify: bool, missing: list[str]) -> str:
    if tail_can_certify:
        return "TRUE_DUAL_PRICING_TAIL_CERTIFIED"
    if "negative_reduced_cost_column_exists" in missing:
        return "TRUE_DUAL_PRICING_TAIL_NEGATIVE_FOUND"
    if "true_dual_bpc_pricing_not_used" in missing:
        return "TRUE_DUAL_PRICING_TAIL_NOT_PORTED"
    return "TRUE_DUAL_PRICING_TAIL_INCOMPLETE"


def _note(status: str) -> str:
    if status == "TRUE_DUAL_PRICING_TAIL_CERTIFIED":
        return "Complete true-dual pricing exhausted the node and certified no negative reduced-cost journey."
    if status == "TRUE_DUAL_PRICING_TAIL_NEGATIVE_FOUND":
        return "Pricing found a negative reduced-cost journey, so the node cannot be certified yet."
    if status == "TRUE_DUAL_PRICING_TAIL_NOT_PORTED":
        return "Diagnostic pricing evidence is bound, but the true-dual BPC pricing tail is not ported."
    return "The true-dual pricing tail is present as an artifact but still missing proof inputs."


def _first_float(*values: object) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            return round(float(value), 9)
        except (TypeError, ValueError):
            continue
    return None


def _pricing_proof_kind(payload: dict[str, Any]) -> str:
    raw = str(payload.get("pricing_proof_kind") or "NONE")
    if raw in {"EXHAUSTIVE_NO_NEGATIVE", "FRONTIER_BOUND_NO_NEGATIVE"}:
        return raw
    return "NONE"
