# GAT Target Mode Stage 3 v41 v39 False-positive Catalog 报告

日期：2026-06-16

## 结论

本报告只读 v39 batch-impact checkpoint / metrics / dataset，复用训练阶段的
candidate admission rule，逐 candidate  catalog 造成
`false_high_priority_on_delay` 的 delay-labeled 候选。它不运行 BPC、pricing、
RMP、worker 或 certificate。

```text
split = validation
batch_record_count = 123
evaluated_batch_record_count = 109
fallback_batch_record_count = 14
evaluated_candidate_count = 1066
predicted_candidate_count = 737
high_priority_true_positive_count = 693
false_high_priority_on_delay_count = 44
delay_label_count = 98
false_high_priority_on_delay = 0.4489795918367347
high_priority_precision = 0.9402985074626866
candidate_delay_gate_blocked_count = 329
candidate_threshold_zero = True
candidate_threshold_zero_effect = candidate_head_threshold_disabled_delay_gate_is_only_filter
all_metric_counts_match = True
primary_diagnosis = raise_candidate_threshold_or_make_candidate_head_usable_before_delay_gate
production_ready = false
selector_can_certificate = false
```

## Metric Count Check

```json
{
  "expected_training_counts": {
    "candidate_delay_gate_blocked_count": 329,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 0,
    "delay_label_count": 98,
    "false_high_priority_on_delay_count": 44,
    "high_priority_true_positive_count": 693,
    "predicted_candidate_count": 737
  },
  "matches_training_metrics": {
    "candidate_delay_gate_blocked_count": true,
    "candidate_rescue_window_eligible_count": true,
    "candidate_rescue_window_promoted_count": true,
    "candidate_risk_adjusted_suppressed_count": true,
    "delay_label_count": true,
    "false_high_priority_on_delay_count": true,
    "high_priority_true_positive_count": true,
    "predicted_candidate_count": true
  }
}
```

## Family / Task Counts

```json
{
  "family_counts": {
    "sector-wave": 44
  },
  "family_task_counts": {
    "sector-wave|20": 44
  },
  "task_count_counts": {
    "20": 44
  },
  "top_contexts": [
    {
      "context_hash": "ac056820151e9ad7",
      "count": 33,
      "family": "sector-wave"
    },
    {
      "context_hash": "79fde658840fe2b8",
      "count": 4,
      "family": "sector-wave"
    },
    {
      "context_hash": "b6d808ebac2a6dd8",
      "count": 4,
      "family": "sector-wave"
    },
    {
      "context_hash": "ac15bc4e7e3d6fff",
      "count": 2,
      "family": "sector-wave"
    },
    {
      "context_hash": "7b430465c7ae76b3",
      "count": 1,
      "family": "sector-wave"
    }
  ]
}
```

## Score Buckets

```json
{
  "candidate_admission_score": {
    "<= 0.25": 1,
    "<= 0.5": 43
  },
  "predicted_delay_risk_score": {
    "<= 0.4": 15,
    "<= 0.5": 29
  },
  "raw_high_priority_score": {
    "<= 0.5": 17,
    "<= 0.75": 27
  }
}
```

## Score Summary

```json
{
  "candidate_admission_score": {
    "count": 44,
    "max": 0.4917332490986581,
    "mean": 0.31605891640837264,
    "median": 0.2895073383095683,
    "min": 0.2410641684736614
  },
  "candidate_score_margin": {
    "count": 44,
    "max": 0.4917332490986581,
    "mean": 0.31605891640837264,
    "median": 0.2895073383095683,
    "min": 0.2410641684736614
  },
  "delay_gate_margin": {
    "count": 44,
    "max": 0.1734294593334198,
    "mean": 0.08581646870483052,
    "median": 0.0685194730758667,
    "min": 0.038285911083221436
  },
  "predicted_delay_risk_score": {
    "count": 44,
    "max": 0.46171408891677856,
    "mean": 0.4141835312951695,
    "median": 0.4314805269241333,
    "min": 0.3265705406665802
  },
  "raw_high_priority_score": {
    "count": 44,
    "max": 0.7301926612854004,
    "mean": 0.5356710153547201,
    "median": 0.5090803802013397,
    "min": 0.44783666729927063
  }
}
```

