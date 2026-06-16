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
train_row_count = 256
validation_row_count = 119
train_label_counts = {'delay_queue': 68, 'high_priority': 188}
validation_label_counts = {'delay_queue': 33, 'high_priority': 86}
batch_threshold = 0.0
candidate_threshold = 0.35319826006889343
threshold_grouping = global
decision_scope = validation
decision_record_count = 119
validation_metrics = {'total': 119, 'coverage_non_ood_count': 119, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 97, 'delay_rate': 0.8151260504201681, 'accepted_batch_count': 22, 'accepted_batch_rate': 0.18487394957983194, 'accepted_batch_roi_positive_count': 22, 'accepted_batch_roi': 2.2334176454835624, 'accepted_batch_roi_ci_low': -0.3230884780601899, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8513404742740388, 'unsafe_label_count': 33, 'knn_unsafe_count': 75, 'unsafe_or_ood_count': 77, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 118, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 9, 'high_priority': 22, 'knn_delay_fraction_delay_queue': 14, 'no_candidate_high_priority_delay_queue': 74}, 'accepted_reason_counts': {'high_priority': 22}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 10, 'delay_rate': 0.7142857142857143, 'accepted_batch_count': 4, 'accepted_batch_rate': 0.2857142857142857, 'accepted_batch_roi_positive_count': 4, 'accepted_batch_roi': 0.12922756214084075, 'accepted_batch_roi_ci_low': -0.05243782835954422, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.5100999795960008, 'unsafe_label_count': 4, 'knn_unsafe_count': 6, 'unsafe_or_ood_count': 8, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'high_priority': 4, 'no_candidate_high_priority_delay_queue': 10}, 'accepted_reason_counts': {'high_priority': 4}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 44, 'coverage_non_ood_count': 44, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 41, 'delay_rate': 0.9318181818181818, 'accepted_batch_count': 3, 'accepted_batch_rate': 0.06818181818181818, 'accepted_batch_roi_positive_count': 3, 'accepted_batch_roi': 0.43123657008012134, 'accepted_batch_roi_ci_low': -0.2311734636415797, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.4384939195509822, 'unsafe_label_count': 9, 'knn_unsafe_count': 27, 'unsafe_or_ood_count': 27, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'high_priority': 3, 'no_candidate_high_priority_delay_queue': 41}, 'accepted_reason_counts': {'high_priority': 3}, 'oracle_high_roi_count': 6, 'max_accepted_batch_roi_label': 4.385624885559082}, 'sector-wave': {'total': 61, 'coverage_non_ood_count': 61, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 46, 'delay_rate': 0.7540983606557377, 'accepted_batch_count': 15, 'accepted_batch_rate': 0.2459016393442623, 'accepted_batch_roi_positive_count': 15, 'accepted_batch_roi': 3.1549712161223096, 'accepted_batch_roi_ci_low': -0.5367636350871496, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7961107336956521, 'unsafe_label_count': 20, 'knn_unsafe_count': 42, 'unsafe_or_ood_count': 42, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 77, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 9, 'high_priority': 15, 'knn_delay_fraction_delay_queue': 14, 'no_candidate_high_priority_delay_queue': 23}, 'accepted_reason_counts': {'high_priority': 15}, 'oracle_high_roi_count': 24, 'max_accepted_batch_roi_label': 41.31852722167969}}}
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
    "candidate_false_high_priority_delay_queue": 9,
    "high_priority": 22,
    "knn_delay_fraction_delay_queue": 14,
    "no_candidate_high_priority_delay_queue": 74
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 22,
    "accepted_batch_rate": 0.18487394957983194,
    "accepted_batch_roi": 2.2334176454835624,
    "accepted_batch_roi_ci_low": -0.3230884780601899,
    "accepted_batch_roi_positive_count": 22,
    "accepted_reason_counts": {
      "high_priority": 22
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 9,
      "high_priority": 22,
      "knn_delay_fraction_delay_queue": 14,
      "no_candidate_high_priority_delay_queue": 74
    },
    "delay_count": 97,
    "delay_label_count": 118,
    "delay_rate": 0.8151260504201681,
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
    "knn_unsafe_count": 75,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8513404742740388,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 77
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
      "candidate_threshold": 0.35319826006889343,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 68,
        "high_priority": 188
      },
      "safe_radius": 4.015931834017404,
      "scope": "global",
      "train_count": 256
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
        "accepted_batch_count": 4,
        "accepted_batch_rate": 0.2857142857142857,
        "accepted_batch_roi": 0.12922756214084075,
        "accepted_batch_roi_ci_low": -0.05243782835954422,
        "accepted_batch_roi_positive_count": 4,
        "accepted_reason_counts": {
          "high_priority": 4
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 14,
        "decision_reason_counts": {
          "high_priority": 4,
          "no_candidate_high_priority_delay_queue": 10
        },
        "delay_count": 10,
        "delay_label_count": 24,
        "delay_rate": 0.7142857142857143,
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
        "knn_unsafe_count": 6,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.5100999795960008,
        "total": 14,
        "unsafe_label_count": 4,
        "unsafe_or_ood_count": 8
      },
      "random-wave": {
        "accepted_batch_count": 3,
        "accepted_batch_rate": 0.06818181818181818,
        "accepted_batch_roi": 0.43123657008012134,
        "accepted_batch_roi_ci_low": -0.2311734636415797,
        "accepted_batch_roi_positive_count": 3,
        "accepted_reason_counts": {
          "high_priority": 3
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 44,
        "decision_reason_counts": {
          "high_priority": 3,
          "no_candidate_high_priority_delay_queue": 41
        },
        "delay_count": 41,
        "delay_label_count": 17,
        "delay_rate": 0.9318181818181818,
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
        "knn_unsafe_count": 27,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.4384939195509822,
        "total": 44,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 27
      },
      "sector-wave": {
        "accepted_batch_count": 15,
        "accepted_batch_rate": 0.2459016393442623,
        "accepted_batch_roi": 3.1549712161223096,
        "accepted_batch_roi_ci_low": -0.5367636350871496,
        "accepted_batch_roi_positive_count": 15,
        "accepted_reason_counts": {
          "high_priority": 15
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 61,
        "decision_reason_counts": {
          "candidate_false_high_priority_delay_queue": 9,
          "high_priority": 15,
          "knn_delay_fraction_delay_queue": 14,
          "no_candidate_high_priority_delay_queue": 23
        },
        "delay_count": 46,
        "delay_label_count": 77,
        "delay_rate": 0.7540983606557377,
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
        "knn_unsafe_count": 42,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7961107336956521,
        "total": 61,
        "unsafe_label_count": 20,
        "unsafe_or_ood_count": 42
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 22,
    "accepted_batch_rate": 0.18487394957983194,
    "accepted_batch_roi": 2.2334176454835624,
    "accepted_batch_roi_ci_low": -0.3230884780601899,
    "accepted_batch_roi_positive_count": 22,
    "accepted_reason_counts": {
      "high_priority": 22
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 9,
      "high_priority": 22,
      "knn_delay_fraction_delay_queue": 14,
      "no_candidate_high_priority_delay_queue": 74
    },
    "delay_count": 97,
    "delay_label_count": 118,
    "delay_rate": 0.8151260504201681,
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
    "knn_unsafe_count": 75,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8513404742740388,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 77
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
