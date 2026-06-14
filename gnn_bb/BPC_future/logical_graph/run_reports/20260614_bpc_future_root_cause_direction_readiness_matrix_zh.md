# Root Cause Direction Readiness Matrix 报告

日期：2026-06-14

## 目的

本报告把当前根因证据转成优化方向 readiness matrix。它只读已有
summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker 或
certificate 配置。

## 机器字段

```text
root_cause_direction_readiness_matrix = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = direction_not_approved
root_cause_supported = true
production_direction_approved = false
approved_production_direction_count = 0
goal_complete = false
recommended_next_stage = selector_holdout_data_expansion
completion_blockers = production_selector,five_ten_full_no_regression_ab,selected_twenty_walltime_speedup
all_checks_pass = true
```

## Readiness Gates

### root_cause_explanation

```text
status = passed
required_before_completion = true
```

根因解释已有证据支持：问题不是 Pulse 单点接线，而是固定开销、20-task true-RC 负列 ROI 和 addition-before selector 泛化共同作用。

```json
{
  "current_answer_all_checks_pass": true,
  "current_answer_status": "root_cause_supported_but_optimization_direction_unproven",
  "objective_root_cause_requirement": "proved"
}
```

### production_selector

```text
status = failed
required_before_completion = true
```

48 条 component payload 行能降低 schema gap，但它们全是正例；合并到 328 行后 robust all-holdout feature/model 仍为 0，不能形成 production selector。

```json
{
  "component_extension_base_rows": 280,
  "component_extension_combined_context_model_folds": "18/30",
  "component_extension_combined_robust_feature_count": 0,
  "component_extension_combined_robust_model_count": 0,
  "component_extension_combined_rows": 328,
  "component_extension_component_positive_only": true,
  "component_extension_component_rows": 48,
  "selector_blocker_ids": [
    "concrete_false_positive_and_false_negative_examples",
    "micro_average_gate_not_fold_stable",
    "aggregate_model_gate_not_fold_stable",
    "simple_rule_family_has_no_all_fold_rule",
    "train_holdout_rules_not_context_stable",
    "context_anatomy_has_opposite_failure_modes"
  ],
  "selector_status": "production_selector_not_validated"
}
```

### five_ten_full_no_regression_ab

```text
status = missing
required_before_completion = true
```

已有证据只能说明 no-op guard 可以保持小实例不被触发；还没有 full 5/10 production A/B 证明触发策略不退化。

```json
{
  "entry_blocker_present": true,
  "objective_missing_requirement_present": true
}
```

### selected_twenty_walltime_speedup

```text
status = missing
required_before_completion = true
```

20-task 上存在 true-RC negative columns 和局部 RMP impact，但尚未证明 selected hard 20 的 wall-time/gap/status/tail 改善。

```json
{
  "entry_blocker_present": true,
  "objective_missing_requirement_present": true,
  "production_direction_proven": false
}
```

### certificate_and_worker_safety_boundary

```text
status = passed_as_boundary_not_as_speedup
required_before_completion = false
```

exactness 边界是清楚的：当前不能默认启用 worker，不能打开 official certificate gate；这只是安全边界，不是优化成功证据。

```json
{
  "forbidden_shortcuts": [
    "post_addition_or_hindsight_features",
    "single_context_replay_success",
    "worker_negative_columns_without_walltime_roi",
    "certificate_effect"
  ],
  "must_not_enable_worker_default": true,
  "must_not_open_certificate_gate": true
}
```

### next_allowed_stage

```text
status = calibration_only
required_before_completion = false
```

下一步只能继续 addition-before selector holdout / 数据扩展，优先补 negative/noop 和 mixed full-snapshot contexts；最新 priority capture 证明补采链路安全，但没有命中目标 contexts，miss 诊断显示原因是 active hash 未到达和同 active 下组件漂移，因此还不能进入 production A/B、默认 worker 或 certificate gate。

```json
{
  "approved_production_direction_count": 0,
  "complete_explicit_forbidden_label_counts": {
    "improved": 48
  },
  "complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "complete_snapshot_mixed_context_count": 0,
  "holdout_gap_recommended_next_stage": "collect_negative_and_mixed_full_snapshot_contexts",
  "holdout_gap_status": "selector_holdout_gap_matrix_audited",
  "mixed_missing_full_snapshot_context_count": 7,
  "next_action_required_holdouts": [
    "context",
    "instance",
    "dataset"
  ],
  "next_action_status": "calibration_only_next_action",
  "noop_missing_full_snapshot_context_count": 12,
  "priority_capture_active_basis_bad_count": 0,
  "priority_capture_event_count": 12,
  "priority_capture_expected_context_hash_count": 3,
  "priority_capture_expected_context_hit_count": 0,
  "priority_capture_missing_expected_context_count": 3,
  "priority_capture_no_certificate_bad_count": 0,
  "priority_capture_ready_for_selector_holdout": false,
  "priority_capture_status": "selector_holdout_collection_capture_audited",
  "priority_context_count": 15,
  "priority_miss_exact_hit_context_count": 0,
  "priority_miss_expected_context_count": 3,
  "priority_miss_same_active_component_drift_context_count": 1,
  "priority_miss_source_active_hash_missing_context_count": 2,
  "priority_miss_status": "selector_holdout_priority_capture_miss_diagnosed",
  "priority_runbook_command_count": 1,
  "priority_runbook_commandable_context_count": 3,
  "priority_runbook_status": "selector_holdout_priority_collection_runbook_ready",
  "priority_runbook_unsupported_context_count": 3,
  "registry_allowed_stage": "calibration_only_selector_holdout",
  "target_priority_status": "selector_holdout_target_priority_matrix_audited",
  "uncovered_priority_context_count": 6
}
```

## 检查项

```json
{
  "completion_blockers_match_expected": true,
  "component_extension_is_not_selector": true,
  "component_extension_passed": true,
  "current_answer_passed": true,
  "entry_blockers_match_expected": true,
  "goal_must_remain_active": true,
  "holdout_gap_matrix_passed": true,
  "holdout_gap_requires_negative_mixed_contexts": true,
  "missing_requirements_match_expected": true,
  "next_action_passed": true,
  "no_approved_production_direction": true,
  "objective_audit_passed": true,
  "priority_capture_miss_explains_context_miss": true,
  "priority_collection_capture_safe_but_not_ready": true,
  "priority_collection_runbook_passed": true,
  "priority_runbook_not_selector_validation": true,
  "production_ab_gate_passed": true,
  "recommended_next_stage_is_selector_data": true,
  "registry_passed": true,
  "required_holdouts_match_expected": true,
  "selector_blocker_passed": true,
  "target_priority_identifies_uncovered_contexts": true,
  "target_priority_matrix_passed": true
}
```

## 结论

根因解释已经被当前证据支持，但 production optimization direction 没有获批。真正阻塞项仍是 production selector、5/10 full no-regression A/B 和 selected 20 wall-time speedup。下一步只允许扩展 no-certificate-effect addition-before selector holdout 数据，尤其是 negative/noop 和 mixed full-snapshot contexts；不能把 component payload calibration signal、worker 负列或局部 RMP impact 当作完成。
