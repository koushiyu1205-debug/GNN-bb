#!/usr/bin/env python3
"""Fail closed on activated censored or unsafe QG2 calibration actions.

The frozen v4 calibrator masks right-censored outcomes when estimating timing
benefit.  That is appropriate for the two training heads, but deployment must
not silently omit an action that TIMEOUTs, reaches MEMORY_LIMIT, or otherwise
fails to produce a matched milestone.  This read-only sidecar recomputes the
frozen GAT activation decision for every calibration/heldout record and vetoes
deployment if any activated record is censored or exact-unsafe.

Unselected records remain literal Q0 and therefore do not count as adverse
GAT actions.  This file never edits the frozen calibration report or manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"
AUDIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibration-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report_path = _resolve(args.calibration_report)
    output_path = _resolve(args.output)
    try:
        report = _load(report_path)
        result = audit_calibration_risk(report, report_path=report_path)
    except Exception as exc:
        result = {
            "passed": False,
            "deployment_authorized": False,
            "issues": [f"audit_exception:{type(exc).__name__}:{exc}"],
            "gat_thresholds": {},
            "counts": {},
        }
    payload = {
        "schema_version": AUDIT_SCHEMA,
        "development_only": True,
        "deployable": bool(result["deployment_authorized"]),
        "calibration_report": str(report_path),
        "calibration_report_sha256": (
            _sha256(report_path) if report_path.is_file() else ""
        ),
        "risk_policy": {
            "activated_right_censored_is_deployment_veto": True,
            "activated_unsafe_is_deployment_veto": True,
            "unselected_adverse_context_falls_back_to_literal_q0": True,
            "censored_outcome_is_not_relabeled_as_negative_training_data": True,
        },
        **result,
    }
    _write(output_path, payload)
    print(json.dumps({
        "passed": payload["passed"],
        "deployment_authorized": payload["deployment_authorized"],
        "issues": payload["issues"],
        "counts": payload["counts"],
    }, sort_keys=True), flush=True)
    return 0 if payload["passed"] else 2


def audit_calibration_risk(
    report: Mapping[str, Any],
    *,
    report_path: Path | None = None,
) -> dict[str, Any]:
    issues: list[str] = []
    if str(report.get("schema_version") or "") != CALIBRATION_SCHEMA:
        issues.append("calibration_schema_mismatch")
    if not bool(report.get("development_only")):
        issues.append("calibration_development_contract_missing")

    models = {
        str(row.get("model_kind") or ""): dict(row)
        for row in report.get("models") or ()
        if isinstance(row, Mapping)
    }
    gat = models.get("gat")
    if not gat:
        issues.append("gat_model_report_missing")
        gat = {}
    thresholds = _thresholds(gat.get("thresholds"), issues)

    records = [
        dict(row)
        for row in report.get("records") or ()
        if isinstance(row, Mapping)
        and str(row.get("model_kind") or "") == "gat"
        and str(row.get("partition") or "") in {"calibration", "heldout"}
    ]
    if not records:
        issues.append("gat_calibration_heldout_records_missing")

    activated: list[dict[str, Any]] = []
    activated_censored: list[dict[str, Any]] = []
    activated_unsafe: list[dict[str, Any]] = []
    activated_memory_adverse: list[dict[str, Any]] = []
    for row in records:
        if not bool(row.get("action_eligible", True)):
            continue
        if not _finite(row.get("benefit_probability")) or not _finite(
            row.get("expected_gain")
        ):
            issues.append(
                "nonfinite_activation_score:"
                f"{str(row.get('state_hash') or '')}"
            )
            continue
        selected = bool(
            float(row["benefit_probability"])
            >= thresholds["probability_threshold"]
            and float(row["expected_gain"])
            >= thresholds["expected_gain_threshold"]
        )
        if not selected:
            continue
        activated.append(row)
        if not bool(row.get("outcome_determined")) or bool(
            row.get("right_censored")
        ):
            activated_censored.append(row)
        if not bool(row.get("safe")):
            activated_unsafe.append(row)
        if _memory_adverse(row):
            activated_memory_adverse.append(row)

    manifest = _bound_manifest(report, report_path, issues)
    manifest_thresholds = dict(
        (manifest.get("calibration") or {}) if manifest else {}
    )
    if manifest:
        for key, value in thresholds.items():
            if not _same_float(manifest_thresholds.get(key), value):
                issues.append(f"manifest_{key}_mismatch")
        if not bool(manifest.get("ordering_only")):
            issues.append("manifest_ordering_only_contract_missing")
        for key in ("can_filter", "can_prune", "can_change_bound", "can_certify"):
            if bool(manifest.get(key)):
                issues.append(f"manifest_forbidden_authority:{key}")
        if str(manifest.get("fallback") or "") != "P0V4_V5_Q0":
            issues.append("manifest_literal_q0_fallback_mismatch")
        if not bool(manifest.get("deployment_authorized")):
            issues.append("manifest_deployment_not_authorized")
        if not bool(manifest_thresholds.get("gate_pass")):
            issues.append("manifest_calibration_gate_not_passed")

    if activated_censored:
        issues.append("activated_right_censored_context")
    if activated_unsafe:
        issues.append("activated_exact_unsafe_context")
    if activated_memory_adverse:
        issues.append("activated_memory_adverse_context")
    base_authorized = bool(
        report.get("gate_pass") and report.get("deployment_authorized")
    )
    if not base_authorized:
        issues.append("base_calibration_not_deployment_authorized")
    if bool(report.get("deployable")) != base_authorized:
        issues.append("base_calibration_deployable_flag_mismatch")
    if base_authorized and not activated:
        issues.append("authorized_calibration_has_zero_recomputed_activations")
    passed = bool(base_authorized and not issues)
    return {
        "passed": passed,
        "deployment_authorized": passed,
        "base_calibration_deployment_authorized": base_authorized,
        "gat_thresholds": thresholds,
        "counts": {
            "gat_calibration_heldout_record_count": len(records),
            "activated_count": len(activated),
            "activated_right_censored_count": len(activated_censored),
            "activated_unsafe_count": len(activated_unsafe),
            "activated_memory_adverse_count": len(activated_memory_adverse),
            "unselected_or_prethreshold_veto_count": (
                len(records) - len(activated)
            ),
        },
        "activated_right_censored_state_hashes": sorted({
            str(row.get("state_hash") or "") for row in activated_censored
        }),
        "activated_unsafe_state_hashes": sorted({
            str(row.get("state_hash") or "") for row in activated_unsafe
        }),
        "activated_memory_adverse_state_hashes": sorted({
            str(row.get("state_hash") or "")
            for row in activated_memory_adverse
        }),
        "issues": list(dict.fromkeys(issues)),
    }


def _thresholds(value: Any, issues: list[str]) -> dict[str, float]:
    raw = dict(value or {}) if isinstance(value, Mapping) else {}
    result = {}
    for key, default in (
        ("probability_threshold", 1.0),
        ("expected_gain_threshold", 1.0e300),
    ):
        candidate = raw.get(key, default)
        if not _finite(candidate):
            issues.append(f"nonfinite_{key}")
            result[key] = default
        else:
            result[key] = float(candidate)
    return result


def _bound_manifest(
    report: Mapping[str, Any],
    report_path: Path | None,
    issues: list[str],
) -> dict[str, Any]:
    raw_path = str(report.get("manifest_path") or "").strip()
    expected = str(report.get("manifest_sha256") or "").strip()
    if not raw_path or not expected:
        issues.append("calibration_manifest_binding_missing")
        return {}
    path = Path(raw_path)
    if not path.is_absolute():
        base = report_path.parent if report_path is not None else ROOT
        path = (base / path).resolve()
    if not path.is_file():
        issues.append("calibration_manifest_missing")
        return {}
    if _sha256(path) != expected:
        issues.append("calibration_manifest_hash_mismatch")
        return {}
    manifest = _load(path)
    if str(manifest.get("schema_version") or "") != MANIFEST_SCHEMA:
        issues.append("calibration_manifest_schema_mismatch")
        return {}
    return manifest


def _memory_adverse(row: Mapping[str, Any]) -> bool:
    if bool(row.get("memory_adverse")):
        return True
    statuses = []
    for key in (
        "engine_status",
        "qg2_engine_status",
        "qg2_termination_reason",
    ):
        if row.get(key) is not None:
            statuses.append(str(row.get(key)).upper())
    for key in ("qg2_engine_statuses", "qg2_termination_reasons"):
        value = row.get(key)
        if isinstance(value, (list, tuple)):
            statuses.extend(str(item).upper() for item in value)
    return any(
        "MEMORY" in value or "OOM" in value or "RSS" in value
        for value in statuses
    )


def _same_float(left: Any, right: float) -> bool:
    return bool(_finite(left) and abs(float(left) - float(right)) <= 1.0e-12)


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
