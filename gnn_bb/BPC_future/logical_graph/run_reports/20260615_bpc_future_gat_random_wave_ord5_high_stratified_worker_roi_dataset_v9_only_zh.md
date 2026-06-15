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
row_count = 2
training_row_count = 2
unique_training_row_count = 2
target_diag_available_count = 2
worker_context_match_count = 2
target_causal_match_count = 2
target_intervention_observed_count = 2
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 0
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {}
label_counts = {'0': 1, '1': 1}
unique_label_counts = {'0': 1, '1': 1}
roi_class_counts = {'negative_primal_roi': 1, 'positive_primal_roi': 1}
positive_training_label_count = 1
negative_training_label_count = 1
positive_instance_count = 1
negative_instance_count = 1
positive_family_count = 1
negative_family_count = 1
positive_region_count = 1
negative_region_count = 1
positive_region_counts = {'tranquillitatis_balmer_like_20km': 1}
negative_region_counts = {'apollo15_20km': 1}
label_distribution_ready_details = {'positive_instances_ready': False, 'negative_instances_ready': False, 'positive_families_ready': False, 'negative_families_ready': False, 'positive_regions_ready': False, 'negative_regions_ready': False, 'positive_instance_fraction_ready': False, 'negative_instance_fraction_ready': False}
sample_collection_gaps = [{'name': 'positive_instance_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'negative_instance_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'positive_family_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'negative_family_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'positive_region_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'negative_region_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'positive_max_instance_fraction', 'observed': 1.0, 'required_max': 0.75, 'excess': 0.25}, {'name': 'negative_max_instance_fraction', 'observed': 1.0, 'required_max': 0.75, 'excess': 0.25}]
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
    "best_true_reduced_cost": -32.4695918,
    "columns_delta": -8.0,
    "decision_probability": 0.8936647176742554,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_05_seed61408_be1c1c2bb30bf3f2_20_17_1_16_4",
    "primal_improvement": -11.301099000000022,
    "roi_class": "negative_primal_roi"
  },
  {
    "best_true_reduced_cost": -64.402114,
    "columns_delta": -12.0,
    "decision_probability": 0.9000977873802185,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_05_seed61411_79c1e81dc9889c24_5_6_10",
    "primal_improvement": 4.6900210000000015,
    "roi_class": "positive_primal_roi"
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
