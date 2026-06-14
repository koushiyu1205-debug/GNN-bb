#!/usr/bin/env python3
"""Batch-level selector audit for returned JourneyColumn batches.

This read-only script uses stage_rows.csv directly, avoiding candidate-level
label expansion.  It checks whether batch-level addition-before features can
generalize across datasets or instances.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_batch_level_selector_20260613")

PRE_BATCH_FEATURES = (
    "best_rc",
    "selected_count",
    "materialized_count",
    "returned_count",
    "unmaterialized_count",
    "negative_sample_count",
    "returned_union_size",
    "returned_avg_size",
    "returned_pair_overlap",
    "returned_pair_jaccard",
    "active_sample_count_before",
    "active_avg_overlap",
    "active_avg_jaccard",
    "active_redundant_frac",
    "active_bridge_frac",
    "active_disjoint_frac",
    "active_fractional_sum_before",
    "active_fractional_count_before",
    "returned_sequence_count",
    "returned_avg_sequence_len",
    "returned_first_task_unique_count",
    "returned_avg_start_time",
    "returned_start_time_zero_frac",
    "returned_arc_count",
    "returned_low_time_arc_frac",
    "returned_low_risk_arc_frac",
    "returned_low_energy_arc_frac",
)

POST_ADDITION_OR_HINDSIGHT_FEATURES = (
    "addition_requested_count",
    "addition_changed_count",
    "addition_new_count",
    "addition_replacement_count",
    "addition_active_changed_count",
    "addition_inactive_changed_count",
    "next_rmp_objective_delta",
    "zero_fractional_within2",
    "incumbent_within2",
    "next_negative_count",
    "next_incomplete_count",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any) -> float:
    text = str(value or "").strip().lower()
    if text in {"true", "yes"}:
        return 1.0
    if text in {"false", "no"}:
        return 0.0
    try:
        result = float(text)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(result) else result


def _rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("scale") == "20"
        and row.get("run_improvement_class") in {"improved", "worsened"}
    ]


def _label(row: dict[str, str]) -> int:
    return 1 if row.get("run_improvement_class") == "improved" else 0


def _metrics(rows: list[dict[str, str]], predictions: list[int]) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row, prediction in zip(rows, predictions):
        actual = _label(row)
        if prediction and actual:
            tp += 1
        elif prediction and not actual:
            fp += 1
        elif not prediction and not actual:
            tn += 1
        else:
            fn += 1
    total = tp + fp + tn + fn
    return {
        "total": total,
        "accuracy": None if total <= 0 else (tp + tn) / total,
        "precision": None if tp + fp <= 0 else tp / (tp + fp),
        "recall": None if tp + fn <= 0 else tp / (tp + fn),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def _auc(pos_values: list[float], neg_values: list[float]) -> float | None:
    if not pos_values or not neg_values:
        return None
    wins = ties = 0
    for pos in pos_values:
        for neg in neg_values:
            if pos > neg:
                wins += 1
            elif pos == neg:
                ties += 1
    return (wins + 0.5 * ties) / (len(pos_values) * len(neg_values))


def _feature_stats(rows: list[dict[str, str]], features: tuple[str, ...]) -> list[dict[str, Any]]:
    stats: list[dict[str, Any]] = []
    for feature in features:
        pos_values = [_as_float(row.get(feature)) for row in rows if _label(row)]
        neg_values = [_as_float(row.get(feature)) for row in rows if not _label(row)]
        pos_mean = sum(pos_values) / len(pos_values) if pos_values else None
        neg_mean = sum(neg_values) / len(neg_values) if neg_values else None
        auc = _auc(pos_values, neg_values)
        stats.append(
            {
                "feature": feature,
                "positive_mean": pos_mean,
                "negative_mean": neg_mean,
                "mean_diff": None if pos_mean is None or neg_mean is None else pos_mean - neg_mean,
                "auc_positive_higher": auc,
                "auc_margin_abs": None if auc is None else abs(auc - 0.5),
            }
        )
    return sorted(stats, key=lambda row: row["auc_margin_abs"] or 0.0, reverse=True)


def _predict(rows: list[dict[str, str]], feature: str, operator: str, threshold: float) -> list[int]:
    predictions: list[int] = []
    for row in rows:
        value = _as_float(row.get(feature))
        predictions.append(1 if (value >= threshold if operator == ">=" else value <= threshold) else 0)
    return predictions


def _fit_best_single_rule(rows: list[dict[str, str]], features: tuple[str, ...]) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for feature in features:
        thresholds = sorted({_as_float(row.get(feature)) for row in rows})
        for threshold in thresholds:
            for operator in (">=", "<="):
                predictions = _predict(rows, feature, operator, threshold)
                metrics = _metrics(rows, predictions)
                precision = metrics["precision"] or 0.0
                recall = metrics["recall"] or 0.0
                f1 = 0.0 if precision + recall <= 0.0 else 2.0 * precision * recall / (precision + recall)
                score = (f1, metrics["tp"], -metrics["fp"], -metrics["fn"])
                candidate = {
                    "feature": feature,
                    "operator": operator,
                    "threshold": threshold,
                    "train_metrics": metrics,
                    "train_f1": f1,
                    "score": score,
                }
                if best is None or candidate["score"] > best["score"]:
                    best = candidate
    assert best is not None
    return {key: value for key, value in best.items() if key != "score"}


def _group_rows(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(key, "")].append(row)
    return dict(groups)


def _leave_one_group(rows: list[dict[str, str]], group_key: str, features: tuple[str, ...]) -> dict[str, Any]:
    groups = _group_rows(rows, group_key)
    all_rows: list[dict[str, str]] = []
    all_predictions: list[int] = []
    group_results: list[dict[str, Any]] = []
    for held_out, test_rows in sorted(groups.items()):
        train_rows = [row for name, group_rows in groups.items() if name != held_out for row in group_rows]
        rule = _fit_best_single_rule(train_rows, features)
        predictions = _predict(test_rows, rule["feature"], rule["operator"], rule["threshold"])
        metrics = _metrics(test_rows, predictions)
        group_results.append({group_key: held_out, "rule": rule, **metrics})
        all_rows.extend(test_rows)
        all_predictions.extend(predictions)
    return {
        "group_key": group_key,
        "metrics": _metrics(all_rows, all_predictions),
        "groups": group_results,
    }


def _label_summary(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for name, group_rows in sorted(_group_rows(rows, key).items()):
        labels = Counter(row.get("run_improvement_class") for row in group_rows)
        payload.append(
            {
                key: name,
                "rows": len(group_rows),
                "improved": labels.get("improved", 0),
                "worsened": labels.get("worsened", 0),
                "improved_rate": labels.get("improved", 0) / len(group_rows) if group_rows else None,
            }
        )
    return payload


def _compact(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload["metrics"]
    return {key: metrics[key] for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")}


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _rows(_read_csv(input_path))
    labels = Counter(row.get("run_improvement_class") for row in rows)
    pre_dataset = _leave_one_group(rows, "dataset", PRE_BATCH_FEATURES)
    pre_instance = _leave_one_group(rows, "instance", PRE_BATCH_FEATURES)
    oracle_dataset = _leave_one_group(rows, "dataset", POST_ADDITION_OR_HINDSIGHT_FEATURES)
    oracle_instance = _leave_one_group(rows, "instance", POST_ADDITION_OR_HINDSIGHT_FEATURES)
    pre_stats = _feature_stats(rows, PRE_BATCH_FEATURES)
    oracle_stats = _feature_stats(rows, POST_ADDITION_OR_HINDSIGHT_FEATURES)
    pre_lod = _compact(pre_dataset)
    pre_loi = _compact(pre_instance)
    oracle_lod = _compact(oracle_dataset)
    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(labels),
        "dataset_label_summary": _label_summary(rows, "dataset"),
        "instance_label_summary": _label_summary(rows, "instance"),
        "pre_batch_features": list(PRE_BATCH_FEATURES),
        "post_addition_or_hindsight_features": list(POST_ADDITION_OR_HINDSIGHT_FEATURES),
        "pre_batch_feature_stats": pre_stats,
        "post_addition_or_hindsight_feature_stats": oracle_stats,
        "leave_one_dataset": {
            "pre_batch": pre_dataset,
            "post_addition_or_hindsight": oracle_dataset,
        },
        "leave_one_instance": {
            "pre_batch": pre_instance,
            "post_addition_or_hindsight": oracle_instance,
        },
        "checks": {
            "pre_batch_lod_not_strict_gate": (
                (pre_lod["precision"] or 0.0) < 0.75
                or (pre_lod["recall"] or 0.0) < 0.5
            ),
            "pre_batch_loi_not_strict_gate": (
                (pre_loi["precision"] or 0.0) < 0.75
                or (pre_loi["recall"] or 0.0) < 0.5
            ),
            "oracle_lod_has_higher_precision": (
                (oracle_lod["precision"] or 0.0) > (pre_lod["precision"] or 0.0)
            ),
            "top_pre_feature_is_batch_size_related": pre_stats[0]["feature"]
            in {"returned_union_size", "returned_count", "materialized_count", "selected_count"},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary = build_summary(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    compact = {
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "top_pre_batch_feature": summary["pre_batch_feature_stats"][0],
        "top_post_addition_or_hindsight_feature": summary[
            "post_addition_or_hindsight_feature_stats"
        ][0],
        "leave_one_dataset": {
            "pre_batch": _compact(summary["leave_one_dataset"]["pre_batch"]),
            "post_addition_or_hindsight": _compact(
                summary["leave_one_dataset"]["post_addition_or_hindsight"]
            ),
        },
        "leave_one_instance": {
            "pre_batch": _compact(summary["leave_one_instance"]["pre_batch"]),
            "post_addition_or_hindsight": _compact(
                summary["leave_one_instance"]["post_addition_or_hindsight"]
            ),
        },
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
