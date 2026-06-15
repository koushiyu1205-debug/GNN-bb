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
threshold_grouping = scale_family
decision_scope = all
decision_record_count = 294
decision_split_counts = {'train': 209, 'validation': 85}
decision_threshold_group_counts = {'010|greedy-anchor': 8, '020|greedy-anchor': 44, '020|random-wave': 24, '020|sector-wave': 50, '030|random-wave': 76, '050|random-wave': 89, 'global': 3}
decision_threshold_scope_counts = {'global': 3, 'scale_family': 291}
validation_safety_shell_metrics = {'total': 85, 'coverage_non_ood_count': 80, 'coverage': 0.9411764705882353, 'ood_count': 5, 'ood_rate': 0.058823529411764705, 'delay_count': 38, 'delay_rate': 0.4470588235294118, 'accepted_batch_count': 47, 'accepted_batch_rate': 0.5529411764705883, 'accepted_batch_roi_positive_count': 47, 'accepted_batch_roi': 1.0, 'safe_precision': 1.0, 'unsafe_label_count': 16, 'knn_unsafe_count': 29, 'unsafe_or_ood_count': 31, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_threshold_delay_queue': 29, 'high_priority': 47, 'knn_delay_fraction_delay_queue': 9}, 'accepted_reason_counts': {'high_priority': 47}}
decision_scope_safety_shell_metrics = {'total': 294, 'coverage_non_ood_count': 285, 'coverage': 0.9693877551020408, 'ood_count': 9, 'ood_rate': 0.030612244897959183, 'delay_count': 143, 'delay_rate': 0.48639455782312924, 'accepted_batch_count': 151, 'accepted_batch_rate': 0.5136054421768708, 'accepted_batch_roi_positive_count': 151, 'accepted_batch_roi': 1.0, 'safe_precision': 1.0, 'unsafe_label_count': 63, 'knn_unsafe_count': 112, 'unsafe_or_ood_count': 114, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_threshold_delay_queue': 117, 'high_priority': 151, 'knn_delay_fraction_delay_queue': 26}, 'accepted_reason_counts': {'high_priority': 151}}
validation_candidate_ready = true
validation_safety_ready = true
validation_safety_checks = {'no_false_high_priority': True, 'min_high_priority_met': True, 'delay_recall_met': True, 'false_safe_rate_met': True}
production_block_reasons = []
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "below_threshold_delay_queue": 117,
    "high_priority": 151,
    "knn_delay_fraction_delay_queue": 26
  },
  "decision_scope_metrics": {
    "accuracy": 0.7278911564625851,
    "actual_delay_queue": 63,
    "actual_high_priority": 231,
    "fn_delayed_high_priority": 80,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.6536796536796536,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 151,
    "tn_delay_queue": 63,
    "total": 294,
    "tp_high_priority": 151
  },
  "decision_scope_safety_shell_metrics": {
    "accepted_batch_count": 151,
    "accepted_batch_rate": 0.5136054421768708,
    "accepted_batch_roi": 1.0,
    "accepted_batch_roi_positive_count": 151,
    "accepted_reason_counts": {
      "high_priority": 151
    },
    "coverage": 0.9693877551020408,
    "coverage_non_ood_count": 285,
    "decision_reason_counts": {
      "below_threshold_delay_queue": 117,
      "high_priority": 151,
      "knn_delay_fraction_delay_queue": 26
    },
    "delay_count": 143,
    "delay_rate": 0.48639455782312924,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 0,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_unsafe_count": 112,
    "ood_count": 9,
    "ood_rate": 0.030612244897959183,
    "safe_precision": 1.0,
    "total": 294,
    "unsafe_label_count": 63,
    "unsafe_or_ood_count": 114
  },
  "decision_split_counts": {
    "train": 209,
    "validation": 85
  },
  "decision_threshold_group_counts": {
    "010|greedy-anchor": 8,
    "020|greedy-anchor": 44,
    "020|random-wave": 24,
    "020|sector-wave": 50,
    "030|random-wave": 76,
    "050|random-wave": 89,
    "global": 3
  },
  "decision_threshold_scope_counts": {
    "global": 3,
    "scale_family": 291
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
      "010|greedy-anchor": {
        "group": "010|greedy-anchor",
        "label_counts": {
          "delay_queue": 3,
          "high_priority": 2
        },
        "safe_radius": 1.0909139926618652,
        "scope": "scale_family",
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
      "020|greedy-anchor": {
        "group": "020|greedy-anchor",
        "label_counts": {
          "delay_queue": 9,
          "high_priority": 28
        },
        "safe_radius": 4.04257433685198,
        "scope": "scale_family",
        "threshold": 0.8167873024940491,
        "threshold_info": {
          "threshold": 0.8167873024940491,
          "train_metrics": {
            "accuracy": 0.8648648648648649,
            "actual_delay_queue": 9,
            "actual_high_priority": 28,
            "fn_delayed_high_priority": 5,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 0.8214285714285714,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 23,
            "tn_delay_queue": 9,
            "total": 37,
            "tp_high_priority": 23
          },
          "train_predicted_high_priority": 23
        },
        "train_count": 37
      },
      "020|random-wave": {
        "group": "020|random-wave",
        "label_counts": {
          "delay_queue": 4,
          "high_priority": 12
        },
        "safe_radius": 3.214755120511002,
        "scope": "scale_family",
        "threshold": 0.6580277681350708,
        "threshold_info": {
          "threshold": 0.6580277681350708,
          "train_metrics": {
            "accuracy": 0.9375,
            "actual_delay_queue": 4,
            "actual_high_priority": 12,
            "fn_delayed_high_priority": 1,
            "fp_high_priority_on_delay": 0,
            "high_priority_precision": 1.0,
            "high_priority_recall": 0.9166666666666666,
            "negative_recall_delay_queue": 1.0,
            "predicted_high_priority": 11,
            "tn_delay_queue": 4,
            "total": 16,
            "tp_high_priority": 11
          },
          "train_predicted_high_priority": 11
        },
        "train_count": 16
      },
      "020|sector-wave": {
        "group": "020|sector-wave",
        "label_counts": {
          "delay_queue": 7,
          "high_priority": 33
        },
        "safe_radius": 4.243743512183245,
        "scope": "scale_family",
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
      },
      "030|random-wave": {
        "group": "030|random-wave",
        "label_counts": {
          "delay_queue": 14,
          "high_priority": 34
        },
        "safe_radius": 5.15786950333306,
        "scope": "scale_family",
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
      "050|random-wave": {
        "group": "050|random-wave",
        "label_counts": {
          "delay_queue": 8,
          "high_priority": 52
        },
        "safe_radius": 1.720650621671079,
        "scope": "scale_family",
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
      "005|greedy-anchor": {
        "label_counts": {
          "delay_queue": 2
        },
        "scope": "fallback_global",
        "skip_reason": "sparse_or_single_label_group",
        "train_count": 2
      },
      "100|random-wave": {
        "label_counts": {
          "high_priority": 1
        },
        "scope": "fallback_global",
        "skip_reason": "sparse_or_single_label_group",
        "train_count": 1
      }
    },
    "threshold_grouping": "scale_family"
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
    "accuracy": 0.7411764705882353,
    "actual_delay_queue": 16,
    "actual_high_priority": 69,
    "fn_delayed_high_priority": 22,
    "fp_high_priority_on_delay": 0,
    "high_priority_precision": 1.0,
    "high_priority_recall": 0.6811594202898551,
    "negative_recall_delay_queue": 1.0,
    "predicted_high_priority": 47,
    "tn_delay_queue": 16,
    "total": 85,
    "tp_high_priority": 47
  },
  "validation_safety_checks": {
    "delay_recall_met": true,
    "false_safe_rate_met": true,
    "min_high_priority_met": true,
    "no_false_high_priority": true
  },
  "validation_safety_shell_metrics": {
    "accepted_batch_count": 47,
    "accepted_batch_rate": 0.5529411764705883,
    "accepted_batch_roi": 1.0,
    "accepted_batch_roi_positive_count": 47,
    "accepted_reason_counts": {
      "high_priority": 47
    },
    "coverage": 0.9411764705882353,
    "coverage_non_ood_count": 80,
    "decision_reason_counts": {
      "below_threshold_delay_queue": 29,
      "high_priority": 47,
      "knn_delay_fraction_delay_queue": 9
    },
    "delay_count": 38,
    "delay_rate": 0.4470588235294118,
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 0,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_unsafe_count": 29,
    "ood_count": 5,
    "ood_rate": 0.058823529411764705,
    "safe_precision": 1.0,
    "total": 85,
    "unsafe_label_count": 16,
    "unsafe_or_ood_count": 31
  }
}
```

## 结论

- `validation_candidate_ready=false` 时，不允许进入 audit-only worker；
- `decision_scope=all` 只用于扩充采样候选，不等同于 holdout validation 通过；
- delay queue 标签代表 true-RC negative 需要延迟，不允许永久丢弃；
- 该审计只验证表示/安全壳，不证明 5/10 不退化，也不证明 20 规模收益。
