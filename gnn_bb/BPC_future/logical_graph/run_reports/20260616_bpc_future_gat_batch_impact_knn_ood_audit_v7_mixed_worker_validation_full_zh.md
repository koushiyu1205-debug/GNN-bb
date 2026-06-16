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
train_row_count = 222
validation_row_count = 92
train_label_counts = {'delay_queue': 47, 'high_priority': 175}
validation_label_counts = {'delay_queue': 20, 'high_priority': 72}
batch_threshold = 0.7440426349639893
candidate_threshold = 0.45480406284332275
threshold_grouping = family
decision_scope = validation
decision_record_count = 92
validation_metrics = {'total': 92, 'coverage_non_ood_count': 87, 'coverage': 0.9456521739130435, 'ood_count': 5, 'ood_rate': 0.05434782608695652, 'delay_count': 90, 'delay_rate': 0.9782608695652174, 'accepted_batch_count': 2, 'accepted_batch_rate': 0.021739130434782608, 'accepted_batch_roi_positive_count': 2, 'accepted_batch_roi': 1.1196053624153137, 'accepted_batch_roi_ci_low': 1.0928950548171996, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.3423719528896193, 'unsafe_label_count': 20, 'knn_unsafe_count': 47, 'unsafe_or_ood_count': 52, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 77, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 85, 'high_priority': 2, 'knn_delay_fraction_delay_queue': 4, 'ood_radius_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 2}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': ['greedy-anchor'], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': ['greedy-anchor'], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 14, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 4, 'knn_unsafe_count': 8, 'unsafe_or_ood_count': 8, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 14}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 38, 'coverage_non_ood_count': 38, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 37, 'delay_rate': 0.9736842105263158, 'accepted_batch_count': 1, 'accepted_batch_rate': 0.02631578947368421, 'accepted_batch_roi_positive_count': 1, 'accepted_batch_roi': 1.1059776544570923, 'accepted_batch_roi_ci_low': None, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.20654329147389294, 'unsafe_label_count': 9, 'knn_unsafe_count': 21, 'unsafe_or_ood_count': 22, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 37, 'high_priority': 1}, 'accepted_reason_counts': {'high_priority': 1}, 'oracle_high_roi_count': 3, 'max_accepted_batch_roi_label': 1.1059776544570923}, 'sector-wave': {'total': 40, 'coverage_non_ood_count': 35, 'coverage': 0.875, 'ood_count': 5, 'ood_rate': 0.125, 'delay_count': 39, 'delay_rate': 0.975, 'accepted_batch_count': 1, 'accepted_batch_rate': 0.025, 'accepted_batch_roi_positive_count': 1, 'accepted_batch_roi': 1.1332330703735352, 'accepted_batch_roi_ci_low': None, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.20654329147389294, 'unsafe_label_count': 7, 'knn_unsafe_count': 18, 'unsafe_or_ood_count': 22, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 36, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 34, 'high_priority': 1, 'knn_delay_fraction_delay_queue': 4, 'ood_radius_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 1}, 'oracle_high_roi_count': 16, 'max_accepted_batch_roi_label': 41.31852722167969}}}
validation_safety_checks = {'min_high_priority_met': True, 'safe_precision_met': True, 'safe_precision_ci_low_met': False, 'accepted_batch_count_met': True, 'accepted_batch_rate_met': True, 'accepted_batch_roi_met': True, 'accepted_batch_roi_ci_low_met': True, 'false_high_priority_on_delay_met': True, 'false_safe_rate_met': True, 'coverage_met': True, 'family_holdout_all_high_roi_opportunity_families_accepted': True}
validation_candidate_ready = false
production_block_reasons = ['validation_safe_precision_ci_low_below_min', 'validation_candidate_not_ready']
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "below_batch_threshold_delay_queue": 85,
    "high_priority": 2,
    "knn_delay_fraction_delay_queue": 4,
    "ood_radius_delay_queue": 1
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 2,
    "accepted_batch_rate": 0.021739130434782608,
    "accepted_batch_roi": 1.1196053624153137,
    "accepted_batch_roi_ci_low": 1.0928950548171996,
    "accepted_batch_roi_positive_count": 2,
    "accepted_reason_counts": {
      "high_priority": 2
    },
    "coverage": 0.9456521739130435,
    "coverage_non_ood_count": 87,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 85,
      "high_priority": 2,
      "knn_delay_fraction_delay_queue": 4,
      "ood_radius_delay_queue": 1
    },
    "delay_count": 90,
    "delay_label_count": 77,
    "delay_rate": 0.9782608695652174,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_positive_context_count": 0,
    "false_positive_contexts": [],
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 0,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_unsafe_count": 47,
    "ood_count": 5,
    "ood_rate": 0.05434782608695652,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.3423719528896193,
    "total": 92,
    "unsafe_label_count": 20,
    "unsafe_or_ood_count": 52
  },
  "decision_split_counts": {
    "validation": 92
  },
  "decision_threshold_group_counts": {
    "greedy-anchor": 14,
    "random-wave": 38,
    "sector-wave": 40
  },
  "decision_threshold_scope_counts": {
    "family": 92
  },
  "production_block_reasons": [
    "validation_safe_precision_ci_low_below_min",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.7440426349639893,
      "batch_thresholds_by_family": {},
      "candidate_threshold": 0.45480406284332275,
      "group": "global",
      "label_counts": {
        "delay_queue": 47,
        "high_priority": 175
      },
      "safe_radius": 12.050378078672423,
      "scope": "global",
      "train_count": 222
    },
    "groups": {
      "greedy-anchor": {
        "batch_threshold": 0.7440426349639893,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.45480406284332275,
        "group": "greedy-anchor",
        "label_counts": {
          "delay_queue": 14,
          "high_priority": 26
        },
        "safe_radius": 5.6468908601393,
        "scope": "family",
        "train_count": 40
      },
      "random-wave": {
        "batch_threshold": 0.7440426349639893,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.45480406284332275,
        "group": "random-wave",
        "label_counts": {
          "delay_queue": 28,
          "high_priority": 127
        },
        "safe_radius": 12.050378078672423,
        "scope": "family",
        "train_count": 155
      },
      "sector-wave": {
        "batch_threshold": 0.7440426349639893,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.45480406284332275,
        "group": "sector-wave",
        "label_counts": {
          "delay_queue": 5,
          "high_priority": 22
        },
        "safe_radius": 6.204527248848638,
        "scope": "family",
        "train_count": 27
      }
    },
    "skipped_groups": {},
    "threshold_grouping": "family"
  },
  "validation_false_safe_rates": {
    "knn_unsafe": 0.0,
    "label_unsafe": 0.0,
    "max_observed_false_safe_rate": 0.0,
    "max_observed_false_safe_source": "ood",
    "ood": 0.0,
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
          "below_batch_threshold_delay_queue": 14
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
        "knn_unsafe_count": 8,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "safe_precision_ci_low": null,
        "total": 14,
        "unsafe_label_count": 4,
        "unsafe_or_ood_count": 8
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
          "below_batch_threshold_delay_queue": 37,
          "high_priority": 1
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
        "accepted_batch_rate": 0.025,
        "accepted_batch_roi": 1.1332330703735352,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 1,
        "accepted_reason_counts": {
          "high_priority": 1
        },
        "coverage": 0.875,
        "coverage_non_ood_count": 35,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 34,
          "high_priority": 1,
          "knn_delay_fraction_delay_queue": 4,
          "ood_radius_delay_queue": 1
        },
        "delay_count": 39,
        "delay_label_count": 36,
        "delay_rate": 0.975,
        "false_high_priority_on_delay": 0.0,
        "false_high_priority_on_delay_count": 0,
        "false_positive_context_count": 0,
        "false_positive_contexts": [],
        "false_safe_knn_unsafe_count": 0,
        "false_safe_label_unsafe_count": 0,
        "false_safe_ood_count": 0,
        "false_safe_rate_knn_unsafe": 0.0,
        "false_safe_rate_label_unsafe": 0.0,
        "false_safe_rate_ood": 0.0,
        "false_safe_rate_union": 0.0,
        "false_safe_union_count": 0,
        "knn_unsafe_count": 18,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 5,
        "ood_rate": 0.125,
        "oracle_high_roi_count": 16,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.20654329147389294,
        "total": 40,
        "unsafe_label_count": 7,
        "unsafe_or_ood_count": 22
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 2,
    "accepted_batch_rate": 0.021739130434782608,
    "accepted_batch_roi": 1.1196053624153137,
    "accepted_batch_roi_ci_low": 1.0928950548171996,
    "accepted_batch_roi_positive_count": 2,
    "accepted_reason_counts": {
      "high_priority": 2
    },
    "coverage": 0.9456521739130435,
    "coverage_non_ood_count": 87,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 85,
      "high_priority": 2,
      "knn_delay_fraction_delay_queue": 4,
      "ood_radius_delay_queue": 1
    },
    "delay_count": 90,
    "delay_label_count": 77,
    "delay_rate": 0.9782608695652174,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_positive_context_count": 0,
    "false_positive_contexts": [],
    "false_safe_knn_unsafe_count": 0,
    "false_safe_label_unsafe_count": 0,
    "false_safe_ood_count": 0,
    "false_safe_rate_knn_unsafe": 0.0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_unsafe_count": 47,
    "ood_count": 5,
    "ood_rate": 0.05434782608695652,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.3423719528896193,
    "total": 92,
    "unsafe_label_count": 20,
    "unsafe_or_ood_count": 52
  },
  "validation_safety_checks": {
    "accepted_batch_count_met": true,
    "accepted_batch_rate_met": true,
    "accepted_batch_roi_ci_low_met": true,
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
