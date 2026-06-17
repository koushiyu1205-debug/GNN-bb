# GAT Batch Impact Opportunity Mining 报告

日期：2026-06-16

## 结论

本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。
它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。

```text
validation_record_count = 119
threshold_scope = family_delay_fallback
threshold_mode = family_delay_fallback
batch_threshold = 0.44375303387641907
candidate_threshold = 0.0
candidate_admission_score_mode = risk_adjusted_rescue_window
candidate_delay_score_penalty = 0.75
candidate_rescue_raw_score_threshold = 0.3
candidate_rescue_delay_risk_threshold = 0.75
candidate_rescue_delay_score_penalty = 0.25
candidate_delay_gate_enabled = True
candidate_delay_risk_threshold = 0.5
family_delay_fallback_families = ['greedy-anchor']
context_delay_fallback_contexts = []
accepted = 62
high_roi_opportunities = 30
accepted_high_roi_opportunities = 29
missed_high_roi_opportunities = 1
accepted_high_roi_capture_rate = 0.9666666666666667
accepted_low_roi_or_bad = 33
recommended_primary = improve_batch_roi_ranking_or_collect_more_high_roi_batch_examples
production_ready = false
selector_can_certificate = false
```

## Missed Reasons

```json
{
  "batch_score_below_family_threshold": 1,
  "candidate_delay_risk_above_threshold": 1,
  "no_candidate_above_threshold": 1
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
    "accepted": 24,
    "accepted_high_roi_opportunities": 6,
    "accepted_low_roi_or_bad": 18,
    "high_roi_opportunities": 6,
    "missed_high_roi_opportunities": 0,
    "records": 44
  },
  "sector-wave": {
    "accepted": 38,
    "accepted_high_roi_opportunities": 23,
    "accepted_low_roi_or_bad": 15,
    "high_roi_opportunities": 24,
    "missed_high_roi_opportunities": 1,
    "records": 61
  }
}
```

## Recommended Next Step

```json
{
  "missed_family_counts": {
    "sector-wave": 1
  },
  "missed_reason_counts": {
    "batch_score_below_family_threshold": 1,
    "candidate_delay_risk_above_threshold": 1,
    "no_candidate_above_threshold": 1
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
