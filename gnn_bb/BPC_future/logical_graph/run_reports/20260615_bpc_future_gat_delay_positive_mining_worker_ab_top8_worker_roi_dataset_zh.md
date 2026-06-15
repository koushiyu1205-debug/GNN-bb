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
label_counts = {'0': 6, '1': 1}
unique_label_counts = {'0': 6, '1': 1}
roi_class_counts = {'columns_only_roi': 1, 'negative_primal_roi': 1, 'negative_retry_roi': 4, 'no_observed_roi': 1, 'positive_primal_roi': 1}
positive_training_label_count = 1
negative_training_label_count = 6
positive_instance_count = 1
negative_instance_count = 3
positive_family_count = 1
negative_family_count = 1
positive_region_count = 1
negative_region_count = 2
positive_region_counts = {'apollo15_20km': 1}
negative_region_counts = {'apollo15_20km': 3, 'tranquillitatis_balmer_like_20km': 3}
label_distribution_ready_details = {'positive_instances_ready': False, 'negative_instances_ready': True, 'positive_families_ready': False, 'negative_families_ready': False, 'positive_regions_ready': False, 'negative_regions_ready': True, 'positive_instance_fraction_ready': False, 'negative_instance_fraction_ready': True}
sample_collection_gaps = [{'name': 'positive_training_label_count', 'observed': 1, 'required': 5, 'missing': 4}, {'name': 'positive_instance_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'positive_family_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'negative_family_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'positive_region_count', 'observed': 1, 'required': 2, 'missing': 1}, {'name': 'positive_max_instance_fraction', 'observed': 1.0, 'required_max': 0.75, 'excess': 0.25}]
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
    "best_true_reduced_cost": -6.021628,
    "columns_delta": 67.0,
    "decision_probability": 0.652938187122345,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_8_6_1_4_10_14",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -1.9389955,
    "columns_delta": -12.0,
    "decision_probability": 0.6399354338645935,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_13_12_15_6_1_4_10",
    "primal_improvement": -1.8813429999999016,
    "roi_class": "negative_primal_roi"
  },
  {
    "best_true_reduced_cost": -0.207493,
    "columns_delta": 0.0,
    "decision_probability": 0.6308647990226746,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_33788d6b7bdf8387_13_12_15_6_16_9_19",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -0.5009735,
    "columns_delta": 34.0,
    "decision_probability": 0.6249439120292664,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_15_6_1_9_19",
    "primal_improvement": 0.38613900000007106,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -0.852234,
    "columns_delta": 19.0,
    "decision_probability": 0.8255921602249146,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_0f0c5d214add6400_18_2_11_17_3_15",
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi"
  },
  {
    "best_true_reduced_cost": -2.24368875,
    "columns_delta": -16.0,
    "decision_probability": 0.7292459607124329,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_08_seed61744_1b98b5f990279d7b_2_17_18_1_16_8",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -1.185535,
    "columns_delta": -7.0,
    "decision_probability": 0.6598120927810669,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_14_2_1_10",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -1.2206915,
    "columns_delta": 0.0,
    "decision_probability": 0.6049104332923889,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d8e422fc4def1c51_3_4_18",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
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
