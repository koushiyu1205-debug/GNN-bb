# BPC Future GAT Stage 3 v33 v15 Context Contrast Priority 审计

日期：2026-06-16

## 结论

本报告把 v15 的 score-margin 审计和 v32 embedding separation 审计合并到 context 级别，
只用于决定下一轮 same-context contrast / candidate-head 结构修正优先级。
它不运行 BPC、pricing、RMP、worker 或 certificate。

```text
stage = Stage 3
variant = v33_v15_context_contrast_priority
context_count = 10
contexts_requiring_data_collection = 10
contexts_requiring_model_change = 0
contexts_with_negative_neighbor_mixture = 7
contexts_with_deep_candidate_gap = 7
primary_blocker = structural_negative_neighbor_mixture_or_missing_context_contrast
diagnostic_only = true
runs_bpc_or_pricing = false
selector_can_certificate = false
official_bound_effect = false
training_label_allowed_before_worker_reachability = false
```

## Top Contexts

```json
[
  {
    "context_hash": "5751b1799b606ad1",
    "deep_candidate_gap_count": 2,
    "embedding_missed_high_roi_count": 3,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "random-wave",
    "max_missed_roi": 4.385624885559082,
    "mean_candidate_margin": -0.4258081912994385,
    "mean_knn_positive_fraction": 0.13333333333333333,
    "mean_missed_roi": 3.1119513511657715,
    "median_knn_positive_fraction": 0.2,
    "min_candidate_margin": -0.4904479384422302,
    "missed_high_roi_count_proxy": 3,
    "missing_same_context_contrast_count": 0,
    "moderate_candidate_gap_count": 0,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 3,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 43.38562488555908,
    "region": "tranquillitatis_balmer_like_20km",
    "same_context_low_roi_or_delay_record_count": 2,
    "score_missed_high_roi_count": 2,
    "task_count": 50,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "9fadf4f7b39742a2",
    "deep_candidate_gap_count": 2,
    "embedding_missed_high_roi_count": 3,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "sector-wave",
    "max_missed_roi": 11.614195823669434,
    "mean_candidate_margin": -0.33332987626393634,
    "mean_knn_positive_fraction": 0.3333333333333333,
    "mean_missed_roi": 7.392339706420898,
    "median_knn_positive_fraction": 0.2,
    "min_candidate_margin": -0.574665367603302,
    "missed_high_roi_count_proxy": 3,
    "missing_same_context_contrast_count": 3,
    "moderate_candidate_gap_count": 1,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 0,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 40.0,
    "region": "tranquillitatis_balmer_like_20km",
    "same_context_low_roi_or_delay_record_count": 0,
    "score_missed_high_roi_count": 3,
    "task_count": 20,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "ce3508e12ad69da7",
    "deep_candidate_gap_count": 2,
    "embedding_missed_high_roi_count": 2,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "sector-wave",
    "max_missed_roi": 2.1054060459136963,
    "mean_candidate_margin": -0.6600249037146568,
    "mean_knn_positive_fraction": 0.0,
    "mean_missed_roi": 1.5790545344352722,
    "median_knn_positive_fraction": 0.0,
    "min_candidate_margin": -0.7810833007097244,
    "missed_high_roi_count_proxy": 2,
    "missing_same_context_contrast_count": 0,
    "moderate_candidate_gap_count": 0,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 2,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 31.105406045913696,
    "region": "apollo15_20km",
    "same_context_low_roi_or_delay_record_count": 2,
    "score_missed_high_roi_count": 2,
    "task_count": 20,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "79fde658840fe2b8",
    "deep_candidate_gap_count": 1,
    "embedding_missed_high_roi_count": 2,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "sector-wave",
    "max_missed_roi": 14.969822883605957,
    "mean_candidate_margin": -0.1931183934211731,
    "mean_knn_positive_fraction": 0.1,
    "mean_missed_roi": 14.269014835357666,
    "median_knn_positive_fraction": 0.1,
    "min_candidate_margin": -0.31396740674972534,
    "missed_high_roi_count_proxy": 2,
    "missing_same_context_contrast_count": 0,
    "moderate_candidate_gap_count": 1,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 1,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 28.0,
    "region": "tranquillitatis_balmer_like_20km",
    "same_context_low_roi_or_delay_record_count": 2,
    "score_missed_high_roi_count": 2,
    "task_count": 20,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "a67f331bdb819d7d",
    "deep_candidate_gap_count": 1,
    "embedding_missed_high_roi_count": 1,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "random-wave",
    "max_missed_roi": 0.9191120266914368,
    "mean_candidate_margin": -0.4573090076446533,
    "mean_knn_positive_fraction": 0.0,
    "mean_missed_roi": 0.9191120266914368,
    "median_knn_positive_fraction": 0.0,
    "min_candidate_margin": -0.4573090076446533,
    "missed_high_roi_count_proxy": 1,
    "missing_same_context_contrast_count": 1,
    "moderate_candidate_gap_count": 0,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 1,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 20.919112026691437,
    "region": "tranquillitatis_balmer_like_20km",
    "same_context_low_roi_or_delay_record_count": 0,
    "score_missed_high_roi_count": 1,
    "task_count": 50,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "e6b17bbf825984ae",
    "deep_candidate_gap_count": 1,
    "embedding_missed_high_roi_count": 1,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "random-wave",
    "max_missed_roi": 0.8415210247039795,
    "mean_candidate_margin": -0.8569196499884129,
    "mean_knn_positive_fraction": 0.0,
    "mean_missed_roi": 0.8415210247039795,
    "median_knn_positive_fraction": 0.0,
    "min_candidate_margin": -0.8569196499884129,
    "missed_high_roi_count_proxy": 1,
    "missing_same_context_contrast_count": 1,
    "moderate_candidate_gap_count": 0,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 1,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 20.84152102470398,
    "region": "tranquillitatis_balmer_like_20km",
    "same_context_low_roi_or_delay_record_count": 0,
    "score_missed_high_roi_count": 1,
    "task_count": 50,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "ac15bc4e7e3d6fff",
    "deep_candidate_gap_count": 0,
    "embedding_missed_high_roi_count": 1,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "sector-wave",
    "max_missed_roi": 15.120423316955566,
    "mean_candidate_margin": -0.07268983125686646,
    "mean_knn_positive_fraction": 0.4,
    "mean_missed_roi": 15.120423316955566,
    "median_knn_positive_fraction": 0.4,
    "min_candidate_margin": -0.07268983125686646,
    "missed_high_roi_count_proxy": 1,
    "missing_same_context_contrast_count": 1,
    "moderate_candidate_gap_count": 1,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 1,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 20.0,
    "region": "tranquillitatis_balmer_like_20km",
    "same_context_low_roi_or_delay_record_count": 0,
    "score_missed_high_roi_count": 1,
    "task_count": 20,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "3d1bd8618099b573",
    "deep_candidate_gap_count": 0,
    "embedding_missed_high_roi_count": 1,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "sector-wave",
    "max_missed_roi": 13.129931449890137,
    "mean_candidate_margin": -0.09617090225219727,
    "mean_knn_positive_fraction": 0.2,
    "mean_missed_roi": 13.129931449890137,
    "median_knn_positive_fraction": 0.2,
    "min_candidate_margin": -0.09617090225219727,
    "missed_high_roi_count_proxy": 1,
    "missing_same_context_contrast_count": 0,
    "moderate_candidate_gap_count": 1,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 1,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 19.0,
    "region": "tranquillitatis_balmer_like_20km",
    "same_context_low_roi_or_delay_record_count": 1,
    "score_missed_high_roi_count": 1,
    "task_count": 20,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "45baa40751a0bf77",
    "deep_candidate_gap_count": 1,
    "embedding_missed_high_roi_count": 1,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "sector-wave",
    "max_missed_roi": 13.436327934265137,
    "mean_candidate_margin": -0.5750163197517395,
    "mean_knn_positive_fraction": 0.2,
    "mean_missed_roi": 13.436327934265137,
    "median_knn_positive_fraction": 0.2,
    "min_candidate_margin": -0.5750163197517395,
    "missed_high_roi_count_proxy": 1,
    "missing_same_context_contrast_count": 0,
    "moderate_candidate_gap_count": 0,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 0,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 17.0,
    "region": "tranquillitatis_balmer_like_20km",
    "same_context_low_roi_or_delay_record_count": 1,
    "score_missed_high_roi_count": 1,
    "task_count": 20,
    "training_label_allowed_before_worker_reachability": false
  },
  {
    "context_hash": "b6d808ebac2a6dd8",
    "deep_candidate_gap_count": 0,
    "embedding_missed_high_roi_count": 1,
    "exact_safe_scope": "diagnostic_only_no_certificate_effect",
    "family": "sector-wave",
    "max_missed_roi": 0.8736749887466431,
    "mean_candidate_margin": -0.14950644969940186,
    "mean_knn_positive_fraction": 0.2,
    "mean_missed_roi": 0.8736749887466431,
    "median_knn_positive_fraction": 0.2,
    "min_candidate_margin": -0.14950644969940186,
    "missed_high_roi_count_proxy": 1,
    "missing_same_context_contrast_count": 1,
    "moderate_candidate_gap_count": 1,
    "near_candidate_threshold_count": 0,
    "nearest_negative_closer_count": 0,
    "primary_action": "collect_same_context_positive_negative_contrast",
    "priority_score": 13.873674988746643,
    "region": "apollo15_20km",
    "same_context_low_roi_or_delay_record_count": 0,
    "score_missed_high_roi_count": 1,
    "task_count": 20,
    "training_label_allowed_before_worker_reachability": false
  }
]
```

## 下一步

```json
{
  "do_not_do": [
    "lower_candidate_threshold_to_force_acceptance",
    "treat_true_rc_negative_or_exact_safe_hit_as_positive_label",
    "use_gat_or_knn_ood_as_certificate_source"
  ],
  "primary": "collect_context_local_contrast_before_threshold_or_rescue_changes"
}
```

## Exact-safe 边界

- 该审计只读离线 artifact，不产生训练标签；
- worker reachability / causal ROI 审计完成前，任何候选都不能转成 positive label；
- GAT / kNN / OOD 仍不能产生 official bound 或 certificate；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
