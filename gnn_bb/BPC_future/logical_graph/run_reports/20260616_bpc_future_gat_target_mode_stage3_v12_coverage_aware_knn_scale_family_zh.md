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
validation_row_count = 102
train_label_counts = {'delay_queue': 47, 'high_priority': 175}
validation_label_counts = {'delay_queue': 20, 'high_priority': 82}
batch_threshold = 0.5210162401199341
candidate_threshold = 0.5344150066375732
threshold_grouping = scale_family
decision_scope = validation
decision_record_count = 102
validation_metrics = {'total': 102, 'coverage_non_ood_count': 93, 'coverage': 0.9117647058823529, 'ood_count': 9, 'ood_rate': 0.08823529411764706, 'delay_count': 96, 'delay_rate': 0.9411764705882353, 'accepted_batch_count': 6, 'accepted_batch_rate': 0.058823529411764705, 'accepted_batch_roi_positive_count': 6, 'accepted_batch_roi': 1.3204368948936462, 'accepted_batch_roi_ci_low': 0.09419327958600476, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.6096569663469354, 'unsafe_label_count': 20, 'knn_unsafe_count': 29, 'unsafe_or_ood_count': 44, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 77, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 79, 'high_priority': 6, 'knn_delay_fraction_delay_queue': 14, 'no_candidate_high_priority_delay_queue': 1, 'ood_radius_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 6}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': ['greedy-anchor'], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': ['greedy-anchor'], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 13, 'coverage': 0.9285714285714286, 'ood_count': 1, 'ood_rate': 0.07142857142857142, 'delay_count': 14, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 4, 'knn_unsafe_count': 2, 'unsafe_or_ood_count': 4, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 14}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 42, 'coverage_non_ood_count': 42, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 37, 'delay_rate': 0.8809523809523809, 'accepted_batch_count': 5, 'accepted_batch_rate': 0.11904761904761904, 'accepted_batch_roi_positive_count': 5, 'accepted_batch_roi': 1.4226340055465698, 'accepted_batch_roi_ci_low': -0.05902930412701113, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.565508505247919, 'unsafe_label_count': 9, 'knn_unsafe_count': 4, 'unsafe_or_ood_count': 12, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 37, 'high_priority': 5}, 'accepted_reason_counts': {'high_priority': 5}, 'oracle_high_roi_count': 5, 'max_accepted_batch_roi_label': 4.385624885559082}, 'sector-wave': {'total': 46, 'coverage_non_ood_count': 38, 'coverage': 0.8260869565217391, 'ood_count': 8, 'ood_rate': 0.17391304347826086, 'delay_count': 45, 'delay_rate': 0.9782608695652174, 'accepted_batch_count': 1, 'accepted_batch_rate': 0.021739130434782608, 'accepted_batch_roi_positive_count': 1, 'accepted_batch_roi': 0.8094513416290283, 'accepted_batch_roi_ci_low': None, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.20654329147389294, 'unsafe_label_count': 7, 'knn_unsafe_count': 23, 'unsafe_or_ood_count': 28, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 36, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 28, 'high_priority': 1, 'knn_delay_fraction_delay_queue': 14, 'no_candidate_high_priority_delay_queue': 1, 'ood_radius_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 1}, 'oracle_high_roi_count': 22, 'max_accepted_batch_roi_label': 41.31852722167969}}}
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
    "below_batch_threshold_delay_queue": 79,
    "high_priority": 6,
    "knn_delay_fraction_delay_queue": 14,
    "no_candidate_high_priority_delay_queue": 1,
    "ood_radius_delay_queue": 2
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 6,
    "accepted_batch_rate": 0.058823529411764705,
    "accepted_batch_roi": 1.3204368948936462,
    "accepted_batch_roi_ci_low": 0.09419327958600476,
    "accepted_batch_roi_positive_count": 6,
    "accepted_reason_counts": {
      "high_priority": 6
    },
    "coverage": 0.9117647058823529,
    "coverage_non_ood_count": 93,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 79,
      "high_priority": 6,
      "knn_delay_fraction_delay_queue": 14,
      "no_candidate_high_priority_delay_queue": 1,
      "ood_radius_delay_queue": 2
    },
    "delay_count": 96,
    "delay_label_count": 77,
    "delay_rate": 0.9411764705882353,
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
    "knn_unsafe_count": 29,
    "ood_count": 9,
    "ood_rate": 0.08823529411764706,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.6096569663469354,
    "total": 102,
    "unsafe_label_count": 20,
    "unsafe_or_ood_count": 44
  },
  "decision_split_counts": {
    "validation": 102
  },
  "decision_threshold_group_counts": {
    "020|greedy-anchor": 14,
    "020|sector-wave": 46,
    "030|random-wave": 17,
    "050|random-wave": 25
  },
  "decision_threshold_scope_counts": {
    "scale_family": 102
  },
  "production_block_reasons": [
    "validation_safe_precision_ci_low_below_min",
    "validation_accepted_batch_roi_ci_low_below_min",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.5210162401199341,
      "batch_thresholds_by_family": {},
      "candidate_threshold": 0.5344150066375732,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 47,
        "high_priority": 175
      },
      "safe_radius": 11.49708205185682,
      "scope": "global",
      "train_count": 222
    },
    "groups": {
      "010|greedy-anchor": {
        "batch_threshold": 0.5210162401199341,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.5344150066375732,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "010|greedy-anchor",
        "label_counts": {
          "delay_queue": 5,
          "high_priority": 3
        },
        "safe_radius": 5.790726407680484,
        "scope": "scale_family",
        "train_count": 8
      },
      "020|greedy-anchor": {
        "batch_threshold": 0.5210162401199341,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.5344150066375732,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020|greedy-anchor",
        "label_counts": {
          "delay_queue": 7,
          "high_priority": 23
        },
        "safe_radius": 5.445102359314099,
        "scope": "scale_family",
        "train_count": 30
      },
      "020|random-wave": {
        "batch_threshold": 0.5210162401199341,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.5344150066375732,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020|random-wave",
        "label_counts": {
          "delay_queue": 5,
          "high_priority": 22
        },
        "safe_radius": 18.746443946866588,
        "scope": "scale_family",
        "train_count": 27
      },
      "020|sector-wave": {
        "batch_threshold": 0.5210162401199341,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.5344150066375732,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020|sector-wave",
        "label_counts": {
          "delay_queue": 5,
          "high_priority": 22
        },
        "safe_radius": 6.414398807586493,
        "scope": "scale_family",
        "train_count": 27
      },
      "030|random-wave": {
        "batch_threshold": 0.5210162401199341,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.5344150066375732,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "030|random-wave",
        "label_counts": {
          "delay_queue": 8,
          "high_priority": 51
        },
        "safe_radius": 14.286153682403402,
        "scope": "scale_family",
        "train_count": 59
      },
      "050|random-wave": {
        "batch_threshold": 0.5210162401199341,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.5344150066375732,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "050|random-wave",
        "label_counts": {
          "delay_queue": 15,
          "high_priority": 53
        },
        "safe_radius": 13.290242272834485,
        "scope": "scale_family",
        "train_count": 68
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
        "coverage": 0.9285714285714286,
        "coverage_non_ood_count": 13,
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
        "false_safe_rate_ood": 0.0,
        "false_safe_rate_union": 0.0,
        "false_safe_union_count": 0,
        "knn_unsafe_count": 2,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "ood_count": 1,
        "ood_rate": 0.07142857142857142,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "safe_precision_ci_low": null,
        "total": 14,
        "unsafe_label_count": 4,
        "unsafe_or_ood_count": 4
      },
      "random-wave": {
        "accepted_batch_count": 5,
        "accepted_batch_rate": 0.11904761904761904,
        "accepted_batch_roi": 1.4226340055465698,
        "accepted_batch_roi_ci_low": -0.05902930412701113,
        "accepted_batch_roi_positive_count": 5,
        "accepted_reason_counts": {
          "high_priority": 5
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 42,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 37,
          "high_priority": 5
        },
        "delay_count": 37,
        "delay_label_count": 17,
        "delay_rate": 0.8809523809523809,
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
        "knn_unsafe_count": 4,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 5,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.565508505247919,
        "total": 42,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 12
      },
      "sector-wave": {
        "accepted_batch_count": 1,
        "accepted_batch_rate": 0.021739130434782608,
        "accepted_batch_roi": 0.8094513416290283,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 1,
        "accepted_reason_counts": {
          "high_priority": 1
        },
        "coverage": 0.8260869565217391,
        "coverage_non_ood_count": 38,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 28,
          "high_priority": 1,
          "knn_delay_fraction_delay_queue": 14,
          "no_candidate_high_priority_delay_queue": 1,
          "ood_radius_delay_queue": 2
        },
        "delay_count": 45,
        "delay_label_count": 36,
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
        "knn_unsafe_count": 23,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 8,
        "ood_rate": 0.17391304347826086,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.20654329147389294,
        "total": 46,
        "unsafe_label_count": 7,
        "unsafe_or_ood_count": 28
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 6,
    "accepted_batch_rate": 0.058823529411764705,
    "accepted_batch_roi": 1.3204368948936462,
    "accepted_batch_roi_ci_low": 0.09419327958600476,
    "accepted_batch_roi_positive_count": 6,
    "accepted_reason_counts": {
      "high_priority": 6
    },
    "coverage": 0.9117647058823529,
    "coverage_non_ood_count": 93,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 79,
      "high_priority": 6,
      "knn_delay_fraction_delay_queue": 14,
      "no_candidate_high_priority_delay_queue": 1,
      "ood_radius_delay_queue": 2
    },
    "delay_count": 96,
    "delay_label_count": 77,
    "delay_rate": 0.9411764705882353,
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
    "knn_unsafe_count": 29,
    "ood_count": 9,
    "ood_rate": 0.08823529411764706,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.6096569663469354,
    "total": 102,
    "unsafe_label_count": 20,
    "unsafe_or_ood_count": 44
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
