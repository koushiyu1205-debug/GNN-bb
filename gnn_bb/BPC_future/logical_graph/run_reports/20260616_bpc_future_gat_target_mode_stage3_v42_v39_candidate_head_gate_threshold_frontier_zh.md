# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 16303
family_local_frontier_count = 0
family_delay_fallback_frontier_count = 19896
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = model_ranking_false_delay_blocker
best_accepted_batch_count = 46
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.0
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
candidate_delay_gate_enabled = True
candidate_delay_risk_threshold = 0.5
evaluated_candidate_count = 1066
candidate_score_threshold_blocked_count = 126
candidate_delay_gate_blocked_count = 203
candidate_risk_adjusted_suppressed_count = 44
candidate_rescue_window_eligible_count = 0
candidate_rescue_window_promoted_count = 0
best_family_delay_fallback_families = ['greedy-anchor']
best_context_delay_fallback_contexts = []
best_safe_precision_ci_low = 0.9229238226702192
best_accepted_batch_roi_ci_low = 3.3215176548675847
best_local_reject_reasons = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high']
best_fallback_accepted_batch_count = 46
best_fallback_safe_precision_ci_low = 0.9229238226702192
best_fallback_accepted_batch_roi_ci_low = 3.3215176548675847
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
    "accepted_batch_count_too_low": 1730,
    "accepted_batch_rate_too_low": 2464,
    "accepted_batch_roi_below_baseline_margin": 1730,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 3322,
    "candidate_threshold_zero_disables_candidate_head_filter": 269,
    "expected_trajectory_utility_not_positive": 1730,
    "false_high_priority_on_delay_too_high": 34890,
    "false_safe_rate_union_too_high": 34890,
    "family_holdout_accepted_batch_missing": 10363,
    "family_holdout_accepted_roi_below_threshold": 14172,
    "family_holdout_accepted_roi_not_measurable": 1730,
    "family_holdout_precision_not_measurable": 1730,
    "high_priority_precision_below_threshold_or_no_predictions": 5021,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 21639,
    "knn_ood_audit_missing": 36199,
    "safe_precision_below_threshold_or_no_accepted_batches": 1730,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 26772
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 1730,
    "accepted_batch_rate_too_low": 2464,
    "accepted_batch_roi_below_baseline_margin": 1730,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 3322,
    "candidate_threshold_zero_disables_candidate_head_filter": 269,
    "expected_trajectory_utility_not_positive": 1730,
    "false_high_priority_on_delay_too_high": 34890,
    "false_safe_rate_union_too_high": 34890,
    "family_holdout_accepted_batch_missing": 10363,
    "family_holdout_accepted_roi_below_threshold": 14172,
    "family_holdout_accepted_roi_not_measurable": 1730,
    "family_holdout_precision_not_measurable": 1730,
    "high_priority_precision_below_threshold_or_no_predictions": 5021,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 21639,
    "safe_precision_below_threshold_or_no_accepted_batches": 1730,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 26772
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
