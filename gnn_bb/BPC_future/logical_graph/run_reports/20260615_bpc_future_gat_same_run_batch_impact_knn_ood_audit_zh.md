# GAT Same-Run Batch Impact kNN/OOD Audit 报告

日期：2026-06-15

## 目的

审计 same-run batch-impact GAT checkpoint 的离线 holdout 表现，并用
kNN/OOD safety shell 检查 HIGH_PRIORITY 是否安全。该流程不运行求解器，
不接 production driver，不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_same_run_batch_impact_knn_ood = current
status = gat_same_run_batch_impact_knn_ood_audited
train_row_count = 53
validation_row_count = 15
train_label_counts = {'delay_queue': 8, 'high_priority': 45}
validation_label_counts = {'delay_queue': 4, 'high_priority': 11}
threshold = 0.8481688499450684
safe_radius = 4.075623358319574
validation_candidate_ready = true
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "below_threshold_delay_queue": 8,
    "high_priority": 6,
    "knn_delay_fraction_delay_queue": 1
  },
  "threshold_info": {
    "threshold": 0.8481688499450684,
    "train_metrics": {
      "accuracy": 0.7358490566037735,
      "actual_delay_queue": 8,
      "actual_high_priority": 45,
      "fn_delayed_high_priority": 14,
      "fp_high_priority_on_delay": 0,
      "high_priority_precision": 1.0,
      "high_priority_recall": 0.6888888888888889,
      "negative_recall_delay_queue": 1.0,
      "predicted_high_priority": 31,
      "tn_delay_queue": 8,
      "total": 53,
      "tp_high_priority": 31
    },
    "train_predicted_high_priority": 31
  },
  "validation_metrics": {
    "accuracy": 0.6666666666666666,
    "actual_delay_queue": 4,
    "actual_high_priority": 11,
    "fn_delayed_high_priority": 5,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.5454545454545454,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 6,
    "tn_delay_queue": 4,
    "total": 15,
    "tp_high_priority": 6
  }
}
```

## 结论

- `validation_candidate_ready=false` 时，不允许进入 audit-only worker；
- delay queue 标签代表 true-RC negative 需要延迟，不允许永久丢弃；
- 该审计只验证表示/安全壳，不证明 5/10 不退化，也不证明 20 规模收益。
