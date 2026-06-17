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
training_run_config = {'seed': 13, 'validation_fraction': 0.25, 'epochs': 8, 'device': 'cpu', 'lr': 0.001, 'weight_decay': 1e-05, 'max_grad_norm': 5.0, 'model_config': {'node_dim': 9, 'option_dim': 10, 'candidate_feature_dim': 40, 'context_feature_dim': 26, 'batch_feature_dim': 18, 'path_token_vocab_size': 4096, 'path_pair_vocab_size': 4096, 'path_type_vocab_size': 3, 'path_token_dim': 16, 'path_hidden_dim': 32, 'hidden_dim': 32, 'option_hidden_dim': 32, 'pair_edge_dim': 32, 'num_gnn_layers': 1, 'heads': 4, 'dropout': 0.05, 'candidate_hidden_dim': 32, 'context_hidden_dim': 24, 'batch_hidden_dim': 32, 'impact_hidden_dim': 32, 'use_layer_norm': True}, 'loss_options': {'false_high_priority_loss_multiplier': 8.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 1.0, 'hard_roi_negative_delay_loss_multiplier': 2.0, 'hard_roi_safe_delay_loss_multiplier': 0.5, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 2.0, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'focused_pair_loss_multiplier': 0.0, 'focused_pair_candidate_loss_multiplier': 1.0, 'focused_pair_admission_loss_multiplier': 1.0, 'focused_pair_delay_risk_loss_multiplier': 1.0, 'focused_pair_batch_loss_multiplier': 0.0, 'focused_pair_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_row_indices.json', 'focused_pair_row_indices': [10, 11, 16, 80, 89, 106, 109, 112, 121, 133, 294, 295, 296, 297, 298, 302, 303, 304, 305, 306, 307, 308, 311, 312, 313, 315, 316, 317, 319, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 380, 381, 382, 386, 387, 388, 389, 390, 391], 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}, 'gate_config': {'min_high_priority_precision': 0.9, 'min_high_priority_precision_ci_low': 0.9, 'min_safe_precision': 0.9, 'min_safe_precision_ci_low': 0.9, 'confidence_z': 1.96, 'max_false_high_priority_on_delay': 0.01, 'max_false_safe_union_rate': 0.02, 'max_accepted_bad_mode_count': 0, 'min_accepted_batch_count': 1, 'min_accepted_batch_rate': 0.02, 'min_accepted_batch_roi': 0.65, 'min_accepted_batch_roi_ci_low': 0.65, 'baseline_accepted_batch_roi': 0.0, 'baseline_selection_roi': 0.0, 'baseline_roi_ci_high': 0.0, 'baseline_roi_ci_high_source': 'configured_point_estimate_no_baseline_distribution', 'random_baseline_accepted_batch_roi': 0.0, 'best_rc_baseline_accepted_batch_roi': 0.0, 'old_gat_baseline_accepted_batch_roi': 0.0, 'min_roi_margin_over_baseline': 0.2, 'min_family_holdout_precision': 0.8, 'min_family_holdout_accepted_roi': 0.65, 'min_family_accepted_high_roi_count': 0, 'min_family_high_roi_capture_rate': 0.0, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 2.0, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'min_major_families': 2, 'observed_family_count': 3, 'stage3_min_samples': 200, 'actual_sample_count': 392, 'knn_ood_audit_completed': False, 'candidate_delay_gate_enabled': True, 'candidate_delay_risk_threshold': 0.5, 'require_positive_candidate_threshold': True}, 'focused_pair_gate_config': {'focused_pair_gate_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_row_indices.json', 'focused_pair_row_indices_count': 82, 'focused_pair_selector': 'explicit_row_indices', 'min_focused_pair_count': 1, 'min_focused_raw_pair_pass_rate': 1.0, 'min_focused_admission_pair_pass_rate': 1.0, 'min_focused_delay_risk_pair_pass_rate': 1.0, 'min_focused_strict_pair_pass_rate': 1.0}, 'checkpoint_selection': 'deployment_gate_first_then_roi_ci_baseline_utility_loss'}
hard_roi_threshold = 0.65
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.5
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 2.0
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
loss_options = {'false_high_priority_loss_multiplier': 8.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 1.0, 'hard_roi_negative_delay_loss_multiplier': 2.0, 'hard_roi_safe_delay_loss_multiplier': 0.5, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 2.0, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'focused_pair_loss_multiplier': 0.0, 'focused_pair_candidate_loss_multiplier': 1.0, 'focused_pair_admission_loss_multiplier': 1.0, 'focused_pair_delay_risk_loss_multiplier': 1.0, 'focused_pair_batch_loss_multiplier': 0.0, 'focused_pair_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_row_indices.json', 'focused_pair_row_indices': [10, 11, 16, 80, 89, 106, 109, 112, 121, 133, 294, 295, 296, 297, 298, 302, 303, 304, 305, 306, 307, 308, 311, 312, 313, 315, 316, 317, 319, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 380, 381, 382, 386, 387, 388, 389, 390, 391], 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}
pairwise_ranking_loss_active = true
pairwise_candidate_ranking_loss_multiplier = 0.75
pairwise_false_delay_contrast_loss_multiplier = 0.5
pairwise_delay_risk_contrast_loss_multiplier = 1.0
focused_pair_loss_multiplier = 0.0
focused_pair_candidate_loss_multiplier = 1.0
focused_pair_admission_loss_multiplier = 1.0
focused_pair_delay_risk_loss_multiplier = 1.0
focused_pair_batch_loss_multiplier = 0.0
focused_pair_row_index_min = None
focused_pair_row_indices_file = BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_row_indices.json
focused_pair_row_indices_count = 82
pairwise_ranking_status = active_same_context_roi_margin_ranking
context_pair_stats = {'all': {'sample_count': 392, 'context_count': 295, 'multi_context_count': 16, 'same_context_pair_count': 427, 'same_context_comparable_pair_count': 406, 'positive_negative_label_pair_count': 159, 'roi_diverse_context_count': 16, 'largest_context_size': 12}, 'train': {'sample_count': 319, 'context_count': 248, 'multi_context_count': 11, 'same_context_pair_count': 319, 'same_context_comparable_pair_count': 298, 'positive_negative_label_pair_count': 106, 'roi_diverse_context_count': 11, 'largest_context_size': 12}, 'validation': {'sample_count': 73, 'context_count': 47, 'multi_context_count': 5, 'same_context_pair_count': 108, 'same_context_comparable_pair_count': 108, 'positive_negative_label_pair_count': 53, 'roi_diverse_context_count': 5, 'largest_context_size': 12}}
focused_pair_gate_active = true
focused_pair_gate_summary = {'focused_row_count': 82, 'context_count': 11, 'contexts_with_positive_and_negative': 11, 'positive_row_count': 39, 'negative_row_count': 43, 'ambiguous_row_count': 0, 'pair_count': 145, 'raw_pair_pass_count': 86, 'admission_pair_pass_count': 77, 'delay_risk_pair_pass_count': 87, 'strict_pair_pass_count': 64, 'raw_pair_pass_rate': 0.593103448275862, 'admission_pair_pass_rate': 0.5310344827586206, 'delay_risk_pair_pass_rate': 0.6, 'strict_pair_pass_rate': 0.4413793103448276, 'label_counts': {'delay_or_hard_negative': 43, 'positive_high_priority': 39}, 'family_counts': {'random-wave': 24, 'sector-wave': 58}, 'primary': 'candidate_head_context_ranking_failure'}
focused_pair_gate_reject_reasons = ['raw_pair_pass_rate_below_threshold', 'admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_roi_ci
rejected_checkpoint_reasons = ['admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'knn_ood_audit_missing', 'raw_pair_pass_rate_below_threshold', 'safe_precision_ci_low_below_threshold_or_not_measurable', 'strict_pair_pass_rate_below_threshold']
rejected_checkpoint_reason_categories = ['focused_pair_gate_failed', 'knn_ood_audit_missing', 'precision_ci_below_gate']
best_epoch = 1
selected_validation_loss = 3.9792477538994637
best_loss_epoch = 7
best_validation_loss = 3.456395530853485
best_loss_epoch_gate_pass = false
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run', 'raw_pair_pass_rate_below_threshold', 'safe_precision_ci_low_below_threshold_or_not_measurable', 'strict_pair_pass_rate_below_threshold']
attempted_update_count = 5696
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
    "family_holdout_min_accepted_high_roi_count": 1,
    "family_holdout_min_accepted_roi": 0.9718791544437408,
    "family_holdout_min_high_roi_capture_rate": 0.16666666666666666,
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
        "max_accepted_batch_roi_label": 0.45004528760910034,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 17
      },
      "random-wave": {
        "accepted_batch_count": 2,
        "accepted_batch_roi": 0.9718791544437408,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.5,
        "max_accepted_batch_roi_label": 1.3259137868881226,
        "oracle_high_roi_count": 2,
        "safe_precision": 1.0,
        "total_batches": 15
      },
      "sector-wave": {
        "accepted_batch_count": 3,
        "accepted_batch_roi": 0.9823677937189738,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 31.935651779174805,
        "oracle_high_roi_count": 18,
        "safe_precision": 1.0,
        "total_batches": 41
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
        "max_accepted_batch_roi_label": 0.45004528760910034,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 17
      },
      "random-wave": {
        "accepted_batch_count": 2,
        "accepted_batch_roi": 0.9718791544437408,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.5,
        "max_accepted_batch_roi_label": 1.3259137868881226,
        "oracle_high_roi_count": 2,
        "safe_precision": 1.0,
        "total_batches": 15
      },
      "sector-wave": {
        "accepted_batch_count": 3,
        "accepted_batch_roi": 0.9823677937189738,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 31.935651779174805,
        "oracle_high_roi_count": 18,
        "safe_precision": 1.0,
        "total_batches": 41
      }
    }
  },
  "focused_pair_gate": {
    "active": true,
    "context_rows": [
      {
        "admission_pair_pass_rate": 0.8571428571428571,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_pair_pass_rate": 0.5714285714285714,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 7,
        "positive_count": 7,
        "raw_pair_pass_rate": 0.8571428571428571,
        "row_count": 8,
        "strict_pair_pass_rate": 0.5714285714285714
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 2,
        "pair_count": 10,
        "positive_count": 5,
        "raw_pair_pass_rate": 1.0,
        "row_count": 7,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "9a2ca522ff49991c",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks050_01_seed91000|9a2ca522ff49991c",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 1,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 2,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 9,
        "pair_count": 9,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 10,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 1,
        "pair_count": 2,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 0.48,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_pair_pass_rate": 0.56,
        "family": "sector-wave",
        "negative_count": 5,
        "pair_count": 25,
        "positive_count": 5,
        "raw_pair_pass_rate": 0.6,
        "row_count": 10,
        "strict_pair_pass_rate": 0.36
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 6,
        "pair_count": 6,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 7,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 0.2857142857142857,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_pair_pass_rate": 0.22857142857142856,
        "family": "sector-wave",
        "negative_count": 5,
        "pair_count": 35,
        "positive_count": 7,
        "raw_pair_pass_rate": 0.5428571428571428,
        "row_count": 12,
        "strict_pair_pass_rate": 0.22857142857142856
      },
      {
        "admission_pair_pass_rate": 0.5,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_pair_pass_rate": 0.5,
        "family": "sector-wave",
        "negative_count": 3,
        "pair_count": 12,
        "positive_count": 4,
        "raw_pair_pass_rate": 0.5,
        "row_count": 7,
        "strict_pair_pass_rate": 0.4166666666666667
      },
      {
        "admission_pair_pass_rate": 0.6666666666666666,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_pair_pass_rate": 0.6666666666666666,
        "family": "sector-wave",
        "negative_count": 3,
        "pair_count": 3,
        "positive_count": 1,
        "raw_pair_pass_rate": 0.3333333333333333,
        "row_count": 4,
        "strict_pair_pass_rate": 0.3333333333333333
      },
      {
        "admission_pair_pass_rate": 0.37142857142857144,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_pair_pass_rate": 0.7142857142857143,
        "family": "sector-wave",
        "negative_count": 7,
        "pair_count": 35,
        "positive_count": 5,
        "raw_pair_pass_rate": 0.3142857142857143,
        "row_count": 12,
        "strict_pair_pass_rate": 0.2571428571428571
      }
    ],
    "diagnostic_only": true,
    "focus_row_index_min": null,
    "focus_row_indices_count": 82,
    "focus_row_indices_file": "BPC_future/results/gat_batch_impact_focused_tranche_mining_v95_v75_20260617/focused_row_indices.json",
    "focus_selector": "explicit_row_indices",
    "gate": {
      "blocking_primary": "candidate_head_context_ranking_failure",
      "diagnostic_only": true,
      "gate_name": "focused_same_context_positive_negative_pair_gate",
      "gate_pass": false,
      "observed": {
        "admission_pair_pass_rate": 0.5310344827586206,
        "delay_risk_pair_pass_rate": 0.6,
        "pair_count": 145,
        "raw_pair_pass_rate": 0.593103448275862,
        "strict_pair_pass_rate": 0.4413793103448276
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
        "admission_margin": 0.01227681630571048,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.011938333511352539,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 348,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.564840454545447,
        "positive_row_index": 11,
        "positive_signature_ids": [
          "faa3e5eeea745d947ae4d0698ed0ab2d096fee55",
          "8d7b86da08c08250173761ceee64c94abd8a4078",
          "57884349bab8de75786bc13edbc3915db23c2234",
          "adec5d2f3718fdedd4151be259175be791580cb8",
          "cccfb81dcbea4e3ea439538fe2022b8e1661fed2",
          "45e6b1118b5efb320fbb38fccfba3cdcc5119a9c",
          "311aa3340bbfff00cf8e5b09494d24341c9e070f",
          "d24813f231732df0f62a59048808af0e3c297aaa",
          "9d6f8b92f69b677e2784e157fc708cd3527c0c82",
          "02374efacd87edbff20e824f009a0800e430e9ef",
          "4ff77aada3bed1157cf8d2056c968e0f3b5ec28c"
        ],
        "raw_margin": 0.020785510540008545,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.002749329751342816,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.004134118556976318,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 348,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 35.640572999999904,
        "positive_row_index": 308,
        "positive_signature_ids": [
          "faa3e5eeea745d947ae4d0698ed0ab2d096fee55"
        ],
        "raw_margin": 0.0027875304222106934,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.002749329751342816,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.004134118556976318,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 348,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 347,
        "positive_signature_ids": [
          "faa3e5eeea745d947ae4d0698ed0ab2d096fee55"
        ],
        "raw_margin": 0.0027875304222106934,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0003637144827136063,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": -6.967782974243164e-05,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 348,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 349,
        "positive_signature_ids": [
          "4ff77aada3bed1157cf8d2056c968e0f3b5ec28c"
        ],
        "raw_margin": 0.0016429424285888672,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.002749329751342816,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.004134118556976318,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 348,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 369,
        "positive_signature_ids": [
          "faa3e5eeea745d947ae4d0698ed0ab2d096fee55"
        ],
        "raw_margin": 0.0027875304222106934,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.0,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 348,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 370,
        "positive_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0003637144827136063,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": -6.967782974243164e-05,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 348,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 371,
        "positive_signature_ids": [
          "4ff77aada3bed1157cf8d2056c968e0f3b5ec28c"
        ],
        "raw_margin": 0.0016429424285888672,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02689108220994192,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.02505934238433838,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 342,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 5.672967599999997,
        "positive_row_index": 10,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6",
          "2790b1a6fd6539333755651296d7389a9b4651ec",
          "c1f4ab3caf4d0ab917bb251e1adcd55d21e06cb7",
          "c66fe0ce4b9d58d4e6450e227af52f3177549f9b",
          "8cf38b4aebfa9cd86a446be798382d9ff2f4415c",
          "b99beee79a25f47a7cbe635afbc720de210bb8a7",
          "e08bab78c383524a0199fd0139e7c1415fe06b13",
          "fec81566da104bd5e777b057c017cea385678699",
          "e1a7f5f625c66e587282a36b9a26a6ea7bbca1f8",
          "4a4511f4c1a4e49e4a5bc33c1d173b660876637b",
          "3d2a7df0be008706b1d47d87d9ee7dd67b8fe34b",
          "ecbae07d1b3079a4148c38548a4e64e646e03e09",
          "7b830e63fbfa9177950747a92223d099d690b1d7",
          "d72ebae20742d3eb2024dcb557d75a88775be15a",
          "e0f32b5244452460777a30e0d95a2be649f77dac",
          "b3df2ad72b73c50b3cb081932f27063566a9fbcb",
          "2a4ac6935dc8d9b018a576a38f43c57e3c4b0246",
          "8e8fe4e562995e828787aa4642085f1d95950389",
          "0f12cfc19ca71cf4db994c109c16fa9328d8c736",
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e",
          "207be087c559fdd7767d55018cc505bb9cc459e7",
          "7650207bb91b4a2af2162417e6d800fb64a99bef",
          "c31793b1f429ef89ae54ed0eafdd1cebc8ffba9d",
          "8b1ef144fc5141c5ba8c895022ea1eae12c8a6b1",
          "70528f366b9729f3372416ac2d3cf7fffc8fe0d2"
        ],
        "raw_margin": 0.05351865291595459,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02689108220994192,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.02505934238433838,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 364,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 5.672967599999997,
        "positive_row_index": 10,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6",
          "2790b1a6fd6539333755651296d7389a9b4651ec",
          "c1f4ab3caf4d0ab917bb251e1adcd55d21e06cb7",
          "c66fe0ce4b9d58d4e6450e227af52f3177549f9b",
          "8cf38b4aebfa9cd86a446be798382d9ff2f4415c",
          "b99beee79a25f47a7cbe635afbc720de210bb8a7",
          "e08bab78c383524a0199fd0139e7c1415fe06b13",
          "fec81566da104bd5e777b057c017cea385678699",
          "e1a7f5f625c66e587282a36b9a26a6ea7bbca1f8",
          "4a4511f4c1a4e49e4a5bc33c1d173b660876637b",
          "3d2a7df0be008706b1d47d87d9ee7dd67b8fe34b",
          "ecbae07d1b3079a4148c38548a4e64e646e03e09",
          "7b830e63fbfa9177950747a92223d099d690b1d7",
          "d72ebae20742d3eb2024dcb557d75a88775be15a",
          "e0f32b5244452460777a30e0d95a2be649f77dac",
          "b3df2ad72b73c50b3cb081932f27063566a9fbcb",
          "2a4ac6935dc8d9b018a576a38f43c57e3c4b0246",
          "8e8fe4e562995e828787aa4642085f1d95950389",
          "0f12cfc19ca71cf4db994c109c16fa9328d8c736",
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e",
          "207be087c559fdd7767d55018cc505bb9cc459e7",
          "7650207bb91b4a2af2162417e6d800fb64a99bef",
          "c31793b1f429ef89ae54ed0eafdd1cebc8ffba9d",
          "8b1ef144fc5141c5ba8c895022ea1eae12c8a6b1",
          "70528f366b9729f3372416ac2d3cf7fffc8fe0d2"
        ],
        "raw_margin": 0.05351865291595459,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0031826057657445006,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.004847228527069092,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 342,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1144286500000005,
        "positive_row_index": 341,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.0032001137733459473,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0031826057657445006,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.004847228527069092,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 364,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1144286500000005,
        "positive_row_index": 341,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.0032001137733459473,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.000818169736162791,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.0011504888534545898,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 342,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 343,
        "positive_signature_ids": [
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e"
        ],
        "raw_margin": 0.0010390281677246094,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.000818169736162791,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.0011504888534545898,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 364,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 343,
        "positive_signature_ids": [
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e"
        ],
        "raw_margin": 0.0010390281677246094,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0031826057657445006,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.004847228527069092,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 342,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1685759999999998,
        "positive_row_index": 363,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.0032001137733459473,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0031826057657445006,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.004847228527069092,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 364,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1685759999999998,
        "positive_row_index": 363,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.0032001137733459473,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.000818169736162791,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.0011504888534545898,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 342,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 365,
        "positive_signature_ids": [
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e"
        ],
        "raw_margin": 0.0010390281677246094,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.000818169736162791,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.0011504888534545898,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 364,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 365,
        "positive_signature_ids": [
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e"
        ],
        "raw_margin": 0.0010390281677246094,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02976199302470592,
        "admission_positive_above_negative": true,
        "context_hash": "9a2ca522ff49991c",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks050_01_seed91000|9a2ca522ff49991c",
        "delay_risk_margin": 0.025860100984573364,
        "family": "random-wave",
        "negative_roi": -4.876676650000114,
        "negative_row_index": 350,
        "negative_signature_ids": [
          "12506331f28530e7a9219a687bfbce8930dacb32"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.3691615510204067,
        "positive_row_index": 133,
        "positive_signature_ids": [
          "afd1e5dcbb49c6a0c685fc993bb0a12effe17aba",
          "0f3a0b7b208f18d8faeee179bb80b65bae938d25",
          "c57c57fe6ee47176db09e04d2166dcc3bc658e82",
          "bbb751253e8aee945288eb8350793aada2ce9172",
          "d7978fbcd4a868f37d3294f067ad8c8beabc89f0",
          "412cbd21daf59f4c5217f75f74799761fccb85ce",
          "3574117717e5953e3bf7a18436b1a0e1f4c17b20",
          "afb275ff9065297e9fee872756289c1b30a75ed9",
          "0be569f92ef54ac48307b81be3a6b7c538d9c2b9",
          "b5c54307cbb07907f31e21b02d0a98b5ab6fde24",
          "b6005a7561ded1bd1ce40e58487f586cdb59ab67",
          "d4d9ac9b1065a63fa5d9ad103f3123a53deb294c",
          "475dd082c7a479fdcf4dbb7734d6433ccd08617a",
          "ed0e5311a6f2be9b51f48254cfbdc3259b64df06",
          "011237a18bc88be41ed2c7d7c7a7543634dd2d74",
          "83faf5b314db40745f880e13fab83ad9cb1c13b6",
          "12506331f28530e7a9219a687bfbce8930dacb32",
          "03bdcb74ac2507b8860dd89c4889462f1b275f15",
          "28145ad3c6708d8266d50ddd459ec50102869eab",
          "78b42c206f79755f53a879e03f154694eec4a476",
          "0655f9c65b160964cdea99dec24a830f69e3518f",
          "dbf352960eb82b7f481732b4dc2c44cc7ef47c6b",
          "5257dac2014444bba20bc69dd19ec235e0793311",
          "e2b78df9240c4127838d77e6b45623263caad58c",
          "bf77f4f7eea3317d010100f75f62c8b5a51209f9",
          "cbc1c292097ac0eb3043633e1e59855fe872b1ff",
          "5dbe916c65d02175476479cac27d70fdb89835ed",
          "a25ba15e577002081e1179e3d85985f5d8736742",
          "c216dca49101942a506a467e04090ff9d983efea",
          "8507b7a2bc2d98a02cb0d9f6bedf86db73adef65",
          "51ae999a343f6af427ebef5afcdc666aea01755b",
          "9edc7819e03bdd61030a871173561771e148b6f4"
        ],
        "raw_margin": 0.06017494201660156,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.030762914740466482,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.02499416470527649,
        "family": "sector-wave",
        "negative_roi": -13.87521635,
        "negative_row_index": 351,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.0670015811920166,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03152606391539457,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.025172263383865356,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 352,
        "negative_signature_ids": [
          "c0771a6971b1c99da7faa77ced05e673ae7db66e"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.06976902484893799,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03211152154556253,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.025917083024978638,
        "family": "sector-wave",
        "negative_roi": -23.7883061,
        "negative_row_index": 353,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.07066687941551208,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.030762914740466482,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.02499416470527649,
        "family": "sector-wave",
        "negative_roi": -14.043427099999999,
        "negative_row_index": 354,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.0670015811920166,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03152606391539457,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.025172263383865356,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 355,
        "negative_signature_ids": [
          "c0771a6971b1c99da7faa77ced05e673ae7db66e"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.06976902484893799,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03211152154556253,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.025917083024978638,
        "family": "sector-wave",
        "negative_roi": -25.23878605,
        "negative_row_index": 356,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.07066687941551208,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.030762914740466482,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.02499416470527649,
        "family": "sector-wave",
        "negative_roi": -14.056986299999998,
        "negative_row_index": 372,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.0670015811920166,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03152606391539457,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.025172263383865356,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 373,
        "negative_signature_ids": [
          "c0771a6971b1c99da7faa77ced05e673ae7db66e"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.06976902484893799,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03211152154556253,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.025917083024978638,
        "family": "sector-wave",
        "negative_roi": -24.82134895,
        "negative_row_index": 374,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 80,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "ea7d1d5e5b3fd962e31369b0a575b00ba7a06d77",
          "f74e7b5bf148ce419faa9df1833b8506884ce8b8",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "17ac6cfa4de7915c4580f5973b639740714a25b7",
          "75ebbcc3c4a2da659953cbda065896c8c2154e24",
          "793893e58bd0e06a4febd9d839ac8cba86fbffb6",
          "b2679a5f4a14f3a54e966eedd9434dcf3a168e1f",
          "3cc078d7eeb11efc4b2d1fe562c4f2ccfab61ab9",
          "ea06a4a0d0c7f2ff8ed663dc1e873351e68c497e",
          "49969583813f467db98c280e15c011ce24577d03",
          "b1ad0dbba78ae95d1580a5da1c5469af1977cf37",
          "89210b19974164dbe19f1886ce1d9c319e9b22b4",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "ecebe87553a56e26394397bff798a09ea20b0315",
          "b30e5698875a0afe2242d51ea2b99d64ba485c0d",
          "954b4d35d070e35628aa42a30af32e6e52c1cc09",
          "eb1ddc226c7ebf4146cc8835e1586c31b2bef4cc",
          "05815c79aa3b42f00564138dbcf65de24215b532",
          "2ec5d0d84b69d0b002a240a57ef6d848aeed14a3",
          "ffa43ed1744b8e26f7511d8f1c9fba572e862d60",
          "232903f9320ae84f67f0b4edf0b2a472d863f895",
          "67caf60b647eefa8ef777bcfa6ef681fa1d25fd9",
          "eba597d4bea663cceb5d0c8879baea5dd5923d5d",
          "e470106a024a71028e8ae1a3acd59f1173849f60",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4",
          "028f98a16412c8c9aa487456ecde6dd6ec0c0f7d",
          "0ab9228dfa692b23028d5ff7c885f9297333a4e0",
          "1548787cbe2e8feb5b3d92dafacb096e5c6b6fc7",
          "8c0befa19c2822ac42db6528d63aacc51f944171",
          "57a9cd60a8677ec893d21fc6bf2f5688ccf21b0b",
          "7bfab6d54b69268bc25e724500b0555dca1e7b92"
        ],
        "raw_margin": 0.07066687941551208,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0017604603585706785,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.0023044347763061523,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 295,
        "negative_signature_ids": [
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0527030000000082,
        "positive_row_index": 106,
        "positive_signature_ids": [
          "da4897072bd28baa1076c17c9401b3b21c9496a7",
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "raw_margin": 0.002409040927886963,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.003056274635235015,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.004004418849945068,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 295,
        "negative_signature_ids": [
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.1054060000000163,
        "positive_row_index": 294,
        "positive_signature_ids": [
          "da4897072bd28baa1076c17c9401b3b21c9496a7"
        ],
        "raw_margin": 0.004434704780578613,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02398086609110217,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.020481377840042114,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 375,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 112,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "0d54fe90fffc3ab9063300e392ce54b42328477a",
          "0107d3195d9067b2c62b8739978238140d2318eb",
          "1eff90b1cccb1c380d4201ab8897332d0d010e8a",
          "ea1ca15a9853790b8cc3bb22f7f5ed4db5ead2f9",
          "3fbf64b5865afcb59a3adb484ac16af91af85c9e",
          "7e391b480f09814f3afdbc35a3713a5a0a9ff00b",
          "1dfb71571ce359f27b19c747d59491626ef02e9a",
          "982a0c7a31f96ca33ddb2f867dd0bddcfc19b45b",
          "24c734d8a828ea6c60663471bc6593d24a66c490",
          "4fbe5e6369122e8b80256821a833b536cc518273",
          "b1bd8afa017496c1ccb58773dab278ba496dd474",
          "ac26273e0b24d1d130919c45d9a59480d004d863",
          "656553bcca13d70b45f597f8b014fc6148012e43",
          "97db7b98a28c623801ecf90b88f0b6931638ae4a",
          "e00631e665adb31d0d1377124e44cc57a06e721b",
          "b0ee8b55af14132dd78808ad657352107465ce1d",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c",
          "248da019a9711562239c39a8eb5c620f9132a0cf",
          "545cebe0e6179675d2d37140a14a01d402ee5f74",
          "208faf7c1b2a4316a51e29089020f0e73e292bd6",
          "d3f33252f9f06971f7bdab393f8499d237befab4",
          "b57dd0e73e6d4a775a5f5ac5b45384d4cef94d67",
          "876f719274567fae0fdd457e4eafb1a02f5b6f9c"
        ],
        "raw_margin": 0.05063575506210327,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02457521916142902,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.021469444036483765,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 376,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 112,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "0d54fe90fffc3ab9063300e392ce54b42328477a",
          "0107d3195d9067b2c62b8739978238140d2318eb",
          "1eff90b1cccb1c380d4201ab8897332d0d010e8a",
          "ea1ca15a9853790b8cc3bb22f7f5ed4db5ead2f9",
          "3fbf64b5865afcb59a3adb484ac16af91af85c9e",
          "7e391b480f09814f3afdbc35a3713a5a0a9ff00b",
          "1dfb71571ce359f27b19c747d59491626ef02e9a",
          "982a0c7a31f96ca33ddb2f867dd0bddcfc19b45b",
          "24c734d8a828ea6c60663471bc6593d24a66c490",
          "4fbe5e6369122e8b80256821a833b536cc518273",
          "b1bd8afa017496c1ccb58773dab278ba496dd474",
          "ac26273e0b24d1d130919c45d9a59480d004d863",
          "656553bcca13d70b45f597f8b014fc6148012e43",
          "97db7b98a28c623801ecf90b88f0b6931638ae4a",
          "e00631e665adb31d0d1377124e44cc57a06e721b",
          "b0ee8b55af14132dd78808ad657352107465ce1d",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c",
          "248da019a9711562239c39a8eb5c620f9132a0cf",
          "545cebe0e6179675d2d37140a14a01d402ee5f74",
          "208faf7c1b2a4316a51e29089020f0e73e292bd6",
          "d3f33252f9f06971f7bdab393f8499d237befab4",
          "b57dd0e73e6d4a775a5f5ac5b45384d4cef94d67",
          "876f719274567fae0fdd457e4eafb1a02f5b6f9c"
        ],
        "raw_margin": 0.0510408878326416,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02496025631375176,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.02252975106239319,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 377,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 112,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "0d54fe90fffc3ab9063300e392ce54b42328477a",
          "0107d3195d9067b2c62b8739978238140d2318eb",
          "1eff90b1cccb1c380d4201ab8897332d0d010e8a",
          "ea1ca15a9853790b8cc3bb22f7f5ed4db5ead2f9",
          "3fbf64b5865afcb59a3adb484ac16af91af85c9e",
          "7e391b480f09814f3afdbc35a3713a5a0a9ff00b",
          "1dfb71571ce359f27b19c747d59491626ef02e9a",
          "982a0c7a31f96ca33ddb2f867dd0bddcfc19b45b",
          "24c734d8a828ea6c60663471bc6593d24a66c490",
          "4fbe5e6369122e8b80256821a833b536cc518273",
          "b1bd8afa017496c1ccb58773dab278ba496dd474",
          "ac26273e0b24d1d130919c45d9a59480d004d863",
          "656553bcca13d70b45f597f8b014fc6148012e43",
          "97db7b98a28c623801ecf90b88f0b6931638ae4a",
          "e00631e665adb31d0d1377124e44cc57a06e721b",
          "b0ee8b55af14132dd78808ad657352107465ce1d",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c",
          "248da019a9711562239c39a8eb5c620f9132a0cf",
          "545cebe0e6179675d2d37140a14a01d402ee5f74",
          "208faf7c1b2a4316a51e29089020f0e73e292bd6",
          "d3f33252f9f06971f7bdab393f8499d237befab4",
          "b57dd0e73e6d4a775a5f5ac5b45384d4cef94d67",
          "876f719274567fae0fdd457e4eafb1a02f5b6f9c"
        ],
        "raw_margin": 0.05044668912887573,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.024631433262705435,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.02156546711921692,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 378,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 112,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "0d54fe90fffc3ab9063300e392ce54b42328477a",
          "0107d3195d9067b2c62b8739978238140d2318eb",
          "1eff90b1cccb1c380d4201ab8897332d0d010e8a",
          "ea1ca15a9853790b8cc3bb22f7f5ed4db5ead2f9",
          "3fbf64b5865afcb59a3adb484ac16af91af85c9e",
          "7e391b480f09814f3afdbc35a3713a5a0a9ff00b",
          "1dfb71571ce359f27b19c747d59491626ef02e9a",
          "982a0c7a31f96ca33ddb2f867dd0bddcfc19b45b",
          "24c734d8a828ea6c60663471bc6593d24a66c490",
          "4fbe5e6369122e8b80256821a833b536cc518273",
          "b1bd8afa017496c1ccb58773dab278ba496dd474",
          "ac26273e0b24d1d130919c45d9a59480d004d863",
          "656553bcca13d70b45f597f8b014fc6148012e43",
          "97db7b98a28c623801ecf90b88f0b6931638ae4a",
          "e00631e665adb31d0d1377124e44cc57a06e721b",
          "b0ee8b55af14132dd78808ad657352107465ce1d",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c",
          "248da019a9711562239c39a8eb5c620f9132a0cf",
          "545cebe0e6179675d2d37140a14a01d402ee5f74",
          "208faf7c1b2a4316a51e29089020f0e73e292bd6",
          "d3f33252f9f06971f7bdab393f8499d237befab4",
          "b57dd0e73e6d4a775a5f5ac5b45384d4cef94d67",
          "876f719274567fae0fdd457e4eafb1a02f5b6f9c"
        ],
        "raw_margin": 0.051074326038360596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02447906911767074,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.021659880876541138,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 380,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 112,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "0d54fe90fffc3ab9063300e392ce54b42328477a",
          "0107d3195d9067b2c62b8739978238140d2318eb",
          "1eff90b1cccb1c380d4201ab8897332d0d010e8a",
          "ea1ca15a9853790b8cc3bb22f7f5ed4db5ead2f9",
          "3fbf64b5865afcb59a3adb484ac16af91af85c9e",
          "7e391b480f09814f3afdbc35a3713a5a0a9ff00b",
          "1dfb71571ce359f27b19c747d59491626ef02e9a",
          "982a0c7a31f96ca33ddb2f867dd0bddcfc19b45b",
          "24c734d8a828ea6c60663471bc6593d24a66c490",
          "4fbe5e6369122e8b80256821a833b536cc518273",
          "b1bd8afa017496c1ccb58773dab278ba496dd474",
          "ac26273e0b24d1d130919c45d9a59480d004d863",
          "656553bcca13d70b45f597f8b014fc6148012e43",
          "97db7b98a28c623801ecf90b88f0b6931638ae4a",
          "e00631e665adb31d0d1377124e44cc57a06e721b",
          "b0ee8b55af14132dd78808ad657352107465ce1d",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c",
          "248da019a9711562239c39a8eb5c620f9132a0cf",
          "545cebe0e6179675d2d37140a14a01d402ee5f74",
          "208faf7c1b2a4316a51e29089020f0e73e292bd6",
          "d3f33252f9f06971f7bdab393f8499d237befab4",
          "b57dd0e73e6d4a775a5f5ac5b45384d4cef94d67",
          "876f719274567fae0fdd457e4eafb1a02f5b6f9c"
        ],
        "raw_margin": 0.05329453945159912,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 375,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 296,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0005943530703268474,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0009880661964416504,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 376,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 296,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": 0.0004051327705383301,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0009793902226495899,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0020483732223510742,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 377,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 296,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": -0.00018906593322753906,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.000650567171603264,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0010840892791748047,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 378,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 296,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": 0.0004385709762573242,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0004982030265685694,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0011785030364990234,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 380,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 296,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": 0.0026587843894958496,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0005943530703268474,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.0009880661964416504,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 375,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 297,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": -0.0004051327705383301,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 376,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 297,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0003850371523227425,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0010603070259094238,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 377,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 297,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": -0.0005941987037658691,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 5.6214101276416684e-05,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 9.60230827331543e-05,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 378,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 297,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 3.343820571899414e-05,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -9.615004375827796e-05,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.00019043684005737305,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 380,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 297,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 0.0022536516189575195,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0009793902226495899,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.0020483732223510742,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 375,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 298,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": 0.00018906593322753906,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0003850371523227425,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.0010603070259094238,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 376,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 298,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": 0.0005941987037658691,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 377,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 298,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0003288230510463258,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.0009642839431762695,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 378,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 298,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": 0.0006276369094848633,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.00048118719608102045,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.0008698701858520508,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 380,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 298,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": 0.0028478503227233887,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.000650567171603264,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.0010840892791748047,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 375,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 315,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": -0.0004385709762573242,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -5.6214101276416684e-05,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -9.60230827331543e-05,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 376,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 315,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": -3.343820571899414e-05,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0003288230510463258,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0009642839431762695,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 377,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 315,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": -0.0006276369094848633,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 378,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 315,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.00015236414503469464,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 9.441375732421875e-05,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 380,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 315,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 0.0022202134132385254,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.023801862664116186,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.022271543741226196,
        "family": "random-wave",
        "negative_roi": -4.615673,
        "negative_row_index": 344,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 16,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610",
          "5eb6524966fda15efa4e7e09c01583fd595708eb",
          "5941b6246365253c722846bc57d6aa0ff1d5678b",
          "1b91dc4cacee8b52126c978f183be529a6eecd15",
          "87e39fb82467fa27cfb15520d217a890fe1e34b9",
          "e274eadc330adbff3ee7816c10f24ebf5ee28072",
          "f19f75a3f612989de8501dec61d8a5f280dde982",
          "a00def804157834ef1ef693490b054d3a1b06a52",
          "12d39a9166c07584339956724c3b9629f60e96ec",
          "dec5836ca4c31a94151790b646161738d76354ca",
          "63a6716c5204d479cee65dfde777b80d389e151d",
          "e7ef98113df78e51601008e2700211bcbaf2a93b",
          "dbdd3d8c99c0c20b39e54754321d5647e2715296",
          "add17947f4c14ea3b8def062a7e9e84c75c6d472",
          "30bfa95f96ced77ef83d28e40f8b615d35916f58",
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b",
          "3cae3edaa55c8bae673db1fd81ae1dbbc76ed896",
          "0ff57baa1b7be2817c6d59eb6662e91dbf5f32cf",
          "a428ce2b0def8f6319942cc9674b40bcb85fa845",
          "48fc4bdb216aaeff6c2f62dded62d51c2e573418",
          "95caeedc4414c9eae8e1ac97492f36b36cb071ec",
          "a51028330795a1be87b3d6b39bf888659a9cd336",
          "67a161990fafc0e4aaf2913a454761a4154262d5",
          "6af3092db17ab8ea04873e5342a56f5c572f4290",
          "38d6756e98294a53a2af8a87a4ad51923b8f67d9"
        ],
        "raw_margin": 0.047313809394836426,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.026432794798973147,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.02534148097038269,
        "family": "random-wave",
        "negative_roi": -3.1229681,
        "negative_row_index": 345,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 16,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610",
          "5eb6524966fda15efa4e7e09c01583fd595708eb",
          "5941b6246365253c722846bc57d6aa0ff1d5678b",
          "1b91dc4cacee8b52126c978f183be529a6eecd15",
          "87e39fb82467fa27cfb15520d217a890fe1e34b9",
          "e274eadc330adbff3ee7816c10f24ebf5ee28072",
          "f19f75a3f612989de8501dec61d8a5f280dde982",
          "a00def804157834ef1ef693490b054d3a1b06a52",
          "12d39a9166c07584339956724c3b9629f60e96ec",
          "dec5836ca4c31a94151790b646161738d76354ca",
          "63a6716c5204d479cee65dfde777b80d389e151d",
          "e7ef98113df78e51601008e2700211bcbaf2a93b",
          "dbdd3d8c99c0c20b39e54754321d5647e2715296",
          "add17947f4c14ea3b8def062a7e9e84c75c6d472",
          "30bfa95f96ced77ef83d28e40f8b615d35916f58",
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b",
          "3cae3edaa55c8bae673db1fd81ae1dbbc76ed896",
          "0ff57baa1b7be2817c6d59eb6662e91dbf5f32cf",
          "a428ce2b0def8f6319942cc9674b40bcb85fa845",
          "48fc4bdb216aaeff6c2f62dded62d51c2e573418",
          "95caeedc4414c9eae8e1ac97492f36b36cb071ec",
          "a51028330795a1be87b3d6b39bf888659a9cd336",
          "67a161990fafc0e4aaf2913a454761a4154262d5",
          "6af3092db17ab8ea04873e5342a56f5c572f4290",
          "38d6756e98294a53a2af8a87a4ad51923b8f67d9"
        ],
        "raw_margin": 0.051980674266815186,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.025536370216310555,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.02466556429862976,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 346,
        "negative_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 16,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610",
          "5eb6524966fda15efa4e7e09c01583fd595708eb",
          "5941b6246365253c722846bc57d6aa0ff1d5678b",
          "1b91dc4cacee8b52126c978f183be529a6eecd15",
          "87e39fb82467fa27cfb15520d217a890fe1e34b9",
          "e274eadc330adbff3ee7816c10f24ebf5ee28072",
          "f19f75a3f612989de8501dec61d8a5f280dde982",
          "a00def804157834ef1ef693490b054d3a1b06a52",
          "12d39a9166c07584339956724c3b9629f60e96ec",
          "dec5836ca4c31a94151790b646161738d76354ca",
          "63a6716c5204d479cee65dfde777b80d389e151d",
          "e7ef98113df78e51601008e2700211bcbaf2a93b",
          "dbdd3d8c99c0c20b39e54754321d5647e2715296",
          "add17947f4c14ea3b8def062a7e9e84c75c6d472",
          "30bfa95f96ced77ef83d28e40f8b615d35916f58",
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b",
          "3cae3edaa55c8bae673db1fd81ae1dbbc76ed896",
          "0ff57baa1b7be2817c6d59eb6662e91dbf5f32cf",
          "a428ce2b0def8f6319942cc9674b40bcb85fa845",
          "48fc4bdb216aaeff6c2f62dded62d51c2e573418",
          "95caeedc4414c9eae8e1ac97492f36b36cb071ec",
          "a51028330795a1be87b3d6b39bf888659a9cd336",
          "67a161990fafc0e4aaf2913a454761a4154262d5",
          "6af3092db17ab8ea04873e5342a56f5c572f4290",
          "38d6756e98294a53a2af8a87a4ad51923b8f67d9"
        ],
        "raw_margin": 0.049621015787124634,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.023801862664116186,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.022271543741226196,
        "family": "random-wave",
        "negative_roi": -4.6268153,
        "negative_row_index": 366,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 16,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610",
          "5eb6524966fda15efa4e7e09c01583fd595708eb",
          "5941b6246365253c722846bc57d6aa0ff1d5678b",
          "1b91dc4cacee8b52126c978f183be529a6eecd15",
          "87e39fb82467fa27cfb15520d217a890fe1e34b9",
          "e274eadc330adbff3ee7816c10f24ebf5ee28072",
          "f19f75a3f612989de8501dec61d8a5f280dde982",
          "a00def804157834ef1ef693490b054d3a1b06a52",
          "12d39a9166c07584339956724c3b9629f60e96ec",
          "dec5836ca4c31a94151790b646161738d76354ca",
          "63a6716c5204d479cee65dfde777b80d389e151d",
          "e7ef98113df78e51601008e2700211bcbaf2a93b",
          "dbdd3d8c99c0c20b39e54754321d5647e2715296",
          "add17947f4c14ea3b8def062a7e9e84c75c6d472",
          "30bfa95f96ced77ef83d28e40f8b615d35916f58",
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b",
          "3cae3edaa55c8bae673db1fd81ae1dbbc76ed896",
          "0ff57baa1b7be2817c6d59eb6662e91dbf5f32cf",
          "a428ce2b0def8f6319942cc9674b40bcb85fa845",
          "48fc4bdb216aaeff6c2f62dded62d51c2e573418",
          "95caeedc4414c9eae8e1ac97492f36b36cb071ec",
          "a51028330795a1be87b3d6b39bf888659a9cd336",
          "67a161990fafc0e4aaf2913a454761a4154262d5",
          "6af3092db17ab8ea04873e5342a56f5c572f4290",
          "38d6756e98294a53a2af8a87a4ad51923b8f67d9"
        ],
        "raw_margin": 0.047313809394836426,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.026432794798973147,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.02534148097038269,
        "family": "random-wave",
        "negative_roi": -3.1140998,
        "negative_row_index": 367,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 16,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610",
          "5eb6524966fda15efa4e7e09c01583fd595708eb",
          "5941b6246365253c722846bc57d6aa0ff1d5678b",
          "1b91dc4cacee8b52126c978f183be529a6eecd15",
          "87e39fb82467fa27cfb15520d217a890fe1e34b9",
          "e274eadc330adbff3ee7816c10f24ebf5ee28072",
          "f19f75a3f612989de8501dec61d8a5f280dde982",
          "a00def804157834ef1ef693490b054d3a1b06a52",
          "12d39a9166c07584339956724c3b9629f60e96ec",
          "dec5836ca4c31a94151790b646161738d76354ca",
          "63a6716c5204d479cee65dfde777b80d389e151d",
          "e7ef98113df78e51601008e2700211bcbaf2a93b",
          "dbdd3d8c99c0c20b39e54754321d5647e2715296",
          "add17947f4c14ea3b8def062a7e9e84c75c6d472",
          "30bfa95f96ced77ef83d28e40f8b615d35916f58",
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b",
          "3cae3edaa55c8bae673db1fd81ae1dbbc76ed896",
          "0ff57baa1b7be2817c6d59eb6662e91dbf5f32cf",
          "a428ce2b0def8f6319942cc9674b40bcb85fa845",
          "48fc4bdb216aaeff6c2f62dded62d51c2e573418",
          "95caeedc4414c9eae8e1ac97492f36b36cb071ec",
          "a51028330795a1be87b3d6b39bf888659a9cd336",
          "67a161990fafc0e4aaf2913a454761a4154262d5",
          "6af3092db17ab8ea04873e5342a56f5c572f4290",
          "38d6756e98294a53a2af8a87a4ad51923b8f67d9"
        ],
        "raw_margin": 0.051980674266815186,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.025536370216310555,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.02466556429862976,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 368,
        "negative_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 16,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610",
          "5eb6524966fda15efa4e7e09c01583fd595708eb",
          "5941b6246365253c722846bc57d6aa0ff1d5678b",
          "1b91dc4cacee8b52126c978f183be529a6eecd15",
          "87e39fb82467fa27cfb15520d217a890fe1e34b9",
          "e274eadc330adbff3ee7816c10f24ebf5ee28072",
          "f19f75a3f612989de8501dec61d8a5f280dde982",
          "a00def804157834ef1ef693490b054d3a1b06a52",
          "12d39a9166c07584339956724c3b9629f60e96ec",
          "dec5836ca4c31a94151790b646161738d76354ca",
          "63a6716c5204d479cee65dfde777b80d389e151d",
          "e7ef98113df78e51601008e2700211bcbaf2a93b",
          "dbdd3d8c99c0c20b39e54754321d5647e2715296",
          "add17947f4c14ea3b8def062a7e9e84c75c6d472",
          "30bfa95f96ced77ef83d28e40f8b615d35916f58",
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b",
          "3cae3edaa55c8bae673db1fd81ae1dbbc76ed896",
          "0ff57baa1b7be2817c6d59eb6662e91dbf5f32cf",
          "a428ce2b0def8f6319942cc9674b40bcb85fa845",
          "48fc4bdb216aaeff6c2f62dded62d51c2e573418",
          "95caeedc4414c9eae8e1ac97492f36b36cb071ec",
          "a51028330795a1be87b3d6b39bf888659a9cd336",
          "67a161990fafc0e4aaf2913a454761a4154262d5",
          "6af3092db17ab8ea04873e5342a56f5c572f4290",
          "38d6756e98294a53a2af8a87a4ad51923b8f67d9"
        ],
        "raw_margin": 0.049621015787124634,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.030265135415031064,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.02400323748588562,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 332,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 89,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "8542f41b465c625a6f70966f170fc547ac713bc5",
          "115b353fbbe325151d1d572a6dece2341ca66fb7",
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868",
          "3ab47c08e43e31061dd578dd045175695d6ff0af",
          "3dc1e4ad634f968f3901deeeb5fd360c94940ebc",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "b46a019dedc5387f9d28d8c71ad394dc6efbac29",
          "4bfa8fc05f987dbceb24a6b769749380c2b1c6fd",
          "439b7b8900988aa08d459904417c872be5dcb16f",
          "ec0f6ec0d089d9ac107b8a9870c2170594c9c95b",
          "6fe6f3720ea5387bf77a6d11ee5ef218417a98a3",
          "9410032377db4ebcaafbc31a2f3bbf90dcc8cfe4",
          "d91b78e745b525c74290f230e24353dd7d8b189b",
          "1be1163d34970254d92cb1a16b0337b399a0fff6",
          "526bf101cb3b54b6a76c82c37bb16f1d1987355b",
          "e9b1b18782094bafa9212a8a5fd7f674cf5fc2ff",
          "7cbc01d28add72d0f29827907667042d67ce717c",
          "4beb7059475b972ac442390e875785db5f7354b1",
          "d690299650dba89ea96815c77623afec08aaa746",
          "23113ba4b29c0b6533bcdc79cfab21d906b85043",
          "f0a6d29f9cd28fd87bc41b47d5f6eef45650c9df",
          "ed6d69e23b8496caad478c0800c1c24dc43fb2de",
          "4d84e597f56c71eb28d4433c9a258b7bcef92136",
          "1fd976f5de7e388fcaebb8edd5ef810db37be606",
          "52ffe12432cd297b194f997810c5e9192778624a",
          "b765b2e8cb86b8c54b76356f0279b8e196d3eeae",
          "88f54bdb57bf73eb3a29714db0e99e94c56a236f",
          "a6e761272d5e361994c8931437cd7d3b1f540e62",
          "e26ea5e31cf2dddbec82219e36b0a9631c0ff891",
          "d9bc5f3eb86f9df6c8c544c5beeb1ec58ea705f0",
          "56ff1ccba3f60ad19238ce72ee6c7edcfe2519de"
        ],
        "raw_margin": 0.06670284271240234,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.030854624884410722,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.024598151445388794,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 334,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 89,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "8542f41b465c625a6f70966f170fc547ac713bc5",
          "115b353fbbe325151d1d572a6dece2341ca66fb7",
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868",
          "3ab47c08e43e31061dd578dd045175695d6ff0af",
          "3dc1e4ad634f968f3901deeeb5fd360c94940ebc",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "b46a019dedc5387f9d28d8c71ad394dc6efbac29",
          "4bfa8fc05f987dbceb24a6b769749380c2b1c6fd",
          "439b7b8900988aa08d459904417c872be5dcb16f",
          "ec0f6ec0d089d9ac107b8a9870c2170594c9c95b",
          "6fe6f3720ea5387bf77a6d11ee5ef218417a98a3",
          "9410032377db4ebcaafbc31a2f3bbf90dcc8cfe4",
          "d91b78e745b525c74290f230e24353dd7d8b189b",
          "1be1163d34970254d92cb1a16b0337b399a0fff6",
          "526bf101cb3b54b6a76c82c37bb16f1d1987355b",
          "e9b1b18782094bafa9212a8a5fd7f674cf5fc2ff",
          "7cbc01d28add72d0f29827907667042d67ce717c",
          "4beb7059475b972ac442390e875785db5f7354b1",
          "d690299650dba89ea96815c77623afec08aaa746",
          "23113ba4b29c0b6533bcdc79cfab21d906b85043",
          "f0a6d29f9cd28fd87bc41b47d5f6eef45650c9df",
          "ed6d69e23b8496caad478c0800c1c24dc43fb2de",
          "4d84e597f56c71eb28d4433c9a258b7bcef92136",
          "1fd976f5de7e388fcaebb8edd5ef810db37be606",
          "52ffe12432cd297b194f997810c5e9192778624a",
          "b765b2e8cb86b8c54b76356f0279b8e196d3eeae",
          "88f54bdb57bf73eb3a29714db0e99e94c56a236f",
          "a6e761272d5e361994c8931437cd7d3b1f540e62",
          "e26ea5e31cf2dddbec82219e36b0a9631c0ff891",
          "d9bc5f3eb86f9df6c8c544c5beeb1ec58ea705f0",
          "56ff1ccba3f60ad19238ce72ee6c7edcfe2519de"
        ],
        "raw_margin": 0.06789791584014893,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03035642404291146,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.024540871381759644,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 382,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 89,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "8542f41b465c625a6f70966f170fc547ac713bc5",
          "115b353fbbe325151d1d572a6dece2341ca66fb7",
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868",
          "3ab47c08e43e31061dd578dd045175695d6ff0af",
          "3dc1e4ad634f968f3901deeeb5fd360c94940ebc",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "b46a019dedc5387f9d28d8c71ad394dc6efbac29",
          "4bfa8fc05f987dbceb24a6b769749380c2b1c6fd",
          "439b7b8900988aa08d459904417c872be5dcb16f",
          "ec0f6ec0d089d9ac107b8a9870c2170594c9c95b",
          "6fe6f3720ea5387bf77a6d11ee5ef218417a98a3",
          "9410032377db4ebcaafbc31a2f3bbf90dcc8cfe4",
          "d91b78e745b525c74290f230e24353dd7d8b189b",
          "1be1163d34970254d92cb1a16b0337b399a0fff6",
          "526bf101cb3b54b6a76c82c37bb16f1d1987355b",
          "e9b1b18782094bafa9212a8a5fd7f674cf5fc2ff",
          "7cbc01d28add72d0f29827907667042d67ce717c",
          "4beb7059475b972ac442390e875785db5f7354b1",
          "d690299650dba89ea96815c77623afec08aaa746",
          "23113ba4b29c0b6533bcdc79cfab21d906b85043",
          "f0a6d29f9cd28fd87bc41b47d5f6eef45650c9df",
          "ed6d69e23b8496caad478c0800c1c24dc43fb2de",
          "4d84e597f56c71eb28d4433c9a258b7bcef92136",
          "1fd976f5de7e388fcaebb8edd5ef810db37be606",
          "52ffe12432cd297b194f997810c5e9192778624a",
          "b765b2e8cb86b8c54b76356f0279b8e196d3eeae",
          "88f54bdb57bf73eb3a29714db0e99e94c56a236f",
          "a6e761272d5e361994c8931437cd7d3b1f540e62",
          "e26ea5e31cf2dddbec82219e36b0a9631c0ff891",
          "d9bc5f3eb86f9df6c8c544c5beeb1ec58ea705f0",
          "56ff1ccba3f60ad19238ce72ee6c7edcfe2519de"
        ],
        "raw_margin": 0.0674850344657898,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.030265135415031064,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.02400323748588562,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 389,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 89,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "8542f41b465c625a6f70966f170fc547ac713bc5",
          "115b353fbbe325151d1d572a6dece2341ca66fb7",
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868",
          "3ab47c08e43e31061dd578dd045175695d6ff0af",
          "3dc1e4ad634f968f3901deeeb5fd360c94940ebc",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "b46a019dedc5387f9d28d8c71ad394dc6efbac29",
          "4bfa8fc05f987dbceb24a6b769749380c2b1c6fd",
          "439b7b8900988aa08d459904417c872be5dcb16f",
          "ec0f6ec0d089d9ac107b8a9870c2170594c9c95b",
          "6fe6f3720ea5387bf77a6d11ee5ef218417a98a3",
          "9410032377db4ebcaafbc31a2f3bbf90dcc8cfe4",
          "d91b78e745b525c74290f230e24353dd7d8b189b",
          "1be1163d34970254d92cb1a16b0337b399a0fff6",
          "526bf101cb3b54b6a76c82c37bb16f1d1987355b",
          "e9b1b18782094bafa9212a8a5fd7f674cf5fc2ff",
          "7cbc01d28add72d0f29827907667042d67ce717c",
          "4beb7059475b972ac442390e875785db5f7354b1",
          "d690299650dba89ea96815c77623afec08aaa746",
          "23113ba4b29c0b6533bcdc79cfab21d906b85043",
          "f0a6d29f9cd28fd87bc41b47d5f6eef45650c9df",
          "ed6d69e23b8496caad478c0800c1c24dc43fb2de",
          "4d84e597f56c71eb28d4433c9a258b7bcef92136",
          "1fd976f5de7e388fcaebb8edd5ef810db37be606",
          "52ffe12432cd297b194f997810c5e9192778624a",
          "b765b2e8cb86b8c54b76356f0279b8e196d3eeae",
          "88f54bdb57bf73eb3a29714db0e99e94c56a236f",
          "a6e761272d5e361994c8931437cd7d3b1f540e62",
          "e26ea5e31cf2dddbec82219e36b0a9631c0ff891",
          "d9bc5f3eb86f9df6c8c544c5beeb1ec58ea705f0",
          "56ff1ccba3f60ad19238ce72ee6c7edcfe2519de"
        ],
        "raw_margin": 0.06670284271240234,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.030854624884410722,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.024598151445388794,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 89,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "8542f41b465c625a6f70966f170fc547ac713bc5",
          "115b353fbbe325151d1d572a6dece2341ca66fb7",
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868",
          "3ab47c08e43e31061dd578dd045175695d6ff0af",
          "3dc1e4ad634f968f3901deeeb5fd360c94940ebc",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "b46a019dedc5387f9d28d8c71ad394dc6efbac29",
          "4bfa8fc05f987dbceb24a6b769749380c2b1c6fd",
          "439b7b8900988aa08d459904417c872be5dcb16f",
          "ec0f6ec0d089d9ac107b8a9870c2170594c9c95b",
          "6fe6f3720ea5387bf77a6d11ee5ef218417a98a3",
          "9410032377db4ebcaafbc31a2f3bbf90dcc8cfe4",
          "d91b78e745b525c74290f230e24353dd7d8b189b",
          "1be1163d34970254d92cb1a16b0337b399a0fff6",
          "526bf101cb3b54b6a76c82c37bb16f1d1987355b",
          "e9b1b18782094bafa9212a8a5fd7f674cf5fc2ff",
          "7cbc01d28add72d0f29827907667042d67ce717c",
          "4beb7059475b972ac442390e875785db5f7354b1",
          "d690299650dba89ea96815c77623afec08aaa746",
          "23113ba4b29c0b6533bcdc79cfab21d906b85043",
          "f0a6d29f9cd28fd87bc41b47d5f6eef45650c9df",
          "ed6d69e23b8496caad478c0800c1c24dc43fb2de",
          "4d84e597f56c71eb28d4433c9a258b7bcef92136",
          "1fd976f5de7e388fcaebb8edd5ef810db37be606",
          "52ffe12432cd297b194f997810c5e9192778624a",
          "b765b2e8cb86b8c54b76356f0279b8e196d3eeae",
          "88f54bdb57bf73eb3a29714db0e99e94c56a236f",
          "a6e761272d5e361994c8931437cd7d3b1f540e62",
          "e26ea5e31cf2dddbec82219e36b0a9631c0ff891",
          "d9bc5f3eb86f9df6c8c544c5beeb1ec58ea705f0",
          "56ff1ccba3f60ad19238ce72ee6c7edcfe2519de"
        ],
        "raw_margin": 0.06789791584014893,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 332,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 302,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0005894894693796587,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0005949139595031738,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 334,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 302,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.001195073127746582,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 9.128862788039538e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0005376338958740234,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 382,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 302,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0007821917533874512,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 389,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 302,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0005894894693796587,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0005949139595031738,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 302,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.001195073127746582,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.000620354893106495,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0008791685104370117,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 332,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 303,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0007417201995849609,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -3.0865423726836316e-05,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0002842545509338379,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 334,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 303,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.0004533529281616211,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0005290662652260997,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0003415346145629883,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 382,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 303,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 4.0471553802490234e-05,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.000620354893106495,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0008791685104370117,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 389,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 303,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0007417201995849609,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -3.0865423726836316e-05,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0002842545509338379,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 303,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.0004533529281616211,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0005894894693796587,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0005949139595031738,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 332,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 304,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.001195073127746582,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 334,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 304,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0004982008414992634,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -5.728006362915039e-05,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 382,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 304,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.00041288137435913086,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0005894894693796587,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0005949139595031738,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 389,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 304,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.001195073127746582,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 304,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0005813900859883425,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0007111430168151855,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 332,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 316,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": -0.0009250044822692871,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 8.099383391316217e-06,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.00011622905731201172,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 334,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 316,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": 0.0002700686454772949,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0004901014581079471,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0001735091209411621,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 382,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 316,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": -0.00014281272888183594,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0005813900859883425,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0007111430168151855,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 389,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 316,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": -0.0009250044822692871,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 8.099383391316217e-06,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.00011622905731201172,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 316,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": 0.0002700686454772949,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.000620354893106495,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0008791685104370117,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 332,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 333,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0007417201995849609,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -3.0865423726836316e-05,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0002842545509338379,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 334,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 333,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.0004533529281616211,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0005290662652260997,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0003415346145629883,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 382,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 333,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 4.0471553802490234e-05,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.000620354893106495,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0008791685104370117,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 389,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 333,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0007417201995849609,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -3.0865423726836316e-05,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0002842545509338379,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 333,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.0004533529281616211,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.000620354893106495,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0008791685104370117,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 332,
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
        "raw_margin": -0.0007417201995849609,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -3.0865423726836316e-05,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0002842545509338379,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 334,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 390,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.0004533529281616211,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0005290662652260997,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0003415346145629883,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 382,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 390,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 4.0471553802490234e-05,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.000620354893106495,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0008791685104370117,
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
        "raw_margin": -0.0007417201995849609,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -3.0865423726836316e-05,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0002842545509338379,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 390,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.0004533529281616211,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03337130434806451,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.026193439960479736,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 311,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 109,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d",
          "e92756f39247cf7a0abeb6c6c67a11df2eb656da",
          "07ab39f6d67a922f7c2400b352e0f46d988de197",
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba",
          "5010788a87cbb728d6ddb5c5d1e9a006d61d9fe2",
          "3cc76d9fa753f980535e956a3b833c5fc2fdb564",
          "b473f765eb30279603db8771482064992678125a",
          "98210e3f8ea57dab49cb747a439f3f6f0d8d75a1",
          "c3ed3ff468be157a5e2bffb76e3362334e672393",
          "5d4e83a8c0a47051d184ed1fe6ec5fda7d9b9ed5",
          "4ed772c70b22652028885035f7d723b60c7285db",
          "84f653a181c1a9c95cbb1a72fdb894c0d479d555",
          "1a0f6d593b501079ec45dab7fb8e2a3b033e0647",
          "89e72db1e137c4f79d7835cb04d3b3054b847e13",
          "88bb2e1b190bab3a5dc49d9588c9a4c7f30b28f5",
          "caf91cba20530e86476264ff69d164c8c9fe35c4",
          "37c26ebfd6a6d0846b72a1f987bfcd58ac10b08d",
          "ec548a5054201b1d9938be8cf2c81cb51dbaaa6e",
          "e17fa2296cba926ecf7471c10ffa68677f541d12",
          "035605b74e0149eea2a2e6a3edef8683563c7b62",
          "275bdd9e3ec8b32715eab9ae0be34a87a0782082",
          "8af2b78f1ba49dd346fae60196aa41895d2703fc",
          "ec6a8b326669a89d4af12e330332fb9ffe0434f6",
          "7e33e5cc0ae138857495782469e091c16e0187dd",
          "a0d8e8cdf633b8eb88d72b46ea27f57b3eb39aee",
          "714e381fd8037c2407e76df0ba81b9458bd0c75d",
          "933f7b9b54cfb75a85309f186ce8e340f330c7c3",
          "88f60cba49e5d8608c9252f502a958727efc2262",
          "9459e597fb3b95b2129b3cea9846fda136bc80b2",
          "22abe14ddf1a48b9b5a5bf98a65d0dea467bfb9c",
          "c52c024812ef68aad39a25d86a29cce7e7829619",
          "9ed8c41e1ff40771bd9787fcbd0f4860d45b4012"
        ],
        "raw_margin": 0.0741618275642395,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03310636574491997,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.02584207057952881,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 361,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 109,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d",
          "e92756f39247cf7a0abeb6c6c67a11df2eb656da",
          "07ab39f6d67a922f7c2400b352e0f46d988de197",
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba",
          "5010788a87cbb728d6ddb5c5d1e9a006d61d9fe2",
          "3cc76d9fa753f980535e956a3b833c5fc2fdb564",
          "b473f765eb30279603db8771482064992678125a",
          "98210e3f8ea57dab49cb747a439f3f6f0d8d75a1",
          "c3ed3ff468be157a5e2bffb76e3362334e672393",
          "5d4e83a8c0a47051d184ed1fe6ec5fda7d9b9ed5",
          "4ed772c70b22652028885035f7d723b60c7285db",
          "84f653a181c1a9c95cbb1a72fdb894c0d479d555",
          "1a0f6d593b501079ec45dab7fb8e2a3b033e0647",
          "89e72db1e137c4f79d7835cb04d3b3054b847e13",
          "88bb2e1b190bab3a5dc49d9588c9a4c7f30b28f5",
          "caf91cba20530e86476264ff69d164c8c9fe35c4",
          "37c26ebfd6a6d0846b72a1f987bfcd58ac10b08d",
          "ec548a5054201b1d9938be8cf2c81cb51dbaaa6e",
          "e17fa2296cba926ecf7471c10ffa68677f541d12",
          "035605b74e0149eea2a2e6a3edef8683563c7b62",
          "275bdd9e3ec8b32715eab9ae0be34a87a0782082",
          "8af2b78f1ba49dd346fae60196aa41895d2703fc",
          "ec6a8b326669a89d4af12e330332fb9ffe0434f6",
          "7e33e5cc0ae138857495782469e091c16e0187dd",
          "a0d8e8cdf633b8eb88d72b46ea27f57b3eb39aee",
          "714e381fd8037c2407e76df0ba81b9458bd0c75d",
          "933f7b9b54cfb75a85309f186ce8e340f330c7c3",
          "88f60cba49e5d8608c9252f502a958727efc2262",
          "9459e597fb3b95b2129b3cea9846fda136bc80b2",
          "22abe14ddf1a48b9b5a5bf98a65d0dea467bfb9c",
          "c52c024812ef68aad39a25d86a29cce7e7829619",
          "9ed8c41e1ff40771bd9787fcbd0f4860d45b4012"
        ],
        "raw_margin": 0.07379072904586792,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.032645349033111684,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.025928080081939697,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 362,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 109,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d",
          "e92756f39247cf7a0abeb6c6c67a11df2eb656da",
          "07ab39f6d67a922f7c2400b352e0f46d988de197",
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba",
          "5010788a87cbb728d6ddb5c5d1e9a006d61d9fe2",
          "3cc76d9fa753f980535e956a3b833c5fc2fdb564",
          "b473f765eb30279603db8771482064992678125a",
          "98210e3f8ea57dab49cb747a439f3f6f0d8d75a1",
          "c3ed3ff468be157a5e2bffb76e3362334e672393",
          "5d4e83a8c0a47051d184ed1fe6ec5fda7d9b9ed5",
          "4ed772c70b22652028885035f7d723b60c7285db",
          "84f653a181c1a9c95cbb1a72fdb894c0d479d555",
          "1a0f6d593b501079ec45dab7fb8e2a3b033e0647",
          "89e72db1e137c4f79d7835cb04d3b3054b847e13",
          "88bb2e1b190bab3a5dc49d9588c9a4c7f30b28f5",
          "caf91cba20530e86476264ff69d164c8c9fe35c4",
          "37c26ebfd6a6d0846b72a1f987bfcd58ac10b08d",
          "ec548a5054201b1d9938be8cf2c81cb51dbaaa6e",
          "e17fa2296cba926ecf7471c10ffa68677f541d12",
          "035605b74e0149eea2a2e6a3edef8683563c7b62",
          "275bdd9e3ec8b32715eab9ae0be34a87a0782082",
          "8af2b78f1ba49dd346fae60196aa41895d2703fc",
          "ec6a8b326669a89d4af12e330332fb9ffe0434f6",
          "7e33e5cc0ae138857495782469e091c16e0187dd",
          "a0d8e8cdf633b8eb88d72b46ea27f57b3eb39aee",
          "714e381fd8037c2407e76df0ba81b9458bd0c75d",
          "933f7b9b54cfb75a85309f186ce8e340f330c7c3",
          "88f60cba49e5d8608c9252f502a958727efc2262",
          "9459e597fb3b95b2129b3cea9846fda136bc80b2",
          "22abe14ddf1a48b9b5a5bf98a65d0dea467bfb9c",
          "c52c024812ef68aad39a25d86a29cce7e7829619",
          "9ed8c41e1ff40771bd9787fcbd0f4860d45b4012"
        ],
        "raw_margin": 0.07172411680221558,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.00026493860314454054,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.00035136938095092773,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 311,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 7.900282999999945,
        "positive_row_index": 312,
        "positive_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "raw_margin": 0.00037109851837158203,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 361,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 7.900282999999945,
        "positive_row_index": 312,
        "positive_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0004610167118082875,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 8.600950241088867e-05,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 362,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 7.900282999999945,
        "positive_row_index": 312,
        "positive_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "raw_margin": -0.0020666122436523438,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0007259553149528281,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.00026535987854003906,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 311,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.1534749999999576,
        "positive_row_index": 313,
        "positive_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": 0.0024377107620239258,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0004610167118082875,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": -8.600950241088867e-05,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 361,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 2.1534749999999576,
        "positive_row_index": 313,
        "positive_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": 0.0020666122436523438,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 362,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 2.1534749999999576,
        "positive_row_index": 313,
        "positive_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 311,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 360,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.00026493860314454054,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": -0.00035136938095092773,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 361,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 360,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "raw_margin": -0.00037109851837158203,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007259553149528281,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": -0.00026535987854003906,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 362,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 360,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "raw_margin": -0.0024377107620239258,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -3.6452848,
        "negative_row_index": 338,
        "negative_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 13.436328000000003,
        "positive_row_index": 319,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0008159779987962634,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.0012491345405578613,
        "family": "sector-wave",
        "negative_roi": -7.4290636999999995,
        "negative_row_index": 339,
        "negative_signature_ids": [
          "20fdd4b4d638d08cd21bc466cba236faf2b07360"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.436328000000003,
        "positive_row_index": 319,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "raw_margin": 0.0008600354194641113,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 1.5705225570317172e-06,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.0011816024780273438,
        "family": "sector-wave",
        "negative_roi": -2.5419104,
        "negative_row_index": 340,
        "negative_signature_ids": [
          "10f81606d859bf88c1a08bfaab80e229131db94c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.436328000000003,
        "positive_row_index": 319,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "raw_margin": -0.002393960952758789,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.031806219050061424,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.025480836629867554,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 306,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 121,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "634afee36f73a0b14a4505f16b2aad1b47d11c3c",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "2a3774366df9a0b68b08e6d1329214ca486bdde7",
          "ddaf656f075d9c970e9dcafb85db34e5638afcd0",
          "af2e719e7627cb68ba7141edd31368ffa750f1ea",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64",
          "7bc9075584116399f11fff88d64af1ae5c5f313e",
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa",
          "a39eeb12843064b93c89218d0a505ca64d0e437e",
          "ca4724435b906001b47f20e6043d028a3eda9749",
          "331a67344f8a5d9e0f55334d1ca5937990eb827f",
          "a77067df0e61e35e0cae59d44f62de1b54f2623a",
          "cb7abb40ed1b5ab706baf5b0c1b7b084d9b20c72",
          "b3966b681991b453f0f3a0a589e303f4c3e112d7",
          "66ca0b38ce0f8f589b98ff51395c7ba1ecd87ef5",
          "9918afd4acae06fd903e914332a2f6feeaa76abb",
          "66bb115fb5718b2e71302e366571b2d1707571a1",
          "34816fce8565b960f87ec8a3c193bdccade7a295",
          "ed3cd9d3476c4faca905f5398c342e57793ac6bb",
          "d767aa93ac2d6f05a171b39a30e3ea64eec9b91c",
          "190c81dea56d673d968fe6c8c40f399b99e2d06c",
          "d6b748df389ff0d51d4f261766c79751c5c3eb4b",
          "2a5041a0443d496feb062f4303bc7f4b94ab2dcf",
          "60ea06a1d1115af7bcab1de181f0897812637783",
          "a2230b33b193ce6c52531c20482e40da332eb04c",
          "fb2cd7f34207d76086f276cea21f8bf07376d2a8",
          "d1ca6aff92e33f89a9675cc41d13e9c31a33d5a3",
          "dc7ce8eb7a840194cb36fbd4da4ce472390d5f90",
          "e70c2ab46ab825e9f3dd38418cca12f02596a55d",
          "8f251e5e1f4df8ed50d3e61b5c2abcf8b611fdb2",
          "1394e85840c3321d3b58db6bcd9f15abb3ef2080"
        ],
        "raw_margin": 0.0690985918045044,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0325573048230271,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.024463146924972534,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 307,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 121,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "634afee36f73a0b14a4505f16b2aad1b47d11c3c",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "2a3774366df9a0b68b08e6d1329214ca486bdde7",
          "ddaf656f075d9c970e9dcafb85db34e5638afcd0",
          "af2e719e7627cb68ba7141edd31368ffa750f1ea",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64",
          "7bc9075584116399f11fff88d64af1ae5c5f313e",
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa",
          "a39eeb12843064b93c89218d0a505ca64d0e437e",
          "ca4724435b906001b47f20e6043d028a3eda9749",
          "331a67344f8a5d9e0f55334d1ca5937990eb827f",
          "a77067df0e61e35e0cae59d44f62de1b54f2623a",
          "cb7abb40ed1b5ab706baf5b0c1b7b084d9b20c72",
          "b3966b681991b453f0f3a0a589e303f4c3e112d7",
          "66ca0b38ce0f8f589b98ff51395c7ba1ecd87ef5",
          "9918afd4acae06fd903e914332a2f6feeaa76abb",
          "66bb115fb5718b2e71302e366571b2d1707571a1",
          "34816fce8565b960f87ec8a3c193bdccade7a295",
          "ed3cd9d3476c4faca905f5398c342e57793ac6bb",
          "d767aa93ac2d6f05a171b39a30e3ea64eec9b91c",
          "190c81dea56d673d968fe6c8c40f399b99e2d06c",
          "d6b748df389ff0d51d4f261766c79751c5c3eb4b",
          "2a5041a0443d496feb062f4303bc7f4b94ab2dcf",
          "60ea06a1d1115af7bcab1de181f0897812637783",
          "a2230b33b193ce6c52531c20482e40da332eb04c",
          "fb2cd7f34207d76086f276cea21f8bf07376d2a8",
          "d1ca6aff92e33f89a9675cc41d13e9c31a33d5a3",
          "dc7ce8eb7a840194cb36fbd4da4ce472390d5f90",
          "e70c2ab46ab825e9f3dd38418cca12f02596a55d",
          "8f251e5e1f4df8ed50d3e61b5c2abcf8b611fdb2",
          "1394e85840c3321d3b58db6bcd9f15abb3ef2080"
        ],
        "raw_margin": 0.07424664497375488,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03324336685883217,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.025927215814590454,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 335,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 121,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "634afee36f73a0b14a4505f16b2aad1b47d11c3c",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "2a3774366df9a0b68b08e6d1329214ca486bdde7",
          "ddaf656f075d9c970e9dcafb85db34e5638afcd0",
          "af2e719e7627cb68ba7141edd31368ffa750f1ea",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64",
          "7bc9075584116399f11fff88d64af1ae5c5f313e",
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa",
          "a39eeb12843064b93c89218d0a505ca64d0e437e",
          "ca4724435b906001b47f20e6043d028a3eda9749",
          "331a67344f8a5d9e0f55334d1ca5937990eb827f",
          "a77067df0e61e35e0cae59d44f62de1b54f2623a",
          "cb7abb40ed1b5ab706baf5b0c1b7b084d9b20c72",
          "b3966b681991b453f0f3a0a589e303f4c3e112d7",
          "66ca0b38ce0f8f589b98ff51395c7ba1ecd87ef5",
          "9918afd4acae06fd903e914332a2f6feeaa76abb",
          "66bb115fb5718b2e71302e366571b2d1707571a1",
          "34816fce8565b960f87ec8a3c193bdccade7a295",
          "ed3cd9d3476c4faca905f5398c342e57793ac6bb",
          "d767aa93ac2d6f05a171b39a30e3ea64eec9b91c",
          "190c81dea56d673d968fe6c8c40f399b99e2d06c",
          "d6b748df389ff0d51d4f261766c79751c5c3eb4b",
          "2a5041a0443d496feb062f4303bc7f4b94ab2dcf",
          "60ea06a1d1115af7bcab1de181f0897812637783",
          "a2230b33b193ce6c52531c20482e40da332eb04c",
          "fb2cd7f34207d76086f276cea21f8bf07376d2a8",
          "d1ca6aff92e33f89a9675cc41d13e9c31a33d5a3",
          "dc7ce8eb7a840194cb36fbd4da4ce472390d5f90",
          "e70c2ab46ab825e9f3dd38418cca12f02596a55d",
          "8f251e5e1f4df8ed50d3e61b5c2abcf8b611fdb2",
          "1394e85840c3321d3b58db6bcd9f15abb3ef2080"
        ],
        "raw_margin": 0.07407140731811523,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.031806219050061424,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.025480836629867554,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 336,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 121,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "634afee36f73a0b14a4505f16b2aad1b47d11c3c",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "2a3774366df9a0b68b08e6d1329214ca486bdde7",
          "ddaf656f075d9c970e9dcafb85db34e5638afcd0",
          "af2e719e7627cb68ba7141edd31368ffa750f1ea",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64",
          "7bc9075584116399f11fff88d64af1ae5c5f313e",
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa",
          "a39eeb12843064b93c89218d0a505ca64d0e437e",
          "ca4724435b906001b47f20e6043d028a3eda9749",
          "331a67344f8a5d9e0f55334d1ca5937990eb827f",
          "a77067df0e61e35e0cae59d44f62de1b54f2623a",
          "cb7abb40ed1b5ab706baf5b0c1b7b084d9b20c72",
          "b3966b681991b453f0f3a0a589e303f4c3e112d7",
          "66ca0b38ce0f8f589b98ff51395c7ba1ecd87ef5",
          "9918afd4acae06fd903e914332a2f6feeaa76abb",
          "66bb115fb5718b2e71302e366571b2d1707571a1",
          "34816fce8565b960f87ec8a3c193bdccade7a295",
          "ed3cd9d3476c4faca905f5398c342e57793ac6bb",
          "d767aa93ac2d6f05a171b39a30e3ea64eec9b91c",
          "190c81dea56d673d968fe6c8c40f399b99e2d06c",
          "d6b748df389ff0d51d4f261766c79751c5c3eb4b",
          "2a5041a0443d496feb062f4303bc7f4b94ab2dcf",
          "60ea06a1d1115af7bcab1de181f0897812637783",
          "a2230b33b193ce6c52531c20482e40da332eb04c",
          "fb2cd7f34207d76086f276cea21f8bf07376d2a8",
          "d1ca6aff92e33f89a9675cc41d13e9c31a33d5a3",
          "dc7ce8eb7a840194cb36fbd4da4ce472390d5f90",
          "e70c2ab46ab825e9f3dd38418cca12f02596a55d",
          "8f251e5e1f4df8ed50d3e61b5c2abcf8b611fdb2",
          "1394e85840c3321d3b58db6bcd9f15abb3ef2080"
        ],
        "raw_margin": 0.0690985918045044,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.031775628551373544,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02583971619606018,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 381,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 121,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "634afee36f73a0b14a4505f16b2aad1b47d11c3c",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "2a3774366df9a0b68b08e6d1329214ca486bdde7",
          "ddaf656f075d9c970e9dcafb85db34e5638afcd0",
          "af2e719e7627cb68ba7141edd31368ffa750f1ea",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64",
          "7bc9075584116399f11fff88d64af1ae5c5f313e",
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa",
          "a39eeb12843064b93c89218d0a505ca64d0e437e",
          "ca4724435b906001b47f20e6043d028a3eda9749",
          "331a67344f8a5d9e0f55334d1ca5937990eb827f",
          "a77067df0e61e35e0cae59d44f62de1b54f2623a",
          "cb7abb40ed1b5ab706baf5b0c1b7b084d9b20c72",
          "b3966b681991b453f0f3a0a589e303f4c3e112d7",
          "66ca0b38ce0f8f589b98ff51395c7ba1ecd87ef5",
          "9918afd4acae06fd903e914332a2f6feeaa76abb",
          "66bb115fb5718b2e71302e366571b2d1707571a1",
          "34816fce8565b960f87ec8a3c193bdccade7a295",
          "ed3cd9d3476c4faca905f5398c342e57793ac6bb",
          "d767aa93ac2d6f05a171b39a30e3ea64eec9b91c",
          "190c81dea56d673d968fe6c8c40f399b99e2d06c",
          "d6b748df389ff0d51d4f261766c79751c5c3eb4b",
          "2a5041a0443d496feb062f4303bc7f4b94ab2dcf",
          "60ea06a1d1115af7bcab1de181f0897812637783",
          "a2230b33b193ce6c52531c20482e40da332eb04c",
          "fb2cd7f34207d76086f276cea21f8bf07376d2a8",
          "d1ca6aff92e33f89a9675cc41d13e9c31a33d5a3",
          "dc7ce8eb7a840194cb36fbd4da4ce472390d5f90",
          "e70c2ab46ab825e9f3dd38418cca12f02596a55d",
          "8f251e5e1f4df8ed50d3e61b5c2abcf8b611fdb2",
          "1394e85840c3321d3b58db6bcd9f15abb3ef2080"
        ],
        "raw_margin": 0.06954437494277954,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03324336685883217,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.025927215814590454,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 121,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "634afee36f73a0b14a4505f16b2aad1b47d11c3c",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "2a3774366df9a0b68b08e6d1329214ca486bdde7",
          "ddaf656f075d9c970e9dcafb85db34e5638afcd0",
          "af2e719e7627cb68ba7141edd31368ffa750f1ea",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64",
          "7bc9075584116399f11fff88d64af1ae5c5f313e",
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa",
          "a39eeb12843064b93c89218d0a505ca64d0e437e",
          "ca4724435b906001b47f20e6043d028a3eda9749",
          "331a67344f8a5d9e0f55334d1ca5937990eb827f",
          "a77067df0e61e35e0cae59d44f62de1b54f2623a",
          "cb7abb40ed1b5ab706baf5b0c1b7b084d9b20c72",
          "b3966b681991b453f0f3a0a589e303f4c3e112d7",
          "66ca0b38ce0f8f589b98ff51395c7ba1ecd87ef5",
          "9918afd4acae06fd903e914332a2f6feeaa76abb",
          "66bb115fb5718b2e71302e366571b2d1707571a1",
          "34816fce8565b960f87ec8a3c193bdccade7a295",
          "ed3cd9d3476c4faca905f5398c342e57793ac6bb",
          "d767aa93ac2d6f05a171b39a30e3ea64eec9b91c",
          "190c81dea56d673d968fe6c8c40f399b99e2d06c",
          "d6b748df389ff0d51d4f261766c79751c5c3eb4b",
          "2a5041a0443d496feb062f4303bc7f4b94ab2dcf",
          "60ea06a1d1115af7bcab1de181f0897812637783",
          "a2230b33b193ce6c52531c20482e40da332eb04c",
          "fb2cd7f34207d76086f276cea21f8bf07376d2a8",
          "d1ca6aff92e33f89a9675cc41d13e9c31a33d5a3",
          "dc7ce8eb7a840194cb36fbd4da4ce472390d5f90",
          "e70c2ab46ab825e9f3dd38418cca12f02596a55d",
          "8f251e5e1f4df8ed50d3e61b5c2abcf8b611fdb2",
          "1394e85840c3321d3b58db6bcd9f15abb3ef2080"
        ],
        "raw_margin": 0.07407140731811523,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.031806219050061424,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.025480836629867554,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 121,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "634afee36f73a0b14a4505f16b2aad1b47d11c3c",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "2a3774366df9a0b68b08e6d1329214ca486bdde7",
          "ddaf656f075d9c970e9dcafb85db34e5638afcd0",
          "af2e719e7627cb68ba7141edd31368ffa750f1ea",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64",
          "7bc9075584116399f11fff88d64af1ae5c5f313e",
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa",
          "a39eeb12843064b93c89218d0a505ca64d0e437e",
          "ca4724435b906001b47f20e6043d028a3eda9749",
          "331a67344f8a5d9e0f55334d1ca5937990eb827f",
          "a77067df0e61e35e0cae59d44f62de1b54f2623a",
          "cb7abb40ed1b5ab706baf5b0c1b7b084d9b20c72",
          "b3966b681991b453f0f3a0a589e303f4c3e112d7",
          "66ca0b38ce0f8f589b98ff51395c7ba1ecd87ef5",
          "9918afd4acae06fd903e914332a2f6feeaa76abb",
          "66bb115fb5718b2e71302e366571b2d1707571a1",
          "34816fce8565b960f87ec8a3c193bdccade7a295",
          "ed3cd9d3476c4faca905f5398c342e57793ac6bb",
          "d767aa93ac2d6f05a171b39a30e3ea64eec9b91c",
          "190c81dea56d673d968fe6c8c40f399b99e2d06c",
          "d6b748df389ff0d51d4f261766c79751c5c3eb4b",
          "2a5041a0443d496feb062f4303bc7f4b94ab2dcf",
          "60ea06a1d1115af7bcab1de181f0897812637783",
          "a2230b33b193ce6c52531c20482e40da332eb04c",
          "fb2cd7f34207d76086f276cea21f8bf07376d2a8",
          "d1ca6aff92e33f89a9675cc41d13e9c31a33d5a3",
          "dc7ce8eb7a840194cb36fbd4da4ce472390d5f90",
          "e70c2ab46ab825e9f3dd38418cca12f02596a55d",
          "8f251e5e1f4df8ed50d3e61b5c2abcf8b611fdb2",
          "1394e85840c3321d3b58db6bcd9f15abb3ef2080"
        ],
        "raw_margin": 0.0690985918045044,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0014371478087707446,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.0004463791847229004,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 306,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 305,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": -0.00497281551361084,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0006860620358050684,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.00146406888961792,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 307,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 305,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.00017523765563964844,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 335,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 305,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0014371478087707446,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.0004463791847229004,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 336,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 305,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": -0.00497281551361084,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0014677383074586242,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -8.749961853027344e-05,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 381,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 305,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": -0.004527032375335693,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 305,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0014371478087707446,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.0004463791847229004,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 305,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": -0.00497281551361084,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0009349915960700089,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.00048792362213134766,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 306,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 317,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": -0.004821062088012695,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0001839058231043328,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.0005297660827636719,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 307,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 317,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.00032699108123779297,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0005021562127007356,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.000934302806854248,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 335,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 317,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.00015175342559814453,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0009349915960700089,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.00048792362213134766,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 336,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 317,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": -0.004821062088012695,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0009655820947578886,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0008468031883239746,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 381,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 317,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": -0.004375278949737549,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0005021562127007356,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.000934302806854248,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 317,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.00015175342559814453,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0009349915960700089,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.00048792362213134766,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 317,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": -0.004821062088012695,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007510857729656761,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0010176897048950195,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 306,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 337,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.005148053169250488,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 307,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 337,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0006860620358050684,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.00146406888961792,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 335,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 337,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.00017523765563964844,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007510857729656761,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0010176897048950195,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 336,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 337,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.005148053169250488,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007816762716535558,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0013765692710876465,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 381,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 337,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.004702270030975342,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0006860620358050684,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.00146406888961792,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 337,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.00017523765563964844,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007510857729656761,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0010176897048950195,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 337,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.005148053169250488,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007510857729656761,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0010176897048950195,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 306,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.005148053169250488,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 307,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0006860620358050684,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.00146406888961792,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 335,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.00017523765563964844,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007510857729656761,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0010176897048950195,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 336,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.005148053169250488,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007816762716535558,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0013765692710876465,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 381,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.004702270030975342,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0006860620358050684,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.00146406888961792,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.00017523765563964844,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0007510857729656761,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0010176897048950195,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 388,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.005148053169250488,
        "raw_positive_above_negative": false
      }
    ],
    "production_ready": false,
    "runs_bpc_or_pricing": false,
    "summary": {
      "admission_pair_pass_count": 77,
      "admission_pair_pass_rate": 0.5310344827586206,
      "ambiguous_row_count": 0,
      "context_count": 11,
      "contexts_with_positive_and_negative": 11,
      "delay_risk_pair_pass_count": 87,
      "delay_risk_pair_pass_rate": 0.6,
      "family_counts": {
        "random-wave": 24,
        "sector-wave": 58
      },
      "focused_row_count": 82,
      "label_counts": {
        "delay_or_hard_negative": 43,
        "positive_high_priority": 39
      },
      "negative_row_count": 43,
      "pair_count": 145,
      "positive_row_count": 39,
      "primary": "candidate_head_context_ranking_failure",
      "raw_pair_pass_count": 86,
      "raw_pair_pass_rate": 0.593103448275862,
      "strict_pair_pass_count": 64,
      "strict_pair_pass_rate": 0.4413793103448276
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
    "train_context_count": 248,
    "train_family_counts": {
      "greedy-anchor": 37,
      "random-wave": 203,
      "sector-wave": 79
    },
    "train_instances": [
      "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_03_seed71204_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_04_seed71306_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_05_seed71408_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_01_seed71000_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_03_seed71204_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_04_seed71306_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_03_seed91204_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_04_seed91307_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_03_seed91204_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_04_seed91307_logical_graph.json"
    ],
    "validation_context_count": 47,
    "validation_family_counts": {
      "greedy-anchor": 17,
      "random-wave": 15,
      "sector-wave": 41
    },
    "validation_instances": [
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_01_seed71000_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_02_seed71102_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_04_seed141309_logical_graph.json"
    ]
  },
  "threshold_search": {
    "best_local_rejected_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable"
    ],
    "best_rejected_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "knn_ood_audit_missing"
    ],
    "candidate_count": 1,
    "feasible_threshold_count": 0,
    "selected_metrics": {
      "accepted_bad_mode_count": 0,
      "accepted_batch_count": 5,
      "accepted_batch_precision": 1.0,
      "accepted_batch_rate": 0.0684931506849315,
      "accepted_batch_roi": 0.9781723380088806,
      "accepted_batch_roi_ci_low": 0.7365433101612989,
      "accepted_batch_roi_over_baseline": 0.9781723380088806,
      "accepted_batch_roi_over_baseline_ci_low": 0.7365433101612989,
      "accepted_batch_roi_over_best_rc_baseline": 0.9781723380088806,
      "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.7365433101612989,
      "accepted_batch_roi_over_old_gat_baseline": 0.9781723380088806,
      "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.7365433101612989,
      "accepted_batch_roi_over_random_baseline": 0.9781723380088806,
      "accepted_batch_roi_over_random_baseline_ci_low": 0.7365433101612989,
      "baseline_roi_ci_high": 0.0,
      "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
      "baseline_selection_roi": 0.0,
      "batch_threshold": 0.4963304400444031,
      "batch_thresholds_by_family": {
        "random-wave": 0.4963304400444031,
        "sector-wave": 0.4922087788581848
      },
      "best_rc_baseline_accepted_batch_roi": 0.0,
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_blocked_count": 0,
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.5,
      "candidate_delay_score_penalty": 2.0,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_rescue_window_eligible_count": 0,
      "candidate_rescue_window_promoted_count": 0,
      "candidate_risk_adjusted_suppressed_count": 342,
      "candidate_score_threshold_blocked_count": 342,
      "candidate_threshold": 0.15007750573798778,
      "checkpoint_gate_pass": false,
      "checkpoint_gate_reject_reasons": [
        "safe_precision_ci_low_below_threshold_or_not_measurable",
        "knn_ood_audit_missing"
      ],
      "context_delay_fallback_contexts": [],
      "coverage_non_ood": 1.0,
      "delay_label_count": 87,
      "delay_rate": 0.9315068493150684,
      "evaluated_candidate_count": 912,
      "expected_trajectory_utility": 1.0181723380088807,
      "false_high_priority_on_delay": 0.0,
      "false_high_priority_on_delay_count": 0,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 0.0,
      "family_delay_fallback_families": [],
      "family_holdout_min_accepted_high_roi_count": 1,
      "family_holdout_min_accepted_roi": 0.9718791544437408,
      "family_holdout_min_high_roi_capture_rate": 0.16666666666666666,
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
          "max_accepted_batch_roi_label": 0.45004528760910034,
          "oracle_high_roi_count": 0,
          "safe_precision": null,
          "total_batches": 17
        },
        "random-wave": {
          "accepted_batch_count": 2,
          "accepted_batch_roi": 0.9718791544437408,
          "accepted_high_roi_count": 1,
          "high_roi_capture_rate": 0.5,
          "max_accepted_batch_roi_label": 1.3259137868881226,
          "oracle_high_roi_count": 2,
          "safe_precision": 1.0,
          "total_batches": 15
        },
        "sector-wave": {
          "accepted_batch_count": 3,
          "accepted_batch_roi": 0.9823677937189738,
          "accepted_high_roi_count": 3,
          "high_roi_capture_rate": 0.16666666666666666,
          "max_accepted_batch_roi_label": 31.935651779174805,
          "oracle_high_roi_count": 18,
          "safe_precision": 1.0,
          "total_batches": 41
        }
      },
      "family_specific_delay_fallback_families": [
        "greedy-anchor"
      ],
      "hard_reject_reason_categories": [
        "knn_ood_audit_missing",
        "precision_ci_below_gate"
      ],
      "high_priority_precision": 1.0,
      "high_priority_precision_ci_low": 0.9933054696627083,
      "high_priority_prediction_count": 570,
      "high_priority_true_positive_count": 570,
      "max_accepted_bad_mode_count": 0,
      "min_family_accepted_high_roi_count": 0,
      "min_family_high_roi_capture_rate": 0.0,
      "old_gat_baseline_accepted_batch_roi": 0.0,
      "random_baseline_accepted_batch_roi": 0.0,
      "safe_precision": 1.0,
      "safe_precision_ci_low": 0.565508505247919,
      "threshold": 0.4963304400444031,
      "threshold_local_gate_pass": false,
      "threshold_local_hard_reject_reason_categories": [
        "precision_ci_below_gate"
      ],
      "threshold_local_reject_reasons": [
        "safe_precision_ci_low_below_threshold_or_not_measurable"
      ],
      "threshold_mode": "family_local_batch_candidate",
      "total_batches": 73
    }
  },
  "train_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 18,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.05642633228840126,
    "accepted_batch_roi": 0.7535897518197695,
    "accepted_batch_roi_ci_low": 0.3331138152392272,
    "accepted_batch_roi_over_baseline": 0.7535897518197695,
    "accepted_batch_roi_over_baseline_ci_low": 0.3331138152392272,
    "accepted_batch_roi_over_best_rc_baseline": 0.7535897518197695,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.3331138152392272,
    "accepted_batch_roi_over_old_gat_baseline": 0.7535897518197695,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.3331138152392272,
    "accepted_batch_roi_over_random_baseline": 0.7535897518197695,
    "accepted_batch_roi_over_random_baseline_ci_low": 0.3331138152392272,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.4963304400444031,
    "batch_thresholds_by_family": {
      "random-wave": 0.4963304400444031,
      "sector-wave": 0.4922087788581848
    },
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_blocked_count": 1,
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 2.0,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 1651,
    "candidate_score_threshold_blocked_count": 1651,
    "candidate_threshold": 0.15007750573798778,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_batch_missing",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 320,
    "delay_rate": 0.9435736677115988,
    "evaluated_candidate_count": 3791,
    "expected_trajectory_utility": 0.7952564184864362,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.0,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 0,
    "family_holdout_min_accepted_roi": 0.7344213096158845,
    "family_holdout_min_high_roi_capture_rate": 0.0,
    "family_holdout_min_precision": 1.0,
    "family_holdout_missing_accepted_families": [
      "greedy-anchor"
    ],
    "family_holdout_missing_accepted_opportunity_families": [
      "greedy-anchor"
    ],
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
        "total_batches": 37
      },
      "random-wave": {
        "accepted_batch_count": 14,
        "accepted_batch_roi": 0.7344213096158845,
        "accepted_high_roi_count": 4,
        "high_roi_capture_rate": 0.14814814814814814,
        "max_accepted_batch_roi_label": 35.64057159423828,
        "oracle_high_roi_count": 27,
        "safe_precision": 1.0,
        "total_batches": 203
      },
      "sector-wave": {
        "accepted_batch_count": 4,
        "accepted_batch_roi": 0.8206792995333672,
        "accepted_high_roi_count": 2,
        "high_roi_capture_rate": 0.11764705882352941,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 17,
        "safe_precision": 1.0,
        "total_batches": 79
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "holdout_family_collapse",
      "knn_ood_audit_missing",
      "precision_ci_below_gate",
      "roi_ci_below_baseline"
    ],
    "high_priority_precision": 1.0,
    "high_priority_precision_ci_low": 0.9982072403298499,
    "high_priority_prediction_count": 2139,
    "high_priority_true_positive_count": 2139,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8241154494176252,
    "threshold": 0.4963304400444031,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "holdout_family_collapse",
      "precision_ci_below_gate",
      "roi_ci_below_baseline"
    ],
    "threshold_local_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable",
      "family_holdout_accepted_batch_missing"
    ],
    "threshold_mode": "family_local_batch_candidate",
    "total_batches": 319
  },
  "validation_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 5,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.0684931506849315,
    "accepted_batch_roi": 0.9781723380088806,
    "accepted_batch_roi_ci_low": 0.7365433101612989,
    "accepted_batch_roi_over_baseline": 0.9781723380088806,
    "accepted_batch_roi_over_baseline_ci_low": 0.7365433101612989,
    "accepted_batch_roi_over_best_rc_baseline": 0.9781723380088806,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 0.7365433101612989,
    "accepted_batch_roi_over_old_gat_baseline": 0.9781723380088806,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 0.7365433101612989,
    "accepted_batch_roi_over_random_baseline": 0.9781723380088806,
    "accepted_batch_roi_over_random_baseline_ci_low": 0.7365433101612989,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.4963304400444031,
    "batch_thresholds_by_family": {
      "random-wave": 0.4963304400444031,
      "sector-wave": 0.4922087788581848
    },
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_blocked_count": 0,
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.5,
    "candidate_delay_score_penalty": 2.0,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 342,
    "candidate_score_threshold_blocked_count": 342,
    "candidate_threshold": 0.15007750573798778,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 87,
    "delay_rate": 0.9315068493150684,
    "evaluated_candidate_count": 912,
    "expected_trajectory_utility": 1.0181723380088807,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.0,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 1,
    "family_holdout_min_accepted_roi": 0.9718791544437408,
    "family_holdout_min_high_roi_capture_rate": 0.16666666666666666,
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
        "max_accepted_batch_roi_label": 0.45004528760910034,
        "oracle_high_roi_count": 0,
        "safe_precision": null,
        "total_batches": 17
      },
      "random-wave": {
        "accepted_batch_count": 2,
        "accepted_batch_roi": 0.9718791544437408,
        "accepted_high_roi_count": 1,
        "high_roi_capture_rate": 0.5,
        "max_accepted_batch_roi_label": 1.3259137868881226,
        "oracle_high_roi_count": 2,
        "safe_precision": 1.0,
        "total_batches": 15
      },
      "sector-wave": {
        "accepted_batch_count": 3,
        "accepted_batch_roi": 0.9823677937189738,
        "accepted_high_roi_count": 3,
        "high_roi_capture_rate": 0.16666666666666666,
        "max_accepted_batch_roi_label": 31.935651779174805,
        "oracle_high_roi_count": 18,
        "safe_precision": 1.0,
        "total_batches": 41
      }
    },
    "family_specific_delay_fallback_families": [
      "greedy-anchor"
    ],
    "hard_reject_reason_categories": [
      "knn_ood_audit_missing",
      "precision_ci_below_gate"
    ],
    "high_priority_precision": 1.0,
    "high_priority_precision_ci_low": 0.9933054696627083,
    "high_priority_prediction_count": 570,
    "high_priority_true_positive_count": 570,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.565508505247919,
    "threshold": 0.4963304400444031,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "precision_ci_below_gate"
    ],
    "threshold_local_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable"
    ],
    "threshold_mode": "family_local_batch_candidate",
    "total_batches": 73
  }
}
```

## 边界

- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；
- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；
- 当前 checkpoint 仍 `production_ready=false`；
- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；
- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。
