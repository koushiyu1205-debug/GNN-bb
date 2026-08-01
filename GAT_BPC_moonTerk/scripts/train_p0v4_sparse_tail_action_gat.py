#!/usr/bin/env python3
"""Train the context-level two-head sparse-tail GAT.

The current bounded dataset supports ``--development-smoke`` only.  Formal
training requires a dataset manifest that explicitly authorizes it and whose
rows are all runtime-eligible.  Smoke output is hash-bound but always carries
``evaluation_authorized=false`` and therefore executes as shadow NOOP.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
import random
import sys
from time import perf_counter_ns

import torch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.cuts import stable_payload_hash  # noqa: E402
from lunar_ice_bpc.guidance.sparse_tail_action import (  # noqa: E402
    SPARSE_TAIL_ACTIONS,
    SPARSE_TAIL_GAT_FEATURE_SCHEMA,
    SPARSE_TAIL_GAT_MANIFEST_SCHEMA,
    SPARSE_TAIL_GAT_MODEL_SCHEMA,
    TwoHeadSparseTailActionGAT,
    sparse_tail_feature_schema,
    sparse_tail_two_head_loss,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--learning-rate", type=float, default=1.0e-3)
    parser.add_argument("--seed", type=int, default=629_061)
    parser.add_argument("--development-smoke", action="store_true")
    args = parser.parse_args()
    manifest_path = _resolve(args.dataset_manifest)
    output = _resolve(args.output_dir)
    training_manifest_path = output / "training_manifest.json"
    if training_manifest_path.exists():
        raise SystemExit(
            "fixed sparse-tail pilot is train-once; use a fresh output directory"
        )
    dataset_manifest = _load_json(manifest_path)
    dataset_path = Path(str(dataset_manifest.get("dataset") or "")).resolve()
    if _sha256(dataset_path) != str(
        dataset_manifest.get("dataset_sha256") or ""
    ):
        raise SystemExit("sparse-tail dataset hash mismatch")
    formal_authorized = bool(
        dataset_manifest.get("formal_training_authorized")
    )
    if not formal_authorized and not bool(args.development_smoke):
        raise SystemExit(
            "dataset authorizes development smoke only; pass "
            "--development-smoke"
        )
    rows = _load_jsonl(dataset_path)
    _validate_rows(rows)
    if formal_authorized and any(
        not bool(row.get("runtime_eligible")) for row in rows
    ):
        raise SystemExit("formal dataset contains non-runtime labels")
    train_rows = [row for row in rows if row["split"] == "train"]
    calibration_rows = [
        row for row in rows if row["split"] == "calibration"
    ]
    if not train_rows or not calibration_rows:
        raise SystemExit("sparse-tail dataset needs train and calibration rows")

    random.seed(int(args.seed))
    torch.manual_seed(int(args.seed))
    first = train_rows[0]
    dimensions = {
        "node_input_dim": len(first["node_features"][0]),
        "edge_input_dim": len(first["edge_features"][0]),
        "global_input_dim": len(first["global_features"]),
        "action_input_dim": len(first["action_features"][0]),
        "hidden_dim": 32,
        "heads": 2,
        "layers": 2,
    }
    model = TwoHeadSparseTailActionGAT(**dimensions)
    optimizer = torch.optim.Adam(
        model.parameters(), lr=float(args.learning_rate)
    )
    history = []
    for epoch in range(max(1, int(args.epochs))):
        random.shuffle(train_rows)
        total = 0.0
        for row in train_rows:
            tensors = _tensorize(row)
            outputs = model(**tensors["inputs"])
            losses = sparse_tail_two_head_loss(
                outputs,
                beneficial=tensors["beneficial"],
                observed_mask=tensors["observed_mask"],
                positive_relative_gain=tensors[
                    "positive_relative_gain"
                ],
            )
            optimizer.zero_grad(set_to_none=True)
            losses["loss"].backward()
            optimizer.step()
            total += float(losses["loss"].detach())
        history.append(
            {
                "epoch": epoch + 1,
                "mean_loss": total / len(train_rows),
            }
        )

    model.eval()
    predictions = []
    latencies_ms = []
    with torch.no_grad():
        for row in rows:
            tensors = _tensorize(row)
            started = perf_counter_ns()
            outputs = model(**tensors["inputs"])
            latencies_ms.append(
                (perf_counter_ns() - started) / 1_000_000.0
            )
            for index, action in enumerate(row["action_ids"]):
                probability = float(
                    outputs["positive_probability"][index]
                )
                magnitude = float(
                    outputs[
                        "conditional_positive_relative_gain"
                    ][index]
                )
                predictions.append(
                    {
                        "context_id": row["context_id"],
                        "split": row["split"],
                        "source_role": row["source_role"],
                        "runtime_eligible": bool(
                            row["runtime_eligible"]
                        ),
                        "action": str(action),
                        "positive_probability": probability,
                        "conditional_positive_relative_gain": magnitude,
                        "expected_positive_relative_gain": (
                            probability * magnitude
                        ),
                        "beneficial": bool(row["beneficial"][index]),
                        "observed": bool(row["observed_mask"][index]),
                    }
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

    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / "two_head_sparse_tail_gat.pt"
    torch.save(
        {
            "schema_version": SPARSE_TAIL_GAT_MODEL_SCHEMA,
            "dimensions": dimensions,
            "state_dict": model.state_dict(),
        },
        checkpoint_path,
    )
    runtime_rows = [row for row in rows if row["runtime_eligible"]]
    training_positive_action_count = sum(
        sum(int(value) for value in row["beneficial"])
        for row in train_rows
    )
    calibration_positive_action_count = sum(
        sum(int(value) for value in row["beneficial"])
        for row in calibration_rows
    )
    calibration_observed_action_count = sum(
        sum(int(value) for value in row["observed_mask"])
        for row in calibration_rows
    )
    formal_context_gate = bool(
        formal_authorized
        and len(runtime_rows) >= 40
        and {
            int(row["scale"]) for row in runtime_rows
        }.issuperset({30, 50})
    )
    # The harm/precision thresholds are intentionally closed until the formal
    # runtime-eligible oracle/calibration quotas pass.
    calibration = {
        "probability_threshold": 1.0,
        "expected_gain_threshold": 1.0e9,
        "harm_gate_pass": False,
        "harmful_promotion_rate_ucb95": None,
        "beneficial_precision_lcb95": None,
        "reason": (
            "formal_calibration_not_authorized"
            if not formal_context_gate
            else "formal_calibrator_not_run"
        ),
    }
    pilot_reason_codes = []
    if not runtime_rows:
        pilot_reason_codes.append("no_runtime_eligible_end_to_end_labels")
    if calibration_positive_action_count == 0:
        pilot_reason_codes.append("zero_beneficial_calibration_actions")
    if not formal_context_gate:
        pilot_reason_codes.append("formal_context_quota_not_met")
    run_binding = {
        "dataset_manifest_sha256": _sha256(manifest_path),
        "dataset_sha256": _sha256(dataset_path),
        "seed": int(args.seed),
        "epochs": max(1, int(args.epochs)),
        "learning_rate": float(args.learning_rate),
        "architecture": "context_gat_2x32x2_two_head",
        "development_smoke": bool(args.development_smoke),
    }
    manifest = {
        "schema_version": SPARSE_TAIL_GAT_MANIFEST_SCHEMA,
        "status": (
            "DEVELOPMENT_SMOKE_TRAINED"
            if bool(args.development_smoke)
            else "FORMAL_TRAINING_INCOMPLETE_CALIBRATION"
        ),
        "architecture": "context_gat_2x32x2_two_head",
        "action_ids": list(SPARSE_TAIL_ACTIONS),
        "feature_schema": sparse_tail_feature_schema(),
        "feature_schema_hash": stable_payload_hash(
            sparse_tail_feature_schema()
        ),
        "dataset_manifest": str(manifest_path),
        "dataset_manifest_sha256": _sha256(manifest_path),
        "dataset": str(dataset_path),
        "dataset_sha256": _sha256(dataset_path),
        "training_run_binding": run_binding,
        "training_run_binding_hash": stable_payload_hash(run_binding),
        "fixed_single_training_run": True,
        "training_seed": int(args.seed),
        "training_epochs": max(1, int(args.epochs)),
        "learning_rate": float(args.learning_rate),
        "training_row_count": len(train_rows),
        "calibration_row_count": len(calibration_rows),
        "training_positive_action_count": training_positive_action_count,
        "calibration_positive_action_count": (
            calibration_positive_action_count
        ),
        "calibration_observed_action_count": (
            calibration_observed_action_count
        ),
        "runtime_eligible_row_count": len(runtime_rows),
        "mathematical_context_only_row_count": sum(
            int(row["source_role"] == "mathematical_context_only")
            for row in rows
        ),
        "dimensions": dimensions,
        "checkpoint": checkpoint_path.name,
        "checkpoint_sha256": _sha256(checkpoint_path),
        "calibration": calibration,
        "feature_envelope": _feature_envelope(rows),
        "inference_p99_ms": inference_p99_ms,
        "inference_p99_gate_pass": inference_p99_ms <= 10.0,
        "formal_context_gate_pass": formal_context_gate,
        "fixed_pilot_model_gate_pass": False,
        "fixed_pilot_reason_codes": pilot_reason_codes,
        "evaluation_authorized": False,
        "deployment_authorized": False,
        "deployment_failure_policy": "always_noop",
        "certificate_or_bound_role": "none",
        "history": history,
    }
    training_manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "predictions.json").write_text(
        json.dumps(predictions, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


def _validate_rows(rows: list[dict]) -> None:
    if not rows:
        raise SystemExit("empty sparse-tail dataset")
    dimensions = None
    seen = set()
    for row in rows:
        if row.get("feature_schema_version") != (
            SPARSE_TAIL_GAT_FEATURE_SCHEMA
        ):
            raise SystemExit("sparse-tail row feature schema mismatch")
        if tuple(row.get("action_ids") or ()) != SPARSE_TAIL_ACTIONS:
            raise SystemExit("sparse-tail row action space mismatch")
        if row.get("context_id") in seen:
            raise SystemExit("duplicate sparse-tail context")
        seen.add(row.get("context_id"))
        if bool(row.get("post_action_features_exposed_to_model")):
            raise SystemExit("post-action feature leakage")
        if row.get("certificate_authority") != "none":
            raise SystemExit("sparse-tail label has certificate authority")
        payload = {
            "schema_version": row["feature_schema_version"],
            "instance_content_hash": row["instance_content_hash"],
            "input_hash": row["input_hash"],
            "scale": row["scale"],
            "node_features": row["node_features"],
            "edge_index": row["edge_index"],
            "edge_features": row["edge_features"],
            "global_features": row["global_features"],
            "action_ids": row["action_ids"],
            "action_features": row["action_features"],
        }
        if stable_payload_hash(payload) != str(row.get("feature_hash") or ""):
            raise SystemExit("sparse-tail feature hash mismatch")
        shape = (
            len(row["node_features"][0]),
            len(row["edge_features"][0]),
            len(row["global_features"]),
            len(row["action_features"][0]),
        )
        if dimensions is None:
            dimensions = shape
        elif shape != dimensions:
            raise SystemExit("sparse-tail feature dimension mismatch")
        for key in (
            "beneficial",
            "observed_mask",
            "positive_relative_gain",
            "delta_time_sec",
            "memory_adverse_event",
        ):
            if len(row[key]) != len(SPARSE_TAIL_ACTIONS):
                raise SystemExit(f"sparse-tail label width mismatch: {key}")


def _tensorize(row: dict) -> dict[str, object]:
    return {
        "inputs": {
            "node_features": torch.tensor(
                row["node_features"], dtype=torch.float32
            ),
            "edge_index": torch.tensor(
                row["edge_index"], dtype=torch.long
            ),
            "edge_features": torch.tensor(
                row["edge_features"], dtype=torch.float32
            ),
            "global_features": torch.tensor(
                row["global_features"], dtype=torch.float32
            ),
            "action_features": torch.tensor(
                row["action_features"], dtype=torch.float32
            ),
        },
        "beneficial": torch.tensor(row["beneficial"], dtype=torch.bool),
        "observed_mask": torch.tensor(
            row["observed_mask"], dtype=torch.bool
        ),
        "positive_relative_gain": torch.tensor(
            row["positive_relative_gain"], dtype=torch.float32
        ),
    }


def _feature_envelope(rows: list[dict]) -> dict[str, object]:
    columns = list(zip(*(row["global_features"] for row in rows), strict=True))
    return {
        "allowed_scales": sorted({int(row["scale"]) for row in rows}),
        "global_min": [min(float(value) for value in column) for column in columns],
        "global_max": [max(float(value) for value in column) for column in columns],
        "policy": "closed_box_training_envelope_v1",
    }


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve(value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
