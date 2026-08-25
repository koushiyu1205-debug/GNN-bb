#!/usr/bin/env python3
"""Train Linear, MLP, and Tiny-GAT QG2 models after the oracle gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.qg2_admission_supervision import (  # noqa: E402
    QG2_QUEUE_ACTION_SURFACE_V1,
    QG2_SUPERVISION_SCHEMA_V2,
)


SCHEMA = "lunar_ice_bpc.p0v5_qg2_model_comparison.v3"
ORACLE_SCHEMA = "lunar_ice_bpc.p0v5_qg2_bounded_oracle.v5"
MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE = 52


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--max-pairs-per-context", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=20260801)
    args = parser.parse_args()

    oracle_path = _resolve(args.oracle_summary)
    oracle = _load(oracle_path)
    if oracle.get("schema_version") != ORACLE_SCHEMA:
        raise SystemExit("QG2 training oracle schema mismatch")
    gate = dict(oracle.get("oracle_gate") or {})
    if not bool(gate.get("passed")) or not bool(oracle.get("training_permitted")):
        raise SystemExit(
            "QG2 training is forbidden until the bounded oracle gate passes"
        )

    import torch
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2Linear,
        QG2MLP,
        QG2TinyGAT,
        checkpoint_payload,
        qg2_training_loss,
    )

    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    examples = _load_examples(oracle)
    split = _instance_split(examples)
    calibration_context_count = sum(
        split[row["instance_hash"]] == "calibration"
        for row in examples
    )
    if (
        calibration_context_count
        < MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE
    ):
        raise SystemExit(
            "QG2 training is deferred because the downstream harmful-rate "
            "confidence gate is statistically unreachable: "
            f"calibration_contexts={calibration_context_count} "
            "required_at_zero_harm="
            f"{MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE}"
        )
    feature_envelope = _feature_envelope(
        [row for row in examples if split[row["instance_hash"]] == "train"]
    )
    split_payload = {
        "schema_version": "lunar_ice_bpc.p0v5_qg2_instance_split.v1",
        "unit": "instance_content_hash",
        "ratio": [60, 20, 20],
        "assignments": split,
    }
    split_path = output_dir / "instance_split.json"
    _write(split_path, split_payload)
    training_hash = _hash({
        "oracle_sha256": _sha256(oracle_path),
        "split_sha256": _hash(split_payload),
        "state_hashes": sorted(row["state_hash"] for row in examples),
    })

    model_specs = {
        "linear": QG2Linear,
        "mlp": QG2MLP,
        "gat": QG2TinyGAT,
    }
    model_rows = []
    for model_index, (kind, model_class) in enumerate(model_specs.items()):
        torch.manual_seed(int(args.seed) + model_index * 1009)
        model = model_class()
        optimizer = torch.optim.Adam(
            model.parameters(), lr=float(args.learning_rate)
        )
        training = [
            row for row in examples if split[row["instance_hash"]] == "train"
        ]
        if not training:
            raise SystemExit("QG2 instance split has no training examples")
        for epoch in range(max(1, int(args.epochs))):
            rng = random.Random(int(args.seed) + model_index * 10_000 + epoch)
            order = list(training)
            rng.shuffle(order)
            for example in order:
                optimizer.zero_grad()
                output = model(**example["features"].to_tensors())
                sampled = list(example["pairs"])
                rng.shuffle(sampled)
                sampled = sampled[: max(1, int(args.max_pairs_per_context))]
                preferred = torch.stack([
                    _label_score(output, example, winner)
                    for winner, _loser in sampled
                ])
                other = torch.stack([
                    _label_score(output, example, loser)
                    for _winner, loser in sampled
                ])
                outcome_mask = torch.tensor(
                    [bool(example["outcome_determined"])], dtype=torch.bool
                )
                positive = bool(
                    example["outcome_determined"]
                    and float(example["saved_wall_sec"]) > 0.0
                )
                loss = qg2_training_loss(
                    preferred_scores=preferred,
                    other_scores=other,
                    benefit_probability=output["benefit_probability"].reshape(1),
                    benefit_target=torch.tensor([1.0 if positive else 0.0]),
                    conditional_positive_gain=output[
                        "conditional_positive_gain"
                    ].reshape(1),
                    positive_gain_target=torch.tensor([
                        float(example["saved_wall_sec"])
                    ]),
                    outcome_mask=outcome_mask,
                    positive_mask=torch.tensor([positive], dtype=torch.bool),
                )
                loss.backward()
                optimizer.step()

        checkpoint = output_dir / f"qg2_{kind}.pt"
        torch.save(
            checkpoint_payload(
                model,
                metadata={
                    "training_data_hash": training_hash,
                    "supervision_schema_version": (
                        QG2_SUPERVISION_SCHEMA_V2
                    ),
                    "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
                    "oracle_summary_sha256": _sha256(oracle_path),
                    "split_sha256": _sha256(split_path),
                    "training_instance_hashes": sorted(
                        key for key, value in split.items() if value == "train"
                    ),
                },
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
            )
            for partition in ("train", "calibration", "heldout")
        }
        model_rows.append({
            "model_kind": kind,
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": _sha256(checkpoint),
            "partition_metrics": partition_metrics,
        })
        print(json.dumps(model_rows[-1], sort_keys=True), flush=True)

    report = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "oracle_gate_passed": True,
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "training_data_hash": training_hash,
        "calibration_context_count": calibration_context_count,
        "minimum_calibration_contexts_for_harmful_gate": (
            MINIMUM_CALIBRATION_CONTEXTS_FOR_HARMFUL_GATE
        ),
        "split_path": str(split_path),
        "split_sha256": _sha256(split_path),
        "feature_schema_version": "lunar_ice_bpc.p0v5_qg2_features.v1",
        "label_state_schema_version": "lunar_spprc.qg2_label_state.v1",
        "supervision_schema_version": QG2_SUPERVISION_SCHEMA_V2,
        "queue_action_surface": QG2_QUEUE_ACTION_SURFACE_V1,
        "feature_envelope": feature_envelope,
        "loss": "label_rank_plus_0.1_benefit_plus_0.1_positive_gain",
        "models": model_rows,
        "next_gate": {
            "requires_fresh_process_calibration": True,
            "deployment_authorized": False,
            "thresholds_frozen": False,
        },
    }
    _write(output_dir / "training_report.json", report)
    return 0


def _load_examples(oracle: dict):
    from lunar_ice_bpc.exact.bpc.pricing.backends.base import PRICING_LIFECYCLE_SCOPE_ROOT_CG
    from lunar_ice_bpc.exact.core.branching import branch_context_from_payload
    from lunar_ice_bpc.exact.core.data import load_lunar_ice_data
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import build_qg2_features
    from lunar_ice_bpc.guidance.qg2_admission_supervision import (
        build_admission_aware_preference_pairs,
    )

    initial = {
        row["state_hash"]: dict(row)
        for row in oracle.get("initial_rows") or ()
        if row.get("compliant_context")
    }
    replicate_by_state: dict[str, list[dict]] = {}
    for row in oracle.get("replicate_rows") or ():
        replicate_by_state.setdefault(str(row["state_hash"]), []).append(dict(row))
    examples = []
    for context in oracle.get("context_rows") or ():
        state = str(context["state_hash"])
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
            labeled_pairs, supervision = (
                build_admission_aware_preference_pairs(
                    q0,
                    labels,
                    seed=20260801,
                    maximum=50_000,
                )
            )
        except ValueError as exc:
            raise SystemExit(
                f"QG2 training admission supervision failed closed: {exc}"
            )
        if (
            supervision.get("supervision_schema_version")
            != QG2_SUPERVISION_SCHEMA_V2
            or supervision.get("queue_action_surface")
            != QG2_QUEUE_ACTION_SURFACE_V1
            or int(supervision.get("action_reachable_pair_count") or 0)
            != len(labeled_pairs)
        ):
            raise SystemExit(
                "QG2 training supervision/action-surface contract mismatch"
            )
        if any(
            not _pair_is_action_reachable(labels, winner, loser)
            for winner, loser, _kind in labeled_pairs
        ):
            raise SystemExit("QG2 training received an unreachable label pair")
        pairs = [(winner, loser) for winner, loser, _kind in labeled_pairs]
        if not pairs:
            continue
        true_duals = dict(snapshot.get("true_duals") or {})
        trajectory = dict(snapshot.get("trajectory_features") or {})
        features = build_qg2_features(
            data,
            cover_duals=dict(true_duals.get("task_duals") or true_duals.get("cover") or {}),
            fleet_dual=float(true_duals.get("fleet_dual") or true_duals.get("fleet_limit") or 0.0),
            active_column_count=_optional_int(snapshot.get("active_column_count")),
            active_task_sets=_active_task_sets(snapshot.get("active_task_sets")),
            round_index=_optional_int(snapshot.get("round")),
            previous_proof_wall_sec=_optional_float(trajectory.get("previous_proof_pass_wall_time")),
            previous_processed_labels=_optional_int(
                trajectory.get("previous_proof_processed_labels")
                if trajectory.get("previous_proof_processed_labels") is not None
                else trajectory.get("previous_harvest_processed_labels")
            ),
            dual_l1_delta_from_previous=_optional_float(trajectory.get("dual_l1_delta_from_previous")),
            branch_decisions=tuple(
                branch_context_from_payload(snapshot.get("branch_context") or {}).pair_decisions
            ),
            cut_duals=dict(true_duals.get("cut_duals") or true_duals.get("cuts") or {}),
            v5_midpoint_wall_sec=_optional_float(
                snapshot.get("bidirectional_midpoint_prepass_wall_sec")
                if snapshot.get("bidirectional_midpoint_prepass_wall_sec") is not None
                else trajectory.get("v5_midpoint_wall_sec")
            ),
            root_lifecycle_scope=(
                str(snapshot.get("pricing_lifecycle_scope") or PRICING_LIFECYCLE_SCOPE_ROOT_CG)
                == PRICING_LIFECYCLE_SCOPE_ROOT_CG
            ),
        )
        repeats = replicate_by_state.get(state, [])
        determined = bool(context.get("outcome_determined"))
        if repeats:
            determined = all(_matched_milestone_outcome(
                _load(_resolve(row["q0_path"])),
                _load(_resolve(row["qo2_path"])),
            ) for row in repeats)
        examples.append({
            "state_hash": state,
            "instance_hash": str(context["instance_hash"]),
            "scale": int(context["scale"]),
            "features": features,
            "labels": labels,
            "pairs": tuple(dict.fromkeys(pairs)),
            "supervision": supervision,
            "outcome_determined": determined,
            "saved_wall_sec": float(context.get("saved_wall_sec") or 0.0),
        })
    if not examples:
        raise SystemExit("QG2 oracle produced no trainable examples")
    return examples


def _matched_milestone_outcome(control: dict, arm: dict) -> bool:
    left = str(control.get("milestone_kind") or "")
    right = str(arm.get("milestone_kind") or "")
    return bool(
        control.get("milestone_reached")
        and arm.get("milestone_reached")
        and left == right
        and left in {"ADMISSION_BATCH_READY", "EXACT_PROOF_COMPLETION"}
    )


def _pair_is_action_reachable(
    labels: dict[int, dict], winner: int, loser: int
) -> bool:
    left = labels[int(winner)]
    right = labels[int(loser)]
    return bool(
        bool(left.get("terminal")) == bool(right.get("terminal"))
        and int(left["reduced_cost_bucket"])
        == int(right["reduced_cost_bucket"])
    )


def _label_score(output, example: dict, label_id: int):
    import torch

    labels = example["labels"]
    row = labels[label_id]
    node_id = int(row.get("node_id", 0))
    node_score = (
        output["node_scores"][node_id]
        if 0 < node_id < output["node_scores"].numel()
        else output["node_scores"].new_zeros(())
    )
    arc_score = output["arc_scores"].new_zeros(())
    cursor = label_id
    seen = set()
    while cursor in labels and cursor not in seen:
        seen.add(cursor)
        current = labels[cursor]
        arc_index = int(current.get("incoming_arc_index", 2**64 - 1))
        if 0 <= arc_index < output["arc_scores"].numel():
            arc_score = arc_score + output["arc_scores"][arc_index]
        parent = int(current.get("parent_label_id", 2**64 - 1))
        if parent not in labels:
            break
        cursor = parent
    state = torch.tensor(row["features"], dtype=torch.float32)
    return node_score + arc_score + torch.dot(
        output["label_state_coefficients"], state
    )


def _instance_split(examples: list[dict]):
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


def _feature_envelope(examples: list[dict]):
    if not examples:
        raise SystemExit("QG2 instance split has no training feature envelope")
    contexts = [tuple(row["features"].context_features) for row in examples]
    dimension = len(contexts[0])
    if any(len(row) != dimension for row in contexts):
        raise SystemExit("QG2 context feature dimension drift")
    return {
        "context_min": [
            min(row[index] for row in contexts) for index in range(dimension)
        ],
        "context_max": [
            max(row[index] for row in contexts) for index in range(dimension)
        ],
        "node_max_abs": max(1.0e-9, max(
            abs(value)
            for example in examples
            for row in example["features"].node_features
            for value in row
        )),
        "edge_max_abs": max(1.0e-9, max(
            abs(value)
            for example in examples
            for row in example["features"].edge_features
            for value in row
        )),
        "relative_margin": 0.05,
        "fit_partition": "train_instances_only",
    }


def _evaluate(model, examples):
    import torch

    if not examples:
        return {"context_count": 0, "pair_accuracy": None}
    accuracies = []
    probabilities = []
    with torch.inference_mode():
        for example in examples:
            output = model(**example["features"].to_tensors())
            pairs = example["pairs"][:4096]
            margins = [
                float(
                    _label_score(output, example, winner)
                    - _label_score(output, example, loser)
                )
                for winner, loser in pairs
            ]
            accuracies.append(sum(value > 0.0 for value in margins) / max(1, len(margins)))
            probabilities.append(float(output["benefit_probability"]))
    return {
        "context_count": len(examples),
        "instance_count": len({row["instance_hash"] for row in examples}),
        "mean_pair_accuracy": statistics.fmean(accuracies),
        "mean_benefit_probability": statistics.fmean(probabilities),
    }


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


def _write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
