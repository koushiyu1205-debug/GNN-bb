# 2026-06-17 BPC_future GAT Target Mode Stage 3 v107 Sector-wave Context Contrast 报告

## 结论

本报告只做离线 Stage 3 诊断：读取 v106 sector-wave validation decisions，构造同 context high-ROI vs accepted low-ROI/bad contrast pairs，判断 high-ROI miss 是阈值近失还是模型排序结构性失败。

```text
focus_family = sector-wave
run_count = 3
pair_count = 6
missed_high_roi_pair_count = 4
missed_raw_rank_failure_rate = 1.0000
missed_safe_rank_failure_rate = 1.0000
recommended_next_step = train_sector_wave_same_context_pairwise_ranking_with_trace_features
stage3_completed = false
stage4_candidate_ready = false
selector_can_certificate = false
```

## Aggregate Buckets

```json
{
  "accepted_high_roi_low_roi_suppression_pair": 2,
  "missed_high_roi_raw_and_safe_rank_reversal": 4
}
```

## Run Comparison

| run | pairs | missed-pairs | raw rank fail | safe rank fail | batch rank fail | buckets |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v99 | 2 | 0 | 0 | 0 | 0 | {'accepted_high_roi_low_roi_suppression_pair': 2} |
| v102 | 2 | 2 | 2 | 2 | 1 | {'missed_high_roi_raw_and_safe_rank_reversal': 2} |
| v103 | 2 | 2 | 2 | 2 | 0 | {'missed_high_roi_raw_and_safe_rank_reversal': 2} |

## Top Contrast Evidence

### v99

```json
{
  "context_contrast_pairs_path": "BPC_future/results/gat_batch_impact_sector_wave_context_contrast_v107_v106_20260617/v99_sector-wave_context_contrast_pairs.jsonl",
  "context_contrast_rows_path": "BPC_future/results/gat_batch_impact_sector_wave_context_contrast_v107_v106_20260617/v99_sector-wave_context_contrast_rows.jsonl",
  "top_context_rows": [
    {
      "context_hash": "3d1bd8618099b573",
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "min_missed_raw_candidate_score_gap": null,
      "min_missed_safe_candidate_score_gap": null,
      "missed_high_roi_pair_count": 0,
      "missed_raw_rank_failure_count": 0,
      "missed_safe_rank_failure_count": 0,
      "pair_count": 1,
      "recommended_repair": "low_roi_acceptance_suppression",
      "repair_bucket_counts": {
        "accepted_high_roi_low_roi_suppression_pair": 1
      }
    },
    {
      "context_hash": "45baa40751a0bf77",
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "min_missed_raw_candidate_score_gap": null,
      "min_missed_safe_candidate_score_gap": null,
      "missed_high_roi_pair_count": 0,
      "missed_raw_rank_failure_count": 0,
      "missed_safe_rank_failure_count": 0,
      "pair_count": 1,
      "recommended_repair": "low_roi_acceptance_suppression",
      "repair_bucket_counts": {
        "accepted_high_roi_low_roi_suppression_pair": 1
      }
    }
  ],
  "top_missed_rank_failures": []
}
```

### v102

```json
{
  "context_contrast_pairs_path": "BPC_future/results/gat_batch_impact_sector_wave_context_contrast_v107_v106_20260617/v102_sector-wave_context_contrast_pairs.jsonl",
  "context_contrast_rows_path": "BPC_future/results/gat_batch_impact_sector_wave_context_contrast_v107_v106_20260617/v102_sector-wave_context_contrast_rows.jsonl",
  "top_context_rows": [
    {
      "context_hash": "45baa40751a0bf77",
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "min_missed_raw_candidate_score_gap": -0.06656420230865479,
      "min_missed_safe_candidate_score_gap": -0.03136645563161074,
      "missed_high_roi_pair_count": 1,
      "missed_raw_rank_failure_count": 1,
      "missed_safe_rank_failure_count": 1,
      "pair_count": 1,
      "recommended_repair": "pairwise_ranking_or_representation_repair",
      "repair_bucket_counts": {
        "missed_high_roi_raw_and_safe_rank_reversal": 1
      }
    },
    {
      "context_hash": "3d1bd8618099b573",
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "min_missed_raw_candidate_score_gap": -0.0634964108467102,
      "min_missed_safe_candidate_score_gap": -0.029105437273190884,
      "missed_high_roi_pair_count": 1,
      "missed_raw_rank_failure_count": 1,
      "missed_safe_rank_failure_count": 1,
      "pair_count": 1,
      "recommended_repair": "pairwise_ranking_or_representation_repair",
      "repair_bucket_counts": {
        "missed_high_roi_raw_and_safe_rank_reversal": 1
      }
    }
  ],
  "top_missed_rank_failures": [
    {
      "batch_score_gap": 0.00017023086547851562,
      "context_hash": "45baa40751a0bf77",
      "negative_roi": 0.4757407009601593,
      "positive_missed_reasons": [
        "no_candidate_above_threshold",
        "candidate_risk_adjusted_below_threshold",
        "candidate_delay_risk_above_threshold"
      ],
      "positive_raw_candidate_margin": 0.34714193758324025,
      "positive_roi": 13.436327934265137,
      "positive_safe_candidate_margin": -0.030077336943372265,
      "raw_candidate_score_gap": -0.06656420230865479,
      "repair_bucket": "missed_high_roi_raw_and_safe_rank_reversal",
      "roi_gap": 12.960587233304977,
      "safe_candidate_score_gap": -0.03136645563161074,
      "task_count": 20
    },
    {
      "batch_score_gap": -0.015042990446090698,
      "context_hash": "3d1bd8618099b573",
      "negative_roi": 0.5492770671844482,
      "positive_missed_reasons": [
        "no_candidate_above_threshold",
        "candidate_risk_adjusted_below_threshold",
        "candidate_delay_risk_above_threshold"
      ],
      "positive_raw_candidate_margin": 0.35286589083031056,
      "positive_roi": 13.129931449890137,
      "positive_safe_candidate_margin": -0.026812396311212003,
      "raw_candidate_score_gap": -0.0634964108467102,
      "repair_bucket": "missed_high_roi_raw_and_safe_rank_reversal",
      "roi_gap": 12.580654382705688,
      "safe_candidate_score_gap": -0.029105437273190884,
      "task_count": 20
    }
  ]
}
```

