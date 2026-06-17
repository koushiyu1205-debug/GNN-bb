# BPC Future GAT Target Mode Stage 3 v43 v15 Missed High-ROI 诊断

日期：2026-06-16

## 结论

本报告将 v15 score-margin 与 embedding-separation 审计合并为可复跑诊断。
结论是：v15 missed high-ROI 不是简单阈值差一点，而是 candidate-head
分数缺口和 embedding 结构混杂同时存在；Stage4 first-tranche 回流还显示
显式 target worker 候选 ROI 混合，不能直接作为 HIGH_PRIORITY 证据。

```text
primary = candidate_head_score_gap_plus_embedding_structural_gap
missed_high_roi_opportunities = 16
accepted_high_roi_opportunities = 12
candidate_threshold = 0.9019626379013062
near_threshold_miss_count = 0
non_near_threshold_miss_count = 16
candidate_margin_bucket_counts = {'deep_candidate_score_gap': 11, 'moderate_candidate_score_gap': 5}
missed_candidate_score_margin_mean = -0.3829170756507665
missed_candidate_score_margin_min = -0.8569196499884129
missed_candidate_score_margin_max = -0.07226938009262085
missed_nearest_negative_closer_count = 10
missed_nearest_negative_closer_rate = 0.625
missed_knn_positive_fraction_mean = 0.1625
accepted_high_roi_knn_positive_fraction_mean = 0.5
worker_positive_trajectory_roi_count = 2
worker_nonpositive_trajectory_roi_count = 7
v16_checkpoint_gate_pass = False
v16_stage4_candidate_ready = False
recommended_next_step = collect_train_split_same_context_positive_negative_pairs_and_delay_hard_negatives
production_ready = false
selector_can_certificate = false
```

## Family Diagnosis

```json
[
  {
    "candidate_margin_bucket_counts": {},
    "classification": "no_missed_high_roi",
    "deep_candidate_score_gap_count": 0,
    "family": "greedy-anchor",
    "missed_high_roi_opportunities": 0,
    "missed_nearest_negative_closer_count": 0,
    "missed_nearest_negative_closer_rate": 0.0,
    "missed_without_same_context_contrast_count": 0,
    "moderate_candidate_score_gap_count": 0,
    "near_threshold_miss_count": 0,
    "non_near_threshold_miss_count": 0,
    "task_count_counts": {}
  },
  {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 5
    },
    "classification": "embedding_structural_gap",
    "deep_candidate_score_gap_count": 5,
    "family": "random-wave",
    "missed_high_roi_opportunities": 5,
    "missed_nearest_negative_closer_count": 5,
    "missed_nearest_negative_closer_rate": 1.0,
    "missed_without_same_context_contrast_count": 2,
    "moderate_candidate_score_gap_count": 0,
    "near_threshold_miss_count": 0,
    "non_near_threshold_miss_count": 5,
    "task_count_counts": {
      "50": 5
    }
  },
  {
    "candidate_margin_bucket_counts": {
      "deep_candidate_score_gap": 6,
      "moderate_candidate_score_gap": 5
    },
    "classification": "mixed_candidate_head_embedding_gap",
    "deep_candidate_score_gap_count": 6,
    "family": "sector-wave",
    "missed_high_roi_opportunities": 11,
    "missed_nearest_negative_closer_count": 5,
    "missed_nearest_negative_closer_rate": 0.45454545454545453,
    "missed_without_same_context_contrast_count": 5,
    "moderate_candidate_score_gap_count": 5,
    "near_threshold_miss_count": 0,
    "non_near_threshold_miss_count": 11,
    "task_count_counts": {
      "20": 11
    }
  }
]
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
