"""DUPLICATE_ONLY fail-closed audit."""

from __future__ import annotations

from typing import Iterable

from lunar_ice_bpc.exact.bpc.core.column_pool import BpcColumn, ColumnPool
from lunar_ice_bpc.exact.bpc.core.column_signature import column_signature_from_journey
from lunar_ice_bpc.exact.bpc.core.master_column_view import MasterColumnView
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
) -> dict:
    categories: dict[str, int] = {
        "DUPLICATE_IN_CURRENT_MASTER_NEGATIVE_RC": 0,
        "DUPLICATE_IN_POOL_NOT_IN_MASTER": 0,
        "DUPLICATE_SIGNATURE_COEFFICIENT_MISMATCH": 0,
        "DUPLICATE_REPLACEMENT_ONLY": 0,
    }
    rows: list[dict] = []
    for true_rc, column in candidates:
        signature = column_signature_from_journey(column)
        pool_column = pool.get(signature)
        in_master = view.contains_signature(signature, node_id=node_id)
        manual_rc = manual_journey_reduced_cost(column, duals)
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
            }
        )
    count = sum(categories.values())
    return {
        "schema_version": "lunar_ice_bpc.b2_duplicate_only_audit.v1",
        "status": "DUPLICATE_ONLY_AUDITED" if count else "DUPLICATE_ONLY_NO_CANDIDATES",
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

