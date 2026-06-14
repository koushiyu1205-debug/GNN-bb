# Selector Feature Availability Audit 报告

日期：2026-06-14

## 目的

本报告审计当前 exact-context replay candidate rows 中有哪些字段可用，
哪些字段只能作为 replay 后标签，以及生产 selector 还缺哪些 RMP 轨迹字段值。
它只读 CSV/summary，不运行 solver，不改变 pricing / worker / certificate。

## 机器字段

```text
selector_feature_availability_audit = current
dataset_count = 5
row_count = 280
addition_before_present_count = 16
post_addition_label_present_count = 6
desired_rmp_trajectory_present_count = 17
desired_rmp_trajectory_missing_count = 0
all_checks_pass = true
```

## 可用字段分类

```text
addition_before_present = active_support_changing,cg_iter,control_objective,control_status,cost,duplicate_signature,new_task_set,pricing_kind,pricing_state,sequence,strict_replacement_by_cost,task_count,task_set,true_reduced_cost,vehicle_count,weak_replacement_or_duplicate
identity_or_diagnostic_present = candidate_id,case_id,context_hash,instance
post_addition_label_present = single_changed_journey_count,single_dual_l1_delta,single_impact_class,single_no_op_treatment,single_objective_delta,single_treatment_found
desired_rmp_trajectory_present = active_hash_before,active_basis_size_before,active_basis_unique_task_set_count_before,active_basis_churn_count_before,dual_hash_before,dual_l1_norm_before,dual_linf_norm_before,column_pool_size_before,duplicate_signature_pool_count_before,task_set_pool_count_before,lambda_active_count_before,lambda_fractional_count_before,rmp_degeneracy_pressure_before,recent_objective_delta_before,recent_dual_l1_delta_before,recent_added_column_acceptance_rate_before,pricing_tail_retry_count_before
desired_rmp_trajectory_missing = 
```

## 结论

当前 replay candidate rows 已有局部列特征、online flags、control objective，以及从 manifest 和 source JSONL 事件历史透传/派生出的active-basis / lambda / dual / pool-saturation / recent-trajectory 前置字段。active-basis churn 和 RMP degeneracy pressure 字段也已进入 candidate rows，但旧 replay 证据包多数没有 full active-basis snapshot 值。因此下一步仍不是直接上线 selector，而是重新采集no-certificate-effect exact-context snapshot 数据并重新做 holdout。
