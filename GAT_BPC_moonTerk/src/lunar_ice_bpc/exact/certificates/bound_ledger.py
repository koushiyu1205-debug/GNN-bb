"""Fail-closed lower-bound ledger for lunar-ice exact reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from lunar_ice_bpc.exact.solver.lower_bounds import relative_gap


@dataclass(frozen=True)
class BoundRecord:
    name: str
    status: str
    value: float | None
    scope: str
    official_lower_bound: bool
    certificate_status: str
    exact_status: str
    note: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "value": self.value,
            "scope": self.scope,
            "official_lower_bound": self.official_lower_bound,
            "certificate_status": self.certificate_status,
            "exact_status": self.exact_status,
            "note": self.note,
        }


def build_bound_ledger(
    *,
    incumbent_objective: float | None,
    analytic_lower_bound: Any,
    direct_root_certificate: dict[str, Any] | None = None,
    restricted_rmp: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a JSON-safe bound ledger without upgrading diagnostic bounds.

    Only records explicitly marked ``official_lower_bound`` are eligible for
    the public ``official_lower_bound`` and ``official_gap`` values. Restricted
    RMP records remain diagnostic; fixed-root or closure records become official
    only when their scoped true-dual certificate checks pass.
    """

    records = [
        BoundRecord(
            name="analytic_relaxation",
            status=str(getattr(analytic_lower_bound, "status", "ANALYTIC_RELAXATION_BOUND")),
            value=_float_or_none(getattr(analytic_lower_bound, "bound", None)),
            scope="global_relaxation",
            official_lower_bound=True,
            certificate_status="RELAXATION_NOT_BPC_CERTIFICATE",
            exact_status=str(getattr(analytic_lower_bound, "exact_status", "RELAXATION_LOWER_BOUND")),
            note=str(
                getattr(
                    analytic_lower_bound,
                    "note",
                    "Conservative global relaxation lower bound; not a true-dual BPC certificate.",
                )
            ),
        )
    ]
    records.extend(_direct_root_records(direct_root_certificate or {}))
    records.extend(_restricted_rmp_records(restricted_rmp or {}))
    records.extend(_fixed_graph_pricing_closure_records(restricted_rmp or {}))

    official = _best_record(row for row in records if row.official_lower_bound)
    diagnostic = _best_record(row for row in records if not row.official_lower_bound)
    return {
        "schema_version": "lunar_ice_bpc.bound_ledger.v1",
        "official_lower_bound": official.value if official else None,
        "official_lower_bound_source": official.name if official else None,
        "official_lower_bound_scope": official.scope if official else None,
        "official_gap": relative_gap(incumbent_objective, official.value if official else None),
        "best_diagnostic_bound": diagnostic.value if diagnostic else None,
        "best_diagnostic_bound_source": diagnostic.name if diagnostic else None,
        "best_diagnostic_bound_scope": diagnostic.scope if diagnostic else None,
        "diagnostic_bound_is_official": False,
        "records": [row.to_payload() for row in records],
        "note": (
            "Only records with official_lower_bound=true feed public lower_bound/gap. "
            "Diagnostic restricted bounds are retained for debugging but cannot certify optimality."
        ),
    }


def _direct_root_records(payload: dict[str, Any]) -> tuple[BoundRecord, ...]:
    value = _float_or_none(payload.get("lp_bound"))
    if value is None:
        return tuple()
    certified = _direct_root_has_bpc_bound(payload)
    return (
        BoundRecord(
            name="direct_fixed_graph_root_lp",
            status=str(payload.get("status") or "UNKNOWN"),
            value=value,
            scope=str(payload.get("certificate_scope") or "fixed_logical_graph_direct_root"),
            official_lower_bound=certified,
            certificate_status=(
                "BPC_NODE_BOUND_CERTIFIED"
                if certified
                else "FIXED_GRAPH_ROOT_DIAGNOSTIC"
            ),
            exact_status=str(payload.get("exact_status") or "NOT_SOLVED"),
            note=(
                "Scoped official fixed three-path logical graph root LP bound."
                if certified
                else (
                    "Scoped to the current fixed three-path logical graph root LP; "
                    "reported separately from true-dual BPC certificates."
                )
            ),
        ),
    )


