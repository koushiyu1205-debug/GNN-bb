#!/usr/bin/env python3
"""Start exploratory QG2 training after a relaxed, exact-safe Oracle gate.

This controller is independent from the frozen strict-gate controller.  It
waits for the same Oracle, defers to the strict controller when the original
gate passes, and otherwise authorizes model fitting only through the relaxed
training sidecar.  Calibration and all later deployment gates remain intact.
"""

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
FREEZE = RUN_ROOT / "qg2_action_surface_v2_relaxed_training_freeze.json"
ORACLE_EXECUTION_FREEZE = (
    RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
)
ORACLE_SUMMARY = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
GATE_REPORT = RUN_ROOT / "qg2_action_surface_v2_relaxed_training_gate.json"
AUTHORIZED_ORACLE = (
    RUN_ROOT / "oracle_qg2_action_surface_v2_relaxed_training_view.json"
)
TRAINING_DIR = RUN_ROOT / "training_qg2_action_surface_v2_relaxed"
TRAINING_REPORT = TRAINING_DIR / "training_report.json"
CALIBRATION_DIR = RUN_ROOT / "calibration_qg2_action_surface_v2_relaxed"
CALIBRATION_REPORT = CALIBRATION_DIR / "calibration_report.json"
STATE = RUN_ROOT / "qg2_action_surface_v2_relaxed_post_oracle_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"

ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
GATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_relaxed_training_gate.v1"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
MINIMUM_STRICT_CALIBRATION_CONTEXTS = 52
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
    if not _oracle_contract_valid(oracle, expected_oracle_freeze_sha):
        _state("NOT_STARTED_ORACLE_CONTRACT_FAILED")
        return 3
    if bool((oracle.get("oracle_gate") or {}).get("passed")) and bool(
        oracle.get("training_permitted")
    ):
        _state("DEFERRED_TO_STRICT_GATE_CONTROLLER")
        return 0

    gate_run = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/evaluate_p0v5_qg2_relaxed_training_gate.py"),
            "--oracle-summary", str(ORACLE_SUMMARY),
            "--output", str(GATE_REPORT),
        ],
        cwd=ROOT,
        env=_python_env(),
        check=False,
    )
    if gate_run.returncode not in {0, 2} or not GATE_REPORT.is_file():
        _state("RELAXED_GATE_EXECUTION_ERROR", returncode=gate_run.returncode)
        return int(gate_run.returncode or 3)
    gate = _load(GATE_REPORT)
    authorized = bool(
        gate.get("schema_version") == GATE_SCHEMA
        and gate.get("supervision_schema_version") == SUPERVISION_SCHEMA
        and gate.get("queue_action_surface") == ACTION_SURFACE
        and str(gate.get("oracle_summary_sha256") or "")
        == _sha256(ORACLE_SUMMARY)
        and bool((gate.get("gate") or {}).get("passed"))
        and bool(gate.get("training_authorized"))
        and not bool(gate.get("deployment_authorized"))
    )
    if not authorized:
        _state("NOT_STARTED_RELAXED_TRAINING_GATE_FAILED", gate=gate.get("gate"))
        return 2
    if any(path.exists() for path in (
        AUTHORIZED_ORACLE, TRAINING_DIR, CALIBRATION_DIR
    )):
        _state("REFUSED_EXISTING_RELAXED_POST_ORACLE_OUTPUT")
        return 3

    authorized_oracle = dict(oracle)
    authorized_oracle["strict_oracle_gate"] = dict(
        oracle.get("oracle_gate") or {}
    )
    authorized_oracle["oracle_gate"] = dict(gate["gate"])
    authorized_oracle["training_permitted"] = True
    authorized_oracle["status"] = "PASSED"
    authorized_oracle["deployable"] = False
    authorized_oracle["relaxed_training_authority"] = {
        "authority": "exploratory_model_training_only",
        "gate_report": str(GATE_REPORT),
        "gate_report_sha256": _sha256(GATE_REPORT),
        "deployment_authorized": False,
        "paper_claim_authorized": False,
    }
    _write(AUTHORIZED_ORACLE, authorized_oracle)

    _state("RUNNING_RELAXED_MODEL_COMPARISON_TRAINING")
    training = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/run_p0v5_qg2_relaxed_training_entry.py"),
            "--oracle-summary", str(AUTHORIZED_ORACLE),
            "--output-dir", str(TRAINING_DIR),
        ],
        cwd=ROOT,
        env=_python_env(),
        check=False,
    )
    if training.returncode != 0 or not TRAINING_REPORT.is_file():
        _state("RELAXED_TRAINING_FAILED", returncode=training.returncode)
        return int(training.returncode or 3)
    report = _load(TRAINING_REPORT)
    if (
        report.get("schema_version") != TRAINING_SCHEMA
        or report.get("supervision_schema_version") != SUPERVISION_SCHEMA
        or report.get("queue_action_surface") != ACTION_SURFACE
        or not bool(report.get("oracle_gate_passed"))
    ):
        _state("RELAXED_TRAINING_REPORT_CONTRACT_FAILED")
        return 3

    calibration_context_count = int(
        report.get("calibration_context_count") or 0
    )
    if not _strict_calibration_sample_reachable(report):
        # The user-authorized relaxation applies only to fitting exploratory
        # models.  It does not weaken the Wilson-bound sample requirement used
        # by deployment calibration, and it must not launch Native replays that
        # are statistically incapable of passing that unchanged gate.
        _state(
            "TRAINING_COMPLETE_CALIBRATION_DEFERRED_SAMPLE_SIZE",
            training_report=str(TRAINING_REPORT),
            calibration_context_count=calibration_context_count,
            minimum_strict_calibration_contexts=(
                MINIMUM_STRICT_CALIBRATION_CONTEXTS
            ),
            deployment_authorized=False,
        )
        return 0

    _state("RUNNING_RELAXED_FRESH_PROCESS_CALIBRATION")
    command = [
        sys.executable,
        str(ROOT / "scripts/calibrate_p0v5_qg2_models.py"),
        "--training-report", str(TRAINING_REPORT),
        "--oracle-summary", str(AUTHORIZED_ORACLE),
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
            "RELAXED_CALIBRATION_EXECUTION_ERROR",
            returncode=calibration.returncode,
        )
        return int(calibration.returncode or 3)
    calibration_report = _load(CALIBRATION_REPORT)
    passed = bool(
        calibration_report.get("schema_version") == CALIBRATION_SCHEMA
        and calibration_report.get("gate_pass")
        and calibration_report.get("deployment_authorized")
    )
    _state(
        (
            "CALIBRATION_PASSED_PENDING_HELDOUT_E2E"
            if passed
            else "RELAXED_CALIBRATION_GATE_FAILED"
        ),
        returncode=calibration.returncode,
        calibration_gate_passed=passed,
        deployment_authorized=False,
        calibration_report=str(CALIBRATION_REPORT),
    )
    return 0 if passed else 2


