# GAT Batch Impact Training 报告

日期：2026-06-17

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
sample_count = 392
candidate_count = 4703
family_counts = {'greedy-anchor': 54, 'random-wave': 218, 'sector-wave': 120}
task_count_counts = {'10': 8, '100': 1, '20': 209, '30': 76, '5': 2, '50': 96}
training_objective = precision_constrained_roi_maximization
hard_roi_threshold = 0.65
candidate_delay_gate_enabled = false
candidate_delay_risk_threshold = 0.5
candidate_admission_score_mode = high_priority
candidate_delay_score_penalty = 0.0
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
loss_options = {'false_high_priority_loss_multiplier': 4.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 0.5, 'hard_roi_negative_delay_loss_multiplier': 0.0, 'hard_roi_safe_delay_loss_multiplier': 0.0, 'candidate_admission_score_mode': 'high_priority', 'candidate_delay_score_penalty': 0.0, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}
pairwise_ranking_loss_active = true
pairwise_candidate_ranking_loss_multiplier = 0.75
pairwise_false_delay_contrast_loss_multiplier = 0.5
pairwise_delay_risk_contrast_loss_multiplier = 1.0
pairwise_ranking_status = active_same_context_roi_margin_ranking
context_pair_stats = {'all': {'sample_count': 392, 'context_count': 295, 'multi_context_count': 16, 'same_context_pair_count': 427, 'same_context_comparable_pair_count': 406, 'positive_negative_label_pair_count': 159, 'roi_diverse_context_count': 16, 'largest_context_size': 12}, 'train': {'sample_count': 256, 'context_count': 216, 'multi_context_count': 7, 'same_context_pair_count': 160, 'same_context_comparable_pair_count': 145, 'positive_negative_label_pair_count': 47, 'roi_diverse_context_count': 7, 'largest_context_size': 10}, 'validation': {'sample_count': 136, 'context_count': 79, 'multi_context_count': 9, 'same_context_pair_count': 267, 'same_context_comparable_pair_count': 261, 'positive_negative_label_pair_count': 112, 'roi_diverse_context_count': 9, 'largest_context_size': 12}}
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
rejected_checkpoint_reasons = ['accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable', 'family_holdout_accepted_roi_below_threshold', 'knn_ood_audit_missing']
rejected_checkpoint_reason_categories = ['holdout_family_collapse', 'knn_ood_audit_missing', 'roi_ci_below_baseline']
best_epoch = 1
selected_validation_loss = 2.9551853539788113
best_loss_epoch = 1
best_validation_loss = 2.9551853539788113
best_loss_epoch_gate_pass = false
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable', 'family_holdout_accepted_roi_below_threshold', 'knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run']
attempted_update_count = 401
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
    "family_holdout_min_accepted_roi": 0.09050442464649677,
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
        "accepted_batch_count": 3,
        "accepted_batch_roi": 0.09050442464649677,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_roi": 0.2792740027335557,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 23,
        "accepted_batch_roi": 2.3766293707101243,
        "accepted_high_roi_count": 9,
        "high_roi_capture_rate": 0.34615384615384615,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 26,
        "safe_precision": 1.0,
        "total_batches": 78
      }
    },
    "family_specific_delay_fallback_families": [],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 3,
        "accepted_batch_roi": 0.09050442464649677,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_roi": 0.2792740027335557,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 23,
        "accepted_batch_roi": 2.3766293707101243,
        "accepted_high_roi_count": 9,
        "high_roi_capture_rate": 0.34615384615384615,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 26,
        "safe_precision": 1.0,
        "total_batches": 78
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
      "sector-wave": 78
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
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "best_rejected_reasons": [
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold",
      "knn_ood_audit_missing"
    ],
    "candidate_count": 1,
    "feasible_threshold_count": 0,
    "selected_metrics": {
      "accepted_bad_mode_count": 0,
      "accepted_batch_count": 37,
      "accepted_batch_precision": 1.0,
      "accepted_batch_rate": 0.27205882352941174,
      "accepted_batch_roi": 1.5677298062254448,
      "accepted_batch_roi_ci_low": 0.03792591292409453,
      "accepted_batch_roi_over_baseline": 1.5677298062254448,
      "accepted_batch_roi_over_baseline_ci_low": 0.03792591292409453,
      "accepted_batch_roi_over_best_rc_baseline": 1.5677298062254448,
      "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.03792591292409453,
      "accepted_batch_roi_over_old_gat_baseline": 1.5677298062254448,
      "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.03792591292409453,
      "accepted_batch_roi_over_random_baseline": 1.5677298062254448,
      "accepted_batch_roi_over_random_baseline_ci_low": 0.03792591292409453,
      "baseline_roi_ci_high": 0.0,
      "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
      "baseline_selection_roi": 0.0,
      "batch_threshold": 0.4815117120742798,
      "batch_thresholds_by_family": {},
      "best_rc_baseline_accepted_batch_roi": 0.0,
      "candidate_admission_score_mode": "high_priority",
      "candidate_delay_gate_blocked_count": 0,
      "candidate_delay_gate_enabled": false,
      "candidate_delay_risk_threshold": 0.5,
      "candidate_delay_score_penalty": 0.0,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_rescue_window_eligible_count": 0,
      "candidate_rescue_window_promoted_count": 0,
      "candidate_risk_adjusted_suppressed_count": 0,
      "candidate_score_threshold_blocked_count": 315,
      "candidate_threshold": 0.3725598454475403,
      "checkpoint_gate_pass": false,
      "checkpoint_gate_reject_reasons": [
        "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
        "family_holdout_accepted_roi_below_threshold",
        "knn_ood_audit_missing"
      ],
      "context_delay_fallback_contexts": [],
      "coverage_non_ood": 1.0,
      "delay_label_count": 141,
      "delay_rate": 0.7279411764705883,
      "evaluated_candidate_count": 1236,
      "expected_trajectory_utility": 1.6096216981173366,
      "false_high_priority_on_delay": 0.0070921985815602835,
      "false_high_priority_on_delay_count": 1,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 0.0070921985815602835,
      "family_delay_fallback_families": [],
      "family_holdout_min_accepted_high_roi_count": 1,
      "family_holdout_min_accepted_roi": 0.09050442464649677,
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
          "accepted_batch_count": 3,
          "accepted_batch_roi": 0.09050442464649677,
          "accepted_high_roi_count": 0,
          "high_roi_capture_rate": null,
          "max_accepted_batch_roi_label": 0.4039181172847748,
          "oracle_high_roi_count": 0,
          "safe_precision": 1.0,
          "total_batches": 14
        },
        "random-wave": {
          "accepted_batch_count": 11,
          "accepted_batch_roi": 0.2792740027335557,
          "accepted_high_roi_count": 1,
          "high_roi_capture_rate": 0.16666666666666666,
          "max_accepted_batch_roi_label": 4.385624885559082,
          "oracle_high_roi_count": 6,
          "safe_precision": 1.0,
          "total_batches": 44
        },
        "sector-wave": {
          "accepted_batch_count": 23,
          "accepted_batch_roi": 2.3766293707101243,
          "accepted_high_roi_count": 9,
          "high_roi_capture_rate": 0.34615384615384615,
          "max_accepted_batch_roi_label": 41.31852722167969,
          "oracle_high_roi_count": 26,
          "safe_precision": 1.0,
          "total_batches": 78
        }
      },
      "family_specific_delay_fallback_families": [],
      "hard_reject_reason_categories": [
        "holdout_family_collapse",
        "knn_ood_audit_missing",
        "roi_ci_below_baseline"
      ],
      "high_priority_precision": 0.998914223669924,
      "high_priority_precision_ci_low": 0.9938753621003081,
      "high_priority_prediction_count": 921,
      "high_priority_true_positive_count": 920,
      "max_accepted_bad_mode_count": 0,
      "min_family_accepted_high_roi_count": 0,
      "min_family_high_roi_capture_rate": 0.0,
      "old_gat_baseline_accepted_batch_roi": 0.0,
      "random_baseline_accepted_batch_roi": 0.0,
      "safe_precision": 1.0,
      "safe_precision_ci_low": 0.9059390425448562,
      "threshold": 0.4815117120742798,
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
      "total_batches": 136
    }
  },
  "train_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 100,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.390625,
    "accepted_batch_roi": 0.45833644684054886,
    "accepted_batch_roi_ci_low": 0.2710576677570607,
    "accepted_batch_roi_over_baseline": 0.45833644684054886,
    "accepted_batch_roi_over_baseline_ci_low": 0.2710576677570607,
    "accepted_batch_roi_over_best_rc_baseline": 0.45833644684054886,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.2710576677570607,
    "accepted_batch_roi_over_old_gat_baseline": 0.45833644684054886,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.2710576677570607,
    "accepted_batch_roi_over_random_baseline": 0.45833644684054886,
    "accepted_batch_roi_over_random_baseline_ci_low": 0.2710576677570607,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.4815117120742798,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "high_priority",
    "candidate_delay_gate_blocked_count": 0,
    "candidate_delay_gate_enabled": false,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 0.0,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 0,
    "candidate_score_threshold_blocked_count": 689,
    "candidate_threshold": 0.3725598454475403,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "accepted_batch_roi_below_baseline_margin",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "family_holdout_accepted_roi_below_threshold",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 266,
    "delay_rate": 0.609375,
    "evaluated_candidate_count": 3467,
    "expected_trajectory_utility": 0.4908364468405489,
    "false_high_priority_on_delay": 0.22932330827067668,
    "false_high_priority_on_delay_count": 61,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.22932330827067668,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 1,
    "family_holdout_min_accepted_roi": 0.23347363645831745,
    "family_holdout_min_high_roi_capture_rate": 0.3333333333333333,
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
        "accepted_batch_count": 15,
        "accepted_batch_roi": 0.23347363645831745,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 1.0,
        "max_accepted_batch_roi_label": 1.043739914894104,
        "oracle_high_roi_count": 1,
        "safe_precision": 1.0,
        "total_batches": 40
      },
      "random-wave": {
        "accepted_batch_count": 69,
        "accepted_batch_roi": 0.534116229091339,
        "accepted_high_roi_count": 10,
        "high_roi_capture_rate": 0.43478260869565216,
        "max_accepted_batch_roi_label": 35.64057159423828,
        "oracle_high_roi_count": 23,
        "safe_precision": 1.0,
        "total_batches": 174
      },
      "sector-wave": {
        "accepted_batch_count": 16,
        "accepted_batch_roi": 0.3423450206173584,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.3333333333333333,
        "max_accepted_batch_roi_label": 7.900282859802246,
        "oracle_high_roi_count": 9,
        "safe_precision": 1.0,
        "total_batches": 42
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "false_high_priority_on_delay_too_high",
      "false_safe_too_high",
      "holdout_family_collapse",
      "knn_ood_audit_missing",
      "roi_below_baseline",
      "roi_ci_below_baseline"
    ],
    "high_priority_precision": 0.9780417566594672,
    "high_priority_precision_ci_low": 0.971895864538708,
    "high_priority_prediction_count": 2778,
    "high_priority_true_positive_count": 2717,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.963005192523998,
    "threshold": 0.4815117120742798,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "false_high_priority_on_delay_too_high",
      "false_safe_too_high",
      "holdout_family_collapse",
      "roi_below_baseline",
      "roi_ci_below_baseline"
    ],
    "threshold_local_reject_reasons": [
      "accepted_batch_roi_below_baseline_margin",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "false_high_priority_on_delay_too_high",
      "false_safe_rate_union_too_high",
      "family_holdout_accepted_roi_below_threshold"
    ],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 256
  },
  "validation_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 37,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.27205882352941174,
    "accepted_batch_roi": 1.5677298062254448,
    "accepted_batch_roi_ci_low": 0.03792591292409453,
    "accepted_batch_roi_over_baseline": 1.5677298062254448,
    "accepted_batch_roi_over_baseline_ci_low": 0.03792591292409453,
    "accepted_batch_roi_over_best_rc_baseline": 1.5677298062254448,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.03792591292409453,
    "accepted_batch_roi_over_old_gat_baseline": 1.5677298062254448,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.03792591292409453,
    "accepted_batch_roi_over_random_baseline": 1.5677298062254448,
    "accepted_batch_roi_over_random_baseline_ci_low": 0.03792591292409453,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.4815117120742798,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "high_priority",
    "candidate_delay_gate_blocked_count": 0,
    "candidate_delay_gate_enabled": false,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 0.0,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 0,
    "candidate_score_threshold_blocked_count": 315,
    "candidate_threshold": 0.3725598454475403,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_roi_below_threshold",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 141,
    "delay_rate": 0.7279411764705883,
    "evaluated_candidate_count": 1236,
    "expected_trajectory_utility": 1.6096216981173366,
    "false_high_priority_on_delay": 0.0070921985815602835,
    "false_high_priority_on_delay_count": 1,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.0070921985815602835,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 1,
    "family_holdout_min_accepted_roi": 0.09050442464649677,
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
        "accepted_batch_count": 3,
        "accepted_batch_roi": 0.09050442464649677,
        "accepted_high_roi_count": 0,
        "high_roi_capture_rate": null,
        "max_accepted_batch_roi_label": 0.4039181172847748,
        "oracle_high_roi_count": 0,
        "safe_precision": 1.0,
        "total_batches": 14
      },
      "random-wave": {
        "accepted_batch_count": 11,
        "accepted_batch_roi": 0.2792740027335557,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 23,
        "accepted_batch_roi": 2.3766293707101243,
        "accepted_high_roi_count": 9,
        "high_roi_capture_rate": 0.34615384615384615,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 26,
        "safe_precision": 1.0,
        "total_batches": 78
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "holdout_family_collapse",
      "knn_ood_audit_missing",
      "roi_ci_below_baseline"
    ],
    "high_priority_precision": 0.998914223669924,
    "high_priority_precision_ci_low": 0.9938753621003081,
    "high_priority_prediction_count": 921,
    "high_priority_true_positive_count": 920,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9059390425448562,
    "threshold": 0.4815117120742798,
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
    "total_batches": 136
  }
}
```

## 边界

- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；
- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；
- 当前 checkpoint 仍 `production_ready=false`；
- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；
- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。
