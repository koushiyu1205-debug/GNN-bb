#!/usr/bin/env python3
"""Audit counterfactual replay capture JSONL events.

This script is diagnostic-only.  It validates whether logs produced with
``journey_counterfactual_replay_capture_enabled=True`` contain enough returned
batch and context payload to seed a later no-certificate-effect replay harness.
It does not run the solver and does not certify any pricing result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


EVENT_NAME = "journey_counterfactual_replay_capture"
SCHEMA_VERSION = "journey_counterfactual_replay_capture_v1"


def _iter_jsonl_paths(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".jsonl":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(candidate for candidate in path.rglob("*.jsonl") if candidate.is_file()))
    return sorted(dict.fromkeys(files))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            records.append(
                {
                    "event": "__json_decode_error__",
                    "path": str(path),
                    "line": int(line_number),
                    "error": str(exc),
                }
            )
            continue
        if isinstance(row, dict):
            records.append(row)
    return records


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _journey_payload_complete(journey: dict[str, Any]) -> bool:
    if not isinstance(journey, dict):
        return False
    required = ("signature", "task_set", "sequence", "true_reduced_cost", "trips")
    if any(key not in journey for key in required):
        return False
    trips = journey.get("trips")
    if not isinstance(trips, list) or not trips:
        return False
    for trip in trips:
        if not isinstance(trip, dict):
            return False
        for key in ("tasks", "start_time", "end_time", "arc_option_ids", "occupancy"):
            if key not in trip:
                return False
        if len(trip.get("arc_option_ids") or []) != len(trip.get("tasks") or []) + 1:
            return False
    return True


def _journey_true_rc(journey: dict[str, Any]) -> float | None:
    try:
        return float(journey.get("true_reduced_cost"))
    except (TypeError, ValueError):
        return None


def _event_issues(event: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if event.get("schema_version") != SCHEMA_VERSION:
        issues.append("schema_version_mismatch")
    if event.get("diagnostic_only") is not True:
        issues.append("diagnostic_only_not_true")
    if event.get("replay_no_certificate_effect") is not True:
        issues.append("replay_no_certificate_effect_not_true")
    if event.get("certificate_capable") is not False:
        issues.append("certificate_capable_not_false")
    if event.get("official_bound_effect") is not False:
        issues.append("official_bound_effect_not_false")
    for key in (
        "context_hash",
        "true_dual_hash",
        "cut_hash",
        "branch_hash",
        "forbidden_signature_hash",
    ):
        if not _has_text(event.get(key)):
            issues.append(f"missing_{key}")
    if "rmp_objective_before" not in event:
        issues.append("missing_rmp_objective_before")
    if not isinstance(event.get("true_dual_vector"), list):
        issues.append("missing_true_dual_vector")
    if not isinstance(event.get("cuts"), list):
        issues.append("missing_cut_payload")
    if not isinstance(event.get("pool_signatures"), list):
        issues.append("missing_pool_signatures")
    if not isinstance(event.get("pool_task_sets"), list):
        issues.append("missing_pool_task_sets")
    pool_journeys = event.get("pool_journeys")
    if not isinstance(pool_journeys, list):
        issues.append("missing_pool_journeys")
        pool_journeys = []
    returned_count = int(event.get("returned_journey_count") or 0)
    captured_count = int(event.get("captured_journey_count") or 0)
    pool_count = int(event.get("pool_journey_count") or 0)
    pool_payload_count = int(event.get("pool_journey_payload_count") or len(pool_journeys))
    journeys = event.get("returned_journeys")
    if not isinstance(journeys, list):
        issues.append("missing_returned_journeys")
        journeys = []
    if captured_count != len(journeys):
        issues.append("captured_count_mismatch")
    if bool(event.get("returned_batch_complete")) and captured_count != returned_count:
        issues.append("complete_batch_count_mismatch")
    if bool(event.get("returned_batch_truncated")) and bool(event.get("returned_batch_complete")):
        issues.append("batch_both_complete_and_truncated")
    if returned_count > 0 and not journeys:
        issues.append("positive_returned_count_without_payload")
    if any(not _journey_payload_complete(journey) for journey in journeys):
        issues.append("incomplete_journey_payload")
    if str(event.get("pricing_state", "")) == "FOUND_NEGATIVE":
        rcs = [_journey_true_rc(journey) for journey in journeys]
        if not any(rc is not None and rc < -1.0e-9 for rc in rcs):
            issues.append("found_negative_without_negative_returned_true_rc")
    if pool_payload_count != len(pool_journeys):
        issues.append("pool_payload_count_mismatch")
    if bool(event.get("pool_snapshot_truncated")) and pool_payload_count >= pool_count and pool_count > 0:
        issues.append("pool_snapshot_truncated_but_payload_not_smaller")
    if not bool(event.get("pool_snapshot_truncated")) and pool_payload_count != pool_count:
        issues.append("pool_complete_payload_count_mismatch")
    if any(not _journey_payload_complete(journey) for journey in pool_journeys):
        issues.append("incomplete_pool_journey_payload")
    return issues


def audit(paths: Iterable[Path]) -> dict[str, Any]:
    files = _iter_jsonl_paths(paths)
    events: list[dict[str, Any]] = []
    decode_errors = 0
    for path in files:
        for record in _read_jsonl(path):
            if record.get("event") == "__json_decode_error__":
                decode_errors += 1
                continue
            if record.get("event") != EVENT_NAME:
                continue
            event = dict(record)
            event["_source_file"] = str(path)
            events.append(event)

    issue_counts: dict[str, int] = {}
    event_summaries: list[dict[str, Any]] = []
    complete_events = 0
    truncated_events = 0
    returned_journeys = 0
    captured_journeys = 0
    pool_journeys = 0
    pool_payload_journeys = 0
    for event in events:
        issues = _event_issues(event)
        for issue in issues:
            issue_counts[issue] = int(issue_counts.get(issue, 0)) + 1
        if bool(event.get("returned_batch_complete")):
            complete_events += 1
        if bool(event.get("returned_batch_truncated")):
            truncated_events += 1
        returned_journeys += int(event.get("returned_journey_count") or 0)
        captured_journeys += int(event.get("captured_journey_count") or 0)
        pool_journeys += int(event.get("pool_journey_count") or 0)
        pool_payload_journeys += int(event.get("pool_journey_payload_count") or 0)
        event_summaries.append(
            {
                "source_file": event.get("_source_file", ""),
                "cg_iter": event.get("cg_iter"),
                "pricing_kind": event.get("pricing_kind"),
                "pricing_state": event.get("pricing_state"),
                "returned_journey_count": event.get("returned_journey_count"),
                "captured_journey_count": event.get("captured_journey_count"),
                "pool_journey_count": event.get("pool_journey_count"),
                "pool_journey_payload_count": event.get("pool_journey_payload_count"),
                "returned_batch_complete": event.get("returned_batch_complete"),
                "returned_batch_truncated": event.get("returned_batch_truncated"),
                "context_hash": event.get("context_hash", ""),
                "active_hash_before": event.get("active_hash_before"),
                "pool_active_task_set_hash_before": event.get(
                    "pool_active_task_set_hash_before"
                ),
                "issues": issues,
            }
        )

    all_events_no_certificate_effect = all(
        event.get("diagnostic_only") is True
        and event.get("replay_no_certificate_effect") is True
        and event.get("certificate_capable") is False
        and event.get("official_bound_effect") is False
        for event in events
    )
    all_complete_events_have_full_batch = all(
        not bool(event.get("returned_batch_complete"))
        or int(event.get("returned_journey_count") or 0) == int(event.get("captured_journey_count") or 0)
        for event in events
    )
    all_returned_journeys_have_trip_payloads = all(
        all(_journey_payload_complete(journey) for journey in event.get("returned_journeys", []) or [])
        for event in events
    )
    all_pool_journeys_have_trip_payloads = all(
        all(_journey_payload_complete(journey) for journey in event.get("pool_journeys", []) or [])
        for event in events
    )
    all_complete_events_have_pool_payloads = all(
        bool(event.get("pool_snapshot_truncated"))
        or int(event.get("pool_journey_count") or 0) == int(event.get("pool_journey_payload_count") or 0)
        for event in events
    )
    all_context_hashes_present = all(
        _has_text(event.get("context_hash"))
        and _has_text(event.get("true_dual_hash"))
        and _has_text(event.get("cut_hash"))
        and _has_text(event.get("branch_hash"))
        and _has_text(event.get("forbidden_signature_hash"))
        for event in events
    )
    checks = {
        "has_capture_events": bool(events),
        "no_json_decode_errors": decode_errors == 0,
        "all_events_no_certificate_effect": all_events_no_certificate_effect,
        "all_complete_events_have_full_batch": all_complete_events_have_full_batch,
        "all_returned_journeys_have_trip_payloads": all_returned_journeys_have_trip_payloads,
        "all_pool_journeys_have_trip_payloads": all_pool_journeys_have_trip_payloads,
        "all_complete_events_have_pool_payloads": all_complete_events_have_pool_payloads,
        "all_context_hashes_present": all_context_hashes_present,
        "no_schema_issues": not bool(issue_counts),
    }
    return {
        "files_scanned": len(files),
        "event_count": len(events),
        "decode_error_count": decode_errors,
        "complete_event_count": complete_events,
        "truncated_event_count": truncated_events,
        "returned_journey_count": returned_journeys,
        "captured_journey_count": captured_journeys,
        "pool_journey_count": pool_journeys,
        "pool_journey_payload_count": pool_payload_journeys,
        "issue_counts": issue_counts,
        "checks": checks,
        "all_checks_pass": all(bool(value) for value in checks.values()),
        "events": event_summaries[:100],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="JSONL files or directories to scan.")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = audit(args.paths)
    output_path = args.output_dir / "summary.json"
    output_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
