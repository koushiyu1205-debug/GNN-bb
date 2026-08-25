#!/usr/bin/env python3
"""Run exploratory QG2 fitting after the frozen Oracle and old controllers.

The controller never authorizes deployment.  It waits for the existing strict
and relaxed paths, defers if either path already produced or started training,
and otherwise creates a separately bound training-only authorization view.
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
FREEZE = RUN_ROOT / "qg2_action_surface_v2_training_only_v2_freeze.json"
ORACLE_EXECUTION_FREEZE = (
    RUN_ROOT / "qg2_action_surface_v2_oracle_execution_freeze.json"
)
ORACLE_SUMMARY = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
GATE_REPORT = RUN_ROOT / "qg2_action_surface_v2_training_only_gate_v2.json"
AUTHORIZED_ORACLE = (
    RUN_ROOT / "oracle_qg2_action_surface_v2_training_only_v2_view.json"
)
TRAINING_DIR = RUN_ROOT / "training_qg2_action_surface_v2_training_only_v2"
TRAINING_REPORT = TRAINING_DIR / "training_report.json"
STATE = RUN_ROOT / "qg2_action_surface_v2_training_only_v2_state.json"
STRICT_TRAINING_DIR = RUN_ROOT / "training_qg2_action_surface_v2"
RELAXED_TRAINING_DIR = RUN_ROOT / "training_qg2_action_surface_v2_relaxed"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"

ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
GATE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_training_only_gate.v2"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
SUPERVISION_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_action_reachable_supervision.v2"
)
ACTION_SURFACE = "same_terminal_class_and_reduced_cost_bucket.v1"
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
OLD_CONTROLLER_NAMES = (
    "run_p0v5_qg2_action_surface_v2_training_after_oracle.py",
    "run_p0v5_qg2_relaxed_training_after_oracle.py",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument(
        "--wait-for-controller-pid", type=int, action="append", default=[]
    )
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

    pending = [int(pid) for pid in args.wait_for_controller_pid]
    while any(_matching_old_controller_alive(pid) for pid in pending):
        alive = [pid for pid in pending if _matching_old_controller_alive(pid)]
        _state("WAITING_FOR_OLDER_TRAINING_CONTROLLERS", pids=alive)
        print(json.dumps({
            "status": "waiting_for_older_training_controllers",
            "pids": alive,
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    if STRICT_TRAINING_DIR.exists() or RELAXED_TRAINING_DIR.exists():
        _state(
            "DEFERRED_TO_OLDER_TRAINING_CONTROLLER",
            strict_training_dir_exists=STRICT_TRAINING_DIR.exists(),
            relaxed_training_dir_exists=RELAXED_TRAINING_DIR.exists(),
        )
        return 0
    if not ORACLE_SUMMARY.is_file():
        _state("NOT_STARTED_ORACLE_SUMMARY_MISSING")
        return 2
    oracle = _load(ORACLE_SUMMARY)
    if not _oracle_contract_valid(oracle, expected_oracle_freeze_sha):
        _state("NOT_STARTED_ORACLE_CONTRACT_FAILED")
        return 3

    gate_run = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/evaluate_p0v5_qg2_training_only_gate_v2.py"),
            "--oracle-summary", str(ORACLE_SUMMARY),
            "--output", str(GATE_REPORT),
        ],
        cwd=ROOT,
        env=_python_env(),
        check=False,
    )
    if gate_run.returncode not in {0, 2} or not GATE_REPORT.is_file():
        _state("TRAINING_ONLY_GATE_EXECUTION_ERROR", returncode=gate_run.returncode)
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
        and bool(gate.get("point_geomean_is_report_only"))
        and bool(gate.get("instance_bootstrap_is_report_only"))
    )
    if not authorized:
        _state("NOT_STARTED_TRAINING_ONLY_GATE_V2_FAILED", gate=gate.get("gate"))
        return 2
    if any(path.exists() for path in (
        AUTHORIZED_ORACLE, TRAINING_DIR
    )):
        _state("REFUSED_EXISTING_TRAINING_ONLY_V2_OUTPUT")
        return 3

    authorized_oracle = dict(oracle)
    authorized_oracle["strict_oracle_gate"] = dict(
        oracle.get("oracle_gate") or {}
    )
    authorized_oracle["oracle_gate"] = dict(gate["gate"])
    authorized_oracle["training_permitted"] = True
    authorized_oracle["status"] = "PASSED_TRAINING_ONLY_V2"
    authorized_oracle["deployable"] = False
    authorized_oracle["training_only_v2_authority"] = {
        "authority": "exploratory_model_fitting_only",
        "gate_report": str(GATE_REPORT),
        "gate_report_sha256": _sha256(GATE_REPORT),
        "point_geomean_is_report_only": True,
        "instance_bootstrap_is_report_only": True,
        "deployment_authorized": False,
        "paper_claim_authorized": False,
    }
    _write(AUTHORIZED_ORACLE, authorized_oracle)

    _state("RUNNING_TRAINING_ONLY_V2_MODEL_COMPARISON")
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
        _state("TRAINING_ONLY_V2_FAILED", returncode=training.returncode)
        return int(training.returncode or 3)
    report = _load(TRAINING_REPORT)
    if (
        report.get("schema_version") != TRAINING_SCHEMA
        or report.get("supervision_schema_version") != SUPERVISION_SCHEMA
        or report.get("queue_action_surface") != ACTION_SURFACE
        or not bool(report.get("oracle_gate_passed"))
    ):
        _state("TRAINING_ONLY_V2_REPORT_CONTRACT_FAILED")
        return 3
    _state(
        "TRAINING_ONLY_V2_COMPLETE_PENDING_STRICT_CALIBRATION",
        training_report=str(TRAINING_REPORT),
        calibration_context_count=int(
            report.get("calibration_context_count") or 0
        ),
        deployment_authorized=False,
    )
    return 0


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
    command = _command_line(pid)
    return bool(
        command
        and "run_p0v5_qg2_bounded_oracle.py" in command
        and "oracle_qg2_action_surface_v2_stage1" in command
        and "qg2_action_surface_v2_oracle_execution_freeze.json" in command
    )


def _matching_old_controller_alive(pid: int) -> bool:
    command = _command_line(pid)
    return bool(command and any(name in command for name in OLD_CONTROLLER_NAMES))


def _command_line(pid: int) -> str:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        return path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return ""


def _validate_freeze() -> dict:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_training_only_v2_freeze.v1"
    ):
        raise SystemExit("QG2 training-only-v2 freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        raise SystemExit("QG2 training-only-v2 freeze safety mismatch")
    if not bool(payload.get("deployment_gate_unchanged")):
        raise SystemExit("QG2 training-only-v2 deployment gate drift")
    if str(payload.get("oracle_execution_freeze_sha256") or "") != (
        _sha256(ORACLE_EXECUTION_FREEZE)
    ):
        raise SystemExit("QG2 training-only-v2 Oracle freeze drift")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(raw_path)
        path = path if path.is_absolute() else ROOT / path
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"QG2 training-only-v2 frozen drift: {path}")
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
            "lunar_ice_bpc.p0v5_qg2_training_only_v2_state.v1"
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
