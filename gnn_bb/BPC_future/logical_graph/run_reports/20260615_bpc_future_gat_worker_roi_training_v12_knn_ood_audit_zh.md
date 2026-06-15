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
train_row_count = 38
validation_row_count = 12
train_label_counts = {'delay_queue': 21, 'high_priority': 17}
validation_label_counts = {'delay_queue': 11, 'high_priority': 1}
threshold = 0.5701112151145935
safe_radius = 1.569250721150529
decision_scope = all
decision_record_count = 50
decision_split_counts = {'train': 38, 'validation': 12}
validation_candidate_ready = false
validation_safety_ready = false
validation_safety_checks = {'no_false_high_priority': False, 'min_high_priority_met': True, 'delay_recall_met': True}
production_block_reasons = ['validation_false_high_priority_on_delay', 'validation_candidate_not_ready']
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "below_threshold_delay_queue": 46,
    "high_priority": 3,
    "knn_delay_fraction_delay_queue": 1
  },
  "decision_scope_metrics": {
    "accuracy": 0.66,
    "actual_delay_queue": 32,
    "actual_high_priority": 18,
    "fn_delayed_high_priority": 16,
    "fp_high_priority_on_delay": 1,
    "high_priority_precision": 0.6666666666666666,
    "high_priority_recall": 0.1111111111111111,
    "negative_recall_delay_queue": 0.96875,
    "predicted_high_priority": 3,
    "tn_delay_queue": 31,
    "total": 50,
    "tp_high_priority": 2
  },
  "decision_split_counts": {
    "train": 38,
    "validation": 12
  },
  "production_block_reasons": [
    "validation_false_high_priority_on_delay",
    "validation_candidate_not_ready"
  ],
  "threshold_info": {
    "threshold": 0.5701112151145935,
    "train_metrics": {
      "accuracy": 0.631578947368421,
      "actual_delay_queue": 21,
      "actual_high_priority": 17,
      "fn_delayed_high_priority": 14,
      "fp_high_priority_on_delay": 0,
      "high_priority_precision": 1.0,
      "high_priority_recall": 0.17647058823529413,
      "negative_recall_delay_queue": 1.0,
      "predicted_high_priority": 3,
      "tn_delay_queue": 21,
      "total": 38,
      "tp_high_priority": 3
    },
    "train_predicted_high_priority": 3
  },
  "validation_metrics": {
    "accuracy": 0.8333333333333334,
    "actual_delay_queue": 11,
    "actual_high_priority": 1,
    "fn_delayed_high_priority": 1,
    "fp_high_priority_on_delay": 1,
    "high_priority_precision": 0.0,
    "high_priority_recall": 0.0,
    "negative_recall_delay_queue": 0.9090909090909091,
    "predicted_high_priority": 1,
    "tn_delay_queue": 10,
    "total": 12,
    "tp_high_priority": 0
  },
  "validation_safety_checks": {
    "delay_recall_met": true,
    "min_high_priority_met": true,
    "no_false_high_priority": false
  }
}
```

## 结论

- `validation_candidate_ready=false` 时，不允许进入 audit-only worker；
- `decision_scope=all` 只用于扩充采样候选，不等同于 holdout validation 通过；
- delay queue 标签代表 true-RC negative 需要延迟，不允许永久丢弃；
- 该审计只验证表示/安全壳，不证明 5/10 不退化，也不证明 20 规模收益。
