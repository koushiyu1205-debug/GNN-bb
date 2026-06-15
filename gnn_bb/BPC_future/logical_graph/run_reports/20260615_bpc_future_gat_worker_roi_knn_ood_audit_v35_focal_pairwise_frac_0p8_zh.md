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
train_row_count = 167
validation_row_count = 38
validation_candidate_ready = false
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 验证指标

```json
{
  "decision_reason_counts": {
    "high_priority": 42,
    "neighbor_delay_fraction_too_high": 14,
    "score_below_threshold": 149
  },
  "decision_scope_safety_shell_metrics": {
    "accepted_batch_count": 42,
    "accepted_batch_rate": 0.2048780487804878,
    "accepted_batch_roi": 0.4523809523809524,
    "accepted_batch_roi_positive_count": 19,
    "accepted_reason_counts": {
      "high_priority": 42
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 205,
    "decision_reason_counts": {
      "high_priority": 42,
      "neighbor_delay_fraction_too_high": 14,
      "score_below_threshold": 149
    },
    "delay_count": 163,
    "delay_rate": 0.7951219512195122,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 23,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.15862068965517243,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.15436241610738255,
    "false_safe_union_count": 23,
    "harmful_batch_recall": 0.8413793103448276,
    "knn_unsafe_count": 78,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.4523809523809524,
    "total": 205,
    "unsafe_label_count": 145,
    "unsafe_or_ood_count": 149
  },
  "production_block_reasons": [
    "validation_add_recall_below_min",
    "validation_false_high_priority_rate_above_max",
    "validation_false_safe_rate_above_max",
    "validation_candidate_not_ready"
  ],
  "safe_radius": 2.822849935806684,
  "threshold": 0.5075374841690063,
  "validation_metrics": {
    "accuracy": 0.6578947368421053,
    "add_precision": 0.2857142857142857,
    "add_recall": 0.2,
    "false_high_priority_rate": 0.17857142857142858,
    "false_negative_delay_queue": 8,
    "false_positive_high_priority": 5,
    "predicted_delay_queue": 31,
    "predicted_high_priority": 7,
    "total": 38,
    "true_negative_delay_queue": 23,
    "true_positive_high_priority": 2
  },
  "validation_safety_shell_metrics": {
    "accepted_batch_count": 7,
    "accepted_batch_rate": 0.18421052631578946,
    "accepted_batch_roi": 0.2857142857142857,
    "accepted_batch_roi_positive_count": 2,
    "accepted_reason_counts": {
      "high_priority": 7
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 38,
    "decision_reason_counts": {
      "high_priority": 7,
      "neighbor_delay_fraction_too_high": 4,
      "score_below_threshold": 27
    },
    "delay_count": 31,
    "delay_rate": 0.8157894736842105,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 5,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.17857142857142858,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.15625,
    "false_safe_union_count": 5,
    "harmful_batch_recall": 0.8214285714285714,
    "knn_unsafe_count": 14,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.2857142857142857,
    "total": 38,
    "unsafe_label_count": 28,
    "unsafe_or_ood_count": 32
  }
}
```

## 边界

- 不运行 BPC / pricing / RMP / worker；
- 不产生 certificate，也不影响 official lower bound；
- HIGH_PRIORITY 只是调度优先级；
- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；
- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。
