# GAT Batch Impact Opportunity Mining 报告

日期：2026-06-16

## 结论

本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。
它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。

```text
validation_record_count = 104
threshold_scope = family_delay_fallback
threshold_mode = context_delay_fallback
batch_threshold = 0.4583219885826111
candidate_threshold = 0.60591059923172
accepted = 35
high_roi_opportunities = 27
accepted_high_roi_opportunities = 18
missed_high_roi_opportunities = 9
accepted_high_roi_capture_rate = 0.6666666666666666
accepted_low_roi_or_bad = 17
recommended_primary = improve_candidate_high_priority_scores_for_high_roi_batches
production_ready = false
selector_can_certificate = false
```

## Missed Reasons

```json
{
  "batch_score_below_family_threshold": 4,
  "no_candidate_above_threshold": 9
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
    "accepted": 8,
    "accepted_high_roi_opportunities": 1,
    "accepted_low_roi_or_bad": 7,
    "high_roi_opportunities": 5,
    "missed_high_roi_opportunities": 4,
    "records": 42
  },
  "sector-wave": {
    "accepted": 27,
    "accepted_high_roi_opportunities": 17,
    "accepted_low_roi_or_bad": 10,
    "high_roi_opportunities": 22,
    "missed_high_roi_opportunities": 5,
    "records": 48
  }
}
```

## Recommended Next Step

```json
{
  "missed_family_counts": {
    "random-wave": 4,
    "sector-wave": 5
  },
  "missed_reason_counts": {
    "batch_score_below_family_threshold": 4,
    "no_candidate_above_threshold": 9
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
