#!/usr/bin/env python3
"""Run the fixed tree supplement only if the root-only pilot is insufficient."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
STATE = RUN / "realmap_v4_tree_successor_state.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = min(60.0, max(5.0, float(args.poll_sec)))
    _state("WAITING_FOR_ROOT_PILOT", wait_for_pid=int(args.wait_for_pid))
    while _alive(args.wait_for_pid):
        time.sleep(poll)
    primary = _load(RUN / "realmap_v4_watch_controller_state.json")
    collection = _load(RUN / "realmap_v4_collection_state.json")
    primary_status = str(primary.get("status") or "")
    collection_status = str(collection.get("status") or "")
    if primary_status != "SNAPSHOT_COLLECTION_FAILED":
        _state(
            "PRIMARY_PIPELINE_OWNED_OUTCOME_NO_SUPPLEMENT",
            primary_status=primary_status,
            collection_status=collection_status,
        )
        return 0
    if collection_status != "COLLECTION_INCOMPLETE":
        _state(
            "ROOT_PILOT_FAILED_FOR_NON_COVERAGE_REASON",
            primary_status=primary_status,
            collection_status=collection_status,
        )
        return 2
    _state("RUNNING_FIXED_TREE_SUPPLEMENT")
    supplement = subprocess.run([
        sys.executable,
        str(ROOT / "scripts/continue_p0v5_qg2_realmap_v4_tree_supplement.py"),
        "--snapshot-max-per-instance", "15",
    ], cwd=ROOT, check=False)
    if supplement.returncode != 0:
        _state(
            "TREE_SUPPLEMENT_FAILED",
            returncode=supplement.returncode,
        )
        return supplement.returncode
    _state("RUNNING_GAT_FIRST_AFTER_TREE_SUPPLEMENT")
    gat = subprocess.run([
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_realmap_v4_gat_first.py"),
        "--oracle-contexts", "120",
        "--oracle-contexts-per-scale", "60",
    ], cwd=ROOT, check=False)
    _state(
        "GAT_FIRST_PIPELINE_FINISHED"
        if gat.returncode in {0, 2}
        else "GAT_FIRST_PIPELINE_EXECUTION_ERROR",
        returncode=gat.returncode,
    )
    return gat.returncode


def _alive(pid: int) -> bool:
    return int(pid) > 0 and Path(f"/proc/{int(pid)}").is_dir()


def _load(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def _state(status: str, **extra) -> None:
    RUN.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_qg2_realmap_v4_tree_successor_state.v1"
        ),
        "status": str(status),
        **extra,
    }
    temporary = STATE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)


if __name__ == "__main__":
    raise SystemExit(main())
