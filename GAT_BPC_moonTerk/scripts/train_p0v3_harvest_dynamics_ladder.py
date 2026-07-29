#!/usr/bin/env python3
"""Grouped dense pretraining pilot for proof-tail harvestability."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from math import log1p
from pathlib import Path
import random
import statistics
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.exact.core.data import load_lunar_ice_data  # noqa: E402
from lunar_ice_bpc.guidance.proof_tail_veto_features import (  # noqa: E402
    build_harvest_dynamics_features,
    build_proof_tail_veto_features,
    proof_tail_veto_feature_dimensions,
)


SCHEMA = "lunar_ice_bpc.p0v3_harvest_dynamics_ladder_pilot.v1"


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


def _enrich_history(snapshot: dict, root_source: dict) -> dict:
    enriched = dict(snapshot)
    trajectory = dict(enriched.get("trajectory_features") or {})
    current_round = int(enriched.get("round") or 0)
    by_round = {
        int(row.get("round") or 0): dict(row)
        for row in (
            (root_source.get("result") or {}).get("history")
            or ()
        )
    }
    penultimate = by_round.get(current_round - 2, {})
    current_duals = dict(
        (enriched.get("true_duals") or {}).get("task_duals")
        or {}
    )
    penultimate_duals = dict(
        (penultimate.get("dual_context") or {}).get("task_duals")
        or {}
    )
    dual_deltas = [
        abs(
            float(current_duals.get(key, 0.0))
            - float(penultimate_duals.get(key, 0.0))
        )
        for key in set(current_duals) | set(penultimate_duals)
    ]
    current_bound = float(enriched.get("node_lp_bound") or 0.0)
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
            "dual_l1_delta_from_penultimate": sum(dual_deltas),
            "dual_linf_delta_from_penultimate": max(
                dual_deltas,
                default=0.0,
            ),
            "node_lp_bound_delta_from_penultimate": (
                current_bound
                - float(
                    penultimate.get("node_lp_bound")
                    or current_bound
                )
            ),
        }
    )
    enriched["trajectory_features"] = trajectory
    return enriched


def _examples(path: Path) -> list[dict]:
    payload = _load(path)
    data_cache = {}
    root_cache = {}
    catalog_cache = {}
    examples = []
    for row in payload["rows"]:
        snapshot_path = Path(row["snapshot_path"])
        root_path = Path(row["root_source_path"])
        root = root_cache.get(root_path)
        if root is None:
            root = _load(root_path)
            root_cache[root_path] = root
        snapshot = _enrich_history(
            _load(snapshot_path),
            root,
        )
        instance_path = Path(row["instance_path"])
        data = data_cache.get(instance_path)
        if data is None:
            data = load_lunar_ice_data(_load(instance_path))
            data_cache[instance_path] = data
        catalog_path = Path(row["column_catalog_path"])
        catalog = catalog_cache.get(catalog_path)
        if catalog is None:
            catalog = _load(catalog_path)
            catalog_cache[catalog_path] = catalog
        features = build_harvest_dynamics_features(
            data,
            snapshot,
            column_catalog=catalog,
        )
        examples.append(
            {
                **dict(row),
                "features": features,
                "best_rc_log_magnitude": log1p(
                    abs(float(row["harvest_best_true_rc"]))
                    * 1.0e6
                ),
                "log_wall_sec": log1p(
                    float(row["harvest_pass_wall_sec"])
                ),
            }
        )
    return examples


def _action_probe_examples(path: Path) -> list[dict]:
    payload = _load(path)
    data_cache = {}
    catalog_cache = {}
    root_cache = {}
    examples = []
    for row in payload["rows"]:
        proof_path = Path(
            row["fork_paths_by_action"]["proof_only"][0]
        )
        fork = _load(proof_path)
        snapshot_path = Path(fork["source_snapshot_path"])
        snapshot = _load(snapshot_path)
        if (
            str(snapshot.get("source_pass_strategy") or "")
            != "proof_only"
            or int(
                snapshot.get(
                    "required_sparse_harvest_strikes"
                )
                or 1
            )
            < 2
            or int(
                snapshot.get("sparse_harvest_strike_count")
                or 0
            )
            != int(
                snapshot.get(
                    "required_sparse_harvest_strikes"
                )
                or 1
            )
        ):
            continue
        root_path = snapshot_path.parent.parent / "root_source.json"
        root = root_cache.get(root_path)
        if root is None:
            root = _load(root_path)
            root_cache[root_path] = root
        snapshot = _enrich_history(snapshot, root)
        instance_path = Path(root["instance_path"])
        data = data_cache.get(instance_path)
        if data is None:
            data = load_lunar_ice_data(_load(instance_path))
            data_cache[instance_path] = data
        catalog_path = snapshot_path.parent / "column_catalog.json"
        catalog = catalog_cache.get(catalog_path)
        if catalog is None:
            catalog = _load(catalog_path)
            catalog_cache[catalog_path] = catalog
        examples.append(
            {
                "instance_id": row["instance_id"],
                "instance_content_hash": row[
                    "instance_content_hash"
                ],
                "scale": int(row["scale"]),
                "state_hash": row["source_state_hash"],
                "features": build_proof_tail_veto_features(
                    data,
                    snapshot,
                    column_catalog=catalog,
                ),
                "actual_veto_target": bool(
                    row["override_or_abstain_target"]
                    == "harvest_then_proof"
                ),
                "actual_advantage_sec": (
                    float(row["proof_cost_to_closure_sec"])
                    - float(row["harvest_cost_to_closure_sec"])
                ),
            }
        )
    return examples


def _tensor(row: dict, torch) -> dict:
    features = row["features"]
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


def _train_fold(
    *,
    kind: str,
    train_rows: list[dict],
    heldout_rows: list[dict],
    heldout_action_rows: list[dict],
    tensors: dict,
    epochs: int,
    seed: int,
    torch,
    ProofTailVetoModel,
    harvest_dynamics_loss,
) -> tuple[dict, object]:
    random.seed(seed)
    torch.manual_seed(seed)
    dimensions = proof_tail_veto_feature_dimensions()
    model = ProofTailVetoModel(
        kind=kind,
        node_input_dim=dimensions[0],
        edge_input_dim=dimensions[1],
        global_input_dim=dimensions[2],
    )
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=1.0e-3,
        weight_decay=1.0e-4,
    )
    instance_counts = Counter(
        row["instance_content_hash"] for row in train_rows
    )
    started = perf_counter()
    final_losses = {}
    for _ in range(max(1, int(epochs))):
        optimizer.zero_grad(set_to_none=True)
        losses = []
        components = {
            "yield": [],
            "added": [],
            "best_rc": [],
            "wall": [],
            "sparse": [],
        }
        sparse_count = sum(row["sparse_harvest"] for row in train_rows)
        nonsparse_count = len(train_rows) - sparse_count
        sparse_positive_weight = (
            nonsparse_count / max(1.0, float(sparse_count))
        )
        for row in train_rows:
            output = model(**tensors[row["state_hash"]])
            result = harvest_dynamics_loss(
                output,
                yield_fraction=torch.tensor(
                    row["harvest_yield_fraction"],
                    dtype=torch.float32,
                ),
                added_fraction=torch.tensor(
                    row["added_fraction"],
                    dtype=torch.float32,
                ),
                best_rc_log_magnitude=torch.tensor(
                    row["best_rc_log_magnitude"],
                    dtype=torch.float32,
                ),
                log_wall_sec=torch.tensor(
                    row["log_wall_sec"],
                    dtype=torch.float32,
                ),
                sparse_target=torch.tensor(
                    float(row["sparse_harvest"]),
                    dtype=torch.float32,
                ),
                sparse_positive_weight=torch.tensor(
                    sparse_positive_weight,
                    dtype=torch.float32,
                ),
                instance_weight=torch.tensor(
                    1.0
                    / instance_counts[row["instance_content_hash"]],
                    dtype=torch.float32,
                ),
            )
            losses.append(result["total"])
            for key in components:
                components[key].append(result[key])
        total = torch.stack(losses).sum() / max(
            1,
            len(instance_counts),
        )
        total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        optimizer.step()
        final_losses = {
            "total": float(total.detach()),
            **{
                key: float(
                    torch.stack(values).sum().detach()
                    / max(1, len(instance_counts))
                )
                for key, values in components.items()
            },
        }
    model.eval()
    predictions = []
    with torch.no_grad():
        for row in heldout_rows:
            output = model(**tensors[row["state_hash"]])
            predictions.append(
                {
                    "instance_content_hash": row[
                        "instance_content_hash"
                    ],
                    "scale": int(row["scale"]),
                    "state_hash": row["state_hash"],
                    "actual_yield_fraction": float(
                        row["harvest_yield_fraction"]
                    ),
                    "predicted_yield_fraction": float(
                        output["harvest_yield_fraction"]
                    ),
                    "actual_added_fraction": float(
                        row["added_fraction"]
                    ),
                    "predicted_added_fraction": float(
                        output["harvest_added_fraction"]
                    ),
                    "actual_best_rc_log_magnitude": float(
                        row["best_rc_log_magnitude"]
                    ),
                    "predicted_best_rc_log_magnitude": float(
                        output[
                            "harvest_best_rc_log_magnitude"
                        ]
                    ),
                    "actual_log_wall_sec": float(
                        row["log_wall_sec"]
                    ),
                    "predicted_log_wall_sec": float(
                        output["harvest_log_wall_sec"]
                    ),
                    "actual_sparse": bool(row["sparse_harvest"]),
                    "predicted_sparse_probability": float(
                        output["harvest_sparse_probability"]
                    ),
                }
            )
        action_probes = []
        for row in heldout_action_rows:
            output = model(**tensors[row["state_hash"]])
            action_probes.append(
                {
                    "instance_id": row["instance_id"],
                    "instance_content_hash": row[
                        "instance_content_hash"
                    ],
                    "scale": int(row["scale"]),
                    "state_hash": row["state_hash"],
                    "actual_veto_target": bool(
                        row["actual_veto_target"]
                    ),
                    "actual_advantage_sec": float(
                        row["actual_advantage_sec"]
                    ),
                    "predicted_harvest_yield_fraction": float(
                        output["harvest_yield_fraction"]
                    ),
                    "predicted_harvest_sparse_probability": float(
                        output["harvest_sparse_probability"]
                    ),
                    "predicted_best_rc_log_magnitude": float(
                        output[
                            "harvest_best_rc_log_magnitude"
                        ]
                    ),
                }
            )
    return {
        "kind": kind,
        "epochs": int(epochs),
        "seed": int(seed),
        "parameter_count": sum(
            parameter.numel() for parameter in model.parameters()
        ),
        "train_instance_count": len(instance_counts),
        "train_row_count": len(train_rows),
        "train_wall_sec": perf_counter() - started,
        "final_losses": final_losses,
        "heldout_predictions": predictions,
        "heldout_action_probes": action_probes,
    }, model


def _auc(predictions: list[dict]) -> float | None:
    positive = [
        row["predicted_sparse_probability"]
        for row in predictions
        if row["actual_sparse"]
    ]
    negative = [
        row["predicted_sparse_probability"]
        for row in predictions
        if not row["actual_sparse"]
    ]
    if not positive or not negative:
        return None
    return sum(
        (left > right) + 0.5 * (left == right)
        for left in positive
        for right in negative
    ) / (len(positive) * len(negative))


def _metrics(predictions: list[dict]) -> dict:
    def mae(actual: str, predicted: str) -> float:
        return statistics.fmean(
            abs(float(row[actual]) - float(row[predicted]))
            for row in predictions
        )

    scale_metrics = {}
    for scale in sorted({row["scale"] for row in predictions}):
        selected = [
            row for row in predictions if row["scale"] == scale
        ]
        scale_metrics[str(scale)] = {
            "row_count": len(selected),
            "yield_mae": statistics.fmean(
                abs(
                    row["actual_yield_fraction"]
                    - row["predicted_yield_fraction"]
                )
                for row in selected
            ),
            "sparse_auc": _auc(selected),
        }
    return {
        "heldout_row_count": len(predictions),
        "yield_mae": mae(
            "actual_yield_fraction",
            "predicted_yield_fraction",
        ),
        "added_mae": mae(
            "actual_added_fraction",
            "predicted_added_fraction",
        ),
        "best_rc_log_magnitude_mae": mae(
            "actual_best_rc_log_magnitude",
            "predicted_best_rc_log_magnitude",
        ),
        "log_wall_sec_mae": mae(
            "actual_log_wall_sec",
            "predicted_log_wall_sec",
        ),
        "sparse_auc": _auc(predictions),
        "scale_metrics": scale_metrics,
    }


def _binary_auc(
    rows: list[dict],
    *,
    score_key: str,
    reverse: bool = False,
) -> float | None:
    positive = [
        float(row[score_key])
        for row in rows
        if row["actual_veto_target"]
    ]
    negative = [
        float(row[score_key])
        for row in rows
        if not row["actual_veto_target"]
    ]
    if not positive or not negative:
        return None
    direction = -1.0 if reverse else 1.0
    return sum(
        (direction * left > direction * right)
        + 0.5 * (left == right)
        for left in positive
        for right in negative
    ) / (len(positive) * len(negative))


def _action_probe_metrics(rows: list[dict]) -> dict:
    return {
        "first_trigger_count": len(rows),
        "veto_target_count": sum(
            row["actual_veto_target"] for row in rows
        ),
        "veto_auc_from_predicted_harvest_yield": _binary_auc(
            rows,
            score_key="predicted_harvest_yield_fraction",
        ),
        "veto_auc_from_predicted_sparse_probability": _binary_auc(
            rows,
            score_key="predicted_harvest_sparse_probability",
            reverse=True,
        ),
        "veto_auc_from_predicted_best_rc_magnitude": _binary_auc(
            rows,
            score_key="predicted_best_rc_log_magnitude",
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--first-trigger-labels")
    parser.add_argument("--fold-count", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20260726)
    args = parser.parse_args()
    examples = _examples((ROOT / args.rows).resolve())
    action_examples = (
        _action_probe_examples(
            (ROOT / args.first_trigger_labels).resolve()
        )
        if args.first_trigger_labels
        else []
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
        harvest_dynamics_loss,
    )

    torch.set_num_threads(1)
    tensors = {
        row["state_hash"]: _tensor(row, torch)
        for row in (*examples, *action_examples)
    }
    models = []
    for kind in PROOF_TAIL_VETO_MODEL_LADDER:
        folds = []
        predictions = []
        action_probes = []
        for fold in range(fold_count):
            heldout_hashes = {
                instance_hash
                for instance_hash, assigned in instance_folds.items()
                if assigned == fold
            }
            if not heldout_hashes:
                continue
            train_rows = [
                row
                for row in examples
                if row["instance_content_hash"]
                not in heldout_hashes
            ]
            heldout_rows = [
                row
                for row in examples
                if row["instance_content_hash"] in heldout_hashes
            ]
            heldout_action_rows = [
                row
                for row in action_examples
                if row["instance_content_hash"] in heldout_hashes
            ]
            result, _ = _train_fold(
                kind=kind,
                train_rows=train_rows,
                heldout_rows=heldout_rows,
                heldout_action_rows=heldout_action_rows,
                tensors=tensors,
                epochs=int(args.epochs),
                seed=int(args.seed) + fold,
                torch=torch,
                ProofTailVetoModel=ProofTailVetoModel,
                harvest_dynamics_loss=harvest_dynamics_loss,
            )
            result["fold"] = fold
            result["heldout_instance_hashes"] = sorted(
                heldout_hashes
            )
            folds.append(result)
            predictions.extend(result["heldout_predictions"])
            action_probes.extend(
                result["heldout_action_probes"]
            )
        models.append(
            {
                "kind": kind,
                "folds": folds,
                "metrics": _metrics(predictions),
                "action_probe_metrics": _action_probe_metrics(
                    action_probes
                ),
            }
        )
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "pretraining_only": True,
        "selector_training_authorized": False,
        "rows_path": str((ROOT / args.rows).resolve()),
        "row_count": len(examples),
        "instance_count": len(instance_folds),
        "first_trigger_action_probe_count": len(action_examples),
        "fold_count": fold_count,
        "instance_folds": instance_folds,
        "epochs": int(args.epochs),
        "models": models,
        "selection_status": "DENSE_PRETRAINING_PILOT_ONLY",
        "torch_version": str(torch.__version__),
    }
    payload["artifact_hash"] = _hash(payload)
    _write((ROOT / args.output).resolve(), payload)
    print(
        json.dumps(
            {
                "row_count": payload["row_count"],
                "instance_count": payload["instance_count"],
                "models": [
                    {
                        "kind": row["kind"],
                        **row["metrics"],
                        "action_probe_metrics": row[
                            "action_probe_metrics"
                        ],
                    }
                    for row in models
                ],
                "selection_status": payload["selection_status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
