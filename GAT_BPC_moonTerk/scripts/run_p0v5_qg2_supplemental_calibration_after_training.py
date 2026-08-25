#!/usr/bin/env python3
"""Continue QG2 with leakage-safe supplemental calibration after training."""

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
FREEZE = RUN_ROOT / "qg2_supplemental_calibration_controller_freeze.json"
STRICT_TRAINING = RUN_ROOT / "training_qg2_action_surface_v2/training_report.json"
RELAXED_TRAINING = (
    RUN_ROOT / "training_qg2_action_surface_v2_relaxed/training_report.json"
)
STRICT_CALIBRATION = (
    RUN_ROOT / "calibration_qg2_action_surface_v2/calibration_report.json"
)
RELAXED_CALIBRATION = (
    RUN_ROOT / "calibration_qg2_action_surface_v2_relaxed/calibration_report.json"
)
MANIFEST = RUN_ROOT / "qg2_supplemental_calibration_manifest.json"
OUTPUT_DIR = RUN_ROOT / "calibration_qg2_action_surface_v2_supplemental"
OUTPUT = OUTPUT_DIR / "calibration_report.json"
STATE = RUN_ROOT / "qg2_supplemental_calibration_controller_state.json"
BUILD_MANIFEST = (
    ROOT / "scripts/build_p0v5_qg2_supplemental_calibration_manifest.py"
)
RUN_CALIBRATION = ROOT / "scripts/run_p0v5_qg2_supplemental_calibration.py"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_MODEL_TRAINING", wait_for_pid=args.wait_for_pid)
    while _matching_training_controller_alive(args.wait_for_pid):
        time.sleep(poll)

    passed = _passed_calibration()
    if passed is not None:
        _state(
            "SUPPLEMENT_NOT_NEEDED_STANDARD_CALIBRATION_PASSED",
            calibration_report=str(passed),
        )
        return 0
    training_path = _training_authority()
    if training_path is None:
        _state("NOT_STARTED_TRAINING_REPORT_MISSING_OR_INVALID")
        return 2
    training = _load(training_path)
    oracle_path = _resolve(training.get("oracle_summary") or "")
    if not oracle_path.is_file():
        _state("NOT_STARTED_TRAINING_ORACLE_MISSING")
        return 3
    oracle = _load(oracle_path)
    if (
        oracle.get("schema_version") != ORACLE_SCHEMA
        or str(training.get("oracle_summary_sha256") or "")
        != _sha256(oracle_path)
        or not bool((oracle.get("oracle_gate") or {}).get("passed"))
    ):
        _state("NOT_STARTED_TRAINING_ORACLE_BINDING_FAILED")
        return 3
    state_index = _resolve(oracle.get("source_state_index") or "")
    if (
        not state_index.is_file()
        or str(oracle.get("source_state_index_sha256") or "")
        != _sha256(state_index)
    ):
        _state("NOT_STARTED_STATE_INDEX_BINDING_FAILED")
        return 3

    _state("BUILDING_SUPPLEMENTAL_CALIBRATION_MANIFEST")
    built = subprocess.run(
        [
            sys.executable,
            str(BUILD_MANIFEST),
            "--training-report", str(training_path),
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
            "SUPPLEMENTAL_MANIFEST_INSUFFICIENT_OR_FAILED",
            returncode=built.returncode,
        )
        return int(built.returncode or 3)
    manifest = _load(MANIFEST)
    if not bool(manifest.get("sufficient")):
        _state("SUPPLEMENTAL_MANIFEST_INSUFFICIENT")
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
        "RUNNING_SUPPLEMENTAL_FRESH_PROCESS_CALIBRATION",
        supplemental_manifest=str(MANIFEST),
        supplemental_context_count=len(manifest.get("rows") or ()),
    )
    command = [
        sys.executable,
        str(RUN_CALIBRATION),
        "--training-report", str(training_path),
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
            "SUPPLEMENTAL_CALIBRATION_EXECUTION_FAILED",
            returncode=calibrated.returncode,
        )
        return int(calibrated.returncode or 3)
    report = _load(OUTPUT)
    passed = bool(
        report.get("schema_version") == CALIBRATION_SCHEMA
        and report.get("gate_pass")
        and report.get("deployment_authorized")
    )
    _state(
        (
            "SUPPLEMENTAL_CALIBRATION_PASSED_PENDING_E2E"
            if passed
            else "SUPPLEMENTAL_CALIBRATION_GATE_FAILED"
        ),
        calibration_report=str(OUTPUT),
        calibration_report_sha256=_sha256(OUTPUT),
        deployment_authorized=passed,
        returncode=calibrated.returncode,
    )
    return 0 if passed else 2


def _training_authority() -> Path | None:
    for path in (STRICT_TRAINING, RELAXED_TRAINING):
        if not path.is_file():
            continue
        payload = _load(path)
        if (
            payload.get("schema_version") == TRAINING_SCHEMA
            and bool(payload.get("oracle_gate_passed"))
            and not bool(payload.get("deployable"))
        ):
            return path
    return None


def _passed_calibration() -> Path | None:
    for path in (STRICT_CALIBRATION, RELAXED_CALIBRATION):
        if not path.is_file():
            continue
        payload = _load(path)
        if (
            payload.get("schema_version") == CALIBRATION_SCHEMA
            and bool(payload.get("gate_pass"))
            and bool(payload.get("deployment_authorized"))
        ):
            return path
    return None


def _matching_training_controller_alive(pid: int) -> bool:
    try:
        command = Path(f"/proc/{int(pid)}/cmdline").read_bytes().replace(
            b"\0", b" "
        ).decode("utf-8", errors="replace")
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_relaxed_training_after_oracle.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_supplemental_calibration_controller_freeze.v1"
    ):
        raise SystemExit("supplemental calibration freeze schema mismatch")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("deployable"))
        or int(payload.get("training_rows_added", -1)) != 0
    ):
        raise SystemExit("supplemental calibration freeze safety mismatch")
    if str(payload.get("controller_sha256") or "") != _sha256(
        Path(__file__).resolve()
    ):
        raise SystemExit("supplemental calibration controller drift")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"supplemental calibration frozen drift: {path}")


def _state(status: str, **extra: Any) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_supplemental_calibration_controller_state.v1"
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
