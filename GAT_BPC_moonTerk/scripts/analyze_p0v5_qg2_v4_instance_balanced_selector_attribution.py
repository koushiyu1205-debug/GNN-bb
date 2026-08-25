#!/usr/bin/env python3
"""Run frozen Context-GAT attribution at the instance experimental unit."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
    instance_balanced_metric,
)


FROZEN = ROOT / "scripts/analyze_p0v5_qg2_v3_selector_attribution.py"
BALANCED_TRAINER = (
    ROOT / "scripts/train_p0v5_qg2_v4_instance_balanced_arm_selector.py"
)
SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_selector_attribution.v1"


def main() -> int:
    module = _load_module("qg2_v4_frozen_selector_attribution", FROZEN)
    report = _load(_argument_path("--selector-training-report"))
    if str(report.get("instance_balancing_policy") or "") != (
        INSTANCE_BALANCING_POLICY_V1
    ):
        raise SystemExit("Context-GAT attribution lacks instance authority")
    original_helpers = module._training_helpers
    balanced = _load_module(
        "qg2_v4_selector_attribution_balanced_helpers", BALANCED_TRAINER
    )

    def helpers():
        trainer = original_helpers()
        trainer._classification_metrics = lambda rows, **kwargs: (
            balanced._instance_balanced_classification(
                trainer, rows, **kwargs
            )
        )
        trainer._arm_rank_metrics = lambda rows, **kwargs: (
            balanced._instance_balanced_arm_rank(trainer, rows, **kwargs)
        )
        trainer._evaluate_policy = lambda rows, thresholds: (
            balanced._instance_balanced_policy(trainer, rows, thresholds)
        )
        return trainer

    module._training_helpers = helpers
    module._metrics = _instance_balanced_metrics
    module._ablation_row = _instance_balanced_ablation_row
    returncode = int(module.main())
    if returncode == 0:
        _postprocess(_argument_path("--output"))
    return returncode


def _instance_balanced_metrics(helper, rows, thresholds):
    active_arms = tuple(
        arm for arm in ("QG2", "QD1", "QB1")
        if arm not in set(thresholds.get("forced_veto_arms") or ())
        and all(row["arms"][arm]["outcome"] is not None for row in rows)
    )
    classification = helper._classification_metrics(
        rows, trainable_arms=active_arms
    )
    arm_rank = helper._arm_rank_metrics(
        rows, trainable_arms=active_arms
    )
    policy = helper._evaluate_policy(rows, thresholds)
    actions = [helper._selected_arm(row, thresholds) for row in rows]
    instance_values = [
        float(value)
        for arm in active_arms
        for value in (
            classification[arm]["instance_balanced_benefit_accuracy"],
            classification[arm]["instance_balanced_adverse_accuracy"],
        )
        if value is not None
    ]
    raw_values = [
        float(value)
        for arm in active_arms
        for value in (
            classification[arm]["benefit_accuracy"],
            classification[arm]["adverse_accuracy"],
        )
        if value is not None
    ]
    instance_rank = arm_rank.get("mean_instance_pair_accuracy")
    raw_rank = arm_rank.get("mean_context_pair_accuracy")
    return {
        "mean_classification_accuracy": (
            sum(instance_values) / max(1, len(instance_values))
        ),
        "raw_context_classification_accuracy": (
            sum(raw_values) / max(1, len(raw_values))
        ),
        "mean_context_arm_rank_accuracy": float(
            0.0 if instance_rank is None else instance_rank
        ),
        "mean_instance_arm_rank_accuracy": float(
            0.0 if instance_rank is None else instance_rank
        ),
        "raw_context_arm_rank_accuracy": float(
            0.0 if raw_rank is None else raw_rank
        ),
        "net_geomean_ratio": float(policy["net_geomean_ratio"]),
        "raw_context_net_geomean_ratio": float(
            policy["context_weighted_net_geomean_ratio"]
        ),
        "activated_count": int(policy["activated_count"]),
        "activated_instance_count": int(policy["activated_instance_count"]),
        "harmful_count": int(policy["harmful_count"]),
        "harmful_instance_count": int(policy["harmful_instance_count"]),
        "actions": actions,
        "instance_hashes": [str(row["instance_hash"]) for row in rows],
    }


def _instance_balanced_ablation_row(name, metrics, baseline):
    changes = [
        {
            "instance_hash": instance,
            "changed": float(left != right),
        }
        for instance, left, right in zip(
            metrics["instance_hashes"], metrics["actions"],
            baseline["actions"], strict=True,
        )
    ]
    disagreement = instance_balanced_metric(changes, value_key="changed")
    return {
        "ablation": name,
        "mean_classification_accuracy": metrics[
            "mean_classification_accuracy"
        ],
        "raw_context_classification_accuracy": metrics[
            "raw_context_classification_accuracy"
        ],
        "mean_context_arm_rank_accuracy": metrics[
            "mean_instance_arm_rank_accuracy"
        ],
        "mean_instance_arm_rank_accuracy": metrics[
            "mean_instance_arm_rank_accuracy"
        ],
        "raw_context_arm_rank_accuracy": metrics[
            "raw_context_arm_rank_accuracy"
        ],
        "arm_rank_accuracy_drop": (
            baseline["mean_instance_arm_rank_accuracy"]
            - metrics["mean_instance_arm_rank_accuracy"]
        ),
        "raw_context_arm_rank_accuracy_drop": (
            baseline["raw_context_arm_rank_accuracy"]
            - metrics["raw_context_arm_rank_accuracy"]
        ),
        "classification_accuracy_drop": (
            baseline["mean_classification_accuracy"]
            - metrics["mean_classification_accuracy"]
        ),
        "raw_context_classification_accuracy_drop": (
            baseline["raw_context_classification_accuracy"]
            - metrics["raw_context_classification_accuracy"]
        ),
        "selected_action_disagreement_rate": float(
            disagreement["mean_instance_value"]
        ),
        "raw_context_selected_action_disagreement_rate": float(
            disagreement["mean_context_value"]
        ),
        "net_geomean_ratio": metrics["net_geomean_ratio"],
        "raw_context_net_geomean_ratio": metrics[
            "raw_context_net_geomean_ratio"
        ],
        "activated_count": metrics["activated_count"],
        "activated_instance_count": metrics["activated_instance_count"],
        "harmful_count": metrics["harmful_count"],
        "harmful_instance_count": metrics["harmful_instance_count"],
    }


def _postprocess(path: Path) -> None:
    payload = _load(path)
    baseline = dict(payload.get("baseline") or {})
    payload.update({
        "instance_balanced_wrapper_schema_version": SCHEMA,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "headline_metric_unit": "instance",
        "baseline": {
            **baseline,
            "mean_instance_arm_rank_accuracy": baseline.get(
                "mean_instance_arm_rank_accuracy"
            ),
        },
    })
    _write(path, payload)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load attribution module:{path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
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
