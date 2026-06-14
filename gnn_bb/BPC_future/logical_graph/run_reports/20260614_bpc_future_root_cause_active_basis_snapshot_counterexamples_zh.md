# Active-basis Snapshot Counterexamples 审计报告

日期：2026-06-14

## 目标

本报告只读 no-certificate-effect active-basis snapshot impact rows，列出当前根因判断所依赖的具体反例。

它不运行 BPC / pricing / RMP / replay / worker / certificate。

## 关键结果

```text
all_checks_pass = true
row_count = 14
task20_row_count = 12
label_counts = {'improved': 11, 'noop': 3}
task20_label_counts = {'improved': 10, 'noop': 2}
task20_new_task_set_row_count = 12
false_positive_count = 2
weaker_improved_than_strongest_noop_count = 8
positive_churn_label_counts = {'noop': 2, 'improved': 4}
degeneracy_one_label_counts = {'improved': 3, 'noop': 2}
```

## False-positive Rows

```json
[
  {
    "active_basis_churn_count_before": 4,
    "active_basis_journey_count_before": 10,
    "cg_iter": 2,
    "column_pool_size_before": 165,
    "context_hash": "e55ea3e7d277b6d1",
    "control_objective": 921.640296,
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 1.0,
    "sequence": "12-18-5",
    "single_impact_class": "noop",
    "single_objective_delta": 0.0,
    "snapshot_dataset": "root_cause_active_basis_snapshot_mt20_smoke_20260614",
    "task_count": 20,
    "task_set": "5,12,18",
    "true_reduced_cost": -128.547499
  },
  {
    "active_basis_churn_count_before": 15,
    "active_basis_journey_count_before": 9,
    "cg_iter": 2,
    "column_pool_size_before": 251,
    "context_hash": "988c728382b4a376",
    "control_objective": 873.331193,
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 1.0,
    "sequence": "18-2-10",
    "single_impact_class": "noop",
    "single_objective_delta": 0.0,
    "snapshot_dataset": "root_cause_active_basis_snapshot_greedy20_pair_smoke_20260614",
    "task_count": 20,
    "task_set": "2,10,18",
    "true_reduced_cost": -41.9490035
  }
]
```

## Strongest Noop

```json
{
  "active_basis_churn_count_before": 4,
  "active_basis_journey_count_before": 10,
  "cg_iter": 2,
  "column_pool_size_before": 165,
  "context_hash": "e55ea3e7d277b6d1",
  "control_objective": 921.640296,
  "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
  "new_task_set": true,
  "rmp_degeneracy_pressure_before": 1.0,
  "sequence": "12-18-5",
  "single_impact_class": "noop",
  "single_objective_delta": 0.0,
  "snapshot_dataset": "root_cause_active_basis_snapshot_mt20_smoke_20260614",
  "task_count": 20,
  "task_set": "5,12,18",
  "true_reduced_cost": -128.547499
}
```

## Weaker Improved Examples

```json
[
  {
    "active_basis_churn_count_before": 0,
    "active_basis_journey_count_before": 15,
    "cg_iter": 1,
    "column_pool_size_before": 250,
    "context_hash": "8c60fac6ce5f475f",
    "control_objective": 800.4027645,
    "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 1.866666667,
    "sequence": "10-13-8",
    "single_impact_class": "improved",
    "single_objective_delta": -38.5883615,
    "snapshot_dataset": "root_cause_active_basis_snapshot_multi20_smoke_20260614",
    "task_count": 20,
    "task_set": "8,10,13",
    "true_reduced_cost": -38.7838905
  },
  {
    "active_basis_churn_count_before": 17,
    "active_basis_journey_count_before": 8,
    "cg_iter": 2,
    "column_pool_size_before": 251,
    "context_hash": "f67cf0852ea7df8b",
    "control_objective": 761.814403,
    "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 0.75,
    "sequence": "2-7-9",
    "single_impact_class": "improved",
    "single_objective_delta": -23.46338,
    "snapshot_dataset": "root_cause_active_basis_snapshot_multi20_smoke_20260614",
    "task_count": 20,
    "task_set": "2,7,9",
    "true_reduced_cost": -32.5008455
  },
  {
    "active_basis_churn_count_before": 0,
    "active_basis_journey_count_before": 13,
    "cg_iter": 1,
    "column_pool_size_before": 250,
    "context_hash": "c30ee076e24e6460",
    "control_objective": 838.0048415,
    "instance": "tranquillitatis_balmer_like_20km_tasks20_01_seed21000",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 1.538461538,
    "sequence": "20-15-5",
    "single_impact_class": "improved",
    "single_objective_delta": -56.9035325,
    "snapshot_dataset": "root_cause_active_basis_snapshot_multi20_smoke_20260614",
    "task_count": 20,
    "task_set": "5,15,20",
    "true_reduced_cost": -57.0891735
  },
  {
    "active_basis_churn_count_before": 14,
    "active_basis_journey_count_before": 9,
    "cg_iter": 2,
    "column_pool_size_before": 251,
    "context_hash": "8f9a20ae99268746",
    "control_objective": 781.101309,
    "instance": "tranquillitatis_balmer_like_20km_tasks20_01_seed21000",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 1.0,
    "sequence": "18-13-4",
    "single_impact_class": "improved",
    "single_objective_delta": -53.5053115,
    "snapshot_dataset": "root_cause_active_basis_snapshot_multi20_smoke_20260614",
    "task_count": 20,
    "task_set": "4,13,18",
    "true_reduced_cost": -53.518311
  },
  {
    "active_basis_churn_count_before": 0,
    "active_basis_journey_count_before": 10,
    "cg_iter": 1,
    "column_pool_size_before": 250,
    "context_hash": "ad8b0be13bd7bb93",
    "control_objective": 890.449593,
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 0.8,
    "sequence": "9-6-8",
    "single_impact_class": "improved",
    "single_objective_delta": -92.4295805,
    "snapshot_dataset": "root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_20260614",
    "task_count": 20,
    "task_set": "6,8,9",
    "true_reduced_cost": -97.163992
  },
  {
    "active_basis_churn_count_before": 14,
    "active_basis_journey_count_before": 12,
    "cg_iter": 2,
    "column_pool_size_before": 251,
    "context_hash": "d97c4048488f096c",
    "control_objective": 798.0200125,
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 1.416666667,
    "sequence": "7-16-15",
    "single_impact_class": "improved",
    "single_objective_delta": -62.6305895,
    "snapshot_dataset": "root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_20260614",
    "task_count": 20,
    "task_set": "7,15,16",
    "true_reduced_cost": -62.6305895
  }
]
```

