# Remaining RMP Trajectory Field Recovery Audit 报告

日期：2026-06-14

## 目的

本报告只回答一个问题：当前 selector 仍缺的 10 个 RMP trajectory 字段，
哪些能从已有 replay source JSONL 事件历史恢复，哪些仍需要新的 full
active-basis snapshot 数据。该审计不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
remaining_rmp_trajectory_field_recovery = current
diagnostic_only = true
runs_bpc_or_pricing = false
case_count = 82
source_file_exists_count = 82
unique_source_file_count = 25
remaining_field_count = 10
production_ready_field_count = 8
needs_metric_definition_fields = 
needs_full_active_basis_capture_fields = active_basis_churn_count_before,rmp_degeneracy_pressure_before
still_missing_or_partial_fields = active_basis_churn_count_before,rmp_degeneracy_pressure_before
all_checks_pass = true
```

## 字段恢复矩阵

```text
active_basis_size_before: recoverable_from_event_history_with_legacy_log_gap exact=81/82 partial=0/82 missing=1/82
active_basis_unique_task_set_count_before: recoverable_from_event_history_with_legacy_log_gap exact=81/82 partial=0/82 missing=1/82
active_basis_churn_count_before: partially_recoverable_existing_history_incomplete exact=0/82 partial=81/82 missing=1/82
lambda_active_count_before: recoverable_from_event_history_with_legacy_log_gap exact=81/82 partial=0/82 missing=1/82
lambda_fractional_count_before: recoverable_from_event_history_with_legacy_log_gap exact=81/82 partial=0/82 missing=1/82
rmp_degeneracy_pressure_before: partially_recoverable_existing_history_incomplete exact=0/82 partial=81/82 missing=1/82
recent_objective_delta_before: fully_recoverable_from_existing_event_history exact=82/82 partial=0/82 missing=0/82
recent_dual_l1_delta_before: fully_recoverable_from_existing_event_history exact=82/82 partial=0/82 missing=0/82
recent_added_column_acceptance_rate_before: fully_recoverable_from_existing_event_history exact=82/82 partial=0/82 missing=0/82
pricing_tail_retry_count_before: fully_recoverable_from_existing_event_history exact=82/82 partial=0/82 missing=0/82
```

## 解释

现有 JSONL 事件历史已经足以恢复一批 addition-before RMP trajectory 字段，例如 active basis size、lambda active/fractional count、recent objective/dual delta、prior addition acceptance 和 prior retry count。active-basis churn 和 RMP degeneracy pressure 的 full-snapshot 指标已经定义在 candidate row builder 中，但现有历史证据包仍缺完整active-basis snapshot，因此这两个字段还不能直接投入 production selector。因此问题不是 Pulse 还少一个参数，而是 selector 仍缺能在加列前判定 RMP 轨迹影响的上下文 schema。

## 下一步边界

- 可以做：用 active-basis snapshot capture 重新生成 replay rows，并重新跑 addition-before selector holdout。
- 已完成：active-basis churn 与 RMP degeneracy pressure 已有 full-snapshot 指标定义。
- 仍需做：采集包含完整 active-basis snapshot 的 no-certificate-effect exact-context 数据。
- 不能做：只因为 Pulse 能加 true-RC negative columns 就默认启用 worker。
- 不能做：在 selector 未验证前打开 production A/B 或 official certificate gate。
