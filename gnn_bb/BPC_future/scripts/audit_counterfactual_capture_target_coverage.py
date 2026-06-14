#!/usr/bin/env python3
"""Audit whether existing capture logs cover planned counterfactual targets.

This diagnostic is read-only.  It checks the target manifest produced by
``build_counterfactual_capture_targets.py`` against existing
``journey_counterfactual_replay_capture`` events.  A target is considered
covered only by a replay-ready, no-certificate-effect capture that matches the
target's exact context.  Missing active-hash evidence fails closed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from BPC_future.scripts.audit_counterfactual_replay_capture import (
    EVENT_NAME,
    _event_issues,
    _iter_jsonl_paths,
    _read_jsonl,
)


DEFAULT_TARGETS = Path(
    "BPC_future/results/root_cause_counterfactual_capture_targets_20260613/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_counterfactual_capture_target_coverage_20260613"
)


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _float_equal(left: Any, right: Any, *, eps: float = 1.0e-6) -> bool:
    left_float = _as_float(left)
    right_float = _as_float(right)
    if left_float is None or right_float is None:
        return False
    return abs(left_float - right_float) <= eps


def _iter_capture_events(paths: Iterable[Path]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in _iter_jsonl_paths(paths):
        for record in _read_jsonl(path):
            if record.get("event") != EVENT_NAME:
                continue
            event = dict(record)
            event["_source_file"] = str(path)
            events.append(event)
    return events


def _text_blob(event: dict[str, Any]) -> str:
    parts = [
        str(event.get("instance", "")),
        str(event.get("instance_path", "")),
        str(event.get("source_log_path", "")),
        str(event.get("_source_file", "")),
    ]
    return " ".join(parts)


def _event_summary(event: dict[str, Any]) -> dict[str, Any]:
    issues = _event_issues(event)
    return {
        "source_file": event.get("_source_file", ""),
        "source_log_path": event.get("source_log_path", ""),
        "instance": event.get("instance", ""),
        "task_count": event.get("task_count"),
        "cg_iter": event.get("cg_iter"),
        "pricing_kind": event.get("pricing_kind"),
        "rmp_objective_before": event.get("rmp_objective_before"),
        "context_hash": event.get("context_hash", ""),
        "active_hash_before": event.get("active_hash_before"),
        "ready_like": not bool(issues),
        "issues": issues,
    }


def _target_event_match(target: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    context = target["context"]
    target_instance = str(context.get("instance", ""))
    event_blob = _text_blob(event)
    instance_match = bool(target_instance and target_instance in event_blob)
    cg_iter_match = _as_int(event.get("cg_iter")) == _as_int(context.get("cg_iter"))
    pricing_kind_match = str(event.get("pricing_kind", "")) == str(
        context.get("pricing_kind", "")
    )
    rmp_objective_match = _float_equal(
        event.get("rmp_objective_before"), context.get("rmp_objective_before")
    )
    active_hash_available = "active_hash_before" in event
    active_hash_match = bool(
        active_hash_available
        and str(event.get("active_hash_before", ""))
        == str(context.get("active_hash_before", ""))
    )
    captured_journey_count = _as_int(event.get("captured_journey_count")) or 0
    returned_journey_count = _as_int(event.get("returned_journey_count")) or 0
    has_captured_returned_batch = captured_journey_count > 0 and returned_journey_count > 0
    no_certificate_effect = bool(
        event.get("diagnostic_only") is True
        and event.get("replay_no_certificate_effect") is True
        and event.get("certificate_capable") is False
        and event.get("official_bound_effect") is False
    )
    complete_payload = bool(
        event.get("returned_batch_complete")
        and not event.get("returned_batch_truncated")
        and not event.get("pool_snapshot_truncated")
        and int(event.get("pool_journey_count") or 0)
        == int(event.get("pool_journey_payload_count") or -1)
    )
    replay_ready = bool(
        no_certificate_effect
        and has_captured_returned_batch
        and complete_payload
        and not _event_issues(event)
        and event.get("vehicle_count") is not None
    )
    exact_target_match = bool(
        instance_match
        and cg_iter_match
        and pricing_kind_match
        and rmp_objective_match
        and active_hash_match
        and replay_ready
    )
    near_match = bool(instance_match or cg_iter_match or rmp_objective_match)
    return {
        "near_match": near_match,
        "exact_target_match": exact_target_match,
        "instance_match": instance_match,
        "cg_iter_match": cg_iter_match,
        "pricing_kind_match": pricing_kind_match,
        "rmp_objective_match": rmp_objective_match,
        "active_hash_available": active_hash_available,
        "active_hash_match": active_hash_match,
        "captured_journey_count": captured_journey_count,
        "returned_journey_count": returned_journey_count,
        "has_captured_returned_batch": has_captured_returned_batch,
        "no_certificate_effect": no_certificate_effect,
        "complete_payload": complete_payload,
        "replay_ready": replay_ready,
        "event": _event_summary(event),
    }


def audit_targets(targets_path: Path, paths: Iterable[Path]) -> dict[str, Any]:
    target_summary = json.loads(targets_path.read_text(encoding="utf-8"))
    targets = list(target_summary.get("targets") or [])
    events = _iter_capture_events(paths)
    target_results: list[dict[str, Any]] = []
    for target in targets:
        matches = [_target_event_match(target, event) for event in events]
        near_matches = [match for match in matches if match["near_match"]]
        exact_matches = [match for match in matches if match["exact_target_match"]]
        target_results.append(
            {
                "target_id": target.get("target_id"),
                "candidate_id": target.get("candidate_id"),
                "context": target.get("context"),
                "exact_target_match_count": len(exact_matches),
                "near_match_count": len(near_matches),
                "covered_by_replay_ready_exact_capture": bool(exact_matches),
                "near_matches": near_matches[:10],
            }
        )
    covered_targets = [
        result for result in target_results if result["covered_by_replay_ready_exact_capture"]
    ]
    near_targets = [result for result in target_results if result["near_match_count"] > 0]
    uncovered_target_count = len(targets) - len(covered_targets)
    checks = {
        "has_targets": bool(targets),
        "scanned_capture_events": bool(events),
        "coverage_counts_consistent": uncovered_target_count >= 0
        and uncovered_target_count + len(covered_targets) == len(targets),
        "has_replay_ready_exact_capture": bool(covered_targets),
        "no_target_exact_capture_coverage_yet": not bool(covered_targets),
        "near_matches_do_not_count_as_exact_capture": len(near_targets)
        >= len(covered_targets),
        "targets_still_need_new_capture": uncovered_target_count > 0,
    }
    structural_check_keys = (
        "has_targets",
        "scanned_capture_events",
        "coverage_counts_consistent",
        "near_matches_do_not_count_as_exact_capture",
    )
    return {
        "targets": str(targets_path),
        "scan_paths": [str(path) for path in paths],
        "target_count": len(targets),
        "capture_event_count": len(events),
        "target_with_near_match_count": len(near_targets),
        "target_with_exact_capture_count": len(covered_targets),
        "uncovered_target_count": uncovered_target_count,
        "target_results": target_results,
        "checks": checks,
        "all_checks_pass": all(bool(checks[key]) for key in structural_check_keys),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("BPC_future/results")],
        help="JSONL files or directories to scan.",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = audit_targets(args.targets, args.paths)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
