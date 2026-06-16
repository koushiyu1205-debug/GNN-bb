# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 16303
family_local_frontier_count = 401
family_delay_fallback_frontier_count = 27911
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 21
best_family_delay_fallback_families = []
best_context_delay_fallback_contexts = ['0dab6941e7ad46c4', '5e253e60eb577a74']
best_safe_precision_ci_low = 0.8453561767357979
best_accepted_batch_roi_ci_low = 2.1236682014139197
best_local_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
best_fallback_accepted_batch_count = 21
best_fallback_safe_precision_ci_low = 0.8453561767357979
best_fallback_accepted_batch_roi_ci_low = 2.1236682014139197
best_fallback_delay_families = []
best_fallback_delay_contexts = ['0dab6941e7ad46c4', '5e253e60eb577a74']
best_fallback_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 3279,
    "accepted_batch_rate_too_low": 4774,
    "accepted_batch_roi_below_baseline_margin": 7216,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 27199,
    "expected_trajectory_utility_not_positive": 3279,
    "false_high_priority_on_delay_too_high": 18188,
    "false_safe_rate_union_too_high": 17267,
    "family_accepted_high_roi_count_below_threshold": 25714,
    "family_high_roi_capture_rate_below_threshold": 25795,
    "family_holdout_accepted_batch_missing": 6458,
    "family_holdout_accepted_roi_below_threshold": 15929,
    "family_holdout_accepted_roi_not_measurable": 3279,
    "family_holdout_precision_not_measurable": 3279,
    "high_priority_precision_below_threshold_or_no_predictions": 3629,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 6922,
    "knn_ood_audit_missing": 44615,
    "safe_precision_below_threshold_or_no_accepted_batches": 3279,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 37459
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 3279,
    "accepted_batch_rate_too_low": 4774,
    "accepted_batch_roi_below_baseline_margin": 7216,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 27199,
    "expected_trajectory_utility_not_positive": 3279,
    "false_high_priority_on_delay_too_high": 18188,
    "false_safe_rate_union_too_high": 17267,
    "family_accepted_high_roi_count_below_threshold": 25714,
    "family_high_roi_capture_rate_below_threshold": 25795,
    "family_holdout_accepted_batch_missing": 6458,
    "family_holdout_accepted_roi_below_threshold": 15929,
    "family_holdout_accepted_roi_not_measurable": 3279,
    "family_holdout_precision_not_measurable": 3279,
    "high_priority_precision_below_threshold_or_no_predictions": 3629,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 6922,
    "safe_precision_below_threshold_or_no_accepted_batches": 3279,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 37459
  },
  "min_all_success_samples_needed": {
    "high_priority_all_success_count": 35,
    "high_priority_precision_ci_low_target": 0.9,
    "safe_all_success_count": 35,
    "safe_precision_ci_low_target": 0.9
  }
}
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
