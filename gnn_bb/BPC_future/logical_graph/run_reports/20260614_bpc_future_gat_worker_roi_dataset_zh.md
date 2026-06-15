# GAT Worker ROI Dataset 报告

日期：2026-06-14

## 目的

把 target-priority worker A/B 审计结果转成第二阶段 GAT ROI 标签。
该数据集用于学习“候选是否真的改变 RMP / primal 轨迹”，不是 pricing oracle，
不运行 BPC / pricing / RMP / worker，也不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_worker_roi_dataset = current
status = built
row_count = 13
training_row_count = 0
unique_training_row_count = 0
target_diag_available_count = 3
worker_context_match_count = 2
target_causal_match_count = 0
target_intervention_observed_count = 2
positive_roi_without_target_causal_match_count = 2
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 1
no_worker_target_intervention_count = 10
label_counts = {}
unique_label_counts = {}
roi_class_counts = {'no_observed_roi': 11, 'positive_primal_roi': 2}
label_distribution_ready = false
training_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
all_checks_pass = false
```

## 样例

```json
[
  {
    "best_true_reduced_cost": -14.8269665,
    "columns_delta": 2.0,
    "decision_probability": 0.7530577778816223,
    "label_worker_roi_positive": null,
    "name": "apollo20_sector_wave_c488c428_target_20_17_16",
    "primal_improvement": 0.9636629999999968,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -2.550058,
    "columns_delta": 0.0,
    "decision_probability": 0.8607129454612732,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_7e0afd09753effed_19",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -9.747246,
    "columns_delta": 0.0,
    "decision_probability": 0.8709929585456848,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_a3b5b5263e1cfe17_14_5_8_18_12",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -6.935715,
    "columns_delta": 0.0,
    "decision_probability": 0.9100852012634277,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_de2c1d84615d5c71_14_6_1_20_9",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -3.463997,
    "columns_delta": 0.0,
    "decision_probability": 0.8218390345573425,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_05_seed61408_157f03afc868de3b_13",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -14.8269665,
    "columns_delta": 2.0,
    "decision_probability": 0.7530577778816223,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_c488c428ee5822de_20_17_16",
    "primal_improvement": 0.9636629999999968,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -52.519726,
    "columns_delta": 0.0,
    "decision_probability": 0.823053240776062,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -4.138581667,
    "columns_delta": 0.0,
    "decision_probability": 0.8623261451721191,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_d44af494d156d43e_6",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -29.371658,
    "columns_delta": 0.0,
    "decision_probability": 0.8148101568222046,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_09187873900ecefa_6_20",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -18.801739389,
    "columns_delta": 0.0,
    "decision_probability": 0.8177616000175476,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_06_seed61513_39ec05e43b291642_20_1",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -16.242464,
    "columns_delta": 0.0,
    "decision_probability": 0.8786776065826416,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_07_seed61615_727eba0fe29647bc_2",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -25.062302,
    "columns_delta": 0.0,
    "decision_probability": 0.8543282747268677,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_08_seed61718_e6a026e516dfd2f4_12_4",
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
