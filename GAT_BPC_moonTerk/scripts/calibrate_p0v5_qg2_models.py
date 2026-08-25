#!/usr/bin/env python3
"""Fresh-process calibration of QG2 Linear/MLP/GAT activation heads."""

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

from lunar_ice_bpc.guidance.qg2_admission_supervision import (  # noqa: E402
    QG2_QUEUE_ACTION_SURFACE_V1,
    QG2_SUPERVISION_SCHEMA_V2,
)

PREDICT = ROOT / "scripts/predict_p0v5_qg2_potential.py"
REPLAY = ROOT / "scripts/replay_p0v5_qg2_label_state_snapshot.py"
SCHEMA = "lunar_ice_bpc.p0v5_qg2_fresh_process_calibration.v4"
REPLAY_SCHEMA = "lunar_ice_bpc.p0v5_qg2_snapshot_replay.v3"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
HARMFUL_RATE_95_UPPER_LIMIT = 0.05


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-report", required=True)
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--scale30-wall-sec", type=float, default=180.0)
    parser.add_argument("--scale50-wall-sec", type=float, default=300.0)
    parser.add_argument("--memory-limit-gb", type=float, default=10.867)
    parser.add_argument("--allowed-engine-hash", action="append", default=[])
    parser.add_argument("--allowed-config-hash", action="append", default=[])
    parser.add_argument(
        "--allowed-exact-action-policy-hash",
        action="append",
        default=[],
    )
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
        raise SystemExit("QG2 calibration training schema mismatch")
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        raise SystemExit("QG2 calibration oracle schema mismatch")
    if not bool(oracle.get("oracle_gate", {}).get("passed")):
        raise SystemExit("QG2 calibration is forbidden before oracle pass")
    if not bool(training.get("oracle_gate_passed")):
        raise SystemExit("QG2 training report is not oracle-authorized")
    split = _load(_resolve(training["split_path"]))["assignments"]
    source_by_state = {
        str(row["state_hash"]): dict(row)
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    contexts = [
        {
            **dict(row),
            **{
                "instance_path": source_by_state[str(row["state_hash"])]["instance_path"],
                "snapshot_path": source_by_state[str(row["state_hash"])]["snapshot_path"],
            },
        }
        for row in oracle.get("context_rows") or ()
        if str(row["state_hash"]) in source_by_state
        and split.get(str(row["instance_hash"])) in {"calibration", "heldout"}
    ]
    minimum_zero_harm_activations = _minimum_zero_harm_sample_size(
        HARMFUL_RATE_95_UPPER_LIMIT
    )
    calibration_context_count = sum(
        split[str(row["instance_hash"])] == "calibration"
        for row in contexts
    )
    if calibration_context_count < minimum_zero_harm_activations:
        raise SystemExit(
            "QG2 calibration is statistically incapable of satisfying the "
            "declared harmful-rate confidence gate: "
            f"calibration_contexts={calibration_context_count} "
            f"required_at_zero_harm={minimum_zero_harm_activations}"
        )
    output_dir = _resolve(args.output_dir)
    output_path = _resolve(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    feature_envelope_path = output_dir / "feature_envelope.json"
    _write(
        feature_envelope_path,
        dict(training.get("feature_envelope") or {}),
    )
    native_build = _resolve(args.native_build_dir)
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT / 'src'}:{native_build}"
    bucket = float(oracle["frozen_guidance_bucket_width"])

    model_reports = []
    all_records = []
    for model_row in training.get("models") or ():
        kind = str(model_row["model_kind"])
        checkpoint = _resolve(model_row["checkpoint_path"])
        records = []
        for context_index, context in enumerate(contexts):
            partition = split[str(context["instance_hash"])]
            context_dir = output_dir / kind / partition / f"{context['scale']}_{context['state_hash'][:16]}"
            context_dir.mkdir(parents=True, exist_ok=True)
            potential_path = context_dir / "potential.json"
            if not potential_path.exists():
                _run([
                    sys.executable, str(PREDICT),
                    "--instance", str(context["instance_path"]),
                    "--snapshot", str(context["snapshot_path"]),
                    "--checkpoint", str(checkpoint),
                    "--feature-envelope", str(feature_envelope_path),
                    "--output", str(potential_path),
                ], env=env)
            potential = _load(potential_path)
            if (
                potential.get("schema_version")
                != "lunar_ice_bpc.p0v5_qg2_label_state_potential.v2"
                or potential.get("supervision_schema_version")
                != QG2_SUPERVISION_SCHEMA_V2
                or potential.get("queue_action_surface")
                != QG2_QUEUE_ACTION_SURFACE_V1
                or str(potential.get("source_state_hash") or "")
                != str(context["state_hash"])
                or str(potential.get("checkpoint_sha256") or "")
                != _sha256(checkpoint)
                or str(potential.get("feature_envelope_sha256") or "")
                != _sha256(feature_envelope_path)
                or str(potential.get("source_engine_hash") or "")
                != str(context.get("source_engine_hash") or "")
                or str(potential.get("source_config_hash") or "")
                != str(context.get("source_config_hash") or "")
                or str(
                    potential.get("source_exact_action_policy_hash") or ""
                )
                != str(
                    context.get("source_exact_action_policy_hash") or ""
                )
            ):
                raise SystemExit(
                    f"stale or mismatched QG2 potential: {potential_path}"
                )
            if bool(potential.get("runtime_prethreshold_veto")):
                record = {
                    "model_kind": kind,
                    "partition": partition,
                    "scale": int(context["scale"]),
                    "instance_hash": str(context["instance_hash"]),
                    "state_hash": str(context["state_hash"]),
                    "benefit_probability": 0.0,
                    "conditional_positive_gain": 0.0,
                    "expected_gain": 0.0,
                    "tensorization_wall_ms": float(
                        potential.get("tensorization_wall_ms") or 0.0
                    ),
                    "inference_wall_ms": float(
                        potential.get("inference_wall_ms") or 0.0
                    ),
                    "q0_median_wall_sec": None,
                    "qg2_net_median_wall_sec": None,
                    "ratio": 1.0,
                    "outcome_determined": False,
                    "right_censored": False,
                    "beneficial": False,
                    "harmful": False,
                    "safe": True,
                    "action_eligible": False,
                    "ood": bool(potential.get("ood")),
                    "prethreshold_veto_reason": str(
                        potential.get("runtime_prethreshold_veto_reason")
                        or "runtime_prethreshold_veto"
                    ),
                    "potential_path": str(potential_path),
                }
                records.append(record)
                all_records.append(record)
                continue
            wall_limit = float(args.scale30_wall_sec) if int(context["scale"]) == 30 else float(args.scale50_wall_sec)
            repeat_rows = []
            for repeat in range(1, max(3, int(args.repeats)) + 1):
                order = ["Q0", "QG2"]
                random.Random(20260801 + context_index * 101 + repeat).shuffle(order)
                outputs = {}
                for arm in order:
                    target = context_dir / (
                        f"{arm.lower()}_{bucket:g}_rep{repeat}.json"
                    )
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
                    if (
                        outputs[arm].get("schema_version") != REPLAY_SCHEMA
                        or str(outputs[arm].get("source_state_hash") or "")
                        != str(context["state_hash"])
                        or str(outputs[arm].get("policy") or "") != arm
                        or int(outputs[arm].get("repeat_index") or 0)
                        != int(repeat)
                        or str(outputs[arm].get("source_backend_id") or "")
                        != str(
                            context.get("source_backend_id")
                            or "native_rcspp_bidirectional_root_partial_hybrid_v3"
                        )
                        or str(outputs[arm].get("source_engine_hash") or "")
                        != str(context.get("source_engine_hash") or "")
                        or str(outputs[arm].get("source_config_hash") or "")
                        != str(context.get("source_config_hash") or "")
                        or str(
                            outputs[arm].get(
                                "source_exact_action_policy_hash"
                            ) or ""
                        )
                        != str(
                            context.get(
                                "source_exact_action_policy_hash"
                            ) or ""
                        )
                        or float(
                            outputs[arm].get(
                                "guidance_bucket_width"
                            ) or 0.0
                        ) != bucket
                        or float(
                            outputs[arm].get(
                                "requested_wall_time_limit_sec"
                            ) or 0.0
                        ) != wall_limit
                        or float(
                            outputs[arm].get(
                                "requested_memory_limit_gb"
                            ) or 0.0
                        ) != float(args.memory_limit_gb)
                        or bool(
                            outputs[arm].get("requested_label_trace")
                        )
                        or str(
                            outputs[arm].get(
                                "potential_file_sha256"
                            ) or ""
                        ) != (
                            _sha256(potential_path)
                            if arm == "QG2"
                            else ""
                        )
                        or outputs[arm].get("random_seed") is not None
                    ):
                        raise SystemExit(
                            f"stale or mismatched calibration replay: {target}"
                        )
                q0_wall = _effective_wall(outputs["Q0"], wall_limit)
                qg2_wall = _effective_wall(outputs["QG2"], wall_limit)
                repeat_rows.append({
                    "repeat": repeat,
                    "q0_wall_sec": q0_wall,
                    "qg2_wall_sec": qg2_wall,
                    "outcome_determined": _matched_milestone_outcome(
                        outputs["Q0"], outputs["QG2"]
                    ),
                    "safe": _safe(outputs["Q0"], outputs["QG2"]),
                })
            inference_sec = (
                float(potential.get("tensorization_wall_ms") or 0.0)
                + float(potential.get("inference_wall_ms") or 0.0)
            ) / 1000.0
            q0 = statistics.median(row["q0_wall_sec"] for row in repeat_rows)
            qg2 = statistics.median(row["qg2_wall_sec"] for row in repeat_rows) + inference_sec
            outcome_determined = all(
                row["outcome_determined"] for row in repeat_rows
            )
            record = {
                "model_kind": kind,
                "partition": partition,
                "scale": int(context["scale"]),
                "instance_hash": str(context["instance_hash"]),
                "state_hash": str(context["state_hash"]),
                "benefit_probability": float(potential["benefit_probability"]),
                "conditional_positive_gain": float(potential["conditional_positive_gain"]),
                "expected_gain": float(potential["expected_gain"]),
                "tensorization_wall_ms": float(potential["tensorization_wall_ms"]),
                "inference_wall_ms": float(potential["inference_wall_ms"]),
                "q0_median_wall_sec": q0,
                "qg2_net_median_wall_sec": qg2,
                "ratio": qg2 / q0 if outcome_determined else 1.0,
                "outcome_determined": outcome_determined,
                "right_censored": not outcome_determined,
                "beneficial": bool(outcome_determined and qg2 < q0),
                "harmful": bool(outcome_determined and qg2 > q0),
                "safe": all(row["safe"] for row in repeat_rows),
                "action_eligible": True,
                "ood": False,
                "prethreshold_veto_reason": "",
                "potential_path": str(potential_path),
            }
            records.append(record)
            all_records.append(record)
            print(json.dumps({
                "model": kind,
                "partition": partition,
                "state": context["state_hash"][:16],
                "ratio": record["ratio"],
                "safe": record["safe"],
            }, sort_keys=True), flush=True)

        calibration = [row for row in records if row["partition"] == "calibration"]
        heldout = [row for row in records if row["partition"] == "heldout"]
        thresholds = _select_thresholds(calibration)
        calibration_metrics = _activation_metrics(calibration, thresholds)
        heldout_metrics = _activation_metrics(heldout, thresholds)
        model_reports.append({
            "model_kind": kind,
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": _sha256(checkpoint),
            "thresholds": thresholds,
            "calibration": calibration_metrics,
            "heldout": heldout_metrics,
        })

    by_kind = {row["model_kind"]: row for row in model_reports}
    gat = by_kind.get("gat") or {}
    non_gat = [
        row["heldout"]["net_geomean_ratio"]
        for kind, row in by_kind.items()
        if kind in {"linear", "mlp"}
    ]
    best_non_gat = min(non_gat, default=1.0e30)
    gat_ratio = float((gat.get("heldout") or {}).get("net_geomean_ratio", 1.0e30))
    gat_advantage_ratio = (
        gat_ratio / best_non_gat if best_non_gat < 1.0e29 else 1.0e30
    )
    inference = sorted(
        float(row["inference_wall_ms"])
        for row in all_records
        if row["model_kind"] == "gat" and row["partition"] == "heldout"
    )
    inference_p99 = _quantile(inference, 0.99)
    gate_pass = bool(
        gat
        and (gat.get("calibration") or {}).get("passes_risk_precision_gate")
        and (gat.get("heldout") or {}).get("net_geomean_ratio", 1.0) <= 0.90
        and gat_advantage_ratio <= 0.98
        and inference_p99 <= 10.0
        and all(row["safe"] for row in all_records if row["model_kind"] == "gat")
    )
    observed_engine_hashes = sorted({
        str(row.get("source_engine_hash") or "")
        for row in contexts
        if str(row.get("source_engine_hash") or "")
    })
    observed_config_hashes = sorted({
        str(row.get("source_config_hash") or "")
        for row in contexts
        if str(row.get("source_config_hash") or "")
    })
    observed_action_policy_hashes = sorted({
        str(row.get("source_exact_action_policy_hash") or "")
        for row in contexts
        if str(row.get("source_exact_action_policy_hash") or "")
    })
    requested_engine_hashes = sorted(set(args.allowed_engine_hash))
    requested_config_hashes = sorted(set(args.allowed_config_hash))
    requested_action_policy_hashes = sorted(set(
        args.allowed_exact_action_policy_hash
    ))
    if (
        requested_engine_hashes
        and requested_engine_hashes != observed_engine_hashes
    ):
        raise SystemExit(
            "QG2 allowed engine hashes do not match oracle source hashes"
        )
    if (
        requested_config_hashes
        and requested_config_hashes != observed_config_hashes
    ):
        raise SystemExit(
            "QG2 allowed config hashes do not match oracle source hashes"
        )
    if (
        requested_action_policy_hashes
        and requested_action_policy_hashes
        != observed_action_policy_hashes
    ):
        raise SystemExit(
            "QG2 allowed exact action-policy hashes do not match oracle source hashes"
        )
    hashes_present = bool(
        observed_engine_hashes and observed_action_policy_hashes
    )
    deployment_authorized = bool(gate_pass and hashes_present)
    manifest = _manifest(
        training=training,
        oracle=oracle,
        gat=gat,
        gate_pass=gate_pass,
        deployment_authorized=deployment_authorized,
        allowed_engines=observed_engine_hashes,
        allowed_action_policies=observed_action_policy_hashes,
        observed_configs=observed_config_hashes,
        gat_advantage_ratio=gat_advantage_ratio,
    )
    manifest_path = output_dir / "qg2_gat_manifest.json"
    _write(manifest_path, manifest)
    report = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": deployment_authorized,
        "training_report": str(training_path),
        "training_report_sha256": _sha256(training_path),
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "bucket_width": bucket,
        "minimum_zero_harm_calibration_activations": (
            minimum_zero_harm_activations
        ),
        "records": all_records,
        "models": model_reports,
        "gat_vs_best_non_gat_ratio": gat_advantage_ratio,
        "gat_inference_p99_ms": inference_p99,
        "observed_exact_engine_hashes": observed_engine_hashes,
        "observed_exact_config_hashes": observed_config_hashes,
        "observed_exact_action_policy_hashes": (
            observed_action_policy_hashes
        ),
        "gate_pass": gate_pass,
        "deployment_authorized": deployment_authorized,
        "deployment_blocker": "" if deployment_authorized else (
            "exact_engine_and_action_policy_hashes_required"
            if gate_pass and not hashes_present
            else "fresh_process_calibration_gate_failed"
        ),
        "manifest_path": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
    }
    _write(output_path, report)
    print(json.dumps({
        "gate_pass": gate_pass,
        "deployment_authorized": deployment_authorized,
        "gat_vs_best_non_gat_ratio": gat_advantage_ratio,
        "gat_inference_p99_ms": inference_p99,
    }, sort_keys=True))
    return 0 if gate_pass else 2


