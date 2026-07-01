"""B4 cut coefficient, dominance, and reduced-cost audits."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from typing import Iterable

from lunar_ice_bpc.exact.bpc.core.column_signature import ColumnSemanticSignature, column_signature_from_journey
from lunar_ice_bpc.exact.core.branching import BranchContext
from lunar_ice_bpc.exact.core.cuts import FLEET_LOWER_BOUND_CUT, SUBSET_ROW_CUT, CutContext
from lunar_ice_bpc.exact.core.journey import JourneyColumn
from lunar_ice_bpc.exact.master.journey_rmp import JourneyDuals, manual_journey_reduced_cost


def cut_coefficient_vector(column: JourneyColumn, cut_context: CutContext | None) -> tuple[tuple[str, float], ...]:
    context = cut_context or CutContext()
    return tuple(
        (str(cut.cut_id), round(float(cut.coefficient(column)), 9))
        for cut in sorted(context.cuts, key=lambda row: row.cut_id)
    )


def cut_coefficient_vector_hash(column: JourneyColumn, cut_context: CutContext | None) -> str:
    vector = cut_coefficient_vector(column, cut_context)
    if not vector:
        return ""
    return hashlib.sha256(json.dumps(vector, sort_keys=True).encode("utf-8")).hexdigest()


def cut_aware_column_signature_from_journey(
    column: JourneyColumn,
    *,
    cut_context: CutContext | None = None,
    branch_context: BranchContext | None = None,
) -> ColumnSemanticSignature:
    base = column_signature_from_journey(column)
    return replace(
        base,
        cut_coefficient_vector_hash=cut_coefficient_vector_hash(column, cut_context),
        branch_signature=_branch_signature(branch_context),
    )


def build_cut_dominance_compatibility_report(cut_context: CutContext | None) -> dict:
    context = cut_context or CutContext()
    rows: list[dict] = []
    issues: list[str] = []
    for cut in context.cuts:
        if cut.cut_type == SUBSET_ROW_CUT:
            rows.append(
                {
                    "cut_id": cut.cut_id,
                    "cut_type": cut.cut_type,
                    "coefficient_dependency": "task_set",
                    "dominance_key_requirements": ["task_set", "branch_signature", "cut_coefficient_vector_hash"],
                    "pricing_supported": True,
                    "completion_bound_supported": False,
                    "live_supported": True,
                    "route_order_sensitive": False,
                    "resource_sensitive": False,
                    "diagnostic_only": False,
                    "issue": "",
                }
            )
        elif cut.cut_type == FLEET_LOWER_BOUND_CUT:
            issue = "fleet_lower_bound_cut_live_not_proven_for_multi_sortie_journey_master"
            issues.append(issue)
            rows.append(
                {
                    "cut_id": cut.cut_id,
                    "cut_type": cut.cut_type,
                    "coefficient_dependency": "nonempty_journey_indicator",
                    "dominance_key_requirements": ["cut_coefficient_vector_hash"],
                    "pricing_supported": True,
                    "completion_bound_supported": False,
                    "live_supported": False,
                    "route_order_sensitive": False,
                    "resource_sensitive": False,
                    "diagnostic_only": True,
                    "issue": issue,
                }
            )
        else:
            issue = f"unsupported_cut_type:{cut.cut_type}"
            issues.append(issue)
            rows.append(
                {
                    "cut_id": cut.cut_id,
                    "cut_type": cut.cut_type,
                    "pricing_supported": False,
                    "completion_bound_supported": False,
                    "live_supported": False,
                    "diagnostic_only": True,
                    "issue": issue,
                }
            )
    return {
        "schema_version": "lunar_ice_bpc.b4_cut_dominance_compatibility.v1",
        "cut_count": len(context.cuts),
        "rows": rows,
        "dominance_key_covers_active_cut_coefficients": not issues,
        "pricing_supported_count": sum(1 for row in rows if row.get("pricing_supported")),
        "cut_completion_bound_fail_closed_count": sum(1 for row in rows if not row.get("completion_bound_supported")),
        "live_supported_count": sum(1 for row in rows if row.get("live_supported")),
        "issues": issues,
        "valid": not issues,
    }


def audit_cut_reduced_cost_consistency(
    columns: Iterable[JourneyColumn],
    duals: JourneyDuals,
    cut_context: CutContext | None,
    pricing_payload: dict | None,
    *,
    negative_eps: float = 1.0e-6,
) -> dict:
    context = cut_context or CutContext()
    column_tuple = tuple(columns)
    manual_values = tuple(
        manual_journey_reduced_cost(
            column,
            duals,
            cut_coefficients=context.coefficients_for(column),
        )
        for column in column_tuple
    )
    manual_best = min(manual_values) if manual_values else None
    pricing_best = None if not pricing_payload else pricing_payload.get("best_reduced_cost")
    best_match = bool(
        manual_best is None
        and pricing_best is None
        or (
            manual_best is not None
            and pricing_best is not None
            and abs(float(manual_best) - float(pricing_best)) <= abs(float(negative_eps))
        )
    )
    sign_audit = _cut_dual_sign_audit(duals, context, negative_eps=negative_eps)
    coefficient_rows = [
        {
            "column_index": index,
            "task_set": sorted(str(task_id) for task_id in column.task_set),
            "cut_coefficient_vector": list(cut_coefficient_vector(column, context)),
            "cut_coefficient_vector_hash": cut_coefficient_vector_hash(column, context),
        }
        for index, column in enumerate(column_tuple)
    ]
    return {
        "schema_version": "lunar_ice_bpc.b4_cut_reduced_cost_audit.v1",
        "cut_count": len(context.cuts),
        "column_count": len(column_tuple),
        "manual_best_reduced_cost": manual_best,
        "pricing_best_reduced_cost": pricing_best,
        "manual_rc_with_cuts_matches_pricing_rc": best_match,
        "manual_rc_cut_consistency_pass": bool(best_match and sign_audit["valid"]),
        "cut_dual_sign_audit": sign_audit,
        "cut_dual_sign_audit_pass": sign_audit["valid"],
        "nonzero_cut_coefficient_column_count": sum(
            1 for row in coefficient_rows if row["cut_coefficient_vector"]
        ),
        "coefficient_rows": coefficient_rows[:20],
        "negative_manual_rc_count": sum(1 for value in manual_values if value < -abs(float(negative_eps))),
    }


def _cut_dual_sign_audit(duals: JourneyDuals, cut_context: CutContext, *, negative_eps: float) -> dict:
    rows: list[dict] = []
    issues: list[str] = []
    for cut in cut_context.cuts:
        dual_value = float((duals.cuts or {}).get(cut.cut_id, 0.0))
        if cut.cut_type == SUBSET_ROW_CUT:
            valid = dual_value <= abs(float(negative_eps))
            expected = "<= 0"
        elif cut.cut_type == FLEET_LOWER_BOUND_CUT:
            valid = dual_value >= -abs(float(negative_eps))
            expected = ">= 0"
        else:
            valid = False
            expected = "unsupported"
        if not valid:
            issues.append(f"cut_dual_sign_mismatch:{cut.cut_id}")
        rows.append(
            {
                "cut_id": cut.cut_id,
                "cut_type": cut.cut_type,
                "dual_value": round(float(dual_value), 9),
                "expected_sign": expected,
                "valid": bool(valid),
            }
        )
    return {
        "schema_version": "lunar_ice_bpc.b4_cut_dual_sign_audit.v1",
        "cut_count": len(cut_context.cuts),
        "rows": rows,
        "issues": issues,
        "valid": not issues,
    }


def _branch_signature(context: BranchContext | None) -> tuple[str, ...]:
    if context is None or context.empty:
        return tuple()
    return tuple(f"{a}:{b}:{sense}" for a, b, sense in (decision.key for decision in context.pair_decisions))
