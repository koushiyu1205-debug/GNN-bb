#!/usr/bin/env python3
"""Run development Q0/GAT E2E from the selective runtime authority."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import run_p0v5_qg2_action_surface_v2_e2e_after_calibration as base  # noqa: E402

from lunar_ice_bpc.guidance.qg2_oracle_evidence import (  # noqa: E402
    SELECTIVE_TRAINING_ONLY_MODE,
)
from lunar_ice_bpc.guidance.qg2_runtime_oracle_authority import (  # noqa: E402
    validate_qg2_runtime_oracle_authority,
)


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
AUTHORITY = RUN_ROOT / "qg2_training_only_v2_selective_runtime_authority.json"
TRAINING_REPORT = (
    RUN_ROOT
    / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
)
OUTPUT_ROOT = RUN_ROOT / "e2e_qg2_selective_runtime_v1"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "e2e_qg2_selective_runtime_v1_acceptance.json"
STATE = RUN_ROOT / "qg2_selective_runtime_e2e_state.json"

AUTHORITY_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_selective_runtime_e2e_authority.v1"
)
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
ACCEPTANCE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _state("WAITING_FOR_SELECTIVE_RUNTIME_BINDING", wait_for_pid=args.wait_for_pid)
    while _matching_binding_controller(args.wait_for_pid):
        time.sleep(poll)

    if not AUTHORITY.is_file() or not TRAINING_REPORT.is_file():
        _state("NOT_STARTED_SELECTIVE_RUNTIME_AUTHORITY_MISSING")
        return 2
    authority = _load(AUTHORITY)
    training = _load(TRAINING_REPORT)
    try:
        manifest = validate_selective_runtime_e2e_authority(
            authority,
            authority_path=AUTHORITY,
            training=training,
            training_path=TRAINING_REPORT,
        )
    except Exception as exc:
        _state(
            "NOT_STARTED_SELECTIVE_RUNTIME_AUTHORITY_INVALID",
            error=f"{type(exc).__name__}:{exc}",
        )
        return 3
    if OUTPUT_ROOT.exists() or RESULT.exists():
        _state("REFUSED_EXISTING_SELECTIVE_RUNTIME_E2E_OUTPUT")
        return 3
    instances = base._heldout_instances(training)

    _state(
        "RUNNING_SELECTIVE_RUNTIME_EXACT_CONTROL",
        instances=[str(path) for path in instances],
        manifest=str(manifest),
    )
    control_code = base._run_acceptance(
        output=CONTROL_ROOT,
        instances=instances,
        manifest=None,
    )
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=int(control_code))
        return int(control_code)
    _state("RUNNING_SELECTIVE_RUNTIME_QG2", manifest=str(manifest))
    guided_code = base._run_acceptance(
        output=GUIDED_ROOT,
        instances=instances,
        manifest=manifest,
    )
    if guided_code not in {0, 1}:
        _state("GUIDED_EXECUTION_ERROR", returncode=int(guided_code))
        return int(guided_code)

    analyzed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/analyze_p0v5_qg2_paired_acceptance.py"),
            "--control-root", str(CONTROL_ROOT),
            "--guided-root", str(GUIDED_ROOT),
            "--output", str(RESULT),
            "--mode", "development",
        ],
        cwd=ROOT,
        env=base._environment(manifest=None),
        check=False,
    )
    if analyzed.returncode not in {0, 2} or not RESULT.is_file():
        _state("ANALYZER_EXECUTION_ERROR", returncode=int(analyzed.returncode))
        return int(analyzed.returncode or 3)
    result = _load(RESULT)
    passed = bool(
        result.get("schema_version") == ACCEPTANCE_SCHEMA
        and result.get("mode") == "development"
        and result.get("passed")
        and int(result.get("violation_count") or 0) == 0
    )
    _state(
        (
            "SELECTIVE_RUNTIME_E2E_PASSED_PENDING_FORMAL"
            if passed
            else "SELECTIVE_RUNTIME_E2E_GATE_FAILED"
        ),
        authority=str(AUTHORITY),
        authority_sha256=_sha256(AUTHORITY),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        formal_experiment_authorized=passed,
        production_switch_authorized=False,
        fallback_action="Q0",
    )
    return 0 if passed else 2


def validate_selective_runtime_e2e_authority(
    authority: Mapping[str, Any],
    *,
    authority_path: Path,
    training: Mapping[str, Any],
    training_path: Path,
) -> Path:
    errors: list[str] = []
    if authority.get("schema_version") != AUTHORITY_SCHEMA:
        errors.append("authority_schema_mismatch")
    if not bool(authority.get("development_only")) or not bool(
        authority.get("development_e2e_authorized")
    ):
        errors.append("development_e2e_not_authorized")
    if bool(authority.get("formal_experiment_authorized")) or bool(
        authority.get("production_switch_authorized")
    ):
        errors.append("authority_scope_expansion")
    if str(authority.get("fallback_action") or "") != "Q0" or str(
        authority.get("all_arms_rejected_action") or ""
    ) != "Q0":
        errors.append("literal_q0_fallback_mismatch")
    if str(authority.get("oracle_evidence_mode") or "") != (
        SELECTIVE_TRAINING_ONLY_MODE
    ):
        errors.append("oracle_evidence_mode_mismatch")
    if not bool(authority.get("ordering_only")):
        errors.append("ordering_only_contract_missing")

    manifest = _bound_path(
        authority,
        authority_path=authority_path,
        path_key="runtime_manifest",
        hash_key="runtime_manifest_sha256",
        errors=errors,
    )
    for path_key, hash_key in (
        ("calibration_report", "calibration_report_sha256"),
        ("calibration_risk_audit", "calibration_risk_audit_sha256"),
        ("selective_oracle_evidence", "selective_oracle_evidence_sha256"),
        ("context_selector_report", "context_selector_report_sha256"),
    ):
        _bound_path(
            authority,
            authority_path=authority_path,
            path_key=path_key,
            hash_key=hash_key,
            errors=errors,
        )
    if training.get("schema_version") != TRAINING_SCHEMA:
        errors.append("training_schema_mismatch")
    if not bool(training.get("oracle_gate_passed")) or bool(
        training.get("deployable")
    ):
        errors.append("training_authority_mismatch")
    if not training_path.is_file():
        errors.append("training_report_missing")

    if manifest.is_file():
        payload = _load(manifest)
        try:
            mode = validate_qg2_runtime_oracle_authority(payload)
        except Exception as exc:
            errors.append(f"runtime_oracle_authority:{type(exc).__name__}:{exc}")
            mode = ""
        if mode != SELECTIVE_TRAINING_ONLY_MODE:
            errors.append("runtime_oracle_authority_mode_mismatch")
        if not bool(payload.get("deployment_authorized")):
            errors.append("runtime_manifest_not_calibration_authorized")
        if str(payload.get("fallback") or "") != "P0V4_V5_Q0":
            errors.append("runtime_manifest_literal_q0_fallback_mismatch")
        for key in ("can_filter", "can_prune", "can_change_bound", "can_certify"):
            if bool(payload.get(key)):
                errors.append(f"runtime_manifest_forbidden_authority:{key}")
    if errors:
        raise ValueError(
            "selective runtime E2E authority failed: "
            + ",".join(sorted(set(errors)))
        )
    return manifest


def _bound_path(
    payload: Mapping[str, Any],
    *,
    authority_path: Path,
    path_key: str,
    hash_key: str,
    errors: list[str],
) -> Path:
    raw = Path(str(payload.get(path_key) or ""))
    path = raw.resolve() if raw.is_absolute() else (
        authority_path.parent / raw
    ).resolve()
    if not path.is_file():
        errors.append(f"{path_key}_missing")
    elif str(payload.get(hash_key) or "") != _sha256(path):
        errors.append(f"{path_key}_hash_mismatch")
    return path


def _matching_binding_controller(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_selective_runtime_binding_after_calibration.py" in command


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_selective_runtime_e2e_state.v1",
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": str(status),
        **extra,
    })


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
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
