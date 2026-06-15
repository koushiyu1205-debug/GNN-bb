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
threshold_grouping = family
decision_scope = all
decision_record_count = 294
decision_split_counts = {'train': 209, 'validation': 85}
decision_threshold_group_counts = {'greedy-anchor': 54, 'random-wave': 190, 'sector-wave': 50}
decision_threshold_scope_counts = {'family': 294}
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
    "below_threshold_delay_queue": 128,
    "high_priority": 146,
    "knn_delay_fraction_delay_queue": 20
  },
  "decision_scope_metrics": {
    "accuracy": 0.7108843537414966,
    "actual_delay_queue": 63,
    "actual_high_priority": 231,
    "fn_delayed_high_priority": 85,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.6320346320346321,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 146,
    "tn_delay_queue": 63,
    "total": 294,
    "tp_high_priority": 146
  },
  "decision_split_counts": {
    "train": 209,
    "validation": 85
  },
  "decision_threshold_group_counts": {
    "greedy-anchor": 54,
    "random-wave": 190,
    "sector-wave": 50
  },
  "decision_threshold_scope_counts": {
    "family": 294
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
      "greedy-anchor": {
        "group": "greedy-anchor",
        "label_counts": {
          "delay_queue": 14,
          "high_priority": 30
        },
        "safe_radius": 4.04257433685198,
        "scope": "family",
        "threshold": 0.8167873024940491,
        "threshold_info": {
          "threshold": 0.8167873024940491,
          "train_metrics": {
            "accuracy": 0.8636363636363636,
            "actual_delay_queue": 14,
            "actual_high_priority": 30,
            "fn_delayed_high_priority": 6,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 0.8,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 24,
            "tn_delay_queue": 14,
            "total": 44,
            "tp_high_priority": 24
          },
          "train_predicted_high_priority": 24
        },
        "train_count": 44
      },
      "random-wave": {
        "group": "random-wave",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 99
        },
        "safe_radius": 2.1458133018593273,
        "scope": "family",
        "threshold": 0.8850595951080322,
        "threshold_info": {
          "threshold": 0.8850595951080322,
          "train_metrics": {
            "accuracy": 0.712,
            "actual_delay_queue": 26,
            "actual_high_priority": 99,
            "fn_delayed_high_priority": 36,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 0.6363636363636364,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 63,
            "tn_delay_queue": 26,
            "total": 125,
            "tp_high_priority": 63
          },
          "train_predicted_high_priority": 63
        },
        "train_count": 125
      },
      "sector-wave": {
        "group": "sector-wave",
        "label_counts": {
          "delay_queue": 7,
          "high_priority": 33
        },
        "safe_radius": 4.243743512183245,
        "scope": "family",
        "threshold": 0.868527352809906,
        "threshold_info": {
          "threshold": 0.868527352809906,
          "train_metrics": {
            "accuracy": 0.825,
            "actual_delay_queue": 7,
            "actual_high_priority": 33,
            "fn_delayed_high_priority": 7,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 0.7878787878787878,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 26,
            "tn_delay_queue": 7,
            "total": 40,
            "tp_high_priority": 26
          },
          "train_predicted_high_priority": 26
        },
        "train_count": 40
      }
    },
    "skipped_groups": {},
    "threshold_grouping": "family"
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
    "accuracy": 0.7294117647058823,
    "actual_delay_queue": 16,
    "actual_high_priority": 69,
    "fn_delayed_high_priority": 23,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.6666666666666666,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 46,
    "tn_delay_queue": 16,
    "total": 85,
    "tp_high_priority": 46
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
