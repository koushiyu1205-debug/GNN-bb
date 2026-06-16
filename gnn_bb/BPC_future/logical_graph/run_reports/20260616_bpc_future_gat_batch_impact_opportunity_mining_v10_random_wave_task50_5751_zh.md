# GAT Batch Impact Opportunity Mining 报告

日期：2026-06-16

## 结论

本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。
它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。

```text
validation_record_count = 102
threshold_scope = family_delay_fallback
threshold_mode = family_delay_fallback
batch_threshold = 0.42934882640838623
candidate_threshold = 0.5509535670280457
accepted = 45
high_roi_opportunities = 27
accepted_high_roi_opportunities = 22
missed_high_roi_opportunities = 5
accepted_high_roi_capture_rate = 0.8148148148148148
accepted_low_roi_or_bad = 23
recommended_primary = improve_candidate_high_priority_scores_for_high_roi_batches
production_ready = false
selector_can_certificate = false
```

## Missed Reasons

```json
{
  "batch_score_below_family_threshold": 3,
  "no_candidate_above_threshold": 5
}
```

## Family Summary

```json
{
  "greedy-anchor": {
    "accepted": 3,
    "accepted_high_roi_opportunities": 0,
    "accepted_low_roi_or_bad": 3,
    "high_roi_opportunities": 0,
    "missed_high_roi_opportunities": 0,
    "records": 14
  },
  "random-wave": {
    "accepted": 12,
    "accepted_high_roi_opportunities": 3,
    "accepted_low_roi_or_bad": 9,
    "high_roi_opportunities": 5,
    "missed_high_roi_opportunities": 2,
    "records": 42
  },
  "sector-wave": {
    "accepted": 30,
    "accepted_high_roi_opportunities": 19,
    "accepted_low_roi_or_bad": 11,
    "high_roi_opportunities": 22,
    "missed_high_roi_opportunities": 3,
    "records": 46
  }
}
```

## Recommended Next Step

```json
{
  "missed_family_counts": {
    "random-wave": 2,
    "sector-wave": 3
  },
  "missed_reason_counts": {
    "batch_score_below_family_threshold": 3,
    "no_candidate_above_threshold": 5
  },
  "primary": "improve_candidate_high_priority_scores_for_high_roi_batches"
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
