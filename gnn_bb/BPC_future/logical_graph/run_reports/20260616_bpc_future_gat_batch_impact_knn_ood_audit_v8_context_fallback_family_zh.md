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
validation_row_count = 98
train_label_counts = {'delay_queue': 47, 'high_priority': 175}
validation_label_counts = {'delay_queue': 20, 'high_priority': 78}
batch_threshold = 0.0
candidate_threshold = 0.4662156403064728
threshold_grouping = family
decision_scope = validation
decision_record_count = 98
validation_metrics = {'total': 98, 'coverage_non_ood_count': 96, 'coverage': 0.9795918367346939, 'ood_count': 2, 'ood_rate': 0.02040816326530612, 'delay_count': 80, 'delay_rate': 0.8163265306122449, 'accepted_batch_count': 18, 'accepted_batch_rate': 0.1836734693877551, 'accepted_batch_roi_positive_count': 18, 'accepted_batch_roi': 0.43031982746389175, 'accepted_batch_roi_ci_low': 0.30512991782027354, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8241154494176252, 'unsafe_label_count': 20, 'knn_unsafe_count': 54, 'unsafe_or_ood_count': 60, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 77, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'family_delay_fallback_delay_queue': 52, 'high_priority': 18, 'knn_delay_fraction_delay_queue': 16, 'no_candidate_high_priority_delay_queue': 11, 'ood_radius_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 18}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': ['greedy-anchor', 'random-wave'], 'missing_accepted_opportunity_families': ['random-wave'], 'family_specific_delay_fallback_families': ['greedy-anchor'], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 14, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 4, 'knn_unsafe_count': 9, 'unsafe_or_ood_count': 9, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'family_delay_fallback_delay_queue': 14}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 38, 'coverage_non_ood_count': 38, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 38, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 9, 'knn_unsafe_count': 21, 'unsafe_or_ood_count': 23, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'family_delay_fallback_delay_queue': 38}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 3, 'max_accepted_batch_roi_label': 1.1059776544570923}, 'sector-wave': {'total': 46, 'coverage_non_ood_count': 44, 'coverage': 0.9565217391304348, 'ood_count': 2, 'ood_rate': 0.043478260869565216, 'delay_count': 28, 'delay_rate': 0.6086956521739131, 'accepted_batch_count': 18, 'accepted_batch_rate': 0.391304347826087, 'accepted_batch_roi_positive_count': 18, 'accepted_batch_roi': 0.43031982746389175, 'accepted_batch_roi_ci_low': 0.30512991782027354, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8241154494176252, 'unsafe_label_count': 7, 'knn_unsafe_count': 24, 'unsafe_or_ood_count': 28, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 36, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'high_priority': 18, 'knn_delay_fraction_delay_queue': 16, 'no_candidate_high_priority_delay_queue': 11, 'ood_radius_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 18}, 'oracle_high_roi_count': 22, 'max_accepted_batch_roi_label': 41.31852722167969}}}
validation_safety_checks = {'min_high_priority_met': True, 'safe_precision_met': True, 'safe_precision_ci_low_met': False, 'accepted_batch_count_met': True, 'accepted_batch_rate_met': True, 'accepted_batch_roi_met': False, 'accepted_batch_roi_ci_low_met': False, 'false_high_priority_on_delay_met': True, 'false_safe_rate_met': True, 'coverage_met': True, 'family_holdout_all_high_roi_opportunity_families_accepted': False}
validation_candidate_ready = false
production_block_reasons = ['validation_safe_precision_ci_low_below_min', 'validation_accepted_batch_roi_below_min', 'validation_accepted_batch_roi_ci_low_below_min', 'family_holdout_accepted_batch_missing', 'validation_candidate_not_ready']
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "family_delay_fallback_delay_queue": 52,
    "high_priority": 18,
    "knn_delay_fraction_delay_queue": 16,
    "no_candidate_high_priority_delay_queue": 11,
    "ood_radius_delay_queue": 1
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 18,
    "accepted_batch_rate": 0.1836734693877551,
    "accepted_batch_roi": 0.43031982746389175,
    "accepted_batch_roi_ci_low": 0.30512991782027354,
    "accepted_batch_roi_positive_count": 18,
    "accepted_reason_counts": {
      "high_priority": 18
    },
    "coverage": 0.9795918367346939,
    "coverage_non_ood_count": 96,
    "decision_reason_counts": {
      "family_delay_fallback_delay_queue": 52,
      "high_priority": 18,
      "knn_delay_fraction_delay_queue": 16,
      "no_candidate_high_priority_delay_queue": 11,
      "ood_radius_delay_queue": 1
    },
    "delay_count": 80,
    "delay_label_count": 77,
    "delay_rate": 0.8163265306122449,
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
    "knn_unsafe_count": 54,
    "ood_count": 2,
    "ood_rate": 0.02040816326530612,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8241154494176252,
    "total": 98,
    "unsafe_label_count": 20,
    "unsafe_or_ood_count": 60
  },
  "decision_split_counts": {
    "validation": 98
  },
  "decision_threshold_group_counts": {
    "greedy-anchor": 14,
    "random-wave": 38,
    "sector-wave": 46
  },
  "decision_threshold_scope_counts": {
    "family": 98
  },
  "production_block_reasons": [
    "validation_safe_precision_ci_low_below_min",
    "validation_accepted_batch_roi_below_min",
    "validation_accepted_batch_roi_ci_low_below_min",
    "family_holdout_accepted_batch_missing",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.0,
      "batch_thresholds_by_family": {},
      "candidate_threshold": 0.4662156403064728,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [
        "greedy-anchor",
        "random-wave"
      ],
      "group": "global",
      "label_counts": {
        "delay_queue": 47,
        "high_priority": 175
      },
      "safe_radius": 9.672298380131055,
      "scope": "global",
      "train_count": 222
    },
    "groups": {
      "greedy-anchor": {
        "batch_threshold": 0.0,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.4662156403064728,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [
          "greedy-anchor",
          "random-wave"
        ],
        "group": "greedy-anchor",
        "label_counts": {
          "delay_queue": 14,
          "high_priority": 26
        },
        "safe_radius": 5.069668343595483,
        "scope": "family",
        "train_count": 40
      },
      "random-wave": {
        "batch_threshold": 0.0,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.4662156403064728,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [
          "greedy-anchor",
          "random-wave"
        ],
        "group": "random-wave",
        "label_counts": {
          "delay_queue": 28,
          "high_priority": 127
        },
        "safe_radius": 9.672298380131055,
        "scope": "family",
        "train_count": 155
      },
      "sector-wave": {
        "batch_threshold": 0.0,
        "batch_thresholds_by_family": {},
        "candidate_threshold": 0.4662156403064728,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [
          "greedy-anchor",
          "random-wave"
        ],
        "group": "sector-wave",
        "label_counts": {
          "delay_queue": 5,
          "high_priority": 22
        },
        "safe_radius": 6.230188395436468,
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
      "greedy-anchor",
      "random-wave"
    ],
    "missing_accepted_opportunity_families": [
      "random-wave"
    ],
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
          "family_delay_fallback_delay_queue": 14
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
        "knn_unsafe_count": 9,
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
        "accepted_batch_count": 0,
        "accepted_batch_rate": 0.0,
        "accepted_batch_roi": null,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 0,
        "accepted_reason_counts": {},
        "coverage": 1.0,
        "coverage_non_ood_count": 38,
        "decision_reason_counts": {
          "family_delay_fallback_delay_queue": 38
        },
        "delay_count": 38,
        "delay_label_count": 17,
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
        "knn_unsafe_count": 21,
        "max_accepted_batch_roi_label": 1.1059776544570923,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 3,
        "safe_precision": null,
        "safe_precision_ci_low": null,
        "total": 38,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 23
      },
      "sector-wave": {
        "accepted_batch_count": 18,
        "accepted_batch_rate": 0.391304347826087,
        "accepted_batch_roi": 0.43031982746389175,
        "accepted_batch_roi_ci_low": 0.30512991782027354,
        "accepted_batch_roi_positive_count": 18,
        "accepted_reason_counts": {
          "high_priority": 18
        },
        "coverage": 0.9565217391304348,
        "coverage_non_ood_count": 44,
        "decision_reason_counts": {
          "high_priority": 18,
          "knn_delay_fraction_delay_queue": 16,
          "no_candidate_high_priority_delay_queue": 11,
          "ood_radius_delay_queue": 1
        },
        "delay_count": 28,
        "delay_label_count": 36,
        "delay_rate": 0.6086956521739131,
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
        "knn_unsafe_count": 24,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 2,
        "ood_rate": 0.043478260869565216,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.8241154494176252,
        "total": 46,
        "unsafe_label_count": 7,
        "unsafe_or_ood_count": 28
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 18,
    "accepted_batch_rate": 0.1836734693877551,
    "accepted_batch_roi": 0.43031982746389175,
    "accepted_batch_roi_ci_low": 0.30512991782027354,
    "accepted_batch_roi_positive_count": 18,
    "accepted_reason_counts": {
      "high_priority": 18
    },
    "coverage": 0.9795918367346939,
    "coverage_non_ood_count": 96,
    "decision_reason_counts": {
      "family_delay_fallback_delay_queue": 52,
      "high_priority": 18,
      "knn_delay_fraction_delay_queue": 16,
      "no_candidate_high_priority_delay_queue": 11,
      "ood_radius_delay_queue": 1
    },
    "delay_count": 80,
    "delay_label_count": 77,
    "delay_rate": 0.8163265306122449,
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
    "knn_unsafe_count": 54,
    "ood_count": 2,
    "ood_rate": 0.02040816326530612,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8241154494176252,
    "total": 98,
    "unsafe_label_count": 20,
    "unsafe_or_ood_count": 60
  },
  "validation_safety_checks": {
    "accepted_batch_count_met": true,
    "accepted_batch_rate_met": true,
    "accepted_batch_roi_ci_low_met": false,
    "accepted_batch_roi_met": false,
    "coverage_met": true,
    "false_high_priority_on_delay_met": true,
    "false_safe_rate_met": true,
    "family_holdout_all_high_roi_opportunity_families_accepted": false,
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
