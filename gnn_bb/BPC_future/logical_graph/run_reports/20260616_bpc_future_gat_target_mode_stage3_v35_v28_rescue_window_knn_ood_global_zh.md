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
candidate_threshold = 0.3353747177982669
candidate_admission_score_mode = risk_adjusted_rescue_window
candidate_delay_score_penalty = 1.0
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.5
candidate_rescue_raw_score_threshold = 0.3
candidate_rescue_delay_risk_threshold = 0.75
candidate_rescue_delay_score_penalty = 0.25
threshold_grouping = global
decision_scope = validation
decision_record_count = 119
validation_metrics = {'total': 119, 'coverage_non_ood_count': 119, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 80, 'delay_rate': 0.6722689075630253, 'accepted_batch_count': 39, 'accepted_batch_rate': 0.3277310924369748, 'accepted_batch_roi_positive_count': 39, 'accepted_batch_roi': 2.8588009188223134, 'accepted_batch_roi_ci_low': 0.10006027383500982, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.910330146399761, 'unsafe_label_count': 33, 'knn_unsafe_count': 72, 'unsafe_or_ood_count': 74, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 118, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 13, 'context_delay_fallback_delay_queue': 1, 'high_priority': 39, 'knn_delay_fraction_delay_queue': 17, 'no_candidate_high_priority_delay_queue': 49}, 'accepted_reason_counts': {'high_priority': 39}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 14, 'coverage_non_ood_count': 14, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 8, 'delay_rate': 0.5714285714285714, 'accepted_batch_count': 6, 'accepted_batch_rate': 0.42857142857142855, 'accepted_batch_roi_positive_count': 6, 'accepted_batch_roi': 0.11975858719658088, 'accepted_batch_roi_ci_low': -0.0020965470092783878, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.6096569663469354, 'unsafe_label_count': 4, 'knn_unsafe_count': 7, 'unsafe_or_ood_count': 7, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 24, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'high_priority': 6, 'no_candidate_high_priority_delay_queue': 8}, 'accepted_reason_counts': {'high_priority': 6}, 'oracle_high_roi_count': 0, 'max_accepted_batch_roi_label': 0.4039181172847748}, 'random-wave': {'total': 44, 'coverage_non_ood_count': 44, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 32, 'delay_rate': 0.7272727272727273, 'accepted_batch_count': 12, 'accepted_batch_rate': 0.2727272727272727, 'accepted_batch_roi_positive_count': 12, 'accepted_batch_roi': 0.2696304570417851, 'accepted_batch_roi_ci_low': 0.10822452443318259, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7574992425007574, 'unsafe_label_count': 9, 'knn_unsafe_count': 26, 'unsafe_or_ood_count': 27, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 17, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'context_delay_fallback_delay_queue': 1, 'high_priority': 12, 'knn_delay_fraction_delay_queue': 3, 'no_candidate_high_priority_delay_queue': 28}, 'accepted_reason_counts': {'high_priority': 12}, 'oracle_high_roi_count': 6, 'max_accepted_batch_roi_label': 4.385624885559082}, 'sector-wave': {'total': 61, 'coverage_non_ood_count': 61, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 40, 'delay_rate': 0.6557377049180327, 'accepted_batch_count': 21, 'accepted_batch_rate': 0.3442622950819672, 'accepted_batch_roi_positive_count': 21, 'accepted_batch_roi': 5.120910420304253, 'accepted_batch_roi_ci_low': 0.14948860682153775, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8453561767357979, 'unsafe_label_count': 20, 'knn_unsafe_count': 39, 'unsafe_or_ood_count': 40, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 77, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'candidate_false_high_priority_delay_queue': 13, 'high_priority': 21, 'knn_delay_fraction_delay_queue': 14, 'no_candidate_high_priority_delay_queue': 13}, 'accepted_reason_counts': {'high_priority': 21}, 'oracle_high_roi_count': 24, 'max_accepted_batch_roi_label': 41.31852722167969}}}
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
    "candidate_false_high_priority_delay_queue": 13,
    "context_delay_fallback_delay_queue": 1,
    "high_priority": 39,
    "knn_delay_fraction_delay_queue": 17,
    "no_candidate_high_priority_delay_queue": 49
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 39,
    "accepted_batch_rate": 0.3277310924369748,
    "accepted_batch_roi": 2.8588009188223134,
    "accepted_batch_roi_ci_low": 0.10006027383500982,
    "accepted_batch_roi_positive_count": 39,
    "accepted_reason_counts": {
      "high_priority": 39
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 13,
      "context_delay_fallback_delay_queue": 1,
      "high_priority": 39,
      "knn_delay_fraction_delay_queue": 17,
      "no_candidate_high_priority_delay_queue": 49
    },
    "delay_count": 80,
    "delay_label_count": 118,
    "delay_rate": 0.6722689075630253,
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
    "knn_unsafe_count": 72,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.910330146399761,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 74
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
      "candidate_admission_score_mode": "risk_adjusted_rescue_window",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.5,
      "candidate_delay_score_penalty": 1.0,
      "candidate_rescue_delay_risk_threshold": 0.75,
      "candidate_rescue_delay_score_penalty": 0.25,
      "candidate_rescue_raw_score_threshold": 0.3,
      "candidate_threshold": 0.3353747177982669,
      "context_delay_fallback_contexts": [
        "5e253e60eb577a74"
      ],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 68,
        "high_priority": 188
      },
      "safe_radius": 5.1049104054262715,
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
        "knn_unsafe_count": 7,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.6096569663469354,
        "total": 14,
        "unsafe_label_count": 4,
        "unsafe_or_ood_count": 7
      },
      "random-wave": {
        "accepted_batch_count": 12,
        "accepted_batch_rate": 0.2727272727272727,
        "accepted_batch_roi": 0.2696304570417851,
        "accepted_batch_roi_ci_low": 0.10822452443318259,
        "accepted_batch_roi_positive_count": 12,
        "accepted_reason_counts": {
          "high_priority": 12
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 44,
        "decision_reason_counts": {
          "context_delay_fallback_delay_queue": 1,
          "high_priority": 12,
          "knn_delay_fraction_delay_queue": 3,
          "no_candidate_high_priority_delay_queue": 28
        },
        "delay_count": 32,
        "delay_label_count": 17,
        "delay_rate": 0.7272727272727273,
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
        "knn_unsafe_count": 26,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7574992425007574,
        "total": 44,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 27
      },
      "sector-wave": {
        "accepted_batch_count": 21,
        "accepted_batch_rate": 0.3442622950819672,
        "accepted_batch_roi": 5.120910420304253,
        "accepted_batch_roi_ci_low": 0.14948860682153775,
        "accepted_batch_roi_positive_count": 21,
        "accepted_reason_counts": {
          "high_priority": 21
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 61,
        "decision_reason_counts": {
          "candidate_false_high_priority_delay_queue": 13,
          "high_priority": 21,
          "knn_delay_fraction_delay_queue": 14,
          "no_candidate_high_priority_delay_queue": 13
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
        "knn_unsafe_count": 39,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.8453561767357979,
        "total": 61,
        "unsafe_label_count": 20,
        "unsafe_or_ood_count": 40
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 39,
    "accepted_batch_rate": 0.3277310924369748,
    "accepted_batch_roi": 2.8588009188223134,
    "accepted_batch_roi_ci_low": 0.10006027383500982,
    "accepted_batch_roi_positive_count": 39,
    "accepted_reason_counts": {
      "high_priority": 39
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 119,
    "decision_reason_counts": {
      "candidate_false_high_priority_delay_queue": 13,
      "context_delay_fallback_delay_queue": 1,
      "high_priority": 39,
      "knn_delay_fraction_delay_queue": 17,
      "no_candidate_high_priority_delay_queue": 49
    },
    "delay_count": 80,
    "delay_label_count": 118,
    "delay_rate": 0.6722689075630253,
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
    "knn_unsafe_count": 72,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.910330146399761,
    "total": 119,
    "unsafe_label_count": 33,
    "unsafe_or_ood_count": 74
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
