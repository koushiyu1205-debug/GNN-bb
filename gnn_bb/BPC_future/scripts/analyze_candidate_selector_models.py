#!/usr/bin/env python3
"""Calibration-only candidate selector model checks.

This script evaluates whether simple addition-before candidate/batch features can
generalize across datasets or instances.  It is read-only with respect to the
solver: it reads candidate_rows.csv produced by
analyze_returned_batch_trajectory_dataset.py and writes a summary.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Callable


DEFAULT_INPUT = Path("BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/candidate_rows.csv")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_candidate_selector_models_20260613")

FEATURES = (
    "candidate_position_frac",
    "candidate_sequence_len",
    "candidate_start_time",
    "candidate_arc_count",
    "candidate_low_time_arc_frac",
    "candidate_low_risk_arc_frac",
    "candidate_low_energy_arc_frac",
    "candidate_active_overlap",
    "candidate_active_jaccard",
    "batch_returned_count",
    "batch_pair_overlap",
    "batch_pair_jaccard",
    "batch_active_avg_overlap",
    "batch_active_redundant_frac",
    "batch_active_bridge_frac",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(result):
        return 0.0
    return result


def _label(row: dict[str, str]) -> int:
    return 1 if row.get("run_improvement_class") == "improved" else 0


def _candidate_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("scale") == "20"
        and row.get("run_improvement_class") in {"improved", "worsened"}
    ]


def _matrix(rows: list[dict[str, str]], means: list[float], scales: list[float]) -> list[list[float]]:
    values: list[list[float]] = []
    for row in rows:
        raw = [_as_float(row.get(feature)) for feature in FEATURES]
        values.append([(value - mean) / scale for value, mean, scale in zip(raw, means, scales)])
    return values


def _fit_standardizer(rows: list[dict[str, str]]) -> tuple[list[float], list[float]]:
    columns = [[_as_float(row.get(feature)) for row in rows] for feature in FEATURES]
    means: list[float] = []
    scales: list[float] = []
    for column in columns:
        mean = sum(column) / len(column) if column else 0.0
        variance = sum((value - mean) ** 2 for value in column) / len(column) if column else 0.0
        scale = math.sqrt(variance)
        means.append(mean)
        scales.append(scale if scale > 1e-12 else 1.0)
    return means, scales


def _metrics(rows: list[dict[str, str]], predictions: list[int]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row, pred in zip(rows, predictions):
        actual = _label(row)
        if pred and actual:
            tp += 1
        elif pred and not actual:
            fp += 1
        elif not pred and not actual:
            tn += 1
        else:
            fn += 1
    total = tp + fp + tn + fn
    accuracy = None if total <= 0 else (tp + tn) / total
    precision = None if tp + fp <= 0 else tp / (tp + fp)
    recall = None if tp + fn <= 0 else tp / (tp + fn)
    return {
        "total": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


class _Model:
    def predict(self, rows: list[dict[str, str]]) -> list[int]:
        raise NotImplementedError


class _NearestCentroidModel(_Model):
    def __init__(self, means: list[float], scales: list[float], pos: list[float], neg: list[float]):
        self.means = means
        self.scales = scales
        self.pos = pos
        self.neg = neg

    def predict(self, rows: list[dict[str, str]]) -> list[int]:
        predictions: list[int] = []
        for vector in _matrix(rows, self.means, self.scales):
            pos_dist = sum((value - center) ** 2 for value, center in zip(vector, self.pos))
            neg_dist = sum((value - center) ** 2 for value, center in zip(vector, self.neg))
            predictions.append(1 if pos_dist <= neg_dist else 0)
        return predictions


def _fit_nearest_centroid(rows: list[dict[str, str]]) -> _Model:
    means, scales = _fit_standardizer(rows)
    matrix = _matrix(rows, means, scales)
    labels = [_label(row) for row in rows]
    pos_rows = [vector for vector, label in zip(matrix, labels) if label == 1]
    neg_rows = [vector for vector, label in zip(matrix, labels) if label == 0]

    def average(items: list[list[float]]) -> list[float]:
        if not items:
            return [0.0 for _ in FEATURES]
        return [sum(row[index] for row in items) / len(items) for index in range(len(FEATURES))]

    return _NearestCentroidModel(means, scales, average(pos_rows), average(neg_rows))


class _LinearMeanDiffModel(_Model):
    def __init__(self, means: list[float], scales: list[float], weights: list[float], threshold: float):
        self.means = means
        self.scales = scales
        self.weights = weights
        self.threshold = threshold

    def predict(self, rows: list[dict[str, str]]) -> list[int]:
        predictions: list[int] = []
        for vector in _matrix(rows, self.means, self.scales):
            score = sum(weight * value for weight, value in zip(self.weights, vector))
            predictions.append(1 if score >= self.threshold else 0)
        return predictions


def _fit_linear_mean_diff(rows: list[dict[str, str]]) -> _Model:
    means, scales = _fit_standardizer(rows)
    matrix = _matrix(rows, means, scales)
    labels = [_label(row) for row in rows]
    pos_rows = [vector for vector, label in zip(matrix, labels) if label == 1]
    neg_rows = [vector for vector, label in zip(matrix, labels) if label == 0]

    def average(items: list[list[float]]) -> list[float]:
        if not items:
            return [0.0 for _ in FEATURES]
        return [sum(row[index] for row in items) / len(items) for index in range(len(FEATURES))]

    pos_mean = average(pos_rows)
    neg_mean = average(neg_rows)
    weights = [pos - neg for pos, neg in zip(pos_mean, neg_mean)]
    scores = [sum(weight * value for weight, value in zip(weights, vector)) for vector in matrix]
    thresholds = sorted(set(scores))
    best_threshold = 0.0
    best_score: tuple[float, int, int, int] | None = None
    for threshold in thresholds:
        predictions = [1 if score >= threshold else 0 for score in scores]
        metrics = _metrics(rows, predictions)
        precision = metrics["precision"] or 0.0
        recall = metrics["recall"] or 0.0
        f1 = 0.0 if precision + recall <= 0.0 else 2.0 * precision * recall / (precision + recall)
        score_tuple = (f1, metrics["tp"], -metrics["fp"], -metrics["fn"])
        if best_score is None or score_tuple > best_score:
            best_score = score_tuple
            best_threshold = threshold
    return _LinearMeanDiffModel(means, scales, weights, best_threshold)


class _TreeNode:
    def __init__(
        self,
        *,
        prediction: int,
        feature_index: int | None = None,
        threshold: float | None = None,
        left: "_TreeNode | None" = None,
        right: "_TreeNode | None" = None,
    ):
        self.prediction = prediction
        self.feature_index = feature_index
        self.threshold = threshold
        self.left = left
        self.right = right

    def predict_one(self, vector: list[float]) -> int:
        if self.feature_index is None or self.threshold is None:
            return self.prediction
        branch = self.left if vector[self.feature_index] <= self.threshold else self.right
        return self.prediction if branch is None else branch.predict_one(vector)


class _ShallowTreeModel(_Model):
    def __init__(self, means: list[float], scales: list[float], root: _TreeNode):
        self.means = means
        self.scales = scales
        self.root = root

    def predict(self, rows: list[dict[str, str]]) -> list[int]:
        return [self.root.predict_one(vector) for vector in _matrix(rows, self.means, self.scales)]


def _gini(labels: list[int]) -> float:
    if not labels:
        return 0.0
    pos = sum(labels)
    p = pos / len(labels)
    return 1.0 - p * p - (1.0 - p) * (1.0 - p)


def _threshold_values(values: list[float], max_values: int = 11) -> list[float]:
    unique = sorted(set(values))
    if len(unique) <= max_values:
        return unique
    selected: list[float] = []
    for index in range(max_values):
        position = round(index * (len(unique) - 1) / (max_values - 1))
        selected.append(unique[position])
    return sorted(set(selected))


def _build_tree(matrix: list[list[float]], labels: list[int], depth: int, max_depth: int) -> _TreeNode:
    pos = sum(labels)
    prediction = 1 if pos * 2 >= len(labels) else 0
    if depth >= max_depth or len(set(labels)) <= 1 or len(labels) < 12:
        return _TreeNode(prediction=prediction)
    parent_impurity = _gini(labels) * len(labels)
    best: tuple[float, int, float, list[int], list[int]] | None = None
    for feature_index in range(len(FEATURES)):
        values = [row[feature_index] for row in matrix]
        for threshold in _threshold_values(values):
            left_indices = [index for index, row in enumerate(matrix) if row[feature_index] <= threshold]
            right_indices = [index for index, row in enumerate(matrix) if row[feature_index] > threshold]
            if len(left_indices) < 6 or len(right_indices) < 6:
                continue
            left_labels = [labels[index] for index in left_indices]
            right_labels = [labels[index] for index in right_indices]
            impurity = _gini(left_labels) * len(left_labels) + _gini(right_labels) * len(right_labels)
            gain = parent_impurity - impurity
            candidate = (gain, feature_index, threshold, left_indices, right_indices)
            if best is None or candidate[:3] > best[:3]:
                best = candidate
    if best is None or best[0] <= 1e-9:
        return _TreeNode(prediction=prediction)
    _, feature_index, threshold, left_indices, right_indices = best
    left_matrix = [matrix[index] for index in left_indices]
    right_matrix = [matrix[index] for index in right_indices]
    left_labels = [labels[index] for index in left_indices]
    right_labels = [labels[index] for index in right_indices]
    return _TreeNode(
        prediction=prediction,
        feature_index=feature_index,
        threshold=threshold,
        left=_build_tree(left_matrix, left_labels, depth + 1, max_depth),
        right=_build_tree(right_matrix, right_labels, depth + 1, max_depth),
    )


def _fit_shallow_tree(rows: list[dict[str, str]]) -> _Model:
    means, scales = _fit_standardizer(rows)
    matrix = _matrix(rows, means, scales)
    labels = [_label(row) for row in rows]
    return _ShallowTreeModel(means, scales, _build_tree(matrix, labels, 0, 3))


MODEL_BUILDERS: dict[str, Callable[[list[dict[str, str]]], _Model]] = {
    "nearest_centroid": _fit_nearest_centroid,
    "linear_mean_diff": _fit_linear_mean_diff,
    "shallow_tree_depth3": _fit_shallow_tree,
}


def _leave_one_group(rows: list[dict[str, str]], group_key: str) -> dict[str, Any]:
    groups = sorted({row[group_key] for row in rows if row.get(group_key)})
    result: dict[str, Any] = {"group_key": group_key, "models": {}}
    for model_name, builder in MODEL_BUILDERS.items():
        total = tp = fp = tn = fn = 0
        group_metrics: list[dict[str, Any]] = []
        for held_out in groups:
            train = [row for row in rows if row.get(group_key) != held_out]
            test = [row for row in rows if row.get(group_key) == held_out]
            if not train or not test:
                continue
            model = builder(train)
            metrics = _metrics(test, model.predict(test))
            total += metrics["total"]
            tp += metrics["tp"]
            fp += metrics["fp"]
            tn += metrics["tn"]
            fn += metrics["fn"]
            group_metrics.append({"held_out": held_out, **metrics})
        precision = None if tp + fp <= 0 else tp / (tp + fp)
        recall = None if tp + fn <= 0 else tp / (tp + fn)
        accuracy = None if total <= 0 else (tp + tn) / total
        result["models"][model_name] = {
            "total": total,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "groups": group_metrics,
        }
    return result


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _candidate_rows(_read_csv(input_path))
    label_counts = dict(Counter(row["run_improvement_class"] for row in rows))
    return {
        "input": str(input_path),
        "features": list(FEATURES),
        "rows": len(rows),
        "label_counts": label_counts,
        "instance_counts": dict(Counter(row["instance"] for row in rows)),
        "dataset_counts": dict(Counter(row["dataset"] for row in rows)),
        "leave_one_dataset": _leave_one_group(rows, "dataset"),
        "leave_one_instance": _leave_one_group(rows, "instance"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    summary = build_summary(Path(args.input))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "summary.json"
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
