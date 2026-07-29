#!/usr/bin/env python3
"""Grouped dense-pretrain/frozen-selector proof-tail pilot."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SCHEMA = "lunar_ice_bpc.p0v3_proof_tail_transfer_ladder_pilot.v1"


def _module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(
        name,
        ROOT / relative_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harvest-dynamics-rows", required=True)
    parser.add_argument("--all-state-labels", required=True)
    parser.add_argument("--first-trigger-labels", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--fold-count", type=int, default=5)
    parser.add_argument("--pretrain-epochs", type=int, default=40)
    parser.add_argument("--selector-epochs", type=int, default=120)
    parser.add_argument("--seed", type=int, default=20260726)
    parser.add_argument(
        "--minimum-call-cost-sec",
        type=float,
        default=0.02,
    )
    args = parser.parse_args()
    dense_module = _module(
        "p0v3_harvest_dynamics_train",
        "scripts/train_p0v3_harvest_dynamics_ladder.py",
    )
    selector_module = _module(
        "p0v3_proof_tail_selector_train",
        "scripts/train_p0v3_proof_tail_veto_ladder.py",
    )
    dense_rows = dense_module._examples(
        (ROOT / args.harvest_dynamics_rows).resolve()
    )
    selector_rows, excluded = selector_module._examples(
        all_state_labels=(
            ROOT / args.all_state_labels
        ).resolve(),
        first_trigger_labels=(
            ROOT / args.first_trigger_labels
        ).resolve(),
    )
    selector_rows = [
        row for row in selector_rows if row["is_first_trigger"]
    ]
    fold_count = max(2, int(args.fold_count))
    instance_hashes = sorted(
        {row["instance_content_hash"] for row in dense_rows}
    )
    instance_folds = {
        instance_hash: dense_module._fold(
            instance_hash,
            fold_count,
        )
        for instance_hash in instance_hashes
    }
    if not {
        row["instance_content_hash"] for row in selector_rows
    }.issubset(instance_folds):
        raise SystemExit(
            "selector instances are missing dense pretraining rows"
        )

    import torch

    from lunar_ice_bpc.guidance.proof_tail_veto_model import (
        PROOF_TAIL_VETO_MODEL_LADDER,
        ProofTailVetoModel,
        harvest_dynamics_loss,
        proof_tail_veto_loss,
    )

    torch.set_num_threads(1)
    dense_tensors = {
        row["state_hash"]: dense_module._tensor(row, torch)
        for row in dense_rows
    }
    models = []
    for kind in PROOF_TAIL_VETO_MODEL_LADDER:
        folds = []
        predictions = []
        for fold in range(fold_count):
            heldout_hashes = {
                instance_hash
                for instance_hash, assigned in instance_folds.items()
                if assigned == fold
            }
            if not heldout_hashes:
                continue
            dense_train = [
                row
                for row in dense_rows
                if row["instance_content_hash"]
                not in heldout_hashes
            ]
            selector_train = [
                row
                for row in selector_rows
                if row["instance_content_hash"]
                not in heldout_hashes
            ]
            selector_heldout = [
                row
                for row in selector_rows
                if row["instance_content_hash"] in heldout_hashes
            ]
            dense_result, pretrained = dense_module._train_fold(
                kind=kind,
                train_rows=dense_train,
                heldout_rows=[],
                heldout_action_rows=[],
                tensors=dense_tensors,
                epochs=int(args.pretrain_epochs),
                seed=int(args.seed) + fold,
                torch=torch,
                ProofTailVetoModel=ProofTailVetoModel,
                harvest_dynamics_loss=harvest_dynamics_loss,
            )
            selector_result, _ = selector_module._train_one(
                kind=kind,
                train_rows=selector_train,
                heldout_rows=selector_heldout,
                epochs=int(args.selector_epochs),
                seed=int(args.seed) + fold,
                torch=torch,
                ProofTailVetoModel=ProofTailVetoModel,
                proof_tail_veto_loss=proof_tail_veto_loss,
                initial_model=pretrained,
                freeze_pretrained_encoder=True,
            )
            selector_result["fold"] = fold
            selector_result["heldout_instance_hashes"] = sorted(
                heldout_hashes
            )
            selector_result["dense_pretraining"] = {
                key: dense_result[key]
                for key in (
                    "train_instance_count",
                    "train_row_count",
                    "train_wall_sec",
                    "final_losses",
                )
            }
            folds.append(selector_result)
            predictions.extend(
                selector_result["heldout_predictions"]
            )
        models.append(
            {
                "kind": kind,
                "folds": folds,
                "metrics": selector_module._metrics(
                    predictions,
                    minimum_call_cost_sec=float(
                        args.minimum_call_cost_sec
                    ),
                ),
            }
        )
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "training_authorized": False,
        "promotion_authorized": False,
        "harvest_dynamics_rows": str(
            (ROOT / args.harvest_dynamics_rows).resolve()
        ),
        "all_state_labels": str(
            (ROOT / args.all_state_labels).resolve()
        ),
        "first_trigger_labels": str(
            (ROOT / args.first_trigger_labels).resolve()
        ),
        "dense_row_count": len(dense_rows),
        "dense_instance_count": len(instance_hashes),
        "selector_first_trigger_count": len(selector_rows),
        "excluded_non_call_state_count": len(excluded),
        "fold_count": fold_count,
        "instance_folds": instance_folds,
        "pretrain_epochs": int(args.pretrain_epochs),
        "selector_epochs": int(args.selector_epochs),
        "seed": int(args.seed),
        "minimum_call_cost_sec": float(
            args.minimum_call_cost_sec
        ),
        "encoder_policy": (
            "dense_pretrain_then_freeze_for_selector"
        ),
        "models": models,
        "selection_status": "TRANSFER_PILOT_ONLY_NO_MODEL_PROMOTED",
        "torch_version": str(torch.__version__),
    }
    payload["artifact_hash"] = _hash(payload)
    output = (ROOT / args.output).resolve()
    _write(output, payload)
    print(
        json.dumps(
            {
                "dense_row_count": payload["dense_row_count"],
                "selector_first_trigger_count": payload[
                    "selector_first_trigger_count"
                ],
                "models": [
                    {"kind": row["kind"], **row["metrics"]}
                    for row in models
                ],
                "selection_status": payload["selection_status"],
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
