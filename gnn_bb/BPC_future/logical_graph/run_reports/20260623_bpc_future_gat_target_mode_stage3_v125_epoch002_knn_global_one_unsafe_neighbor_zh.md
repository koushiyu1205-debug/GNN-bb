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
train_row_count = 825
validation_row_count = 292
train_label_counts = {'delay_queue': 210, 'high_priority': 615}
validation_label_counts = {'delay_queue': 83, 'high_priority': 209}
batch_threshold = 0.6610236167907715
candidate_threshold = 0.22744405938493414
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
decision_record_count = 292
validation_metrics = {'total': 292, 'coverage_non_ood_count': 292, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 257, 'delay_rate': 0.8801369863013698, 'accepted_batch_count': 35, 'accepted_batch_rate': 0.11986301369863013, 'accepted_batch_roi_positive_count': 35, 'accepted_batch_roi': 19.450745317765644, 'accepted_batch_roi_ci_low': 10.357919595213447, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.9010957324106112, 'unsafe_label_count': 83, 'knn_unsafe_count': 92, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 120, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 277, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 254, 'candidate_false_high_priority_delay_queue': 2, 'high_priority': 35, 'no_candidate_high_priority_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 35}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['greedy-anchor', 'random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 124, 'coverage_non_ood_count': 124, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 115, 'delay_rate': 0.9274193548387096, 'accepted_batch_count': 9, 'accepted_batch_rate': 0.07258064516129033, 'accepted_batch_roi_positive_count': 9, 'accepted_batch_roi': 33.91330652766757, 'accepted_batch_roi_ci_low': 9.08681403916039, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7008472464490406, 'unsafe_label_count': 31, 'knn_unsafe_count': 38, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 54, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 122, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 115, 'high_priority': 9}, 'accepted_reason_counts': {'high_priority': 9}, 'oracle_high_roi_count': 20, 'max_accepted_batch_roi_label': 106.158935546875}, 'random-wave': {'total': 113, 'coverage_non_ood_count': 113, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 100, 'delay_rate': 0.8849557522123894, 'accepted_batch_count': 13, 'accepted_batch_rate': 0.11504424778761062, 'accepted_batch_roi_positive_count': 13, 'accepted_batch_roi': 22.33463243681651, 'accepted_batch_roi_ci_low': 7.667186740760123, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7718981569447084, 'unsafe_label_count': 43, 'knn_unsafe_count': 45, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 55, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 124, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 98, 'candidate_false_high_priority_delay_queue': 1, 'high_priority': 13, 'no_candidate_high_priority_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 13}, 'oracle_high_roi_count': 22, 'max_accepted_batch_roi_label': 79.51943969726562}, 'sector-wave': {'total': 55, 'coverage_non_ood_count': 55, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 42, 'delay_rate': 0.7636363636363637, 'accepted_batch_count': 13, 'accepted_batch_rate': 0.23636363636363636, 'accepted_batch_roi_positive_count': 13, 'accepted_batch_roi': 6.554315822628828, 'accepted_batch_roi_ci_low': 1.1852641695978905, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7718981569447084, 'unsafe_label_count': 9, 'knn_unsafe_count': 9, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 11, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 31, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 41, 'candidate_false_high_priority_delay_queue': 1, 'high_priority': 13}, 'accepted_reason_counts': {'high_priority': 13}, 'oracle_high_roi_count': 17, 'max_accepted_batch_roi_label': 33.70098114013672}}}
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
    "below_batch_threshold_delay_queue": 254,
    "candidate_false_high_priority_delay_queue": 2,
    "high_priority": 35,
    "no_candidate_high_priority_delay_queue": 1
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 35,
    "accepted_batch_rate": 0.11986301369863013,
    "accepted_batch_roi": 19.450745317765644,
    "accepted_batch_roi_ci_low": 10.357919595213447,
    "accepted_batch_roi_positive_count": 35,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 35
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 292,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 254,
      "candidate_false_high_priority_delay_queue": 2,
      "high_priority": 35,
      "no_candidate_high_priority_delay_queue": 1
    },
    "delay_count": 257,
    "delay_label_count": 277,
    "delay_rate": 0.8801369863013698,
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
    "knn_unsafe_count": 92,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "total": 292,
    "unsafe_label_count": 83,
    "unsafe_or_ood_count": 120
  },
  "decision_split_counts": {
    "validation": 292
  },
  "decision_threshold_group_counts": {
    "global": 292
  },
  "decision_threshold_scope_counts": {
    "global": 292
  },
  "production_block_reasons": [],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.6610236167907715,
      "batch_thresholds_by_family": {},
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.55,
      "candidate_delay_score_penalty": 1.5,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_threshold": 0.22744405938493414,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 210,
        "high_priority": 615
      },
      "min_neighbor_accepted_batch_roi": null,
      "min_neighbor_accepted_batch_roi_ci_low": null,
      "safe_radius": 13.094838205964715,
      "scope": "global",
      "train_count": 825
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
        "accepted_batch_count": 9,
        "accepted_batch_rate": 0.07258064516129033,
        "accepted_batch_roi": 33.91330652766757,
        "accepted_batch_roi_ci_low": 9.08681403916039,
        "accepted_batch_roi_positive_count": 9,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 9
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 124,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 115,
          "high_priority": 9
        },
        "delay_count": 115,
        "delay_label_count": 122,
        "delay_rate": 0.9274193548387096,
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
        "knn_unsafe_count": 38,
        "max_accepted_batch_roi_label": 106.158935546875,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7008472464490406,
        "total": 124,
        "unsafe_label_count": 31,
        "unsafe_or_ood_count": 54
      },
      "random-wave": {
        "accepted_batch_count": 13,
        "accepted_batch_rate": 0.11504424778761062,
        "accepted_batch_roi": 22.33463243681651,
        "accepted_batch_roi_ci_low": 7.667186740760123,
        "accepted_batch_roi_positive_count": 13,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 13
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 113,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 98,
          "candidate_false_high_priority_delay_queue": 1,
          "high_priority": 13,
          "no_candidate_high_priority_delay_queue": 1
        },
        "delay_count": 100,
        "delay_label_count": 124,
        "delay_rate": 0.8849557522123894,
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
        "knn_unsafe_count": 45,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7718981569447084,
        "total": 113,
        "unsafe_label_count": 43,
        "unsafe_or_ood_count": 55
      },
      "sector-wave": {
        "accepted_batch_count": 13,
        "accepted_batch_rate": 0.23636363636363636,
        "accepted_batch_roi": 6.554315822628828,
        "accepted_batch_roi_ci_low": 1.1852641695978905,
        "accepted_batch_roi_positive_count": 13,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 13
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 55,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 41,
          "candidate_false_high_priority_delay_queue": 1,
          "high_priority": 13
        },
        "delay_count": 42,
        "delay_label_count": 31,
        "delay_rate": 0.7636363636363637,
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
        "knn_unsafe_count": 9,
        "max_accepted_batch_roi_label": 33.70098114013672,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 17,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7718981569447084,
        "total": 55,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 11
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 35,
    "accepted_batch_rate": 0.11986301369863013,
    "accepted_batch_roi": 19.450745317765644,
    "accepted_batch_roi_ci_low": 10.357919595213447,
    "accepted_batch_roi_positive_count": 35,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 35
    },
    "coverage": 1.0,
    "coverage_non_ood_count": 292,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 254,
      "candidate_false_high_priority_delay_queue": 2,
      "high_priority": 35,
      "no_candidate_high_priority_delay_queue": 1
    },
    "delay_count": 257,
    "delay_label_count": 277,
    "delay_rate": 0.8801369863013698,
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
    "knn_unsafe_count": 92,
    "ood_count": 0,
    "ood_rate": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "total": 292,
    "unsafe_label_count": 83,
    "unsafe_or_ood_count": 120
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
