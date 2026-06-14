# Production A/B Entry Gate Catalog 报告

日期：2026-06-14

## 目的

本报告只读当前 evidence ledger 和 production selector blocker catalog，明确
production BPC A/B 还不能启动的入口门槛。它不运行 solver，也不改变任何
worker / certificate 配置。

## 机器字段

```text
production_ab_entry_gate_catalog = current
production_candidate_ab_entry_status = blocked
production_candidate_ab = blocked
entry_gate_blockers = selector_not_validated,five_ten_full_no_regression_missing,twenty_speedup_missing
must_not_enable_worker_default = true
must_not_open_certificate_gate = true
requires_selector_holdout_before_ab = true
requires_5_10_full_no_regression_before_ab = true
requires_selected_20_speedup_before_ab = true
selector_feature_scope = addition_before_only
required_selector_holdouts = context/instance/dataset
forbidden_shortcuts = post_addition_or_hindsight_features,single_context_replay_success,worker_negative_columns_without_walltime_roi,certificate_effect
all_checks_pass = true
```

## 阻塞点

### 1. selector 仍未 production validated

```text
has_replay_calibrated_selector_candidate = true
has_production_validated_selector = false
production_selector_status = production_selector_not_validated
production_selector_blocker_count = 6
```

### 2. 5/10 full no-regression A/B 仍缺失

```text
has_task5_noop_no_regression_guard = true
has_task10_noop_no_regression_guard = true
has_task10_triggered_regression_evidence = true
has_full_5_10_production_ab_evidence = false
```

### 3. 20-task wall-time speedup 仍缺失

```text
has_20_negative_columns = true
has_local_rmp_impact = true
has_20_walltime_speedup_evidence = false
production_direction_proven = false
```

## 结论

当前 ledger 支持根因解释，但 production BPC A/B 入口仍被阻塞。原因不是没有 calibration signal，而是 selector 未通过生产 holdout，5/10 full no-regression A/B 缺失，20-task wall-time speedup 缺失。在这些门槛解除前，不应默认启用 worker，也不应打开 official certificate gate。
