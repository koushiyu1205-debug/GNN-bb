#!/usr/bin/env python3
"""Freeze selective Oracle evidence after exploratory QG2 training finishes."""

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
FREEZE = RUN_ROOT / "qg2_selective_oracle_evidence_controller_freeze.json"
STATE = RUN_ROOT / "qg2_selective_oracle_evidence_controller_state.json"
ORACLE = RUN_ROOT / "oracle_qg2_action_surface_v2_stage1.json"
GATE = RUN_ROOT / "qg2_action_surface_v2_training_only_gate_v2.json"
AUTHORIZED = (
    RUN_ROOT / "oracle_qg2_action_surface_v2_training_only_v2_view.json"
)
TRAINING = (
    RUN_ROOT
    / "training_qg2_action_surface_v2_training_only_v2/training_report.json"
)
OUTPUT = RUN_ROOT / "qg2_training_only_v2_selective_oracle_evidence.json"
BUILDER = ROOT / "scripts/build_p0v5_qg2_selective_oracle_evidence.py"
TRAINING_FREEZE = RUN_ROOT / "qg2_action_surface_v2_training_only_v2_freeze.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_freeze()
    _state("WAITING_FOR_TRAINING_ONLY_V2", wait_for_pid=args.wait_for_pid)
    while _matching_training_controller_alive(args.wait_for_pid):
        time.sleep(poll)

    required = (ORACLE, GATE, AUTHORIZED, TRAINING)
    if not all(path.is_file() for path in required):
        _state(
            "NOT_STARTED_TRAINING_AUTHORITY_MISSING",
            missing=[str(path) for path in required if not path.is_file()],
        )
        return 2
    if OUTPUT.exists():
        _state("REFUSED_EXISTING_SELECTIVE_ORACLE_EVIDENCE")
        return 3
    training = _load(TRAINING)
    if str(training.get("oracle_summary_sha256") or "") != _sha256(
        AUTHORIZED
    ):
        _state("NOT_STARTED_TRAINING_AUTHORIZED_ORACLE_BINDING_FAILED")
        return 3

    _state("BUILDING_SELECTIVE_ORACLE_EVIDENCE")
    completed = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--oracle-summary", str(ORACLE),
            "--authorized-oracle", str(AUTHORIZED),
            "--training-gate", str(GATE),
            "--output", str(OUTPUT),
        ],
        cwd=ROOT,
        check=False,
    )
    if completed.returncode != 0 or not OUTPUT.is_file():
        _state(
            "SELECTIVE_ORACLE_EVIDENCE_FAILED",
            returncode=int(completed.returncode),
        )
        return int(completed.returncode or 3)
    evidence = _load(OUTPUT)
    if not bool(
        evidence.get("passed")
        and not evidence.get("deployment_authorized")
        and str(evidence.get("authorized_oracle_sha256") or "")
        == _sha256(AUTHORIZED)
        and str(evidence.get("source_oracle_sha256") or "")
        == _sha256(ORACLE)
        and str(evidence.get("source_gate_sha256") or "") == _sha256(GATE)
    ):
        _state("SELECTIVE_ORACLE_EVIDENCE_CONTRACT_FAILED")
        return 3
    _state(
        "SELECTIVE_ORACLE_EVIDENCE_FROZEN",
        evidence=str(OUTPUT),
        evidence_sha256=_sha256(OUTPUT),
        context_count=int(evidence.get("context_count") or 0),
        deployment_authorized=False,
    )
    return 0


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
        "lunar_ice_bpc.p0v5_qg2_selective_oracle_evidence_controller_freeze.v1"
    ):
        raise SystemExit("selective Oracle evidence controller freeze mismatch")
    if bool(payload.get("deployable")) or str(
        payload.get("authority") or ""
    ) != "model_fitting_and_evaluation_only":
        raise SystemExit("selective Oracle evidence controller safety mismatch")
    if str(payload.get("training_only_v2_freeze_sha256") or "") != _sha256(
        TRAINING_FREEZE
    ):
        raise SystemExit("selective Oracle evidence training freeze drift")
    for raw, expected in dict(payload.get("frozen_file_sha256") or {}).items():
        path = _resolve(raw)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"selective Oracle evidence frozen drift: {path}")


def _state(status: str, **extra) -> None:
    _write(STATE, {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_selective_oracle_evidence_controller_state.v1"
        ),
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": str(status),
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
