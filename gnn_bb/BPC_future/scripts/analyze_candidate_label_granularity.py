#!/usr/bin/env python3
"""Audit the label granularity of returned candidate rows.

This read-only script checks whether candidate_rows.csv contains true
candidate-level causal labels or batch/run-level labels replicated across
returned candidates.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT_DIR = Path("BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_candidate_label_granularity_20260613")

BATCH_KEY = ("dataset", "instance", "profile", "repeat_index", "cg_iter")
STRICT_LABELS = {"improved", "worsened"}

STAGE_LEVEL_FIELDS = (
    "run_improvement_class",
    "run_status",
    "run_primal",
    "run_wall_time",
    "batch_returned_count",
    "batch_pair_overlap",
    "batch_pair_jaccard",
    "batch_active_avg_overlap",
    "batch_active_redundant_frac",
    "batch_active_bridge_frac",
    "incumbent_within2",
    "zero_fractional_within2",
    "next_negative_count",
    "next_incomplete_count",
)

CANDIDATE_LEVEL_FIELDS = (
    "candidate_task_set",
    "candidate_sequence",
    "candidate_first_task",
    "candidate_sequence_len",
    "candidate_start_time",
    "candidate_arc_count",
    "candidate_low_time_arc_frac",
    "candidate_low_risk_arc_frac",
    "candidate_low_energy_arc_frac",
    "candidate_active_overlap",
    "candidate_active_jaccard",
    "candidate_added",
    "candidate_new_task_set",
    "candidate_replacement_task_set",
    "candidate_future_active_within2",
    "candidate_future_active_value",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _batch_key(row: dict[str, str]) -> tuple[str, ...]:
    return tuple(row.get(key, "") for key in BATCH_KEY)


def _strict_stage_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("scale") == "20"
        and row.get("run_improvement_class") in STRICT_LABELS
    ]


def _strict_candidate_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("scale") == "20"
        and row.get("run_improvement_class") in STRICT_LABELS
    ]


def _group(rows: list[dict[str, str]]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[_batch_key(row)].append(row)
    return dict(groups)


def _field_constant_groups(groups: dict[tuple[str, ...], list[dict[str, str]]], field: str) -> int:
    return sum(1 for rows in groups.values() if len({row.get(field, "") for row in rows}) <= 1)


def _field_variable_groups(groups: dict[tuple[str, ...], list[dict[str, str]]], field: str) -> int:
    return sum(1 for rows in groups.values() if len({row.get(field, "") for row in rows}) > 1)


def _distribution_by_label(groups: dict[tuple[str, ...], list[dict[str, str]]]) -> dict[str, Any]:
    by_label: dict[str, list[int]] = defaultdict(list)
    for rows in groups.values():
        label = rows[0].get("run_improvement_class", "")
        by_label[label].append(len(rows))
    payload: dict[str, Any] = {}
    for label, counts in sorted(by_label.items()):
        payload[label] = {
            "batches": len(counts),
            "candidate_rows": sum(counts),
            "avg_candidates_per_batch": None if not counts else sum(counts) / len(counts),
            "max_candidates_per_batch": max(counts) if counts else 0,
        }
    return payload


def build_summary(input_dir: Path) -> dict[str, Any]:
    stage_rows = _strict_stage_rows(_read_csv(input_dir / "stage_rows.csv"))
    candidate_rows = _strict_candidate_rows(_read_csv(input_dir / "candidate_rows.csv"))
    candidate_groups = _group(candidate_rows)
    stage_groups = _group(stage_rows)

    label_mixed_candidate_batches = sum(
        1
        for rows in candidate_groups.values()
        if len({row.get("run_improvement_class", "") for row in rows}) > 1
    )
    candidate_labels = Counter(row.get("run_improvement_class") for row in candidate_rows)
    batch_labels = Counter(rows[0].get("run_improvement_class") for rows in candidate_groups.values())
    stage_labels = Counter(row.get("run_improvement_class") for row in stage_rows)
    expansion_by_label = _distribution_by_label(candidate_groups)

    candidate_positive_rate = candidate_labels["improved"] / len(candidate_rows) if candidate_rows else None
    batch_positive_rate = batch_labels["improved"] / len(candidate_groups) if candidate_groups else None
    stage_positive_rate = stage_labels["improved"] / len(stage_rows) if stage_rows else None

    field_granularity = {
        "stage_level_fields_constant_groups": {
            field: _field_constant_groups(candidate_groups, field)
            for field in STAGE_LEVEL_FIELDS
        },
        "candidate_level_fields_variable_groups": {
            field: _field_variable_groups(candidate_groups, field)
            for field in CANDIDATE_LEVEL_FIELDS
        },
    }
    multi_candidate_batches = sum(1 for rows in candidate_groups.values() if len(rows) > 1)
    stage_keys_missing_candidate_rows = sorted(
        ["|".join(key) for key in set(stage_groups) - set(candidate_groups)]
    )
    candidate_keys_missing_stage_rows = sorted(
        ["|".join(key) for key in set(candidate_groups) - set(stage_groups)]
    )

    improved_expansion = expansion_by_label.get("improved", {})
    worsened_expansion = expansion_by_label.get("worsened", {})
    expansion_ratio = None
    if improved_expansion and worsened_expansion:
        denominator = _as_float(worsened_expansion.get("avg_candidates_per_batch"))
        expansion_ratio = (
            None
            if denominator <= 0.0
            else _as_float(improved_expansion.get("avg_candidates_per_batch")) / denominator
        )

    return {
        "input_dir": str(input_dir),
        "batch_key": list(BATCH_KEY),
        "stage_rows": len(stage_rows),
        "candidate_rows": len(candidate_rows),
        "candidate_batches": len(candidate_groups),
        "stage_batches": len(stage_groups),
        "stage_label_counts": dict(stage_labels),
        "batch_label_counts": dict(batch_labels),
        "candidate_label_counts": dict(candidate_labels),
        "stage_positive_rate": stage_positive_rate,
        "batch_positive_rate": batch_positive_rate,
        "candidate_positive_rate": candidate_positive_rate,
        "positive_rate_shift_candidate_minus_batch": None
        if candidate_positive_rate is None or batch_positive_rate is None
        else candidate_positive_rate - batch_positive_rate,
        "label_mixed_candidate_batches": label_mixed_candidate_batches,
        "multi_candidate_batches": multi_candidate_batches,
        "expansion_by_label": expansion_by_label,
        "improved_vs_worsened_avg_candidate_expansion_ratio": expansion_ratio,
        "field_granularity": field_granularity,
        "stage_keys_missing_candidate_rows": stage_keys_missing_candidate_rows[:20],
        "candidate_keys_missing_stage_rows": candidate_keys_missing_stage_rows[:20],
        "checks": {
            "candidate_rows_are_batch_label_expansion": (
                len(candidate_rows) == 848
                and len(candidate_groups) == 288
                and label_mixed_candidate_batches == 0
            ),
            "candidate_expansion_changes_label_balance": (
                batch_positive_rate is not None
                and candidate_positive_rate is not None
                and candidate_positive_rate - batch_positive_rate > 0.15
            ),
            "improved_batches_have_more_returned_candidates": (
                expansion_ratio is not None and expansion_ratio > 1.5
            ),
            "stage_and_candidate_batch_keys_align": (
                not stage_keys_missing_candidate_rows and not candidate_keys_missing_stage_rows
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    summary = build_summary(args.input_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "summary.json"
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
