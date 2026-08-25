#!/usr/bin/env python3
"""Train/calibrate action-surface-v2 QG2 only after Oracle v5 passes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
FREEZE = RUN_ROOT / "qg2_action_surface_v2_post_oracle_freeze.json"
ORACLE_EXECUTION_FREEZE = (
    RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
)
ORACLE_SUMMARY = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
TRAINING_DIR = RUN_ROOT / "training_qg2_action_surface_v2"
TRAINING_REPORT = TRAINING_DIR / "training_report.json"
CALIBRATION_DIR = RUN_ROOT / "calibration_qg2_action_surface_v2"
CALIBRATION_REPORT = CALIBRATION_DIR / "calibration_report.json"
STATE = RUN_ROOT / "qg2_action_surface_v2_post_oracle_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
SUPERVISION_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_action_reachable_supervision.v2"
)
ACTION_SURFACE = "same_terminal_class_and_reduced_cost_bucket.v1"
SOURCE_ENGINE_HASH = "0389484e5f5623f2"
EXACT_ACTION_POLICY_HASHES = (
    "9dcedb7b74c0a9c20a3a64484067b87300b9267e8bd450fcfff74d2a8c7406ca",
    "b2f9eab6bd01d12a0f4319342550733ddb0510e559d5e6a6abc119765d2203e2",
)
GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_MANIFEST",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST",
    "LUNAR_ICE_GAT_GUIDANCE_MODE",
    "LUNAR_ICE_GAT_TRAINING_ROWS_DIR",
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_GLOBAL_STORAGE_CAP",
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_PER_SCALE_STORAGE_CAP",
    "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR",
    "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    freeze = _validate_freeze()
    expected_oracle_freeze_sha = str(
        freeze["oracle_execution_freeze_sha256"]
    )
    _state("WAITING_FOR_ACTION_SURFACE_V2_ORACLE", wait_for_pid=args.wait_for_pid)
    while _matching_oracle_alive(args.wait_for_pid):
        print(json.dumps({
            "status": "waiting_for_action_surface_v2_oracle",
            "pid": int(args.wait_for_pid),
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    if not ORACLE_SUMMARY.is_file():
        _state("NOT_STARTED_ORACLE_SUMMARY_MISSING")
        return 2
    oracle = _load(ORACLE_SUMMARY)
    authorized = bool(
        oracle.get("schema_version") == ORACLE_SCHEMA
        and oracle.get("supervision_schema_version") == SUPERVISION_SCHEMA
        and oracle.get("queue_action_surface") == ACTION_SURFACE
        and str(oracle.get("execution_freeze_sha256") or "")
        == expected_oracle_freeze_sha
        and bool((oracle.get("oracle_gate") or {}).get("passed"))
        and bool(oracle.get("training_permitted"))
        and str(oracle.get("status") or "") == "PASSED"
    )
    if not authorized:
        _state(
            "NOT_STARTED_ORACLE_GATE_FAILED",
            oracle_status=oracle.get("status"),
            oracle_gate=oracle.get("oracle_gate"),
        )
        return 2
    if TRAINING_DIR.exists() or CALIBRATION_DIR.exists():
        _state("REFUSED_EXISTING_POST_ORACLE_OUTPUT")
        return 3

    _state("RUNNING_MODEL_COMPARISON_TRAINING")
    training = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/train_p0v5_qg2_model_comparison.py"),
            "--oracle-summary", str(ORACLE_SUMMARY),
            "--output-dir", str(TRAINING_DIR),
        ],
        cwd=ROOT,
        env=_python_env(),
        check=False,
    )
    if training.returncode != 0 or not TRAINING_REPORT.is_file():
        _state("TRAINING_FAILED", returncode=training.returncode)
        return int(training.returncode or 3)
    training_report = _load(TRAINING_REPORT)
    if (
        training_report.get("schema_version") != TRAINING_SCHEMA
        or training_report.get("supervision_schema_version")
        != SUPERVISION_SCHEMA
        or training_report.get("queue_action_surface") != ACTION_SURFACE
        or not bool(training_report.get("oracle_gate_passed"))
    ):
        _state("TRAINING_REPORT_CONTRACT_FAILED")
        return 3

    _state("RUNNING_FRESH_PROCESS_CALIBRATION")
    command = [
        sys.executable,
        str(ROOT / "scripts/calibrate_p0v5_qg2_models.py"),
        "--training-report", str(TRAINING_REPORT),
        "--oracle-summary", str(ORACLE_SUMMARY),
        "--output-dir", str(CALIBRATION_DIR),
        "--output", str(CALIBRATION_REPORT),
        "--repeats", "3",
        "--scale30-wall-sec", "180",
        "--scale50-wall-sec", "300",
        "--memory-limit-gb", "10.867",
        "--allowed-engine-hash", SOURCE_ENGINE_HASH,
    ]
    for digest in EXACT_ACTION_POLICY_HASHES:
        command.extend(("--allowed-exact-action-policy-hash", digest))
    calibration = subprocess.run(
        command,
        cwd=ROOT,
        env=_python_env(),
        check=False,
    )
    if calibration.returncode not in {0, 2} or not CALIBRATION_REPORT.is_file():
        _state(
            "CALIBRATION_EXECUTION_ERROR",
            returncode=calibration.returncode,
        )
        return int(calibration.returncode or 3)
    report = _load(CALIBRATION_REPORT)
    passed = bool(
        report.get("schema_version") == CALIBRATION_SCHEMA
        and report.get("gate_pass")
        and report.get("deployment_authorized")
    )
    _state(
        "CALIBRATION_PASSED" if passed else "CALIBRATION_GATE_FAILED",
        returncode=calibration.returncode,
        deployment_authorized=passed,
        calibration_report=str(CALIBRATION_REPORT),
    )
    return 0 if passed else 2


def _matching_oracle_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return bool(
        "run_p0v5_qg2_bounded_oracle.py" in command
        and "oracle_qg2_action_surface_v2_stage1" in command
        and "qg2_action_surface_v2_oracle_execution_freeze.json" in command
    )


def _validate_freeze() -> dict:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_post_oracle_controller_freeze.v3"
    ):
        raise SystemExit("action-surface post-oracle freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        raise SystemExit("action-surface post-oracle freeze safety mismatch")
    if str(payload.get("oracle_execution_freeze_sha256") or "") != (
        _sha256(ORACLE_EXECUTION_FREEZE)
    ):
        raise SystemExit("action-surface Oracle execution freeze drift")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(raw_path)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"action-surface post-oracle frozen drift: {path}")
    return payload


def _python_env() -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    return env


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_post_oracle_controller_state.v2"
        ),
        "status": str(status),
        **extra,
    }
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
