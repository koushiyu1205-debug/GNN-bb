# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 16303
family_local_frontier_count = 41
family_delay_fallback_frontier_count = 10253
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 25
candidate_admission_score_mode = risk_adjusted_rescue_window
candidate_delay_score_penalty = 1.0
candidate_rescue_raw_score_threshold = 0.3
candidate_rescue_delay_risk_threshold = 0.75
candidate_rescue_delay_score_penalty = 0.25
candidate_delay_gate_enabled = True
candidate_delay_risk_threshold = 0.5
candidate_delay_gate_blocked_count = 0
candidate_risk_adjusted_suppressed_count = 692
candidate_rescue_window_eligible_count = 1001
candidate_rescue_window_promoted_count = 469
best_family_delay_fallback_families = []
best_context_delay_fallback_contexts = ['0dab6941e7ad46c4', '5e253e60eb577a74', '9854af45f1e410a6']
best_safe_precision_ci_low = 0.8668035060468212
best_accepted_batch_roi_ci_low = 3.9177806231494863
best_local_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
best_fallback_accepted_batch_count = 25
best_fallback_safe_precision_ci_low = 0.8668035060468212
best_fallback_accepted_batch_roi_ci_low = 3.9177806231494863
best_fallback_delay_families = []
best_fallback_delay_contexts = ['0dab6941e7ad46c4', '5e253e60eb577a74', '9854af45f1e410a6']
best_fallback_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 3227,
    "accepted_batch_rate_too_low": 4784,
    "accepted_batch_roi_below_baseline_margin": 3227,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 5368,
    "expected_trajectory_utility_not_positive": 3227,
    "false_high_priority_on_delay_too_high": 16706,
    "false_safe_rate_union_too_high": 16706,
    "family_accepted_high_roi_count_below_threshold": 19988,
    "family_high_roi_capture_rate_below_threshold": 19992,
    "family_holdout_accepted_batch_missing": 10750,
    "family_holdout_accepted_roi_below_threshold": 7691,
    "family_holdout_accepted_roi_not_measurable": 3227,
    "family_holdout_precision_not_measurable": 3227,
    "high_priority_precision_below_threshold_or_no_predictions": 833,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 5193,
    "knn_ood_audit_missing": 26597,
    "safe_precision_below_threshold_or_no_accepted_batches": 3227,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 20988
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 3227,
    "accepted_batch_rate_too_low": 4784,
    "accepted_batch_roi_below_baseline_margin": 3227,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 5368,
    "expected_trajectory_utility_not_positive": 3227,
    "false_high_priority_on_delay_too_high": 16706,
    "false_safe_rate_union_too_high": 16706,
    "family_accepted_high_roi_count_below_threshold": 19988,
    "family_high_roi_capture_rate_below_threshold": 19992,
    "family_holdout_accepted_batch_missing": 10750,
    "family_holdout_accepted_roi_below_threshold": 7691,
    "family_holdout_accepted_roi_not_measurable": 3227,
    "family_holdout_precision_not_measurable": 3227,
    "high_priority_precision_below_threshold_or_no_predictions": 833,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 5193,
    "safe_precision_below_threshold_or_no_accepted_batches": 3227,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 20988
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
