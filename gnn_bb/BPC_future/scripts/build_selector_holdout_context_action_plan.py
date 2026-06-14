#!/usr/bin/env python3
"""Build an execution-level action plan for selector holdout contexts.

This diagnostic-only helper turns the selector holdout context worklist into a
machine-checkable action plan.  It records which contexts are already usable as
complete snapshot rows, which unresolved contexts still need full component
matching, and which contexts cannot be collected until their source mapping is
recovered.

It does not run BPC, pricing, RMP, Pulse, workers, replay, certificates, or
benchmarks.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_WORKLIST = Path(
    "BPC_future/results/root_cause_selector_holdout_context_worklist_20260614/"
    "summary.json"
)
DEFAULT_COLLECTION_RUNBOOK = Path(
    "BPC_future/results/root_cause_selector_holdout_collection_runbook_20260614/"
    "summary.json"
)
DEFAULT_PRIORITY_RUNBOOK = Path(
    "BPC_future/results/root_cause_selector_holdout_priority_collection_runbook_20260614/"
    "summary.json"
)
DEFAULT_NEXT_ACTION = Path(
    "BPC_future/results/root_cause_next_action_plan_20260614/summary.json"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_selector_holdout_context_action_plan_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_selector_holdout_context_action_plan_zh.md"
)

EXACT_COMPONENT_GATES = [
    "context_hash",
    "active_hash_before",
    "pool_signature_hash",
    "pool_task_set_hash",
    "forbidden_signature_hash",
    "returned_task_set_hash",
    "rmp_objective_before",
    "pricing_state",
    "pricing_best_reduced_cost",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _command_map(*runbooks: dict[str, Any]) -> dict[str, dict[str, Any]]:
    commands: dict[str, dict[str, Any]] = {}
    for runbook in runbooks:
        for command in runbook.get("commands") or []:
            command_id = str(command.get("command_id") or "")
            if command_id:
                commands[command_id] = command
    return commands


def _row_command_id(row: dict[str, Any]) -> str:
    for key in ("collection_runbook_command_id", "priority_runbook_command_id"):
        value = str(row.get(key) or "")
        if value:
            return value
    return ""


def _execution_category(row: dict[str, Any]) -> str:
    action = str(row.get("recommended_action") or "")
    miss_class = str(row.get("priority_miss_class") or "")
    if action == "use_as_complete_snapshot_row_then_replay_label_if_needed":
        return "complete_snapshot_available"
    if action == "run_existing_collection_manifest_command_and_audit_exact_components":
        return "run_or_reaudit_existing_manifest_command"
    if miss_class == "source_active_hash_not_reached":
        return "trajectory_variant_capture_required"
    if miss_class == "same_active_but_returned_batch_or_component_drift":
        return "full_component_match_required"
    if action == "unsupported_until_source_profile_or_instance_mapping_is_recovered":
        return "source_mapping_recovery_required"
    if row.get("priority_commandable"):
        return "priority_command_available_but_needs_exact_component_audit"
    return "needs_manual_source_mapping"


def _closure_gate(row: dict[str, Any]) -> str:
    category = _execution_category(row)
    if category == "complete_snapshot_available":
        return "use existing complete no-certificate-effect active-basis snapshot row"
    if category == "trajectory_variant_capture_required":
        return (
            "must reach source active_hash_before and then match all exact "
            "context components; same profile rerun alone is not closure"
        )
    if category == "full_component_match_required":
        return (
            "must match active hash plus pool/forbidden/returned-batch/RMP/pricing "
            "components; same active hash alone is insufficient"
        )
    if category == "run_or_reaudit_existing_manifest_command":
        return (
            "run or re-audit referenced manifest command and accept only complete "
            "exact-context component hits"
        )
    if category == "source_mapping_recovery_required":
        return "recover source profile or instance mapping before any capture command can close this context"
    return "requires explicit source mapping and exact-context component audit"


def _why_not_production(row: dict[str, Any]) -> str:
    if row.get("basic_capture_complete_hit") or row.get("priority_capture_complete_hit"):
        return "complete snapshot row can seed calibration, but selector holdout still needs mixed/noop distribution coverage"
    action = str(row.get("recommended_action") or "")
    if action == "unsupported_until_source_profile_or_instance_mapping_is_recovered":
        return "source mapping is missing, so this context cannot yet be sampled or labeled for holdout"
    miss_class = str(row.get("priority_miss_class") or "")
    if miss_class == "source_active_hash_not_reached":
        return "current rerun did not reach the source active-basis neighborhood"
    if miss_class == "same_active_but_returned_batch_or_component_drift":
        return "current rerun reached same active hash but changed components that affect returned-batch impact"
    return "context is unresolved and cannot prove selector generalization"


def _build_action(row: dict[str, Any], commands: dict[str, dict[str, Any]]) -> dict[str, Any]:
    command_id = _row_command_id(row)
    command = commands.get(command_id, {})
    category = _execution_category(row)
    return {
        "context_hash": row.get("context_hash"),
        "priority_score": row.get("priority_score"),
        "row_count": row.get("row_count"),
        "label_counts": row.get("label_counts"),
        "gap_tags": row.get("gap_tags"),
        "recommended_action": row.get("recommended_action"),
        "execution_category": category,
        "current_capture_complete": bool(
            row.get("basic_capture_complete_hit")
            or row.get("priority_capture_complete_hit")
        ),
        "priority_miss_class": row.get("priority_miss_class"),
        "source_active_hash": row.get("source_active_hash"),
        "source_cg_iter": row.get("source_cg_iter"),
        "same_active_event_count": row.get("priority_same_active_event_count"),
        "same_cg_iter_event_count": row.get("priority_same_cg_iter_event_count"),
        "command_id": command_id,
        "command_available": bool(command),
        "command": command.get("command"),
        "expected_context_hashes": command.get("expected_context_hashes"),
        "closure_gate": _closure_gate(row),
        "exact_component_gates": EXACT_COMPONENT_GATES,
        "why_not_production": _why_not_production(row),
    }


def build_summary(
    *,
    worklist_path: Path,
    collection_runbook_path: Path,
    priority_runbook_path: Path,
    next_action_path: Path,
) -> dict[str, Any]:
    worklist = _read_json(worklist_path)
    collection_runbook = _read_json(collection_runbook_path)
    priority_runbook = _read_json(priority_runbook_path)
    next_action = _read_json(next_action_path)
    commands = _command_map(collection_runbook, priority_runbook)

    rows = worklist.get("rows") or []
    actions = [_build_action(row, commands) for row in rows]
    unresolved_actions = [
        action for action in actions if not action["current_capture_complete"]
    ]

    execution_counts: dict[str, int] = {}
    for action in actions:
        key = str(action["execution_category"])
        execution_counts[key] = execution_counts.get(key, 0) + 1

    unresolved_execution_counts: dict[str, int] = {}
    for action in unresolved_actions:
        key = str(action["execution_category"])
        unresolved_execution_counts[key] = unresolved_execution_counts.get(key, 0) + 1

    unresolved_with_command = [
        action for action in unresolved_actions if action["command_available"]
    ]
    unresolved_without_command = [
        action for action in unresolved_actions if not action["command_available"]
    ]
    blind_rerun_actions = [
        action
        for action in unresolved_actions
        if action["execution_category"]
        == "trajectory_variant_capture_required"
        and action["command_available"]
    ]

    checks = {
        "worklist_passed": worklist.get("all_checks_pass") is True,
        "collection_runbook_passed": collection_runbook.get("all_checks_pass") is True,
        "priority_runbook_passed": priority_runbook.get("all_checks_pass") is True,
        "next_action_passed": next_action.get("all_checks_pass") is True,
        "diagnostic_only": True,
        "runs_bpc_or_pricing_false": True,
        "unresolved_count_matches_worklist": (
            len(unresolved_actions) == worklist.get("unresolved_context_count")
        ),
        "all_unresolved_have_closure_gate": all(
            bool(action["closure_gate"]) for action in unresolved_actions
        ),
        "all_referenced_commands_exist": all(
            action["command_available"] or not action["command_id"]
            for action in actions
        ),
        "unsupported_context_has_no_command": all(
            bool(action["command_available"]) is False
            for action in unresolved_actions
            if action["execution_category"] == "source_mapping_recovery_required"
        ),
        "blind_same_profile_rerun_not_allowed_as_closure": all(
            "same profile rerun alone is not closure" in action["closure_gate"]
            for action in blind_rerun_actions
        ),
        "production_direction_still_unproven": (
            next_action.get("production_direction_proven") is False
            and next_action.get("goal_complete") is False
        ),
    }

    return {
        "schema_version": "selector_holdout_context_action_plan_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "selector_holdout_context_action_plan_ready",
        "row_count": len(actions),
        "complete_snapshot_action_count": sum(
            1 for action in actions if action["current_capture_complete"]
        ),
        "unresolved_action_count": len(unresolved_actions),
        "unresolved_with_command_count": len(unresolved_with_command),
        "unresolved_without_command_count": len(unresolved_without_command),
        "execution_category_counts": execution_counts,
        "unresolved_execution_category_counts": unresolved_execution_counts,
        "actions": actions,
        "unresolved_actions": unresolved_actions,
        "sources": {
            "worklist": str(worklist_path),
            "collection_runbook": str(collection_runbook_path),
            "priority_runbook": str(priority_runbook_path),
            "next_action": str(next_action_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "interpretation": (
            "The remaining selector holdout gap is not closed by more Pulse "
            "or by a blind source-profile rerun.  The unresolved contexts need "
            "full component-aware context capture, source active-basis recovery, "
            "or source mapping recovery before production selector validation."
        ),
    }


CSV_FIELDS = [
    "context_hash",
    "priority_score",
    "row_count",
    "label_counts",
    "recommended_action",
    "execution_category",
    "current_capture_complete",
    "priority_miss_class",
    "source_active_hash",
    "source_cg_iter",
    "same_active_event_count",
    "same_cg_iter_event_count",
    "command_id",
    "command_available",
    "closure_gate",
    "why_not_production",
]


def write_csv(summary: dict[str, Any], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for action in summary["actions"]:
            row = {field: action.get(field) for field in CSV_FIELDS}
            row["label_counts"] = json.dumps(
                row["label_counts"], ensure_ascii=False, sort_keys=True
            )
            writer.writerow(row)


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Root Cause Selector Holdout Context Action Plan 报告",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告把 selector holdout context worklist 转成执行级 action plan。",
        "它只读已有 summary/runbook，不运行 BPC / pricing / RMP / Pulse / worker，",
        "不改变 certificate 或 solver 默认行为。",
        "",
        "```text",
        "root_cause_selector_holdout_context_action_plan = current",
        f"diagnostic_only = {str(summary['diagnostic_only']).lower()}",
        f"runs_bpc_or_pricing = {str(summary['runs_bpc_or_pricing']).lower()}",
        f"status = {summary['status']}",
        f"row_count = {summary['row_count']}",
        f"unresolved_action_count = {summary['unresolved_action_count']}",
        f"unresolved_with_command_count = {summary['unresolved_with_command_count']}",
        f"unresolved_without_command_count = {summary['unresolved_without_command_count']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "```",
        "",
        "## 结论",
        "",
        summary["interpretation"],
        "",
        "## Unresolved Execution Category Counts",
        "",
        "```json",
        json.dumps(
            summary["unresolved_execution_category_counts"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Unresolved Actions",
        "",
        "```json",
        json.dumps(
            summary["unresolved_actions"],
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
    parser.add_argument("--worklist", type=Path, default=DEFAULT_WORKLIST)
    parser.add_argument(
        "--collection-runbook", type=Path, default=DEFAULT_COLLECTION_RUNBOOK
    )
    parser.add_argument("--priority-runbook", type=Path, default=DEFAULT_PRIORITY_RUNBOOK)
    parser.add_argument("--next-action", type=Path, default=DEFAULT_NEXT_ACTION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        worklist_path=args.worklist,
        collection_runbook_path=args.collection_runbook,
        priority_runbook_path=args.priority_runbook,
        next_action_path=args.next_action,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "summary.json"
    csv_path = args.output_dir / "context_action_plan.csv"
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
