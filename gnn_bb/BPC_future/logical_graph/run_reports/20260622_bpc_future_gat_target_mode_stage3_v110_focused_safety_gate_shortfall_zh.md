# GAT Batch Impact Gate Shortfall 报告

日期：2026-06-16

## 结论

本报告只审计 Stage 3 threshold frontier 的 gate shortfall，不运行 BPC、pricing、RMP 或 certificate。
它的用途是把 `stage4_candidate_ready=false` 拆成可执行的补数据 / 调阈值方向，而不是放宽 gate。

```text
total_frontier_rows = 18848
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
best_threshold_scope = global
best_threshold_mode = separate_batch_candidate
best_accepted_batch_count = 11
best_safe_precision_ci_low = 0.7411599827511859
best_safe_precision_extra_all_success_needed = 24
best_accepted_batch_roi = 11.667098435488613
best_accepted_batch_roi_ci_low = 6.569454500960253
best_accepted_batch_roi_ci_low_gap = 0.0
delay_safe_threshold_count = 3093
delay_safe_with_accepted_batch_count = 2340
delay_safe_accepted_batch_count_max = 11
delay_safe_candidate_threshold_min = 0.45149831826078507
delay_safe_candidate_threshold_max = 0.7725125999996239
best_delay_safe_accepted_batch_count = 11
best_delay_safe_accepted_batch_roi_ci_low = 6.569454500960253
best_delay_safe_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
recommended_primary = collect_more_safe_validation_accepts
production_ready = false
selector_can_certificate = false
```

## Family Shortfall

```json
{
  "top_family_specific_delay_fallback_families": {},
  "top_missing_accepted_families": {},
  "top_missing_accepted_opportunity_families": {}
}
```

## Delay-Safe Frontier

```json
{
  "delay_safe_local_gate_pass_count": 0,
  "delay_safe_reject_reason_counts": {
    "accepted_batch_rate_too_low": 1138,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 427,
    "family_holdout_accepted_batch_missing": 571,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 399,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 2340
  },
  "delay_safe_threshold_count": 3093,
  "delay_safe_with_accepted_batch_count": 2340
}
```

## Recommended Next Step

```json
{
  "accepted_batch_roi_ci_low_gap": 0.0,
  "delay_safe_accepted_batch_count_max": 11,
  "delay_safe_candidate_threshold_max": 0.7725125999996239,
  "delay_safe_candidate_threshold_min": 0.45149831826078507,
  "delay_safe_threshold_count": 3093,
  "families_recommended_for_delay_fallback": [],
  "families_with_missed_opportunity": [],
  "primary": "collect_more_safe_validation_accepts",
  "safe_precision_additional_all_success_needed": 24
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
