#!/usr/bin/env python3
"""Train and calibrate the sole P0V4 two-head one-deviation GAT."""

from __future__ import annotations

import argparse
import hashlib
import json
from math import ceil
import os
from pathlib import Path
import random
import sys
from time import perf_counter_ns

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.one_deviation import (  # noqa: E402
    ONE_DEVIATION_RELATIONAL_CONTEXT_SCHEMA,
    TwoHeadOneDeviationGAT,
    calibrate_one_deviation_thresholds,
    one_deviation_hurdle_loss,
)
from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402
from lunar_ice_bpc.guidance.one_deviation_runtime import (  # noqa: E402
    one_deviation_runtime_implementation_hash,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--oracle-gate", required=True)
    parser.add_argument("--fixed-k-selection", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument("--seed", type=int, default=629_043)
    args = parser.parse_args()
    dataset_path = _resolve(args.dataset)
    oracle_gate_path = _resolve(args.oracle_gate)
    fixed_k_path = _resolve(args.fixed_k_selection)
    output = _resolve(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    oracle_gate = _load_json(oracle_gate_path)
    fixed_k = _load_json(fixed_k_path)
    if not bool(oracle_gate.get("gat_training_authorized")):
        raise SystemExit("oracle gate did not authorize GAT training")
    if str(fixed_k.get("status")) != "FIXED_K_SELECTED":
        raise SystemExit("fixed E_K selection is not frozen")
    rows = _load_jsonl(dataset_path)
    _validate_rows(
        rows,
        expected_fixed_k_selection_hash=_sha256(fixed_k_path),
    )
    exact_runtime_bindings_by_scale = (
        _exact_runtime_bindings_by_scale(rows)
    )
    train_rows = [row for row in rows if row["split"] == "train"]
    calibration_rows = [
        row for row in rows if row["split"] == "calibration"
    ]
    if not train_rows or not calibration_rows:
        raise SystemExit("dataset requires train and calibration instances")
    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    first = train_rows[0]
    feature_schema = _feature_schema(first)
    feature_schema_hash = stable_payload_hash(feature_schema)
    model = TwoHeadOneDeviationGAT(
        node_input_dim=len(first["node_features"][0]),
        edge_input_dim=len(first["edge_features"][0]),
        candidate_context_dim=len(first["candidate_context"][0]),
        global_context_dim=len(first["global_context"]),
        hidden_dim=24,
        heads=2,
        layers=2,
    )
    optimizer = torch.optim.Adam(
        model.parameters(), lr=float(args.learning_rate)
    )
    history = []
    for epoch in range(max(1, int(args.epochs))):
        random.shuffle(train_rows)
        epoch_loss = 0.0
        for row in train_rows:
            tensors = _tensorize(row)
            outputs = model(**tensors["inputs"])
            losses = one_deviation_hurdle_loss(
                outputs,
                beneficial=tensors["beneficial"],
                observed_mask=tensors["observed_mask"],
                positive_relative_gain=tensors[
                    "positive_relative_gain"
                ],
                right_censored_positive_mask=tensors[
                    "right_censored_positive_mask"
                ],
                censor_lower_bound_relative=tensors[
                    "censor_lower_bound_relative"
                ],
            )
            optimizer.zero_grad(set_to_none=True)
            losses["loss"].backward()
            optimizer.step()
            epoch_loss += float(losses["loss"].detach())
        history.append(
            {
                "epoch": epoch + 1,
                "mean_loss": epoch_loss / len(train_rows),
            }
        )
    model.eval()
    calibration_predictions = []
    latencies_ms = []
    feature_envelope = _feature_envelope(train_rows)
    deployment_rank_offsets = _deployment_rank_offsets(
        calibration_rows
    )
    with torch.no_grad():
        warm_row = calibration_rows[0]
        for _index in range(5):
            warm_tensors = _tensorize(warm_row)
            model(**warm_tensors["inputs"])
        for row in calibration_rows:
            outputs = None
            for _repeat in range(5):
                started = perf_counter_ns()
                tensors = _tensorize(row)
                outputs = model(**tensors["inputs"])
                latencies_ms.append(
                    (perf_counter_ns() - started) / 1_000_000.0
                )
            assert outputs is not None
            context_ood = not _row_within_feature_envelope(
                row, feature_envelope
            )
            probabilities = outputs[
                "positive_probability"
            ].tolist()
            gains = outputs[
                "expected_positive_relative_gain"
            ].tolist()
            calibration_predictions.extend(
                _calibration_prediction_rows(
                    row,
                    probabilities=probabilities,
                    expected_relative_gains=gains,
                    context_ood=context_ood,
                    allowed_rank_offsets=deployment_rank_offsets,
                )
            )
    calibration = calibrate_one_deviation_thresholds(
        [
            row
            for row in calibration_predictions
            if not bool(row["context_ood"])
        ]
    )
    ordered_latency = sorted(latencies_ms)
    p99_index = max(
        0,
        min(
            len(ordered_latency) - 1,
            ceil(0.99 * len(ordered_latency)) - 1,
        ),
    )
    inference_p99_ms = (
        float("inf")
        if not ordered_latency
        else ordered_latency[p99_index]
    )
    evaluation_authorized = bool(
        calibration["gate_pass"] and inference_p99_ms <= 10.0
    )
    checkpoint = output / "two_head_one_deviation_gat.pt"
    torch.save(
        {
            "schema_version": model.schema_version,
            "state_dict": model.state_dict(),
            "dimensions": {
                "node_input_dim": len(first["node_features"][0]),
                "edge_input_dim": len(first["edge_features"][0]),
                "candidate_context_dim": len(
                    first["candidate_context"][0]
                ),
                "global_context_dim": len(first["global_context"]),
                "hidden_dim": 24,
                "heads": 2,
                "layers": 2,
            },
        },
        checkpoint,
    )
    manifest = {
        "schema_version": (
            "lunar_ice_bpc.two_head_one_deviation_training_manifest.v1"
        ),
        "architecture": "gat_2x24x2",
        "magnitude_target": "relative_time_gain",
        "deployment_score": (
            "positive_probability_times_conditional_relative_gain"
        ),
        "dataset": str(dataset_path),
        "dataset_sha256": _sha256(dataset_path),
        "oracle_gate": str(oracle_gate_path),
        "oracle_gate_sha256": _sha256(oracle_gate_path),
        "fixed_k_selection": str(fixed_k_path),
        "fixed_k_selection_sha256": _sha256(fixed_k_path),
        "train_instance_hashes": sorted(
            {
                str(row["instance_content_hash"])
                for row in train_rows
            }
        ),
        "calibration_instance_hashes": sorted(
            {
                str(row["instance_content_hash"])
                for row in calibration_rows
            }
        ),
        "instance_split_disjoint": not bool(
            {
                str(row["instance_content_hash"])
                for row in train_rows
            }
            & {
                str(row["instance_content_hash"])
                for row in calibration_rows
            }
        ),
        "allowed_scales": sorted(
            {int(row["scale"]) for row in rows}
        ),
        "allowed_exact_binary_hashes": sorted(
            {str(row["exact_binary_hash"]) for row in rows}
        ),
        "allowed_exact_engine_hashes": sorted(
            {str(row["exact_engine_hash"]) for row in rows}
        ),
        "allowed_exact_runtime_binding_hashes": sorted(
            {
                str(row["exact_runtime_binding_hash"])
                for row in rows
            }
        ),
        "exact_runtime_bindings_by_scale": (
            exact_runtime_bindings_by_scale
        ),
        "training_exact_config_hashes": sorted(
            {str(row["exact_config_hash"]) for row in rows}
        ),
        "runtime_policy_id": (
            "one_deviation_full_audited_p0_prefix_v1"
        ),
        "runtime_implementation_hash": (
            one_deviation_runtime_implementation_hash()
        ),
        "deployment_rank_offsets": deployment_rank_offsets,
        "deployment_candidate_scope": (
            "intersection_of_calibration_context_rank_offsets"
        ),
        "feature_schema": feature_schema,
        "feature_schema_hash": feature_schema_hash,
        "calibration": calibration,
        "feature_envelope": feature_envelope,
        "inference_p99_ms": inference_p99_ms,
        "inference_latency_sample_count": len(latencies_ms),
        "inference_latency_scope": (
            "cached_model_tensorization_plus_forward_cpu"
        ),
        "inference_p99_gate_pass": inference_p99_ms <= 10.0,
        "evaluation_authorized": evaluation_authorized,
        "deployment_authorized": False,
        "deployment_gate_status": "HELDOUT_END_TO_END_REQUIRED",
        "heldout_scale_speedup_required": 0.05,
        "deployment_failure_policy": "always_noop",
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": _sha256(checkpoint),
        "certificate_or_bound_role": "none",
        "history": history,
    }
    _write_json(output / "training_manifest.json", manifest)
    _write_json(
        output / "calibration_predictions.json",
        calibration_predictions,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if evaluation_authorized else 3


def _validate_rows(
    rows: list[dict],
    *,
    expected_fixed_k_selection_hash: str,
) -> None:
    required = {
        "instance_content_hash",
        "context_hash",
        "scale",
        "split",
        "action_ids",
        "candidate_rank_offsets",
        "node_features",
        "edge_index",
        "edge_features",
        "candidate_task_masks",
        "candidate_context",
        "global_context",
        "beneficial",
        "observed_mask",
        "positive_gain_sec",
        "positive_relative_gain",
        "delta_time_sec",
        "relative_time_gain",
        "right_censored_positive_mask",
        "censor_lower_bound_sec",
        "censor_lower_bound_relative",
        "memory_adverse_event",
        "pre_action_feature_hash",
        "fixed_k_selection_hash",
        "exact_binary_hash",
        "exact_config_hash",
        "exact_engine_hash",
        "exact_runtime_binding",
        "exact_runtime_binding_hash",
    }
    if not rows:
        raise SystemExit("empty one-deviation dataset")
    train_instances = set()
    calibration_instances = set()
    context_hashes = set()
    for row in rows:
        missing = sorted(required - row.keys())
        if missing:
            raise SystemExit("dataset row missing: " + ",".join(missing))
        split = str(row["split"])
        if split not in {"train", "calibration", "test"}:
            raise SystemExit(f"unsupported dataset split {split!r}")
        instance = str(row["instance_content_hash"])
        context_hash = str(row["context_hash"])
        if not context_hash:
            raise SystemExit("dataset row lacks context hash")
        if context_hash in context_hashes:
            raise SystemExit("duplicate one-deviation context row")
        context_hashes.add(context_hash)
        if split == "train":
            train_instances.add(instance)
        elif split == "calibration":
            calibration_instances.add(instance)
        candidate_count = len(row["candidate_context"])
        expected_candidate_context_width = 4 + len(
            ONE_DEVIATION_RELATIONAL_CONTEXT_SCHEMA
        )
        if any(
            len(values) != expected_candidate_context_width
            for values in row["candidate_context"]
        ):
            raise SystemExit(
                "candidate context does not match the relational schema"
            )
        for key in (
            "candidate_task_masks",
            "action_ids",
            "candidate_rank_offsets",
            "beneficial",
            "observed_mask",
            "positive_gain_sec",
            "positive_relative_gain",
            "delta_time_sec",
            "relative_time_gain",
            "right_censored_positive_mask",
            "censor_lower_bound_sec",
            "censor_lower_bound_relative",
            "memory_adverse_event",
        ):
            if len(row[key]) != candidate_count:
                raise SystemExit(f"candidate tensor length mismatch: {key}")
        rank_offsets = [
            int(value) for value in row["candidate_rank_offsets"]
        ]
        if (
            len(rank_offsets) != len(set(rank_offsets))
            or any(value < 1 or value > 32 for value in rank_offsets)
        ):
            raise SystemExit(
                "candidate rank offsets must be unique within [1,32]"
            )
        if str(row["fixed_k_selection_hash"]) != str(
            expected_fixed_k_selection_hash
        ):
            raise SystemExit("dataset/fixed E_K selection hash mismatch")
        pre_action_payload = {
            key: row[key]
            for key in (
                "node_features",
                "edge_index",
                "edge_features",
                "candidate_task_masks",
                "candidate_context",
                "global_context",
            )
        }
        if str(row["pre_action_feature_hash"]) != stable_payload_hash(
            pre_action_payload
        ):
            raise SystemExit("pre-action feature hash mismatch")
        if bool(row.get("post_action_features_exposed_to_model")):
            raise SystemExit("post-action feature leakage")
        if bool(row.get("certificate_paths_mutated")):
            raise SystemExit("certificate path mutation in training data")
        if any(
            not str(row.get(key) or "")
            for key in (
                "exact_binary_hash",
                "exact_config_hash",
                "exact_engine_hash",
                "exact_runtime_binding_hash",
            )
        ):
            raise SystemExit("training row lacks exact runtime binding")
        runtime = dict(row.get("exact_runtime_binding") or {})
        runtime_hash = str(row["exact_runtime_binding_hash"])
        unsigned_runtime = {
            key: value
            for key, value in runtime.items()
            if key != "runtime_binding_hash"
        }
        if (
            str(runtime.get("runtime_binding_hash") or "")
            != runtime_hash
            or stable_payload_hash(unsigned_runtime) != runtime_hash
            or int(runtime.get("scale") or 0) != int(row["scale"])
        ):
            raise SystemExit("invalid exact runtime binding in dataset")
    if train_instances & calibration_instances:
        raise SystemExit("train/calibration instance leakage")


def _exact_runtime_bindings_by_scale(
    rows: list[dict],
) -> dict[str, dict]:
    bindings: dict[str, dict] = {}
    for row in rows:
        scale_key = str(int(row["scale"]))
        runtime = dict(row["exact_runtime_binding"])
        previous = bindings.get(scale_key)
        if previous is not None and previous != runtime:
            raise SystemExit(
                f"multiple exact runtime bindings for scale{scale_key}"
            )
        bindings[scale_key] = runtime
    return {
        key: bindings[key]
        for key in sorted(bindings, key=int)
    }


def _calibration_prediction_rows(
    row: dict,
    *,
    probabilities: list[float],
    expected_relative_gains: list[float] | None = None,
    expected_gains_sec: list[float] | None = None,
    context_ood: bool,
    allowed_rank_offsets: list[int] | None = None,
) -> list[dict]:
    """Materialize observed outcomes plus every memory-adverse action.

    A memory adverse event is a harmful deployment outcome even when the
    matched progress milestone is right-censored.  Excluding that row from
    calibration would understate the harmful-promotion upper confidence bound.
    """

    gains = (
        expected_relative_gains
        if expected_relative_gains is not None
        else expected_gains_sec
    )
    if gains is None:
        raise ValueError("expected relative gains are required")
    predictions = []
    action_ids = list(row.get("action_ids") or ())
    rank_offsets = [
        int(value)
        for value in row.get("candidate_rank_offsets", ())
    ]
    allowed = (
        None
        if allowed_rank_offsets is None
        else {int(value) for value in allowed_rank_offsets}
    )
    for index, (observed, memory_adverse) in enumerate(
        zip(
            row["observed_mask"],
            row["memory_adverse_event"],
            strict=True,
        )
    ):
        rank_offset = rank_offsets[index]
        if allowed is not None and rank_offset not in allowed:
            continue
        adverse = bool(memory_adverse)
        relative_gain = float(row["relative_time_gain"][index])
        outcome = (
            "harmful"
            if adverse
            else "unknown"
            if not bool(observed)
            else "beneficial"
            if relative_gain > 0.0
            else "harmful"
            if relative_gain < 0.0
            else "neutral"
        )
        predictions.append(
            {
                "positive_probability": float(probabilities[index]),
                "expected_positive_relative_gain": float(gains[index]),
                "outcome": outcome,
                "action_id": str(
                    action_ids[index]
                    if index < len(action_ids)
                    else index
                ),
                "instance_content_hash": str(
                    row["instance_content_hash"]
                ),
                "context_hash": str(row["context_hash"]),
                "candidate_rank": rank_offset,
                "context_ood": bool(context_ood),
            }
        )
    return predictions


def _deployment_rank_offsets(rows: list[dict]) -> list[int]:
    observed_sets = []
    for row in rows:
        values = {
            int(value)
            for value in row.get("candidate_rank_offsets", ())
        }
        if (
            not values
            or any(value < 1 or value > 32 for value in values)
        ):
            raise SystemExit(
                "calibration row has invalid promotion rank offsets"
            )
        observed_sets.append(values)
    shared = set.intersection(*observed_sets)
    if not shared:
        raise SystemExit(
            "calibration contexts have no shared promotion rank offset"
        )
    return sorted(shared)


def _tensorize(row: dict) -> dict:
    inputs = {
        "node_features": torch.tensor(
            row["node_features"], dtype=torch.float32
        ),
        "edge_index": torch.tensor(
            row["edge_index"], dtype=torch.long
        ),
        "edge_features": torch.tensor(
            row["edge_features"], dtype=torch.float32
        ),
        "candidate_task_masks": torch.tensor(
            row["candidate_task_masks"], dtype=torch.float32
        ),
        "candidate_context": torch.tensor(
            row["candidate_context"], dtype=torch.float32
        ),
        "global_context": torch.tensor(
            row["global_context"], dtype=torch.float32
        ),
    }
    return {
        "inputs": inputs,
        "beneficial": torch.tensor(
            [
                bool(beneficial) and not bool(adverse)
                for beneficial, adverse in zip(
                    row["beneficial"],
                    row["memory_adverse_event"],
                    strict=True,
                )
            ],
            dtype=torch.bool,
        ),
        "observed_mask": torch.tensor(
            [
                bool(observed) or bool(adverse)
                for observed, adverse in zip(
                    row["observed_mask"],
                    row["memory_adverse_event"],
                    strict=True,
                )
            ],
            dtype=torch.bool,
        ),
        "positive_relative_gain": torch.tensor(
            row["positive_relative_gain"], dtype=torch.float32
        ),
        "right_censored_positive_mask": torch.tensor(
            row["right_censored_positive_mask"], dtype=torch.bool
        ),
        "censor_lower_bound_relative": torch.tensor(
            row["censor_lower_bound_relative"], dtype=torch.float32
        ),
    }


def _feature_schema(row: dict) -> dict:
    return {
        "schema_version": (
            "lunar_ice_bpc.one_deviation_feature_schema.v1"
        ),
        "node_input_dim": len(row["node_features"][0]),
        "edge_input_dim": len(row["edge_features"][0]),
        "candidate_context_dim": len(
            row["candidate_context"][0]
        ),
        "global_context_dim": len(row["global_context"]),
        "candidate_context_schema": [
            "true_reduced_cost",
            "would_change_active_support",
            "is_new_task_set",
            "task_fraction",
            *ONE_DEVIATION_RELATIONAL_CONTEXT_SCHEMA,
        ],
        "global_context_schema": [
            "log1p_memory_limit_bytes",
            "log1p_remaining_wall_time_sec",
            "reserved_0",
            "reserved_1",
        ],
    }


def _feature_envelope(rows: list[dict]) -> dict:
    return {
        key: _per_dimension_envelope(
            [
                vector
                for row in rows
                for vector in (
                    row[key]
                    if key
                    in {
                        "node_features",
                        "edge_features",
                        "candidate_context",
                    }
                    else [row[key]]
                )
            ]
        )
        for key in (
            "node_features",
            "edge_features",
            "candidate_context",
            "global_context",
        )
    }


def _per_dimension_envelope(rows: list[list[float]]) -> dict:
    if not rows:
        raise SystemExit("cannot calibrate an empty feature envelope")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise SystemExit("inconsistent feature width")
    minima = [min(float(row[index]) for row in rows) for index in range(width)]
    maxima = [max(float(row[index]) for row in rows) for index in range(width)]
    margins = [
        max(1.0e-6, 0.05 * max(1.0, abs(low), abs(high)))
        for low, high in zip(minima, maxima, strict=True)
    ]
    return {
        "minimum": [
            low - margin
            for low, margin in zip(minima, margins, strict=True)
        ],
        "maximum": [
            high + margin
            for high, margin in zip(maxima, margins, strict=True)
        ],
    }


def _row_within_feature_envelope(
    row: dict, envelope: dict
) -> bool:
    for key in (
        "node_features",
        "edge_features",
        "candidate_context",
        "global_context",
    ):
        rows = row[key] if key != "global_context" else [row[key]]
        bounds = dict(envelope.get(key) or {})
        minimum = list(bounds.get("minimum") or [])
        maximum = list(bounds.get("maximum") or [])
        if not rows or not minimum or len(minimum) != len(maximum):
            return False
        if any(len(values) != len(minimum) for values in rows):
            return False
        if any(
            float(value) < float(minimum[index])
            or float(value) > float(maximum[index])
            for values in rows
            for index, value in enumerate(values)
        ):
            return False
    return True


def _resolve(value: object) -> Path:
    path = Path(str(value))
    return path if path.is_absolute() else ROOT / path


def _load_json(path: Path) -> dict:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _load_jsonl(path: Path) -> list[dict]:
    return [
        dict(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
