#!/usr/bin/env python3
"""Train P0V5 QG2 V3 admission rankers, GAT first.

This script trains ordering potentials only.  It intentionally does not train
activation from the leaked QO2 oracle outcome; runtime authority is learned
later from each arm's own fresh-process matched outcomes.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_ranker_training.v1"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
SPLIT_SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_instance_split.v1"
REALMAP_SPLIT_SCHEMA = (
    "lunar_ice_bpc.p0v5_qg2_realmap_v4_instance_split.v1"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--models",
        default="gat",
        help="comma-separated subset; execution order is always gat,mlp,linear",
    )
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--max-pairs-per-context", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20260806)
    parser.add_argument("--early-stopping-patience", type=int, default=8)
    parser.add_argument("--resume-report")
    parser.add_argument(
        "--instance-split",
        help="pre-outcome instance split; required for real-map V4 training",
    )
    args = parser.parse_args()

    import torch
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        QG2V3Linear,
        QG2V3MLP,
        QG2V3TinyGAT,
        QG2_V3_MODEL_ORDER,
        fit_qg2_v3_normalization,
        qg2_v3_checkpoint_payload,
        qg2_v3_weighted_rank_loss,
    )

    requested = {
        value.strip().lower()
        for value in str(args.models).split(",")
        if value.strip()
    }
    unknown = requested - set(QG2_V3_MODEL_ORDER)
    if not requested or unknown:
        raise SystemExit(f"invalid QG2 V3 model set: {sorted(unknown)}")
    model_classes = {
        "gat": QG2V3TinyGAT,
        "mlp": QG2V3MLP,
        "linear": QG2V3Linear,
    }

    oracle_path = _resolve(args.oracle_summary)
    oracle = _load(oracle_path)
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        raise SystemExit("QG2 V3 oracle schema mismatch")
    if not bool(oracle.get("oracle_gate", {}).get("passed")) or not bool(
        oracle.get("training_permitted")
    ):
        raise SystemExit("QG2 V3 training requires the frozen bounded-oracle gate")

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    examples = _load_examples(oracle, seed=int(args.seed))
    if args.instance_split:
        split_path = _resolve(args.instance_split)
        split_payload = _load(split_path)
        if split_payload.get("schema_version") != REALMAP_SPLIT_SCHEMA or not bool(
            split_payload.get("frozen_before_matched_outcomes")
        ):
            raise SystemExit("QG2 V3 real-map split is not pre-outcome frozen")
        split = {
            str(key): str(value)
            for key, value in dict(split_payload.get("assignments") or {}).items()
        }
        example_hashes = {str(row["instance_hash"]) for row in examples}
        if not example_hashes.issubset(split) or any(
            split[value] not in {"train", "calibration", "heldout"}
            for value in example_hashes
        ):
            raise SystemExit("QG2 V3 real-map split does not cover every example")
    else:
        split = _instance_split(examples)
        split_payload = {
            "schema_version": SPLIT_SCHEMA,
            "unit": "instance_content_hash",
            "ratio": [60, 20, 20],
            "assignments": split,
        }
        split_path = output_dir / "instance_split.json"
        _write(split_path, split_payload)
    training = [
        row for row in examples if split[row["instance_hash"]] == "train"
    ]
    calibration = [
        row for row in examples
        if split[row["instance_hash"]] == "calibration"
    ]
    if not training or not calibration:
        raise SystemExit("QG2 V3 split needs train and calibration examples")
    normalization = fit_qg2_v3_normalization(
        [row["features"] for row in training]
    )
    normalization_path = output_dir / "train_normalization.json"
    feature_envelope_path = output_dir / "feature_envelope.json"
    _write(normalization_path, normalization)
    _write(feature_envelope_path, _feature_envelope(training))
    training_hash = _hash({
        "oracle_sha256": _sha256(oracle_path),
        "split_sha256": _sha256(split_path),
        "normalization_sha256": _sha256(normalization_path),
        "states": sorted(row["state_hash"] for row in examples),
        "supervision_hashes": sorted(row["supervision_hash"] for row in examples),
    })

    previous_models: list[dict] = []
    if args.resume_report:
        previous = _load(_resolve(args.resume_report))
        if previous.get("schema_version") != SCHEMA:
            raise SystemExit("QG2 V3 resume-report schema mismatch")
        if str(previous.get("training_data_hash") or "") != training_hash:
            raise SystemExit("QG2 V3 resume-report training-data drift")
        previous_models = [dict(row) for row in previous.get("models") or ()]
    completed = {str(row.get("model_kind") or "") for row in previous_models}
    curve_path = output_dir / "training_curve.jsonl"
    if not args.resume_report and curve_path.exists():
        raise SystemExit(
            "QG2 V3 output already contains training_curve.jsonl; use a new "
            "directory or an explicit --resume-report"
        )

    model_rows = list(previous_models)
    for model_index, kind in enumerate(QG2_V3_MODEL_ORDER):
        if kind not in requested or kind in completed:
            continue
        torch.manual_seed(int(args.seed) + model_index * 1009)
        model = model_classes[kind](normalization)
        optimizer = torch.optim.Adam(
            model.parameters(), lr=float(args.learning_rate)
        )
        latest_path = output_dir / f"qg2_v3_{kind}_latest.pt"
        checkpoint = output_dir / f"qg2_v3_{kind}.pt"
        best_accuracy = -math.inf
        best_loss = math.inf
        best_epoch = 0
        best_state = None
        stale_epochs = 0
        epochs_completed = 0
        for epoch in range(1, max(1, int(args.epochs)) + 1):
            started = perf_counter()
            rng = random.Random(
                int(args.seed) + model_index * 10_000 + epoch
            )
            order = list(training)
            rng.shuffle(order)
            losses: list[float] = []
            model.train()
            for example in order:
                optimizer.zero_grad()
                output = model(**example["features"].to_tensors())
                pairs, sampled_weights = _systematic_weighted_sample(
                    example["pairs"],
                    maximum=max(1, int(args.max_pairs_per_context)),
                    rng=rng,
                )
                score_cache: dict[int, torch.Tensor] = {}
                arc_cache: dict[int, torch.Tensor] = {}
                preferred = torch.stack([
                    _label_score(
                        output, example, row.preferred_label_id,
                        score_cache=score_cache, arc_cache=arc_cache,
                    )
                    for row in pairs
                ])
                other = torch.stack([
                    _label_score(
                        output, example, row.other_label_id,
                        score_cache=score_cache, arc_cache=arc_cache,
                    )
                    for row in pairs
                ])
                weights = torch.tensor(sampled_weights, dtype=torch.float32)
                loss = qg2_v3_weighted_rank_loss(
                    preferred, other, weights
                )
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
                optimizer.step()
                losses.append(float(loss.detach()))
            mean_rank_loss = statistics.fmean(losses)
            calibration_metrics = _evaluate(
                model, calibration,
                maximum=max(1, int(args.max_pairs_per_context)),
            )
            calibration_accuracy = float(
                calibration_metrics["mean_context_pair_accuracy"]
            )
            improved = bool(
                calibration_accuracy > best_accuracy + 1.0e-6
                or (
                    abs(calibration_accuracy - best_accuracy) <= 1.0e-6
                    and mean_rank_loss < best_loss - 1.0e-8
                )
            )
            if improved:
                best_accuracy = calibration_accuracy
                best_loss = mean_rank_loss
                best_epoch = epoch
                best_state = copy.deepcopy(model.state_dict())
                stale_epochs = 0
            else:
                stale_epochs += 1
            epochs_completed = epoch
            epoch_wall = perf_counter() - started
            curve_row = {
                "model": kind,
                "epoch": epoch,
                "total_loss": mean_rank_loss,
                "rank_loss": mean_rank_loss,
                "benefit_loss": 0.0,
                "positive_gain_loss": 0.0,
                "adverse_loss": 0.0,
                "calibration_mean_context_pair_accuracy": calibration_accuracy,
                "is_best_epoch": improved,
                "epoch_wall_sec": epoch_wall,
            }
            _append_jsonl(curve_path, curve_row)
            torch.save(
                qg2_v3_checkpoint_payload(
                    model,
                    normalization=normalization,
                    metadata=_checkpoint_metadata(
                        training_hash=training_hash,
                        oracle_path=oracle_path,
                        split_path=split_path,
                        normalization_path=normalization_path,
                        epoch=epoch,
                    ),
                ),
                latest_path,
            )
            print(json.dumps(curve_row, sort_keys=True), flush=True)
            if stale_epochs >= max(1, int(args.early_stopping_patience)):
                break

        if best_state is None:
            raise SystemExit("QG2 V3 ranker failed to select a calibration epoch")
        model.load_state_dict(best_state, strict=True)
        torch.save(
            qg2_v3_checkpoint_payload(
                model,
                normalization=normalization,
                metadata=_checkpoint_metadata(
                    training_hash=training_hash,
                    oracle_path=oracle_path,
                    split_path=split_path,
                    normalization_path=normalization_path,
                    epoch=best_epoch,
                ),
            ),
            checkpoint,
        )
        partition_metrics = {
            partition: _evaluate(
                model,
                [
                    row for row in examples
                    if split[row["instance_hash"]] == partition
                ],
                maximum=max(1, int(args.max_pairs_per_context)),
            )
            for partition in ("train", "calibration", "heldout")
        }
        row = {
            "model_kind": kind,
            "parameter_count": sum(
                int(parameter.numel()) for parameter in model.parameters()
            ),
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": _sha256(checkpoint),
            "latest_checkpoint_path": str(latest_path),
            "checkpoint_selection_partition": "calibration",
            "checkpoint_selection_metric": "mean_context_pair_accuracy",
            "best_epoch": best_epoch,
            "epochs_completed": epochs_completed,
            "early_stopping_patience": max(
                1, int(args.early_stopping_patience)
            ),
            "partition_metrics": partition_metrics,
        }
        model_rows.append(row)
        report = _report(
            oracle_path=oracle_path,
            training_hash=training_hash,
            split_path=split_path,
            normalization_path=normalization_path,
            feature_envelope_path=feature_envelope_path,
            examples=examples,
            split=split,
            curve_path=curve_path,
            model_rows=model_rows,
        )
        _write(output_dir / "training_report.json", report)
        print(json.dumps(row, sort_keys=True), flush=True)
    return 0


def _load_examples(oracle: dict, *, seed: int):
    from lunar_ice_bpc.exact.bpc.pricing.backends.base import (
        PRICING_LIFECYCLE_SCOPE_ROOT_CG,
    )
    from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        build_qg2_features,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        normalize_qg2_v3_features,
    )
    from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
        QG2_V3_SUPERVISION_SCHEMA,
        build_qg2_v3_weighted_pairs,
    )

    initial = {
        str(row["state_hash"]): dict(row)
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    examples = []
    for context in oracle.get("context_rows") or ():
        state = str(context["state_hash"])
        if state not in initial:
            continue
        source = initial[state]
        data = load_lunar_ice_data(_load(_resolve(source["instance_path"])))
        snapshot = _load(_resolve(source["snapshot_path"]))
        q0 = _load(_resolve(source["q0_trace_path"]))
        telemetry = dict(q0.get("proof_telemetry") or {})
        labels = {
            int(row["label_id"]): dict(row)
            for row in telemetry.get("proof_queue_label_state_trace") or ()
        }
        try:
            pairs, supervision = build_qg2_v3_weighted_pairs(
                q0, labels, seed=seed, maximum=50_000
            )
        except ValueError as exc:
            raise SystemExit(
                f"QG2 V3 supervision failed closed for {state}: {exc}"
            ) from exc
        if (
            supervision.get("supervision_schema_version")
            != QG2_V3_SUPERVISION_SCHEMA
            or not pairs
            or abs(sum(row.weight for row in pairs) - 1.0) > 1.0e-6
        ):
            raise SystemExit("QG2 V3 supervision contract mismatch")
        if any(
            not _pair_is_action_reachable(
                labels, row.preferred_label_id, row.other_label_id
            )
            for row in pairs
        ):
            raise SystemExit("QG2 V3 received an unreachable label pair")
        true_duals = dict(snapshot.get("true_duals") or {})
        trajectory = dict(snapshot.get("trajectory_features") or {})
        features = normalize_qg2_v3_features(data, build_qg2_features(
            data,
            cover_duals=dict(
                true_duals.get("task_duals")
                or true_duals.get("cover")
                or {}
            ),
            fleet_dual=float(
                true_duals.get("fleet_dual")
                if true_duals.get("fleet_dual") is not None
                else true_duals.get("fleet_limit") or 0.0
            ),
            active_column_count=_optional_int(
                snapshot.get("active_column_count")
            ),
            active_task_sets=_active_task_sets(
                snapshot.get("active_task_sets")
            ),
            round_index=_optional_int(snapshot.get("round")),
            previous_proof_wall_sec=_optional_float(
                trajectory.get("previous_proof_pass_wall_time")
            ),
            previous_processed_labels=_optional_int(
                trajectory.get("previous_proof_processed_labels")
                if trajectory.get("previous_proof_processed_labels")
                is not None
                else trajectory.get("previous_harvest_processed_labels")
            ),
            dual_l1_delta_from_previous=_optional_float(
                trajectory.get("dual_l1_delta_from_previous")
            ),
            branch_decisions=tuple(
                branch_context_from_payload(
                    snapshot.get("branch_context") or {}
                ).pair_decisions
            ),
            cut_duals=dict(
                true_duals.get("cut_duals")
                or true_duals.get("cuts")
                or {}
            ),
            v5_midpoint_wall_sec=_optional_float(
                snapshot.get("bidirectional_midpoint_prepass_wall_sec")
                if snapshot.get("bidirectional_midpoint_prepass_wall_sec")
                is not None
                else trajectory.get("v5_midpoint_wall_sec")
            ),
            root_lifecycle_scope=(
                str(
                    snapshot.get("pricing_lifecycle_scope")
                    or PRICING_LIFECYCLE_SCOPE_ROOT_CG
                )
                == PRICING_LIFECYCLE_SCOPE_ROOT_CG
            ),
        ))
        examples.append({
            "state_hash": state,
            "instance_hash": str(context["instance_hash"]),
            "scale": int(context["scale"]),
            "milestone_kind": str(q0.get("milestone_kind") or ""),
            "features": features,
            "labels": labels,
            "pairs": pairs,
            "supervision": supervision,
            "supervision_hash": _hash(supervision),
        })
    if not examples:
        raise SystemExit("QG2 V3 oracle produced no trainable examples")
    return examples


def _systematic_weighted_sample(rows, *, maximum: int, rng: random.Random):
    if len(rows) <= maximum:
        return tuple(rows), tuple(float(row.weight) for row in rows)
    cumulative: list[float] = []
    total = 0.0
    for row in rows:
        total += max(0.0, float(row.weight))
        cumulative.append(total)
    if total <= 0.0:
        raise ValueError("QG2 V3 systematic sample has zero mass")
    offset = rng.random()
    selected = []
    cursor = 0
    for index in range(maximum):
        target = (index + offset) * total / maximum
        while cursor + 1 < len(cumulative) and cumulative[cursor] < target:
            cursor += 1
        selected.append(rows[cursor])
    return tuple(selected), (1.0,) * len(selected)


def _label_score(output, example, label_id, *, score_cache, arc_cache):
    import torch

    label_id = int(label_id)
    if label_id in score_cache:
        return score_cache[label_id]
    labels = example["labels"]
    row = labels[label_id]
    node_id = int(row.get("node_id", 0))
    node_score = (
        output["node_scores"][node_id]
        if 0 < node_id < output["node_scores"].numel()
        else output["node_scores"].new_zeros(())
    )

    def path_arc_score(cursor: int):
        if cursor in arc_cache:
            return arc_cache[cursor]
        current = labels[cursor]
        parent = int(current.get("parent_label_id", 2**64 - 1))
        value = output["arc_scores"].new_zeros(())
        if parent in labels and parent != cursor:
            value = path_arc_score(parent)
        arc_index = int(current.get("incoming_arc_index", 2**64 - 1))
        if 0 <= arc_index < output["arc_scores"].numel():
            value = value + output["arc_scores"][arc_index]
        arc_cache[cursor] = value
        return value

    state = torch.tensor(row["features"], dtype=torch.float32)
    result = node_score + path_arc_score(label_id) + torch.dot(
        output["label_state_coefficients"], state
    )
    score_cache[label_id] = result
    return result


def _evaluate(model, examples, *, maximum: int):
    import torch

    if not examples:
        return {"context_count": 0, "pair_accuracy": None}
    context_accuracy = []
    weighted_correct = 0.0
    total_weight = 0.0
    by_kind: dict[str, list[float]] = {}
    model.eval()
    with torch.inference_mode():
        for example in examples:
            output = model(**example["features"].to_tensors())
            pairs, weights = _systematic_weighted_sample(
                example["pairs"], maximum=maximum,
                rng=random.Random(20260806),
            )
            score_cache = {}
            arc_cache = {}
            local_correct = 0.0
            local_total = 0.0
            for row, weight in zip(pairs, weights, strict=True):
                margin = float(
                    _label_score(
                        output, example, row.preferred_label_id,
                        score_cache=score_cache, arc_cache=arc_cache,
                    )
                    - _label_score(
                        output, example, row.other_label_id,
                        score_cache=score_cache, arc_cache=arc_cache,
                    )
                )
                correct = 1.0 if margin > 0.0 else 0.0
                local_correct += correct * weight
                local_total += weight
                by_kind.setdefault(row.kind, [0.0, 0.0])
                by_kind[row.kind][0] += correct * weight
                by_kind[row.kind][1] += weight
            context_accuracy.append(local_correct / max(1.0e-12, local_total))
            weighted_correct += local_correct
            total_weight += local_total
    return {
        "context_count": len(examples),
        "instance_count": len({row["instance_hash"] for row in examples}),
        "mean_context_pair_accuracy": statistics.fmean(context_accuracy),
        "weighted_pair_accuracy": weighted_correct / max(1.0e-12, total_weight),
        "per_kind_weighted_pair_accuracy": {
            kind: values[0] / max(1.0e-12, values[1])
            for kind, values in sorted(by_kind.items())
        },
    }


def _instance_split(examples):
    assignments = {}
    for scale in (30, 50):
        instances = sorted(
            {row["instance_hash"] for row in examples if row["scale"] == scale},
            key=lambda value: hashlib.sha256(value.encode()).hexdigest(),
        )
        for index, instance in enumerate(instances):
            fraction = index / max(1, len(instances))
            assignments[instance] = (
                "train" if fraction < 0.60
                else "calibration" if fraction < 0.80
                else "heldout"
            )
    return assignments


def _feature_envelope(examples):
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2_CONTEXT_FEATURES,
        QG2_NODE_DYNAMIC_FEATURES,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        QG2_V3_FEATURE_ENVELOPE_SCHEMA,
    )
    from lunar_ice_bpc.guidance.tensorization import (
        EDGE_STATIC_FEATURES,
        NODE_STATIC_FEATURES,
    )

    names = {
        "context": tuple(QG2_CONTEXT_FEATURES),
        "node": (*NODE_STATIC_FEATURES, *QG2_NODE_DYNAMIC_FEATURES),
        "edge": tuple(
            "risk_over_objective_reference" if value == "risk" else value
            for value in EDGE_STATIC_FEATURES
        ),
    }
    rows = {
        "context": [
            tuple(example["features"].context_features)
            for example in examples
        ],
        "node": [
            tuple(row) for example in examples
            for row in example["features"].node_features
        ],
        "edge": [
            tuple(row) for example in examples
            for row in example["features"].edge_features
        ],
    }
    payload = {
        "schema_version": QG2_V3_FEATURE_ENVELOPE_SCHEMA,
        "relative_margin": 0.05,
        "fit_partition": "train_instances_only",
    }
    for group in ("context", "node", "edge"):
        if not rows[group] or any(
            len(row) != len(names[group]) for row in rows[group]
        ):
            raise ValueError(f"QG2 V3.1 {group} envelope dimension mismatch")
        payload[f"{group}_feature_names"] = list(names[group])
        payload[f"{group}_min"] = [
            min(row[index] for row in rows[group])
            for index in range(len(names[group]))
        ]
        payload[f"{group}_max"] = [
            max(row[index] for row in rows[group])
            for index in range(len(names[group]))
        ]
    return payload


def _checkpoint_metadata(*, training_hash, oracle_path, split_path, normalization_path, epoch):
    from lunar_ice_bpc.guidance.qg2_admission_supervision import (
        QG2_QUEUE_ACTION_SURFACE_V1,
    )
    from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
        QG2_V3_SUPERVISION_SCHEMA,
    )

    return {
        "training_data_hash": training_hash,
        "supervision_schema_version": QG2_V3_SUPERVISION_SCHEMA,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "oracle_summary_sha256": _sha256(oracle_path),
        "split_sha256": _sha256(split_path),
        "normalization_sha256": _sha256(normalization_path),
        "trained_epoch": int(epoch),
        "activation_authority": False,
        "activation_training_source": "none_ranker_only",
    }


def _report(*, oracle_path, training_hash, split_path, normalization_path, feature_envelope_path, examples, split, curve_path, model_rows):
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        QG2_V3_MODEL_ORDER,
        QG2_V3_RANKER_SCHEMA,
    )
    from lunar_ice_bpc.guidance.qg2_admission_supervision_v3 import (
        QG2_V3_SUPERVISION_SCHEMA,
    )

    return {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "ranker_only": True,
        "activation_authority": False,
        "model_execution_order": list(QG2_V3_MODEL_ORDER),
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "training_data_hash": training_hash,
        "split_path": str(split_path),
        "split_sha256": _sha256(split_path),
        "normalization_path": str(normalization_path),
        "normalization_sha256": _sha256(normalization_path),
        "feature_envelope_path": str(feature_envelope_path),
        "feature_envelope_sha256": _sha256(feature_envelope_path),
        "training_curve_path": str(curve_path),
        "training_curve_sha256": _sha256(curve_path),
        "ranker_schema_version": QG2_V3_RANKER_SCHEMA,
        "supervision_schema_version": QG2_V3_SUPERVISION_SCHEMA,
        "loss": "context_normalized_route_balanced_weighted_pairwise_logistic",
        "context_count": len(examples),
        "instance_count": len({row["instance_hash"] for row in examples}),
        "partition_context_counts": {
            partition: sum(
                split[row["instance_hash"]] == partition for row in examples
            )
            for partition in ("train", "calibration", "heldout")
        },
        "models": model_rows,
        "next_gate": {
            "action": "force_on_fresh_process_q0_vs_gat",
            "requires_actual_gat_outcomes": True,
            "selector_training_permitted": False,
        },
    }


def _pair_is_action_reachable(labels, winner, loser):
    left = labels[int(winner)]
    right = labels[int(loser)]
    return bool(
        bool(left.get("terminal")) == bool(right.get("terminal"))
        and int(left["reduced_cost_bucket"])
        == int(right["reduced_cost_bucket"])
    )


def _optional_int(value):
    return None if value is None else max(0, int(value))


def _optional_float(value):
    return None if value is None else max(0.0, float(value))


def _active_task_sets(value):
    if value is None:
        return None
    return tuple(tuple(str(task_id) for task_id in row) for row in value)


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _append_jsonl(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash(payload):
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
    ).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
