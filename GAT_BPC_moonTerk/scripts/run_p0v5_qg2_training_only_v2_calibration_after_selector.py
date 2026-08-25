#!/usr/bin/env python3
"""Conditionally calibrate training-only QG2 after selector feasibility.

If the offline QD1/QB1 selector is recommended for continued development, the
controller stops before calibration because the deployed action surface would
first need a separately implemented and tested combined policy.  Otherwise it
runs the unchanged supplemental QG2 calibration path, then applies the frozen
activated-censor/unsafe risk veto.  No result from this controller launches
E2E or production deployment by itself.
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


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_training_only_v2_calibration_controller_freeze.json"
SELECTOR_FREEZE = RUN_ROOT / "qg2_context_arm_selector_controller_freeze.json"
RISK_FREEZE = RUN_ROOT / "qg2_calibration_risk_v2_freeze.json"
STATE = RUN_ROOT / "qg2_training_only_v2_calibration_controller_state.json"
SELECTOR_STATE = RUN_ROOT / "qg2_context_arm_selector_controller_state.json"
SELECTOR_REPORT = (
    RUN_ROOT / "context_arm_selector_feasibility_v1/selector_report.json"
)
TRAINING_REPORT = (
    RUN_ROOT
    / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
)
MANIFEST = RUN_ROOT / "qg2_training_only_v2_supplemental_manifest.json"
OUTPUT_DIR = (
    RUN_ROOT / "calibration_qg2_action_surface_v2_training_only_v2"
)
OUTPUT = OUTPUT_DIR / "calibration_report.json"
RISK_AUDIT = RUN_ROOT / "qg2_training_only_v2_calibration_risk_audit.json"
BUILD_MANIFEST = (
    ROOT / "scripts/build_p0v5_qg2_supplemental_calibration_manifest.py"
)
RUN_CALIBRATION = ROOT / "scripts/run_p0v5_qg2_supplemental_calibration.py"
RUN_RISK_AUDIT = ROOT / "scripts/audit_p0v5_qg2_calibration_risk_v2.py"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SELECTOR_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"
)
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
RISK_AUDIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_CONTEXT_ARM_SELECTOR", wait_for_pid=args.wait_for_pid)
    while _matching_selector_controller_alive(args.wait_for_pid):
        time.sleep(poll)

    if not SELECTOR_REPORT.is_file() or not SELECTOR_STATE.is_file():
        _state("NOT_STARTED_SELECTOR_REPORT_MISSING")
        return 2
    selector = _load(SELECTOR_REPORT)
    selector_state = _load(SELECTOR_STATE)
    if not _valid_selector(selector, selector_state):
        _state("NOT_STARTED_SELECTOR_CONTRACT_FAILED")
        return 3
    if bool(selector.get("continued_development_recommended")):
        _state(
            "PENDING_COMBINED_QG2_CONTEXT_SELECTOR_IMPLEMENTATION",
            selector_report=str(SELECTOR_REPORT),
            selector_report_sha256=_sha256(SELECTOR_REPORT),
            calibration_started=False,
            deployment_authorized=False,
            fallback_action="Q0",
        )
        return 0

    if not TRAINING_REPORT.is_file():
        _state("NOT_STARTED_TRAINING_REPORT_MISSING")
        return 2
    training = _load(TRAINING_REPORT)
    oracle_path = _resolve(training.get("oracle_summary") or "")
    if not _valid_training(training, oracle_path, selector):
        _state("NOT_STARTED_TRAINING_ORACLE_BINDING_FAILED")
        return 3
    oracle = _load(oracle_path)
    state_index = _resolve(oracle.get("source_state_index") or "")
    if (
        not state_index.is_file()
        or str(oracle.get("source_state_index_sha256") or "")
        != _sha256(state_index)
    ):
        _state("NOT_STARTED_STATE_INDEX_BINDING_FAILED")
        return 3
    if any(path.exists() for path in (MANIFEST, OUTPUT_DIR, RISK_AUDIT)):
        _state("REFUSED_EXISTING_TRAINING_ONLY_V2_CALIBRATION_OUTPUT")
        return 3

    _state("BUILDING_TRAINING_ONLY_V2_SUPPLEMENTAL_MANIFEST")
    built = subprocess.run(
        [
            sys.executable,
            str(BUILD_MANIFEST),
            "--training-report", str(TRAINING_REPORT),
            "--oracle-summary", str(oracle_path),
            "--state-index", str(state_index),
            "--output", str(MANIFEST),
            "--minimum-calibration-contexts", "52",
            "--minimum-calibration-contexts-per-scale", "20",
            "--minimum-heldout-contexts-per-scale", "10",
        ],
        cwd=ROOT,
        check=False,
    )
    if built.returncode != 0 or not MANIFEST.is_file():
        _state(
            "TRAINING_ONLY_V2_SUPPLEMENTAL_MANIFEST_INSUFFICIENT_OR_FAILED",
            returncode=int(built.returncode),
        )
        return int(built.returncode or 3)
    manifest = _load(MANIFEST)
    if not bool(manifest.get("sufficient")):
        _state("TRAINING_ONLY_V2_SUPPLEMENTAL_MANIFEST_INSUFFICIENT")
        return 2
    engines = sorted({
        str(row.get("source_engine_hash") or "")
        for row in manifest.get("rows") or ()
        if row.get("source_engine_hash")
    })
    policies = sorted({
        str(row.get("source_exact_action_policy_hash") or "")
        for row in manifest.get("rows") or ()
        if row.get("source_exact_action_policy_hash")
    })

    _state(
        "RUNNING_TRAINING_ONLY_V2_FRESH_PROCESS_CALIBRATION",
        supplemental_context_count=len(manifest.get("rows") or ()),
        supplemental_manifest=str(MANIFEST),
    )
    command = [
        sys.executable,
        str(RUN_CALIBRATION),
        "--training-report", str(TRAINING_REPORT),
        "--oracle-summary", str(oracle_path),
        "--supplemental-manifest", str(MANIFEST),
        "--output-dir", str(OUTPUT_DIR),
        "--output", str(OUTPUT),
        "--repeats", "3",
        "--scale30-wall-sec", "180",
        "--scale50-wall-sec", "300",
        "--memory-limit-gb", "10.867",
    ]
    for digest in engines:
        command.extend(("--allowed-engine-hash", digest))
    for digest in policies:
        command.extend(("--allowed-exact-action-policy-hash", digest))
    calibrated = subprocess.run(command, cwd=ROOT, check=False)
    if not OUTPUT.is_file():
        _state(
            "TRAINING_ONLY_V2_CALIBRATION_EXECUTION_FAILED",
            returncode=int(calibrated.returncode),
        )
        return int(calibrated.returncode or 3)
    calibration = _load(OUTPUT)
    base_passed = bool(
        calibration.get("schema_version") == CALIBRATION_SCHEMA
        and calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
    )

    _state(
        "RUNNING_TRAINING_ONLY_V2_CALIBRATION_RISK_AUDIT",
        base_calibration_passed=base_passed,
        calibration_report=str(OUTPUT),
    )
    audited = subprocess.run(
        [
            sys.executable,
            str(RUN_RISK_AUDIT),
            "--calibration-report", str(OUTPUT),
            "--output", str(RISK_AUDIT),
        ],
        cwd=ROOT,
        check=False,
    )
    if not RISK_AUDIT.is_file():
        _state(
            "TRAINING_ONLY_V2_CALIBRATION_RISK_AUDIT_FAILED",
            returncode=int(audited.returncode),
        )
        return int(audited.returncode or 3)
    risk = _load(RISK_AUDIT)
    risk_passed = bool(
        risk.get("schema_version") == RISK_AUDIT_SCHEMA
        and risk.get("passed")
        and risk.get("deployment_authorized")
        and str(risk.get("calibration_report_sha256") or "")
        == _sha256(OUTPUT)
    )
    passed = bool(base_passed and risk_passed)
    _state(
        (
            "CALIBRATION_AND_RISK_AUDIT_PASSED_PENDING_E2E"
            if passed
            else "TRAINING_ONLY_V2_CALIBRATION_OR_RISK_GATE_FAILED"
        ),
        calibration_report=str(OUTPUT),
        calibration_report_sha256=_sha256(OUTPUT),
        risk_audit=str(RISK_AUDIT),
        risk_audit_sha256=_sha256(RISK_AUDIT),
        base_calibration_passed=base_passed,
        risk_audit_passed=risk_passed,
        deployment_authorized=False,
        fallback_action="Q0",
        calibration_returncode=int(calibrated.returncode),
        risk_audit_returncode=int(audited.returncode),
    )
    return 0 if passed else 2


def _valid_selector(selector: dict, state: dict) -> bool:
    return bool(
        selector.get("schema_version") == SELECTOR_SCHEMA
        and not bool(selector.get("deployable"))
        and not bool(selector.get("starts_solver_process"))
        and not bool(selector.get("changes_qg2"))
        and str(selector.get("fallback_action") or "") == "Q0"
        and str(selector.get("all_arms_rejected_action") or "") == "Q0"
        and str(state.get("selector_report_sha256") or "")
        == _sha256(SELECTOR_REPORT)
        and not bool(state.get("deployment_authorized"))
    )


def _valid_training(training: dict, oracle_path: Path, selector: dict) -> bool:
    if not oracle_path.is_file():
        return False
    oracle = _load(oracle_path)
    return bool(
        training.get("schema_version") == TRAINING_SCHEMA
        and bool(training.get("oracle_gate_passed"))
        and not bool(training.get("deployable"))
        and str(training.get("oracle_summary_sha256") or "")
        == _sha256(oracle_path)
        and oracle.get("schema_version") == ORACLE_SCHEMA
        and bool((oracle.get("oracle_gate") or {}).get("passed"))
        and not bool(oracle.get("deployable"))
        and str(selector.get("training_report_sha256") or "")
        == _sha256(TRAINING_REPORT)
        and str(selector.get("oracle_summary_sha256") or "")
        == _sha256(oracle_path)
    )


def _matching_selector_controller_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_context_arm_selector_after_training.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_training_only_v2_calibration_controller_freeze.v1"
    ):
        raise SystemExit("training-only-v2 calibration freeze schema mismatch")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("deployable"))
        or str(payload.get("fallback_action") or "") != "Q0"
        or not bool(payload.get("selector_precedes_calibration"))
    ):
        raise SystemExit("training-only-v2 calibration safety mismatch")
    if str(payload.get("context_selector_freeze_sha256") or "") != _sha256(
        SELECTOR_FREEZE
    ):
        raise SystemExit("training-only-v2 context-selector freeze drift")
    if str(payload.get("calibration_risk_freeze_sha256") or "") != _sha256(
        RISK_FREEZE
    ):
        raise SystemExit("training-only-v2 calibration-risk freeze drift")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(
                f"training-only-v2 calibration frozen drift: {path}"
            )


def _state(status: str, **extra) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_calibration_controller_state.v1"
        ),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": status,
        **extra,
    })


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
