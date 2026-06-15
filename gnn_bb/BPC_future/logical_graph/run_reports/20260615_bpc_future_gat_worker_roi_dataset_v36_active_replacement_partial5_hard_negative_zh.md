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
row_count = 5
training_row_count = 3
unique_training_row_count = 3
target_diag_available_count = 5
worker_context_match_count = 5
target_causal_match_count = 4
target_intervention_observed_count = 5
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 1
worker_context_mismatch_count = 0
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {'roi_without_target_causal_match': 1, 'unsupported_roi_class:positive_walltime_roi': 1}
positive_trajectory_roi_guard_reason_counts = {'not_positive_roi_class': 2, 'worse_than_baseline_same_iter_objective': 3}
post_injection_guard_present_count = 5
post_injection_positive_downgraded_count = 3
label_counts = {'0': 3}
unique_label_counts = {'0': 3}
roi_class_counts = {'negative_walltime_roi': 1, 'positive_exact_roi': 2, 'positive_pricing_roi': 1, 'positive_walltime_roi': 1}
positive_training_label_count = 0
negative_training_label_count = 3
positive_instance_count = 0
negative_instance_count = 1
positive_family_count = 0
negative_family_count = 1
positive_region_count = 0
negative_region_count = 1
positive_region_counts = {}
negative_region_counts = {'apollo15_20km': 3}
label_distribution_ready_details = {'positive_instances_ready': False, 'negative_instances_ready': True, 'positive_families_ready': False, 'negative_families_ready': True, 'positive_regions_ready': False, 'negative_regions_ready': True, 'positive_instance_fraction_ready': True, 'negative_instance_fraction_ready': False}
sample_collection_gaps = [{'name': 'positive_training_label_count', 'observed': 0, 'required': 1, 'missing': 1}, {'name': 'positive_instance_count', 'observed': 0, 'required': 1, 'missing': 1}, {'name': 'positive_family_count', 'observed': 0, 'required': 1, 'missing': 1}, {'name': 'positive_region_count', 'observed': 0, 'required': 1, 'missing': 1}, {'name': 'negative_max_instance_fraction', 'observed': 1.0, 'required_max': 0.75, 'excess': 0.25}]
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
    "best_true_reduced_cost": -1.864621,
    "columns_delta": null,
    "decision_probability": 1.0,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_d519291840dd7000_rank1_8_11_batch4",
    "primal_improvement": null,
    "roi_class": "positive_pricing_roi"
  },
  {
    "best_true_reduced_cost": -0.183465,
    "columns_delta": null,
    "decision_probability": 0.999996542930603,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_67c11b5ec80925ec_rank1_5_1_2_18_3_batch4",
    "primal_improvement": null,
    "roi_class": "positive_exact_roi"
  },
  {
    "best_true_reduced_cost": null,
    "columns_delta": null,
    "decision_probability": null,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_409f65576794fa39_rank2_17_13",
    "primal_improvement": null,
    "roi_class": "positive_exact_roi"
  },
  {
    "best_true_reduced_cost": -0.127459,
    "columns_delta": null,
    "decision_probability": 0.8121140599250793,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_62c86745ed2b3aaa_rank1_8_20_13_batch4",
    "primal_improvement": null,
    "roi_class": "negative_walltime_roi"
  },
  {
    "best_true_reduced_cost": -0.824859,
    "columns_delta": null,
    "decision_probability": 0.4149324893951416,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_random_wave_randomtw_tasks020_08_seed61715_3100b787bf438dfe_rank3_5_1_2_4_7_11",
    "primal_improvement": null,
    "roi_class": "positive_walltime_roi"
  }
]
```

## 结论

- 当前 ROI 标签数量或分布仍不足以训练可靠 gate；应继续扩充 20-task A/B 标签。
- `positive_primal_roi` / `positive_retry_roi` / `positive_status_roi` 等作为 trajectory 正样本；
- `no_observed_roi` / `negative_primal_roi` / `negative_retry_roi` 等作为负样本；
- `columns_only_roi` 暂不作为主训练标签，可作为辅助分析；
- 若存在 post-injection 后效字段，positive ROI 必须通过 active-support / baseline-same-iter guard，否则降为 DELAY 标签；
- missing / certificate-effect / official-bound-effect 样本不进入训练；
- 所有 ROI 训练标签都必须在同一个 expected context hash 下发生，否则排除训练；
- 所有 ROI 训练标签都必须能在 worker 日志中因果匹配 target，否则排除训练；
- no-observed ROI 还必须有实际 worker target intervention 证据，避免把 context mismatch 当负样本；
- `training_ready` 同时要求 unique 标签数量和实例/family 分布达标，避免小样本或单实例标签把 GAT 带偏；
- 该数据集只能用于离线校准，不能参与证书或官方下界。
