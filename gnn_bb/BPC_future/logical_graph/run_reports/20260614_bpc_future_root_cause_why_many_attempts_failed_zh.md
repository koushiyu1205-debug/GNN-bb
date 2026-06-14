# 为什么做了很多工作仍不行：根因机制报告

日期：2026-06-14

## 目的

本报告只回答一个问题：为什么已经实现了 Sharded Pulse、audit、worker、
current-context probe、selector calibration 之后，仍然不能同时做到 5/10 不退化
和 20-task 明显优化？

它只读现有 summary artifacts，不运行 BPC / pricing / RMP / Pulse，
也不改变 worker / certificate / solver 默认行为。

## 机器字段

```text
why_many_attempts_failed = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = supported_but_optimization_direction_unproven
all_checks_pass = true
```

## 一句话结论

5/10 卡在固定开销；20 卡在 returned-batch 与 RMP trajectory 的上下文耦合；当前缺少 production-validated addition-before selector。

## 因果链

### small_scale_fixed_overhead_sensitivity

5/10 规模不是缺负列，而是触发 worker/audit/probe 的固定开销吃掉收益。

```json
{
  "missing_requirement": "five_ten_full_no_regression_ab",
  "nontriggered_official_changed": 0,
  "triggered_better_count": 0,
  "triggered_rows": 220,
  "triggered_worse_count": 220
}
```

### twenty_returned_batch_rmp_trajectory_coupling

20-task 不是完全找不到 true-RC negative columns；问题是 returned batch 是否改变后续 RMP active-basis / dual / pricing tail。

```json
{
  "active_basis_counterexample_strongest_noop_true_rc": -128.547499,
  "active_basis_counterexample_task20_label_counts": {
    "improved": 10,
    "noop": 2
  },
  "active_basis_counterexample_task20_new_task_sets": 12,
  "active_basis_counterexample_task20_rows": 12,
  "has_20_walltime_speedup_evidence": false,
  "negative_columns_route_evidence": {
    "phase7o_all_time_limit": true,
    "phase8q_added_journeys": 10,
    "phase8q_added_new_task_sets": 8,
    "phase8q_all_time_limit": true,
    "phase8q_completion_bound_retry_count": 0
  },
  "negative_columns_route_status": "ruled_out_as_sufficient_condition",
  "phase7o_nonbaseline_rows": 96,
  "phase7o_nonbaseline_worsened_rows": 96,
  "phase7o_worker_added_journeys": 63,
  "phase7o_worker_added_new_task_sets": 30,
  "phase8q_improved_without_worker_added_count": 1,
  "phase8q_worker_added_journeys": 10,
  "phase8q_worker_added_rows": 3,
  "pulse_route_evidence": {
    "code_boundary_pass": true,
    "phase8q_added_journeys": 10,
    "phase8q_added_new_task_sets": 8,
    "phase8q_all_time_limit": true
  },
  "pulse_route_status": "ruled_out_as_primary_root_cause",
  "weaker_improved_than_strongest_noop_count": 8,
  "worker_negative_roi_blocker_status": "worker_negative_columns_not_sufficient_for_roi"
}
```

### addition_before_selector_not_production_validated

当前已有 calibration signal，但没有一个只用 addition-before 特征的 selector 能通过 context / instance / dataset holdout。补回 event-history 可恢复字段并定义full-snapshot active-basis churn / RMP degeneracy pressure 后，旧 replay 证据包仍缺这些 snapshot 指标的实际值。最新 component payload 已能转成 addition-before rows；最小合并到 base selector rows 后仍没有 robust all-holdout feature/model。

