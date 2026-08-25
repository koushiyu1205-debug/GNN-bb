#!/usr/bin/env python3
"""Collect clean, force-on Q0/GAT outcomes for QG2 V3.

This runner does not tune an activation threshold and cannot authorize
deployment.  Its sole purpose is to measure the frozen GAT ranker's own action
and produce leakage-safe labels for the later unified arm selector.
"""

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
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (  # noqa: E402
    QG2_V3_SUPERVISION_SCHEMA,
)


TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_ranker_training.v1"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
REPLAY_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
POTENTIAL_SCHEMA = "lunar_ice_bpc.p0v5_qg2_label_state_potential.v2"
REPORT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_gat_force_on_calibration.v1"
PREDICT = ROOT / "scripts/predict_p0v5_qg2_v3_potential.py"
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-report", required=True)
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--partition", choices=("train", "calibration", "heldout"),
        default="calibration",
    )
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

    training_path = _resolve(args.training_report)
    oracle_path = _resolve(args.oracle_summary)
    training = _load(training_path)
    oracle = _load(oracle_path)
    if training.get("schema_version") != TRAINING_SCHEMA:
        raise SystemExit("QG2 V3 force-on training schema mismatch")
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        raise SystemExit("QG2 V3 force-on oracle schema mismatch")
    if bool(training.get("activation_authority")):
        raise SystemExit("QG2 V3 ranker report unexpectedly claims activation")
    gat_rows = [
        dict(row) for row in training.get("models") or ()
        if str(row.get("model_kind") or "") == "gat"
    ]
    if len(gat_rows) != 1:
        raise SystemExit("QG2 V3 force-on requires exactly one frozen GAT")
    checkpoint = _resolve(gat_rows[0]["checkpoint_path"])
    split = _load(_resolve(training["split_path"]))["assignments"]
    source_by_state = {
        str(row["state_hash"]): dict(row)
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    contexts = [
        {
            **dict(row),
            "instance_path": source_by_state[str(row["state_hash"])]["instance_path"],
            "snapshot_path": source_by_state[str(row["state_hash"])]["snapshot_path"],
        }
        for row in oracle.get("context_rows") or ()
        if str(row["state_hash"]) in source_by_state
        and split.get(str(row["instance_hash"])) == str(args.partition)
    ]
    contexts = _frozen_context_order(
        contexts,
        maximum_per_scale=max(0, int(args.maximum_contexts_per_scale)),
    )
    if not contexts:
        raise SystemExit("QG2 V3 force-on selection has no contexts")

    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_envelope = _resolve(training["feature_envelope_path"])
    native_build = _resolve(args.native_build_dir)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{native_build}"
    bucket = float(oracle["frozen_guidance_bucket_width"])
    repeats = max(1, int(args.repeats))
    records_path = output_dir / "force_on_records.jsonl"
    records_by_state = _existing_records(records_path)

    for context_index, context in enumerate(contexts):
        state = str(context["state_hash"])
        if state in records_by_state:
            continue
        scale = int(context["scale"])
        context_dir = output_dir / f"scale{scale}" / state[:16]
        context_dir.mkdir(parents=True, exist_ok=True)
        potential_path = context_dir / "gat_potential.json"
        if not potential_path.exists():
            _run([
                sys.executable, str(PREDICT),
                "--instance", str(context["instance_path"]),
                "--snapshot", str(context["snapshot_path"]),
                "--checkpoint", str(checkpoint),
                "--feature-envelope", str(feature_envelope),
                "--output", str(potential_path),
            ], env=env)
        potential = _load(potential_path)
        _validate_potential(
            potential,
            context=context,
            checkpoint=checkpoint,
            feature_envelope=feature_envelope,
        )
        if bool(potential.get("runtime_prethreshold_veto")):
            record = {
                "partition": str(args.partition),
                "scale": scale,
                "instance_hash": str(context["instance_hash"]),
                "state_hash": state,
                "action_eligible": False,
                "ood": bool(potential.get("ood")),
                "veto_reason": str(
                    potential.get("runtime_prethreshold_veto_reason") or ""
                ),
                "safe": True,
                "comparison_class": "literal_q0_veto",
                "ratio": 1.0,
                "repeat_rows": [],
                "potential_path": str(potential_path),
            }
        else:
            wall_limit = (
                float(args.scale30_wall_sec)
                if scale == 30 else float(args.scale50_wall_sec)
            )
            repeat_rows = []
            for repeat in range(1, repeats + 1):
                order = ["Q0", "QG2"]
                random.Random(
                    20260806 + context_index * 101 + repeat
                ).shuffle(order)
                outputs = {}
                paths = {}
                for arm in order:
                    target = context_dir / f"{arm.lower()}_rep{repeat}.json"
                    paths[arm] = str(target)
                    if not target.exists():
                        command = [
                            sys.executable, str(REPLAY),
                            "--instance", str(context["instance_path"]),
                            "--snapshot", str(context["snapshot_path"]),
                            "--output", str(target),
                            "--policy", arm,
                            "--repeat-index", str(repeat),
                            "--wall-time-limit-sec", str(wall_limit),
                            "--memory-limit-gb", str(float(args.memory_limit_gb)),
                            "--guidance-bucket-width", str(bucket),
                            "--source-backend-id", str(
                                context.get("source_backend_id")
                                or "native_rcspp_bidirectional_root_partial_hybrid_v3"
                            ),
                        ]
                        if arm == "QG2":
                            command.extend(["--potential", str(potential_path)])
                        _run(command, env=env)
                    outputs[arm] = _load(target)
                    _validate_replay(
                        outputs[arm],
                        arm=arm,
                        repeat=repeat,
                        context=context,
                        wall_limit=wall_limit,
                        memory_limit=float(args.memory_limit_gb),
                        bucket=bucket,
                        potential_path=potential_path,
                    )
                repeat_rows.append(_repeat_outcome(
                    outputs["Q0"], outputs["QG2"],
                    budget=wall_limit,
                    inference_sec=(
                        float(potential.get("tensorization_wall_ms") or 0.0)
                        + float(potential.get("inference_wall_ms") or 0.0)
                    ) / 1000.0,
                    repeat=repeat,
                    paths=paths,
                ))
            record = _context_outcome(
                context=context,
                partition=str(args.partition),
                potential=potential,
                potential_path=potential_path,
                repeat_rows=repeat_rows,
            )
        _append_jsonl(records_path, record)
        records_by_state[state] = record
        _write(output_dir / "progress.json", {
            "schema_version": "lunar_ice_bpc.p0v5_qg2_v3_force_on_progress.v1",
            "completed_contexts": len(records_by_state),
            "selected_contexts": len(contexts),
            "completed_by_scale": {
                str(scale): sum(
                    int(row.get("scale") or 0) == scale
                    for row in records_by_state.values()
                )
                for scale in (30, 50)
            },
            "last_state_hash": state,
        })
        print(json.dumps({
            "completed": len(records_by_state),
            "total": len(contexts),
            "scale": scale,
            "state": state[:16],
            "class": record["comparison_class"],
            "ratio": record["ratio"],
            "safe": record["safe"],
        }, sort_keys=True), flush=True)

    records = [records_by_state[str(row["state_hash"])] for row in contexts]
    report = {
        "schema_version": REPORT_SCHEMA,
        "development_only": True,
        "deployable": False,
        "force_on_ranker_evaluation": True,
        "activation_threshold_tuned": False,
        "selector_training_source": "actual_frozen_gat_fresh_process_outcomes",
        "training_report": str(training_path),
        "training_report_sha256": _sha256(training_path),
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "partition": str(args.partition),
        "bucket_width": bucket,
        "repeat_count": repeats,
        "context_selection_policy": "hash_frozen_stratified_all_or_prefix.v1",
        "maximum_contexts_per_scale": max(
            0, int(args.maximum_contexts_per_scale)
        ),
        "records_path": str(records_path),
        "records_path_sha256": _sha256(records_path),
        "records": records,
        "summary": _summary(records),
        "selector_training_permitted": bool(
            all(bool(row.get("safe")) for row in records)
            and sum(bool(row.get("action_eligible")) for row in records) >= 10
            and sum(
                row.get("comparison_class")
                not in {"both_censored", "literal_q0_veto"}
                for row in records
            ) >= 5
        ),
        "deployment_authorized": False,
        "next_action": "train_unified_q0_qg2_qd1_qb1_selector",
    }
    _write(output_path, report)
    print(json.dumps(report["summary"], sort_keys=True), flush=True)
    return 0 if all(bool(row.get("safe")) for row in records) else 3


def _frozen_context_order(rows, *, maximum_per_scale: int):
    result = []
    for scale in (30, 50):
        candidates = [row for row in rows if int(row["scale"]) == scale]
        candidates.sort(key=lambda row: (
            str(row.get("q0_milestone_kind") or ""),
            hashlib.sha256(str(row["state_hash"]).encode()).hexdigest(),
        ))
        if maximum_per_scale > 0:
            candidates = candidates[:maximum_per_scale]
        result.extend(candidates)
    return result


def _validate_potential(payload, *, context, checkpoint, feature_envelope):
    errors = []
    if payload.get("schema_version") != POTENTIAL_SCHEMA:
        errors.append("schema")
    if payload.get("supervision_schema_version") != QG2_V3_SUPERVISION_SCHEMA:
        errors.append("supervision")
    if bool(payload.get("ranker_activation_authority")):
        errors.append("ranker_claims_activation")
    expected = {
        "source_state_hash": str(context["state_hash"]),
        "source_engine_hash": str(context.get("source_engine_hash") or ""),
        "source_config_hash": str(context.get("source_config_hash") or ""),
        "source_exact_action_policy_hash": str(
            context.get("source_exact_action_policy_hash") or ""
        ),
        "checkpoint_sha256": _sha256(checkpoint),
        "feature_envelope_sha256": _sha256(feature_envelope),
    }
    for key, value in expected.items():
        if str(payload.get(key) or "") != value:
            errors.append(key)
    if errors:
        raise SystemExit("QG2 V3 stale potential:" + ",".join(errors))


def _validate_replay(payload, *, arm, repeat, context, wall_limit, memory_limit, bucket, potential_path):
    errors = []
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
    for key, value in expected.items():
        if str(payload.get(key) or "") != str(value):
            errors.append(key)
    if int(payload.get("repeat_index") or 0) != repeat:
        errors.append("repeat")
    if float(payload.get("guidance_bucket_width") or 0.0) != bucket:
        errors.append("bucket")
    if float(payload.get("requested_wall_time_limit_sec") or 0.0) != wall_limit:
        errors.append("wall")
    if float(payload.get("requested_memory_limit_gb") or 0.0) != memory_limit:
        errors.append("memory")
    expected_potential = _sha256(potential_path) if arm == "QG2" else ""
    if str(payload.get("potential_file_sha256") or "") != expected_potential:
        errors.append("potential")
    if errors:
        raise SystemExit("QG2 V3 stale replay:" + ",".join(errors))


def _repeat_outcome(q0, gat, *, budget, inference_sec, repeat, paths):
    q0_wall = _effective_wall(q0, budget)
    gat_wall = _effective_wall(gat, budget) + inference_sec
    q0_reached = bool(q0.get("milestone_reached"))
    gat_reached = bool(gat.get("milestone_reached"))
    q0_kind = str(q0.get("milestone_kind") or "")
    gat_kind = str(gat.get("milestone_kind") or "")
    matched = bool(
        q0_reached and gat_reached and q0_kind == gat_kind
        and q0_kind in {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
    )
    if matched:
        comparison = "matched_milestone"
    elif q0_reached and not gat_reached:
        comparison = "gat_adverse_censor"
    elif gat_reached and not q0_reached:
        comparison = "gat_beneficial_censor"
    elif not q0_reached and not gat_reached:
        comparison = "both_censored"
    else:
        comparison = "milestone_mismatch"
    return {
        "repeat": repeat,
        "q0_wall_sec": q0_wall,
        "gat_net_wall_sec": gat_wall,
        "ratio": gat_wall / q0_wall,
        "q0_milestone_reached": q0_reached,
        "gat_milestone_reached": gat_reached,
        "q0_milestone_kind": q0_kind,
        "gat_milestone_kind": gat_kind,
        "comparison_class": comparison,
        "safe": _safe(q0, gat),
        "q0_path": paths["Q0"],
        "gat_path": paths["QG2"],
    }


def _context_outcome(*, context, partition, potential, potential_path, repeat_rows):
    classes = [row["comparison_class"] for row in repeat_rows]
    comparison = (
        classes[0] if len(set(classes)) == 1 else "replicate_class_disagreement"
    )
    q0 = statistics.median(row["q0_wall_sec"] for row in repeat_rows)
    gat = statistics.median(row["gat_net_wall_sec"] for row in repeat_rows)
    comparable = comparison not in {"both_censored", "replicate_class_disagreement"}
    return {
        "partition": partition,
        "scale": int(context["scale"]),
        "instance_hash": str(context["instance_hash"]),
        "state_hash": str(context["state_hash"]),
        "milestone_kind": str(context.get("q0_milestone_kind") or ""),
        "action_eligible": True,
        "ood": False,
        "veto_reason": "",
        "safe": all(bool(row["safe"]) for row in repeat_rows),
        "comparison_class": comparison,
        "q0_median_wall_sec": q0,
        "gat_net_median_wall_sec": gat,
        "ratio": gat / q0 if comparable else 1.0,
        "beneficial": bool(comparable and gat < q0),
        "harmful": bool(comparable and gat > q0),
        "adverse_target": bool(
            comparison in {"gat_adverse_censor", "milestone_mismatch"}
            or (comparable and gat > q0)
        ),
        "relative_positive_gain": max(0.0, (q0 - gat) / q0),
        "tensorization_wall_ms": float(
            potential.get("tensorization_wall_ms") or 0.0
        ),
        "inference_wall_ms": float(potential.get("inference_wall_ms") or 0.0),
        "potential_path": str(potential_path),
        "repeat_rows": repeat_rows,
    }


def _summary(records):
    def summarize(rows):
        ratios = [float(row["ratio"]) for row in rows]
        return {
            "context_count": len(rows),
            "action_eligible_count": sum(bool(row.get("action_eligible")) for row in rows),
            "comparable_count": sum(
                row.get("comparison_class")
                not in {"both_censored", "literal_q0_veto", "replicate_class_disagreement"}
                for row in rows
            ),
            "beneficial_count": sum(bool(row.get("beneficial")) for row in rows),
            "harmful_count": sum(bool(row.get("harmful")) for row in rows),
            "adverse_count": sum(bool(row.get("adverse_target")) for row in rows),
            "both_censored_count": sum(row.get("comparison_class") == "both_censored" for row in rows),
            "observed_net_geomean_ratio": _geomean(ratios),
            "all_safe": all(bool(row.get("safe")) for row in rows),
        }
    return {
        "overall": summarize(records),
        "scale30": summarize([row for row in records if int(row["scale"]) == 30]),
        "scale50": summarize([row for row in records if int(row["scale"]) == 50]),
    }


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


def _geomean(values):
    return 1.0 if not values else math.exp(
        statistics.fmean(math.log(max(1.0e-12, float(value))) for value in values)
    )


def _existing_records(path: Path):
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


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _append_jsonl(path: Path, payload):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
