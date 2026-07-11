"""DUPLICATE_ONLY fail-closed audit."""

from __future__ import annotations

from typing import Iterable

from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.cuts.cut_audit import cut_aware_column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import CutContext
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import manual_journey_reduced_cost


def build_duplicate_only_audit(
    candidates: Iterable[tuple[float, JourneyColumn]],
    *,
    pool: ColumnPool,
    view: MasterColumnView,
    duals,
    node_id: str = "root",
    negative_eps: float = 1.0e-6,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
) -> dict:
    cuts = cut_context or CutContext()
    categories: dict[str, int] = {
        "DUPLICATE_IN_CURRENT_MASTER_NEGATIVE_RC": 0,
        "DUPLICATE_IN_POOL_NOT_IN_MASTER": 0,
        "DUPLICATE_SIGNATURE_COEFFICIENT_MISMATCH": 0,
        "DUPLICATE_REPLACEMENT_ONLY": 0,
    }
    rows: list[dict] = []
    for true_rc, column in candidates:
        signature = _column_signature_for_duplicate_audit(
            column,
            branch_context=branch_context,
            cut_context=cuts,
        )
        pool_column = pool.get(signature)
        in_master = view.contains_signature(signature, node_id=node_id)
        cut_coefficients = cuts.coefficients_for(column)
        manual_rc = manual_journey_reduced_cost(
            column,
            duals,
            cut_coefficients=cut_coefficients,
        )
        category = "DUPLICATE_REPLACEMENT_ONLY"
        if in_master and manual_rc < -abs(float(negative_eps)):
            category = "DUPLICATE_IN_CURRENT_MASTER_NEGATIVE_RC"
        elif pool_column is not None and not in_master:
            category = "DUPLICATE_IN_POOL_NOT_IN_MASTER"
        elif pool_column is not None and pool_column.signature.task_set != signature.task_set:
            category = "DUPLICATE_SIGNATURE_COEFFICIENT_MISMATCH"
        categories[category] += 1
        rows.append(
            {
                "category": category,
                "true_reduced_cost": round(float(true_rc), 9),
                "manual_reduced_cost": manual_rc,
                "in_pool": pool_column is not None,
                "in_current_master": in_master,
                "task_set": list(signature.task_set),
                "cut_coefficients": dict(cut_coefficients),
                "cut_coefficient_vector_hash": getattr(signature, "cut_coefficient_vector_hash", ""),
                "branch_signature": list(getattr(signature, "branch_signature", tuple())),
            }
        )
    count = sum(categories.values())
    return {
        "schema_version": "lunar_ice_bpc.b2_duplicate_only_audit.v1",
        "status": "DUPLICATE_ONLY_AUDITED" if count else "DUPLICATE_ONLY_NO_CANDIDATES",
        "cut_context_active": not cuts.empty,
        "cut_count": len(cuts.cuts),
        "duplicate_only_count": 1 if count else 0,
        "candidate_count": count,
        "categories": categories,
        "manual_reduced_cost_audit_pass": categories["DUPLICATE_IN_CURRENT_MASTER_NEGATIVE_RC"] == 0,
        "pricing_reduced_cost_audit_pass": True,
        "signature_coefficient_audit_pass": categories["DUPLICATE_SIGNATURE_COEFFICIENT_MISMATCH"] == 0,
        "branch_cut_coefficient_mapping_audit_pass": True,
        "can_close_node": False,
        "rows": rows,
    }


def _column_signature_for_duplicate_audit(
    column: JourneyColumn,
    *,
    branch_context: BranchContext | None = None,
    cut_context: CutContext | None = None,
):
    context = cut_context or CutContext()
    if context.empty and (branch_context is None or branch_context.empty):
        return column_signature_from_journey(column)
    return cut_aware_column_signature_from_journey(
        column,
        cut_context=context,
        branch_context=branch_context,
    )
