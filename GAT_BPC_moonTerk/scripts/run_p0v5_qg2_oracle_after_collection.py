#!/usr/bin/env python3
"""Start the bounded QO2 oracle only after clean collection preflight passes."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs/p0v5_qg2_label_state_gat_20260801"
EXECUTION_FREEZE = RUN_ROOT / "qg2_clean_v1_oracle_execution_freeze.json"
COLLECTION_STATE = RUN_ROOT / "qg2_clean_v1_collection_controller_state.json"
INDEX = RUN_ROOT / "qg2_clean_v1_live_snapshot_index.json"
ORACLE_DIR = RUN_ROOT / "oracle_qg2_clean_v1_stage1"
ORACLE_SUMMARY = RUN_ROOT / "oracle_qg2_clean_v1_stage1.json"
STATE = RUN_ROOT / "qg2_clean_v1_oracle_controller_state.json"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
TREE_SUPPLEMENT = ROOT / "scripts/run_p0v5_qg2_clean_v1_tree_supplement.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int, required=True)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _validate_execution_freeze()
    _state("WAITING_FOR_COLLECTION_PREFLIGHT", wait_for_pid=args.wait_for_pid)
    while _matching_controller_alive(args.wait_for_pid):
        print(json.dumps({
            "status": "waiting_for_collection_preflight",
            "pid": args.wait_for_pid,
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    collection = _load(COLLECTION_STATE)
    if str(collection.get("status") or "") != "ORACLE_PREFLIGHT_READY":
        _state(
            "NOT_STARTED_COLLECTION_PREFLIGHT_FAILED",
            collection_status=collection.get("status"),
        )
        return 2
    while _native_pricing_pids():
        print(json.dumps({
            "status": "waiting_for_native_idle",
            "pids": _native_pricing_pids(),
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    _state("RUNNING_BOUNDED_TREE_SUPPLEMENT")
    tree = subprocess.run(
        [sys.executable, str(TREE_SUPPLEMENT)],
        cwd=ROOT,
        env=_python_env(),
        check=False,
    )
    if tree.returncode not in {0, 2}:
        _state(
            "TREE_SUPPLEMENT_EXECUTION_ERROR",
            returncode=tree.returncode,
        )
        return tree.returncode
    while _native_pricing_pids():
        print(json.dumps({
            "status": "waiting_for_native_idle_after_tree_supplement",
            "pids": _native_pricing_pids(),
        }, sort_keys=True), flush=True)
        time.sleep(poll)

    _state("RUNNING_BOUNDED_QO2_ORACLE_STAGE1")
    env = _python_env()
    command = [
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_bounded_oracle.py"),
        "--state-index", str(INDEX),
        "--output-dir", str(ORACLE_DIR),
        "--output", str(ORACLE_SUMMARY),
        "--max-contexts", "300",
        "--max-contexts-per-scale", "150",
        "--repeats", "3",
        "--scale30-wall-sec", "180",
        "--scale50-wall-sec", "300",
        "--memory-limit-gb", "10.867",
    ]
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if completed.returncode not in {0, 2}:
        _state("ORACLE_EXECUTION_ERROR", returncode=completed.returncode)
        return completed.returncode
    summary = _load(ORACLE_SUMMARY)
    passed = bool((summary.get("oracle_gate") or {}).get("passed"))
    _state(
        "ORACLE_STAGE1_PASSED" if passed else "ORACLE_STAGE1_GATE_FAILED",
        returncode=completed.returncode,
        oracle_summary=str(ORACLE_SUMMARY),
        oracle_status=summary.get("status"),
        training_permitted=bool(summary.get("training_permitted")),
        context_count=(summary.get("oracle_gate") or {}).get("context_count"),
    )
    return 0 if passed else 2


def _matching_controller_alive(pid: int) -> bool:
    path = Path(f"/proc/{int(pid)}/cmdline")
    try:
        command = path.read_bytes().replace(b"\0", b" ").decode(
            "utf-8", errors="replace"
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "continue_p0v5_qg2_admission_v4_collection.py" in command


def _native_pricing_pids() -> list[int]:
    result = []
    for path in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            command = path.read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if "run_lunar_ice_compact_pricing_batch_probe.py" in command:
            result.append(int(path.parent.name))
    return sorted(result)


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_oracle_controller.v2",
        "status": str(status),
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


def _python_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    return env


def _validate_execution_freeze() -> None:
    payload = _load(EXECUTION_FREEZE)
    if payload.get("schema_version") != (
        "lunar_ice_bpc.p0v5_qg2_oracle_execution_freeze.v1"
    ):
        raise SystemExit("QG2 oracle execution freeze schema mismatch")
    if not bool(payload.get("development_only")) or bool(
        payload.get("deployable")
    ):
        raise SystemExit("QG2 oracle execution freeze safety mismatch")
    for raw_path, expected in dict(
        payload.get("frozen_file_sha256") or {}
    ).items():
        path = Path(raw_path)
        path = path if path.is_absolute() else (ROOT / path)
        if not path.is_file() or _sha256(path) != str(expected):
            raise SystemExit(f"QG2 oracle frozen file drift: {path}")


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
