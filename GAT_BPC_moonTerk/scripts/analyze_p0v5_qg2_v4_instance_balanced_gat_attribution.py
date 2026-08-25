#!/usr/bin/env python3
"""Run frozen Label-GAT attribution with instance-balanced aggregation."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import random
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
    instance_balanced_metric,
)


FROZEN = ROOT / "scripts/analyze_p0v5_qg2_v3_gat_attribution.py"
SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_label_attribution.v1"
_CALLS: list[dict[str, object]] = []


def main() -> int:
    module = _load_frozen()
    training = _load(_argument_path("--training-report"))
    if str(training.get("instance_balancing_policy") or "") != (
        INSTANCE_BALANCING_POLICY_V1
    ):
        raise SystemExit("Label-GAT attribution lacks instance authority")
    _CALLS.clear()
    module._accuracy = _instance_balanced_accuracy
    returncode = int(module.main())
    if returncode == 0:
        _postprocess(_argument_path("--output"))
    return returncode


def _instance_balanced_accuracy(model, examples, *, maximum, transform=None):
    import torch

    helper = _load_training_helpers()
    context_rows = []
    with torch.inference_mode():
        model.eval()
        for example in examples:
            tensors = example["features"].to_tensors()
            if transform is not None:
                tensors = transform(tensors)
            output = model(**tensors)
            pairs, weights = helper._systematic_weighted_sample(
                example["pairs"], maximum=maximum,
                rng=random.Random(20260806),
            )
            correct = 0.0
            total = 0.0
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
                correct += (1.0 if margin > 0.0 else 0.0) * float(weight)
                total += float(weight)
            context_rows.append({
                "instance_hash": str(example["instance_hash"]),
                "accuracy": correct / max(1.0e-12, total),
            })
    metric = instance_balanced_metric(context_rows, value_key="accuracy")
    result = {
        "instance_balanced_accuracy": float(metric["mean_instance_value"]),
        "raw_context_accuracy": float(metric["mean_context_value"]),
        "context_count": int(metric["context_count"]),
        "instance_count": int(metric["instance_count"]),
        "maximum_context_fraction_by_instance": float(
            metric["maximum_context_fraction_by_instance"]
        ),
    }
    _CALLS.append(result)
    return result["instance_balanced_accuracy"]


def _postprocess(path: Path) -> None:
    payload = _load(path)
    group_rows = [dict(row) for row in payload.get("group_ablations") or ()]
    feature_rows = [
        dict(row) for row in payload.get("single_feature_ablations") or ()
    ]
    expected = 1 + len(group_rows) + len(feature_rows)
    if len(_CALLS) != expected:
        raise SystemExit("instance-balanced Label attribution call drift")
    baseline = dict(_CALLS[0])
    cursor = 1
    for row in group_rows:
        call = dict(_CALLS[cursor])
        cursor += 1
        row.update({
            "raw_context_weighted_pair_accuracy": call["raw_context_accuracy"],
            "raw_context_accuracy_drop": (
                baseline["raw_context_accuracy"] - call["raw_context_accuracy"]
            ),
            "instance_count": call["instance_count"],
        })
    for row in feature_rows:
        call = dict(_CALLS[cursor])
        cursor += 1
        row.update({
            "raw_context_weighted_pair_accuracy": call["raw_context_accuracy"],
            "raw_context_accuracy_drop": (
                baseline["raw_context_accuracy"] - call["raw_context_accuracy"]
            ),
            "instance_count": call["instance_count"],
        })
    feature_rows.sort(key=lambda row: (
        -float(row["accuracy_drop"]), str(row["group"]), str(row["feature"])
    ))
    positive = [
        row for row in feature_rows if float(row["accuracy_drop"]) > 0.0
    ]
    positive_drop_sum = sum(float(row["accuracy_drop"]) for row in positive)
    group_drop = {
        str(row["ablation"]).split("_to_train_mean")[0]: float(
            row["accuracy_drop"]
        )
        for row in group_rows
        if str(row.get("ablation") or "").endswith("_to_train_mean")
    }
    top = None if not positive else positive[0]
    dominance = {
        "candidate": None if top is None else {
            "group": str(top["group"]),
            "feature": str(top["feature"]),
            "instance_balanced_accuracy_drop": float(top["accuracy_drop"]),
            "share_of_all_positive_single_feature_drop": (
                float(top["accuracy_drop"]) / positive_drop_sum
                if positive_drop_sum > 0.0 else None
            ),
            "share_of_positive_group_accuracy_drop": (
                float(top["accuracy_drop"])
                / group_drop[str(top["group"])]
                if group_drop.get(str(top["group"]), 0.0) > 0.0 else None
            ),
        },
        "interpretation": (
            "large shares identify a feature-dominance candidate only; "
            "ablation drops are non-additive and fresh wall remains authority"
        ),
    }
    payload.update({
        "instance_balanced_wrapper_schema_version": SCHEMA,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "headline_accuracy_unit": "instance",
        "baseline_instance_balanced_pair_accuracy": payload.get(
            "baseline_weighted_pair_accuracy"
        ),
        "baseline_raw_context_pair_accuracy": baseline[
            "raw_context_accuracy"
        ],
        "instance_count": baseline["instance_count"],
        "maximum_context_fraction_by_instance": baseline[
            "maximum_context_fraction_by_instance"
        ],
        "group_ablations": group_rows,
        "single_feature_ablations": feature_rows,
        "top_positive_contributors": positive[:15],
        "single_feature_dominance_diagnostic": dominance,
    })
    _write(path, payload)


def _load_training_helpers():
    path = ROOT / "scripts/train_p0v5_qg2_v3_rankers.py"
    spec = importlib.util.spec_from_file_location(
        "qg2_v4_instance_attribution_training_helpers", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen Label-GAT training helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_frozen():
    spec = importlib.util.spec_from_file_location(
        "qg2_v4_frozen_label_attribution", FROZEN
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen Label-GAT attribution")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _argument_path(name: str) -> Path:
    try:
        raw = sys.argv[sys.argv.index(name) + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit(f"missing attribution argument {name}") from exc
    path = Path(raw)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


if __name__ == "__main__":
    raise SystemExit(main())
