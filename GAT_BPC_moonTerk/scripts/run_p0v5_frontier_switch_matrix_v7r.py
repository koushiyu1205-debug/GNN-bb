#!/usr/bin/env python3
"""Run the fixed-context QPF0/QPD1 x3 V7R root-cause matrix."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_frontier_observability_v7r_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, geometric_mean, load, sha256,
    update_state, write_once, write_terminal,
)
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    collapse_matched_blocks,
)


REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--task-limit", type=int)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(run_root, "SWITCH_MATRIX")
    config = load(run_root / "config.freeze.json")
    imported = load(run_root / "v7_preaction_import.freeze.json")
    contexts = list(imported["rows"])
    schedule_path = run_root / "switch_matrix.execution.freeze.json"
    if not schedule_path.is_file():
        write_once(schedule_path, _schedule(config, contexts))
    schedule = load(schedule_path)
    raw_dir = run_root / "switch_matrix_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    by_context = {row["context_id"]: row for row in contexts}
    completed = 0
    for task in schedule["tasks"]:
        output = raw_dir / _task_name(task)
        if output.is_file():
            continue
        if args.task_limit is not None and completed >= args.task_limit:
            break
        context = by_context[task["context_id"]]
        command = [
            sys.executable, str(REPLAY),
            "--instance", str(context["instance_path"]),
            "--snapshot", str(context["snapshot_path"]),
            "--output", str(output),
            "--policy", str(task["arm"]),
            "--repeat-index", str(int(task["block"]) + 1),
            "--wall-time-limit-sec", str(task["cap_seconds"]),
            "--memory-limit-gb", str(config["execution"]["memory_limit_gb"]),
        ]
        result = subprocess.run(
            command, cwd=ROOT, env=_native_environment(run_root), check=False
        )
        if result.returncode:
            raise SystemExit(f"V7R replay task failed:{output.name}")
        completed += 1
    missing = [task for task in schedule["tasks"]
               if not (raw_dir / _task_name(task)).is_file()]
    if missing:
        print(json.dumps({"status": "PARTIAL", "completed_this_call": completed,
                          "remaining_tasks": len(missing)}, indent=2))
        return 0

    raw_rows = _raw_rows(schedule, raw_dir, by_context)
    redlines = sorted({value for row in raw_rows for value in row["correctness_redlines"]})
    if redlines:
        write_terminal(run_root, "V7R_FRONTIER_CORRECTNESS_REDLINE", "SWITCH_MATRIX",
                       {"redlines": redlines})
        raise SystemExit("V7R frontier correctness redline")
    rows_path = run_root / "switch_matrix.rows.json"
    write_once(rows_path, {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_raw_matrix.v1",
        "source_schedule_sha256": sha256(schedule_path),
        "single_native_process": True,
        "rows": raw_rows,
    })
    collapsed = _collapse(raw_rows)
    collapsed_path = run_root / "switch_matrix.collapsed.json"
    write_once(collapsed_path, {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_collapsed.v1",
        "rows": collapsed,
    })
    decision = _gate(config, collapsed)
    write_once(run_root / "switch_oracle.decision.json", decision)
    if decision["decision"] == "FAIL":
        write_terminal(run_root, decision["reason"], "SWITCH_MATRIX", decision)
    else:
        update_state(run_root, "COVERAGE_AUDIT")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _schedule(config, contexts):
    actions = tuple(config["actions"])
    tasks = []
    for context in contexts:
        for block in range(3):
            digest = hashlib.sha256(
                f"v7r:{context['state_hash']}:{block}".encode()
            ).digest()
            shift = int.from_bytes(digest[:2], "big") % len(actions)
            order = actions[shift:] + actions[:shift]
            for ordinal, arm in enumerate(order):
                tasks.append({
                    "context_id": context["context_id"],
                    "instance_hash": context["instance_content_hash"],
                    "scale": int(context["scale"]),
                    "state_hash": context["state_hash"],
                    "block": block,
                    "block_id": f"{context['context_id']}:b{block}",
                    "ordinal_in_block": ordinal,
                    "arm": arm,
                    "cap_seconds": float(config["execution"]["replay_caps_sec"][str(context["scale"])]),
                })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_execution.v1",
        "frozen_before_arm_outcomes": True,
        "blocked_fresh_process_repeats": 3,
        "actions": list(actions),
        "tasks": tasks,
    }


def _task_name(task):
    return f"{task['context_id']}_b{task['block']}_{task['ordinal_in_block']}_{task['arm']}.json"


def _native_environment(run_root):
    source = load(run_root / "source.freeze.json")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str(Path(source["native_binary"]).parent), str((ROOT / "src").resolve())
    ))
    environment.pop("LUNAR_ICE_P0V5_FRONTIER_GAT_QD1_V7_MANIFEST", None)
    return environment


def _raw_rows(schedule, raw_dir, by_context):
    rows = []
    for task in schedule["tasks"]:
        path = raw_dir / _task_name(task)
        raw = load(path)
        context = by_context[task["context_id"]]
        if str(raw.get("instance_content_hash")) != context["instance_content_hash"]:
            raise SystemExit("V7R instance binding drift")
        telemetry = dict(raw.get("proof_telemetry") or {})
        frontier = dict(telemetry.get("proof_queue_frontier_probe") or {})
        redlines = []
        if raw.get("labels_dropped"):
            redlines.append("labels_dropped")
        if frontier.get("reached") and not frontier.get("graph_built"):
            redlines.append("probe_reached_without_graph")
        if task["arm"] == "QPD1" and frontier.get("reached"):
            before = int(frontier.get("frontier_before_migration") or 0)
            if not (
                frontier.get("switched_to_qd1")
                and before == int(frontier.get("drained_count") or -1)
                and before == int(frontier.get("migrated_count") or -1)
                and int(frontier.get("duplicate_count") or 0) == 0
                and int(frontier.get("creation_hash_before") or 0)
                    == int(frontier.get("creation_hash_after") or -1)
            ):
                redlines.append("frontier_migration_mismatch")
        reached = bool(
            raw.get("milestone_reached")
            and raw.get("milestone_kind") == context["target_milestone_kind"]
        )
        rows.append({
            "context_id": task["context_id"],
            "block_id": task["block_id"],
            "block": task["block"],
            "arm": task["arm"],
            "status": "COMPLETE" if reached else str(raw.get("engine_status") or "INCOMPLETE"),
            "wall_seconds": float(raw.get("milestone_wall_sec") or raw.get("backend_solve_wall_sec") or 0.0),
            "cap_seconds": float(task["cap_seconds"]),
            "correctness_redlines": redlines,
            "metadata": {
                "scale": int(context["scale"]),
                "instance_hash": context["instance_content_hash"],
                "state_hash": context["state_hash"],
            },
            "frontier_graph": ({
                "graph_hash": frontier.get("graph_hash"),
                "node_features": frontier.get("node_features"),
                "edges": frontier.get("edges"),
                "context_features": frontier.get("context_features"),
            } if frontier.get("graph_built") else None),
            "frontier_telemetry": frontier,
            "raw_path": str(path),
            "raw_sha256": sha256(path),
        })
    return rows


def _collapse(raw_rows):
    collapsed = collapse_matched_blocks(raw_rows)
    graphs = defaultdict(list)
    for row in raw_rows:
        if row["arm"] == "QPF0" and row["frontier_graph"]:
            graphs[row["context_id"]].append(row["frontier_graph"])
    output = []
    for row in collapsed:
        hashes = {graph["graph_hash"] for graph in graphs[row["context_id"]]}
        redlines = list(row["correctness_redlines"])
        if len(hashes) != 1:
            redlines.append("nondeterministic_frontier_graph")
        output.append({
            **row,
            "correctness_redlines": sorted(set(redlines)),
            "qpf0_graph": graphs[row["context_id"]][0] if graphs[row["context_id"]] else None,
        })
    if any(row["correctness_redlines"] for row in output):
        raise SystemExit("V7R graph determinism redline")
    return output


def _instance_values(rows):
    grouped = defaultdict(list)
    for row in rows:
        if row["determined"]:
            grouped[row["instance_hash"]].append(float(row["ratio"]))
    return {key: geometric_mean(values) for key, values in grouped.items()}


def _gate(config, rows):
    gate = config["switch_gate"]
    scales = {}
    failures = []
    for scale in (30, 50):
        selected = [row for row in rows if int(row["scale"]) == scale]
        determined = [row for row in selected if row["determined"]]
        instances = _instance_values(determined)
        oracle = geometric_mean(min(1.0, value) for value in instances.values()) if instances else None
        metrics = {
            "contexts": len(selected),
            "determined_contexts": len(determined),
            "determined_context_fraction": len(determined) / max(1, len(selected)),
            "determined_instances": len(instances),
            "fixed_qpd1_gm": geometric_mean(instances.values()) if instances else None,
            "oracle_gm": oracle,
            "winner_instances": sum(value < 1.0 for value in instances.values()),
            "benefit_instances": sum(value <= 0.98 for value in instances.values()),
            "neutral_or_harm_instances": sum(value > 0.98 for value in instances.values()),
            "harm_instances": sum(value >= 1.05 for value in instances.values()),
        }
        scales[str(scale)] = metrics
        if metrics["determined_context_fraction"] < gate["minimum_determined_context_fraction"]:
            failures.append(f"scale{scale}:determined_context_fraction")
        if metrics["determined_instances"] < gate["minimum_determined_instances_per_scale"]:
            failures.append(f"scale{scale}:determined_instances")
        if oracle is None or oracle > gate["oracle_gm_at_most"]:
            failures.append(f"scale{scale}:oracle_gm")
        if metrics["winner_instances"] < gate["minimum_winner_instances_per_scale"]:
            failures.append(f"scale{scale}:winner_instances")
    if scales["50"]["benefit_instances"] < gate["minimum_scale50_benefit_instances"]:
        failures.append("scale50:benefit_support")
    if scales["50"]["neutral_or_harm_instances"] < gate["minimum_scale50_neutral_or_harm_instances"]:
        failures.append("scale50:neutral_harm_support")
    oracle_failure = any(value.endswith("oracle_gm") for value in failures)
    reason = "NO_POST4096_SWITCH_ORACLE_HEADROOM" if oracle_failure else (
        "INSUFFICIENT_SWITCH_LABEL_SUPPORT" if failures else None
    )
    return {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_observability_oracle_decision.v1",
        "decision": "FAIL" if failures else "PASS",
        "reason": reason,
        "scales": scales,
        "failures": failures,
        "correctness_redline_count": 0,
        "candidate_trained": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
