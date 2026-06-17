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
candidate_threshold = 0.27313859528943996
candidate_admission_score_mode = risk_adjusted_rescue_window
candidate_delay_score_penalty = 0.75
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.5
candidate_rescue_raw_score_threshold = 0.3
candidate_rescue_delay_risk_threshold = 0.75
candidate_rescue_delay_score_penalty = 0.25
min_neighbor_accepted_batch_roi = None
min_neighbor_accepted_batch_roi_ci_low = 0.65
threshold_grouping = global
decision_scope = validation
decision_record_count = 119
validation_metrics = {'total': 119, 'coverage_non_ood_count': 119, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 119, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 33, 'knn_unsafe_count': 68, 'knn_roi_unsafe_count': 119, 'unsafe_or_ood_count': 72, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 118, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 14, 'knn_delay_fraction_delay_queue': 25, 'knn_roi_ci_low_delay_queue': 44, 'no_candidate_high_priority_delay_queue': 36}, 'accepted_reason_counts': {}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': ['greedy-anchor', 'random-wave', 'sector-wave'], 'missing_accepted_opportunity_families': ['random-wave', 'sector-wave'], 'family_specific_delay_fallback_families': ['greedy-anchor'], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 14, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 4, 'knn_unsafe_count': 6, 'knn_roi_unsafe_count': 14, 'unsafe_or_ood_count': 7, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 1, 'knn_delay_fraction_delay_queue': 1, 'knn_roi_ci_low_delay_queue': 6, 'no_candidate_high_priority_delay_queue': 6}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 44, 'coverage_non_ood_count': 44, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 44, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 9, 'knn_unsafe_count': 23, 'knn_roi_unsafe_count': 44, 'unsafe_or_ood_count': 24, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'knn_delay_fraction_delay_queue': 6, 'knn_roi_ci_low_delay_queue': 18, 'no_candidate_high_priority_delay_queue': 20}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 6, 'max_accepted_batch_roi_label': 4.385624885559082}, 'sector-wave': {'total': 61, 'coverage_non_ood_count': 61, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 61, 'delay_rate': 1.0, 'accepted_batch_count': 0, 'accepted_batch_rate': 0.0, 'accepted_batch_roi_positive_count': 0, 'accepted_batch_roi': None, 'accepted_batch_roi_ci_low': None, 'safe_precision': None, 'safe_precision_ci_low': None, 'unsafe_label_count': 20, 'knn_unsafe_count': 39, 'knn_roi_unsafe_count': 61, 'unsafe_or_ood_count': 41, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 77, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 13, 'knn_delay_fraction_delay_queue': 18, 'knn_roi_ci_low_delay_queue': 20, 'no_candidate_high_priority_delay_queue': 10}, 'accepted_reason_counts': {}, 'oracle_high_roi_count': 24, 'max_accepted_batch_roi_label': 41.31852722167969}}}
validation_safety_checks = {'min_high_priority_met': False, 'safe_precision_met': False, 'safe_precision_ci_low_met': False, 'accepted_batch_count_met': False, 'accepted_batch_rate_met': False, 'accepted_batch_roi_met': False, 'accepted_batch_roi_ci_low_met': False, 'false_high_priority_on_delay_met': True, 'false_safe_rate_met': True, 'coverage_met': True, 'family_holdout_all_high_roi_opportunity_families_accepted': False}
validation_candidate_ready = false
production_block_reasons = ['validation_high_priority_below_min', 'validation_safe_precision_below_min', 'validation_safe_precision_ci_low_below_min', 'validation_accepted_batch_count_below_min', 'validation_accepted_batch_rate_below_min', 'validation_accepted_batch_roi_below_min', 'validation_accepted_batch_roi_ci_low_below_min', 'family_holdout_accepted_batch_missing', 'validation_candidate_not_ready']
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 指标

