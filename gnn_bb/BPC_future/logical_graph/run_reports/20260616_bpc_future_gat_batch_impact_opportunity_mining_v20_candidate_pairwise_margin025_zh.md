# GAT Batch Impact Opportunity Mining 报告

日期：2026-06-16

## 结论

本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。
它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。

```text
validation_record_count = 119
threshold_scope = family_local
threshold_mode = family_local_batch_candidate
batch_threshold = 0.4863094091415405
candidate_threshold = 0.5760983228683472
accepted = 10
high_roi_opportunities = 30
accepted_high_roi_opportunities = 8
missed_high_roi_opportunities = 22
accepted_high_roi_capture_rate = 0.26666666666666666
accepted_low_roi_or_bad = 2
recommended_primary = improve_candidate_high_priority_scores_for_high_roi_batches
production_ready = false
selector_can_certificate = false
```

## Missed Reasons

```json
{
  "batch_score_below_family_threshold": 7,
  "no_candidate_above_threshold": 22
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
    "high_roi_opportunities": 6,
    "missed_high_roi_opportunities": 5,
    "records": 44
  },
  "sector-wave": {
    "accepted": 9,
    "accepted_high_roi_opportunities": 7,
    "accepted_low_roi_or_bad": 2,
    "high_roi_opportunities": 24,
    "missed_high_roi_opportunities": 17,
    "records": 61
  }
}
```

## Recommended Next Step

```json
{
  "missed_family_counts": {
    "random-wave": 5,
    "sector-wave": 17
  },
  "missed_reason_counts": {
    "batch_score_below_family_threshold": 7,
    "no_candidate_above_threshold": 22
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
