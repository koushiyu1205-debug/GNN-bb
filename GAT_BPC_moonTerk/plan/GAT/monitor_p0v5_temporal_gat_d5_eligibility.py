#!/usr/bin/env python3
"""Append-only read-only heartbeat monitor for the frozen D5 eligibility run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
COLLECTOR = "collect_p0v5_temporal_gat_root_contexts_v1.py"
REPLAY = "replay_p0v5_qg2_label_state_snapshot.py"


def load(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def process_rows(run_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    writers: list[dict[str, Any]] = []
    children: list[dict[str, Any]] = []
    run_name = run_root.name
    for proc in Path("/proc").glob("[0-9]*"):
        try:
            args = [
                value.decode(errors="replace")
                for value in (proc / "cmdline").read_bytes().split(b"\0")
                if value
            ]
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        joined = " ".join(args)
        if run_name not in joined:
            continue
        pid = int(proc.name)
        row = {"pid": pid, "cmd": joined}
        if COLLECTOR in joined and "eligibility" in args:
            writers.append(row)
        elif REPLAY in joined:
            output = ""
            if "--output" in args and args.index("--output") + 1 < len(args):
                output = args[args.index("--output") + 1]
            row["output"] = output
            row["state_hash"] = Path(output).name.removesuffix(".json.partial")
            row["scale"] = (
                50 if "--frontier-probe-boundary 16384" in joined else 30
            )
            children.append(row)
    return writers, children


def process_resource(pid: int) -> dict[str, Any]:
    completed = subprocess.run(
        ["ps", "-o", "etimes=,rss=", "-p", str(pid)],
        check=False,
        capture_output=True,
        text=True,
    )
    fields = completed.stdout.split()
    if len(fields) != 2:
        return {"elapsed_sec": None, "rss_gib": None}
    return {
        "elapsed_sec": int(fields[0]),
        "rss_gib": round(int(fields[1]) / 1024 / 1024, 6),
    }


def mem_available_gib() -> float:
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    raise RuntimeError("MemAvailable unavailable")


def binding_status(run_root: Path, config_path: Path, corpus_path: Path) -> dict[str, Any]:
    issues: list[str] = []
    config = load(config_path)
    if config != load(run_root / "config.freeze.json"):
        issues.append("CONFIG_SEMANTIC_DRIFT")
    registry = load(run_root / "bootstrap.freeze.registry.json")
    for relative, expected in dict(registry["artifact_sha256"]).items():
        path = run_root / relative
        if not path.is_file() or sha256(path) != expected:
            issues.append(f"BOOTSTRAP_DRIFT:{relative}")
    source = load(run_root / "source.freeze.json")
    for field in (
        "corpus_manifest",
        "formal_acceptance_contract",
        "native_binary",
        "native_test_binary",
        "protected_history_cache",
        "reference_native_binary",
        "selected_exact_config",
    ):
        path = Path(str(source[field]))
        if not path.is_file() or sha256(path) != str(source[f"{field}_sha256"]):
            issues.append(f"BOUND_ARTIFACT_DRIFT:{field}")
    if sha256(corpus_path) != str(source["corpus_manifest_sha256"]):
        issues.append("CORPUS_MANIFEST_DRIFT")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--interval-sec", type=int, default=30)
    parser.add_argument("--target", type=int, default=274)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    heartbeat_path = output_dir / "heartbeat.jsonl"
    latest_path = output_dir / "latest.json"
    status_counts: Counter[str] = Counter()
    seen: set[str] = set()
    boundary_reached = 0
    graph_built = 0
    model_called = 0
    label_drop = 0
    binding = binding_status(
        run_root, args.config.resolve(), args.corpus.resolve()
    )
    heartbeat_index = 0
    while True:
        heartbeat_index += 1
        if heartbeat_index > 1 and heartbeat_index % 20 == 1:
            binding = binding_status(
                run_root, args.config.resolve(), args.corpus.resolve()
            )
        files = sorted((run_root / "boundary_eligibility").glob("*.json"))
        duplicate_states = 0
        final_states: set[str] = set()
        corrupt: list[str] = []
        for path in files:
            if path.stem in seen:
                final_states.add(path.stem)
                continue
            try:
                row = load(path)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                corrupt.append(f"{path.name}:{type(exc).__name__}")
                continue
            state_hash = str(row.get("source_state_hash") or "")
            if state_hash in final_states:
                duplicate_states += 1
            final_states.add(state_hash)
            if state_hash != path.stem:
                corrupt.append(f"{path.name}:STATE_FILENAME_MISMATCH")
                continue
            status_counts[str(row.get("engine_status") or "MISSING")]
            status_counts[str(row.get("engine_status") or "MISSING")] += 1
            frontier = dict(
                dict(row.get("proof_telemetry") or {}).get(
                    "proof_queue_frontier_probe"
                )
                or {}
            )
            boundary_reached += int(bool(frontier.get("reached")))
            graph_built += int(bool(frontier.get("graph_built")))
            model_called += int(bool(frontier.get("model_called")))
            label_drop += int(bool(row.get("labels_dropped")))
            seen.add(state_hash)
            del row
        writers, children = process_rows(run_root)
        active_outputs = {str(row.get("output") or "") for row in children}
        partials = sorted(run_root.rglob("*.partial"))
        orphan_partials = [
            str(path) for path in partials if str(path) not in active_outputs
        ]
        forbidden = [
            name
            for name in (
                "contexts.freeze.json",
                "train_trial_schedule.freeze.json",
                "train_trial_preflight.audit.json",
                "terminal_decision.json",
            )
            if (run_root / name).exists()
        ]
        child = children[0] if len(children) == 1 else None
        child_resource = (
            process_resource(int(child["pid"])) if child else {
                "elapsed_sec": None,
                "rss_gib": None,
            }
        )
        current_state_hash = str(child.get("state_hash") or "") if child else None
        redlines: list[str] = []
        if len(writers) > 1:
            redlines.append("SECOND_WRITER")
        if len(children) > 1:
            redlines.append("SECOND_CHILD")
        if binding["status"] != "PASS":
            redlines.append("BINDING_DRIFT")
        if model_called:
            redlines.append("MODEL_CALLED")
        if label_drop:
            redlines.append("LABEL_DROP")
        if duplicate_states:
            redlines.append("DUPLICATE_STATE")
        if corrupt:
            redlines.append("CORRUPT_FINAL")
        if orphan_partials:
            redlines.append("ORPHAN_PARTIAL")
        if forbidden:
            redlines.append("FORBIDDEN_POST_ELIGIBILITY_ARTIFACT")
        available = mem_available_gib()
        if available < 2.0 and writers:
            redlines.append("MEMAVAILABLE_RESERVE_VIOLATION")
        payload = {
            "schema_version": "lunar_ice_bpc.d5_eligibility_heartbeat.v1",
            "timestamp": datetime.now().astimezone().isoformat(),
            "valid_completed": len(final_states),
            "target": int(args.target),
            "missing_count": max(0, int(args.target) - len(final_states)),
            "duplicate_count": duplicate_states,
            "partial_count": len(partials),
            "orphan_partial_count": len(orphan_partials),
            "writer_count": len(writers),
            "child_count": len(children),
            "current_state_hash": current_state_hash,
            "current_scale": child.get("scale") if child else None,
            "current_child_pid": child.get("pid") if child else None,
            "current_wall_sec": child_resource["elapsed_sec"],
            "current_rss_gib": child_resource["rss_gib"],
            "mem_available_gib": round(available, 6),
            "boundary_reached_count": boundary_reached,
            "graph_built_count": graph_built,
            "model_called_count": model_called,
            "label_drop_count": label_drop,
            "engine_status_counts": dict(sorted(status_counts.items())),
            "arm_outcome_artifact_count": len(forbidden),
            "binding_hash_status": binding,
            "redlines": redlines,
        }
        with heartbeat_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        atomic_json(latest_path, payload)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)
        if redlines:
            return 2
        if len(final_states) == int(args.target) and not writers and not children:
            return 0
        time.sleep(max(5, int(args.interval_sec)))


if __name__ == "__main__":
    raise SystemExit(main())
