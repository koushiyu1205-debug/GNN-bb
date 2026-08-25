"""Independent numerical validation of QG2 calibration authority."""

from __future__ import annotations

import math
from typing import Any, Mapping


EXPECTED_MODEL_KINDS = frozenset({"linear", "mlp", "gat"})
MAXIMUM_HARMFUL_RATE_95_UPPER = 0.05
MINIMUM_BENEFICIAL_PRECISION_95_LOWER = 0.80
MAXIMUM_HELDOUT_TAIL_RATIO = 0.90
MAXIMUM_GAT_VS_BEST_NON_GAT_RATIO = 0.98
MAXIMUM_INFERENCE_P99_MS = 10.0


def validate_qg2_calibration_performance_authority(
    calibration_report: Mapping[str, Any],
    runtime_manifest: Mapping[str, Any],
) -> None:
    """Recheck every numerical deployment gate instead of trusting a flag."""

    errors: list[str] = []
    models = {
        str(row.get("model_kind") or ""): dict(row)
        for row in calibration_report.get("models") or ()
        if isinstance(row, Mapping)
    }
    if set(models) != EXPECTED_MODEL_KINDS:
        errors.append("model_comparison_universe_mismatch")
    gat = dict(models.get("gat") or {})
    gat_calibration = dict(gat.get("calibration") or {})
    gat_heldout = dict(gat.get("heldout") or {})
    thresholds = dict(gat.get("thresholds") or {})
    manifest_calibration = dict(runtime_manifest.get("calibration") or {})

    if not bool(gat_calibration.get("passes_risk_precision_gate")):
        errors.append("gat_calibration_risk_precision_gate_failed")
    harmful = _number(
        gat_calibration.get("harmful_rate_95_upper"),
        "gat_harmful_rate_95_upper_missing",
        errors,
    )
    precision = _number(
        gat_calibration.get("beneficial_precision_95_lower"),
        "gat_beneficial_precision_95_lower_missing",
        errors,
    )
    heldout = _number(
        gat_heldout.get("net_geomean_ratio"),
        "gat_heldout_tail_ratio_missing",
        errors,
    )
    advantage = _number(
        calibration_report.get("gat_vs_best_non_gat_ratio"),
        "gat_vs_best_non_gat_ratio_missing",
        errors,
    )
    inference_p99 = _number(
        calibration_report.get("gat_inference_p99_ms"),
        "gat_inference_p99_missing",
        errors,
    )
    if harmful is not None and harmful > MAXIMUM_HARMFUL_RATE_95_UPPER:
        errors.append("gat_harmful_rate_95_upper_exceeded")
    if precision is not None and precision < MINIMUM_BENEFICIAL_PRECISION_95_LOWER:
        errors.append("gat_beneficial_precision_95_lower_not_met")
    if heldout is not None and heldout > MAXIMUM_HELDOUT_TAIL_RATIO:
        errors.append("gat_heldout_tail_ratio_not_met")
    if advantage is not None and advantage > MAXIMUM_GAT_VS_BEST_NON_GAT_RATIO:
        errors.append("gat_advantage_over_non_gat_not_met")
    if inference_p99 is not None and not (
        0.0 <= inference_p99 <= MAXIMUM_INFERENCE_P99_MS
    ):
        errors.append("gat_inference_p99_exceeded")

    if not bool(
        calibration_report.get("gate_pass")
        and calibration_report.get("deployment_authorized")
        and runtime_manifest.get("evaluation_authorized")
        and runtime_manifest.get("deployment_authorized")
        and manifest_calibration.get("gate_pass")
    ):
        errors.append("calibration_or_manifest_authority_missing")
    if str(gat.get("checkpoint_sha256") or "") != str(
        runtime_manifest.get("checkpoint_sha256") or ""
    ) or not str(gat.get("checkpoint_sha256") or ""):
        errors.append("gat_checkpoint_manifest_binding_mismatch")
    for kind in EXPECTED_MODEL_KINDS:
        if not str((models.get(kind) or {}).get("checkpoint_sha256") or ""):
            errors.append(f"model_checkpoint_hash_missing:{kind}")

    _require_equal_number(
        manifest_calibration,
        "harmful_rate_95_upper",
        harmful,
        "manifest_harmful_rate_mismatch",
        errors,
    )
    _require_equal_number(
        manifest_calibration,
        "beneficial_precision_95_lower",
        precision,
        "manifest_beneficial_precision_mismatch",
        errors,
    )
    _require_equal_number(
        manifest_calibration,
        "heldout_tail_ratio",
        heldout,
        "manifest_heldout_tail_ratio_mismatch",
        errors,
    )
    _require_equal_number(
        manifest_calibration,
        "gat_vs_best_non_gat_ratio",
        advantage,
        "manifest_gat_advantage_ratio_mismatch",
        errors,
    )
    for key in ("probability_threshold", "expected_gain_threshold"):
        expected = _number(
            thresholds.get(key),
            f"gat_{key}_missing",
            errors,
        )
        _require_equal_number(
            manifest_calibration,
            key,
            expected,
            f"manifest_{key}_mismatch",
            errors,
        )
    if errors:
        raise ValueError(
            "QG2 calibration performance authority failed:"
            + ",".join(sorted(set(errors)))
        )


def _number(
    value: Any,
    error: str,
    errors: list[str],
) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        errors.append(error)
        return None
    if not math.isfinite(result):
        errors.append(error)
        return None
    return result


def _require_equal_number(
    payload: Mapping[str, Any],
    key: str,
    expected: float | None,
    error: str,
    errors: list[str],
) -> None:
    observed = _number(payload.get(key), error, errors)
    if (
        observed is not None
        and expected is not None
        and not math.isclose(observed, expected, rel_tol=0.0, abs_tol=1.0e-12)
    ):
        errors.append(error)
