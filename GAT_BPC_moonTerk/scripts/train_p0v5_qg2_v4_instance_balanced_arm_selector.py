#!/usr/bin/env python3
"""Train the frozen multi-arm selector with instance-balanced authority."""

from __future__ import annotations

from collections import defaultdict
import importlib.util
import json
import math
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
    instance_balanced_geomean,
    instance_balanced_metric,
)


SCHEMA = "lunar_ice_bpc.p0v5_qg2_v4_instance_balanced_selector_wrapper.v1"
FROZEN_TRAINER = ROOT / "scripts/train_p0v5_qg2_v3_gat_arm_selector.py"
_LAST_CALIBRATION_LOSS: dict[str, object] = {}


def main() -> int:
    trainer = _load_frozen_trainer()
    original_append = trainer._append_jsonl
    trainer.random = SimpleNamespace(
        Random=_InstanceBalancedRandom,
        seed=_stdlib_random.seed,
    )
    trainer._class_balance_weights = lambda rows, *, trainable_arms: (
        _instance_balanced_class_weights(
            trainer, rows, trainable_arms=trainable_arms
        )
    )
    trainer._qg2_screen = lambda records: _instance_balanced_qg2_screen(
        trainer, records
    )
    trainer._qg2_arm_is_trainable = _instance_balanced_qg2_arm_is_trainable
    def selector_loss(model, rows, **kwargs):
        result = _instance_balanced_selector_loss(
            trainer, model, rows, **kwargs
        )
        _LAST_CALIBRATION_LOSS.clear()
        _LAST_CALIBRATION_LOSS.update(result)
        return result

    trainer._mean_selector_loss = selector_loss
    trainer._evaluate_policy = lambda rows, thresholds: (
        _instance_balanced_policy(trainer, rows, thresholds)
    )
    trainer._threshold_selection_key = lambda metrics: (
        _instance_balanced_threshold_key(trainer, metrics)
    )
    trainer._choose_thresholds = lambda rows, **kwargs: (
        _instance_balanced_thresholds(trainer, rows, **kwargs)
    )
    trainer._classification_metrics = lambda rows, **kwargs: (
        _instance_balanced_classification(trainer, rows, **kwargs)
    )
    trainer._arm_rank_metrics = lambda rows, **kwargs: (
        _instance_balanced_arm_rank(trainer, rows, **kwargs)
    )
    trainer._instance_bootstrap_geomean = (
        _instance_balanced_bootstrap_geomean
    )
    trainer._append_jsonl = lambda path, payload: original_append(
        path, _selector_curve_row(payload)
    )
    returncode = int(trainer.main())
    if returncode == 0:
        _postprocess_report(_argument_path("--output-dir"))
    return returncode


def _instance_balanced_qg2_screen(trainer, records):
    def summarize(rows):
        available_rows = []
        for row in rows:
            outcome = trainer._force_outcome(row)
            if outcome is not None:
                available_rows.append((row, outcome))
        beneficial_rows = [
            (row, outcome) for row, outcome in available_rows
            if bool(outcome.beneficial)
        ]
        return {
            "record_count": len(rows),
            "safe_count": sum(bool(row.get("safe")) for row in rows),
            "available_outcome_count": len(available_rows),
            "available_instance_count": len({
                str(row.get("instance_hash") or "")
                for row, _outcome in available_rows
            }),
            "beneficial_count": len(beneficial_rows),
            "beneficial_instance_count": len({
                str(row.get("instance_hash") or "")
                for row, _outcome in beneficial_rows
            }),
            "harmful_count": sum(
                bool(outcome.harmful) for _row, outcome in available_rows
            ),
            "available_instance_count_by_scale": {
                str(scale): len({
                    str(row.get("instance_hash") or "")
                    for row, _outcome in available_rows
                    if int(row.get("scale") or 0) == scale
                })
                for scale in (30, 50)
            },
            "net_geomean_ratio": trainer._geomean([
                outcome.ratio for _row, outcome in available_rows
            ]),
        }

    partitions = {
        name: summarize([
            row for row in records.values()
            if str(row.get("partition") or "") == name
        ])
        for name in ("train", "calibration", "heldout")
    }
    return {
        "arm_enable_authority_partition": "train",
        "minimum_train_available_outcomes": 5,
        "minimum_train_available_instances": 5,
        "minimum_train_available_instances_per_scale": 2,
        "minimum_train_beneficial_outcomes": 2,
        "minimum_train_beneficial_instances": 2,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "partitions": partitions,
    }


