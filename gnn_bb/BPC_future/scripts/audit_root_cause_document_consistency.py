#!/usr/bin/env python3
"""Audit consistency between root-cause summaries and human-facing docs.

This diagnostic-only helper checks that the main Chinese documents and concise
reports agree with the authoritative machine summaries for the current
root-cause conclusion.  It does not run BPC, pricing, RMP, Pulse, workers,
certificates, or benchmarks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_WORKER_BLOCKER = Path(
    "BPC_future/results/root_cause_worker_negative_column_roi_blocker_20260614/"
    "summary.json"
)
DEFAULT_GAP_MATRIX = Path(
    "BPC_future/results/root_cause_selector_holdout_gap_matrix_20260614/"
    "summary.json"
)
DEFAULT_CURRENT_ANSWER = Path(
    "BPC_future/results/root_cause_current_answer_20260614/summary.json"
)
DEFAULT_NEXT_ACTION = Path(
    "BPC_future/results/root_cause_next_action_plan_20260614/summary.json"
)
DEFAULT_CONTEXT_WORKLIST = Path(
    "BPC_future/results/root_cause_selector_holdout_context_worklist_20260614/"
    "summary.json"
)
DEFAULT_CONTEXT_ACTION_PLAN = Path(
    "BPC_future/results/root_cause_selector_holdout_context_action_plan_20260614/"
    "summary.json"
)
DEFAULT_DIAGNOSIS_DOC = Path("BPC_future/docs/bpc_future_root_cause_diagnosis_zh.md")
DEFAULT_TARGET_DOC = Path("BPC_future/logical_graph/目标.md")
DEFAULT_CURRENT_ANSWER_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_current_answer_zh.md"
)
DEFAULT_NEXT_ACTION_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_next_action_plan_zh.md"
)
DEFAULT_OUTPUT_DIR = Path(
    "BPC_future/results/root_cause_document_consistency_20260614"
)
DEFAULT_REPORT = Path(
    "BPC_future/logical_graph/run_reports/"
    "20260614_bpc_future_root_cause_document_consistency_zh.md"
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _contains_all(text: str, phrases: list[str]) -> bool:
    return all(phrase in text for phrase in phrases)


def build_summary(
    *,
    worker_blocker_path: Path,
    gap_matrix_path: Path,
    current_answer_path: Path,
    next_action_path: Path,
    context_worklist_path: Path,
    context_action_plan_path: Path,
    diagnosis_doc_path: Path,
    target_doc_path: Path,
    current_answer_report_path: Path,
    next_action_report_path: Path,
) -> dict[str, Any]:
    worker = _read_json(worker_blocker_path)
    gap = _read_json(gap_matrix_path)
    current = _read_json(current_answer_path)
    next_action = _read_json(next_action_path)
    worklist = _read_json(context_worklist_path)
    action_plan = _read_json(context_action_plan_path)
    diagnosis_text = _read_text(diagnosis_doc_path)
    target_text = _read_text(target_doc_path)
    current_report_text = _read_text(current_answer_report_path)
    next_action_report_text = _read_text(next_action_report_path)

    phase7o = worker.get("phase7o_expanded", {})
    phase8q = worker.get("phase8q_validation", {})
    snapshot_total = gap.get("complete_snapshot_total", {}) or {}
    snapshot_mix = gap.get("complete_snapshot_context_label_mix", {}) or {}
    explicit_total = gap.get("complete_explicit_forbidden_total", {}) or {}
    explicit_mix = gap.get("complete_explicit_forbidden_context_label_mix", {}) or {}

    authoritative_metrics = {
        "phase7o_nonbaseline_rows": phase7o.get("nonbaseline_rows"),
        "phase7o_nonbaseline_worsened_rows": phase7o.get(
            "nonbaseline_worsened_rows"
        ),
        "phase7o_worker_added_journeys": phase7o.get("worker_added_journeys"),
        "phase7o_worker_added_new_task_sets": phase7o.get(
            "worker_added_new_task_sets"
        ),
        "phase7o_worker_added_support_changing": phase7o.get(
            "worker_added_support_changing"
        ),
        "phase8q_worker_added_journeys": phase8q.get("worker_added_journeys"),
        "phase8q_worker_added_rows": phase8q.get("worker_added_rows"),
        "phase8q_improved_without_worker_added_count": worker.get(
            "phase8q_improved_without_worker_added_count"
        ),
        "context_worklist_row_count": worklist.get("row_count"),
        "context_worklist_unresolved_context_count": worklist.get(
            "unresolved_context_count"
        ),
        "context_worklist_actionable_context_count": worklist.get(
            "actionable_context_count"
        ),
        "context_worklist_priority_miss_class_counts": worklist.get(
            "priority_miss_class_counts"
        ),
        "context_action_plan_unresolved_action_count": action_plan.get(
            "unresolved_action_count"
        ),
        "context_action_plan_unresolved_with_command_count": action_plan.get(
            "unresolved_with_command_count"
        ),
        "context_action_plan_unresolved_without_command_count": action_plan.get(
            "unresolved_without_command_count"
        ),
        "context_action_plan_unresolved_execution_category_counts": (
            action_plan.get("unresolved_execution_category_counts")
        ),
        "complete_snapshot_row_count": snapshot_total.get("row_count"),
        "complete_snapshot_label_counts": snapshot_total.get("label_counts"),
        "complete_snapshot_mixed_context_count": snapshot_mix.get(
            "mixed_label_context_count"
        ),
        "complete_snapshot_noop_only_context_count": snapshot_mix.get(
            "noop_only_context_count"
        ),
        "complete_snapshot_positive_only_context_count": snapshot_mix.get(
            "positive_only_context_count"
        ),
        "complete_explicit_forbidden_row_count": explicit_total.get("row_count"),
        "complete_explicit_forbidden_label_counts": explicit_total.get(
            "label_counts"
        ),
        "complete_explicit_forbidden_mixed_context_count": explicit_mix.get(
            "mixed_label_context_count"
        ),
        "complete_explicit_forbidden_noop_only_context_count": explicit_mix.get(
            "noop_only_context_count"
        ),
    }

    stale_patterns = [
        "complete_snapshot_mixed_context_count = 5",
        "complete_snapshot_mixed_context_count=5",
        '"complete_snapshot_mixed_context_count": 5',
        "target002 is exact-covered",
        "target002 is now exact-covered",
        "target002 已 exact-covered",
        "target002 已经 exact-covered",
    ]
    ambiguous_stage_patterns = [
        "selector holdout 仍不能开始",
        "selector holdout 不能开始",
    ]
    combined_human_text = "\n".join(
        [diagnosis_text, target_text, current_report_text, next_action_report_text]
    )

    checks = {
        "input_summaries_pass": (
            worker.get("all_checks_pass") is True
            and gap.get("all_checks_pass") is True
            and current.get("all_checks_pass") is True
            and next_action.get("all_checks_pass") is True
            and worklist.get("all_checks_pass") is True
            and action_plan.get("all_checks_pass") is True
        ),
        "worker_metrics_match_authoritative_values": (
            _as_int(phase7o.get("nonbaseline_rows")) == 96
            and _as_int(phase7o.get("nonbaseline_worsened_rows")) == 96
            and _as_int(phase7o.get("worker_added_journeys")) == 63
            and _as_int(phase7o.get("worker_added_new_task_sets")) == 30
            and _as_int(phase7o.get("worker_added_support_changing")) == 13
            and _as_int(phase8q.get("worker_added_journeys")) == 10
            and _as_int(phase8q.get("worker_added_rows")) == 3
            and _as_int(worker.get("phase8q_improved_without_worker_added_count"))
            == 1
        ),
        "gap_metrics_match_authoritative_values": (
            _as_int(snapshot_total.get("row_count")) == 62
            and snapshot_total.get("label_counts") == {"improved": 59, "noop": 3}
            and _as_int(snapshot_mix.get("mixed_label_context_count")) == 0
            and _as_int(snapshot_mix.get("noop_only_context_count")) == 3
            and _as_int(snapshot_mix.get("positive_only_context_count")) == 14
            and _as_int(explicit_total.get("row_count")) == 48
            and explicit_total.get("label_counts") == {"improved": 48}
            and _as_int(explicit_mix.get("mixed_label_context_count")) == 0
            and _as_int(explicit_mix.get("noop_only_context_count")) == 0
        ),
        "context_worklist_metrics_match_authoritative_values": (
            _as_int(worklist.get("row_count")) == 12
            and _as_int(worklist.get("unresolved_context_count")) == 5
            and _as_int(worklist.get("actionable_context_count")) == 5
            and (
                worklist.get("recommended_action_counts", {}).get(
                    "use_as_complete_snapshot_row_then_replay_label_if_needed"
                )
                == 7
            )
            and (
                worklist.get("priority_miss_class_counts", {}).get(
                    "source_active_hash_not_reached"
                )
                == 2
            )
            and (
                worklist.get("priority_miss_class_counts", {}).get(
                    "same_active_but_returned_batch_or_component_drift"
                )
                == 1
            )
        ),
        "context_action_plan_metrics_match_authoritative_values": (
            _as_int(action_plan.get("row_count")) == 12
            and _as_int(action_plan.get("complete_snapshot_action_count")) == 7
            and _as_int(action_plan.get("unresolved_action_count")) == 5
            and _as_int(action_plan.get("unresolved_with_command_count")) == 4
            and _as_int(action_plan.get("unresolved_without_command_count")) == 1
            and (
                action_plan.get("unresolved_execution_category_counts", {}).get(
                    "trajectory_variant_capture_required"
                )
                == 2
            )
            and (
                action_plan.get("unresolved_execution_category_counts", {}).get(
                    "full_component_match_required"
                )
                == 1
            )
            and (
                action_plan.get("unresolved_execution_category_counts", {}).get(
                    "source_mapping_recovery_required"
                )
                == 1
            )
        ),
        "current_answer_reports_worker_and_gap": (
            current.get("checks", {}).get("worker_negative_roi_blocker_passed")
            is True
            and _contains_all(
                current_report_text,
                [
                    "worker 负列 ROI 阻塞结论",
                    '"complete_snapshot_mixed_context_count": 0',
                    "missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup",
                ],
            )
        ),
        "next_action_reports_worker_and_gap": (
            next_action.get("checks", {}).get("worker_negative_roi_blocker_passed")
            is True
            and "increase_worker_budget_without_selector_roi"
            in next_action.get("forbidden_actions", [])
            and _contains_all(
                next_action_report_text,
                [
                    "Worker Negative ROI Blocker",
                    '"complete_snapshot_mixed_context_count": 0',
                    "increase_worker_budget_without_selector_roi",
                ],
            )
        ),
        "diagnosis_doc_has_current_metrics": _contains_all(
            diagnosis_text,
                [
                    "Worker Negative Column ROI Blocker",
                    "Selector Holdout Context Worklist",
                    "Selector Holdout Context Action Plan",
                    "complete_snapshot_mixed_context_count=0",
                    "unresolved_context_count=5",
                    "unresolved_action_count=5",
                    "increase_worker_budget_without_selector_roi",
                    "可以继续做 calibration-only 数据补齐",
                    "production selector validation 与",
                "completion_decision=keep_goal_active",
            ],
        ),
        "target_doc_has_current_metrics": _contains_all(
            target_text,
                [
                    "Worker Negative Column ROI Blocker",
                    "Selector Holdout Context Worklist",
                    "Selector Holdout Context Action Plan",
                    "complete_snapshot_mixed_context_count=0",
                    "unresolved_context_count=5",
                    "unresolved_action_count=5",
                    "increase_worker_budget_without_selector_roi",
                    "可以继续做 calibration-only 数据补齐",
                    "production selector validation 与 production BPC A/B",
                "目标保持 active",
            ],
        ),
        "no_stale_mixed_context_count_claim": not any(
            pattern in combined_human_text for pattern in stale_patterns
        ),
        "no_ambiguous_selector_holdout_blocked_claim": not any(
            pattern in combined_human_text for pattern in ambiguous_stage_patterns
        ),
    }

    return {
        "schema_version": "root_cause_document_consistency_v1",
        "diagnostic_only": True,
        "runs_bpc_or_pricing": False,
        "status": "root_cause_documents_consistent",
        "authoritative_metrics": authoritative_metrics,
        "checked_documents": {
            "diagnosis_doc": str(diagnosis_doc_path),
            "target_doc": str(target_doc_path),
            "current_answer_report": str(current_answer_report_path),
            "next_action_report": str(next_action_report_path),
        },
        "sources": {
            "worker_blocker": str(worker_blocker_path),
            "gap_matrix": str(gap_matrix_path),
            "current_answer": str(current_answer_path),
            "next_action": str(next_action_path),
            "context_worklist": str(context_worklist_path),
            "context_action_plan": str(context_action_plan_path),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
    }


def write_report(summary: dict[str, Any], report_path: Path) -> None:
    lines = [
        "# Root Cause Document Consistency 审计",
        "",
        "日期：2026-06-14",
        "",
        "## 目的",
        "",
        "本报告只核对根因机器摘要与人工中文文档是否一致；不运行 BPC、pricing、RMP、Pulse、worker 或 benchmark。",
        "",
        "## 结论",
        "",
        f"status = {summary['status']}",
        f"all_checks_pass = {str(summary['all_checks_pass']).lower()}",
        "diagnostic_only = true",
        "runs_bpc_or_pricing = false",
        "",
        "关键口径：`complete_snapshot_mixed_context_count=0`，"
        "`increase_worker_budget_without_selector_roi` 是当前硬禁止项。",
        "",
        "## Authoritative Metrics",
        "",
        "```json",
        json.dumps(
            summary["authoritative_metrics"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Checked Documents",
        "",
        "```json",
        json.dumps(
            summary["checked_documents"],
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
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker-blocker", type=Path, default=DEFAULT_WORKER_BLOCKER)
    parser.add_argument("--gap-matrix", type=Path, default=DEFAULT_GAP_MATRIX)
    parser.add_argument("--current-answer", type=Path, default=DEFAULT_CURRENT_ANSWER)
    parser.add_argument("--next-action", type=Path, default=DEFAULT_NEXT_ACTION)
    parser.add_argument(
        "--context-worklist", type=Path, default=DEFAULT_CONTEXT_WORKLIST
    )
    parser.add_argument(
        "--context-action-plan", type=Path, default=DEFAULT_CONTEXT_ACTION_PLAN
    )
    parser.add_argument("--diagnosis-doc", type=Path, default=DEFAULT_DIAGNOSIS_DOC)
    parser.add_argument("--target-doc", type=Path, default=DEFAULT_TARGET_DOC)
    parser.add_argument(
        "--current-answer-report",
        type=Path,
        default=DEFAULT_CURRENT_ANSWER_REPORT,
    )
    parser.add_argument(
        "--next-action-report",
        type=Path,
        default=DEFAULT_NEXT_ACTION_REPORT,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    summary = build_summary(
        worker_blocker_path=args.worker_blocker,
        gap_matrix_path=args.gap_matrix,
        current_answer_path=args.current_answer,
        next_action_path=args.next_action,
        context_worklist_path=args.context_worklist,
        context_action_plan_path=args.context_action_plan,
        diagnosis_doc_path=args.diagnosis_doc,
        target_doc_path=args.target_doc,
        current_answer_report_path=args.current_answer_report,
        next_action_report_path=args.next_action_report,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_report(summary, args.report)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if summary["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
