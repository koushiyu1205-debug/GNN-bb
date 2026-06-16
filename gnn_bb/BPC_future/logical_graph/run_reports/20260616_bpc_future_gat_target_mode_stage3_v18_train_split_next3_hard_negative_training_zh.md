# GAT Batch Impact Training 报告

日期：2026-06-16

## 目的

训练 offline batch-impact GAT checkpoint，目标是 high-precision / high-ROI
admission scheduling，而不是普通分类 F1。该训练不运行 BPC / pricing / RMP，
不生成 certificate 或 official lower bound。

## 机器字段

```text
gat_batch_impact_training = current
status = gat_batch_impact_trained
diagnostic_only = true
runs_bpc_or_pricing = false
sample_count = 354
candidate_count = 4657
family_counts = {'greedy-anchor': 54, 'random-wave': 209, 'sector-wave': 91}
task_count_counts = {'10': 8, '100': 1, '20': 171, '30': 76, '5': 2, '50': 96}
training_objective = precision_constrained_roi_maximization
hard_roi_threshold = 0.65
loss_options = {'false_high_priority_loss_multiplier': 4.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}
pairwise_ranking_loss_active = true
pairwise_ranking_status = active_same_context_roi_margin_ranking
context_pair_stats = {'all': {'sample_count': 354, 'context_count': 295, 'multi_context_count': 15, 'same_context_pair_count': 172, 'same_context_comparable_pair_count': 168, 'positive_negative_label_pair_count': 60, 'roi_diverse_context_count': 15, 'largest_context_size': 8}, 'train': {'sample_count': 235, 'context_count': 216, 'multi_context_count': 6, 'same_context_pair_count': 46, 'same_context_comparable_pair_count': 45, 'positive_negative_label_pair_count': 19, 'roi_diverse_context_count': 6, 'largest_context_size': 7}, 'validation': {'sample_count': 119, 'context_count': 79, 'multi_context_count': 9, 'same_context_pair_count': 126, 'same_context_comparable_pair_count': 123, 'positive_negative_label_pair_count': 41, 'roi_diverse_context_count': 9, 'largest_context_size': 8}}
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
rejected_checkpoint_reasons = ['family_holdout_accepted_roi_below_threshold', 'knn_ood_audit_missing']
rejected_checkpoint_reason_categories = ['holdout_family_collapse', 'knn_ood_audit_missing']
best_epoch = 6
selected_validation_loss = 3.905518565973467
best_loss_epoch = 8
best_validation_loss = 3.092116102176018
best_loss_epoch_gate_pass = false
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['family_holdout_accepted_roi_below_threshold', 'knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run']
attempted_update_count = 2240
nonfinite_skipped_update_count = 0
nonfinite_skipped_update_rate = 0.0
training_stability_reject_reasons = []
production_ready = false
default_enabled = false
all_checks_pass = true
```

## Deployment Metrics