def _instance_balanced_qg2_arm_is_trainable(screen) -> bool:
    train = dict(screen["partitions"]["train"])
    return bool(
        int(train.get("available_outcome_count") or 0)
        >= int(screen["minimum_train_available_outcomes"])
        and int(train.get("available_instance_count") or 0)
        >= int(screen["minimum_train_available_instances"])
        and all(
            int(dict(train.get("available_instance_count_by_scale") or {}).get(
                str(scale), 0
            )) >= int(screen["minimum_train_available_instances_per_scale"])
            for scale in (30, 50)
        )
        and int(train.get("beneficial_count") or 0)
        >= int(screen["minimum_train_beneficial_outcomes"])
        and int(train.get("beneficial_instance_count") or 0)
        >= int(screen["minimum_train_beneficial_instances"])
        and int(train.get("safe_count") or 0)
        == int(train.get("record_count") or 0)
    )


def _selector_curve_row(payload: dict) -> dict:
    row = dict(payload)
    if row.get("calibration_total_loss") is not None:
        row.update({
            "calibration_metric_unit": "instance",
            "calibration_instance_balanced_total_loss": row[
                "calibration_total_loss"
            ],
            "calibration_raw_context_total_loss": (
                _LAST_CALIBRATION_LOSS.get("raw_context_total_loss")
            ),
            "legacy_calibration_total_loss_key_is_instance_balanced": True,
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


def _instance_balanced_class_weights(trainer, rows, *, trainable_arms):
    result = {"benefit_positive_weight": [], "adverse_positive_weight": []}
    for arm in trainer.ARMS:
        for key, attribute in (
            ("benefit_positive_weight", "beneficial"),
            ("adverse_positive_weight", "harmful"),
        ):
            values = []
            for row in rows:
                outcome = row["outcomes"].get(arm)
                if arm in trainable_arms and outcome is not None:
                    values.append({
                        "instance_hash": str(row["instance_hash"]),
                        "positive": float(bool(getattr(outcome, attribute))),
                    })
            metric = instance_balanced_metric(values, value_key="positive")
            positive_mass = metric["mean_instance_value"]
            if positive_mass is None or positive_mass in {0.0, 1.0}:
                weight = 1.0
            else:
                weight = min(
                    4.0, max(0.25, (1.0 - positive_mass) / positive_mass)
                )
            result[key].append(weight)
    return result


def _instance_balanced_selector_loss(
    trainer, model, rows, *, trainable_arms, class_weights,
):
    import torch
    from lunar_ice_bpc.guidance.qg2_unified_arm_selector_v3 import (
        qg2_v3_selector_loss,
    )

    if not rows:
        raise ValueError("selector calibration partition is empty")
    values = []
    model.eval()
    with torch.inference_mode():
        for row in rows:
            component = {
                key: float(value)
                for key, value in qg2_v3_selector_loss(
                    predictions=model(**row["features"].to_tensors()),
                    **trainer._target_tensors(
                        row, trainable_arms=trainable_arms
                    ),
                    **trainer._class_weight_tensors(class_weights),
                ).items()
            }
            values.append({
                "instance_hash": str(row["instance_hash"]),
                **component,
            })
    result = {}
    for key in (
        "total_loss", "rank_loss", "benefit_loss",
        "positive_gain_loss", "adverse_loss",
    ):
        metric = instance_balanced_metric(values, value_key=key)
        result[key] = float(metric["mean_instance_value"])
        result[f"raw_context_{key}"] = float(metric["mean_context_value"])
    result["instance_count"] = int(
        instance_balanced_metric(values, value_key="total_loss")[
            "instance_count"
        ]
    )
    return result


def _instance_balanced_policy(trainer, rows, thresholds):
    actions = [trainer._selected_arm(row, thresholds) for row in rows]
    evaluated = []
    for row, arm in zip(rows, actions, strict=True):
        ratio = (
            1.0
            if arm == "Q0"
            else float(row["arms"][arm]["outcome"].ratio)
        )
        evaluated.append({
            "row": row,
            "arm": arm,
            "ratio": ratio,
            "instance_hash": str(row["instance_hash"]),
            "scale": int(row["scale"]),
        })
    activated = [row for row in evaluated if row["arm"] != "Q0"]
    overall = instance_balanced_geomean(evaluated, ratio_key="ratio")
    activated_instances = {row["instance_hash"] for row in activated}
    harmful_instances = {
        row["instance_hash"] for row in activated
        if bool(row["row"]["arms"][row["arm"]]["outcome"].harmful)
    }
    beneficial_instances = {
        row["instance_hash"] for row in activated
        if bool(row["row"]["arms"][row["arm"]]["outcome"].beneficial)
    }
    return {
        "context_count": len(rows),
        "instance_count": int(overall["instance_count"]),
        "activated_count": len(activated),
        "activated_instance_count": len(activated_instances),
        "q0_count": sum(arm == "Q0" for arm in actions),
        "qd1_count": sum(arm == "QD1" for arm in actions),
        "qb1_count": sum(arm == "QB1" for arm in actions),
        "harmful_count": sum(
            bool(row["row"]["arms"][row["arm"]]["outcome"].harmful)
            for row in activated
        ),
        "harmful_instance_count": len(harmful_instances),
        "beneficial_count": sum(
            bool(row["row"]["arms"][row["arm"]]["outcome"].beneficial)
            for row in activated
        ),
        "beneficial_instance_count": len(beneficial_instances),
        # Preserve the downstream key, now with the correct experimental unit.
        "net_geomean_ratio": float(
            overall["instance_balanced_geomean_ratio"]
        ),
        "context_weighted_net_geomean_ratio": float(
            overall["context_geomean_ratio"]
        ),
        "maximum_context_fraction_by_instance": float(
            overall["maximum_context_fraction_by_instance"]
        ),
        "per_instance_geomean_ratio": dict(
            overall["per_instance_geomean_ratio"]
        ),
        "per_scale": {
            str(scale): _scale_policy_summary(
                [row for row in evaluated if row["scale"] == scale]
            )
            for scale in (30, 50)
        },
    }


def _scale_policy_summary(rows):
    if not rows:
        return {
            "context_count": 0,
            "instance_count": 0,
            "activated_count": 0,
            "activated_instance_count": 0,
            "net_geomean_ratio": 1.0,
            "context_weighted_net_geomean_ratio": 1.0,
        }
    metric = instance_balanced_geomean(rows, ratio_key="ratio")
    activated = [row for row in rows if row["arm"] != "Q0"]
    return {
        "context_count": len(rows),
        "instance_count": int(metric["instance_count"]),
        "activated_count": len(activated),
        "activated_instance_count": len({
            row["instance_hash"] for row in activated
        }),
        "net_geomean_ratio": float(
            metric["instance_balanced_geomean_ratio"]
        ),
        "context_weighted_net_geomean_ratio": float(
            metric["context_geomean_ratio"]
        ),
    }


def _instance_balanced_threshold_key(trainer, metrics):
    activated = int(metrics.get("activated_count") or 0)
    activated_instances = int(metrics.get("activated_instance_count") or 0)
    harmful = int(metrics.get("harmful_count") or 0)
    harmful_instances = int(metrics.get("harmful_instance_count") or 0)
    beneficial = int(metrics.get("beneficial_count") or 0)
    harmful_interval = trainer._wilson_interval(harmful, activated)
    harmful_instance_interval = trainer._wilson_interval(
        harmful_instances, activated_instances
    )
    beneficial_interval = trainer._wilson_interval(beneficial, activated)
    uncertainty = {
        "harmful_rate_wilson_95": harmful_interval,
        "harmful_instance_rate_wilson_95": harmful_instance_interval,
        "beneficial_precision_wilson_95": beneficial_interval,
    }
    return (
        (
            int(harmful > 0),
            float(harmful_instance_interval["upper"]),
            float(harmful_interval["upper"]),
            -float(beneficial_interval["lower"]),
            float(metrics.get("net_geomean_ratio") or 1.0),
            -activated_instances,
            -activated,
        ),
        uncertainty,
    )


def _instance_balanced_thresholds(
    trainer, rows, *, trainable_arms=None,
):
    trainable_arms = (
        trainer.TRAINABLE_ARMS if trainable_arms is None else trainable_arms
    )
    values = [
        arm for row in rows for name, arm in row["arms"].items()
        if name in trainable_arms
    ]
    probabilities = trainer._candidate_grid(
        (row["benefit_probability"] for row in values), (0.5, 0.7, 0.8)
    )
    probabilities = [value for value in probabilities if value >= 0.5]
    gains = trainer._candidate_grid(
        (row["expected_gain"] for row in values), (0.0, 0.01, 0.03)
    )
    risks = trainer._candidate_grid(
        (row["adverse_probability"] for row in values), (0.1, 0.25, 0.5)
    )
    risks = [value for value in risks if value <= 0.5]
    best = None
    evaluated = 0
    feasible = 0
    for probability in probabilities:
        for gain in gains:
            for risk in risks:
                for penalty in (0.5, 1.0, 2.0):
                    evaluated += 1
                    thresholds = {
                        "minimum_benefit_probability": probability,
                        "minimum_expected_gain": gain,
                        "maximum_adverse_probability": risk,
                        "risk_penalty": penalty,
                        "forced_veto_arms": [
                            arm for arm in trainer.ARMS
                            if arm not in trainable_arms
                        ],
                    }
                    metrics = trainer._evaluate_policy(rows, thresholds)
                    if (
                        metrics["activated_count"] < 3
                        or metrics["activated_instance_count"] < 2
                        or any(
                            float(metrics["per_scale"][str(scale)][
                                "net_geomean_ratio"
                            ]) > 1.0
                            for scale in (30, 50)
                        )
                    ):
                        continue
                    feasible += 1
                    policy_key, uncertainty = trainer._threshold_selection_key(
                        metrics
                    )
                    candidate = (
                        *policy_key, probability, gain, risk, penalty,
                    )
                    if best is None or candidate < best[0]:
                        best = (candidate, thresholds, metrics, uncertainty)
    thresholds = best[1] if best is not None else {
        "minimum_benefit_probability": 1.0,
        "minimum_expected_gain": 0.0,
        "maximum_adverse_probability": 0.0,
        "risk_penalty": 1.0,
        "forced_veto_arms": list(trainer.ARMS),
    }
    return thresholds, {
        "candidate_count": evaluated,
        "feasible_candidate_count": feasible,
        "selected_noop_only": best is None,
        "selection_rule": (
            "zero_harm_then_instance_harm_upper_then_context_harm_upper_then_"
            "beneficial_lower_then_instance_balanced_gm_then_instance_coverage.v1"
        ),
        "selected_calibration_policy": None if best is None else best[2],
        "selected_calibration_uncertainty": None if best is None else best[3],
    }


def _instance_balanced_classification(
    trainer, rows, *, trainable_arms=None,
):
    trainable_arms = (
        trainer.TRAINABLE_ARMS if trainable_arms is None else trainable_arms
    )
    base = {}
    for arm in trainable_arms:
        benefit_pairs = []
        adverse_pairs = []
        benefit_correct = []
        adverse_correct = []
        for row in rows:
            prediction = row["arms"][arm]
            outcome = prediction["outcome"]
            actual_benefit = bool(outcome.beneficial)
            actual_adverse = bool(outcome.harmful)
            benefit_probability = float(prediction["benefit_probability"])
            adverse_probability = float(prediction["adverse_probability"])
            benefit_pairs.append((benefit_probability, actual_benefit))
            adverse_pairs.append((adverse_probability, actual_adverse))
            benefit_correct.append({
                "instance_hash": str(row["instance_hash"]),
                "correct": float(
                    (benefit_probability >= 0.5) == actual_benefit
                ),
            })
            adverse_correct.append({
                "instance_hash": str(row["instance_hash"]),
                "correct": float(
                    (adverse_probability >= 0.5) == actual_adverse
                ),
            })
        benefit = trainer._binary_metrics(benefit_pairs)
        adverse = trainer._binary_metrics(adverse_pairs)
        benefit_instance = instance_balanced_metric(
            benefit_correct, value_key="correct"
        )
        adverse_instance = instance_balanced_metric(
            adverse_correct, value_key="correct"
        )
        base[arm] = {
            "benefit_accuracy": benefit["accuracy"],
            "adverse_accuracy": adverse["accuracy"],
            "instance_balanced_benefit_accuracy": (
                benefit_instance["mean_instance_value"]
            ),
            "instance_balanced_adverse_accuracy": (
                adverse_instance["mean_instance_value"]
            ),
            "benefit": benefit,
            "adverse": adverse,
        }
    return base


def _instance_balanced_arm_rank(
    trainer, rows, *, trainable_arms=None,
):
    trainable_arms = (
        trainer.TRAINABLE_ARMS if trainable_arms is None else trainable_arms
    )
    correct = 0
    total = 0
    context_rows = []
    for row in rows:
        available = []
        for arm in trainable_arms:
            prediction = row["arms"][arm]
            outcome = prediction.get("outcome")
            if (
                outcome is None
                or not bool(outcome.milestone_matched)
                or bool(outcome.right_censored)
            ):
                continue
            predicted = float(prediction["expected_gain"]) - float(
                prediction["adverse_probability"]
            )
            observed = max(-1.0, min(1.0, 1.0 - float(outcome.ratio)))
            available.append((arm, predicted, observed))
        local_correct = 0
        local_total = 0
        for _arm, predicted, observed in available:
            if abs(observed) <= 1.0e-9:
                continue
            local_total += 1
            local_correct += int((predicted > 0.0) == (observed > 0.0))
        for index, (_left, left_pred, left_obs) in enumerate(available):
            for _right, right_pred, right_obs in available[index + 1:]:
                difference = left_obs - right_obs
                if abs(difference) <= 1.0e-9:
                    continue
                local_total += 1
                local_correct += int(
                    (left_pred > right_pred) == (difference > 0.0)
                )
        if local_total:
            context_rows.append({
                "instance_hash": str(row["instance_hash"]),
                "accuracy": local_correct / local_total,
            })
            correct += local_correct
            total += local_total
    metric = instance_balanced_metric(context_rows, value_key="accuracy")
    return {
        "context_count": len(context_rows),
        "instance_count": int(metric["instance_count"]),
        "pair_count": total,
        "pair_accuracy": None if total == 0 else correct / total,
        "mean_context_pair_accuracy": metric["mean_context_value"],
        "mean_instance_pair_accuracy": metric["mean_instance_value"],
        "maximum_context_fraction_by_instance": metric[
            "maximum_context_fraction_by_instance"
        ],
    }


def _instance_balanced_bootstrap_geomean(
    ratios_by_instance, *, seed, replicates,
):
    instances = sorted(ratios_by_instance)
    if not instances:
        return {"lower": 1.0, "median": 1.0, "upper": 1.0}
    per_instance = {
        key: math.exp(statistics.fmean(
            math.log(max(1.0e-12, float(value)))
            for value in ratios_by_instance[key]
        ))
        for key in instances
    }
    generator = _stdlib_random.Random(int(seed))
    values = []
    for _ in range(max(1, int(replicates))):
        sample = [
            per_instance[instances[generator.randrange(len(instances))]]
            for _ in instances
        ]
        values.append(math.exp(statistics.fmean(math.log(value) for value in sample)))
    values.sort()
    return {
        "lower": _quantile(values, 0.025),
        "median": _quantile(values, 0.5),
        "upper": _quantile(values, 0.975),
    }


def _quantile(values, probability):
    position = (len(values) - 1) * float(probability)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(values[lower])
    weight = position - lower
    return float(values[lower]) * (1.0 - weight) + float(values[upper]) * weight


def _postprocess_report(output_dir: Path) -> None:
    import torch

    path = output_dir / "training_report.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    checkpoint = Path(payload["checkpoint_path"])
    checkpoint_payload = torch.load(
        checkpoint, map_location="cpu", weights_only=False
    )
    checkpoint_payload.update({
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "optimizer_sampling_unit": "instance",
        "calibration_aggregation_unit": "instance",
        "checkpoint_selection_metric": "instance_balanced_total_loss",
        "threshold_net_metric": "instance_balanced_geomean_ratio",
    })
    torch.save(checkpoint_payload, checkpoint)
    payload.update({
        "instance_balanced_wrapper_schema_version": SCHEMA,
        "instance_balancing_policy": INSTANCE_BALANCING_POLICY_V1,
        "optimizer_sampling_unit": "instance",
        "class_balance_unit": "instance",
        "calibration_aggregation_unit": "instance",
        "checkpoint_selection_metric": "instance_balanced_total_loss",
        "threshold_net_metric": "instance_balanced_geomean_ratio",
        "checkpoint_sha256": _sha256(checkpoint),
    })
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_frozen_trainer():
    spec = importlib.util.spec_from_file_location(
        "p0v5_qg2_v4_frozen_selector_trainer", FROZEN_TRAINER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load frozen QG2 selector trainer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _argument_path(name: str) -> Path:
    try:
        value = sys.argv[sys.argv.index(name) + 1]
    except (ValueError, IndexError) as exc:
        raise SystemExit(f"missing required wrapper argument {name}") from exc
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
