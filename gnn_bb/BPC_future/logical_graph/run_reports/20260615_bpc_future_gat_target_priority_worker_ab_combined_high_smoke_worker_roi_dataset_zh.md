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
row_count = 4
training_row_count = 2
unique_training_row_count = 2
target_diag_available_count = 4
worker_context_match_count = 4
target_causal_match_count = 4
target_intervention_observed_count = 4
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 0
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {'unsupported_roi_class:columns_only_roi': 2}
label_counts = {'0': 2}
unique_label_counts = {'0': 2}
roi_class_counts = {'columns_only_roi': 2, 'no_observed_roi': 2}
positive_training_label_count = 0
negative_training_label_count = 2
positive_instance_count = 0
negative_instance_count = 2
positive_family_count = 0
negative_family_count = 1
positive_region_count = 0
negative_region_count = 2
positive_region_counts = {}
negative_region_counts = {'apollo15_20km': 1, 'tranquillitatis_balmer_like_20km': 1}
label_distribution_ready_details = {'positive_instances_ready': False, 'negative_instances_ready': True, 'positive_families_ready': False, 'negative_families_ready': True, 'positive_regions_ready': False, 'negative_regions_ready': True, 'positive_instance_fraction_ready': True, 'negative_instance_fraction_ready': True}
sample_collection_gaps = [{'name': 'positive_training_label_count', 'observed': 0, 'required': 1, 'missing': 1}, {'name': 'positive_instance_count', 'observed': 0, 'required': 1, 'missing': 1}, {'name': 'positive_family_count', 'observed': 0, 'required': 1, 'missing': 1}, {'name': 'positive_region_count', 'observed': 0, 'required': 1, 'missing': 1}]
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
    "best_true_reduced_cost": -9.973161,
    "columns_delta": 1.0,
    "decision_probability": 1.0,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_5_1_2_18_3",
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi"
  },
  {
    "best_true_reduced_cost": -13.062224625,
    "columns_delta": -8.0,
    "decision_probability": 0.999996542930603,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_5_1_15_3",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -28.8175178,
    "columns_delta": -20.0,
    "decision_probability": 1.0,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_ddcb5387bef3bf63_8_4_5_16",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -33.0433475,
    "columns_delta": 1.0,
    "decision_probability": 0.9998422861099243,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_5c522ff2995f86be_11_1_13_20",
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi"
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
