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
threshold_grouping = scale
decision_scope = all
decision_record_count = 328
validation_metrics = {'total': 106, 'coverage_non_ood_count': 106, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 83, 'delay_rate': 0.7830188679245284, 'accepted_batch_count': 23, 'accepted_batch_rate': 0.2169811320754717, 'accepted_batch_roi_positive_count': 23, 'accepted_batch_roi': 7.057523978509657, 'accepted_batch_roi_ci_low': 2.1087118375497003, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8568788745827373, 'unsafe_label_count': 22, 'knn_unsafe_count': 44, 'unsafe_or_ood_count': 53, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 79, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 71, 'high_priority': 23, 'knn_delay_fraction_delay_queue': 11, 'no_candidate_high_priority_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 23}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': ['greedy-anchor'], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': ['greedy-anchor'], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 14, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 4, 'knn_unsafe_count': 8, 'unsafe_or_ood_count': 8, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 14}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 44, 'coverage_non_ood_count': 44, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 39, 'delay_rate': 0.8863636363636364, 'accepted_batch_count': 5, 'accepted_batch_rate': 0.11363636363636363, 'accepted_batch_roi_positive_count': 5, 'accepted_batch_roi': 0.3710645424202085, 'accepted_batch_roi_ci_low': -0.00908376499923641, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.565508505247919, 'unsafe_label_count': 9, 'knn_unsafe_count': 15, 'unsafe_or_ood_count': 22, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 36, 'high_priority': 5, 'knn_delay_fraction_delay_queue': 3}, 'accepted_reason_counts': {'high_priority': 5}, 'oracle_high_roi_count': 6, 'max_accepted_batch_roi_label': 4.385624885559082}, 'sector-wave': {'total': 48, 'coverage_non_ood_count': 48, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 30, 'delay_rate': 0.625, 'accepted_batch_count': 18, 'accepted_batch_rate': 0.375, 'accepted_batch_roi_positive_count': 18, 'accepted_batch_roi': 8.914873821867836, 'accepted_batch_roi_ci_low': 2.8401448655117525, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8241154494176252, 'unsafe_label_count': 9, 'knn_unsafe_count': 21, 'unsafe_or_ood_count': 23, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 38, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 21, 'high_priority': 18, 'knn_delay_fraction_delay_queue': 8, 'no_candidate_high_priority_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 18}, 'oracle_high_roi_count': 22, 'max_accepted_batch_roi_label': 41.31852722167969}}}
validation_safety_checks = {'min_high_priority_met': True, 'safe_precision_met': True, 'safe_precision_ci_low_met': True, 'accepted_batch_count_met': True, 'accepted_batch_rate_met': True, 'accepted_batch_roi_met': True, 'accepted_batch_roi_ci_low_met': True, 'false_high_priority_on_delay_met': True, 'false_safe_rate_met': True, 'coverage_met': True, 'family_holdout_all_high_roi_opportunity_families_accepted': True}
validation_candidate_ready = true
production_block_reasons = []
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
    "high_priority": 56,
    "knn_delay_fraction_delay_queue": 13,
    "no_candidate_high_priority_delay_queue": 1
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 56,
    "accepted_batch_rate": 0.17073170731707318,
    "accepted_batch_roi": 4.388821013554532,
    "accepted_batch_roi_ci_low": 1.9554472890162349,
    "accepted_batch_roi_positive_count": 56,
    "accepted_reason_counts": {
      "high_priority": 56
    },
    "coverage": 0.9878048780487805,
    "coverage_non_ood_count": 324,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 258,
      "high_priority": 56,
      "knn_delay_fraction_delay_queue": 13,
      "no_candidate_high_priority_delay_queue": 1
    },
    "delay_count": 272,
    "delay_label_count": 324,
    "delay_rate": 0.8292682926829268,
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
    "knn_unsafe_count": 124,
    "ood_count": 4,
    "ood_rate": 0.012195121951219513,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9358038555118847,
    "total": 328,
    "unsafe_label_count": 69,
    "unsafe_or_ood_count": 133
  },
  "decision_split_counts": {
    "train": 222,
    "validation": 106
  },
  "decision_threshold_group_counts": {
    "010": 8,
    "020": 146,
    "030": 76,
    "050": 95,
    "global": 3
  },
  "decision_threshold_scope_counts": {
    "global": 3,
    "scale": 325
  },
  "production_block_reasons": [],
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
      "010": {
        "batch_threshold": 0.48810529708862305,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.43579602241516113,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "010",
        "label_counts": {
          "delay_queue": 5,
          "high_priority": 3
        },
        "safe_radius": 5.625337395112799,
        "scope": "scale",
        "train_count": 8
      },
      "020": {
        "batch_threshold": 0.48810529708862305,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.43579602241516113,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020",
        "label_counts": {
          "delay_queue": 17,
          "high_priority": 67
        },
        "safe_radius": 18.522371188168737,
        "scope": "scale",
        "train_count": 84
      },
      "030": {
        "batch_threshold": 0.48810529708862305,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.43579602241516113,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "030",
        "label_counts": {
          "delay_queue": 8,
          "high_priority": 51
        },
        "safe_radius": 14.122759848529087,
        "scope": "scale",
        "train_count": 59
      },
      "050": {
        "batch_threshold": 0.48810529708862305,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.43579602241516113,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "050",
        "label_counts": {
          "delay_queue": 15,
          "high_priority": 53
        },
        "safe_radius": 12.991210192247225,
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
        "knn_unsafe_count": 15,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.565508505247919,
        "total": 44,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 22
      },
      "sector-wave": {
        "accepted_batch_count": 18,
        "accepted_batch_rate": 0.375,
        "accepted_batch_roi": 8.914873821867836,
        "accepted_batch_roi_ci_low": 2.8401448655117525,
        "accepted_batch_roi_positive_count": 18,
        "accepted_reason_counts": {
          "high_priority": 18
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 48,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 21,
          "high_priority": 18,
          "knn_delay_fraction_delay_queue": 8,
          "no_candidate_high_priority_delay_queue": 1
        },
        "delay_count": 30,
        "delay_label_count": 38,
        "delay_rate": 0.625,
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
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.8241154494176252,
        "total": 48,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 23
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 23,
    "accepted_batch_rate": 0.2169811320754717,
    "accepted_batch_roi": 7.057523978509657,
    "accepted_batch_roi_ci_low": 2.1087118375497003,
    "accepted_batch_roi_positive_count": 23,
    "accepted_reason_counts": {
      "high_priority": 23
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 106,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 71,
      "high_priority": 23,
      "knn_delay_fraction_delay_queue": 11,
      "no_candidate_high_priority_delay_queue": 1
    },
    "delay_count": 83,
    "delay_label_count": 79,
    "delay_rate": 0.7830188679245284,
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
    "knn_unsafe_count": 44,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8568788745827373,
    "total": 106,
    "unsafe_label_count": 22,
    "unsafe_or_ood_count": 53
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
