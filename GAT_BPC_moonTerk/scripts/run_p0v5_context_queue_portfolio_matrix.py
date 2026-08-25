#!/usr/bin/env python3
"""Execute one portfolio replay task at a time and emit canonical rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lunar_ice_bpc.guidance.context_queue_portfolio_freeze import (  # noqa: E402
    verify_portfolio_freezes,
)
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
DEFAULT_RUN_ROOT = ROOT / "runs/p0v5_context_queue_portfolio_v1_20260807_r1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("milestone", "matrix"))
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--schedule", type=Path)
    parser.add_argument("--potential-index", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--raw-dir", type=Path)
    args = parser.parse_args()
    run_root = args.run_root.resolve()
    _verify_freezes(run_root)
    config = _load(run_root / "config.freeze.json")
    corpus = _load(run_root / "corpus.freeze.json")
    by_context = {row["context_id"]: row for row in corpus["rows"]}
    schedule_path = (
        args.schedule.resolve() if args.schedule else run_root / (
            "q0_milestone_execution.freeze.json"
            if args.mode == "milestone"
            else "matched_qd1_qb1_execution.freeze.json"
        )
    )
    schedule = _load(schedule_path)
    expected_schema = (
        "lunar_ice_bpc.p0v5_context_queue_portfolio_q0_milestone_execution.v1"
        if args.mode == "milestone"
        else "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_execution.v1"
    )
    if schedule.get("schema_version") != expected_schema:
        raise SystemExit("execution schedule schema mismatch")
    milestone_registry = None
    if args.mode == "matrix":
        milestone_registry = _load(run_root / "q0_milestone.freeze.json")
        if milestone_registry.get("source_schedule_sha256") != _sha256(
            run_root / "q0_milestone_execution.freeze.json"
        ):
            raise SystemExit("Q0 milestone registry binding drift")
    potential_index = (
        {} if args.potential_index is None
        else dict(_load(args.potential_index.resolve()).get("by_state_hash") or {})
    )
    raw_dir = (
        args.raw_dir.resolve() if args.raw_dir else run_root /
        (
            "q0_milestone_raw"
            if args.mode == "milestone"
            else f"{schedule_path.stem}_raw"
        )
    )
    raw_dir.mkdir(parents=True, exist_ok=True)
    canonical = []
    for task in schedule["tasks"]:
        context = by_context[str(task["context_id"])]
        arm = str(task["arm"])
        execution_policy = str(task.get("execution_policy") or arm)
        suffix = (
            "milestone" if args.mode == "milestone"
            else f"b{int(task['block'])}_{int(task['ordinal_in_block'])}"
        )
        raw_path = raw_dir / f"{task['context_id']}_{suffix}_{arm}.json"
        if not raw_path.is_file():
            command = [
                sys.executable, str(REPLAY),
                "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]),
                "--output", str(raw_path),
                "--policy", execution_policy,
                "--repeat-index", str(
                    0 if args.mode == "milestone" else int(task["block"]) + 1
                ),
                "--wall-time-limit-sec", str(task["cap_sec"]),
                "--memory-limit-gb", str(task["memory_limit_gb"]),
            ]
            if args.mode == "milestone" and context["partition"] == "train":
                command.extend([
                    "--label-trace", "--label-trace-max-rows", "50000",
                    # Q0 ordering ignores this value; freezing it here makes
                    # the trace buckets identical to QGR1's action surface.
                    "--guidance-bucket-width", "0.0001",
                ])
            if execution_policy == "QGR1":
                potential = potential_index.get(str(task["state_hash"]))
                if not potential:
                    raise SystemExit(f"QGR1 potential missing for {task['state_hash']}")
                command.extend([
                    "--potential", str(Path(potential).resolve()),
                    "--guidance-bucket-width", "0.0001",
                ])
            _run_one(command, config)
        raw = _load(raw_path)
        _validate_raw_binding(raw, task, context)
        if args.mode == "milestone":
            canonical.append(_milestone_row(task, context, raw, raw_path))
        else:
            target = dict(milestone_registry["by_context"])[str(task["context_id"])]
            canonical.append(_matrix_row(task, context, raw, raw_path, target))
    if args.mode == "milestone":
        payload = {
            "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_q0_milestone_freeze.v1",
            "status": "FROZEN_BEFORE_ANY_MATCHED_ARM_OUTCOME",
            "source_schedule": str(schedule_path),
            "source_schedule_sha256": _sha256(schedule_path),
            "by_context": {row["context_id"]: row for row in canonical},
        }
        _write_once(run_root / "q0_milestone.freeze.json", payload)
        _write_trace_corpus(run_root, corpus, canonical)
        _update_state(run_root, "QD1_QB1_MATCHED_MATRIX", "READY")
    else:
        _add_cross_arm_redlines(canonical)
        payload = {
            "schema_version": "lunar_ice_bpc.p0v5_context_queue_portfolio_matched_rows.v1",
            "source_schedule": str(schedule_path),
            "source_schedule_sha256": _sha256(schedule_path),
            "rows": canonical,
        }
        if str(schedule.get("mode") or "") == "selector_heldout":
            payload["preparation_p99_ms_by_scale"] = {
                str(scale): _percentile([
                    1000.0 * float(task.get("preparation_wall_sec") or 0.0)
                    for task in schedule["tasks"]
                    if int(task["scale"]) == scale and str(task["arm"]) != "Q0"
                ], 0.99)
                for scale in (30, 50)
            }
        output = (
            args.output.resolve() if args.output
            else run_root / "matched_matrix_rows.json"
        )
        _write_once(output, payload)
        next_stage = {
            "qgr1_force_on": "QGR1_FORCE_ON_DECISION",
            "qgr1_supplement": "PORTFOLIO_ORACLE",
            "selector_heldout": "HELDOUT_DECISION",
        }.get(str(schedule.get("mode") or ""), "ARM_ADMISSION")
        _update_state(run_root, next_stage, "READY")
    print(json.dumps({
        "mode": args.mode, "task_count": len(canonical),
        "single_native_process": True,
    }, ensure_ascii=False, indent=2))
    return 0


def _run_one(command, config):
    environment = dict(os.environ)
    native = str((ROOT / config["native_build_dir"]).resolve())
    source = str((ROOT / "src").resolve())
    inherited = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        value for value in (native, source, inherited) if value
    )
    for key in tuple(environment):
        if (
            key.startswith("LUNAR_ICE_P0V5_")
            or key.startswith("LUNAR_ICE_PROOF_TAIL_GAT")
            or key.startswith("LUNAR_ICE_GAT_")
        ):
            environment.pop(key, None)
    completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    if completed.returncode != 0:
        raise SystemExit(f"fresh replay failed with code {completed.returncode}")


def _milestone_row(task, context, raw, raw_path):
    target_kind = (
        str(raw["milestone_kind"])
        if bool(raw["milestone_reached"])
        else "ANY_VALID_TERMINAL_MILESTONE"
    )
    return {
        "context_id": task["context_id"],
        "instance_hash": context["instance_content_hash"],
        "scale": context["scale"],
        "partition": context["partition"],
        "state_hash": context["state_hash"],
        "target_milestone_kind": target_kind,
        "q0_milestone_reached": bool(raw["milestone_reached"]),
        "q0_status": str(raw["engine_status"]),
        "q0_wall_sec": float(raw["milestone_wall_sec"]),
        "q0_trace_path": str(raw_path),
        "q0_trace_sha256": _sha256(raw_path),
    }


def _matrix_row(task, context, raw, raw_path, target):
    target_kind = str(target["target_milestone_kind"])
    reached = bool(
        raw["milestone_reached"]
        and (
            raw["milestone_kind"] == target_kind
            or target_kind == "ANY_VALID_TERMINAL_MILESTONE"
        )
    )
    engine_status = str(raw["engine_status"])
    status = "COMPLETED" if reached else (
        engine_status if engine_status in {"TIMEOUT", "MEMORY_LIMIT"} else "CENSORED"
    )
    redlines = _correctness_redlines(raw, context)
    telemetry = dict(raw.get("proof_telemetry") or {})
    preparation_wall = float(task.get("preparation_wall_sec") or 0.0)
    return {
        "context_id": task["context_id"],
        "instance_hash": context["instance_content_hash"],
        "scale": context["scale"],
        "partition": context["partition"],
        "state_hash": context["state_hash"],
        "arm": str(task["arm"]),
        "repeat": int(task["block"]),
        "block": int(task["block"]),
        "ordinal_in_block": int(task["ordinal_in_block"]),
        "status": status,
        "wall_sec": float(raw["milestone_wall_sec"]) + preparation_wall,
        "solver_wall_sec": float(raw["milestone_wall_sec"]),
        "preparation_wall_sec": preparation_wall,
        "execution_policy": str(task.get("execution_policy") or task["arm"]),
        "selected_action": task.get("selected_action"),
        "target_milestone_kind": target_kind,
        "observed_milestone_kind": str(raw["milestone_kind"]),
        "milestone_reached": reached,
        "fresh_process": True,
        "correctness_audit_complete": True,
        "correctness_redlines": redlines,
        "search_exhaustive": bool(raw.get("search_exhaustive")),
        "frontier_empty": bool(raw.get("frontier_empty")),
        "labels_dropped": bool(raw.get("labels_dropped")),
        "global_min_rc": raw.get("global_min_rc"),
        "global_min_rc_is_exact": bool(raw.get("global_min_rc_is_exact")),
        "proved_no_rc_below": raw.get("proved_no_rc_below"),
        "certificate_blockers": list(raw.get("certificate_blockers") or ()),
        "processed_labels": int(telemetry.get("processed_labels") or 0),
        "dominance_candidate_checks": int(
            telemetry.get("dominance_candidate_checks") or 0
        ),
        "dominance_wall_sec": float(
            telemetry.get("dominance_wall_time_seconds") or 0.0
        ),
        "max_visited_bucket_size": int(
            telemetry.get("max_visited_bucket_size") or 0
        ),
        "ordering_decisions": int(
            telemetry.get("proof_queue_guidance_order_decisions") or 0
        ),
        "reordered_label_hash_count": int(
            telemetry.get("proof_queue_guidance_reordered_label_hash_count") or 0
        ),
        "covered_bucket_hash_count": int(
            telemetry.get("proof_queue_guidance_bucket_hash_count") or 0
        ),
        "guidance_scored_labels": int(
            telemetry.get("proof_queue_guidance_scored_labels") or 0
        ),
        "guidance_nonzero_labels": int(
            telemetry.get("proof_queue_guidance_nonzero_labels") or 0
        ),
        "native_scoring_wall_sec": float(
            telemetry.get("proof_queue_native_scoring_wall_time_seconds") or 0.0
        ),
        "raw_path": str(raw_path),
        "raw_sha256": _sha256(raw_path),
    }


def _correctness_redlines(raw, context):
    redlines = []
    if bool(raw.get("search_exhaustive")) and bool(raw.get("labels_dropped")):
        redlines.append("exhaustive_with_label_drop")
    if any(not bool(row.get("accepted")) for row in raw.get("route_audit") or ()):
        redlines.append("reduced_cost_mismatch")
    if str(raw.get("instance_content_hash")) != str(context["instance_content_hash"]):
        redlines.append("legal_universe_mismatch")
    telemetry = dict(raw.get("proof_telemetry") or {})
    if telemetry.get("request_bindings_match") is False:
        redlines.append("legal_universe_mismatch")
    return sorted(set(redlines))


def _add_cross_arm_redlines(rows):
    by_block = {}
    for row in rows:
        by_block.setdefault((row["context_id"], row["block"]), []).append(row)
    for block_rows in by_block.values():
        q0 = next((row for row in block_rows if row["arm"] == "Q0"), None)
        if q0 is None:
            # QGR1 supplement intentionally reuses the separately frozen Q0
            # comparator from the primary matched matrix.
            continue
        for row in block_rows:
            if row is q0:
                continue
            redlines = set(row["correctness_redlines"])
            if q0["search_exhaustive"] and row["search_exhaustive"]:
                if (
                    q0["global_min_rc_is_exact"]
                    and row["global_min_rc_is_exact"]
                    and q0["global_min_rc"] is not None
                    and row["global_min_rc"] is not None
                    and abs(float(q0["global_min_rc"]) - float(row["global_min_rc"])) > 1.0e-7
                ):
                    redlines.add("global_min_rc_mismatch")
                if (
                    q0["proved_no_rc_below"] is not None
                    and row["proved_no_rc_below"] is not None
                    and abs(float(q0["proved_no_rc_below"]) - float(row["proved_no_rc_below"])) > 1.0e-7
                ):
                    redlines.add("certificate_mismatch")
                if bool(q0["certificate_blockers"]) != bool(row["certificate_blockers"]):
                    redlines.add("certificate_mismatch")
            row["correctness_redlines"] = sorted(redlines)
            if redlines:
                row["correctness_audit_complete"] = False


def _validate_raw_binding(raw, task, context):
    if (
        str(raw.get("source_state_hash")) != str(task["state_hash"])
        or str(raw.get("instance_content_hash")) != str(context["instance_content_hash"])
        or str(raw.get("policy")) != str(task.get("execution_policy") or task["arm"])
        or not bool(raw.get("fresh_process_arm"))
    ):
        raise SystemExit("fresh replay output binding mismatch")


def _write_trace_corpus(run_root, corpus, rows):
    by_context = {row["context_id"]: row for row in rows}
    sources = []
    for context in corpus["rows"]:
        if context["partition"] != "train":
            continue
        milestone = by_context.get(context["context_id"])
        if not milestone:
            continue
        trace_path = Path(milestone["q0_trace_path"])
        trace = _load(trace_path)
        telemetry = dict(trace.get("proof_telemetry") or {})
        if bool(telemetry.get("proof_queue_label_trace_truncated")):
            continue
        sources.append({
            "instance_hash": context["instance_content_hash"],
            "scale": context["scale"],
            "partition": "train",
            "state_hash": context["state_hash"],
            "instance_path": context["instance_path"],
            "instance_sha256": _sha256(Path(context["instance_path"])),
            "snapshot_path": context["snapshot_path"],
            "snapshot_sha256": context["snapshot_sha256"],
            "q0_trace_path": str(trace_path),
            "q0_trace_sha256": _sha256(trace_path),
        })
    payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qgr1_q0_trace_corpus.v1",
        "literal_q0_future_trace_only": True,
        "performance_outcomes_used": False,
        "formal_benchmark_instances_used": False,
        "diagnostic_only_outcomes_used": False,
        "rows": sources,
    }
    _write_once(run_root / "qgr1_q0_trace_corpus.freeze.json", payload)


def _verify_freezes(run_root):
    try:
        verify_portfolio_freezes(run_root, ROOT)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc


def _update_state(run_root, stage, status):
    path = run_root / "state.json"
    payload = _load(path)
    if bool(payload.get("terminal")):
        raise SystemExit("experiment chain is already terminal")
    payload.update({"current_stage": stage, "status": status})
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_once(path, payload):
    path = Path(path)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") != text:
        raise SystemExit(f"immutable execution artifact drift:{path}")
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _percentile(values, quantile):
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    position = max(0.0, min(1.0, float(quantile))) * (len(ordered) - 1)
    low = int(position)
    high = min(len(ordered) - 1, low + 1)
    fraction = position - low
    return ordered[low] * (1.0 - fraction) + ordered[high] * fraction


if __name__ == "__main__":
    raise SystemExit(main())