```json
{
  "decision_reason_counts": {
    "candidate_false_high_priority_delay_queue": 14,
    "knn_delay_fraction_delay_queue": 25,
    "knn_roi_ci_low_delay_queue": 44,
    "no_candidate_high_priority_delay_queue": 36
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 0,
    "accepted_batch_rate": 0.0,
    "accepted_batch_roi": null,
    "accepted_batch_roi_ci_low": null,
    "accepted_batch_roi_positive_count": 0,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": 0.0,
    "accepted_reason_counts": {},
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 14,
      "knn_delay_fraction_delay_queue": 25,
      "knn_roi_ci_low_delay_queue": 44,
      "no_candidate_high_priority_delay_queue": 36
    },
    "delay_count": 119,
    "delay_label_count": 118,
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
    "knn_roi_unsafe_count": 119,
    "knn_unsafe_count": 68,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": null,
    "safe_precision_ci_low": null,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 72
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
    "validation_high_priority_below_min",
    "validation_safe_precision_below_min",
    "validation_safe_precision_ci_low_below_min",
    "validation_accepted_batch_count_below_min",
    "validation_accepted_batch_rate_below_min",
    "validation_accepted_batch_roi_below_min",
    "validation_accepted_batch_roi_ci_low_below_min",
    "family_holdout_accepted_batch_missing",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.0,
      "batch_thresholds_by_family": {},
      "candidate_admission_score_mode": "risk_adjusted_rescue_window",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.5,
      "candidate_delay_score_penalty": 0.75,
      "candidate_rescue_delay_risk_threshold": 0.75,
      "candidate_rescue_delay_score_penalty": 0.25,
      "candidate_rescue_raw_score_threshold": 0.3,
      "candidate_threshold": 0.27313859528943996,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 68,
        "high_priority": 188
      },
      "min_neighbor_accepted_batch_roi": null,
      "min_neighbor_accepted_batch_roi_ci_low": 0.65,
      "safe_radius": 6.355181720131418,
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
    "family_specific_delay_fallback_families": [
      "greedy-anchor"
    ],
    "missing_accepted_families": [
      "greedy-anchor",
      "random-wave",
      "sector-wave"
    ],
    "missing_accepted_opportunity_families": [
      "random-wave",
      "sector-wave"
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
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": 0.0,
        "accepted_reason_counts": {},
        "coverage": 1.0,
        "coverage_non_ood_count": 14,
        "decision_reason_counts": {
          "candidate_false_high_priority_delay_queue": 1,
          "knn_delay_fraction_delay_queue": 1,
          "knn_roi_ci_low_delay_queue": 6,
          "no_candidate_high_priority_delay_queue": 6
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
        "knn_roi_unsafe_count": 14,
        "knn_unsafe_count": 6,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "safe_precision_ci_low": null,
        "total": 14,
        "unsafe_label_count": 4,
        "unsafe_or_ood_count": 7
      },
      "random-wave": {
        "accepted_batch_count": 0,
        "accepted_batch_rate": 0.0,
        "accepted_batch_roi": null,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 0,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": 0.0,
        "accepted_reason_counts": {},
        "coverage": 1.0,
        "coverage_non_ood_count": 44,
        "decision_reason_counts": {
          "knn_delay_fraction_delay_queue": 6,
          "knn_roi_ci_low_delay_queue": 18,
          "no_candidate_high_priority_delay_queue": 20
        },
        "delay_count": 44,
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
        "knn_roi_unsafe_count": 44,
        "knn_unsafe_count": 23,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 6,
        "safe_precision": null,
        "safe_precision_ci_low": null,
        "total": 44,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 24
      },
      "sector-wave": {
        "accepted_batch_count": 0,
        "accepted_batch_rate": 0.0,
        "accepted_batch_roi": null,
        "accepted_batch_roi_ci_low": null,
        "accepted_batch_roi_positive_count": 0,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": 0.0,
        "accepted_reason_counts": {},
        "coverage": 1.0,
        "coverage_non_ood_count": 61,
        "decision_reason_counts": {
          "candidate_false_high_priority_delay_queue": 13,
          "knn_delay_fraction_delay_queue": 18,
          "knn_roi_ci_low_delay_queue": 20,
          "no_candidate_high_priority_delay_queue": 10
        },
        "delay_count": 61,
        "delay_label_count": 77,
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
        "knn_roi_unsafe_count": 61,
        "knn_unsafe_count": 39,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 24,
        "safe_precision": null,
        "safe_precision_ci_low": null,
        "total": 61,
        "unsafe_label_count": 20,
        "unsafe_or_ood_count": 41
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 0,
    "accepted_batch_rate": 0.0,
    "accepted_batch_roi": null,
    "accepted_batch_roi_ci_low": null,
    "accepted_batch_roi_positive_count": 0,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": 0.0,
    "accepted_reason_counts": {},
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 14,
      "knn_delay_fraction_delay_queue": 25,
      "knn_roi_ci_low_delay_queue": 44,
      "no_candidate_high_priority_delay_queue": 36
    },
    "delay_count": 119,
    "delay_label_count": 118,
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
    "knn_roi_unsafe_count": 119,
    "knn_unsafe_count": 68,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": null,
    "safe_precision_ci_low": null,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 72
  },
  "validation_safety_checks": {
    "accepted_batch_count_met": false,
    "accepted_batch_rate_met": false,
    "accepted_batch_roi_ci_low_met": false,
    "accepted_batch_roi_met": false,
    "coverage_met": true,
    "false_high_priority_on_delay_met": true,
    "false_safe_rate_met": true,
    "family_holdout_all_high_roi_opportunity_families_accepted": false,
    "min_high_priority_met": false,
    "safe_precision_ci_low_met": false,
    "safe_precision_met": false
  }
}
```

## 边界

- 本审计只验证 offline admission safety shell，不证明 5/10 no-regression；
- kNN/OOD 只能把 true-RC negative 延迟到 DELAY_QUEUE，不能永久丢弃；
- kNN/OOD no-column / no-safe 不能产生 `CERTIFIED_NO_NEGATIVE`；
- final certificate 仍必须来自 exact pricing full closure。
