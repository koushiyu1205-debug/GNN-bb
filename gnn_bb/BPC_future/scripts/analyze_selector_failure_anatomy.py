#!/usr/bin/env python3
"""Explain why simple returned-batch selectors do not generalize.

The script is read-only with respect to solver state.  It reads the
candidate_rows.csv artifact produced by
analyze_returned_batch_trajectory_dataset.py, then writes a compact summary of
label concentration and per-feature direction stability.
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
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_selector_failure_anatomy_20260613")

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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any) -> float:
    try:
        result = float(value)
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


def _mean(values: list[float]) -> float | None:
    return None if not values else sum(values) / len(values)


def _variance(values: list[float], mean: float | None) -> float:
    if not values or mean is None:
        return 0.0
    return sum((value - mean) ** 2 for value in values) / len(values)


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


def _feature_stats(rows: list[dict[str, str]], feature: str) -> dict[str, Any]:
    pos_values = [_as_float(row.get(feature)) for row in rows if _label(row)]
    neg_values = [_as_float(row.get(feature)) for row in rows if not _label(row)]
    pos_mean = _mean(pos_values)
    neg_mean = _mean(neg_values)
    diff = None if pos_mean is None or neg_mean is None else pos_mean - neg_mean
    pos_var = _variance(pos_values, pos_mean)
    neg_var = _variance(neg_values, neg_mean)
    pooled = math.sqrt((pos_var + neg_var) / 2.0)
    effect = None if diff is None or pooled <= 1e-12 else diff / pooled
    auc = _auc(pos_values, neg_values)
    direction = "flat"
    if diff is not None and abs(diff) > 1e-12:
        direction = "positive" if diff > 0.0 else "negative"
    return {
        "rows": len(rows),
        "positive_rows": len(pos_values),
        "negative_rows": len(neg_values),
        "positive_mean": pos_mean,
        "negative_mean": neg_mean,
        "mean_diff": diff,
        "standardized_effect": effect,
        "auc_positive_higher": auc,
        "direction": direction,
    }


def _group_rows(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(key, "")].append(row)
    return dict(groups)


def _group_label_summary(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for name, group_rows in sorted(_group_rows(rows, key).items()):
        labels = Counter(row.get("run_improvement_class") for row in group_rows)
        total = len(group_rows)
        improved = labels.get("improved", 0)
        worsened = labels.get("worsened", 0)
        summaries.append(
            {
                key: name,
                "rows": total,
                "improved": improved,
                "worsened": worsened,
                "improved_rate": None if total <= 0 else improved / total,
            }
        )
    return summaries


def _direction_summary(rows: list[dict[str, str]], group_key: str, feature: str) -> dict[str, Any]:
    group_stats: list[dict[str, Any]] = []
    direction_counts: Counter[str] = Counter()
    auc_values: list[float] = []
    signed_auc_margins: list[float] = []
    for name, group_rows in sorted(_group_rows(rows, group_key).items()):
        stats = _feature_stats(group_rows, feature)
        if stats["positive_rows"] <= 0 or stats["negative_rows"] <= 0:
            stats["usable_for_direction"] = False
        else:
            stats["usable_for_direction"] = True
            direction_counts[stats["direction"]] += 1
            auc = stats["auc_positive_higher"]
            if auc is not None:
                auc_values.append(auc)
                signed_auc_margins.append(auc - 0.5)
        stats[group_key] = name
        group_stats.append(stats)
    nonflat = direction_counts["positive"] + direction_counts["negative"]
    mixed_sign = direction_counts["positive"] > 0 and direction_counts["negative"] > 0
    return {
        "group_key": group_key,
        "usable_groups": nonflat + direction_counts["flat"],
        "positive_direction_groups": direction_counts["positive"],
        "negative_direction_groups": direction_counts["negative"],
        "flat_direction_groups": direction_counts["flat"],
        "mixed_sign": mixed_sign,
        "auc_min": min(auc_values) if auc_values else None,
        "auc_max": max(auc_values) if auc_values else None,
        "auc_margin_min": min(signed_auc_margins) if signed_auc_margins else None,
        "auc_margin_max": max(signed_auc_margins) if signed_auc_margins else None,
        "groups": group_stats,
    }


def _feature_direction_table(rows: list[dict[str, str]]) -> dict[str, Any]:
    table: dict[str, Any] = {}
    robust_features: list[str] = []
    for feature in ADDITION_BEFORE_FEATURES:
        aggregate = _feature_stats(rows, feature)
        dataset = _direction_summary(rows, "dataset", feature)
        instance = _direction_summary(rows, "instance", feature)
        aggregate_auc = aggregate["auc_positive_higher"]
        aggregate_margin = None if aggregate_auc is None else abs(aggregate_auc - 0.5)
        aggregate_direction = "positive" if (aggregate_auc or 0.5) >= 0.5 else "negative"
        dataset_margin_ok = (
            dataset["auc_margin_min"] is not None
            and dataset["auc_margin_max"] is not None
            and (
                (aggregate_direction == "positive" and dataset["auc_margin_min"] >= 0.03)
                or (aggregate_direction == "negative" and dataset["auc_margin_max"] <= -0.03)
            )
        )
        instance_margin_ok = (
            instance["auc_margin_min"] is not None
            and instance["auc_margin_max"] is not None
            and (
                (aggregate_direction == "positive" and instance["auc_margin_min"] >= 0.03)
                or (aggregate_direction == "negative" and instance["auc_margin_max"] <= -0.03)
            )
        )
        robust = bool(
            aggregate_margin is not None
            and aggregate_margin >= 0.15
            and not dataset["mixed_sign"]
            and not instance["mixed_sign"]
            and dataset_margin_ok
            and instance_margin_ok
        )
        if robust:
            robust_features.append(feature)
        table[feature] = {
            "aggregate": aggregate,
            "dataset_direction": {
                key: value for key, value in dataset.items() if key != "groups"
            },
            "instance_direction": {
                key: value for key, value in instance.items() if key != "groups"
            },
            "robust_single_feature_candidate": robust,
            "dataset_groups": dataset["groups"],
            "instance_groups": instance["groups"],
        }
    return {"features": table, "robust_single_feature_candidates": robust_features}


def _top_feature_effects(feature_table: dict[str, Any], limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feature, payload in feature_table.items():
        aggregate = payload["aggregate"]
        effect = aggregate["standardized_effect"]
        auc = aggregate["auc_positive_higher"]
        rows.append(
            {
                "feature": feature,
                "standardized_effect": effect,
                "auc_positive_higher": auc,
                "dataset_mixed_sign": payload["dataset_direction"]["mixed_sign"],
                "instance_mixed_sign": payload["instance_direction"]["mixed_sign"],
                "robust_single_feature_candidate": payload["robust_single_feature_candidate"],
            }
        )
    return sorted(
        rows,
        key=lambda row: abs(row["standardized_effect"] or 0.0),
        reverse=True,
    )[:limit]


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _candidate_rows(_read_csv(input_path))
    labels = Counter(row.get("run_improvement_class") for row in rows)
    dataset_summary = _group_label_summary(rows, "dataset")
    instance_summary = _group_label_summary(rows, "instance")
    direction = _feature_direction_table(rows)
    feature_table = direction["features"]
    positive_total = labels.get("improved", 0)
    dataset_positive_shares = [
        {
            "dataset": row["dataset"],
            "positive_share": None
            if positive_total <= 0
            else row["improved"] / positive_total,
            "improved": row["improved"],
            "worsened": row["worsened"],
            "rows": row["rows"],
        }
        for row in dataset_summary
    ]
    top_positive_dataset = max(
        dataset_positive_shares,
        key=lambda row: row["positive_share"] or 0.0,
        default=None,
    )
    mixed_dataset_features = [
        feature
        for feature, payload in feature_table.items()
        if payload["dataset_direction"]["mixed_sign"]
    ]
    mixed_instance_features = [
        feature
        for feature, payload in feature_table.items()
        if payload["instance_direction"]["mixed_sign"]
    ]
    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(labels),
        "dataset_label_summary": dataset_summary,
        "instance_label_summary": instance_summary,
        "top_positive_dataset": top_positive_dataset,
        "addition_before_features": list(ADDITION_BEFORE_FEATURES),
        "top_aggregate_feature_effects": _top_feature_effects(feature_table),
        "robust_single_feature_candidates": direction["robust_single_feature_candidates"],
        "mixed_dataset_direction_features": mixed_dataset_features,
        "mixed_instance_direction_features": mixed_instance_features,
        "feature_direction_table": feature_table,
        "checks": {
            "positive_labels_concentrated": bool(
                top_positive_dataset
                and (top_positive_dataset["positive_share"] or 0.0) >= 0.75
            ),
            "no_robust_single_feature": not direction["robust_single_feature_candidates"],
            "dataset_direction_instability_present": bool(mixed_dataset_features),
            "instance_direction_instability_present": bool(mixed_instance_features),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary = build_summary(args.input)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "summary.json"
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in summary.items() if key != "feature_direction_table"}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
