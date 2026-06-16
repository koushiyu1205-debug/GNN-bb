# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 13015
family_local_frontier_count = 1250
family_delay_fallback_frontier_count = 4791
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 44
best_family_delay_fallback_families = []
best_safe_precision_ci_low = 0.919701682217986
best_accepted_batch_roi_ci_low = 0.787639392741144
best_local_reject_reasons = ['family_holdout_accepted_roi_below_threshold']
best_fallback_accepted_batch_count = 25
best_fallback_safe_precision_ci_low = 0.8668035060468212
best_fallback_accepted_batch_roi_ci_low = 1.42949258589271
best_fallback_delay_families = ['greedy-anchor', 'random-wave']
best_fallback_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 865,
    "accepted_batch_rate_too_low": 1537,
    "accepted_batch_roi_below_baseline_margin": 865,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 12925,
    "expected_trajectory_utility_not_positive": 865,
    "false_high_priority_on_delay_too_high": 3507,
    "false_safe_rate_union_too_high": 3389,
    "family_holdout_accepted_batch_missing": 3095,
    "family_holdout_accepted_roi_below_threshold": 4791,
    "family_holdout_accepted_roi_not_measurable": 865,
    "family_holdout_precision_not_measurable": 865,
    "high_priority_precision_below_threshold_or_no_predictions": 190,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 665,
    "knn_ood_audit_missing": 19056,
    "safe_precision_below_threshold_or_no_accepted_batches": 865,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 18342
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 865,
    "accepted_batch_rate_too_low": 1537,
    "accepted_batch_roi_below_baseline_margin": 865,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 12925,
    "expected_trajectory_utility_not_positive": 865,
    "false_high_priority_on_delay_too_high": 3507,
    "false_safe_rate_union_too_high": 3389,
    "family_holdout_accepted_batch_missing": 3095,
    "family_holdout_accepted_roi_below_threshold": 4791,
    "family_holdout_accepted_roi_not_measurable": 865,
    "family_holdout_precision_not_measurable": 865,
    "high_priority_precision_below_threshold_or_no_predictions": 190,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 665,
    "safe_precision_below_threshold_or_no_accepted_batches": 865,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 18342
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
