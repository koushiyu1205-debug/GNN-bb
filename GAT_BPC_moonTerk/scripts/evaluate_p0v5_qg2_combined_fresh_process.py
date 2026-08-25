#!/usr/bin/env python3
"""Fresh-process evaluation of QG2 -> QD1/QB1 -> literal-Q0 hierarchy.

The base QG2 model ladder is calibrated first and remains unchanged.  This
sidecar collects blocked Q0/QD1/QB1 repeats from the same admission-bound
snapshots, calibrates the secondary thresholds only after each model's QG2
thresholds are frozen, and evaluates the fixed hierarchy on heldout instances.
It never authorizes deployment; a passing result still requires a separately
implemented, hashed, and tested runtime policy plus E2E acceptance.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.qg2_combined_policy import (  # noqa: E402
    ArmOutcome,
    ArmScore,
    CombinedContext,
    QG2_COMBINED_ACTION_HIERARCHY_V1,
    QG2_POSITIVE_NET_EVALUATION_GATE_V1,
    choose_secondary_thresholds,
    choose_secondary_thresholds_for_positive_net_evaluation,
    evaluate_combined_policy,
)
from lunar_ice_bpc.guidance.qg2_context_arm_selector import (  # noqa: E402
    QG2_CONTEXT_ARM_SELECTOR_PREDICTION_V1,
)


SCHEMA = "lunar_ice_bpc.p0v5_qg2_combined_fresh_process.v1"
BASE_CALIBRATION_SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SELECTOR_SCHEMA = "lunar_ice_bpc.p0v5_qg2_context_arm_selector_feasibility.v1"
REPLAY_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
EXPECTED_MODELS = ("linear", "mlp", "gat")
SECONDARY_ARMS = ("QD1", "QB1")
PREDICT = ROOT / "scripts/predict_p0v5_qg2_context_arm.py"
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
GUIDANCE_ENV_KEYS = (
    "LUNAR_ICE_PROOF_TAIL_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_TAIL_GAT_EVALUATION_MODE",
    "LUNAR_ICE_PROOF_QUEUE_GAT_MANIFEST",
    "LUNAR_ICE_PROOF_QUEUE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_MANIFEST",
    "LUNAR_ICE_BIDIRECTIONAL_GATE_GAT_EVALUATION_MODE",
    "LUNAR_ICE_GAT_DEPLOYMENT_MANIFEST",
    "LUNAR_ICE_GAT_GUIDANCE_MODE",
    "LUNAR_ICE_GAT_TRAINING_ROWS_DIR",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-calibration-report", required=True)
    parser.add_argument("--selector-report", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--scale30-wall-sec", type=float, default=180.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=300.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument(
        "--evaluation-gate-policy",
        choices=("strict", QG2_POSITIVE_NET_EVALUATION_GATE_V1),
        default=QG2_POSITIVE_NET_EVALUATION_GATE_V1,
    )
    parser.add_argument(
        "--native-build-dir",
        default="build/native-spprc-bidirectional-feasibility-v1",
    )
    args = parser.parse_args()

    base_path = _resolve(args.base_calibration_report)
    selector_path = _resolve(args.selector_report)
    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = _load(base_path)
    selector = _load(selector_path)
    training_path, oracle_path, split, sources, contexts = _validate_inputs(
        base_path=base_path,
        base=base,
        selector_path=selector_path,
        selector=selector,
    )
    bucket = float(base["bucket_width"])
    env = _clean_environment(args.native_build_dir)
    repeats = max(3, int(args.repeats))

    secondary_records = []
    for context_index, context in enumerate(contexts):
        source = sources[str(context["state_hash"])]
        partition = split[str(context["instance_hash"])]
        state = str(context["state_hash"])
        scale = int(context["scale"])
        context_dir = (
            output_dir / partition / f"{scale}_{state[:16]}"
        )
        context_dir.mkdir(parents=True, exist_ok=True)
        prediction_path = context_dir / "context_arm_prediction.json"
        if not prediction_path.exists():
            _run(
                [
                    sys.executable,
                    str(PREDICT),
                    "--instance",
                    str(source["instance_path"]),
                    "--snapshot",
                    str(source["snapshot_path"]),
                    "--selector-report",
                    str(selector_path),
                    "--output",
                    str(prediction_path),
                ],
                env=env,
            )
        prediction = _load(prediction_path)
        _validate_prediction(
            prediction,
            prediction_path=prediction_path,
            selector_path=selector_path,
            source=source,
        )
        wall_limit = (
            float(args.scale30_wall_sec)
            if scale == 30
            else float(args.scale50_wall_sec)
        )
        if bool(prediction.get("runtime_prethreshold_veto")):
            secondary_records.append(
                _veto_record(
                    context=context,
                    partition=partition,
                    prediction=prediction,
                    prediction_path=prediction_path,
                )
            )
            continue

        repeat_rows = []
        for repeat in range(1, repeats + 1):
            order = ["Q0", *SECONDARY_ARMS]
            random.Random(
                20260805 + context_index * 1009 + repeat
            ).shuffle(order)
            outputs = {}
            for arm in order:
                target = context_dir / f"{arm.lower()}_rep{repeat}.json"
                if not target.exists():
                    _run(
                        [
                            sys.executable,
                            str(REPLAY),
                            "--instance",
                            str(source["instance_path"]),
                            "--snapshot",
                            str(source["snapshot_path"]),
                            "--output",
                            str(target),
                            "--policy",
                            arm,
                            "--repeat-index",
                            str(repeat),
                            "--wall-time-limit-sec",
                            str(wall_limit),
                            "--memory-limit-gb",
                            str(float(args.memory_limit_gb)),
                            "--guidance-bucket-width",
                            str(bucket),
                            "--source-backend-id",
                            str(source["source_backend_id"]),
                        ],
                        env=env,
                    )
                output = _load(target)
                _validate_replay(
                    output,
                    path=target,
                    arm=arm,
                    repeat=repeat,
                    source=source,
                    bucket=bucket,
                    wall_limit=wall_limit,
                    memory_limit=float(args.memory_limit_gb),
                )
                outputs[arm] = output
            q0_wall = _effective_wall(outputs["Q0"], wall_limit)
            repeat_rows.append(
                {
                    "repeat": repeat,
                    "q0_wall_sec": q0_wall,
                    "arms": {
                        arm: {
                            "wall_sec": _effective_wall(
                                outputs[arm], wall_limit
                            ),
                            "outcome_determined": _matched_milestone_outcome(
                                outputs["Q0"], outputs[arm]
                            ),
                            "safe": _safe(outputs["Q0"], outputs[arm]),
                        }
                        for arm in SECONDARY_ARMS
                    },
                }
            )
        secondary_records.append(
            _completed_record(
                context=context,
                partition=partition,
                prediction=prediction,
                prediction_path=prediction_path,
                repeat_rows=repeat_rows,
            )
        )
        print(
            json.dumps(
                {
                    "partition": partition,
                    "scale": scale,
                    "state": state[:16],
                    "qd1_ratio": secondary_records[-1]["arms"]["QD1"][
                        "ratio"
                    ],
                    "qb1_ratio": secondary_records[-1]["arms"]["QB1"][
                        "ratio"
                    ],
                    "safe": all(
                        secondary_records[-1]["arms"][arm]["safe"]
                        for arm in SECONDARY_ARMS
                    ),
                },
                sort_keys=True,
            ),
            flush=True,
        )

    base_models = {
        str(row["model_kind"]): dict(row)
        for row in base.get("models") or ()
    }
    base_records = {
        (str(row["model_kind"]), str(row["state_hash"])): dict(row)
        for row in base.get("records") or ()
    }
    secondary_by_state = {
        str(row["state_hash"]): row for row in secondary_records
    }
    model_reports = []
    for kind in EXPECTED_MODELS:
        base_model = base_models[kind]
        primary_thresholds = dict(base_model.get("thresholds") or {})
        combined_contexts = [
            _combined_context(
                kind=kind,
                context=context,
                base_record=base_records[(kind, str(context["state_hash"]))],
                secondary=secondary_by_state[str(context["state_hash"])],
            )
            for context in contexts
        ]
        calibration_contexts = [
            row
            for row in combined_contexts
            if split[row.instance_hash] == "calibration"
        ]
        heldout_contexts = [
            row
            for row in combined_contexts
            if split[row.instance_hash] == "heldout"
        ]
        threshold_selector = (
            choose_secondary_thresholds
            if args.evaluation_gate_policy == "strict"
            else choose_secondary_thresholds_for_positive_net_evaluation
        )
        thresholds = threshold_selector(
            calibration_contexts,
            primary_probability_threshold=float(
                primary_thresholds.get("probability_threshold", math.inf)
            ),
            primary_expected_gain_threshold=float(
                primary_thresholds.get("expected_gain_threshold", math.inf)
            ),
        )
        calibration_metrics = evaluate_combined_policy(
            calibration_contexts, thresholds
        )
        heldout_metrics = evaluate_combined_policy(
            heldout_contexts, thresholds
        )
        primary_only_thresholds = {
            "primary_probability_threshold": float(
                primary_thresholds.get("probability_threshold", math.inf)
            ),
            "primary_expected_gain_threshold": float(
                primary_thresholds.get("expected_gain_threshold", math.inf)
            ),
            "secondary_probability_threshold": 2.0,
            "secondary_expected_gain_threshold": 1.0e30,
        }
        primary_only_calibration = evaluate_combined_policy(
            calibration_contexts, primary_only_thresholds
        )
        primary_only_heldout = evaluate_combined_policy(
            heldout_contexts, primary_only_thresholds
        )
        secondary_heldout_count = sum(
            int(heldout_metrics["arm_counts"].get(arm, 0))
            for arm in SECONDARY_ARMS
        )
        secondary_adopted = bool(
            secondary_heldout_count > 0
            and float(heldout_metrics["net_geomean_ratio"])
            < float(primary_only_heldout["net_geomean_ratio"])
            and int(heldout_metrics["right_censored_count"]) == 0
            and int(heldout_metrics["unsafe_count"]) == 0
            and all(
                float(
                    heldout_metrics["per_scale"][str(scale)][
                        "net_geomean_ratio"
                    ]
                )
                <= 1.03
                for scale in (30, 50)
            )
        )
        selected_calibration = (
            calibration_metrics
            if secondary_adopted
            else primary_only_calibration
        )
        selected_heldout = (
            heldout_metrics if secondary_adopted else primary_only_heldout
        )
        selected_thresholds = (
            {
                key: value
                for key, value in thresholds.items()
                if key.endswith("_threshold")
            }
            if secondary_adopted
            else primary_only_thresholds
        )
        model_reports.append(
            {
                "model_kind": kind,
                "checkpoint_path": str(base_model["checkpoint_path"]),
                "checkpoint_sha256": str(base_model["checkpoint_sha256"]),
                "base_primary_thresholds": primary_thresholds,
                "proposed_combined_thresholds": {
                    key: value
                    for key, value in thresholds.items()
                    if key.endswith("_threshold")
                },
                "selected_evaluation_thresholds": selected_thresholds,
                "secondary_gate_passed": bool(
                    thresholds.get("secondary_gate_passed")
                    or thresholds.get("evaluation_gate_passed")
                ),
                "secondary_gate_reason": str(thresholds.get("reason") or ""),
                "secondary_adopted": secondary_adopted,
                "secondary_heldout_activation_count": secondary_heldout_count,
                "base_calibration": dict(base_model.get("calibration") or {}),
                "base_heldout": dict(base_model.get("heldout") or {}),
                "primary_only_calibration": primary_only_calibration,
                "primary_only_heldout": primary_only_heldout,
                "combined_calibration": calibration_metrics,
                "combined_heldout": heldout_metrics,
                "selected_calibration": selected_calibration,
                "selected_heldout": selected_heldout,
            }
        )

    by_kind = {row["model_kind"]: row for row in model_reports}
    gat = by_kind["gat"]
    gat_heldout_ratio = float(gat["selected_heldout"]["net_geomean_ratio"])
    best_non_gat_ratio = min(
        float(by_kind[kind]["selected_heldout"]["net_geomean_ratio"])
        for kind in ("linear", "mlp")
    )
    gat_vs_best_non_gat = gat_heldout_ratio / max(
        1.0e-12, best_non_gat_ratio
    )
    base_gat_ratio = float(gat["base_heldout"]["net_geomean_ratio"])
    selector_heldout_activations = int(
        gat["secondary_heldout_activation_count"]
        if gat["secondary_adopted"]
        else 0
    )
    selector_improves_gat = bool(gat["secondary_adopted"])
    strict_gate_pass = bool(
        gat["secondary_gate_passed"]
        and gat["selected_calibration"]["passes_risk_precision_gate"]
        and gat_heldout_ratio <= 0.90
        and gat_vs_best_non_gat <= 0.98
        and float(base.get("gat_inference_p99_ms") or math.inf) <= 10.0
        and (
            not gat["secondary_adopted"]
            or selector_improves_gat
        )
    )
    positive_net_gate_pass = bool(
        int(gat["selected_calibration"]["activation_count"]) > 0
        and float(gat["selected_calibration"]["net_geomean_ratio"]) < 1.0
        and int(gat["selected_calibration"]["right_censored_count"]) == 0
        and int(gat["selected_calibration"]["unsafe_count"]) == 0
        and int(gat["selected_heldout"]["activation_count"]) > 0
        and gat_heldout_ratio < 1.0
        and int(gat["selected_heldout"]["right_censored_count"]) == 0
        and int(gat["selected_heldout"]["unsafe_count"]) == 0
        and all(
            float(
                gat["selected_heldout"]["per_scale"][str(scale)][
                    "net_geomean_ratio"
                ]
            )
            <= 1.03
            for scale in (30, 50)
        )
        and float(base.get("gat_inference_p99_ms") or math.inf) <= 10.0
    )
    gate_pass = (
        strict_gate_pass
        if args.evaluation_gate_policy == "strict"
        else positive_net_gate_pass
    )
    report = {
        "schema_version": SCHEMA,
        "generated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "development_only": True,
        "deployable": False,
        "deployment_authorized": False,
        "runtime_implemented": False,
        "starts_solver_process": True,
        "action_hierarchy": QG2_COMBINED_ACTION_HIERARCHY_V1,
        "fallback_action": "Q0",
        "all_arms_rejected_action": "Q0",
        "evaluation_gate_policy": str(args.evaluation_gate_policy),
        "minimum_speedup_gate_enabled": bool(
            args.evaluation_gate_policy == "strict"
        ),
        "harmful_rate_confidence_gate_blocks_e2e": bool(
            args.evaluation_gate_policy == "strict"
        ),
        "base_calibration_report": str(base_path),
        "base_calibration_report_sha256": _sha256(base_path),
        "selector_report": str(selector_path),
        "selector_report_sha256": _sha256(selector_path),
        "training_report": str(training_path),
        "training_report_sha256": _sha256(training_path),
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "context_count": len(contexts),
        "secondary_records": secondary_records,
        "models": model_reports,
        "gat_combined_heldout_ratio": gat_heldout_ratio,
        "gat_base_heldout_ratio": base_gat_ratio,
        "gat_vs_best_non_gat_ratio": gat_vs_best_non_gat,
        "selector_heldout_activation_count": selector_heldout_activations,
        "selector_improves_gat": selector_improves_gat,
        "strict_statistical_gate_passed": strict_gate_pass,
        "positive_net_exact_safe_gate_passed": positive_net_gate_pass,
        "combined_candidate_gate_passed": gate_pass,
        "development_e2e_authorized": gate_pass,
        "next_action": (
            "implement_and_hash_combined_runtime_then_e2e"
            if gate_pass
            else "retain_base_qg2_with_literal_q0_fallback"
        ),
    }
    _write(output_path, report)
    print(
        json.dumps(
            {
                "combined_candidate_gate_passed": gate_pass,
                "gat_base_heldout_ratio": base_gat_ratio,
                "gat_combined_heldout_ratio": gat_heldout_ratio,
                "gat_vs_best_non_gat_ratio": gat_vs_best_non_gat,
                "selector_heldout_activation_count": (
                    selector_heldout_activations
                ),
                "output": str(output_path),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0 if gate_pass else 2


def _validate_inputs(
    *,
    base_path: Path,
    base: dict,
    selector_path: Path,
    selector: dict,
) -> tuple[Path, Path, dict[str, str], dict[str, dict], list[dict]]:
    errors = []
    if base.get("schema_version") != BASE_CALIBRATION_SCHEMA:
        errors.append("base_calibration_schema_mismatch")
    if not bool(base.get("development_only")):
        errors.append("base_calibration_development_contract_missing")
    if selector.get("schema_version") != SELECTOR_SCHEMA:
        errors.append("selector_schema_mismatch")
    if bool(selector.get("deployable")) or bool(
        selector.get("deployment_authorized")
    ):
        errors.append("selector_deployment_authority_forbidden")
    if not bool(selector.get("continued_development_recommended")):
        errors.append("selector_not_recommended_for_combined_evaluation")
    if str(selector.get("fallback_action") or "") != "Q0" or str(
        selector.get("all_arms_rejected_action") or ""
    ) != "Q0":
        errors.append("selector_literal_q0_fallback_missing")
    training_path = _resolve(base.get("training_report") or "")
    oracle_path = _resolve(base.get("oracle_summary") or "")
    if not training_path.is_file() or str(
        base.get("training_report_sha256") or ""
    ) != _sha256(training_path):
        errors.append("base_training_binding_mismatch")
        training = {}
    else:
        training = _load(training_path)
        if training.get("schema_version") != TRAINING_SCHEMA:
            errors.append("training_schema_mismatch")
    if not oracle_path.is_file() or str(
        base.get("oracle_summary_sha256") or ""
    ) != _sha256(oracle_path):
        errors.append("base_oracle_binding_mismatch")
        oracle = {}
    else:
        oracle = _load(oracle_path)
        if oracle.get("schema_version") != ORACLE_SCHEMA:
            errors.append("oracle_schema_mismatch")
    split_path = _resolve(training.get("split_path") or "")
    if not split_path.is_file() or str(training.get("split_sha256") or "") != _sha256(
        split_path
    ):
        errors.append("split_binding_mismatch")
        split = {}
    else:
        split = {
            str(key): str(value)
            for key, value in dict(_load(split_path).get("assignments") or {}).items()
        }
    sources = {
        str(row.get("state_hash") or ""): dict(row)
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    seen = set()
    contexts = []
    for row in oracle.get("context_rows") or ():
        state = str(row.get("state_hash") or "")
        instance = str(row.get("instance_hash") or "")
        if state in seen or state not in sources:
            continue
        if split.get(instance) not in {"calibration", "heldout"}:
            continue
        seen.add(state)
        contexts.append(dict(row))
    contexts.sort(key=lambda row: (int(row["scale"]), str(row["state_hash"])))
    models = {str(row.get("model_kind") or "") for row in base.get("models") or ()}
    if models != set(EXPECTED_MODELS):
        errors.append("base_model_universe_mismatch")
    record_keys = {
        (str(row.get("model_kind") or ""), str(row.get("state_hash") or ""))
        for row in base.get("records") or ()
    }
    expected_keys = {
        (kind, str(row["state_hash"]))
        for kind in EXPECTED_MODELS
        for row in contexts
    }
    if record_keys != expected_keys:
        errors.append("base_calibration_record_universe_mismatch")
    source_training = _resolve(selector.get("training_report") or "")
    source_oracle = _resolve(selector.get("oracle_summary") or "")
    if (
        not source_training.is_file()
        or str(selector.get("training_report_sha256") or "")
        != _sha256(source_training)
        or not source_oracle.is_file()
        or str(selector.get("oracle_summary_sha256") or "")
        != _sha256(source_oracle)
    ):
        errors.append("selector_source_binding_mismatch")
    if errors:
        raise ValueError(
            "combined QG2 fresh-process input contract failed:"
            + ",".join(sorted(set(errors)))
        )
    return training_path, oracle_path, split, sources, contexts


def _validate_prediction(
    prediction: dict,
    *,
    prediction_path: Path,
    selector_path: Path,
    source: Mapping[str, Any],
) -> None:
    errors = []
    if prediction.get("schema_version") != QG2_CONTEXT_ARM_SELECTOR_PREDICTION_V1:
        errors.append("prediction_schema_mismatch")
    if bool(prediction.get("deployable")) or not bool(
        prediction.get("development_only")
    ):
        errors.append("prediction_safety_mismatch")
    if str(prediction.get("fallback_action") or "") != "Q0":
        errors.append("prediction_literal_q0_fallback_missing")
    for key, source_key in (
        ("source_state_hash", "state_hash"),
        ("source_engine_hash", "source_engine_hash"),
        ("source_config_hash", "source_config_hash"),
        ("source_exact_action_policy_hash", "source_exact_action_policy_hash"),
    ):
        if str(prediction.get(key) or "") != str(source.get(source_key) or ""):
            errors.append(f"prediction_binding_mismatch:{key}")
    if str(prediction.get("selector_report_sha256") or "") != _sha256(
        selector_path
    ):
        errors.append("prediction_selector_hash_mismatch")
    if not bool(prediction.get("runtime_prethreshold_veto")) and set(
        prediction.get("arms") or {}
    ) != set(SECONDARY_ARMS):
        errors.append("prediction_arm_universe_mismatch")
    if errors:
        raise ValueError(
            f"combined selector prediction invalid:{prediction_path}:"
            + ",".join(sorted(set(errors)))
        )


def _validate_replay(
    replay: dict,
    *,
    path: Path,
    arm: str,
    repeat: int,
    source: Mapping[str, Any],
    bucket: float,
    wall_limit: float,
    memory_limit: float,
) -> None:
    errors = []
    expected = {
        "schema_version": REPLAY_SCHEMA,
        "policy": arm,
        "source_state_hash": str(source["state_hash"]),
        "source_backend_id": str(source["source_backend_id"]),
        "source_engine_hash": str(source["source_engine_hash"]),
        "source_config_hash": str(source["source_config_hash"]),
        "source_exact_action_policy_hash": str(
            source["source_exact_action_policy_hash"]
        ),
    }
    for key, value in expected.items():
        if replay.get(key) != value:
            errors.append(f"replay_binding_mismatch:{key}")
    if int(replay.get("repeat_index") or 0) != int(repeat):
        errors.append("replay_repeat_mismatch")
    for key, value in (
        ("guidance_bucket_width", bucket),
        ("requested_wall_time_limit_sec", wall_limit),
        ("requested_memory_limit_gb", memory_limit),
    ):
        if not math.isclose(
            float(replay.get(key) or 0.0), float(value), rel_tol=0.0, abs_tol=1.0e-12
        ):
            errors.append(f"replay_numeric_binding_mismatch:{key}")
    if replay.get("potential_file_sha256") not in {None, ""}:
        errors.append("secondary_replay_received_potential")
    if replay.get("random_seed") is not None:
        errors.append("secondary_replay_received_random_seed")
    if bool(replay.get("requested_label_trace")):
        errors.append("secondary_replay_label_trace_enabled")
    if errors:
        raise ValueError(
            f"combined secondary replay invalid:{path}:"
            + ",".join(sorted(set(errors)))
        )


def _veto_record(*, context, partition, prediction, prediction_path) -> dict:
    return {
        "state_hash": str(context["state_hash"]),
        "instance_hash": str(context["instance_hash"]),
        "scale": int(context["scale"]),
        "partition": partition,
        "prediction_path": str(prediction_path),
        "prediction_sha256": _sha256(prediction_path),
        "ood": bool(prediction.get("ood")),
        "runtime_prethreshold_veto": True,
        "runtime_prethreshold_veto_reason": str(
            prediction.get("runtime_prethreshold_veto_reason") or ""
        ),
        "tensorization_wall_ms": float(
            prediction.get("tensorization_wall_ms") or 0.0
        ),
        "inference_wall_ms": float(
            prediction.get("inference_wall_ms") or 0.0
        ),
        "arms": {
            arm: {
                "benefit_probability": 0.0,
                "conditional_positive_gain": 0.0,
                "expected_gain": 0.0,
                "ratio": 1.0,
                "outcome_determined": False,
                "right_censored": False,
                "safe": True,
                "eligible": False,
            }
            for arm in SECONDARY_ARMS
        },
    }


def _completed_record(
    *, context, partition, prediction, prediction_path, repeat_rows
) -> dict:
    q0 = statistics.median(row["q0_wall_sec"] for row in repeat_rows)
    arms = {}
    for arm in SECONDARY_ARMS:
        wall = statistics.median(
            row["arms"][arm]["wall_sec"] for row in repeat_rows
        )
        determined = all(
            row["arms"][arm]["outcome_determined"] for row in repeat_rows
        )
        score = dict(prediction["arms"][arm])
        arms[arm] = {
            **score,
            "ratio": wall / max(1.0e-9, q0) if determined else 1.0,
            "outcome_determined": determined,
            "right_censored": not determined,
            "safe": all(row["arms"][arm]["safe"] for row in repeat_rows),
            "eligible": True,
            "median_wall_sec": wall,
        }
    return {
        "state_hash": str(context["state_hash"]),
        "instance_hash": str(context["instance_hash"]),
        "scale": int(context["scale"]),
        "partition": partition,
        "prediction_path": str(prediction_path),
        "prediction_sha256": _sha256(prediction_path),
        "ood": False,
        "runtime_prethreshold_veto": False,
        "runtime_prethreshold_veto_reason": "",
        "tensorization_wall_ms": float(
            prediction.get("tensorization_wall_ms") or 0.0
        ),
        "inference_wall_ms": float(
            prediction.get("inference_wall_ms") or 0.0
        ),
        "q0_median_wall_sec": q0,
        "arms": arms,
    }


def _combined_context(*, kind, context, base_record, secondary) -> CombinedContext:
    primary_eligible = bool(base_record.get("action_eligible", True))
    primary = ArmScore(
        benefit_probability=float(
            base_record.get("benefit_probability") or 0.0
        ),
        expected_gain=float(base_record.get("expected_gain") or 0.0),
        eligible=primary_eligible,
    )
    secondary_scores = {
        arm: ArmScore(
            benefit_probability=float(
                secondary["arms"][arm]["benefit_probability"]
            ),
            expected_gain=float(secondary["arms"][arm]["expected_gain"]),
            eligible=bool(secondary["arms"][arm]["eligible"]),
        )
        for arm in SECONDARY_ARMS
    }
    outcomes = {
        "QG2": ArmOutcome(
            ratio=float(base_record.get("ratio") or 1.0),
            matched_milestone=bool(base_record.get("outcome_determined")),
            exact_safe=bool(base_record.get("safe")),
            right_censored=bool(base_record.get("right_censored")),
        ),
        **{
            arm: ArmOutcome(
                ratio=float(secondary["arms"][arm]["ratio"]),
                matched_milestone=bool(
                    secondary["arms"][arm]["outcome_determined"]
                ),
                exact_safe=bool(secondary["arms"][arm]["safe"]),
                right_censored=bool(
                    secondary["arms"][arm]["right_censored"]
                ),
            )
            for arm in SECONDARY_ARMS
        },
    }
    return CombinedContext(
        state_hash=str(context["state_hash"]),
        instance_hash=str(context["instance_hash"]),
        scale=int(context["scale"]),
        primary_score=primary,
        secondary_scores=secondary_scores,
        outcomes=outcomes,
        ood=False,
    )


def _safe(control, guided) -> bool:
    left = dict(control.get("proof_telemetry") or {})
    right = dict(guided.get("proof_telemetry") or {})
    return bool(
        not guided.get("labels_dropped")
        and all(
            int(right.get(key) or 0) == 0
            for key in (
                "guidance_filter_count",
                "guidance_arc_drop_count",
                "guidance_label_drop_count",
                "guidance_branch_pair_drop_count",
            )
        )
        and all(
            left.get(key) == right.get(key)
            for key in (
                "legal_action_universe_hash_before_sort",
                "legal_arc_universe_hash_before_sort",
            )
        )
        and (
            not (
                control.get("search_exhaustive")
                and guided.get("search_exhaustive")
            )
            or _exact_match(control, guided)
        )
    )


def _exact_match(left, right) -> bool:
    if left.get("global_min_rc") is not None and right.get("global_min_rc") is not None:
        return abs(float(left["global_min_rc"]) - float(right["global_min_rc"])) <= 2.0e-6
    if left.get("proved_no_rc_below") is not None and right.get("proved_no_rc_below") is not None:
        return abs(float(left["proved_no_rc_below"]) - float(right["proved_no_rc_below"])) <= 1.0e-12
    return False


def _effective_wall(row, budget) -> float:
    measured = max(
        1.0e-9,
        float(
            row.get("admission_milestone_wall_sec")
            or row.get("milestone_wall_sec")
            or row.get("total_fresh_process_wall_sec")
            or 0.0
        ),
    )
    return measured if row.get("milestone_reached") else max(measured, budget)


def _matched_milestone_outcome(control, guided) -> bool:
    left = str(control.get("milestone_kind") or "")
    right = str(guided.get("milestone_kind") or "")
    return bool(
        control.get("milestone_reached")
        and guided.get("milestone_reached")
        and left == right
        and left in {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
    )


def _clean_environment(native_build_dir: str) -> dict[str, str]:
    env = dict(os.environ)
    for key in GUIDANCE_ENV_KEYS:
        env.pop(key, None)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{_resolve(native_build_dir)}"
    return env


def _run(command: list[str], *, env: Mapping[str, str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, env=dict(env), check=False)
    if completed.returncode != 0:
        raise SystemExit(
            "combined fresh-process command failed:"
            + " ".join(command)
            + f" returncode={completed.returncode}"
        )


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
