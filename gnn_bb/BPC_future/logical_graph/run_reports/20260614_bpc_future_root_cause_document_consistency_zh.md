# Root Cause Document Consistency 审计

日期：2026-06-14

## 目的

本报告只核对根因机器摘要与人工中文文档是否一致；不运行 BPC、pricing、RMP、Pulse、worker 或 benchmark。

## 结论

status = root_cause_documents_consistent
all_checks_pass = true
diagnostic_only = true
runs_bpc_or_pricing = false

关键口径：`complete_snapshot_mixed_context_count=0`，`increase_worker_budget_without_selector_roi` 是当前硬禁止项。

## Authoritative Metrics

```json
{
  "complete_explicit_forbidden_label_counts": {
    "improved": 48
  },
  "complete_explicit_forbidden_mixed_context_count": 0,
  "complete_explicit_forbidden_noop_only_context_count": 0,
  "complete_explicit_forbidden_row_count": 48,
  "complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "complete_snapshot_mixed_context_count": 0,
  "complete_snapshot_noop_only_context_count": 3,
  "complete_snapshot_positive_only_context_count": 14,
  "complete_snapshot_row_count": 62,
  "context_action_plan_unresolved_action_count": 5,
  "context_action_plan_unresolved_execution_category_counts": {
    "full_component_match_required": 1,
    "run_or_reaudit_existing_manifest_command": 1,
    "source_mapping_recovery_required": 1,
    "trajectory_variant_capture_required": 2
  },
  "context_action_plan_unresolved_with_command_count": 4,
  "context_action_plan_unresolved_without_command_count": 1,
  "context_worklist_actionable_context_count": 5,
  "context_worklist_priority_miss_class_counts": {
    "same_active_but_returned_batch_or_component_drift": 1,
    "source_active_hash_not_reached": 2
  },
  "context_worklist_row_count": 12,
  "context_worklist_unresolved_context_count": 5,
  "phase7o_nonbaseline_rows": 96,
  "phase7o_nonbaseline_worsened_rows": 96,
  "phase7o_worker_added_journeys": 63,
  "phase7o_worker_added_new_task_sets": 30,
  "phase7o_worker_added_support_changing": 13,
  "phase8q_improved_without_worker_added_count": 1,
  "phase8q_worker_added_journeys": 10,
  "phase8q_worker_added_rows": 3
}
```

## Checked Documents

```json
{
  "current_answer_report": "BPC_future/logical_graph/run_reports/20260614_bpc_future_root_cause_current_answer_zh.md",
  "diagnosis_doc": "BPC_future/docs/bpc_future_root_cause_diagnosis_zh.md",
  "next_action_report": "BPC_future/logical_graph/run_reports/20260614_bpc_future_root_cause_next_action_plan_zh.md",
  "target_doc": "BPC_future/logical_graph/目标.md"
}
```

## 检查项

```json
{
  "context_action_plan_metrics_match_authoritative_values": true,
  "context_worklist_metrics_match_authoritative_values": true,
  "current_answer_reports_worker_and_gap": true,
  "diagnosis_doc_has_current_metrics": true,
  "gap_metrics_match_authoritative_values": true,
  "input_summaries_pass": true,
  "next_action_reports_worker_and_gap": true,
  "no_ambiguous_selector_holdout_blocked_claim": true,
  "no_stale_mixed_context_count_claim": true,
  "target_doc_has_current_metrics": true,
  "worker_metrics_match_authoritative_values": true
}
```
