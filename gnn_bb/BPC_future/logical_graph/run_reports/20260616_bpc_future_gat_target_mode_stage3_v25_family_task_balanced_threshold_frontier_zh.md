# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 16303
family_local_frontier_count = 0
family_delay_fallback_frontier_count = 32331
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 58
best_family_delay_fallback_families = []
best_context_delay_fallback_contexts = []
best_safe_precision_ci_low = 0.9378800031047062
best_accepted_batch_roi_ci_low = 2.689249384486058
best_local_reject_reasons = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high', 'family_holdout_accepted_roi_below_threshold']
best_fallback_accepted_batch_count = 46
best_fallback_safe_precision_ci_low = 0.9229238226702192
best_fallback_accepted_batch_roi_ci_low = 3.4505214688238652
best_fallback_delay_families = []
best_fallback_delay_contexts = ['5e253e60eb577a74', '9554cd95954623fb', 'ed559d52013e0db0', 'fe1efba5e8e6424a']
best_fallback_reject_reasons = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high', 'family_holdout_accepted_roi_below_threshold']
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 6712,
    "accepted_batch_rate_too_low": 8880,
    "accepted_batch_roi_below_baseline_margin": 13315,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 25562,
    "expected_trajectory_utility_not_positive": 6712,
    "false_high_priority_on_delay_too_high": 39915,
    "false_safe_rate_union_too_high": 39782,
    "family_accepted_high_roi_count_below_threshold": 29934,
    "family_high_roi_capture_rate_below_threshold": 31464,
    "family_holdout_accepted_batch_missing": 6098,
    "family_holdout_accepted_roi_below_threshold": 21435,
    "family_holdout_accepted_roi_not_measurable": 6712,
    "family_holdout_precision_not_measurable": 6712,
    "high_priority_precision_below_threshold_or_no_predictions": 10767,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 26536,
    "knn_ood_audit_missing": 48634,
    "safe_precision_below_threshold_or_no_accepted_batches": 6712,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 35774
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 6712,
    "accepted_batch_rate_too_low": 8880,
    "accepted_batch_roi_below_baseline_margin": 13315,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 25562,
    "expected_trajectory_utility_not_positive": 6712,
    "false_high_priority_on_delay_too_high": 39915,
    "false_safe_rate_union_too_high": 39782,
    "family_accepted_high_roi_count_below_threshold": 29934,
    "family_high_roi_capture_rate_below_threshold": 31464,
    "family_holdout_accepted_batch_missing": 6098,
    "family_holdout_accepted_roi_below_threshold": 21435,
    "family_holdout_accepted_roi_not_measurable": 6712,
    "family_holdout_precision_not_measurable": 6712,
    "high_priority_precision_below_threshold_or_no_predictions": 10767,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 26536,
    "safe_precision_below_threshold_or_no_accepted_batches": 6712,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 35774
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
