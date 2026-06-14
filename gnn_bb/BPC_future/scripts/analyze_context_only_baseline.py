#!/usr/bin/env python3
"""Context-only baseline for returned-batch trajectory labels.

This read-only audit checks how much improved/worsened separation comes from
dataset/instance/profile identities alone.  It helps distinguish real
addition-before batch signals from context base-rate effects.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv")
DEFAULT_OUTPUT_DIR = Path("BPC_future/results/root_cause_context_only_baseline_20260613")

CONTEXT_SETS = {
    "dataset": ("dataset",),
    "instance": ("instance",),
    "profile": ("profile",),
    "profile_then_instance": ("profile", "instance"),
    "instance_then_profile": ("instance", "profile"),
    "dataset_then_instance": ("dataset", "instance"),
}


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


def _group_rows(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row.get(key, "")].append(row)
    return dict(groups)


def _context_rates(rows: list[dict[str, str]], context_keys: tuple[str, ...]) -> dict[tuple[str, str], float]:
    rates: dict[tuple[str, str], float] = {}
    for context_key in context_keys:
        groups = _group_rows(rows, context_key)
        for value, group_rows in groups.items():
            rates[(context_key, value)] = sum(_label(row) for row in group_rows) / len(group_rows)
    return rates


def _predict_with_context(
    train_rows: list[dict[str, str]],
    test_rows: list[dict[str, str]],
    context_keys: tuple[str, ...],
) -> tuple[list[int], list[dict[str, Any]]]:
    global_rate = sum(_label(row) for row in train_rows) / len(train_rows) if train_rows else 0.0
    rates = _context_rates(train_rows, context_keys)
    predictions: list[int] = []
    decisions: list[dict[str, Any]] = []
    for row in test_rows:
        used_key = "global"
        used_value = ""
        rate = global_rate
        for context_key in context_keys:
            candidate = (context_key, row.get(context_key, ""))
            if candidate in rates:
                used_key, used_value = candidate
                rate = rates[candidate]
                break
        predictions.append(1 if rate >= 0.5 else 0)
        decisions.append({"context_key": used_key, "context_value": used_value, "rate": rate})
    return predictions, decisions


def _leave_one_group(
    rows: list[dict[str, str]],
    holdout_key: str,
    context_keys: tuple[str, ...],
) -> dict[str, Any]:
    groups = _group_rows(rows, holdout_key)
    all_rows: list[dict[str, str]] = []
    all_predictions: list[int] = []
    group_results: list[dict[str, Any]] = []
    for held_out, test_rows in sorted(groups.items()):
        train_rows = [
            row
            for group_name, group_rows in groups.items()
            if group_name != held_out
            for row in group_rows
        ]
        predictions, decisions = _predict_with_context(train_rows, test_rows, context_keys)
        used_context_counts = Counter(decision["context_key"] for decision in decisions)
        metrics = _metrics(test_rows, predictions)
        group_results.append(
            {
                holdout_key: held_out,
                "used_context_counts": dict(used_context_counts),
                **metrics,
            }
        )
        all_rows.extend(test_rows)
        all_predictions.extend(predictions)
    return {
        "holdout_key": holdout_key,
        "context_keys": list(context_keys),
        "metrics": _metrics(all_rows, all_predictions),
        "groups": group_results,
    }


def _label_summary(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for name, group_rows in sorted(_group_rows(rows, key).items()):
        labels = Counter(row.get("run_improvement_class") for row in group_rows)
        total = len(group_rows)
        improved = labels.get("improved", 0)
        summaries.append(
            {
                key: name,
                "rows": total,
                "improved": improved,
                "worsened": labels.get("worsened", 0),
                "improved_rate": improved / total if total else None,
            }
        )
    return summaries


def build_summary(input_path: Path) -> dict[str, Any]:
    rows = _rows(_read_csv(input_path))
    labels = Counter(row.get("run_improvement_class") for row in rows)
    results: dict[str, dict[str, Any]] = {}
    for holdout_key in ("dataset", "instance", "profile"):
        holdout_results = {}
        for context_name, context_keys in CONTEXT_SETS.items():
            holdout_results[context_name] = _leave_one_group(rows, holdout_key, context_keys)
        results[holdout_key] = holdout_results

    def compact_metric(holdout_key: str, context_name: str) -> dict[str, Any]:
        metrics = results[holdout_key][context_name]["metrics"]
        return {
            key: metrics[key]
            for key in ("total", "accuracy", "precision", "recall", "tp", "fp", "tn", "fn")
        }

    best_by_holdout: dict[str, dict[str, Any]] = {}
    for holdout_key, holdout_results in results.items():
        best_name = max(
            holdout_results,
            key=lambda name: (
                holdout_results[name]["metrics"]["accuracy"] or 0.0,
                holdout_results[name]["metrics"]["precision"] or 0.0,
                holdout_results[name]["metrics"]["recall"] or 0.0,
            ),
        )
        best_by_holdout[holdout_key] = {
            "context_set": best_name,
            "metrics": compact_metric(holdout_key, best_name),
        }

    return {
        "input": str(input_path),
        "rows": len(rows),
        "label_counts": dict(labels),
        "label_summary": {
            key: _label_summary(rows, key)
            for key in ("dataset", "instance", "profile")
        },
        "context_sets": {key: list(value) for key, value in CONTEXT_SETS.items()},
        "leave_one_results": results,
        "best_by_holdout": best_by_holdout,
        "checks": {
            "context_only_has_signal": (
                (best_by_holdout["instance"]["metrics"]["precision"] or 0.0) >= 0.6
                and (best_by_holdout["profile"]["metrics"]["precision"] or 0.0) >= 0.6
            ),
            "context_only_not_production_gate": any(
                (payload["metrics"]["precision"] or 0.0) < 0.75
                or (payload["metrics"]["recall"] or 0.0) < 0.5
                for payload in best_by_holdout.values()
            ),
            "dataset_holdout_context_is_weak": (
                (best_by_holdout["dataset"]["metrics"]["precision"] or 0.0) < 0.6
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
        "best_by_holdout": summary["best_by_holdout"],
        "checks": summary["checks"],
    }
    print(json.dumps(compact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
