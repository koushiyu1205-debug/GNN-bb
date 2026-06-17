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
sample_count = 379
candidate_count = 4682
family_counts = {'greedy-anchor': 54, 'random-wave': 218, 'sector-wave': 107}
task_count_counts = {'10': 8, '100': 1, '20': 196, '30': 76, '5': 2, '50': 96}
training_objective = precision_constrained_roi_maximization
hard_roi_threshold = 0.65
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.5
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.0
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
loss_options = {'false_high_priority_loss_multiplier': 12.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 1.5, 'hard_roi_positive_candidate_loss_multiplier': 1.5, 'hard_roi_positive_group_balance': 'family_task', 'hard_roi_positive_group_weight_power': 1.0, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {'greedy-anchor|10': 1, 'random-wave|20': 14, 'random-wave|30': 6, 'random-wave|50': 3, 'sector-wave|20': 9}, 'hard_roi_positive_group_weights': {'greedy-anchor|10': 4.0, 'random-wave|20': 1.0, 'random-wave|30': 1.0999999999999999, 'random-wave|50': 2.1999999999999997, 'sector-wave|20': 1.0}, 'candidate_delay_loss_multiplier': 2.0, 'hard_roi_negative_delay_loss_multiplier': 2.0, 'hard_roi_safe_delay_loss_multiplier': 1.0, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 1.0, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}
pairwise_ranking_loss_active = true
pairwise_candidate_ranking_loss_multiplier = 0.75
pairwise_false_delay_contrast_loss_multiplier = 0.5
pairwise_ranking_status = active_same_context_roi_margin_ranking
context_pair_stats = {'all': {'sample_count': 379, 'context_count': 295, 'multi_context_count': 16, 'same_context_pair_count': 312, 'same_context_comparable_pair_count': 293, 'positive_negative_label_pair_count': 108, 'roi_diverse_context_count': 16, 'largest_context_size': 10}, 'train': {'sample_count': 256, 'context_count': 216, 'multi_context_count': 7, 'same_context_pair_count': 160, 'same_context_comparable_pair_count': 145, 'positive_negative_label_pair_count': 47, 'roi_diverse_context_count': 7, 'largest_context_size': 10}, 'validation': {'sample_count': 123, 'context_count': 79, 'multi_context_count': 9, 'same_context_pair_count': 152, 'same_context_comparable_pair_count': 148, 'positive_negative_label_pair_count': 61, 'roi_diverse_context_count': 9, 'largest_context_size': 9}}
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
rejected_checkpoint_reasons = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high', 'high_priority_precision_below_threshold_or_no_predictions', 'high_priority_precision_ci_low_below_threshold_or_not_measurable', 'knn_ood_audit_missing']
rejected_checkpoint_reason_categories = ['false_high_priority_on_delay_too_high', 'false_safe_too_high', 'knn_ood_audit_missing', 'precision_below_gate', 'precision_ci_below_gate']
best_epoch = 8
selected_validation_loss = 6.4187900180966215
best_loss_epoch = 3
best_validation_loss = 5.974782809993163
best_loss_epoch_gate_pass = false
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high', 'high_priority_precision_below_threshold_or_no_predictions', 'high_priority_precision_ci_low_below_threshold_or_not_measurable', 'knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run']
attempted_update_count = 3208
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
    "family_holdout_min_accepted_high_roi_count": 3,
    "family_holdout_min_accepted_roi": 1.2027715540801485,
    "family_holdout_min_high_roi_capture_rate": 0.5,
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
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_roi": 1.2027715540801485,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.5,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 26,
        "accepted_batch_roi": 10.825974055780815,
        "accepted_high_roi_count": 20,
        "high_roi_capture_rate": 0.8333333333333334,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "total_batches": 65
      }
    },
    "family_specific_delay_fallback_families": [
      "greedy-anchor"
    ],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 0,
        "accepted_batch_roi": 0.0,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_roi": 1.2027715540801485,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.5,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 26,
        "accepted_batch_roi": 10.825974055780815,
        "accepted_high_roi_count": 20,
        "high_roi_capture_rate": 0.8333333333333334,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "total_batches": 65
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
      "random-wave": 174,
      "sector-wave": 42
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
      "sector-wave": 65
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
      "high_priority_precision_below_threshold_or_no_predictions",
      "high_priority_precision_ci_low_below_threshold_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high"
    ],
    "best_rejected_reasons": [
      "high_priority_precision_below_threshold_or_no_predictions",
      "high_priority_precision_ci_low_below_threshold_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "knn_ood_audit_missing"
    ],
    "candidate_count": 1,
    "feasible_threshold_count": 0,
    "selected_metrics": {
      "accepted_bad_mode_count": 0,
      "accepted_batch_count": 35,
      "accepted_batch_precision": 1.0,
      "accepted_batch_rate": 0.2845528455284553,
      "accepted_batch_roi": 8.351436269629215,
      "accepted_batch_roi_ci_low": 4.462122673861284,
      "accepted_batch_roi_over_baseline": 8.351436269629215,
      "accepted_batch_roi_over_baseline_ci_low": 4.462122673861284,
      "accepted_batch_roi_over_best_rc_baseline": 8.351436269629215,
      "accepted_batch_roi_over_best_rc_baseline_ci_low": 4.462122673861284,
      "accepted_batch_roi_over_old_gat_baseline": 8.351436269629215,
      "accepted_batch_roi_over_old_gat_baseline_ci_low": 4.462122673861284,
      "accepted_batch_roi_over_random_baseline": 8.351436269629215,
      "accepted_batch_roi_over_random_baseline_ci_low": 4.462122673861284,
      "baseline_roi_ci_high": 0.0,
      "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
      "baseline_selection_roi": 0.0,
      "batch_threshold": 0.45603272318840027,
      "batch_thresholds_by_family": {},
      "best_rc_baseline_accepted_batch_roi": 0.0,
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_blocked_count": 656,
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.5,
      "candidate_delay_score_penalty": 1.0,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_rescue_window_eligible_count": 0,
      "candidate_rescue_window_promoted_count": 0,
      "candidate_risk_adjusted_suppressed_count": 49,
      "candidate_score_threshold_blocked_count": 115,
      "candidate_threshold": 0.1531489953101488,
      "checkpoint_gate_pass": false,
      "checkpoint_gate_reject_reasons": [
        "high_priority_precision_below_threshold_or_no_predictions",
        "high_priority_precision_ci_low_below_threshold_or_not_measurable",
        "false_high_priority_on_delay_too_high",
        "false_safe_rate_union_too_high",
        "knn_ood_audit_missing"
      ],
      "context_delay_fallback_contexts": [],
      "coverage_non_ood": 1.0,
      "delay_label_count": 98,
      "delay_rate": 0.7154471544715447,
      "evaluated_candidate_count": 1066,
      "expected_trajectory_utility": 8.371436269629214,
      "false_high_priority_on_delay": 0.4489795918367347,
      "false_high_priority_on_delay_count": 44,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 0.4489795918367347,
      "family_delay_fallback_families": [
        "greedy-anchor"
      ],
      "family_holdout_min_accepted_high_roi_count": 3,
      "family_holdout_min_accepted_roi": 1.2027715540801485,
      "family_holdout_min_high_roi_capture_rate": 0.5,
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
          "accepted_high_roi_count": 0,
          "high_roi_capture_rate": null,
          "max_accepted_batch_roi_label": 0.4039181172847748,
          "oracle_high_roi_count": 0,
          "safe_precision": null,
          "total_batches": 14
        },
        "random-wave": {
          "accepted_batch_count": 9,
          "accepted_batch_roi": 1.2027715540801485,
          "accepted_high_roi_count": 3,
          "high_roi_capture_rate": 0.5,
          "max_accepted_batch_roi_label": 4.385624885559082,
          "oracle_high_roi_count": 6,
          "safe_precision": 1.0,
          "total_batches": 44
        },
        "sector-wave": {
          "accepted_batch_count": 26,
          "accepted_batch_roi": 10.825974055780815,
          "accepted_high_roi_count": 20,
          "high_roi_capture_rate": 0.8333333333333334,
          "max_accepted_batch_roi_label": 41.31852722167969,
          "oracle_high_roi_count": 24,
          "safe_precision": 1.0,
          "total_batches": 65
        }
      },
      "family_specific_delay_fallback_families": [
        "greedy-anchor"
      ],
      "hard_reject_reason_categories": [
        "false_high_priority_on_delay_too_high",
        "false_safe_too_high",
        "knn_ood_audit_missing",
        "precision_below_gate",
        "precision_ci_below_gate"
      ],
      "high_priority_precision": 0.8508474576271187,
      "high_priority_precision_ci_low": 0.8056960270785619,
      "high_priority_prediction_count": 295,
      "high_priority_true_positive_count": 251,
      "max_accepted_bad_mode_count": 0,
      "min_family_accepted_high_roi_count": 0,
      "min_family_high_roi_capture_rate": 0.0,
      "old_gat_baseline_accepted_batch_roi": 0.0,
      "random_baseline_accepted_batch_roi": 0.0,
      "safe_precision": 1.0,
      "safe_precision_ci_low": 0.9010957324106112,
      "threshold": 0.45603272318840027,
      "threshold_local_gate_pass": false,
      "threshold_local_hard_reject_reason_categories": [
        "false_high_priority_on_delay_too_high",
        "false_safe_too_high",
        "precision_below_gate",
        "precision_ci_below_gate"
      ],
      "threshold_local_reject_reasons": [
        "high_priority_precision_below_threshold_or_no_predictions",
        "high_priority_precision_ci_low_below_threshold_or_not_measurable",
        "false_high_priority_on_delay_too_high",
        "false_safe_rate_union_too_high"
      ],
      "threshold_mode": "family_delay_fallback",
      "total_batches": 123
    }
  },
  "train_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 54,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.2109375,
    "accepted_batch_roi": 1.7943940530579614,
    "accepted_batch_roi_ci_low": 0.4709777965616051,
    "accepted_batch_roi_over_baseline": 1.7943940530579614,
    "accepted_batch_roi_over_baseline_ci_low": 0.4709777965616051,
    "accepted_batch_roi_over_best_rc_baseline": 1.7943940530579614,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.4709777965616051,
    "accepted_batch_roi_over_old_gat_baseline": 1.7943940530579614,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.4709777965616051,
    "accepted_batch_roi_over_random_baseline": 1.7943940530579614,
    "accepted_batch_roi_over_random_baseline_ci_low": 0.4709777965616051,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.45603272318840027,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_blocked_count": 2273,
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 1.0,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 61,
    "candidate_score_threshold_blocked_count": 173,
    "candidate_threshold": 0.1531489953101488,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 179,
    "delay_rate": 0.7890625,
    "evaluated_candidate_count": 2938,
    "expected_trajectory_utility": 1.839764423428332,
    "false_high_priority_on_delay": 0.03910614525139665,
    "false_high_priority_on_delay_count": 7,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.03910614525139665,
    "family_delay_fallback_families": [
      "greedy-anchor"
    ],
    "family_holdout_min_accepted_high_roi_count": 0,
    "family_holdout_min_accepted_roi": 1.7440657664192258,
    "family_holdout_min_high_roi_capture_rate": 0.0,
    "family_holdout_min_precision": 1.0,
    "family_holdout_missing_accepted_families": [
      "greedy-anchor"
    ],
    "family_holdout_missing_accepted_opportunity_families": [],
    "family_holdout_oracle_high_roi_families": [
      "greedy-anchor",
      "random-wave",
      "sector-wave"
    ],
    "family_holdout_per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 0,
        "accepted_batch_roi": 0.0,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": 0.0,
        "max_accepted_batch_roi_label": 1.043739914894104,
        "oracle_high_roi_count": 1,
        "safe_precision": null,
        "total_batches": 40
      },
      "random-wave": {
        "accepted_batch_count": 44,
        "accepted_batch_roi": 1.7440657664192258,
        "accepted_high_roi_count": 17,
        "high_roi_capture_rate": 0.7391304347826086,
        "max_accepted_batch_roi_label": 35.64057159423828,
        "oracle_high_roi_count": 23,
        "safe_precision": 1.0,
        "total_batches": 174
      },
      "sector-wave": {
        "accepted_batch_count": 10,
        "accepted_batch_roi": 2.015838514268398,
        "accepted_high_roi_count": 9,
        "high_roi_capture_rate": 1.0,
        "max_accepted_batch_roi_label": 7.900282859802246,
        "oracle_high_roi_count": 9,
        "safe_precision": 1.0,
        "total_batches": 42
      }
    },
    "family_specific_delay_fallback_families": [
      "greedy-anchor"
    ],
    "hard_reject_reason_categories": [
      "false_high_priority_on_delay_too_high",
      "false_safe_too_high",
      "knn_ood_audit_missing",
      "roi_ci_below_baseline"
    ],
    "high_priority_precision": 0.9857723577235772,
    "high_priority_precision_ci_low": 0.9709260428103818,
    "high_priority_prediction_count": 492,
    "high_priority_true_positive_count": 485,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9335841332189981,
    "threshold": 0.45603272318840027,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "false_high_priority_on_delay_too_high",
      "false_safe_too_high",
      "roi_ci_below_baseline"
    ],
    "threshold_local_reject_reasons": [
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high"
    ],
    "threshold_mode": "family_delay_fallback",
    "total_batches": 256
  },
  "validation_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 35,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.2845528455284553,
    "accepted_batch_roi": 8.351436269629215,
    "accepted_batch_roi_ci_low": 4.462122673861284,
    "accepted_batch_roi_over_baseline": 8.351436269629215,
    "accepted_batch_roi_over_baseline_ci_low": 4.462122673861284,
    "accepted_batch_roi_over_best_rc_baseline": 8.351436269629215,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 4.462122673861284,
    "accepted_batch_roi_over_old_gat_baseline": 8.351436269629215,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 4.462122673861284,
    "accepted_batch_roi_over_random_baseline": 8.351436269629215,
    "accepted_batch_roi_over_random_baseline_ci_low": 4.462122673861284,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.45603272318840027,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_blocked_count": 656,
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 1.0,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 49,
    "candidate_score_threshold_blocked_count": 115,
    "candidate_threshold": 0.1531489953101488,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "high_priority_precision_below_threshold_or_no_predictions",
      "high_priority_precision_ci_low_below_threshold_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 98,
    "delay_rate": 0.7154471544715447,
    "evaluated_candidate_count": 1066,
    "expected_trajectory_utility": 8.371436269629214,
    "false_high_priority_on_delay": 0.4489795918367347,
    "false_high_priority_on_delay_count": 44,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.4489795918367347,
    "family_delay_fallback_families": [
      "greedy-anchor"
    ],
    "family_holdout_min_accepted_high_roi_count": 3,
    "family_holdout_min_accepted_roi": 1.2027715540801485,
    "family_holdout_min_high_roi_capture_rate": 0.5,
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
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_roi": 1.2027715540801485,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.5,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 26,
        "accepted_batch_roi": 10.825974055780815,
        "accepted_high_roi_count": 20,
        "high_roi_capture_rate": 0.8333333333333334,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 24,
        "safe_precision": 1.0,
        "total_batches": 65
      }
    },
    "family_specific_delay_fallback_families": [
      "greedy-anchor"
    ],
    "hard_reject_reason_categories": [
      "false_high_priority_on_delay_too_high",
      "false_safe_too_high",
      "knn_ood_audit_missing",
      "precision_below_gate",
      "precision_ci_below_gate"
    ],
    "high_priority_precision": 0.8508474576271187,
    "high_priority_precision_ci_low": 0.8056960270785619,
    "high_priority_prediction_count": 295,
    "high_priority_true_positive_count": 251,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "threshold": 0.45603272318840027,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "false_high_priority_on_delay_too_high",
      "false_safe_too_high",
      "precision_below_gate",
      "precision_ci_below_gate"
    ],
    "threshold_local_reject_reasons": [
      "high_priority_precision_below_threshold_or_no_predictions",
      "high_priority_precision_ci_low_below_threshold_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high"
    ],
    "threshold_mode": "family_delay_fallback",
    "total_batches": 123
  }
}
```

## 边界

- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；
- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；
- 当前 checkpoint 仍 `production_ready=false`；
- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；
- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。
