#!/usr/bin/env python3
"""Evaluate the frozen proof-tail transfer ladder on fresh action labels."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SCHEMA = "lunar_ice_bpc.p0v3_proof_tail_transfer_heldout.v1"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _verify_protocol(protocol: dict) -> None:
    code = dict(protocol["frozen_code"])
    expected = {
        "src/lunar_ice_bpc/guidance/proof_tail_veto_features.py": (
            code["feature_file_sha256"]
        ),
        "src/lunar_ice_bpc/guidance/proof_tail_veto_model.py": (
            code["model_file_sha256"]
        ),
        "scripts/train_p0v3_harvest_dynamics_ladder.py": (
            code["dense_pretrainer_sha256"]
        ),
        "scripts/train_p0v3_proof_tail_veto_ladder.py": (
            code["selector_trainer_sha256"]
        ),
        "scripts/train_p0v3_proof_tail_transfer_ladder.py": (
            code["transfer_trainer_sha256"]
        ),
    }
    mismatches = {
        path: {"expected": digest, "observed": _sha256(ROOT / path)}
        for path, digest in expected.items()
        if _sha256(ROOT / path) != digest
    }
    if mismatches:
        raise SystemExit(
            f"frozen heldout protocol code mismatch: {mismatches}"
        )
    for item in protocol["frozen_training_inputs"].values():
        path = ROOT / item["path"]
        if _sha256(path) != item["sha256"]:
            raise SystemExit(
                f"frozen training input mismatch: {path}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--heldout-labels", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    protocol_path = (ROOT / args.protocol).resolve()
    protocol = _load(protocol_path)
    _verify_protocol(protocol)
    training = dict(protocol["training_protocol"])
    inputs = dict(protocol["frozen_training_inputs"])
    dense_module = _module(
        "p0v3_heldout_dense_train",
        "scripts/train_p0v3_harvest_dynamics_ladder.py",
    )
    selector_module = _module(
        "p0v3_heldout_selector_train",
        "scripts/train_p0v3_proof_tail_veto_ladder.py",
    )
    dense_rows = dense_module._examples(
        ROOT / inputs["harvest_dynamics_rows"]["path"]
    )
    train_selector_rows, _ = selector_module._examples(
        all_state_labels=(
            ROOT / inputs["all_state_labels"]["path"]
        ),
        first_trigger_labels=(
            ROOT / inputs["first_trigger_labels"]["path"]
        ),
    )
    train_selector_rows = [
        row
        for row in train_selector_rows
        if row["is_first_trigger"]
    ]
    heldout_path = (ROOT / args.heldout_labels).resolve()
    heldout_rows, heldout_excluded = selector_module._examples(
        all_state_labels=heldout_path,
        first_trigger_labels=heldout_path,
    )
    heldout_rows = [
        row for row in heldout_rows if row["is_first_trigger"]
    ]

    import torch

    from lunar_ice_bpc.guidance.proof_tail_veto_model import (
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
    for kind in training["model_ladder"]:
        dense_result, pretrained = dense_module._train_fold(
            kind=kind,
            train_rows=dense_rows,
            heldout_rows=[],
            heldout_action_rows=[],
            tensors=dense_tensors,
            epochs=int(training["dense_pretrain_epochs"]),
            seed=int(training["seed"]),
            torch=torch,
            ProofTailVetoModel=ProofTailVetoModel,
            harvest_dynamics_loss=harvest_dynamics_loss,
        )
        selector_result, _ = selector_module._train_one(
            kind=kind,
            train_rows=train_selector_rows,
            heldout_rows=heldout_rows,
            epochs=int(training["selector_epochs"]),
            seed=int(training["seed"]),
            torch=torch,
            ProofTailVetoModel=ProofTailVetoModel,
            proof_tail_veto_loss=proof_tail_veto_loss,
            initial_model=pretrained,
            freeze_pretrained_encoder=bool(
                training["encoder_frozen_during_selector_training"]
            ),
        )
        metrics = selector_module._metrics(
            selector_result["heldout_predictions"],
            minimum_call_cost_sec=float(
                training["minimum_full_call_cost_sec"]
            ),
        )
        models.append(
            {
                "kind": kind,
                "dense_pretraining": {
                    key: dense_result[key]
                    for key in (
                        "train_instance_count",
                        "train_row_count",
                        "train_wall_sec",
                        "final_losses",
                    )
                },
                "selector_training": {
                    key: selector_result[key]
                    for key in (
                        "train_instance_count",
                        "train_state_count",
                        "train_wall_sec",
                        "final_losses",
                        "veto_probability_threshold",
                        "trainable_parameter_count",
                        "pretrained_encoder_frozen",
                    )
                },
                "heldout_predictions": selector_result[
                    "heldout_predictions"
                ],
                "metrics": metrics,
            }
        )
    by_kind = {row["kind"]: row for row in models}
    gat = by_kind["gat1x32x1"]["metrics"]
    smaller_net = max(
        by_kind[kind]["metrics"]["realized_net_gain_sec"]
        for kind in ("linear", "mlp2x32")
    )
    gate = dict(protocol["heldout_decision_rule"])
    criteria = {
        "false_veto_count": (
            gat["false_veto_count"]
            == int(gate["false_veto_count_must_equal"])
        ),
        "positive_net_gain": (
            gat["realized_net_gain_sec"]
            > float(
                gate[
                    "realized_net_gain_sec_must_be_greater_than"
                ]
            )
        ),
        "outperforms_smaller_models": (
            gat["realized_net_gain_sec"] > smaller_net
        ),
    }
    payload = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "promotion_authorized": False,
        "protocol_path": str(protocol_path),
        "protocol_sha256": _sha256(protocol_path),
        "protocol_verified_before_training": True,
        "heldout_labels_path": str(heldout_path),
        "heldout_labels_sha256": _sha256(heldout_path),
        "heldout_label_count": len(heldout_rows),
        "heldout_excluded_non_call_state_count": len(
            heldout_excluded
        ),
        "heldout_used_for_training": False,
        "heldout_used_for_threshold_selection": False,
        "calibration_content_read": False,
        "models": models,
        "gat_gate_criteria": criteria,
        "gat_gate_passed": all(criteria.values()),
        "decision": (
            "PROOF_TAIL_GAT_HELDOUT_GATE_PASSED"
            if all(criteria.values())
            else "PROOF_TAIL_GAT_HELDOUT_GATE_FAILED"
        ),
    }
    payload["artifact_hash"] = _hash(payload)
    output = (ROOT / args.output).resolve()
    _write(output, payload)
    print(
        json.dumps(
            {
                "models": [
                    {"kind": row["kind"], **row["metrics"]}
                    for row in models
                ],
                "gat_gate_criteria": criteria,
                "gat_gate_passed": payload["gat_gate_passed"],
                "decision": payload["decision"],
                "output": str(output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
