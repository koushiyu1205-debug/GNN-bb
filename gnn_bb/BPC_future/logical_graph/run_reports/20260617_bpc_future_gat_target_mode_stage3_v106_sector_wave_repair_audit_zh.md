# 2026-06-17 BPC_future GAT Target Mode Stage 3 v106 Sector-wave Repair Audit 报告

## 结论

本报告只做离线 Stage 3 诊断：读取 v105 coverage frontier，重放各 run 的 best coverage candidate，定位 sector-wave high-ROI miss 和 low-ROI accept 的 context-local 修复方向。

```text
focus_family = sector-wave
run_count = 3
recommended_next_step = collect_or_train_same_context_sector_wave_high_roi_vs_low_roi_contrast
stage3_completed = false
stage4_candidate_ready = false
selector_can_certificate = false
```

## Run Comparison

| run | high-ROI | accepted high-ROI | missed high-ROI | low-ROI/bad accepts | capture | primary actions |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v99 | 18 | 18 | 0 | 11 | 1.0000 | {'low_roi_acceptance_suppression': 11, 'no_sector_wave_repair_needed': 4} |
| v102 | 18 | 3 | 15 | 6 | 0.1667 | {'delay_risk_or_risk_adjusted_score_repair': 3, 'low_roi_acceptance_suppression': 4, 'no_sector_wave_repair_needed': 6, 'same_context_high_roi_vs_low_roi_contrast': 2} |
| v103 | 18 | 3 | 15 | 7 | 0.1667 | {'delay_risk_or_risk_adjusted_score_repair': 3, 'low_roi_acceptance_suppression': 5, 'no_sector_wave_repair_needed': 5, 'same_context_high_roi_vs_low_roi_contrast': 2} |

## Top Contexts

### v99

```json
{
  "context_repair_rows_path": "BPC_future/results/gat_batch_impact_sector_wave_repair_v106_v105_frontier_20260617/v99_sector-wave_context_repair_rows.jsonl",
  "missed_high_roi_path": "BPC_future/results/gat_batch_impact_sector_wave_repair_v106_v105_frontier_20260617/v99_sector-wave_missed_high_roi.jsonl",
  "missed_reason_counts": {},
  "selected_threshold": {
    "accepted_batch_count": 54,
    "accepted_batch_roi": 3.6421064379890056,
    "accepted_batch_roi_ci_low": 1.604991839953049,
    "batch_threshold": 0.0,
    "candidate_admission_score_mode": "high_priority",
    "candidate_delay_gate_enabled": false,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 0.0,
    "candidate_threshold": 0.0,
    "coverage_constraint_pass": false,
    "coverage_reject_reasons": [
      "false_high_priority_on_delay_above_coverage_limit",
      "false_safe_rate_union_above_coverage_limit"
    ],
    "false_safe_rate_union": 1.0,
    "safe_precision_ci_low": 0.9335841332189981,
    "sector_wave_accepted_high_roi_count": 18,
    "sector_wave_oracle_high_roi_count": 18,
    "threshold_local_gate_pass": false,
    "threshold_local_reject_reasons": [
      "high_priority_precision_ci_low_below_threshold_or_not_measurable",
      "candidate_threshold_zero_disables_candidate_head_filter",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "threshold_scope": "global"
  },
  "top_context_repair_rows": [
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "02259d538b5f4b8d",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "1205094f54e7f599",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "17ccb5dc2e9bbac0",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "1f855fbf33f8155e",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "3adafd77c6d915d3",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 1,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "3d1bd8618099b573",
      "high_roi_capture_rate": 1.0,
      "high_roi_opportunity_count": 1,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 2,
      "task_count_counts": {
        "20": 2
      }
    },
    {
      "accepted_high_roi_count": 1,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "45baa40751a0bf77",
      "high_roi_capture_rate": 1.0,
      "high_roi_opportunity_count": 1,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 5,
      "task_count_counts": {
        "20": 5
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "71b6550435f541fe",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "ae5a79f7507b389f",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "c9ce44041df47f36",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    }
  ]
}
```