## Candidate Feature Summary

```json
{
  "best_position": {
    "count": 44,
    "max": 1.0,
    "mean": 1.0,
    "median": 1.0,
    "min": 1.0
  },
  "cost": {
    "count": 44,
    "max": 110.48400115966797,
    "mean": 92.73904904452237,
    "median": 93.94089126586914,
    "min": 73.62255096435547
  },
  "duplicate_signature": {
    "count": 44,
    "max": 0.0,
    "mean": 0.0,
    "median": 0.0,
    "min": 0.0
  },
  "duplicate_signature_pool_count_before": {
    "count": 44,
    "max": 0.0,
    "mean": 0.0,
    "median": 0.0,
    "min": 0.0
  },
  "new_task_set": {
    "count": 44,
    "max": 1.0,
    "mean": 0.9090909090909091,
    "median": 1.0,
    "min": 0.0
  },
  "order_observed": {
    "count": 44,
    "max": 1.0,
    "mean": 1.0,
    "median": 1.0,
    "min": 1.0
  },
  "sequence_length": {
    "count": 44,
    "max": 5.0,
    "mean": 3.2045454545454546,
    "median": 3.0,
    "min": 2.0
  },
  "sortie_count": {
    "count": 44,
    "max": 2.0,
    "mean": 1.7045454545454546,
    "median": 2.0,
    "min": 1.0
  },
  "strict_replacement_by_cost": {
    "count": 44,
    "max": 0.0,
    "mean": 0.0,
    "median": 0.0,
    "min": 0.0
  },
  "task_count": {
    "count": 44,
    "max": 5.0,
    "mean": 3.2045454545454546,
    "median": 3.0,
    "min": 2.0
  },
  "task_set_pool_count_before": {
    "count": 44,
    "max": 1.0,
    "mean": 0.09090909090909091,
    "median": 0.0,
    "min": 0.0
  },
  "true_reduced_cost": {
    "count": 44,
    "max": -0.8736760020256042,
    "mean": -11.022367047992619,
    "median": -5.022778272628784,
    "min": -41.31852722167969
  },
  "vehicle_count": {
    "count": 44,
    "max": 2.0,
    "mean": 1.7045454545454546,
    "median": 2.0,
    "min": 1.0
  },
  "weak_replacement_or_duplicate": {
    "count": 44,
    "max": 1.0,
    "mean": 0.09090909090909091,
    "median": 0.0,
    "min": 0.0
  }
}
```

## Diagnosis

```json
{
  "findings": [
    "candidate_threshold_zero_disables_candidate_head_as_a_filter",
    "false_positives_are_context_concentrated",
    "checkpoint_remains_diagnostic_not_stage4_candidate"
  ],
  "primary": "raise_candidate_threshold_or_make_candidate_head_usable_before_delay_gate",
  "production_ready": false,
  "stage4_candidate_ready": false
}
```

## Next Step

- 不应继续把 v39 送入 Stage 4 shadow / opt-in admission；
- 下一轮 threshold frontier 必须让 candidate head 成为真实过滤器，不能选出
  `candidate_threshold=0` 后只依赖 delay gate；
- false positive 高度集中在少数 `sector-wave|20` context，优先对这些 context
  补同 context low-ROI / delay hard-negative contrast，或加入 context-specific
  fallback / calibration audit；
- 该 catalog 只能指导离线训练和采样，不能作为 pruning、official bound 或
  certificate 来源。

## Artifacts

```text
summary = BPC_future/results/gat_batch_impact_false_positive_catalog_v39_neighbor_roi_b6d808_20260616/summary.json
false_positive_candidates = BPC_future/results/gat_batch_impact_false_positive_catalog_v39_neighbor_roi_b6d808_20260616/false_high_priority_on_delay_candidates.jsonl
context_summary = BPC_future/results/gat_batch_impact_false_positive_catalog_v39_neighbor_roi_b6d808_20260616/context_false_positive_summary.jsonl
batch_record_summary = BPC_future/results/gat_batch_impact_false_positive_catalog_v39_neighbor_roi_b6d808_20260616/batch_record_decision_summary.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- `DELAY_QUEUE` 只能有限延迟 true-RC negative，不能永久 reject；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
