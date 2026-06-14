#!/usr/bin/env python3
"""Audit selector holdout active-basis capture outputs.

This post-run diagnostic checks the commands emitted by the selector holdout
collection runbook.  It verifies that capture events are diagnostic-only,
no-certificate-effect, and contain complete active-basis snapshots.  It also
records whether the expected context hashes were actually hit.  Missing context
hits are not treated as script failure; they mean the dataset is not yet ready
for selector holdout.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_RUNBOOK = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_runbook_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_capture_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_collection_capture_audit_zh.md"
)
EVENT_NAME = "journey_counterfactual_replay_capture"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _capture_events(output_dir: Path) -> tuple[list[Path], list[dict[str, Any]]]:
    logs = sorted((output_dir / "logs").glob("*.jsonl"))
    events: list[dict[str, Any]] = []
    for log_path in logs:
        for row in _read_jsonl(log_path):
            if row.get("event") == EVENT_NAME:
                enriched = dict(row)
                enriched["_log_path"] = str(log_path)
                events.append(enriched)
    return logs, events


def _event_has_no_certificate_effect(event: dict[str, Any]) -> bool:
    return bool(
        event.get("diagnostic_only") is True
        and event.get("replay_no_certificate_effect") is True
        and event.get("certificate_capable") is False
        and event.get("official_bound_effect") is False
    )


def _event_has_complete_active_basis(event: dict[str, Any]) -> bool:
    return bool(
        event.get("active_basis_snapshot_enabled") is True
        and event.get("active_basis_snapshot_complete") is True
        and event.get("active_basis_snapshot_truncated") is False
        and int(event.get("active_basis_payload_count") or 0) > 0
        and int(event.get("active_basis_journey_count") or 0)
        == int(event.get("active_basis_payload_count") or 0)
    )


def _compact_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "log_path": event.get("_log_path"),
        "context_hash": event.get("context_hash"),
        "cg_iter": event.get("cg_iter"),
        "pricing_kind": event.get("pricing_kind"),
        "pricing_state": event.get("pricing_state"),
        "returned_journey_count": event.get("returned_journey_count"),
        "captured_journey_count": event.get("captured_journey_count"),
        "active_basis_journey_count": event.get("active_basis_journey_count"),
        "active_basis_payload_count": event.get("active_basis_payload_count"),
        "active_basis_fractional_journey_count": event.get(
            "active_basis_fractional_journey_count"
        ),
        "active_basis_snapshot_hash": event.get("active_basis_snapshot_hash"),
        "no_certificate_effect": _event_has_no_certificate_effect(event),
        "complete_active_basis": _event_has_complete_active_basis(event),
    }


def audit_capture(*, runbook_path: Path) -> dict[str, Any]:
    runbook = _read_json(runbook_path)
    command_summaries: list[dict[str, Any]] = []
    total_events = 0
    no_certificate_bad_count = 0
    active_basis_bad_count = 0
    expected_total = 0
    expected_hit_count = 0
    expected_complete_hit_count = 0
    output_missing_count = 0
    log_missing_count = 0

    for command in runbook.get("commands", []) or []:
        output_dir = Path(str(command.get("output_dir", "")))
        expected = set(str(item) for item in command.get("expected_context_hashes", []) or [])
        logs, events = _capture_events(output_dir)
        contexts_seen = {str(event.get("context_hash", "")) for event in events}
        complete_contexts_seen = {
            str(event.get("context_hash", ""))
            for event in events
            if _event_has_no_certificate_effect(event)
            and _event_has_complete_active_basis(event)
        }
        missing = sorted(expected - contexts_seen)
        missing_complete = sorted(expected - complete_contexts_seen)
        event_no_cert_bad = [
            event for event in events if not _event_has_no_certificate_effect(event)
        ]
        event_active_bad = [
            event for event in events if not _event_has_complete_active_basis(event)
        ]
        total_events += len(events)
        expected_total += len(expected)
        expected_hit_count += len(expected & contexts_seen)
        expected_complete_hit_count += len(expected & complete_contexts_seen)
        no_certificate_bad_count += len(event_no_cert_bad)
        active_basis_bad_count += len(event_active_bad)
        if not output_dir.exists():
            output_missing_count += 1
        if not logs:
            log_missing_count += 1
        command_summaries.append(
            {
                "command_id": command.get("command_id"),
                "instance": command.get("instance"),
                "profile": command.get("profile"),
                "output_dir": str(output_dir),
                "output_exists": output_dir.exists(),
                "log_count": len(logs),
                "capture_event_count": len(events),
                "expected_context_hashes": sorted(expected),
                "hit_context_hashes": sorted(expected & contexts_seen),
                "complete_hit_context_hashes": sorted(
                    expected & complete_contexts_seen
                ),
                "missing_context_hashes": missing,
                "missing_complete_context_hashes": missing_complete,
                "no_certificate_bad_count": len(event_no_cert_bad),
                "active_basis_bad_count": len(event_active_bad),
                "sample_events": [_compact_event(event) for event in events[:5]],
            }
        )

    all_expected_contexts_hit = bool(
        expected_total > 0 and expected_hit_count == expected_total
    )
    all_expected_contexts_have_complete_snapshot = bool(
        expected_total > 0 and expected_complete_hit_count == expected_total
    )
    checks = {
        "runbook_passed": runbook.get("all_checks_pass") is True,
        "has_commands": bool(runbook.get("commands")),
        "all_command_outputs_exist": output_missing_count == 0,
        "all_commands_have_logs": log_missing_count == 0,
        "has_capture_events": total_events > 0,
        "all_capture_events_no_certificate_effect": no_certificate_bad_count == 0,
        "all_capture_events_have_complete_active_basis": active_basis_bad_count == 0,
        "audit_generation_does_not_run_bpc_or_pricing": True,
    }
    ready_for_selector_holdout = bool(
        all(checks.values())
        and all_expected_contexts_hit
        and all_expected_contexts_have_complete_snapshot
    )
    return {
        "schema_version": "root_cause_selector_holdout_collection_capture_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_collection_capture_audited",
        "source_runbook": str(runbook_path),
        "command_count": len(command_summaries),
        "output_missing_count": output_missing_count,
        "log_missing_count": log_missing_count,
        "capture_event_count": total_events,
        "expected_context_hash_count": expected_total,
        "expected_context_hit_count": expected_hit_count,
        "expected_context_complete_hit_count": expected_complete_hit_count,
        "missing_expected_context_count": expected_total - expected_hit_count,
        "missing_expected_complete_context_count": (
            expected_total - expected_complete_hit_count
        ),
        "no_certificate_bad_count": no_certificate_bad_count,
        "active_basis_bad_count": active_basis_bad_count,
        "all_expected_contexts_hit": all_expected_contexts_hit,
        "all_expected_contexts_have_complete_snapshot": (
            all_expected_contexts_have_complete_snapshot
        ),
        "ready_for_selector_holdout": ready_for_selector_holdout,
        "command_summaries": command_summaries,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "该审计只检查已执行 runbook 的 capture 输出是否满足"
            " no-certificate-effect active-basis snapshot 采集契约。"
            "如果 expected context 未全部命中，则还不能进入 selector holdout，"
            "但这不是 official solver 结果变化。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout Collection Capture Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告审计 selector holdout collection runbook 的实际采集输出。它只读",
        " JSONL/summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker、",
        "certificate 或 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_holdout_collection_capture_audit = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"command_count = {summary['command_count']}",
        f"capture_event_count = {summary['capture_event_count']}",
        f"expected_context_hash_count = {summary['expected_context_hash_count']}",
        f"expected_context_hit_count = {summary['expected_context_hit_count']}",
        "all_expected_contexts_hit = "
        f"{str(summary['all_expected_contexts_hit']).lower()}",
        "all_expected_contexts_have_complete_snapshot = "
        f"{str(summary['all_expected_contexts_have_complete_snapshot']).lower()}",
        f"ready_for_selector_holdout = {str(summary['ready_for_selector_holdout']).lower()}",
        f"no_certificate_bad_count = {summary['no_certificate_bad_count']}",
        f"active_basis_bad_count = {summary['active_basis_bad_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Command summaries",
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
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    summary = audit_capture(runbook_path=Path(args.runbook))
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
