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
row_count = 24
training_row_count = 18
unique_training_row_count = 18
target_diag_available_count = 24
worker_context_match_count = 21
target_causal_match_count = 21
target_intervention_observed_count = 21
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 3
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {'unsupported_roi_class:columns_only_roi': 3, 'worker_context_mismatch': 3}
label_counts = {'0': 16, '1': 2}
unique_label_counts = {'0': 16, '1': 2}
roi_class_counts = {'columns_only_roi': 3, 'negative_primal_roi': 2, 'negative_retry_roi': 12, 'no_observed_roi': 5, 'positive_primal_roi': 1, 'positive_retry_roi': 1}
positive_training_label_count = 2
negative_training_label_count = 16
positive_instance_count = 2
negative_instance_count = 10
positive_family_count = 1
negative_family_count = 3
positive_region_count = 2
negative_region_count = 2
positive_region_counts = {'apollo15_20km': 1, 'tranquillitatis_balmer_like_20km': 1}
negative_region_counts = {'apollo15_20km': 12, 'tranquillitatis_balmer_like_20km': 4}
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
    "columns_delta": 6.0,
    "decision_probability": null,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_1_10",
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -29.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_8_20",
    "primal_improvement": 0.0,
    "roi_class": "positive_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -1.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_5_1_2_4_11_6",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -1.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_06_seed61510_9cb802808b9a3356_19_6_13",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -6.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_07_seed61612_411d44c3e21bcb1f_17_18_9_5",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 0.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_10_seed61919_e978a55b1e53d13f_3_18_8_9",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -5.0,
    "decision_probability": null,
    "label_worker_roi_positive": null,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_da555dc83edc174c_5_16_1",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 0.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_08b8d772e2ab9623_10_11",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": 4.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_10_seed61923_ec59d1f203f1630c_12_5_8",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -16.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_03_seed61205_e897b76f2888f822_10_11_14_9",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -3.0,
    "decision_probability": null,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_09_seed61820_7cb380a02e30e5a8_14_6_7",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": -7.0,
    "decision_probability": null,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_random_wave_randomtw_tasks020_08_seed61717_a77e5457bde80b8e_18_4_3_13",
    "primal_improvement": 4.172122999999942,
    "roi_class": "positive_primal_roi"
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
