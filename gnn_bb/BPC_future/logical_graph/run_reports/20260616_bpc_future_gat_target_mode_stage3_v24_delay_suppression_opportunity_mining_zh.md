# GAT Batch Impact Opportunity Mining 报告

日期：2026-06-16

## 结论

本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。
它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。

```text
validation_record_count = 119
threshold_scope = global
threshold_mode = separate_batch_candidate
batch_threshold = 0.0
candidate_threshold = 0.4959893226623535
accepted = 17
high_roi_opportunities = 30
accepted_high_roi_opportunities = 13
missed_high_roi_opportunities = 17
accepted_high_roi_capture_rate = 0.43333333333333335
accepted_low_roi_or_bad = 4
recommended_primary = improve_candidate_high_priority_scores_for_high_roi_batches
production_ready = false
selector_can_certificate = false
```

## Missed Reasons

```json
{
  "no_candidate_above_threshold": 17
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
    "accepted": 0,
    "accepted_high_roi_opportunities": 0,
    "accepted_low_roi_or_bad": 0,
    "high_roi_opportunities": 6,
    "missed_high_roi_opportunities": 6,
    "records": 44
  },
  "sector-wave": {
    "accepted": 17,
    "accepted_high_roi_opportunities": 13,
    "accepted_low_roi_or_bad": 4,
    "high_roi_opportunities": 24,
    "missed_high_roi_opportunities": 11,
    "records": 61
  }
}
```

## Recommended Next Step

```json
{
  "missed_family_counts": {
    "random-wave": 6,
    "sector-wave": 11
  },
  "missed_reason_counts": {
    "no_candidate_above_threshold": 17
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
