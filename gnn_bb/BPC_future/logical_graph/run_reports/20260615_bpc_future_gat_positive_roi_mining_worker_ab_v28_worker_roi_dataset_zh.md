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
row_count = 16
training_row_count = 16
unique_training_row_count = 16
target_diag_available_count = 16
worker_context_match_count = 16
target_causal_match_count = 16
target_intervention_observed_count = 16
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 0
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {}
label_counts = {'0': 8, '1': 8}
unique_label_counts = {'0': 8, '1': 8}
roi_class_counts = {'negative_primal_roi': 3, 'negative_retry_roi': 4, 'no_observed_roi': 1, 'positive_primal_roi': 7, 'positive_retry_roi': 1}
positive_training_label_count = 8
negative_training_label_count = 8
positive_instance_count = 6
negative_instance_count = 7
positive_family_count = 2
negative_family_count = 2
positive_region_count = 2
negative_region_count = 2
positive_region_counts = {'apollo15_20km': 5, 'tranquillitatis_balmer_like_20km': 3}
negative_region_counts = {'apollo15_20km': 3, 'tranquillitatis_balmer_like_20km': 5}
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
    "best_true_reduced_cost": -0.01253975,
    "columns_delta": -1.0,
    "decision_probability": 0.7674699425697327,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_e8e35421df342768_5_14_1_20",
    "primal_improvement": 4.700892000000067,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -19.1028872,
    "columns_delta": -15.0,
    "decision_probability": 0.6914450526237488,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b6507dfb6db81d64_16_11_12_10",
    "primal_improvement": 0.0,
    "roi_class": "positive_retry_roi"
  },
  {
    "best_true_reduced_cost": -0.595437,
    "columns_delta": -8.0,
    "decision_probability": 0.7294490933418274,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_02_seed61103_126440b08b9f25f5_5_18_10_14_1_20",
    "primal_improvement": 4.700892000000067,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -13.6231534,
    "columns_delta": 8.0,
    "decision_probability": 0.9435222744941711,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_20_18_3_4",
    "primal_improvement": 2.650588999999968,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -7.912891273,
    "columns_delta": -5.0,
    "decision_probability": 0.9285477995872498,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_7db256d4f7224cc6_10_1_16_7_17_4",
    "primal_improvement": 2.650588999999968,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -59.766543,
    "columns_delta": -64.0,
    "decision_probability": 0.965408444404602,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_9fadf4f7b39742a2_13_8_11",
    "primal_improvement": 10.185688999999911,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -9.919815,
    "columns_delta": 11.0,
    "decision_probability": 0.9190742373466492,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_bec78bfc0baddb44_6_11_2",
    "primal_improvement": -2.2324689999999237,
    "roi_class": "negative_primal_roi"
  },
  {
    "best_true_reduced_cost": -3.429108,
    "columns_delta": -1.0,
    "decision_probability": 0.8592458367347717,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_04_seed61308_587e2ac350a8619b_15_6_11_12_14",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -1.466535,
    "columns_delta": -22.0,
    "decision_probability": 0.9196915626525879,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_20_18_2_1_19",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -2.185878,
    "columns_delta": 10.0,
    "decision_probability": 0.8320755362510681,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_03_seed61206_d1096c4029531f56_7_1_8_11_19",
    "primal_improvement": 0.9745249999999714,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -3.04092475,
    "columns_delta": -14.0,
    "decision_probability": 0.7292459607124329,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_13_1_16_8",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -0.028786,
    "columns_delta": 0.0,
    "decision_probability": 0.8972326517105103,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_01_seed61000_3a9af4966d4b91d5_8_15_12_9",
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
