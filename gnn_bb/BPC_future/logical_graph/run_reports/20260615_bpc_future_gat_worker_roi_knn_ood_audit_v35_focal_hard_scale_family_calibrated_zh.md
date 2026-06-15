# GAT Worker ROI kNN/OOD Audit 报告

日期：2026-06-15

## 目的

本报告只做离线审计：GAT 负责 trajectory ROI 表达，kNN/OOD 负责安全壳。
通过者只能进入 HIGH_PRIORITY；未通过者进入 DELAY_QUEUE，不能永久丢弃。

## 机器字段

```text
gat_worker_roi_knn_ood_audit = current
diagnostic_only = true
runs_bpc_or_pricing = false
target_label = paired_worker_ab_trajectory_roi
train_row_count = 161
validation_row_count = 44
validation_candidate_ready = false
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 验证指标

```json
{
  "decision_reason_counts": {
    "high_priority": 8,
    "neighbor_delay_fraction_too_high": 141,
    "score_below_threshold": 56
  },
  "decision_scope_safety_shell_metrics": {
    "accepted_batch_count": 8,
    "accepted_batch_rate": 0.03902439024390244,
    "accepted_batch_roi": 1.0,
    "accepted_batch_roi_positive_count": 8,
    "accepted_reason_counts": {
      "high_priority": 8
    },
    "coverage": 0.975609756097561,
    "coverage_non_ood_count": 200,
    "decision_reason_counts": {
      "high_priority": 8,
      "neighbor_delay_fraction_too_high": 141,
      "score_below_threshold": 56
    },
    "delay_count": 197,
    "delay_rate": 0.9609756097560975,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 0,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "harmful_batch_recall": 1.0,
    "knn_unsafe_count": 197,
    "ood_count": 5,
    "ood_rate": 0.024390243902439025,
    "safe_precision": 1.0,
    "total": 205,
    "unsafe_label_count": 145,
    "unsafe_or_ood_count": 197
  },
  "production_block_reasons": [
    "validation_high_priority_below_min",
    "validation_add_precision_below_min",
    "validation_add_recall_below_min",
    "validation_add_f0p5_below_min",
    "validation_candidate_not_ready"
  ],
  "safe_radius": 0.6781460062223517,
  "threshold": 0.5129124522209167,
  "validation_false_safe_rates": {
    "knn_unsafe": 0.0,
    "label_unsafe": 0.0,
    "max_observed_false_safe_rate": 0.0,
    "max_observed_false_safe_source": "ood",
    "ood": 0.0,
    "union": 0.0
  },
  "validation_metrics": {
    "accuracy": 0.6363636363636364,
    "add_f0p5": null,
    "add_precision": null,
    "add_recall": 0.0,
    "false_high_priority_rate": 0.0,
    "false_negative_delay_queue": 16,
    "false_positive_context_count": 0,
    "false_positive_contexts": [],
    "false_positive_high_priority": 0,
    "predicted_delay_queue": 44,
    "predicted_high_priority": 0,
    "total": 44,
    "true_negative_delay_queue": 28,
    "true_positive_high_priority": 0
  },
  "validation_safety_shell_metrics": {
    "accepted_batch_count": 0,
    "accepted_batch_rate": 0.0,
    "accepted_batch_roi": null,
    "accepted_batch_roi_positive_count": 0,
    "accepted_reason_counts": {},
    "coverage": 0.9545454545454546,
    "coverage_non_ood_count": 42,
    "decision_reason_counts": {
      "neighbor_delay_fraction_too_high": 30,
      "score_below_threshold": 14
    },
    "delay_count": 44,
    "delay_rate": 1.0,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 0,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "harmful_batch_recall": 1.0,
    "knn_unsafe_count": 44,
    "ood_count": 2,
    "ood_rate": 0.045454545454545456,
    "safe_precision": null,
    "total": 44,
    "unsafe_label_count": 28,
    "unsafe_or_ood_count": 44
  }
}
```

## 边界

- 不运行 BPC / pricing / RMP / worker；
- 不产生 certificate，也不影响 official lower bound；
- HIGH_PRIORITY 只是调度优先级；
- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；
- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。
