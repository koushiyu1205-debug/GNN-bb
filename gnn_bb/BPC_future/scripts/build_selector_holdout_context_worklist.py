#!/usr/bin/env python3
"""Build a machine-checkable selector holdout context worklist.

This diagnostic-only helper merges priority context gaps, collection runbooks,
capture audits, and capture-miss diagnostics into a concrete next-data
worklist.  It does not run BPC, pricing, RMP, Pulse, workers, replay,
certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_TARGET_PRIORITY = Path(
    "BPC_future/results/root_cause_selector_holdout_target_priority_matrix_20260614/"
    "summary.json"
)
DEFAULT_COLLECTION_MANIFEST = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_manifest_20260614/"
    "summary.json"
)
DEFAULT_COLLECTION_RUNBOOK = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_runbook_20260614/"
    "summary.json"
)
DEFAULT_COLLECTION_CAPTURE_AUDIT = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_RUNBOOK = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_collection_runbook_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_CAPTURE_AUDIT = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_audit_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_CAPTURE_MISS = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_capture_miss_20260614/"
    "summary.json"
)
DEFAULT_NEXT_ACTION = Path(
    "BPC_future/results/root_cause_next_action_plan_20260614/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_context_worklist_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_context_worklist_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _set_from_list(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(value) for value in values if str(value)}


def _runbook_context_map(runbook: dict[str, Any]) -> dict[str, dict[str, Any]]:
    context_map: dict[str, dict[str, Any]] = {}
    for command in runbook.get("commands") or []:
        command_id = str(command.get("command_id") or "")
        for context_hash in command.get("expected_context_hashes") or []:
            context_map[str(context_hash)] = {
                "command_id": command_id,
                "instance": command.get("instance"),
                "profile": command.get("profile"),
                "source_config_class": command.get("source_config_class"),
                "pricing_time_limit": command.get("pricing_time_limit"),
                "pricing_max_dp_states": command.get("pricing_max_dp_states"),
                "repeat_count": command.get("repeat_count"),
                "time_limit": command.get("time_limit"),
            }
    return context_map


def _capture_hit_sets(capture_audit: dict[str, Any]) -> dict[str, set[str]]:
    hits: set[str] = set()
    complete_hits: set[str] = set()
    expected: set[str] = set()
    observed: set[str] = set()
    for command in capture_audit.get("command_summaries") or []:
        hits.update(_set_from_list(command.get("hit_context_hashes")))
        complete_hits.update(_set_from_list(command.get("complete_hit_context_hashes")))
        expected.update(_set_from_list(command.get("expected_context_hashes")))
        for event in command.get("sample_events") or []:
            context_hash = str(event.get("context_hash") or "")
            if context_hash:
                observed.add(context_hash)
    return {
        "hits": hits,
        "complete_hits": complete_hits,
        "expected": expected,
        "observed": observed,
    }


def _manifest_context_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    context_map: dict[str, dict[str, Any]] = {}
    for target in manifest.get("targets") or []:
        context_hash = str(target.get("context_hash") or "")
        if not context_hash:
            continue
        context_map[context_hash] = {
            "collection_target_id": target.get("collection_target_id"),
            "failure_kind": target.get("failure_kind"),
            "candidate_row_count": target.get("candidate_row_count"),
            "candidate_label_counts": target.get("candidate_label_counts"),
            "needs_active_basis_snapshot_capture": target.get(
                "needs_active_basis_snapshot_capture"
            ),
            "candidate_source_file_count": target.get("candidate_source_file_count"),
        }
    return context_map


def _priority_miss_map(priority_miss: dict[str, Any]) -> dict[str, dict[str, Any]]:
    miss_map: dict[str, dict[str, Any]] = {}
    for command in priority_miss.get("command_summaries") or []:
        command_id = str(command.get("command_id") or "")
        for comparison in command.get("comparisons") or []:
            context_hash = str(comparison.get("context_hash") or "")
            if not context_hash:
                continue
            source = comparison.get("source_event") or {}
            miss_map[context_hash] = {
                "priority_command_id": command_id,
                "miss_class": comparison.get("miss_class"),
                "exact_hit_count": comparison.get("exact_hit_count"),
                "same_active_event_count": comparison.get("same_active_event_count"),
                "same_cg_iter_event_count": comparison.get(
                    "same_cg_iter_event_count"
                ),
                "source_active_hash": source.get("active_hash_before"),
                "source_cg_iter": source.get("cg_iter"),
                "source_pricing_state": source.get("pricing_state"),
                "source_returned_journey_count": source.get(
                    "returned_journey_count"
                ),
            }
    return miss_map


def _priority_runbook_contexts(
    priority_runbook: dict[str, Any],
) -> tuple[set[str], set[str]]:
    commandable = _set_from_list(priority_runbook.get("commandable_contexts"))
    unsupported = _set_from_list(priority_runbook.get("unsupported_contexts"))
    for row in priority_runbook.get("target_profile_rows") or []:
        context_hash = str(row.get("context_hash") or "")
        if not context_hash:
            continue
        if _as_int(row.get("commandable_source_file_count")) > 0:
            commandable.add(context_hash)
        if row.get("unsupported_reason_counts"):
            unsupported.add(context_hash)
    return commandable, unsupported


def _recommend_action(
    *,
    context_hash: str,
    basic_complete: bool,
    priority_complete: bool,
    manifest_present: bool,
    priority_commandable: bool,
    priority_unsupported: bool,
    miss_class: str,
    gap_tags: list[str],
) -> str:
    if basic_complete or priority_complete:
        if any("noop" in tag or "mixed" in tag for tag in gap_tags):
            return "use_as_complete_snapshot_row_then_replay_label_if_needed"
        return "covered_by_existing_complete_capture"
    if miss_class == "same_active_but_returned_batch_or_component_drift":
        return "treat_current_rerun_as_near_miss_and_target_full_component_match"
    if miss_class == "source_active_hash_not_reached":
        return "do_not_repeat_same_source_profile_blindly_collect_trajectory_variants"
    if priority_commandable:
        return "run_priority_context_trajectory_capture_with_full_component_audit"
    if manifest_present:
        return "run_existing_collection_manifest_command_and_audit_exact_components"
    if priority_unsupported:
        return "unsupported_until_source_profile_or_instance_mapping_is_recovered"
    return "needs_new_source_profile_mapping_before_capture"


def build_summary(
    *,
    target_priority_path: Path,
    collection_manifest_path: Path,
    collection_runbook_path: Path,
    collection_capture_audit_path: Path,
    priority_runbook_path: Path,
    priority_capture_audit_path: Path,
    priority_capture_miss_path: Path,
    next_action_path: Path,
) -> dict[str, Any]:
    target_priority = _read_json(target_priority_path)
    manifest = _read_json(collection_manifest_path)
    collection_runbook = _read_json(collection_runbook_path)
    collection_capture = _read_json(collection_capture_audit_path)
    priority_runbook = _read_json(priority_runbook_path)
    priority_capture = _read_json(priority_capture_audit_path)
    priority_miss = _read_json(priority_capture_miss_path)
    next_action = _read_json(next_action_path)

    manifest_map = _manifest_context_map(manifest)
    collection_runbook_map = _runbook_context_map(collection_runbook)
    priority_runbook_map = _runbook_context_map(priority_runbook)
    collection_hits = _capture_hit_sets(collection_capture)
    priority_hits = _capture_hit_sets(priority_capture)
    miss_map = _priority_miss_map(priority_miss)
    priority_commandable, priority_unsupported = _priority_runbook_contexts(
        priority_runbook
    )

    rows: list[dict[str, Any]] = []
    for target in target_priority.get("top_priority_targets") or []:
        context_hash = str(target.get("context_hash") or "")
        if not context_hash:
            continue
        gap_tags = [str(tag) for tag in target.get("gap_tags") or []]
        miss = miss_map.get(context_hash, {})
        manifest_info = manifest_map.get(context_hash, {})
        basic_complete = context_hash in collection_hits["complete_hits"]
        priority_complete = context_hash in priority_hits["complete_hits"]
        row = {
            "context_hash": context_hash,
            "priority_score": target.get("priority_score"),
            "row_count": target.get("row_count"),
            "label_counts": target.get("label_counts"),
            "gap_tags": gap_tags,
            "complete_snapshot_row_count": target.get("complete_snapshot_row_count"),
            "explicit_forbidden_row_count": target.get(
                "explicit_forbidden_row_count"
            ),
            "manifest_target_id": manifest_info.get("collection_target_id"),
            "manifest_failure_kind": manifest_info.get("failure_kind"),
            "manifest_candidate_label_counts": manifest_info.get(
                "candidate_label_counts"
            ),
            "collection_runbook_command_id": collection_runbook_map.get(
                context_hash, {}
            ).get("command_id"),
            "priority_runbook_command_id": priority_runbook_map.get(
                context_hash, {}
            ).get("command_id"),
            "basic_capture_hit": context_hash in collection_hits["hits"],
            "basic_capture_complete_hit": basic_complete,
            "priority_capture_hit": context_hash in priority_hits["hits"],
            "priority_capture_complete_hit": priority_complete,
            "priority_commandable": context_hash in priority_commandable,
            "priority_unsupported": context_hash in priority_unsupported,
            "priority_miss_class": miss.get("miss_class"),
            "priority_same_active_event_count": miss.get("same_active_event_count"),
            "priority_same_cg_iter_event_count": miss.get("same_cg_iter_event_count"),
            "source_active_hash": miss.get("source_active_hash"),
            "source_cg_iter": miss.get("source_cg_iter"),
            "recommended_action": _recommend_action(
                context_hash=context_hash,
                basic_complete=basic_complete,
                priority_complete=priority_complete,
                manifest_present=bool(manifest_info),
                priority_commandable=context_hash in priority_commandable,
                priority_unsupported=context_hash in priority_unsupported,
                miss_class=str(miss.get("miss_class") or ""),
                gap_tags=gap_tags,
            ),
        }
        rows.append(row)

    status_counts: dict[str, int] = {}
    for row in rows:
        status_counts[row["recommended_action"]] = (
            status_counts.get(row["recommended_action"], 0) + 1
        )
    priority_miss_class_counts: dict[str, int] = {}
    for row in rows:
        miss_class = row.get("priority_miss_class") or ""
        if miss_class:
            priority_miss_class_counts[str(miss_class)] = (
                priority_miss_class_counts.get(str(miss_class), 0) + 1
            )

    not_complete_rows = [
        row
        for row in rows
        if not row["basic_capture_complete_hit"]
        and not row["priority_capture_complete_hit"]
    ]
    actionable_rows = [
        row
        for row in not_complete_rows
        if row["recommended_action"]
        not in {
            "covered_by_existing_complete_capture",
            "use_as_complete_snapshot_row_then_replay_label_if_needed",
        }
    ]

    checks = {
        "target_priority_passed": target_priority.get("all_checks_pass") is True,
        "collection_manifest_passed": manifest.get("all_checks_pass") is True,
        "collection_runbook_passed": collection_runbook.get("all_checks_pass") is True,
        "collection_capture_passed": collection_capture.get("all_checks_pass") is True,
        "priority_runbook_passed": priority_runbook.get("all_checks_pass") is True,
        "priority_capture_passed": priority_capture.get("all_checks_pass") is True,
        "priority_miss_passed": priority_miss.get("all_checks_pass") is True,
        "next_action_passed": next_action.get("all_checks_pass") is True,
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "has_priority_rows": bool(rows),
        "has_unresolved_contexts": bool(not_complete_rows),
        "has_component_drift_or_active_miss": any(
            row.get("priority_miss_class")
            in {
                "same_active_but_returned_batch_or_component_drift",
                "source_active_hash_not_reached",
            }
            for row in rows
        ),
        "same_profile_rerun_not_sufficient": (
            _as_int(priority_miss.get("expected_context_count")) > 0
            and _as_int(priority_miss.get("exact_hit_context_count")) == 0
        ),
        "production_direction_still_unproven": (
            next_action.get("production_direction_proven") is False
            and next_action.get("goal_complete") is False
        ),
    }

    return {
        "schema_version": "selector_holdout_context_worklist_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_context_worklist_ready",
        "row_count": len(rows),
        "unresolved_context_count": len(not_complete_rows),
        "actionable_context_count": len(actionable_rows),
        "recommended_action_counts": status_counts,
        "priority_miss_class_counts": priority_miss_class_counts,
        "rows": rows,
        "top_actionable_contexts": actionable_rows[:8],
        "sources": {
            "target_priority": str(target_priority_path),
            "collection_manifest": str(collection_manifest_path),
            "collection_runbook": str(collection_runbook_path),
            "collection_capture_audit": str(collection_capture_audit_path),
            "priority_runbook": str(priority_runbook_path),
            "priority_capture_audit": str(priority_capture_audit_path),
            "priority_capture_miss": str(priority_capture_miss_path),
            "next_action": str(next_action_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "Priority selector holdout gaps are actionable only through full "
            "component-aware context capture.  Existing complete hits can seed replay, "
            "but rerun-missed or unsupported contexts cannot be closed by blind "
            "source-profile reruns; they require trajectory/component targeting or "
            "source-profile recovery."
        ),
    }


CSV_FIELDS = [
    "context_hash",
    "priority_score",
    "row_count",
    "label_counts",
    "gap_tags",
    "manifest_target_id",
    "collection_runbook_command_id",
    "priority_runbook_command_id",
    "basic_capture_complete_hit",
    "priority_capture_complete_hit",
    "priority_commandable",
    "priority_unsupported",
    "priority_miss_class",
    "priority_same_active_event_count",
    "priority_same_cg_iter_event_count",
    "recommended_action",
]


def write_csv(summary: dict[str, Any], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for row in summary["rows"]:
            out = {field: row.get(field) for field in CSV_FIELDS}
            out["label_counts"] = json.dumps(
                out["label_counts"], ensure_ascii=False, sort_keys=True
            )
            out["gap_tags"] = json.dumps(out["gap_tags"], ensure_ascii=False)
            writer.writerow(out)


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout Context Worklist 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把 priority context gap、runbook、capture audit 与 capture-miss",
        "诊断合并成下一轮 selector holdout 数据补齐 worklist。它只读已有",
        "summary，不运行 BPC / pricing / RMP / Pulse / worker，不改变 certificate",
        "或 solver 默认行为。",
        "",
        "```text",
        "root_cause_selector_holdout_context_worklist = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"row_count = {summary['row_count']}",
        f"unresolved_context_count = {summary['unresolved_context_count']}",
        f"actionable_context_count = {summary['actionable_context_count']}",
        "same_profile_rerun_not_sufficient = "
        f"{str(summary['checks']['same_profile_rerun_not_sufficient']).lower()}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Recommended Action Counts",
        "",
        "```json",
        json.dumps(
            summary["recommended_action_counts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Priority Miss Class Counts",
        "",
        "```json",
        json.dumps(
            summary["priority_miss_class_counts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Top Actionable Contexts",
        "",
        "```json",
        json.dumps(
            summary["top_actionable_contexts"],
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
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-priority", type=Path, default=DEFAULT_TARGET_PRIORITY)
    parser.add_argument(
        "--collection-manifest", type=Path, default=DEFAULT_COLLECTION_MANIFEST
    )
    parser.add_argument(
        "--collection-runbook", type=Path, default=DEFAULT_COLLECTION_RUNBOOK
    )
    parser.add_argument(
        "--collection-capture-audit",
        type=Path,
        default=DEFAULT_COLLECTION_CAPTURE_AUDIT,
    )
    parser.add_argument("--priority-runbook", type=Path, default=DEFAULT_PRIORITY_RUNBOOK)
    parser.add_argument(
        "--priority-capture-audit",
        type=Path,
        default=DEFAULT_PRIORITY_CAPTURE_AUDIT,
    )
    parser.add_argument(
        "--priority-capture-miss",
        type=Path,
        default=DEFAULT_PRIORITY_CAPTURE_MISS,
    )
    parser.add_argument("--next-action", type=Path, default=DEFAULT_NEXT_ACTION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        target_priority_path=args.target_priority,
        collection_manifest_path=args.collection_manifest,
        collection_runbook_path=args.collection_runbook,
        collection_capture_audit_path=args.collection_capture_audit,
        priority_runbook_path=args.priority_runbook,
        priority_capture_audit_path=args.priority_capture_audit,
        priority_capture_miss_path=args.priority_capture_miss,
        next_action_path=args.next_action,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    csv_path = args.output_dir / "context_worklist.csv"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(summary, csv_path)
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
