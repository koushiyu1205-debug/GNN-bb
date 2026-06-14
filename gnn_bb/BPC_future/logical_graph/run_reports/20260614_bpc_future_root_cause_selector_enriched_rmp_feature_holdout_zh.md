# Enriched RMP Feature Holdout 审计

日期：2026-06-14

## 目的

本报告检查新进入 candidate rows 的 RMP/context trajectory 字段是否已经足以
形成 production selector。审计只读 `candidate_impact_rows.csv`，不运行 BPC /
pricing / RMP / Pulse。

## 机器字段

```text
selector_enriched_rmp_feature_holdout = current
diagnostic_only = true
runs_bpc_or_pricing = false
row_count = 280
label_counts = {'noop': 71, 'improved': 209}
enriched_rmp_features = active_basis_size_before,active_basis_unique_task_set_count_before,dual_l1_norm_before,dual_linf_norm_before,column_pool_size_before,duplicate_signature_pool_count_before,task_set_pool_count_before,lambda_active_count_before,lambda_fractional_count_before,active_basis_hash_churn_count_before,active_basis_hash_unique_count_before,rmp_degeneracy_proxy_score_before,recent_objective_delta_before,recent_dual_l1_delta_before,recent_added_column_acceptance_rate_before,pricing_tail_retry_count_before
robust_all_holdout_enriched_feature_count = 0
robust_all_holdout_numeric_feature_count = 0
all_checks_pass = true
```

## Holdout Summary

| Feature | Type | Context folds | Instance folds | Dataset folds |
|---|---|---:|---:|---:|
| true_reduced_cost | reference | 19/28 | 3/4 | 4/5 |
| cost | reference | 18/28 | 2/4 | 3/5 |
| control_objective | reference | 13/28 | 2/4 | 5/5 |
| rmp_objective_before | reference | 13/28 | 2/4 | 5/5 |
| active_basis_size_before | enriched | 11/28 | 2/4 | 4/5 |
| active_basis_unique_task_set_count_before | enriched | 11/28 | 2/4 | 4/5 |
| dual_l1_norm_before | enriched | 16/28 | 2/4 | 4/5 |
| dual_linf_norm_before | enriched | 12/28 | 0/4 | 2/5 |
| column_pool_size_before | enriched | 15/28 | 1/4 | 3/5 |
| duplicate_signature_pool_count_before | enriched | 1/28 | 1/4 | 1/5 |
| task_set_pool_count_before | enriched | 15/28 | 1/4 | 3/5 |
| lambda_active_count_before | enriched | 11/28 | 2/4 | 4/5 |
| lambda_fractional_count_before | enriched | 11/28 | 1/4 | 2/5 |
| active_basis_hash_churn_count_before | enriched | 14/28 | 2/4 | 4/5 |
| active_basis_hash_unique_count_before | enriched | 14/28 | 2/4 | 4/5 |
| rmp_degeneracy_proxy_score_before | enriched | 9/28 | 0/4 | 1/5 |
| recent_objective_delta_before | enriched | 17/28 | 1/4 | 3/5 |
| recent_dual_l1_delta_before | enriched | 16/28 | 1/4 | 3/5 |
| recent_added_column_acceptance_rate_before | enriched | 3/28 | 1/4 | 2/5 |
| pricing_tail_retry_count_before | enriched | 1/28 | 1/4 | 1/5 |

## 关键数字

```text
control_objective_context_folds = 13/28
rmp_objective_before_context_folds = 13/28
best_enriched_feature = recent_objective_delta_before
best_enriched_context_folds = 17/28
robust_all_holdout_enriched_features = 
robust_all_holdout_numeric_features = 
```

## 结论

The newly available RMP/context trajectory fields are valid addition-before calibration signals, but simple single-feature train-on-fold threshold rules still fail held-out contexts or instances. The selector remains calibration-only and is not a production optimization direction.

这说明当前 15 个已补 RMP trajectory 字段，加上 3 个 addition-before
diagnostic proxy，仍不能形成 production selector。
proxy 可以解释一部分 RMP 轨迹压力，但还不足以跨 context / instance /
dataset 稳定泛化。
