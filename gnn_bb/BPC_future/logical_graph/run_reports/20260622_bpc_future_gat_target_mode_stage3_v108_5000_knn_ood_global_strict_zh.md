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
batch_threshold = 0.5830044746398926
candidate_threshold = 0.3149940616839544
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.0
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.6
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
min_neighbor_accepted_batch_roi = None
min_neighbor_accepted_batch_roi_ci_low = None
threshold_grouping = global
decision_scope = all
decision_record_count = 1221
validation_metrics = {'total': 326, 'coverage_non_ood_count': 326, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 317, 'delay_rate': 0.9723926380368099, 'accepted_batch_count': 9, 'accepted_batch_rate': 0.027607361963190184, 'accepted_batch_roi_positive_count': 9, 'accepted_batch_roi': 14.004474004109701, 'accepted_batch_roi_ci_low': 8.752982125355302, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7008472464490406, 'unsafe_label_count': 90, 'knn_unsafe_count': 167, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 185, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 286, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 313, 'high_priority': 9, 'knn_delay_fraction_delay_queue': 4}, 'accepted_reason_counts': {'high_priority': 9}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['greedy-anchor', 'random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 124, 'coverage_non_ood_count': 124, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 121, 'delay_rate': 0.9758064516129032, 'accepted_batch_count': 3, 'accepted_batch_rate': 0.024193548387096774, 'accepted_batch_roi_positive_count': 3, 'accepted_batch_roi': 8.780579249064127, 'accepted_batch_roi_ci_low': 7.143820828177686, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.4384939195509822, 'unsafe_label_count': 31, 'knn_unsafe_count': 60, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 69, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 122, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 119, 'high_priority': 3, 'knn_delay_fraction_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 3}, 'oracle_high_roi_count': 20, 'max_accepted_batch_roi_label': 106.158935546875}, 'random-wave': {'total': 132, 'coverage_non_ood_count': 132, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 129, 'delay_rate': 0.9772727272727273, 'accepted_batch_count': 3, 'accepted_batch_rate': 0.022727272727272728, 'accepted_batch_roi_positive_count': 3, 'accepted_batch_roi': 12.345690409342447, 'accepted_batch_roi_ci_low': 9.785389855025354, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.4384939195509822, 'unsafe_label_count': 46, 'knn_unsafe_count': 82, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 90, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 127, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 127, 'high_priority': 3, 'knn_delay_fraction_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 3}, 'oracle_high_roi_count': 34, 'max_accepted_batch_roi_label': 79.51943969726562}, 'sector-wave': {'total': 70, 'coverage_non_ood_count': 70, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 67, 'delay_rate': 0.9571428571428572, 'accepted_batch_count': 3, 'accepted_batch_rate': 0.04285714285714286, 'accepted_batch_roi_positive_count': 3, 'accepted_batch_roi': 20.887152353922527, 'accepted_batch_roi_ci_low': 7.733783678047011, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.4384939195509822, 'unsafe_label_count': 13, 'knn_unsafe_count': 25, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 26, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 37, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 67, 'high_priority': 3}, 'accepted_reason_counts': {'high_priority': 3}, 'oracle_high_roi_count': 28, 'max_accepted_batch_roi_label': 41.31852722167969}}}
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
    "below_batch_threshold_delay_queue": 1179,
    "candidate_false_high_priority_delay_queue": 1,
    "high_priority": 37,
    "knn_delay_fraction_delay_queue": 4
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 37,
    "accepted_batch_rate": 0.030303030303030304,
    "accepted_batch_roi": 13.776652767851546,
    "accepted_batch_roi_ci_low": 10.558759708957336,
    "accepted_batch_roi_positive_count": 37,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 37
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 1221,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 1179,
      "candidate_false_high_priority_delay_queue": 1,
      "high_priority": 37,
      "knn_delay_fraction_delay_queue": 4
    },
    "delay_count": 1184,
    "delay_label_count": 1339,
    "delay_rate": 0.9696969696969697,
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
    "knn_unsafe_count": 548,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9059390425448562,
    "total": 1221,
    "unsafe_label_count": 335,
    "unsafe_or_ood_count": 566
  },
  "decision_split_counts": {
    "train": 895,
    "validation": 326
  },
  "decision_threshold_group_counts": {
    "global": 1221
  },
  "decision_threshold_scope_counts": {
    "global": 1221
  },
  "production_block_reasons": [
    "validation_safe_precision_ci_low_below_min",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.5830044746398926,
      "batch_thresholds_by_family": {},
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.6,
      "candidate_delay_score_penalty": 1.0,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_threshold": 0.3149940616839544,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 245,
        "high_priority": 650
      },
      "min_neighbor_accepted_batch_roi": null,
      "min_neighbor_accepted_batch_roi_ci_low": null,
      "safe_radius": 8.676678938933101,
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
        "accepted_batch_count": 3,
        "accepted_batch_rate": 0.024193548387096774,
        "accepted_batch_roi": 8.780579249064127,
        "accepted_batch_roi_ci_low": 7.143820828177686,
        "accepted_batch_roi_positive_count": 3,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 3
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 124,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 119,
          "high_priority": 3,
          "knn_delay_fraction_delay_queue": 2
        },
        "delay_count": 121,
        "delay_label_count": 122,
        "delay_rate": 0.9758064516129032,
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
        "knn_unsafe_count": 60,
        "max_accepted_batch_roi_label": 106.158935546875,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.4384939195509822,
        "total": 124,
        "unsafe_label_count": 31,
        "unsafe_or_ood_count": 69
      },
      "random-wave": {
        "accepted_batch_count": 3,
        "accepted_batch_rate": 0.022727272727272728,
        "accepted_batch_roi": 12.345690409342447,
        "accepted_batch_roi_ci_low": 9.785389855025354,
        "accepted_batch_roi_positive_count": 3,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 3
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 132,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 127,
          "high_priority": 3,
          "knn_delay_fraction_delay_queue": 2
        },
        "delay_count": 129,
        "delay_label_count": 127,
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
        "knn_roi_unsafe_count": 0,
        "knn_unsafe_count": 82,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 34,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.4384939195509822,
        "total": 132,
        "unsafe_label_count": 46,
        "unsafe_or_ood_count": 90
      },
      "sector-wave": {
        "accepted_batch_count": 3,
        "accepted_batch_rate": 0.04285714285714286,
        "accepted_batch_roi": 20.887152353922527,
        "accepted_batch_roi_ci_low": 7.733783678047011,
        "accepted_batch_roi_positive_count": 3,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 3
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 70,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 67,
          "high_priority": 3
        },
        "delay_count": 67,
        "delay_label_count": 37,
        "delay_rate": 0.9571428571428572,
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
        "knn_unsafe_count": 25,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 28,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.4384939195509822,
        "total": 70,
        "unsafe_label_count": 13,
        "unsafe_or_ood_count": 26
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 9,
    "accepted_batch_rate": 0.027607361963190184,
    "accepted_batch_roi": 14.004474004109701,
    "accepted_batch_roi_ci_low": 8.752982125355302,
    "accepted_batch_roi_positive_count": 9,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 9
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 326,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 313,
      "high_priority": 9,
      "knn_delay_fraction_delay_queue": 4
    },
    "delay_count": 317,
    "delay_label_count": 286,
    "delay_rate": 0.9723926380368099,
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
    "knn_unsafe_count": 167,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.7008472464490406,
    "total": 326,
    "unsafe_label_count": 90,
    "unsafe_or_ood_count": 185
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
