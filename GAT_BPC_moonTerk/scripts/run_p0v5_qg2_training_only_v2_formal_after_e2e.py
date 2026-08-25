#!/usr/bin/env python3
"""Run formal scale5/10/20/30/50 full20 after training-only-v2 E2E.

The formal experiment logic and acceptance analyzer are reused unchanged.  A
separate wrapper binds the training-only-v2 E2E, calibration, risk audit, and
manifest hashes to unique formal outputs.  Passing permits candidate freezing
only; it never changes the production default.
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

import run_p0v5_qg2_action_surface_v2_formal_after_e2e as base  # noqa: E402


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_training_only_v2_formal_controller_freeze.json"
E2E_FREEZE = RUN_ROOT / "qg2_training_only_v2_e2e_controller_freeze.json"
E2E_STATE = RUN_ROOT / "qg2_training_only_v2_e2e_controller_state.json"
E2E_RESULT = RUN_ROOT / "e2e_training_only_v2_development_acceptance.json"
RISK_AUDIT = RUN_ROOT / "qg2_training_only_v2_calibration_risk_audit.json"
OUTPUT_ROOT = RUN_ROOT / "formal_full20_qg2_training_only_v2"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "formal_full20_acceptance_qg2_training_only_v2.json"
STATE = RUN_ROOT / "qg2_training_only_v2_formal_controller_state.json"
RISK_SCHEMA = "lunar_ice_bpc.p0v5_qg2_calibration_risk_audit.v2"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_TRAINING_ONLY_V2_DEVELOPMENT_E2E", wait_for_pid=args.wait_for_pid)
    while _matching_e2e_controller_alive(args.wait_for_pid):
        time.sleep(poll)

    if not E2E_STATE.is_file() or not E2E_RESULT.is_file() or not RISK_AUDIT.is_file():
        _state("NOT_STARTED_DEVELOPMENT_E2E_EVIDENCE_MISSING")
        return 2
    e2e_state = _load(E2E_STATE)
    e2e = _load(E2E_RESULT)
    if not _valid_e2e_result(e2e, e2e_state):
        _state("NOT_STARTED_DEVELOPMENT_E2E_EVIDENCE_INVALID")
        return 2
    calibration_path = _resolve(e2e_state.get("calibration_report") or "")
    if (
        not calibration_path.is_file()
        or _sha256(calibration_path)
        != str(e2e_state.get("calibration_report_sha256") or "")
    ):
        raise SystemExit("training-only-v2 formal calibration binding mismatch")
    calibration = _load(calibration_path)
    risk = _load(RISK_AUDIT)
    if not bool(
        calibration.get("schema_version") == base.CALIBRATION_SCHEMA
        and calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
        and risk.get("schema_version") == RISK_SCHEMA
        and risk.get("passed")
        and risk.get("deployment_authorized")
        and str(risk.get("calibration_report_sha256") or "")
        == _sha256(calibration_path)
        and str(e2e_state.get("risk_audit_sha256") or "")
        == _sha256(RISK_AUDIT)
    ):
        _state("NOT_STARTED_CALIBRATION_OR_RISK_NOT_AUTHORIZED")
        return 2
    manifest = base._validated_manifest(calibration, e2e_state)
    if OUTPUT_ROOT.exists() or RESULT.exists():
        raise SystemExit("training-only-v2 formal refuses overwrite or resume")

    _state(
        "RUNNING_FORMAL_EXACT_CONTROL",
        calibration_report=str(calibration_path),
        risk_audit=str(RISK_AUDIT),
    )
    control_code = base._run_acceptance(output=CONTROL_ROOT, manifest=None)
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=control_code)
        return control_code
    _state("RUNNING_FORMAL_QG2_GUIDED", manifest=str(manifest))
    guided_code = base._run_acceptance(output=GUIDED_ROOT, manifest=manifest)
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
            "--mode", "formal",
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
        "FORMAL_FULL20_PASSED" if passed else "FORMAL_FULL20_GATE_FAILED",
        e2e_state=str(E2E_STATE),
        e2e_state_sha256=_sha256(E2E_STATE),
        calibration_report=str(calibration_path),
        calibration_report_sha256=_sha256(calibration_path),
        risk_audit=str(RISK_AUDIT),
        risk_audit_sha256=_sha256(RISK_AUDIT),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        candidate_freeze_permitted=passed,
        production_switch_performed=False,
        fallback_action="Q0",
    )
    return 0 if passed else 2


def _valid_e2e_result(payload: dict, state: dict) -> bool:
    if str(state.get("status") or "") != "E2E_PASSED_PENDING_FORMAL_FULL20":
        return False
    if not bool(
        payload.get("schema_version")
        == "lunar_ice_bpc.p0v5_qg2_paired_acceptance.v1"
        and payload.get("mode") == "development"
        and payload.get("passed")
        and int(payload.get("violation_count") or 0) == 0
        and {int(value) for value in (payload.get("by_scale") or {})}
        == {30, 50}
        and _sha256(E2E_RESULT) == str(state.get("result_sha256") or "")
        and not bool(state.get("deployment_authorized"))
        and str(state.get("fallback_action") or "") == "Q0"
    ):
        return False
    for prefix in ("control", "guided"):
        root = _resolve(payload.get(f"{prefix}_root") or "")
        if (
            not root.is_dir()
            or base._acceptance_artifact_hash(root)
            != str(payload.get(f"{prefix}_root_hash") or "")
        ):
            return False
    return True


def _matching_e2e_controller_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_training_only_v2_e2e_after_calibration.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_training_only_v2_formal_controller_freeze.v1"
    ):
        raise SystemExit("training-only-v2 formal freeze schema mismatch")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("production_default"))
        or str(payload.get("fallback_action") or "") != "Q0"
        or not bool(payload.get("risk_audit_required"))
    ):
        raise SystemExit("training-only-v2 formal safety mismatch")
    if str(payload.get("training_only_v2_e2e_freeze_sha256") or "") != _sha256(
        E2E_FREEZE
    ):
        raise SystemExit("training-only-v2 formal E2E freeze drift")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"training-only-v2 formal frozen drift: {path}")


def _state(status: str, **extra) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_formal_controller_state.v1"
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
