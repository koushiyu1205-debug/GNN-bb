#!/usr/bin/env python3
"""Fresh-process evaluation of a frozen QG2 V3 multi-arm selector."""

from __future__ import annotations

import argparse
import importlib.util
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

SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_gat_selector_fresh.v1"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_gat_arm_selector_training.v3"
CONTROL_TRAINING_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_v4_arm_selector_control_training.v3"
)
REPLAY_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selector-training-report", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--partition", choices=("calibration", "heldout"), default="heldout"
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--minimum-expected-gain-floor", type=float, default=0.0)
    parser.add_argument("--minimum-benefit-probability-floor", type=float)
    parser.add_argument("--maximum-adverse-probability-ceiling", type=float)
    parser.add_argument("--scale30-wall-sec", type=float, default=300.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=600.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    args = parser.parse_args()

    import torch
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        qg2_v3_is_ood,
    )
    from lunar_ice_bpc.guidance.qg2_unified_arm_selector_v3 import (
        QG2V3GraphArmSelector,
        QG2V3LinearGraphArmSelector,
        QG2V3MLPArmSelector,
        QG2_V4_SELECTOR_CHECKPOINT_SCHEMA,
    )

    report_path = _resolve(args.selector_training_report)
    report = _load(report_path)
    if report.get("schema_version") not in {
        TRAINING_SCHEMA, CONTROL_TRAINING_SCHEMA,
    }:
        raise SystemExit("QG2 V3 fresh selector training schema mismatch")
    if bool(report.get("deployment_authorized")):
        raise SystemExit("QG2 V3 development selector claims deployment")
    helper = _load_training_helpers()
    oracle = _load(_resolve(report["oracle_summary"]))
    ranker = _load(_resolve(report["ranker_training_report"]))
    split = _load(_resolve(ranker["split_path"]))["assignments"]
    normalization = _load(_resolve(ranker["normalization_path"]))
    feature_envelope = _load(_resolve(ranker["feature_envelope_path"]))
    force_reports = [
        _load(_resolve(path))
        for path in report.get("qg2_force_on_reports") or ()
    ]
    matched = (
        None if not report.get("matched_arm_report")
        else _load(_resolve(report["matched_arm_report"]))
    )
    examples, _rejections = helper._load_examples(
        oracle, split,
        qg2_records=helper._force_records(force_reports),
        qg2_enabled="QG2" in set(report.get("trainable_arms") or ()),
        matched_arm_records=(
            {} if matched is None else {
                str(row["state_hash"]): dict(row)
                for row in matched.get("records") or ()
            }
        ),
        matched_arms_required=matched is not None,
    )
    examples = [
        row for row in examples if row["partition"] == str(args.partition)
    ]
    checkpoint = torch.load(
        _resolve(report["checkpoint_path"]),
        map_location="cpu",
        weights_only=False,
    )
    if checkpoint.get("schema_version") != QG2_V4_SELECTOR_CHECKPOINT_SCHEMA:
        raise SystemExit("QG2 V4 fresh selector checkpoint schema mismatch")
    if str(checkpoint.get("input_parity_contract") or "") != (
        "node_edge_context_identical_gat_topology_only_difference.v1"
    ):
        raise SystemExit("QG2 V4 fresh selector input-parity contract mismatch")
    model_kind = str(report.get("trained_model") or "")
    model_class = {
        "gat": QG2V3GraphArmSelector,
        "mlp": QG2V3MLPArmSelector,
        "linear": QG2V3LinearGraphArmSelector,
    }.get(model_kind)
    if model_class is None:
        raise SystemExit(f"unsupported QG2 V3 selector model: {model_kind}")
    model = model_class(normalization)
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.eval()
    predictions = helper._predict(model, examples)
    thresholds = _fresh_thresholds(
        report["thresholds"],
        minimum_expected_gain_floor=float(args.minimum_expected_gain_floor),
        minimum_benefit_probability_floor=(
            None if args.minimum_benefit_probability_floor is None
            else float(args.minimum_benefit_probability_floor)
        ),
        maximum_adverse_probability_ceiling=(
            None if args.maximum_adverse_probability_ceiling is None
            else float(args.maximum_adverse_probability_ceiling)
        ),
    )
    by_state = {str(row["state_hash"]): row for row in examples}
    source_by_state = {
        str(row["state_hash"]): dict(row)
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    selected = []
    for prediction in predictions:
        state = str(prediction["state_hash"])
        example = by_state[state]
        ood, reason = qg2_v3_is_ood(
            example["features"], feature_envelope
        )
        action = "Q0" if ood else helper._selected_arm(prediction, thresholds)
        selected.append({
            "prediction": prediction,
            "example": example,
            "source": source_by_state[state],
            "action": action,
            "ood": bool(ood),
            "ood_reason": str(reason if ood else ""),
        })
    selected.sort(key=lambda row: (
        int(row["example"]["scale"]), str(row["example"]["state_hash"])
    ))

    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / "fresh_records.jsonl"
    existing = _existing_records(records_path)
    env = dict(os.environ)
    env["PYTHONPATH"] = (
        f"{ROOT / 'src'}:{_resolve(args.native_build_dir)}"
    )
    bucket = float(oracle["frozen_guidance_bucket_width"])
    repeats = max(1, int(args.repeats))
    for index, row in enumerate(selected):
        state = str(row["example"]["state_hash"])
        if state in existing:
            continue
        action = str(row["action"])
        prediction = dict(row["prediction"]["arms"].get(action) or {})
        if action == "Q0":
            record = {
                "partition": str(args.partition),
                "scale": int(row["example"]["scale"]),
                "instance_hash": str(row["example"]["instance_hash"]),
                "state_hash": state,
                "selected_action": "Q0",
                "selection_reason": (
                    "ood_literal_q0" if row["ood"] else "all_arms_rejected"
                ),
                "ood": row["ood"],
                "ood_reason": row["ood_reason"],
                "ratio": 1.0,
                "safe": True,
                "comparison_class": "literal_q0",
                "repeat_rows": [],
            }
        else:
            source = row["source"]
            scale = int(row["example"]["scale"])
            wall = (
                float(args.scale30_wall_sec)
                if scale == 30 else float(args.scale50_wall_sec)
            )
            context_dir = output_dir / f"scale{scale}" / state[:16]
            context_dir.mkdir(parents=True, exist_ok=True)
            repeat_rows = []
            for repeat in range(1, repeats + 1):
                arms = ["Q0", action]
                random.Random(20260806 + index * 101 + repeat).shuffle(arms)
                outputs = {}
                paths = {}
                qg2_potential = (
                    _resolve(dict(
                        row["example"].get("qg2_force_record") or {}
                    ).get("potential_path") or "")
                    if action == "QG2" else None
                )
                if action == "QG2" and not qg2_potential.is_file():
                    raise SystemExit("selected QG2 arm lacks a bound potential")
                for arm in arms:
                    target = context_dir / f"{arm.lower()}_rep{repeat}.json"
                    paths[arm] = str(target)
                    if not target.exists():
                        command = [
                            sys.executable, str(REPLAY),
                            "--instance", str(source["instance_path"]),
                            "--snapshot", str(source["snapshot_path"]),
                            "--output", str(target),
                            "--policy", arm,
                            "--repeat-index", str(repeat),
                            "--wall-time-limit-sec", str(wall),
                            "--memory-limit-gb", str(float(args.memory_limit_gb)),
                            "--guidance-bucket-width", str(bucket),
                            "--source-backend-id", str(
                                source.get("source_backend_id")
                                or "native_rcspp_bidirectional_root_partial_hybrid_v3"
                            ),
                        ]
                        if arm == "QG2":
                            command.extend(["--potential", str(qg2_potential)])
                        _run(command, env=env)
                    outputs[arm] = _load(target)
                    _validate_replay(
                        outputs[arm], arm=arm, repeat=repeat,
                        source=source, wall=wall,
                        memory=float(args.memory_limit_gb), bucket=bucket,
                        potential_path=(
                            qg2_potential if arm == "QG2" else None
                        ),
                    )
                repeat_rows.append(_repeat_outcome(
                    outputs["Q0"], outputs[action],
                    budget=wall, repeat=repeat, action=action, paths=paths,
                ))
            record = _context_outcome(
                row=row,
                action=action,
                prediction=prediction,
                repeat_rows=repeat_rows,
                model_kind=model_kind,
            )
        _append_jsonl(records_path, record)
        existing[state] = record
        print(json.dumps({
            "completed": len(existing),
            "total": len(selected),
            "state": state[:16],
            "scale": record["scale"],
            "action": record["selected_action"],
            "ratio": record["ratio"],
            "class": record["comparison_class"],
            "safe": record["safe"],
        }, sort_keys=True), flush=True)

    records = [existing[str(row["example"]["state_hash"])] for row in selected]
    result = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "selector_training_report": str(report_path),
        "selector_training_report_sha256": _sha256(report_path),
        "checkpoint_path": str(_resolve(report["checkpoint_path"])),
        "checkpoint_sha256": _sha256(_resolve(report["checkpoint_path"])),
        "partition": str(args.partition),
        "trained_model": model_kind,
        "thresholds": thresholds,
        "minimum_expected_gain_floor": float(
            args.minimum_expected_gain_floor
        ),
        "repeat_count": repeats,
        "records_path": str(records_path),
        "records_path_sha256": _sha256(records_path),
        "records": records,
        "summary": _summary(records),
        "deployment_authorized": False,
    }
    _write(output_path, result)
    print(json.dumps(result["summary"], sort_keys=True), flush=True)
    return 0 if result["summary"]["overall"]["all_safe"] else 3


