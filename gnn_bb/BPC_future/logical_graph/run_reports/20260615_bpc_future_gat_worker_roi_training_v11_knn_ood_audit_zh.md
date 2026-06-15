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
train_row_count = 37
validation_row_count = 12
train_label_counts = {'delay_queue': 20, 'high_priority': 17}
validation_label_counts = {'delay_queue': 11, 'high_priority': 1}
threshold = 0.5713773965835571
safe_radius = 1.4085705558540937
decision_scope = all
decision_record_count = 49
decision_split_counts = {'train': 37, 'validation': 12}
validation_candidate_ready = false
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "below_threshold_delay_queue": 43,
    "high_priority": 1,
    "knn_delay_fraction_delay_queue": 5
  },
  "decision_scope_metrics": {
    "accuracy": 0.6530612244897959,
    "actual_delay_queue": 31,
    "actual_high_priority": 18,
    "fn_delayed_high_priority": 17,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.05555555555555555,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 1,
    "tn_delay_queue": 31,
    "total": 49,
    "tp_high_priority": 1
  },
  "decision_split_counts": {
    "train": 37,
    "validation": 12
  },
  "threshold_info": {
    "threshold": 0.5713773965835571,
    "train_metrics": {
      "accuracy": 0.6486486486486487,
      "actual_delay_queue": 20,
      "actual_high_priority": 17,
      "fn_delayed_high_priority": 13,
      "fp_high_priority_on_delay": 0,
      "high_priority_precision": 1.0,
      "high_priority_recall": 0.23529411764705882,
      "negative_recall_delay_queue": 1.0,
      "predicted_high_priority": 4,
      "tn_delay_queue": 20,
      "total": 37,
      "tp_high_priority": 4
    },
    "train_predicted_high_priority": 4
  },
  "validation_metrics": {
    "accuracy": 0.9166666666666666,
    "actual_delay_queue": 11,
    "actual_high_priority": 1,
    "fn_delayed_high_priority": 1,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": null,
    "high_priority_recall": 0.0,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 0,
    "tn_delay_queue": 11,
    "total": 12,
    "tp_high_priority": 0
  }
}
```

## 结论

- `validation_candidate_ready=false` 时，不允许进入 audit-only worker；
- `decision_scope=all` 只用于扩充采样候选，不等同于 holdout validation 通过；
- delay queue 标签代表 true-RC negative 需要延迟，不允许永久丢弃；
- 该审计只验证表示/安全壳，不证明 5/10 不退化，也不证明 20 规模收益。
