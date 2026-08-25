#!/usr/bin/env python3
"""Run and gate the frozen V10 Q0/QPF0/QPD1 temporal matrix."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.p0v5_native_frontier_gat_qd1_v7_common import (  # noqa: E402
    collapse_matched_blocks,
)
from scripts.p0v5_temporal_frontier_late_switch_v10_common import (  # noqa: E402
    DEFAULT_RUN_ROOT, assert_active, geometric_mean, load, sha256,
    update_state, write_once, write_terminal,
)


REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"


def _task_name(task: dict) -> str:
    return (
        f"{task['context_id']}_b{task['block']}_"
        f"{task['ordinal_in_block']}_{task['arm_id']}.json"
    )


def _native_environment(run_root: Path) -> dict[str, str]:
    source = load(run_root / "source.freeze.json")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str(Path(source["temporal_native_build"])), str(ROOT / "src"),
    ))
    for key in (
        "LUNAR_ICE_P0V5_FRONTIER_GAT_QD1_V7_MANIFEST",
        "LUNAR_ICE_P0V5_COUNTERFACTUAL_PREFIX_GAT_QD1_V8_MANIFEST",
    ):
        environment.pop(key, None)
    return environment


def _run_task(run_root: Path, config: dict, context: dict,
              task: dict, output: Path) -> None:
    command = [
        sys.executable, str(REPLAY),
        "--instance", str(context["instance_path"]),
        "--snapshot", str(context["snapshot_path"]),
        "--output", str(output),
        "--policy", str(task["policy"]),
        "--repeat-index", str(int(task["block"]) + 1),
        "--wall-time-limit-sec", str(task["cap_seconds"]),
        "--memory-limit-gb", str(config["execution"]["memory_limit_gb"]),
    ]
    if task["decision_boundary"] is not None:
        command.extend((
            "--frontier-probe-boundary", str(task["decision_boundary"]),
            "--frontier-observation-boundaries",
            *map(str, task["observation_boundaries"]),
        ))
    completed = subprocess.run(
        command, cwd=ROOT, env=_native_environment(run_root), check=False,
    )
    if completed.returncode:
        raise SystemExit(f"V10 replay task failed:{output.name}")


def _frontier_redlines(task: dict, raw: dict, frontier: dict) -> list[str]:
    redlines = []
    if raw.get("labels_dropped"):
        redlines.append("labels_dropped")
    if any(not bool(row.get("accepted")) for row in raw.get("route_audit") or ()):
        redlines.append("route_reduced_cost_reaudit_failed")
    if task["policy"] == "Q0":
        if frontier.get("enabled"):
            redlines.append("literal_q0_unexpected_frontier_probe")
        return redlines
    expected_boundary = int(task["decision_boundary"])
    expected_observations = list(map(int, task["observation_boundaries"]))
    if not frontier.get("enabled"):
        redlines.append("temporal_probe_not_enabled")
    if int(frontier.get("boundary") or 0) != expected_boundary:
        redlines.append("temporal_probe_boundary_mismatch")
    if list(map(int, frontier.get("observation_boundaries") or ())) != expected_observations:
        redlines.append("temporal_observation_contract_mismatch")
    snapshots = list(frontier.get("snapshots") or ())
    snapshot_boundaries = [int(row.get("boundary") or 0) for row in snapshots]
    if frontier.get("reached") and snapshot_boundaries != expected_observations:
        redlines.append("temporal_snapshot_boundary_mismatch")
    if any(not row.get("reached") or not row.get("graph_built") for row in snapshots):
        redlines.append("temporal_snapshot_graph_missing")
    if task["policy"] == "QPF0":
        if frontier.get("switched_to_qd1"):
            redlines.append("qpf0_unexpected_qd1_switch")
    elif frontier.get("reached"):
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
    return redlines


def _raw_rows(schedule: dict, raw_dir: Path,
              by_context: dict[str, dict]) -> list[dict]:
    rows = []
    for task in schedule["tasks"]:
        path = raw_dir / _task_name(task)
        raw = load(path)
        context = by_context[task["context_id"]]
        if raw.get("instance_content_hash") != context["instance_content_hash"]:
            raise SystemExit("V10 instance binding drift")
        if raw.get("source_state_hash") != context["state_hash"]:
            raise SystemExit("V10 state binding drift")
        telemetry = dict(raw.get("proof_telemetry") or {})
        frontier = dict(telemetry.get("proof_queue_frontier_probe") or {})
        milestone_reached = bool(
            raw.get("milestone_reached")
            and raw.get("milestone_kind") == context["target_milestone_kind"]
        )
        boundary_reached = bool(
            task["policy"] == "Q0" or frontier.get("reached")
        )
        rows.append({
            "context_id": task["context_id"],
            "block_id": task["block_id"],
            "block": int(task["block"]),
            "arm": task["arm_id"],
            "policy": task["policy"],
            "decision_boundary": task["decision_boundary"],
            "observation_boundaries": task["observation_boundaries"],
            "status": (
                "COMPLETE" if milestone_reached and boundary_reached
                else str(raw.get("engine_status") or "INCOMPLETE")
            ),
            "milestone_reached": milestone_reached,
            "boundary_reached": boundary_reached,
            "wall_seconds": float(
                raw.get("milestone_wall_sec")
                or raw.get("backend_solve_wall_sec") or 0.0
            ),
            "cap_seconds": float(task["cap_seconds"]),
            "correctness_redlines": _frontier_redlines(task, raw, frontier),
            "metadata": {
                "scale": int(context["scale"]),
                "instance_hash": context["instance_content_hash"],
                "state_hash": context["state_hash"],
                "decision_boundary": task["decision_boundary"],
            },
            "frontier_telemetry": frontier,
            "raw_path": str(path),
            "raw_sha256": sha256(path),
        })
    return rows


def _graph_determinism_redlines(rows: list[dict]) -> list[str]:
    hashes: dict[tuple[str, int, int], set[str]] = defaultdict(set)
    expected: dict[tuple[str, int], set[int]] = defaultdict(set)
    for row in rows:
        boundary = row["decision_boundary"]
        if boundary is None or not row["boundary_reached"]:
            continue
        expected[(row["context_id"], int(boundary))].update(
            map(int, row["observation_boundaries"])
        )
        for snapshot in row["frontier_telemetry"].get("snapshots") or ():
            hashes[(
                row["context_id"], int(boundary),
                int(snapshot.get("boundary") or 0),
            )].add(str(snapshot.get("graph_hash") or ""))
    redlines = []
    for (context_id, decision), observations in expected.items():
        for observation in observations:
            values = hashes.get((context_id, decision, observation), set())
            if len(values) != 1 or "" in values:
                redlines.append(
                    f"nondeterministic_graph:{context_id}:{decision}:{observation}"
                )
    return sorted(redlines)


def _pair(rows: list[dict], left: str, right: str) -> dict[str, dict]:
    selected = []
    for row in rows:
        if row["arm"] not in {left, right}:
            continue
        copied = dict(row)
        copied["arm"] = "QPF0" if row["arm"] == left else "QPD1"
        selected.append(copied)
    return {row["context_id"]: row for row in collapse_matched_blocks(selected)}


def _boundary_rows(rows: list[dict], scale: int, boundary: int) -> list[dict]:
    scale_rows = [row for row in rows if int(row["metadata"]["scale"]) == scale]
    qpf0 = f"QPF0_B{boundary}"
    qpd1 = f"QPD1_B{boundary}"
    overhead = _pair(scale_rows, "Q0", qpf0)
    switch = _pair(scale_rows, qpf0, qpd1)
    net = _pair(scale_rows, "Q0", qpd1)
    output = []
    for context_id in sorted(set(overhead) | set(switch) | set(net)):
        probe = overhead.get(context_id, {})
        switched = switch.get(context_id, {})
        direct = net.get(context_id, {})
        determined = all(
            row.get("determined") for row in (probe, switched, direct)
        )
        metadata = direct.get("metadata") or switched.get("metadata") or probe.get("metadata") or {}
        output.append({
            "context_id": context_id,
            "scale": scale,
            "instance_hash": metadata.get("instance_hash"),
            "decision_boundary": boundary,
            "determined": determined,
            "probe_ratio": probe.get("ratio") if probe.get("determined") else None,
            "switch_ratio": switched.get("ratio") if switched.get("determined") else None,
            "net_ratio": direct.get("ratio") if direct.get("determined") else None,
            "resource_censor_positive": any(
                bool(row.get("resource_censor_positive"))
                for row in (probe, switched, direct)
            ),
            "correctness_redlines": sorted({
                value for row in (probe, switched, direct)
                for value in row.get("correctness_redlines", ())
            }),
        })
    return output


def _metrics(rows: list[dict]) -> dict:
    determined = [row for row in rows if row["determined"]]
    net = [float(row["net_ratio"]) for row in determined]
    probe = [float(row["probe_ratio"]) for row in determined]
    return {
        "contexts": len(rows),
        "determined_contexts": len(determined),
        "determined_instances": len({row["instance_hash"] for row in determined}),
        "probe_overhead_gm": geometric_mean(probe) if probe else None,
        "probe_overhead_worst_ratio": max(probe) if probe else None,
        "fixed_qpd1_net_gm": geometric_mean(net) if net else None,
        "net_oracle_gm": (
            geometric_mean(min(1.0, value) for value in net) if net else None
        ),
        "qpd1_winner_instances": sum(value < 1.0 for value in net),
        "strong_benefit_instances": sum(value <= 0.95 for value in net),
        "benefit_instances": sum(value <= 0.98 for value in net),
        "neutral_or_harm_instances": sum(value > 0.98 for value in net),
        "harm_instances": sum(value >= 1.05 for value in net),
        "resource_censor_contexts": sum(
            bool(row["resource_censor_positive"]) for row in rows
        ),
    }


def _gate(config: dict, collapsed: list[dict]) -> dict:
    by_boundary = {
        str(scale): {
            str(boundary): _metrics([
                row for row in collapsed
                if int(row["scale"]) == scale
                and int(row["decision_boundary"]) == boundary
            ])
            for boundary in config["decision_boundaries"][str(scale)]
        } for scale in (30, 50)
    }
    overhead_gate = config["probe_overhead_gate"]
    failures = []
    passing: dict[str, list[int]] = {"30": [], "50": []}
    for scale in (30, 50):
        for boundary in config["decision_boundaries"][str(scale)]:
            metrics = by_boundary[str(scale)][str(boundary)]
            if (
                metrics["probe_overhead_gm"] is None
                or metrics["probe_overhead_gm"] > overhead_gate["gm_at_most"]
                or metrics["probe_overhead_worst_ratio"]
                    > overhead_gate["worst_ratio_at_most"]
            ):
                continue
            gate = (
                config["scale30_gate"] if scale == 30
                else config["scale50_boundary_gate"]
            )
            valid = (
                metrics["determined_instances"] >= gate["minimum_determined_instances"]
                and metrics["qpd1_winner_instances"]
                    >= gate["minimum_qpd1_winner_instances"]
                and metrics["net_oracle_gm"] <= gate["net_oracle_gm_at_most"]
                and metrics["resource_censor_contexts"] == 0
            )
            if scale == 30:
                valid = valid and (
                    metrics["fixed_qpd1_net_gm"]
                    <= gate["fixed_qpd1_net_gm_at_most"]
                )
            else:
                valid = valid and (
                    metrics["strong_benefit_instances"]
                        >= gate["minimum_strong_benefit_instances"]
                    and metrics["neutral_or_harm_instances"]
                        >= gate["minimum_neutral_or_harm_instances"]
                )
            if valid:
                passing[str(scale)].append(boundary)
    if not passing["30"]:
        failures.append("scale30:no_4096_qd1_headroom")
    if not passing["50"]:
        failures.append("scale50:no_late_switch_boundary_headroom")
    selected_scale50 = None
    if passing["50"]:
        selected_scale50 = min(
            passing["50"],
            key=lambda boundary: (
                by_boundary["50"][str(boundary)]["net_oracle_gm"], boundary,
            ),
        )
    reason = None
    if failures:
        reason = (
            "NO_SCALE50_LATE_SWITCH_ORACLE_HEADROOM"
            if any(value.startswith("scale50") for value in failures)
            else "NO_SCALE30_QD1_HEADROOM"
        )
    return {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_oracle_decision.v1"
        ),
        "decision": "FAIL" if failures else "PASS",
        "reason": reason,
        "failures": failures,
        "boundary_metrics": by_boundary,
        "passing_boundaries": passing,
        "selected_scale30_boundary": 4096 if passing["30"] else None,
        "selected_scale50_boundary": selected_scale50,
        "candidate_training_authorized_in_this_chain": False,
        "fresh_new_instance_temporal_gat_chain_authorized_next": not failures,
        "correctness_redline_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--task-limit", type=int)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    assert_active(
        run_root, "LATE_SWITCH_MATRIX", performance=True,
    )
    config = load(run_root / "config.freeze.json")
    corpus = load(run_root / "pilot_corpus.freeze.json")
    schedule = load(run_root / "late_switch.execution.freeze.json")
    by_context = {row["context_id"]: row for row in corpus["rows"]}
    raw_dir = run_root / "late_switch_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    completed = 0
    for task in schedule["tasks"]:
        output = raw_dir / _task_name(task)
        if output.is_file():
            continue
        if args.task_limit is not None and completed >= args.task_limit:
            break
        _run_task(run_root, config, by_context[task["context_id"]], task, output)
        completed += 1
    missing = [
        task for task in schedule["tasks"]
        if not (raw_dir / _task_name(task)).is_file()
    ]
    if missing:
        print(json.dumps({
            "status": "PARTIAL",
            "completed_this_call": completed,
            "remaining_tasks": len(missing),
        }, indent=2))
        return 0

    raw_rows = _raw_rows(schedule, raw_dir, by_context)
    redlines = sorted({
        value for row in raw_rows for value in row["correctness_redlines"]
    } | set(_graph_determinism_redlines(raw_rows)))
    if redlines:
        write_terminal(
            run_root, "V10_TEMPORAL_FRONTIER_CORRECTNESS_REDLINE",
            "LATE_SWITCH_MATRIX", {"redlines": redlines},
        )
        raise SystemExit("V10 temporal frontier correctness redline")
    write_once(run_root / "late_switch.rows.json", {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_raw_matrix.v1"
        ),
        "single_native_process": True,
        "rows": raw_rows,
    })
    collapsed = []
    for scale in (30, 50):
        for boundary in config["decision_boundaries"][str(scale)]:
            collapsed.extend(_boundary_rows(raw_rows, scale, int(boundary)))
    write_once(run_root / "late_switch.collapsed.json", {
        "schema_version": (
            "lunar_ice_bpc.p0v5_temporal_frontier_collapsed.v1"
        ),
        "rows": collapsed,
    })
    decision = _gate(config, collapsed)
    write_once(run_root / "late_switch_oracle.decision.json", decision)
    if decision["decision"] == "FAIL":
        write_terminal(
            run_root, decision["reason"], "LATE_SWITCH_MATRIX", decision,
        )
    else:
        write_once(run_root / "temporal_gat_next_chain.authorization.json", {
            "schema_version": (
                "lunar_ice_bpc.p0v5_temporal_gat_next_chain_authorization.v1"
            ),
            "decision": "AUTHORIZED_FOR_FRESH_NEW_INSTANCE_PILOT",
            "selected_scale30_boundary": decision[
                "selected_scale30_boundary"
            ],
            "selected_scale50_boundary": decision[
                "selected_scale50_boundary"
            ],
            "this_chain_diagnostic_only": True,
            "candidate_training_in_this_chain": False,
            "deployment_authorized": False,
            "production_switch_authorized": False,
        })
        update_state(
            run_root, "COMPLETE", status="PASS",
            advancement="temporal_gat_next_chain.authorization.json",
        )
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

