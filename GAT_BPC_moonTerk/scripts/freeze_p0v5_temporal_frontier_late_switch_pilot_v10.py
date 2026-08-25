#!/usr/bin/env python3
"""Rebind pre-action states and freeze the V10 late-switch schedule."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_temporal_frontier_late_switch_v10_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, load, sha256, update_state, write_once,
)


def _snapshot_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode()).hexdigest()


def _task_order(state_hash: str, block: int, rows: list[dict]) -> list[dict]:
    digest = hashlib.sha256(
        f"v10-late-switch:{state_hash}:{block}".encode()
    ).digest()
    shift = int.from_bytes(digest[:2], "big") % len(rows)
    return rows[shift:] + rows[:shift]


def _schedule(config: dict, contexts: list[dict]) -> dict:
    tasks = []
    repeats = int(config["execution"]["blocked_fresh_process_repeats"])
    prefixes = config["observation_prefixes"]
    for context in contexts:
        scale = int(context["scale"])
        specs = [{
            "arm_id": "Q0",
            "policy": "Q0",
            "decision_boundary": None,
            "observation_boundaries": [],
        }]
        for boundary in config["decision_boundaries"][str(scale)]:
            for policy in ("QPF0", "QPD1"):
                specs.append({
                    "arm_id": f"{policy}_B{int(boundary)}",
                    "policy": policy,
                    "decision_boundary": int(boundary),
                    "observation_boundaries": list(prefixes[str(boundary)]),
                })
        for block in range(repeats):
            for ordinal, spec in enumerate(
                _task_order(context["state_hash"], block, specs)
            ):
                tasks.append({
                    "context_id": context["context_id"],
                    "instance_hash": context["instance_content_hash"],
                    "scale": scale,
                    "state_hash": context["state_hash"],
                    "block": block,
                    "block_id": f"{context['context_id']}:b{block}",
                    "ordinal_in_block": ordinal,
                    "cap_seconds": float(
                        config["execution"]["replay_caps_sec"][str(scale)]
                    ),
                    **spec,
                })
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_execution.v1"
        ),
        "frozen_before_late_switch_wall_outcomes": True,
        "single_native_process": True,
        "blocked_fresh_process_repeats": repeats,
        "task_count": len(tasks),
        "tasks": tasks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root, "PERFORMANCE_FREEZE")
    config = load(run_root / "config.freeze.json")
    source = load(run_root / "source.freeze.json")
    report_path = run_root / "native_differential.report.json"
    report = load(report_path)
    if report.get("decision") != "PASS" or report.get("mismatch_count") != 0:
        raise SystemExit("V10 Native differential is not a clean PASS")
    if int(report.get("case_count") or 0) != int(
        config["native_differential"]["case_count"]
    ):
        raise SystemExit("V10 Native differential case-count drift")

    imported = load(run_root / "preaction_source.freeze.json")
    engine_hash = source["temporal_engine_hashes"]["root_partial_hybrid"]
    rows = []
    for raw in imported["selected_rows"]:
        source_path = Path(raw["source_snapshot_path"])
        original = load(source_path)
        rebound = dict(original)
        rebound["engine_hash"] = str(engine_hash)
        rebound.pop("state_hash", None)
        rebound["state_hash"] = _snapshot_hash(rebound)
        target = (
            run_root / "rebound_preaction_snapshots"
            / f"scale{int(raw['scale'])}" / raw["instance_content_hash"]
            / f"{rebound['state_hash']}.json"
        )
        write_once(target, rebound)
        changed_keys = sorted(
            key for key in set(original) | set(rebound)
            if original.get(key) != rebound.get(key)
        )
        if changed_keys != ["engine_hash", "state_hash"]:
            raise SystemExit(
                f"V10 rebound changed forbidden fields:{raw['context_id']}:{changed_keys}"
            )
        rows.append({
            **raw,
            "original_engine_hash": original["engine_hash"],
            "original_state_hash": original["state_hash"],
            "snapshot_path": str(target.resolve()),
            "snapshot_sha256": sha256(target),
            "state_hash": rebound["state_hash"],
            "engine_hash": rebound["engine_hash"],
            "rebound_changes_only_engine_and_state_hash": True,
            "rebound_frozen_before_late_switch_wall_outcomes": True,
        })

    corpus = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_pilot_corpus.v1"
        ),
        "diagnostic_only": True,
        "fresh_late_switch_outcomes": True,
        "historical_arm_outcomes_imported": 0,
        "counts": {
            str(scale): {
                "contexts": sum(int(row["scale"]) == scale for row in rows),
                "instances": len({
                    row["instance_content_hash"] for row in rows
                    if int(row["scale"]) == scale
                }),
            } for scale in (30, 50)
        },
        "rows": rows,
    }
    if corpus["counts"] != {
        "30": {"contexts": 8, "instances": 8},
        "50": {"contexts": 8, "instances": 8},
    }:
        raise SystemExit(f"V10 corpus count drift:{corpus['counts']}")
    corpus_path = run_root / "pilot_corpus.freeze.json"
    schedule_path = run_root / "late_switch.execution.freeze.json"
    write_once(corpus_path, corpus)
    write_once(schedule_path, _schedule(config, rows))
    differential_import = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_differential_import.v1"
        ),
        "decision": "PASS",
        "case_count": report["case_count"],
        "mismatch_count": 0,
        "report_sha256": sha256(report_path),
        "temporal_native_binary_sha256": source[
            "temporal_native_binary_sha256"
        ],
    }
    differential_path = run_root / "native_differential.import.freeze.json"
    write_once(differential_path, differential_import)
    artifacts = (
        "native_differential.report.json",
        "native_differential.import.freeze.json",
        "pilot_corpus.freeze.json",
        "late_switch.execution.freeze.json",
    )
    write_once(run_root / "performance.freeze.registry.json", {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_performance_freeze.v1"
        ),
        "immutable": True,
        "frozen_before_late_switch_wall_outcomes": True,
        "artifact_sha256": {
            name: sha256(run_root / name) for name in artifacts
        },
    })
    update_state(
        run_root, "LATE_SWITCH_MATRIX",
        performance_freeze="performance.freeze.registry.json",
        scheduled_task_count=load(schedule_path)["task_count"],
    )
    print(json.dumps({
        "status": "READY_FOR_LATE_SWITCH_MATRIX",
        "counts": corpus["counts"],
        "scheduled_task_count": load(schedule_path)["task_count"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

