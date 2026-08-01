#!/usr/bin/env python3
"""Train grouped-OOF arc-potential GATs for exact QG1 ordering.

The supervision is the completed-control dominance trace already materialized
as development-only arc potentials.  The produced online manifest remains
evaluation-only until independent paired wall-time calibration authorizes it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
from typing import Any

import torch
from torch.nn import functional as F


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.proof_queue_gat import (  # noqa: E402
    PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1,
    ProofQueuePotentialGAT,
    build_proof_queue_gat_features,
    checkpoint_payload,
    normalized_arc_potentials,
    proof_queue_arc_ranking_loss,
)
from lunar_ice_bpc.guidance.proof_queue_gat_runtime import (  # noqa: E402
    PROOF_QUEUE_GAT_RUNTIME_POLICY_ID,
    proof_queue_gat_runtime_implementation_hash,
)


TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_proof_queue_gat_training.v1"
CV_SCHEMA = "lunar_ice_bpc.p0v5_proof_queue_gat_grouped_cv.v1"
POTENTIAL_SCHEMA = "lunar_ice_bpc.p0v3_proof_queue_potential.v1"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_proof_queue_gat_manifest.v1"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--oracle-summary",
        default=(
            "runs/p0v3_gat_landing_search_20260726/"
            "proof_queue_arc_dominance_oracle_gate_v2_summary.json"
        ),
    )
    parser.add_argument(
        "--state-index",
        default=(
            "runs/p0v3_gat_landing_search_20260726/"
            "proof_queue_arc_linear_cv_v1_summary.json"
        ),
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--final-epochs", type=int, default=60)
    parser.add_argument("--learning-rate", type=float, default=0.002)
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument(
        "--allowed-scale", action="append", type=int, default=[]
    )
    parser.add_argument(
        "--allowed-engine-hash", action="append", default=[]
    )
    parser.add_argument(
        "--allowed-config-hash", action="append", default=[]
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    oracle_path = _resolve(args.oracle_summary)
    state_index_path = _resolve(args.state_index)
    examples = _load_examples(oracle_path, state_index_path)
    if len(examples) < 8:
        raise SystemExit("proof-queue GAT requires at least eight states")
    training_identity = {
        "schema_version": TRAINING_SCHEMA,
        "oracle_summary": str(oracle_path),
        "oracle_summary_sha256": _sha256(oracle_path),
        "state_index": str(state_index_path),
        "state_index_sha256": _sha256(state_index_path),
        "state_hashes": sorted(row["state_hash"] for row in examples),
        "instance_hashes": sorted(
            {row["instance_hash"] for row in examples}
        ),
    }
    training_hash = _stable_hash(training_identity)
    _write(output_dir / "training_identity.json", training_identity)

    folds = max(2, min(int(args.folds), len(examples)))
    assignment = {
        row["instance_hash"]: int(
            hashlib.sha256(row["instance_hash"].encode()).hexdigest(), 16
        )
        % folds
        for row in examples
    }
    oof_rows: list[dict[str, Any]] = []
    fold_rows = []
    for fold in range(folds):
        training = [
            row for row in examples if assignment[row["instance_hash"]] != fold
        ]
        validation = [
            row for row in examples if assignment[row["instance_hash"]] == fold
        ]
        if not validation or not training:
            continue
        model = _train(
            training,
            epochs=int(args.epochs),
            learning_rate=float(args.learning_rate),
            seed=int(args.seed) + fold,
        )
        fold_checkpoint = output_dir / f"fold_{fold:02d}.pt"
        torch.save(
            checkpoint_payload(
                model,
                metadata={
                    "training_data_hash": training_hash,
                    "fold": fold,
                    "training_state_hashes": sorted(
                        row["state_hash"] for row in training
                    ),
                    "validation_state_hashes": sorted(
                        row["state_hash"] for row in validation
                    ),
                },
            ),
            fold_checkpoint,
        )
        fold_metrics = []
        for row in validation:
            prediction = _predict(model, row)
            metrics = _metrics(prediction, row["target"])
            potential_path = (
                output_dir
                / "oof_potentials"
                / f"{row['scale']}_{row['state_hash'][:16]}"
                / "gat_oof_potential.json"
            )
            potential = {
                "schema_version": POTENTIAL_SCHEMA,
                "development_only": True,
                "deployable": False,
                "ordering_only": True,
                "can_filter": False,
                "can_prune": False,
                "can_change_reduced_cost": False,
                "can_certify": False,
                "future_leakage": False,
                "valid_use": "grouped_oof_exact_replay_only",
                "source_kind": "grouped_oof_proof_queue_gat",
                "instance_content_hash": row["instance_hash"],
                "source_state_hash": row["state_hash"],
                "method": "gat_arc_dominance_potential",
                "sign": "learned_target",
                "feature_schema_version": (
                    PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1
                ),
                "normalization_version": (
                    "centered_maxabs_arc_potential.v1"
                ),
                "ood_policy_version": "grouped_oof_instance_hash.v1",
                "potential_id": _stable_hash(
                    {
                        "fold": fold,
                        "state_hash": row["state_hash"],
                        "prediction": [round(value, 12) for value in prediction],
                    }
                ),
                "task_potentials": {
                    task_id: 0.0 for task_id in row["data"].task_ids
                },
                "arc_potentials": {
                    candidate_id: round(float(value), 12)
                    for candidate_id, value in zip(
                        row["features"].arc_candidate_ids,
                        prediction,
                        strict=True,
                    )
                },
                "audit": {
                    "fold": fold,
                    "target_instance_excluded_from_training": True,
                    **metrics,
                },
            }
            _write(potential_path, potential)
            oof = {
                "fold": fold,
                "instance_id": row["data"].instance_id,
                "instance_content_hash": row["instance_hash"],
                "source_state_hash": row["state_hash"],
                "scale": row["scale"],
                "instance_path": str(row["instance_path"]),
                "snapshot_path": str(row["snapshot_path"]),
                "potential_path": str(potential_path),
                "checkpoint_path": str(fold_checkpoint),
                **metrics,
            }
            oof_rows.append(oof)
            fold_metrics.append(metrics)
        fold_rows.append(
            {
                "fold": fold,
                "training_state_count": len(training),
                "validation_state_count": len(validation),
                "mean_spearman": statistics.fmean(
                    row["spearman"] for row in fold_metrics
                ),
                "mean_top_target_count_recall": statistics.fmean(
                    row["top_target_count_recall"] for row in fold_metrics
                ),
                "checkpoint_path": str(fold_checkpoint),
                "checkpoint_sha256": _sha256(fold_checkpoint),
            }
        )
        print(json.dumps(fold_rows[-1], sort_keys=True), flush=True)

    final_model = _train(
        examples,
        epochs=int(args.final_epochs),
        learning_rate=float(args.learning_rate),
        seed=int(args.seed) + 1000,
    )
    checkpoint_path = output_dir / "proof_queue_gat_final.pt"
    torch.save(
        checkpoint_payload(
            final_model,
            metadata={
                "training_data_hash": training_hash,
                "training_state_hashes": sorted(
                    row["state_hash"] for row in examples
                ),
                "training_instance_hashes": sorted(
                    {row["instance_hash"] for row in examples}
                ),
                "context_gate_target": (
                    "oracle_qg1_vs_fixed_best_ratio"
                ),
            },
        ),
        checkpoint_path,
    )
    aggregate = {
        "state_count": len(oof_rows),
        "instance_count": len(
            {row["instance_content_hash"] for row in oof_rows}
        ),
        "mean_spearman": statistics.fmean(
            row["spearman"] for row in oof_rows
        ),
        "median_spearman": statistics.median(
            row["spearman"] for row in oof_rows
        ),
        "mean_top_target_count_recall": statistics.fmean(
            row["top_target_count_recall"] for row in oof_rows
        ),
    }
    cv_summary = {
        "schema_version": CV_SCHEMA,
        "development_only": True,
        "deployable": False,
        "training_data_hash": training_hash,
        "feature_schema_version": PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1,
        "split_unit": "instance_content_hash",
        "target_state_excluded_from_training": True,
        "rows": oof_rows,
        "folds": fold_rows,
        "aggregate": aggregate,
        "gate": {
            "permits_exact_replay": True,
            "permits_online_deployment": False,
            "reason": (
                "paired fresh-process wall-time calibration is required"
            ),
        },
    }
    cv_path = output_dir / "grouped_oof_summary.json"
    _write(cv_path, cv_summary)

    envelope = _feature_envelope(examples)
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "runtime_policy_id": PROOF_QUEUE_GAT_RUNTIME_POLICY_ID,
        "runtime_implementation_hash": (
            proof_queue_gat_runtime_implementation_hash()
        ),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "training_data_hash": training_hash,
        "grouped_oof_summary": str(cv_path),
        "grouped_oof_summary_sha256": _sha256(cv_path),
        "allowed_scales": sorted(
            set(args.allowed_scale or [20, 30, 50])
        ),
        "allowed_exact_engine_hashes": sorted(
            set(str(value) for value in args.allowed_engine_hash)
        ),
        "allowed_exact_config_hashes": sorted(
            set(str(value) for value in args.allowed_config_hash)
        ),
        "ood_policy_version": "precall_feature_envelope.v1",
        "feature_envelope": envelope,
        "torch_num_threads": 1,
        "evaluation_authorized": True,
        "evaluation_force_qg1": True,
        "deployment_authorized": False,
        "calibration": {
            "gate_pass": False,
            "probability_threshold": 1.0,
            "expected_gain_threshold": 1.0,
            "harmful_action_rate_95_upper": None,
            "beneficial_precision_95_lower": None,
        },
        "ordering_only": True,
        "can_filter": False,
        "can_prune": False,
        "can_change_bound": False,
        "can_certify": False,
        "fallback": "P0V4_V5_Q0",
    }
    manifest_path = output_dir / "evaluation_manifest.json"
    _write(manifest_path, manifest)
    print(
        json.dumps(
            {
                "aggregate": aggregate,
                "checkpoint": str(checkpoint_path),
                "manifest": str(manifest_path),
            },
            sort_keys=True,
        )
    )
    return 0


def _load_examples(oracle_path: Path, state_index_path: Path):
    oracle = _load(oracle_path)
    index = _load(state_index_path)
    state_rows = {
        str(row["source_state_hash"]): dict(row)
        for row in index.get("rows") or ()
    }
    oracle_by_state = {}
    for row in oracle.get("records") or ():
        oracle_by_state.setdefault(str(row["source_state_hash"]), dict(row))
    examples = []
    for state_hash, row in sorted(state_rows.items()):
        oracle_row = oracle_by_state.get(state_hash)
        if oracle_row is None:
            continue
        instance_path = Path(row["instance_path"]).resolve()
        snapshot_path = Path(row["snapshot_path"]).resolve()
        target_path = Path(oracle_row["potential_path"]).resolve()
        data = load_lunar_ice_data(_load(instance_path))
        snapshot = _load(snapshot_path)
        target_payload = _load(target_path)
        true_duals = dict(snapshot.get("true_duals") or {})
        # Runtime has no active-column or previous-round trajectory payload.
        # Train on exactly the feature surface available before every backend
        # call instead of leaking persisted replay-only state.
        features = build_proof_queue_gat_features(
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
        )
        target_lookup = {
            str(key): float(value)
            for key, value in dict(
                target_payload.get("arc_potentials") or {}
            ).items()
        }
        if set(target_lookup) != set(features.arc_candidate_ids):
            raise SystemExit("GAT target/feature arc universe mismatch")
        target = torch.tensor(
            [target_lookup[key] for key in features.arc_candidate_ids],
            dtype=torch.float32,
        )
        ratio = float(oracle_row["qg1_vs_fixed_best_ratio"])
        examples.append(
            {
                "state_hash": state_hash,
                "instance_hash": data.instance_content_hash,
                "scale": int(data.scale),
                "data": data,
                "instance_path": instance_path,
                "snapshot_path": snapshot_path,
                "features": features,
                "tensors": features.to_tensors(),
                "target": target,
                "beneficial": 1.0 if ratio < 1.0 else 0.0,
                "positive_gain": max(0.0, 1.0 - ratio),
            }
        )
    return examples


def _train(examples, *, epochs: int, learning_rate: float, seed: int):
    torch.manual_seed(seed)
    model = ProofQueuePotentialGAT()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=1.0e-5
    )
    rng = random.Random(seed)
    for _epoch in range(max(1, epochs)):
        order = list(range(len(examples)))
        rng.shuffle(order)
        for index in order:
            row = examples[index]
            output = model(**row["tensors"])
            rank_loss = proof_queue_arc_ranking_loss(
                output["arc_scores"], row["target"]
            )
            probability = output["benefit_probability"].clamp(
                1.0e-6, 1.0 - 1.0e-6
            )
            benefit_target = torch.tensor(row["beneficial"])
            gate_loss = F.binary_cross_entropy(
                probability, benefit_target
            )
            gain_target = torch.tensor(row["positive_gain"])
            gain_loss = (
                F.smooth_l1_loss(
                    output["conditional_positive_gain"], gain_target
                )
                if row["beneficial"] > 0.0
                else torch.zeros(())
            )
            loss = rank_loss + 0.1 * gate_loss + 0.1 * gain_loss
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
    model.eval()
    return model


def _predict(model, row) -> list[float]:
    with torch.inference_mode():
        output = model(**row["tensors"])
        values = normalized_arc_potentials(output["arc_scores"])
    return [float(value) for value in values.tolist()]


def _metrics(prediction: list[float], target_tensor: torch.Tensor) -> dict:
    target = [float(value) for value in target_tensor.tolist()]
    positive_count = sum(value > 0.0 for value in target)
    width = max(1, positive_count)
    target_top = set(
        sorted(range(len(target)), key=lambda i: (-target[i], i))[:width]
    )
    predicted_top = set(
        sorted(
            range(len(prediction)), key=lambda i: (-prediction[i], i)
        )[:width]
    )
    return {
        "mse": statistics.fmean(
            (left - right) ** 2
            for left, right in zip(prediction, target, strict=True)
        ),
        "pearson": _pearson(prediction, target),
        "spearman": _pearson(_ranks(prediction), _ranks(target)),
        "positive_target_arc_count": positive_count,
        "top_target_count_recall": len(
            target_top & predicted_top
        )
        / width,
        "random_top_recall": width / max(1, len(target)),
    }


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    result = [0.0] * len(values)
    cursor = 0
    while cursor < len(order):
        end = cursor + 1
        while end < len(order) and values[order[end]] == values[order[cursor]]:
            end += 1
        rank = (cursor + end - 1) / 2.0
        for position in order[cursor:end]:
            result[position] = rank
        cursor = end
    return result


def _pearson(left: list[float], right: list[float]) -> float:
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum(
        (x - left_mean) * (y - right_mean)
        for x, y in zip(left, right, strict=True)
    )
    denominator = math.sqrt(
        sum((x - left_mean) ** 2 for x in left)
        * sum((y - right_mean) ** 2 for y in right)
    )
    return 0.0 if denominator <= 0.0 else numerator / denominator


def _feature_envelope(examples) -> dict[str, Any]:
    contexts = [row["features"].context_features for row in examples]
    return {
        "context_min": [min(row[index] for row in contexts) for index in range(len(contexts[0]))],
        "context_max": [max(row[index] for row in contexts) for index in range(len(contexts[0]))],
        "node_max_abs": max(
            abs(value)
            for row in examples
            for values in row["features"].node_features
            for value in values
        ),
        "edge_max_abs": max(
            abs(value)
            for row in examples
            for values in row["features"].edge_features
            for value in values
        ),
        "relative_margin": 0.25,
    }


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
