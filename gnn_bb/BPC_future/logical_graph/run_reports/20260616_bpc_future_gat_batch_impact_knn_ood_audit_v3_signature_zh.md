# GAT Batch Impact kNN/OOD Audit 报告

日期：2026-06-15

## 目的

审计 `GATBatchImpactModel` checkpoint 的离线 validation 表现，并用 kNN/OOD
safety shell 检查 HIGH_PRIORITY batch 是否安全。该流程不运行 BPC、pricing、
RMP、worker 或 certificate。

## 机器字段

```text
gat_batch_impact_knn_ood = current
status = gat_batch_impact_knn_ood_audited
train_row_count = 216
validation_row_count = 78
train_label_counts = {'delay_queue': 46, 'high_priority': 170}
validation_label_counts = {'delay_queue': 17, 'high_priority': 61}
batch_threshold = 0.8389831185340881
candidate_threshold = 0.8163509964942932
threshold_grouping = global
decision_scope = validation
decision_record_count = 78
validation_metrics = {'total': 78, 'coverage_non_ood_count': 78, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 76, 'delay_rate': 0.9743589743589743, 'accepted_batch_count': 2, 'accepted_batch_rate': 0.02564102564102564, 'accepted_batch_roi_positive_count': 2, 'accepted_batch_roi': 0.9396930038928986, 'accepted_batch_roi_ci_low': 0.6137750887870789, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.3423719528896193, 'unsafe_label_count': 17, 'knn_unsafe_count': 38, 'unsafe_or_ood_count': 42, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 74, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 69, 'high_priority': 2, 'no_candidate_high_priority_delay_queue': 7}, 'accepted_reason_counts': {'high_priority': 2}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': ['greedy-anchor'], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': ['greedy-anchor'], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 14, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 4, 'knn_unsafe_count': 7, 'unsafe_or_ood_count': 9, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 12, 'no_candidate_high_priority_delay_queue': 2}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 38, 'coverage_non_ood_count': 38, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 37, 'delay_rate': 0.9736842105263158, 'accepted_batch_count': 1, 'accepted_batch_rate': 0.02631578947368421, 'accepted_batch_roi_positive_count': 1, 'accepted_batch_roi': 1.1059776544570923, 'accepted_batch_roi_ci_low': None, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.20654329147389294, 'unsafe_label_count': 9, 'knn_unsafe_count': 21, 'unsafe_or_ood_count': 22, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 34, 'high_priority': 1, 'no_candidate_high_priority_delay_queue': 3}, 'accepted_reason_counts': {'high_priority': 1}, 'oracle_high_roi_count': 3, 'max_accepted_batch_roi_label': 1.1059776544570923}, 'sector-wave': {'total': 26, 'coverage_non_ood_count': 26, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 25, 'delay_rate': 0.9615384615384616, 'accepted_batch_count': 1, 'accepted_batch_rate': 0.038461538461538464, 'accepted_batch_roi_positive_count': 1, 'accepted_batch_roi': 0.7734083533287048, 'accepted_batch_roi_ci_low': None, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.20654329147389294, 'unsafe_label_count': 4, 'knn_unsafe_count': 10, 'unsafe_or_ood_count': 11, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 33, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 23, 'high_priority': 1, 'no_candidate_high_priority_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 1}, 'oracle_high_roi_count': 5, 'max_accepted_batch_roi_label': 2.5879690647125244}}}
validation_safety_checks = {'min_high_priority_met': True, 'safe_precision_met': True, 'safe_precision_ci_low_met': False, 'accepted_batch_count_met': True, 'accepted_batch_rate_met': True, 'accepted_batch_roi_met': True, 'accepted_batch_roi_ci_low_met': False, 'false_high_priority_on_delay_met': True, 'false_safe_rate_met': True, 'coverage_met': True, 'family_holdout_all_high_roi_opportunity_families_accepted': True}
validation_candidate_ready = false
production_block_reasons = ['validation_safe_precision_ci_low_below_min', 'validation_accepted_batch_roi_ci_low_below_min', 'validation_candidate_not_ready']
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "below_batch_threshold_delay_queue": 69,
    "high_priority": 2,
    "no_candidate_high_priority_delay_queue": 7
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 2,
    "accepted_batch_rate": 0.02564102564102564,
    "accepted_batch_roi": 0.9396930038928986,
    "accepted_batch_roi_ci_low": 0.6137750887870789,
    "accepted_batch_roi_positive_count": 2,
    "accepted_reason_counts": {
      "high_priority": 2
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 78,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 69,
      "high_priority": 2,
      "no_candidate_high_priority_delay_queue": 7
    },
    "delay_count": 76,
    "delay_label_count": 74,
    "delay_rate": 0.9743589743589743,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_positive_context_count": 0,
    "false_positive_contexts": [],
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 0,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_unsafe_count": 38,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.3423719528896193,
    "total": 78,
    "unsafe_label_count": 17,
    "unsafe_or_ood_count": 42
  },
  "decision_split_counts": {
    "validation": 78
  },
  "decision_threshold_group_counts": {
    "global": 78
  },
  "decision_threshold_scope_counts": {
    "global": 78
  },
  "production_block_reasons": [
    "validation_safe_precision_ci_low_below_min",
    "validation_accepted_batch_roi_ci_low_below_min",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.8389831185340881,
      "batch_thresholds_by_family": {},
      "candidate_threshold": 0.8163509964942932,
      "group": "global",
      "label_counts": {
        "delay_queue": 46,
        "high_priority": 170
      },
      "safe_radius": 1.2481723996145013,
      "scope": "global",
      "train_count": 216
    },
    "groups": {},
    "skipped_groups": {},
    "threshold_grouping": "global"
  },
  "validation_false_safe_rates": {
    "knn_unsafe": 0.0,
    "label_unsafe": 0.0,
    "max_observed_false_safe_rate": 0.0,
    "max_observed_false_safe_source": "knn_unsafe",
    "ood": null,
    "union": 0.0
  },
  "validation_family_metrics": {
    "family_count": 3,
    "family_specific_delay_fallback_families": [
      "greedy-anchor"
    ],
    "missing_accepted_families": [
      "greedy-anchor"
    ],
    "missing_accepted_opportunity_families": [],
    "oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 0,
        "accepted_batch_rate": 0.0,
        "accepted_batch_roi": null,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 0,
        "accepted_reason_counts": {},
        "coverage": 1.0,
        "coverage_non_ood_count": 14,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 12,
          "no_candidate_high_priority_delay_queue": 2
        },
        "delay_count": 14,
        "delay_label_count": 24,
        "delay_rate": 1.0,
        "false_high_priority_on_delay": 0.0,
        "false_high_priority_on_delay_count": 0,
        "false_positive_context_count": 0,
        "false_positive_contexts": [],
        "false_safe_knn_unsafe_count": 0,
        "false_safe_label_unsafe_count": 0,
        "false_safe_ood_count": 0,
        "false_safe_rate_knn_unsafe": 0.0,
        "false_safe_rate_label_unsafe": 0.0,
        "false_safe_rate_ood": null,
        "false_safe_rate_union": 0.0,
        "false_safe_union_count": 0,
        "knn_unsafe_count": 7,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "safe_precision_ci_low": null,
        "total": 14,
        "unsafe_label_count": 4,
        "unsafe_or_ood_count": 9
      },
      "random-wave": {
        "accepted_batch_count": 1,
        "accepted_batch_rate": 0.02631578947368421,
        "accepted_batch_roi": 1.1059776544570923,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 1,
        "accepted_reason_counts": {
          "high_priority": 1
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 38,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 34,
          "high_priority": 1,
          "no_candidate_high_priority_delay_queue": 3
        },
        "delay_count": 37,
        "delay_label_count": 17,
        "delay_rate": 0.9736842105263158,
        "false_high_priority_on_delay": 0.0,
        "false_high_priority_on_delay_count": 0,
        "false_positive_context_count": 0,
        "false_positive_contexts": [],
        "false_safe_knn_unsafe_count": 0,
        "false_safe_label_unsafe_count": 0,
        "false_safe_ood_count": 0,
        "false_safe_rate_knn_unsafe": 0.0,
        "false_safe_rate_label_unsafe": 0.0,
        "false_safe_rate_ood": null,
        "false_safe_rate_union": 0.0,
        "false_safe_union_count": 0,
        "knn_unsafe_count": 21,
        "max_accepted_batch_roi_label": 1.1059776544570923,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 3,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.20654329147389294,
        "total": 38,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 22
      },
      "sector-wave": {
        "accepted_batch_count": 1,
        "accepted_batch_rate": 0.038461538461538464,
        "accepted_batch_roi": 0.7734083533287048,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 1,
        "accepted_reason_counts": {
          "high_priority": 1
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 26,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 23,
          "high_priority": 1,
          "no_candidate_high_priority_delay_queue": 2
        },
        "delay_count": 25,
        "delay_label_count": 33,
        "delay_rate": 0.9615384615384616,
        "false_high_priority_on_delay": 0.0,
        "false_high_priority_on_delay_count": 0,
        "false_positive_context_count": 0,
        "false_positive_contexts": [],
        "false_safe_knn_unsafe_count": 0,
        "false_safe_label_unsafe_count": 0,
        "false_safe_ood_count": 0,
        "false_safe_rate_knn_unsafe": 0.0,
        "false_safe_rate_label_unsafe": 0.0,
        "false_safe_rate_ood": null,
        "false_safe_rate_union": 0.0,
        "false_safe_union_count": 0,
        "knn_unsafe_count": 10,
        "max_accepted_batch_roi_label": 2.5879690647125244,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 5,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.20654329147389294,
        "total": 26,
        "unsafe_label_count": 4,
        "unsafe_or_ood_count": 11
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 2,
    "accepted_batch_rate": 0.02564102564102564,
    "accepted_batch_roi": 0.9396930038928986,
    "accepted_batch_roi_ci_low": 0.6137750887870789,
    "accepted_batch_roi_positive_count": 2,
    "accepted_reason_counts": {
      "high_priority": 2
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 78,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 69,
      "high_priority": 2,
      "no_candidate_high_priority_delay_queue": 7
    },
    "delay_count": 76,
    "delay_label_count": 74,
    "delay_rate": 0.9743589743589743,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_positive_context_count": 0,
    "false_positive_contexts": [],
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 0,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_ood": null,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_unsafe_count": 38,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.3423719528896193,
    "total": 78,
    "unsafe_label_count": 17,
    "unsafe_or_ood_count": 42
  },
  "validation_safety_checks": {
    "accepted_batch_count_met": true,
    "accepted_batch_rate_met": true,
    "accepted_batch_roi_ci_low_met": false,
    "accepted_batch_roi_met": true,
    "coverage_met": true,
    "false_high_priority_on_delay_met": true,
    "false_safe_rate_met": true,
    "family_holdout_all_high_roi_opportunity_families_accepted": true,
    "min_high_priority_met": true,
    "safe_precision_ci_low_met": false,
    "safe_precision_met": true
  }
}
```

## 边界

- 本审计只验证 offline admission safety shell，不证明 5/10 no-regression；
- kNN/OOD 只能把 true-RC negative 延迟到 DELAY_QUEUE，不能永久丢弃；
- kNN/OOD no-column / no-safe 不能产生 `CERTIFIED_NO_NEGATIVE`；
- final certificate 仍必须来自 exact pricing full closure。