def _restricted_rmp_records(payload: dict[str, Any]) -> tuple[BoundRecord, ...]:
    value = _float_or_none(payload.get("objective_bound"))
    if value is None:
        return tuple()
    return (
        BoundRecord(
            name="restricted_journey_rmp",
            status=str(payload.get("status") or "UNKNOWN"),
            value=value,
            scope=str(payload.get("pool_type") or "restricted_column_pool"),
            official_lower_bound=False,
            certificate_status="RESTRICTED_POOL_DIAGNOSTIC",
            exact_status=str(payload.get("exact_status") or "NOT_SOLVED"),
            note=(
                "LP bound over a supplied restricted column pool. It is useful workload evidence, "
                "but is not a global lower bound for the full journey pricing space."
            ),
        ),
    )


def _fixed_graph_pricing_closure_records(payload: dict[str, Any]) -> tuple[BoundRecord, ...]:
    closure = payload.get("fixed_graph_pricing_closure") or {}
    value = _float_or_none(closure.get("final_bound"))
    if value is None:
        return tuple()
    certified = _fixed_graph_closure_has_bpc_bound(closure)
    return (
        BoundRecord(
            name="fixed_graph_pricing_closure_lp",
            status=str(closure.get("status") or "UNKNOWN"),
            value=value,
            scope="fixed_logical_graph_exhaustive_pricing_closure",
            official_lower_bound=certified,
            certificate_status=(
                "BPC_NODE_BOUND_CERTIFIED"
                if certified
                else "FIXED_GRAPH_PRICING_CLOSURE_DIAGNOSTIC"
            ),
            exact_status=(
                "BPC_NODE_BOUND_CERTIFIED"
                if certified
                else str(closure.get("exact_status") or "NOT_SOLVED")
            ),
            note=(
                "LP value after exact fixed-graph true-dual pricing closure; scoped to the fixed "
                "three-path logical graph BPC node."
                if certified
                else (
                    "LP value after diagnostic fixed-graph exhaustive pricing closure. "
                    "It is scoped to the fixed logical graph and cannot certify the full BPC node."
                )
            ),
        ),
    )


def _best_record(records: Iterable[BoundRecord]) -> BoundRecord | None:
    best: BoundRecord | None = None
    for record in records:
        if record.value is None:
            continue
        if best is None or float(record.value) > float(best.value):
            best = record
    return best


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _fixed_graph_closure_has_bpc_bound(closure: dict[str, Any]) -> bool:
    dual_binding = closure.get("dual_vector_binding") or {}
    completion_consistency = closure.get("completion_bound_consistency") or {}
    min_reduced_cost = _float_or_none(closure.get("last_best_reduced_cost"))
    return bool(
        closure.get("status") == "FIXED_GRAPH_PRICING_CLOSED"
        and closure.get("fixed_graph_no_negative_proved") is True
        and closure.get("last_pricing_complete_for_all_task_subsets") is True
        and closure.get("final_rmp_status") == "RESTRICTED_RMP_OPTIMAL"
        and dual_binding.get("dual_vector_bound_to_rmp") is True
        and completion_consistency.get("consistent") is True
        and min_reduced_cost is not None
        and min_reduced_cost >= -1.0e-6
    )


def _direct_root_has_bpc_bound(payload: dict[str, Any]) -> bool:
    min_reduced_cost = _float_or_none(payload.get("min_reduced_cost"))
    return bool(
        payload.get("enabled") is True
        and payload.get("uses_true_dual_bpc_certificate") is True
        and str(payload.get("exact_status") or "")
        in {"FIXED_GRAPH_ROOT_LP_CERTIFIED", "FIXED_GRAPH_INTEGER_OPTIMAL"}
        and min_reduced_cost is not None
        and min_reduced_cost >= -1.0e-6
    )
