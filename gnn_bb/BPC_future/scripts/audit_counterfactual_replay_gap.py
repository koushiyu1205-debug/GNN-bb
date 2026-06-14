#!/usr/bin/env python3
"""Audit which real addition events still lack exact replay capture payloads.

The existing historical logs often contain ``journey_column_addition`` events
with productivity summaries, but those summaries are observational.  They do
not include the full returned JourneyColumn batch, RMP pool payload, true dual
vector, cut payload, and branch/forbidden context required for controlled
no-certificate-effect replay.

This script is read-only.  It scans JSONL logs and reports how many addition
events are replay-candidate events, and how many have a matching
``journey_counterfactual_replay_capture`` event in the same file/cg_iter/pricing
kind.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


ADDITION_EVENT = "journey_column_addition"
CAPTURE_EVENT = "journey_counterfactual_replay_capture"


def _iter_jsonl_paths(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(candidate for candidate in path.rglob("*.jsonl") if candidate.is_file()))
    return sorted(dict.fromkeys(files))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            rows.append(
                {
                    "event": "__json_decode_error__",
                    "path": str(path),
                    "line": int(line_number),
                    "error": str(exc),
                }
            )
            continue
        if isinstance(record, dict):
            rows.append(record)
    return rows


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _event_key(path: Path, event: dict[str, Any]) -> tuple[str, int, str]:
    return (
        str(path),
        _as_int(event.get("cg_iter")),
        str(event.get("pricing_kind") or ""),
    )


def _addition_replay_candidate(event: dict[str, Any]) -> bool:
    if _as_int(event.get("added_journeys")) <= 0:
        return False
    if str(event.get("pricing_state") or "") != "FOUND_NEGATIVE":
        return False
    if _as_float(event.get("pricing_best_reduced_cost")) >= -1.0e-9:
        return False
    return True


def _addition_priority(event: dict[str, Any]) -> tuple[int, float, int]:
    active_changed = _as_int(event.get("active_changed_task_set_count"))
    new_task_sets = _as_int(event.get("new_task_set_count"))
    replacements = _as_int(event.get("replacement_task_set_count"))
    added = _as_int(event.get("added_journeys"))
    best_rc = _as_float(event.get("pricing_best_reduced_cost"))
    structure_score = 4 * active_changed + 2 * new_task_sets + replacements
    return (-structure_score, best_rc, -added)


def audit(paths: Iterable[Path]) -> dict[str, Any]:
    files = _iter_jsonl_paths(paths)
    decode_errors = 0
    additions: list[dict[str, Any]] = []
    capture_keys: set[tuple[str, int, str]] = set()
    capture_count = 0

    for path in files:
        for record in _read_jsonl(path):
            if record.get("event") == "__json_decode_error__":
                decode_errors += 1
                continue
            if record.get("event") == CAPTURE_EVENT:
                capture_count += 1
                capture_keys.add(_event_key(path, record))
            elif record.get("event") == ADDITION_EVENT:
                event = dict(record)
                event["_source_file"] = str(path)
                event["_has_matching_capture"] = _event_key(path, event) in capture_keys
                additions.append(event)

    replay_candidates = [event for event in additions if _addition_replay_candidate(event)]
    missing_capture = [
        event
        for event in replay_candidates
        if not bool(event.get("_has_matching_capture"))
    ]
    with_capture = [
        event
        for event in replay_candidates
        if bool(event.get("_has_matching_capture"))
    ]
    missing_capture.sort(key=_addition_priority)
    total_added = sum(_as_int(event.get("added_journeys")) for event in replay_candidates)
    active_changed = sum(_as_int(event.get("active_changed_task_set_count")) for event in replay_candidates)
    inactive_changed = sum(_as_int(event.get("inactive_changed_task_set_count")) for event in replay_candidates)
    new_task_sets = sum(_as_int(event.get("new_task_set_count")) for event in replay_candidates)
    replacements = sum(_as_int(event.get("replacement_task_set_count")) for event in replay_candidates)
    checks = {
        "has_addition_events": bool(additions),
        "has_replay_candidate_additions": bool(replay_candidates),
        "has_missing_capture_replay_candidates": bool(missing_capture),
        "no_json_decode_errors": decode_errors == 0,
        "historical_additions_are_not_controlled_replay_ready": bool(replay_candidates)
        and len(missing_capture) == len(replay_candidates),
    }
    return {
        "files_scanned": len(files),
        "decode_error_count": decode_errors,
        "addition_event_count": len(additions),
        "capture_event_count": capture_count,
        "replay_candidate_addition_count": len(replay_candidates),
        "replay_candidate_with_capture_count": len(with_capture),
        "missing_capture_replay_candidate_count": len(missing_capture),
        "replay_candidate_added_journey_total": total_added,
        "replay_candidate_active_changed_task_set_total": active_changed,
        "replay_candidate_inactive_changed_task_set_total": inactive_changed,
        "replay_candidate_new_task_set_total": new_task_sets,
        "replay_candidate_replacement_task_set_total": replacements,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "top_missing_capture_samples": [
            {
                "source_file": event.get("_source_file", ""),
                "cg_iter": event.get("cg_iter"),
                "pricing_kind": event.get("pricing_kind"),
                "pricing_reason": event.get("pricing_reason"),
                "pricing_best_reduced_cost": event.get("pricing_best_reduced_cost"),
                "added_journeys": event.get("added_journeys"),
                "addition_productivity_class": event.get("addition_productivity_class"),
                "new_task_set_count": event.get("new_task_set_count"),
                "replacement_task_set_count": event.get("replacement_task_set_count"),
                "active_changed_task_set_count": event.get("active_changed_task_set_count"),
                "inactive_changed_task_set_count": event.get("inactive_changed_task_set_count"),
                "changed_task_set_samples": event.get("changed_task_set_samples", []),
            }
            for event in missing_capture[:50]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="JSONL files or directories to scan.")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = audit(args.paths)
    output_path = args.output_dir / "summary.json"
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
