#!/usr/bin/env python3
"""Collect a fresh, hash-frozen P0V5 QG2 admission-aware corpus.

The controller never runs two Native pricing jobs concurrently.  It starts
from an empty clean-v1 namespace, validates every batch against the immutable
collection freeze, and extends the frozen v3 candidate prefix until both
scales reach the bounded-oracle context target or all 200 candidates are used.
Earlier admission-v3/v4 artifacts are diagnostic-only and are never indexed.
"""

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
COLLECTION_ID = "qg2_clean_v1"
SNAPSHOT_DIR = RUN_ROOT / "fallback_snapshots_qg2_clean_v1"
FREEZE = RUN_ROOT / "qg2_clean_v1_collection_freeze.json"
INDEX = RUN_ROOT / "qg2_clean_v1_live_snapshot_index.json"
CONFIG = ROOT / "runs/p0v4_v5_exact_gat_binding_20260731/selected_exact_v5.yaml"
CORPUS_ROOT = ROOT / "data/p0v5_qg2_oracle_development_v3"
SCALE30_ROOT = CORPUS_ROOT / "scale_030"
SCALE50_ROOT = CORPUS_ROOT / "scale_050"
BUILD = ROOT / "build/native-spprc-bidirectional-feasibility-v1"
STATE = RUN_ROOT / "qg2_clean_v1_collection_controller_state.json"
CANDIDATE_INSTANCE_LIMIT_PER_SCALE = 200
ORACLE_CONTEXT_TARGET_PER_SCALE = 150
INITIAL_BATCH_SIZE = 30
EXTENSION_BATCH_SIZE = 10


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-for-pid", type=int)
    parser.add_argument("--poll-sec", type=float, default=30.0)
    args = parser.parse_args()
    poll = max(1.0, min(60.0, float(args.poll_sec)))
    _assert_fresh_namespace()
    if args.wait_for_pid:
        _state("WAITING_FOR_DIAGNOSTIC_COLLECTION", wait_for_pid=args.wait_for_pid)
        while _pid_alive(args.wait_for_pid):
            print(
                json.dumps({
                    "status": "waiting_for_diagnostic_collection",
                    "pid": args.wait_for_pid,
                }, sort_keys=True),
                flush=True,
            )
            time.sleep(poll)
    _wait_for_native_idle(poll)
    _state("RUNNING_SCALE30_BATCH01")
    _run_acceptance(
        scale=30,
        instances=_instances(SCALE30_ROOT)[:INITIAL_BATCH_SIZE],
        output_dir=_batch_output_dir(scale=30, batch_number=1),
    )
    coverage = _build_index()

    _state("RUNNING_SCALE50_BATCH01", coverage=coverage)
    _run_acceptance(
        scale=50,
        instances=_instances(SCALE50_ROOT)[:INITIAL_BATCH_SIZE],
        output_dir=_batch_output_dir(scale=50, batch_number=1),
    )
    coverage = _build_index()

    coverage = _extend_frozen_prefix_until_target(coverage)

    preflight = _run_preflight()
    ready = _collection_target_ready(coverage)
    _state(
        "ORACLE_PREFLIGHT_READY" if ready and preflight == 0 else "COVERAGE_INCOMPLETE",
        coverage=coverage,
        preflight_exit_code=preflight,
    )
    return 0 if ready and preflight == 0 else 2


def _run_acceptance(*, scale: int, instances: tuple[Path, ...], output_dir: Path) -> None:
    if not instances:
        raise SystemExit(f"no scale{scale} instances available for collection")
    _wait_for_native_idle(30.0)
    command = [
        sys.executable,
        str(ROOT / "scripts/run_lunar_ice_native_spprc_acceptance.py"),
        "--config", str(CONFIG),
        "--scales", str(scale),
    ]
    for path in instances:
        command.extend(("--instance", str(path)))
    command.extend((
        "--limit", str(len(instances)),
        "--output-dir", str(output_dir),
        "--no-resume",
        "--route-opportunity-collection-only-root-pool",
        "--route-opportunity-collection-root-pool-time-cap-sec", "300",
    ))
    env = dict(os.environ)
    env.update({
        "LUNAR_ICE_P0V5_QG2_SNAPSHOT_MAX_PER_INSTANCE": "15",
        "LUNAR_ICE_P0V5_QG2_FALLBACK_SNAPSHOT_DIR": str(SNAPSHOT_DIR),
        "PYTHONPATH": f"{ROOT / 'src'}:{BUILD}",
    })
    print(json.dumps({
        "status": "starting_acceptance_batch",
        "scale": scale,
        "instance_count": len(instances),
        "output_dir": str(output_dir),
    }, sort_keys=True), flush=True)
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    # The acceptance wrapper returns 1 when rows are intentionally stopped
    # before exact tree closure.  That is the expected collection-only status;
    # snapshot/index validation below is the authoritative success check.
    if completed.returncode not in {0, 1}:
        raise SystemExit(
            f"scale{scale} clean collection batch failed: {completed.returncode}"
        )


