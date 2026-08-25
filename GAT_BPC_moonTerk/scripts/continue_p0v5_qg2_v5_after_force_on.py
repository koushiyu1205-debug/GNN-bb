#!/usr/bin/env python3
"""Serial handoff: force-on -> bucket screen -> matched arms -> Context GAT."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v5_trace_first_20260807"
FORCE = RUN / "label_gat_force_on_train_screen/force_on_train.json"
STATE = RUN / "POST_FORCE_STATE.json"
HEAVY_STATE = (
    "1ceab640c7be1580bfbbe75807b8609870783c51746b739f23006aedd2feb9f3"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=15.0)
    args = parser.parse_args()

    _state("WAITING_FOR_FORCE_ON", force_pid=int(args.force_pid))
    while _alive(int(args.force_pid)):
        time.sleep(max(5.0, min(30.0, float(args.poll_sec))))
    if not FORCE.is_file():
        _state("FORCE_ON_FAILED_NO_REPORT", force_pid=int(args.force_pid))
        return 2
    force = _load(FORCE)
    records = list(force.get("records") or ())
    if (
        len(records) != 10
        or not all(bool(row.get("safe")) for row in records)
        or bool(force.get("deployable"))
    ):
        _state(
            "FORCE_ON_REPORT_INVALID", record_count=len(records),
            all_safe=all(bool(row.get("safe")) for row in records),
        )
        return 3

    _state("RUNNING_TINYGAT_BUCKET_SCREEN", force_record_count=len(records))
    code = _run([
        sys.executable,
        str(ROOT / "scripts/screen_p0v5_qg2_v5_tinygat_bucket_arms.py"),
        "--state-hash", HEAVY_STATE,
        "--bucket-widths", "0.0001", "0.0003",
        "--repeats", "1",
    ])
    bucket_report = RUN / "label_gat_bucket_screen/bucket_screen.json"
    if code != 0 or not bucket_report.is_file():
        _state("TINYGAT_BUCKET_SCREEN_FAILED", exit_code=code)
        return code or 4

    _state("RUNNING_QD1_QB1_MATCHED_ARMS")
    code = _run([
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_v5_matched_arms.py"),
    ])
    matched = RUN / "matched_arms_qd1_qb1.json"
    if code != 0 or not matched.is_file():
        _state("QD1_QB1_MATCHED_ARMS_FAILED", exit_code=code)
        return code or 5

    beneficial = sum(
        bool(row.get("beneficial")) for row in records
        if bool(row.get("action_eligible"))
    )
    if beneficial >= 2:
        _state(
            "QG2_POSITIVE_SUPPORT_NEEDS_CALIBRATION_HELDOUT_FORCE_ON",
            train_beneficial_count=beneficial,
        )
        return 0

    _state(
        "RUNNING_CONTEXT_GAT_QD1_QB1_WITH_QG2_VETO",
        train_beneficial_count=beneficial,
    )
    context_dir = RUN / "context_gat"
    code = _run([
        sys.executable,
        str(ROOT / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py"),
        "--oracle-summary", str(RUN / "trace_training_view.json"),
        "--ranker-training-report", str(RUN / "label_gat/training_report.json"),
        "--matched-arm-report", str(matched),
        "--qg2-force-on-report", str(FORCE),
        "--output-dir", str(context_dir),
        "--model-kind", "gat",
    ])
    report = context_dir / "training_report.json"
    if code != 0 or not report.is_file():
        _state("CONTEXT_GAT_TRAINING_FAILED", exit_code=code)
        return code or 6
    _state(
        "CONTEXT_GAT_TRAINING_COMPLETE_FRESH_REQUIRED",
        context_gat_report=str(report),
    )
    return 0


def _run(command: list[str]) -> int:
    completed = subprocess.run(
        command, cwd=ROOT, env=_environment(), check=False,
    )
    return int(completed.returncode)


def _environment() -> dict[str, str]:
    env = dict(os.environ)
    build = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{build}"
    for key in (
        "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
        "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
        "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
    ):
        env.pop(key, None)
    return env


def _state(status: str, **fields) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_v5_post_force_state.v1",
        "status": status,
        "development_only": True,
        "deployable": False,
        "production_switch_authorized": False,
        **fields,
    }
    temporary = STATE.with_suffix(STATE.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)


def _alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, ValueError):
        return False


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
