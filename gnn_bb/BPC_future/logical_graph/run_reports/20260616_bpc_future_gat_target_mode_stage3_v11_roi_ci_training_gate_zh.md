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
sample_count = 324
candidate_count = 4599
family_counts = {'greedy-anchor': 54, 'random-wave': 197, 'sector-wave': 73}
task_count_counts = {'10': 8, '100': 1, '20': 144, '30': 76, '5': 2, '50': 93}
training_objective = precision_constrained_roi_maximization
hard_roi_threshold = 0.65
loss_options = {'false_high_priority_loss_multiplier': 4.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}
pairwise_ranking_loss_active = true
pairwise_ranking_status = active_same_context_roi_margin_ranking
context_pair_stats = {'all': {'sample_count': 324, 'context_count': 294, 'multi_context_count': 10, 'same_context_pair_count': 67, 'same_context_comparable_pair_count': 66, 'positive_negative_label_pair_count': 11, 'roi_diverse_context_count': 10, 'largest_context_size': 5}, 'train': {'sample_count': 222, 'context_count': 216, 'multi_context_count': 2, 'same_context_pair_count': 12, 'same_context_comparable_pair_count': 12, 'positive_negative_label_pair_count': 3, 'roi_diverse_context_count': 2, 'largest_context_size': 4}, 'validation': {'sample_count': 102, 'context_count': 78, 'multi_context_count': 8, 'same_context_pair_count': 55, 'same_context_comparable_pair_count': 54, 'positive_negative_label_pair_count': 8, 'roi_diverse_context_count': 8, 'largest_context_size': 5}}
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
rejected_checkpoint_reasons = ['knn_ood_audit_missing']
rejected_checkpoint_reason_categories = ['knn_ood_audit_missing']
best_epoch = 8
selected_validation_loss = 2.737273688380344
best_loss_epoch = 7
best_validation_loss = 2.589875146866036
best_loss_epoch_gate_pass = true
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run']
attempted_update_count = 1872
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
    "family_holdout_measured_family_count": 2,
    "family_holdout_min_accepted_roi": 1.1059776544570923,
    "family_holdout_min_precision": 1.0,
    "family_holdout_missing_accepted_families": [
      "greedy-anchor"
    ],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "family_holdout_per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 0,
        "accepted_batch_roi": 0.0,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 1,
        "accepted_batch_roi": 1.1059776544570923,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 5,
        "safe_precision": 1.0,
        "total_batches": 42
      },
      "sector-wave": {
        "accepted_batch_count": 21,
        "accepted_batch_roi": 14.337164829174677,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "total_batches": 46
      }
    },
    "family_specific_delay_fallback_families": [
      "greedy-anchor"
    ],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 0,
        "accepted_batch_roi": 0.0,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 1,
        "accepted_batch_roi": 1.1059776544570923,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 5,
        "safe_precision": 1.0,
        "total_batches": 42
      },
      "sector-wave": {
        "accepted_batch_count": 21,
        "accepted_batch_roi": 14.337164829174677,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "total_batches": 46
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
      "random-wave": 155,
      "sector-wave": 27
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
    "validation_context_count": 78,
    "validation_family_counts": {
      "greedy-anchor": 14,
      "random-wave": 42,
      "sector-wave": 46
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
    "best_local_rejected_reasons": [],
    "best_rejected_reasons": [
      "knn_ood_audit_missing"
    ],
    "candidate_count": 1,
    "feasible_threshold_count": 1,
    "selected_metrics": {
      "accepted_batch_count": 22,
      "accepted_batch_precision": 1.0,
      "accepted_batch_rate": 0.21568627450980393,
      "accepted_batch_roi": 13.735747230323879,
      "accepted_batch_roi_ci_low": 8.516215416032171,
      "accepted_batch_roi_over_baseline": 13.28574723032388,
      "accepted_batch_roi_over_baseline_ci_low": 8.066215416032172,
      "accepted_batch_roi_over_best_rc_baseline": 13.28574723032388,
      "accepted_batch_roi_over_best_rc_baseline_ci_low": 8.066215416032172,
      "accepted_batch_roi_over_old_gat_baseline": 13.28574723032388,
      "accepted_batch_roi_over_old_gat_baseline_ci_low": 8.066215416032172,
      "accepted_batch_roi_over_random_baseline": 13.28574723032388,
      "accepted_batch_roi_over_random_baseline_ci_low": 8.066215416032172,
      "baseline_roi_ci_high": 0.45,
      "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
      "baseline_selection_roi": 0.45,
      "batch_threshold": 0.5520985722541809,
      "batch_thresholds_by_family": {},
      "best_rc_baseline_accepted_batch_roi": 0.45,
      "candidate_threshold": 0.24711552262306213,
      "checkpoint_gate_pass": false,
      "checkpoint_gate_reject_reasons": [
        "knn_ood_audit_missing"
      ],
      "context_delay_fallback_contexts": [],
      "coverage_non_ood": 1.0,
      "delay_label_count": 77,
      "delay_rate": 0.7843137254901961,
      "expected_trajectory_utility": 13.75165632123297,
      "false_high_priority_on_delay": 0.0,
      "false_high_priority_on_delay_count": 0,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 0.0,
      "family_delay_fallback_families": [],
      "family_holdout_min_accepted_roi": 1.1059776544570923,
      "family_holdout_min_precision": 1.0,
      "family_holdout_missing_accepted_families": [
        "greedy-anchor"
      ],
      "family_holdout_missing_accepted_opportunity_families": [],
      "family_holdout_oracle_high_roi_families": [
        "random-wave",
        "sector-wave"
      ],
      "family_holdout_per_family": {
        "greedy-anchor": {
          "accepted_batch_count": 0,
          "accepted_batch_roi": 0.0,
          "max_accepted_batch_roi_label": 0.4039181172847748,
          "oracle_high_roi_count": 0,
          "safe_precision": null,
          "total_batches": 14
        },
        "random-wave": {
          "accepted_batch_count": 1,
          "accepted_batch_roi": 1.1059776544570923,
          "max_accepted_batch_roi_label": 4.385624885559082,
          "oracle_high_roi_count": 5,
          "safe_precision": 1.0,
          "total_batches": 42
        },
        "sector-wave": {
          "accepted_batch_count": 21,
          "accepted_batch_roi": 14.337164829174677,
          "max_accepted_batch_roi_label": 41.31852722167969,
          "oracle_high_roi_count": 22,
          "safe_precision": 1.0,
          "total_batches": 46
        }
      },
      "family_specific_delay_fallback_families": [
        "greedy-anchor"
      ],
      "hard_reject_reason_categories": [
        "knn_ood_audit_missing"
      ],
      "high_priority_precision": 1.0,
      "high_priority_precision_ci_low": 0.9961769098731579,
      "high_priority_prediction_count": 1001,
      "high_priority_true_positive_count": 1001,
      "old_gat_baseline_accepted_batch_roi": 0.45,
      "random_baseline_accepted_batch_roi": 0.45,
      "safe_precision": 1.0,
      "safe_precision_ci_low": 0.8513404742740388,
      "threshold": 0.5520985722541809,
      "threshold_local_gate_pass": true,
      "threshold_local_hard_reject_reason_categories": [],
      "threshold_local_reject_reasons": [],
      "threshold_mode": "separate_batch_candidate",
      "total_batches": 102
    }
  },
  "train_deployment_metrics": {
    "accepted_batch_count": 21,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.0945945945945946,
    "accepted_batch_roi": 3.8581707874933877,
    "accepted_batch_roi_ci_low": 0.6270297279541115,
    "accepted_batch_roi_over_baseline": 3.4081707874933875,
    "accepted_batch_roi_over_baseline_ci_low": 0.17702972795411148,
    "accepted_batch_roi_over_best_rc_baseline": 3.4081707874933875,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.17702972795411148,
    "accepted_batch_roi_over_old_gat_baseline": 3.4081707874933875,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.17702972795411148,
    "accepted_batch_roi_over_random_baseline": 3.4081707874933875,
    "accepted_batch_roi_over_random_baseline_ci_low": 0.17702972795411148,
    "baseline_roi_ci_high": 0.45,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.45,
    "batch_threshold": 0.5520985722541809,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.45,
    "candidate_threshold": 0.24711552262306213,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 245,
    "delay_rate": 0.9054054054054054,
    "expected_trajectory_utility": 3.898646977969578,
    "false_high_priority_on_delay": 0.2530612244897959,
    "false_high_priority_on_delay_count": 62,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.2530612244897959,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_roi": 1.043739914894104,
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
        "accepted_batch_count": 1,
        "accepted_batch_roi": 1.043739914894104,
        "max_accepted_batch_roi_label": 1.043739914894104,
        "oracle_high_roi_count": 1,
        "safe_precision": 1.0,
        "total_batches": 40
      },
      "random-wave": {
        "accepted_batch_count": 16,
        "accepted_batch_roi": 4.274850144982338,
        "max_accepted_batch_roi_label": 35.64057159423828,
        "oracle_high_roi_count": 14,
        "safe_precision": 1.0,
        "total_batches": 155
      },
      "sector-wave": {
        "accepted_batch_count": 4,
        "accepted_batch_roi": 2.8950610756874084,
        "max_accepted_batch_roi_label": 7.900282859802246,
        "oracle_high_roi_count": 5,
        "safe_precision": 1.0,
        "total_batches": 27
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "false_high_priority_on_delay_too_high",
      "false_safe_too_high",
      "knn_ood_audit_missing",
      "precision_ci_below_gate",
      "roi_ci_below_baseline"
    ],
    "high_priority_precision": 0.9801282051282051,
    "high_priority_precision_ci_low": 0.9746081848179461,
    "high_priority_prediction_count": 3120,
    "high_priority_true_positive_count": 3058,
    "old_gat_baseline_accepted_batch_roi": 0.45,
    "random_baseline_accepted_batch_roi": 0.45,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8453561767357979,
    "threshold": 0.5520985722541809,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "false_high_priority_on_delay_too_high",
      "false_safe_too_high",
      "precision_ci_below_gate",
      "roi_ci_below_baseline"
    ],
    "threshold_local_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high"
    ],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 222
  },
  "validation_deployment_metrics": {
    "accepted_batch_count": 22,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.21568627450980393,
    "accepted_batch_roi": 13.735747230323879,
    "accepted_batch_roi_ci_low": 8.516215416032171,
    "accepted_batch_roi_over_baseline": 13.28574723032388,
    "accepted_batch_roi_over_baseline_ci_low": 8.066215416032172,
    "accepted_batch_roi_over_best_rc_baseline": 13.28574723032388,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 8.066215416032172,
    "accepted_batch_roi_over_old_gat_baseline": 13.28574723032388,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 8.066215416032172,
    "accepted_batch_roi_over_random_baseline": 13.28574723032388,
    "accepted_batch_roi_over_random_baseline_ci_low": 8.066215416032172,
    "baseline_roi_ci_high": 0.45,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.45,
    "batch_threshold": 0.5520985722541809,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.45,
    "candidate_threshold": 0.24711552262306213,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 77,
    "delay_rate": 0.7843137254901961,
    "expected_trajectory_utility": 13.75165632123297,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.0,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_roi": 1.1059776544570923,
    "family_holdout_min_precision": 1.0,
    "family_holdout_missing_accepted_families": [
      "greedy-anchor"
    ],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "random-wave",
      "sector-wave"
    ],
    "family_holdout_per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 0,
        "accepted_batch_roi": 0.0,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 1,
        "accepted_batch_roi": 1.1059776544570923,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 5,
        "safe_precision": 1.0,
        "total_batches": 42
      },
      "sector-wave": {
        "accepted_batch_count": 21,
        "accepted_batch_roi": 14.337164829174677,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "total_batches": 46
      }
    },
    "family_specific_delay_fallback_families": [
      "greedy-anchor"
    ],
    "hard_reject_reason_categories": [
      "knn_ood_audit_missing"
    ],
    "high_priority_precision": 1.0,
    "high_priority_precision_ci_low": 0.9961769098731579,
    "high_priority_prediction_count": 1001,
    "high_priority_true_positive_count": 1001,
    "old_gat_baseline_accepted_batch_roi": 0.45,
    "random_baseline_accepted_batch_roi": 0.45,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8513404742740388,
    "threshold": 0.5520985722541809,
    "threshold_local_gate_pass": true,
    "threshold_local_hard_reject_reason_categories": [],
    "threshold_local_reject_reasons": [],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 102
  }
}
```

## 边界

- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；
- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；
- 当前 checkpoint 仍 `production_ready=false`；
- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；
- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。
