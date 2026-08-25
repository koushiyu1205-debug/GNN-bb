#!/usr/bin/env python3
"""Collect V8 prefixes and materialize the three frozen-budget triplets."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.counterfactual_prefix_gat_qd1_v8 import (  # noqa: E402
    ROLLOUT_CHECKPOINTS,
    build_triplet,
)
from scripts.p0v5_counterfactual_prefix_gat_qd1_v8_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    assert_active,
    load,
    sha256,
    update_state,
    write_once,
)


def _run_task(run_root: Path, task: dict) -> None:
    output = Path(task["output_path"])
    if output.is_file():
        payload = load(output)
        prefix = dict(payload.get("prefix") or {})
        if bool(prefix.get("complete")) and payload.get("policy") == task["arm"]:
            return
        raise SystemExit(f"partial V8 prefix artifact is not reusable:{output}")
    command = [
        sys.executable,
        str(ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"),
        "--instance", task["instance_path"],
        "--snapshot", task["snapshot_path"],
        "--output", str(output),
        "--policy", task["arm"],
        "--repeat-index", "1",
        "--wall-time-limit-sec", str(task["cap_seconds"]),
        "--memory-limit-gb", "10.867",
        "--counterfactual-max-rollout-budget", "2048",
    ]
    source = load(run_root / "source.freeze.json")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str(source["native_build_dir"]),
        str(ROOT / "src"),
    ))
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.returncode:
        raise SystemExit(
            f"V8 prefix task failed:{task['task_id']}\n{completed.stdout[-4000:]}"
        )
    payload = load(output)
    prefix = dict(payload.get("prefix") or {})
    if not bool(prefix.get("complete")):
        raise SystemExit(f"V8 prefix incomplete:{task['task_id']}")


def collect(run_root: Path, task_limit: int) -> None:
    assert_active(run_root, "REPRESENTATION_PREFIX")
    execution = load(run_root / "representation_execution.freeze.json")
    pending = [
        task for task in execution["tasks"]
        if not Path(task["output_path"]).is_file()
    ]
    for task in pending[:max(0, int(task_limit))]:
        _run_task(run_root, task)
    remaining = sum(
        not Path(task["output_path"]).is_file()
        for task in execution["tasks"]
    )
    if remaining:
        update_state(
            run_root,
            "REPRESENTATION_PREFIX",
            "PARTIAL",
            representation_prefix_tasks_complete=len(execution["tasks"]) - remaining,
            representation_prefix_tasks_total=len(execution["tasks"]),
        )
        print(json.dumps({"status": "PARTIAL", "remaining": remaining}))
        return
    update_state(
        run_root,
        "REPRESENTATION_TRAIN",
        "READY",
        representation_prefix_tasks_complete=len(execution["tasks"]),
        representation_prefix_tasks_total=len(execution["tasks"]),
    )
    print(json.dumps({"status": "COMPLETE", "next": "REPRESENTATION_TRAIN"}))


def _graph_payload(graph) -> dict:
    return {
        "node_features": [list(row) for row in graph.node_features],
        "edge_index": [list(side) for side in graph.edge_index],
        "edge_features": [list(row) for row in graph.edge_features],
        "context_features": list(graph.context_features),
        "graph_hash": graph.graph_hash,
        "label_count": graph.label_count,
        "task_count": graph.task_count,
    }


def materialize(run_root: Path) -> None:
    assert_active(run_root, "REPRESENTATION_TRAIN")
    execution = load(run_root / "representation_execution.freeze.json")
    labels = {
        str(row["context_id"]): dict(row)
        for row in load(run_root / "v7r3_collapsed_labels.freeze.json")["rows"]
    }
    by_context: dict[str, dict[str, dict]] = {}
    raw_hashes = {}
    for task in execution["tasks"]:
        path = Path(task["output_path"])
        if not path.is_file():
            raise SystemExit("V8 representation prefix output missing")
        raw_hashes[path.name] = sha256(path)
        by_context.setdefault(task["context_id"], {})[task["arm"]] = load(path)
    rows = []
    for context_id, arms in sorted(by_context.items()):
        if set(arms) != {"Q0_PREFIX", "QD1_PREFIX"}:
            raise SystemExit("V8 representation prefix pair incomplete")
        q0, qd1 = arms["Q0_PREFIX"], arms["QD1_PREFIX"]
        inputs = dict(q0["graph_inputs"])
        if inputs != dict(qd1["graph_inputs"]):
            raise SystemExit("V8 Q0/QD1 prefix static-input mismatch")
        label = labels[context_id]
        for budget in ROLLOUT_CHECKPOINTS:
            q0_endpoint = next(
                (
                    dict(row) for row in q0["prefix"]["endpoints"]
                    if int(row["rollout_budget"]) == int(budget)
                ), None,
            )
            qd1_endpoint = next(
                (
                    dict(row) for row in qd1["prefix"]["endpoints"]
                    if int(row["rollout_budget"]) == int(budget)
                ), None,
            )
            if q0_endpoint is None or qd1_endpoint is None:
                raise SystemExit(
                    f"V8 per-checkpoint timing missing:{context_id}:{budget}"
                )
            q0_warm = float(q0_endpoint["request_elapsed_wall_seconds"])
            qd1_warm = float(qd1_endpoint["request_elapsed_wall_seconds"])
            graph_wall = sum((
                float(q0["prefix"]["base_graph_build_wall_seconds"]),
                float(q0_endpoint["graph_build_wall_seconds"]),
                float(qd1["prefix"]["base_graph_build_wall_seconds"]),
                float(qd1_endpoint["graph_build_wall_seconds"]),
            ))
            triplet = build_triplet(
                q0["prefix"],
                qd1["prefix"],
                rollout_budget=budget,
                state_hash=str(label["state_hash"]),
                **inputs,
            )
            ratio = float(label["ratio"])
            rows.append({
                "context_id": context_id,
                "instance_hash": str(label["instance_hash"]),
                "state_hash": str(label["state_hash"]),
                "scale": int(label["scale"]),
                "rollout_budget": int(budget),
                "base": _graph_payload(triplet.base),
                "q0": _graph_payload(triplet.q0),
                "qd1": _graph_payload(triplet.qd1),
                "counter_deltas": list(triplet.counter_deltas),
                "target": {
                    "ratio": ratio,
                    "benefit": int(ratio <= 0.98),
                    "positive_gain": max(0.0, 1.0 - ratio),
                    "adverse": int(bool(label.get("adverse")) or ratio >= 1.05),
                },
                "diagnostic_only": True,
                "performance_authority": False,
                "q0_prefix_wall_seconds": q0_warm,
                "qd1_prefix_wall_seconds": qd1_warm,
                "paired_prefix_native_warm_wall_seconds": q0_warm + qd1_warm,
                "paired_prefix_graph_build_wall_seconds": graph_wall,
                "q0_prefix_cold_fresh_process_wall_seconds": float(
                    q0["total_fresh_process_wall_sec"]
                ),
                "qd1_prefix_cold_fresh_process_wall_seconds": float(
                    qd1["total_fresh_process_wall_sec"]
                ),
                "qpf0_reference_wall_seconds": float(
                    label.get("qpf0_median_wall_seconds") or 0.0
                ),
            })
    if len(rows) != 38 * 3:
        raise SystemExit(f"V8 triplet count drift:{len(rows)}")
    payload = {
        "schema_version": (
            "lunar_ice_bpc.p0v5_counterfactual_prefix_representation_dataset.v1"
        ),
        "rows": rows,
        "raw_prefix_sha256": raw_hashes,
        "context_count": 38,
        "triplet_count": 114,
        "performance_authority": False,
        "timing_contract": {
            "gate_wall": "native_per_checkpoint_request_elapsed_wall_seconds",
            "cold_fresh_process_wall_is_diagnostic_only": True,
            "budgets_share_one_2048_collection_but_use_endpoint_timestamps": True,
        },
    }
    write_once(run_root / "representation_triplets.json", payload)
    print(json.dumps({"status": "COMPLETE", "triplets": len(rows)}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("collect", "materialize"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--task-limit", type=int, default=1)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    if args.command == "collect":
        collect(run_root, args.task_limit)
    else:
        materialize(run_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
