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
train_row_count = 154
validation_row_count = 53
validation_candidate_ready = false
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 验证指标

```json
{
  "decision_reason_counts": {
    "high_priority": 4,
    "neighbor_delay_fraction_too_high": 132,
    "score_below_threshold": 71
  },
  "decision_scope_safety_shell_metrics": {
    "accepted_batch_count": 4,
    "accepted_batch_rate": 0.01932367149758454,
    "accepted_batch_roi": 0.75,
    "accepted_batch_roi_positive_count": 3,
    "accepted_reason_counts": {
      "high_priority": 4
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 207,
    "decision_reason_counts": {
      "high_priority": 4,
      "neighbor_delay_fraction_too_high": 132,
      "score_below_threshold": 71
    },
    "delay_count": 203,
    "delay_rate": 0.9806763285024155,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 1,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.006802721088435374,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.004901960784313725,
    "false_safe_union_count": 1,
    "harmful_batch_recall": 0.9931972789115646,
    "knn_unsafe_count": 201,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.75,
    "total": 207,
    "unsafe_label_count": 147,
    "unsafe_or_ood_count": 204
  },
  "production_block_reasons": [
    "validation_add_precision_below_min",
    "validation_add_recall_below_min",
    "validation_add_f0p5_below_min",
    "validation_false_high_priority_rate_above_max",
    "validation_false_positive_contexts_above_max",
    "validation_false_safe_rate_above_max",
    "validation_candidate_not_ready"
  ],
  "safe_radius": 1.7584231782502133,
  "threshold": 0.497152179479599,
  "validation_false_safe_rates": {
    "knn_unsafe": 0.0,
    "label_unsafe": 0.027777777777777776,
    "max_observed_false_safe_rate": 0.027777777777777776,
    "max_observed_false_safe_source": "label_unsafe",
    "ood": null,
    "union": 0.019230769230769232
  },
  "validation_metrics": {
    "accuracy": 0.6792452830188679,
    "add_f0p5": 0.19999999999999998,
    "add_precision": 0.5,
    "add_recall": 0.058823529411764705,
    "false_high_priority_rate": 0.027777777777777776,
    "false_negative_delay_queue": 16,
    "false_positive_context_count": 1,
    "false_positive_contexts": [
      "3d1bd8618099b573"
    ],
    "false_positive_high_priority": 1,
    "predicted_delay_queue": 51,
    "predicted_high_priority": 2,
    "total": 53,
    "true_negative_delay_queue": 35,
    "true_positive_high_priority": 1
  },
  "validation_safety_shell_metrics": {
    "accepted_batch_count": 2,
    "accepted_batch_rate": 0.03773584905660377,
    "accepted_batch_roi": 0.5,
    "accepted_batch_roi_positive_count": 1,
    "accepted_reason_counts": {
      "high_priority": 2
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 53,
    "decision_reason_counts": {
      "high_priority": 2,
      "neighbor_delay_fraction_too_high": 35,
      "score_below_threshold": 16
    },
    "delay_count": 51,
    "delay_rate": 0.9622641509433962,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 1,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.027777777777777776,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.019230769230769232,
    "false_safe_union_count": 1,
    "harmful_batch_recall": 0.9722222222222222,
    "knn_unsafe_count": 49,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.5,
    "total": 53,
    "unsafe_label_count": 36,
    "unsafe_or_ood_count": 52
  }
}
```

## 边界

- 不运行 BPC / pricing / RMP / worker；
- 不产生 certificate，也不影响 official lower bound；
- HIGH_PRIORITY 只是调度优先级；
- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；
- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。
