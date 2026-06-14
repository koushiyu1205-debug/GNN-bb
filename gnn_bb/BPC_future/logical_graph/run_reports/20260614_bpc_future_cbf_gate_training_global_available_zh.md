# CBF Gate 离线训练报告

日期：2026-06-14

## 目的

训练一个保守的离线 CBF/RMP-impact gate，用于判断已经 true-RC 验证的
候选列批是否可能维持 Lyapunov/CBF surrogate 稳定。该模型不运行 BPC / pricing / RMP，
不生成列，不证明 no-negative，不产生 official lower bound。

## 机器字段

```text
cbf_gate_training = current
status = cbf_gate_trained_offline
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
selector_is_pricing_oracle = false
selector_can_certificate = false
all_checks_pass = true
```

## 摘要

```json
{
  "chosen_gate": {
    "decision": "candidate_add_gate",
    "reason": "met_conservative_precision_fpr_gate",
    "threshold": 0.78,
    "validation_metrics": {
      "false_positive_rate": 0.0,
      "fn": 4,
      "fp": 0,
      "negative_count": 5,
      "positive_count": 6,
      "precision": 1.0,
      "predicted_positive": 2,
      "recall": 0.3333333333333333,
      "threshold": 0.78,
      "tn": 5,
      "total": 11,
      "tp": 2
    }
  },
  "feature_count": 30,
  "label_counts": {
    "0": 151,
    "1": 30
  },
  "row_count": 181,
  "split": {
    "seed": 17,
    "split_kind": "instance_holdout",
    "train_count": 170,
    "train_instances": [
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
      "apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103",
      "apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205",
      "apollo15_20km_random-wave_randomtw_tasks020_02_seed61102",
      "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000",
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103",
      "tranquillitatis_balmer_like_20km_tasks10_01_seed11000",
      "tranquillitatis_balmer_like_20km_tasks20_01_seed21000"
    ],
    "validation_count": 11,
    "validation_fraction": 0.25,
    "validation_instances": [
      "apollo15_20km_random-wave_randomtw_tasks020_01_seed61000",
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002",
      "very_small"
    ]
  },
  "validation_metrics_at_gate": {
    "false_positive_rate": 0.0,
    "fn": 4,
    "fp": 0,
    "negative_count": 5,
    "positive_count": 6,
    "precision": 1.0,
    "predicted_positive": 2,
    "recall": 0.3333333333333333,
    "threshold": 0.78,
    "tn": 5,
    "total": 11,
    "tp": 2
  }
}
```

## 解释

- 该 gate 的动作只有 `ADD` 或 `ABSTAIN`，且只能作用于已通过 true-RC 的候选列批；
- 特征选择排除了 `state_next_*`、`delta_*`、`barrier_slack`、label 等未来信息；
- `production_ready=false` 是刻意的：还需要 holdout、5/10 no-regression 和 20-task A/B。
