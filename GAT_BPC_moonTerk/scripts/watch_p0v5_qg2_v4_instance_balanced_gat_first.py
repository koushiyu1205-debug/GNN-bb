#!/usr/bin/env python3
"""Hand a completed frozen Oracle to the instance-balanced GAT-first run.

The legacy parent is deliberately stopped while its Oracle child finishes so
it cannot enter the old context-weighted trainers.  This watcher treats a
zombie Oracle child as complete, retires the stopped parent gracefully, and
only then starts the new two-stage training entry point.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/p0v5_qg2_v4_realmap_gat_first_20260806"
ORACLE = RUN / "oracle_realmap_v4.json"
STATE = RUN / "instance_balanced_handoff_state.json"
ENTRY = ROOT / "scripts/run_p0v5_qg2_realmap_v4_instance_balanced_gat_first.py"
REPLAY_MARKER = "replay_p0v5_qg2_label_state_snapshot.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-pid", type=int, required=True)
    parser.add_argument("--paused-parent-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    oracle_pid = int(args.oracle_pid)
    parent_pid = int(args.paused_parent_pid)
    poll = min(60.0, max(1.0, float(args.poll_sec)))
    if _pid_state(parent_pid) not in {"T", "t"}:
        raise SystemExit("legacy GAT-first parent is not safely SIGSTOP-paused")
    _state(
        "WAITING_FOR_FROZEN_ORACLE",
        oracle_pid=oracle_pid,
        paused_parent_pid=parent_pid,
        poll_sec=poll,
    )
    while _pid_running(oracle_pid):
        time.sleep(poll)
    if not ORACLE.is_file():
        _state("ORACLE_EXITED_WITHOUT_SUMMARY", oracle_pid=oracle_pid)
        return 2
    replay_processes = _matching_processes(REPLAY_MARKER)
    if replay_processes:
        _state(
            "ORPHAN_REPLAY_REFUSES_TRAINING",
            replay_processes=replay_processes,
        )
        return 3
    if not _retire_stopped_parent(parent_pid):
        _state("LEGACY_PARENT_RETIREMENT_FAILED", paused_parent_pid=parent_pid)
        return 4
    _state(
        "STARTING_INSTANCE_BALANCED_GAT_FIRST",
        oracle_summary=str(ORACLE),
        paused_parent_retired=True,
    )
    completed = subprocess.run(
        [sys.executable, str(ENTRY)], cwd=ROOT, check=False
    )
    _state(
        "INSTANCE_BALANCED_GAT_FIRST_FINISHED",
        returncode=int(completed.returncode),
    )
    return int(completed.returncode)


def _retire_stopped_parent(pid: int) -> bool:
    state = _pid_state(pid)
    if state is None:
        return True
    if state not in {"T", "t"}:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        os.kill(pid, signal.SIGCONT)
    except ProcessLookupError:
        return True
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if not _pid_running(pid):
            return True
        time.sleep(0.1)
    return False


def _pid_running(pid: int) -> bool:
    state = _pid_state(pid)
    return state is not None and state != "Z"


def _pid_state(pid: int) -> str | None:
    try:
        raw = (Path("/proc") / str(int(pid)) / "stat").read_text(
            encoding="utf-8"
        )
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    closing = raw.rfind(")")
    fields = raw[closing + 2:].split() if closing >= 0 else ()
    return fields[0] if fields else None


def _matching_processes(marker: str) -> list[dict[str, object]]:
    matches = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            command = (entry / "cmdline").read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if marker in command:
            matches.append({"pid": int(entry.name), "command": command.strip()})
    return sorted(matches, key=lambda row: int(row["pid"]))


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_v4_gat_handoff.v1",
        "updated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": str(status),
        "development_only": True,
        "production_switch_authorized": False,
        **extra,
    }
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(STATE.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, STATE)


if __name__ == "__main__":
    raise SystemExit(main())
