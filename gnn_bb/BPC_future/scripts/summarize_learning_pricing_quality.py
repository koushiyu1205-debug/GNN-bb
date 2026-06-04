#!/usr/bin/env python3
"""Summarize online column-quality metrics for learning-smoothed pricing logs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize GNN pricing true-RC column-quality logs.")
    parser.add_argument("--logs", nargs="+", required=True, help="JSONL log files or directories.")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-csv", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = [Path(item) for item in args.logs]
    rows = [_summarize_log(path) for path in _iter_jsonl_files(paths)]
    rows = [row for row in rows if row["learning_filter_events"] > 0 or row["status"]]
    summary = {
        "log_count": len(rows),
        "learning_filter_events": sum(int(row["learning_filter_events"]) for row in rows),
        "candidate_journeys": sum(int(row["candidate_journeys"]) for row in rows),
        "true_negative_journeys": sum(int(row["true_negative_journeys"]) for row in rows),
        "kept_journeys": sum(int(row["kept_journeys"]) for row in rows),
        "kept_rate": _safe_ratio(
            sum(int(row["kept_journeys"]) for row in rows),
            sum(int(row["candidate_journeys"]) for row in rows),
        ),
        "true_negative_rate": _safe_ratio(
            sum(int(row["true_negative_journeys"]) for row in rows),
            sum(int(row["candidate_journeys"]) for row in rows),
        ),
        "rows": rows,
    }
    if args.output_csv:
        _write_csv(Path(args.output_csv), rows)
    if args.output_json:
        path = Path(args.output_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


def _iter_jsonl_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.jsonl")))
        else:
            files.append(path)
    return files


def _summarize_log(path: Path) -> dict[str, Any]:
    events = []
    finish: dict[str, Any] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        record = json.loads(raw)
        event = str(record.get("event", ""))
        if event == "journey_learning_true_rc_filter":
            events.append(record)
        elif event == "finish":
            finish = record
    candidate = sum(int(record.get("candidate_journeys", 0)) for record in events)
    true_negative = sum(int(record.get("true_negative_journeys", 0)) for record in events)
    kept = sum(int(record.get("kept_journeys", 0)) for record in events)
    fallback_used = sum(1 for record in events if bool(record.get("fallback_used", False)))
    best_values = [
        float(record["best_true_reduced_cost"])
        for record in events
        if record.get("best_true_reduced_cost") is not None
    ]
    kept_best_values = [
        float(record["kept_best_true_reduced_cost"])
        for record in events
        if record.get("kept_best_true_reduced_cost") is not None
    ]
    return {
        "log_path": str(path),
        "instance": str(finish.get("instance", "") or _instance_from_log_path(path)),
        "status": str(finish.get("status", "")),
        "time": _none_or_float(finish.get("time")),
        "nodes": int(finish.get("nodes", 0) or 0),
        "pricing_calls": int(finish.get("pricing_calls", 0) or 0),
        "learning_filter_events": len(events),
        "candidate_journeys": int(candidate),
        "true_negative_journeys": int(true_negative),
        "kept_journeys": int(kept),
        "kept_rate": _safe_ratio(kept, candidate),
        "true_negative_rate": _safe_ratio(true_negative, candidate),
        "kept_per_true_negative": _safe_ratio(kept, true_negative),
        "fallback_used_events": int(fallback_used),
        "best_true_reduced_cost": None if not best_values else min(best_values),
        "kept_best_true_reduced_cost": None if not kept_best_values else min(kept_best_values),
    }


def _instance_from_log_path(path: Path) -> str:
    name = path.name
    if name.endswith(".json.jsonl"):
        return name[: -len(".json.jsonl")]
    if name.endswith(".jsonl"):
        return name[: -len(".jsonl")]
    return name


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    if float(denominator) == 0.0:
        return 0.0
    return float(numerator) / float(denominator)


def _none_or_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "log_path",
        "instance",
        "status",
        "time",
        "nodes",
        "pricing_calls",
        "learning_filter_events",
        "candidate_journeys",
        "true_negative_journeys",
        "kept_journeys",
        "kept_rate",
        "true_negative_rate",
        "kept_per_true_negative",
        "fallback_used_events",
        "best_true_reduced_cost",
        "kept_best_true_reduced_cost",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


if __name__ == "__main__":
    main()
