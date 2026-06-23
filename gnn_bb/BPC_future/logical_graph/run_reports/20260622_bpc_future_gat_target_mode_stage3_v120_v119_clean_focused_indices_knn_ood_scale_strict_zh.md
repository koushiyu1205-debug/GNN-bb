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
batch_threshold = 0.6024689674377441
candidate_threshold = 0.24160798805678513
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
decision_record_count = 292
validation_metrics = {'total': 292, 'coverage_non_ood_count': 283, 'coverage': 0.9691780821917808, 'ood_count': 9, 'ood_rate': 0.030821917808219176, 'delay_count': 260, 'delay_rate': 0.8904109589041096, 'accepted_batch_count': 32, 'accepted_batch_rate': 0.1095890410958904, 'accepted_batch_roi_positive_count': 32, 'accepted_batch_roi': 18.558433688245714, 'accepted_batch_roi_ci_low': 8.702054229424025, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.8928172849426365, 'unsafe_label_count': 83, 'knn_unsafe_count': 128, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 142, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 277, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 254, 'candidate_false_high_priority_delay_queue': 1, 'high_priority': 32, 'knn_delay_fraction_delay_queue': 3, 'no_candidate_high_priority_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 32}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['greedy-anchor', 'random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 124, 'coverage_non_ood_count': 122, 'coverage': 0.9838709677419355, 'ood_count': 2, 'ood_rate': 0.016129032258064516, 'delay_count': 116, 'delay_rate': 0.9354838709677419, 'accepted_batch_count': 8, 'accepted_batch_rate': 0.06451612903225806, 'accepted_batch_roi_positive_count': 8, 'accepted_batch_roi': 34.43998309969902, 'accepted_batch_roi_ci_low': 6.3137319337343065, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.6755843804891231, 'unsafe_label_count': 31, 'knn_unsafe_count': 54, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 63, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 122, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 115, 'high_priority': 8, 'knn_delay_fraction_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 8}, 'oracle_high_roi_count': 20, 'max_accepted_batch_roi_label': 106.158935546875}, 'random-wave': {'total': 113, 'coverage_non_ood_count': 112, 'coverage': 0.9911504424778761, 'ood_count': 1, 'ood_rate': 0.008849557522123894, 'delay_count': 102, 'delay_rate': 0.9026548672566371, 'accepted_batch_count': 11, 'accepted_batch_rate': 0.09734513274336283, 'accepted_batch_roi_positive_count': 11, 'accepted_batch_roi': 21.511063422669064, 'accepted_batch_roi_ci_low': 4.502739883099661, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7411599827511859, 'unsafe_label_count': 43, 'knn_unsafe_count': 64, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 67, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 124, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 98, 'high_priority': 11, 'knn_delay_fraction_delay_queue': 2, 'no_candidate_high_priority_delay_queue': 2}, 'accepted_reason_counts': {'high_priority': 11}, 'oracle_high_roi_count': 22, 'max_accepted_batch_roi_label': 79.51943969726562}, 'sector-wave': {'total': 55, 'coverage_non_ood_count': 49, 'coverage': 0.8909090909090909, 'ood_count': 6, 'ood_rate': 0.10909090909090909, 'delay_count': 42, 'delay_rate': 0.7636363636363637, 'accepted_batch_count': 13, 'accepted_batch_rate': 0.23636363636363636, 'accepted_batch_roi_positive_count': 13, 'accepted_batch_roi': 6.286793505916228, 'accepted_batch_roi_ci_low': 0.8516317776651556, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7718981569447084, 'unsafe_label_count': 9, 'knn_unsafe_count': 10, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 12, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 31, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 41, 'candidate_false_high_priority_delay_queue': 1, 'high_priority': 13}, 'accepted_reason_counts': {'high_priority': 13}, 'oracle_high_roi_count': 17, 'max_accepted_batch_roi_label': 33.70098114013672}}}
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
    "below_batch_threshold_delay_queue": 254,
    "candidate_false_high_priority_delay_queue": 1,
    "high_priority": 32,
    "knn_delay_fraction_delay_queue": 3,
    "no_candidate_high_priority_delay_queue": 2
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 32,
    "accepted_batch_rate": 0.1095890410958904,
    "accepted_batch_roi": 18.558433688245714,
    "accepted_batch_roi_ci_low": 8.702054229424025,
    "accepted_batch_roi_positive_count": 32,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 32
    },
    "coverage": 0.9691780821917808,
    "coverage_non_ood_count": 283,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 254,
      "candidate_false_high_priority_delay_queue": 1,
      "high_priority": 32,
      "knn_delay_fraction_delay_queue": 3,
      "no_candidate_high_priority_delay_queue": 2
    },
    "delay_count": 260,
    "delay_label_count": 277,
    "delay_rate": 0.8904109589041096,
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
    "knn_unsafe_count": 128,
    "ood_count": 9,
    "ood_rate": 0.030821917808219176,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8928172849426365,
    "total": 292,
    "unsafe_label_count": 83,
    "unsafe_or_ood_count": 142
  },
  "decision_split_counts": {
    "validation": 292
  },
  "decision_threshold_group_counts": {
    "005": 10,
    "010": 12,
    "020": 194,
    "030": 47,
    "050": 20,
    "global": 9
  },
  "decision_threshold_scope_counts": {
    "global": 9,
    "scale": 283
  },
  "production_block_reasons": [
    "validation_safe_precision_ci_low_below_min",
    "validation_candidate_not_ready"
  ],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.6024689674377441,
      "batch_thresholds_by_family": {},
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.55,
      "candidate_delay_score_penalty": 1.5,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_threshold": 0.24160798805678513,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 210,
        "high_priority": 615
      },
      "min_neighbor_accepted_batch_roi": null,
      "min_neighbor_accepted_batch_roi_ci_low": null,
      "safe_radius": 23.873877263653682,
      "scope": "global",
      "train_count": 825
    },
    "groups": {
      "005": {
        "batch_threshold": 0.6024689674377441,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.24160798805678513,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "005",
        "label_counts": {
          "delay_queue": 13,
          "high_priority": 9
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 5.739217919927302,
        "scope": "scale",
        "train_count": 22
      },
      "010": {
        "batch_threshold": 0.6024689674377441,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.24160798805678513,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "010",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 36
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 4.893591805841248,
        "scope": "scale",
        "train_count": 62
      },
      "020": {
        "batch_threshold": 0.6024689674377441,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.24160798805678513,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020",
        "label_counts": {
          "delay_queue": 128,
          "high_priority": 366
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 7.977315952963385,
        "scope": "scale",
        "train_count": 494
      },
      "030": {
        "batch_threshold": 0.6024689674377441,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.24160798805678513,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "030",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 95
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 11.428607779200872,
        "scope": "scale",
        "train_count": 121
      },
      "050": {
        "batch_threshold": 0.6024689674377441,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.24160798805678513,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "050",
        "label_counts": {
          "delay_queue": 17,
          "high_priority": 82
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 8.901893020828464,
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
        "accepted_batch_count": 8,
        "accepted_batch_rate": 0.06451612903225806,
        "accepted_batch_roi": 34.43998309969902,
        "accepted_batch_roi_ci_low": 6.3137319337343065,
        "accepted_batch_roi_positive_count": 8,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 8
        },
        "coverage": 0.9838709677419355,
        "coverage_non_ood_count": 122,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 115,
          "high_priority": 8,
          "knn_delay_fraction_delay_queue": 1
        },
        "delay_count": 116,
        "delay_label_count": 122,
        "delay_rate": 0.9354838709677419,
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
        "knn_unsafe_count": 54,
        "max_accepted_batch_roi_label": 106.158935546875,
        "ood_count": 2,
        "ood_rate": 0.016129032258064516,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.6755843804891231,
        "total": 124,
        "unsafe_label_count": 31,
        "unsafe_or_ood_count": 63
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_rate": 0.09734513274336283,
        "accepted_batch_roi": 21.511063422669064,
        "accepted_batch_roi_ci_low": 4.502739883099661,
        "accepted_batch_roi_positive_count": 11,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 11
        },
        "coverage": 0.9911504424778761,
        "coverage_non_ood_count": 112,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 98,
          "high_priority": 11,
          "knn_delay_fraction_delay_queue": 2,
          "no_candidate_high_priority_delay_queue": 2
        },
        "delay_count": 102,
        "delay_label_count": 124,
        "delay_rate": 0.9026548672566371,
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
        "knn_unsafe_count": 64,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "ood_count": 1,
        "ood_rate": 0.008849557522123894,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7411599827511859,
        "total": 113,
        "unsafe_label_count": 43,
        "unsafe_or_ood_count": 67
      },
      "sector-wave": {
        "accepted_batch_count": 13,
        "accepted_batch_rate": 0.23636363636363636,
        "accepted_batch_roi": 6.286793505916228,
        "accepted_batch_roi_ci_low": 0.8516317776651556,
        "accepted_batch_roi_positive_count": 13,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 13
        },
        "coverage": 0.8909090909090909,
        "coverage_non_ood_count": 49,
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
        "false_safe_rate_ood": 0.0,
        "false_safe_rate_union": 0.0,
        "false_safe_union_count": 0,
        "knn_roi_unsafe_count": 0,
        "knn_unsafe_count": 10,
        "max_accepted_batch_roi_label": 33.70098114013672,
        "ood_count": 6,
        "ood_rate": 0.10909090909090909,
        "oracle_high_roi_count": 17,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7718981569447084,
        "total": 55,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 12
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 32,
    "accepted_batch_rate": 0.1095890410958904,
    "accepted_batch_roi": 18.558433688245714,
    "accepted_batch_roi_ci_low": 8.702054229424025,
    "accepted_batch_roi_positive_count": 32,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 32
    },
    "coverage": 0.9691780821917808,
    "coverage_non_ood_count": 283,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 254,
      "candidate_false_high_priority_delay_queue": 1,
      "high_priority": 32,
      "knn_delay_fraction_delay_queue": 3,
      "no_candidate_high_priority_delay_queue": 2
    },
    "delay_count": 260,
    "delay_label_count": 277,
    "delay_rate": 0.8904109589041096,
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
    "knn_unsafe_count": 128,
    "ood_count": 9,
    "ood_rate": 0.030821917808219176,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8928172849426365,
    "total": 292,
    "unsafe_label_count": 83,
    "unsafe_or_ood_count": 142
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
