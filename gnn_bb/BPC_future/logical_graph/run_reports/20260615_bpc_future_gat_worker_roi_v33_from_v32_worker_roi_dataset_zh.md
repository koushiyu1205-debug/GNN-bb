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
row_count = 17
training_row_count = 15
unique_training_row_count = 15
target_diag_available_count = 17
worker_context_match_count = 16
target_causal_match_count = 16
target_intervention_observed_count = 16
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 1
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {'unsupported_roi_class:columns_only_roi': 1, 'worker_context_mismatch': 1}
label_counts = {'0': 12, '1': 3}
unique_label_counts = {'0': 12, '1': 3}
roi_class_counts = {'columns_only_roi': 1, 'negative_primal_roi': 2, 'negative_retry_roi': 9, 'no_observed_roi': 2, 'positive_primal_roi': 1, 'positive_retry_roi': 2}
positive_training_label_count = 3
negative_training_label_count = 12
positive_instance_count = 2
negative_instance_count = 9
positive_family_count = 1
negative_family_count = 2
positive_region_count = 2
negative_region_count = 2
positive_region_counts = {'apollo15_20km': 2, 'tranquillitatis_balmer_like_20km': 1}
negative_region_counts = {'apollo15_20km': 7, 'tranquillitatis_balmer_like_20km': 5}
label_distribution_ready_details = {'positive_instances_ready': True, 'negative_instances_ready': True, 'positive_families_ready': True, 'negative_families_ready': True, 'positive_regions_ready': True, 'negative_regions_ready': True, 'positive_instance_fraction_ready': True, 'negative_instance_fraction_ready': True}
sample_collection_gaps = []
label_distribution_ready = true
training_ready = true
production_ready = false
default_enabled = false
certificate_ready = false
all_checks_pass = true
```

## 样例

```json
[
  {
    "best_true_reduced_cost": null,
    "columns_delta": -1.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_fbfd88d4ebde5459_5_1_2_4_7_13",
    "primal_improvement": 0.0,
    "roi_class": "positive_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 0.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_13",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -32.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20_13",
    "primal_improvement": 0.0,
    "roi_class": "positive_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -14.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_5f4498eb39858b1d_5_6_10_7_13_11",
    "primal_improvement": 4.6900210000000015,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 0.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_8f2088cfefc3e3b1_20_3_7",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -1.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_2d9686e5aa73b5f3_9_19_1_16_11",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -1.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_02_seed61102_5c6127a7add1e6f6_13_11_15_6",
    "primal_improvement": -2.594432999999981,
    "roi_class": "negative_primal_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 3.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_04_seed61306_ffe911c2088f42a2_6_5_12_11_10_18",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -4.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_94989e70b81983eb_14_4_13_16",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 0.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_02_seed61103_3375e356a084eadb_12_5_1_9_7_15",
    "primal_improvement": -1.2802720000000818,
    "roi_class": "negative_primal_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -3.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_8_4_14_9_3_13",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -1.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_06_seed61513_7c518307952f17f7_19_2_8",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  }
]
```

## 结论

- 当前 positive / negative ROI 标签数量达到训练门槛，可进入 ROI gate 训练。
- `positive_primal_roi` / `positive_retry_roi` / `positive_status_roi` 等作为 trajectory 正样本；
- `no_observed_roi` / `negative_primal_roi` / `negative_retry_roi` 等作为负样本；
- `columns_only_roi` 暂不作为主训练标签，可作为辅助分析；
- missing / certificate-effect / official-bound-effect 样本不进入训练；
- 所有 ROI 训练标签都必须在同一个 expected context hash 下发生，否则排除训练；
- 所有 ROI 训练标签都必须能在 worker 日志中因果匹配 target，否则排除训练；
- no-observed ROI 还必须有实际 worker target intervention 证据，避免把 context mismatch 当负样本；
- `training_ready` 同时要求 unique 标签数量和实例/family 分布达标，避免小样本或单实例标签把 GAT 带偏；
- 该数据集只能用于离线校准，不能参与证书或官方下界。
