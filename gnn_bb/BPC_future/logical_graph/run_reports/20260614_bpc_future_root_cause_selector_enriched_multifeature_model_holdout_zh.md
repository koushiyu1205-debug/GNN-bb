# Enriched Multifeature Model Holdout 审计

日期：2026-06-14

## 目的

本报告检查 local column features 加上已补入的 RMP/context trajectory 字段后，
简单多字段模型是否已经能通过 context / instance / dataset 每个 held-out fold。
审计只读 `candidate_impact_rows.csv`，不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
selector_enriched_multifeature_model_holdout = current
diagnostic_only = true
runs_bpc_or_pricing = false
row_count = 280
label_counts = {'noop': 71, 'improved': 209}
model_features_count = 27
enriched_features_count = 18
best_context_model = shallow_tree_depth3
robust_all_holdout_model_count = 0
all_checks_pass = true
```

## Model Holdout Summary

| Model | Context folds | Instance folds | Dataset folds | Context micro P/R |
|---|---:|---:|---:|---:|
| nearest_centroid | 13/28 | 4/4 | 4/5 | 0.871166/0.679426 |
| linear_mean_diff | 15/28 | 2/4 | 3/5 | 0.789683/0.952153 |
| shallow_tree_depth3 | 15/28 | 1/4 | 4/5 | 0.801282/0.598086 |

## 关键数字

```text
best_context_model = shallow_tree_depth3
best_context_model_context_folds = 15/28
best_context_model_instance_folds = 1/4
best_context_model_dataset_folds = 4/5
robust_all_holdout_models = 
production_validated_selector = false
```

## 结论

Adding the currently available RMP/context trajectory fields and addition-before churn/degeneracy proxy fields to small multifeature models does not produce a selector that passes every context, instance, and dataset fold. The production selector blocker remains active.

因此当前 enriched/proxy features 可以继续作为 calibration 输入，但还不能作为
production-safe 优化方向。下一步不能只靠简单 proxy selector，
需要更真实的 RMP 稳定化/退化处理证据。