def _fresh_thresholds(
    frozen,
    *,
    minimum_expected_gain_floor=0.0,
    minimum_benefit_probability_floor=None,
    maximum_adverse_probability_ceiling=None,
):
    """Apply only explicitly requested conservative fresh-test overrides."""

    thresholds = dict(frozen)
    thresholds["minimum_expected_gain"] = max(
        float(thresholds.get("minimum_expected_gain") or 0.0),
        max(0.0, float(minimum_expected_gain_floor)),
    )
    if minimum_benefit_probability_floor is not None:
        thresholds["minimum_benefit_probability"] = max(
            float(thresholds.get("minimum_benefit_probability") or 0.0),
            float(minimum_benefit_probability_floor),
        )
    if maximum_adverse_probability_ceiling is not None:
        thresholds["maximum_adverse_probability"] = min(
            float(thresholds.get("maximum_adverse_probability") or 0.0),
            float(maximum_adverse_probability_ceiling),
        )
    return thresholds


def _repeat_outcome(q0, arm, *, budget, repeat, action, paths):
    left = _effective_wall(q0, budget)
    right = _effective_wall(arm, budget)
    left_reached = bool(q0.get("milestone_reached"))
    right_reached = bool(arm.get("milestone_reached"))
    left_kind = str(q0.get("milestone_kind") or "")
    right_kind = str(arm.get("milestone_kind") or "")
    matched = bool(
        left_reached and right_reached and left_kind == right_kind
        and left_kind in {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
    )
    if matched:
        kind = "matched_milestone"
    elif left_reached and not right_reached:
        kind = "arm_adverse_censor"
    elif right_reached and not left_reached:
        kind = "arm_beneficial_censor"
    elif not left_reached and not right_reached:
        kind = "both_censored"
    else:
        kind = "milestone_mismatch"
    safety_violations = _safety_violations(q0, arm)
    return {
        "repeat": repeat,
        "action": action,
        "q0_wall_sec": left,
        "arm_wall_sec": right,
        "ratio": right / left,
        "comparison_class": kind,
        "safe": not safety_violations,
        "safety_violations": list(safety_violations),
        "q0_path": paths["Q0"],
        "arm_path": paths[action],
    }


def _context_outcome(*, row, action, prediction, repeat_rows, model_kind):
    classes = [value["comparison_class"] for value in repeat_rows]
    comparison = classes[0] if len(set(classes)) == 1 else "replicate_class_disagreement"
    q0 = statistics.median(value["q0_wall_sec"] for value in repeat_rows)
    arm = statistics.median(value["arm_wall_sec"] for value in repeat_rows)
    comparable = comparison not in {"both_censored", "replicate_class_disagreement"}
    safety_violations = sorted({
        str(reason)
        for value in repeat_rows
        for reason in value.get("safety_violations") or ()
    })
    return {
        "partition": row["example"]["partition"],
        "scale": int(row["example"]["scale"]),
        "instance_hash": str(row["example"]["instance_hash"]),
        "state_hash": str(row["example"]["state_hash"]),
        "milestone_kind": str(row["example"]["milestone_kind"]),
        "selected_action": action,
        "selection_reason": f"risk_adjusted_{model_kind}_selector",
        "prediction": {
            key: float(prediction[key])
            for key in (
                "benefit_probability", "conditional_positive_gain",
                "expected_gain", "adverse_probability",
            )
        },
        "ood": False,
        "ood_reason": "",
        "q0_median_wall_sec": q0,
        "arm_median_wall_sec": arm,
        "ratio": arm / q0 if comparable else 1.0,
        "safe": all(bool(value["safe"]) for value in repeat_rows),
        "safety_violations": safety_violations,
        "comparison_class": comparison,
        "beneficial": bool(comparable and arm < q0),
        "harmful": bool(comparable and arm > q0),
        "repeat_rows": repeat_rows,
    }


def _summary(records):
    def one(rows):
        return {
            "context_count": len(rows),
            "activated_count": sum(row["selected_action"] != "Q0" for row in rows),
            "beneficial_count": sum(bool(row.get("beneficial")) for row in rows),
            "harmful_count": sum(bool(row.get("harmful")) for row in rows),
            "net_geomean_ratio": _geomean([float(row["ratio"]) for row in rows]),
            "all_safe": all(bool(row["safe"]) for row in rows),
            "hard_safety_violation_count": sum(
                not bool(row["safe"]) for row in rows
            ),
        }
    return {
        "overall": one(records),
        "scale30": one([row for row in records if int(row["scale"]) == 30]),
        "scale50": one([row for row in records if int(row["scale"]) == 50]),
    }


def _validate_replay(
    payload, *, arm, repeat, source, wall, memory, bucket,
    potential_path=None,
):
    errors = []
    expected = {
        "schema_version": REPLAY_SCHEMA,
        "policy": arm,
        "source_state_hash": str(source["state_hash"]),
        "source_engine_hash": str(source.get("source_engine_hash") or ""),
        "source_config_hash": str(source.get("source_config_hash") or ""),
        "source_exact_action_policy_hash": str(
            source.get("source_exact_action_policy_hash") or ""
        ),
    }
    for key, value in expected.items():
        if str(payload.get(key) or "") != str(value):
            errors.append(key)
    if int(payload.get("repeat_index") or 0) != repeat:
        errors.append("repeat")
    if float(payload.get("guidance_bucket_width") or 0.0) != bucket:
        errors.append("bucket")
    if float(payload.get("requested_wall_time_limit_sec") or 0.0) != wall:
        errors.append("wall")
    if float(payload.get("requested_memory_limit_gb") or 0.0) != memory:
        errors.append("memory")
    expected_potential = (
        _sha256(potential_path) if arm == "QG2" and potential_path else ""
    )
    if str(payload.get("potential_file_sha256") or "") != expected_potential:
        errors.append("potential")
    if errors:
        raise SystemExit("QG2 V3 selector stale replay:" + ",".join(errors))


def _safety_violations(control, guided):
    left = dict(control.get("proof_telemetry") or {})
    right = dict(guided.get("proof_telemetry") or {})
    violations = []
    for key in (
        "guidance_filter_count", "guidance_arc_drop_count",
        "guidance_label_drop_count", "guidance_branch_pair_drop_count",
    ):
        if int(right.get(key) or 0) != 0:
            violations.append(key)
    for key in (
        "legal_action_universe_hash_before_sort",
        "legal_arc_universe_hash_before_sort",
    ):
        if left.get(key) != right.get(key):
            violations.append(key)
    if bool(guided.get("search_exhaustive")) and bool(
        guided.get("labels_dropped")
    ):
        violations.append("exhaustive_with_labels_dropped")
    if (
        control.get("search_exhaustive")
        and guided.get("search_exhaustive")
        and not _exact_match(control, guided)
    ):
        violations.append("exact_result_mismatch")
    return tuple(violations)


def _safe(control, guided):
    return not _safety_violations(control, guided)


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
    return 1.0 if not values else math.exp(statistics.fmean(
        math.log(max(1.0e-12, float(value))) for value in values
    ))


def _load_training_helpers():
    path = ROOT / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py"
    spec = importlib.util.spec_from_file_location("qg2_v3_selector_helpers", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("cannot load QG2 V3 selector helpers")
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _existing_records(path):
    result = {}
    if path.exists():
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


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _append_jsonl(path, payload):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def _sha256(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
