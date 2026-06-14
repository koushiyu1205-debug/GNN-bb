# Selector Rule-Family Train-Holdout 审计

日期：2026-06-14

## 目标

对每个 held-out context / instance / dataset fold，只在训练折上选择
最优单条件或两条件 addition-before 规则，再评估该规则在测试折上的表现。
该审计只读已有 exact replay rows，不运行求解器，不接 production path。

## 结论

all_checks_pass = true
selector_rule_family_train_holdout = current
task_count_filter = 20
row_count = 279
label_counts = {'improved': 209, 'noop': 70}
context_count = 27
instance_count = 3
impact_dataset_count = 4
production_validated_selector = false

## Holdout Summary

| Holdout | Strict Passing Folds | Material Passing Folds | Micro P/R |
|---|---:|---:|---:|
| context_hash | 16/27 | 17/27 | 0.837500/0.961722 |
| instance | 3/3 | 3/3 | 0.848739/0.966507 |
| impact_dataset | 4/4 | 4/4 | 0.841004/0.961722 |

## Worst Fold Samples

### context_hash

```text
material_passing_fold_count = 17/27
worst_folds = [{'holdout': '46e7a2883459d4fb', 'selected_rule': 'cost>=73.9194 AND true_reduced_cost<=-3.82619', 'precision': None, 'recall': None, 'tp': 0, 'fp': 0, 'fn': 0}, {'holdout': '05695ab419abfb4b', 'selected_rule': 'true_reduced_cost<=-6.72239 AND cost>=73.9194', 'precision': None, 'recall': 0.0, 'tp': 0, 'fp': 0, 'fn': 3}, {'holdout': '1db815e33b9ea471', 'selected_rule': 'true_reduced_cost<=-6.72239 AND cost>=73.9194', 'precision': None, 'recall': 0.0, 'tp': 0, 'fp': 0, 'fn': 1}]
```

### instance

```text
material_passing_fold_count = 3/3
worst_folds = [{'holdout': 'tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001', 'selected_rule': 'cost>=73.9194 AND true_reduced_cost<=-3.82619', 'precision': 0.7777777777777778, 'recall': 1.0, 'tp': 63, 'fp': 18, 'fn': 0}, {'holdout': 'apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000', 'selected_rule': 'true_reduced_cost<=-8.18679 AND cost>=73.9194', 'precision': 0.8646616541353384, 'recall': 0.9583333333333334, 'tp': 115, 'fp': 18, 'fn': 5}, {'holdout': 'tranquillitatis_balmer_like_20km_tasks20_01_seed21000', 'selected_rule': 'cost>=75.069 AND true_reduced_cost<=-3.82619', 'precision': 1.0, 'recall': 0.9230769230769231, 'tp': 24, 'fp': 0, 'fn': 2}]
```

### impact_dataset

```text
material_passing_fold_count = 4/4
worst_folds = [{'holdout': 'root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613', 'selected_rule': 'true_reduced_cost<=-6.72239', 'precision': 0.7602739726027398, 'recall': 0.9487179487179487, 'tp': 111, 'fp': 35, 'fn': 6}, {'holdout': 'root_cause_target002_capture_pt03_r3_20260613', 'selected_rule': 'cost>=73.9194 AND true_reduced_cost<=-3.82619', 'precision': 0.9538461538461539, 'recall': 1.0, 'tp': 62, 'fp': 3, 'fn': 0}, {'holdout': 'root_cause_counterfactual_target_capture_dp1000_tranq20_20260613', 'selected_rule': 'cost>=75.069 AND true_reduced_cost<=-3.82619', 'precision': 1.0, 'recall': 0.9230769230769231, 'tp': 24, 'fp': 0, 'fn': 2}]
```

## 解释

这排除了另一个可能解释：不是因为 full-sample 规则选择方式不符合
训练流程才导致 selector 不稳。即使每个 fold 都重新用训练集选择规则，
测试 fold 仍不能全部通过。当前 selector 路线仍必须停留在 calibration-only。
