# GAT Batch Impact Opportunity Mining 报告

日期：2026-06-16

## 结论

本报告在 validation split 上应用当前 best threshold，定位 high-ROI batch 是被接受还是被错过。
它只做离线模型/阈值审计，不运行 BPC、pricing、RMP 或 certificate。

```text
validation_record_count = 136
threshold_scope = global
threshold_mode = separate_batch_candidate
batch_threshold = 0.47844576835632324
candidate_threshold = 0.19717147624284692
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.0
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
candidate_delay_gate_enabled = True
candidate_delay_risk_threshold = 0.5
family_delay_fallback_families = []
context_delay_fallback_contexts = []
accepted = 3
high_roi_opportunities = 32
accepted_high_roi_opportunities = 3
missed_high_roi_opportunities = 29
accepted_high_roi_capture_rate = 0.09375
accepted_low_roi_or_bad = 0
recommended_primary = calibrate_delay_risk_penalty_against_missed_high_roi_safe_candidates
production_ready = false
selector_can_certificate = false
```

## Missed Reasons

```json
{
  "batch_score_below_family_threshold": 28,
  "candidate_delay_risk_above_threshold": 27,
  "candidate_risk_adjusted_below_threshold": 27,
  "no_candidate_above_threshold": 29
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
    "accepted": 3,
    "accepted_high_roi_opportunities": 3,
    "accepted_low_roi_or_bad": 0,
    "high_roi_opportunities": 26,
    "missed_high_roi_opportunities": 23,
    "records": 78
  }
}
```

## Recommended Next Step

```json
{
  "missed_family_counts": {
    "random-wave": 6,
    "sector-wave": 23
  },
  "missed_reason_counts": {
    "batch_score_below_family_threshold": 28,
    "candidate_delay_risk_above_threshold": 27,
    "candidate_risk_adjusted_below_threshold": 27,
    "no_candidate_above_threshold": 29
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
