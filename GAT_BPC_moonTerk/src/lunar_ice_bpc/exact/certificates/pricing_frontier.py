"""Reduced-cost frontier ledger for no-negative pricing certification."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PricingFrontierLedger:
    status: str
    frontier_scope: str
    source: str
    uses_true_dual_bpc_certificate: bool
    pricing_complete: bool
    coverage_complete: bool
    min_reduced_cost: float | None
    global_remaining_rc_lower_bound: float | None
    global_remaining_rc_lb_valid: bool
    global_remaining_rc_lb_coverage_complete: bool
    frontier_region_count: int
    frontier_unsupported_region_count: int
    pending_complete_min_rc: float | None
    true_remaining_best_rc: float | None
    global_remaining_rc_lb_leq_true_remaining_best_rc: bool | None
    pricing_proof_kind: str
    lower_bound_official: bool
    can_certify_no_negative: bool
    negative_eps: float
    issues: tuple[str, ...]
    note: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "lunar_ice_bpc.pricing_frontier_ledger.v1",
            "status": self.status,
            "frontier_scope": self.frontier_scope,
            "source": self.source,
            "uses_true_dual_bpc_certificate": self.uses_true_dual_bpc_certificate,
            "pricing_complete": self.pricing_complete,
            "coverage_complete": self.coverage_complete,
            "min_reduced_cost": self.min_reduced_cost,
            "global_remaining_rc_lower_bound": self.global_remaining_rc_lower_bound,
            "global_remaining_rc_lb": self.global_remaining_rc_lower_bound,
            "global_remaining_rc_lb_valid": self.global_remaining_rc_lb_valid,
            "global_remaining_rc_lb_coverage_complete": self.global_remaining_rc_lb_coverage_complete,
            "frontier_region_count": self.frontier_region_count,
            "frontier_unsupported_region_count": self.frontier_unsupported_region_count,
            "pending_complete_min_rc": self.pending_complete_min_rc,
            "true_remaining_best_rc": self.true_remaining_best_rc,
            "global_remaining_rc_lb_leq_true_remaining_best_rc": self.global_remaining_rc_lb_leq_true_remaining_best_rc,
            "pricing_proof_kind": self.pricing_proof_kind,
            "lower_bound_official": self.lower_bound_official,
            "can_certify_no_negative": self.can_certify_no_negative,
            "negative_eps": self.negative_eps,
            "issues": list(self.issues),
            "note": self.note,
        }


def build_pricing_frontier_ledger(
    *,
    source: str,
    pricing_payload: dict[str, Any] | None = None,
    rmp_payload: dict[str, Any] | None = None,
    uses_true_dual_bpc_certificate: bool = False,
    pricing_complete: bool = False,
    coverage_complete: bool = False,
    frontier_scope: str = "journey_pricing",
    negative_eps: float = 1.0e-6,
) -> PricingFrontierLedger:
    pricing_payload = pricing_payload or {}
    rmp_payload = rmp_payload or {}
    min_rc = _first_float(
        pricing_payload.get("best_reduced_cost"),
        rmp_payload.get("min_reduced_cost"),
    )
    global_remaining_rc_lb = _first_float(
        pricing_payload.get("global_remaining_rc_lb"),
        pricing_payload.get("global_remaining_rc_lower_bound"),
        pricing_payload.get("dual_bound"),
        pricing_payload.get("bound"),
        min_rc,
    )
    pending_complete_min_rc = _first_float(
        pricing_payload.get("pending_complete_min_rc"),
        pricing_payload.get("best_reduced_cost"),
        min_rc,
    )
    true_remaining_best_rc = _first_float(
        pricing_payload.get("true_remaining_best_rc"),
        pricing_payload.get("exhaustive_remaining_best_rc"),
        pricing_payload.get("exhaustive_best_reduced_cost"),
    )
    proof_kind = _pricing_proof_kind(pricing_payload.get("pricing_proof_kind"))
    lb_valid = bool(pricing_payload.get("global_remaining_rc_lb_valid") is True or global_remaining_rc_lb is not None)
    lb_coverage_complete = bool(
        pricing_payload.get("global_remaining_rc_lb_coverage_complete") is True
        or coverage_complete
    )
    frontier_region_count = _nonnegative_int(pricing_payload.get("frontier_region_count"), default=0)
    unsupported_region_count = _nonnegative_int(
        pricing_payload.get("frontier_unsupported_region_count"),
        default=0 if lb_coverage_complete else 1,
    )
    issues: list[str] = []
    if not uses_true_dual_bpc_certificate:
        issues.append("true_dual_bpc_pricing_not_used")
    if not pricing_complete:
        issues.append("pricing_not_complete")
    if not coverage_complete:
        issues.append("pricing_coverage_not_complete")
    if proof_kind == "NONE":
        issues.append("pricing_proof_kind_missing")
    elif proof_kind == "UNKNOWN":
        issues.append("pricing_proof_kind_unknown")
    elif proof_kind == "EXHAUSTIVE_INCOMPLETE":
        issues.append("exhaustive_pricing_incomplete")
    elif proof_kind == "EXHAUSTIVE_FOUND_NEGATIVE":
        issues.append("exhaustive_pricing_found_negative")
    if proof_kind == "FRONTIER_BOUND_INCOMPLETE":
        issues.append("frontier_bound_incomplete")
    if proof_kind == "FRONTIER_BOUND_NO_NEGATIVE" and unsupported_region_count > 0:
        issues.append("frontier_unsupported_regions_exist")
    if proof_kind == "FRONTIER_BOUND_NO_NEGATIVE" and not lb_coverage_complete:
        issues.append("frontier_lower_bound_coverage_not_complete")
    if min_rc is None and proof_kind != "FRONTIER_BOUND_NO_NEGATIVE":
        issues.append("min_reduced_cost_missing")
    elif min_rc is not None and float(min_rc) < -abs(float(negative_eps)):
        issues.append("negative_reduced_cost_column_exists")
    lb_leq_true_best: bool | None = None
    if true_remaining_best_rc is not None and global_remaining_rc_lb is not None:
        lb_leq_true_best = bool(
            float(global_remaining_rc_lb) <= float(true_remaining_best_rc) + abs(float(negative_eps))
        )
        if not lb_leq_true_best:
            issues.append("frontier_lower_bound_exceeds_true_remaining_best_rc")

    bound_no_negative = bool(
        proof_kind == "FRONTIER_BOUND_NO_NEGATIVE"
        and uses_true_dual_bpc_certificate
        and pricing_complete
        and coverage_complete
        and lb_valid
        and lb_coverage_complete
        and unsupported_region_count == 0
        and global_remaining_rc_lb is not None
        and float(global_remaining_rc_lb) >= -abs(float(negative_eps))
        and lb_leq_true_best is not False
    )
    exhaustive_no_negative = bool(
        proof_kind == "EXHAUSTIVE_NO_NEGATIVE"
        and not issues
    )
    can_certify = bool(exhaustive_no_negative or bound_no_negative)
    negative_found = (
        (min_rc is not None and float(min_rc) < -abs(float(negative_eps)))
        or (global_remaining_rc_lb is not None and float(global_remaining_rc_lb) < -abs(float(negative_eps)))
    )
    if can_certify:
        status = "CERTIFIED_FRONTIER_NO_NEGATIVE"
        note = "Complete true-dual pricing frontier proves no negative reduced-cost journey."
    elif negative_found:
        status = "NEGATIVE_REDUCED_COST_FOUND"
        note = "A negative reduced-cost journey exists; no no-negative certificate is possible."
    elif not uses_true_dual_bpc_certificate:
        status = "DIAGNOSTIC_FRONTIER_ONLY"
        note = "Pricing frontier is diagnostic because true-dual BPC pricing was not used."
    else:
        status = "FRONTIER_INCOMPLETE"
        note = "Pricing frontier coverage is incomplete; fail closed."
    return PricingFrontierLedger(
        status=status,
        frontier_scope=str(frontier_scope),
        source=str(source),
        uses_true_dual_bpc_certificate=bool(uses_true_dual_bpc_certificate),
        pricing_complete=bool(pricing_complete),
        coverage_complete=bool(coverage_complete),
        min_reduced_cost=min_rc,
        global_remaining_rc_lower_bound=global_remaining_rc_lb if (can_certify or lb_valid) else None,
        global_remaining_rc_lb_valid=lb_valid,
        global_remaining_rc_lb_coverage_complete=lb_coverage_complete,
        frontier_region_count=frontier_region_count,
        frontier_unsupported_region_count=unsupported_region_count,
        pending_complete_min_rc=pending_complete_min_rc,
        true_remaining_best_rc=true_remaining_best_rc,
        global_remaining_rc_lb_leq_true_remaining_best_rc=lb_leq_true_best,
        pricing_proof_kind=proof_kind,
        lower_bound_official=bool(can_certify),
        can_certify_no_negative=bool(can_certify),
        negative_eps=float(negative_eps),
        issues=tuple(issues),
        note=note,
    )


def _first_float(*values: object) -> float | None:
    for value in values:
        if value is None:
            continue
        try:
            return round(float(value), 9)
        except (TypeError, ValueError):
            continue
    return None


def _pricing_proof_kind(value: object) -> str:
    raw = str(value or "NONE")
    if raw in {
        "NONE",
        "EXHAUSTIVE_FOUND_NEGATIVE",
        "EXHAUSTIVE_INCOMPLETE",
        "EXHAUSTIVE_NO_NEGATIVE",
        "FRONTIER_BOUND_INCOMPLETE",
        "FRONTIER_BOUND_NO_NEGATIVE",
    }:
        return raw
    return "UNKNOWN"


def _nonnegative_int(value: object, *, default: int) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return max(0, int(default))
