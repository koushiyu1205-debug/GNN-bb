# GAT Batch Impact Opportunity Mining 报告

日期：2026-06-16

## 结论

本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。
它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。

```text
validation_record_count = 78
threshold_scope = global
threshold_mode = separate_batch_candidate
batch_threshold = 0.5142228007316589
candidate_threshold = 0.6242105960845947
accepted = 14
high_roi_opportunities = 8
accepted_high_roi_opportunities = 5
missed_high_roi_opportunities = 3
accepted_high_roi_capture_rate = 0.625
accepted_low_roi_or_bad = 9
recommended_primary = improve_batch_roi_ranking_or_collect_more_high_roi_batch_examples
production_ready = false
selector_can_certificate = false
```

## Missed Reasons

```json
{
  "batch_score_below_family_threshold": 3,
  "no_candidate_above_threshold": 3
}
```

## Family Summary

```json
{
  "greedy-anchor": {
    "accepted": 0,
    "accepted_high_roi_opportunities": 0,
    "accepted_low_roi_or_bad": 0,
    "high_roi_opportunities": 0,
    "missed_high_roi_opportunities": 0,
    "records": 14
  },
  "random-wave": {
    "accepted": 1,
    "accepted_high_roi_opportunities": 1,
    "accepted_low_roi_or_bad": 0,
    "high_roi_opportunities": 3,
    "missed_high_roi_opportunities": 2,
    "records": 38
  },
  "sector-wave": {
    "accepted": 13,
    "accepted_high_roi_opportunities": 4,
    "accepted_low_roi_or_bad": 9,
    "high_roi_opportunities": 5,
    "missed_high_roi_opportunities": 1,
    "records": 26
  }
}
```

## Recommended Next Step

```json
{
  "missed_family_counts": {
    "random-wave": 2,
    "sector-wave": 1
  },
  "missed_reason_counts": {
    "batch_score_below_family_threshold": 3,
    "no_candidate_above_threshold": 3
  },
  "primary": "improve_batch_roi_ranking_or_collect_more_high_roi_batch_examples"
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
