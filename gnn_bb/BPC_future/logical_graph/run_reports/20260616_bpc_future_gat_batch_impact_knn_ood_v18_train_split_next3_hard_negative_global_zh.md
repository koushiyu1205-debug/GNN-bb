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
train_row_count = 235
validation_row_count = 119
train_label_counts = {'delay_queue': 56, 'high_priority': 179}
validation_label_counts = {'delay_queue': 33, 'high_priority': 86}
batch_threshold = 0.0
candidate_threshold = 0.7447547316551208
threshold_grouping = global
decision_scope = validation
decision_record_count = 119
validation_metrics = {'total': 119, 'coverage_non_ood_count': 119, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 81, 'delay_rate': 0.680672268907563, 'accepted_batch_count': 38, 'accepted_batch_rate': 0.31932773109243695, 'accepted_batch_roi_positive_count': 38, 'accepted_batch_roi': 3.4119277786693076, 'accepted_batch_roi_ci_low': 0.607449381373161, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.90818706741616, 'unsafe_label_count': 33, 'knn_unsafe_count': 62, 'unsafe_or_ood_count': 68, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 118, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 1, 'high_priority': 38, 'knn_delay_fraction_delay_queue': 1, 'no_candidate_high_priority_delay_queue': 79}, 'accepted_reason_counts': {'high_priority': 38}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 8, 'delay_rate': 0.5714285714285714, 'accepted_batch_count': 6, 'accepted_batch_rate': 0.42857142857142855, 'accepted_batch_roi_positive_count': 6, 'accepted_batch_roi': 0.11975858719658088, 'accepted_batch_roi_ci_low': -0.0020965470092783878, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.6096569663469354, 'unsafe_label_count': 4, 'knn_unsafe_count': 5, 'unsafe_or_ood_count': 6, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'high_priority': 6, 'no_candidate_high_priority_delay_queue': 8}, 'accepted_reason_counts': {'high_priority': 6}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 44, 'coverage_non_ood_count': 44, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 33, 'delay_rate': 0.75, 'accepted_batch_count': 11, 'accepted_batch_rate': 0.25, 'accepted_batch_roi_positive_count': 11, 'accepted_batch_roi': 0.2805267370051958, 'accepted_batch_roi_ci_low': 0.10652672721139428, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7411599827511859, 'unsafe_label_count': 9, 'knn_unsafe_count': 24, 'unsafe_or_ood_count': 24, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'high_priority': 11, 'no_candidate_high_priority_delay_queue': 33}, 'accepted_reason_counts': {'high_priority': 11}, 'oracle_high_roi_count': 6, 'max_accepted_batch_roi_label': 4.385624885559082}, 'sector-wave': {'total': 61, 'coverage_non_ood_count': 61, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 40, 'delay_rate': 0.6557377049180327, 'accepted_batch_count': 21, 'accepted_batch_rate': 0.3442622950819672, 'accepted_batch_roi_positive_count': 21, 'accepted_batch_roi': 5.992805236152241, 'accepted_batch_roi_ci_low': 1.1493000249604677, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8453561767357979, 'unsafe_label_count': 20, 'knn_unsafe_count': 33, 'unsafe_or_ood_count': 38, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 77, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 1, 'high_priority': 21, 'knn_delay_fraction_delay_queue': 1, 'no_candidate_high_priority_delay_queue': 38}, 'accepted_reason_counts': {'high_priority': 21}, 'oracle_high_roi_count': 24, 'max_accepted_batch_roi_label': 41.31852722167969}}}
validation_safety_checks = {'min_high_priority_met': True, 'safe_precision_met': True, 'safe_precision_ci_low_met': True, 'accepted_batch_count_met': True, 'accepted_batch_rate_met': True, 'accepted_batch_roi_met': True, 'accepted_batch_roi_ci_low_met': False, 'false_high_priority_on_delay_met': True, 'false_safe_rate_met': True, 'coverage_met': True, 'family_holdout_all_high_roi_opportunity_families_accepted': True}
validation_candidate_ready = false
production_block_reasons = ['validation_accepted_batch_roi_ci_low_below_min', 'validation_candidate_not_ready']
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "candidate_false_high_priority_delay_queue": 1,
    "high_priority": 38,
    "knn_delay_fraction_delay_queue": 1,
    "no_candidate_high_priority_delay_queue": 79
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 38,
    "accepted_batch_rate": 0.31932773109243695,
    "accepted_batch_roi": 3.4119277786693076,
    "accepted_batch_roi_ci_low": 0.607449381373161,
    "accepted_batch_roi_positive_count": 38,
    "accepted_reason_counts": {
      "high_priority": 38
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 1,
      "high_priority": 38,
      "knn_delay_fraction_delay_queue": 1,
      "no_candidate_high_priority_delay_queue": 79
    },
    "delay_count": 81,
    "delay_label_count": 118,
    "delay_rate": 0.680672268907563,
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
    "knn_unsafe_count": 62,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.90818706741616,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 68
  },
  "decision_split_counts": {
    "validation": 119
  },
  "decision_threshold_group_counts": {
    "global": 119
  },
  "decision_threshold_scope_counts": {
    "global": 119
  },
  "production_block_reasons": [
    "validation_accepted_batch_roi_ci_low_below_min",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.0,
      "batch_thresholds_by_family": {},
      "candidate_threshold": 0.7447547316551208,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 56,
        "high_priority": 179
      },
      "safe_radius": 8.314975144312793,
      "scope": "global",
      "train_count": 235
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
    "family_specific_delay_fallback_families": [],
    "missing_accepted_families": [],
    "missing_accepted_opportunity_families": [],
    "oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 6,
        "accepted_batch_rate": 0.42857142857142855,
        "accepted_batch_roi": 0.11975858719658088,
        "accepted_batch_roi_ci_low": -0.0020965470092783878,
        "accepted_batch_roi_positive_count": 6,
        "accepted_reason_counts": {
          "high_priority": 6
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 14,
        "decision_reason_counts": {
          "high_priority": 6,
          "no_candidate_high_priority_delay_queue": 8
        },
        "delay_count": 8,
        "delay_label_count": 24,
        "delay_rate": 0.5714285714285714,
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
        "knn_unsafe_count": 5,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.6096569663469354,
        "total": 14,
        "unsafe_label_count": 4,
        "unsafe_or_ood_count": 6
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_rate": 0.25,
        "accepted_batch_roi": 0.2805267370051958,
        "accepted_batch_roi_ci_low": 0.10652672721139428,
        "accepted_batch_roi_positive_count": 11,
        "accepted_reason_counts": {
          "high_priority": 11
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 44,
        "decision_reason_counts": {
          "high_priority": 11,
          "no_candidate_high_priority_delay_queue": 33
        },
        "delay_count": 33,
        "delay_label_count": 17,
        "delay_rate": 0.75,
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
        "knn_unsafe_count": 24,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7411599827511859,
        "total": 44,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 24
      },
      "sector-wave": {
        "accepted_batch_count": 21,
        "accepted_batch_rate": 0.3442622950819672,
        "accepted_batch_roi": 5.992805236152241,
        "accepted_batch_roi_ci_low": 1.1493000249604677,
        "accepted_batch_roi_positive_count": 21,
        "accepted_reason_counts": {
          "high_priority": 21
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 61,
        "decision_reason_counts": {
          "candidate_false_high_priority_delay_queue": 1,
          "high_priority": 21,
          "knn_delay_fraction_delay_queue": 1,
          "no_candidate_high_priority_delay_queue": 38
        },
        "delay_count": 40,
        "delay_label_count": 77,
        "delay_rate": 0.6557377049180327,
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
        "knn_unsafe_count": 33,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.8453561767357979,
        "total": 61,
        "unsafe_label_count": 20,
        "unsafe_or_ood_count": 38
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 38,
    "accepted_batch_rate": 0.31932773109243695,
    "accepted_batch_roi": 3.4119277786693076,
    "accepted_batch_roi_ci_low": 0.607449381373161,
    "accepted_batch_roi_positive_count": 38,
    "accepted_reason_counts": {
      "high_priority": 38
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 1,
      "high_priority": 38,
      "knn_delay_fraction_delay_queue": 1,
      "no_candidate_high_priority_delay_queue": 79
    },
    "delay_count": 81,
    "delay_label_count": 118,
    "delay_rate": 0.680672268907563,
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
    "knn_unsafe_count": 62,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.90818706741616,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 68
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
    "safe_precision_ci_low_met": true,
    "safe_precision_met": true
  }
}
```

## 边界

- 本审计只验证 offline admission safety shell，不证明 5/10 no-regression；
- kNN/OOD 只能把 true-RC negative 延迟到 DELAY_QUEUE，不能永久丢弃；
- kNN/OOD no-column / no-safe 不能产生 `CERTIFIED_NO_NEGATIVE`；
- final certificate 仍必须来自 exact pricing full closure。
