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
    issues: list[str] = []
    if not uses_true_dual_bpc_certificate:
        issues.append("true_dual_bpc_pricing_not_used")
    if not pricing_complete:
        issues.append("pricing_not_complete")
    if not coverage_complete:
        issues.append("pricing_coverage_not_complete")
    if min_rc is None:
        issues.append("min_reduced_cost_missing")
    elif float(min_rc) < -abs(float(negative_eps)):
        issues.append("negative_reduced_cost_column_exists")

    can_certify = not issues
    negative_found = min_rc is not None and float(min_rc) < -abs(float(negative_eps))
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
        global_remaining_rc_lower_bound=min_rc if can_certify else None,
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
