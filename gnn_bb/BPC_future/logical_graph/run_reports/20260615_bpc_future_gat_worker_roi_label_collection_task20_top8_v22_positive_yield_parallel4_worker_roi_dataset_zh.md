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
row_count = 8
training_row_count = 7
unique_training_row_count = 7
target_diag_available_count = 8
worker_context_match_count = 8
target_causal_match_count = 8
target_intervention_observed_count = 8
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 0
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {'unsupported_roi_class:columns_only_roi': 1}
label_counts = {'0': 3, '1': 4}
unique_label_counts = {'0': 3, '1': 4}
roi_class_counts = {'columns_only_roi': 1, 'negative_primal_roi': 1, 'negative_retry_roi': 2, 'positive_primal_roi': 3, 'positive_retry_roi': 1}
positive_training_label_count = 4
negative_training_label_count = 3
positive_instance_count = 3
negative_instance_count = 3
positive_family_count = 2
negative_family_count = 2
positive_region_count = 2
negative_region_count = 2
positive_region_counts = {'apollo15_20km': 2, 'tranquillitatis_balmer_like_20km': 2}
negative_region_counts = {'apollo15_20km': 1, 'tranquillitatis_balmer_like_20km': 2}
label_distribution_ready_details = {'positive_instances_ready': True, 'negative_instances_ready': True, 'positive_families_ready': True, 'negative_families_ready': True, 'positive_regions_ready': True, 'negative_regions_ready': True, 'positive_instance_fraction_ready': True, 'negative_instance_fraction_ready': True}
sample_collection_gaps = [{'name': 'positive_training_label_count', 'observed': 4, 'required': 5, 'missing': 1}, {'name': 'negative_training_label_count', 'observed': 3, 'required': 5, 'missing': 2}]
label_distribution_ready = true
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
    "best_true_reduced_cost": null,
    "columns_delta": 3.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_07_seed61635_048e5f66efcd12df_2_10_19_9_1",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -108.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_3d1bd8618099b573_8_11_10_17",
    "primal_improvement": -1.4553480000000718,
    "roi_class": "negative_primal_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -28.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_ac15bc4e7e3d6fff_4_19_10_17",
    "primal_improvement": 0.0,
    "roi_class": "positive_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 0.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_7fcd171c2901efb5_6_12_13_8_15_3",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 11.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_f9d0b6b18a0a28d3_18_3_13_6_19",
    "primal_improvement": 2.650588999999968,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 11.0,
    "decision_probability": null,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_02_seed61104_17ccb5dc2e9bbac0_20_5_6_3",
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 0.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_05_seed61410_fd0697a8f685dbe7_12_15_1_7_17_14",
    "primal_improvement": 2.650588999999968,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 0.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_03_seed61206_02259d538b5f4b8d_8_13_3_9_15",
    "primal_improvement": 10.185688999999911,
    "roi_class": "positive_primal_roi"
  }
]
```

## 结论

- 当前 ROI 标签数量或分布仍不足以训练可靠 gate；应继续扩充 20-task A/B 标签。
- `positive_primal_roi` / `positive_retry_roi` / `positive_status_roi` 等作为 trajectory 正样本；
- `no_observed_roi` / `negative_primal_roi` / `negative_retry_roi` 等作为负样本；
- `columns_only_roi` 暂不作为主训练标签，可作为辅助分析；
- missing / certificate-effect / official-bound-effect 样本不进入训练；
- 所有 ROI 训练标签都必须在同一个 expected context hash 下发生，否则排除训练；
- 所有 ROI 训练标签都必须能在 worker 日志中因果匹配 target，否则排除训练；
- no-observed ROI 还必须有实际 worker target intervention 证据，避免把 context mismatch 当负样本；
- `training_ready` 同时要求 unique 标签数量和实例/family 分布达标，避免小样本或单实例标签把 GAT 带偏；
- 该数据集只能用于离线校准，不能参与证书或官方下界。
