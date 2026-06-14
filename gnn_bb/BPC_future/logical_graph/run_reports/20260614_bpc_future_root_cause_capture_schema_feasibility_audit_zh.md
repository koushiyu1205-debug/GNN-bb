# Capture Schema Feasibility Audit 报告

日期：2026-06-14

## 目的

本报告回答一个很具体的问题：当前 selector 缺的 RMP/context trajectory
字段，是已经在 capture/manifest 里只是没有进入 candidate rows，还是必须
扩展 no-certificate-effect 采集 schema。

该审计只读 existing summary / manifest / CSV，不运行 BPC / pricing / RMP / Pulse，
也不改变 worker、certificate 或 official lower bound。

## 机器字段

```text
capture_schema_feasibility_audit = current
diagnostic_only = true
runs_bpc_or_pricing = false
impact_dataset_count = 5
candidate_row_count = 280
manifest_case_count = 82
desired_present_in_candidate_rows_count = 17
desired_missing_in_candidate_rows_count = 0
direct_or_alias_available_field_count = 3
derivable_from_manifest_field_count = 4
recovered_from_event_history_field_count = 8
active_basis_snapshot_metric_field_count = 2
requires_metric_definition_count = 0
requires_manifest_pass_through_count = 0
requires_event_history_join_count = 0
requires_capture_schema_extension_count = 0
complete_pool_case_count = 82
all_checks_pass = true
```

## 已进入 candidate rows 的目标字段

```text
desired_present_in_candidate_rows = active_hash_before,active_basis_size_before,active_basis_unique_task_set_count_before,active_basis_churn_count_before,dual_hash_before,dual_l1_norm_before,dual_linf_norm_before,column_pool_size_before,duplicate_signature_pool_count_before,task_set_pool_count_before,lambda_active_count_before,lambda_fractional_count_before,rmp_degeneracy_pressure_before,recent_objective_delta_before,recent_dual_l1_delta_before,recent_added_column_acceptance_rate_before,pricing_tail_retry_count_before
desired_missing_in_candidate_rows = 
```

## 字段分类

```text
active_hash_before: available_in_candidate_rows_from_manifest_or_alias
active_basis_size_before: recovered_in_candidate_rows_from_event_history
active_basis_unique_task_set_count_before: recovered_in_candidate_rows_from_event_history
active_basis_churn_count_before: available_in_candidate_rows_from_active_basis_snapshot_metric
dual_hash_before: available_in_candidate_rows_from_manifest_or_alias
dual_l1_norm_before: derivable_in_candidate_rows_from_manifest
dual_linf_norm_before: derivable_in_candidate_rows_from_manifest
column_pool_size_before: available_in_candidate_rows_from_manifest_or_alias
duplicate_signature_pool_count_before: derivable_in_candidate_rows_from_manifest
task_set_pool_count_before: derivable_in_candidate_rows_from_manifest
lambda_active_count_before: recovered_in_candidate_rows_from_event_history
lambda_fractional_count_before: recovered_in_candidate_rows_from_event_history
rmp_degeneracy_pressure_before: available_in_candidate_rows_from_active_basis_snapshot_metric
recent_objective_delta_before: recovered_in_candidate_rows_from_event_history
recent_dual_l1_delta_before: recovered_in_candidate_rows_from_event_history
recent_added_column_acceptance_rate_before: recovered_in_candidate_rows_from_event_history
pricing_tail_retry_count_before: recovered_in_candidate_rows_from_event_history
```

## 解释

现有 exact-context capture/manifest 已经包含部分可用的 RMP/context 字段，尤其是 true_dual_hash、true_dual_vector、pool_journey_count 和完整 pool_journeys；当前 candidate_impact_rows.csv 已补入 17 个可从 manifest 透传、派生或从 source JSONL 事件历史恢复的目标 RMP 轨迹字段，其中 active-basis churn 和 RMP degeneracy pressure 已有full-snapshot 指标定义，但旧 replay 证据包多数没有 full active-basis snapshot 值。因此下一步只能继续做离线 snapshot 采集和 selector holdout，不能进入 production A/B、默认 worker 或 certificate gate。

## 下一步边界

- 可以做：打开 default-off active-basis snapshot capture 重新采集 no-certificate-effect exact-context 数据。
- 可以做：用包含 snapshot 值的 candidate rows 重新做 context / instance / dataset holdout。
- 不能做：把当前 selector 直接进入 production A/B。
- 不能做：默认启用 Pulse worker 或打开 official certificate gate。