```json
{
  "active_basis_snapshot_metric_fields": 2,
  "best_context_model": "shallow_tree_depth3",
  "candidate_row_count": 280,
  "component_payload_extension_base_row_count": 280,
  "component_payload_extension_combined_robust_features": 0,
  "component_payload_extension_combined_robust_models": 0,
  "component_payload_extension_combined_row_count": 328,
  "component_payload_extension_component_positive_only": true,
  "component_payload_extension_component_row_count": 48,
  "component_payload_rows_candidate_row_count": 48,
  "component_payload_rows_explicit_forbidden_true_count": 48,
  "component_payload_rows_ready_case_count": 6,
  "component_payload_rows_runs_local_rmp_replay": true,
  "context_trajectory_exact_component_count": 9,
  "context_trajectory_required_payload_count": 9,
  "counterexample_degeneracy_one_label_counts": {
    "improved": 3,
    "noop": 2
  },
  "counterexample_false_positive_count": 2,
  "counterexample_mixed_instance_group_count": 2,
  "counterexample_positive_churn_label_counts": {
    "improved": 4,
    "noop": 2
  },
  "missing_rmp_fields": 0,
  "present_rmp_fields": 17,
  "priority_capture_miss_exact_hit_context_count": 0,
  "priority_capture_miss_expected_context_count": 3,
  "priority_capture_miss_same_active_component_drift_context_count": 1,
  "priority_capture_miss_source_active_hash_missing_context_count": 2,
  "recovered_from_event_history": 8,
  "requires_capture_schema_extension": 0,
  "requires_event_history_join": 0,
  "requires_manifest_pass_through": 0,
  "requires_metric_definition": 0,
  "robust_enriched_features": [],
  "robust_models": [],
  "robust_single_features": [],
  "same_active_hash_is_not_sufficient": true,
  "selector_blocker_count": 6,
  "selector_context_action_plan_complete_snapshot_action_count": 7,
  "selector_context_action_plan_unresolved_action_count": 5,
  "selector_context_action_plan_unresolved_execution_category_counts": {
    "full_component_match_required": 1,
    "run_or_reaudit_existing_manifest_command": 1,
    "source_mapping_recovery_required": 1,
    "trajectory_variant_capture_required": 2
  },
  "selector_holdout_blocker_collection_expected_count": 10,
  "selector_holdout_blocker_collection_hit_count": 9,
  "selector_holdout_blocker_complete_explicit_forbidden_label_counts": {
    "improved": 48
  },
  "selector_holdout_blocker_complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "selector_holdout_blocker_priority_expected_count": 3,
  "selector_holdout_blocker_priority_hit_count": 0,
  "selector_holdout_blocker_status": "selector_holdout_blocked_by_snapshot_label_mix",
  "selector_holdout_gap_complete_explicit_label_counts": {
    "improved": 48
  },
  "selector_holdout_gap_complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "selector_holdout_gap_complete_snapshot_rows": 62,
  "selector_holdout_gap_mixed_context_count": 0,
  "selector_holdout_gap_total_candidate_rows": 630,
  "selector_status": "production_selector_not_validated",
  "source_profile_rerun_is_not_sufficient": true
}
```

## 已排除解释

### Pulse 接线、物化或证书语义是主因

状态：`ruled_out_as_primary_root_cause`

Worker/capture paths can safely add or record true-RC negative journeys without critical disagreement; the remaining failure is ROI.

```json
{
  "code_boundary_pass": true,
  "phase8q_added_journeys": 10,
  "phase8q_added_new_task_sets": 8,
  "phase8q_all_time_limit": true
}
```

### 只要找更多或更负 true-RC negative columns 就会优化

状态：`ruled_out_as_sufficient_condition`

20-task runs can add true-RC negative journeys, including new task sets, but Phase 7O/8Q still end in TIME_LIMIT.

```json
{
  "phase7o_all_time_limit": true,
  "phase7o_nonbaseline_rows": 96,
  "phase7o_nonbaseline_worsened_rows": 96,
  "phase7o_worker_added_journeys": 63,
  "phase7o_worker_added_new_task_sets": 30,
  "phase8q_added_journeys": 10,
  "phase8q_added_new_task_sets": 8,
  "phase8q_all_time_limit": true,
  "phase8q_completion_bound_retry_count": 0,
  "phase8q_improved_without_worker_added_count": 1,
  "phase8q_worker_added_journeys": 10,
  "phase8q_worker_added_rows": 3,
  "worker_negative_roi_blocker_status": "worker_negative_columns_not_sufficient_for_roi"
}
```

### 扩大 worker 预算或默认启用 worker

状态：`ruled_out_for_5_10_safety`

