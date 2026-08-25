#!/usr/bin/env python3
"""Feature and message-passing diagnostics for the frozen QG2 V3 GAT."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCHEMA = "lunar_ice_bpc.p0v5_qg2_v3_gat_attribution.v1"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-report", required=True)
    parser.add_argument("--oracle-summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--maximum-pairs-per-context", type=int, default=512)
    parser.add_argument(
        "--partitions", nargs="+", default=("calibration",),
        choices=("train", "calibration", "heldout"),
    )
    args = parser.parse_args()

    import torch
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat import (
        QG2_CONTEXT_FEATURES,
        QG2_NODE_DYNAMIC_FEATURES,
    )
    from lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 import (
        load_qg2_v3_checkpoint,
    )
    from lunar_ice_bpc.guidance.tensorization import (
        EDGE_STATIC_FEATURES,
        NODE_STATIC_FEATURES,
    )

    training_path = _resolve(args.training_report)
    training = _load(training_path)
    oracle = _load(_resolve(args.oracle_summary))
    gat = next(
        dict(row) for row in training.get("models") or ()
        if str(row.get("model_kind") or "") == "gat"
    )
    model, metadata, normalization = load_qg2_v3_checkpoint(
        str(_resolve(gat["checkpoint_path"]))
    )
    if bool(metadata.get("activation_authority")):
        raise SystemExit("attribution checkpoint unexpectedly owns activation")
    loader = _load_training_helpers()
    examples = loader._load_examples(oracle, seed=20260806)
    split = _load(_resolve(training["split_path"]))["assignments"]
    allowed = {str(value) for value in args.partitions}
    validation = [
        row for row in examples
        if split[row["instance_hash"]] in allowed
    ]
    maximum = max(1, int(args.maximum_pairs_per_context))
    baseline = _accuracy(model, validation, maximum=maximum)
    group_rows = []
    for name, transform in (
        ("node_to_train_mean", _to_train_mean("node", normalization)),
        ("edge_to_train_mean", _to_train_mean("edge", normalization)),
        ("context_to_train_mean", _to_train_mean("context", normalization)),
        ("no_message_passing", lambda tensors: {**tensors, "disable_message_passing": True}),
        ("shuffled_message_topology", _shuffle_message_topology),
    ):
        accuracy = _accuracy(
            model, validation, maximum=maximum, transform=transform
        )
        group_rows.append({
            "ablation": name,
            "weighted_pair_accuracy": accuracy,
            "accuracy_drop": baseline - accuracy,
        })

    feature_rows = []
    groups = (
        ("node", (*NODE_STATIC_FEATURES, *QG2_NODE_DYNAMIC_FEATURES)),
        ("edge", tuple(EDGE_STATIC_FEATURES)),
        ("context", tuple(QG2_CONTEXT_FEATURES)),
    )
    for group, names in groups:
        means = list(dict(normalization[group])["mean"])
        for index, feature_name in enumerate(names):
            accuracy = _accuracy(
                model,
                validation,
                maximum=maximum,
                transform=_single_feature_to_mean(
                    group, index, float(means[index])
                ),
            )
            feature_rows.append({
                "group": group,
                "feature": str(feature_name),
                "weighted_pair_accuracy": accuracy,
                "accuracy_drop": baseline - accuracy,
            })
    feature_rows.sort(key=lambda row: (-row["accuracy_drop"], row["group"], row["feature"]))
    report = {
        "schema_version": SCHEMA,
        "development_only": True,
        "deployable": False,
        "checkpoint_path": str(_resolve(gat["checkpoint_path"])),
        "training_data_hash": str(training.get("training_data_hash") or ""),
        "partitions": sorted(allowed),
        "context_count": len(validation),
        "maximum_pairs_per_context": maximum,
        "baseline_weighted_pair_accuracy": baseline,
        "group_ablations": group_rows,
        "single_feature_ablations": feature_rows,
        "top_positive_contributors": [
            row for row in feature_rows if row["accuracy_drop"] > 0.0
        ][:15],
        "interpretation_boundary": (
            "pair-ranking diagnostic only; fresh-process admission/proof wall "
            "remains the performance authority"
        ),
    }
    _write(_resolve(args.output), report)
    print(json.dumps({
        "baseline": baseline,
        "group_ablations": group_rows,
        "top_features": report["top_positive_contributors"][:8],
    }, sort_keys=True))
    return 0


def _load_training_helpers():
    path = ROOT / "scripts/train_p0v5_qg2_v3_rankers.py"
    spec = importlib.util.spec_from_file_location("qg2_v3_training_helpers", path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError("cannot load QG2 V3 training helpers")
    spec.loader.exec_module(module)
    return module


def _accuracy(model, examples, *, maximum, transform=None):
    import torch

    helper = _load_training_helpers()
    correct = 0.0
    total = 0.0
    model.eval()
    with torch.inference_mode():
        for example in examples:
            tensors = example["features"].to_tensors()
            if transform is not None:
                tensors = transform(tensors)
            output = model(**tensors)
            pairs, weights = helper._systematic_weighted_sample(
                example["pairs"], maximum=maximum,
                rng=random.Random(20260806),
            )
            score_cache = {}
            arc_cache = {}
            for row, weight in zip(pairs, weights, strict=True):
                margin = float(
                    helper._label_score(
                        output, example, row.preferred_label_id,
                        score_cache=score_cache, arc_cache=arc_cache,
                    )
                    - helper._label_score(
                        output, example, row.other_label_id,
                        score_cache=score_cache, arc_cache=arc_cache,
                    )
                )
                correct += (1.0 if margin > 0.0 else 0.0) * weight
                total += weight
    return correct / max(1.0e-12, total)


def _to_train_mean(group, normalization):
    means = list(dict(normalization[group])["mean"])
    key = f"{group}_features"
    if group == "context":
        key = "context_features"
    def transform(tensors):
        import torch
        result = dict(tensors)
        replacement = torch.tensor(means, dtype=result[key].dtype)
        result[key] = (
            replacement if result[key].ndim == 1
            else replacement.expand_as(result[key]).clone()
        )
        return result
    return transform


def _single_feature_to_mean(group, index, mean):
    key = f"{group}_features"
    if group == "context":
        key = "context_features"
    def transform(tensors):
        result = dict(tensors)
        values = result[key].clone()
        if values.ndim == 1:
            values[index] = mean
        else:
            values[:, index] = mean
        result[key] = values
        return result
    return transform


def _shuffle_message_topology(tensors):
    import torch
    result = dict(tensors)
    edge_index = result["edge_index"]
    if int(edge_index.shape[1]) > 1:
        result["message_edge_index"] = torch.stack(
            (edge_index[0], torch.roll(edge_index[1], shifts=1)), dim=0
        )
    return result


def _resolve(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
