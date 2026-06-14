# Selector Rule-Family Search 审计

日期：2026-06-14

## 目标

在现有 exact replay candidate rows 上，扩大只读 selector 搜索范围：
不仅检查单特征，还检查最多两个 addition-before 条件的 conjunction。
该审计不运行求解器，不修改 production path，也不把 full-sample hindsight
规则当作可上线 selector。

## 结论

all_checks_pass = true
selector_rule_family_search = current
task_count_filter = None
row_count = 280
label_counts = {'noop': 71, 'improved': 209}
context_count = 28
instance_count = 4
impact_dataset_count = 5
single_clause_count = 948
rule_count = 18887
strict_all_fold_passing_rule_count = 0
material_all_fold_passing_rule_count = 0
production_validated_selector = false

解释：full sample 上仍有明显 calibration signal，但即使把搜索扩展到
单 clause + 两 clause conjunction，也没有规则能跨 context / instance / dataset
全部 fold 稳定通过。`material_all_fold` 已经允许 no-positive fold 在不产生
false positive 时通过，因此这个失败不是单纯被空正例 fold 卡死。

## Top Full-Sample Rules

| Rule | Precision | Recall | TP | FP | FN | Predicted |
|---|---:|---:|---:|---:|---:|---:|
| cost>=73.9194 AND true_reduced_cost<=-3.82619 | 0.839357 | 1.000000 | 209 | 40 | 0 | 249 |
| cost>=73.9194 AND rc_per_task<=-0.979531 | 0.839357 | 1.000000 | 209 | 40 | 0 | 249 |
| true_reduced_cost<=-6.72239 AND cost>=73.9194 | 0.860169 | 0.971292 | 203 | 33 | 6 | 236 |
| rc_per_task<=-2.2408 AND cost>=73.9194 | 0.860169 | 0.971292 | 203 | 33 | 6 | 236 |
| true_reduced_cost<=-6.11073 AND cost>=73.9194 | 0.860169 | 0.971292 | 203 | 33 | 6 | 236 |
| cost>=73.9194 AND rc_per_task<=-2.23359 | 0.860169 | 0.971292 | 203 | 33 | 6 | 236 |
| true_reduced_cost<=-8.18679 AND cost>=73.9194 | 0.866379 | 0.961722 | 201 | 31 | 8 | 232 |
| rc_per_task<=-2.72893 AND cost>=73.9194 | 0.866379 | 0.961722 | 201 | 31 | 8 | 232 |
| true_reduced_cost<=-5.95739 AND cost>=73.9194 | 0.856540 | 0.971292 | 203 | 34 | 6 | 237 |
| cost>=73.9194 AND true_reduced_cost<=-5.52759 | 0.856540 | 0.971292 | 203 | 34 | 6 | 237 |

## Best Rule Fold Failure Sample

```text
best_rule = cost>=73.9194 AND true_reduced_cost<=-3.82619
best_full_sample = {'total': 280, 'predicted_positive': 249, 'tp': 209, 'fp': 40, 'tn': 31, 'fn': 0, 'precision': 0.8393574297188755, 'recall': 1.0, 'accuracy': 0.8571428571428571}
```

### context_hash

```text
strict_passing_fold_count = 19/28
material_passing_fold_count = 20/28
worst_folds = [{'holdout': '46e7a2883459d4fb', 'precision': None, 'recall': None, 'tp': 0, 'fp': 0, 'fn': 0}, {'holdout': '3f914a0d2b97fd27', 'precision': 0.0, 'recall': None, 'tp': 0, 'fp': 1, 'fn': 0}, {'holdout': '7b9a35f8f7c6581a', 'precision': 0.0, 'recall': None, 'tp': 0, 'fp': 1, 'fn': 0}]
```

### instance

```text
strict_passing_fold_count = 3/4
material_passing_fold_count = 3/4
worst_folds = [{'holdout': 'very_small', 'precision': 0.0, 'recall': None, 'tp': 0, 'fp': 1, 'fn': 0}, {'holdout': 'tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001', 'precision': 0.7777777777777778, 'recall': 1.0, 'tp': 63, 'fp': 18, 'fn': 0}, {'holdout': 'apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000', 'precision': 0.851063829787234, 'recall': 1.0, 'tp': 120, 'fp': 21, 'fn': 0}]
```

### impact_dataset

```text
strict_passing_fold_count = 4/5
material_passing_fold_count = 4/5
worst_folds = [{'holdout': 'duplicate_noop_smoke', 'precision': 0.0, 'recall': None, 'tp': 0, 'fp': 1, 'fn': 0}, {'holdout': 'root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613', 'precision': 0.7647058823529411, 'recall': 1.0, 'tp': 117, 'fp': 36, 'fn': 0}, {'holdout': 'root_cause_target002_capture_pt03_r3_20260613', 'precision': 0.9538461538461539, 'recall': 1.0, 'tp': 62, 'fp': 3, 'fn': 0}]
```

## 解释

这进一步收紧当前根因判断：问题不是缺少一个简单阈值、布尔条件或
两个局部特征的组合。returned batch 是否有用仍然依赖 context / RMP
trajectory。下一步若继续 selector 路线，必须继续扩展 no-certificate-effect
exact-context replay，并寻找可泛化的 RMP/context 特征；不能把这些
full-sample calibration 规则接入 production worker。