```json
{
  "family_holdout_metrics": {
    "family_count": 3,
    "family_holdout_measured_family_count": 3,
    "family_holdout_min_accepted_high_roi_count": 1,
    "family_holdout_min_accepted_roi": 0.11975858719658088,
    "family_holdout_min_high_roi_capture_rate": 0.16666666666666666,
    "family_holdout_min_precision": 1.0,
    "family_holdout_missing_accepted_families": [],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "family_holdout_per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 6,
        "accepted_batch_roi": 0.11975858719658088,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_roi": 0.2805267370051958,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 22,
        "accepted_batch_roi": 7.598519871858033,
        "accepted_high_roi_count": 11,
        "high_roi_capture_rate": 0.4583333333333333,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "total_batches": 61
      }
    },
    "family_specific_delay_fallback_families": [],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 6,
        "accepted_batch_roi": 0.11975858719658088,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_roi": 0.2805267370051958,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 22,
        "accepted_batch_roi": 7.598519871858033,
        "accepted_high_roi_count": 11,
        "high_roi_capture_rate": 0.4583333333333333,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "total_batches": 61
      }
    }
  },
  "split": {
    "mode": "instance_path",
    "pairwise_split_adjustment": "not_needed_train_has_comparable_pairs",
    "pairwise_train_preserved": true,
    "train_context_count": 216,
    "train_family_counts": {
      "greedy-anchor": 40,
      "random-wave": 165,
      "sector-wave": 30
    },
    "train_instances": [
      "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_01_seed71000_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_02_seed71102_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_04_seed71306_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_05_seed71408_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_01_seed71000_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_04_seed71306_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_03_seed91204_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_04_seed91307_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_04_seed141309_logical_graph.json"
    ],
    "validation_context_count": 79,
    "validation_family_counts": {
      "greedy-anchor": 14,
      "random-wave": 44,
      "sector-wave": 61
    },
    "validation_instances": [
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_03_seed71204_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_03_seed71204_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_03_seed91204_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_04_seed91307_logical_graph.json"
    ]
  },
  "threshold_search": {
    "best_local_rejected_reasons": [
      "family_holdout_accepted_roi_below_threshold"
    ],
    "best_rejected_reasons": [
      "family_holdout_accepted_roi_below_threshold",
      "knn_ood_audit_missing"
    ],
    "candidate_count": 1,
    "feasible_threshold_count": 0,
    "selected_metrics": {
      "accepted_bad_mode_count": 0,
      "accepted_batch_count": 39,
      "accepted_batch_precision": 1.0,
      "accepted_batch_rate": 0.3277310924369748,
      "accepted_batch_roi": 4.3838918669516245,
      "accepted_batch_roi_ci_low": 1.0535803658133176,
      "accepted_batch_roi_over_baseline": 4.3838918669516245,
      "accepted_batch_roi_over_baseline_ci_low": 1.0535803658133176,
      "accepted_batch_roi_over_best_rc_baseline": 4.3838918669516245,
      "accepted_batch_roi_over_best_rc_baseline_ci_low": 1.0535803658133176,
      "accepted_batch_roi_over_old_gat_baseline": 4.3838918669516245,
      "accepted_batch_roi_over_old_gat_baseline_ci_low": 1.0535803658133176,
      "accepted_batch_roi_over_random_baseline": 4.3838918669516245,
      "accepted_batch_roi_over_random_baseline_ci_low": 1.0535803658133176,
      "baseline_roi_ci_high": 0.0,
      "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
      "baseline_selection_roi": 0.0,
      "batch_threshold": 0.0,
      "batch_thresholds_by_family": {},
      "best_rc_baseline_accepted_batch_roi": 0.0,
      "candidate_threshold": 0.7447547316551208,
      "checkpoint_gate_pass": false,
      "checkpoint_gate_reject_reasons": [
        "family_holdout_accepted_roi_below_threshold",
        "knn_ood_audit_missing"
      ],
      "context_delay_fallback_contexts": [],
      "coverage_non_ood": 1.0,
      "delay_label_count": 118,
      "delay_rate": 0.6722689075630253,
      "expected_trajectory_utility": 4.4261995592593175,
      "false_high_priority_on_delay": 0.00847457627118644,
      "false_high_priority_on_delay_count": 1,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 0.00847457627118644,
      "family_delay_fallback_families": [],
      "family_holdout_min_accepted_high_roi_count": 1,
      "family_holdout_min_accepted_roi": 0.11975858719658088,
      "family_holdout_min_high_roi_capture_rate": 0.16666666666666666,
      "family_holdout_min_precision": 1.0,
      "family_holdout_missing_accepted_families": [],
      "family_holdout_missing_accepted_opportunity_families": [],
      "family_holdout_oracle_high_roi_families": [
        "random-wave",
        "sector-wave"
      ],
      "family_holdout_per_family": {
        "greedy-anchor": {
          "accepted_batch_count": 6,
          "accepted_batch_roi": 0.11975858719658088,
          "accepted_high_roi_count": 0,
          "high_roi_capture_rate": null,
          "max_accepted_batch_roi_label": 0.4039181172847748,
          "oracle_high_roi_count": 0,
          "safe_precision": 1.0,
          "total_batches": 14
        },
        "random-wave": {
          "accepted_batch_count": 11,
          "accepted_batch_roi": 0.2805267370051958,
          "accepted_high_roi_count": 1,
          "high_roi_capture_rate": 0.16666666666666666,
          "max_accepted_batch_roi_label": 4.385624885559082,
          "oracle_high_roi_count": 6,
          "safe_precision": 1.0,
          "total_batches": 44
        },
        "sector-wave": {
          "accepted_batch_count": 22,
          "accepted_batch_roi": 7.598519871858033,
          "accepted_high_roi_count": 11,
          "high_roi_capture_rate": 0.4583333333333333,
          "max_accepted_batch_roi_label": 41.31852722167969,
          "oracle_high_roi_count": 24,
          "safe_precision": 1.0,
          "total_batches": 61
        }
      },
      "family_specific_delay_fallback_families": [],
      "hard_reject_reason_categories": [
        "holdout_family_collapse",
        "knn_ood_audit_missing"
      ],
      "high_priority_precision": 0.9987745098039216,
      "high_priority_precision_ci_low": 0.9930910774764203,
      "high_priority_prediction_count": 816,
      "high_priority_true_positive_count": 815,
      "max_accepted_bad_mode_count": 0,
      "min_family_accepted_high_roi_count": 0,
      "min_family_high_roi_capture_rate": 0.0,
      "old_gat_baseline_accepted_batch_roi": 0.0,
      "random_baseline_accepted_batch_roi": 0.0,
      "safe_precision": 1.0,
      "safe_precision_ci_low": 0.910330146399761,
      "threshold": 0.0,
      "threshold_local_gate_pass": false,
      "threshold_local_hard_reject_reason_categories": [
        "holdout_family_collapse"
      ],
      "threshold_local_reject_reasons": [
        "family_holdout_accepted_roi_below_threshold"
      ],
      "threshold_mode": "separate_batch_candidate",
      "total_batches": 119
    }
  },
  "train_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 98,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.41702127659574467,
    "accepted_batch_roi": 0.9075149034262202,
    "accepted_batch_roi_ci_low": 0.17693279563586295,
    "accepted_batch_roi_over_baseline": 0.9075149034262202,
    "accepted_batch_roi_over_baseline_ci_low": 0.17693279563586295,
    "accepted_batch_roi_over_best_rc_baseline": 0.9075149034262202,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.17693279563586295,
    "accepted_batch_roi_over_old_gat_baseline": 0.9075149034262202,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.17693279563586295,
    "accepted_batch_roi_over_random_baseline": 0.9075149034262202,
    "accepted_batch_roi_over_random_baseline_ci_low": 0.17693279563586295,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.0,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_threshold": 0.7447547316551208,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 254,
    "delay_rate": 0.5829787234042554,
    "expected_trajectory_utility": 0.9508822503649957,
    "false_high_priority_on_delay": 0.007874015748031496,
    "false_high_priority_on_delay_count": 2,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.007874015748031496,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 0,
    "family_holdout_min_accepted_roi": 0.20420707909700772,
    "family_holdout_min_high_roi_capture_rate": 0.0,
    "family_holdout_min_precision": 1.0,
    "family_holdout_missing_accepted_families": [],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "greedy-anchor",
      "random-wave",
      "sector-wave"
    ],
    "family_holdout_per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 12,
        "accepted_batch_roi": 0.20420707909700772,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": 0.0,
        "max_accepted_batch_roi_label": 1.043739914894104,
        "oracle_high_roi_count": 1,
        "safe_precision": 1.0,
        "total_batches": 40
      },
      "random-wave": {
        "accepted_batch_count": 70,
        "accepted_batch_roi": 1.1267211699430066,
        "accepted_high_roi_count": 15,
        "high_roi_capture_rate": 0.8333333333333334,
        "max_accepted_batch_roi_label": 35.64057159423828,
        "oracle_high_roi_count": 18,
        "safe_precision": 1.0,
        "total_batches": 165
      },
      "sector-wave": {
        "accepted_batch_count": 16,
        "accepted_batch_roi": 0.4759683556621894,
        "accepted_high_roi_count": 4,
        "high_roi_capture_rate": 0.8,
        "max_accepted_batch_roi_label": 7.900282859802246,
        "oracle_high_roi_count": 5,
        "safe_precision": 1.0,
        "total_batches": 30
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "holdout_family_collapse",
      "knn_ood_audit_missing",
      "roi_ci_below_baseline"
    ],
    "high_priority_precision": 0.9990583804143126,
    "high_priority_precision_ci_low": 0.9965730219176737,
    "high_priority_prediction_count": 2124,
    "high_priority_true_positive_count": 2122,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9622786759045421,
    "threshold": 0.0,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "holdout_family_collapse",
      "roi_ci_below_baseline"
    ],
    "threshold_local_reject_reasons": [
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 235
  },
  "validation_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 39,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.3277310924369748,
    "accepted_batch_roi": 4.3838918669516245,
    "accepted_batch_roi_ci_low": 1.0535803658133176,
    "accepted_batch_roi_over_baseline": 4.3838918669516245,
    "accepted_batch_roi_over_baseline_ci_low": 1.0535803658133176,
    "accepted_batch_roi_over_best_rc_baseline": 4.3838918669516245,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 1.0535803658133176,
    "accepted_batch_roi_over_old_gat_baseline": 4.3838918669516245,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 1.0535803658133176,
    "accepted_batch_roi_over_random_baseline": 4.3838918669516245,
    "accepted_batch_roi_over_random_baseline_ci_low": 1.0535803658133176,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.0,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_threshold": 0.7447547316551208,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "family_holdout_accepted_roi_below_threshold",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 118,
    "delay_rate": 0.6722689075630253,
    "expected_trajectory_utility": 4.4261995592593175,
    "false_high_priority_on_delay": 0.00847457627118644,
    "false_high_priority_on_delay_count": 1,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.00847457627118644,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 1,
    "family_holdout_min_accepted_roi": 0.11975858719658088,
    "family_holdout_min_high_roi_capture_rate": 0.16666666666666666,
    "family_holdout_min_precision": 1.0,
    "family_holdout_missing_accepted_families": [],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "family_holdout_per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 6,
        "accepted_batch_roi": 0.11975858719658088,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_roi": 0.2805267370051958,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 22,
        "accepted_batch_roi": 7.598519871858033,
        "accepted_high_roi_count": 11,
        "high_roi_capture_rate": 0.4583333333333333,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "total_batches": 61
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "holdout_family_collapse",
      "knn_ood_audit_missing"
    ],
    "high_priority_precision": 0.9987745098039216,
    "high_priority_precision_ci_low": 0.9930910774764203,
    "high_priority_prediction_count": 816,
    "high_priority_true_positive_count": 815,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.910330146399761,
    "threshold": 0.0,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "holdout_family_collapse"
    ],
    "threshold_local_reject_reasons": [
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 119
  }
}
```

## 边界

- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；
- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；
- 当前 checkpoint 仍 `production_ready=false`；
- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；
- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。
