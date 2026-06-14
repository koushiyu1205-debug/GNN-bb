# Active-basis Snapshot Selector Signal 审计报告

日期：2026-06-14

## 目标

本报告只读已经生成的 active-basis snapshot smoke impact rows，检查这些新字段是否已经进入 selector 数据层，以及当前小样本是否足以支持 production selector。

它不运行 BPC / pricing / replay / worker / certificate。

## 关键结果

```text
all_checks_pass = true
row_count = 14
task20_row_count = 12
label_counts = {'improved': 11, 'noop': 3}
task20_label_counts = {'improved': 10, 'noop': 2}
task20_new_task_set_row_count = 12
snapshot_complete_count = 14
active_basis_churn_nonempty_count = 14
rmp_degeneracy_pressure_nonempty_count = 14
perfect_single_feature_rule_count = 0
```

## 20-task True-RC Threshold

```json
{
  "accuracy": 0.8333333333333334,
  "fn": 0,
  "fp": 2,
  "precision": 0.8333333333333334,
  "predicted_positive": 12,
  "recall": 1.0,
  "tn": 0,
  "total": 12,
  "tp": 10
}
```

## Mixed Instance Groups

```json
[
  {
    "active_basis_churn": [
      0.0,
      4.0
    ],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "label_counts": {
      "improved": 1,
      "noop": 1
    },
    "row_count": 2,
    "task_sets": [
      "5,8,15",
      "5,12,18"
    ],
    "true_reduced_costs": [
      -139.913748,
      -128.547499
    ]
  },
  {
    "active_basis_churn": [
      0.0,
      15.0
    ],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205",
    "label_counts": {
      "improved": 1,
      "noop": 1
    },
    "row_count": 2,
    "task_sets": [
      "2,18,20",
      "2,10,18"
    ],
    "true_reduced_costs": [
      -130.406733,
      -41.9490035
    ]
  },
  {
    "active_basis_churn": [
      0.0,
      4.0
    ],
    "instance": "very_small",
    "label_counts": {
      "improved": 1,
      "noop": 1
    },
    "row_count": 2,
    "task_sets": [
      "3,4",
      "1,4"
    ],
    "true_reduced_costs": [
      -7.631622,
      -5.20414
    ]
  }
]
```

## Best Single Feature Rules

```json
[
  {
    "feature": "true_reduced_cost",
    "metrics": {
      "accuracy": 0.8571428571428571,
      "fn": 0,
      "fp": 2,
      "precision": 0.8461538461538461,
      "predicted_positive": 13,
      "recall": 1.0,
      "tn": 1,
      "total": 14,
      "tp": 11
    },
    "operator": "<=",
    "threshold": -7.631622
  },
  {
    "feature": "active_basis_journey_count_before",
    "metrics": {
      "accuracy": 0.7857142857142857,
      "fn": 0,
      "fp": 3,
      "precision": 0.7857142857142857,
      "predicted_positive": 14,
      "recall": 1.0,
      "tn": 0,
      "total": 14,
      "tp": 11
    },
    "operator": "<=",
    "threshold": 17.0
  },
  {
    "feature": "active_basis_churn_count_before",
    "metrics": {
      "accuracy": 0.7857142857142857,
      "fn": 0,
      "fp": 3,
      "precision": 0.7857142857142857,
      "predicted_positive": 14,
      "recall": 1.0,
      "tn": 0,
      "total": 14,
      "tp": 11
    },
    "operator": "<=",
    "threshold": 18.0
  },
  {
    "feature": "rmp_degeneracy_pressure_before",
    "metrics": {
      "accuracy": 0.7857142857142857,
      "fn": 0,
      "fp": 3,
      "precision": 0.7857142857142857,
      "predicted_positive": 14,
      "recall": 1.0,
      "tn": 0,
      "total": 14,
      "tp": 11
    },
    "operator": "<=",
    "threshold": 1.882352941
  },
  {
    "feature": "column_pool_size_before",
    "metrics": {
      "accuracy": 0.7857142857142857,
      "fn": 0,
      "fp": 3,
      "precision": 0.7857142857142857,
      "predicted_positive": 14,
      "recall": 1.0,
      "tn": 0,
      "total": 14,
      "tp": 11
    },
    "operator": "<=",
    "threshold": 251.0
  }
]
```

## Checks

```json
{
  "active_basis_churn_populated": true,
  "all_audit_summaries_no_certificate_effect": true,
  "all_rows_have_active_basis_snapshot": true,
  "audit_summaries_exist": true,
  "dataset_is_too_small_for_production_holdout": true,
  "has_high_impact_and_noop_rows": true,
  "has_snapshot_rows": true,
  "has_twenty_scale_rows": true,
  "inputs_exist": true,
  "rmp_degeneracy_pressure_populated": true,
  "true_rc_threshold_has_false_positive_on_twenty": true,
  "twenty_new_task_set_contains_high_and_noop": true
}
```

## 解释

这 14 行 snapshot rows 证明 full active-basis 字段已经能进入 candidate impact rows；其中 12 行是 20-task，全部是 new task-set，且 true-RC 都明显为负。

但 20-task 行中同时存在 high-impact 和 noop，`true_reduced_cost <= -12.430587` 在这个小样本上已有 false positive。因此不能把 true-RC 阈值、new-task-set 或任意单个 snapshot scalar 当成 production selector。

这个报告支持当前根因判断：下一步仍需要扩展 no-certificate-effect exact-context snapshot 数据，并在 context / instance / dataset holdout 上验证 addition-before selector；它本身不是 5/10 no-regression 或 20-task speedup 证明。
