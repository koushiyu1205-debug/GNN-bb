# Root Cause Selector Holdout Context Worklist 报告

日期：2026-06-14

## 目的

本报告把 priority context gap、runbook、capture audit 与 capture-miss
诊断合并成下一轮 selector holdout 数据补齐 worklist。它只读已有
summary，不运行 BPC / pricing / RMP / Pulse / worker，不改变 certificate
或 solver 默认行为。

```text
root_cause_selector_holdout_context_worklist = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_context_worklist_ready
row_count = 12
unresolved_context_count = 5
actionable_context_count = 5
same_profile_rerun_not_sufficient = true
all_checks_pass = true
```

## 结论

Priority selector holdout gaps are actionable only through full component-aware context capture.  Existing complete hits can seed replay, but rerun-missed or unsupported contexts cannot be closed by blind source-profile reruns; they require trajectory/component targeting or source-profile recovery.

## Recommended Action Counts

```json
{
  "do_not_repeat_same_source_profile_blindly_collect_trajectory_variants": 2,
  "run_existing_collection_manifest_command_and_audit_exact_components": 1,
  "treat_current_rerun_as_near_miss_and_target_full_component_match": 1,
  "unsupported_until_source_profile_or_instance_mapping_is_recovered": 1,
  "use_as_complete_snapshot_row_then_replay_label_if_needed": 7
}
```

## Priority Miss Class Counts

```json
{
  "same_active_but_returned_batch_or_component_drift": 1,
  "source_active_hash_not_reached": 2
}
```

## Top Actionable Contexts

```json
[
  {
    "basic_capture_complete_hit": false,
    "basic_capture_hit": false,
    "collection_runbook_command_id": null,
    "complete_snapshot_row_count": 0,
    "context_hash": "c27d904416342f6b",
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot"
    ],
    "label_counts": {
      "improved": 14,
      "noop": 2
    },
    "manifest_candidate_label_counts": null,
    "manifest_failure_kind": null,
    "manifest_target_id": null,
    "priority_capture_complete_hit": false,
    "priority_capture_hit": false,
    "priority_commandable": true,
    "priority_miss_class": "source_active_hash_not_reached",
    "priority_runbook_command_id": "selector_priority_capture_001",
    "priority_same_active_event_count": 0,
    "priority_same_cg_iter_event_count": 6,
    "priority_score": 379,
    "priority_unsupported": false,
    "recommended_action": "do_not_repeat_same_source_profile_blindly_collect_trajectory_variants",
    "row_count": 16,
    "source_active_hash": "16862add48072518",
    "source_cg_iter": 3
  },
  {
    "basic_capture_complete_hit": false,
    "basic_capture_hit": false,
    "collection_runbook_command_id": null,
    "complete_snapshot_row_count": 0,
    "context_hash": "794ecbd6fefaa1d7",
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "mixed_missing_full_snapshot",
      "mixed_context_not_represented_as_complete_mixed",
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "positive_missing_full_snapshot"
    ],
    "label_counts": {
      "improved": 14,
      "noop": 2
    },
    "manifest_candidate_label_counts": null,
    "manifest_failure_kind": null,
    "manifest_target_id": null,
    "priority_capture_complete_hit": false,
    "priority_capture_hit": false,
    "priority_commandable": true,
    "priority_miss_class": "source_active_hash_not_reached",
    "priority_runbook_command_id": "selector_priority_capture_001",
    "priority_same_active_event_count": 0,
    "priority_same_cg_iter_event_count": 6,
    "priority_score": 379,
    "priority_unsupported": false,
    "recommended_action": "do_not_repeat_same_source_profile_blindly_collect_trajectory_variants",
    "row_count": 16,
    "source_active_hash": "16862add48072518",
    "source_cg_iter": 3
  },
  {
    "basic_capture_complete_hit": false,
    "basic_capture_hit": false,
    "collection_runbook_command_id": "selector_holdout_capture_002",
    "complete_snapshot_row_count": 0,
    "context_hash": "3f914a0d2b97fd27",
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "existing_collection_manifest_target"
    ],
    "label_counts": {
      "noop": 10
    },
    "manifest_candidate_label_counts": {
      "noop": 5
    },
    "manifest_failure_kind": "false_positive_no_positive_context",
    "manifest_target_id": "selector_holdout_context_001",
    "priority_capture_complete_hit": false,
    "priority_capture_hit": false,
    "priority_commandable": false,
    "priority_miss_class": null,
    "priority_runbook_command_id": null,
    "priority_same_active_event_count": null,
    "priority_same_cg_iter_event_count": null,
    "priority_score": 163,
    "priority_unsupported": false,
    "recommended_action": "run_existing_collection_manifest_command_and_audit_exact_components",
    "row_count": 10,
    "source_active_hash": null,
    "source_cg_iter": null
  },
  {
    "basic_capture_complete_hit": false,
    "basic_capture_hit": false,
    "collection_runbook_command_id": null,
    "complete_snapshot_row_count": 0,
    "context_hash": "46e7a2883459d4fb",
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden"
    ],
    "label_counts": {
      "noop": 8
    },
    "manifest_candidate_label_counts": null,
    "manifest_failure_kind": null,
    "manifest_target_id": null,
    "priority_capture_complete_hit": false,
    "priority_capture_hit": false,
    "priority_commandable": true,
    "priority_miss_class": "same_active_but_returned_batch_or_component_drift",
    "priority_runbook_command_id": "selector_priority_capture_001",
    "priority_same_active_event_count": 6,
    "priority_same_cg_iter_event_count": 0,
    "priority_score": 141,
    "priority_unsupported": false,
    "recommended_action": "treat_current_rerun_as_near_miss_and_target_full_component_match",
    "row_count": 8,
    "source_active_hash": "f0b96be45c5015c9",
    "source_cg_iter": 4
  },
  {
    "basic_capture_complete_hit": false,
    "basic_capture_hit": false,
    "collection_runbook_command_id": null,
    "complete_snapshot_row_count": 0,
    "context_hash": "7b9a35f8f7c6581a",
    "explicit_forbidden_row_count": 0,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden"
    ],
    "label_counts": {
      "noop": 2
    },
    "manifest_candidate_label_counts": null,
    "manifest_failure_kind": null,
    "manifest_target_id": null,
    "priority_capture_complete_hit": false,
    "priority_capture_hit": false,
    "priority_commandable": false,
    "priority_miss_class": null,
    "priority_runbook_command_id": null,
    "priority_same_active_event_count": null,
    "priority_same_cg_iter_event_count": null,
    "priority_score": 135,
    "priority_unsupported": true,
    "recommended_action": "unsupported_until_source_profile_or_instance_mapping_is_recovered",
    "row_count": 2,
    "source_active_hash": null,
    "source_cg_iter": null
  }
]
```

## Checks

```json
{
  "collection_capture_passed": true,
  "collection_manifest_passed": true,
  "collection_runbook_passed": true,
  "diagnostic_only": true,
  "has_component_drift_or_active_miss": true,
  "has_priority_rows": true,
  "has_unresolved_contexts": true,
  "next_action_passed": true,
  "priority_capture_passed": true,
  "priority_miss_passed": true,
  "priority_runbook_passed": true,
  "production_direction_still_unproven": true,
  "runs_bpc_or_pricing_false": true,
  "same_profile_rerun_not_sufficient": true,
  "target_priority_passed": true
}
```
