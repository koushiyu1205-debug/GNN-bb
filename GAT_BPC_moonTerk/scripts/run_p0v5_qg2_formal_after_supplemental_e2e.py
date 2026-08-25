#!/usr/bin/env python3
"""Run formal QG2 full20 after the supplemental-aware development E2E."""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "scripts/run_p0v5_qg2_action_surface_v2_formal_after_e2e.py"
SPEC = importlib.util.spec_from_file_location("qg2_formal_base", BASE_PATH)
assert SPEC is not None and SPEC.loader is not None
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)


RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_supplemental_formal_controller_freeze.json"
E2E_STATE = RUN_ROOT / "qg2_supplemental_e2e_controller_state.json"
E2E_RESULT = RUN_ROOT / "e2e_development_acceptance_qg2_action_surface_v2.json"
OUTPUT_ROOT = RUN_ROOT / "formal_full20_qg2_action_surface_v2"
CONTROL_ROOT = OUTPUT_ROOT / "control"
GUIDED_ROOT = OUTPUT_ROOT / "guided"
RESULT = RUN_ROOT / "formal_full20_acceptance_qg2_action_surface_v2.json"
STATE = RUN_ROOT / "qg2_supplemental_formal_controller_state.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_SUPPLEMENTAL_DEVELOPMENT_E2E", wait_for_pid=args.wait_for_pid)
    while _matching_supplemental_e2e_alive(args.wait_for_pid):
        time.sleep(poll)
    if not E2E_STATE.is_file() or not E2E_RESULT.is_file():
        _state("NOT_STARTED_SUPPLEMENTAL_E2E_EVIDENCE_MISSING")
        return 0
    e2e_state = _load(E2E_STATE)
    e2e = _load(E2E_RESULT)
    original_result = base.E2E_RESULT
    base.E2E_RESULT = E2E_RESULT
    try:
        valid_e2e = base._valid_e2e_result(e2e, e2e_state)
    finally:
        base.E2E_RESULT = original_result
    if not valid_e2e:
        _state("NOT_STARTED_SUPPLEMENTAL_E2E_EVIDENCE_INVALID")
        return 0
    calibration_path = _resolve(e2e_state.get("calibration_report") or "")
    if (
        not calibration_path.is_file()
        or _sha256(calibration_path)
        != str(e2e_state.get("calibration_report_sha256") or "")
    ):
        raise SystemExit("supplemental formal calibration binding mismatch")
    calibration = _load(calibration_path)
    if not bool(
        calibration.get("schema_version") == base.CALIBRATION_SCHEMA
        and calibration.get("gate_pass")
        and calibration.get("deployment_authorized")
    ):
        _state("NOT_STARTED_SUPPLEMENTAL_CALIBRATION_NOT_AUTHORIZED")
        return 2
    manifest = base._validated_manifest(calibration, e2e_state)
    if OUTPUT_ROOT.exists() or RESULT.exists():
        if RESULT.is_file() and bool(_load(RESULT).get("passed")):
            _state(
                "NOT_NEEDED_FORMAL_FULL20_ALREADY_PASSED",
                result=str(RESULT),
                result_sha256=_sha256(RESULT),
            )
            return 0
        raise SystemExit("supplemental formal refuses partial/failed output")
    _state(
        "RUNNING_SUPPLEMENTAL_FORMAL_EXACT_CONTROL",
        calibration_report=str(calibration_path),
    )
    control_code = base._run_acceptance(output=CONTROL_ROOT, manifest=None)
    if control_code not in {0, 1}:
        _state("CONTROL_EXECUTION_ERROR", returncode=control_code)
        return control_code
    _state("RUNNING_SUPPLEMENTAL_FORMAL_QG2_GUIDED")
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
        authority="supplemental_calibration_hash_bound",
        e2e_state=str(E2E_STATE),
        e2e_state_sha256=_sha256(E2E_STATE),
        calibration_report=str(calibration_path),
        calibration_report_sha256=_sha256(calibration_path),
        manifest=str(manifest),
        manifest_sha256=_sha256(manifest),
        result=str(RESULT),
        result_sha256=_sha256(RESULT),
        violations=result.get("violations"),
        candidate_freeze_permitted=passed,
        production_switch_performed=False,
    )
    return 0 if passed else 2


def _matching_supplemental_e2e_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_e2e_after_supplemental_calibration.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_supplemental_formal_controller_freeze.v1"
    ):
        raise SystemExit("supplemental formal freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("production_default")
    ):
        raise SystemExit("supplemental formal freeze safety mismatch")
    if str(payload.get("controller_sha256") or "") != _sha256(
        Path(__file__).resolve()
    ):
        raise SystemExit("supplemental formal controller drift")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"supplemental formal frozen drift: {path}")


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_supplemental_formal_controller_state.v1"
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
