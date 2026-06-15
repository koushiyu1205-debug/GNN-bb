# GAT Worker ROI Dataset 报告

日期：2026-06-15

## 目的

把 target-priority worker A/B 审计结果转成第二阶段 GAT ROI 标签。
该数据集用于学习“候选是否真的改变 RMP / primal 轨迹”，不是 pricing oracle，
不运行 BPC / pricing / RMP / worker，也不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_worker_roi_dataset = current
status = built
row_count = 6
training_row_count = 6
unique_training_row_count = 6
target_diag_available_count = 6
worker_context_match_count = 6
target_causal_match_count = 6
target_intervention_observed_count = 6
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 0
no_worker_target_intervention_count = 0
label_counts = {'0': 3, '1': 3}
unique_label_counts = {'0': 3, '1': 3}
roi_class_counts = {'negative_primal_roi': 2, 'no_observed_roi': 1, 'positive_primal_roi': 3}
label_distribution_ready = false
training_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
all_checks_pass = true
```

## 样例

```json
[
  {
    "best_true_reduced_cost": -7.298596667,
    "columns_delta": 4.0,
    "decision_probability": 0.8592458367347717,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_3_9_11_14",
    "primal_improvement": 3.820515999999998,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -62.608718,
    "columns_delta": -35.0,
    "decision_probability": 0.9526166915893555,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_ea2f1344458c548f_1_11",
    "primal_improvement": -4.358571999999981,
    "roi_class": "negative_primal_roi"
  },
  {
    "best_true_reduced_cost": -29.371658,
    "columns_delta": 7.0,
    "decision_probability": 0.9269914627075195,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20_4_16",
    "primal_improvement": 0.652150000000006,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -18.801739389,
    "columns_delta": -5.0,
    "decision_probability": 0.9364012479782104,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1_16_9",
    "primal_improvement": -1.1803939999999784,
    "roi_class": "negative_primal_roi"
  },
  {
    "best_true_reduced_cost": -7.43333825,
    "columns_delta": -5.0,
    "decision_probability": 0.9044457674026489,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_09_seed61821_b46cdc0f247ab6e3_7_8_2_13",
    "primal_improvement": 2.191962999999987,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -0.246951143,
    "columns_delta": -1.0,
    "decision_probability": 0.8972326517105103,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_18_12",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  }
]
```

## 结论

- 当前 ROI 标签数量或分布仍不足以训练可靠 gate；应继续扩充 20-task A/B 标签。
- `positive_primal_roi` 作为保守正样本；`no_observed_roi` / `negative_primal_roi` 作为负样本；
- `columns_only_roi` 暂不作为主训练标签，可作为辅助分析；
- missing / certificate-effect / official-bound-effect 样本不进入训练；
- 所有 ROI 训练标签都必须在同一个 expected context hash 下发生，否则排除训练；
- 所有 ROI 训练标签都必须能在 worker 日志中因果匹配 target，否则排除训练；
- no-observed ROI 还必须有实际 worker target intervention 证据，避免把 context mismatch 当负样本；
- `training_ready` 同时要求 unique 标签数量和实例/family 分布达标，避免小样本或单实例标签把 GAT 带偏；
- 该数据集只能用于离线校准，不能参与证书或官方下界。
