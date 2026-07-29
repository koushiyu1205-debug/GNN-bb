#!/usr/bin/env python3
"""Grouped realizability pilot for the P0 V3 one-shot proof-tail veto."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from math import expm1, log1p
from pathlib import Path
import random
import statistics
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.proof_tail_veto_features import (  # noqa: E402
    build_proof_tail_veto_features,
    proof_tail_veto_feature_dimensions,
)


SCHEMA = "lunar_ice_bpc.p0v3_proof_tail_veto_ladder_pilot.v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _fold(instance_hash: str, fold_count: int) -> int:
    return int(
        hashlib.sha256(instance_hash.encode("utf-8")).hexdigest()[:16],
        16,
    ) % int(fold_count)


def _enrich_two_strike_history(
    snapshot: dict,
    root_source: dict,
) -> dict:
    """Backfill V2 two-strike fields for immutable V1 snapshots."""

    enriched = dict(snapshot)
    trajectory = dict(enriched.get("trajectory_features") or {})
    round_index = int(enriched.get("round") or 0)
    history_by_round = {
        int(row.get("round") or 0): dict(row)
        for row in (
            (root_source.get("result") or {}).get("history")
            or ()
        )
    }
    penultimate = history_by_round.get(round_index - 2, {})
    previous = history_by_round.get(round_index - 1, {})
    if not previous or not penultimate:
        raise ValueError(
            "two-strike feature history is missing from root source"
        )
    trajectory.update(
        {
            "penultimate_harvest_column_count": int(
                penultimate.get(
                    "labeling_final_judge_harvest_pass_column_count"
                )
                or 0
            ),
            "penultimate_harvest_processed_labels": int(
                penultimate.get(
                    "labeling_final_judge_harvest_pass_processed_labels"
                )
                or 0
            ),
            "penultimate_best_true_rc": float(
                penultimate.get("harvest_best_true_rc") or 0.0
            ),
        }
    )
    current_duals = dict(
        (enriched.get("true_duals") or {}).get("task_duals")
        or {}
    )
    penultimate_duals = dict(
        (penultimate.get("dual_context") or {}).get("task_duals")
        or {}
    )
    dual_keys = set(current_duals) | set(penultimate_duals)
    dual_deltas = [
        abs(
            float(current_duals.get(key, 0.0))
            - float(penultimate_duals.get(key, 0.0))
        )
        for key in dual_keys
    ]
    trajectory["dual_l1_delta_from_penultimate"] = sum(
        dual_deltas
    )
    trajectory["dual_linf_delta_from_penultimate"] = max(
        dual_deltas,
        default=0.0,
    )
    current_bound = float(enriched.get("node_lp_bound") or 0.0)
    trajectory["node_lp_bound_delta_from_penultimate"] = (
        current_bound
        - float(penultimate.get("node_lp_bound") or current_bound)
    )
    if int(
        trajectory.get("previous_harvest_column_count") or 0
    ) != int(
        previous.get(
            "labeling_final_judge_harvest_pass_column_count"
        )
        or 0
    ):
        raise ValueError(
            "snapshot previous harvest does not match root history"
        )
    enriched["trajectory_features"] = trajectory
    return enriched


def _examples(
    *,
    all_state_labels: Path,
    first_trigger_labels: Path,
) -> tuple[list[dict], list[dict]]:
    all_payload = _load(all_state_labels)
    first_payload = _load(first_trigger_labels)
    first_by_state = {
        str(row["source_state_hash"]): dict(row)
        for row in first_payload["rows"]
    }
    data_cache = {}
    catalog_cache = {}
    examples = []
    excluded = []
    for source in all_payload["rows"]:
        row = dict(
            first_by_state.get(
                str(source["source_state_hash"]),
                source,
            )
        )
        fork_path = Path(
            source["fork_paths_by_action"]["proof_only"][0]
        )
        fork = _load(fork_path)
        snapshot_path = Path(fork["source_snapshot_path"])
        snapshot = _load(snapshot_path)
        required_strikes = int(
            snapshot.get("required_sparse_harvest_strikes") or 1
        )
        observed_strikes = int(
            snapshot.get("sparse_harvest_strike_count") or 0
        )
        if (
            str(snapshot.get("source_pass_strategy") or "")
            != "proof_only"
            or required_strikes < 2
            or observed_strikes != required_strikes
        ):
            excluded.append(
                {
                    "instance_id": source["instance_id"],
                    "state_hash": source["source_state_hash"],
                    "source_pass_strategy": snapshot.get(
                        "source_pass_strategy"
                    ),
                    "required_sparse_harvest_strikes": (
                        required_strikes
                    ),
                    "observed_sparse_harvest_strikes": (
                        observed_strikes
                    ),
                    "reason": (
                        "NOT_A_TWO_STRIKE_PRE_CALL_STATE"
                    ),
                }
            )
            continue
        catalog_path = snapshot_path.parent / "column_catalog.json"
        root_source_path = snapshot_path.parent.parent / "root_source.json"
        root_source = _load(root_source_path)
        snapshot = _enrich_two_strike_history(
            snapshot,
            root_source,
        )
        instance_path = Path(root_source["instance_path"])
        data = data_cache.get(instance_path)
        if data is None:
            data = load_lunar_ice_data(_load(instance_path))
            data_cache[instance_path] = data
        catalog = catalog_cache.get(catalog_path)
        if catalog is None:
            catalog = _load(catalog_path)
            catalog_cache[catalog_path] = catalog
        features = build_proof_tail_veto_features(
            data,
            snapshot,
            column_catalog=catalog,
        )
        examples.append(
            {
                "instance_id": row["instance_id"],
                "instance_content_hash": row[
                    "instance_content_hash"
                ],
                "state_hash": row["source_state_hash"],
                "scale": int(row["scale"]),
                "is_first_trigger": (
                    str(row["source_state_hash"])
                    in first_by_state
                ),
                "features": features,
                "harvest_cost_sec": float(
                    row["harvest_cost_to_closure_sec"]
                ),
                "proof_cost_sec": float(
                    row["proof_cost_to_closure_sec"]
                ),
                "raw_advantage_sec": float(
                    row["proof_cost_to_closure_sec"]
                )
                - float(row["harvest_cost_to_closure_sec"]),
                "deadband_sec": float(row["deadband_sec"]),
                "veto_target": (
                    row["override_or_abstain_target"]
                    == "harvest_then_proof"
                ),
            }
        )
    return examples, excluded


def _tensor(example: dict, torch):
    features = example["features"]
    return {
        "node_features": torch.tensor(
            features.node_features,
            dtype=torch.float32,
        ),
        "edge_index": torch.tensor(
            features.edge_index,
            dtype=torch.long,
        ),
        "edge_features": torch.tensor(
            features.edge_features,
            dtype=torch.float32,
        ),
        "global_features": torch.tensor(
            features.global_features,
            dtype=torch.float32,
        ),
    }


def _train_one(
    *,
    kind: str,
    train_rows: list[dict],
    heldout_rows: list[dict],
    epochs: int,
    seed: int,
    torch,
    ProofTailVetoModel,
    proof_tail_veto_loss,
    initial_model=None,
    freeze_pretrained_encoder: bool = False,
) -> tuple[dict, object]:
    random.seed(seed)
    torch.manual_seed(seed)
    dimensions = proof_tail_veto_feature_dimensions()
    model = (
        initial_model
        if initial_model is not None
        else ProofTailVetoModel(
            kind=kind,
            node_input_dim=dimensions[0],
            edge_input_dim=dimensions[1],
            global_input_dim=dimensions[2],
        )
    )
    if str(model.kind) != str(kind):
        raise ValueError("pretrained model kind mismatch")
    if freeze_pretrained_encoder:
        for module in (
            model.node_encoder,
            model.edge_encoder,
            model.attention,
            model.harvest_dynamics_head,
        ):
            for parameter in module.parameters():
                parameter.requires_grad_(False)
    optimizer = torch.optim.Adam(
        [
            parameter
            for parameter in model.parameters()
            if parameter.requires_grad
        ],
        lr=1.0e-3,
        weight_decay=1.0e-4,
    )
    state_count = Counter(
        row["instance_content_hash"] for row in train_rows
    )
    tensors = {
        row["state_hash"]: _tensor(row, torch)
        for row in (*train_rows, *heldout_rows)
    }
    started = perf_counter()
    final_losses = {}
    model.train()
    for _ in range(max(1, int(epochs))):
        optimizer.zero_grad(set_to_none=True)
        losses = []
        components = {
            "cost": [],
            "advantage": [],
            "ranking": [],
            "selective_classification": [],
            "expected_regret": [],
        }
        for row in train_rows:
            output = model(**tensors[row["state_hash"]])
            result = proof_tail_veto_loss(
                output,
                harvest_log_cost=torch.tensor(
                    log1p(row["harvest_cost_sec"]),
                    dtype=torch.float32,
                ),
                proof_log_cost=torch.tensor(
                    log1p(row["proof_cost_sec"]),
                    dtype=torch.float32,
                ),
                instance_weight=torch.tensor(
                    1.0
                    / state_count[row["instance_content_hash"]],
                    dtype=torch.float32,
                ),
                raw_advantage_sec=torch.tensor(
                    row["raw_advantage_sec"],
                    dtype=torch.float32,
                ),
                deadband_sec=torch.tensor(
                    row["deadband_sec"],
                    dtype=torch.float32,
                ),
                veto_target=torch.tensor(
                    float(row["veto_target"]),
                    dtype=torch.float32,
                ),
            )
            losses.append(result["total"])
            for key in components:
                components[key].append(result[key])
        loss = torch.stack(losses).sum() / max(
            1, len(state_count)
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        final_losses = {
            "total": float(loss.detach()),
            **{
                key: float(
                    torch.stack(values).sum().detach()
                    / max(1, len(state_count))
                )
                for key, values in components.items()
            },
        }
    train_wall = perf_counter() - started
    model.eval()
    train_first = [
        row for row in train_rows if row["is_first_trigger"]
    ]
    train_predictions = [
        _predict(model, row, tensors[row["state_hash"]], torch)
        for row in train_first
    ]
    unsafe_scores = [
        pred["veto_probability"]
        for row, pred in zip(
            train_first,
            train_predictions,
            strict=True,
        )
        if not row["veto_target"]
    ]
    threshold = (
        min(1.0, max(unsafe_scores) + 1.0e-6)
        if unsafe_scores
        else 0.5
    )
    heldout_predictions = []
    inference_times = []
    for row in heldout_rows:
        if not row["is_first_trigger"]:
            continue
        started = perf_counter()
        prediction = _predict(
            model,
            row,
            tensors[row["state_hash"]],
            torch,
        )
        inference_times.append(perf_counter() - started)
        prediction["veto_probability_threshold"] = threshold
        prediction["predicted_veto"] = bool(
            prediction["veto_probability"] > threshold
        )
        heldout_predictions.append(prediction)
    result = {
        "kind": kind,
        "seed": seed,
        "epochs": int(epochs),
        "parameter_count": sum(
            parameter.numel() for parameter in model.parameters()
        ),
        "trainable_parameter_count": sum(
            parameter.numel()
            for parameter in model.parameters()
            if parameter.requires_grad
        ),
        "pretrained_encoder_frozen": bool(
            freeze_pretrained_encoder
        ),
        "train_instance_count": len(state_count),
        "train_state_count": len(train_rows),
        "train_wall_sec": train_wall,
        "final_losses": final_losses,
        "veto_probability_threshold": threshold,
        "heldout_predictions": heldout_predictions,
        "forward_wall_sec": inference_times,
    }
    return result, model


def _predict(model, row: dict, tensors: dict, torch) -> dict:
    with torch.no_grad():
        output = model(**tensors)
    harvest = expm1(float(output["harvest_log_cost"]))
    proof = expm1(float(output["proof_log_cost"]))
    return {
        "instance_id": row["instance_id"],
        "instance_content_hash": row["instance_content_hash"],
        "state_hash": row["state_hash"],
        "scale": row["scale"],
        "actual_veto_target": bool(row["veto_target"]),
        "actual_advantage_sec": row["raw_advantage_sec"],
        "predicted_harvest_cost_sec": harvest,
        "predicted_proof_cost_sec": proof,
        "predicted_advantage_sec": proof - harvest,
        "veto_probability": float(output["veto_probability"]),
    }


def _metrics(
    predictions: list[dict],
    *,
    minimum_call_cost_sec: float,
) -> dict:
    true_positive = sum(
        row["predicted_veto"] and row["actual_veto_target"]
        for row in predictions
    )
    false_positive = sum(
        row["predicted_veto"] and not row["actual_veto_target"]
        for row in predictions
    )
    false_negative = sum(
        not row["predicted_veto"] and row["actual_veto_target"]
        for row in predictions
    )
    action_gain = sum(
        float(row["actual_advantage_sec"])
        for row in predictions
        if row["predicted_veto"]
    )
    total_call_cost = (
        len(predictions) * float(minimum_call_cost_sec)
    )
    return {
        "first_trigger_count": len(predictions),
        "true_veto_count": true_positive,
        "false_veto_count": false_positive,
        "missed_veto_count": false_negative,
        "veto_precision": (
            true_positive / (true_positive + false_positive)
            if true_positive + false_positive
            else 1.0
        ),
        "veto_recall": (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 1.0
        ),
        "action_gain_before_call_cost_sec": action_gain,
        "assumed_total_call_cost_sec": total_call_cost,
        "realized_net_gain_sec": action_gain - total_call_cost,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-state-labels", required=True)
    parser.add_argument("--first-trigger-labels", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--fold-count", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20260726)
    parser.add_argument(
        "--minimum-call-cost-sec",
        type=float,
        default=0.02,
    )
    args = parser.parse_args()
    examples, excluded_examples = _examples(
        all_state_labels=(ROOT / args.all_state_labels).resolve(),
        first_trigger_labels=(
            ROOT / args.first_trigger_labels
        ).resolve(),
    )
    fold_count = max(2, int(args.fold_count))
    instance_folds = {
        row["instance_content_hash"]: _fold(
            row["instance_content_hash"],
            fold_count,
        )
        for row in examples
    }

    import torch

    from lunar_ice_bpc.guidance.proof_tail_veto_model import (
        PROOF_TAIL_VETO_MODEL_LADDER,
        ProofTailVetoModel,
        proof_tail_veto_loss,
    )

    torch.set_num_threads(1)
    model_results = []
    for kind in PROOF_TAIL_VETO_MODEL_LADDER:
        folds = []
        all_predictions = []
        all_forward = []
        for fold in range(fold_count):
            heldout_instances = {
                instance_hash
                for instance_hash, assigned in instance_folds.items()
                if assigned == fold
            }
            if not heldout_instances:
                continue
            train_rows = [
                row
                for row in examples
                if row["instance_content_hash"]
                not in heldout_instances
            ]
            heldout_rows = [
                row
                for row in examples
                if row["instance_content_hash"]
                in heldout_instances
            ]
            fold_result, _ = _train_one(
                kind=kind,
                train_rows=train_rows,
                heldout_rows=heldout_rows,
                epochs=int(args.epochs),
                seed=int(args.seed) + fold,
                torch=torch,
                ProofTailVetoModel=ProofTailVetoModel,
                proof_tail_veto_loss=proof_tail_veto_loss,
            )
            fold_result["fold"] = fold
            fold_result["heldout_instance_hashes"] = sorted(
                heldout_instances
            )
            folds.append(fold_result)
            all_predictions.extend(
                fold_result["heldout_predictions"]
            )
            all_forward.extend(fold_result["forward_wall_sec"])
        metrics = _metrics(
            all_predictions,
            minimum_call_cost_sec=float(
                args.minimum_call_cost_sec
            ),
        )
        model_results.append(
            {
                "kind": kind,
                "folds": folds,
                "metrics": metrics,
                "forward_wall_sec_p50": (
                    statistics.median(all_forward)
                    if all_forward
                    else None
                ),
                "forward_wall_sec_max": (
                    max(all_forward) if all_forward else None
                ),
            }
        )
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "promotion_authorized": False,
        "all_state_labels": str(
            (ROOT / args.all_state_labels).resolve()
        ),
        "first_trigger_labels": str(
            (ROOT / args.first_trigger_labels).resolve()
        ),
        "example_count": len(examples),
        "instance_count": len(
            {row["instance_content_hash"] for row in examples}
        ),
        "first_trigger_count": sum(
            row["is_first_trigger"] for row in examples
        ),
        "excluded_non_call_state_count": len(excluded_examples),
        "excluded_non_call_states": excluded_examples,
        "fold_count": fold_count,
        "instance_folds": instance_folds,
        "epochs": int(args.epochs),
        "minimum_call_cost_sec": float(
            args.minimum_call_cost_sec
        ),
        "models": model_results,
        "selection_status": (
            "PILOT_ONLY_NO_MODEL_PROMOTED"
        ),
        "torch_version": str(torch.__version__),
    }
    payload["artifact_hash"] = _hash(payload)
    _write((ROOT / args.output).resolve(), payload)
    print(
        json.dumps(
            {
                "example_count": payload["example_count"],
                "instance_count": payload["instance_count"],
                "models": [
                    {
                        "kind": row["kind"],
                        **row["metrics"],
                    }
                    for row in model_results
                ],
                "selection_status": payload[
                    "selection_status"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
