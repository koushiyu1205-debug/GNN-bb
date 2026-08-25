#!/usr/bin/env python3
"""Run the frozen QG2 ranker trainer with instance-balanced authority.

The V4 real-map Oracle is intentionally left untouched.  This wrapper loads
the frozen trainer as a library and replaces only sampling, normalization, and
calibration aggregation.  Checkpoint/runtime schemas remain compatible, while
the report records the stronger experimental-unit contract.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random as _stdlib_random
import statistics
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.guidance.instance_balanced_learning import (  # noqa: E402
    INSTANCE_BALANCING_POLICY_V1,
    instance_balanced_epoch_order,
    instance_balanced_metric,
)


SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_ranker_wrapper.v1"
FROZEN_TRAINER = ROOT / "scripts/train_p0v5_qg2_v3_rankers.py"
_EXAMPLES: list[dict] = []
_FIT_SEED = 20260807
_LAST_CALIBRATION_METRICS: dict[str, object] = {}


def main() -> int:
    trainer = _load_frozen_trainer()
    original_load_examples = trainer._load_examples
    original_evaluate = trainer._evaluate
    original_metadata = trainer._checkpoint_metadata
    original_append = trainer._append_jsonl

    def load_examples(oracle, *, seed):
        rows = original_load_examples(oracle, seed=seed)
        _EXAMPLES.clear()
        _EXAMPLES.extend(rows)
        return rows

    def evaluate(model, examples, *, maximum):
        result = _instance_balanced_evaluate(
            trainer,
            model,
            examples,
            maximum=maximum,
            original_evaluate=original_evaluate,
        )
        _LAST_CALIBRATION_METRICS.clear()
        _LAST_CALIBRATION_METRICS.update(result)
        return result

    def checkpoint_metadata(**kwargs):
        return {
            **original_metadata(**kwargs),
            "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
            "optimizer_sampling_unit": "instance",
            "calibration_aggregation_unit": "instance",
        }

    trainer._load_examples = load_examples
    trainer._evaluate = evaluate
    trainer._checkpoint_metadata = checkpoint_metadata
    trainer._append_jsonl = lambda path, payload: original_append(
        path, _ranker_curve_row(payload)
    )
    trainer.random = SimpleNamespace(
        Random=_InstanceBalancedRandom,
        seed=_stdlib_random.seed,
    )

    import lunar_ice_bpc.guidance.proof_queue_label_state_gat_v3 as models

    original_fit = models.fit_qg2_v3_normalization

    def balanced_fit(features):
        by_identity = {id(row["features"]): row for row in _EXAMPLES}
        source = []
        for value in features:
            row = by_identity.get(id(value))
            if row is None:
                raise ValueError(
                    "instance-balanced normalization lost example identity"
                )
            source.append(row)
        balanced = instance_balanced_epoch_order(
            source,
            instance_key=lambda row: str(row["instance_hash"]),
            context_key=lambda row: str(row["state_hash"]),
            seed=_FIT_SEED,
            epoch=0,
            steps=len(source),
        )
        return original_fit([row["features"] for row in balanced])

    models.fit_qg2_v3_normalization = balanced_fit
    returncode = int(trainer.main())
    if returncode == 0:
        _postprocess_report(_argument_path("--output-dir"))
    return returncode


def _ranker_curve_row(payload: dict) -> dict:
    row = dict(payload)
    legacy = row.get("calibration_mean_context_pair_accuracy")
    if legacy is not None:
        row.update({
            "calibration_metric_unit": "instance",
            "calibration_mean_instance_pair_accuracy": legacy,
            "calibration_raw_mean_context_pair_accuracy": (
                _LAST_CALIBRATION_METRICS.get(
                    "raw_mean_context_pair_accuracy"
                )
            ),
            "legacy_calibration_mean_context_key_is_instance_balanced": True,
        })
    return row


class _InstanceBalancedRandom(_stdlib_random.Random):
    def __init__(self, seed=None):
        super().__init__(seed)
        self._qg2_seed = 0 if seed is None else int(seed)

    def shuffle(self, values) -> None:
        if values and all(
            isinstance(row, dict)
            and row.get("instance_hash")
            and row.get("state_hash")
            for row in values
        ):
            values[:] = instance_balanced_epoch_order(
                values,
                instance_key=lambda row: str(row["instance_hash"]),
                context_key=lambda row: str(row["state_hash"]),
                seed=self._qg2_seed,
                epoch=1,
                steps=len(values),
            )
            return
        super().shuffle(values)


def _instance_balanced_evaluate(
    trainer, model, examples, *, maximum, original_evaluate,
):
    import torch

    if not examples:
        return {
            **original_evaluate(model, examples, maximum=maximum),
            "raw_mean_context_pair_accuracy": None,
            "mean_instance_pair_accuracy": None,
            "maximum_context_fraction_by_instance": None,
        }
    context_rows = []
    weighted_correct = 0.0
    total_weight = 0.0
    by_kind: dict[str, list[float]] = {}
    model.eval()
    with torch.inference_mode():
        for example in examples:
            output = model(**example["features"].to_tensors())
            pairs, weights = trainer._systematic_weighted_sample(
                example["pairs"], maximum=maximum,
                rng=_stdlib_random.Random(20260806),
            )
            score_cache = {}
            arc_cache = {}
            local_correct = 0.0
            local_total = 0.0
            for row, weight in zip(pairs, weights, strict=True):
                margin = float(
                    trainer._label_score(
                        output, example, row.preferred_label_id,
                        score_cache=score_cache, arc_cache=arc_cache,
                    )
                    - trainer._label_score(
                        output, example, row.other_label_id,
                        score_cache=score_cache, arc_cache=arc_cache,
                    )
                )
                correct = 1.0 if margin > 0.0 else 0.0
                local_correct += correct * weight
                local_total += weight
                by_kind.setdefault(row.kind, [0.0, 0.0])
                by_kind[row.kind][0] += correct * weight
                by_kind[row.kind][1] += weight
            accuracy = local_correct / max(1.0e-12, local_total)
            context_rows.append({
                "instance_hash": str(example["instance_hash"]),
                "state_hash": str(example["state_hash"]),
                "accuracy": accuracy,
                "milestone_kind": str(example.get("milestone_kind") or ""),
            })
            weighted_correct += local_correct
            total_weight += local_total
    metric = instance_balanced_metric(context_rows, value_key="accuracy")
    by_milestone = {}
    for milestone in sorted({row["milestone_kind"] for row in context_rows}):
        subset = [
            row for row in context_rows if row["milestone_kind"] == milestone
        ]
        by_milestone[milestone] = instance_balanced_metric(
            subset, value_key="accuracy"
        )
    return {
        "context_count": len(context_rows),
        "instance_count": int(metric["instance_count"]),
        # Preserve the legacy key used by the frozen early-stopping loop, but
        # bind it to the experimental unit rather than context multiplicity.
        "mean_context_pair_accuracy": float(metric["mean_instance_value"]),
        "raw_mean_context_pair_accuracy": float(
            metric["mean_context_value"]
        ),
        "mean_instance_pair_accuracy": float(metric["mean_instance_value"]),
        "maximum_context_fraction_by_instance": float(
            metric["maximum_context_fraction_by_instance"]
        ),
        "per_instance_mean_context_pair_accuracy": dict(
            metric["per_instance_mean"]
        ),
        "per_instance_context_count": dict(
            metric["per_instance_context_count"]
        ),
        "per_milestone_instance_balanced_accuracy": by_milestone,
        "weighted_pair_accuracy": weighted_correct / max(
            1.0e-12, total_weight
        ),
        "per_kind_weighted_pair_accuracy": {
            kind: values[0] / max(1.0e-12, values[1])
            for kind, values in sorted(by_kind.items())
        },
    }


def _postprocess_report(output_dir: Path) -> None:
    path = output_dir / "training_report.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    for row in payload.get("models") or ():
        row["checkpoint_selection_metric"] = "mean_instance_pair_accuracy"
        row["instance_balancing_policy"] = INSTANCE_BALANCING_POLICY_V1
    split_path = Path(payload["split_path"])
    split = json.loads(split_path.read_text(encoding="utf-8"))["assignments"]
    partition_balance = {}
    for partition in ("train", "calibration", "heldout"):
        rows = [
            {
                "instance_hash": str(row["instance_hash"]),
                "unit": 1.0,
            }
            for row in _EXAMPLES
            if str(split[str(row["instance_hash"])]) == partition
        ]
        partition_balance[partition] = instance_balanced_metric(
            rows, value_key="unit"
        )
    payload.update({
        "instance_balanced_wrapper_schema_version": SCHEMA,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "normalization_sampling_unit": "instance",
        "optimizer_sampling_unit": "instance",
        "calibration_aggregation_unit": "instance",
        "checkpoint_selection_metric": "mean_instance_pair_accuracy",
        "partition_instance_balance": partition_balance,
    })
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_frozen_trainer():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_v4_frozen_ranker_trainer", FROZEN_TRAINER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen QG2 ranker trainer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _argument_path(name: str) -> Path:
    try:
        value = sys.argv[sys.argv.index(name) + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit(f"missing required wrapper argument {name}") from exc
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
