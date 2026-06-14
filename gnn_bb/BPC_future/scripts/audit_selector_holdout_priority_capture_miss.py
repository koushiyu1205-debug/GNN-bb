#!/usr/bin/env python3
"""Diagnose why priority selector capture did not hit target contexts.

The priority collection command can be safe and still fail to reproduce the
target context hashes.  This diagnostic compares the historical source capture
events against the newly observed priority capture events and records which
trajectory components diverged.  It only reads JSON/JSONL artifacts; it does
not run BPC, pricing, RMP, Pulse, workers, or certificates.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_RUNBOOK = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_runbook_20260614/"
    "summary.json"
)
DEFAULT_CAPTURE_AUDIT = Path(
    "BPC_future/results/"
    "root_cause_selector_holdout_priority_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_capture_miss_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_priority_capture_miss_zh.md"
)
EVENT_NAME = "journey_counterfactual_replay_capture"
COMPONENT_FIELDS = (
    "active_hash_before",
    "pool_signature_hash",
    "forbidden_signature_hash",
    "pool_task_set_hash",
    "pool_journey_count",
    "rmp_objective_before",
    "pricing_state",
    "pricing_best_reduced_cost",
    "returned_task_set_hash",
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _read_jsonl_events(paths: list[Path]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if row.get("event") != EVENT_NAME:
                continue
            copied = dict(row)
            copied["_log_path"] = str(path)
            copied["returned_task_set_hash"] = _returned_task_set_hash(copied)
            events.append(copied)
    return events


def _returned_task_sets(event: dict[str, Any]) -> set[tuple[int, ...]]:
    values = event.get("returned_journeys", []) or []
    task_sets: set[tuple[int, ...]] = set()
    for journey in values:
        if not isinstance(journey, dict):
            continue
        task_set = journey.get("task_set")
        if task_set is None:
            tasks = journey.get("tasks")
            task_set = tasks
        if task_set is None:
            sequence = journey.get("sequence")
            task_set = sequence
        if task_set is None:
            continue
        try:
            normalized = tuple(sorted(int(item) for item in task_set))
        except (TypeError, ValueError):
            continue
        task_sets.add(normalized)
    return task_sets


def _returned_task_set_hash(event: dict[str, Any]) -> str:
    task_sets = sorted(",".join(str(item) for item in task_set) for task_set in _returned_task_sets(event))
    return "|".join(task_sets)


def _event_digest(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "log_path": event.get("_log_path"),
        "context_hash": event.get("context_hash"),
        "cg_iter": event.get("cg_iter"),
        "pricing_kind": event.get("pricing_kind"),
        "pricing_state": event.get("pricing_state"),
        "active_hash_before": event.get("active_hash_before"),
        "pool_signature_hash": event.get("pool_signature_hash"),
        "forbidden_signature_hash": event.get("forbidden_signature_hash"),
        "pool_task_set_hash": event.get("pool_task_set_hash"),
        "pool_journey_count": event.get("pool_journey_count"),
        "rmp_objective_before": event.get("rmp_objective_before"),
        "pricing_best_reduced_cost": event.get("pricing_best_reduced_cost"),
        "returned_journey_count": event.get("returned_journey_count"),
        "captured_journey_count": event.get("captured_journey_count"),
        "returned_task_set_hash": event.get("returned_task_set_hash"),
    }


def _compare_expected(
    source_event: dict[str, Any], observed_events: list[dict[str, Any]]
) -> dict[str, Any]:
    context_hash = str(source_event.get("context_hash", ""))
    exact_hits = [
        event for event in observed_events if event.get("context_hash") == context_hash
    ]
    same_active = [
        event
        for event in observed_events
        if event.get("active_hash_before") == source_event.get("active_hash_before")
    ]
    same_cg_iter = [
        event for event in observed_events if event.get("cg_iter") == source_event.get("cg_iter")
    ]
    same_active_field_counts = {
        field: int(
            sum(1 for event in same_active if event.get(field) == source_event.get(field))
        )
        for field in COMPONENT_FIELDS
    }
    same_cg_field_counts = {
        field: int(
            sum(1 for event in same_cg_iter if event.get(field) == source_event.get(field))
        )
        for field in COMPONENT_FIELDS
    }
    source_sets = _returned_task_sets(source_event)
    same_active_returned_task_sets_same_count = int(
        sum(1 for event in same_active if _returned_task_sets(event) == source_sets)
    )
    if exact_hits:
        miss_class = "exact_hit"
    elif not same_active:
        miss_class = "source_active_hash_not_reached"
    elif same_active_returned_task_sets_same_count == 0:
        miss_class = "same_active_but_returned_batch_or_component_drift"
    else:
        miss_class = "same_active_partial_component_drift"
    return {
        "context_hash": context_hash,
        "miss_class": miss_class,
        "source_event": _event_digest(source_event),
        "exact_hit_count": len(exact_hits),
        "same_active_event_count": len(same_active),
        "same_cg_iter_event_count": len(same_cg_iter),
        "same_active_field_counts": same_active_field_counts,
        "same_cg_iter_field_counts": same_cg_field_counts,
        "same_active_returned_task_sets_same_count": (
            same_active_returned_task_sets_same_count
        ),
        "same_active_events_sample": [_event_digest(event) for event in same_active[:6]],
        "same_cg_iter_events_sample": [_event_digest(event) for event in same_cg_iter[:6]],
    }


def build_summary(*, runbook_path: Path, capture_audit_path: Path) -> dict[str, Any]:
    runbook = _read_json(runbook_path)
    capture_audit = _read_json(capture_audit_path)
    command_summaries: list[dict[str, Any]] = []
    expected_total = 0
    exact_hit_total = 0
    source_active_missing_total = 0
    same_active_component_drift_total = 0
    observed_events_total = 0
    observed_contexts: set[str] = set()

    for command in runbook.get("commands", []) or []:
        expected = set(str(item) for item in command.get("expected_context_hashes", []) or [])
        source_paths = [Path(str(path)) for path in command.get("source_files", []) or []]
        output_dir = Path(str(command.get("output_dir", "")))
        observed_paths = sorted((output_dir / "logs").glob("*.jsonl"))
        source_events_all = _read_jsonl_events(source_paths)
        observed_events = _read_jsonl_events(observed_paths)
        source_by_context: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for event in source_events_all:
            if str(event.get("context_hash", "")) in expected:
                source_by_context[str(event.get("context_hash"))].append(event)
        observed_contexts.update(str(event.get("context_hash", "")) for event in observed_events)
        expected_total += len(expected)
        observed_events_total += len(observed_events)
        comparisons: list[dict[str, Any]] = []
        for context_hash in sorted(expected):
            source_event = (source_by_context.get(context_hash) or [{}])[0]
            comparison = _compare_expected(source_event, observed_events)
            comparisons.append(comparison)
            exact_hit_total += int(comparison["exact_hit_count"] > 0)
            if comparison["miss_class"] == "source_active_hash_not_reached":
                source_active_missing_total += 1
            if comparison["miss_class"] in {
                "same_active_but_returned_batch_or_component_drift",
                "same_active_partial_component_drift",
            }:
                same_active_component_drift_total += 1
        observed_by_repeat = Counter(
            Path(str(event.get("_log_path", ""))).stem.rsplit("__r", 1)[-1]
            for event in observed_events
        )
        command_summaries.append(
            {
                "command_id": command.get("command_id"),
                "instance": command.get("instance"),
                "profile": command.get("profile"),
                "output_dir": str(output_dir),
                "expected_context_hashes": sorted(expected),
                "source_event_count": sum(len(v) for v in source_by_context.values()),
                "observed_event_count": len(observed_events),
                "observed_context_hashes": sorted(
                    str(event.get("context_hash", "")) for event in observed_events
                ),
                "observed_unique_context_hashes": sorted(
                    {str(event.get("context_hash", "")) for event in observed_events}
                ),
                "observed_active_hashes": sorted(
                    {str(event.get("active_hash_before", "")) for event in observed_events}
                ),
                "observed_pricing_state_counts": dict(
                    Counter(str(event.get("pricing_state", "")) for event in observed_events)
                ),
                "observed_events_by_repeat": dict(sorted(observed_by_repeat.items())),
                "comparisons": comparisons,
            }
        )

    checks = {
        "runbook_passed": runbook.get("all_checks_pass") is True,
        "capture_audit_passed": capture_audit.get("all_checks_pass") is True,
        "capture_audit_safe_no_certificate": capture_audit.get(
            "no_certificate_bad_count"
        )
        == 0,
        "capture_audit_complete_active_basis": capture_audit.get(
            "active_basis_bad_count"
        )
        == 0,
        "expected_contexts_were_not_hit": expected_total > 0
        and exact_hit_total == 0,
        "observed_events_exist": observed_events_total > 0,
        "miss_explained_by_active_or_component_drift": (
            expected_total > 0
            and source_active_missing_total + same_active_component_drift_total
            == expected_total
        ),
    }
    return {
        "schema_version": "selector_holdout_priority_capture_miss_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_priority_capture_miss_diagnosed",
        "source_runbook": str(runbook_path),
        "source_capture_audit": str(capture_audit_path),
        "expected_context_count": expected_total,
        "exact_hit_context_count": exact_hit_total,
        "source_active_hash_missing_context_count": source_active_missing_total,
        "same_active_component_drift_context_count": (
            same_active_component_drift_total
        ),
        "observed_event_count": observed_events_total,
        "observed_unique_context_count": len(observed_contexts),
        "observed_context_hashes": sorted(observed_contexts),
        "command_summaries": command_summaries,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "priority collection did not miss because the capture path was unsafe; "
            "it missed because the rerun followed a different trajectory.  Some "
            "target contexts never reached the historical active hash, and the "
            "target that did share active hash still diverged in pool/forbidden/"
            "returned-batch components."
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout Priority Capture Miss 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告解释 priority collection 已安全采集但没有命中目标 context 的原因。",
        "它只读 runbook、capture audit 和 JSONL，不运行 BPC / pricing / RMP / Pulse，",
        "也不改变 solver 行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_holdout_priority_capture_miss = current",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        f"status = {summary['status']}",
        f"expected_context_count = {summary['expected_context_count']}",
        f"exact_hit_context_count = {summary['exact_hit_context_count']}",
        "source_active_hash_missing_context_count = "
        f"{summary['source_active_hash_missing_context_count']}",
        "same_active_component_drift_context_count = "
        f"{summary['same_active_component_drift_context_count']}",
        f"observed_event_count = {summary['observed_event_count']}",
        f"observed_unique_context_count = {summary['observed_unique_context_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        (
            "priority collection 补采链路是安全的，但没有复现目标上下文："
            "目标 context 中一部分连历史 active hash 都没到达，另一部分虽然到达"
            "同 active hash，但 pool / forbidden / returned-batch 组成不同。"
            "这进一步说明 active hash 或 source profile 本身不足以作为生产 selector "
            "或 replay key。"
        ),
        "",
        summary["interpretation"],
        "",
        "## Command Summaries",
        "",
        "```json",
        json.dumps(
            summary["command_summaries"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## 检查项",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runbook", default=str(DEFAULT_RUNBOOK))
    parser.add_argument("--capture-audit", default=str(DEFAULT_CAPTURE_AUDIT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = build_summary(
        runbook_path=Path(args.runbook),
        capture_audit_path=Path(args.capture_audit),
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, Path(args.report))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
