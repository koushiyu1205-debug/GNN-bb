# Selector Micro-vs-Fold Gate 审计

日期：2026-06-14

## 目标

复查 exact replay selector gate 中看似通过的单特征规则，确认它们是否只是
micro-average 通过，还是每个 context / instance / dataset fold 都稳定通过。
本脚本只读已有 selector gate summary，不运行求解器。

## 结论

all_checks_pass = true
selector_micro_vs_fold_gate = current
row_count = 280
label_counts = {'improved': 209, 'noop': 71}
micro_passing_features = ['true_reduced_cost', 'cost', 'new_task_set', 'strict_replacement_by_cost']
robust_all_fold_passing_feature_count = 0

关键结论：旧 gate 的 `passing_features_all_holdouts` 是 micro-average 通过；
这些特征没有一个能在所有 held-out folds 上都过严格门槛。

## Feature Fold Summary

| Feature | Holdout | Micro P/R | Passing Folds | All Folds Pass | Failing Folds |
|---|---|---:|---:|---:|---:|
| true_reduced_cost | context_hash | 0.846535/0.818182 | 13/28 | false | 15 |
| true_reduced_cost | instance | 0.863309/0.574163 | 2/4 | false | 2 |
| true_reduced_cost | impact_dataset | 0.859296/0.818182 | 4/5 | false | 1 |
| cost | context_hash | 0.831081/0.588517 | 11/28 | false | 17 |
| cost | instance | 0.818182/0.732057 | 3/4 | false | 1 |
| cost | impact_dataset | 0.788793/0.875598 | 2/5 | false | 3 |
| new_task_set | context_hash | 0.793249/0.899522 | 16/28 | false | 12 |
| new_task_set | instance | 0.793249/0.899522 | 3/4 | false | 1 |
| new_task_set | impact_dataset | 0.793249/0.899522 | 3/5 | false | 2 |
| strict_replacement_by_cost | context_hash | 0.789916/0.899522 | 16/28 | false | 12 |
| strict_replacement_by_cost | instance | 0.789916/0.899522 | 3/4 | false | 1 |
| strict_replacement_by_cost | impact_dataset | 0.789916/0.899522 | 3/5 | false | 2 |

## 关键失败模式

```text
true_rc_context_micro_precision = 0.846535
true_rc_context_micro_recall = 0.818182
true_rc_context_passing_folds = 13/28
new_task_set_dataset_micro_precision = 0.793249
new_task_set_dataset_micro_recall = 0.899522
new_task_set_dataset_passing_folds = 3/5
robust_all_fold_passing_feature_count = 0
production_validated_selector = false
```

解释：row-level micro average 会被大 fold 和重复 candidate rows 主导；
但生产 selector 要面对的是新的 context / instance / dataset，不应依赖某些
held-out folds 失败后仍被总体 micro average 掩盖的规则。
