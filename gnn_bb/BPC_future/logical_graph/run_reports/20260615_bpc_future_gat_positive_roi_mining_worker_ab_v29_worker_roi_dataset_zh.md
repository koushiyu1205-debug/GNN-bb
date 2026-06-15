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
row_count = 22
training_row_count = 21
unique_training_row_count = 21
target_diag_available_count = 22
worker_context_match_count = 22
target_causal_match_count = 22
target_intervention_observed_count = 22
positive_roi_without_target_causal_match_count = 0
roi_without_target_causal_match_count = 0
worker_context_mismatch_count = 0
no_worker_target_intervention_count = 0
training_exclusion_reason_counts = {'unsupported_roi_class:columns_only_roi': 1}
label_counts = {'0': 16, '1': 5}
unique_label_counts = {'0': 16, '1': 5}
roi_class_counts = {'columns_only_roi': 1, 'negative_primal_roi': 2, 'negative_retry_roi': 13, 'no_observed_roi': 1, 'positive_primal_roi': 4, 'positive_retry_roi': 1}
positive_training_label_count = 5
negative_training_label_count = 16
positive_instance_count = 3
negative_instance_count = 10
positive_family_count = 2
negative_family_count = 2
positive_region_count = 2
negative_region_count = 2
positive_region_counts = {'apollo15_20km': 4, 'tranquillitatis_balmer_like_20km': 1}
negative_region_counts = {'apollo15_20km': 8, 'tranquillitatis_balmer_like_20km': 8}
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
    "best_true_reduced_cost": -10.169579,
    "columns_delta": 39.0,
    "decision_probability": 0.652938187122345,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_4848230110b93844_18_3_11",
    "primal_improvement": 0.38613900000007106,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -2.267482,
    "columns_delta": 69.0,
    "decision_probability": 0.6399354338645935,
    "label_worker_roi_positive": 1,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_94206d715106bf37_15_6_2_4_1_11",
    "primal_improvement": 0.38613900000007106,
    "roi_class": "positive_primal_roi"
  },
  {
    "best_true_reduced_cost": -0.720149,
    "columns_delta": 0.0,
    "decision_probability": 0.6249439120292664,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_c5025a0583f6ea6c_13_12_3_5",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -1.012332,
    "columns_delta": -9.0,
    "decision_probability": 0.600702702999115,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_10_seed61921_7390856b04698300_8_16_9_20",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -3.3822515,
    "columns_delta": 0.0,
    "decision_probability": 0.6598120927810669,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_27b61a4367a5c961_4_19_3",
    "primal_improvement": 0.0,
    "roi_class": "no_observed_roi"
  },
  {
    "best_true_reduced_cost": -7.018125,
    "columns_delta": -9.0,
    "decision_probability": 0.47529077529907227,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_10_seed61948_a05232b2b6c99641_18_4_11_5",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -5.466797222,
    "columns_delta": -2.0,
    "decision_probability": 0.988737940788269,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_07e693c5f161a590_18_5_4_14_17",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -2.723312,
    "columns_delta": -42.0,
    "decision_probability": 0.5473371744155884,
    "label_worker_roi_positive": 1,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_7079ec06a2d9eab3_8_14_11_9_17_5",
    "primal_improvement": 0.0,
    "roi_class": "positive_retry_roi"
  },
  {
    "best_true_reduced_cost": -0.923862,
    "columns_delta": 0.0,
    "decision_probability": 0.576228678226471,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_8_12_18_5",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -0.4163,
    "columns_delta": 0.0,
    "decision_probability": 0.576228678226471,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_09_seed61846_d067a87292522613_4_3_19_18_5",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -4.289458192,
    "columns_delta": 8.0,
    "decision_probability": 0.9490636587142944,
    "label_worker_roi_positive": 0,
    "name": "apollo15_20km_greedy_anchor_randomtw_tasks020_04_seed61308_37e3048dada58785_2_6_12_13_7_17",
    "primal_improvement": 0.0,
    "roi_class": "negative_retry_roi"
  },
  {
    "best_true_reduced_cost": -0.949764,
    "columns_delta": -1.0,
    "decision_probability": 0.4637874364852905,
    "label_worker_roi_positive": 0,
    "name": "tranquillitatis_balmer_like_20km_greedy_anchor_randomtw_tasks020_04_seed61311_7714263901aeb2ec_8_14_19",
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
