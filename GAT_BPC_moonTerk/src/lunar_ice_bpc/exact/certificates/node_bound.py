"""Fail-closed BPC node-bound certificate artifact."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NodeBoundCertificate:
    status: str
    exact_status: str
    node_id: str
    node_depth: int
    incumbent_objective: float | None
    node_lower_bound: float | None
    lower_bound_source: str | None
    lower_bound_scope: str | None
    lower_bound_official: bool
    can_fathom_by_bound: bool
    uses_true_dual_bpc_certificate: bool
    pricing_certificate_status: str
    branch_decision_count: int
    cut_count: int
    issues: tuple[str, ...]
    note: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "lunar_ice_bpc.node_bound_certificate.v1",
            "status": self.status,
            "exact_status": self.exact_status,
            "node_id": self.node_id,
            "node_depth": self.node_depth,
            "incumbent_objective": self.incumbent_objective,
            "node_lower_bound": self.node_lower_bound,
            "lower_bound_source": self.lower_bound_source,
            "lower_bound_scope": self.lower_bound_scope,
            "lower_bound_official": self.lower_bound_official,
            "can_fathom_by_bound": self.can_fathom_by_bound,
            "uses_true_dual_bpc_certificate": self.uses_true_dual_bpc_certificate,
            "pricing_certificate_status": self.pricing_certificate_status,
            "branch_decision_count": self.branch_decision_count,
            "cut_count": self.cut_count,
            "issues": list(self.issues),
            "note": self.note,
        }


def build_node_bound_certificate(
    *,
    incumbent_objective: float | None,
    bound_ledger: dict[str, Any],
    pricing_certificate: dict[str, Any],
    restricted_rmp: dict[str, Any] | None = None,
    node_id: str = "root",
    node_depth: int = 0,
    bound_eps: float = 1.0e-6,
) -> NodeBoundCertificate:
    """Build a node-bound certificate without upgrading diagnostic evidence."""

    restricted_rmp = restricted_rmp or {}
    branch_context = restricted_rmp.get("branch_context") or {}
    cut_context = restricted_rmp.get("cut_context") or {}
    pricing_ok = bool(pricing_certificate.get("can_certify_no_negative"))
    uses_true_dual = bool(pricing_certificate.get("uses_true_dual_bpc_certificate"))
    official_source = _official_bpc_bound_record(bound_ledger)

    issues: list[str] = []
    if not pricing_ok:
        issues.append("pricing_certificate_not_certified")
    if not uses_true_dual:
        issues.append("true_dual_bpc_pricing_not_used")
    if official_source is None:
        issues.append("official_bpc_node_bound_missing")
    if incumbent_objective is None:
        issues.append("incumbent_objective_missing")

    node_bound = official_source.get("value") if official_source else None
    can_fathom = (
        not issues
        and node_bound is not None
        and incumbent_objective is not None
        and float(node_bound) >= float(incumbent_objective) - abs(float(bound_eps))
    )
    if not issues and not can_fathom:
        issues.append("bound_does_not_close_node")

    status = "NODE_BOUND_FATHOMED" if can_fathom else "NODE_BOUND_FAIL_CLOSED"
    exact_status = "BPC_NODE_FATHOMED" if can_fathom else "NOT_SOLVED"
    return NodeBoundCertificate(
        status=status,
        exact_status=exact_status,
        node_id=str(node_id),
        node_depth=int(node_depth),
        incumbent_objective=_float_or_none(incumbent_objective),
        node_lower_bound=_float_or_none(node_bound),
        lower_bound_source=str(official_source.get("name")) if official_source else None,
        lower_bound_scope=str(official_source.get("scope")) if official_source else None,
        lower_bound_official=bool(official_source),
        can_fathom_by_bound=bool(can_fathom),
        uses_true_dual_bpc_certificate=uses_true_dual,
        pricing_certificate_status=str(pricing_certificate.get("status") or "missing"),
        branch_decision_count=int(branch_context.get("pair_decision_count") or 0),
        cut_count=int(cut_context.get("cut_count") or 0),
        issues=tuple(issues),
        note=(
            "Certified node fathoming by exact true-dual pricing and official BPC node bound."
            if can_fathom
            else "Fail-closed node-bound artifact; current evidence cannot fathom this BPC node."
        ),
    )


def _official_bpc_bound_record(bound_ledger: dict[str, Any]) -> dict[str, Any] | None:
    for record in bound_ledger.get("records", []) or []:
        if (
            record.get("official_lower_bound") is True
            and str(record.get("certificate_status") or "").startswith("BPC_")
        ):
            return record
    return None


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None
