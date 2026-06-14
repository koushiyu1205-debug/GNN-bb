#!/usr/bin/env python3
"""Audit label conflicts under exact RMP/returned-batch contexts.

This read-only script checks whether identical addition-before contexts and
returned-batch descriptors can receive both improved and worsened run labels.
Such conflicts mean the existing observational labels are not causal labels for
the returned batch itself; downstream trajectory or profile effects are still
confounding the outcome.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path(
    "BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/"
    "stage_rows.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_exact_context_label_conflicts_20260613"
)

KEY_LEVELS: dict[str, tuple[str, ...]] = {
    "exact_context": (
        "instance",
        "cg_iter",
        "pricing_kind",
        "active_hash_before",
        "rmp_objective_before",
    ),
    "exact_context_tasksets": (
        "instance",
        "cg_iter",
        "pricing_kind",
        "active_hash_before",
        "rmp_objective_before",
        "returned_task_sets",
    ),
    "exact_context_sequences": (
        "instance",
        "cg_iter",
        "pricing_kind",
        "active_hash_before",
        "rmp_objective_before",
        "returned_sequences",
    ),
    "exact_context_full_returned": (
        "instance",
        "cg_iter",
        "pricing_kind",
        "active_hash_before",
        "rmp_objective_before",
        "returned_task_sets",
        "returned_sequences",
        "returned_arc_families",
    ),
    "exact_context_full_features": (
        "instance",
        "cg_iter",
        "pricing_kind",
        "active_hash_before",
        "rmp_objective_before",
        "best_rc",
        "selected_count",
        "materialized_count",
        "returned_count",
        "returned_union_size",
        "returned_task_sets",
        "returned_sequences",
        "returned_arc_families",
    ),
}

SAMPLE_COLUMNS = (
    "dataset",
    "profile",
    "run_improvement_class",
    "run_primal",
    "run_wall_time",
    "cg_iter",
    "best_rc",
    "returned_count",
    "returned_union_size",
    "returned_task_sets",
    "returned_sequences",
    "returned_arc_families",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _strict_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row.get("scale") == "20"
        and row.get("run_improvement_class") in {"improved", "worsened"}
    ]


def _group_rows(rows: list[dict[str, str]], keys: tuple[str, ...]) -> dict[tuple[str, ...], list[dict[str, str]]]:
    groups: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row.get(key, "") for key in keys)].append(row)
    return dict(groups)


def _summarize_level(rows: list[dict[str, str]], keys: tuple[str, ...]) -> dict[str, Any]:
    groups = _group_rows(rows, keys)
    conflicts: list[dict[str, Any]] = []
    for key, group_rows in sorted(groups.items()):
        label_counts = Counter(row.get("run_improvement_class") for row in group_rows)
        if not label_counts.get("improved") or not label_counts.get("worsened"):
            continue
        conflicts.append(
            {
                "key": list(key),
                "rows": len(group_rows),
                "label_counts": dict(label_counts),
                "dataset_counts": dict(Counter(row.get("dataset") for row in group_rows)),
                "profile_counts": dict(Counter(row.get("profile") for row in group_rows)),
                "samples": [
                    {column: row.get(column, "") for column in SAMPLE_COLUMNS}
                    for row in group_rows[:8]
                ],
            }
        )
    conflicts.sort(key=lambda item: item["rows"], reverse=True)
    conflict_rows = sum(item["rows"] for item in conflicts)
    return {
        "keys": list(keys),
        "group_count": len(groups),
        "conflict_group_count": len(conflicts),
        "conflict_rows": conflict_rows,
        "conflict_row_share": conflict_rows / len(rows) if rows else None,
        "largest_conflict": conflicts[0] if conflicts else None,
        "conflicts": conflicts,
    }


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _strict_rows(_read_csv(input_path))
    label_counts = Counter(row.get("run_improvement_class") for row in rows)
    levels = {
        name: _summarize_level(rows, keys)
        for name, keys in KEY_LEVELS.items()
    }
    full_features = levels["exact_context_full_features"]
    exact_context = levels["exact_context"]
    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(label_counts),
        "levels": levels,
        "checks": {
            "exact_context_has_conflicts": exact_context["conflict_group_count"] > 0,
            "full_feature_vectors_have_conflicts": (
                full_features["conflict_group_count"] > 0
            ),
            "full_feature_conflict_rows_are_material": (
                full_features["conflict_rows"] >= 50
            ),
            "observational_labels_not_causal_for_batch": (
                full_features["conflict_group_count"] > 0
                and full_features["conflict_rows"] >= 50
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
        "exact_context": {
            key: value
            for key, value in summary["levels"]["exact_context"].items()
            if key != "conflicts"
        },
        "exact_context_full_features": {
            key: value
            for key, value in summary["levels"]["exact_context_full_features"].items()
            if key != "conflicts"
        },
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
