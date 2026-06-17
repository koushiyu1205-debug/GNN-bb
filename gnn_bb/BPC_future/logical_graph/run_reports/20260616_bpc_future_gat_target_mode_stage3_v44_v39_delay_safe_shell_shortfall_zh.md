# GAT Batch Impact Gate Shortfall 报告

日期：2026-06-16

## 结论

本报告只审计 Stage 3 threshold frontier 的 gate shortfall，不运行 BPC、pricing、RMP 或 certificate。
它的用途是把 `stage4_candidate_ready=false` 拆成可执行的补数据 / 调阈值方向，而不是放宽 gate。

```text
total_frontier_rows = 36199
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
best_threshold_scope = family_delay_fallback
best_threshold_mode = family_delay_fallback
best_accepted_batch_count = 46
best_safe_precision_ci_low = 0.9229238226702192
best_safe_precision_extra_all_success_needed = 0
best_accepted_batch_roi = 6.435102400106742
best_accepted_batch_roi_ci_low = 3.3215176548675847
best_accepted_batch_roi_ci_low_gap = 0.0
delay_safe_threshold_count = 1309
delay_safe_with_accepted_batch_count = 335
delay_safe_accepted_batch_count_max = 2
delay_safe_candidate_threshold_min = 0.48583269260814177
delay_safe_candidate_threshold_max = 0.4917332490986581
best_delay_safe_accepted_batch_count = 2
best_delay_safe_accepted_batch_roi_ci_low = -16.002698850631717
best_delay_safe_reject_reasons = ['high_priority_precision_ci_low_below_threshold_or_not_measurable', 'safe_precision_ci_low_below_threshold_or_not_measurable', 'accepted_batch_rate_too_low', 'accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable', 'family_holdout_accepted_batch_missing']
recommended_primary = delay_safe_shell_exists_but_coverage_too_small
production_ready = false
selector_can_certificate = false
```

## Family Shortfall

```json
{
  "top_family_specific_delay_fallback_families": {
    "greedy-anchor": 30
  },
  "top_missing_accepted_families": {
    "greedy-anchor": 30
  },
  "top_missing_accepted_opportunity_families": {}
}
```

## Delay-Safe Frontier

```json
{
  "delay_safe_local_gate_pass_count": 0,
  "delay_safe_reject_reason_counts": {
    "accepted_batch_rate_too_low": 335,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 335,
    "family_holdout_accepted_batch_missing": 335,
    "high_priority_precision_below_threshold_or_no_predictions": 109,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 335,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 335
  },
  "delay_safe_threshold_count": 1309,
  "delay_safe_with_accepted_batch_count": 335
}
```

## Recommended Next Step

```json
{
  "accepted_batch_roi_ci_low_gap": 0.0,
  "delay_safe_accepted_batch_count_max": 2,
  "delay_safe_candidate_threshold_max": 0.4917332490986581,
  "delay_safe_candidate_threshold_min": 0.48583269260814177,
  "delay_safe_threshold_count": 1309,
  "families_recommended_for_delay_fallback": [
    "greedy-anchor"
  ],
  "families_with_missed_opportunity": [],
  "primary": "delay_safe_shell_exists_but_coverage_too_small",
  "safe_precision_additional_all_success_needed": 0
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