### v103

```json
{
  "context_contrast_pairs_path": "BPC_future/results/gat_batch_impact_sector_wave_context_contrast_v107_v106_20260617/v103_sector-wave_context_contrast_pairs.jsonl",
  "context_contrast_rows_path": "BPC_future/results/gat_batch_impact_sector_wave_context_contrast_v107_v106_20260617/v103_sector-wave_context_contrast_rows.jsonl",
  "top_context_rows": [
    {
      "context_hash": "45baa40751a0bf77",
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "min_missed_raw_candidate_score_gap": -0.025783628225326538,
      "min_missed_safe_candidate_score_gap": -0.056338698524500685,
      "missed_high_roi_pair_count": 1,
      "missed_raw_rank_failure_count": 1,
      "missed_safe_rank_failure_count": 1,
      "pair_count": 1,
      "recommended_repair": "pairwise_ranking_or_representation_repair",
      "repair_bucket_counts": {
        "missed_high_roi_raw_and_safe_rank_reversal": 1
      }
    },
    {
      "context_hash": "3d1bd8618099b573",
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "min_missed_raw_candidate_score_gap": -0.014831185340881348,
      "min_missed_safe_candidate_score_gap": -0.048666504484558004,
      "missed_high_roi_pair_count": 1,
      "missed_raw_rank_failure_count": 1,
      "missed_safe_rank_failure_count": 1,
      "pair_count": 1,
      "recommended_repair": "pairwise_ranking_or_representation_repair",
      "repair_bucket_counts": {
        "missed_high_roi_raw_and_safe_rank_reversal": 1
      }
    }
  ],
  "top_missed_rank_failures": [
    {
      "batch_score_gap": 0.003704845905303955,
      "context_hash": "45baa40751a0bf77",
      "negative_roi": 0.4757407009601593,
      "positive_missed_reasons": [
        "no_candidate_above_threshold",
        "candidate_risk_adjusted_below_threshold"
      ],
      "positive_raw_candidate_margin": 0.20681095858878962,
      "positive_roi": 13.436327934265137,
      "positive_safe_candidate_margin": -0.03524219770333836,
      "raw_candidate_score_gap": -0.025783628225326538,
      "repair_bucket": "missed_high_roi_raw_and_safe_rank_reversal",
      "roi_gap": 12.960587233304977,
      "safe_candidate_score_gap": -0.056338698524500685,
      "task_count": 20
    },
    {
      "batch_score_gap": 0.010232359170913696,
      "context_hash": "3d1bd8618099b573",
      "negative_roi": 0.5492770671844482,
      "positive_missed_reasons": [
        "no_candidate_above_threshold",
        "candidate_risk_adjusted_below_threshold"
      ],
      "positive_raw_candidate_margin": 0.22175971409149042,
      "positive_roi": 13.129931449890137,
      "positive_safe_candidate_margin": -0.030585010458928252,
      "raw_candidate_score_gap": -0.014831185340881348,
      "repair_bucket": "missed_high_roi_raw_and_safe_rank_reversal",
      "roi_gap": 12.580654382705688,
      "safe_candidate_score_gap": -0.048666504484558004,
      "task_count": 20
    }
  ]
}
```

## Interpretation

- 如果 missed high-ROI 对 accepted low-ROI 的 `raw_candidate_score_gap <= 0`，说明不是阈值差一点，而是当前表示/排序已经把正样本排在负样本后面。
- 如果 raw gap 为正但 safe gap 为负，优先修 risk-adjusted / delay head；如果 raw 和 safe 都反排，优先补 same-context pairwise ranking 与候选表示。
- 这些 pair 只能进入 Stage 2/3 训练或诊断，不能作为 online HIGH_PRIORITY、pricing oracle 或 certificate 依据。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```
