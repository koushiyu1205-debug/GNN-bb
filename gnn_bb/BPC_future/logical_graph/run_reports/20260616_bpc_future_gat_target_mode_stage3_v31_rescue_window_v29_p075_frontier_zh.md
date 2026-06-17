# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 16303
family_local_frontier_count = 0
family_delay_fallback_frontier_count = 12224
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 62
candidate_admission_score_mode = risk_adjusted_rescue_window
candidate_delay_score_penalty = 0.75
candidate_rescue_raw_score_threshold = 0.3
candidate_rescue_delay_risk_threshold = 0.75
candidate_rescue_delay_score_penalty = 0.25
candidate_delay_gate_enabled = True
candidate_delay_risk_threshold = 0.5
candidate_delay_gate_blocked_count = 109
candidate_risk_adjusted_suppressed_count = 0
candidate_rescue_window_eligible_count = 953
candidate_rescue_window_promoted_count = 435
best_family_delay_fallback_families = ['greedy-anchor']
best_context_delay_fallback_contexts = []
best_safe_precision_ci_low = 0.9416539087749994
best_accepted_batch_roi_ci_low = 2.703277064310553
best_local_reject_reasons = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high']
best_fallback_accepted_batch_count = 62
best_fallback_safe_precision_ci_low = 0.9416539087749994
best_fallback_accepted_batch_roi_ci_low = 2.703277064310553
best_fallback_delay_families = ['greedy-anchor']
best_fallback_delay_contexts = []
best_fallback_reject_reasons = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high']
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 1745,
    "accepted_batch_rate_too_low": 2113,
    "accepted_batch_roi_below_baseline_margin": 1745,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 2481,
    "expected_trajectory_utility_not_positive": 1745,
    "false_high_priority_on_delay_too_high": 26980,
    "false_safe_rate_union_too_high": 26147,
    "family_accepted_high_roi_count_below_threshold": 12932,
    "family_high_roi_capture_rate_below_threshold": 12932,
    "family_holdout_accepted_batch_missing": 7654,
    "family_holdout_accepted_roi_below_threshold": 9389,
    "family_holdout_accepted_roi_not_measurable": 1745,
    "family_holdout_precision_not_measurable": 1745,
    "high_priority_precision_below_threshold_or_no_predictions": 833,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 5275,
    "knn_ood_audit_missing": 28527,
    "safe_precision_below_threshold_or_no_accepted_batches": 1745,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 19922
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 1745,
    "accepted_batch_rate_too_low": 2113,
    "accepted_batch_roi_below_baseline_margin": 1745,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 2481,
    "expected_trajectory_utility_not_positive": 1745,
    "false_high_priority_on_delay_too_high": 26980,
    "false_safe_rate_union_too_high": 26147,
    "family_accepted_high_roi_count_below_threshold": 12932,
    "family_high_roi_capture_rate_below_threshold": 12932,
    "family_holdout_accepted_batch_missing": 7654,
    "family_holdout_accepted_roi_below_threshold": 9389,
    "family_holdout_accepted_roi_not_measurable": 1745,
    "family_holdout_precision_not_measurable": 1745,
    "high_priority_precision_below_threshold_or_no_predictions": 833,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 5275,
    "safe_precision_below_threshold_or_no_accepted_batches": 1745,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 19922
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
