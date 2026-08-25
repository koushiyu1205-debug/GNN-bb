#!/usr/bin/env python3
"""Fresh-process Q0/QPF0/QPD1 matrices and frozen V7 evidence gates."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from math import ceil
import os
from pathlib import Path
import subprocess
import sys
from statistics import median
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    DEFAULT_RUN_ROOT,
    assert_active,
    collapse_matched_blocks,
    geometric_mean,
    load,
    sha256,
    update_state,
    write_once,
    write_terminal,
)


REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("diagnostic", "pilot", "main"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--task-limit", type=int)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    stage = {"diagnostic": "PROBE_DIAGNOSTIC", "pilot": "PILOT_MATRIX",
             "main": "MAIN_MATRIX"}[args.mode]
    assert_active(run_root, stage)
    config = load(run_root / "config.freeze.json")
    corpus_path = run_root / {
        "diagnostic": "probe_diagnostic_contexts.freeze.json",
        "pilot": "pilot_corpus.freeze.json",
        "main": "main_corpus.freeze.json",
    }[args.mode]
    corpus = load(corpus_path)
    contexts = list(corpus["rows"])
    if args.mode == "main":
        contexts = [row for row in contexts if row["partition"] in {"train", "calibration"}]
    actions = ("Q0", "QPF0") if args.mode == "diagnostic" else ("Q0", "QPF0", "QPD1")
    milestones = _freeze_milestones(run_root, config, args.mode, contexts)
    contexts = [row for row in contexts if milestones[row["context_id"]]["replay_eligible"]]
    for row in contexts:
        row["target_milestone_kind"] = milestones[row["context_id"]]["milestone_kind"]
    schedule_path = run_root / f"{args.mode}_matrix.execution.freeze.json"
    if not schedule_path.is_file():
        write_once(schedule_path, _schedule(config, contexts, actions, args.mode))
    schedule = load(schedule_path)
    raw_dir = run_root / f"{args.mode}_matrix_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    context_by_id = {row["context_id"]: row for row in contexts}
    completed_count = 0
    for task in schedule["tasks"]:
        output = raw_dir / (
            f"{task['context_id']}_b{task['block']}_{task['ordinal_in_block']}_{task['arm']}.json"
        )
        if output.is_file():
            continue
        if args.task_limit is not None and completed_count >= args.task_limit:
            break
        context = context_by_id[task["context_id"]]
        command = [
            sys.executable, str(REPLAY), "--instance", str(context["instance_path"]),
            "--snapshot", str(context["snapshot_path"]), "--output", str(output),
            "--policy", str(task["arm"]), "--repeat-index", str(int(task["block"]) + 1),
            "--wall-time-limit-sec", str(task["cap_seconds"]),
            "--memory-limit-gb", str(config["execution"]["memory_limit_gb"]),
        ]
        if args.mode == "diagnostic":
            command.append("--diagnostic-rebind-source-engine")
        result = subprocess.run(
            command, cwd=ROOT, env=_native_environment(config), check=False
        )
        if result.returncode:
            raise SystemExit(f"V7 replay task failed:{output.name}")
        completed_count += 1
    missing = [task for task in schedule["tasks"] if not (
        raw_dir / f"{task['context_id']}_b{task['block']}_{task['ordinal_in_block']}_{task['arm']}.json"
    ).is_file()]
    if missing:
        print(json.dumps({"mode": args.mode, "status": "PARTIAL",
                          "completed_this_call": completed_count,
                          "remaining_tasks": len(missing)}, indent=2))
        return 0
    raw_rows = _raw_rows(schedule, raw_dir, context_by_id)
    raw_payload = {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_probe_raw_matrix.v1",
        "mode": args.mode, "single_native_process": True,
        "source_schedule_sha256": sha256(schedule_path), "rows": raw_rows,
    }
    raw_path = run_root / f"{args.mode}_matrix.rows.json"
    write_once(raw_path, raw_payload)
    redlines = sorted({value for row in raw_rows for value in row["correctness_redlines"]})
    if redlines:
        write_terminal(run_root, reason="V7_NATIVE_FRONTIER_CORRECTNESS_REDLINE",
                       stage=stage, detail={"redlines": redlines})
        raise SystemExit("V7 exact/migration correctness redline")
    collapsed = _collapse(raw_rows, actions)
    collapsed_redlines = sorted({
        value for row in collapsed for value in row.get("correctness_redlines", ())
    })
    if collapsed_redlines:
        write_terminal(run_root, reason="V7_NATIVE_FRONTIER_CORRECTNESS_REDLINE",
                       stage=stage, detail={"redlines": collapsed_redlines})
        raise SystemExit("V7 collapsed graph/correctness redline")
    collapsed_path = run_root / f"{args.mode}_matrix.collapsed.json"
    write_once(collapsed_path, {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_probe_collapsed_matrix.v1",
        "mode": args.mode, "rows": collapsed,
    })
    decision = _gate(args.mode, config, collapsed, raw_rows)
    write_once(run_root / f"{args.mode}_gate.decision.json", decision)
    if decision["decision"] == "FAIL":
        write_terminal(run_root, reason=decision["reason"], stage=stage, detail=decision)
    else:
        update_state(run_root, {
            "diagnostic": "PILOT_CENSUS", "pilot": "MAIN_CENSUS", "main": "TRAINING"
        }[args.mode], "READY")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


def _freeze_milestones(run_root, config, mode, contexts):
    """Freeze one literal-Q0 target before creating any non-Q0 task."""

    path = run_root / f"{mode}_q0_milestone.freeze.json"
    if path.is_file():
        return {row["context_id"]: row for row in load(path)["rows"]}
    raw_dir = run_root / f"{mode}_q0_milestone_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for context in contexts:
        output = raw_dir / f"{context['context_id']}_Q0.json"
        if not output.is_file():
            command = [
                sys.executable, str(REPLAY), "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]), "--output", str(output),
                "--policy", "Q0", "--repeat-index", "0",
                "--wall-time-limit-sec",
                str(config["execution"]["replay_caps_sec"][str(context["scale"])]),
                "--memory-limit-gb", str(config["execution"]["memory_limit_gb"]),
            ]
            if mode == "diagnostic":
                command.append("--diagnostic-rebind-source-engine")
            completed = subprocess.run(
                command, cwd=ROOT, env=_native_environment(config), check=False
            )
            if completed.returncode:
                raise SystemExit(f"V7 Q0 milestone failed:{context['context_id']}")
        raw = load(output)
        status = str(raw.get("engine_status") or "")
        reached = bool(raw.get("milestone_reached"))
        eligible = bool(reached and status not in {"TIMEOUT", "MEMORY_LIMIT"}
                        and not raw.get("labels_dropped"))
        rows.append({
            "context_id": context["context_id"], "scale": int(context["scale"]),
            "instance_hash": context["instance_content_hash"],
            "milestone_kind": raw.get("milestone_kind") if reached else None,
            "milestone_reached": reached, "engine_status": status,
            "labels_dropped": bool(raw.get("labels_dropped")),
            "replay_eligible": eligible,
            "raw_path": str(output), "raw_sha256": sha256(output),
        })
    write_once(path, {
        "schema_version": "lunar_ice_bpc.p0v5_v7_q0_milestone_freeze.v1",
        "frozen_before_non_q0_tasks": True, "mode": mode, "rows": rows,
    })
    return {row["context_id"]: row for row in rows}


def _schedule(config, contexts, actions, mode):
    tasks = []
    for context in contexts:
        scale = int(context["scale"])
        for block in range(3):
            digest = hashlib.sha256(
                f"v7:{context['state_hash']}:{block}".encode()
            ).digest()
            shift = int.from_bytes(digest[:2], "big") % len(actions)
            order = actions[shift:] + actions[:shift]
            for ordinal, arm in enumerate(order):
                tasks.append({
                    "context_id": context["context_id"],
                    "instance_hash": context["instance_content_hash"],
                    "scale": scale, "partition": context.get("partition", "diagnostic"),
                    "state_hash": context["state_hash"], "block": block,
                    "block_id": f"{context['context_id']}:b{block}",
                    "ordinal_in_block": ordinal, "arm": arm,
                    "cap_seconds": float(config["execution"]["replay_caps_sec"][str(scale)]),
                })
    return {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_probe_execution.v1",
        "mode": mode, "frozen_before_arm_outcomes": True,
        "blocked_fresh_process_repeats": 3, "single_native_process": True,
        "tasks": tasks,
    }


def _native_environment(config) -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()), str((ROOT / "src").resolve())
    ))
    for key in tuple(environment):
        if key == "LUNAR_ICE_P0V5_FRONTIER_GAT_QD1_V7_MANIFEST":
            environment.pop(key, None)
    return environment


def _raw_rows(schedule, raw_dir, context_by_id):
    rows = []
    for task in schedule["tasks"]:
        path = raw_dir / (
            f"{task['context_id']}_b{task['block']}_{task['ordinal_in_block']}_{task['arm']}.json"
        )
        raw = load(path)
        context = context_by_id[task["context_id"]]
        if str(raw["instance_content_hash"]) != str(context["instance_content_hash"]):
            raise SystemExit("V7 replay instance binding drift")
        telemetry = dict(raw.get("proof_telemetry") or {})
        frontier = dict(telemetry.get("proof_queue_frontier_probe") or {})
        redlines = []
        if bool(raw.get("labels_dropped")):
            redlines.append("labels_dropped")
        if task["arm"] == "QPD1" and bool(frontier.get("reached")):
            before = int(frontier.get("frontier_before_migration") or 0)
            if not (
                bool(frontier.get("switched_to_qd1"))
                and before == int(frontier.get("drained_count") or -1)
                and before == int(frontier.get("migrated_count") or -1)
                and int(frontier.get("duplicate_count") or 0) == 0
                and int(frontier.get("creation_hash_before") or 0)
                    == int(frontier.get("creation_hash_after") or -1)
            ):
                redlines.append("frontier_migration_mismatch")
        reached = bool(
            raw.get("milestone_reached")
            and raw.get("milestone_kind") == context.get("target_milestone_kind")
        )
        rows.append({
            "context_id": task["context_id"], "block_id": task["block_id"],
            "block": task["block"], "arm": task["arm"],
            "status": "COMPLETE" if reached else str(raw.get("engine_status") or "INCOMPLETE"),
            "wall_seconds": float(raw.get("milestone_wall_sec") or raw.get("backend_solve_wall_sec") or 0.0),
            "cap_seconds": float(task["cap_seconds"]),
            "correctness_redlines": redlines,
            "metadata": {
                "scale": int(context["scale"]), "partition": context.get("partition", "diagnostic"),
                "instance_hash": context["instance_content_hash"],
                "state_hash": context["state_hash"],
                "target_milestone_kind": context.get("target_milestone_kind"),
            },
            "frontier_graph": ({
                "graph_hash": frontier.get("graph_hash"),
                "node_features": frontier.get("node_features"),
                "edges": frontier.get("edges"),
                "context_features": frontier.get("context_features"),
            } if task["arm"] == "QPF0" and frontier.get("graph_built") else None),
            "frontier_telemetry": frontier,
            "raw_path": str(path), "raw_sha256": sha256(path),
        })
    return rows


def _pair(rows, left: str, right: str) -> dict[str, dict[str, Any]]:
    prepared = []
    for row in rows:
        if row["arm"] not in {left, right}:
            continue
        copied = dict(row)
        copied["arm"] = "QPF0" if row["arm"] == left else "QPD1"
        prepared.append(copied)
    return {row["context_id"]: row for row in collapse_matched_blocks(prepared)}


def _collapse(rows, actions):
    probe = _pair(rows, "Q0", "QPF0")
    if "QPD1" not in actions:
        return [{**row, "probe_ratio": row["ratio"]} for row in probe.values()]
    switch = _pair(rows, "QPF0", "QPD1")
    net = _pair(rows, "Q0", "QPD1")
    graphs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["arm"] == "QPF0" and row["frontier_graph"]:
            graphs[row["context_id"]].append(row["frontier_graph"])
    output = []
    for context_id in sorted(switch):
        row = dict(switch[context_id])
        hashes = {value["graph_hash"] for value in graphs[context_id]}
        if len(hashes) != 1:
            row["correctness_redlines"] = sorted(set(
                row["correctness_redlines"] + ["nondeterministic_frontier_graph"]
            ))
        row["probe_ratio"] = probe.get(context_id, {}).get("ratio")
        row["net_ratio"] = net.get(context_id, {}).get("ratio")
        row["qpf0_graph"] = graphs[context_id][0] if graphs[context_id] else None
        output.append(row)
    return output


def _gate(mode, config, rows, raw_rows):
    by_scale = {}
    for scale in (30, 50):
        selected = [row for row in rows if int(row["scale"]) == scale]
        if mode == "diagnostic":
            ratios = [float(row["probe_ratio"]) for row in selected if row["determined"]]
            p99_ms = _p99([
                1000.0 * (float(item["frontier_telemetry"].get("graph_build_wall_seconds") or 0.0)
                          + float(item["frontier_telemetry"].get("inference_wall_seconds") or 0.0))
                for item in raw_rows if int(item["metadata"]["scale"]) == scale
                and item["arm"] == "QPF0"
            ])
            metrics = {"gm": geometric_mean(ratios), "p90": _quantile(ratios, .9),
                       "worst": max(ratios), "warm_p99_ms": p99_ms,
                       "determined_contexts": len(ratios)}
        else:
            determined = [row for row in selected if row["determined"]]
            instance_switch = _instance_values(determined, "ratio")
            instance_net = _instance_values(determined, "net_ratio")
            oracle_probe = geometric_mean(min(1.0, value) for value in instance_switch.values())
            oracle_net = geometric_mean(min(1.0, value) for value in instance_net.values())
            winners = sum(value < 1.0 for value in instance_switch.values())
            metrics = {
                "context_count": len(selected), "determined_contexts": len(determined),
                "determined_instances": len(instance_switch),
                "oracle_qpf0_qpd1_gm": oracle_probe,
                "oracle_q0_qpd1_gm": oracle_net,
                "qpd1_winner_instances": winners,
                "benefit_instances": sum(value <= .98 for value in instance_switch.values()),
                "neutral_or_harm_instances": sum(value > .98 for value in instance_switch.values()),
            }
        by_scale[str(scale)] = metrics
    reason = None
    if mode == "diagnostic":
        gate = config["gates"]["probe_overhead"]
        if any(by_scale[str(scale)]["gm"] > gate["gm_at_most"]
               or by_scale[str(scale)]["p90"] > gate["p90_at_most"]
               or by_scale[str(scale)]["worst"] > gate["worst_at_most"]
               or by_scale[str(scale)]["warm_p99_ms"] > gate["warm_p99_ms_at_most"]
               for scale in (30, 50)):
            reason = "FRONTIER_PROBE_OVERHEAD_FAILED"
    elif mode == "pilot":
        gate = config["gates"]["pilot"]
        if any(by_scale[str(scale)]["determined_contexts"] < gate["determined_contexts_per_scale"]
               or by_scale[str(scale)]["oracle_qpf0_qpd1_gm"] > gate["oracle_gm_at_most"]
               or by_scale[str(scale)]["qpd1_winner_instances"] < gate["minimum_qpd1_winner_instances"]
               for scale in (30, 50)):
            reason = "NO_FRONTIER_SWITCH_HEADROOM"
        elif not (by_scale["50"]["benefit_instances"] > 0
                  and by_scale["50"]["neutral_or_harm_instances"] > 0):
            reason = "NO_FRONTIER_SWITCH_HEADROOM"
    else:
        gate = config["gates"]["main"]
        train_rows = [row for row in rows if row["partition"] == "train"]
        for scale in (30, 50):
            scale_rows = [row for row in train_rows if int(row["scale"]) == scale]
            determined = [row for row in scale_rows if row["determined"]]
            instances = _instance_values(determined, "ratio")
            net = _instance_values(determined, "net_ratio")
            if (
                len(determined) / max(1, len(scale_rows)) < gate["determined_context_fraction"]
                or len(instances) < gate["determined_train_instances"]
                or sum(value <= .98 for value in instances.values()) < gate["minimum_benefit_instances"]
                or sum(value > .98 for value in instances.values()) < gate["minimum_adverse_or_neutral_instances"]
                or geometric_mean(min(1.0, value) for value in instances.values()) > gate["oracle_gm_at_most"]
                or geometric_mean(min(1.0, value) for value in net.values()) > gate["oracle_gm_at_most"]
                or sum(value < 1.0 for value in instances.values()) < gate["minimum_switch_winner_instances"]
            ):
                reason = "INSUFFICIENT_FRONTIER_GAT_TRAINING_SUPPORT"
    return {
        "schema_version": "lunar_ice_bpc.p0v5_frontier_probe_gate.v1",
        "stage": mode, "decision": "FAIL" if reason else "PASS", "reason": reason,
        "scales": by_scale, "correctness_redline_count": 0,
    }


def _instance_values(rows, field):
    grouped = defaultdict(list)
    for row in rows:
        value = row.get(field)
        if value is not None:
            grouped[row["instance_hash"]].append(float(value))
    return {key: geometric_mean(values) for key, values in grouped.items()}


def _quantile(values: Iterable[float], probability: float) -> float:
    rows = sorted(float(value) for value in values)
    return rows[max(0, min(len(rows) - 1, ceil(probability * len(rows)) - 1))]


def _p99(values: Iterable[float]) -> float:
    rows = list(values)
    return _quantile(rows, .99) if rows else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
