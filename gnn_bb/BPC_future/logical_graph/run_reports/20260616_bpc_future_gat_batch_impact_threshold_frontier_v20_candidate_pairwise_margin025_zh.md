# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 16303
family_local_frontier_count = 647
family_delay_fallback_frontier_count = 20495
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 10
best_family_delay_fallback_families = []
best_context_delay_fallback_contexts = []
best_safe_precision_ci_low = 0.7224598312333834
best_accepted_batch_roi_ci_low = 0.8042559559050559
best_local_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
best_fallback_accepted_batch_count = 10
best_fallback_safe_precision_ci_low = 0.7224598312333834
best_fallback_accepted_batch_roi_ci_low = 0.7068633969367273
best_fallback_delay_families = ['random-wave']
best_fallback_delay_contexts = []
best_fallback_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 1579,
    "accepted_batch_rate_too_low": 3043,
    "accepted_batch_roi_below_baseline_margin": 2105,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 23790,
    "expected_trajectory_utility_not_positive": 1579,
    "false_high_priority_on_delay_too_high": 15220,
    "false_safe_rate_union_too_high": 15118,
    "family_holdout_accepted_batch_missing": 6215,
    "family_holdout_accepted_roi_below_threshold": 11524,
    "family_holdout_accepted_roi_not_measurable": 1579,
    "family_holdout_precision_not_measurable": 1579,
    "high_priority_precision_below_threshold_or_no_predictions": 1553,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 3318,
    "knn_ood_audit_missing": 37445,
    "safe_precision_below_threshold_or_no_accepted_batches": 1579,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 32744
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 1579,
    "accepted_batch_rate_too_low": 3043,
    "accepted_batch_roi_below_baseline_margin": 2105,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 23790,
    "expected_trajectory_utility_not_positive": 1579,
    "false_high_priority_on_delay_too_high": 15220,
    "false_safe_rate_union_too_high": 15118,
    "family_holdout_accepted_batch_missing": 6215,
    "family_holdout_accepted_roi_below_threshold": 11524,
    "family_holdout_accepted_roi_not_measurable": 1579,
    "family_holdout_precision_not_measurable": 1579,
    "high_priority_precision_below_threshold_or_no_predictions": 1553,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 3318,
    "safe_precision_below_threshold_or_no_accepted_batches": 1579,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 32744
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
