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
    "high_priority": 56,
    "score_below_threshold": 149
  },
  "decision_scope_safety_shell_metrics": {
    "accepted_batch_count": 56,
    "accepted_batch_rate": 0.2731707317073171,
    "accepted_batch_roi": 0.39285714285714285,
    "accepted_batch_roi_positive_count": 22,
    "accepted_reason_counts": {
      "high_priority": 56
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 205,
    "decision_reason_counts": {
      "high_priority": 56,
      "score_below_threshold": 149
    },
    "delay_count": 149,
    "delay_rate": 0.7268292682926829,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 34,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": null,
    "false_safe_rate_label_unsafe": 0.23448275862068965,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.23448275862068965,
    "false_safe_union_count": 34,
    "harmful_batch_recall": 0.7655172413793103,
    "knn_unsafe_count": 0,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.39285714285714285,
    "total": 205,
    "unsafe_label_count": 145,
    "unsafe_or_ood_count": 145
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
    "accuracy": 0.7105263157894737,
    "add_precision": 0.45454545454545453,
    "add_recall": 0.5,
    "false_high_priority_rate": 0.21428571428571427,
    "false_negative_delay_queue": 5,
    "false_positive_high_priority": 6,
    "predicted_delay_queue": 27,
    "predicted_high_priority": 11,
    "total": 38,
    "true_negative_delay_queue": 22,
    "true_positive_high_priority": 5
  },
  "validation_safety_shell_metrics": {
    "accepted_batch_count": 11,
    "accepted_batch_rate": 0.2894736842105263,
    "accepted_batch_roi": 0.45454545454545453,
    "accepted_batch_roi_positive_count": 5,
    "accepted_reason_counts": {
      "high_priority": 11
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 38,
    "decision_reason_counts": {
      "high_priority": 11,
      "score_below_threshold": 27
    },
    "delay_count": 27,
    "delay_rate": 0.7105263157894737,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 6,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": null,
    "false_safe_rate_label_unsafe": 0.21428571428571427,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.21428571428571427,
    "false_safe_union_count": 6,
    "harmful_batch_recall": 0.7857142857142857,
    "knn_unsafe_count": 0,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 0.45454545454545453,
    "total": 38,
    "unsafe_label_count": 28,
    "unsafe_or_ood_count": 28
  }
}
```

## 边界

- 不运行 BPC / pricing / RMP / worker；
- 不产生 certificate，也不影响 official lower bound；
- HIGH_PRIORITY 只是调度优先级；
- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；
- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。