5/10 scale is fixed-overhead sensitive: triggered mechanisms consistently worsen wall time, while non-triggered rows preserve official results.

```json
{
  "nontriggered_official_changed": 0,
  "triggered_better_count": 0,
  "triggered_rows": 220,
  "triggered_worse_count": 220
}
```

### 用 true-RC 阈值或局部列形状做 selector 已足够

状态：`not_production_validated`

Replay-local selector candidates exist, but exact holdout still has false positives and false negatives; mixed task-set/sequence groups prove local column shape is insufficient.

```json
{
  "exact_false_negative_count": 31,
  "exact_false_positive_count": 22,
  "false_negative_new_task_set_improved_count": 23,
  "false_positive_new_task_set_noop_count": 21,
  "perfect_threshold_count": 0,
  "recommended_selector_candidate": "true_reduced_cost_<=_-12.430587",
  "task_sequence_mixed_group_count": 5,
  "task_set_mixed_group_count": 6,
  "task_set_true_rc_improved_lower_count": 2,
  "task_set_true_rc_noop_lower_count": 4
}
```

### 重跑 source profile 或只匹配 active hash 就足够补齐 selector holdout

状态：`ruled_out_as_sufficient_condition`

Priority capture produced safe no-certificate-effect events, but hit 0/3 expected contexts. Two targets did not reach the source active hash, and one same-active case drifted in pool/forbidden/returned-batch components, so source-profile rerun and active-hash-only matching are not sufficient evidence for selector holdout.

```json
{
  "context_trajectory_protocol_status": "selector_context_trajectory_capture_protocol_ready",
  "exact_hit_context_count": 0,
  "expected_context_count": 3,
  "observed_event_count": 12,
  "priority_capture_miss_status": "selector_holdout_priority_capture_miss_diagnosed",
  "same_active_component_drift_context_count": 1,
  "same_active_hash_is_not_sufficient": true,
  "selector_context_action_plan_status": "selector_holdout_context_action_plan_ready",
  "selector_context_action_plan_unresolved_action_count": 5,
  "selector_context_action_plan_unresolved_execution_category_counts": {
    "full_component_match_required": 1,
    "run_or_reaudit_existing_manifest_command": 1,
    "source_mapping_recovery_required": 1,
    "trajectory_variant_capture_required": 2
  },
  "source_active_hash_missing_context_count": 2,
  "source_profile_rerun_is_not_sufficient": true
}
```

## 为什么这不是已完成目标

当前仍缺三项硬证据：

```text
missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup
```

含义是：根因解释已经有证据，但生产优化方向仍未证明。不能把
worker 找到负列、单 context replay 成功、或 calibration threshold 当成
5/10 不退化且 20-task 大幅加速的证明。

## 下一步只能补的证据

- 继续扩展 component-payload / full-snapshot addition-before rows 的负例和 mixed context 分布
- 按完整 context 组件捕获目标轨迹；不能用 source profile 重跑或 active hash 近似替代 exact context
- 只用 addition-before 特征通过 context / instance / dataset selector holdout
- 之后才做 full BPC A/B：先 5/10 no-regression，再 selected 20 hard-repeat speedup

## 检查项

```json
{
  "active_basis_counterexamples_present": true,
  "component_payload_extension_still_not_production": true,
  "component_payload_rows_constructed_but_not_production": true,
  "context_trajectory_protocol_requires_exact_components": true,
  "goal_still_active": true,
  "ledger_core_status_consistent": true,
  "missing_requirements_match_expected": true,
  "multifeature_selector_not_robust": true,
  "negative_columns_not_sufficient": true,
  "priority_capture_miss_blocks_source_profile_rerun_shortcut": true,
  "production_ab_still_blocked": true,
  "rmp_feature_gap_present": true,
  "selector_blocker_passed": true,
  "selector_context_action_plan_confirms_unresolved_context_actions": true,
  "selector_holdout_blocker_status_confirms_snapshot_label_mix_gap": true,
  "selector_holdout_gap_requires_negative_mixed_contexts": true,
  "single_feature_selector_not_robust": true,
  "small_overhead_evidence_present": true,
  "worker_negative_column_roi_blocker_confirms_negative_columns_not_sufficient": true
}
```
