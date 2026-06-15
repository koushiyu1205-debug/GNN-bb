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
train_row_count = 120
validation_row_count = 36
validation_candidate_ready = true
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 验证指标

```json
{
  "decision_reason_counts": {
    "high_priority": 29,
    "neighbor_delay_fraction_too_high": 93,
    "score_below_threshold": 34
  },
  "production_block_reasons": [],
  "safe_radius": 1.513672772544315,
  "threshold": 0.5340699553489685,
  "validation_metrics": {
    "accuracy": 0.6666666666666666,
    "add_precision": 0.5555555555555556,
    "add_recall": 0.38461538461538464,
    "false_high_priority_rate": 0.17391304347826086,
    "false_negative_delay_queue": 8,
    "false_positive_high_priority": 4,
    "predicted_delay_queue": 27,
    "predicted_high_priority": 9,
    "total": 36,
    "true_negative_delay_queue": 19,
    "true_positive_high_priority": 5
  }
}
```

## 边界

- 不运行 BPC / pricing / RMP / worker；
- 不产生 certificate，也不影响 official lower bound；
- HIGH_PRIORITY 只是调度优先级；
- DELAY_QUEUE 只是延迟队列，不能永久拒绝 true-RC negative；
- 生产化前仍需 5/10 no-regression 和 20-task ROI A/B。
