#!/usr/bin/env python3
"""Wait for real-map generation, then continue the frozen GAT-first pipeline."""

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
STATE = RUN / "realmap_v4_watch_controller_state.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generation-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = min(60.0, max(5.0, float(args.poll_sec)))
    _state("WAITING_FOR_REALMAP_GENERATION", generation_pid=args.generation_pid)
    while _matching_generation_alive(args.generation_pid):
        time.sleep(poll)
    _state("AUDITING_COMPLETED_REALMAP_CORPUS")
    audit = subprocess.run([
        sys.executable,
        str(ROOT / "scripts/audit_p0v5_qg2_realmap_v4_corpus.py"),
        "--output",
        str(RUN / "realmap_v4_corpus_audit.json"),
    ], cwd=ROOT, check=False)
    if audit.returncode != 0:
        _state("REALMAP_CORPUS_AUDIT_FAILED", returncode=audit.returncode)
        return audit.returncode

    _state("RUNNING_SEQUENTIAL_SNAPSHOT_COLLECTION")
    collection = subprocess.run([
        sys.executable,
        str(ROOT / "scripts/continue_p0v5_qg2_realmap_v4_collection.py"),
        "--root-pool-cap-sec", "300",
        "--snapshot-max-per-instance", "15",
    ], cwd=ROOT, check=False)
    if collection.returncode != 0:
        _state("SNAPSHOT_COLLECTION_FAILED", returncode=collection.returncode)
        return collection.returncode

    _state("RUNNING_GAT_FIRST_PIPELINE")
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


def _matching_generation_alive(pid):
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return (
        "generate_lunar_real_map_benchmark.py" in command
        and "p0v5_qg2_realmap_development_v4" in command
    )


def _state(status, **extra):
    RUN.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_watch_state.v1",
        "status": status,
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
