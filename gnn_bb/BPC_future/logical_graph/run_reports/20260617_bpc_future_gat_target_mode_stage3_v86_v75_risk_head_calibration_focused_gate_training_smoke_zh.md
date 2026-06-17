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
training_run_config = {'seed': 41, 'validation_fraction': 0.25, 'epochs': 1, 'device': 'cpu', 'lr': 0.001, 'weight_decay': 1e-05, 'max_grad_norm': 5.0, 'model_config': {'node_dim': 9, 'option_dim': 10, 'candidate_feature_dim': 40, 'context_feature_dim': 26, 'batch_feature_dim': 18, 'path_token_vocab_size': 4096, 'path_pair_vocab_size': 4096, 'path_type_vocab_size': 3, 'path_token_dim': 16, 'path_hidden_dim': 32, 'hidden_dim': 32, 'option_hidden_dim': 32, 'pair_edge_dim': 32, 'num_gnn_layers': 1, 'heads': 4, 'dropout': 0.05, 'candidate_hidden_dim': 32, 'context_hidden_dim': 24, 'batch_hidden_dim': 32, 'impact_hidden_dim': 32, 'use_layer_norm': True}, 'loss_options': {'false_high_priority_loss_multiplier': 4.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 0.5, 'hard_roi_negative_delay_loss_multiplier': 1.0, 'hard_roi_safe_delay_loss_multiplier': 1.0, 'candidate_admission_score_mode': 'high_priority', 'candidate_delay_score_penalty': 0.0, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}, 'gate_config': {'min_high_priority_precision': 0.9, 'min_high_priority_precision_ci_low': 0.9, 'min_safe_precision': 0.9, 'min_safe_precision_ci_low': 0.9, 'confidence_z': 1.96, 'max_false_high_priority_on_delay': 0.01, 'max_false_safe_union_rate': 0.02, 'max_accepted_bad_mode_count': 0, 'min_accepted_batch_count': 1, 'min_accepted_batch_rate': 0.02, 'min_accepted_batch_roi': 0.65, 'min_accepted_batch_roi_ci_low': 0.65, 'baseline_accepted_batch_roi': 0.0, 'baseline_selection_roi': 0.0, 'baseline_roi_ci_high': 0.0, 'baseline_roi_ci_high_source': 'configured_point_estimate_no_baseline_distribution', 'random_baseline_accepted_batch_roi': 0.0, 'best_rc_baseline_accepted_batch_roi': 0.0, 'old_gat_baseline_accepted_batch_roi': 0.0, 'min_roi_margin_over_baseline': 0.2, 'min_family_holdout_precision': 0.8, 'min_family_holdout_accepted_roi': 0.65, 'min_family_accepted_high_roi_count': 0, 'min_family_high_roi_capture_rate': 0.0, 'candidate_admission_score_mode': 'high_priority', 'candidate_delay_score_penalty': 0.0, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'min_major_families': 2, 'observed_family_count': 3, 'stage3_min_samples': 200, 'actual_sample_count': 392, 'knn_ood_audit_completed': False, 'candidate_delay_gate_enabled': False, 'candidate_delay_risk_threshold': 0.5, 'require_positive_candidate_threshold': True}, 'focused_pair_gate_config': {'focused_pair_gate_row_index_min': 383, 'min_focused_pair_count': 1, 'min_focused_raw_pair_pass_rate': 1.0, 'min_focused_admission_pair_pass_rate': 1.0, 'min_focused_delay_risk_pair_pass_rate': 1.0, 'min_focused_strict_pair_pass_rate': 1.0}, 'checkpoint_selection': 'deployment_gate_first_then_roi_ci_baseline_utility_loss'}
hard_roi_threshold = 0.65
candidate_delay_gate_enabled = false
candidate_delay_risk_threshold = 0.5
candidate_admission_score_mode = high_priority
candidate_delay_score_penalty = 0.0
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
loss_options = {'false_high_priority_loss_multiplier': 4.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 0.5, 'hard_roi_negative_delay_loss_multiplier': 1.0, 'hard_roi_safe_delay_loss_multiplier': 1.0, 'candidate_admission_score_mode': 'high_priority', 'candidate_delay_score_penalty': 0.0, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}
pairwise_ranking_loss_active = true
pairwise_candidate_ranking_loss_multiplier = 0.75
pairwise_false_delay_contrast_loss_multiplier = 0.5
pairwise_delay_risk_contrast_loss_multiplier = 1.0
pairwise_ranking_status = active_same_context_roi_margin_ranking
context_pair_stats = {'all': {'sample_count': 392, 'context_count': 295, 'multi_context_count': 16, 'same_context_pair_count': 427, 'same_context_comparable_pair_count': 406, 'positive_negative_label_pair_count': 159, 'roi_diverse_context_count': 16, 'largest_context_size': 12}, 'train': {'sample_count': 256, 'context_count': 216, 'multi_context_count': 7, 'same_context_pair_count': 160, 'same_context_comparable_pair_count': 145, 'positive_negative_label_pair_count': 47, 'roi_diverse_context_count': 7, 'largest_context_size': 10}, 'validation': {'sample_count': 136, 'context_count': 79, 'multi_context_count': 9, 'same_context_pair_count': 267, 'same_context_comparable_pair_count': 261, 'positive_negative_label_pair_count': 112, 'roi_diverse_context_count': 9, 'largest_context_size': 12}}
focused_pair_gate_active = true
focused_pair_gate_summary = {'focused_row_count': 9, 'context_count': 3, 'contexts_with_positive_and_negative': 2, 'positive_row_count': 2, 'negative_row_count': 7, 'ambiguous_row_count': 0, 'pair_count': 4, 'raw_pair_pass_count': 1, 'admission_pair_pass_count': 1, 'delay_risk_pair_pass_count': 1, 'strict_pair_pass_count': 1, 'raw_pair_pass_rate': 0.25, 'admission_pair_pass_rate': 0.25, 'delay_risk_pair_pass_rate': 0.25, 'strict_pair_pass_rate': 0.25, 'label_counts': {'delay_or_hard_negative': 7, 'positive_high_priority': 2}, 'family_counts': {'sector-wave': 9}, 'primary': 'candidate_head_context_ranking_failure'}
focused_pair_gate_reject_reasons = ['raw_pair_pass_rate_below_threshold', 'admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
rejected_checkpoint_reasons = ['admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high', 'high_priority_precision_below_threshold_or_no_predictions', 'high_priority_precision_ci_low_below_threshold_or_not_measurable', 'knn_ood_audit_missing', 'raw_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
rejected_checkpoint_reason_categories = ['false_high_priority_on_delay_too_high', 'false_safe_too_high', 'focused_pair_gate_failed', 'knn_ood_audit_missing', 'precision_below_gate', 'precision_ci_below_gate']
best_epoch = 1
selected_validation_loss = 3.18193700507058
best_loss_epoch = 1
best_validation_loss = 3.18193700507058
best_loss_epoch_gate_pass = false
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high', 'high_priority_precision_below_threshold_or_no_predictions', 'high_priority_precision_ci_low_below_threshold_or_not_measurable', 'knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run', 'raw_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
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
    "family_holdout_measured_family_count": 2,
    "family_holdout_min_accepted_high_roi_count": 5,
    "family_holdout_min_accepted_roi": 0.6621513013008304,
    "family_holdout_min_high_roi_capture_rate": 0.8333333333333334,
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
        "accepted_batch_count": 22,
        "accepted_batch_roi": 0.6621513013008304,
        "accepted_high_roi_count": 5,
        "high_roi_capture_rate": 0.8333333333333334,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 38,
        "accepted_batch_roi": 8.30312846248087,
        "accepted_high_roi_count": 26,
        "high_roi_capture_rate": 1.0,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 26,
        "safe_precision": 1.0,
        "total_batches": 78
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
        "accepted_batch_count": 22,
        "accepted_batch_roi": 0.6621513013008304,
        "accepted_high_roi_count": 5,
        "high_roi_capture_rate": 0.8333333333333334,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 38,
        "accepted_batch_roi": 8.30312846248087,
        "accepted_high_roi_count": 26,
        "high_roi_capture_rate": 1.0,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 26,
        "safe_precision": 1.0,
        "total_batches": 78
      }
    }
  },
  "focused_pair_gate": {
    "active": true,
    "context_rows": [
      {
        "admission_pair_pass_rate": null,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_pair_pass_rate": null,
        "family": "sector-wave",
        "negative_count": 3,
        "pair_count": 0,
        "positive_count": 0,
        "raw_pair_pass_rate": null,
        "row_count": 3,
        "strict_pair_pass_rate": null
      },
      {
        "admission_pair_pass_rate": 0.5,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_pair_pass_rate": 0.5,
        "family": "sector-wave",
        "negative_count": 2,
        "pair_count": 2,
        "positive_count": 1,
        "raw_pair_pass_rate": 0.5,
        "row_count": 3,
        "strict_pair_pass_rate": 0.5
      },
      {
        "admission_pair_pass_rate": 0.0,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_pair_pass_rate": 0.0,
        "family": "sector-wave",
        "negative_count": 2,
        "pair_count": 2,
        "positive_count": 1,
        "raw_pair_pass_rate": 0.0,
        "row_count": 3,
        "strict_pair_pass_rate": 0.0
      }
    ],
    "diagnostic_only": true,
    "focus_row_index_min": 383,
    "gate": {
      "blocking_primary": "candidate_head_context_ranking_failure",
      "diagnostic_only": true,
      "gate_name": "focused_same_context_positive_negative_pair_gate",
      "gate_pass": false,
      "observed": {
        "admission_pair_pass_rate": 0.25,
        "delay_risk_pair_pass_rate": 0.25,
        "pair_count": 4,
        "raw_pair_pass_rate": 0.25,
        "strict_pair_pass_rate": 0.25
      },
      "production_ready": false,
      "reject_reasons": [
        "raw_pair_pass_rate_below_threshold",
        "admission_pair_pass_rate_below_threshold",
        "delay_risk_pair_pass_rate_below_threshold",
        "strict_pair_pass_rate_below_threshold"
      ],
      "selector_can_certificate": false,
      "thresholds": {
        "min_admission_pair_pass_rate": 1.0,
        "min_delay_risk_pair_pass_rate": 1.0,
        "min_focused_pair_count": 1,
        "min_raw_pair_pass_rate": 1.0,
        "min_strict_pair_pass_rate": 1.0
      }
    },
    "pair_rows": [
      {
        "admission_margin": -0.00033926963806152344,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0029191672801971436,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 389,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 390,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.00033926963806152344,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0034467875957489014,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.00435185432434082,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 390,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.0034467875957489014,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.008721411228179932,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.00602191686630249,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.008721411228179932,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.000310361385345459,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.0023650527000427246,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.000310361385345459,
        "raw_positive_above_negative": false
      }
    ],
    "production_ready": false,
    "runs_bpc_or_pricing": false,
    "summary": {
      "admission_pair_pass_count": 1,
      "admission_pair_pass_rate": 0.25,
      "ambiguous_row_count": 0,
      "context_count": 3,
      "contexts_with_positive_and_negative": 2,
      "delay_risk_pair_pass_count": 1,
      "delay_risk_pair_pass_rate": 0.25,
      "family_counts": {
        "sector-wave": 9
      },
      "focused_row_count": 9,
      "label_counts": {
        "delay_or_hard_negative": 7,
        "positive_high_priority": 2
      },
      "negative_row_count": 7,
      "pair_count": 4,
      "positive_row_count": 2,
      "primary": "candidate_head_context_ranking_failure",
      "raw_pair_pass_count": 1,
      "raw_pair_pass_rate": 0.25,
      "strict_pair_pass_count": 1,
      "strict_pair_pass_rate": 0.25
    },
    "thresholds": {
      "min_admission_pair_pass_rate": 1.0,
      "min_delay_risk_pair_pass_rate": 1.0,
      "min_focused_pair_count": 1,
      "min_raw_pair_pass_rate": 1.0,
      "min_strict_pair_pass_rate": 1.0
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
      "accepted_batch_count": 60,
      "accepted_batch_precision": 1.0,
      "accepted_batch_rate": 0.4411764705882353,
      "accepted_batch_roi": 5.5014368367148565,
      "accepted_batch_roi_ci_low": 3.0197149083421886,
      "accepted_batch_roi_over_baseline": 5.5014368367148565,
      "accepted_batch_roi_over_baseline_ci_low": 3.0197149083421886,
      "accepted_batch_roi_over_best_rc_baseline": 5.5014368367148565,
      "accepted_batch_roi_over_best_rc_baseline_ci_low": 3.0197149083421886,
      "accepted_batch_roi_over_old_gat_baseline": 5.5014368367148565,
      "accepted_batch_roi_over_old_gat_baseline_ci_low": 3.0197149083421886,
      "accepted_batch_roi_over_random_baseline": 5.5014368367148565,
      "accepted_batch_roi_over_random_baseline_ci_low": 3.0197149083421886,
      "baseline_roi_ci_high": 0.0,
      "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
      "baseline_selection_roi": 0.0,
      "batch_threshold": 0.45817795395851135,
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
      "candidate_score_threshold_blocked_count": 0,
      "candidate_threshold": 0.3834974765777588,
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
      "delay_label_count": 117,
      "delay_rate": 0.5588235294117647,
      "evaluated_candidate_count": 1087,
      "expected_trajectory_utility": 5.5256035033815225,
      "false_high_priority_on_delay": 1.0,
      "false_high_priority_on_delay_count": 117,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 1.0,
      "family_delay_fallback_families": [
        "greedy-anchor"
      ],
      "family_holdout_min_accepted_high_roi_count": 5,
      "family_holdout_min_accepted_roi": 0.6621513013008304,
      "family_holdout_min_high_roi_capture_rate": 0.8333333333333334,
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
          "accepted_batch_count": 22,
          "accepted_batch_roi": 0.6621513013008304,
          "accepted_high_roi_count": 5,
          "high_roi_capture_rate": 0.8333333333333334,
          "max_accepted_batch_roi_label": 4.385624885559082,
          "oracle_high_roi_count": 6,
          "safe_precision": 1.0,
          "total_batches": 44
        },
        "sector-wave": {
          "accepted_batch_count": 38,
          "accepted_batch_roi": 8.30312846248087,
          "accepted_high_roi_count": 26,
          "high_roi_capture_rate": 1.0,
          "max_accepted_batch_roi_label": 41.31852722167969,
          "oracle_high_roi_count": 26,
          "safe_precision": 1.0,
          "total_batches": 78
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
      "high_priority_precision": 0.8923643054277829,
      "high_priority_precision_ci_low": 0.87253887789687,
      "high_priority_prediction_count": 1087,
      "high_priority_true_positive_count": 970,
      "max_accepted_bad_mode_count": 0,
      "min_family_accepted_high_roi_count": 0,
      "min_family_high_roi_capture_rate": 0.0,
      "old_gat_baseline_accepted_batch_roi": 0.0,
      "random_baseline_accepted_batch_roi": 0.0,
      "safe_precision": 1.0,
      "safe_precision_ci_low": 0.939826069522067,
      "threshold": 0.45817795395851135,
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
      "total_batches": 136
    }
  },
  "train_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 102,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.3984375,
    "accepted_batch_roi": 1.0784972156937276,
    "accepted_batch_roi_ci_low": 0.36238418719819954,
    "accepted_batch_roi_over_baseline": 1.0784972156937276,
    "accepted_batch_roi_over_baseline_ci_low": 0.36238418719819954,
    "accepted_batch_roi_over_best_rc_baseline": 1.0784972156937276,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.36238418719819954,
    "accepted_batch_roi_over_old_gat_baseline": 1.0784972156937276,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.36238418719819954,
    "accepted_batch_roi_over_random_baseline": 1.0784972156937276,
    "accepted_batch_roi_over_random_baseline_ci_low": 0.36238418719819954,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.45817795395851135,
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
    "candidate_score_threshold_blocked_count": 22,
    "candidate_threshold": 0.3834974765777588,
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
    "delay_rate": 0.6015625,
    "evaluated_candidate_count": 2938,
    "expected_trajectory_utility": 1.1216344705956884,
    "false_high_priority_on_delay": 1.0,
    "false_high_priority_on_delay_count": 179,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 1.0,
    "family_delay_fallback_families": [
      "greedy-anchor"
    ],
    "family_holdout_min_accepted_high_roi_count": 0,
    "family_holdout_min_accepted_roi": 1.0766931678168477,
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
        "accepted_batch_count": 82,
        "accepted_batch_roi": 1.0789372273710154,
        "accepted_high_roi_count": 21,
        "high_roi_capture_rate": 0.9130434782608695,
        "max_accepted_batch_roi_label": 35.64057159423828,
        "oracle_high_roi_count": 23,
        "safe_precision": 1.0,
        "total_batches": 174
      },
      "sector-wave": {
        "accepted_batch_count": 20,
        "accepted_batch_roi": 1.0766931678168477,
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
    "high_priority_precision": 0.9386145404663924,
    "high_priority_precision_ci_low": 0.9293116724186362,
    "high_priority_prediction_count": 2916,
    "high_priority_true_positive_count": 2737,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9637042523922542,
    "threshold": 0.45817795395851135,
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
    "accepted_batch_count": 60,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.4411764705882353,
    "accepted_batch_roi": 5.5014368367148565,
    "accepted_batch_roi_ci_low": 3.0197149083421886,
    "accepted_batch_roi_over_baseline": 5.5014368367148565,
    "accepted_batch_roi_over_baseline_ci_low": 3.0197149083421886,
    "accepted_batch_roi_over_best_rc_baseline": 5.5014368367148565,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 3.0197149083421886,
    "accepted_batch_roi_over_old_gat_baseline": 5.5014368367148565,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 3.0197149083421886,
    "accepted_batch_roi_over_random_baseline": 5.5014368367148565,
    "accepted_batch_roi_over_random_baseline_ci_low": 3.0197149083421886,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.45817795395851135,
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
    "candidate_score_threshold_blocked_count": 0,
    "candidate_threshold": 0.3834974765777588,
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
    "delay_label_count": 117,
    "delay_rate": 0.5588235294117647,
    "evaluated_candidate_count": 1087,
    "expected_trajectory_utility": 5.5256035033815225,
    "false_high_priority_on_delay": 1.0,
    "false_high_priority_on_delay_count": 117,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 1.0,
    "family_delay_fallback_families": [
      "greedy-anchor"
    ],
    "family_holdout_min_accepted_high_roi_count": 5,
    "family_holdout_min_accepted_roi": 0.6621513013008304,
    "family_holdout_min_high_roi_capture_rate": 0.8333333333333334,
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
        "accepted_batch_count": 22,
        "accepted_batch_roi": 0.6621513013008304,
        "accepted_high_roi_count": 5,
        "high_roi_capture_rate": 0.8333333333333334,
        "max_accepted_batch_roi_label": 4.385624885559082,
        "oracle_high_roi_count": 6,
        "safe_precision": 1.0,
        "total_batches": 44
      },
      "sector-wave": {
        "accepted_batch_count": 38,
        "accepted_batch_roi": 8.30312846248087,
        "accepted_high_roi_count": 26,
        "high_roi_capture_rate": 1.0,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 26,
        "safe_precision": 1.0,
        "total_batches": 78
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
    "high_priority_precision": 0.8923643054277829,
    "high_priority_precision_ci_low": 0.87253887789687,
    "high_priority_prediction_count": 1087,
    "high_priority_true_positive_count": 970,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.939826069522067,
    "threshold": 0.45817795395851135,
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
