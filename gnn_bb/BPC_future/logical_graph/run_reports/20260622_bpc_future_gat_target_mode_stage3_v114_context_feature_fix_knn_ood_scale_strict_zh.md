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
batch_threshold = 0.4893101453781128
candidate_threshold = 0.2156521021231845
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
decision_record_count = 326
validation_metrics = {'total': 326, 'coverage_non_ood_count': 312, 'coverage': 0.9570552147239264, 'ood_count': 14, 'ood_rate': 0.04294478527607362, 'delay_count': 291, 'delay_rate': 0.8926380368098159, 'accepted_batch_count': 35, 'accepted_batch_rate': 0.10736196319018405, 'accepted_batch_roi_positive_count': 35, 'accepted_batch_roi': 4.6058581354894805, 'accepted_batch_roi_ci_low': 2.28981506277122, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.9010957324106112, 'unsafe_label_count': 90, 'knn_unsafe_count': 165, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 178, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 286, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 11, 'high_priority': 35, 'no_candidate_high_priority_delay_queue': 280}, 'accepted_reason_counts': {'high_priority': 35}}
validation_family_metrics = {'family_count': 3, 'missing_accepted_families': [], 'missing_accepted_opportunity_families': [], 'family_specific_delay_fallback_families': [], 'oracle_high_roi_families': ['greedy-anchor', 'random-wave', 'sector-wave'], 'per_family': {'greedy-anchor': {'total': 124, 'coverage_non_ood_count': 119, 'coverage': 0.9596774193548387, 'ood_count': 5, 'ood_rate': 0.04032258064516129, 'delay_count': 115, 'delay_rate': 0.9274193548387096, 'accepted_batch_count': 9, 'accepted_batch_rate': 0.07258064516129033, 'accepted_batch_roi_positive_count': 9, 'accepted_batch_roi': 3.751724203427633, 'accepted_batch_roi_ci_low': 1.103745492694029, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7008472464490406, 'unsafe_label_count': 31, 'knn_unsafe_count': 66, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 70, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 122, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 4, 'high_priority': 9, 'no_candidate_high_priority_delay_queue': 111}, 'accepted_reason_counts': {'high_priority': 9}, 'oracle_high_roi_count': 20, 'max_accepted_batch_roi_label': 106.158935546875}, 'random-wave': {'total': 132, 'coverage_non_ood_count': 129, 'coverage': 0.9772727272727273, 'ood_count': 3, 'ood_rate': 0.022727272727272728, 'delay_count': 117, 'delay_rate': 0.8863636363636364, 'accepted_batch_count': 15, 'accepted_batch_rate': 0.11363636363636363, 'accepted_batch_roi_positive_count': 15, 'accepted_batch_roi': 3.6985094266633194, 'accepted_batch_roi_ci_low': 1.2010461958876473, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7961107336956521, 'unsafe_label_count': 46, 'knn_unsafe_count': 85, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 90, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 127, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 1, 'high_priority': 15, 'no_candidate_high_priority_delay_queue': 116}, 'accepted_reason_counts': {'high_priority': 15}, 'oracle_high_roi_count': 34, 'max_accepted_batch_roi_label': 79.51943969726562}, 'sector-wave': {'total': 70, 'coverage_non_ood_count': 64, 'coverage': 0.9142857142857143, 'ood_count': 6, 'ood_rate': 0.08571428571428572, 'delay_count': 59, 'delay_rate': 0.8428571428571429, 'accepted_batch_count': 11, 'accepted_batch_rate': 0.15714285714285714, 'accepted_batch_roi_positive_count': 11, 'accepted_batch_roi': 6.541988682848486, 'accepted_batch_roi_ci_low': 0.2625358334422545, 'safe_precision': 1.0, 'safe_precision_ci_low': 0.7411599827511859, 'unsafe_label_count': 13, 'knn_unsafe_count': 14, 'knn_roi_unsafe_count': 0, 'unsafe_or_ood_count': 18, 'false_high_priority_on_delay_count': 0, 'delay_label_count': 37, 'false_high_priority_on_delay': 0.0, 'false_safe_ood_count': 0, 'false_safe_rate_ood': 0.0, 'false_safe_knn_unsafe_count': 0, 'false_safe_rate_knn_unsafe': 0.0, 'accepted_knn_roi_unsafe_count': 0, 'accepted_knn_roi_unsafe_rate': None, 'false_safe_label_unsafe_count': 0, 'false_safe_rate_label_unsafe': 0.0, 'false_positive_context_count': 0, 'false_positive_contexts': [], 'false_safe_union_count': 0, 'false_safe_rate_union': 0.0, 'decision_reason_counts': {'below_batch_threshold_delay_queue': 6, 'high_priority': 11, 'no_candidate_high_priority_delay_queue': 53}, 'accepted_reason_counts': {'high_priority': 11}, 'oracle_high_roi_count': 28, 'max_accepted_batch_roi_label': 41.31852722167969}}}
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
    "below_batch_threshold_delay_queue": 11,
    "high_priority": 35,
    "no_candidate_high_priority_delay_queue": 280
  },
  "decision_scope_metrics": {
    "accepted_batch_count": 35,
    "accepted_batch_rate": 0.10736196319018405,
    "accepted_batch_roi": 4.6058581354894805,
    "accepted_batch_roi_ci_low": 2.28981506277122,
    "accepted_batch_roi_positive_count": 35,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 35
    },
    "coverage": 0.9570552147239264,
    "coverage_non_ood_count": 312,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 11,
      "high_priority": 35,
      "no_candidate_high_priority_delay_queue": 280
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
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_roi_unsafe_count": 0,
    "knn_unsafe_count": 165,
    "ood_count": 14,
    "ood_rate": 0.04294478527607362,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "total": 326,
    "unsafe_label_count": 90,
    "unsafe_or_ood_count": 178
  },
  "decision_split_counts": {
    "validation": 326
  },
  "decision_threshold_group_counts": {
    "005": 10,
    "010": 12,
    "020": 228,
    "030": 47,
    "050": 20,
    "global": 9
  },
  "decision_threshold_scope_counts": {
    "global": 9,
    "scale": 317
  },
  "production_block_reasons": [],
  "threshold_group_info": {
    "global": {
      "batch_threshold": 0.4893101453781128,
      "batch_thresholds_by_family": {},
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.55,
      "candidate_delay_score_penalty": 1.5,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_threshold": 0.2156521021231845,
      "context_delay_fallback_contexts": [],
      "family_delay_fallback_families": [],
      "group": "global",
      "label_counts": {
        "delay_queue": 245,
        "high_priority": 650
      },
      "min_neighbor_accepted_batch_roi": null,
      "min_neighbor_accepted_batch_roi_ci_low": null,
      "safe_radius": 16.477040665634608,
      "scope": "global",
      "train_count": 895
    },
    "groups": {
      "005": {
        "batch_threshold": 0.4893101453781128,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.2156521021231845,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "005",
        "label_counts": {
          "delay_queue": 13,
          "high_priority": 9
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 4.15788042101461,
        "scope": "scale",
        "train_count": 22
      },
      "010": {
        "batch_threshold": 0.4893101453781128,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.2156521021231845,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "010",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 36
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 3.5398492494113545,
        "scope": "scale",
        "train_count": 62
      },
      "020": {
        "batch_threshold": 0.4893101453781128,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.2156521021231845,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "020",
        "label_counts": {
          "delay_queue": 163,
          "high_priority": 401
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 4.604428412613674,
        "scope": "scale",
        "train_count": 564
      },
      "030": {
        "batch_threshold": 0.4893101453781128,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.2156521021231845,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "030",
        "label_counts": {
          "delay_queue": 26,
          "high_priority": 95
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 12.60391453405251,
        "scope": "scale",
        "train_count": 121
      },
      "050": {
        "batch_threshold": 0.4893101453781128,
        "batch_thresholds_by_family": {},
        "candidate_admission_score_mode": "risk_adjusted_product",
        "candidate_delay_gate_enabled": true,
        "candidate_delay_risk_threshold": 0.55,
        "candidate_delay_score_penalty": 1.5,
        "candidate_rescue_delay_risk_threshold": 1.0,
        "candidate_rescue_delay_score_penalty": 0.0,
        "candidate_rescue_raw_score_threshold": 1.0,
        "candidate_threshold": 0.2156521021231845,
        "context_delay_fallback_contexts": [],
        "family_delay_fallback_families": [],
        "group": "050",
        "label_counts": {
          "delay_queue": 17,
          "high_priority": 82
        },
        "min_neighbor_accepted_batch_roi": null,
        "min_neighbor_accepted_batch_roi_ci_low": null,
        "safe_radius": 8.33955510931449,
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
        "accepted_batch_count": 9,
        "accepted_batch_rate": 0.07258064516129033,
        "accepted_batch_roi": 3.751724203427633,
        "accepted_batch_roi_ci_low": 1.103745492694029,
        "accepted_batch_roi_positive_count": 9,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 9
        },
        "coverage": 0.9596774193548387,
        "coverage_non_ood_count": 119,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 4,
          "high_priority": 9,
          "no_candidate_high_priority_delay_queue": 111
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
        "false_safe_rate_ood": 0.0,
        "false_safe_rate_union": 0.0,
        "false_safe_union_count": 0,
        "knn_roi_unsafe_count": 0,
        "knn_unsafe_count": 66,
        "max_accepted_batch_roi_label": 106.158935546875,
        "ood_count": 5,
        "ood_rate": 0.04032258064516129,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7008472464490406,
        "total": 124,
        "unsafe_label_count": 31,
        "unsafe_or_ood_count": 70
      },
      "random-wave": {
        "accepted_batch_count": 15,
        "accepted_batch_rate": 0.11363636363636363,
        "accepted_batch_roi": 3.6985094266633194,
        "accepted_batch_roi_ci_low": 1.2010461958876473,
        "accepted_batch_roi_positive_count": 15,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 15
        },
        "coverage": 0.9772727272727273,
        "coverage_non_ood_count": 129,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 1,
          "high_priority": 15,
          "no_candidate_high_priority_delay_queue": 116
        },
        "delay_count": 117,
        "delay_label_count": 127,
        "delay_rate": 0.8863636363636364,
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
        "knn_unsafe_count": 85,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "ood_count": 3,
        "ood_rate": 0.022727272727272728,
        "oracle_high_roi_count": 34,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7961107336956521,
        "total": 132,
        "unsafe_label_count": 46,
        "unsafe_or_ood_count": 90
      },
      "sector-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_rate": 0.15714285714285714,
        "accepted_batch_roi": 6.541988682848486,
        "accepted_batch_roi_ci_low": 0.2625358334422545,
        "accepted_batch_roi_positive_count": 11,
        "accepted_knn_roi_unsafe_count": 0,
        "accepted_knn_roi_unsafe_rate": null,
        "accepted_reason_counts": {
          "high_priority": 11
        },
        "coverage": 0.9142857142857143,
        "coverage_non_ood_count": 64,
        "decision_reason_counts": {
          "below_batch_threshold_delay_queue": 6,
          "high_priority": 11,
          "no_candidate_high_priority_delay_queue": 53
        },
        "delay_count": 59,
        "delay_label_count": 37,
        "delay_rate": 0.8428571428571429,
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
        "knn_unsafe_count": 14,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "ood_count": 6,
        "ood_rate": 0.08571428571428572,
        "oracle_high_roi_count": 28,
        "safe_precision": 1.0,
        "safe_precision_ci_low": 0.7411599827511859,
        "total": 70,
        "unsafe_label_count": 13,
        "unsafe_or_ood_count": 18
      }
    }
  },
  "validation_metrics": {
    "accepted_batch_count": 35,
    "accepted_batch_rate": 0.10736196319018405,
    "accepted_batch_roi": 4.6058581354894805,
    "accepted_batch_roi_ci_low": 2.28981506277122,
    "accepted_batch_roi_positive_count": 35,
    "accepted_knn_roi_unsafe_count": 0,
    "accepted_knn_roi_unsafe_rate": null,
    "accepted_reason_counts": {
      "high_priority": 35
    },
    "coverage": 0.9570552147239264,
    "coverage_non_ood_count": 312,
    "decision_reason_counts": {
      "below_batch_threshold_delay_queue": 11,
      "high_priority": 35,
      "no_candidate_high_priority_delay_queue": 280
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
    "false_safe_rate_ood": 0.0,
    "false_safe_rate_union": 0.0,
    "false_safe_union_count": 0,
    "knn_roi_unsafe_count": 0,
    "knn_unsafe_count": 165,
    "ood_count": 14,
    "ood_rate": 0.04294478527607362,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "total": 326,
    "unsafe_label_count": 90,
    "unsafe_or_ood_count": 178
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
