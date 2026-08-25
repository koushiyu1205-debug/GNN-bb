#!/usr/bin/env python3
"""Train and calibrate QG2 only after the frozen oracle controller passes."""

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
FREEZE = RUN_ROOT / "qg2_clean_v1_post_oracle_controller_freeze.json"
ORACLE_STATE = RUN_ROOT / "qg2_clean_v1_oracle_controller_state.json"
ORACLE_SUMMARY = RUN_ROOT / "oracle_qg2_clean_v1_stage1.json"
TRAINING_DIR = RUN_ROOT / "training_qg2_clean_v1"
TRAINING_REPORT = TRAINING_DIR / "training_report.json"
CALIBRATION_DIR = RUN_ROOT / "calibration_qg2_clean_v1"
CALIBRATION_REPORT = CALIBRATION_DIR / "calibration_report.json"
STATE = RUN_ROOT / "qg2_clean_v1_post_oracle_controller_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
SOURCE_ENGINE_HASH = "0389484e5f5623f2"
EXACT_ACTION_POLICY_HASHES = (
    "9dcedb7b74c0a9c20a3a64484067b87300b9267e8bd450fcfff74d2a8c7406ca",
    "b2f9eab6bd01d12a0f4319342550733ddb0510e559d5e6a6abc119765d2203e2",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_ORACLE_GATE", wait_for_pid=args.wait_for_pid)
    while _matching_oracle_controller_alive(args.wait_for_pid):
        print(json.dumps({
            "status": "waiting_for_oracle_gate",
            "pid": args.wait_for_pid,
        }, sort_keys=True), flush=True)
        time.sleep(poll)
    oracle_state = _load(ORACLE_STATE)
    if str(oracle_state.get("status") or "") != "ORACLE_STAGE1_PASSED":
        _state(
            "NOT_STARTED_ORACLE_GATE_FAILED",
            oracle_status=oracle_state.get("status"),
        )
        return 2
    oracle = _load(ORACLE_SUMMARY)
    if (
        oracle.get("schema_version")
        != "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
        or not bool((oracle.get("oracle_gate") or {}).get("passed"))
        or not bool(oracle.get("training_permitted"))
    ):
        _state("NOT_STARTED_ORACLE_SUMMARY_NOT_AUTHORIZED")
        return 2
    if TRAINING_DIR.exists() or CALIBRATION_DIR.exists():
        raise SystemExit(
            "post-oracle controller refuses implicit resume or overwrite"
        )

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
    if training.returncode != 0:
        _state("TRAINING_FAILED", returncode=training.returncode)
        return training.returncode

    _state("RUNNING_FRESH_PROCESS_CALIBRATION")
    calibration_command = [
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
        calibration_command.extend((
            "--allowed-exact-action-policy-hash", digest,
        ))
    calibration = subprocess.run(
        calibration_command,
        cwd=ROOT,
        env=_python_env(),
        check=False,
    )
    if calibration.returncode not in {0, 2}:
        _state(
            "CALIBRATION_EXECUTION_ERROR",
            returncode=calibration.returncode,
        )
        return calibration.returncode
    report = _load(CALIBRATION_REPORT)
    passed = bool(
        report.get("gate_pass") and report.get("deployment_authorized")
    )
    _state(
        "CALIBRATION_PASSED" if passed else "CALIBRATION_GATE_FAILED",
        returncode=calibration.returncode,
        deployment_authorized=passed,
        calibration_report=str(CALIBRATION_REPORT),
    )
    return 0 if passed else 2


def _matching_oracle_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "run_p0v5_qg2_oracle_after_collection.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") not in {
        "lunar_ice_bpc.p0v5_qg2_post_oracle_controller_freeze.v1",
        "lunar_ice_bpc.p0v5_qg2_post_oracle_controller_freeze.v2",
    }:
        raise SystemExit("post-oracle controller freeze schema mismatch")
    allowed = tuple(sorted(
        str(value)
        for value in payload.get(
            "allowed_exact_action_policy_hashes"
        ) or ()
    ))
    if allowed and allowed != tuple(sorted(EXACT_ACTION_POLICY_HASHES)):
        raise SystemExit(
            "post-oracle scale-aware exact-action allowlist mismatch"
        )
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(raw_path)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"post-oracle frozen file drift: {path}")


def _python_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    env.pop("LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST", None)
    env.pop("LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE", None)
    return env


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_post_oracle_controller_state.v1",
        "status": status,
        **extra,
    }
    temporary = STATE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
