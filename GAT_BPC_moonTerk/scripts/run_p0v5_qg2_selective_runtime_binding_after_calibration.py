#!/usr/bin/env python3
"""Bind the selective QG2 runtime only after every safety authority exists.

This controller is deliberately downstream of model fitting, the offline
context-arm selector, fresh-process calibration, the activated-action risk
audit, and the selective Oracle-evidence sidecar.  It creates a new manifest
and a hash-bound E2E authority; it never edits the calibrated base manifest or
authorizes a production-default switch.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (  # noqa: E402
    SELECTIVE_TRAINING_ONLY_MODE,
    validate_qg2_oracle_evidence,
)
from lunar_ice_bpc.guidance.qg2_calibration_authority import (  # noqa: E402
    validate_qg2_calibration_performance_authority,
)
from lunar_ice_bpc.guidance.qg2_runtime_oracle_authority import (  # noqa: E402
    validate_qg2_runtime_oracle_authority,
)
from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (  # noqa: E402
    QG2_RUNTIME_POLICY_ID,
    qg2_runtime_implementation_hash,
)


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
CALIBRATION_STATE = (
    RUN_ROOT / "qg2_training_only_v2_calibration_controller_state.json"
)
CALIBRATION_REPORT = (
    RUN_ROOT
    / "calibration_qg2_action_surface_v2_training_only_v2"
    / "calibration_report.json"
)
RISK_AUDIT = RUN_ROOT / "qg2_training_only_v2_calibration_risk_audit.json"
SELECTIVE_EVIDENCE_STATE = (
    RUN_ROOT / "qg2_selective_oracle_evidence_controller_state.json"
)
SELECTIVE_EVIDENCE = (
    RUN_ROOT / "qg2_training_only_v2_selective_oracle_evidence.json"
)
SELECTOR_REPORT = (
    RUN_ROOT / "context_arm_selector_feasibility_v1/selector_report.json"
)
BOUND_MANIFEST = RUN_ROOT / "qg2_training_only_v2_selective_runtime_manifest.json"
AUTHORITY = RUN_ROOT / "qg2_training_only_v2_selective_runtime_authority.json"
STATE = RUN_ROOT / "qg2_training_only_v2_selective_runtime_binding_state.json"
BINDER = ROOT / "scripts/bind_p0v5_qg2_selective_runtime_manifest.py"

CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
RISK_SCHEMA = "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"
SELECTOR_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"
)
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_qg2_manifest.v1"
AUTHORITY_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_selective_runtime_e2e_authority.v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-calibration-pid", type=int, required=True)
    parser.add_argument("--wait-for-evidence-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _state(
        "WAITING_FOR_CALIBRATION_AND_SELECTIVE_EVIDENCE",
        wait_for_calibration_pid=int(args.wait_for_calibration_pid),
        wait_for_evidence_pid=int(args.wait_for_evidence_pid),
    )
    while (
        _matching_process(
            args.wait_for_calibration_pid,
            "run_p0v5_qg2_training_only_v2_calibration_after_selector.py",
        )
        or _matching_process(
            args.wait_for_evidence_pid,
            "run_p0v5_qg2_selective_oracle_evidence_after_training.py",
        )
    ):
        time.sleep(poll)

    required = (
        CALIBRATION_STATE,
        CALIBRATION_REPORT,
        RISK_AUDIT,
        SELECTIVE_EVIDENCE_STATE,
        SELECTIVE_EVIDENCE,
        SELECTOR_REPORT,
    )
    if not all(path.is_file() for path in required):
        _state(
            "NOT_STARTED_REQUIRED_AUTHORITY_MISSING",
            missing=[str(path) for path in required if not path.is_file()],
        )
        return 2
    if BOUND_MANIFEST.exists() or AUTHORITY.exists():
        _state("REFUSED_EXISTING_SELECTIVE_RUNTIME_OUTPUT")
        return 3

    calibration = _load(CALIBRATION_REPORT)
    base_manifest = _resolve(calibration.get("manifest_path") or "")
    if not base_manifest.is_file():
        _state("NOT_STARTED_BASE_MANIFEST_MISSING")
        return 3
    completed = subprocess.run(
        [
            sys.executable,
            str(BINDER),
            "--base-manifest", str(base_manifest),
            "--calibration-report", str(CALIBRATION_REPORT),
            "--risk-audit", str(RISK_AUDIT),
            "--selective-evidence", str(SELECTIVE_EVIDENCE),
            "--output", str(BOUND_MANIFEST),
        ],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != 0 or not BOUND_MANIFEST.is_file():
        _state(
            "SELECTIVE_RUNTIME_BINDING_FAILED",
            returncode=int(completed.returncode),
        )
        return int(completed.returncode or 3)

    try:
        authority = build_selective_runtime_e2e_authority(
            calibration_state_path=CALIBRATION_STATE,
            calibration_report_path=CALIBRATION_REPORT,
            risk_audit_path=RISK_AUDIT,
            selective_evidence_state_path=SELECTIVE_EVIDENCE_STATE,
            selective_evidence_path=SELECTIVE_EVIDENCE,
            selector_report_path=SELECTOR_REPORT,
            bound_manifest_path=BOUND_MANIFEST,
        )
    except Exception as exc:
        _state(
            "SELECTIVE_RUNTIME_AUTHORITY_FAILED",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3
    _write(AUTHORITY, authority)
    _state(
        "SELECTIVE_RUNTIME_BOUND_PENDING_DEVELOPMENT_E2E",
        authority=str(AUTHORITY),
        authority_sha256=_sha256(AUTHORITY),
        manifest=str(BOUND_MANIFEST),
        manifest_sha256=_sha256(BOUND_MANIFEST),
        development_e2e_authorized=True,
        production_switch_authorized=False,
        fallback_action="Q0",
    )
    return 0


def build_selective_runtime_e2e_authority(
    *,
    calibration_state_path: Path,
    calibration_report_path: Path,
    risk_audit_path: Path,
    selective_evidence_state_path: Path,
    selective_evidence_path: Path,
    selector_report_path: Path,
    bound_manifest_path: Path,
) -> dict[str, Any]:
    paths = (
        calibration_state_path,
        calibration_report_path,
        risk_audit_path,
        selective_evidence_state_path,
        selective_evidence_path,
        selector_report_path,
        bound_manifest_path,
    )
    if not all(path.is_file() for path in paths):
        raise ValueError("selective runtime authority input missing")
    calibration_state = _load(calibration_state_path)
    calibration = _load(calibration_report_path)
    risk = _load(risk_audit_path)
    evidence_state = _load(selective_evidence_state_path)
    evidence = _load(selective_evidence_path)
    selector = _load(selector_report_path)
    manifest = _load(bound_manifest_path)
    errors: list[str] = []

    if str(calibration_state.get("status") or "") != (
        "CALIBRATION_AND_RISK_AUDIT_PASSED_PENDING_E2E"
    ):
        errors.append("calibration_controller_not_authorized")
    if str(calibration_state.get("calibration_report_sha256") or "") != (
        _sha256(calibration_report_path)
    ):
        errors.append("calibration_controller_report_hash_mismatch")
    if str(calibration_state.get("risk_audit_sha256") or "") != _sha256(
        risk_audit_path
    ):
        errors.append("calibration_controller_risk_hash_mismatch")
    if calibration.get("schema_version") != CALIBRATION_SCHEMA:
        errors.append("calibration_schema_mismatch")
    if not bool(calibration.get("gate_pass")) or not bool(
        calibration.get("deployment_authorized")
    ):
        errors.append("calibration_not_authorized")
    try:
        validate_qg2_calibration_performance_authority(
            calibration,
            manifest,
        )
    except ValueError as exc:
        errors.append(str(exc))

    if risk.get("schema_version") != RISK_SCHEMA:
        errors.append("risk_schema_mismatch")
    if not bool(risk.get("passed")) or not bool(
        risk.get("deployment_authorized")
    ):
        errors.append("risk_not_authorized")
    if str(risk.get("calibration_report_sha256") or "") != _sha256(
        calibration_report_path
    ):
        errors.append("risk_calibration_hash_mismatch")

    if str(evidence_state.get("status") or "") != (
        "SELECTIVE_ORACLE_EVIDENCE_FROZEN"
    ):
        errors.append("selective_evidence_controller_not_frozen")
    if str(evidence_state.get("evidence_sha256") or "") != _sha256(
        selective_evidence_path
    ):
        errors.append("selective_evidence_controller_hash_mismatch")
    if validate_qg2_oracle_evidence(evidence) != SELECTIVE_TRAINING_ONLY_MODE:
        errors.append("selective_evidence_mode_mismatch")
    if bool(evidence.get("deployment_authorized")):
        errors.append("selective_evidence_has_deployment_authority")

    if selector.get("schema_version") != SELECTOR_SCHEMA:
        errors.append("selector_schema_mismatch")
    if bool(selector.get("continued_development_recommended")):
        errors.append("combined_selector_implementation_required")
    if bool(selector.get("deployable")):
        errors.append("selector_has_deployment_authority")
    if str(selector.get("fallback_action") or "") != "Q0" or str(
        selector.get("all_arms_rejected_action") or ""
    ) != "Q0":
        errors.append("selector_literal_q0_fallback_mismatch")

    if manifest.get("schema_version") != MANIFEST_SCHEMA:
        errors.append("bound_manifest_schema_mismatch")
    if str(manifest.get("runtime_policy_id") or "") != QG2_RUNTIME_POLICY_ID:
        errors.append("bound_manifest_runtime_policy_mismatch")
    if str(manifest.get("runtime_implementation_hash") or "") != (
        qg2_runtime_implementation_hash()
    ):
        errors.append("bound_manifest_runtime_implementation_drift")
    if str(manifest.get("feature_schema_version") or "") != (
        "lunar_ice_bpc.p0v5_qg2_features.v1"
    ):
        errors.append("bound_manifest_feature_schema_mismatch")
    if str(manifest.get("label_state_schema_version") or "") != (
        "lunar_spprc.qg2_label_state.v1"
    ):
        errors.append("bound_manifest_label_state_schema_mismatch")
    if {int(value) for value in manifest.get("allowed_scales") or ()} != {
        30, 50
    }:
        errors.append("bound_manifest_allowed_scales_mismatch")
    if not list(manifest.get("allowed_exact_engine_hashes") or ()):
        errors.append("bound_manifest_engine_allowlist_missing")
    if not list(manifest.get("allowed_exact_action_policy_hashes") or ()):
        errors.append("bound_manifest_action_policy_allowlist_missing")
    checkpoint = _resolve_manifest_relative_path(
        bound_manifest_path,
        manifest.get("checkpoint_path") or "",
    )
    if not checkpoint.is_file():
        errors.append("bound_manifest_checkpoint_missing")
    elif str(manifest.get("checkpoint_sha256") or "") != _sha256(checkpoint):
        errors.append("bound_manifest_checkpoint_hash_mismatch")
    if not bool(manifest.get("deployment_authorized")):
        errors.append("bound_manifest_not_calibration_authorized")
    if str(manifest.get("fresh_process_calibration_report_sha256") or "") != (
        _sha256(calibration_report_path)
    ):
        errors.append("bound_manifest_calibration_hash_mismatch")
    if str(manifest.get("calibration_risk_audit_sha256") or "") != _sha256(
        risk_audit_path
    ):
        errors.append("bound_manifest_risk_hash_mismatch")
    if str(manifest.get("selective_oracle_evidence_sha256") or "") != (
        _sha256(selective_evidence_path)
    ):
        errors.append("bound_manifest_evidence_hash_mismatch")
    if str(manifest.get("fallback") or "") != "P0V4_V5_Q0":
        errors.append("bound_manifest_literal_q0_fallback_mismatch")
    for key in ("can_filter", "can_prune", "can_change_bound", "can_certify"):
        if bool(manifest.get(key)):
            errors.append(f"bound_manifest_forbidden_authority:{key}")
    try:
        mode = validate_qg2_runtime_oracle_authority(manifest)
    except Exception as exc:
        errors.append(f"runtime_oracle_authority:{type(exc).__name__}:{exc}")
        mode = ""
    if mode != SELECTIVE_TRAINING_ONLY_MODE:
        errors.append("runtime_oracle_authority_mode_mismatch")
    if errors:
        raise ValueError(
            "selective runtime E2E authority failed: "
            + ",".join(sorted(set(errors)))
        )

    return {
        "schema_version": AUTHORITY_SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "development_only": True,
        "development_e2e_authorized": True,
        "formal_experiment_authorized": False,
        "production_switch_authorized": False,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "runtime_manifest": str(bound_manifest_path),
        "runtime_manifest_sha256": _sha256(bound_manifest_path),
        "calibration_report": str(calibration_report_path),
        "calibration_report_sha256": _sha256(calibration_report_path),
        "calibration_risk_audit": str(risk_audit_path),
        "calibration_risk_audit_sha256": _sha256(risk_audit_path),
        "selective_oracle_evidence": str(selective_evidence_path),
        "selective_oracle_evidence_sha256": _sha256(selective_evidence_path),
        "context_selector_report": str(selector_report_path),
        "context_selector_report_sha256": _sha256(selector_report_path),
        "oracle_evidence_mode": mode,
        "ordering_only": True,
    }


def _matching_process(pid: int, script_name: str) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return script_name in command


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_selective_runtime_binding_state.v1"
        ),
        "updated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "status": str(status),
        **extra,
    })


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _resolve_manifest_relative_path(manifest: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (manifest.parent / path).resolve()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any]) -> None:
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
