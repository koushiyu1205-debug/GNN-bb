"""Summarize journey-column addition productivity from BPC_future JSONL logs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
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


def _summarize_file(path: Path) -> dict[str, Any] | None:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("event") == "journey_column_addition":
            events.append(record)
    if not events:
        return None

    by_kind = Counter(str(event.get("pricing_kind", "")) for event in events)
    by_class = Counter(str(event.get("addition_productivity_class", "")) for event in events)
    requested = sum(_int(event, "requested_journeys") for event in events)
    added = sum(_int(event, "added_journeys") for event in events)
    new = sum(_int(event, "new_journeys") for event in events)
    replacement = sum(_int(event, "replacement_journeys") for event in events)
    unchanged = sum(_int(event, "unchanged_journeys") for event in events)
    active_changed = sum(_int(event, "active_changed_task_set_count") for event in events)
    inactive_changed = sum(_int(event, "inactive_changed_task_set_count") for event in events)

    return {
        "log_file": str(path),
        "addition_events": len(events),
        "requested_journeys": requested,
        "added_journeys": added,
        "new_journeys": new,
        "replacement_journeys": replacement,
        "unchanged_journeys": unchanged,
        "changed_ratio": _ratio(added, requested),
        "new_ratio": _ratio(new, requested),
        "replacement_ratio": _ratio(replacement, requested),
        "unchanged_ratio": _ratio(unchanged, requested),
        "active_changed_task_set_count": active_changed,
        "inactive_changed_task_set_count": inactive_changed,
        "active_changed_ratio": _ratio(active_changed, active_changed + inactive_changed),
        "pricing_kind_counts": ";".join(f"{key}:{value}" for key, value in sorted(by_kind.items())),
        "productivity_class_counts": ";".join(f"{key}:{value}" for key, value in sorted(by_class.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="JSONL files or directories containing JSONL logs.")
    args = parser.parse_args(argv)

    rows = [row for path in _iter_jsonl(args.paths) if (row := _summarize_file(path)) is not None]
    fieldnames = [
        "log_file",
        "addition_events",
        "requested_journeys",
        "added_journeys",
        "new_journeys",
        "replacement_journeys",
        "unchanged_journeys",
        "changed_ratio",
        "new_ratio",
        "replacement_ratio",
        "unchanged_ratio",
        "active_changed_task_set_count",
        "inactive_changed_task_set_count",
        "active_changed_ratio",
        "pricing_kind_counts",
        "productivity_class_counts",
    ]
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
