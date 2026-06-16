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
validation_row_count = 106
train_label_counts = {'delay_queue': 47, 'high_priority': 175}
validation_label_counts = {'delay_queue': 22, 'high_priority': 84}
batch_threshold = 0.48810529708862305
candidate_threshold = 0.43579602241516113
threshold_grouping = family
decision_scope = all
decision_record_count = 328
validation_metrics = {'total': 106, 'coverage_non_ood_count': 97, 'coverage': 0.9150943396226415, 'ood_count': 9, 'ood_rate': 0.08490566037735849, 'delay_count': 92, 'delay_rate': 0.8679245283018868, 'accepted_batch_count': 14, 'accepted_batch_rate': 0.1320754716981132, 'accepted_batch_roi_positive_count': 14, 'accepted_batch_roi': 0.47220919341115014, 'accepted_batch_roi_ci_low': 0.32354690958853094, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7846829880728186, 'unsafe_label_count': 22, 'knn_unsafe_count': 59, 'unsafe_or_ood_count': 66, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 79, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 71, 'high_priority': 14, 'knn_delay_fraction_delay_queue': 18, 'no_candidate_high_priority_delay_queue': 1, 'ood_radius_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 14}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': ['greedy-anchor'], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': ['greedy-anchor'], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 14, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 4, 'knn_unsafe_count': 8, 'unsafe_or_ood_count': 8, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 14}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 44, 'coverage_non_ood_count': 44, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 39, 'delay_rate': 0.8863636363636364, 'accepted_batch_count': 5, 'accepted_batch_rate': 0.11363636363636363, 'accepted_batch_roi_positive_count': 5, 'accepted_batch_roi': 0.3710645424202085, 'accepted_batch_roi_ci_low': -0.00908376499923641, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.565508505247919, 'unsafe_label_count': 9, 'knn_unsafe_count': 25, 'unsafe_or_ood_count': 26, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 36, 'high_priority': 5, 'knn_delay_fraction_delay_queue': 3}, 'accepted_reason_counts': {'high_priority': 5}, 'oracle_high_roi_count': 6, 'max_accepted_batch_roi_label': 4.385624885559082}, 'sector-wave': {'total': 48, 'coverage_non_ood_count': 39, 'coverage': 0.8125, 'ood_count': 9, 'ood_rate': 0.1875, 'delay_count': 39, 'delay_rate': 0.8125, 'accepted_batch_count': 9, 'accepted_batch_rate': 0.1875, 'accepted_batch_roi_positive_count': 9, 'accepted_batch_roi': 0.5284006661838956, 'accepted_batch_roi_ci_low': 0.42126879132961276, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7008472464490406, 'unsafe_label_count': 9, 'knn_unsafe_count': 26, 'unsafe_or_ood_count': 32, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 38, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 21, 'high_priority': 9, 'knn_delay_fraction_delay_queue': 15, 'no_candidate_high_priority_delay_queue': 1, 'ood_radius_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 9}, 'oracle_high_roi_count': 22, 'max_accepted_batch_roi_label': 41.31852722167969}}}
validation_safety_checks = {'min_high_priority_met': True, 'safe_precision_met': True, 'safe_precision_ci_low_met': False, 'accepted_batch_count_met': True, 'accepted_batch_rate_met': True, 'accepted_batch_roi_met': False, 'accepted_batch_roi_ci_low_met': False, 'false_high_priority_on_delay_met': True, 'false_safe_rate_met': True, 'coverage_met': True, 'family_holdout_all_high_roi_opportunity_families_accepted': True}
validation_candidate_ready = false
production_block_reasons = ['validation_safe_precision_ci_low_below_min', 'validation_accepted_batch_roi_below_min', 'validation_accepted_batch_roi_ci_low_below_min', 'validation_candidate_not_ready']
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "below_batch_threshold_delay_queue": 258,
    "high_priority": 46,
    "knn_delay_fraction_delay_queue": 21,
    "no_candidate_high_priority_delay_queue": 1,
    "ood_radius_delay_queue": 2
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 46,
    "accepted_batch_rate": 0.1402439024390244,
    "accepted_batch_roi": 1.7861211108975112,
    "accepted_batch_roi_ci_low": 0.2632457698943125,
    "accepted_batch_roi_positive_count": 46,
    "accepted_reason_counts": {
      "high_priority": 46
    },
    "coverage": 0.9725609756097561,
    "coverage_non_ood_count": 319,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 258,
      "high_priority": 46,
      "knn_delay_fraction_delay_queue": 21,
      "no_candidate_high_priority_delay_queue": 1,
      "ood_radius_delay_queue": 2
    },
    "delay_count": 282,
    "delay_label_count": 324,
    "delay_rate": 0.8597560975609756,
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
    "knn_unsafe_count": 142,
    "ood_count": 9,
    "ood_rate": 0.027439024390243903,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9229238226702192,
    "total": 328,
    "unsafe_label_count": 69,
    "unsafe_or_ood_count": 149
  },
  "decision_split_counts": {
    "train": 222,
    "validation": 106
  },
  "decision_threshold_group_counts": {
    "greedy-anchor": 54,
    "random-wave": 199,
    "sector-wave": 75
  },
  "decision_threshold_scope_counts": {
    "family": 328
  },
  "production_block_reasons": [
    "validation_safe_precision_ci_low_below_min",
    "validation_accepted_batch_roi_below_min",
    "validation_accepted_batch_roi_ci_low_below_min",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.48810529708862305,
      "batch_thresholds_by_family": {},
      "candidate_threshold": 0.43579602241516113,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 47,
        "high_priority": 175
      },
      "safe_radius": 12.054692846681657,
      "scope": "global",
      "train_count": 222
    },
    "groups": {
      "greedy-anchor": {
        "batch_threshold": 0.48810529708862305,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.43579602241516113,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "greedy-anchor",
        "label_counts": {
          "delay_queue": 14,
          "high_priority": 26
        },
        "safe_radius": 5.625337395112799,
        "scope": "family",
        "train_count": 40
      },
      "random-wave": {
        "batch_threshold": 0.48810529708862305,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.43579602241516113,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "random-wave",
        "label_counts": {
          "delay_queue": 28,
          "high_priority": 127
        },
        "safe_radius": 12.054692846681657,
        "scope": "family",
        "train_count": 155
      },
      "sector-wave": {
        "batch_threshold": 0.48810529708862305,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.43579602241516113,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "sector-wave",
        "label_counts": {
          "delay_queue": 5,
          "high_priority": 22
        },
        "safe_radius": 6.001310058265435,
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
        "accepted_batch_count": 5,
        "accepted_batch_rate": 0.11363636363636363,
        "accepted_batch_roi": 0.3710645424202085,
        "accepted_batch_roi_ci_low": -0.00908376499923641,
        "accepted_batch_roi_positive_count": 5,
        "accepted_reason_counts": {
          "high_priority": 5
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 44,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 36,
          "high_priority": 5,
          "knn_delay_fraction_delay_queue": 3
        },
        "delay_count": 39,
        "delay_label_count": 17,
        "delay_rate": 0.8863636363636364,
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
        "knn_unsafe_count": 25,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.565508505247919,
        "total": 44,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 26
      },
      "sector-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_rate": 0.1875,
        "accepted_batch_roi": 0.5284006661838956,
        "accepted_batch_roi_ci_low": 0.42126879132961276,
        "accepted_batch_roi_positive_count": 9,
        "accepted_reason_counts": {
          "high_priority": 9
        },
        "coverage": 0.8125,
        "coverage_non_ood_count": 39,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 21,
          "high_priority": 9,
          "knn_delay_fraction_delay_queue": 15,
          "no_candidate_high_priority_delay_queue": 1,
          "ood_radius_delay_queue": 2
        },
        "delay_count": 39,
        "delay_label_count": 38,
        "delay_rate": 0.8125,
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
        "knn_unsafe_count": 26,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 9,
        "ood_rate": 0.1875,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7008472464490406,
        "total": 48,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 32
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 14,
    "accepted_batch_rate": 0.1320754716981132,
    "accepted_batch_roi": 0.47220919341115014,
    "accepted_batch_roi_ci_low": 0.32354690958853094,
    "accepted_batch_roi_positive_count": 14,
    "accepted_reason_counts": {
      "high_priority": 14
    },
    "coverage": 0.9150943396226415,
    "coverage_non_ood_count": 97,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 71,
      "high_priority": 14,
      "knn_delay_fraction_delay_queue": 18,
      "no_candidate_high_priority_delay_queue": 1,
      "ood_radius_delay_queue": 2
    },
    "delay_count": 92,
    "delay_label_count": 79,
    "delay_rate": 0.8679245283018868,
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
    "knn_unsafe_count": 59,
    "ood_count": 9,
    "ood_rate": 0.08490566037735849,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.7846829880728186,
    "total": 106,
    "unsafe_label_count": 22,
    "unsafe_or_ood_count": 66
  },
  "validation_safety_checks": {
    "accepted_batch_count_met": true,
    "accepted_batch_rate_met": true,
    "accepted_batch_roi_ci_low_met": false,
    "accepted_batch_roi_met": false,
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
