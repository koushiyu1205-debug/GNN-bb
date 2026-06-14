#!/usr/bin/env python3
"""Audit target002 same-active trajectory branch differences.

This read-only diagnostic compares capture events that share the target
active-task-set hash but differ in exact context hash.  The goal is to explain
the remaining target002 holdout gap at the returned-batch / pool / forbidden
signature level, without running BPC or changing solver behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EVENT_NAME = "journey_counterfactual_replay_capture"
TARGET_CONTEXT_HASH = "3f914a0d2b97fd27"
TARGET_ACTIVE_HASH = "f0b96be45c5015c9"

DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_target002_trajectory_branch_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_target002_trajectory_branch_zh.md"
)

LOG_GROUPS = [
    {
        "group_id": "historical_source",
        "log_dir": Path("BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs"),
        "log_glob": "*.jsonl",
    },
    {
        "group_id": "config_matched_active_basis_capture",
        "log_dir": Path(
            "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/"
            "002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000"
            "__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs"
        ),
        "log_glob": "*.jsonl",
    },
    {
        "group_id": "no_active_basis_capture",
        "log_dir": Path(
            "BPC_future/results/root_cause_selector_holdout_target002_no_active_basis_probe_20260614/logs"
        ),
        "log_glob": "*.jsonl",
    },
    {
        "group_id": "alias_instance_capture",
        "log_dir": Path(
            "BPC_future/results/root_cause_selector_holdout_target002_alias_probe_20260614/logs"
        ),
        "log_glob": "*.jsonl",
    },
    {
        "group_id": "multi_profile_order_capture",
        "log_dir": Path(
            "BPC_future/results/root_cause_selector_holdout_target002_multi_profile_order_probe_20260614/logs"
        ),
        "log_glob": "*experimental_early_new_task_set_quota_3_20_only*.jsonl",
    },
]


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


def _events(group: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for log_path in sorted(Path(group["log_dir"]).glob(str(group["log_glob"]))):
        for row in _read_jsonl(log_path):
            if row.get("event") != EVENT_NAME:
                continue
            event = dict(row)
            event["_group_id"] = group["group_id"]
            event["_log_path"] = str(log_path)
            event["_repeat"] = log_path.stem.rsplit("__r", 1)[-1] if "__r" in log_path.stem else ""
            rows.append(event)
    return rows


def _task_set_key(journey: dict[str, Any]) -> tuple[int, ...]:
    raw = journey.get("task_set") or []
    return tuple(sorted(int(task) for task in raw))


def _sequence_key(journey: dict[str, Any]) -> tuple[tuple[int, ...], ...]:
    sequence = journey.get("sequence") or []
    return tuple(tuple(int(task) for task in sortie) for sortie in sequence)


def _returned_summary(event: dict[str, Any]) -> dict[str, Any]:
    journeys = [j for j in (event.get("returned_journeys") or []) if isinstance(j, dict)]
    ordered_task_sets = [_task_set_key(journey) for journey in journeys]
    ordered_sequences = [_sequence_key(journey) for journey in journeys]
    true_rcs = [journey.get("true_reduced_cost") for journey in journeys]
    costs = [journey.get("cost") for journey in journeys]
    return {
        "returned_journey_count": event.get("returned_journey_count"),
        "captured_journey_count": event.get("captured_journey_count"),
        "returned_batch_complete": event.get("returned_batch_complete"),
        "returned_batch_truncated": event.get("returned_batch_truncated"),
        "ordered_task_sets": [list(key) for key in ordered_task_sets],
        "ordered_sequences": [[list(sortie) for sortie in key] for key in ordered_sequences],
        "task_set_set": [list(key) for key in sorted(set(ordered_task_sets))],
        "sequence_set": [
            [list(sortie) for sortie in key] for key in sorted(set(ordered_sequences))
        ],
        "true_reduced_costs": true_rcs,
        "costs": costs,
    }


def _compact_event(event: dict[str, Any]) -> dict[str, Any]:
    returned = _returned_summary(event)
    return {
        "group_id": event.get("_group_id"),
        "repeat": event.get("_repeat"),
        "cg_iter": event.get("cg_iter"),
        "context_hash": event.get("context_hash"),
        "active_hash_before": event.get("active_hash_before"),
        "rmp_objective_before": event.get("rmp_objective_before"),
        "pricing_state": event.get("pricing_state"),
        "pricing_best_reduced_cost": event.get("pricing_best_reduced_cost"),
        "pool_journey_count": event.get("pool_journey_count"),
        "pool_signature_hash": event.get("pool_signature_hash"),
        "forbidden_signature_hash": event.get("forbidden_signature_hash"),
        "pool_task_set_hash": event.get("pool_task_set_hash"),
        "returned": returned,
    }


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _compare_to_source(source: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    source_returned = _returned_summary(source)
    event_returned = _returned_summary(event)
    source_task_set_set = {tuple(items) for items in source_returned["task_set_set"]}
    event_task_set_set = {tuple(items) for items in event_returned["task_set_set"]}
    source_sequences = {
        tuple(tuple(sortie) for sortie in sequence)
        for sequence in source_returned["sequence_set"]
    }
    event_sequences = {
        tuple(tuple(sortie) for sortie in sequence)
        for sequence in event_returned["sequence_set"]
    }
    source_obj = _as_float(source.get("rmp_objective_before"))
    event_obj = _as_float(event.get("rmp_objective_before"))
    objective_delta = (
        None if source_obj is None or event_obj is None else round(event_obj - source_obj, 9)
    )
    return {
        "group_id": event.get("_group_id"),
        "repeat": event.get("_repeat"),
        "cg_iter": event.get("cg_iter"),
        "context_hash": event.get("context_hash"),
        "same_context_hash": event.get("context_hash") == source.get("context_hash"),
        "same_active_hash": event.get("active_hash_before") == source.get("active_hash_before"),
        "same_pool_signature_hash": event.get("pool_signature_hash")
        == source.get("pool_signature_hash"),
        "same_forbidden_signature_hash": event.get("forbidden_signature_hash")
        == source.get("forbidden_signature_hash"),
        "same_pool_task_set_hash": event.get("pool_task_set_hash")
        == source.get("pool_task_set_hash"),
        "same_returned_count": event.get("returned_journey_count")
        == source.get("returned_journey_count"),
        "same_returned_task_set_set": source_task_set_set == event_task_set_set,
        "same_returned_sequence_set": source_sequences == event_sequences,
        "source_only_task_sets": [list(key) for key in sorted(source_task_set_set - event_task_set_set)],
        "event_only_task_sets": [list(key) for key in sorted(event_task_set_set - source_task_set_set)],
        "objective_delta_vs_source": objective_delta,
        "source_rmp_objective_before": source.get("rmp_objective_before"),
        "event_rmp_objective_before": event.get("rmp_objective_before"),
        "source_pricing_best_reduced_cost": source.get("pricing_best_reduced_cost"),
        "event_pricing_best_reduced_cost": event.get("pricing_best_reduced_cost"),
    }


def audit() -> dict[str, Any]:
    all_events: list[dict[str, Any]] = []
    for group in LOG_GROUPS:
        all_events.extend(_events(group))
    target_events = [
        event for event in all_events if event.get("context_hash") == TARGET_CONTEXT_HASH
    ]
    source_target_events = [
        event
        for event in target_events
        if event.get("_group_id") == "historical_source"
    ]
    source_target = source_target_events[0] if source_target_events else {}
    same_active_events = [
        event for event in all_events if event.get("active_hash_before") == TARGET_ACTIVE_HASH
    ]
    non_source_same_active = [
        event
        for event in same_active_events
        if not (
            event.get("_group_id") == "historical_source"
            and event.get("context_hash") == TARGET_CONTEXT_HASH
        )
    ]
    comparisons = (
        [_compare_to_source(source_target, event) for event in non_source_same_active]
        if source_target
        else []
    )
    checks = {
        "source_target_event_exists": bool(source_target),
        "same_active_events_exist": len(same_active_events) > 1,
        "non_source_same_active_events_exist": bool(non_source_same_active),
        "no_non_source_event_matches_target_context": all(
            event.get("context_hash") != TARGET_CONTEXT_HASH
            for event in non_source_same_active
        ),
        "same_active_has_pool_or_forbidden_signature_drift": any(
            comparison["same_active_hash"]
            and (
                not comparison["same_pool_signature_hash"]
                or not comparison["same_forbidden_signature_hash"]
            )
            for comparison in comparisons
        ),
        "same_active_has_objective_or_batch_drift": any(
            comparison["objective_delta_vs_source"] not in (None, 0.0)
            or not comparison["same_returned_count"]
            or not comparison["same_returned_task_set_set"]
            for comparison in comparisons
        ),
    }
    return {
        "schema_version": "root_cause_selector_holdout_target002_trajectory_branch_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_target002_trajectory_branch_audited",
        "target_context_hash": TARGET_CONTEXT_HASH,
        "target_active_hash": TARGET_ACTIVE_HASH,
        "source_target_event": _compact_event(source_target) if source_target else {},
        "same_active_event_count": len(same_active_events),
        "non_source_same_active_event_count": len(non_source_same_active),
        "same_active_context_hashes": sorted(
            {str(event.get("context_hash")) for event in same_active_events if event.get("context_hash")}
        ),
        "non_source_same_active_events": [_compact_event(event) for event in non_source_same_active],
        "comparisons_to_source": comparisons,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "target002 的目标 active hash 可以在多个 probe 中再次到达，但 exact "
            "context hash 没有复现。same-active 对比显示 pool/forbidden signature、"
            "RMP objective 或 returned batch composition 会分叉；因此 active-task-set "
            "相同并不足以确定后续 pricing universe，production selector 需要更完整的 "
            "pool/forbidden/RMP trajectory 前置上下文。"
        ),
    }


def write_report(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout target002 Trajectory Branch 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只读 target002 source/probe 日志，比较同一 active hash 附近的",
        " exact context 分叉。它不运行 BPC / pricing / RMP / Pulse，也不改变",
        " worker、certificate 或 solver 默认行为。",
        "",
        "## 机器字段",
        "",
        "```text",
        "root_cause_selector_holdout_target002_trajectory_branch = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"target_context_hash = {summary['target_context_hash']}",
        f"target_active_hash = {summary['target_active_hash']}",
        f"same_active_event_count = {summary['same_active_event_count']}",
        "non_source_same_active_event_count = "
        f"{summary['non_source_same_active_event_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Same-active Contexts",
        "",
        "```json",
        json.dumps(
            summary["same_active_context_hashes"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Comparisons To Source",
        "",
        "```json",
        json.dumps(
            summary["comparisons_to_source"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Checks",
        "",
        "```json",
        json.dumps(summary["checks"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
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
