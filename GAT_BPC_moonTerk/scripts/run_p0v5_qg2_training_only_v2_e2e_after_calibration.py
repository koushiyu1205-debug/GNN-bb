#!/usr/bin/env python3
"""Run paired development E2E after training-only-v2 calibration passes.

The heavy acceptance and analysis functions are reused from the frozen
action-surface-v2 E2E implementation.  This wrapper adds the training-only-v2
calibration/risk bindings and unique output paths; it remains inert when the
context selector requires a different combined action surface.
"""

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


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import run_p0v5_qg2_action_surface_v2_e2e_after_calibration as base  # noqa: E402


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_training_only_v2_e2e_controller_freeze.json"
CALIBRATION_FREEZE = (
    RUN_ROOT / "qg2_training_only_v2_calibration_controller_freeze.json"
)
CALIBRATION_STATE = (
    RUN_ROOT / "qg2_training_only_v2_calibration_controller_state.json"
)
TRAINING_REPORT = (
    RUN_ROOT
    / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
)
CALIBRATION_REPORT = (
    RUN_ROOT
    / "calibration_qg2_action_surface_v2_training_only_v2/calibration_report.json"
)
RISK_AUDIT = RUN_ROOT / "qg2_training_only_v2_calibration_risk_audit.json"
SELECTOR_REPORT = (
    RUN_ROOT / "context_arm_selector_feasibility_v1/selector_report.json"
)
OUTPUT_ROOT = RUN_ROOT / "e2e_qg2_action_surface_v2_training_only_v2"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "e2e_training_only_v2_development_acceptance.json"
STATE = RUN_ROOT / "qg2_training_only_v2_e2e_controller_state.json"

TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
RISK_SCHEMA = "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"
SELECTOR_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_TRAINING_ONLY_V2_CALIBRATION", wait_for_pid=args.wait_for_pid)
    while _matching_calibration_controller_alive(args.wait_for_pid):
        time.sleep(poll)

    if not all(path.is_file() for path in (
        CALIBRATION_STATE,
        TRAINING_REPORT,
        CALIBRATION_REPORT,
        RISK_AUDIT,
        SELECTOR_REPORT,
    )):
        _state("NOT_STARTED_CALIBRATION_ARTIFACT_MISSING")
        return 2
    state = _load(CALIBRATION_STATE)
    training = _load(TRAINING_REPORT)
    calibration = _load(CALIBRATION_REPORT)
    risk = _load(RISK_AUDIT)
    selector = _load(SELECTOR_REPORT)
    if not _authorized(state, training, calibration, risk, selector):
        _state(
            "NOT_STARTED_CALIBRATION_OR_RISK_GATE_FAILED",
            calibration_status=state.get("status"),
        )
        return 2
    manifest = base._validated_manifest(calibration)
    if OUTPUT_ROOT.exists() or RESULT.exists():
        raise SystemExit("training-only-v2 E2E refuses overwrite or resume")
    instances = base._heldout_instances(training)

    _state(
        "RUNNING_EXACT_CONTROL",
        instances=[str(path) for path in instances],
        training_report=str(TRAINING_REPORT),
        calibration_report=str(CALIBRATION_REPORT),
        risk_audit=str(RISK_AUDIT),
    )
    control_code = base._run_acceptance(
        output=CONTROL_ROOT,
        instances=instances,
        manifest=None,
    )
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=control_code)
        return control_code
    _state("RUNNING_QG2_GUIDED", manifest=str(manifest))
    guided_code = base._run_acceptance(
        output=GUIDED_ROOT,
        instances=instances,
        manifest=manifest,
    )
    if guided_code not in {0, 1}:
        _state("GUIDED_EXECUTION_ERROR", returncode=guided_code)
        return guided_code

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
        _state("ANALYZER_EXECUTION_ERROR", returncode=analyzed.returncode)
        return int(analyzed.returncode or 3)
    result = _load(RESULT)
    passed = bool(result.get("passed"))
    _state(
        "E2E_PASSED_PENDING_FORMAL_FULL20" if passed else "E2E_GATE_FAILED",
        calibration_report=str(CALIBRATION_REPORT),
        calibration_report_sha256=_sha256(CALIBRATION_REPORT),
        risk_audit=str(RISK_AUDIT),
        risk_audit_sha256=_sha256(RISK_AUDIT),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        deployment_authorized=False,
        fallback_action="Q0",
    )
    return 0 if passed else 2


def _authorized(
    state: dict,
    training: dict,
    calibration: dict,
    risk: dict,
    selector: dict,
) -> bool:
    return bool(
        str(state.get("status") or "")
        == "CALIBRATION_AND_RISK_AUDIT_PASSED_PENDING_E2E"
        and str(state.get("calibration_report_sha256") or "")
        == _sha256(CALIBRATION_REPORT)
        and str(state.get("risk_audit_sha256") or "") == _sha256(RISK_AUDIT)
        and not bool(state.get("deployment_authorized"))
        and training.get("schema_version") == TRAINING_SCHEMA
        and bool(training.get("oracle_gate_passed"))
        and not bool(training.get("deployable"))
        and base._authorized_reports(
            training,
            calibration,
            training_path=TRAINING_REPORT,
        )
        and calibration.get("schema_version") == CALIBRATION_SCHEMA
        and calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
        and risk.get("schema_version") == RISK_SCHEMA
        and risk.get("passed")
        and risk.get("deployment_authorized")
        and str(risk.get("calibration_report_sha256") or "")
        == _sha256(CALIBRATION_REPORT)
        and selector.get("schema_version") == SELECTOR_SCHEMA
        and not bool(selector.get("continued_development_recommended"))
        and str(selector.get("fallback_action") or "") == "Q0"
        and not bool(selector.get("deployable"))
    )


def _matching_calibration_controller_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return (
        "run_p0v5_qg2_training_only_v2_calibration_after_selector.py"
        in command
    )


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_training_only_v2_e2e_controller_freeze.v1"
    ):
        raise SystemExit("training-only-v2 E2E freeze schema mismatch")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("deployable"))
        or str(payload.get("fallback_action") or "") != "Q0"
        or not bool(payload.get("risk_audit_required"))
    ):
        raise SystemExit("training-only-v2 E2E safety mismatch")
    if str(
        payload.get("training_only_v2_calibration_freeze_sha256") or ""
    ) != _sha256(CALIBRATION_FREEZE):
        raise SystemExit("training-only-v2 E2E calibration freeze drift")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"training-only-v2 E2E frozen drift: {path}")


def _state(status: str, **extra) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_e2e_controller_state.v1"
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
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
