#!/usr/bin/env python3
"""Train a conservative offline CBF/RMP-impact gate.

This script trains a small linear logistic model over flattened
``cbf_gate_transitions.jsonl`` rows.  It is diagnostic-only: the resulting
model may suggest ADD/ABSTAIN thresholds for already true-RC-validated column
batches, but it is not a pricing oracle and cannot create certificates or
official lower bounds.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_DATASET = Path("BPC_future/results/cbf_gate_dataset_global_available_20260614/cbf_gate_transitions.jsonl")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/cbf_gate_training_20260614")
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_cbf_gate_training_zh.md"
)

LEAKAGE_PREFIXES = ("state_next_", "delta_", "next_")
LEAKAGE_FIELDS = {
    "active_hash_switched",
    "barrier_slack",
    "h_next",
    "label_bad_mode_transition",
    "label_cbf_feasible",
    "label_delta_v_nonpositive",
    "mode_switched",
    "state_next_z_hash",
    "v_next",
}
ALLOWED_EXACT_FEATURES = {
    "cg_iter",
    "depth",
    "h_t",
    "node_id",
    "task_count",
    "v_t",
}
ALLOWED_PREFIXES = ("action_", "state_t_", "history_")


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except (TypeError, ValueError):
        return default


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _is_no_effect_row(row: dict[str, Any]) -> bool:
    return (
        row.get("diagnostic_only") is True
        and row.get("certificate_capable") is False
        and row.get("official_bound_effect") is False
    )


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        item = json.loads(raw)
        if not isinstance(item, dict):
            raise ValueError(f"{path}:{line_number}: row is not an object")
        rows.append(dict(item))
    return rows


def cbf_gate_feature_names(rows: list[dict[str, Any]]) -> list[str]:
    """Return feature names available before RMP applies the candidate batch."""

    names: set[str] = set()
    for row in rows:
        for key, value in row.items():
            if key in LEAKAGE_FIELDS or key.startswith(LEAKAGE_PREFIXES):
                continue
            if key in ALLOWED_EXACT_FEATURES or key.startswith(ALLOWED_PREFIXES):
                if isinstance(value, bool):
                    names.add(key)
                else:
                    try:
                        float(value)
                    except (TypeError, ValueError):
                        continue
                    names.add(key)
    return sorted(names)


def _features(row: dict[str, Any], names: list[str]) -> list[float]:
    return [_as_float(row.get(name)) for name in names]


def _labels(rows: Iterable[dict[str, Any]]) -> list[int]:
    return [1 if int(row.get("label_cbf_feasible", 0)) else 0 for row in rows]


def _split_by_instance(
    rows: list[dict[str, Any]],
    *,
    validation_fraction: float,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    by_instance: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_instance.setdefault(str(row.get("instance", "")), []).append(row)
    instances = sorted(by_instance)
    rng = random.Random(int(seed))
    rng.shuffle(instances)
    if len(instances) <= 1:
        train_instances = set(instances)
        validation_instances: set[str] = set()
    else:
        validation_count = max(1, min(len(instances) - 1, round(len(instances) * float(validation_fraction))))
        validation_instances = set(instances[:validation_count])
        train_instances = set(instances[validation_count:])
    train = [row for row in rows if str(row.get("instance", "")) in train_instances]
    validation = [row for row in rows if str(row.get("instance", "")) in validation_instances]
    if not validation and train:
        validation = train[-1:]
        train = train[:-1] or validation
    return train, validation, {
        "split_kind": "instance_holdout",
        "seed": int(seed),
        "validation_fraction": float(validation_fraction),
        "train_instances": sorted(train_instances),
        "validation_instances": sorted(validation_instances),
        "train_count": len(train),
        "validation_count": len(validation),
    }


def _standardize_fit(xs: list[list[float]]) -> tuple[list[float], list[float]]:
    if not xs:
        return [], []
    width = len(xs[0])
    means: list[float] = []
    stds: list[float] = []
    for idx in range(width):
        values = [row[idx] for row in xs]
        mean = sum(values) / float(len(values))
        variance = sum((value - mean) ** 2 for value in values) / float(len(values))
        std = math.sqrt(variance)
        means.append(mean)
        stds.append(std if std > 1.0e-12 else 1.0)
    return means, stds


def _standardize(xs: list[list[float]], means: list[float], stds: list[float]) -> list[list[float]]:
    return [
        [(value - means[idx]) / stds[idx] for idx, value in enumerate(row)]
        for row in xs
    ]


def _train_logistic(
    xs: list[list[float]],
    ys: list[int],
    *,
    epochs: int,
    lr: float,
    l2: float,
) -> list[float]:
    if not xs:
        return []
    width = len(xs[0])
    weights = [0.0] * (width + 1)
    positives = sum(ys)
    negatives = len(ys) - positives
    positive_weight = 1.0 if positives <= 0 else max(1.0, negatives / float(positives))
    for _epoch in range(int(epochs)):
        grad = [0.0] * (width + 1)
        for x, y in zip(xs, ys):
            score = weights[0] + sum(weights[idx + 1] * value for idx, value in enumerate(x))
            p = _sigmoid(score)
            sample_weight = positive_weight if y else 1.0
            err = (p - float(y)) * sample_weight
            grad[0] += err
            for idx, value in enumerate(x):
                grad[idx + 1] += err * value
        denom = max(1.0, float(len(xs)))
        weights[0] -= float(lr) * grad[0] / denom
        for idx in range(1, len(weights)):
            weights[idx] -= float(lr) * ((grad[idx] / denom) + float(l2) * weights[idx])
    return weights


def _predict_probabilities(xs: list[list[float]], weights: list[float]) -> list[float]:
    if not weights:
        return []
    return [
        _sigmoid(weights[0] + sum(weights[idx + 1] * value for idx, value in enumerate(x)))
        for x in xs
    ]


def _metrics(probabilities: list[float], labels: list[int], threshold: float) -> dict[str, Any]:
    predictions = [1 if prob >= threshold else 0 for prob in probabilities]
    tp = sum(1 for pred, label in zip(predictions, labels) if pred == 1 and label == 1)
    fp = sum(1 for pred, label in zip(predictions, labels) if pred == 1 and label == 0)
    tn = sum(1 for pred, label in zip(predictions, labels) if pred == 0 and label == 0)
    fn = sum(1 for pred, label in zip(predictions, labels) if pred == 0 and label == 1)
    predicted_positive = tp + fp
    positives = tp + fn
    negatives = tn + fp
    return {
        "threshold": float(threshold),
        "total": len(labels),
        "positive_count": positives,
        "negative_count": negatives,
        "predicted_positive": predicted_positive,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": None if predicted_positive == 0 else tp / float(predicted_positive),
        "recall": None if positives == 0 else tp / float(positives),
        "false_positive_rate": None if negatives == 0 else fp / float(negatives),
    }


def _select_conservative_threshold(
    probabilities: list[float],
    labels: list[int],
    *,
    min_precision: float,
    max_false_positive_rate: float,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for step in range(50, 100):
        threshold = step / 100.0
        metric = _metrics(probabilities, labels, threshold)
        precision = metric["precision"]
        fpr = metric["false_positive_rate"]
        if (
            metric["predicted_positive"] > 0
            and precision is not None
            and precision >= float(min_precision)
            and (fpr is None or fpr <= float(max_false_positive_rate))
        ):
            candidates.append(metric)
    if not candidates:
        metric = _metrics(probabilities, labels, 1.01)
        return {
            "decision": "abstain_all_on_validation",
            "threshold": 1.01,
            "validation_metrics": metric,
            "reason": "no_threshold_met_conservative_precision_fpr_gate",
        }
    candidates.sort(
        key=lambda item: (
            item["recall"] if item["recall"] is not None else -1.0,
            item["precision"] if item["precision"] is not None else -1.0,
            -item["threshold"],
        ),
        reverse=True,
    )
    best = candidates[0]
    return {
        "decision": "candidate_add_gate",
        "threshold": float(best["threshold"]),
        "validation_metrics": best,
        "reason": "met_conservative_precision_fpr_gate",
    }


def train_cbf_gate(
    dataset: Path,
    *,
    output_dir: Path,
    report: Path,
    epochs: int = 500,
    lr: float = 0.05,
    l2: float = 1.0e-4,
    validation_fraction: float = 0.25,
    seed: int = 17,
    min_precision: float = 0.8,
    max_false_positive_rate: float = 0.05,
) -> dict[str, Any]:
    rows = load_rows(dataset)
    no_effect_count = sum(1 for row in rows if _is_no_effect_row(row))
    feature_names = cbf_gate_feature_names(rows)
    if not rows or no_effect_count != len(rows) or not feature_names:
        summary = {
            "schema_version": "cbf_gate_training_v1",
            "diagnostic_only": True,
            "runs_bpc_or_pricing": False,
            "status": "cbf_gate_training_rejected_input",
            "dataset": str(dataset),
            "row_count": len(rows),
            "no_effect_row_count": no_effect_count,
            "feature_count": len(feature_names),
            "production_ready": False,
            "selector_is_pricing_oracle": False,
            "selector_can_certificate": False,
            "all_checks_pass": False,
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_report(report, summary)
        return summary

    train_rows, validation_rows, split = _split_by_instance(
        rows,
        validation_fraction=validation_fraction,
        seed=seed,
    )
    train_x_raw = [_features(row, feature_names) for row in train_rows]
    validation_x_raw = [_features(row, feature_names) for row in validation_rows]
    train_y = _labels(train_rows)
    validation_y = _labels(validation_rows)
    means, stds = _standardize_fit(train_x_raw)
    train_x = _standardize(train_x_raw, means, stds)
    validation_x = _standardize(validation_x_raw, means, stds)
    weights = _train_logistic(train_x, train_y, epochs=epochs, lr=lr, l2=l2)
    train_prob = _predict_probabilities(train_x, weights)
    validation_prob = _predict_probabilities(validation_x, weights)
    chosen_gate = _select_conservative_threshold(
        validation_prob,
        validation_y,
        min_precision=min_precision,
        max_false_positive_rate=max_false_positive_rate,
    )
    threshold = float(chosen_gate["threshold"])
    model = {
        "schema_version": "cbf_linear_gate_model_v1",
        "exactness_contract": (
            "Diagnostic RMP-impact / CBF gate only.  Inputs are already "
            "true-RC-validated candidate batches.  Never a pricing oracle, "
            "certificate source, or official lower-bound source."
        ),
        "feature_names": feature_names,
        "feature_mean": means,
        "feature_std": stds,
        "weights": weights,
        "threshold": threshold,
        "decision": chosen_gate["decision"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "cbf_linear_gate_model.json"
    model_path.write_text(json.dumps(model, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "schema_version": "cbf_gate_training_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "cbf_gate_trained_offline",
        "dataset": str(dataset),
        "model_path": str(model_path),
        "row_count": len(rows),
        "no_effect_row_count": no_effect_count,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "label_counts": dict(Counter(str(label) for label in _labels(rows))),
        "split": split,
        "train_metrics_at_gate": _metrics(train_prob, train_y, threshold),
        "validation_metrics_at_gate": _metrics(validation_prob, validation_y, threshold),
        "chosen_gate": chosen_gate,
        "min_precision": float(min_precision),
        "max_false_positive_rate": float(max_false_positive_rate),
        "production_ready": False,
        "selector_is_pricing_oracle": False,
        "selector_can_certificate": False,
        "official_bound_effect": False,
        "all_checks_pass": bool(
            len(rows) > 0
            and no_effect_count == len(rows)
            and len(feature_names) > 0
            and len(train_rows) > 0
            and len(validation_rows) > 0
        ),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(report, summary)
    return summary


def _write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# CBF Gate 离线训练报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "训练一个保守的离线 CBF/RMP-impact gate，用于判断已经 true-RC 验证的",
        "候选列批是否可能维持 Lyapunov/CBF surrogate 稳定。该模型不运行 BPC / pricing / RMP，",
        "不生成列，不证明 no-negative，不产生 official lower bound。",
        "",
        "## 机器字段",
        "",
        "```text",
        "cbf_gate_training = current",
        f"status = {summary['status']}",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"production_ready = {str(summary['production_ready']).lower()}",
        f"selector_is_pricing_oracle = {str(summary['selector_is_pricing_oracle']).lower()}",
        f"selector_can_certificate = {str(summary['selector_can_certificate']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 摘要",
        "",
        "```json",
        json.dumps(
            {
                "row_count": summary.get("row_count"),
                "feature_count": summary.get("feature_count"),
                "label_counts": summary.get("label_counts"),
                "split": summary.get("split"),
                "chosen_gate": summary.get("chosen_gate"),
                "validation_metrics_at_gate": summary.get("validation_metrics_at_gate"),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 解释",
        "",
        "- 该 gate 的动作只有 `ADD` 或 `ABSTAIN`，且只能作用于已通过 true-RC 的候选列批；",
        "- 特征选择排除了 `state_next_*`、`delta_*`、`barrier_slack`、label 等未来信息；",
        "- `production_ready=false` 是刻意的：还需要 holdout、5/10 no-regression 和 20-task A/B。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=1.0e-4)
    parser.add_argument("--validation-fraction", type=float, default=0.25)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--min-precision", type=float, default=0.8)
    parser.add_argument("--max-false-positive-rate", type=float, default=0.05)
    args = parser.parse_args(argv)
    summary = train_cbf_gate(
        args.dataset,
        output_dir=args.output_dir,
        report=args.report,
        epochs=args.epochs,
        lr=args.lr,
        l2=args.l2,
        validation_fraction=args.validation_fraction,
        seed=args.seed,
        min_precision=args.min_precision,
        max_false_positive_rate=args.max_false_positive_rate,
    )
    print(
        json.dumps(
            {
                "summary": str(args.output_dir / "summary.json"),
                "report": str(args.report),
                "all_checks_pass": summary["all_checks_pass"],
                "production_ready": summary["production_ready"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
