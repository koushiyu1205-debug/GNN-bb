#!/usr/bin/env python3
"""Collect clean blocked Q0/QD1/QB1 outcomes for the V4 selector."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SPLIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_realmap_v4_instance_split.v1"
REPLAY_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
REPORT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_realmap_v4_matched_arms.v1"
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
ARMS = ("QD1", "QB1")
GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_MANIFEST",
    "LUNAR_ICE_P0V5_QG2_V3_SELECTOR_EVALUATION_MODE",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--instance-split", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--maximum-contexts-per-scale", type=int, default=0)
    parser.add_argument("--scale30-wall-sec", type=float, default=300.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=600.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    args = parser.parse_args()

    oracle_path = _resolve(args.oracle_summary)
    split_path = _resolve(args.instance_split)
    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    oracle = _load(oracle_path)
    split = _load(split_path)
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        raise SystemExit("V4 matched-arm Oracle schema mismatch")
    if split.get("schema_version") != SPLIT_SCHEMA or not bool(
        split.get("frozen_before_matched_outcomes")
    ):
        raise SystemExit("V4 matched-arm split is not pre-outcome frozen")
    assignments = dict(split.get("assignments") or {})
    contexts = _contexts(
        oracle, assignments,
        maximum_per_scale=max(0, int(args.maximum_contexts_per_scale)),
    )
    if not contexts:
        raise SystemExit("V4 matched-arm collection has no contexts")
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "matched_arm_records.jsonl"
    records = _existing(records_path)
    repeats = max(3, int(args.repeats))
    bucket = float(oracle["frozen_guidance_bucket_width"])
    env = _environment(_resolve(args.native_build_dir))

    for context_index, context in enumerate(contexts):
        state = str(context["state_hash"])
        if state in records:
            continue
        scale = int(context["scale"])
        wall = (
            float(args.scale30_wall_sec)
            if scale == 30 else float(args.scale50_wall_sec)
        )
        context_dir = output_dir / f"scale{scale}" / state[:16]
        context_dir.mkdir(parents=True, exist_ok=True)
        repeat_rows = []
        for repeat in range(1, repeats + 1):
            order = ["Q0", *ARMS]
            random.Random(20260806 + context_index * 1009 + repeat).shuffle(order)
            outputs = {}
            paths = {}
            for arm in order:
                target = context_dir / f"{arm.lower()}_rep{repeat}.json"
                paths[arm] = str(target)
                if not target.exists():
                    _run([
                        sys.executable, str(REPLAY),
                        "--instance", str(context["instance_path"]),
                        "--snapshot", str(context["snapshot_path"]),
                        "--output", str(target),
                        "--policy", arm,
                        "--repeat-index", str(repeat),
                        "--wall-time-limit-sec", str(wall),
                        "--memory-limit-gb", str(float(args.memory_limit_gb)),
                        "--guidance-bucket-width", str(bucket),
                        "--source-backend-id", str(
                            context.get("source_backend_id")
                            or "native_rcspp_bidirectional_root_partial_hybrid_v3"
                        ),
                    ], env=env)
                outputs[arm] = _load(target)
                _validate_replay(
                    outputs[arm], arm=arm, repeat=repeat,
                    context=context, wall=wall,
                    memory=float(args.memory_limit_gb), bucket=bucket,
                )
            repeat_rows.append({
                "repeat": repeat,
                "blocked_order": order,
                "q0_path": paths["Q0"],
                "arms": {
                    arm: _repeat_outcome(
                        outputs["Q0"], outputs[arm],
                        budget=wall, arm_path=paths[arm],
                    )
                    for arm in ARMS
                },
            })
        record = _aggregate(context, assignments, repeat_rows)
        _append(records_path, record)
        records[state] = record
        _write(output_dir / "progress.json", {
            "schema_version": "lunar_ice_bpc.p0v5_qg2_realmap_v4_matched_arms_progress.v1",
            "completed_contexts": len(records),
            "selected_contexts": len(contexts),
            "last_state_hash": state,
            "completed_by_scale": {
                str(value): sum(
                    int(row["scale"]) == value for row in records.values()
                )
                for value in (30, 50)
            },
        })
        print(json.dumps({
            "completed": len(records),
            "total": len(contexts),
            "scale": scale,
            "state": state[:16],
            "outcomes": record["outcomes"],
            "safe": record["safe"],
        }, sort_keys=True), flush=True)

    ordered = [records[str(row["state_hash"])] for row in contexts]
    report = {
        "schema_version": REPORT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "instance_split": str(split_path),
        "instance_split_sha256": _sha256(split_path),
        "repeat_count": repeats,
        "scale30_wall_sec": float(args.scale30_wall_sec),
        "scale50_wall_sec": float(args.scale50_wall_sec),
        "memory_limit_gb": float(args.memory_limit_gb),
        "guidance_bucket_width": bucket,
        "records_path": str(records_path),
        "records_path_sha256": _sha256(records_path),
        "records": ordered,
        "summary": _summary(ordered),
        "all_safe": all(bool(row["safe"]) for row in ordered),
        "training_labels_only": True,
        "deployment_authorized": False,
    }
    _write(output_path, report)
    print(json.dumps(report["summary"], sort_keys=True), flush=True)
    return 0 if report["all_safe"] else 3


def _contexts(oracle, assignments, *, maximum_per_scale):
    rows = []
    for source in oracle.get("initial_rows") or ():
        if not bool(source.get("compliant_context")) or not bool(
            source.get("all_initial_arms_safe")
        ):
            continue
        instance = str(source.get("instance_hash") or "")
        if instance not in assignments:
            raise SystemExit("V4 matched-arm context is outside frozen split")
        rows.append(dict(source))
    selected = []
    for scale in (30, 50):
        candidates = [row for row in rows if int(row["scale"]) == scale]
        candidates.sort(key=lambda row: (
            str(assignments[str(row["instance_hash"])]),
            hashlib.sha256(str(row["state_hash"]).encode()).hexdigest(),
        ))
        if maximum_per_scale:
            candidates = candidates[:maximum_per_scale]
        selected.extend(candidates)
    return selected


def _repeat_outcome(q0, arm, *, budget, arm_path):
    q0_wall = _effective_wall(q0, budget)
    arm_wall = _effective_wall(arm, budget)
    q0_reached = bool(q0.get("milestone_reached"))
    arm_reached = bool(arm.get("milestone_reached"))
    q0_kind = str(q0.get("milestone_kind") or "")
    arm_kind = str(arm.get("milestone_kind") or "")
    matched = bool(
        q0_reached and arm_reached and q0_kind == arm_kind
        and q0_kind in {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
    )
    if matched:
        comparison = "matched_milestone"
    elif q0_reached and not arm_reached:
        comparison = "arm_adverse_censor"
    elif arm_reached and not q0_reached:
        comparison = "arm_beneficial_censor"
    elif not q0_reached and not arm_reached:
        comparison = "both_censored"
    else:
        comparison = "milestone_mismatch"
    return {
        "comparison_class": comparison,
        "q0_wall_sec": q0_wall,
        "arm_wall_sec": arm_wall,
        "ratio": arm_wall / q0_wall,
        "safe": _safe(q0, arm),
        "arm_path": arm_path,
    }


def _aggregate(context, assignments, repeat_rows):
    outcomes = {}
    for arm in ARMS:
        rows = [row["arms"][arm] for row in repeat_rows]
        classes = {str(row["comparison_class"]) for row in rows}
        comparison = (
            next(iter(classes))
            if len(classes) == 1 else "replicate_class_disagreement"
        )
        q0 = statistics.median(float(row["q0_wall_sec"]) for row in rows)
        value = statistics.median(float(row["arm_wall_sec"]) for row in rows)
        ratio = value / q0
        determined = comparison not in {
            "both_censored", "replicate_class_disagreement",
        }
        beneficial = bool(
            determined and (
                comparison == "arm_beneficial_censor" or ratio < 1.0
            )
        )
        harmful = bool(
            comparison in {"arm_adverse_censor", "milestone_mismatch"}
            or (determined and ratio > 1.0)
        )
        outcomes[arm] = {
            "comparison_class": comparison,
            "outcome_determined": determined,
            "q0_median_wall_sec": q0,
            "arm_median_wall_sec": value,
            "ratio": ratio if determined else 1.0,
            "beneficial": beneficial,
            "harmful": harmful,
            "right_censored": comparison != "matched_milestone",
            "positive_gain_fraction": (
                max(0.0, 1.0 - ratio) if beneficial else 0.0
            ),
        }
    return {
        "scale": int(context["scale"]),
        "instance_hash": str(context["instance_hash"]),
        "state_hash": str(context["state_hash"]),
        "partition": str(assignments[str(context["instance_hash"])]),
        "safe": all(
            bool(value["safe"])
            for row in repeat_rows for value in row["arms"].values()
        ),
        "outcomes": outcomes,
        "repeat_rows": repeat_rows,
    }


def _validate_replay(payload, *, arm, repeat, context, wall, memory, bucket):
    expected = {
        "schema_version": REPLAY_SCHEMA,
        "policy": arm,
        "source_state_hash": str(context["state_hash"]),
        "source_engine_hash": str(context.get("source_engine_hash") or ""),
        "source_config_hash": str(context.get("source_config_hash") or ""),
        "source_exact_action_policy_hash": str(
            context.get("source_exact_action_policy_hash") or ""
        ),
    }
    errors = [
        key for key, value in expected.items()
        if str(payload.get(key) or "") != str(value)
    ]
    if int(payload.get("repeat_index") or 0) != repeat:
        errors.append("repeat")
    if float(payload.get("guidance_bucket_width") or 0.0) != bucket:
        errors.append("bucket")
    if float(payload.get("requested_wall_time_limit_sec") or 0.0) != wall:
        errors.append("wall")
    if float(payload.get("requested_memory_limit_gb") or 0.0) != memory:
        errors.append("memory")
    if str(payload.get("potential_file_sha256") or ""):
        errors.append("unexpected_potential")
    if errors:
        raise SystemExit("V4 matched-arm stale replay:" + ",".join(errors))


def _safe(control, guided):
    left = dict(control.get("proof_telemetry") or {})
    right = dict(guided.get("proof_telemetry") or {})
    return bool(
        not guided.get("labels_dropped")
        and all(int(right.get(key) or 0) == 0 for key in (
            "guidance_filter_count", "guidance_arc_drop_count",
            "guidance_label_drop_count", "guidance_branch_pair_drop_count",
        ))
        and all(left.get(key) == right.get(key) for key in (
            "legal_action_universe_hash_before_sort",
            "legal_arc_universe_hash_before_sort",
        ))
        and (
            not (control.get("search_exhaustive") and guided.get("search_exhaustive"))
            or _exact_match(control, guided)
        )
    )


def _exact_match(left, right):
    if left.get("global_min_rc") is not None and right.get("global_min_rc") is not None:
        return abs(float(left["global_min_rc"]) - float(right["global_min_rc"])) <= 2.0e-6
    if left.get("proved_no_rc_below") is not None and right.get("proved_no_rc_below") is not None:
        return abs(float(left["proved_no_rc_below"]) - float(right["proved_no_rc_below"])) <= 1.0e-12
    return False


def _effective_wall(row, budget):
    measured = max(1.0e-9, float(
        row.get("admission_milestone_wall_sec")
        or row.get("milestone_wall_sec")
        or row.get("total_fresh_process_wall_sec")
        or 0.0
    ))
    return measured if row.get("milestone_reached") else max(measured, budget)


def _summary(records):
    result = {}
    for partition in ("train", "calibration", "heldout", "overall"):
        rows = records if partition == "overall" else [
            row for row in records if row["partition"] == partition
        ]
        result[partition] = {
            "context_count": len(rows),
            "instance_count": len({row["instance_hash"] for row in rows}),
            "safe": all(bool(row["safe"]) for row in rows),
            "arms": {
                arm: {
                    "determined_count": sum(
                        bool(row["outcomes"][arm]["outcome_determined"])
                        for row in rows
                    ),
                    "beneficial_count": sum(
                        bool(row["outcomes"][arm]["beneficial"])
                        for row in rows
                    ),
                    "harmful_count": sum(
                        bool(row["outcomes"][arm]["harmful"])
                        for row in rows
                    ),
                    "geomean_ratio": _geomean([
                        float(row["outcomes"][arm]["ratio"])
                        for row in rows
                        if row["outcomes"][arm]["outcome_determined"]
                    ]),
                }
                for arm in ARMS
            },
        }
    return result


def _geomean(values):
    return None if not values else math.exp(statistics.fmean(
        math.log(max(1.0e-12, float(value))) for value in values
    ))


def _environment(build):
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{build}"
    return env


def _existing(path):
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            result[str(row["state_hash"])] = row
    return result


def _run(command, *, env):
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def _resolve(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _append(path, payload):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
