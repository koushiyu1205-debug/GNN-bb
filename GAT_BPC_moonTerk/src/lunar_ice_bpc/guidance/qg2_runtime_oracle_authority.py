"""Runtime Oracle-authority validation for legacy and selective QG2 manifests.

This module is intentionally separate from the already frozen selective
evidence builder.  It can be integrated into the QG2 runtime after the active
bounded Oracle finishes without changing any currently running hash binding.
"""

from __future__ import annotations

from typing import Any, Mapping

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (
    MAXIMUM_CONTEXTS,
    SCALES,
    STRICT_FIXED_ARM_MODE,
    validate_qg2_manifest_oracle_evidence,
)


def validate_qg2_runtime_oracle_authority(
    manifest: Mapping[str, Any],
) -> str:
    """Validate selective evidence or preserve the original strict gate."""

    if manifest.get("oracle_evidence"):
        return validate_qg2_manifest_oracle_evidence(manifest)

    oracle = dict(manifest.get("oracle_gate") or {})
    if not bool(oracle.get("passed")):
        raise ValueError("QG2 oracle gate has not passed")
    if int(oracle.get("context_count") or 0) > MAXIMUM_CONTEXTS:
        raise ValueError("QG2 oracle exceeded bounded context budget")
    for scale in SCALES:
        _validate_strict_scale(
            scale, dict(oracle.get(f"scale{scale}") or {})
        )
    if int(oracle.get("net_gain_5pct_context_count") or 0) < 50:
        raise ValueError("QG2 oracle has insufficient material wins")
    if float(
        oracle.get("max_instance_saved_wall_fraction", 1.0)
    ) > 0.35:
        raise ValueError("QG2 oracle is dominated by one instance")
    return STRICT_FIXED_ARM_MODE


def _validate_strict_scale(scale: int, row: Mapping[str, Any]) -> None:
    if not bool(
        int(row.get("context_count") or 0) >= 20
        and int(row.get("determined_context_count") or 0) >= 20
        and int(row.get("positive_context_count") or 0) >= 20
        and int(row.get("positive_instance_count") or 0) >= 5
        and float(row.get("paired_geomean_ratio", 1.0)) <= 0.85
        and float(row.get("bootstrap_95_upper", 1.0)) <= 0.90
        and float(row.get("positive_fraction", 0.0)) > 0.20
    ):
        raise ValueError(
            f"QG2 scale{scale} strict fixed-arm evidence mismatch"
        )
