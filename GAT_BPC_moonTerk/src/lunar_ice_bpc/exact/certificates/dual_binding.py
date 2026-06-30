"""RMP dual-vector binding artifact for pricing proof inputs."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def build_rmp_dual_binding_from_result(
    rmp: Any,
    *,
    source: str,
    binding_scope: str,
    pricing_source: str | None = None,
) -> dict[str, Any]:
    """Bind a pricing call to a solved RMP result's dual vector."""

    duals = getattr(rmp, "duals", None)
    cover_duals = dict(getattr(duals, "cover", {}) or {})
    cut_duals = dict(getattr(duals, "cuts", {}) or {})
    fleet_dual = getattr(duals, "fleet_limit", None)
    payload = {
        "status": getattr(rmp, "status", None),
        "exact_status": getattr(rmp, "exact_status", None),
        "objective_bound": getattr(rmp, "objective_bound", None),
        "min_reduced_cost": getattr(rmp, "min_reduced_cost", None),
        "task_cover_duals": cover_duals,
        "fleet_dual": fleet_dual,
        "cut_duals": cut_duals,
        "branch_context": getattr(rmp, "branch_context", None),
        "cut_context": getattr(rmp, "cut_context", None),
        "cut_rows_active": getattr(rmp, "cut_rows_active", None),
    }
    return build_rmp_dual_binding_from_payload(
        payload,
        source=source,
        binding_scope=binding_scope,
        pricing_source=pricing_source,
    )


def build_rmp_dual_binding_from_payload(
    rmp_payload: Mapping[str, Any],
    *,
    source: str,
    binding_scope: str,
    pricing_source: str | None = None,
) -> dict[str, Any]:
    """Build a JSON-safe dual binding from a restricted-RMP payload."""

    cover_duals = _float_mapping(rmp_payload.get("task_cover_duals") or {})
    cut_duals = _float_mapping(rmp_payload.get("cut_duals") or {})
    fleet_dual = _float_or_none(rmp_payload.get("fleet_dual"))
    rmp_status = str(rmp_payload.get("status") or "UNKNOWN")
    missing = []
    if rmp_status != "RESTRICTED_RMP_OPTIMAL":
        missing.append("rmp_not_optimal")
    if not cover_duals and rmp_payload.get("task_cover_duals") is None:
        missing.append("task_cover_duals_missing")
    if fleet_dual is None:
        missing.append("fleet_dual_missing")
    fingerprint_payload = {
        "status": rmp_status,
        "objective_bound": _float_or_none(rmp_payload.get("objective_bound")),
        "min_reduced_cost": _float_or_none(rmp_payload.get("min_reduced_cost")),
        "cover": cover_duals,
        "fleet": fleet_dual,
        "cuts": cut_duals,
        "branch_context": rmp_payload.get("branch_context") or {},
        "cut_context": rmp_payload.get("cut_context") or {},
    }
    bound = not missing
    return {
        "schema_version": "lunar_ice_bpc.rmp_dual_binding.v1",
        "status": "RMP_DUAL_VECTOR_BOUND" if bound else "RMP_DUAL_VECTOR_UNBOUND",
        "source": str(source),
        "binding_scope": str(binding_scope),
        "pricing_source": pricing_source,
        "dual_vector_bound_to_rmp": bound,
        "rmp_status": rmp_status,
        "rmp_exact_status": rmp_payload.get("exact_status"),
        "objective_bound": _float_or_none(rmp_payload.get("objective_bound")),
        "min_reduced_cost": _float_or_none(rmp_payload.get("min_reduced_cost")),
        "task_cover_dual_count": len(cover_duals),
        "cut_dual_count": len(cut_duals),
        "has_fleet_dual": fleet_dual is not None,
        "cut_rows_active": bool(rmp_payload.get("cut_rows_active")),
        "dual_vector_fingerprint": _fingerprint(fingerprint_payload) if bound else None,
        "missing_input_count": len(missing),
        "missing_inputs": missing,
        "mutates_solver": False,
        "can_certify_no_negative": False,
        "note": (
            "Pricing evidence is bound to this RMP dual vector. This is a proof input, not a certificate."
            if bound
            else "The RMP dual vector is not fully bound; pricing evidence must fail closed."
        ),
    }


def _float_mapping(values: Mapping[str, Any]) -> dict[str, float]:
    result: dict[str, float] = {}
    for key, value in values.items():
        parsed = _float_or_none(value)
        if parsed is not None:
            result[str(key)] = parsed
    return dict(sorted(result.items()))


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 12)
    except (TypeError, ValueError):
        return None


def _fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