### v102

```json
{
  "context_repair_rows_path": "BPC_future/results/gat_batch_impact_sector_wave_repair_v106_v105_frontier_20260617/v102_sector-wave_context_repair_rows.jsonl",
  "missed_high_roi_path": "BPC_future/results/gat_batch_impact_sector_wave_repair_v106_v105_frontier_20260617/v102_sector-wave_missed_high_roi.jsonl",
  "missed_reason_counts": {
    "candidate_delay_risk_above_threshold": 15,
    "candidate_risk_adjusted_below_threshold": 15,
    "no_candidate_above_threshold": 15
  },
  "selected_threshold": {
    "accepted_batch_count": 18,
    "accepted_batch_roi": 0.5027831030181713,
    "accepted_batch_roi_ci_low": 0.2997363556908496,
    "batch_threshold": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 2.0,
    "candidate_threshold": 0.15007750573798778,
    "coverage_constraint_pass": false,
    "coverage_reject_reasons": [
      "safe_precision_ci_low_below_coverage_limit"
    ],
    "false_safe_rate_union": 0.0,
    "safe_precision_ci_low": 0.8241154494176252,
    "sector_wave_accepted_high_roi_count": 3,
    "sector_wave_oracle_high_roi_count": 18,
    "threshold_local_gate_pass": false,
    "threshold_local_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "accepted_batch_roi_below_baseline_margin",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "threshold_scope": "global"
  },
  "top_context_repair_rows": [
    {
      "accepted_high_roi_count": 1,
      "accepted_low_roi_or_bad_count": 0,
      "context_hash": "ac15bc4e7e3d6fff",
      "high_roi_capture_rate": 0.14285714285714285,
      "high_roi_opportunity_count": 7,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": 31.935651779174805,
      "mean_missed_batch_margin": 0.47604458034038544,
      "mean_missed_safe_candidate_margin": -0.02681125040603969,
      "missed_high_roi_count": 6,
      "missed_reason_counts": {
        "candidate_delay_risk_above_threshold": 6,
        "candidate_risk_adjusted_below_threshold": 6,
        "no_candidate_above_threshold": 6
      },
      "primary_repair_action": "delay_risk_or_risk_adjusted_score_repair",
      "record_count": 12,
      "task_count_counts": {
        "20": 12
      }
    },
    {
      "accepted_high_roi_count": 1,
      "accepted_low_roi_or_bad_count": 0,
      "context_hash": "9fadf4f7b39742a2",
      "high_roi_capture_rate": 0.2,
      "high_roi_opportunity_count": 5,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": 27.36725425720215,
      "mean_missed_batch_margin": 0.4732007756829262,
      "mean_missed_safe_candidate_margin": -0.027086119479703078,
      "missed_high_roi_count": 4,
      "missed_reason_counts": {
        "candidate_delay_risk_above_threshold": 4,
        "candidate_risk_adjusted_below_threshold": 4,
        "no_candidate_above_threshold": 4
      },
      "primary_repair_action": "delay_risk_or_risk_adjusted_score_repair",
      "record_count": 5,
      "task_count_counts": {
        "20": 5
      }
    },
    {
      "accepted_high_roi_count": 1,
      "accepted_low_roi_or_bad_count": 0,
      "context_hash": "4e481a6307fca228",
      "high_roi_capture_rate": 0.25,
      "high_roi_opportunity_count": 4,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "max_missed_high_roi_label": 7.900282859802246,
      "mean_missed_batch_margin": 0.4798323412736257,
      "mean_missed_safe_candidate_margin": -0.027295334475275712,
      "missed_high_roi_count": 3,
      "missed_reason_counts": {
        "candidate_delay_risk_above_threshold": 3,
        "candidate_risk_adjusted_below_threshold": 3,
        "no_candidate_above_threshold": 3
      },
      "primary_repair_action": "delay_risk_or_risk_adjusted_score_repair",
      "record_count": 7,
      "task_count_counts": {
        "20": 7
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "45baa40751a0bf77",
      "high_roi_capture_rate": 0.0,
      "high_roi_opportunity_count": 1,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "max_missed_high_roi_label": 13.436327934265137,
      "mean_missed_batch_margin": 0.47260919213294983,
      "mean_missed_safe_candidate_margin": -0.030077336943372265,
      "missed_high_roi_count": 1,
      "missed_reason_counts": {
        "candidate_delay_risk_above_threshold": 1,
        "candidate_risk_adjusted_below_threshold": 1,
        "no_candidate_above_threshold": 1
      },
      "primary_repair_action": "same_context_high_roi_vs_low_roi_contrast",
      "record_count": 5,
      "task_count_counts": {
        "20": 5
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "3d1bd8618099b573",
      "high_roi_capture_rate": 0.0,
      "high_roi_opportunity_count": 1,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": 13.129931449890137,
      "mean_missed_batch_margin": 0.47142356634140015,
      "mean_missed_safe_candidate_margin": -0.026812396311212003,
      "missed_high_roi_count": 1,
      "missed_reason_counts": {
        "candidate_delay_risk_above_threshold": 1,
        "candidate_risk_adjusted_below_threshold": 1,
        "no_candidate_above_threshold": 1
      },
      "primary_repair_action": "same_context_high_roi_vs_low_roi_contrast",
      "record_count": 2,
      "task_count_counts": {
        "20": 2
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "02259d538b5f4b8d",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "1205094f54e7f599",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "1f855fbf33f8155e",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "dfd68d5873b84183",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 0,
      "context_hash": "17ccb5dc2e9bbac0",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "no_sector_wave_repair_needed",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    }
  ]
}
```