def _strict_calibration_sample_reachable(training_report: dict) -> bool:
    return bool(
        int(training_report.get("calibration_context_count") or 0)
        >= MINIMUM_STRICT_CALIBRATION_CONTEXTS
    )


def _oracle_contract_valid(oracle: dict, expected_freeze_sha: str) -> bool:
    return bool(
        oracle.get("schema_version") == ORACLE_SCHEMA
        and oracle.get("supervision_schema_version") == SUPERVISION_SCHEMA
        and oracle.get("queue_action_surface") == ACTION_SURFACE
        and str(oracle.get("execution_freeze_sha256") or "")
        == expected_freeze_sha
        and bool(oracle.get("development_only"))
        and not bool(oracle.get("deployable"))
    )


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
        "lunar_ice_bpc.p0v5_qg2_relaxed_training_freeze.v1"
    ):
        raise SystemExit("QG2 relaxed training freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        raise SystemExit("QG2 relaxed training freeze safety mismatch")
    if str(payload.get("oracle_execution_freeze_sha256") or "") != (
        _sha256(ORACLE_EXECUTION_FREEZE)
    ):
        raise SystemExit("QG2 relaxed training Oracle freeze drift")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(raw_path)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"QG2 relaxed training frozen drift: {path}")
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
            "lunar_ice_bpc.p0v5_qg2_relaxed_post_oracle_state.v1"
        ),
        "status": str(status),
        **extra,
    }
    _write(STATE, payload)


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
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
