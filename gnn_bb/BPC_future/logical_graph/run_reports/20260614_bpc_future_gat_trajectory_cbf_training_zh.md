# GAT Trajectory CBF Training 报告

日期：2026-06-14

## 目的

训练 trajectory-labeled GAT CBF impact/barrier checkpoint。该 checkpoint
只用于离线表示学习和后续 kNN/OOD safety-shell 验证，不运行 BPC / pricing /
RMP，不生成 certificate 或 official bound。

## 机器字段

```text
gat_trajectory_cbf_training = current
status = gat_trajectory_cbf_trained
diagnostic_only = true
runs_bpc_or_pricing = false
sample_count = 136
candidate_count = 1599
target_label = label_horizon_cbf_feasible
selector_can_certificate = false
selector_is_pricing_oracle = false
production_ready = false
all_checks_pass = true
```

## 指标

```json
{
  "best_validation_loss": 0.6777380421757698,
  "split": {
    "mode": "instance",
    "train_instances": [
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
      "apollo15_20km_random-wave_randomtw_tasks020_02_seed61102",
      "apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000",
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821",
      "tranquillitatis_balmer_like_20km_tasks10_01_seed11000"
    ],
    "validation_instances": [
      "apollo15_20km_random-wave_randomtw_tasks020_01_seed61000",
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206",
      "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311",
      "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104",
      "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410"
    ]
  },
  "train_metrics": {
    "accuracy": 0.8421839940164547,
    "add_precision": 0.7955882352941176,
    "add_recall": 0.8825448613376835,
    "class_names": [
      "skip",
      "add",
      "abstain"
    ],
    "confusion": [
      [
        585,
        139,
        0
      ],
      [
        72,
        541,
        0
      ],
      [
        0,
        0,
        0
      ]
    ],
    "total": 1337
  },
  "validation_metrics": {
    "accuracy": 0.6564885496183206,
    "add_precision": 0.6521739130434783,
    "add_recall": 0.9880239520958084,
    "class_names": [
      "skip",
      "add",
      "abstain"
    ],
    "confusion": [
      [
        7,
        88,
        0
      ],
      [
        2,
        165,
        0
      ],
      [
        0,
        0,
        0
      ]
    ],
    "total": 262
  }
}
```

## 边界

- 不可作为 pricing oracle；
- 不可作为 certificate source；
- 不可影响 official lower bound；
- unsafe true-RC negative 只能进入 delay queue，不能永久丢弃；
- 后续必须接 kNN/OOD safety shell 并做独立 sector-wave / 5/10 / 20 ROI 验证。
