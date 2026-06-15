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
train_row_count = 209
validation_row_count = 85
train_label_counts = {'delay_queue': 47, 'high_priority': 162}
validation_label_counts = {'delay_queue': 16, 'high_priority': 69}
threshold = 0.8810842633247375
safe_radius = 2.1235094882395624
threshold_grouping = scale
decision_scope = all
decision_record_count = 294
decision_split_counts = {'train': 209, 'validation': 85}
decision_threshold_group_counts = {'010': 8, '020': 118, '030': 76, '050': 89, 'global': 3}
decision_threshold_scope_counts = {'global': 3, 'scale': 291}
validation_candidate_ready = true
validation_safety_ready = true
validation_safety_checks = {'no_false_high_priority': True, 'min_high_priority_met': True, 'delay_recall_met': True}
production_block_reasons = []
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "below_threshold_delay_queue": 125,
    "high_priority": 144,
    "knn_delay_fraction_delay_queue": 25
  },
  "decision_scope_metrics": {
    "accuracy": 0.7040816326530612,
    "actual_delay_queue": 63,
    "actual_high_priority": 231,
    "fn_delayed_high_priority": 87,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.6233766233766234,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 144,
    "tn_delay_queue": 63,
    "total": 294,
    "tp_high_priority": 144
  },
  "decision_split_counts": {
    "train": 209,
    "validation": 85
  },
  "decision_threshold_group_counts": {
    "010": 8,
    "020": 118,
    "030": 76,
    "050": 89,
    "global": 3
  },
  "decision_threshold_scope_counts": {
    "global": 3,
    "scale": 291
  },
  "production_block_reasons": [],
  "threshold_group_info": {
    "global": {
      "group": "global",
      "label_counts": {
        "delay_queue": 47,
        "high_priority": 162
      },
      "safe_radius": 2.1235094882395624,
      "scope": "global",
      "threshold": 0.8810842633247375,
      "threshold_info": {
        "threshold": 0.8810842633247375,
        "train_metrics": {
          "accuracy": 0.7416267942583732,
          "actual_delay_queue": 47,
          "actual_high_priority": 162,
          "fn_delayed_high_priority": 54,
          "fp_high_priority_on_delay": 0,
          "high_priority_precision": 1.0,
          "high_priority_recall": 0.6666666666666666,
          "negative_recall_delay_queue": 1.0,
          "predicted_high_priority": 108,
          "tn_delay_queue": 47,
          "total": 209,
          "tp_high_priority": 108
        },
        "train_predicted_high_priority": 108
      },
      "train_count": 209
    },
    "groups": {
      "010": {
        "group": "010",
        "label_counts": {
          "delay_queue": 3,
          "high_priority": 2
        },
        "safe_radius": 1.0909139926618652,
        "scope": "scale",
        "threshold": 0.6894165873527527,
        "threshold_info": {
          "threshold": 0.6894165873527527,
          "train_metrics": {
            "accuracy": 1.0,
            "actual_delay_queue": 3,
            "actual_high_priority": 2,
            "fn_delayed_high_priority": 0,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 1.0,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 2,
            "tn_delay_queue": 3,
            "total": 5,
            "tp_high_priority": 2
          },
          "train_predicted_high_priority": 2
        },
        "train_count": 5
      },
      "020": {
        "group": "020",
        "label_counts": {
          "delay_queue": 20,
          "high_priority": 73
        },
        "safe_radius": 2.1235094882395624,
        "scope": "scale",
        "threshold": 0.868527352809906,
        "threshold_info": {
          "threshold": 0.868527352809906,
          "train_metrics": {
            "accuracy": 0.8064516129032258,
            "actual_delay_queue": 20,
            "actual_high_priority": 73,
            "fn_delayed_high_priority": 18,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 0.7534246575342466,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 55,
            "tn_delay_queue": 20,
            "total": 93,
            "tp_high_priority": 55
          },
          "train_predicted_high_priority": 55
        },
        "train_count": 93
      },
      "030": {
        "group": "030",
        "label_counts": {
          "delay_queue": 14,
          "high_priority": 34
        },
        "safe_radius": 5.15786950333306,
        "scope": "scale",
        "threshold": 0.8341923356056213,
        "threshold_info": {
          "threshold": 0.8341923356056213,
          "train_metrics": {
            "accuracy": 0.7708333333333334,
            "actual_delay_queue": 14,
            "actual_high_priority": 34,
            "fn_delayed_high_priority": 11,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 0.6764705882352942,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 23,
            "tn_delay_queue": 14,
            "total": 48,
            "tp_high_priority": 23
          },
          "train_predicted_high_priority": 23
        },
        "train_count": 48
      },
      "050": {
        "group": "050",
        "label_counts": {
          "delay_queue": 8,
          "high_priority": 52
        },
        "safe_radius": 1.720650621671079,
        "scope": "scale",
        "threshold": 0.8850595951080322,
        "threshold_info": {
          "threshold": 0.8850595951080322,
          "train_metrics": {
            "accuracy": 0.7166666666666667,
            "actual_delay_queue": 8,
            "actual_high_priority": 52,
            "fn_delayed_high_priority": 17,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 0.6730769230769231,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 35,
            "tn_delay_queue": 8,
            "total": 60,
            "tp_high_priority": 35
          },
          "train_predicted_high_priority": 35
        },
        "train_count": 60
      }
    },
    "skipped_groups": {
      "005": {
        "label_counts": {
          "delay_queue": 2
        },
        "scope": "fallback_global",
        "skip_reason": "sparse_or_single_label_group",
        "train_count": 2
      },
      "100": {
        "label_counts": {
          "high_priority": 1
        },
        "scope": "fallback_global",
        "skip_reason": "sparse_or_single_label_group",
        "train_count": 1
      }
    },
    "threshold_grouping": "scale"
  },
  "threshold_info": {
    "threshold": 0.8810842633247375,
    "train_metrics": {
      "accuracy": 0.7416267942583732,
      "actual_delay_queue": 47,
      "actual_high_priority": 162,
      "fn_delayed_high_priority": 54,
      "fp_high_priority_on_delay": 0,
      "high_priority_precision": 1.0,
      "high_priority_recall": 0.6666666666666666,
      "negative_recall_delay_queue": 1.0,
      "predicted_high_priority": 108,
      "tn_delay_queue": 47,
      "total": 209,
      "tp_high_priority": 108
    },
    "train_predicted_high_priority": 108
  },
  "validation_metrics": {
    "accuracy": 0.7176470588235294,
    "actual_delay_queue": 16,
    "actual_high_priority": 69,
    "fn_delayed_high_priority": 24,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.6521739130434783,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 45,
    "tn_delay_queue": 16,
    "total": 85,
    "tp_high_priority": 45
  },
  "validation_safety_checks": {
    "delay_recall_met": true,
    "min_high_priority_met": true,
    "no_false_high_priority": true
  }
}
```

## 结论

- `validation_candidate_ready=false` 时，不允许进入 audit-only worker；
- `decision_scope=all` 只用于扩充采样候选，不等同于 holdout validation 通过；
- delay queue 标签代表 true-RC negative 需要延迟，不允许永久丢弃；
- 该审计只验证表示/安全壳，不证明 5/10 不退化，也不证明 20 规模收益。