## Mixed Task20 Instance Groups

```json
[
  {
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "label_counts": {
      "improved": 1,
      "noop": 1
    },
    "row_count": 2,
    "rows": [
      {
        "active_basis_churn_count_before": 0,
        "active_basis_journey_count_before": 12,
        "cg_iter": 1,
        "column_pool_size_before": 164,
        "context_hash": "080a188d2484ee3e",
        "control_objective": 1061.554044,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "new_task_set": true,
        "rmp_degeneracy_pressure_before": 1.0,
        "sequence": "8-15-5",
        "single_impact_class": "improved",
        "single_objective_delta": -139.913748,
        "snapshot_dataset": "root_cause_active_basis_snapshot_mt20_smoke_20260614",
        "task_count": 20,
        "task_set": "5,8,15",
        "true_reduced_cost": -139.913748
      },
      {
        "active_basis_churn_count_before": 4,
        "active_basis_journey_count_before": 10,
        "cg_iter": 2,
        "column_pool_size_before": 165,
        "context_hash": "e55ea3e7d277b6d1",
        "control_objective": 921.640296,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
        "new_task_set": true,
        "rmp_degeneracy_pressure_before": 1.0,
        "sequence": "12-18-5",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "snapshot_dataset": "root_cause_active_basis_snapshot_mt20_smoke_20260614",
        "task_count": 20,
        "task_set": "5,12,18",
        "true_reduced_cost": -128.547499
      }
    ]
  },
  {
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205",
    "label_counts": {
      "improved": 1,
      "noop": 1
    },
    "row_count": 2,
    "rows": [
      {
        "active_basis_churn_count_before": 0,
        "active_basis_journey_count_before": 10,
        "cg_iter": 1,
        "column_pool_size_before": 250,
        "context_hash": "2535416cc731f7b6",
        "control_objective": 959.458157,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205",
        "new_task_set": true,
        "rmp_degeneracy_pressure_before": 1.0,
        "sequence": "2-18-20",
        "single_impact_class": "improved",
        "single_objective_delta": -86.126964,
        "snapshot_dataset": "root_cause_active_basis_snapshot_greedy20_pair_smoke_20260614",
        "task_count": 20,
        "task_set": "2,18,20",
        "true_reduced_cost": -130.406733
      },
      {
        "active_basis_churn_count_before": 15,
        "active_basis_journey_count_before": 9,
        "cg_iter": 2,
        "column_pool_size_before": 251,
        "context_hash": "988c728382b4a376",
        "control_objective": 873.331193,
        "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205",
        "new_task_set": true,
        "rmp_degeneracy_pressure_before": 1.0,
        "sequence": "18-2-10",
        "single_impact_class": "noop",
        "single_objective_delta": 0.0,
        "snapshot_dataset": "root_cause_active_basis_snapshot_greedy20_pair_smoke_20260614",
        "task_count": 20,
        "task_set": "2,10,18",
        "true_reduced_cost": -41.9490035
      }
    ]
  }
]
```

## Checks

```json
{
  "degeneracy_one_contains_high_and_noop": true,
  "has_mixed_task20_instance_group": true,
  "has_rows": true,
  "has_task20_rows": true,
  "inputs_exist": true,
  "positive_churn_contains_high_and_noop": true,
  "strongest_noop_more_negative_than_some_improved": true,
  "task20_has_high_impact_and_noop": true,
  "task20_rows_are_all_new_task_set": true,
  "true_rc_threshold_has_task20_false_positives": true
}
```

## 解释

这些反例说明：即使候选列是 20-task、new-task-set、true-RC negative，并且 active-basis snapshot 字段完整，它仍可能是 noop。

最强 noop 的 true-RC 比多个 improved rows 更负，因此“更负 true-RC 更值得加”的单调假设不成立。

positive active-basis churn 和 `rmp_degeneracy_pressure_before = 1.0` 都同时包含 improved 与 noop；单个 snapshot scalar 也不能解释 production selector。

因此当前根因仍是 returned column batch 与 RMP/active-basis context trajectory 耦合，而不是 Pulse 单组件或负列数量不足。
