"""Fail-closed no-negative pricing certificate artifact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lunar_ice_bpc.exact.certificates.pricing_frontier import build_pricing_frontier_ledger


@dataclass(frozen=True)
class PricingCertificate:
    status: str
    exact_status: str
    certificate_scope: str
    can_certify_no_negative: bool
    uses_true_dual_bpc_certificate: bool
    pricing_complete: bool
    coverage_complete: bool
    min_reduced_cost: float | None
    negative_eps: float
    source: str
    frontier_ledger: dict[str, Any]
    issues: tuple[str, ...]
    note: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "lunar_ice_bpc.pricing_certificate.v1",
            "status": self.status,
            "exact_status": self.exact_status,
            "certificate_scope": self.certificate_scope,
            "can_certify_no_negative": self.can_certify_no_negative,
            "uses_true_dual_bpc_certificate": self.uses_true_dual_bpc_certificate,
            "pricing_complete": self.pricing_complete,
            "coverage_complete": self.coverage_complete,
            "min_reduced_cost": self.min_reduced_cost,
            "negative_eps": self.negative_eps,
            "source": self.source,
            "frontier_ledger": self.frontier_ledger,
            "issues": list(self.issues),
            "note": self.note,
        }


def build_pricing_certificate(
    *,
    source: str,
    pricing_payload: dict[str, Any] | None = None,
    rmp_payload: dict[str, Any] | None = None,
    uses_true_dual_bpc_certificate: bool = False,
    pricing_complete: bool = False,
    coverage_complete: bool = False,
    certificate_scope: str = "journey_pricing",
    negative_eps: float = 1.0e-6,
) -> PricingCertificate:
    """Return a no-negative certificate only when all proof inputs are present.

    Current lunar-ice scaffold pricing is diagnostic. It may find negative
    columns, but it cannot certify their absence. This helper keeps that
    boundary explicit and gives the future true-dual pricing path one place to
    produce a certificate after it verifies complete pricing coverage.
    """

    pricing_payload = pricing_payload or {}
    rmp_payload = rmp_payload or {}
    frontier = build_pricing_frontier_ledger(
        source=source,
        pricing_payload=pricing_payload,
        rmp_payload=rmp_payload,
        uses_true_dual_bpc_certificate=uses_true_dual_bpc_certificate,
        pricing_complete=pricing_complete,
        coverage_complete=coverage_complete,
        frontier_scope=certificate_scope,
        negative_eps=negative_eps,
    )
    frontier_payload = frontier.to_payload()
    min_rc = frontier.min_reduced_cost
    issues = list(frontier.issues)

    can_certify = bool(frontier.can_certify_no_negative and not issues)
    status = "CERTIFIED_NO_NEGATIVE" if can_certify else "NOT_PORTED_TRUE_DUAL_BPC"
    exact_status = "BPC_NO_NEGATIVE_CERTIFIED" if can_certify else "NOT_SOLVED"
    return PricingCertificate(
        status=status,
        exact_status=exact_status,
        certificate_scope=str(certificate_scope),
        can_certify_no_negative=can_certify,
        uses_true_dual_bpc_certificate=bool(uses_true_dual_bpc_certificate),
        pricing_complete=bool(pricing_complete),
        coverage_complete=bool(coverage_complete),
        min_reduced_cost=min_rc,
        negative_eps=float(negative_eps),
        source=str(source),
        frontier_ledger=frontier_payload,
        issues=tuple(issues),
        note=(
            "True-dual complete pricing proved no negative reduced-cost journey."
            if can_certify
            else "Fail-closed certificate artifact; current pricing evidence cannot certify no-negative."
        ),
    )


def select_effective_pricing_certificate(
    *,
    diagnostic_certificate: dict[str, Any],
    true_dual_pricing_tail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select the active no-negative certificate without weakening proof rules."""

    true_dual_pricing_tail = true_dual_pricing_tail or {}
    tail_certificate = true_dual_pricing_tail.get("pricing_certificate") or {}
    if (
        true_dual_pricing_tail.get("can_certify_no_negative") is True
        and tail_certificate.get("can_certify_no_negative") is True
        and tail_certificate.get("uses_true_dual_bpc_certificate") is True
    ):
        selected = dict(tail_certificate)
        selected["selected_certificate_source"] = "true_dual_pricing_tail"
        selected["diagnostic_fallback_status"] = diagnostic_certificate.get("status")
        selected["true_dual_pricing_tail_status"] = true_dual_pricing_tail.get("status")
        return selected

    selected = dict(diagnostic_certificate)
    selected["selected_certificate_source"] = "diagnostic_fallback"
    selected["diagnostic_fallback_status"] = diagnostic_certificate.get("status")
    selected["true_dual_pricing_tail_status"] = true_dual_pricing_tail.get("status")
    return selected
