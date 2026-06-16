# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 5329
family_local_frontier_count = 653
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 44
best_safe_precision_ci_low = 0.919701682217986
best_accepted_batch_roi_ci_low = 0.787639392741144
best_local_reject_reasons = ['family_holdout_accepted_roi_below_threshold']
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 501,
    "accepted_batch_rate_too_low": 867,
    "accepted_batch_roi_below_baseline_margin": 501,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 4559,
    "expected_trajectory_utility_not_positive": 501,
    "false_high_priority_on_delay_too_high": 803,
    "false_safe_rate_union_too_high": 803,
    "family_holdout_accepted_batch_missing": 1429,
    "family_holdout_accepted_roi_below_threshold": 1910,
    "family_holdout_accepted_roi_not_measurable": 501,
    "family_holdout_precision_not_measurable": 501,
    "high_priority_precision_below_threshold_or_no_predictions": 146,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 365,
    "knn_ood_audit_missing": 5982,
    "safe_precision_below_threshold_or_no_accepted_batches": 501,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 5688
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 501,
    "accepted_batch_rate_too_low": 867,
    "accepted_batch_roi_below_baseline_margin": 501,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 4559,
    "expected_trajectory_utility_not_positive": 501,
    "false_high_priority_on_delay_too_high": 803,
    "false_safe_rate_union_too_high": 803,
    "family_holdout_accepted_batch_missing": 1429,
    "family_holdout_accepted_roi_below_threshold": 1910,
    "family_holdout_accepted_roi_not_measurable": 501,
    "family_holdout_precision_not_measurable": 501,
    "high_priority_precision_below_threshold_or_no_predictions": 146,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 365,
    "safe_precision_below_threshold_or_no_accepted_batches": 501,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 5688
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
