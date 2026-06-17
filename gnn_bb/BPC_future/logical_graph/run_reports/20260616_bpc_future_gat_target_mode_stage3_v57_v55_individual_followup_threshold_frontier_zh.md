# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 17125
family_local_frontier_count = 0
family_delay_fallback_frontier_count = 0
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = model_ranking_false_delay_blocker
best_accepted_batch_count = 3
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.0
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
candidate_delay_gate_enabled = True
candidate_delay_risk_threshold = 0.5
evaluated_candidate_count = 1236
candidate_score_threshold_blocked_count = 1213
candidate_delay_gate_blocked_count = 14
candidate_risk_adjusted_suppressed_count = 1129
candidate_rescue_window_eligible_count = 0
candidate_rescue_window_promoted_count = 0
best_family_delay_fallback_families = []
best_context_delay_fallback_contexts = []
best_safe_precision_ci_low = 0.4384939195509822
best_accepted_batch_roi_ci_low = 23.902832583252618
best_local_reject_reasons = ['high_priority_precision_below_threshold_or_no_predictions', 'high_priority_precision_ci_low_below_threshold_or_not_measurable', 'safe_precision_ci_low_below_threshold_or_not_measurable', 'false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high', 'family_holdout_accepted_batch_missing']
best_fallback_accepted_batch_count = None
best_fallback_safe_precision_ci_low = None
best_fallback_accepted_batch_roi_ci_low = None
best_fallback_delay_families = None
best_fallback_delay_contexts = None
best_fallback_reject_reasons = None
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 2533,
    "accepted_batch_rate_too_low": 3028,
    "accepted_batch_roi_below_baseline_margin": 2533,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 2901,
    "candidate_threshold_zero_disables_candidate_head_filter": 125,
    "expected_trajectory_utility_not_positive": 2533,
    "false_high_priority_on_delay_too_high": 16000,
    "false_safe_rate_union_too_high": 16000,
    "family_holdout_accepted_batch_missing": 17125,
    "family_holdout_accepted_roi_not_measurable": 2533,
    "family_holdout_precision_not_measurable": 2533,
    "high_priority_precision_below_threshold_or_no_predictions": 17125,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 17125,
    "knn_ood_audit_missing": 17125,
    "safe_precision_below_threshold_or_no_accepted_batches": 2533,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 17125
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 2533,
    "accepted_batch_rate_too_low": 3028,
    "accepted_batch_roi_below_baseline_margin": 2533,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 2901,
    "candidate_threshold_zero_disables_candidate_head_filter": 125,
    "expected_trajectory_utility_not_positive": 2533,
    "false_high_priority_on_delay_too_high": 16000,
    "false_safe_rate_union_too_high": 16000,
    "family_holdout_accepted_batch_missing": 17125,
    "family_holdout_accepted_roi_not_measurable": 2533,
    "family_holdout_precision_not_measurable": 2533,
    "high_priority_precision_below_threshold_or_no_predictions": 17125,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 17125,
    "safe_precision_below_threshold_or_no_accepted_batches": 2533,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 17125
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
