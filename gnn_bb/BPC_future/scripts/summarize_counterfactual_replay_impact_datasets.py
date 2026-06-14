#!/usr/bin/env python3
"""Combine counterfactual replay impact datasets for selector calibration.

Each input is a directory produced by
``analyze_counterfactual_replay_impact_dataset.py``.  The output is a combined
candidate/treatment table plus a compact summary.  This is diagnostic-only and
does not run the solver or affect certificates.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _as_float(value: Any, default: float | None = None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _impact_class_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        label = str(row.get(key) or "unknown")
        counts[label] = counts.get(label, 0) + 1
    return counts


def _dataset_dir(path: Path) -> Path:
    if path.is_file():
        return path.parent
    return path


def summarize_impact_datasets(paths: list[Path]) -> dict[str, Any]:
    dataset_summaries: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    treatment_rows: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    for raw_path in paths:
        directory = _dataset_dir(raw_path)
        summary_path = directory / "summary.json"
        candidate_path = directory / "candidate_impact_rows.csv"
        treatment_path = directory / "treatment_impact_rows.csv"
        if not summary_path.exists() or not candidate_path.exists() or not treatment_path.exists():
            missing_inputs.append(str(directory))
            continue
        summary = _read_json(summary_path)
        dataset_name = directory.name
        dataset_summaries.append(
            {
                "dataset": dataset_name,
                "path": str(directory),
                "all_checks_pass": bool(summary.get("all_checks_pass")),
                "case_count": int(summary.get("case_count") or 0),
                "candidate_row_count": int(summary.get("candidate_row_count") or 0),
                "high_impact_candidate_count": int(summary.get("high_impact_candidate_count") or 0),
                "noop_candidate_count": int(summary.get("noop_candidate_count") or 0),
                "worsened_candidate_count": int(summary.get("worsened_candidate_count") or 0),
                "full_batch_improved_count": int(summary.get("full_batch_improved_count") or 0),
                "best_objective_delta": summary.get("best_objective_delta"),
            }
        )
        for row in _read_csv(candidate_path):
            row = dict(row)
            row["impact_dataset"] = dataset_name
            row["impact_dataset_path"] = str(directory)
            candidate_rows.append(row)
        for row in _read_csv(treatment_path):
            row = dict(row)
            row["impact_dataset"] = dataset_name
            row["impact_dataset_path"] = str(directory)
            treatment_rows.append(row)
    deltas = [
        _as_float(row.get("objective_delta"))
        for row in treatment_rows
        if row.get("treatment_id") != "control_no_addition"
    ]
    finite_deltas = [value for value in deltas if value is not None]
    high_impact_rows = [
        row for row in candidate_rows if row.get("single_impact_class") == "improved"
    ]
    noop_rows = [row for row in candidate_rows if row.get("single_impact_class") == "noop"]
    checks = {
        "has_input_datasets": bool(dataset_summaries),
        "no_missing_inputs": not missing_inputs,
        "all_dataset_checks_pass": all(item["all_checks_pass"] for item in dataset_summaries),
        "has_candidate_rows": bool(candidate_rows),
        "has_high_impact_and_noop_examples": bool(high_impact_rows) and bool(noop_rows),
    }
    return {
        "schema_version": "counterfactual_replay_impact_dataset_summary_v1",
        "dataset_count": len(dataset_summaries),
        "dataset_summaries": dataset_summaries,
        "candidate_row_count": len(candidate_rows),
        "treatment_row_count": len(treatment_rows),
        "candidate_impact_class_counts": _impact_class_counts(candidate_rows, "single_impact_class"),
        "treatment_impact_class_counts": _impact_class_counts(treatment_rows, "impact_class"),
        "high_impact_candidate_count": len(high_impact_rows),
        "noop_candidate_count": len(noop_rows),
        "best_objective_delta": None if not finite_deltas else min(finite_deltas),
        "missing_inputs": missing_inputs,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "interpretation": (
            "Combined exact-context replay impact rows are calibration evidence only. "
            "They do not prove solver speedup or a production selector."
        ),
        "candidate_rows": candidate_rows,
        "treatment_rows": treatment_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Impact dataset directories or summary paths.")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = summarize_impact_datasets(args.paths)
    candidate_rows = list(result.pop("candidate_rows"))
    treatment_rows = list(result.pop("treatment_rows"))
    result["combined_candidate_rows_csv"] = str(args.output_dir / "combined_candidate_impact_rows.csv")
    result["combined_treatment_rows_csv"] = str(args.output_dir / "combined_treatment_impact_rows.csv")
    _write_csv(args.output_dir / "combined_candidate_impact_rows.csv", candidate_rows)
    _write_csv(args.output_dir / "combined_treatment_impact_rows.csv", treatment_rows)
    (args.output_dir / "summary.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