### v103

```json
{
  "context_repair_rows_path": "BPC_future/results/gat_batch_impact_sector_wave_repair_v106_v105_frontier_20260617/v103_sector-wave_context_repair_rows.jsonl",
  "missed_high_roi_path": "BPC_future/results/gat_batch_impact_sector_wave_repair_v106_v105_frontier_20260617/v103_sector-wave_missed_high_roi.jsonl",
  "missed_reason_counts": {
    "candidate_risk_adjusted_below_threshold": 15,
    "no_candidate_above_threshold": 15
  },
  "selected_threshold": {
    "accepted_batch_count": 19,
    "accepted_batch_roi": 0.47668465815092387,
    "accepted_batch_roi_ci_low": 0.277958020798426,
    "batch_threshold": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.6,
    "candidate_delay_score_penalty": 1.0,
    "candidate_threshold": 0.24574109176330694,
    "coverage_constraint_pass": false,
    "coverage_reject_reasons": [
      "safe_precision_ci_low_below_coverage_limit"
    ],
    "false_safe_rate_union": 0.0,
    "safe_precision_ci_low": 0.8318156346315495,
    "sector_wave_accepted_high_roi_count": 3,
    "sector_wave_oracle_high_roi_count": 18,
    "threshold_local_gate_pass": false,
    "threshold_local_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "accepted_batch_roi_below_baseline_margin",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "threshold_scope": "global"
  },
  "top_context_repair_rows": [
    {
      "accepted_high_roi_count": 1,
      "accepted_low_roi_or_bad_count": 0,
      "context_hash": "ac15bc4e7e3d6fff",
      "high_roi_capture_rate": 0.14285714285714285,
      "high_roi_opportunity_count": 7,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": 31.935651779174805,
      "mean_missed_batch_margin": 0.48132983843485516,
      "mean_missed_safe_candidate_margin": -0.027138446112087305,
      "missed_high_roi_count": 6,
      "missed_reason_counts": {
        "candidate_risk_adjusted_below_threshold": 6,
        "no_candidate_above_threshold": 6
      },
      "primary_repair_action": "delay_risk_or_risk_adjusted_score_repair",
      "record_count": 12,
      "task_count_counts": {
        "20": 12
      }
    },
    {
      "accepted_high_roi_count": 1,
      "accepted_low_roi_or_bad_count": 0,
      "context_hash": "9fadf4f7b39742a2",
      "high_roi_capture_rate": 0.2,
      "high_roi_opportunity_count": 5,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": 27.36725425720215,
      "mean_missed_batch_margin": 0.47796596586704254,
      "mean_missed_safe_candidate_margin": -0.02891620569535469,
      "missed_high_roi_count": 4,
      "missed_reason_counts": {
        "candidate_risk_adjusted_below_threshold": 4,
        "no_candidate_above_threshold": 4
      },
      "primary_repair_action": "delay_risk_or_risk_adjusted_score_repair",
      "record_count": 5,
      "task_count_counts": {
        "20": 5
      }
    },
    {
      "accepted_high_roi_count": 1,
      "accepted_low_roi_or_bad_count": 0,
      "context_hash": "4e481a6307fca228",
      "high_roi_capture_rate": 0.25,
      "high_roi_opportunity_count": 4,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "max_missed_high_roi_label": 7.900282859802246,
      "mean_missed_batch_margin": 0.48495031396547955,
      "mean_missed_safe_candidate_margin": -0.026718990899256667,
      "missed_high_roi_count": 3,
      "missed_reason_counts": {
        "candidate_risk_adjusted_below_threshold": 3,
        "no_candidate_above_threshold": 3
      },
      "primary_repair_action": "delay_risk_or_risk_adjusted_score_repair",
      "record_count": 7,
      "task_count_counts": {
        "20": 7
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "45baa40751a0bf77",
      "high_roi_capture_rate": 0.0,
      "high_roi_opportunity_count": 1,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "max_missed_high_roi_label": 13.436327934265137,
      "mean_missed_batch_margin": 0.46710219979286194,
      "mean_missed_safe_candidate_margin": -0.03524219770333836,
      "missed_high_roi_count": 1,
      "missed_reason_counts": {
        "candidate_risk_adjusted_below_threshold": 1,
        "no_candidate_above_threshold": 1
      },
      "primary_repair_action": "same_context_high_roi_vs_low_roi_contrast",
      "record_count": 5,
      "task_count_counts": {
        "20": 5
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "3d1bd8618099b573",
      "high_roi_capture_rate": 0.0,
      "high_roi_opportunity_count": 1,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": 13.129931449890137,
      "mean_missed_batch_margin": 0.4694955348968506,
      "mean_missed_safe_candidate_margin": -0.030585010458928252,
      "missed_high_roi_count": 1,
      "missed_reason_counts": {
        "candidate_risk_adjusted_below_threshold": 1,
        "no_candidate_above_threshold": 1
      },
      "primary_repair_action": "same_context_high_roi_vs_low_roi_contrast",
      "record_count": 2,
      "task_count_counts": {
        "20": 2
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "02259d538b5f4b8d",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "1205094f54e7f599",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "1f855fbf33f8155e",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "3adafd77c6d915d3",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    },
    {
      "accepted_high_roi_count": 0,
      "accepted_low_roi_or_bad_count": 1,
      "context_hash": "dfd68d5873b84183",
      "high_roi_capture_rate": null,
      "high_roi_opportunity_count": 0,
      "instance": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "max_missed_high_roi_label": null,
      "mean_missed_batch_margin": null,
      "mean_missed_safe_candidate_margin": null,
      "missed_high_roi_count": 0,
      "missed_reason_counts": {},
      "primary_repair_action": "low_roi_acceptance_suppression",
      "record_count": 1,
      "task_count_counts": {
        "20": 1
      }
    }
  ]
}
```

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

这些 context 只能指导 Stage 2/3 数据采集和训练；不能作为 HIGH_PRIORITY admission、pricing oracle 或 certificate 依据。最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
