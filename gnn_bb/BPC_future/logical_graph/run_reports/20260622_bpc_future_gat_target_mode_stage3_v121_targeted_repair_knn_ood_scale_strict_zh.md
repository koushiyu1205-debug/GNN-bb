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
batch_threshold = 0.6510290503501892
candidate_threshold = 0.34849220302706996
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
validation_metrics = {'total': 292, 'coverage_non_ood_count': 283, 'coverage': 0.9691780821917808, 'ood_count': 9, 'ood_rate': 0.030821917808219176, 'delay_count': 257, 'delay_rate': 0.8801369863013698, 'accepted_batch_count': 35, 'accepted_batch_rate': 0.11986301369863013, 'accepted_batch_roi_positive_count': 35, 'accepted_batch_roi': 19.615722810796328, 'accepted_batch_roi_ci_low': 10.55840602117137, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.9010957324106112, 'unsafe_label_count': 83, 'knn_unsafe_count': 113, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 130, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 277, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 244, 'candidate_false_high_priority_delay_queue': 2, 'high_priority': 35, 'no_candidate_high_priority_delay_queue': 11}, 'accepted_reason_counts': {'high_priority': 35}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['greedy-anchor', 'random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 124, 'coverage_non_ood_count': 123, 'coverage': 0.9919354838709677, 'ood_count': 1, 'ood_rate': 0.008064516129032258, 'delay_count': 114, 'delay_rate': 0.9193548387096774, 'accepted_batch_count': 10, 'accepted_batch_rate': 0.08064516129032258, 'accepted_batch_roi_positive_count': 10, 'accepted_batch_roi': 30.654070270061492, 'accepted_batch_roi_ci_low': 7.547974879593443, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7224598312333834, 'unsafe_label_count': 31, 'knn_unsafe_count': 45, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 56, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 122, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 111, 'high_priority': 10, 'no_candidate_high_priority_delay_queue': 3}, 'accepted_reason_counts': {'high_priority': 10}, 'oracle_high_roi_count': 20, 'max_accepted_batch_roi_label': 106.158935546875}, 'random-wave': {'total': 113, 'coverage_non_ood_count': 111, 'coverage': 0.9823008849557522, 'ood_count': 2, 'ood_rate': 0.017699115044247787, 'delay_count': 99, 'delay_rate': 0.8761061946902655, 'accepted_batch_count': 14, 'accepted_batch_rate': 0.12389380530973451, 'accepted_batch_roi_positive_count': 14, 'accepted_batch_roi': 21.08774014775242, 'accepted_batch_roi_ci_low': 7.28975521389585, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7846829880728186, 'unsafe_label_count': 43, 'knn_unsafe_count': 59, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 64, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 124, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 97, 'candidate_false_high_priority_delay_queue': 1, 'high_priority': 14, 'no_candidate_high_priority_delay_queue': 1}, 'accepted_reason_counts': {'high_priority': 14}, 'oracle_high_roi_count': 22, 'max_accepted_batch_roi_label': 79.51943969726562}, 'sector-wave': {'total': 55, 'coverage_non_ood_count': 49, 'coverage': 0.8909090909090909, 'ood_count': 6, 'ood_rate': 0.10909090909090909, 'delay_count': 44, 'delay_rate': 0.8, 'accepted_batch_count': 11, 'accepted_batch_rate': 0.2, 'accepted_batch_roi_positive_count': 11, 'accepted_batch_roi': 7.707384873520244, 'accepted_batch_roi_ci_low': 1.578762386029906, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7411599827511859, 'unsafe_label_count': 9, 'knn_unsafe_count': 9, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 10, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 31, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 36, 'candidate_false_high_priority_delay_queue': 1, 'high_priority': 11, 'no_candidate_high_priority_delay_queue': 7}, 'accepted_reason_counts': {'high_priority': 11}, 'oracle_high_roi_count': 17, 'max_accepted_batch_roi_label': 33.70098114013672}}}
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
    "below_batch_threshold_delay_queue": 244,
    "candidate_false_high_priority_delay_queue": 2,
    "high_priority": 35,
    "no_candidate_high_priority_delay_queue": 11
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 35,
    "accepted_batch_rate": 0.11986301369863013,
    "accepted_batch_roi": 19.615722810796328,
    "accepted_batch_roi_ci_low": 10.55840602117137,
    "accepted_batch_roi_positive_count": 35,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 35
    },
    "coverage": 0.9691780821917808,
    "coverage_non_ood_count": 283,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 244,
      "candidate_false_high_priority_delay_queue": 2,
      "high_priority": 35,
      "no_candidate_high_priority_delay_queue": 11
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
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_roi_unsafe_count": 0,
    "knn_unsafe_count": 113,
    "ood_count": 9,
    "ood_rate": 0.030821917808219176,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "total": 292,
    "unsafe_label_count": 83,
    "unsafe_or_ood_count": 130
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
  "production_block_reasons": [],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.6510290503501892,
      "batch_thresholds_by_family": {},
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.55,
      "candidate_delay_score_penalty": 1.5,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_threshold": 0.34849220302706996,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 210,
        "high_priority": 615
      },
      "min_neighbor_accepted_batch_roi": null,
      "min_neighbor_accepted_batch_roi_ci_low": null,
      "safe_radius": 20.984461764702214,
      "scope": "global",
      "train_count": 825
    },
    "groups": {
      "005": {
        "batch_threshold": 0.6510290503501892,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.34849220302706996,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "005",
        "label_counts": {
          "delay_queue": 13,
          "high_priority": 9
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 5.918602128641101,
        "scope": "scale",
        "train_count": 22
      },
      "010": {
        "batch_threshold": 0.6510290503501892,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.34849220302706996,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "010",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 36
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 4.016499590204356,
        "scope": "scale",
        "train_count": 62
      },
      "020": {
        "batch_threshold": 0.6510290503501892,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.34849220302706996,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020",
        "label_counts": {
          "delay_queue": 128,
          "high_priority": 366
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 5.767933814338349,
        "scope": "scale",
        "train_count": 494
      },
      "030": {
        "batch_threshold": 0.6510290503501892,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.34849220302706996,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "030",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 95
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 7.8609542423364775,
        "scope": "scale",
        "train_count": 121
      },
      "050": {
        "batch_threshold": 0.6510290503501892,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.34849220302706996,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "050",
        "label_counts": {
          "delay_queue": 17,
          "high_priority": 82
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 8.997905965950347,
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
        "accepted_batch_count": 10,
        "accepted_batch_rate": 0.08064516129032258,
        "accepted_batch_roi": 30.654070270061492,
        "accepted_batch_roi_ci_low": 7.547974879593443,
        "accepted_batch_roi_positive_count": 10,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 10
        },
        "coverage": 0.9919354838709677,
        "coverage_non_ood_count": 123,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 111,
          "high_priority": 10,
          "no_candidate_high_priority_delay_queue": 3
        },
        "delay_count": 114,
        "delay_label_count": 122,
        "delay_rate": 0.9193548387096774,
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
        "knn_unsafe_count": 45,
        "max_accepted_batch_roi_label": 106.158935546875,
        "ood_count": 1,
        "ood_rate": 0.008064516129032258,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7224598312333834,
        "total": 124,
        "unsafe_label_count": 31,
        "unsafe_or_ood_count": 56
      },
      "random-wave": {
        "accepted_batch_count": 14,
        "accepted_batch_rate": 0.12389380530973451,
        "accepted_batch_roi": 21.08774014775242,
        "accepted_batch_roi_ci_low": 7.28975521389585,
        "accepted_batch_roi_positive_count": 14,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 14
        },
        "coverage": 0.9823008849557522,
        "coverage_non_ood_count": 111,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 97,
          "candidate_false_high_priority_delay_queue": 1,
          "high_priority": 14,
          "no_candidate_high_priority_delay_queue": 1
        },
        "delay_count": 99,
        "delay_label_count": 124,
        "delay_rate": 0.8761061946902655,
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
        "max_accepted_batch_roi_label": 79.51943969726562,
        "ood_count": 2,
        "ood_rate": 0.017699115044247787,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7846829880728186,
        "total": 113,
        "unsafe_label_count": 43,
        "unsafe_or_ood_count": 64
      },
      "sector-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_rate": 0.2,
        "accepted_batch_roi": 7.707384873520244,
        "accepted_batch_roi_ci_low": 1.578762386029906,
        "accepted_batch_roi_positive_count": 11,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 11
        },
        "coverage": 0.8909090909090909,
        "coverage_non_ood_count": 49,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 36,
          "candidate_false_high_priority_delay_queue": 1,
          "high_priority": 11,
          "no_candidate_high_priority_delay_queue": 7
        },
        "delay_count": 44,
        "delay_label_count": 31,
        "delay_rate": 0.8,
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
        "knn_unsafe_count": 9,
        "max_accepted_batch_roi_label": 33.70098114013672,
        "ood_count": 6,
        "ood_rate": 0.10909090909090909,
        "oracle_high_roi_count": 17,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7411599827511859,
        "total": 55,
        "unsafe_label_count": 9,
        "unsafe_or_ood_count": 10
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 35,
    "accepted_batch_rate": 0.11986301369863013,
    "accepted_batch_roi": 19.615722810796328,
    "accepted_batch_roi_ci_low": 10.55840602117137,
    "accepted_batch_roi_positive_count": 35,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 35
    },
    "coverage": 0.9691780821917808,
    "coverage_non_ood_count": 283,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 244,
      "candidate_false_high_priority_delay_queue": 2,
      "high_priority": 35,
      "no_candidate_high_priority_delay_queue": 11
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
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_roi_unsafe_count": 0,
    "knn_unsafe_count": 113,
    "ood_count": 9,
    "ood_rate": 0.030821917808219176,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "total": 292,
    "unsafe_label_count": 83,
    "unsafe_or_ood_count": 130
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
