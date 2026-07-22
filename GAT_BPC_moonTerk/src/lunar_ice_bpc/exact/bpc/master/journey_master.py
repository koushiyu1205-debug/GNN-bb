"""B1 root journey-master wrapper."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

from lunar_ice_bpc.exact.bpc.master.reduced_cost import ReducedCostContext
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import (
    CutContext,
    CutLineage,
    stable_payload_hash,
    true_dual_binding_hash,
)
from lunar_ice_bpc.exact.core.data import LunarIceData
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import (
    RestrictedRMPResult,
    manual_journey_reduced_cost,
    solve_restricted_journey_rmp,
)


@dataclass(frozen=True)
class JourneyMasterSolve:
    rmp: RestrictedRMPResult
    reduced_cost_context: ReducedCostContext
    reduced_cost_audit: dict


def solve_root_journey_master(
    data: LunarIceData,
    columns: Iterable[JourneyColumn],
    *,
    negative_eps: float = 1.0e-6,
    rmp_iteration_id: str = "root-0",
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
    cut_lineage: CutLineage | None = None,
    live_cut_policy_hash: str = "",
    separator_policy_version: str = "",
) -> JourneyMasterSolve:
    """Solve a journey RMP and bind its exact context into reduced costs."""

    active_columns = tuple(columns)
    active_cut_context = cut_context or CutContext()
    rmp = solve_restricted_journey_rmp(
        data.task_ids,
        active_columns,
        fleet_size=data.fleet_size,
        negative_eps=negative_eps,
        branch_context=branch_context,
        cut_context=active_cut_context,
    )
    context = reduced_cost_context_from_rmp(
        rmp,
        rmp_iteration_id=rmp_iteration_id,
        cut_lineage=cut_lineage,
        live_cut_policy_hash=live_cut_policy_hash,
        separator_policy_version=separator_policy_version,
    )
    return JourneyMasterSolve(
        rmp=rmp,
        reduced_cost_context=context,
        reduced_cost_audit=audit_master_column_reduced_costs(
            active_columns,
            rmp,
            cut_context=active_cut_context,
        ),
    )


def reduced_cost_context_from_rmp(
    rmp: RestrictedRMPResult,
    *,
    rmp_iteration_id: str,
    cut_lineage: CutLineage | None = None,
    live_cut_policy_hash: str = "",
    separator_policy_version: str = "",
) -> ReducedCostContext:
    payload = {
        "cover": {str(key): round(float(value), 9) for key, value in rmp.duals.cover.items()},
        "fleet": round(float(rmp.duals.fleet_limit), 9),
        "cuts": {str(key): round(float(value), 9) for key, value in (rmp.duals.cuts or {}).items()},
        "rmp_iteration_id": str(rmp_iteration_id),
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    active_cut_context = CutContext() if not rmp.cut_context else _cut_context_from_rmp_payload(rmp.cut_context)
    lineage = cut_lineage or CutLineage()
    return ReducedCostContext(
        task_duals=rmp.duals.cover,
        fleet_dual=rmp.duals.fleet_limit,
        cut_duals=rmp.duals.cuts or {},
        branch_context=rmp.branch_context,
        cut_context=rmp.cut_context,
        dual_fingerprint=fingerprint,
        rmp_iteration_id=str(rmp_iteration_id),
        objective_mode="official",
        true_dual_binding_hash=true_dual_binding_hash(
            rmp.duals.cover,
            fleet_limit=rmp.duals.fleet_limit,
            cuts=rmp.duals.cuts,
        ),
        branch_context_hash=stable_payload_hash(rmp.branch_context),
        active_cut_context_hash=active_cut_context.active_cut_context_hash,
        cut_lineage_hash=lineage.cut_lineage_hash,
        live_cut_policy_hash=str(live_cut_policy_hash),
        separator_policy_version=str(separator_policy_version),
    )


def _cut_context_from_rmp_payload(payload: dict) -> CutContext:
    from lunar_ice_bpc.exact.core.cuts import cut_context_from_payload

    return cut_context_from_payload(payload)


def audit_master_column_reduced_costs(
    columns: Iterable[JourneyColumn],
    rmp: RestrictedRMPResult,
    *,
    cut_context: CutContext | None = None,
) -> dict:
    context = cut_context or CutContext()
    values = [
        manual_journey_reduced_cost(
            column,
            rmp.duals,
            cut_coefficients=context.coefficients_for(column),
        )
        for column in columns
    ]
    return {
        "status": "MASTER_RC_AUDITED" if values else "MASTER_RC_NO_COLUMNS",
        "column_count": len(values),
        "cut_context_active": not context.empty,
        "cut_count": len(context.cuts),
        "min_reduced_cost": min(values) if values else None,
        "max_reduced_cost": max(values) if values else None,
        "negative_count": sum(1 for value in values if value < -1.0e-6),
        "dual_fingerprint_bound_to_rmp": bool(rmp.status == "RESTRICTED_RMP_OPTIMAL"),
    }
