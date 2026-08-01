#!/usr/bin/env python3
"""Train and calibrate the exact-safe V5 midpoint run/skip GAT.

Only information available before the midpoint call is used.  The label says
whether the V5 midpoint path returned an audited negative pool; a predicted
failure may skip directly to the unchanged P0V4 exact fallback.  Instance
indices 1--15 train, 16--18 calibrate, and 19--20 remain held out.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import sys
from typing import Any

import torch
from torch.nn import functional as F


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.bidirectional_gate_gat import (  # noqa: E402
    BIDIRECTIONAL_GATE_GAT_POLICY_ID,
    BidirectionalPrepassGAT,
    build_bidirectional_gate_features,
    checkpoint_payload,
)
from lunar_ice_bpc.guidance.bidirectional_gate_runtime import (  # noqa: E402
    bidirectional_gate_runtime_implementation_hash,
)
from lunar_ice_bpc.guidance.proof_queue_gat import (  # noqa: E402
    PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1,
    build_proof_queue_gat_features,
)


TRAINING_SCHEMA = "lunar_ice_bpc.p0v5_bidirectional_gate_training.v1"
DATASET_SCHEMA = "lunar_ice_bpc.p0v5_bidirectional_gate_dataset.v1"
REPORT_SCHEMA = "lunar_ice_bpc.p0v5_bidirectional_gate_report.v1"
MANIFEST_SCHEMA = "lunar_ice_bpc.p0v5_bidirectional_gate_manifest.v1"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        default=(
            "runs/p0v4_final_acceptance_v2_20260801/official/Exact"
        ),
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=0.0015)
    parser.add_argument("--seed", type=int, default=20260801)
    return parser


def main() -> int:
    args = _parser().parse_args()
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    source_root = _resolve(args.source_root)
    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, sources = _load_rows(source_root)
    by_split = {
        split: [row for row in rows if row["split"] == split]
        for split in ("train", "calibration", "heldout")
    }
    if any(not by_split[key] for key in by_split):
        raise SystemExit("train/calibration/heldout split is incomplete")
    identity = {
        "schema_version": TRAINING_SCHEMA,
        "source_root": str(source_root),
        "source_probe_hashes": sources,
        "row_identities": [
            {
                key: row[key]
                for key in (
                    "context_id",
                    "instance_content_hash",
                    "scale",
                    "instance_index",
                    "round",
                    "split",
                    "midpoint_failed",
                    "termination_reason",
                    "dual_fingerprint",
                )
            }
            for row in rows
        ],
    }
    training_hash = _stable_hash(identity)
    _write(output_dir / "training_identity.json", identity)
    _write(
        output_dir / "dataset.json",
        {
            "schema_version": DATASET_SCHEMA,
            "feature_schema_version": PROOF_QUEUE_GAT_FEATURE_SCHEMA_V1,
            "training_data_hash": training_hash,
            "precall_features_only": True,
            "target": "midpoint_did_not_return_audited_negative_pool",
            "rows": [_serializable_row(row) for row in rows],
        },
    )

    model = _train(
        by_split["train"],
        epochs=int(args.epochs),
        learning_rate=float(args.learning_rate),
        seed=int(args.seed),
    )
    calibration_predictions = _predict_rows(
        model, by_split["calibration"]
    )
    calibration = _calibrate(calibration_predictions)
    train_metrics = _metrics(_predict_rows(model, by_split["train"]))
    calibration_metrics = _metrics(calibration_predictions, calibration)
    heldout_metrics = _metrics(
        _predict_rows(model, by_split["heldout"]), calibration
    )

    checkpoint_path = output_dir / "bidirectional_gate_gat_final.pt"
    torch.save(
        checkpoint_payload(
            model,
            metadata={
                "training_data_hash": training_hash,
                "training_instance_indices": list(range(1, 16)),
                "calibration_instance_indices": [16, 17, 18],
                "heldout_instance_indices": [19, 20],
                "target": "midpoint_failure",
                "magnitude_target": (
                    "min(final_judge_wall_time_sec,30)_failure_only_proxy"
                ),
            },
        ),
        checkpoint_path,
    )
    report = {
        "schema_version": REPORT_SCHEMA,
        "training_data_hash": training_hash,
        "split_policy": {
            "train_instance_indices": list(range(1, 16)),
            "calibration_instance_indices": [16, 17, 18],
            "heldout_instance_indices": [19, 20],
        },
        "split_counts": {
            key: _counts(value) for key, value in by_split.items()
        },
        "train_metrics": train_metrics,
        "calibration_metrics": calibration_metrics,
        "heldout_metrics": heldout_metrics,
        "calibration": calibration,
        "exact_safety": {
            "action_space": ["RUN_V5", "SKIP_TO_UNCHANGED_P0V4"],
            "can_change_reduced_cost": False,
            "can_change_bound": False,
            "can_prune": False,
            "can_certify": False,
            "runtime_failure_action": "RUN_V5",
        },
        "deployment_decision": (
            "END_TO_END_PILOT_REQUIRED"
            if calibration["gate_pass"]
            else "NO_DEPLOYMENT_CALIBRATION_FAILED"
        ),
    }
    report_path = output_dir / "training_report.json"
    _write(report_path, report)
    envelope = _feature_envelope(
        by_split["train"] + by_split["calibration"]
    )
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "policy_id": BIDIRECTIONAL_GATE_GAT_POLICY_ID,
        "runtime_implementation_hash": (
            bidirectional_gate_runtime_implementation_hash()
        ),
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_sha256": _sha256(checkpoint_path),
        "training_data_hash": training_hash,
        "training_report": str(report_path),
        "training_report_sha256": _sha256(report_path),
        "allowed_scales": [30, 50],
        "allowed_exact_engine_hashes": [],
        "feature_envelope": envelope,
        "torch_num_threads": 1,
        "evaluation_authorized": bool(calibration["gate_pass"]),
        "deployment_authorized": False,
        "calibration": calibration,
        "can_change_reduced_cost": False,
        "can_change_bound": False,
        "can_prune": False,
        "can_certify": False,
        "fallback_on_error_or_ood": "RUN_V5",
    }
    manifest_path = output_dir / "evaluation_manifest.json"
    _write(manifest_path, manifest)
    print(
        json.dumps(
            {
                "calibration": calibration,
                "heldout": heldout_metrics,
                "manifest": str(manifest_path),
            },
            sort_keys=True,
        ),
        flush=True,
    )
    return 0


def _load_rows(source_root: Path):
    rows = []
    source_hashes = []
    data_cache = {}
    tensor_cache = {}
    probe_paths = sorted(source_root.glob("**/probe.json"))
    for probe_path in probe_paths:
        match_scale = re.findall(r"scale_0*(\d+)", str(probe_path))
        match_instance = re.findall(r"instance_0*(\d+)", str(probe_path))
        if not match_scale or not match_instance:
            continue
        scale = int(match_scale[-1])
        instance_index = int(match_instance[-1])
        if scale not in {30, 50} or not 1 <= instance_index <= 20:
            continue
        probe = _load(probe_path)
        instance_path = Path(str(probe["instance_path"])).resolve()
        data = data_cache.get(instance_path)
        if data is None:
            data = load_lunar_ice_data(_load(instance_path))
            data_cache[instance_path] = data
        source_hashes.append(
            {"path": str(probe_path), "sha256": _sha256(probe_path)}
        )
        static_tensors = tensor_cache.get(data.instance_content_hash)
        previous_outcome = "NONE"
        failure_streak = 0
        for history_row in probe.get("history") or ():
            if not isinstance(history_row, dict) or not bool(
                history_row.get("final_judge_called")
            ):
                continue
            dual = dict(history_row.get("dual_context") or {})
            task_duals = dict(dual.get("task_duals") or {})
            features = build_bidirectional_gate_features(
                data,
                cover_duals=task_duals,
                fleet_dual=float(dual.get("fleet_dual") or 0.0),
                round_index=int(history_row.get("round") or 0),
                previous_midpoint_outcome=previous_outcome,
                consecutive_observed_failures=failure_streak,
            )
            tensors = features.to_tensors()
            if static_tensors is None:
                static_tensors = (
                    tensors["edge_index"], tensors["edge_features"]
                )
                tensor_cache[data.instance_content_hash] = static_tensors
            tensors["edge_index"], tensors["edge_features"] = static_tensors
            termination = str(
                history_row.get("negative_escape_termination_reason") or ""
            )
            failed = not termination.startswith(
                "BIDIRECTIONAL_MIDPOINT_"
            )
            round_index = int(history_row.get("round") or 0)
            context_id = _stable_hash(
                {
                    "instance": data.instance_content_hash,
                    "round": round_index,
                    "dual": str(dual.get("dual_fingerprint") or ""),
                }
            )
            rows.append(
                {
                    "context_id": context_id,
                    "instance_content_hash": data.instance_content_hash,
                    "instance_id": data.instance_id,
                    "instance_path": str(instance_path),
                    "source_probe": str(probe_path),
                    "scale": scale,
                    "instance_index": instance_index,
                    "round": round_index,
                    "split": _split(instance_index),
                    "midpoint_failed": bool(failed),
                    "termination_reason": termination,
                    "dual_fingerprint": str(
                        dual.get("dual_fingerprint") or ""
                    ),
                    "failure_cost_proxy_sec": (
                        min(
                            30.0,
                            max(
                                0.0,
                                float(
                                    history_row.get("final_judge_wall_time")
                                    or 0.0
                                ),
                            ),
                        )
                        if failed
                        else 0.0
                    ),
                    "previous_midpoint_outcome": previous_outcome,
                    "consecutive_observed_failures": failure_streak,
                    "features": features,
                    "tensors": tensors,
                }
            )
            previous_outcome = "FAILED" if failed else "ACCEPTED"
            failure_streak = failure_streak + 1 if failed else 0
    return rows, source_hashes


def _split(instance_index: int) -> str:
    if instance_index <= 15:
        return "train"
    if instance_index <= 18:
        return "calibration"
    return "heldout"


def _train(rows, *, epochs: int, learning_rate: float, seed: int):
    torch.manual_seed(seed)
    first = rows[0]["features"]
    model = BidirectionalPrepassGAT(
        node_input_dim=len(first.node_features[0]),
        context_input_dim=len(first.context_features),
    )
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=learning_rate, weight_decay=1.0e-5
    )
    positives = [row for row in rows if row["midpoint_failed"]]
    negatives = [row for row in rows if not row["midpoint_failed"]]
    rng = random.Random(seed)
    for _epoch in range(max(1, epochs)):
        sampled_negatives = rng.sample(
            negatives, min(len(negatives), 3 * len(positives))
        )
        epoch_rows = positives + sampled_negatives
        rng.shuffle(epoch_rows)
        for row in epoch_rows:
            output = model(**row["tensors"])
            probability = output["failure_probability"].clamp(
                1.0e-6, 1.0 - 1.0e-6
            )
            target = torch.tensor(float(row["midpoint_failed"]))
            probability_loss = F.binary_cross_entropy(
                probability, target
            )
            magnitude_loss = (
                F.smooth_l1_loss(
                    output["conditional_wasted_time_sec"],
                    torch.tensor(row["failure_cost_proxy_sec"]),
                )
                if row["midpoint_failed"]
                else torch.zeros(())
            )
            loss = probability_loss + 0.1 * magnitude_loss
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            optimizer.step()
    model.eval()
    return model


def _predict_rows(model, rows):
    predictions = []
    with torch.inference_mode():
        for row in rows:
            output = model(**row["tensors"])
            probability = float(output["failure_probability"])
            magnitude = float(output["conditional_wasted_time_sec"])
            predictions.append(
                {
                    "context_id": row["context_id"],
                    "instance_index": row["instance_index"],
                    "scale": row["scale"],
                    "target": bool(row["midpoint_failed"]),
                    "failure_probability": probability,
                    "conditional_wasted_time_sec": magnitude,
                    "expected_waste_sec": probability * magnitude,
                }
            )
    return predictions


def _calibrate(rows):
    probability_candidates = sorted(
        {float(row["failure_probability"]) for row in rows}, reverse=True
    )
    expected_values = sorted(
        {float(row["expected_waste_sec"]) for row in rows}, reverse=True
    )
    if len(expected_values) > 32:
        expected_candidates = [
            expected_values[
                round(index * (len(expected_values) - 1) / 31)
            ]
            for index in range(32)
        ]
    else:
        expected_candidates = expected_values
    best = None
    for probability_threshold in probability_candidates:
        for expected_threshold in expected_candidates:
            selected = [
                row
                for row in rows
                if row["failure_probability"] >= probability_threshold
                and row["expected_waste_sec"] >= expected_threshold
            ]
            if not selected:
                continue
            tp = sum(bool(row["target"]) for row in selected)
            fp = len(selected) - tp
            precision_lower = _wilson_lower(tp, len(selected))
            # Exactness cannot be harmed; require no observed time-harmful
            # skip and a conservative beneficial-action precision bound.
            gate_pass = fp == 0 and precision_lower >= 0.80
            candidate = (
                gate_pass,
                tp,
                sum(row["expected_waste_sec"] for row in selected),
                probability_threshold,
                expected_threshold,
                fp,
                precision_lower,
            )
            if best is None or candidate[:3] > best[:3]:
                best = candidate
    if best is None:
        best = (False, 0, 0.0, 1.0, math.inf, 0, 0.0)
    gate_pass, tp, _score, p_threshold, e_threshold, fp, lower = best
    return {
        "gate_pass": bool(gate_pass),
        "failure_probability_threshold": float(p_threshold),
        "expected_waste_threshold_sec": float(e_threshold),
        "selected_count": int(tp + fp),
        "true_failure_count": int(tp),
        "false_skip_count": int(fp),
        "harmful_skip_rate_observed": (
            float(fp / (tp + fp)) if tp + fp else 0.0
        ),
        "beneficial_action_precision_95_lower": float(lower),
        "criteria": {
            "false_skip_count": 0,
            "beneficial_action_precision_95_lower": 0.80,
        },
    }


def _metrics(rows, calibration=None):
    targets = [int(row["target"]) for row in rows]
    scores = [float(row["failure_probability"]) for row in rows]
    result = {
        "count": len(rows),
        "failure_count": sum(targets),
        "success_count": len(rows) - sum(targets),
        "roc_auc": _roc_auc(targets, scores),
        "mean_failure_probability_on_failure": statistics.fmean(
            score for target, score in zip(targets, scores) if target
        ),
        "mean_failure_probability_on_success": statistics.fmean(
            score for target, score in zip(targets, scores) if not target
        ),
    }
    if calibration is not None:
        selected = [
            row
            for row in rows
            if row["failure_probability"]
            >= calibration["failure_probability_threshold"]
            and row["expected_waste_sec"]
            >= calibration["expected_waste_threshold_sec"]
        ]
        tp = sum(bool(row["target"]) for row in selected)
        fp = len(selected) - tp
        result.update(
            {
                "selected_count": len(selected),
                "true_failure_count_selected": tp,
                "false_skip_count": fp,
                "precision": tp / len(selected) if selected else None,
                "failure_recall": tp / sum(targets) if sum(targets) else None,
            }
        )
    return result


def _roc_auc(targets, scores):
    positives = [score for target, score in zip(targets, scores) if target]
    negatives = [score for target, score in zip(targets, scores) if not target]
    if not positives or not negatives:
        return None
    wins = sum(
        1.0 if positive > negative else 0.5 if positive == negative else 0.0
        for positive in positives
        for negative in negatives
    )
    return wins / (len(positives) * len(negatives))


def _wilson_lower(successes: int, total: int) -> float:
    if total <= 0:
        return 0.0
    z = 1.959963984540054
    p = successes / total
    denominator = 1.0 + z * z / total
    center = p + z * z / (2.0 * total)
    radius = z * math.sqrt(
        p * (1.0 - p) / total + z * z / (4.0 * total * total)
    )
    return max(0.0, (center - radius) / denominator)


def _counts(rows):
    return {
        "contexts": len(rows),
        "failures": sum(bool(row["midpoint_failed"]) for row in rows),
        "instances": len({row["instance_content_hash"] for row in rows}),
        "by_scale": {
            str(scale): {
                "contexts": sum(row["scale"] == scale for row in rows),
                "failures": sum(
                    row["scale"] == scale and row["midpoint_failed"]
                    for row in rows
                ),
            }
            for scale in (30, 50)
        },
    }


def _serializable_row(row):
    return {
        key: row[key]
        for key in (
            "context_id",
            "instance_content_hash",
            "instance_id",
            "instance_path",
            "source_probe",
            "scale",
            "instance_index",
            "round",
            "split",
            "midpoint_failed",
            "termination_reason",
            "dual_fingerprint",
            "failure_cost_proxy_sec",
            "previous_midpoint_outcome",
            "consecutive_observed_failures",
        )
    }


def _feature_envelope(rows):
    contexts = [row["features"].context_features for row in rows]
    return {
        "context_min": [
            min(values[index] for values in contexts)
            for index in range(len(contexts[0]))
        ],
        "context_max": [
            max(values[index] for values in contexts)
            for index in range(len(contexts[0]))
        ],
        "node_max_abs": max(
            abs(value)
            for row in rows
            for values in row["features"].node_features
            for value in values
        ),
        "edge_max_abs": max(
            abs(value)
            for row in rows
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
