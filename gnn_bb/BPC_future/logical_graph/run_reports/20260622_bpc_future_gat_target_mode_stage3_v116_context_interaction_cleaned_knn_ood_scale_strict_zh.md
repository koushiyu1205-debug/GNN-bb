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
train_row_count = 868
validation_row_count = 309
train_label_counts = {'delay_queue': 238, 'high_priority': 630}
validation_label_counts = {'delay_queue': 90, 'high_priority': 219}
batch_threshold = 0.65
candidate_threshold = 0.18986651552497125
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.5
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.55
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
min_neighbor_accepted_batch_roi = None
min_neighbor_accepted_batch_roi_ci_low = None
threshold_grouping = scale
decision_scope = validation
decision_record_count = 309
validation_metrics = {'total': 309, 'coverage_non_ood_count': 304, 'coverage': 0.9838187702265372, 'ood_count': 5, 'ood_rate': 0.016181229773462782, 'delay_count': 273, 'delay_rate': 0.883495145631068, 'accepted_batch_count': 36, 'accepted_batch_rate': 0.11650485436893204, 'accepted_batch_roi_positive_count': 36, 'accepted_batch_roi': 4.602682617492974, 'accepted_batch_roi_ci_low': 2.355012379080361, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.9035781695514236, 'unsafe_label_count': 90, 'knn_unsafe_count': 145, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 161, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 286, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 167, 'high_priority': 36, 'no_candidate_high_priority_delay_queue': 106}, 'accepted_reason_counts': {'high_priority': 36}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['greedy-anchor', 'random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 124, 'coverage_non_ood_count': 121, 'coverage': 0.9758064516129032, 'ood_count': 3, 'ood_rate': 0.024193548387096774, 'delay_count': 120, 'delay_rate': 0.967741935483871, 'accepted_batch_count': 4, 'accepted_batch_rate': 0.03225806451612903, 'accepted_batch_roi_positive_count': 4, 'accepted_batch_roi': 7.481053054332733, 'accepted_batch_roi_ci_low': 4.683364457696941, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.5100999795960008, 'unsafe_label_count': 31, 'knn_unsafe_count': 59, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 68, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 122, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 120, 'high_priority': 4}, 'accepted_reason_counts': {'high_priority': 4}, 'oracle_high_roi_count': 20, 'max_accepted_batch_roi_label': 106.158935546875}, 'random-wave': {'total': 123, 'coverage_non_ood_count': 121, 'coverage': 0.983739837398374, 'ood_count': 2, 'ood_rate': 0.016260162601626018, 'delay_count': 106, 'delay_rate': 0.8617886178861789, 'accepted_batch_count': 17, 'accepted_batch_rate': 0.13821138211382114, 'accepted_batch_roi_positive_count': 17, 'accepted_batch_roi': 3.6569566152551594, 'accepted_batch_roi_ci_low': 1.4548549565544682, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8156763396284354, 'unsafe_label_count': 46, 'knn_unsafe_count': 72, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 76, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 127, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'high_priority': 17, 'no_candidate_high_priority_delay_queue': 106}, 'accepted_reason_counts': {'high_priority': 17}, 'oracle_high_roi_count': 29, 'max_accepted_batch_roi_label': 79.51943969726562}, 'sector-wave': {'total': 62, 'coverage_non_ood_count': 62, 'coverage': 1.0, 'ood_count': 0, 'ood_rate': 0.0, 'delay_count': 47, 'delay_rate': 0.7580645161290323, 'accepted_batch_count': 15, 'accepted_batch_rate': 0.24193548387096775, 'accepted_batch_roi_positive_count': 15, 'accepted_batch_roi': 4.906939970205228, 'accepted_batch_roi_ci_low': 0.14520259047803652, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7961107336956521, 'unsafe_label_count': 13, 'knn_unsafe_count': 14, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 17, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 37, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': None, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 47, 'high_priority': 15}, 'accepted_reason_counts': {'high_priority': 15}, 'oracle_high_roi_count': 20, 'max_accepted_batch_roi_label': 33.70098114013672}}}
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
    "below_batch_threshold_delay_queue": 167,
    "high_priority": 36,
    "no_candidate_high_priority_delay_queue": 106
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 36,
    "accepted_batch_rate": 0.11650485436893204,
    "accepted_batch_roi": 4.602682617492974,
    "accepted_batch_roi_ci_low": 2.355012379080361,
    "accepted_batch_roi_positive_count": 36,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 36
    },
    "coverage": 0.9838187702265372,
    "coverage_non_ood_count": 304,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 167,
      "high_priority": 36,
      "no_candidate_high_priority_delay_queue": 106
    },
    "delay_count": 273,
    "delay_label_count": 286,
    "delay_rate": 0.883495145631068,
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
    "knn_roi_unsafe_count": 0,
    "knn_unsafe_count": 145,
    "ood_count": 5,
    "ood_rate": 0.016181229773462782,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9035781695514236,
    "total": 309,
    "unsafe_label_count": 90,
    "unsafe_or_ood_count": 161
  },
  "decision_split_counts": {
    "validation": 309
  },
  "decision_threshold_group_counts": {
    "005": 10,
    "010": 12,
    "020": 211,
    "030": 47,
    "050": 20,
    "global": 9
  },
  "decision_threshold_scope_counts": {
    "global": 9,
    "scale": 300
  },
  "production_block_reasons": [],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.65,
      "batch_thresholds_by_family": {
        "greedy-anchor": 0.65,
        "random-wave": 0.0,
        "sector-wave": 0.6392755508422852
      },
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.55,
      "candidate_delay_score_penalty": 1.5,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_threshold": 0.18986651552497125,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 238,
        "high_priority": 630
      },
      "min_neighbor_accepted_batch_roi": null,
      "min_neighbor_accepted_batch_roi_ci_low": null,
      "safe_radius": 8.196980402163815,
      "scope": "global",
      "train_count": 868
    },
    "groups": {
      "005": {
        "batch_threshold": 0.65,
        "batch_thresholds_by_family": {
          "greedy-anchor": 0.65,
          "random-wave": 0.0,
          "sector-wave": 0.6392755508422852
        },
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.18986651552497125,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "005",
        "label_counts": {
          "delay_queue": 13,
          "high_priority": 9
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 3.0816528758737585,
        "scope": "scale",
        "train_count": 22
      },
      "010": {
        "batch_threshold": 0.65,
        "batch_thresholds_by_family": {
          "greedy-anchor": 0.65,
          "random-wave": 0.0,
          "sector-wave": 0.6392755508422852
        },
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.18986651552497125,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "010",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 36
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 1.6734578622845862,
        "scope": "scale",
        "train_count": 62
      },
      "020": {
        "batch_threshold": 0.65,
        "batch_thresholds_by_family": {
          "greedy-anchor": 0.65,
          "random-wave": 0.0,
          "sector-wave": 0.6392755508422852
        },
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.18986651552497125,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020",
        "label_counts": {
          "delay_queue": 156,
          "high_priority": 381
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 2.7561670676952534,
        "scope": "scale",
        "train_count": 537
      },
      "030": {
        "batch_threshold": 0.65,
        "batch_thresholds_by_family": {
          "greedy-anchor": 0.65,
          "random-wave": 0.0,
          "sector-wave": 0.6392755508422852
        },
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.18986651552497125,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "030",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 95
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 4.893599871044091,
        "scope": "scale",
        "train_count": 121
      },
      "050": {
        "batch_threshold": 0.65,
        "batch_thresholds_by_family": {
          "greedy-anchor": 0.65,
          "random-wave": 0.0,
          "sector-wave": 0.6392755508422852
        },
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.18986651552497125,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "050",
        "label_counts": {
          "delay_queue": 17,
          "high_priority": 82
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 7.3561339931534455,
        "scope": "scale",
        "train_count": 99
      }
    },
    "skipped_groups": {
      "100": {
        "label_counts": {
          "high_priority": 27
        },
        "scope": "fallback_global",
        "skip_reason": "sparse_or_single_label_group",
        "train_count": 27
      }
    },
    "threshold_grouping": "scale"
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
        "accepted_batch_count": 4,
        "accepted_batch_rate": 0.03225806451612903,
        "accepted_batch_roi": 7.481053054332733,
        "accepted_batch_roi_ci_low": 4.683364457696941,
        "accepted_batch_roi_positive_count": 4,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 4
        },
        "coverage": 0.9758064516129032,
        "coverage_non_ood_count": 121,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 120,
          "high_priority": 4
        },
        "delay_count": 120,
        "delay_label_count": 122,
        "delay_rate": 0.967741935483871,
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
        "knn_roi_unsafe_count": 0,
        "knn_unsafe_count": 59,
        "max_accepted_batch_roi_label": 106.158935546875,
        "ood_count": 3,
        "ood_rate": 0.024193548387096774,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.5100999795960008,
        "total": 124,
        "unsafe_label_count": 31,
        "unsafe_or_ood_count": 68
      },
      "random-wave": {
        "accepted_batch_count": 17,
        "accepted_batch_rate": 0.13821138211382114,
        "accepted_batch_roi": 3.6569566152551594,
        "accepted_batch_roi_ci_low": 1.4548549565544682,
        "accepted_batch_roi_positive_count": 17,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 17
        },
        "coverage": 0.983739837398374,
        "coverage_non_ood_count": 121,
        "decision_reason_counts": {
          "high_priority": 17,
          "no_candidate_high_priority_delay_queue": 106
        },
        "delay_count": 106,
        "delay_label_count": 127,
        "delay_rate": 0.8617886178861789,
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
        "knn_roi_unsafe_count": 0,
        "knn_unsafe_count": 72,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "ood_count": 2,
        "ood_rate": 0.016260162601626018,
        "oracle_high_roi_count": 29,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.8156763396284354,
        "total": 123,
        "unsafe_label_count": 46,
        "unsafe_or_ood_count": 76
      },
      "sector-wave": {
        "accepted_batch_count": 15,
        "accepted_batch_rate": 0.24193548387096775,
        "accepted_batch_roi": 4.906939970205228,
        "accepted_batch_roi_ci_low": 0.14520259047803652,
        "accepted_batch_roi_positive_count": 15,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 15
        },
        "coverage": 1.0,
        "coverage_non_ood_count": 62,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 47,
          "high_priority": 15
        },
        "delay_count": 47,
        "delay_label_count": 37,
        "delay_rate": 0.7580645161290323,
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
        "knn_unsafe_count": 14,
        "max_accepted_batch_roi_label": 33.70098114013672,
        "ood_count": 0,
        "ood_rate": 0.0,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7961107336956521,
        "total": 62,
        "unsafe_label_count": 13,
        "unsafe_or_ood_count": 17
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 36,
    "accepted_batch_rate": 0.11650485436893204,
    "accepted_batch_roi": 4.602682617492974,
    "accepted_batch_roi_ci_low": 2.355012379080361,
    "accepted_batch_roi_positive_count": 36,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 36
    },
    "coverage": 0.9838187702265372,
    "coverage_non_ood_count": 304,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 167,
      "high_priority": 36,
      "no_candidate_high_priority_delay_queue": 106
    },
    "delay_count": 273,
    "delay_label_count": 286,
    "delay_rate": 0.883495145631068,
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
    "knn_roi_unsafe_count": 0,
    "knn_unsafe_count": 145,
    "ood_count": 5,
    "ood_rate": 0.016181229773462782,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9035781695514236,
    "total": 309,
    "unsafe_label_count": 90,
    "unsafe_or_ood_count": 161
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
