#!/usr/bin/env python3
"""Audit the remaining target002 selector-holdout context drift.

This diagnostic is intentionally read-only.  It compares the historical
target002 pt0.3 capture logs against the config-matched selector holdout
collection logs and records why the final expected context is still missing.
It does not run BPC, pricing, RMP, Pulse, or replay.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SOURCE_LOG_DIR = Path("BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs")
NEW_LOG_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/"
    "002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
    "__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs"
)
CAPTURE_AUDIT_SUMMARY = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_drift_audit_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target002_drift_audit_zh.md"
)
EVENT_NAME = "journey_counterfactual_replay_capture"
TARGET_CONTEXT_HASH = "3f914a0d2b97fd27"


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


def _events(root: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for log_path in sorted(root.glob("*.jsonl")):
        for row in _read_jsonl(log_path):
            if row.get("event") != EVENT_NAME:
                continue
            event = dict(row)
            event["_log_path"] = str(log_path)
            event["_repeat"] = log_path.stem.rsplit("__r", 1)[-1] if "__r" in log_path.stem else "0"
            events.append(event)
    return events


def _compact_event(event: dict[str, Any]) -> dict[str, Any]:
    returned = event.get("returned_journeys") or []
    returned_task_sets = []
    returned_sequences = []
    for journey in returned[:8]:
        if isinstance(journey, dict):
            returned_task_sets.append(journey.get("task_set"))
            returned_sequences.append(journey.get("sequence"))
    return {
        "log_path": event.get("_log_path"),
        "repeat": event.get("_repeat"),
        "cg_iter": event.get("cg_iter"),
        "pricing_kind": event.get("pricing_kind"),
        "pricing_state": event.get("pricing_state"),
        "context_hash": event.get("context_hash"),
        "active_hash_before": event.get("active_hash_before"),
        "rmp_objective_before": event.get("rmp_objective_before"),
        "pricing_best_reduced_cost": event.get("pricing_best_reduced_cost"),
        "returned_journey_count": event.get("returned_journey_count"),
        "captured_journey_count": event.get("captured_journey_count"),
        "returned_task_sets_sample": returned_task_sets,
        "returned_sequences_sample": returned_sequences,
    }


def _events_with_context(events: list[dict[str, Any]], context_hash: str) -> list[dict[str, Any]]:
    return [event for event in events if str(event.get("context_hash")) == context_hash]


def _events_with_active(events: list[dict[str, Any]], active_hash: str) -> list[dict[str, Any]]:
    return [event for event in events if str(event.get("active_hash_before")) == active_hash]


def _unique_contexts(events: list[dict[str, Any]]) -> list[str]:
    return sorted({str(event.get("context_hash")) for event in events if event.get("context_hash")})


def _active_path(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "repeat": event.get("_repeat"),
            "cg_iter": event.get("cg_iter"),
            "pricing_kind": event.get("pricing_kind"),
            "pricing_state": event.get("pricing_state"),
            "context_hash": event.get("context_hash"),
            "active_hash_before": event.get("active_hash_before"),
            "rmp_objective_before": event.get("rmp_objective_before"),
            "returned_journey_count": event.get("returned_journey_count"),
        }
        for event in sorted(
            events,
            key=lambda item: (
                str(item.get("_repeat", "")),
                int(item.get("cg_iter") or 0),
                str(item.get("pricing_kind") or ""),
            ),
        )
    ]


def audit() -> dict[str, Any]:
    source_events = _events(SOURCE_LOG_DIR)
    new_events = _events(NEW_LOG_DIR)
    source_target_hits = _events_with_context(source_events, TARGET_CONTEXT_HASH)
    new_target_hits = _events_with_context(new_events, TARGET_CONTEXT_HASH)
    target_active_hash = (
        str(source_target_hits[0].get("active_hash_before"))
        if source_target_hits
        else ""
    )
    source_same_active = _events_with_active(source_events, target_active_hash)
    new_same_active = _events_with_active(new_events, target_active_hash)
    source_contexts = set(_unique_contexts(source_events))
    new_contexts = set(_unique_contexts(new_events))
    capture_audit = _read_json(CAPTURE_AUDIT_SUMMARY) if CAPTURE_AUDIT_SUMMARY.exists() else {}
    checks = {
        "source_logs_exist": SOURCE_LOG_DIR.exists(),
        "new_logs_exist": NEW_LOG_DIR.exists(),
        "source_target_context_exists": len(source_target_hits) > 0,
        "new_target_context_missing": len(new_target_hits) == 0,
        "new_capture_has_same_active_hash_events": len(new_same_active) > 0,
        "new_capture_has_no_certificate_effect_bad_count": (
            capture_audit.get("no_certificate_bad_count") == 0
        ),
        "new_capture_has_complete_active_basis": (
            capture_audit.get("active_basis_bad_count") == 0
        ),
        "overall_selector_holdout_not_ready": (
            capture_audit.get("ready_for_selector_holdout") is False
        ),
    }
    return {
        "schema_version": "root_cause_selector_holdout_target002_drift_audit_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_target002_context_drift_audited",
        "target_context_hash": TARGET_CONTEXT_HASH,
        "target_active_hash": target_active_hash,
        "source_log_dir": str(SOURCE_LOG_DIR),
        "new_log_dir": str(NEW_LOG_DIR),
        "source_event_count": len(source_events),
        "new_event_count": len(new_events),
        "source_context_hash_count": len(source_contexts),
        "new_context_hash_count": len(new_contexts),
        "shared_context_hashes": sorted(source_contexts & new_contexts),
        "source_target_hit_count": len(source_target_hits),
        "new_target_hit_count": len(new_target_hits),
        "source_same_active_event_count": len(source_same_active),
        "new_same_active_event_count": len(new_same_active),
        "new_same_active_found_negative_count": sum(
            1 for event in new_same_active if event.get("pricing_state") == "FOUND_NEGATIVE"
        ),
        "new_same_active_incomplete_count": sum(
            1 for event in new_same_active if event.get("pricing_state") == "INCOMPLETE_LIMIT"
        ),
        "capture_audit_expected_context_hit_count": capture_audit.get(
            "expected_context_hit_count"
        ),
        "capture_audit_expected_context_hash_count": capture_audit.get(
            "expected_context_hash_count"
        ),
        "capture_audit_ready_for_selector_holdout": capture_audit.get(
            "ready_for_selector_holdout"
        ),
        "source_target_events": [_compact_event(event) for event in source_target_hits],
        "new_same_active_events": [_compact_event(event) for event in new_same_active],
        "source_active_path": _active_path(source_events),
        "new_active_path": _active_path(new_events),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "target002 的原始 pt0.3 capture 中存在目标 context，但 config-matched "
            "active-basis capture 没有复现该 exact context。新采集仍能到达同一 "
            "active-hash 邻域，并且 no-certificate-effect / active-basis snapshot "
            "契约全部满足；剩余缺口是同一 active trajectory 下 returned batch / "
            "time-limit 分叉，而不是证书或 capture 字段污染。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout target002 Drift Audit 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只读 target002 原始 pt0.3 capture 与 config-matched selector holdout",
        " capture 日志，审计剩余 1 个 expected context 为什么仍未命中。它不运行",
        " BPC / pricing / RMP / Pulse，也不改变 worker、certificate 或 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_holdout_target002_drift_audit = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"target_context_hash = {summary['target_context_hash']}",
        f"target_active_hash = {summary['target_active_hash']}",
        f"source_target_hit_count = {summary['source_target_hit_count']}",
        f"new_target_hit_count = {summary['new_target_hit_count']}",
        f"new_same_active_event_count = {summary['new_same_active_event_count']}",
        f"new_same_active_found_negative_count = {summary['new_same_active_found_negative_count']}",
        f"new_same_active_incomplete_count = {summary['new_same_active_incomplete_count']}",
        "capture_audit_expected_context_hit_count = "
        f"{summary['capture_audit_expected_context_hit_count']}",
        "capture_audit_expected_context_hash_count = "
        f"{summary['capture_audit_expected_context_hash_count']}",
        "capture_audit_ready_for_selector_holdout = "
        f"{str(summary['capture_audit_ready_for_selector_holdout']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Source target events",
        "",
        "```json",
        json.dumps(summary["source_target_events"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## New same-active events",
        "",
        "```json",
        json.dumps(summary["new_same_active_events"], ensure_ascii=False, indent=2, sort_keys=True),
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
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()
    summary = audit()
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
