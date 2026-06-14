#!/usr/bin/env python3
"""Matched-context audit for returned-batch trajectory labels.

This read-only script controls for coarse context keys and checks whether
pre-batch features still separate improved/worsened within matched contexts.
It helps decide whether existing observational logs are enough, or whether
counterfactual/replay evidence is needed.
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
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_matched_context_audit_20260613")

MATCH_KEYS = {
    "instance_profile": ("instance", "profile"),
    "instance_dataset": ("instance", "dataset"),
    "profile": ("profile",),
    "instance": ("instance",),
}

PRE_BATCH_FEATURES = (
    "best_rc",
    "selected_count",
    "materialized_count",
    "returned_count",
    "negative_sample_count",
    "returned_union_size",
    "returned_arc_count",
    "returned_pair_overlap",
    "returned_pair_jaccard",
    "returned_avg_start_time",
    "returned_low_time_arc_frac",
    "returned_low_risk_arc_frac",
    "active_avg_overlap",
    "active_bridge_frac",
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
        "feature": feature,
        "positive_mean": pos_mean,
        "negative_mean": neg_mean,
        "auc_positive_higher": auc,
        "auc_margin_abs": None if auc is None else abs(auc - 0.5),
        "direction": direction,
    }


def _group_rows(rows: list[dict[str, str]], keys: tuple[str, ...]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(key, "") for key in keys)].append(row)
    return dict(groups)


def _matched_summary(rows: list[dict[str, str]], keys: tuple[str, ...]) -> dict[str, Any]:
    groups = _group_rows(rows, keys)
    mixed_groups: list[dict[str, Any]] = []
    top_direction_counts: Counter[str] = Counter()
    top_feature_counts: Counter[str] = Counter()
    strong_positive = strong_negative = 0
    for group_key, group_rows in sorted(groups.items()):
        labels = Counter(row.get("run_improvement_class") for row in group_rows)
        if not labels.get("improved") or not labels.get("worsened"):
            continue
        stats = [_feature_stats(group_rows, feature) for feature in PRE_BATCH_FEATURES]
        stats = [stat for stat in stats if stat["auc_positive_higher"] is not None]
        top = max(stats, key=lambda stat: stat["auc_margin_abs"] or 0.0)
        top_direction_counts[top["direction"]] += 1
        top_feature_counts[top["feature"]] += 1
        if (top["auc_positive_higher"] or 0.5) >= 0.75:
            strong_positive += 1
        if (top["auc_positive_higher"] or 0.5) <= 0.25:
            strong_negative += 1
        mixed_groups.append(
            {
                "group_key": list(group_key),
                "rows": len(group_rows),
                "improved": labels.get("improved", 0),
                "worsened": labels.get("worsened", 0),
                "top_feature": top,
            }
        )
    mixed_rows = sum(group["rows"] for group in mixed_groups)
    return {
        "keys": list(keys),
        "group_count": len(groups),
        "mixed_group_count": len(mixed_groups),
        "mixed_rows": mixed_rows,
        "mixed_row_share": mixed_rows / len(rows) if rows else None,
        "top_direction_counts": dict(top_direction_counts),
        "top_feature_counts": dict(top_feature_counts),
        "strong_positive_top_groups": strong_positive,
        "strong_negative_top_groups": strong_negative,
        "mixed_groups": mixed_groups,
    }


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _rows(_read_csv(input_path))
    labels = Counter(row.get("run_improvement_class") for row in rows)
    summaries = {
        name: _matched_summary(rows, keys)
        for name, keys in MATCH_KEYS.items()
    }
    strict = summaries["instance_profile"]
    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(labels),
        "pre_batch_features": list(PRE_BATCH_FEATURES),
        "matched_summaries": summaries,
        "checks": {
            "strict_matched_context_sparse": strict["mixed_rows"] < 120,
            "strict_top_directions_mixed": (
                strict["top_direction_counts"].get("positive", 0) > 0
                and strict["top_direction_counts"].get("negative", 0) > 0
            ),
            "strict_no_single_top_feature_dominates": (
                max(strict["top_feature_counts"].values() or [0])
                < max(2, strict["mixed_group_count"])
            ),
            "matched_context_requires_counterfactual": (
                strict["mixed_rows"] < 120
                and strict["top_direction_counts"].get("positive", 0) > 0
                and strict["top_direction_counts"].get("negative", 0) > 0
            ),
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
        "strict_instance_profile": {
            key: value
            for key, value in summary["matched_summaries"]["instance_profile"].items()
            if key != "mixed_groups"
        },
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
