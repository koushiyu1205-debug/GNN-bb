"""Summarize final-judge harvesting quality from BPC_future JSONL logs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any, Iterable


def _iter_jsonl(paths: Iterable[str]) -> Iterable[Path]:
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix == ".jsonl":
            yield path
        elif path.is_dir():
            yield from sorted(path.rglob("*.jsonl"))


def _int(record: dict[str, Any], key: str) -> int:
    value = record.get(key, 0)
    if value is None:
        return 0
    return int(value)


def _ratio(numerator: int, denominator: int) -> float:
    return 0.0 if int(denominator) <= 0 else round(float(numerator) / float(denominator), 9)


def _avg(values: list[int]) -> float:
    return 0.0 if not values else round(float(sum(values)) / float(len(values)), 9)


def _summarize_file(path: Path) -> dict[str, Any] | None:
    pricing_events: list[dict[str, Any]] = []
    addition_events: list[dict[str, Any]] = []
    root_tail_rounds = 0
    hidden_negative_audit_count = 0

    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        event = str(record.get("event", ""))
        if event == "journey_pricing" and str(record.get("pricing_kind", "")) == "exact_completion_bound_retry":
            pricing_events.append(record)
        elif event == "journey_column_addition" and str(record.get("pricing_kind", "")) == "exact_completion_bound_retry":
            addition_events.append(record)
        elif event == "journey_cg_progress_diagnostics":
            if int(record.get("depth", 0) or 0) == 0 and int(record.get("certificate_flat_rounds", 0) or 0) > 0:
                root_tail_rounds += 1
        if "hidden_negative_audit" in event:
            hidden_negative_audit_count += 1

    if not pricing_events and not addition_events:
        return None

    selected_counts = [_int(event, "harvest_selected_count") for event in pricing_events]
    selected_new = sum(_int(event, "harvest_selected_new_task_set_count") for event in pricing_events)
    selected_support = sum(_int(event, "harvest_selected_support_changing_count") for event in pricing_events)
    selected_weak = sum(_int(event, "harvest_selected_weak_replacement_count") for event in pricing_events)
    fallback_total = sum(_int(event, "harvest_fallback_fill_count") for event in pricing_events)
    fallback_replacement = sum(_int(event, "harvest_fallback_fill_replacement_count") for event in pricing_events)
    fallback_weak = sum(_int(event, "harvest_fallback_fill_weak_replacement_count") for event in pricing_events)
    active_changed = sum(_int(event, "active_changed_task_set_count") for event in addition_events)
    requested = sum(_int(event, "requested_journeys") for event in addition_events)
    added = sum(_int(event, "added_journeys") for event in addition_events)
    replacement_added = sum(_int(event, "replacement_journeys") for event in addition_events)

    return {
        "log_file": str(path),
        "exact_completion_bound_retry_calls": len(pricing_events),
        "retry_avg_harvest_selected_count": _avg(selected_counts),
        "retry_max_harvest_selected_count": max(selected_counts, default=0),
        "selected_new_mask_count": selected_new,
        "selected_support_changing_count": selected_support,
        "selected_weak_replacement_count": selected_weak,
        "selected_weak_replacement_ratio": _ratio(selected_weak, sum(selected_counts)),
        "fallback_fill_count": fallback_total,
        "fallback_replacement_count": fallback_replacement,
        "fallback_weak_replacement_count": fallback_weak,
        "fallback_replacement_ratio": _ratio(fallback_replacement, fallback_total),
        "active_changed_task_set_count": active_changed,
        "root_tail_rmp_rounds": root_tail_rounds,
        "hidden_negative_audit_count": hidden_negative_audit_count,
        "final_judge_requested_journeys": requested,
        "final_judge_added_journeys": added,
        "final_judge_replacement_journeys": replacement_added,
        "final_judge_addition_ratio": _ratio(added, requested),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="JSONL files or directories containing JSONL logs.")
    args = parser.parse_args(argv)

    rows = [row for path in _iter_jsonl(args.paths) if (row := _summarize_file(path)) is not None]
    fieldnames = [
        "log_file",
        "exact_completion_bound_retry_calls",
        "retry_avg_harvest_selected_count",
        "retry_max_harvest_selected_count",
        "selected_new_mask_count",
        "selected_support_changing_count",
        "selected_weak_replacement_count",
        "selected_weak_replacement_ratio",
        "fallback_fill_count",
        "fallback_replacement_count",
        "fallback_weak_replacement_count",
        "fallback_replacement_ratio",
        "active_changed_task_set_count",
        "root_tail_rmp_rounds",
        "hidden_negative_audit_count",
        "final_judge_requested_journeys",
        "final_judge_added_journeys",
        "final_judge_replacement_journeys",
        "final_judge_addition_ratio",
    ]
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