def _select_thresholds(rows: list[dict]):
    eligible = [
        row for row in rows
        if row.get("action_eligible", True)
        and row.get("outcome_determined")
    ]
    if not eligible:
        return {"probability_threshold": 1.0, "expected_gain_threshold": 1.0e30}
    p_values = sorted({float(row["benefit_probability"]) for row in eligible})
    g_values = sorted({float(row["expected_gain"]) for row in eligible})
    best = None
    for p in p_values:
        for g in g_values:
            metrics = _activation_metrics(rows, {
                "probability_threshold": p,
                "expected_gain_threshold": g,
            })
            if not metrics["passes_risk_precision_gate"]:
                continue
            candidate = (
                metrics["net_geomean_ratio"],
                -metrics["activation_count"],
                p,
                g,
            )
            if best is None or candidate < best[0]:
                best = (candidate, p, g)
    return {
        "probability_threshold": 1.0 if best is None else best[1],
        "expected_gain_threshold": 1.0e30 if best is None else best[2],
    }


def _activation_metrics(rows: list[dict], thresholds: dict):
    eligible = [row for row in rows if row.get("action_eligible", True)]
    determined = [row for row in eligible if row.get("outcome_determined")]
    selected = [
        row for row in determined
        if float(row["benefit_probability"]) >= float(thresholds["probability_threshold"])
        and float(row["expected_gain"]) >= float(thresholds["expected_gain_threshold"])
    ]
    harmful = sum(bool(row["harmful"]) for row in selected)
    beneficial = sum(bool(row["beneficial"]) for row in selected)
    harmful_upper = _wilson(harmful, len(selected))[1]
    precision_lower = _wilson(beneficial, len(selected))[0]
    ratios = [float(row["ratio"]) if row in selected else 1.0 for row in rows]
    return {
        "context_count": len(rows),
        "determined_context_count": len(determined),
        "right_censored_context_count": len(eligible) - len(determined),
        "action_eligible_context_count": len(eligible),
        "prethreshold_veto_context_count": len(rows) - len(eligible),
        "ood_context_count": sum(bool(row.get("ood")) for row in rows),
        "activation_count": len(selected),
        "harmful_count": harmful,
        "beneficial_count": beneficial,
        "harmful_rate_95_upper": harmful_upper,
        "beneficial_precision_95_lower": precision_lower,
        "net_geomean_ratio": _geomean(ratios),
        "all_safe": all(row["safe"] for row in rows),
        "passes_risk_precision_gate": bool(
            selected
            and harmful_upper <= 0.05
            and precision_lower >= 0.80
            and all(row["safe"] for row in rows)
        ),
    }


