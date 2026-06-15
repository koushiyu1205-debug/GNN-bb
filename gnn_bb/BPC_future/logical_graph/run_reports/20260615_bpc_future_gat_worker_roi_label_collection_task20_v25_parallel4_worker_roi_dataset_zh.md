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
row_count = 9
training_row_count = 8
unique_training_row_count = 8
target_diag_available_count = 9
worker_context_match_count = 9
target_causal_match_count = 9
target_intervention_observed_count = 9
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 0
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {'unsupported_roi_class:columns_only_roi': 1}
label_counts = {'0': 4, '1': 4}
unique_label_counts = {'0': 4, '1': 4}
roi_class_counts = {'columns_only_roi': 1, 'negative_retry_roi': 3, 'no_observed_roi': 1, 'positive_primal_roi': 3, 'positive_retry_roi': 1}
positive_training_label_count = 4
negative_training_label_count = 4
positive_instance_count = 3
negative_instance_count = 3
positive_family_count = 1
negative_family_count = 2
positive_region_count = 2
negative_region_count = 2
positive_region_counts = {'apollo15_20km': 3, 'tranquillitatis_balmer_like_20km': 1}
negative_region_counts = {'apollo15_20km': 2, 'tranquillitatis_balmer_like_20km': 2}
label_distribution_ready_details = {'positive_instances_ready': True, 'negative_instances_ready': True, 'positive_families_ready': False, 'negative_families_ready': True, 'positive_regions_ready': True, 'negative_regions_ready': True, 'positive_instance_fraction_ready': True, 'negative_instance_fraction_ready': True}
sample_collection_gaps = [{'name': 'positive_training_label_count', 'observed': 4, 'required': 5, 'missing': 1}, {'name': 'negative_training_label_count', 'observed': 4, 'required': 5, 'missing': 1}, {'name': 'positive_family_count', 'observed': 1, 'required': 2, 'missing': 1}]
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
    "best_true_reduced_cost": -11.873516778,
    "columns_delta": -8.0,
    "decision_probability": 0.9326108694076538,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_577b70605147a3cd_15_9_10_1",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -24.417731778,
    "columns_delta": -15.0,
    "decision_probability": 0.9712288975715637,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_04_seed61306_b9550ffc9a42531a_13_20_7",
    "primal_improvement": 0.0,
    "roi_class": "positive_retry_roi"
  },
  {
    "best_true_reduced_cost": -11.2356885,
    "columns_delta": -36.0,
    "decision_probability": 0.9436773061752319,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_476979944ba39894_12_2",
    "primal_improvement": 56.48128899999995,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -4.998038,
    "columns_delta": 9.0,
    "decision_probability": 0.9237889647483826,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_06_seed61510_95e9afaf1ecbdc5e_16_13_5",
    "primal_improvement": 61.28254700000002,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -25.4432665,
    "columns_delta": -3.0,
    "decision_probability": 0.9266511797904968,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_01_seed61002_ac056820151e9ad7_20_16",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -25.988531,
    "columns_delta": -2.0,
    "decision_probability": 0.9455428123474121,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_sector_wave_randomtw_tasks020_05_seed61410_4e481a6307fca228_11_4_7",
    "primal_improvement": 0.11635799999999108,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -41.3185275,
    "columns_delta": 10.0,
    "decision_probability": 0.9664464592933655,
    "label_worker_roi_positive": null,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b6d808ebac2a6dd8_16_19",
    "primal_improvement": 0.0,
    "roi_class": "columns_only_roi"
  },
  {
    "best_true_reduced_cost": -68.272315824,
    "columns_delta": -39.0,
    "decision_probability": 0.9449954032897949,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_b095fbae18116443_20_8_3_18",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -10.119675,
    "columns_delta": 17.0,
    "decision_probability": 0.9098923802375793,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_sector_wave_randomtw_tasks020_08_seed61715_a4f29d238b2963df_2_20_8_3",
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
