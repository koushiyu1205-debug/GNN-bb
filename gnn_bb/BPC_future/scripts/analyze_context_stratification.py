#!/usr/bin/env python3
"""Audit context stratification behind returned-batch selector failures.

This read-only script checks whether aggregate selector signals are confounded
by dataset/instance/profile base-rate differences, and whether top pre-batch
features keep a stable direction inside those contexts.
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
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_context_stratification_20260613")

GROUP_KEYS = ("dataset", "instance", "profile")
TOP_PRE_FEATURES = (
    "returned_union_size",
    "returned_arc_count",
    "returned_count",
    "materialized_count",
    "returned_pair_overlap",
    "returned_pair_jaccard",
    "selected_count",
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


def _label(row: dict[str, str]) -> int:
    return 1 if row.get("run_improvement_class") == "improved" else 0


def _group_rows(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(key, "")].append(row)
    return dict(groups)


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


def _feature_direction(rows: list[dict[str, str]], feature: str) -> dict[str, Any]:
    pos_values = [_as_float(row.get(feature)) for row in rows if _label(row)]
    neg_values = [_as_float(row.get(feature)) for row in rows if not _label(row)]
    pos_mean = sum(pos_values) / len(pos_values) if pos_values else None
    neg_mean = sum(neg_values) / len(neg_values) if neg_values else None
    auc = _auc(pos_values, neg_values)
    direction = "unusable"
    if pos_mean is not None and neg_mean is not None:
        if abs(pos_mean - neg_mean) <= 1e-12:
            direction = "flat"
        else:
            direction = "positive" if pos_mean > neg_mean else "negative"
    return {
        "positive_rows": len(pos_values),
        "negative_rows": len(neg_values),
        "positive_mean": pos_mean,
        "negative_mean": neg_mean,
        "auc_positive_higher": auc,
        "direction": direction,
    }


def _group_summary(rows: list[dict[str, str]], key: str) -> dict[str, Any]:
    groups = _group_rows(rows, key)
    summaries: list[dict[str, Any]] = []
    for name, group_rows in sorted(groups.items()):
        labels = Counter(row.get("run_improvement_class") for row in group_rows)
        total = len(group_rows)
        improved = labels.get("improved", 0)
        payload: dict[str, Any] = {
            key: name,
            "rows": total,
            "improved": improved,
            "worsened": labels.get("worsened", 0),
            "improved_rate": None if total <= 0 else improved / total,
        }
        payload["feature_directions"] = {
            feature: _feature_direction(group_rows, feature)
            for feature in TOP_PRE_FEATURES
        }
        summaries.append(payload)
    rates = [row["improved_rate"] for row in summaries if row["improved_rate"] is not None]
    direction_counts: dict[str, Counter[str]] = {
        feature: Counter(
            row["feature_directions"][feature]["direction"]
            for row in summaries
            if row["feature_directions"][feature]["direction"] != "unusable"
        )
        for feature in TOP_PRE_FEATURES
    }
    mixed_features = [
        feature
        for feature, counter in direction_counts.items()
        if counter["positive"] > 0 and counter["negative"] > 0
    ]
    return {
        "group_key": key,
        "groups": summaries,
        "group_count": len(summaries),
        "improved_rate_min": min(rates) if rates else None,
        "improved_rate_max": max(rates) if rates else None,
        "improved_rate_range": None if not rates else max(rates) - min(rates),
        "direction_counts": {
            feature: dict(counter) for feature, counter in direction_counts.items()
        },
        "mixed_direction_features": mixed_features,
    }


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _rows(_read_csv(input_path))
    labels = Counter(row.get("run_improvement_class") for row in rows)
    group_summaries = {key: _group_summary(rows, key) for key in GROUP_KEYS}
    dataset = group_summaries["dataset"]
    instance = group_summaries["instance"]
    profile = group_summaries["profile"]
    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(labels),
        "top_pre_features": list(TOP_PRE_FEATURES),
        "group_summaries": group_summaries,
        "checks": {
            "dataset_base_rate_heterogeneous": (
                (dataset["improved_rate_range"] or 0.0) >= 0.7
            ),
            "instance_base_rate_heterogeneous": (
                (instance["improved_rate_range"] or 0.0) >= 0.3
            ),
            "profile_base_rate_heterogeneous": (
                (profile["improved_rate_range"] or 0.0) >= 0.8
            ),
            "top_feature_direction_mixed_somewhere": any(
                summary["mixed_direction_features"] for summary in group_summaries.values()
            ),
            "returned_union_size_mixed_by_profile": "returned_union_size"
            in profile["mixed_direction_features"],
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
        "group_rate_ranges": {
            key: payload["improved_rate_range"]
            for key, payload in summary["group_summaries"].items()
        },
        "mixed_direction_features": {
            key: payload["mixed_direction_features"]
            for key, payload in summary["group_summaries"].items()
        },
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
