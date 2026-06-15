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
    "high_priority": 44,
    "neighbor_delay_fraction_too_high": 105,
    "score_below_threshold": 56
  },
  "decision_scope_safety_shell_metrics": {
    "accepted_batch_count": 44,
    "accepted_batch_rate": 0.2146341463414634,
    "accepted_batch_roi": 0.75,
    "accepted_batch_roi_positive_count": 33,
    "accepted_reason_counts": {
      "high_priority": 44
    },
    "coverage": 0.9853658536585366,
    "coverage_non_ood_count": 202,
    "decision_reason_counts": {
      "high_priority": 44,
      "neighbor_delay_fraction_too_high": 105,
      "score_below_threshold": 56
    },
    "delay_count": 161,
    "delay_rate": 0.7853658536585366,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 11,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.07586206896551724,
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.06470588235294118,
    "false_safe_union_count": 11,
    "harmful_batch_recall": 0.9241379310344827,
    "knn_unsafe_count": 157,
    "ood_count": 3,
    "ood_rate": 0.014634146341463415,
    "safe_precision": 0.75,
    "total": 205,
    "unsafe_label_count": 145,
    "unsafe_or_ood_count": 170
  },
  "production_block_reasons": [
    "validation_add_recall_below_min",
    "validation_false_high_priority_rate_above_max",
    "validation_false_safe_rate_above_max",
    "validation_candidate_not_ready"
  ],
  "safe_radius": 0.6781460062223517,
  "threshold": 0.5129124522209167,
  "validation_metrics": {
    "accuracy": 0.6818181818181818,
    "add_precision": 0.6666666666666666,
    "add_recall": 0.25,
    "false_high_priority_rate": 0.07142857142857142,
    "false_negative_delay_queue": 12,
    "false_positive_high_priority": 2,
    "predicted_delay_queue": 38,
    "predicted_high_priority": 6,
    "total": 44,
    "true_negative_delay_queue": 26,
    "true_positive_high_priority": 4
  },
  "validation_safety_shell_metrics": {
    "accepted_batch_count": 6,
    "accepted_batch_rate": 0.13636363636363635,
    "accepted_batch_roi": 0.6666666666666666,
    "accepted_batch_roi_positive_count": 4,
    "accepted_reason_counts": {
      "high_priority": 6
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 44,
    "decision_reason_counts": {
      "high_priority": 6,
      "neighbor_delay_fraction_too_high": 24,
      "score_below_threshold": 14
    },
    "delay_count": 38,
    "delay_rate": 0.8636363636363636,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 2,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.07142857142857142,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.05,
    "false_safe_union_count": 2,
    "harmful_batch_recall": 0.9285714285714286,
    "knn_unsafe_count": 37,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.6666666666666666,
    "total": 44,
    "unsafe_label_count": 28,
    "unsafe_or_ood_count": 40
  }
}
```

## 边界

- 不运行 BPC / pricing / RMP / worker；
- 不产生 certificate，也不影响 official lower bound；
- HIGH_PRIORITY 只是调度优先级；
- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；
- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。
