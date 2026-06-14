# Root Cause Selector Collection Plan 报告

日期：2026-06-14

## 目的

本报告把当前 selector failure evidence 转成补采目标。它只读已有
summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker、
certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_collection_plan = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = collect_no_certificate_effect_selector_holdout_data
current_stage = calibration_only_selector_holdout
production_direction_proven = false
priority_context_target_count = 3
mixed_instance_target_count = 2
mixed_dataset_target_count = 2
required_capture_field_count = 17
all_checks_pass = true
```

## 优先补采的 context failure 类型

### false_positive_no_positive_context

当前 context 数：4

原因：当前 selector 会在没有 positive 的 context 中误加列。

标签要求：至少保留 no-op/low-impact returned rows，并寻找相邻 context 中同类候选是否能变成 improved。

样例 context：

```json
[
  {
    "context_hash": "3f914a0d2b97fd27",
    "failure_kind": "false_positive_no_positive_context",
    "noop_count": 5,
    "positive_count": 0,
    "positive_rate": 0.0,
    "selected_rule": "cost>=73.9194 AND true_reduced_cost<=-3.82619",
    "total": 5
  },
  {
    "context_hash": "c5a59a95c2c9971a",
    "failure_kind": "false_positive_no_positive_context",
    "noop_count": 3,
    "positive_count": 0,
    "positive_rate": 0.0,
    "selected_rule": "cost>=73.9194 AND true_reduced_cost<=-3.82619",
    "total": 3
  },
  {
    "context_hash": "d60fcf4b919b7d22",
    "failure_kind": "false_positive_no_positive_context",
    "noop_count": 3,
    "positive_count": 0,
    "positive_rate": 0.0,
    "selected_rule": "cost>=73.9194 AND true_reduced_cost<=-3.82619",
    "total": 3
  },
  {
    "context_hash": "e55ea3e7d277b6d1",
    "failure_kind": "false_positive_no_positive_context",
    "noop_count": 3,
    "positive_count": 0,
    "positive_rate": 0.0,
    "selected_rule": "cost>=73.9194 AND true_reduced_cost<=-3.82619",
    "total": 3
  }
]
```

### missed_positive_context

当前 context 数：3

原因：当前 selector 会漏掉有 positive 的 context。

标签要求：至少保留 improved rows，并确认现有 selector 为什么没有选中。

样例 context：

```json
[
  {
    "context_hash": "05695ab419abfb4b",
    "failure_kind": "missed_positive_context",
    "noop_count": 0,
    "positive_count": 3,
    "positive_rate": 1.0,
    "selected_rule": "true_reduced_cost<=-6.72239 AND cost>=73.9194",
    "total": 3
  },
  {
    "context_hash": "1db815e33b9ea471",
    "failure_kind": "missed_positive_context",
    "noop_count": 5,
    "positive_count": 1,
    "positive_rate": 0.16666666666666666,
    "selected_rule": "true_reduced_cost<=-6.72239 AND cost>=73.9194",
    "total": 6
  },
  {
    "context_hash": "7f2e531534d18ad2",
    "failure_kind": "missed_positive_context",
    "noop_count": 9,
    "positive_count": 2,
    "positive_rate": 0.18181818181818182,
    "selected_rule": "true_reduced_cost<=-6.72239 AND cost>=73.9194",
    "total": 11
  }
]
```

### mixed_low_precision_or_recall_context

当前 context 数：3

原因：当前 selector 在同一 context 内 precision/recall 同时不稳。

标签要求：同时保留 improved 与 noop rows，用于训练 context-sensitive gate。

样例 context：

```json
[
  {
    "context_hash": "3c36c602289637b4",
    "failure_kind": "mixed_low_precision_or_recall_context",
    "noop_count": 12,
    "positive_count": 12,
    "positive_rate": 0.5,
    "selected_rule": "true_reduced_cost<=-6.72239 AND cost>=73.9194",
    "total": 24
  },
  {
    "context_hash": "774573a2964cb1c5",
    "failure_kind": "mixed_low_precision_or_recall_context",
    "noop_count": 12,
    "positive_count": 12,
    "positive_rate": 0.5,
    "selected_rule": "true_reduced_cost<=-6.72239 AND cost>=73.9194",
    "total": 24
  },
  {
    "context_hash": "79de1ece885a7f67",
    "failure_kind": "mixed_low_precision_or_recall_context",
    "noop_count": 12,
    "positive_count": 3,
    "positive_rate": 0.2,
    "selected_rule": "cost>=73.9194 AND true_reduced_cost<=-3.82619",
    "total": 15
  }
]
```

## 同 instance / dataset 混合目标

这些目标证明 instance 或 dataset 身份不能解释 selector 成败，补采时应保留同一组内的 high 与 low/noop context。

```json
{
  "mixed_dataset_targets": [
    {
      "context_count": 18,
      "high_context_count": 10,
      "impact_dataset": "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613",
      "low_context_count": 6,
      "max_positive_rate": 1.0,
      "min_positive_rate": 0.0
    },
    {
      "context_count": 6,
      "high_context_count": 4,
      "impact_dataset": "root_cause_target002_capture_pt03_r3_20260613",
      "low_context_count": 2,
      "max_positive_rate": 1.0,
      "min_positive_rate": 0.0
    }
  ],
  "mixed_instance_targets": [
    {
      "context_count": 15,
      "high_context_count": 8,
      "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
      "low_context_count": 6,
      "max_positive_rate": 1.0,
      "min_positive_rate": 0.0
    },
    {
      "context_count": 9,
      "high_context_count": 6,
      "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
      "low_context_count": 2,
      "max_positive_rate": 1.0,
      "min_positive_rate": 0.0
    }
  ]
}
```

## Active-basis 反例目标

这些行证明更负 true-RC / new-task-set / 单个 active-basis scalar 都不能单独作为 production selector。

```json
{
  "false_positive_rows": [
    {
      "active_basis_churn_count_before": 4,
      "cg_iter": 2,
      "context_hash": "e55ea3e7d277b6d1",
      "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
      "new_task_set": true,
      "rmp_degeneracy_pressure_before": 1.0,
      "sequence": "12-18-5",
      "single_impact_class": "noop",
      "single_objective_delta": 0.0,
      "snapshot_dataset": "root_cause_active_basis_snapshot_mt20_smoke_20260614",
      "task_set": "5,12,18",
      "true_reduced_cost": -128.547499
    },
    {
      "active_basis_churn_count_before": 15,
      "cg_iter": 2,
      "context_hash": "988c728382b4a376",
      "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205",
      "new_task_set": true,
      "rmp_degeneracy_pressure_before": 1.0,
      "sequence": "18-2-10",
      "single_impact_class": "noop",
      "single_objective_delta": 0.0,
      "snapshot_dataset": "root_cause_active_basis_snapshot_greedy20_pair_smoke_20260614",
      "task_set": "2,10,18",
      "true_reduced_cost": -41.9490035
    }
  ],
  "strongest_noop": {
    "active_basis_churn_count_before": 4,
    "cg_iter": 2,
    "context_hash": "e55ea3e7d277b6d1",
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "new_task_set": true,
    "rmp_degeneracy_pressure_before": 1.0,
    "sequence": "12-18-5",
    "single_impact_class": "noop",
    "single_objective_delta": 0.0,
    "snapshot_dataset": "root_cause_active_basis_snapshot_mt20_smoke_20260614",
    "task_set": "5,12,18",
    "true_reduced_cost": -128.547499
  },
  "weaker_improved_than_strongest_noop_examples": [
    {
      "active_basis_churn_count_before": 0,
      "cg_iter": 1,
      "context_hash": "8c60fac6ce5f475f",
      "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
      "new_task_set": true,
      "rmp_degeneracy_pressure_before": 1.866666667,
      "sequence": "10-13-8",
      "single_impact_class": "improved",
      "single_objective_delta": -38.5883615,
      "snapshot_dataset": "root_cause_active_basis_snapshot_multi20_smoke_20260614",
      "task_set": "8,10,13",
      "true_reduced_cost": -38.7838905
    },
    {
      "active_basis_churn_count_before": 17,
      "cg_iter": 2,
      "context_hash": "f67cf0852ea7df8b",
      "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
      "new_task_set": true,
      "rmp_degeneracy_pressure_before": 0.75,
      "sequence": "2-7-9",
      "single_impact_class": "improved",
      "single_objective_delta": -23.46338,
      "snapshot_dataset": "root_cause_active_basis_snapshot_multi20_smoke_20260614",
      "task_set": "2,7,9",
      "true_reduced_cost": -32.5008455
    },
    {
      "active_basis_churn_count_before": 0,
      "cg_iter": 1,
      "context_hash": "c30ee076e24e6460",
      "instance": "tranquillitatis_balmer_like_20km_tasks20_01_seed21000",
      "new_task_set": true,
      "rmp_degeneracy_pressure_before": 1.538461538,
      "sequence": "20-15-5",
      "single_impact_class": "improved",
      "single_objective_delta": -56.9035325,
      "snapshot_dataset": "root_cause_active_basis_snapshot_multi20_smoke_20260614",
      "task_set": "5,15,20",
      "true_reduced_cost": -57.0891735
    },
    {
      "active_basis_churn_count_before": 14,
      "cg_iter": 2,
      "context_hash": "8f9a20ae99268746",
      "instance": "tranquillitatis_balmer_like_20km_tasks20_01_seed21000",
      "new_task_set": true,
      "rmp_degeneracy_pressure_before": 1.0,
      "sequence": "18-13-4",
      "single_impact_class": "improved",
      "single_objective_delta": -53.5053115,
      "snapshot_dataset": "root_cause_active_basis_snapshot_multi20_smoke_20260614",
      "task_set": "4,13,18",
      "true_reduced_cost": -53.518311
    },
    {
      "active_basis_churn_count_before": 0,
      "cg_iter": 1,
      "context_hash": "ad8b0be13bd7bb93",
      "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103",
      "new_task_set": true,
      "rmp_degeneracy_pressure_before": 0.8,
      "sequence": "9-6-8",
      "single_impact_class": "improved",
      "single_objective_delta": -92.4295805,
      "snapshot_dataset": "root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_20260614",
      "task_set": "6,8,9",
      "true_reduced_cost": -97.163992
    }
  ]
}
```

## 必须采集字段

- `context_hash`
- `instance`
- `task_count`
- `cg_iter`
- `true_dual_hash`
- `returned_journeys`
- `task_set`
- `sequence`
- `signature`
- `true_reduced_cost`
- `active_basis_churn_count_before`
- `rmp_degeneracy_pressure_before`
- `control_objective`
- `column_pool_size_before`
- `single_impact_class`
- `single_objective_delta`
- `official_effect_count`

## 进入下一关前必须满足

- new rows have official_effect_count=0
- candidate rows include full active-basis snapshot-derived fields
- selector using only addition-before features passes context holdout
- selector using only addition-before features passes instance holdout
- selector using only addition-before features passes dataset holdout

## 仍然禁止

- default worker/audit/probe enable
- official certificate gate
- production BPC A/B before selector holdout pass
- post-addition or hindsight features in online selector

## 检查项

```json
{
  "active_basis_counterexamples_passed": true,
  "active_basis_counterexamples_present": true,
  "context_feature_passed": true,
  "context_fold_passed": true,
  "counterexample_catalog_passed": true,
  "mixed_dataset_targets_present": true,
  "mixed_instance_targets_present": true,
  "next_action_forbids_production_shortcuts": true,
  "next_action_passed": true,
  "priority_targets_have_samples": true,
  "required_fields_include_active_basis": true,
  "status_is_collection_only": true,
  "twenty_failure_kinds_present": true
}
```
