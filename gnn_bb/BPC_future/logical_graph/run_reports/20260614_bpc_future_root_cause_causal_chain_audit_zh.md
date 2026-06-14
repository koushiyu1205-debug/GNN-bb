# BPC_future Root Cause Causal Chain Audit 报告

日期：2026-06-14

## 目的

本报告把当前根因判断整理成一条可复查因果链。它只读已有 summary，
不运行 BPC / pricing / RMP / Pulse，也不改变 worker 或 certificate 行为。

## 机器字段

```text
root_cause_causal_chain_audit = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = causal_chain_supported_but_direction_unapproved
causal_chain_node_count = 7
goal_complete = false
completion_decision = keep_goal_active
missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup
production_direction_approved = false
all_checks_pass = true
```

## 因果链

### observed_requirements_not_met

目标仍未满足：还缺 5/10 full no-regression、production selector 和 selected 20 wall-time speedup。

```json
{
  "completion_decision": "keep_goal_active",
  "goal_complete": false,
  "missing_requirements": [
    "five_ten_full_no_regression_ab",
    "production_validated_selector",
    "twenty_walltime_speedup"
  ]
}
```

### small_scale_fixed_overhead

5/10 的主要失败机制是触发式 worker/audit/probe 固定开销吃掉收益，不是缺少负列。

```json
{
  "nontriggered_official_changed": 0,
  "triggered_better_count": 0,
  "triggered_rows": 220,
  "triggered_worse_count": 220
}
```

### negative_columns_not_sufficient

20-task 上能找到和加入 true-RC negative columns，但这不是稳定加速的充分条件。

```json
{
  "has_20_walltime_speedup_evidence": false,
  "phase8q_added_journeys": 10,
  "phase8q_added_new_task_sets": 8,
  "phase8q_all_time_limit": true
}
```

### returned_batch_context_coupling

负列是否有用取决于 returned-batch composition 与当前 RMP active-basis/dual trajectory 的耦合。

```json
{
  "strongest_noop_true_rc": -128.547499,
  "task20_label_counts": {
    "improved": 10,
    "noop": 2
  },
  "task20_new_task_sets": 12,
  "weaker_improved_than_strongest_noop_count": 8
}
```

### selector_not_validated

现有 addition-before selector 信号还没有通过 context/instance/dataset holdout，因此不能进入 production A/B 或默认 worker。

```json
{
  "component_payload_extension_combined_robust_features": 0,
  "component_payload_extension_combined_robust_models": 0,
  "robust_models": [],
  "robust_single_features": [],
  "selector_holdout_gap_complete_snapshot_label_counts": {
    "improved": 59,
    "noop": 3
  },
  "selector_holdout_gap_mixed_context_count": 0,
  "selector_status": "production_selector_not_validated"
}
```

### exact_context_not_recoverable_by_shortcut

source profile 重跑和 active-hash-only 匹配不能补齐 selector holdout；必须捕获完整 context 组件。

```json
{
  "context_trajectory_exact_component_count": 9,
  "context_trajectory_required_payload_count": 9,
  "priority_capture_miss_exact_hit_context_count": 0,
  "priority_capture_miss_expected_context_count": 3,
  "priority_capture_miss_same_active_component_drift_context_count": 1,
  "priority_capture_miss_source_active_hash_missing_context_count": 2,
  "same_active_hash_is_not_sufficient": true,
  "source_profile_rerun_is_not_sufficient": true
}
```

### allowed_next_stage

下一步只能做 calibration-only selector holdout 数据扩展；production A/B、默认 worker、certificate gate 仍被阻塞。

```json
{
  "approved_production_direction_count": 0,
  "completion_blockers": [
    "production_selector",
    "five_ten_full_no_regression_ab",
    "selected_twenty_walltime_speedup"
  ],
  "direction_status": "direction_not_approved",
  "production_direction_approved": false,
  "recommended_next_stage": "selector_holdout_data_expansion"
}
```

## 结论

当前根因解释已由证据链支持，但 production optimization direction 仍未获批。
因此不能默认启用 worker、不能打开 official certificate gate，也不能把当前
calibration signal 当作 5/10 不退化和 20 大幅加速的证明。

## 检查项

```json
{
  "batch_context_coupling_supported": true,
  "current_answer_passed": true,
  "direction_not_approved": true,
  "exact_context_shortcut_ruled_out": true,
  "ledger_passed_and_goal_active": true,
  "negative_columns_not_sufficient": true,
  "selector_not_validated": true,
  "small_cause_supported": true,
  "why_passed": true
}
```
