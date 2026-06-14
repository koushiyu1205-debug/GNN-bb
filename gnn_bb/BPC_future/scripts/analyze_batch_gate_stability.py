#!/usr/bin/env python3
"""Audit conservative trigger/no-op gates at batch level.

This read-only script searches simple batch-level threshold gates and evaluates
whether high-precision aggregate rules survive leave-one-dataset/instance
validation.  It is evidence for root-cause analysis, not a production selector.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_batch_gate_stability_20260613")

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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("scale") == "20"
        and row.get("run_improvement_class") in {"improved", "worsened"}
    ]


def _as_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(result) else result


def _label(row: dict[str, str], target: str) -> int:
    return 1 if row.get("run_improvement_class") == target else 0


def _metrics(rows: list[dict[str, str]], predictions: list[int], target: str) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for row, prediction in zip(rows, predictions):
        actual = _label(row, target)
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
        "predicted_positive": tp + fp,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def _predict(rows: list[dict[str, str]], feature: str, operator: str, threshold: float) -> list[int]:
    predictions: list[int] = []
    for row in rows:
        value = _as_float(row.get(feature))
        predictions.append(1 if (value >= threshold if operator == ">=" else value <= threshold) else 0)
    return predictions


def _thresholds(rows: list[dict[str, str]], feature: str, max_values: int = 12) -> list[float]:
    values = sorted({_as_float(row.get(feature)) for row in rows})
    if len(values) <= max_values:
        return values
    return sorted({values[round(index * (len(values) - 1) / (max_values - 1))] for index in range(max_values)})


def _all_rules(rows: list[dict[str, str]], target: str, min_predicted: int) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for feature in PRE_BATCH_FEATURES:
        for threshold in _thresholds(rows, feature):
            for operator in (">=", "<="):
                predictions = _predict(rows, feature, operator, threshold)
                metrics = _metrics(rows, predictions, target)
                if metrics["predicted_positive"] < min_predicted:
                    continue
                rules.append(
                    {
                        "feature": feature,
                        "operator": operator,
                        "threshold": threshold,
                        "metrics": metrics,
                    }
                )
    return sorted(
        rules,
        key=lambda rule: (
            rule["metrics"]["precision"] or 0.0,
            rule["metrics"]["tp"],
            rule["metrics"]["recall"] or 0.0,
            -rule["metrics"]["fp"],
        ),
        reverse=True,
    )


def _best_rule(rows: list[dict[str, str]], target: str, min_predicted: int) -> dict[str, Any]:
    rules = _all_rules(rows, target, min_predicted)
    if not rules:
        return {
            "feature": None,
            "operator": None,
            "threshold": None,
            "metrics": _metrics(rows, [0 for _ in rows], target),
        }
    return rules[0]


def _group_rows(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row.get(key, ""), []).append(row)
    return groups


def _leave_one_group(rows: list[dict[str, str]], group_key: str, target: str, min_predicted: int) -> dict[str, Any]:
    groups = _group_rows(rows, group_key)
    all_rows: list[dict[str, str]] = []
    all_predictions: list[int] = []
    group_results: list[dict[str, Any]] = []
    for held_out, test_rows in sorted(groups.items()):
        train_rows = [row for name, group_rows in groups.items() if name != held_out for row in group_rows]
        rule = _best_rule(train_rows, target, min_predicted)
        if rule["feature"] is None:
            predictions = [0 for _ in test_rows]
        else:
            predictions = _predict(test_rows, rule["feature"], rule["operator"], rule["threshold"])
        metrics = _metrics(test_rows, predictions, target)
        group_results.append({group_key: held_out, "rule": rule, **metrics})
        all_rows.extend(test_rows)
        all_predictions.extend(predictions)
    return {
        "group_key": group_key,
        "metrics": _metrics(all_rows, all_predictions, target),
        "groups": group_results,
    }


def _compact(payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload["metrics"]
    return {
        key: metrics[key]
        for key in ("total", "accuracy", "precision", "recall", "predicted_positive", "tp", "fp", "tn", "fn")
    }


def _target_summary(rows: list[dict[str, str]], target: str, min_predicted: int) -> dict[str, Any]:
    aggregate_rules = _all_rules(rows, target, min_predicted)
    lod = _leave_one_group(rows, "dataset", target, min_predicted)
    loi = _leave_one_group(rows, "instance", target, min_predicted)
    top = aggregate_rules[0] if aggregate_rules else None
    return {
        "target": target,
        "min_predicted": min_predicted,
        "top_aggregate_rules": aggregate_rules[:12],
        "leave_one_dataset": lod,
        "leave_one_instance": loi,
        "checks": {
            "aggregate_high_precision_exists": bool(
                top
                and (top["metrics"]["precision"] or 0.0) >= 0.8
                and (top["metrics"]["predicted_positive"] or 0) >= min_predicted
            ),
            "leave_one_dataset_not_viable": (
                (_compact(lod)["precision"] is None or (_compact(lod)["precision"] or 0.0) < 0.75)
                or (_compact(lod)["recall"] is None or (_compact(lod)["recall"] or 0.0) < 0.2)
            ),
            "leave_one_instance_not_viable": (
                (_compact(loi)["precision"] is None or (_compact(loi)["precision"] or 0.0) < 0.75)
                or (_compact(loi)["recall"] is None or (_compact(loi)["recall"] or 0.0) < 0.2)
            ),
        },
    }


def build_summary(input_path: Path, min_predicted: int) -> dict[str, Any]:
    rows = _rows(_read_csv(input_path))
    improved = _target_summary(rows, "improved", min_predicted)
    worsened = _target_summary(rows, "worsened", min_predicted)
    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": {
            "improved": sum(1 for row in rows if row.get("run_improvement_class") == "improved"),
            "worsened": sum(1 for row in rows if row.get("run_improvement_class") == "worsened"),
        },
        "min_predicted": min_predicted,
        "positive_trigger_gate": improved,
        "negative_noop_gate": worsened,
        "checks": {
            "positive_gate_overfits": improved["checks"]["aggregate_high_precision_exists"]
            and improved["checks"]["leave_one_dataset_not_viable"]
            and improved["checks"]["leave_one_instance_not_viable"],
            "negative_gate_not_viable": worsened["checks"]["leave_one_dataset_not_viable"]
            and worsened["checks"]["leave_one_instance_not_viable"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--min-predicted", type=int, default=20)
    args = parser.parse_args()

    summary = build_summary(args.input, args.min_predicted)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    compact = {
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "positive_trigger_gate": {
            "top_aggregate_rule": summary["positive_trigger_gate"]["top_aggregate_rules"][0],
            "leave_one_dataset": _compact(summary["positive_trigger_gate"]["leave_one_dataset"]),
            "leave_one_instance": _compact(summary["positive_trigger_gate"]["leave_one_instance"]),
            "checks": summary["positive_trigger_gate"]["checks"],
        },
        "negative_noop_gate": {
            "top_aggregate_rule": summary["negative_noop_gate"]["top_aggregate_rules"][0],
            "leave_one_dataset": _compact(summary["negative_noop_gate"]["leave_one_dataset"]),
            "leave_one_instance": _compact(summary["negative_noop_gate"]["leave_one_instance"]),
            "checks": summary["negative_noop_gate"]["checks"],
        },
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
