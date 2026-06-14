#!/usr/bin/env python3
"""Pairwise contrast audit inside matched returned-batch contexts.

This read-only script compares improved and worsened returned batches within
the same coarse context.  It asks whether any addition-before feature gives a
stable pairwise ordering signal after controlling for instance/profile.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/"
    "stage_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_matched_context_pairwise_contrast_20260613"
)

MATCH_KEYS = ("instance", "profile")
STRICT_GATE_MIN_BEST_AUC = 0.75
STRICT_GATE_MIN_NON_TIE_SHARE = 0.20
STRICT_GATE_MIN_GROUP_CONSISTENCY = 0.75

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


def _as_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if math.isnan(result) else result


def _strict_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("scale") == "20"
        and row.get("run_improvement_class") in {"improved", "worsened"}
    ]


def _group_rows(rows: list[dict[str, str]]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(key, "") for key in MATCH_KEYS)].append(row)
    return dict(groups)


def _pairwise_feature_stats(groups: dict[tuple[str, ...], list[dict[str, str]]], feature: str) -> dict[str, Any]:
    higher = lower = ties = 0
    group_direction_counts: Counter[str] = Counter()
    group_summaries: list[dict[str, Any]] = []
    for group_key, group_rows in sorted(groups.items()):
        improved = [row for row in group_rows if row.get("run_improvement_class") == "improved"]
        worsened = [row for row in group_rows if row.get("run_improvement_class") == "worsened"]
        if not improved or not worsened:
            continue
        group_higher = group_lower = group_ties = 0
        for good in improved:
            good_value = _as_float(good.get(feature))
            for bad in worsened:
                bad_value = _as_float(bad.get(feature))
                if good_value > bad_value:
                    group_higher += 1
                elif good_value < bad_value:
                    group_lower += 1
                else:
                    group_ties += 1
        group_pairs = group_higher + group_lower + group_ties
        if group_higher > group_lower:
            direction = "positive"
        elif group_lower > group_higher:
            direction = "negative"
        else:
            direction = "flat"
        group_direction_counts[direction] += 1
        higher += group_higher
        lower += group_lower
        ties += group_ties
        group_summaries.append(
            {
                "group_key": list(group_key),
                "pairs": group_pairs,
                "positive_higher": group_higher,
                "positive_lower": group_lower,
                "ties": group_ties,
                "auc_positive_higher": (
                    (group_higher + 0.5 * group_ties) / group_pairs
                    if group_pairs
                    else None
                ),
                "direction": direction,
            }
        )
    pairs = higher + lower + ties
    auc = (higher + 0.5 * ties) / pairs if pairs else None
    best_auc = max(auc, 1.0 - auc) if auc is not None else None
    dominant_direction = "positive" if auc is not None and auc >= 0.5 else "negative"
    same_direction_groups = group_direction_counts.get(dominant_direction, 0)
    mixed_group_count = sum(group_direction_counts.values())
    group_consistency = (
        same_direction_groups / mixed_group_count if mixed_group_count else None
    )
    non_tie_share = (higher + lower) / pairs if pairs else None
    passes_gate = (
        best_auc is not None
        and non_tie_share is not None
        and group_consistency is not None
        and best_auc >= STRICT_GATE_MIN_BEST_AUC
        and non_tie_share >= STRICT_GATE_MIN_NON_TIE_SHARE
        and group_consistency >= STRICT_GATE_MIN_GROUP_CONSISTENCY
    )
    return {
        "feature": feature,
        "pairs": pairs,
        "positive_higher": higher,
        "positive_lower": lower,
        "ties": ties,
        "auc_positive_higher": auc,
        "best_orientation_auc": best_auc,
        "dominant_direction": dominant_direction,
        "non_tie_share": non_tie_share,
        "group_direction_counts": dict(group_direction_counts),
        "group_consistency": group_consistency,
        "passes_strict_pairwise_gate": passes_gate,
        "group_summaries": group_summaries,
    }


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _strict_rows(_read_csv(input_path))
    groups = _group_rows(rows)
    mixed_groups = {
        key: group_rows
        for key, group_rows in groups.items()
        if any(row.get("run_improvement_class") == "improved" for row in group_rows)
        and any(row.get("run_improvement_class") == "worsened" for row in group_rows)
    }
    label_counts = Counter(row.get("run_improvement_class") for row in rows)
    feature_stats = [
        _pairwise_feature_stats(mixed_groups, feature)
        for feature in PRE_BATCH_FEATURES
    ]
    feature_stats.sort(
        key=lambda item: (
            item["best_orientation_auc"] or 0.0,
            item["non_tie_share"] or 0.0,
        ),
        reverse=True,
    )
    passing = [
        item["feature"]
        for item in feature_stats
        if item["passes_strict_pairwise_gate"]
    ]
    top = feature_stats[0] if feature_stats else {}
    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(label_counts),
        "match_keys": list(MATCH_KEYS),
        "group_count": len(groups),
        "mixed_group_count": len(mixed_groups),
        "mixed_rows": sum(len(group_rows) for group_rows in mixed_groups.values()),
        "pre_batch_features": list(PRE_BATCH_FEATURES),
        "strict_gate": {
            "min_best_orientation_auc": STRICT_GATE_MIN_BEST_AUC,
            "min_non_tie_share": STRICT_GATE_MIN_NON_TIE_SHARE,
            "min_group_consistency": STRICT_GATE_MIN_GROUP_CONSISTENCY,
        },
        "feature_pairwise_stats": feature_stats,
        "passing_strict_pairwise_gate": passing,
        "checks": {
            "has_matched_pairs": bool(mixed_groups),
            "no_feature_passes_strict_pairwise_gate": not passing,
            "top_feature_not_production_stable": (
                bool(top)
                and not top["passes_strict_pairwise_gate"]
            ),
            "pairwise_contrast_requires_replay": bool(mixed_groups) and not passing,
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
    compact_top = summary["feature_pairwise_stats"][0] if summary["feature_pairwise_stats"] else {}
    compact = {
        "rows": summary["rows"],
        "label_counts": summary["label_counts"],
        "mixed_group_count": summary["mixed_group_count"],
        "mixed_rows": summary["mixed_rows"],
        "passing_strict_pairwise_gate": summary["passing_strict_pairwise_gate"],
        "top_feature": {
            key: compact_top.get(key)
            for key in (
                "feature",
                "best_orientation_auc",
                "dominant_direction",
                "group_consistency",
                "non_tie_share",
                "group_direction_counts",
            )
        },
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
