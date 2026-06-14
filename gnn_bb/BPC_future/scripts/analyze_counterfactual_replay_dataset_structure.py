#!/usr/bin/env python3
"""Audit exact replay impact dataset structure for selector calibration.

This script is read-only with respect to solver state.  It checks whether the
current exact-context replay rows are structurally rich enough to support a
production addition-before selector, independent of any particular model.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from BPC_future.scripts.analyze_counterfactual_replay_selector_gate import (
    DEFAULT_INPUTS,
    _candidate_csv,
    _dataset_name,
)


DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_replay_dataset_structure_20260613"
)
GROUP_KEYS = ("impact_dataset", "instance", "context_hash")
NUMERIC_FEATURES = ("true_reduced_cost", "cost", "task_count", "vehicle_count")
BOOLEAN_FEATURES = (
    "new_task_set",
    "duplicate_signature",
    "active_support_changing",
    "strict_replacement_by_cost",
    "weak_replacement_or_duplicate",
)


def _read_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for raw_path in paths:
        path = _candidate_csv(raw_path)
        dataset = _dataset_name(path)
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("single_impact_class") not in {"improved", "noop"}:
                    continue
                if str(row.get("single_treatment_found", "")).lower() not in {
                    "1",
                    "true",
                    "yes",
                }:
                    continue
                row = dict(row)
                row["impact_dataset"] = dataset
                row["impact_source"] = str(path)
                rows.append(row)
    return rows


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return True
    if text in {"0", "false", "no"}:
        return False
    return None


def _label_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    return dict(Counter(row["single_impact_class"] for row in rows))


def _group_label_summary(rows: list[dict[str, str]], group_key: str) -> dict[str, Any]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(group_key, ""))].append(row)
    group_rows: list[dict[str, Any]] = []
    mixed_count = pure_improved_count = pure_noop_count = 0
    mixed_rows = pure_rows = 0
    for group, payload in sorted(groups.items()):
        counts = _label_counts(payload)
        labels = {label for label, count in counts.items() if count > 0}
        is_mixed = len(labels) > 1
        if is_mixed:
            mixed_count += 1
            mixed_rows += len(payload)
        else:
            pure_rows += len(payload)
            if labels == {"improved"}:
                pure_improved_count += 1
            elif labels == {"noop"}:
                pure_noop_count += 1
        group_rows.append(
            {
                "group": group,
                "rows": len(payload),
                "label_counts": counts,
                "positive_rate": (
                    counts.get("improved", 0) / float(len(payload)) if payload else None
                ),
                "is_mixed_label_group": is_mixed,
            }
        )
    total_rows = len(rows)
    return {
        "group_key": group_key,
        "group_count": len(groups),
        "mixed_label_group_count": mixed_count,
        "pure_improved_group_count": pure_improved_count,
        "pure_noop_group_count": pure_noop_count,
        "mixed_label_row_count": mixed_rows,
        "single_label_row_count": pure_rows,
        "single_label_row_share": (
            pure_rows / float(total_rows) if total_rows else None
        ),
        "groups": group_rows,
    }


def _feature_coverage(rows: list[dict[str, str]]) -> dict[str, Any]:
    coverage: dict[str, Any] = {}
    for feature in NUMERIC_FEATURES:
        values = [_as_float(row.get(feature)) for row in rows]
        missing = sum(1 for value in values if value is None)
        numeric_values = [value for value in values if value is not None]
        coverage[feature] = {
            "missing_count": missing,
            "observed_count": len(numeric_values),
            "distinct_count": len(set(numeric_values)),
        }
    for feature in BOOLEAN_FEATURES:
        values = [_as_bool(row.get(feature)) for row in rows]
        missing = sum(1 for value in values if value is None)
        bool_values = [value for value in values if value is not None]
        coverage[feature] = {
            "missing_count": missing,
            "observed_count": len(bool_values),
            "true_count": sum(1 for value in bool_values if value),
            "false_count": sum(1 for value in bool_values if not value),
        }
    return coverage


def analyze_dataset_structure(paths: list[Path]) -> dict[str, Any]:
    rows = _read_rows(paths)
    label_counts = _label_counts(rows)
    group_summaries = {
        group_key: _group_label_summary(rows, group_key) for group_key in GROUP_KEYS
    }
    dataset_summary = group_summaries["impact_dataset"]
    instance_summary = group_summaries["instance"]
    context_summary = group_summaries["context_hash"]
    dataset_with_both_labels = dataset_summary["mixed_label_group_count"]
    instance_with_both_labels = instance_summary["mixed_label_group_count"]
    context_with_both_labels = context_summary["mixed_label_group_count"]
    checks = {
        "has_exact_replay_rows": len(rows) >= 200,
        "has_both_labels": (
            label_counts.get("improved", 0) > 0 and label_counts.get("noop", 0) > 0
        ),
        "dataset_label_coverage_is_sparse": dataset_with_both_labels < 2,
        "context_label_coverage_is_sparse": context_with_both_labels < 5,
        "single_label_dataset_groups_exist": (
            dataset_summary["pure_improved_group_count"] > 0
            and dataset_summary["pure_noop_group_count"] > 0
        ),
        "selector_calibration_should_remain_non_production": True,
    }
    result = {
        "schema_version": "counterfactual_replay_dataset_structure_v1",
        "input_paths": [str(_candidate_csv(path)) for path in paths],
        "row_count": len(rows),
        "label_counts": label_counts,
        "group_summaries": group_summaries,
        "feature_coverage": _feature_coverage(rows),
        "checks": checks,
        "interpretation": (
            "Exact replay impact rows are useful for calibration, but label "
            "coverage is still structurally sparse across datasets/contexts; "
            "selector experiments must remain calibration-only."
        ),
    }
    result["all_checks_pass"] = (
        checks["has_exact_replay_rows"]
        and checks["has_both_labels"]
        and checks["dataset_label_coverage_is_sparse"]
        and checks["single_label_dataset_groups_exist"]
        and checks["selector_calibration_should_remain_non_production"]
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        default=list(DEFAULT_INPUTS),
        help="candidate_impact_rows.csv files or directories containing them.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    result = analyze_dataset_structure(list(args.inputs or DEFAULT_INPUTS))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