def _build_index() -> dict:
    command = [
        sys.executable,
        str(ROOT / "scripts/build_p0v5_qg2_fallback_snapshot_index.py"),
        "--snapshot-dir", str(SNAPSHOT_DIR),
        "--instance-root", str(CORPUS_ROOT),
        "--output", str(INDEX),
        "--collection-freeze", str(FREEZE),
        "--require-exact-action-policy-hash",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=_python_env(),
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit("clean-v1 frozen index validation failed")
    payload = _load(INDEX)
    if int(payload.get("excluded_count") or 0) != 0:
        raise SystemExit("clean-v1 index contains excluded snapshots")
    return dict(payload["coverage"])


def _run_preflight() -> int:
    output = RUN_ROOT / "oracle_qg2_clean_v1_preflight.json"
    command = [
        sys.executable,
        str(ROOT / "scripts/run_p0v5_qg2_bounded_oracle.py"),
        "--state-index", str(INDEX),
        "--output-dir", str(RUN_ROOT / "oracle_qg2_clean_v1"),
        "--output", str(output),
        "--preflight-only",
    ]
    return subprocess.run(
        command,
        cwd=ROOT,
        env=_python_env(),
        check=False,
    ).returncode


def _scale_ready(coverage: dict, scale: int) -> bool:
    row = dict(coverage.get(str(scale)) or {})
    return bool(
        int(row.get("context_count") or 0) >= 20
        and int(row.get("instance_count") or 0) >= 10
    )


def _scale_context_count(coverage: dict, scale: int) -> int:
    return int((coverage.get(str(scale)) or {}).get("context_count") or 0)


def _collection_target_ready(coverage: dict) -> bool:
    return all(
        _scale_context_count(coverage, scale) >= ORACLE_CONTEXT_TARGET_PER_SCALE
        for scale in (30, 50)
    )


def _total_contexts(coverage: dict) -> int:
    return sum(
        int((coverage.get(str(scale)) or {}).get("context_count") or 0)
        for scale in (30, 50)
    )


def _extend_frozen_prefix_until_target(coverage: dict) -> dict:
    next_index = {30: INITIAL_BATCH_SIZE, 50: INITIAL_BATCH_SIZE}
    roots = {30: SCALE30_ROOT, 50: SCALE50_ROOT}
    while not _collection_target_ready(coverage):
        available = [
            scale
            for scale in (30, 50)
            if (
                _scale_context_count(coverage, scale)
                < ORACLE_CONTEXT_TARGET_PER_SCALE
                and next_index[scale] < CANDIDATE_INSTANCE_LIMIT_PER_SCALE
            )
        ]
        if not available:
            return coverage
        scale = min(
            available,
            key=lambda value: (
                _scale_context_count(coverage, value),
                value,
            ),
        )
        start = next_index[scale]
        stop = min(
            CANDIDATE_INSTANCE_LIMIT_PER_SCALE,
            start + EXTENSION_BATCH_SIZE,
        )
        batch_number = 2 + (start - INITIAL_BATCH_SIZE) // EXTENSION_BATCH_SIZE
        output_dir = _batch_output_dir(
            scale=scale,
            batch_number=batch_number,
        )
        next_index[scale] = stop
        _state(
            "RUNNING_FROZEN_PREFIX_EXTENSION",
            coverage=coverage,
            scale=scale,
            index_start=start + 1,
            index_stop=stop,
        )
        _run_acceptance(
            scale=scale,
            instances=_instances(roots[scale])[start:stop],
            output_dir=output_dir,
        )
        coverage = _build_index()
    return coverage


def _batch_output_dir(*, scale: int, batch_number: int) -> Path:
    return RUN_ROOT / (
        f"snapshot_collection_{COLLECTION_ID}_"
        f"scale{scale}_batch{batch_number:02d}"
    )


def _assert_fresh_namespace() -> None:
    targets = [SNAPSHOT_DIR, INDEX, STATE]
    targets.extend(
        _batch_output_dir(scale=scale, batch_number=1)
        for scale in (30, 50)
    )
    targets.extend(RUN_ROOT.glob(f"snapshot_collection_{COLLECTION_ID}_*"))
    existing = sorted({str(path) for path in targets if path.exists()})
    if existing:
        raise SystemExit(
            "clean-v1 namespace is not empty; refusing implicit resume or "
            f"deletion: {existing}"
        )


def _wait_for_native_idle(poll: float) -> None:
    while _native_pricing_pids():
        print(json.dumps({
            "status": "waiting_for_native_idle",
            "pids": _native_pricing_pids(),
        }, sort_keys=True), flush=True)
        time.sleep(max(1.0, min(60.0, poll)))


def _native_pricing_pids() -> list[int]:
    values = []
    for path in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            command = path.read_bytes().replace(b"\0", b" ").decode(
                "utf-8", errors="replace"
            )
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if "run_lunar_ice_compact_pricing_batch_probe.py" in command:
            values.append(int(path.parent.name))
    return sorted(values)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(int(pid), 0)
    except (ProcessLookupError, ValueError):
        return False
    except PermissionError:
        return True
    try:
        command = (
            Path(f"/proc/{int(pid)}/cmdline")
            .read_bytes()
            .replace(b"\0", b" ")
            .decode("utf-8", errors="replace")
        )
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        return False
    return "snapshot_collection_admission_v4_scale30_batch01" in command


def _instances(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(root.glob("instance_*_logical_graph.json")))


def _python_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{BUILD}"
    return env


def _state(status: str, **extra) -> None:
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_collection_controller.v2",
        "status": str(status),
        "collection_id": COLLECTION_ID,
        "snapshot_dir": str(SNAPSHOT_DIR),
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


if __name__ == "__main__":
    raise SystemExit(main())
