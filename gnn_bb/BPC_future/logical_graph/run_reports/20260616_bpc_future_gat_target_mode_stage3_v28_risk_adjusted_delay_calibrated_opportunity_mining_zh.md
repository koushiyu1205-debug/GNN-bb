# GAT Batch Impact Opportunity Mining 报告

日期：2026-06-16

## 结论

本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。
它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。

```text
validation_record_count = 119
threshold_scope = family_delay_fallback
threshold_mode = context_delay_fallback
batch_threshold = 0.0
candidate_threshold = 0.3353747177982669
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.0
candidate_delay_gate_enabled = True
candidate_delay_risk_threshold = 0.5
accepted = 23
high_roi_opportunities = 30
accepted_high_roi_opportunities = 15
missed_high_roi_opportunities = 15
accepted_high_roi_capture_rate = 0.5
accepted_low_roi_or_bad = 8
recommended_primary = calibrate_delay_risk_penalty_against_missed_high_roi_safe_candidates
production_ready = false
selector_can_certificate = false
```

## Missed Reasons

```json
{
  "candidate_delay_risk_above_threshold": 1,
  "candidate_risk_adjusted_below_threshold": 12,
  "no_candidate_above_threshold": 15
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
    "accepted": 2,
    "accepted_high_roi_opportunities": 1,
    "accepted_low_roi_or_bad": 1,
    "high_roi_opportunities": 6,
    "missed_high_roi_opportunities": 5,
    "records": 44
  },
  "sector-wave": {
    "accepted": 21,
    "accepted_high_roi_opportunities": 14,
    "accepted_low_roi_or_bad": 7,
    "high_roi_opportunities": 24,
    "missed_high_roi_opportunities": 10,
    "records": 61
  }
}
```

## Recommended Next Step

```json
{
  "missed_family_counts": {
    "random-wave": 5,
    "sector-wave": 10
  },
  "missed_reason_counts": {
    "candidate_delay_risk_above_threshold": 1,
    "candidate_risk_adjusted_below_threshold": 12,
    "no_candidate_above_threshold": 15
  },
  "primary": "calibrate_delay_risk_penalty_against_missed_high_roi_safe_candidates"
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
