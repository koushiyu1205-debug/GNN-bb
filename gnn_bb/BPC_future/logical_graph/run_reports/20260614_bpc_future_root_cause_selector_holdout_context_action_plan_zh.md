# Root Cause Selector Holdout Context Action Plan 报告

日期：2026-06-14

## 目的

本报告把 selector holdout context worklist 转成执行级 action plan。
它只读已有 summary/runbook，不运行 BPC / pricing / RMP / Pulse / worker，
不改变 certificate 或 solver 默认行为。

```text
root_cause_selector_holdout_context_action_plan = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_context_action_plan_ready
row_count = 12
unresolved_action_count = 5
unresolved_with_command_count = 4
unresolved_without_command_count = 1
all_checks_pass = true
```

## 结论

The remaining selector holdout gap is not closed by more Pulse or by a blind source-profile rerun.  The unresolved contexts need full component-aware context capture, source active-basis recovery, or source mapping recovery before production selector validation.

## Unresolved Execution Category Counts

```json
{
  "full_component_match_required": 1,
  "run_or_reaudit_existing_manifest_command": 1,
  "source_mapping_recovery_required": 1,
  "trajectory_variant_capture_required": 2
}
```

## Unresolved Actions

```json
[
  {
    "closure_gate": "must reach source active_hash_before and then match all exact context components; same profile rerun alone is not closure",
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_early_new_task_set_quota_3_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.3 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet",
    "command_available": true,
    "command_id": "selector_priority_capture_001",
    "context_hash": "c27d904416342f6b",
    "current_capture_complete": false,
    "exact_component_gates": [
      "context_hash",
      "active_hash_before",
      "pool_signature_hash",
      "pool_task_set_hash",
      "forbidden_signature_hash",
      "returned_task_set_hash",
      "rmp_objective_before",
      "pricing_state",
      "pricing_best_reduced_cost"
    ],
    "execution_category": "trajectory_variant_capture_required",
    "expected_context_hashes": [
      "46e7a2883459d4fb",
      "794ecbd6fefaa1d7",
      "c27d904416342f6b"
    ],
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
    "priority_miss_class": "source_active_hash_not_reached",
    "priority_score": 379,
    "recommended_action": "do_not_repeat_same_source_profile_blindly_collect_trajectory_variants",
    "row_count": 16,
    "same_active_event_count": 0,
    "same_cg_iter_event_count": 6,
    "source_active_hash": "16862add48072518",
    "source_cg_iter": 3,
    "why_not_production": "current rerun did not reach the source active-basis neighborhood"
  },
  {
    "closure_gate": "must reach source active_hash_before and then match all exact context components; same profile rerun alone is not closure",
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_early_new_task_set_quota_3_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.3 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet",
    "command_available": true,
    "command_id": "selector_priority_capture_001",
    "context_hash": "794ecbd6fefaa1d7",
    "current_capture_complete": false,
    "exact_component_gates": [
      "context_hash",
      "active_hash_before",
      "pool_signature_hash",
      "pool_task_set_hash",
      "forbidden_signature_hash",
      "returned_task_set_hash",
      "rmp_objective_before",
      "pricing_state",
      "pricing_best_reduced_cost"
    ],
    "execution_category": "trajectory_variant_capture_required",
    "expected_context_hashes": [
      "46e7a2883459d4fb",
      "794ecbd6fefaa1d7",
      "c27d904416342f6b"
    ],
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
    "priority_miss_class": "source_active_hash_not_reached",
    "priority_score": 379,
    "recommended_action": "do_not_repeat_same_source_profile_blindly_collect_trajectory_variants",
    "row_count": 16,
    "same_active_event_count": 0,
    "same_cg_iter_event_count": 6,
    "source_active_hash": "16862add48072518",
    "source_cg_iter": 3,
    "why_not_production": "current rerun did not reach the source active-basis neighborhood"
  },
  {
    "closure_gate": "run or re-audit referenced manifest command and accept only complete exact-context component hits",
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_early_new_task_set_quota_3_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.3 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet",
    "command_available": true,
    "command_id": "selector_holdout_capture_002",
    "context_hash": "3f914a0d2b97fd27",
    "current_capture_complete": false,
    "exact_component_gates": [
      "context_hash",
      "active_hash_before",
      "pool_signature_hash",
      "pool_task_set_hash",
      "forbidden_signature_hash",
      "returned_task_set_hash",
      "rmp_objective_before",
      "pricing_state",
      "pricing_best_reduced_cost"
    ],
    "execution_category": "run_or_reaudit_existing_manifest_command",
    "expected_context_hashes": [
      "3f914a0d2b97fd27"
    ],
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden",
      "existing_collection_manifest_target"
    ],
    "label_counts": {
      "noop": 10
    },
    "priority_miss_class": null,
    "priority_score": 163,
    "recommended_action": "run_existing_collection_manifest_command_and_audit_exact_components",
    "row_count": 10,
    "same_active_event_count": null,
    "same_cg_iter_event_count": null,
    "source_active_hash": null,
    "source_cg_iter": null,
    "why_not_production": "context is unresolved and cannot prove selector generalization"
  },
  {
    "closure_gate": "must match active hash plus pool/forbidden/returned-batch/RMP/pricing components; same active hash alone is insufficient",
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_early_new_task_set_quota_3_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.3 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet",
    "command_available": true,
    "command_id": "selector_priority_capture_001",
    "context_hash": "46e7a2883459d4fb",
    "current_capture_complete": false,
    "exact_component_gates": [
      "context_hash",
      "active_hash_before",
      "pool_signature_hash",
      "pool_task_set_hash",
      "forbidden_signature_hash",
      "returned_task_set_hash",
      "rmp_objective_before",
      "pricing_state",
      "pricing_best_reduced_cost"
    ],
    "execution_category": "full_component_match_required",
    "expected_context_hashes": [
      "46e7a2883459d4fb",
      "794ecbd6fefaa1d7",
      "c27d904416342f6b"
    ],
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden"
    ],
    "label_counts": {
      "noop": 8
    },
    "priority_miss_class": "same_active_but_returned_batch_or_component_drift",
    "priority_score": 141,
    "recommended_action": "treat_current_rerun_as_near_miss_and_target_full_component_match",
    "row_count": 8,
    "same_active_event_count": 6,
    "same_cg_iter_event_count": 0,
    "source_active_hash": "f0b96be45c5015c9",
    "source_cg_iter": 4,
    "why_not_production": "current rerun reached same active hash but changed components that affect returned-batch impact"
  },
  {
    "closure_gate": "recover source profile or instance mapping before any capture command can close this context",
    "command": null,
    "command_available": false,
    "command_id": "",
    "context_hash": "7b9a35f8f7c6581a",
    "current_capture_complete": false,
    "exact_component_gates": [
      "context_hash",
      "active_hash_before",
      "pool_signature_hash",
      "pool_task_set_hash",
      "forbidden_signature_hash",
      "returned_task_set_hash",
      "rmp_objective_before",
      "pricing_state",
      "pricing_best_reduced_cost"
    ],
    "execution_category": "source_mapping_recovery_required",
    "expected_context_hashes": null,
    "gap_tags": [
      "noop_missing_full_snapshot",
      "noop_missing_explicit_forbidden"
    ],
    "label_counts": {
      "noop": 2
    },
    "priority_miss_class": null,
    "priority_score": 135,
    "recommended_action": "unsupported_until_source_profile_or_instance_mapping_is_recovered",
    "row_count": 2,
    "same_active_event_count": null,
    "same_cg_iter_event_count": null,
    "source_active_hash": null,
    "source_cg_iter": null,
    "why_not_production": "source mapping is missing, so this context cannot yet be sampled or labeled for holdout"
  }
]
```

## Checks

```json
{
  "all_referenced_commands_exist": true,
  "all_unresolved_have_closure_gate": true,
  "blind_same_profile_rerun_not_allowed_as_closure": true,
  "collection_runbook_passed": true,
  "diagnostic_only": true,
  "next_action_passed": true,
  "priority_runbook_passed": true,
  "production_direction_still_unproven": true,
  "runs_bpc_or_pricing_false": true,
  "unresolved_count_matches_worklist": true,
  "unsupported_context_has_no_command": true,
  "worklist_passed": true
}
```
