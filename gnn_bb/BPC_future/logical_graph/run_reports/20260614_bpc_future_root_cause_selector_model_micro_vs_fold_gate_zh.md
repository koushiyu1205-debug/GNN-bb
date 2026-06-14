# Selector Model Micro-vs-Fold Gate 审计

日期：2026-06-14

## 目标

复查 exact replay model selector gate 中看似通过的简单模型，确认它们是否
只是 aggregate micro 通过，还是每个 context / instance / dataset fold 都稳定通过。
本脚本只读已有 model selector gate summary，不重新运行求解器。

## 结论

all_checks_pass = true
selector_model_micro_vs_fold_gate = current
row_count = 280
label_counts = {'improved': 209, 'noop': 71}
aggregate_all_holdout_models = ['nearest_centroid', 'shallow_tree_depth3']
robust_all_fold_passing_model_count = 0

关键结论：`nearest_centroid` / `shallow_tree_depth3` 等模型有 aggregate
 calibration signal，但没有任何模型能在所有 held-out folds 上都过严格门槛。

## Model Fold Summary

| Model | Holdout | Aggregate P/R | Passing Folds | All Folds Pass | Failing Folds |
|---|---|---:|---:|---:|---:|
| linear_mean_diff | leave_one_context | 0.768627/0.937799 | 16/28 | false | 12 |
| linear_mean_diff | leave_one_instance | 0.734082/0.937799 | 1/4 | false | 3 |
| linear_mean_diff | leave_one_dataset | 0.768627/0.937799 | 3/5 | false | 2 |
| nearest_centroid | leave_one_context | 0.823810/0.827751 | 16/28 | false | 12 |
| nearest_centroid | leave_one_instance | 0.815315/0.866029 | 3/4 | false | 1 |
| nearest_centroid | leave_one_dataset | 0.789474/0.861244 | 3/5 | false | 2 |
| shallow_tree_depth3 | leave_one_context | 0.800926/0.827751 | 15/28 | false | 13 |
| shallow_tree_depth3 | leave_one_instance | 0.837398/0.985646 | 3/4 | false | 1 |
| shallow_tree_depth3 | leave_one_dataset | 0.838843/0.971292 | 4/5 | false | 1 |

## 关键失败模式

```text
nearest_centroid_context_aggregate_precision = 0.823810
nearest_centroid_context_aggregate_recall = 0.827751
nearest_centroid_context_passing_folds = 16/28
shallow_tree_dataset_aggregate_precision = 0.838843
shallow_tree_dataset_aggregate_recall = 0.971292
shallow_tree_dataset_passing_folds = 4/5
robust_all_fold_passing_model_count = 0
production_validated_selector = false
```

解释：模型 gate 的 aggregate P/R 能说明当前 replay 样本里有 signal，
但不能证明 selector 在新 context / instance / dataset 上稳定。生产化需要
每个 held-out fold 或更严格外部 A/B 都稳定，而当前没有达到。
