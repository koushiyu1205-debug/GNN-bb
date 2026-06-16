# GAT Batch Impact Threshold Frontier 报告

日期：2026-06-16

## 结论

本报告展开 Stage 3 checkpoint 的 threshold frontier，用同一套 deployment gate
检查 precision / ROI / safety / coverage。该流程只做离线审计，不运行 BPC、
pricing、RMP 或 certificate。

```text
global_frontier_count = 13837
family_local_frontier_count = 1609
family_delay_fallback_frontier_count = 19320
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 54
best_family_delay_fallback_families = []
best_context_delay_fallback_contexts = []
best_safe_precision_ci_low = 0.9335841332189981
best_accepted_batch_roi_ci_low = 1.227382412845194
best_local_reject_reasons = ['family_holdout_accepted_roi_below_threshold']
best_fallback_accepted_batch_count = 38
best_fallback_safe_precision_ci_low = 0.90818706741616
best_fallback_accepted_batch_roi_ci_low = 1.7721734847088793
best_fallback_delay_families = []
best_fallback_delay_contexts = ['0dab6941e7ad46c4', '109efbbce6a01e0a', '3a96546d8457f0c4', '5751b1799b606ad1', '5e253e60eb577a74', '682ff786fe1517d3', '72cbb81963a67534', '9554cd95954623fb', '9854af45f1e410a6', 'aed425fed6ea2dd3', 'ed559d52013e0db0', 'f097a741fd547926', 'f649a050c04dd416', 'f8293e3b7baa7905', 'fe1efba5e8e6424a']
best_fallback_reject_reasons = ['family_holdout_accepted_roi_below_threshold']
production_ready = false
selector_can_certificate = false
```

## Reject Reason Counts

```json
{
  "checkpoint_reject_reason_counts": {
    "accepted_batch_count_too_low": 645,
    "accepted_batch_rate_too_low": 1168,
    "accepted_batch_roi_below_baseline_margin": 645,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 3254,
    "expected_trajectory_utility_not_positive": 645,
    "false_high_priority_on_delay_too_high": 4561,
    "false_safe_rate_union_too_high": 4561,
    "family_holdout_accepted_batch_missing": 2189,
    "family_holdout_accepted_roi_below_threshold": 9439,
    "family_holdout_accepted_roi_not_measurable": 645,
    "family_holdout_precision_not_measurable": 645,
    "high_priority_precision_below_threshold_or_no_predictions": 101,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 843,
    "knn_ood_audit_missing": 34766,
    "safe_precision_below_threshold_or_no_accepted_batches": 645,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 30985
  },
  "local_reject_reason_counts": {
    "accepted_batch_count_too_low": 645,
    "accepted_batch_rate_too_low": 1168,
    "accepted_batch_roi_below_baseline_margin": 645,
    "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable": 3254,
    "expected_trajectory_utility_not_positive": 645,
    "false_high_priority_on_delay_too_high": 4561,
    "false_safe_rate_union_too_high": 4561,
    "family_holdout_accepted_batch_missing": 2189,
    "family_holdout_accepted_roi_below_threshold": 9439,
    "family_holdout_accepted_roi_not_measurable": 645,
    "family_holdout_precision_not_measurable": 645,
    "high_priority_precision_below_threshold_or_no_predictions": 101,
    "high_priority_precision_ci_low_below_threshold_or_not_measurable": 843,
    "safe_precision_below_threshold_or_no_accepted_batches": 645,
    "safe_precision_ci_low_below_threshold_or_not_measurable": 30985
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
