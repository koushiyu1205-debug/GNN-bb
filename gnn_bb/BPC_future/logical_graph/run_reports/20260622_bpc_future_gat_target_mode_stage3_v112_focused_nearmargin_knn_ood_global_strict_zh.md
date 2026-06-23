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
train_row_count = 895
validation_row_count = 326
train_label_counts = {'delay_queue': 245, 'high_priority': 650}
validation_label_counts = {'delay_queue': 90, 'high_priority': 236}
batch_threshold = 0.5301380157470703
candidate_threshold = 0.2651715148785978
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.5
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.55
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
min_neighbor_accepted_batch_roi = None
min_neighbor_accepted_batch_roi_ci_low = None
threshold_grouping = global
decision_scope = validation
decision_record_count = 326
validation_metrics = {'total': 326, 'coverage_non_ood_count': 326, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 291, 'delay_rate': 0.8926380368098159, 'accepted_batch_count': 35, 'accepted_batch_rate': 0.10736196319018405, 'accepted_batch_roi_positive_count': 35, 'accepted_batch_roi': 4.921132917063577, 'accepted_batch_roi_ci_low': 2.6665812386647936, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.9010957324106112, 'unsafe_label_count': 90, 'knn_unsafe_count': 173, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 181, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 286, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 289, 'high_priority': 35, 'no_candidate_high_priority_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 35}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['greedy-anchor', 'random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 124, 'coverage_non_ood_count': 124, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 119, 'delay_rate': 0.9596774193548387, 'accepted_batch_count': 5, 'accepted_batch_rate': 0.04032258064516129, 'accepted_batch_roi_positive_count': 5, 'accepted_batch_roi': 6.602623319625854, 'accepted_batch_roi_ci_low': 3.834850839853769, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.565508505247919, 'unsafe_label_count': 31, 'knn_unsafe_count': 67, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 68, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 122, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 119, 'high_priority': 5}, 'accepted_reason_counts': {'high_priority': 5}, 'oracle_high_roi_count': 20, 'max_accepted_batch_roi_label': 106.158935546875}, 'random-wave': {'total': 132, 'coverage_non_ood_count': 132, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 123, 'delay_rate': 0.9318181818181818, 'accepted_batch_count': 9, 'accepted_batch_rate': 0.06818181818181818, 'accepted_batch_roi_positive_count': 9, 'accepted_batch_roi': 6.039797802766164, 'accepted_batch_roi_ci_low': 2.632748026042754, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7008472464490406, 'unsafe_label_count': 46, 'knn_unsafe_count': 83, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 89, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 127, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 122, 'high_priority': 9, 'no_candidate_high_priority_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 9}, 'oracle_high_roi_count': 34, 'max_accepted_batch_roi_label': 79.51943969726562}, 'sector-wave': {'total': 70, 'coverage_non_ood_count': 70, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 49, 'delay_rate': 0.7, 'accepted_batch_count': 21, 'accepted_batch_rate': 0.3, 'accepted_batch_roi_positive_count': 21, 'accepted_batch_roi': 4.0413502511524015, 'accepted_batch_roi_ci_low': 0.6257805113390837, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8453561767357979, 'unsafe_label_count': 13, 'knn_unsafe_count': 23, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 24, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 37, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 48, 'high_priority': 21, 'no_candidate_high_priority_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 21}, 'oracle_high_roi_count': 28, 'max_accepted_batch_roi_label': 41.31852722167969}}}
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
    "below_batch_threshold_delay_queue": 289,
    "high_priority": 35,
    "no_candidate_high_priority_delay_queue": 2
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 35,
    "accepted_batch_rate": 0.10736196319018405,
    "accepted_batch_roi": 4.921132917063577,
    "accepted_batch_roi_ci_low": 2.6665812386647936,
    "accepted_batch_roi_positive_count": 35,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 35
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 326,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 289,
      "high_priority": 35,
      "no_candidate_high_priority_delay_queue": 2
    },
    "delay_count": 291,
    "delay_label_count": 286,
    "delay_rate": 0.8926380368098159,
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
    "knn_roi_unsafe_count": 0,
    "knn_unsafe_count": 173,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "total": 326,
    "unsafe_label_count": 90,
    "unsafe_or_ood_count": 181
  },
  "decision_split_counts": {
    "validation": 326
  },
  "decision_threshold_group_counts": {
    "global": 326
  },
  "decision_threshold_scope_counts": {
    "global": 326
  },
  "production_block_reasons": [],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.5301380157470703,
      "batch_thresholds_by_family": {},
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.55,
      "candidate_delay_score_penalty": 1.5,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_threshold": 0.2651715148785978,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 245,
        "high_priority": 650
      },
      "min_neighbor_accepted_batch_roi": null,
      "min_neighbor_accepted_batch_roi_ci_low": null,
      "safe_radius": 9.601651486837216,
      "scope": "global",
      "train_count": 895
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
      "greedy-anchor",
      "random-wave",
      "sector-wave"
    ],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 5,
        "accepted_batch_rate": 0.04032258064516129,
        "accepted_batch_roi": 6.602623319625854,
        "accepted_batch_roi_ci_low": 3.834850839853769,
        "accepted_batch_roi_positive_count": 5,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 5
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 124,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 119,
          "high_priority": 5
        },
        "delay_count": 119,
        "delay_label_count": 122,
        "delay_rate": 0.9596774193548387,
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
        "knn_roi_unsafe_count": 0,
        "knn_unsafe_count": 67,
        "max_accepted_batch_roi_label": 106.158935546875,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.565508505247919,
        "total": 124,
        "unsafe_label_count": 31,
        "unsafe_or_ood_count": 68
      },
      "random-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_rate": 0.06818181818181818,
        "accepted_batch_roi": 6.039797802766164,
        "accepted_batch_roi_ci_low": 2.632748026042754,
        "accepted_batch_roi_positive_count": 9,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 9
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 132,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 122,
          "high_priority": 9,
          "no_candidate_high_priority_delay_queue": 1
        },
        "delay_count": 123,
        "delay_label_count": 127,
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
        "knn_roi_unsafe_count": 0,
        "knn_unsafe_count": 83,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 34,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7008472464490406,
        "total": 132,
        "unsafe_label_count": 46,
        "unsafe_or_ood_count": 89
      },
      "sector-wave": {
        "accepted_batch_count": 21,
        "accepted_batch_rate": 0.3,
        "accepted_batch_roi": 4.0413502511524015,
        "accepted_batch_roi_ci_low": 0.6257805113390837,
        "accepted_batch_roi_positive_count": 21,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 21
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 70,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 48,
          "high_priority": 21,
          "no_candidate_high_priority_delay_queue": 1
        },
        "delay_count": 49,
        "delay_label_count": 37,
        "delay_rate": 0.7,
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
        "knn_roi_unsafe_count": 0,
        "knn_unsafe_count": 23,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 28,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.8453561767357979,
        "total": 70,
        "unsafe_label_count": 13,
        "unsafe_or_ood_count": 24
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 35,
    "accepted_batch_rate": 0.10736196319018405,
    "accepted_batch_roi": 4.921132917063577,
    "accepted_batch_roi_ci_low": 2.6665812386647936,
    "accepted_batch_roi_positive_count": 35,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 35
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 326,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 289,
      "high_priority": 35,
      "no_candidate_high_priority_delay_queue": 2
    },
    "delay_count": 291,
    "delay_label_count": 286,
    "delay_rate": 0.8926380368098159,
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
    "knn_roi_unsafe_count": 0,
    "knn_unsafe_count": 173,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "total": 326,
    "unsafe_label_count": 90,
    "unsafe_or_ood_count": 181
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
