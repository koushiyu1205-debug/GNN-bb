#!/usr/bin/env python3
"""Run the offline QD1/QB1 selector diagnostic after QG2 fitting.

The controller is intentionally downstream of model fitting and upstream of
any new calibration decision.  It starts no solver process and cannot change
the active QG2 candidate.  A negative result retains QG2 with literal Q0 as
the only fallback.
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
FREEZE = RUN_ROOT / "qg2_context_arm_selector_controller_freeze.json"
TRAINING_ONLY_V2_FREEZE = (
    RUN_ROOT / "qg2_action_surface_v2_training_only_v2_freeze.json"
)
STATE = RUN_ROOT / "qg2_context_arm_selector_controller_state.json"
OUTPUT_DIR = RUN_ROOT / "context_arm_selector_feasibility_v1"
OUTPUT = OUTPUT_DIR / "selector_report.json"
EVALUATOR = ROOT / "scripts/evaluate_p0v5_qg2_context_arm_selector.py"
TRAINING_CANDIDATES = (
    RUN_ROOT / "training_qg2_action_surface_v2/training_report.json",
    RUN_ROOT / "training_qg2_action_surface_v2_relaxed/training_report.json",
    RUN_ROOT
    / "training_qg2_action_surface_v2_training_only_v2/training_report.json",
)

TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
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
    _state("WAITING_FOR_QG2_MODEL_COMPARISON", wait_for_pid=args.wait_for_pid)
    while _matching_training_controller_alive(args.wait_for_pid):
        time.sleep(poll)

    training_path = _training_authority()
    if training_path is None:
        _state("NOT_STARTED_QG2_TRAINING_REPORT_MISSING_OR_INVALID")
        return 2
    training = _load(training_path)
    oracle_path = _resolve(training.get("oracle_summary") or "")
    if (
        not oracle_path.is_file()
        or str(training.get("oracle_summary_sha256") or "")
        != _sha256(oracle_path)
    ):
        _state("NOT_STARTED_TRAINING_ORACLE_BINDING_FAILED")
        return 3
    if OUTPUT_DIR.exists():
        _state("REFUSED_EXISTING_SELECTOR_OUTPUT", output_dir=str(OUTPUT_DIR))
        return 3

    _state(
        "RUNNING_OFFLINE_CONTEXT_ARM_SELECTOR_FEASIBILITY",
        training_report=str(training_path),
        oracle_summary=str(oracle_path),
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(EVALUATOR),
            "--oracle-summary", str(oracle_path),
            "--training-report", str(training_path),
            "--output-dir", str(OUTPUT_DIR),
            "--output", str(OUTPUT),
        ],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != 0 or not OUTPUT.is_file():
        _state(
            "CONTEXT_ARM_SELECTOR_FEASIBILITY_FAILED",
            returncode=int(completed.returncode),
        )
        return int(completed.returncode or 3)
    report = _load(OUTPUT)
    valid = bool(
        report.get("schema_version") == SELECTOR_SCHEMA
        and not bool(report.get("deployable"))
        and not bool(report.get("starts_solver_process"))
        and not bool(report.get("changes_qg2"))
        and str(report.get("fallback_action") or "") == "Q0"
        and str(report.get("all_arms_rejected_action") or "") == "Q0"
        and str(report.get("training_report_sha256") or "")
        == _sha256(training_path)
        and str(report.get("oracle_summary_sha256") or "")
        == _sha256(oracle_path)
    )
    if not valid:
        _state("CONTEXT_ARM_SELECTOR_REPORT_CONTRACT_FAILED")
        return 3
    recommended = bool(report.get("continued_development_recommended"))
    _state(
        (
            "COMPLETE_RECOMMENDED_FOR_FRESH_PROCESS_COMBINED_EVALUATION"
            if recommended
            else "COMPLETE_RETAIN_QG2_ONLY_WITH_Q0_FALLBACK"
        ),
        selector_report=str(OUTPUT),
        selector_report_sha256=_sha256(OUTPUT),
        continued_development_recommended=recommended,
        deployment_authorized=False,
        fallback_action="Q0",
    )
    return 0


def _training_authority() -> Path | None:
    for path in TRAINING_CANDIDATES:
        if not path.is_file():
            continue
        payload = _load(path)
        if (
            payload.get("schema_version") == TRAINING_SCHEMA
            and bool(payload.get("oracle_gate_passed"))
            and not bool(payload.get("deployable"))
            and str(payload.get("oracle_summary") or "")
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
    return "run_p0v5_qg2_training_only_v2_after_oracle.py" in command


def _validate_freeze() -> None:
    payload = _load(FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_context_arm_selector_controller_freeze.v1"
    ):
        raise SystemExit("context-arm selector controller freeze schema mismatch")
    if (
        not bool(payload.get("development_only"))
        or bool(payload.get("deployable"))
        or bool(payload.get("starts_solver_process"))
        or str(payload.get("fallback_action") or "") != "Q0"
    ):
        raise SystemExit("context-arm selector controller safety mismatch")
    if str(payload.get("training_only_v2_freeze_sha256") or "") != _sha256(
        TRAINING_ONLY_V2_FREEZE
    ):
        raise SystemExit("context-arm selector training-only-v2 freeze drift")
    for raw_path, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw_path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"context-arm selector frozen drift: {path}")


def _state(status: str, **extra) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_context_arm_selector_controller_state.v1"
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
