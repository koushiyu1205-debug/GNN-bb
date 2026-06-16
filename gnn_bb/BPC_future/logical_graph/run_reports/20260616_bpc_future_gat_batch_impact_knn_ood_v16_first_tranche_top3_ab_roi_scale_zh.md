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
validation_row_count = 119
train_label_counts = {'delay_queue': 47, 'high_priority': 175}
validation_label_counts = {'delay_queue': 33, 'high_priority': 86}
batch_threshold = 0.0
candidate_threshold = 0.85
threshold_grouping = scale
decision_scope = validation
decision_record_count = 119
validation_metrics = {'total': 119, 'coverage_non_ood_count': 119, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 110, 'delay_rate': 0.9243697478991597, 'accepted_batch_count': 9, 'accepted_batch_rate': 0.07563025210084033, 'accepted_batch_roi_positive_count': 9, 'accepted_batch_roi': 11.456397010220421, 'accepted_batch_roi_ci_low': 1.0586008970415683, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7008472464490406, 'unsafe_label_count': 33, 'knn_unsafe_count': 54, 'unsafe_or_ood_count': 66, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 118, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 1, 'high_priority': 9, 'knn_delay_fraction_delay_queue': 3, 'no_candidate_high_priority_delay_queue': 106}, 'accepted_reason_counts': {'high_priority': 9}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': ['greedy-anchor'], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': ['greedy-anchor'], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 14, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 4, 'knn_unsafe_count': 7, 'unsafe_or_ood_count': 8, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'no_candidate_high_priority_delay_queue': 14}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 44, 'coverage_non_ood_count': 44, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 43, 'delay_rate': 0.9772727272727273, 'accepted_batch_count': 1, 'accepted_batch_rate': 0.022727272727272728, 'accepted_batch_roi_positive_count': 1, 'accepted_batch_roi': 1.1059776544570923, 'accepted_batch_roi_ci_low': None, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.20654329147389294, 'unsafe_label_count': 9, 'knn_unsafe_count': 16, 'unsafe_or_ood_count': 22, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'high_priority': 1, 'no_candidate_high_priority_delay_queue': 43}, 'accepted_reason_counts': {'high_priority': 1}, 'oracle_high_roi_count': 6, 'max_accepted_batch_roi_label': 4.385624885559082}, 'sector-wave': {'total': 61, 'coverage_non_ood_count': 61, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 53, 'delay_rate': 0.8688524590163934, 'accepted_batch_count': 8, 'accepted_batch_rate': 0.13114754098360656, 'accepted_batch_roi_positive_count': 8, 'accepted_batch_roi': 12.750199429690838, 'accepted_batch_roi_ci_low': 1.3162116618136253, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.6755843804891231, 'unsafe_label_count': 20, 'knn_unsafe_count': 31, 'unsafe_or_ood_count': 36, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 77, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 1, 'high_priority': 8, 'knn_delay_fraction_delay_queue': 3, 'no_candidate_high_priority_delay_queue': 49}, 'accepted_reason_counts': {'high_priority': 8}, 'oracle_high_roi_count': 24, 'max_accepted_batch_roi_label': 41.31852722167969}}}
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
    "candidate_false_high_priority_delay_queue": 1,
    "high_priority": 9,
    "knn_delay_fraction_delay_queue": 3,
    "no_candidate_high_priority_delay_queue": 106
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 9,
    "accepted_batch_rate": 0.07563025210084033,
    "accepted_batch_roi": 11.456397010220421,
    "accepted_batch_roi_ci_low": 1.0586008970415683,
    "accepted_batch_roi_positive_count": 9,
    "accepted_reason_counts": {
      "high_priority": 9
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 1,
      "high_priority": 9,
      "knn_delay_fraction_delay_queue": 3,
      "no_candidate_high_priority_delay_queue": 106
    },
    "delay_count": 110,
    "delay_label_count": 118,
    "delay_rate": 0.9243697478991597,
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
    "knn_unsafe_count": 54,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.7008472464490406,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 66
  },
  "decision_split_counts": {
    "validation": 119
  },
  "decision_threshold_group_counts": {
    "020": 75,
    "030": 17,
    "050": 27
  },
  "decision_threshold_scope_counts": {
    "scale": 119
  },
  "production_block_reasons": [
    "validation_safe_precision_ci_low_below_min",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.0,
      "batch_thresholds_by_family": {},
      "candidate_threshold": 0.85,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 47,
        "high_priority": 175
      },
      "safe_radius": 12.065425978778217,
      "scope": "global",
      "train_count": 222
    },
    "groups": {
      "010": {
        "batch_threshold": 0.0,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.85,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "010",
        "label_counts": {
          "delay_queue": 5,
          "high_priority": 3
        },
        "safe_radius": 5.771605427505818,
        "scope": "scale",
        "train_count": 8
      },
      "020": {
        "batch_threshold": 0.0,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.85,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020",
        "label_counts": {
          "delay_queue": 17,
          "high_priority": 67
        },
        "safe_radius": 18.593455026048844,
        "scope": "scale",
        "train_count": 84
      },
      "030": {
        "batch_threshold": 0.0,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.85,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "030",
        "label_counts": {
          "delay_queue": 8,
          "high_priority": 51
        },
        "safe_radius": 13.865383632871362,
        "scope": "scale",
        "train_count": 59
      },
      "050": {
        "batch_threshold": 0.0,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.85,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "050",
        "label_counts": {
          "delay_queue": 15,
          "high_priority": 53
        },
        "safe_radius": 13.135793186635103,
        "scope": "scale",
        "train_count": 68
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
          "no_candidate_high_priority_delay_queue": 14
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
        "unsafe_or_ood_count": 8
      },
      "random-wave": {
        "accepted_batch_count": 1,
        "accepted_batch_rate": 0.022727272727272728,
        "accepted_batch_roi": 1.1059776544570923,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 1,
        "accepted_reason_counts": {
          "high_priority": 1
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 44,
        "decision_reason_counts": {
          "high_priority": 1,
          "no_candidate_high_priority_delay_queue": 43
        },
        "delay_count": 43,
        "delay_label_count": 17,
        "delay_rate": 0.9772727272727273,
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
        "knn_unsafe_count": 16,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.20654329147389294,
        "total": 44,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 22
      },
      "sector-wave": {
        "accepted_batch_count": 8,
        "accepted_batch_rate": 0.13114754098360656,
        "accepted_batch_roi": 12.750199429690838,
        "accepted_batch_roi_ci_low": 1.3162116618136253,
        "accepted_batch_roi_positive_count": 8,
        "accepted_reason_counts": {
          "high_priority": 8
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 61,
        "decision_reason_counts": {
          "candidate_false_high_priority_delay_queue": 1,
          "high_priority": 8,
          "knn_delay_fraction_delay_queue": 3,
          "no_candidate_high_priority_delay_queue": 49
        },
        "delay_count": 53,
        "delay_label_count": 77,
        "delay_rate": 0.8688524590163934,
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
        "knn_unsafe_count": 31,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.6755843804891231,
        "total": 61,
        "unsafe_label_count": 20,
        "unsafe_or_ood_count": 36
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 9,
    "accepted_batch_rate": 0.07563025210084033,
    "accepted_batch_roi": 11.456397010220421,
    "accepted_batch_roi_ci_low": 1.0586008970415683,
    "accepted_batch_roi_positive_count": 9,
    "accepted_reason_counts": {
      "high_priority": 9
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 1,
      "high_priority": 9,
      "knn_delay_fraction_delay_queue": 3,
      "no_candidate_high_priority_delay_queue": 106
    },
    "delay_count": 110,
    "delay_label_count": 118,
    "delay_rate": 0.9243697478991597,
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
    "knn_unsafe_count": 54,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.7008472464490406,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 66
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
