#!/usr/bin/env python3
"""Audit whether existing logs contain usable counterfactual replay candidates.

This read-only script works inside exact RMP/active contexts.  It groups rows
by returned-batch descriptors and separates descriptor groups into pure
improved, pure worsened, and mixed labels.  Pure improved-vs-pure worsened
pairs are observational replay candidates; mixed descriptors are evidence that
the existing run-level labels are not causal enough to train a production
selector directly.
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
    "BPC_future/results/root_cause_counterfactual_replay_coverage_20260613"
)

CONTEXT_KEYS = (
    "instance",
    "cg_iter",
    "pricing_kind",
    "active_hash_before",
    "rmp_objective_before",
)

DESCRIPTOR_KEYS = (
    "best_rc",
    "selected_count",
    "materialized_count",
    "returned_count",
    "returned_union_size",
    "returned_task_sets",
    "returned_sequences",
    "returned_arc_families",
)

SAMPLE_COLUMNS = (
    "dataset",
    "profile",
    "repeat_index",
    "run_improvement_class",
    "cg_iter",
    "active_hash_before",
    "rmp_objective_before",
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


def _descriptor_sample(rows: list[dict[str, str]]) -> dict[str, Any]:
    first = rows[0]
    return {
        "descriptor": {key: first.get(key, "") for key in DESCRIPTOR_KEYS},
        "rows": len(rows),
        "label_counts": dict(Counter(row.get("run_improvement_class") for row in rows)),
        "profile_counts": dict(Counter(row.get("profile") for row in rows)),
        "dataset_counts": dict(Counter(row.get("dataset") for row in rows)),
        "samples": [
            {column: row.get(column, "") for column in SAMPLE_COLUMNS}
            for row in rows[:5]
        ],
    }


def _summarize_context(context_key: tuple[str, ...], rows: list[dict[str, str]]) -> dict[str, Any] | None:
    labels = Counter(row.get("run_improvement_class") for row in rows)
    if not labels.get("improved") or not labels.get("worsened"):
        return None
    descriptor_groups = _group_rows(rows, DESCRIPTOR_KEYS)
    pure_improved: list[list[dict[str, str]]] = []
    pure_worsened: list[list[dict[str, str]]] = []
    mixed: list[list[dict[str, str]]] = []
    for descriptor_rows in descriptor_groups.values():
        descriptor_labels = Counter(
            row.get("run_improvement_class") for row in descriptor_rows
        )
        if descriptor_labels.get("improved") and descriptor_labels.get("worsened"):
            mixed.append(descriptor_rows)
        elif descriptor_labels.get("improved"):
            pure_improved.append(descriptor_rows)
        elif descriptor_labels.get("worsened"):
            pure_worsened.append(descriptor_rows)
    pair_count = len(pure_improved) * len(pure_worsened)
    return {
        "context_key": list(context_key),
        "rows": len(rows),
        "label_counts": dict(labels),
        "descriptor_group_count": len(descriptor_groups),
        "pure_improved_descriptor_count": len(pure_improved),
        "pure_worsened_descriptor_count": len(pure_worsened),
        "mixed_descriptor_count": len(mixed),
        "pure_descriptor_pair_count": pair_count,
        "has_replay_candidate_pairs": pair_count > 0,
        "has_mixed_descriptors": bool(mixed),
        "pure_improved_samples": [_descriptor_sample(item) for item in pure_improved],
        "pure_worsened_samples": [_descriptor_sample(item) for item in pure_worsened],
        "mixed_samples": [_descriptor_sample(item) for item in mixed],
    }


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _strict_rows(_read_csv(input_path))
    contexts = _group_rows(rows, CONTEXT_KEYS)
    mixed_contexts = [
        context_summary
        for key, context_rows in sorted(contexts.items())
        if (context_summary := _summarize_context(key, context_rows)) is not None
    ]
    mixed_contexts.sort(key=lambda item: item["rows"], reverse=True)
    descriptor_totals = {
        "pure_improved": sum(
            item["pure_improved_descriptor_count"] for item in mixed_contexts
        ),
        "pure_worsened": sum(
            item["pure_worsened_descriptor_count"] for item in mixed_contexts
        ),
        "mixed": sum(item["mixed_descriptor_count"] for item in mixed_contexts),
    }
    pure_pair_count = sum(item["pure_descriptor_pair_count"] for item in mixed_contexts)
    replay_context_count = sum(
        1 for item in mixed_contexts if item["has_replay_candidate_pairs"]
    )
    mixed_descriptor_context_count = sum(
        1 for item in mixed_contexts if item["has_mixed_descriptors"]
    )
    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(Counter(row.get("run_improvement_class") for row in rows)),
        "context_keys": list(CONTEXT_KEYS),
        "descriptor_keys": list(DESCRIPTOR_KEYS),
        "context_count": len(contexts),
        "mixed_context_count": len(mixed_contexts),
        "mixed_context_rows": sum(item["rows"] for item in mixed_contexts),
        "descriptor_totals_in_mixed_contexts": descriptor_totals,
        "pure_descriptor_pair_count": pure_pair_count,
        "replay_candidate_context_count": replay_context_count,
        "mixed_descriptor_context_count": mixed_descriptor_context_count,
        "mixed_contexts": mixed_contexts,
        "checks": {
            "has_replay_candidates": pure_pair_count > 0,
            "replay_candidates_are_sparse": (
                replay_context_count <= 6 and pure_pair_count <= 50
            ),
            "mixed_descriptors_remain_common": (
                descriptor_totals["mixed"] >= 10
                and mixed_descriptor_context_count >= 8
            ),
            "existing_observational_replay_is_candidate_only": (
                pure_pair_count > 0
                and descriptor_totals["mixed"] >= 10
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
        "mixed_context_count": summary["mixed_context_count"],
        "mixed_context_rows": summary["mixed_context_rows"],
        "descriptor_totals_in_mixed_contexts": summary[
            "descriptor_totals_in_mixed_contexts"
        ],
        "pure_descriptor_pair_count": summary["pure_descriptor_pair_count"],
        "replay_candidate_context_count": summary["replay_candidate_context_count"],
        "mixed_descriptor_context_count": summary["mixed_descriptor_context_count"],
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
