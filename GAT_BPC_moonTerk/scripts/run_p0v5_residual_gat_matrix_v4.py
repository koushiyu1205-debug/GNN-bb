#!/usr/bin/env python3
"""Run V4 milestone/trace first, then only replay-eligible QD1 blocks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
from lunar_ice_bpc.guidance.context_queue_portfolio_gates import (  # noqa: E402
    rotate_blocked_arm_order,
)
import scripts.run_p0v5_context_queue_portfolio_matrix as base  # noqa: E402


DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_residual_gat_censor_aware_selector_v4_20260815"
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
FINALIZER = ROOT / "scripts/finalize_p0v5_residual_gat_stage_v4.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("milestone", "matrix"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify(run_root)
    _assert_active(run_root)
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    by_context = {row["context_id"]: row for row in corpus["rows"]}
    if args.mode == "milestone":
        schedule_path = run_root / "q0_milestone_execution.freeze.json"
    else:
        schedule_path = run_root / "matched_qd1_execution.freeze.json"
        if not schedule_path.is_file():
            raise SystemExit("V4 QD1 schedule is not frozen after milestone screen")
    schedule = _load(schedule_path)
    raw_dir = run_root / ("q0_milestone_raw" if args.mode == "milestone" else "matched_qd1_raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    milestone_registry = (
        None if args.mode == "milestone" else _load(run_root / "q0_milestone.freeze.json")
    )
    for task in schedule["tasks"]:
        context = by_context[str(task["context_id"])]
        arm = str(task["arm"])
        suffix = "milestone" if args.mode == "milestone" else f"b{task['block']}_{task['ordinal_in_block']}"
        raw_path = raw_dir / f"{task['context_id']}_{suffix}_{arm}.json"
        if not raw_path.is_file():
            command = [
                sys.executable, str(REPLAY), "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]), "--output", str(raw_path),
                "--policy", arm, "--repeat-index",
                str(0 if args.mode == "milestone" else int(task["block"]) + 1),
                "--wall-time-limit-sec", str(task["cap_sec"]),
                "--memory-limit-gb", str(task["memory_limit_gb"]),
            ]
            _run(command, config)
        raw = _load(raw_path)
        base._validate_raw_binding(raw, task, context)
        if args.mode == "milestone":
            rows.append(_milestone_row(task, context, raw, raw_path))
        else:
            target = milestone_registry["by_context"][str(task["context_id"])]
            rows.append(base._matrix_row(task, context, raw, raw_path, target))
    if args.mode == "milestone":
        payload = {
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_q0_milestone_freeze.v4",
            "status": "FROZEN_BEFORE_ANY_V4_ARM_OUTCOME",
            "source_schedule_sha256": _sha256(schedule_path),
            "by_context": {row["context_id"]: row for row in rows},
        }
        _write_once(run_root / "q0_milestone.freeze.json", payload)
        trace_rows = _collect_training_traces(
            run_root, config, rows, by_context
        )
        _write_trace_corpus(run_root, corpus, trace_rows)
        _freeze_qd1_schedule(run_root, config, rows)
        _update_state(run_root, "QD1_FRESH_MATCHED_MATRIX", "READY")
    else:
        base._add_cross_arm_redlines(rows)
        payload = {
            "schema_version": "lunar_ice_bpc.p0v5_censor_aware_matched_rows.v1",
            "source_schedule_sha256": _sha256(schedule_path), "rows": rows,
        }
        output = run_root / "matched_qd1_rows.json"
        _write_once(output, payload)
        completed = subprocess.run([
            sys.executable, str(FINALIZER), "qd1", "--run-root", str(run_root),
            "--matrix", str(output),
        ], cwd=ROOT, check=False)
        return int(completed.returncode)
    print(json.dumps({
        "mode": args.mode, "task_count": len(rows), "single_native_process": True,
        "replay_eligible_contexts": sum(row.get("replay_eligible", False) for row in rows),
    }, ensure_ascii=False, indent=2))
    return 0


def _milestone_row(task, context, raw, raw_path):
    status = str(raw.get("engine_status") or "")
    reached = bool(raw.get("milestone_reached"))
    labels_dropped = bool(raw.get("labels_dropped"))
    replay_eligible = bool(reached and status not in {"TIMEOUT", "MEMORY_LIMIT"} and not labels_dropped)
    return {
        "context_id": task["context_id"],
        "instance_hash": context["instance_content_hash"],
        "scale": context["scale"], "partition": context["partition"],
        "state_hash": context["state_hash"],
        "target_milestone_kind": str(raw.get("milestone_kind") or "") if reached else None,
        "q0_milestone_reached": reached, "q0_status": status,
        "q0_wall_sec": float(raw.get("milestone_wall_sec") or 0.0),
        "labels_dropped": labels_dropped, "replay_eligible": replay_eligible,
        "replay_ineligible_reason": None if replay_eligible else (
            "Q0_MILESTONE_NOT_REACHED" if not reached else
            "Q0_RESOURCE_CENSORED" if status in {"TIMEOUT", "MEMORY_LIMIT"} else
            "Q0_LABEL_DROP"
        ),
        "trace_requested": False,
        "trace_incomplete": False,
        "trace_complete": False,
        "trace_sampling_mode": None, "trace_final_rows": 0,
        "q0_screen_path": str(raw_path), "q0_screen_sha256": _sha256(raw_path),
    }


def _collect_training_traces(run_root, config, milestone_rows, by_context):
    eligible = [
        row for row in milestone_rows
        if row["partition"] == "train" and row["replay_eligible"]
    ]
    schedule_path = run_root / "qgr1_q0_trace_execution.freeze.json"
    _write_once(schedule_path, {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_stratified_trace_execution.v4",
        "status": "FROZEN_AFTER_Q0_SCREEN_BEFORE_TRACE_COLLECTION",
        "literal_q0_only": True, "performance_authority": False,
        "single_native_process": True,
        "tasks": [{
            "context_id": row["context_id"], "instance_hash": row["instance_hash"],
            "scale": row["scale"], "partition": "train",
            "state_hash": row["state_hash"], "arm": "Q0", "execution_policy": "Q0",
            "cap_sec": config["execution"]["replay_caps_sec"][str(row["scale"])],
            "memory_limit_gb": config["execution"]["memory_limit_gb"],
        } for row in eligible],
    })
    raw_dir = run_root / "qgr1_q0_trace_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    result = []
    for task in _load(schedule_path)["tasks"]:
        context = by_context[str(task["context_id"])]
        target = next(row for row in eligible if row["context_id"] == task["context_id"])
        raw_path = raw_dir / f"{task['context_id']}_Q0_trace.json"
        if not raw_path.is_file():
            command = [
                sys.executable, str(REPLAY), "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]), "--output", str(raw_path),
                "--policy", "Q0", "--repeat-index", "0",
                "--wall-time-limit-sec", str(task["cap_sec"]),
                "--memory-limit-gb", str(task["memory_limit_gb"]),
                "--label-trace", "--label-trace-max-rows", "100000",
                "--label-trace-sampling-mode", "qgr1_stratified_reservoir_v1",
                "--preference-cap-per-family", "12500",
                "--surface-reservoir-count", "3125",
                "--surface-labels-per-bucket", "8",
                "--witness-route-cap", "512",
                "--witness-ancestor-cap", "25000",
                "--guidance-bucket-width", "0.0001",
            ]
            _run(command, config)
        raw = _load(raw_path)
        base._validate_raw_binding(raw, task, context)
        telemetry = dict(raw.get("proof_telemetry") or {})
        reached = bool(
            raw.get("milestone_reached")
            and raw.get("milestone_kind") == target["target_milestone_kind"]
        )
        incomplete = bool(
            telemetry.get("proof_queue_label_trace_incomplete")
            or telemetry.get("proof_queue_label_trace_truncated")
        )
        result.append({
            "context_id": task["context_id"], "instance_hash": task["instance_hash"],
            "scale": task["scale"], "state_hash": task["state_hash"],
            "trace_complete": bool(reached and not incomplete),
            "trace_incomplete": incomplete, "milestone_reached": reached,
            "trace_sampling_mode": telemetry.get("proof_queue_label_trace_sampling_mode"),
            "trace_final_rows": int(telemetry.get("proof_queue_label_trace_final_rows") or 0),
            "q0_trace_path": str(raw_path), "q0_trace_sha256": _sha256(raw_path),
        })
    return result


def _write_trace_corpus(run_root, corpus, trace_rows):
    by_context = {row["context_id"]: row for row in trace_rows}
    sources = []
    for context in corpus["rows"]:
        if context["partition"] != "train":
            continue
        trace = by_context.get(context["context_id"])
        if not trace or not trace["trace_complete"]:
            continue
        sources.append({
            "instance_hash": context["instance_content_hash"], "scale": context["scale"],
            "partition": "train", "state_hash": context["state_hash"],
            "instance_path": context["instance_path"],
            "instance_sha256": _sha256(context["instance_path"]),
            "snapshot_path": context["snapshot_path"],
            "snapshot_sha256": context["snapshot_sha256"],
            "q0_trace_path": trace["q0_trace_path"],
            "q0_trace_sha256": trace["q0_trace_sha256"],
            "trace_sampling_mode": trace["trace_sampling_mode"],
            "trace_final_rows": trace["trace_final_rows"],
        })
    _write_once(run_root / "qgr1_q0_trace_corpus.freeze.json", {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_stratified_trace_corpus.v4",
        "literal_q0_future_trace_only": True, "performance_outcomes_used": False,
        "trace_incomplete_contexts_excluded": True, "rows": sources,
    })


def _freeze_qd1_schedule(run_root, config, milestone_rows):
    tasks = []
    for row in milestone_rows:
        if not row["replay_eligible"]:
            continue
        common = {
            "context_id": row["context_id"], "instance_hash": row["instance_hash"],
            "scale": row["scale"], "partition": row["partition"],
            "state_hash": row["state_hash"],
            "cap_sec": config["execution"]["replay_caps_sec"][str(row["scale"])],
            "memory_limit_gb": config["execution"]["memory_limit_gb"],
        }
        for block, order in enumerate(rotate_blocked_arm_order(
            row["state_hash"], arms=("Q0", "QD1"), repeats=3
        )):
            for ordinal, arm in enumerate(order):
                tasks.append({**common, "arm": arm, "execution_policy": arm,
                              "block": block, "ordinal_in_block": ordinal})
    schedule = {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_qd1_execution.v4",
        "status": "FROZEN_AFTER_Q0_SCREEN_BEFORE_ANY_NON_Q0_ARM",
        "mode": "qd1_fresh", "single_native_process": True,
        "q0_milestone_sha256": _sha256(run_root / "q0_milestone.freeze.json"),
        "tasks": tasks,
    }
    _write_once(run_root / "matched_qd1_execution.freeze.json", schedule)
    _write_once(run_root / "arm_execution.freeze.registry.json", {
        "schema_version": "lunar_ice_bpc.p0v5_residual_gat_arm_execution_registry.v4",
        "frozen_before_non_q0_outcome": True,
        "artifact_sha256": {
            "q0_milestone.freeze.json": _sha256(run_root / "q0_milestone.freeze.json"),
            "qgr1_q0_trace_corpus.freeze.json": _sha256(
                run_root / "qgr1_q0_trace_corpus.freeze.json"
            ),
            "qgr1_q0_trace_execution.freeze.json": _sha256(
                run_root / "qgr1_q0_trace_execution.freeze.json"
            ),
            "matched_qd1_execution.freeze.json": _sha256(
                run_root / "matched_qd1_execution.freeze.json"
            ),
        },
    })


def _run(command, config):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((
        str((ROOT / config["native_build_dir"]).resolve()), str((ROOT / "src").resolve())
    ))
    for key in tuple(environment):
        if (
            key.startswith("LUNAR_ICE_P0V5_")
            or key.startswith("LUNAR_ICE_PROOF_TAIL_GAT")
            or key.startswith("LUNAR_ICE_GAT_")
        ):
            environment.pop(key, None)
    completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"fresh V4 replay failed:{completed.returncode}")


def _verify(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        _terminal(run_root, "FREEZE_HASH_DRIFT", str(exc))
        raise SystemExit(str(exc)) from exc


def _assert_active(run_root):
    if bool(_load(run_root / "state.json").get("terminal")):
        raise SystemExit("terminal V4 chain forbids replay writer")


def _update_state(run_root, stage, status):
    path = run_root / "state.json"
    payload = _load(path)
    payload.update({"current_stage": stage, "status": status})
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2,
                               sort_keys=True) + "\n", encoding="utf-8")


def _terminal(run_root, reason, detail):
    path = run_root / "terminal_decision.json"
    if not path.exists():
        path.write_text(json.dumps({
            "schema_version": "lunar_ice_bpc.p0v5_residual_gat_terminal.v4",
            "decision": "FAIL", "reason": reason, "detail": detail,
            "development_only": True, "deployment_authorized": False,
            "production_switch_authorized": False,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write_once(path, payload):
    path = Path(path)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != encoded:
        raise SystemExit(f"immutable V4 execution artifact drift:{path}")
    if not path.exists():
        path.write_text(encoded, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
