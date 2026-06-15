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
train_row_count = 144
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
    "high_priority": 19,
    "neighbor_delay_fraction_too_high": 25,
    "score_below_threshold": 9
  },
  "production_block_reasons": [
    "validation_false_high_priority_rate_above_max",
    "validation_candidate_not_ready"
  ],
  "safe_radius": 1.9031938646868303,
  "threshold": 0.6957716345787048,
  "validation_metrics": {
    "accuracy": 0.5849056603773585,
    "add_precision": 0.3684210526315789,
    "add_recall": 0.4117647058823529,
    "false_high_priority_rate": 0.3333333333333333,
    "false_negative_delay_queue": 10,
    "false_positive_high_priority": 12,
    "predicted_delay_queue": 34,
    "predicted_high_priority": 19,
    "total": 53,
    "true_negative_delay_queue": 24,
    "true_positive_high_priority": 7
  }
}
```

## 边界

- 不运行 BPC / pricing / RMP / worker；
- 不产生 certificate，也不影响 official lower bound；
- HIGH_PRIORITY 只是调度优先级；
- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；
- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。
