#!/usr/bin/env python3
"""Compare addition-before selector features against hindsight trajectory signals.

This read-only audit is not a production selector.  It checks whether the
improved/worsened labels are separable by downstream trajectory features, and
therefore whether the current missing piece is prediction of that downstream
trajectory from addition-before context.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/candidate_rows.csv")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_hindsight_oracle_gap_20260613")

ADDITION_BEFORE_FEATURES = (
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

HINDSIGHT_TRAJECTORY_FEATURES = (
    "candidate_future_active_within2",
    "candidate_future_active_value",
    "incumbent_within2",
    "zero_fractional_within2",
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


def _candidate_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
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
        if operator == ">=":
            predictions.append(1 if value >= threshold else 0)
        else:
            predictions.append(1 if value <= threshold else 0)
    return predictions


def _fit_best_rule(rows: list[dict[str, str]], features: tuple[str, ...]) -> dict[str, Any]:
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
    all_predictions: list[int] = []
    all_rows: list[dict[str, str]] = []
    group_results: list[dict[str, Any]] = []
    groups = _group_rows(rows, group_key)
    for held_out, test_rows in sorted(groups.items()):
        train_rows = [row for name, group_rows in groups.items() if name != held_out for row in group_rows]
        rule = _fit_best_rule(train_rows, features)
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


def _positive_concentration(rows: list[dict[str, str]], group_key: str) -> list[dict[str, Any]]:
    groups = _group_rows(rows, group_key)
    total_positive = sum(_label(row) for row in rows)
    payload: list[dict[str, Any]] = []
    for name, group_rows in sorted(groups.items()):
        positives = sum(_label(row) for row in group_rows)
        payload.append(
            {
                group_key: name,
                "rows": len(group_rows),
                "positive_rows": positives,
                "negative_rows": len(group_rows) - positives,
                "positive_share": None if total_positive <= 0 else positives / total_positive,
                "positive_rate": None if not group_rows else positives / len(group_rows),
            }
        )
    return sorted(payload, key=lambda row: row["positive_share"] or 0.0, reverse=True)


def _compact_metrics(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload["metrics"]
    return {key: metrics[key] for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")}


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _candidate_rows(_read_csv(input_path))
    labels = Counter(row.get("run_improvement_class") for row in rows)
    addition_dataset = _leave_one_group(rows, "dataset", ADDITION_BEFORE_FEATURES)
    addition_instance = _leave_one_group(rows, "instance", ADDITION_BEFORE_FEATURES)
    hindsight_dataset = _leave_one_group(rows, "dataset", HINDSIGHT_TRAJECTORY_FEATURES)
    hindsight_instance = _leave_one_group(rows, "instance", HINDSIGHT_TRAJECTORY_FEATURES)
    summary = {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(labels),
        "addition_before_features": list(ADDITION_BEFORE_FEATURES),
        "hindsight_trajectory_features": list(HINDSIGHT_TRAJECTORY_FEATURES),
        "positive_concentration_by_dataset": _positive_concentration(rows, "dataset"),
        "positive_concentration_by_instance": _positive_concentration(rows, "instance"),
        "addition_before_feature_stats": _feature_stats(rows, ADDITION_BEFORE_FEATURES),
        "hindsight_feature_stats": _feature_stats(rows, HINDSIGHT_TRAJECTORY_FEATURES),
        "leave_one_dataset": {
            "addition_before": addition_dataset,
            "hindsight_trajectory": hindsight_dataset,
        },
        "leave_one_instance": {
            "addition_before": addition_instance,
            "hindsight_trajectory": hindsight_instance,
        },
    }
    hindsight_best = summary["hindsight_feature_stats"][0]
    addition_best = summary["addition_before_feature_stats"][0]
    summary["checks"] = {
        "hindsight_has_stronger_aggregate_signal": (
            (hindsight_best["auc_margin_abs"] or 0.0)
            > (addition_best["auc_margin_abs"] or 0.0)
        ),
        "incumbent_or_zero_fractional_is_top_signal": hindsight_best["feature"]
        in {"incumbent_within2", "zero_fractional_within2"},
        "addition_before_lod_not_high_precision_recall": (
            (_compact_metrics(addition_dataset)["precision"] or 0.0) < 0.75
            or (_compact_metrics(addition_dataset)["recall"] or 0.0) < 0.5
        ),
        "hindsight_lod_has_higher_accuracy": (
            (_compact_metrics(hindsight_dataset)["accuracy"] or 0.0)
            > (_compact_metrics(addition_dataset)["accuracy"] or 0.0)
        ),
    }
    return summary


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
        "top_hindsight_feature": summary["hindsight_feature_stats"][0],
        "top_addition_before_feature": summary["addition_before_feature_stats"][0],
        "leave_one_dataset": {
            "addition_before": _compact_metrics(summary["leave_one_dataset"]["addition_before"]),
            "hindsight_trajectory": _compact_metrics(summary["leave_one_dataset"]["hindsight_trajectory"]),
        },
        "leave_one_instance": {
            "addition_before": _compact_metrics(summary["leave_one_instance"]["addition_before"]),
            "hindsight_trajectory": _compact_metrics(summary["leave_one_instance"]["hindsight_trajectory"]),
        },
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
