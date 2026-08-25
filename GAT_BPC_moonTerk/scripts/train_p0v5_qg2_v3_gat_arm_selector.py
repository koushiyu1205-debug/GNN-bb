#!/usr/bin/env python3
"""Train the GAT-first Q0/QG2/QD1/QB1 selector from actual arm outcomes."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import statistics
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_gat_arm_selector_training.v3"
CONTROL_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_arm_selector_control_training.v3"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
RANKER_TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_ranker_training.v1"
FORCE_ON_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_gat_force_on_calibration.v1"
MATCHED_ARM_SCHEMA = "lunar_ice_bpc.p0v5_qg2_realmap_v4_matched_arms.v1"
ARMS = ("QG2", "QD1", "QB1")
TRAINABLE_ARMS = ("QD1", "QB1")
LOSS_CONTRACT = {
    "benefit_weight": 1.0,
    "positive_gain_weight": 0.5,
    "adverse_weight": 1.0,
    "matched_pairwise_arm_rank_weight": 0.25,
    "rank_target": "clipped_one_minus_matched_wall_ratio",
    "censored_rank_masked": True,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--ranker-training-report", required=True)
    parser.add_argument(
        "--matched-arm-report",
        help="required by the real-map V4 protocol for replicated QD1/QB1 labels",
    )
    parser.add_argument(
        "--qg2-force-on-report", action="append", required=True,
        help=(
            "repeat for train/calibration/heldout when QG2 has positive "
            "force-on evidence"
        ),
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--model-kind", choices=("gat", "mlp", "linear"), default="gat"
    )
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--seed", type=int, default=20260806)
    parser.add_argument("--early-stopping-patience", type=int, default=25)
    args = parser.parse_args()

    import torch
    from lunar_ice_bpc.guidance.qg2_unified_arm_selector_v3 import (
        QG2V3GraphArmSelector,
        QG2V3LinearGraphArmSelector,
        QG2V3MLPArmSelector,
        QG2_V4_SELECTOR_CHECKPOINT_SCHEMA,
        qg2_v3_selector_loss,
    )

    oracle_path = _resolve(args.oracle_summary)
    ranker_path = _resolve(args.ranker_training_report)
    matched_path = (
        None if not args.matched_arm_report
        else _resolve(args.matched_arm_report)
    )
    force_paths = [_resolve(value) for value in args.qg2_force_on_report]
    oracle = _load(oracle_path)
    ranker = _load(ranker_path)
    matched = None if matched_path is None else _load(matched_path)
    forces = [_load(path) for path in force_paths]
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        raise SystemExit("QG2 V3 selector oracle schema mismatch")
    if ranker.get("schema_version") != RANKER_TRAINING_SCHEMA:
        raise SystemExit("QG2 V3 selector ranker schema mismatch")
    if matched is not None:
        _validate_matched_arm_report(
            matched, matched_path,
            oracle_path=oracle_path,
            split_path=_resolve(ranker["split_path"]),
        )
    if any(force.get("schema_version") != FORCE_ON_SCHEMA for force in forces):
        raise SystemExit("QG2 V3 selector force-on schema mismatch")
    _validate_force_bindings(
        forces, force_paths, oracle_path=oracle_path, ranker_path=ranker_path
    )
    qg2_records = _force_records(forces)
    qg2_screen = _qg2_screen(qg2_records)
    qg2_enabled = _qg2_arm_is_trainable(qg2_screen)
    qg2_veto = not qg2_enabled
    trainable_arms = ARMS if qg2_enabled else TRAINABLE_ARMS

    split = _load(_resolve(ranker["split_path"]))["assignments"]
    normalization = _load(_resolve(ranker["normalization_path"]))
    examples, rejections = _load_examples(
        oracle, split,
        qg2_records=qg2_records,
        qg2_enabled=qg2_enabled,
        matched_arm_records=(
            {} if matched is None else {
                str(row["state_hash"]): dict(row)
                for row in matched.get("records") or ()
            }
        ),
        matched_arms_required=matched is not None,
    )
    partitions = {
        name: [row for row in examples if row["partition"] == name]
        for name in ("train", "calibration", "heldout")
    }
    if not partitions["train"] or not partitions["calibration"]:
        raise SystemExit("QG2 V3 selector lacks train/calibration examples")
    class_weights = _class_balance_weights(
        partitions["train"], trainable_arms=trainable_arms
    )

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    curve_path = output_dir / "training_curve.jsonl"
    if curve_path.exists():
        raise SystemExit("QG2 V3 selector output already exists")
    model_kind = str(args.model_kind)
    model = {
        "gat": QG2V3GraphArmSelector,
        "mlp": QG2V3MLPArmSelector,
        "linear": QG2V3LinearGraphArmSelector,
    }[model_kind](normalization)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=float(args.learning_rate)
    )
    best_calibration_loss = math.inf
    best_epoch = 0
    best_state = None
    stale_epochs = 0
    epochs_completed = 0
    for epoch in range(1, max(1, int(args.epochs)) + 1):
        started = perf_counter()
        order = list(partitions["train"])
        random.Random(int(args.seed) + epoch).shuffle(order)
        component_rows = []
        model.train()
        for row in order:
            optimizer.zero_grad()
            predictions = model(**row["features"].to_tensors())
            targets = _target_tensors(row, trainable_arms=trainable_arms)
            losses = qg2_v3_selector_loss(
                predictions=predictions, **targets,
                **_class_weight_tensors(class_weights),
            )
            losses["total_loss"].backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
            component_rows.append({
                key: float(value.detach()) for key, value in losses.items()
            })
        calibration_loss = _mean_selector_loss(
            model, partitions["calibration"],
            trainable_arms=trainable_arms,
            class_weights=class_weights,
        )
        improved = bool(
            calibration_loss["total_loss"]
            < best_calibration_loss - 1.0e-8
        )
        if improved:
            best_calibration_loss = calibration_loss["total_loss"]
            best_epoch = epoch
            best_state = copy.deepcopy(model.state_dict())
            stale_epochs = 0
        else:
            stale_epochs += 1
        epochs_completed = epoch
        curve = {
            "model": f"{model_kind}_arm_selector",
            "epoch": epoch,
            **{
                key: statistics.fmean(row[key] for row in component_rows)
                for key in (
                    "total_loss", "rank_loss", "benefit_loss",
                    "positive_gain_loss", "adverse_loss",
                )
            },
            "calibration_total_loss": calibration_loss["total_loss"],
            "calibration_benefit_loss": calibration_loss["benefit_loss"],
            "calibration_positive_gain_loss": calibration_loss[
                "positive_gain_loss"
            ],
            "calibration_adverse_loss": calibration_loss["adverse_loss"],
            "is_best_epoch": improved,
            "epoch_wall_sec": perf_counter() - started,
        }
        _append_jsonl(curve_path, curve)
        print(json.dumps(curve, sort_keys=True), flush=True)
        if stale_epochs >= max(1, int(args.early_stopping_patience)):
            break

    if best_state is None:
        raise SystemExit("QG2 V4 selector failed to select a calibration epoch")
    model.load_state_dict(best_state, strict=True)
    checkpoint = output_dir / f"qg2_v3_{model_kind}_arm_selector.pt"
    torch.save({
        "schema_version": QG2_V4_SELECTOR_CHECKPOINT_SCHEMA,
        "input_parity_contract": (
            "node_edge_context_identical_gat_topology_only_difference.v1"
        ),
        "model_kind": model_kind,
        "action_universe": ["Q0", *ARMS],
        "trainable_arms": list(trainable_arms),
        "forced_veto_arms": ["QG2"] if qg2_veto else [],
        "fallback_action": "Q0",
        "normalization": normalization,
        "state_dict": model.state_dict(),
        "activation_authority": False,
        "deployment_authorized": False,
        "checkpoint_selection_partition": "calibration",
        "checkpoint_selection_metric": "total_loss",
        "best_epoch": best_epoch,
        "class_balance_weights": class_weights,
        "loss_contract": LOSS_CONTRACT,
    }, checkpoint)
    predictions = {
        partition: _predict(model, rows)
        for partition, rows in partitions.items()
    }
    thresholds, threshold_search = _choose_thresholds(
        predictions["calibration"], trainable_arms=trainable_arms
    )
    reports = {
        partition: _evaluate_policy(rows, thresholds)
        for partition, rows in predictions.items()
    }
    uncertainty = {
        partition: _policy_uncertainty(
            rows, thresholds, seed=int(args.seed) + index * 1009
        )
        for index, (partition, rows) in enumerate(predictions.items())
    }
    classification = {
        partition: _classification_metrics(rows, trainable_arms=trainable_arms)
        for partition, rows in predictions.items()
    }
    arm_rank_metrics = {
        partition: _arm_rank_metrics(rows, trainable_arms=trainable_arms)
        for partition, rows in predictions.items()
    }
    report = {
        "schema_version": SCHEMA if model_kind == "gat" else CONTROL_SCHEMA,
        "development_only": True,
        "deployable": False,
        "model_order": ["gat", "mlp", "linear"],
        "trained_model": model_kind,
        "parameter_count": sum(
            int(parameter.numel()) for parameter in model.parameters()
        ),
        "action_universe": ["Q0", *ARMS],
        "trainable_arms": list(trainable_arms),
        "forced_veto_arms": ({
            "QG2": {
                "reason": "real_map_force_on_lacks_trainable_positive_support",
                "screen_summary": qg2_screen,
            }
        } if qg2_veto else {}),
        "all_rejected_action": "Q0",
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "ranker_training_report": str(ranker_path),
        "ranker_training_report_sha256": _sha256(ranker_path),
        "matched_arm_report": (
            None if matched_path is None else str(matched_path)
        ),
        "matched_arm_report_sha256": (
            None if matched_path is None else _sha256(matched_path)
        ),
        "qg2_force_on_reports": [str(path) for path in force_paths],
        "qg2_force_on_report_sha256": {
            str(path): _sha256(path) for path in force_paths
        },
        "qg2_force_on_screen": qg2_screen,
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "training_curve_path": str(curve_path),
        "training_curve_sha256": _sha256(curve_path),
        "checkpoint_selection_partition": "calibration",
        "checkpoint_selection_metric": "total_loss",
        "best_epoch": best_epoch,
        "epochs_completed": epochs_completed,
        "early_stopping_patience": max(
            1, int(args.early_stopping_patience)
        ),
        "class_balance_weights": class_weights,
        "loss_contract": LOSS_CONTRACT,
        "normalization_path": str(_resolve(ranker["normalization_path"])),
        "normalization_sha256": _sha256(_resolve(ranker["normalization_path"])),
        "context_count": len(examples),
        "instance_count": len({row["instance_hash"] for row in examples}),
        "rejection_counts": rejections,
        "partition_counts": {
            key: len(value) for key, value in partitions.items()
        },
        "classification_metrics": classification,
        "arm_rank_metrics": arm_rank_metrics,
        "thresholds": thresholds,
        "threshold_selection": {
            **threshold_search,
            "selection_partition": "calibration",
            "selection_rule": (
                "zero_harm_then_harmful_wilson_upper_then_beneficial_wilson_"
                "lower_then_net_geomean_then_coverage.v1"
            ),
            "confidence_intervals_are_reporting_not_a_small_sample_hard_gate": True,
        },
        "partition_reports": reports,
        "partition_uncertainty": uncertainty,
        "fresh_process_validation_required": True,
        "deployment_authorized": False,
    }
    _write(output_dir / "training_report.json", report)
    print(json.dumps({
        "calibration": reports["calibration"],
        "calibration_uncertainty": uncertainty["calibration"],
        "heldout": reports["heldout"],
        "heldout_uncertainty": uncertainty["heldout"],
        "thresholds": thresholds,
    }, sort_keys=True), flush=True)
    return 0


@dataclass(frozen=True)
class _QG2ForceOutcome:
    wall_sec: float
    ratio: float
    milestone_matched: bool
    right_censored: bool
    beneficial: bool
    harmful: bool
    positive_gain_fraction: float


def _validate_force_bindings(
    forces, force_paths, *, oracle_path, ranker_path
):
    partitions = []
    for force, path in zip(forces, force_paths, strict=True):
        if _resolve(force.get("oracle_summary") or "") != oracle_path:
            raise SystemExit(f"QG2 force-on oracle binding mismatch: {path}")
        if str(force.get("oracle_summary_sha256") or "") != _sha256(
            oracle_path
        ):
            raise SystemExit(f"QG2 force-on oracle hash mismatch: {path}")
        if _resolve(force.get("training_report") or "") != ranker_path:
            raise SystemExit(f"QG2 force-on ranker binding mismatch: {path}")
        if str(force.get("training_report_sha256") or "") != _sha256(
            ranker_path
        ):
            raise SystemExit(f"QG2 force-on ranker hash mismatch: {path}")
        partitions.append(str(force.get("partition") or ""))
    if len(set(partitions)) != len(partitions):
        raise SystemExit("QG2 force-on reports repeat a partition")


def _validate_matched_arm_report(
    report, report_path, *, oracle_path, split_path
):
    if report.get("schema_version") != MATCHED_ARM_SCHEMA:
        raise SystemExit("QG2 V4 matched-arm report schema mismatch")
    if not bool(report.get("all_safe")) or bool(report.get("deployable")):
        raise SystemExit("QG2 V4 matched-arm safety contract failed")
    if _resolve(report.get("oracle_summary") or "") != oracle_path or str(
        report.get("oracle_summary_sha256") or ""
    ) != _sha256(oracle_path):
        raise SystemExit(f"QG2 V4 matched-arm Oracle drift: {report_path}")
    if _resolve(report.get("instance_split") or "") != split_path or str(
        report.get("instance_split_sha256") or ""
    ) != _sha256(split_path):
        raise SystemExit(f"QG2 V4 matched-arm split drift: {report_path}")
    if int(report.get("repeat_count") or 0) < 3:
        raise SystemExit("QG2 V4 matched-arm report lacks three replicates")


def _force_records(forces):
    result = {}
    for force in forces:
        declared_partition = str(force.get("partition") or "")
        for source in force.get("records") or ():
            row = dict(source)
            state = str(row.get("state_hash") or "")
            if not state or state in result:
                raise SystemExit("QG2 force-on records contain duplicate state")
            if str(row.get("partition") or "") != declared_partition:
                raise SystemExit("QG2 force-on record partition drift")
            result[state] = row
    return result


def _qg2_screen(records):
    def summarize(rows):
        outcomes = [_force_outcome(row) for row in rows]
        available = [outcome for outcome in outcomes if outcome is not None]
        return {
            "record_count": len(rows),
            "safe_count": sum(bool(row.get("safe")) for row in rows),
            "available_outcome_count": len(available),
            "beneficial_count": sum(outcome.beneficial for outcome in available),
            "harmful_count": sum(outcome.harmful for outcome in available),
            "net_geomean_ratio": _geomean([
                outcome.ratio for outcome in available
            ]),
        }
    partitions = {
        name: summarize([
            row for row in records.values()
            if str(row.get("partition") or "") == name
        ])
        for name in ("train", "calibration", "heldout")
    }
    return {
        "arm_enable_authority_partition": "train",
        "minimum_train_available_outcomes": 5,
        "minimum_train_beneficial_outcomes": 2,
        "partitions": partitions,
    }


def _qg2_arm_is_trainable(screen):
    train = dict(screen["partitions"]["train"])
    return bool(
        int(train["available_outcome_count"]) >= int(
            screen["minimum_train_available_outcomes"]
        )
        and int(train["beneficial_count"]) >= int(
            screen["minimum_train_beneficial_outcomes"]
        )
        and int(train["safe_count"]) == int(train["record_count"])
    )


def _force_outcome(record):
    if not record or not bool(record.get("safe")) or not bool(
        record.get("action_eligible")
    ):
        return None
    comparison = str(record.get("comparison_class") or "")
    if comparison in {
        "both_censored", "literal_q0_veto", "replicate_class_disagreement",
    }:
        return None
    beneficial = bool(
        record.get("beneficial") or comparison == "gat_beneficial_censor"
    )
    harmful = bool(
        record.get("harmful") or record.get("adverse_target")
        or comparison in {"gat_adverse_censor", "milestone_mismatch"}
    )
    return _QG2ForceOutcome(
        wall_sec=float(record.get("gat_net_median_wall_sec") or 0.0),
        ratio=float(record.get("ratio") or 1.0),
        milestone_matched=(comparison == "matched_milestone"),
        right_censored=(comparison != "matched_milestone"),
        beneficial=beneficial,
        harmful=harmful,
        positive_gain_fraction=float(
            record.get("relative_positive_gain") or 0.0
        ),
    )


def _matched_outcome(record, arm):
    payload = dict(dict(record or {}).get("outcomes") or {}).get(arm)
    if not payload or not bool(record.get("safe")) or not bool(
        payload.get("outcome_determined")
    ):
        return None
    comparison = str(payload.get("comparison_class") or "")
    return _QG2ForceOutcome(
        wall_sec=float(payload.get("arm_median_wall_sec") or 0.0),
        ratio=float(payload.get("ratio") or 1.0),
        milestone_matched=(comparison == "matched_milestone"),
        right_censored=bool(payload.get("right_censored")),
        beneficial=bool(payload.get("beneficial")),
        harmful=bool(payload.get("harmful")),
        positive_gain_fraction=float(
            payload.get("positive_gain_fraction") or 0.0
        ),
    )


def _load_examples(
    oracle, assignments, *, qg2_records=None, qg2_enabled=False,
    matched_arm_records=None, matched_arms_required=False,
):
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
    from lunar_ice_bpc.guidance.qg2_context_arm_selector import (
        qg2_features_from_snapshot,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        normalize_qg2_v3_features,
    )

    old = _load_old_selector_helpers()
    context_rows, rejections = old._load_examples(oracle, assignments)
    source_by_state = {
        str(row["state_hash"]): dict(row)
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    qg2_records = dict(qg2_records or {})
    matched_arm_records = dict(matched_arm_records or {})
    result = []
    for row in context_rows:
        force_record = qg2_records.get(str(row["state_hash"]))
        if qg2_enabled and _force_outcome(force_record) is None:
            rejections["qg2_force_outcome_unavailable"] = (
                rejections.get("qg2_force_outcome_unavailable", 0) + 1
            )
            continue
        matched_record = matched_arm_records.get(str(row["state_hash"]))
        if matched_arms_required and any(
            _matched_outcome(matched_record, arm) is None
            for arm in TRAINABLE_ARMS
        ):
            rejections["replicated_matched_arm_outcome_unavailable"] = (
                rejections.get(
                    "replicated_matched_arm_outcome_unavailable", 0
                ) + 1
            )
            continue
        source = source_by_state[str(row["state_hash"])]
        snapshot = _load(_resolve(source["snapshot_path"]))
        data = load_lunar_ice_data(_load(_resolve(source["instance_path"])))
        outcomes = dict(row["outcomes"])
        if matched_arms_required:
            for arm in TRAINABLE_ARMS:
                outcomes[arm] = _matched_outcome(matched_record, arm)
        outcomes["QG2"] = (
            _force_outcome(force_record) if qg2_enabled else None
        )
        result.append({
            **row,
            "outcomes": outcomes,
            "qg2_force_record": force_record if qg2_enabled else None,
            "features": normalize_qg2_v3_features(
                data, qg2_features_from_snapshot(data, snapshot)
            ),
            "milestone_kind": str(
                _load(_resolve(source["q0_path"])).get("milestone_kind") or ""
            ),
        })
    return result, rejections


def _target_tensors(row, *, trainable_arms=TRAINABLE_ARMS):
    import torch

    benefit = []
    gain = []
    adverse = []
    outcome_mask = []
    positive_mask = []
    adverse_mask = []
    utility = []
    utility_mask = []
    for arm in ARMS:
        outcome = row["outcomes"].get(arm)
        if arm not in trainable_arms or outcome is None:
            benefit.append(0.0)
            gain.append(0.0)
            adverse.append(1.0)
            outcome_mask.append(False)
            positive_mask.append(False)
            adverse_mask.append(False)
            utility.append(0.0)
            utility_mask.append(False)
            continue
        beneficial = bool(outcome.beneficial)
        harmful = bool(outcome.harmful)
        benefit.append(1.0 if beneficial else 0.0)
        gain.append(float(outcome.positive_gain_fraction) if beneficial else 0.0)
        adverse.append(1.0 if harmful else 0.0)
        outcome_mask.append(True)
        positive_mask.append(beneficial and not outcome.right_censored)
        adverse_mask.append(True)
        utility.append(max(-1.0, min(1.0, 1.0 - float(outcome.ratio))))
        utility_mask.append(bool(
            outcome.milestone_matched and not outcome.right_censored
        ))
    shape = (1, len(ARMS))
    return {
        "benefit_target": torch.tensor(benefit, dtype=torch.float32).reshape(shape),
        "positive_gain_target": torch.tensor(gain, dtype=torch.float32).reshape(shape),
        "adverse_target": torch.tensor(adverse, dtype=torch.float32).reshape(shape),
        "outcome_mask": torch.tensor(outcome_mask, dtype=torch.bool).reshape(shape),
        "positive_mask": torch.tensor(positive_mask, dtype=torch.bool).reshape(shape),
        "adverse_mask": torch.tensor(adverse_mask, dtype=torch.bool).reshape(shape),
        "utility_target": torch.tensor(utility, dtype=torch.float32).reshape(shape),
        "utility_mask": torch.tensor(utility_mask, dtype=torch.bool).reshape(shape),
    }


def _class_balance_weights(rows, *, trainable_arms):
    result = {"benefit_positive_weight": [], "adverse_positive_weight": []}
    for arm in ARMS:
        outcomes = [
            row["outcomes"].get(arm) for row in rows
            if arm in trainable_arms and row["outcomes"].get(arm) is not None
        ]
        for key, attribute in (
            ("benefit_positive_weight", "beneficial"),
            ("adverse_positive_weight", "harmful"),
        ):
            positives = sum(bool(getattr(row, attribute)) for row in outcomes)
            negatives = len(outcomes) - positives
            weight = (
                1.0 if positives == 0 or negatives == 0
                else min(4.0, max(0.25, negatives / positives))
            )
            result[key].append(weight)
    return result


def _class_weight_tensors(weights):
    import torch
    return {
        key: torch.tensor(value, dtype=torch.float32).reshape(1, len(ARMS))
        for key, value in weights.items()
    }


def _mean_selector_loss(
    model, rows, *, trainable_arms, class_weights
):
    import torch
    from lunar_ice_bpc.guidance.qg2_unified_arm_selector_v3 import (
        qg2_v3_selector_loss,
    )

    if not rows:
        raise ValueError("selector calibration partition is empty")
    values = []
    model.eval()
    with torch.inference_mode():
        for row in rows:
            values.append({
                key: float(value)
                for key, value in qg2_v3_selector_loss(
                    predictions=model(**row["features"].to_tensors()),
                    **_target_tensors(
                        row, trainable_arms=trainable_arms
                    ),
                    **_class_weight_tensors(class_weights),
                ).items()
            })
    return {
        key: statistics.fmean(row[key] for row in values)
        for key in (
            "total_loss", "rank_loss", "benefit_loss",
            "positive_gain_loss", "adverse_loss",
        )
    }


def _predict(model, rows):
    result = []
    model.eval()
    import torch
    with torch.inference_mode():
        for row in rows:
            output = model(**row["features"].to_tensors())
            arms = {}
            for index, arm in enumerate(ARMS):
                arms[arm] = {
                    "benefit_probability": float(output["benefit_probability"][0, index]),
                    "conditional_positive_gain": float(output["conditional_positive_gain"][0, index]),
                    "adverse_probability": float(output["adverse_probability"][0, index]),
                    "outcome": row["outcomes"].get(arm),
                }
                arms[arm]["expected_gain"] = (
                    arms[arm]["benefit_probability"]
                    * arms[arm]["conditional_positive_gain"]
                )
            result.append({
                "state_hash": row["state_hash"],
                "instance_hash": row["instance_hash"],
                "scale": row["scale"],
                "milestone_kind": row["milestone_kind"],
                "arms": arms,
            })
    return result


def _candidate_grid(values, defaults):
    ordered = sorted({float(value) for value in values})
    if not ordered:
        return list(defaults)
    indices = {
        0,
        len(ordered) // 4,
        len(ordered) // 2,
        3 * len(ordered) // 4,
        len(ordered) - 1,
    }
    return sorted(set(float(value) for value in defaults) | {
        ordered[index] for index in indices
    })


def _choose_thresholds(rows, *, trainable_arms=TRAINABLE_ARMS):
    values = [
        arm for row in rows
        for name, arm in row["arms"].items() if name in trainable_arms
    ]
    probabilities = _candidate_grid(
        (row["benefit_probability"] for row in values), (0.5, 0.7, 0.8)
    )
    probabilities = [value for value in probabilities if value >= 0.5]
    gains = _candidate_grid(
        (row["expected_gain"] for row in values), (0.0, 0.01, 0.03)
    )
    risks = _candidate_grid(
        (row["adverse_probability"] for row in values), (0.1, 0.25, 0.5)
    )
    risks = [value for value in risks if value <= 0.5]
    best = None
    evaluated = 0
    feasible = 0
    for probability in probabilities:
        for gain in gains:
            for risk in risks:
                for penalty in (0.5, 1.0, 2.0):
                    evaluated += 1
                    thresholds = {
                        "minimum_benefit_probability": probability,
                        "minimum_expected_gain": gain,
                        "maximum_adverse_probability": risk,
                        "risk_penalty": penalty,
                        "forced_veto_arms": [
                            arm for arm in ARMS if arm not in trainable_arms
                        ],
                    }
                    metrics = _evaluate_policy(rows, thresholds)
                    if metrics["activated_count"] < 3 or any(
                        float(metrics["per_scale"][str(scale)]["net_geomean_ratio"])
                        > 1.0
                        for scale in (30, 50)
                    ):
                        continue
                    feasible += 1
                    policy_key, policy_uncertainty = (
                        _threshold_selection_key(metrics)
                    )
                    candidate = (
                        *policy_key,
                        probability, gain, risk, penalty,
                    )
                    if best is None or candidate < best[0]:
                        best = (
                            candidate, thresholds, metrics,
                            policy_uncertainty,
                        )
    thresholds = best[1] if best is not None else {
        # No feasible activation is a valid Q0 policy, not a malformed
        # threshold record.  Keep scalar thresholds runtime-valid and veto
        # all learned arms explicitly.
        "minimum_benefit_probability": 1.0,
        "minimum_expected_gain": 0.0,
        "maximum_adverse_probability": 0.0,
        "risk_penalty": 1.0,
        "forced_veto_arms": list(ARMS),
    }
    return thresholds, {
        "candidate_count": evaluated,
        "feasible_candidate_count": feasible,
        "selected_noop_only": best is None,
        "selection_rule": (
            "zero_harm_then_harmful_wilson_upper_then_beneficial_wilson_"
            "lower_then_net_geomean_then_coverage.v1"
        ),
        "selected_calibration_policy": None if best is None else best[2],
        "selected_calibration_uncertainty": None if best is None else best[3],
    }


def _threshold_selection_key(metrics):
    """Return the calibration-only, risk-first threshold ordering key."""

    activated = int(metrics.get("activated_count") or 0)
    harmful = int(metrics.get("harmful_count") or 0)
    beneficial = int(metrics.get("beneficial_count") or 0)
    harmful_interval = _wilson_interval(harmful, activated)
    beneficial_interval = _wilson_interval(beneficial, activated)
    uncertainty = {
        "harmful_rate_wilson_95": harmful_interval,
        "beneficial_precision_wilson_95": beneficial_interval,
    }
    return (
        (
            int(harmful > 0),
            float(harmful_interval["upper"]),
            -float(beneficial_interval["lower"]),
            float(metrics.get("net_geomean_ratio") or 1.0),
            -activated,
        ),
        uncertainty,
    )


def _selected_arm(row, thresholds):
    eligible = []
    forced_veto = set(thresholds.get("forced_veto_arms") or ())
    for arm in ARMS:
        if arm in forced_veto or row["arms"][arm].get("outcome") is None:
            continue
        prediction = row["arms"][arm]
        if (
            prediction["benefit_probability"]
            < thresholds["minimum_benefit_probability"]
            or prediction["expected_gain"]
            < thresholds["minimum_expected_gain"]
            or prediction["adverse_probability"]
            > thresholds["maximum_adverse_probability"]
        ):
            continue
        score = (
            prediction["expected_gain"]
            - thresholds["risk_penalty"]
            * prediction["adverse_probability"]
        )
        if score > 0.0:
            eligible.append((score, arm))
    return "Q0" if not eligible else max(eligible, key=lambda value: (value[0], value[1]))[1]


def _evaluate_policy(rows, thresholds):
    ratios = []
    actions = []
    for row in rows:
        arm = _selected_arm(row, thresholds)
        actions.append(arm)
        ratios.append(
            1.0 if arm == "Q0" else float(row["arms"][arm]["outcome"].ratio)
        )
    activated = [
        (row, arm, ratio)
        for row, arm, ratio in zip(rows, actions, ratios, strict=True)
        if arm != "Q0"
    ]
    return {
        "context_count": len(rows),
        "activated_count": len(activated),
        "q0_count": sum(arm == "Q0" for arm in actions),
        "qd1_count": sum(arm == "QD1" for arm in actions),
        "qb1_count": sum(arm == "QB1" for arm in actions),
        "harmful_count": sum(
            bool(row["arms"][arm]["outcome"].harmful)
            for row, arm, _ratio in activated
        ),
        "beneficial_count": sum(
            bool(row["arms"][arm]["outcome"].beneficial)
            for row, arm, _ratio in activated
        ),
        "net_geomean_ratio": _geomean(ratios),
        "per_scale": {
            str(scale): {
                "context_count": sum(int(row["scale"]) == scale for row in rows),
                "activated_count": sum(
                    int(row["scale"]) == scale and arm != "Q0"
                    for row, arm in zip(rows, actions, strict=True)
                ),
                "net_geomean_ratio": _geomean([
                    ratio for row, ratio in zip(rows, ratios, strict=True)
                    if int(row["scale"]) == scale
                ]),
            }
            for scale in (30, 50)
        },
    }


def _classification_metrics(rows, *, trainable_arms=TRAINABLE_ARMS):
    result = {}
    for arm in trainable_arms:
        benefit_pairs = []
        adverse_pairs = []
        for row in rows:
            prediction = row["arms"][arm]
            outcome = prediction["outcome"]
            actual_benefit = bool(outcome.beneficial)
            actual_adverse = bool(outcome.harmful)
            benefit_pairs.append((
                float(prediction["benefit_probability"]), actual_benefit
            ))
            adverse_pairs.append((
                float(prediction["adverse_probability"]), actual_adverse
            ))
        benefit = _binary_metrics(benefit_pairs)
        adverse = _binary_metrics(adverse_pairs)
        result[arm] = {
            "benefit_accuracy": benefit["accuracy"],
            "adverse_accuracy": adverse["accuracy"],
            "benefit": benefit,
            "adverse": adverse,
        }
    return result


def _arm_rank_metrics(rows, *, trainable_arms=TRAINABLE_ARMS):
    correct = 0
    total = 0
    context_accuracies = []
    for row in rows:
        available = []
        for arm in trainable_arms:
            prediction = row["arms"][arm]
            outcome = prediction.get("outcome")
            if (
                outcome is None
                or not bool(outcome.milestone_matched)
                or bool(outcome.right_censored)
            ):
                continue
            predicted = float(prediction["expected_gain"]) - float(
                prediction["adverse_probability"]
            )
            observed = max(-1.0, min(1.0, 1.0 - float(outcome.ratio)))
            available.append((arm, predicted, observed))
        local_correct = 0
        local_total = 0
        for _arm, predicted, observed in available:
            if abs(observed) <= 1.0e-9:
                continue
            local_total += 1
            local_correct += int((predicted > 0.0) == (observed > 0.0))
        for index, (_left, left_pred, left_obs) in enumerate(available):
            for _right, right_pred, right_obs in available[index + 1:]:
                difference = left_obs - right_obs
                if abs(difference) <= 1.0e-9:
                    continue
                local_total += 1
                local_correct += int(
                    (left_pred > right_pred) == (difference > 0.0)
                )
        if local_total:
            context_accuracies.append(local_correct / local_total)
            correct += local_correct
            total += local_total
    return {
        "context_count": len(context_accuracies),
        "pair_count": total,
        "pair_accuracy": None if total == 0 else correct / total,
        "mean_context_pair_accuracy": (
            None if not context_accuracies
            else statistics.fmean(context_accuracies)
        ),
    }


def _binary_metrics(rows):
    true_positive = sum(probability >= 0.5 and actual for probability, actual in rows)
    true_negative = sum(probability < 0.5 and not actual for probability, actual in rows)
    false_positive = sum(probability >= 0.5 and not actual for probability, actual in rows)
    false_negative = sum(probability < 0.5 and actual for probability, actual in rows)
    positive = true_positive + false_negative
    negative = true_negative + false_positive
    recall = true_positive / max(1, positive)
    specificity = true_negative / max(1, negative)
    return {
        "count": len(rows),
        "positive_count": positive,
        "negative_count": negative,
        "accuracy": (true_positive + true_negative) / max(1, len(rows)),
        "balanced_accuracy": (
            (recall + specificity) / 2.0
            if positive and negative else recall if positive else specificity
        ),
        "precision": true_positive / max(1, true_positive + false_positive),
        "recall": recall,
        "specificity": specificity,
        "brier_score": statistics.fmean([
            (probability - float(actual)) ** 2
            for probability, actual in rows
        ]) if rows else None,
        "confusion": {
            "true_positive": true_positive,
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
        },
    }


def _policy_uncertainty(rows, thresholds, *, seed, replicates=2000):
    """Report uncertainty without using heldout outcomes to move thresholds."""
    actions = [_selected_arm(row, thresholds) for row in rows]
    activated = [
        (row, arm)
        for row, arm in zip(rows, actions, strict=True)
        if arm != "Q0"
    ]
    beneficial = sum(
        bool(row["arms"][arm]["outcome"].beneficial)
        for row, arm in activated
    )
    harmful = sum(
        bool(row["arms"][arm]["outcome"].harmful)
        for row, arm in activated
    )
    ratios_by_instance = {}
    for row, arm in zip(rows, actions, strict=True):
        ratio = (
            1.0 if arm == "Q0"
            else float(row["arms"][arm]["outcome"].ratio)
        )
        ratios_by_instance.setdefault(str(row["instance_hash"]), []).append(
            ratio
        )
    bootstrap = _instance_bootstrap_geomean(
        ratios_by_instance, seed=seed, replicates=replicates
    )
    return {
        "activated_count": len(activated),
        "harmful_rate": harmful / max(1, len(activated)),
        "harmful_rate_wilson_95": _wilson_interval(
            harmful, len(activated)
        ),
        "beneficial_precision": beneficial / max(1, len(activated)),
        "beneficial_precision_wilson_95": _wilson_interval(
            beneficial, len(activated)
        ),
        "instance_count": len(ratios_by_instance),
        "instance_bootstrap_net_geomean_ratio_95": bootstrap,
        "bootstrap_replicates": replicates,
    }


def _wilson_interval(successes, total, *, z=1.959963984540054):
    total = int(total)
    if total <= 0:
        return {"lower": 0.0, "upper": 1.0}
    probability = float(successes) / total
    denominator = 1.0 + z * z / total
    center = (probability + z * z / (2.0 * total)) / denominator
    radius = z * math.sqrt(
        probability * (1.0 - probability) / total
        + z * z / (4.0 * total * total)
    ) / denominator
    return {
        "lower": max(0.0, center - radius),
        "upper": min(1.0, center + radius),
    }


def _instance_bootstrap_geomean(ratios_by_instance, *, seed, replicates):
    instances = sorted(ratios_by_instance)
    if not instances:
        return {"lower": 1.0, "median": 1.0, "upper": 1.0}
    generator = random.Random(int(seed))
    values = []
    for _ in range(max(1, int(replicates))):
        sample = [generator.choice(instances) for _ in instances]
        ratios = [
            ratio for instance in sample
            for ratio in ratios_by_instance[instance]
        ]
        values.append(_geomean(ratios))
    values.sort()
    return {
        "lower": _quantile(values, 0.025),
        "median": _quantile(values, 0.5),
        "upper": _quantile(values, 0.975),
    }


def _quantile(values, probability):
    if not values:
        return 1.0
    position = (len(values) - 1) * float(probability)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(values[lower])
    weight = position - lower
    return float(values[lower]) * (1.0 - weight) + float(values[upper]) * weight


def _load_old_selector_helpers():
    path = ROOT / "scripts/evaluate_p0v5_qg2_context_arm_selector.py"
    spec = importlib.util.spec_from_file_location("old_qg2_arm_helpers", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("cannot load prior arm-outcome helpers")
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _geomean(values):
    return 1.0 if not values else math.exp(statistics.fmean(
        math.log(max(1.0e-12, float(value))) for value in values
    ))


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
