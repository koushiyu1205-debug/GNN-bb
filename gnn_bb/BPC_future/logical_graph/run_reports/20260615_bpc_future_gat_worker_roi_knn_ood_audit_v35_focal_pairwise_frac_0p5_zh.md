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
    "high_priority": 14,
    "neighbor_delay_fraction_too_high": 42,
    "score_below_threshold": 149
  },
  "decision_scope_safety_shell_metrics": {
    "accepted_batch_count": 14,
    "accepted_batch_rate": 0.06829268292682927,
    "accepted_batch_roi": 0.7142857142857143,
    "accepted_batch_roi_positive_count": 10,
    "accepted_reason_counts": {
      "high_priority": 14
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 205,
    "decision_reason_counts": {
      "high_priority": 14,
      "neighbor_delay_fraction_too_high": 42,
      "score_below_threshold": 149
    },
    "delay_count": 191,
    "delay_rate": 0.9317073170731708,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 4,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.027586206896551724,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.022598870056497175,
    "false_safe_union_count": 4,
    "harmful_batch_recall": 0.9724137931034482,
    "knn_unsafe_count": 165,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.7142857142857143,
    "total": 205,
    "unsafe_label_count": 145,
    "unsafe_or_ood_count": 177
  },
  "production_block_reasons": [
    "validation_add_recall_below_min",
    "validation_false_safe_rate_above_max",
    "validation_candidate_not_ready"
  ],
  "safe_radius": 2.822849935806684,
  "threshold": 0.5075374841690063,
  "validation_metrics": {
    "accuracy": 0.7105263157894737,
    "add_precision": 0.0,
    "add_recall": 0.0,
    "false_high_priority_rate": 0.03571428571428571,
    "false_negative_delay_queue": 10,
    "false_positive_high_priority": 1,
    "predicted_delay_queue": 37,
    "predicted_high_priority": 1,
    "total": 38,
    "true_negative_delay_queue": 27,
    "true_positive_high_priority": 0
  },
  "validation_safety_shell_metrics": {
    "accepted_batch_count": 1,
    "accepted_batch_rate": 0.02631578947368421,
    "accepted_batch_roi": 0.0,
    "accepted_batch_roi_positive_count": 0,
    "accepted_reason_counts": {
      "high_priority": 1
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 38,
    "decision_reason_counts": {
      "high_priority": 1,
      "neighbor_delay_fraction_too_high": 10,
      "score_below_threshold": 27
    },
    "delay_count": 37,
    "delay_rate": 0.9736842105263158,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 1,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.03571428571428571,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.02631578947368421,
    "false_safe_union_count": 1,
    "harmful_batch_recall": 0.9642857142857143,
    "knn_unsafe_count": 32,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.0,
    "total": 38,
    "unsafe_label_count": 28,
    "unsafe_or_ood_count": 38
  }
}
```

## 边界

- 不运行 BPC / pricing / RMP / worker；
- 不产生 certificate，也不影响 official lower bound；
- HIGH_PRIORITY 只是调度优先级；
- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；
- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。