def _manifest(
    *, training, oracle, gat, gate_pass, deployment_authorized,
    allowed_engines, allowed_action_policies, observed_configs,
    gat_advantage_ratio,
):
    from lunar_ice_bpc.guidance.proof_queue_label_state_runtime import (
        QG2_RUNTIME_POLICY_ID,
        qg2_runtime_implementation_hash,
    )

    checkpoint = str(gat.get("checkpoint_path") or "")
    thresholds = dict(gat.get("thresholds") or {})
    calibration = dict(gat.get("calibration") or {})
    heldout = dict(gat.get("heldout") or {})
    return {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_manifest.v1",
        "runtime_policy_id": QG2_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": qg2_runtime_implementation_hash(),
        "feature_schema_version": "lunar_ice_bpc.p0v5_qg2_features.v1",
        "label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        "guidance_bucket_width": float(oracle["frozen_guidance_bucket_width"]),
        "checkpoint_path": checkpoint,
        "checkpoint_sha256": _sha256(_resolve(checkpoint)) if checkpoint else "",
        "training_data_hash": str(training["training_data_hash"]),
        "allowed_scales": [30, 50],
        "allowed_exact_engine_hashes": sorted(set(str(value) for value in allowed_engines)),
        "allowed_exact_action_policy_hashes": sorted(set(
            str(value) for value in allowed_action_policies
        )),
        # The full config hash is a dynamic request-state binding.  Preserve
        # it for provenance, but never use it as a held-out activation
        # allowlist.
        "source_exact_config_hashes_observed_diagnostic_only": sorted(set(
            str(value) for value in observed_configs
        )),
        "evaluation_authorized": bool(gate_pass),
        "evaluation_force_qg2": True,
        "deployment_authorized": bool(deployment_authorized),
        "oracle_gate": dict(oracle["oracle_gate"]),
        "feature_envelope": dict(training.get("feature_envelope") or {}),
        "ood_policy_version": "instance_split_feature_envelope.v1",
        "torch_num_threads": 1,
        "calibration": {
            "gate_pass": bool(gate_pass),
            "probability_threshold": float(thresholds.get("probability_threshold", 1.0)),
            "expected_gain_threshold": float(thresholds.get("expected_gain_threshold", 1.0e30)),
            "harmful_rate_95_upper": float(calibration.get("harmful_rate_95_upper", 1.0)),
            "beneficial_precision_95_lower": float(calibration.get("beneficial_precision_95_lower", 0.0)),
            "heldout_tail_ratio": float(heldout.get("net_geomean_ratio", 1.0)),
            "gat_vs_best_non_gat_ratio": float(gat_advantage_ratio),
        },
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "fallback": "P0V4_V5_Q0",
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
    return measured if row.get("milestone_reached") else max(
        measured, budget
    )


def _matched_milestone_outcome(control, guided):
    left = str(control.get("milestone_kind") or "")
    right = str(guided.get("milestone_kind") or "")
    return bool(
        control.get("milestone_reached")
        and guided.get("milestone_reached")
        and left == right
        and left in {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
    )


def _wilson(successes, total, z=1.6448536269514722):
    """One-sided 95% Wilson bound used by the declared risk gates."""
    if total <= 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def _minimum_zero_harm_sample_size(limit: float) -> int:
    threshold = max(0.0, min(1.0, float(limit)))
    for total in range(1, 1_000_001):
        if _wilson(0, total)[1] <= threshold:
            return total
    raise ValueError("harmful-rate confidence threshold is unreachable")


def _geomean(values):
    return 1.0e30 if not values else math.exp(statistics.fmean(math.log(max(1.0e-12, float(value))) for value in values))


def _quantile(values, q):
    if not values:
        return 1.0e30
    index = min(len(values) - 1, max(0, math.ceil(q * len(values)) - 1))
    return values[index]


def _run(command, *, env):
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def _resolve(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
