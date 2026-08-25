#!/usr/bin/env python3
"""Bind selective Oracle evidence to an already calibrated QG2 manifest.

The bounded fixed-arm Oracle and the selective activation policy answer
different questions.  This post-calibration binder preserves that separation:
the selective evidence may authorize model loading for evaluation, while the
independent fresh-process calibration remains the only source of deployment
authority.  The source manifest is immutable and the output is a new artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (  # noqa: E402
    SELECTIVE_TRAINING_ONLY_MODE,
    attach_selective_oracle_evidence_to_manifest,
    validate_qg2_oracle_evidence,
)
from lunar_ice_bpc.guidance.qg2_calibration_authority import (  # noqa: E402
    validate_qg2_calibration_performance_authority,
)


MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
RISK_AUDIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"
BINDING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_selective_runtime_binding.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-manifest", required=True)
    parser.add_argument("--calibration-report", required=True)
    parser.add_argument("--risk-audit", required=True)
    parser.add_argument("--selective-evidence", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = _resolve(args.output)
    if output.exists():
        raise SystemExit("selective runtime manifest refuses overwrite")
    payload = bind_selective_runtime_manifest(
        base_manifest_path=_resolve(args.base_manifest),
        calibration_report_path=_resolve(args.calibration_report),
        risk_audit_path=_resolve(args.risk_audit),
        selective_evidence_path=_resolve(args.selective_evidence),
    )
    _write(output, payload)
    print(json.dumps({
        "status": "SELECTIVE_RUNTIME_MANIFEST_BOUND",
        "output": str(output),
        "deployment_authorized": bool(payload["deployment_authorized"]),
        "oracle_evidence_mode": payload["oracle_evidence"]["mode"],
    }, sort_keys=True), flush=True)
    return 0


def bind_selective_runtime_manifest(
    *,
    base_manifest_path: Path,
    calibration_report_path: Path,
    risk_audit_path: Path,
    selective_evidence_path: Path,
) -> dict:
    for path in (
        base_manifest_path,
        calibration_report_path,
        risk_audit_path,
        selective_evidence_path,
    ):
        if not path.is_file():
            raise ValueError(f"selective runtime binding input missing: {path}")

    manifest = _load(base_manifest_path)
    calibration = _load(calibration_report_path)
    risk = _load(risk_audit_path)
    evidence = _load(selective_evidence_path)
    errors: list[str] = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        errors.append("manifest_schema_mismatch")
    if calibration.get("schema_version") != CALIBRATION_SCHEMA:
        errors.append("calibration_schema_mismatch")
    if risk.get("schema_version") != RISK_AUDIT_SCHEMA:
        errors.append("risk_audit_schema_mismatch")
    if validate_qg2_oracle_evidence(evidence) != SELECTIVE_TRAINING_ONLY_MODE:
        errors.append("oracle_evidence_mode_mismatch")
    try:
        validate_qg2_calibration_performance_authority(
            calibration,
            manifest,
        )
    except ValueError as exc:
        errors.append(str(exc))

    declared_manifest = _resolve(calibration.get("manifest_path") or "")
    if declared_manifest != base_manifest_path:
        errors.append("calibration_manifest_path_mismatch")
    if str(calibration.get("manifest_sha256") or "") != _sha256(
        base_manifest_path
    ):
        errors.append("calibration_manifest_hash_mismatch")
    if not bool(calibration.get("gate_pass")):
        errors.append("calibration_gate_not_passed")
    if not bool(calibration.get("deployment_authorized")):
        errors.append("calibration_deployment_not_authorized")
    if not bool(manifest.get("evaluation_authorized")):
        errors.append("manifest_evaluation_not_authorized")
    if not bool(manifest.get("deployment_authorized")):
        errors.append("manifest_deployment_not_authorized")
    if not bool((manifest.get("calibration") or {}).get("gate_pass")):
        errors.append("manifest_calibration_gate_not_passed")
    if not bool(manifest.get("ordering_only")):
        errors.append("manifest_ordering_only_contract_missing")
    for key in ("can_filter", "can_prune", "can_change_bound", "can_certify"):
        if bool(manifest.get(key)):
            errors.append(f"manifest_forbidden_authority:{key}")
    if str(manifest.get("fallback") or "") != "P0V4_V5_Q0":
        errors.append("manifest_literal_q0_fallback_mismatch")
    checkpoint_value = str(manifest.get("checkpoint_path") or "").strip()
    checkpoint_path = Path(checkpoint_value)
    if checkpoint_value and not checkpoint_path.is_absolute():
        checkpoint_path = (base_manifest_path.parent / checkpoint_path).resolve()
    expected_checkpoint_hash = str(
        manifest.get("checkpoint_sha256") or ""
    )
    if not checkpoint_value or not checkpoint_path.is_file():
        errors.append("manifest_checkpoint_missing")
    elif not expected_checkpoint_hash or _sha256(
        checkpoint_path
    ) != expected_checkpoint_hash:
        errors.append("manifest_checkpoint_hash_mismatch")
    declared_risk_calibration = _resolve(
        risk.get("calibration_report") or ""
    )
    if declared_risk_calibration != calibration_report_path:
        errors.append("risk_audit_calibration_path_mismatch")
    if str(risk.get("calibration_report_sha256") or "") != _sha256(
        calibration_report_path
    ):
        errors.append("risk_audit_calibration_hash_mismatch")
    if not bool(risk.get("passed")):
        errors.append("risk_audit_not_passed")
    if not bool(risk.get("deployment_authorized")):
        errors.append("risk_audit_deployment_not_authorized")
    if list(risk.get("issues") or ()):
        errors.append("risk_audit_has_issues")
    risk_policy = dict(risk.get("risk_policy") or {})
    for key in (
        "activated_right_censored_is_deployment_veto",
        "activated_unsafe_is_deployment_veto",
        "unselected_adverse_context_falls_back_to_literal_q0",
        "censored_outcome_is_not_relabeled_as_negative_training_data",
    ):
        if not bool(risk_policy.get(key)):
            errors.append(f"risk_policy_missing:{key}")
    risk_counts = dict(risk.get("counts") or {})
    for key in (
        "activated_right_censored_count",
        "activated_unsafe_count",
        "activated_memory_adverse_count",
    ):
        if int(risk_counts.get(key) or 0) != 0:
            errors.append(f"risk_audit_adverse_activation:{key}")
    if bool(evidence.get("deployment_authorized")):
        errors.append("oracle_evidence_has_deployment_authority")
    if errors:
        raise ValueError(
            "selective runtime binding contract failed: "
            + ",".join(sorted(set(errors)))
        )

    attached = attach_selective_oracle_evidence_to_manifest(
        manifest, evidence
    )
    attached.update({
        # A copied manifest must not reinterpret a relative checkpoint path
        # against its new output directory.
        "checkpoint_path": str(checkpoint_path),
        "selective_runtime_binding_schema_version": BINDING_SCHEMA,
        "base_manifest": str(base_manifest_path),
        "base_manifest_sha256": _sha256(base_manifest_path),
        "fresh_process_calibration_report": str(calibration_report_path),
        "fresh_process_calibration_report_sha256": _sha256(
            calibration_report_path
        ),
        "calibration_risk_audit": str(risk_audit_path),
        "calibration_risk_audit_sha256": _sha256(risk_audit_path),
        "selective_oracle_evidence_path": str(selective_evidence_path),
        "selective_oracle_evidence_sha256": _sha256(
            selective_evidence_path
        ),
        "deployment_authority_source": (
            "fresh_process_calibration_and_risk_audit_only"
        ),
        "oracle_evidence_authority": "model_fitting_and_evaluation_only",
    })
    return attached


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
