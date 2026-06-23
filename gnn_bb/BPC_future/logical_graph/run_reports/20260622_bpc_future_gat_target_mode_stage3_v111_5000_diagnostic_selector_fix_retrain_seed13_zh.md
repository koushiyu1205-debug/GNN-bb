# GAT Batch Impact Training 报告

日期：2026-06-22

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
sample_count = 1221
candidate_count = 13352
family_counts = {'greedy-anchor': 358, 'random-wave': 449, 'sector-wave': 414}
task_count_counts = {'10': 74, '100': 36, '20': 792, '30': 168, '5': 32, '50': 119}
training_objective = precision_constrained_roi_maximization
training_run_config = {'seed': 13, 'validation_fraction': 0.25, 'epochs': 8, 'device': 'cuda', 'lr': 0.001, 'weight_decay': 1e-05, 'max_grad_norm': 5.0, 'model_config': {'node_dim': 9, 'option_dim': 10, 'candidate_feature_dim': 40, 'context_feature_dim': 26, 'batch_feature_dim': 18, 'path_token_vocab_size': 4096, 'path_pair_vocab_size': 4096, 'path_type_vocab_size': 3, 'path_token_dim': 16, 'path_hidden_dim': 32, 'hidden_dim': 32, 'option_hidden_dim': 32, 'pair_edge_dim': 32, 'num_gnn_layers': 1, 'heads': 4, 'dropout': 0.05, 'candidate_hidden_dim': 32, 'context_hidden_dim': 24, 'batch_hidden_dim': 32, 'impact_hidden_dim': 32, 'use_layer_norm': True}, 'loss_options': {'false_high_priority_loss_multiplier': 8.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 1.25, 'hard_roi_negative_delay_loss_multiplier': 1.25, 'hard_roi_safe_delay_loss_multiplier': 0.35, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 1.5, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'focused_pair_loss_multiplier': 0.5, 'focused_pair_candidate_loss_multiplier': 0.75, 'focused_pair_admission_loss_multiplier': 1.0, 'focused_pair_delay_risk_loss_multiplier': 1.25, 'focused_pair_batch_loss_multiplier': 0.5, 'focused_pair_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/focused_row_indices.json', 'focused_pair_row_indices': [10, 11, 16, 80, 89, 106, 109, 112, 121, 133, 176, 177, 183, 326, 331, 334, 362, 376, 377, 378, 379, 380, 381, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 430, 431, 432, 433, 434, 435, 436, 437, 438, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 459, 460, 461, 463, 475, 483, 492, 509, 514, 517, 527, 553, 670, 729, 730, 740, 741, 742, 743, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 767, 768, 770, 776, 777, 778, 779, 780, 781, 782, 783, 792, 793, 795, 796, 797, 798, 799, 808, 809, 810, 811, 812, 813, 814, 815, 842, 843, 844, 845, 846, 847, 848, 849, 888, 889, 918, 919, 922, 923, 956, 958, 959, 960, 961, 962, 963, 966, 967, 969, 978, 979, 980, 981, 982, 983, 985, 990, 991, 992, 993, 998, 999, 1001, 1010, 1011, 1012, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1040, 1041, 1042, 1050, 1051, 1053, 1097, 1101, 1104, 1123, 1125], 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}, 'gate_config': {'min_high_priority_precision': 0.9, 'min_high_priority_precision_ci_low': 0.9, 'min_safe_precision': 0.9, 'min_safe_precision_ci_low': 0.9, 'confidence_z': 1.96, 'max_false_high_priority_on_delay': 0.01, 'max_false_safe_union_rate': 0.02, 'max_accepted_bad_mode_count': 0, 'min_accepted_batch_count': 1, 'min_accepted_batch_rate': 0.02, 'min_accepted_batch_roi': 0.65, 'min_accepted_batch_roi_ci_low': 0.65, 'baseline_accepted_batch_roi': 0.0, 'baseline_selection_roi': 0.0, 'baseline_roi_ci_high': 0.0, 'baseline_roi_ci_high_source': 'configured_point_estimate_no_baseline_distribution', 'random_baseline_accepted_batch_roi': 0.0, 'best_rc_baseline_accepted_batch_roi': 0.0, 'old_gat_baseline_accepted_batch_roi': 0.0, 'min_roi_margin_over_baseline': 0.2, 'min_family_holdout_precision': 0.8, 'min_family_holdout_accepted_roi': 0.65, 'min_family_accepted_high_roi_count': 0, 'min_family_high_roi_capture_rate': 0.0, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 1.5, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'min_major_families': 2, 'observed_family_count': 3, 'stage3_min_samples': 200, 'actual_sample_count': 1221, 'knn_ood_audit_completed': False, 'candidate_delay_gate_enabled': True, 'candidate_delay_risk_threshold': 0.55, 'require_positive_candidate_threshold': True}, 'focused_pair_gate_config': {'focused_pair_gate_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/focused_row_indices.json', 'focused_pair_row_indices_count': 207, 'focused_pair_selector': 'explicit_row_indices', 'min_focused_pair_count': 1, 'min_focused_raw_pair_pass_rate': 1.0, 'min_focused_admission_pair_pass_rate': 1.0, 'min_focused_delay_risk_pair_pass_rate': 1.0, 'min_focused_strict_pair_pass_rate': 1.0}, 'checkpoint_selection': 'deployment_gate_first_then_roi_ci_baseline_utility_loss'}
hard_roi_threshold = 0.65
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.55
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.5
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
loss_options = {'false_high_priority_loss_multiplier': 8.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 1.25, 'hard_roi_negative_delay_loss_multiplier': 1.25, 'hard_roi_safe_delay_loss_multiplier': 0.35, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 1.5, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'focused_pair_loss_multiplier': 0.5, 'focused_pair_candidate_loss_multiplier': 0.75, 'focused_pair_admission_loss_multiplier': 1.0, 'focused_pair_delay_risk_loss_multiplier': 1.25, 'focused_pair_batch_loss_multiplier': 0.5, 'focused_pair_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/focused_row_indices.json', 'focused_pair_row_indices': [10, 11, 16, 80, 89, 106, 109, 112, 121, 133, 176, 177, 183, 326, 331, 334, 362, 376, 377, 378, 379, 380, 381, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 430, 431, 432, 433, 434, 435, 436, 437, 438, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 459, 460, 461, 463, 475, 483, 492, 509, 514, 517, 527, 553, 670, 729, 730, 740, 741, 742, 743, 748, 749, 750, 751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 767, 768, 770, 776, 777, 778, 779, 780, 781, 782, 783, 792, 793, 795, 796, 797, 798, 799, 808, 809, 810, 811, 812, 813, 814, 815, 842, 843, 844, 845, 846, 847, 848, 849, 888, 889, 918, 919, 922, 923, 956, 958, 959, 960, 961, 962, 963, 966, 967, 969, 978, 979, 980, 981, 982, 983, 985, 990, 991, 992, 993, 998, 999, 1001, 1010, 1011, 1012, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1040, 1041, 1042, 1050, 1051, 1053, 1097, 1101, 1104, 1123, 1125], 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}
pairwise_ranking_loss_active = true
pairwise_candidate_ranking_loss_multiplier = 0.75
pairwise_false_delay_contrast_loss_multiplier = 0.5
pairwise_delay_risk_contrast_loss_multiplier = 1.0
focused_pair_loss_multiplier = 0.5
focused_pair_candidate_loss_multiplier = 0.75
focused_pair_admission_loss_multiplier = 1.0
focused_pair_delay_risk_loss_multiplier = 1.25
focused_pair_batch_loss_multiplier = 0.5
focused_pair_row_index_min = None
focused_pair_row_indices_file = BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/focused_row_indices.json
focused_pair_row_indices_count = 207
pairwise_ranking_status = active_same_context_roi_margin_ranking
context_pair_stats = {'all': {'sample_count': 1221, 'context_count': 546, 'multi_context_count': 235, 'same_context_pair_count': 2050, 'same_context_comparable_pair_count': 1543, 'positive_negative_label_pair_count': 612, 'roi_diverse_context_count': 182, 'largest_context_size': 18}, 'train': {'sample_count': 895, 'context_count': 411, 'multi_context_count': 174, 'same_context_pair_count': 1447, 'same_context_comparable_pair_count': 1090, 'positive_negative_label_pair_count': 444, 'roi_diverse_context_count': 131, 'largest_context_size': 18}, 'validation': {'sample_count': 326, 'context_count': 135, 'multi_context_count': 61, 'same_context_pair_count': 603, 'same_context_comparable_pair_count': 453, 'positive_negative_label_pair_count': 168, 'roi_diverse_context_count': 51, 'largest_context_size': 16}}
focused_pair_gate_active = true
focused_pair_gate_summary = {'focused_row_count': 207, 'context_count': 37, 'contexts_with_positive_and_negative': 37, 'positive_row_count': 117, 'negative_row_count': 90, 'ambiguous_row_count': 0, 'pair_count': 384, 'raw_pair_pass_count': 278, 'admission_pair_pass_count': 297, 'delay_risk_pair_pass_count': 285, 'strict_pair_pass_count': 266, 'raw_pair_pass_rate': 0.7239583333333334, 'admission_pair_pass_rate': 0.7734375, 'delay_risk_pair_pass_rate': 0.7421875, 'strict_pair_pass_rate': 0.6927083333333334, 'label_counts': {'delay_or_hard_negative': 90, 'positive_high_priority': 117}, 'family_counts': {'greedy-anchor': 33, 'random-wave': 75, 'sector-wave': 99}, 'primary': 'candidate_head_context_ranking_failure'}
focused_pair_gate_reject_reasons = ['raw_pair_pass_rate_below_threshold', 'admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_ci_safe_ci_coverage
rejected_checkpoint_reasons = ['admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'knn_ood_audit_missing', 'raw_pair_pass_rate_below_threshold', 'safe_precision_ci_low_below_threshold_or_not_measurable', 'strict_pair_pass_rate_below_threshold']
rejected_checkpoint_reason_categories = ['focused_pair_gate_failed', 'knn_ood_audit_missing', 'precision_ci_below_gate']
best_epoch = 1
selected_validation_loss = 4.016616930127417
best_loss_epoch = 7
best_validation_loss = 2.6069127389770945
best_loss_epoch_gate_pass = false
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run', 'raw_pair_pass_rate_below_threshold', 'safe_precision_ci_low_below_threshold_or_not_measurable', 'strict_pair_pass_rate_below_threshold']
attempted_update_count = 20456
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
    "family_holdout_min_accepted_high_roi_count": 5,
    "family_holdout_min_accepted_roi": 6.602623319625854,
    "family_holdout_min_high_roi_capture_rate": 0.21428571428571427,
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
        "accepted_batch_count": 5,
        "accepted_batch_roi": 6.602623319625854,
        "accepted_high_roi_count": 5,
        "high_roi_capture_rate": 0.25,
        "max_accepted_batch_roi_label": 106.158935546875,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "total_batches": 124
      },
      "random-wave": {
        "accepted_batch_count": 8,
        "accepted_batch_roi": 21.57581076025963,
        "accepted_high_roi_count": 8,
        "high_roi_capture_rate": 0.23529411764705882,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "oracle_high_roi_count": 34,
        "safe_precision": 1.0,
        "total_batches": 132
      },
      "sector-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_roi": 7.988281819555494,
        "accepted_high_roi_count": 6,
        "high_roi_capture_rate": 0.21428571428571427,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 28,
        "safe_precision": 1.0,
        "total_batches": 70
      }
    },
    "family_specific_delay_fallback_families": [],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 5,
        "accepted_batch_roi": 6.602623319625854,
        "accepted_high_roi_count": 5,
        "high_roi_capture_rate": 0.25,
        "max_accepted_batch_roi_label": 106.158935546875,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "total_batches": 124
      },
      "random-wave": {
        "accepted_batch_count": 8,
        "accepted_batch_roi": 21.57581076025963,
        "accepted_high_roi_count": 8,
        "high_roi_capture_rate": 0.23529411764705882,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "oracle_high_roi_count": 34,
        "safe_precision": 1.0,
        "total_batches": 132
      },
      "sector-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_roi": 7.988281819555494,
        "accepted_high_roi_count": 6,
        "high_roi_capture_rate": 0.21428571428571427,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 28,
        "safe_precision": 1.0,
        "total_batches": 70
      }
    }
  },
  "focused_pair_gate": {
    "active": true,
    "context_rows": [
      {
        "admission_pair_pass_rate": 0.0,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_pair_pass_rate": 0.0,
        "family": "greedy-anchor",
        "negative_count": 2,
        "pair_count": 4,
        "positive_count": 2,
        "raw_pair_pass_rate": 0.0,
        "row_count": 4,
        "strict_pair_pass_rate": 0.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "7db256d4f7224cc6",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 1,
        "pair_count": 3,
        "positive_count": 3,
        "raw_pair_pass_rate": 0.6666666666666666,
        "row_count": 4,
        "strict_pair_pass_rate": 0.6666666666666666
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "f9d0b6b18a0a28d3",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|f9d0b6b18a0a28d3",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 2,
        "pair_count": 2,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "84ae11479ed592d4",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 2,
        "pair_count": 2,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "39d7643d5a478407",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614|39d7643d5a478407",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 1,
        "pair_count": 2,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "62c86745ed2b3aaa",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 2,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 0.8571428571428571,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_pair_pass_rate": 0.8571428571428571,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 7,
        "positive_count": 7,
        "raw_pair_pass_rate": 0.7142857142857143,
        "row_count": 8,
        "strict_pair_pass_rate": 0.7142857142857143
      },
      {
        "admission_pair_pass_rate": 0.6666666666666666,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_pair_pass_rate": 0.2222222222222222,
        "family": "random-wave",
        "negative_count": 2,
        "pair_count": 18,
        "positive_count": 9,
        "raw_pair_pass_rate": 0.6666666666666666,
        "row_count": 11,
        "strict_pair_pass_rate": 0.2222222222222222
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "1b5a36a64a700b58",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 3,
        "positive_count": 3,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "4575716b3939cb89",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|4575716b3939cb89",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 2,
        "pair_count": 2,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "ff6827bb236f4831",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|ff6827bb236f4831",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 2,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "9f80ae35ea87da5b",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 2,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
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
        "raw_pair_pass_rate": 0.0,
        "row_count": 2,
        "strict_pair_pass_rate": 0.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 7,
        "pair_count": 28,
        "positive_count": 4,
        "raw_pair_pass_rate": 0.8928571428571429,
        "row_count": 11,
        "strict_pair_pass_rate": 0.8928571428571429
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 1,
        "pair_count": 6,
        "positive_count": 6,
        "raw_pair_pass_rate": 1.0,
        "row_count": 7,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 0.4909090909090909,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_pair_pass_rate": 0.4909090909090909,
        "family": "sector-wave",
        "negative_count": 5,
        "pair_count": 55,
        "positive_count": 11,
        "raw_pair_pass_rate": 0.43636363636363634,
        "row_count": 16,
        "strict_pair_pass_rate": 0.43636363636363634
      },
      {
        "admission_pair_pass_rate": 0.0,
        "context_hash": "1b9dab1b2a407abd",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks030_02_seed71102|1b9dab1b2a407abd",
        "delay_risk_pair_pass_rate": 0.0,
        "family": "sector-wave",
        "negative_count": 1,
        "pair_count": 1,
        "positive_count": 1,
        "raw_pair_pass_rate": 0.0,
        "row_count": 2,
        "strict_pair_pass_rate": 0.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "77bc967e4038b08b",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414|77bc967e4038b08b",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 1,
        "pair_count": 2,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "67925c0d2fd4abde",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 1,
        "pair_count": 3,
        "positive_count": 3,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 0.5,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_pair_pass_rate": 0.5,
        "family": "greedy-anchor",
        "negative_count": 2,
        "pair_count": 4,
        "positive_count": 2,
        "raw_pair_pass_rate": 0.5,
        "row_count": 4,
        "strict_pair_pass_rate": 0.5
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "f4e732e2cfdeea6e",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635|f4e732e2cfdeea6e",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 2,
        "pair_count": 2,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "3d4ab1c1e344186b",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks030_02_seed71115|3d4ab1c1e344186b",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 1,
        "pair_count": 1,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 2,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "5c522ff2995f86be",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 3,
        "positive_count": 3,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "9eb0dc7839bf91ec",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|9eb0dc7839bf91ec",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 2,
        "pair_count": 2,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 0.7333333333333333,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_pair_pass_rate": 0.7333333333333333,
        "family": "random-wave",
        "negative_count": 6,
        "pair_count": 30,
        "positive_count": 5,
        "raw_pair_pass_rate": 0.7333333333333333,
        "row_count": 11,
        "strict_pair_pass_rate": 0.7333333333333333
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "a77e5457bde80b8e",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717|a77e5457bde80b8e",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 3,
        "pair_count": 3,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "7cb380a02e30e5a8",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 3,
        "pair_count": 3,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "03605a430acbd104",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923|03605a430acbd104",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 3,
        "pair_count": 3,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "5368cf35ed6f06cb",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|5368cf35ed6f06cb",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 2,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "a0f80eb374f29f44",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|a0f80eb374f29f44",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "random-wave",
        "negative_count": 1,
        "pair_count": 2,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 3,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "be33b2560df0147a",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_04_seed71306|be33b2560df0147a",
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
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 9,
        "pair_count": 18,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 11,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 0.7538461538461538,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_pair_pass_rate": 0.6923076923076923,
        "family": "sector-wave",
        "negative_count": 5,
        "pair_count": 65,
        "positive_count": 13,
        "raw_pair_pass_rate": 0.6,
        "row_count": 18,
        "strict_pair_pass_rate": 0.5384615384615384
      },
      {
        "admission_pair_pass_rate": 0.7142857142857143,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_pair_pass_rate": 0.7142857142857143,
        "family": "sector-wave",
        "negative_count": 3,
        "pair_count": 21,
        "positive_count": 7,
        "raw_pair_pass_rate": 0.7142857142857143,
        "row_count": 10,
        "strict_pair_pass_rate": 0.7142857142857143
      },
      {
        "admission_pair_pass_rate": 0.8333333333333334,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_pair_pass_rate": 0.8333333333333334,
        "family": "sector-wave",
        "negative_count": 3,
        "pair_count": 6,
        "positive_count": 2,
        "raw_pair_pass_rate": 0.8333333333333334,
        "row_count": 5,
        "strict_pair_pass_rate": 0.8333333333333334
      },
      {
        "admission_pair_pass_rate": 0.8055555555555556,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_pair_pass_rate": 0.8055555555555556,
        "family": "sector-wave",
        "negative_count": 9,
        "pair_count": 72,
        "positive_count": 8,
        "raw_pair_pass_rate": 0.8055555555555556,
        "row_count": 17,
        "strict_pair_pass_rate": 0.8055555555555556
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "5a812898b6327d87",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks030_01_seed71001|5a812898b6327d87",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 1,
        "pair_count": 1,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 2,
        "strict_pair_pass_rate": 1.0
      }
    ],
    "diagnostic_only": true,
    "focus_row_index_min": null,
    "focus_row_indices_count": 207,
    "focus_row_indices_file": "BPC_future/results/gat_batch_impact_focused_tranche_mining_v110_v107_5000_20260622/focused_row_indices.json",
    "focus_selector": "explicit_row_indices",
    "gate": {
      "blocking_primary": "candidate_head_context_ranking_failure",
      "diagnostic_only": true,
      "gate_name": "focused_same_context_positive_negative_pair_gate",
      "gate_pass": false,
      "observed": {
        "admission_pair_pass_rate": 0.7734375,
        "delay_risk_pair_pass_rate": 0.7421875,
        "pair_count": 384,
        "raw_pair_pass_rate": 0.7239583333333334,
        "strict_pair_pass_rate": 0.6927083333333334
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
        "admission_margin": -0.003971210132251185,
        "admission_positive_above_negative": false,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_margin": -0.005556762218475342,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 814,
        "negative_signature_ids": [
          "205a20d28e242d3d13b42954fc1ccae0302a39a4"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 3.0676430000000323,
        "positive_row_index": 812,
        "positive_signature_ids": [
          "3fa5854924ac844a7e090bde70be0e205e2b3410"
        ],
        "raw_margin": -0.004859596490859985,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.00285040252582458,
        "admission_positive_above_negative": false,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_margin": -0.004208624362945557,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 815,
        "negative_signature_ids": [
          "8358066f8e6f161f10e78cd664b24e52bc318cfc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 3.0676430000000323,
        "positive_row_index": 812,
        "positive_signature_ids": [
          "3fa5854924ac844a7e090bde70be0e205e2b3410"
        ],
        "raw_margin": -0.003154456615447998,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.004859642170815359,
        "admission_positive_above_negative": false,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_margin": -0.007098555564880371,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 814,
        "negative_signature_ids": [
          "205a20d28e242d3d13b42954fc1ccae0302a39a4"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.3209439999999972,
        "positive_row_index": 813,
        "positive_signature_ids": [
          "f2813b715a37b431927f932dd1a75815eeb18ff5"
        ],
        "raw_margin": -0.005492866039276123,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0037388345643887544,
        "admission_positive_above_negative": false,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_margin": -0.005750417709350586,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 815,
        "negative_signature_ids": [
          "8358066f8e6f161f10e78cd664b24e52bc318cfc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.3209439999999972,
        "positive_row_index": 813,
        "positive_signature_ids": [
          "f2813b715a37b431927f932dd1a75815eeb18ff5"
        ],
        "raw_margin": -0.0037877261638641357,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.000251307346835955,
        "admission_positive_above_negative": true,
        "context_hash": "7db256d4f7224cc6",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
        "delay_risk_margin": 0.0005550980567932129,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 991,
        "negative_signature_ids": [
          "a9e74d78debdc9131ca24f9a86350c9e7dde56f9"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.9891109999999799,
        "positive_row_index": 990,
        "positive_signature_ids": [
          "5b29de0980e2376e6f56e7594a22af1af46500cf"
        ],
        "raw_margin": -6.639957427978516e-05,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.01466496054401617,
        "admission_positive_above_negative": true,
        "context_hash": "7db256d4f7224cc6",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
        "delay_risk_margin": 0.021856606006622314,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 991,
        "negative_signature_ids": [
          "a9e74d78debdc9131ca24f9a86350c9e7dde56f9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0364000000000146,
        "positive_row_index": 992,
        "positive_signature_ids": [
          "2d975c2f586f85615e98a289530487579b562c9d"
        ],
        "raw_margin": 0.011746764183044434,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0012558605949247459,
        "admission_positive_above_negative": true,
        "context_hash": "7db256d4f7224cc6",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
        "delay_risk_margin": 0.0020828843116760254,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 991,
        "negative_signature_ids": [
          "a9e74d78debdc9131ca24f9a86350c9e7dde56f9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.217899999999986,
        "positive_row_index": 993,
        "positive_signature_ids": [
          "9fd6e3e1347188affb947a53131652576dca9294"
        ],
        "raw_margin": 0.000767827033996582,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0034892483410864927,
        "admission_positive_above_negative": true,
        "context_hash": "f9d0b6b18a0a28d3",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|f9d0b6b18a0a28d3",
        "delay_risk_margin": 0.004551589488983154,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 982,
        "negative_signature_ids": [
          "e45f41289dac40eb617e88a2a264661abecd070f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.9531660000000102,
        "positive_row_index": 985,
        "positive_signature_ids": [
          "46e4bd7a9913a523423aed6549c83ee06e71692a"
        ],
        "raw_margin": 0.0039418041706085205,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.003041735767030068,
        "admission_positive_above_negative": true,
        "context_hash": "f9d0b6b18a0a28d3",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|f9d0b6b18a0a28d3",
        "delay_risk_margin": 0.004054248332977295,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 983,
        "negative_signature_ids": [
          "09c43766c7a8f610ee71bdc3ab21a62121727684"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.9531660000000102,
        "positive_row_index": 985,
        "positive_signature_ids": [
          "46e4bd7a9913a523423aed6549c83ee06e71692a"
        ],
        "raw_margin": 0.003291308879852295,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0009504750600078937,
        "admission_positive_above_negative": true,
        "context_hash": "84ae11479ed592d4",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
        "delay_risk_margin": 0.0015243887901306152,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 999,
        "negative_signature_ids": [
          "8439a663bf57011fe3ca9499e3226ad1b0fe9202"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.464020000000005,
        "positive_row_index": 998,
        "positive_signature_ids": [
          "624a809b7978342288dd6ef2c4b6c3625122f3a2"
        ],
        "raw_margin": 0.0004616975784301758,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0009664193045121616,
        "admission_positive_above_negative": true,
        "context_hash": "84ae11479ed592d4",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
        "delay_risk_margin": 0.0015506148338317871,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1001,
        "negative_signature_ids": [
          "68a37dbe1ced0b422aeba5886ffc851b80f9f6f4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.464020000000005,
        "positive_row_index": 998,
        "positive_signature_ids": [
          "624a809b7978342288dd6ef2c4b6c3625122f3a2"
        ],
        "raw_margin": 0.0004684925079345703,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0005338037900069759,
        "admission_positive_above_negative": true,
        "context_hash": "39d7643d5a478407",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614|39d7643d5a478407",
        "delay_risk_margin": 0.0009131431579589844,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1041,
        "negative_signature_ids": [
          "88f54e2af94b966edf149b9bce397b36e0d64911"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1169499999999744,
        "positive_row_index": 1040,
        "positive_signature_ids": [
          "489af7490ddca08694403458963d66467e80ded6"
        ],
        "raw_margin": 0.00017917156219482422,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.011181421838201339,
        "admission_positive_above_negative": true,
        "context_hash": "39d7643d5a478407",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614|39d7643d5a478407",
        "delay_risk_margin": 0.018668174743652344,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1041,
        "negative_signature_ids": [
          "88f54e2af94b966edf149b9bce397b36e0d64911"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1169499999999744,
        "positive_row_index": 1042,
        "positive_signature_ids": [
          "6e262f3bc968c7e0f5f77e675dfed1cbe24102c6"
        ],
        "raw_margin": 0.003979086875915527,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.003401813582375429,
        "admission_positive_above_negative": true,
        "context_hash": "62c86745ed2b3aaa",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
        "delay_risk_margin": 0.0050560832023620605,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 767,
        "negative_signature_ids": [
          "c983cae2002dd84fcc5647f6d73c5054c6cfc1e9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.427249999999958,
        "positive_row_index": 768,
        "positive_signature_ids": [
          "e41a77bfe8ec226313371d1746808baead648f04"
        ],
        "raw_margin": 0.002668529748916626,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0020623731556732583,
        "admission_positive_above_negative": true,
        "context_hash": "62c86745ed2b3aaa",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
        "delay_risk_margin": 0.0030724406242370605,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 767,
        "negative_signature_ids": [
          "c983cae2002dd84fcc5647f6d73c5054c6cfc1e9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.8316559999999527,
        "positive_row_index": 770,
        "positive_signature_ids": [
          "9ca91e440dcf5e8d27b7d53ff0ad0e1250838d04"
        ],
        "raw_margin": 0.0016219615936279297,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03828954207246474,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.04127207398414612,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 400,
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
        "raw_margin": 0.035486698150634766,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.028692060544470516,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.023032933473587036,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 400,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 399,
        "positive_signature_ids": [
          "faa3e5eeea745d947ae4d0698ed0ab2d096fee55"
        ],
        "raw_margin": 0.039842844009399414,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0025881551084144527,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.005489706993103027,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 400,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 401,
        "positive_signature_ids": [
          "4ff77aada3bed1157cf8d2056c968e0f3b5ec28c"
        ],
        "raw_margin": -0.0013723373413085938,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.0,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 400,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 418,
        "positive_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.028692060544470516,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.023032933473587036,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 400,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 35.640572999999904,
        "positive_row_index": 427,
        "positive_signature_ids": [
          "faa3e5eeea745d947ae4d0698ed0ab2d096fee55"
        ],
        "raw_margin": 0.039842844009399414,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03828954207246474,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.04127207398414612,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 400,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.564840454545447,
        "positive_row_index": 730,
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
        "raw_margin": 0.035486698150634766,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.028692060544470516,
        "admission_positive_above_negative": true,
        "context_hash": "67c11b5ec80925ec",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec",
        "delay_risk_margin": 0.023032933473587036,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 400,
        "negative_signature_ids": [
          "8d7b86da08c08250173761ceee64c94abd8a4078"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 35.640572999999904,
        "positive_row_index": 760,
        "positive_signature_ids": [
          "faa3e5eeea745d947ae4d0698ed0ab2d096fee55"
        ],
        "raw_margin": 0.039842844009399414,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06491188593542122,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.06151062250137329,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
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
        "raw_margin": 0.056104063987731934,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06491188593542122,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.06151062250137329,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
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
        "raw_margin": 0.056104063987731934,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.003708797721341417,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.0012229979038238525,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.1144286500000005,
        "positive_row_index": 393,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.011437654495239258,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.003708797721341417,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.0012229979038238525,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.1144286500000005,
        "positive_row_index": 393,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.011437654495239258,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.01331456545227841,
        "admission_positive_above_negative": false,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.008527815341949463,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 395,
        "positive_signature_ids": [
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e"
        ],
        "raw_margin": -0.02111220359802246,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.01331456545227841,
        "admission_positive_above_negative": false,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.008527815341949463,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 395,
        "positive_signature_ids": [
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e"
        ],
        "raw_margin": -0.02111220359802246,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.003708797721341417,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.0012229979038238525,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.1685759999999998,
        "positive_row_index": 414,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.011437654495239258,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.003708797721341417,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.0012229979038238525,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.1685759999999998,
        "positive_row_index": 414,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.011437654495239258,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06491188593542122,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.06151062250137329,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 5.672967599999997,
        "positive_row_index": 729,
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
        "raw_margin": 0.056104063987731934,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06491188593542122,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.06151062250137329,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 5.672967599999997,
        "positive_row_index": 729,
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
        "raw_margin": 0.056104063987731934,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.003708797721341417,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.0012229979038238525,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 68.34495299999992,
        "positive_row_index": 756,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.011437654495239258,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.003708797721341417,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.0012229979038238525,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 68.34495299999992,
        "positive_row_index": 756,
        "positive_signature_ids": [
          "50e7fd8fc16daef37c4a657b15e38054fe1a7ae6"
        ],
        "raw_margin": 0.011437654495239258,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.0,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 8.901796999999988,
        "positive_row_index": 757,
        "positive_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": 0.0,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 8.901796999999988,
        "positive_row_index": 757,
        "positive_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.01331456545227841,
        "admission_positive_above_negative": false,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.008527815341949463,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.8646209999999428,
        "positive_row_index": 758,
        "positive_signature_ids": [
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e"
        ],
        "raw_margin": -0.02111220359802246,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.01331456545227841,
        "admission_positive_above_negative": false,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.008527815341949463,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.8646209999999428,
        "positive_row_index": 758,
        "positive_signature_ids": [
          "c01f3a4b259a7cfbd2a45d90ceac03471540396e"
        ],
        "raw_margin": -0.02111220359802246,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0030835185788584685,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.00198403000831604,
        "family": "random-wave",
        "negative_roi": -2.091243899999934,
        "negative_row_index": 394,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 60.691508,
        "positive_row_index": 759,
        "positive_signature_ids": [
          "2790b1a6fd6539333755651296d7389a9b4651ec"
        ],
        "raw_margin": 0.011061251163482666,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0030835185788584685,
        "admission_positive_above_negative": true,
        "context_hash": "d519291840dd7000",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000",
        "delay_risk_margin": -0.00198403000831604,
        "family": "random-wave",
        "negative_roi": -2.4618068499999337,
        "negative_row_index": 415,
        "negative_signature_ids": [
          "b99beee79a25f47a7cbe635afbc720de210bb8a7"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 60.691508,
        "positive_row_index": 759,
        "positive_signature_ids": [
          "2790b1a6fd6539333755651296d7389a9b4651ec"
        ],
        "raw_margin": 0.011061251163482666,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0086842314799557,
        "admission_positive_above_negative": true,
        "context_hash": "1b5a36a64a700b58",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
        "delay_risk_margin": 0.012162625789642334,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 962,
        "negative_signature_ids": [
          "3eecf4701b6c140ccfdfe63f73e2344339d73380"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.827841000000035,
        "positive_row_index": 960,
        "positive_signature_ids": [
          "18842c58b0f00e6b29a660ee2a5b6ae0b27e9b7c"
        ],
        "raw_margin": 0.00696486234664917,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.007892085546659877,
        "admission_positive_above_negative": true,
        "context_hash": "1b5a36a64a700b58",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
        "delay_risk_margin": 0.010902702808380127,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 962,
        "negative_signature_ids": [
          "3eecf4701b6c140ccfdfe63f73e2344339d73380"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.547865999999999,
        "positive_row_index": 961,
        "positive_signature_ids": [
          "b5fe09437a6fac7943bdf7d5e984d2e257cf1f24"
        ],
        "raw_margin": 0.0065912604331970215,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.009453282309765249,
        "admission_positive_above_negative": true,
        "context_hash": "1b5a36a64a700b58",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
        "delay_risk_margin": 0.013264894485473633,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 962,
        "negative_signature_ids": [
          "3eecf4701b6c140ccfdfe63f73e2344339d73380"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.7671420000000353,
        "positive_row_index": 963,
        "positive_signature_ids": [
          "8eb838d50c328d925dbc7768e5dd82ac58662dd4"
        ],
        "raw_margin": 0.00750732421875,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0006833046126268338,
        "admission_positive_above_negative": true,
        "context_hash": "4575716b3939cb89",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|4575716b3939cb89",
        "delay_risk_margin": 0.001037895679473877,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 966,
        "negative_signature_ids": [
          "3476c0367a618e78de6462e2b7576afc7633cee5"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.9424950000000081,
        "positive_row_index": 969,
        "positive_signature_ids": [
          "77593990c592b931120e0621f8ed5a9ba4facb07"
        ],
        "raw_margin": 0.00040280818939208984,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0006635907355767579,
        "admission_positive_above_negative": true,
        "context_hash": "4575716b3939cb89",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|4575716b3939cb89",
        "delay_risk_margin": 0.0010363459587097168,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 967,
        "negative_signature_ids": [
          "067e228e74758bc37e5d1e0d7cb5e11d3ab26df4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.9424950000000081,
        "positive_row_index": 969,
        "positive_signature_ids": [
          "77593990c592b931120e0621f8ed5a9ba4facb07"
        ],
        "raw_margin": 0.0003471970558166504,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02375647042278828,
        "admission_positive_above_negative": true,
        "context_hash": "ff6827bb236f4831",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|ff6827bb236f4831",
        "delay_risk_margin": 0.030994415283203125,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 956,
        "negative_signature_ids": [
          "c168f78c7c76623f982e8b808cedd062d2301d92"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7318880000000263,
        "positive_row_index": 958,
        "positive_signature_ids": [
          "338d3c20ead6e7e356b356a449b85989b24cd980"
        ],
        "raw_margin": 0.023127645254135132,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.005015843002070419,
        "admission_positive_above_negative": true,
        "context_hash": "ff6827bb236f4831",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|ff6827bb236f4831",
        "delay_risk_margin": 0.007177472114562988,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 956,
        "negative_signature_ids": [
          "c168f78c7c76623f982e8b808cedd062d2301d92"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.3286259999999857,
        "positive_row_index": 959,
        "positive_signature_ids": [
          "c16a07e07e7bab59cf8c6d8d9dc5087dbebde6d0"
        ],
        "raw_margin": 0.004415601491928101,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08444288321210705,
        "admission_positive_above_negative": true,
        "context_hash": "9f80ae35ea87da5b",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b",
        "delay_risk_margin": 0.09439888596534729,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 845,
        "negative_signature_ids": [
          "69da70b1c525d148dcf51b562acf1ac0a38d3958"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1059776938775532,
        "positive_row_index": 183,
        "positive_signature_ids": [
          "68e5f6c80feb460842b2b56b376e80534bd40d53",
          "f37d8b30013b320a5c8b90b12083fc644d67d8bc",
          "3506ec4833577b465e3fde1365176e653a50dd1d",
          "3adb379a80675284249705ef0e41515d4554cce9",
          "69da70b1c525d148dcf51b562acf1ac0a38d3958",
          "90f6ba933e6210351c2aa3e3cbb04a3a85912bba",
          "cf925748d4991c1df840d7ba0c99702f2befc84a",
          "75ad1f2757c8eb5eafa7986c51dfeb430310ee33",
          "24a51ecb63645bfd198d863c8b6c7386892082b1",
          "09003dba001bc401f6afb81dc00076359cdd6d42",
          "b4a24f0fd8b490e40b99aad922d93afb2d1bbc22",
          "62fb88070314fce3e91e561797bf25d9addcf290",
          "c7633a3402dfcbfb7742e7cced0f8194a44b9f92",
          "94669b9a8cf7eae6f1a1f2fe0eeccab80337f52a",
          "e9dbc3f215b883ae5b95b55e26b316969ff65cec",
          "21cff5c1dd7f2c8683d95b883b4c61bea069ba7b",
          "69a883d26e50ce36c1394ffc74f34953a4a085d8",
          "e9eb9355323afb2c6c226393d2b498619da7ab94",
          "2923d2c6910bde76367b352603557a37d3af20e0",
          "415967decd1740d2f293b0039972581eb34f93f3",
          "71c501920cfbf8ffd50df04c43b21d1966706cf0",
          "02c92fb80cf0a5b94ba2c429815450c0bf143060",
          "39b911da1f64ed29b9269261ab5095ac3e3c9882",
          "b1dfc48644a7f95d4eeadd7e81790f86cba1bd88",
          "d23d0a8d6dfd17de5134c9a02eee2d3fb64221ff",
          "d70d82ae18e967db835b527f3ac7208011d0e546",
          "73a09859858cef3eb732a1090e4ced289d46012a",
          "6253163fc8820cffebc5ccbaaa4c38e94a545b3a",
          "a24c98aa5e616080175ab51d72f414051804e99e",
          "ff7e814c3014a9d2bf593886c485663859df04b7",
          "217a4316772c9124c0a2de292b61ad0bd1bf6322",
          "b53626955150973b9871b577b2f6df2fa619e10a"
        ],
        "raw_margin": 0.07856214046478271,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.048335605655807995,
        "admission_positive_above_negative": true,
        "context_hash": "9f80ae35ea87da5b",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b",
        "delay_risk_margin": 0.045305848121643066,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 845,
        "negative_signature_ids": [
          "69da70b1c525d148dcf51b562acf1ac0a38d3958"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 53.71779400000014,
        "positive_row_index": 844,
        "positive_signature_ids": [
          "68e5f6c80feb460842b2b56b376e80534bd40d53"
        ],
        "raw_margin": 0.0651242733001709,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.008310168730201628,
        "admission_positive_above_negative": true,
        "context_hash": "9a2ca522ff49991c",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks050_01_seed91000|9a2ca522ff49991c",
        "delay_risk_margin": 0.029133230447769165,
        "family": "random-wave",
        "negative_roi": -4.876676650000114,
        "negative_row_index": 402,
        "negative_signature_ids": [
          "12506331f28530e7a9219a687bfbce8930dacb32"
        ],
        "pair_pass": false,
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
        "raw_margin": -0.02758699655532837,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -13.87521635,
        "negative_row_index": 403,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07562480295213986,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0815981924533844,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 404,
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
        "raw_margin": 0.06762087345123291,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -23.7883061,
        "negative_row_index": 405,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -14.043427099999999,
        "negative_row_index": 406,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -25.23878605,
        "negative_row_index": 407,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -14.056986299999998,
        "negative_row_index": 419,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -24.82134895,
        "negative_row_index": 420,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -13.87521635,
        "negative_row_index": 403,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 475,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07562480295213986,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0815981924533844,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 404,
        "negative_signature_ids": [
          "c0771a6971b1c99da7faa77ced05e673ae7db66e"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 475,
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
        "raw_margin": 0.06762087345123291,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -23.7883061,
        "negative_row_index": 405,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 475,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -14.043427099999999,
        "negative_row_index": 406,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 475,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -25.23878605,
        "negative_row_index": 407,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 475,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -14.056986299999998,
        "negative_row_index": 419,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 475,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -24.82134895,
        "negative_row_index": 420,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 475,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -13.87521635,
        "negative_row_index": 403,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 492,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07562480295213986,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0815981924533844,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 404,
        "negative_signature_ids": [
          "c0771a6971b1c99da7faa77ced05e673ae7db66e"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 492,
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
        "raw_margin": 0.06762087345123291,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -23.7883061,
        "negative_row_index": 405,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 492,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -14.043427099999999,
        "negative_row_index": 406,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 492,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -25.23878605,
        "negative_row_index": 407,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 492,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05910291464139261,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0630357563495636,
        "family": "sector-wave",
        "negative_roi": -14.056986299999998,
        "negative_row_index": 419,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 492,
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
        "raw_margin": 0.05035507678985596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08818084103154275,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.09548637270927429,
        "family": "sector-wave",
        "negative_roi": -24.82134895,
        "negative_row_index": 420,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.5335839583333335,
        "positive_row_index": 492,
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
        "raw_margin": 0.08278962969779968,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0005738127989813047,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0018329322338104248,
        "family": "sector-wave",
        "negative_roi": -13.87521635,
        "negative_row_index": 403,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 10.567640000000011,
        "positive_row_index": 1101,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4"
        ],
        "raw_margin": -0.0012447237968444824,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.01709570110972855,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.020395368337631226,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 404,
        "negative_signature_ids": [
          "c0771a6971b1c99da7faa77ced05e673ae7db66e"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 10.567640000000011,
        "positive_row_index": 1101,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4"
        ],
        "raw_margin": 0.01602107286453247,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.029651739189131443,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.03428354859352112,
        "family": "sector-wave",
        "negative_roi": -23.7883061,
        "negative_row_index": 405,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 10.567640000000011,
        "positive_row_index": 1101,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4"
        ],
        "raw_margin": 0.031189829111099243,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0005738127989813047,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0018329322338104248,
        "family": "sector-wave",
        "negative_roi": -14.043427099999999,
        "negative_row_index": 406,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 10.567640000000011,
        "positive_row_index": 1101,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4"
        ],
        "raw_margin": -0.0012447237968444824,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.029651739189131443,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.03428354859352112,
        "family": "sector-wave",
        "negative_roi": -25.23878605,
        "negative_row_index": 407,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 10.567640000000011,
        "positive_row_index": 1101,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4"
        ],
        "raw_margin": 0.031189829111099243,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0005738127989813047,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.0018329322338104248,
        "family": "sector-wave",
        "negative_roi": -14.056986299999998,
        "negative_row_index": 419,
        "negative_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 10.567640000000011,
        "positive_row_index": 1101,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4"
        ],
        "raw_margin": -0.0012447237968444824,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.029651739189131443,
        "admission_positive_above_negative": true,
        "context_hash": "0df8d5cea7864e69",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204|0df8d5cea7864e69",
        "delay_risk_margin": 0.03428354859352112,
        "family": "sector-wave",
        "negative_roi": -24.82134895,
        "negative_row_index": 420,
        "negative_signature_ids": [
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 10.567640000000011,
        "positive_row_index": 1101,
        "positive_signature_ids": [
          "790642e0edd08b069de087221b6ae205c6247908",
          "c0771a6971b1c99da7faa77ced05e673ae7db66e",
          "78ab61774d4cc284554e4a08c8e9fbbc2e8c10a9",
          "77c06eaee31a843ae5b1fa7bf743c7201e2abde4"
        ],
        "raw_margin": 0.031189829111099243,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.006614680541711826,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.009451866149902344,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 426,
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
        "raw_margin": 0.005828768014907837,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.006614680541711826,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.009451866149902344,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 426,
        "negative_signature_ids": [
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0527030000000082,
        "positive_row_index": 331,
        "positive_signature_ids": [
          "da4897072bd28baa1076c17c9401b3b21c9496a7",
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "raw_margin": 0.005828768014907837,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.006614680541711826,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.009451866149902344,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 426,
        "negative_signature_ids": [
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0527030000000082,
        "positive_row_index": 362,
        "positive_signature_ids": [
          "da4897072bd28baa1076c17c9401b3b21c9496a7",
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "raw_margin": 0.005828768014907837,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.007290469872348021,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.010472297668457031,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 426,
        "negative_signature_ids": [
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.1054060000000163,
        "positive_row_index": 425,
        "positive_signature_ids": [
          "da4897072bd28baa1076c17c9401b3b21c9496a7"
        ],
        "raw_margin": 0.006311208009719849,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.006614680541711826,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.009451866149902344,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 426,
        "negative_signature_ids": [
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0527030000000082,
        "positive_row_index": 514,
        "positive_signature_ids": [
          "da4897072bd28baa1076c17c9401b3b21c9496a7",
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "raw_margin": 0.005828768014907837,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.006614680541711826,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.009451866149902344,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 426,
        "negative_signature_ids": [
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0527030000000082,
        "positive_row_index": 1097,
        "positive_signature_ids": [
          "da4897072bd28baa1076c17c9401b3b21c9496a7",
          "2edc790d9698e188e46e80784f5d88c29579b3d4"
        ],
        "raw_margin": 0.005828768014907837,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.029878713983152616,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.04301297664642334,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
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
        "raw_margin": 0.0031020045280456543,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.028476536262161956,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.040900737047195435,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
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
        "raw_margin": 0.0030306577682495117,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04403932554616097,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0475897490978241,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
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
        "raw_margin": 0.03149145841598511,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02845227002379125,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.04086688160896301,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
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
        "raw_margin": 0.0030251145362854004,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.013166684004120743,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.02244052290916443,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
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
        "raw_margin": -0.004526913166046143,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.029878713983152616,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.04301297664642334,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 334,
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
        "raw_margin": 0.0031020045280456543,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.028476536262161956,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.040900737047195435,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 334,
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
        "raw_margin": 0.0030306577682495117,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04403932554616097,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0475897490978241,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 334,
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
        "raw_margin": 0.03149145841598511,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02845227002379125,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.04086688160896301,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 334,
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
        "raw_margin": 0.0030251145362854004,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.013166684004120743,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.02244052290916443,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 334,
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
        "raw_margin": -0.004526913166046143,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 433,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0014021777209906605,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.0021122395992279053,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 433,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": -7.134675979614258e-05,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.014160611563008352,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.004576772451400757,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 433,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": 0.028389453887939453,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0014264439593613676,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.002146095037460327,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 433,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": -7.68899917602539e-05,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.016712029979031873,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.02057245373725891,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 433,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": -0.007628917694091797,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0014021777209906605,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0021122395992279053,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 434,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 7.134675979614258e-05,
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
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 434,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.015562789283999012,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.006689012050628662,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 434,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 0.028460800647735596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -2.426623837070707e-05,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -3.3855438232421875e-05,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 434,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": -5.543231964111328e-06,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.015309852258041212,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.018460214138031006,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 434,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": -0.007557570934295654,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.014160611563008352,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.004576772451400757,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 435,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": -0.028389453887939453,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.015562789283999012,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.006689012050628662,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 435,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": -0.028460800647735596,
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
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 435,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.01558705552236972,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.006722867488861084,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 435,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": -0.028466343879699707,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.030872641542040224,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.025149226188659668,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 435,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": -0.03601837158203125,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0014264439593613676,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.002146095037460327,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 459,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 7.68899917602539e-05,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 2.426623837070707e-05,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 3.3855438232421875e-05,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 459,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 5.543231964111328e-06,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.01558705552236972,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.006722867488861084,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 459,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 0.028466343879699707,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 459,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.015285586019670505,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.018426358699798584,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 459,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": -0.007552027702331543,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.029878713983152616,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.04301297664642334,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 517,
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
        "raw_margin": 0.0031020045280456543,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.028476536262161956,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.040900737047195435,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 517,
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
        "raw_margin": 0.0030306577682495117,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04403932554616097,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0475897490978241,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 517,
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
        "raw_margin": 0.03149145841598511,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02845227002379125,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.04086688160896301,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 517,
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
        "raw_margin": 0.0030251145362854004,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.013166684004120743,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.02244052290916443,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.5879691200000026,
        "positive_row_index": 517,
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
        "raw_margin": -0.004526913166046143,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 740,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0014021777209906605,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.0021122395992279053,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 740,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": -7.134675979614258e-05,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.014160611563008352,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.004576772451400757,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 740,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": 0.028389453887939453,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0014264439593613676,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.002146095037460327,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 740,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": -7.68899917602539e-05,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.016712029979031873,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.02057245373725891,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 41.31852700000002,
        "positive_row_index": 740,
        "positive_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "raw_margin": -0.007628917694091797,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0014021777209906605,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0021122395992279053,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 741,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 7.134675979614258e-05,
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
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 741,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.015562789283999012,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.006689012050628662,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 741,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": 0.028460800647735596,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -2.426623837070707e-05,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -3.3855438232421875e-05,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 741,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": -5.543231964111328e-06,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.015309852258041212,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.018460214138031006,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.23960999999997,
        "positive_row_index": 741,
        "positive_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "raw_margin": -0.007557570934295654,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.014160611563008352,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.004576772451400757,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 742,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": -0.028389453887939453,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.015562789283999012,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.006689012050628662,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 742,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": -0.028460800647735596,
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
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 742,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.01558705552236972,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.006722867488861084,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 742,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": -0.028466343879699707,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.030872641542040224,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.025149226188659668,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.8736750000000484,
        "positive_row_index": 742,
        "positive_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "raw_margin": -0.03601837158203125,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0014264439593613676,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.002146095037460327,
        "family": "sector-wave",
        "negative_roi": -0.80674065,
        "negative_row_index": 421,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 743,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 7.68899917602539e-05,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 2.426623837070707e-05,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 3.3855438232421875e-05,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 422,
        "negative_signature_ids": [
          "51c52a8789203772505909c32dfb2d5545329f2f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 743,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 5.543231964111328e-06,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.01558705552236972,
        "admission_positive_above_negative": true,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.006722867488861084,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 423,
        "negative_signature_ids": [
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 743,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 0.028466343879699707,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -2.04948315,
        "negative_row_index": 424,
        "negative_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 743,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.015285586019670505,
        "admission_positive_above_negative": false,
        "context_hash": "b6d808ebac2a6dd8",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8",
        "delay_risk_margin": -0.018426358699798584,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 446,
        "negative_signature_ids": [
          "6fd6470b7c1b23f8fb4fc4216aab95f807d12621",
          "51c52a8789203772505909c32dfb2d5545329f2f",
          "5f79e0e5dba79d3b4403a3e9cfc2ed470e6f070c"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 28.011491999999976,
        "positive_row_index": 743,
        "positive_signature_ids": [
          "0107d3195d9067b2c62b8739978238140d2318eb"
        ],
        "raw_margin": -0.007552027702331543,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0006641405115258847,
        "admission_positive_above_negative": false,
        "context_hash": "1b9dab1b2a407abd",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks030_02_seed71102|1b9dab1b2a407abd",
        "delay_risk_margin": -0.0007507801055908203,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 923,
        "negative_signature_ids": [
          "6cd52fe5346636609262c4972803573d4e776e12"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0419710000001032,
        "positive_row_index": 922,
        "positive_signature_ids": [
          "7925911ed9a6e62074766bd26509735eb63373d4"
        ],
        "raw_margin": -0.0009091794490814209,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0018968344697236628,
        "admission_positive_above_negative": true,
        "context_hash": "77bc967e4038b08b",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414|77bc967e4038b08b",
        "delay_risk_margin": 0.0030705928802490234,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1011,
        "negative_signature_ids": [
          "3ae3d59f7a866d517d984ec92507da18b4cff4b8"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.7335009999999897,
        "positive_row_index": 1010,
        "positive_signature_ids": [
          "76150322a9464a2a1779bb3ffa191d727437a676"
        ],
        "raw_margin": 0.000985264778137207,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.015755010385239965,
        "admission_positive_above_negative": true,
        "context_hash": "77bc967e4038b08b",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414|77bc967e4038b08b",
        "delay_risk_margin": 0.022131502628326416,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1011,
        "negative_signature_ids": [
          "3ae3d59f7a866d517d984ec92507da18b4cff4b8"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.3906840000000216,
        "positive_row_index": 1012,
        "positive_signature_ids": [
          "ce3d6e55d2e76c0443ad52c323006cb05e7a5a9d"
        ],
        "raw_margin": 0.01229897141456604,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.007202037389715199,
        "admission_positive_above_negative": true,
        "context_hash": "67925c0d2fd4abde",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
        "delay_risk_margin": 0.007897883653640747,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1021,
        "negative_signature_ids": [
          "f7926266fc8ac6ddfd0b886f4d7a18ef63f61544"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.236323999999968,
        "positive_row_index": 1018,
        "positive_signature_ids": [
          "93b4b2a6a7626e4569be6525c7a6adfec9ae5142"
        ],
        "raw_margin": 0.00821983814239502,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.012937435450233514,
        "admission_positive_above_negative": true,
        "context_hash": "67925c0d2fd4abde",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
        "delay_risk_margin": 0.013377010822296143,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1021,
        "negative_signature_ids": [
          "f7926266fc8ac6ddfd0b886f4d7a18ef63f61544"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.784813999999983,
        "positive_row_index": 1019,
        "positive_signature_ids": [
          "0cf6431776dbbea53bdc536c4e82dac937a00284"
        ],
        "raw_margin": 0.015669286251068115,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.013916082688441217,
        "admission_positive_above_negative": true,
        "context_hash": "67925c0d2fd4abde",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
        "delay_risk_margin": 0.017839819192886353,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1021,
        "negative_signature_ids": [
          "f7926266fc8ac6ddfd0b886f4d7a18ef63f61544"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.7677429999999958,
        "positive_row_index": 1020,
        "positive_signature_ids": [
          "f3cf872373bae3316adf2d5ca5c9b67dd0bf8cdc"
        ],
        "raw_margin": 0.011546194553375244,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.00015701524184752458,
        "admission_positive_above_negative": false,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_margin": -0.00014096498489379883,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1023,
        "negative_signature_ids": [
          "fcd09bbac25e9a1a3a18689df81a0a296df13a50"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.6925289999999222,
        "positive_row_index": 1022,
        "positive_signature_ids": [
          "9aaa3dd99445936514f4ca04ace40d7f80516104"
        ],
        "raw_margin": -0.00025200843811035156,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.00014818566382712728,
        "admission_positive_above_negative": false,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_margin": -0.00012874603271484375,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1024,
        "negative_signature_ids": [
          "ad32ef0f1bec6d1378959e4aaeca26ff653c01a5"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.6925289999999222,
        "positive_row_index": 1022,
        "positive_signature_ids": [
          "9aaa3dd99445936514f4ca04ace40d7f80516104"
        ],
        "raw_margin": -0.00024443864822387695,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0016710366290434153,
        "admission_positive_above_negative": true,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_margin": 0.002188742160797119,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1023,
        "negative_signature_ids": [
          "fcd09bbac25e9a1a3a18689df81a0a296df13a50"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.3401669999999513,
        "positive_row_index": 1025,
        "positive_signature_ids": [
          "0f77407934f5f1a9fc8199d71a82909c92f25b24"
        ],
        "raw_margin": 0.0016079246997833252,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0016798662070638126,
        "admission_positive_above_negative": true,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_margin": 0.0022009611129760742,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1024,
        "negative_signature_ids": [
          "ad32ef0f1bec6d1378959e4aaeca26ff653c01a5"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.3401669999999513,
        "positive_row_index": 1025,
        "positive_signature_ids": [
          "0f77407934f5f1a9fc8199d71a82909c92f25b24"
        ],
        "raw_margin": 0.0016154944896697998,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.002359353485672039,
        "admission_positive_above_negative": true,
        "context_hash": "f4e732e2cfdeea6e",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635|f4e732e2cfdeea6e",
        "delay_risk_margin": 0.0033528804779052734,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1051,
        "negative_signature_ids": [
          "edc35f433dd3c971fc31bd40bb9593352b313b40"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4304930000000695,
        "positive_row_index": 1050,
        "positive_signature_ids": [
          "f5c1496c9ce34f7ffb4968638dbeb9d355406b48"
        ],
        "raw_margin": 0.0017325878143310547,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.009722130697889103,
        "admission_positive_above_negative": true,
        "context_hash": "f4e732e2cfdeea6e",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635|f4e732e2cfdeea6e",
        "delay_risk_margin": 0.013070940971374512,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1053,
        "negative_signature_ids": [
          "5a50d1321b610b5a3a5a006fb42f0eab4332c538"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4304930000000695,
        "positive_row_index": 1050,
        "positive_signature_ids": [
          "f5c1496c9ce34f7ffb4968638dbeb9d355406b48"
        ],
        "raw_margin": 0.008654356002807617,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.002447938843019609,
        "admission_positive_above_negative": true,
        "context_hash": "3d4ab1c1e344186b",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks030_02_seed71115|3d4ab1c1e344186b",
        "delay_risk_margin": 0.003929257392883301,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 889,
        "negative_signature_ids": [
          "3c88af57d33e909ff4140ec1c1dff3f0c56fc742"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.622827999999913,
        "positive_row_index": 888,
        "positive_signature_ids": [
          "d6dfc2c50b4a6a090536718b0991683327e778ea"
        ],
        "raw_margin": 0.0015336871147155762,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.015452750166006168,
        "admission_positive_above_negative": true,
        "context_hash": "5c522ff2995f86be",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
        "delay_risk_margin": 0.016918838024139404,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 783,
        "negative_signature_ids": [
          "90422b7e8b517792697fd4097c2f4349fa1ef30b"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 10.645972999999913,
        "positive_row_index": 780,
        "positive_signature_ids": [
          "2a1c9e2ffc87d79bf583f9686f50a36b5d2a8879"
        ],
        "raw_margin": 0.0176047682762146,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.011209974488735869,
        "admission_positive_above_negative": true,
        "context_hash": "5c522ff2995f86be",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
        "delay_risk_margin": 0.011789590120315552,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 783,
        "negative_signature_ids": [
          "90422b7e8b517792697fd4097c2f4349fa1ef30b"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.8766339999999673,
        "positive_row_index": 781,
        "positive_signature_ids": [
          "ff1a1773b4144cefe9afd85664ece46251c78634"
        ],
        "raw_margin": 0.013737738132476807,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.011567069806212582,
        "admission_positive_above_negative": true,
        "context_hash": "5c522ff2995f86be",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
        "delay_risk_margin": 0.01084822416305542,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 783,
        "negative_signature_ids": [
          "90422b7e8b517792697fd4097c2f4349fa1ef30b"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.499916999999982,
        "positive_row_index": 782,
        "positive_signature_ids": [
          "d89987e91ead7ec0bc9d7c73fff2b5d2d0606455"
        ],
        "raw_margin": 0.01619821786880493,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.005537634985703477,
        "admission_positive_above_negative": true,
        "context_hash": "9eb0dc7839bf91ec",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|9eb0dc7839bf91ec",
        "delay_risk_margin": 0.0072247982025146484,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 792,
        "negative_signature_ids": [
          "b9bbfb35d482c5c2be7b55c53dae221dd5199ac7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.411269000000061,
        "positive_row_index": 795,
        "positive_signature_ids": [
          "e01ba3a50f761dc4034c75cbff35f854587ccaef"
        ],
        "raw_margin": 0.005814164876937866,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.004218947947904644,
        "admission_positive_above_negative": true,
        "context_hash": "9eb0dc7839bf91ec",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|9eb0dc7839bf91ec",
        "delay_risk_margin": 0.005594491958618164,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 793,
        "negative_signature_ids": [
          "3054dc876dd8fa9ffd64ecb504ac8858d29091c1"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.411269000000061,
        "positive_row_index": 795,
        "positive_signature_ids": [
          "e01ba3a50f761dc4034c75cbff35f854587ccaef"
        ],
        "raw_margin": 0.0042581260204315186,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04480057711394425,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.052691519260406494,
        "family": "random-wave",
        "negative_roi": -4.615673,
        "negative_row_index": 396,
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
        "raw_margin": 0.027641475200653076,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07631717772640473,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.08255985379219055,
        "family": "random-wave",
        "negative_roi": -3.1229681,
        "negative_row_index": 397,
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
        "raw_margin": 0.06666553020477295,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05252063244612759,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.05777445435523987,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 398,
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
        "raw_margin": 0.03992962837219238,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04480057711394425,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.052691519260406494,
        "family": "random-wave",
        "negative_roi": -4.6268153,
        "negative_row_index": 416,
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
        "raw_margin": 0.027641475200653076,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07631717772640473,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.08255985379219055,
        "family": "random-wave",
        "negative_roi": -3.1140998,
        "negative_row_index": 417,
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
        "raw_margin": 0.06666553020477295,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07631717772640473,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.08255985379219055,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 777,
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
        "raw_margin": 0.06666553020477295,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04480057711394425,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.052691519260406494,
        "family": "random-wave",
        "negative_roi": -4.615673,
        "negative_row_index": 396,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 670,
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
        "raw_margin": 0.027641475200653076,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07631717772640473,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.08255985379219055,
        "family": "random-wave",
        "negative_roi": -3.1229681,
        "negative_row_index": 397,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 670,
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
        "raw_margin": 0.06666553020477295,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05252063244612759,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.05777445435523987,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 398,
        "negative_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 670,
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
        "raw_margin": 0.03992962837219238,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04480057711394425,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.052691519260406494,
        "family": "random-wave",
        "negative_roi": -4.6268153,
        "negative_row_index": 416,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 670,
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
        "raw_margin": 0.027641475200653076,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07631717772640473,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.08255985379219055,
        "family": "random-wave",
        "negative_roi": -3.1140998,
        "negative_row_index": 417,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 670,
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
        "raw_margin": 0.06666553020477295,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07631717772640473,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.08255985379219055,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 777,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.751890000000003,
        "positive_row_index": 670,
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
        "raw_margin": 0.06666553020477295,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.0,
        "family": "random-wave",
        "negative_roi": -4.615673,
        "negative_row_index": 396,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 77.04981300000009,
        "positive_row_index": 776,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.03151660061246048,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.029868334531784058,
        "family": "random-wave",
        "negative_roi": -3.1229681,
        "negative_row_index": 397,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 77.04981300000009,
        "positive_row_index": 776,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "raw_margin": 0.03902405500411987,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.00772005533218334,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.005082935094833374,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 398,
        "negative_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 77.04981300000009,
        "positive_row_index": 776,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "raw_margin": 0.012288153171539307,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.0,
        "family": "random-wave",
        "negative_roi": -4.6268153,
        "negative_row_index": 416,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 77.04981300000009,
        "positive_row_index": 776,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.03151660061246048,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.029868334531784058,
        "family": "random-wave",
        "negative_roi": -3.1140998,
        "negative_row_index": 417,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 77.04981300000009,
        "positive_row_index": 776,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "raw_margin": 0.03902405500411987,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03151660061246048,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.029868334531784058,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 777,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 77.04981300000009,
        "positive_row_index": 776,
        "positive_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "raw_margin": 0.03902405500411987,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.00772005533218334,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": -0.005082935094833374,
        "family": "random-wave",
        "negative_roi": -4.615673,
        "negative_row_index": 396,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 11.230681000000004,
        "positive_row_index": 778,
        "positive_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "raw_margin": -0.012288153171539307,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.023796545280277137,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.024785399436950684,
        "family": "random-wave",
        "negative_roi": -3.1229681,
        "negative_row_index": 397,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 11.230681000000004,
        "positive_row_index": 778,
        "positive_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "raw_margin": 0.026735901832580566,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.0,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 398,
        "negative_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 11.230681000000004,
        "positive_row_index": 778,
        "positive_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.00772005533218334,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": -0.005082935094833374,
        "family": "random-wave",
        "negative_roi": -4.6268153,
        "negative_row_index": 416,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 11.230681000000004,
        "positive_row_index": 778,
        "positive_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "raw_margin": -0.012288153171539307,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.023796545280277137,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.024785399436950684,
        "family": "random-wave",
        "negative_roi": -3.1140998,
        "negative_row_index": 417,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 11.230681000000004,
        "positive_row_index": 778,
        "positive_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "raw_margin": 0.026735901832580566,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.023796545280277137,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.024785399436950684,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 777,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 11.230681000000004,
        "positive_row_index": 778,
        "positive_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "raw_margin": 0.026735901832580566,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.01552675460215508,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": -0.014524579048156738,
        "family": "random-wave",
        "negative_roi": -4.615673,
        "negative_row_index": 396,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 12.995546999999988,
        "positive_row_index": 779,
        "positive_signature_ids": [
          "1b91dc4cacee8b52126c978f183be529a6eecd15"
        ],
        "raw_margin": -0.018503904342651367,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.015989846010305397,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.01534375548362732,
        "family": "random-wave",
        "negative_roi": -3.1229681,
        "negative_row_index": 397,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 12.995546999999988,
        "positive_row_index": 779,
        "positive_signature_ids": [
          "1b91dc4cacee8b52126c978f183be529a6eecd15"
        ],
        "raw_margin": 0.020520150661468506,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.00780669926997174,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": -0.009441643953323364,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 398,
        "negative_signature_ids": [
          "c8c7887e24362bd328c4137cac199ecb3eb89a8b"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 12.995546999999988,
        "positive_row_index": 779,
        "positive_signature_ids": [
          "1b91dc4cacee8b52126c978f183be529a6eecd15"
        ],
        "raw_margin": -0.0062157511711120605,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.01552675460215508,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": -0.014524579048156738,
        "family": "random-wave",
        "negative_roi": -4.6268153,
        "negative_row_index": 416,
        "negative_signature_ids": [
          "c06e494797327cf47f580944ebb8c0dc796c9610"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 12.995546999999988,
        "positive_row_index": 779,
        "positive_signature_ids": [
          "1b91dc4cacee8b52126c978f183be529a6eecd15"
        ],
        "raw_margin": -0.018503904342651367,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.015989846010305397,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.01534375548362732,
        "family": "random-wave",
        "negative_roi": -3.1140998,
        "negative_row_index": 417,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 12.995546999999988,
        "positive_row_index": 779,
        "positive_signature_ids": [
          "1b91dc4cacee8b52126c978f183be529a6eecd15"
        ],
        "raw_margin": 0.020520150661468506,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.015989846010305397,
        "admission_positive_above_negative": true,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": 0.01534375548362732,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 777,
        "negative_signature_ids": [
          "a00def804157834ef1ef693490b054d3a1b06a52"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 12.995546999999988,
        "positive_row_index": 779,
        "positive_signature_ids": [
          "1b91dc4cacee8b52126c978f183be529a6eecd15"
        ],
        "raw_margin": 0.020520150661468506,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.019904410931683048,
        "admission_positive_above_negative": true,
        "context_hash": "a77e5457bde80b8e",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717|a77e5457bde80b8e",
        "delay_risk_margin": 0.02616506814956665,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 796,
        "negative_signature_ids": [
          "bde563aaf379f02e6ca8a7df468c3270407593d9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.813146999999958,
        "positive_row_index": 798,
        "positive_signature_ids": [
          "a37eebcdb5526864e04e79e3bb356e9a64b60a7c"
        ],
        "raw_margin": 0.019186347723007202,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.019939593924008375,
        "admission_positive_above_negative": true,
        "context_hash": "a77e5457bde80b8e",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717|a77e5457bde80b8e",
        "delay_risk_margin": 0.026146233081817627,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 797,
        "negative_signature_ids": [
          "2edf3a52e74a5b4f0bec52d9acc5f2e6664d69bd"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.813146999999958,
        "positive_row_index": 798,
        "positive_signature_ids": [
          "a37eebcdb5526864e04e79e3bb356e9a64b60a7c"
        ],
        "raw_margin": 0.019325286149978638,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.024908364610848693,
        "admission_positive_above_negative": true,
        "context_hash": "a77e5457bde80b8e",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717|a77e5457bde80b8e",
        "delay_risk_margin": 0.034871697425842285,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 799,
        "negative_signature_ids": [
          "d8f07ed206ac2f1881cea1e10a0dc70aa3fa34e7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.813146999999958,
        "positive_row_index": 798,
        "positive_signature_ids": [
          "a37eebcdb5526864e04e79e3bb356e9a64b60a7c"
        ],
        "raw_margin": 0.0213758647441864,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02100460616336,
        "admission_positive_above_negative": true,
        "context_hash": "7cb380a02e30e5a8",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
        "delay_risk_margin": 0.027174383401870728,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 808,
        "negative_signature_ids": [
          "7a60d588833203ecd1a1332abe95da279c4748c0"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.6718080000000555,
        "positive_row_index": 810,
        "positive_signature_ids": [
          "23993e3fd17d5b9a3ef537cbb68b3da5321162ba"
        ],
        "raw_margin": 0.019427627325057983,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.01753427180085207,
        "admission_positive_above_negative": true,
        "context_hash": "7cb380a02e30e5a8",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
        "delay_risk_margin": 0.022489875555038452,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 809,
        "negative_signature_ids": [
          "f7eabbc80a27730e0a08c10e7170bd393a7ed21f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.6718080000000555,
        "positive_row_index": 810,
        "positive_signature_ids": [
          "23993e3fd17d5b9a3ef537cbb68b3da5321162ba"
        ],
        "raw_margin": 0.016207993030548096,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.017456100773258154,
        "admission_positive_above_negative": true,
        "context_hash": "7cb380a02e30e5a8",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
        "delay_risk_margin": 0.022439152002334595,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 811,
        "negative_signature_ids": [
          "6ce7800fe0c2d0b96ea0946c22f54e4a88cbbf7a"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.6718080000000555,
        "positive_row_index": 810,
        "positive_signature_ids": [
          "23993e3fd17d5b9a3ef537cbb68b3da5321162ba"
        ],
        "raw_margin": 0.01605290174484253,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.022272358140315057,
        "admission_positive_above_negative": true,
        "context_hash": "03605a430acbd104",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923|03605a430acbd104",
        "delay_risk_margin": 0.027530789375305176,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 978,
        "negative_signature_ids": [
          "dc403cbcc974a19e21ad953e7f256e0afeb734c2"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4587119999999913,
        "positive_row_index": 980,
        "positive_signature_ids": [
          "a03ec0f7d5709b3b1abe09c677ec8b28c2f706bf"
        ],
        "raw_margin": 0.022980719804763794,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02184241905199505,
        "admission_positive_above_negative": true,
        "context_hash": "03605a430acbd104",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923|03605a430acbd104",
        "delay_risk_margin": 0.0268404483795166,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 979,
        "negative_signature_ids": [
          "17a9e278e5657caa4e5e1986fb1609cdf99422ea"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4587119999999913,
        "positive_row_index": 980,
        "positive_signature_ids": [
          "a03ec0f7d5709b3b1abe09c677ec8b28c2f706bf"
        ],
        "raw_margin": 0.022732138633728027,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0220367808540253,
        "admission_positive_above_negative": true,
        "context_hash": "03605a430acbd104",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923|03605a430acbd104",
        "delay_risk_margin": 0.027165234088897705,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 981,
        "negative_signature_ids": [
          "2138420f8210f99c9085e5ec13a485c090ecc853"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4587119999999913,
        "positive_row_index": 980,
        "positive_signature_ids": [
          "a03ec0f7d5709b3b1abe09c677ec8b28c2f706bf"
        ],
        "raw_margin": 0.02282470464706421,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05780233204033336,
        "admission_positive_above_negative": true,
        "context_hash": "5368cf35ed6f06cb",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|5368cf35ed6f06cb",
        "delay_risk_margin": 0.0651935338973999,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 846,
        "negative_signature_ids": [
          "5e020c3c1f660c2fd941b3b218dd77d8d8e29978"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8279430416666665,
        "positive_row_index": 176,
        "positive_signature_ids": [
          "5e020c3c1f660c2fd941b3b218dd77d8d8e29978",
          "3f5258922c91d13d4b730fd59a0798b99bb9f06b",
          "3e4d524377b425e531b5b5e2a5ce707ba28de637",
          "cab9ed220e0f732da3e2c10e73a1c9529e9f6960",
          "43b8c8fb6df8aa648ecb1d3cf69877e38db40543",
          "d3ff52f22564389063dd7c8e390250cba0dba1db",
          "251eaf96a611dec71ee7aa22950f4c918c08308d",
          "3afebe69541eee20bdec303fd9de8c66ed144c39",
          "5e1b5b47ec92ead4d73de9e36580d1a8fbeeef6d",
          "53798ef6df4947d31cf2da30d82c5b3416b06db6",
          "619510c228d019f9d26cf9c78cf7ea82806cf61a",
          "de76422cd68d9c486058171f2363b7edb3c17c13",
          "5afb110a7d5b5ead95fe3478c814628395e07fc7",
          "7fb64f61dd94e291ed111871134ce4b35e3e229e",
          "0ddcfbf0b1447af33036b8c53ca62e9e76c5470e",
          "985da4a641b962310c2d48d0bedd40d70ad74cc8",
          "553606a49cae770c3459f780cbb8a91f610f718f",
          "dfd420b038662df5423a6fce9e1314a0572a03a1",
          "bfb77acbdcf3fd9b35aee5bbb7865a5586c9c420",
          "9c025d190600a8466c4d08b9d3392e621d3b6a64",
          "0bda70d6b72a099ae8d7783ee8f7c280ad6fd742",
          "df0c1b1c346c7681cc08f0921f1c858c9982f024",
          "191a51d0878da8b26419143570d2d94088acd230",
          "182fc0763dc716ec05bf356b2687c0fb5581d81c",
          "0e96ade89502b77e046291ed283e6f0426e0006f",
          "11b8894f2a7c7d6a75971a2bd5781161ccdca23d",
          "0463c3d28592e6c795381c48a1dd63ff3fb0fccc",
          "72a6042c8c185e58658d45f03e563692c890437d",
          "cbe5e7ff6df284194ca949d1305b9eb45ec475ea",
          "3e363debe9a7c6f40dc9e068f56e0339dd93344d",
          "29eb1a8a2c154b25f613ddffd7306351b9fd67f2",
          "38e34d16f13e5e09ffe1a238c0515e42b41c8ac1"
        ],
        "raw_margin": 0.04182696342468262,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.025228949823319358,
        "admission_positive_above_negative": true,
        "context_hash": "5368cf35ed6f06cb",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|5368cf35ed6f06cb",
        "delay_risk_margin": 0.01932576298713684,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 846,
        "negative_signature_ids": [
          "5e020c3c1f660c2fd941b3b218dd77d8d8e29978"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1743930000000091,
        "positive_row_index": 847,
        "positive_signature_ids": [
          "43b8c8fb6df8aa648ecb1d3cf69877e38db40543"
        ],
        "raw_margin": 0.035076022148132324,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04543888238472635,
        "admission_positive_above_negative": true,
        "context_hash": "a0f80eb374f29f44",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|a0f80eb374f29f44",
        "delay_risk_margin": 0.05763685703277588,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 843,
        "negative_signature_ids": [
          "ff3a30ea27ed0cbefeec472594171c8baea37d94"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.1397708958333321,
        "positive_row_index": 177,
        "positive_signature_ids": [
          "a70dbaa64524bf905fc51b945398aa779b1c7eb0",
          "f7b3b676cb88bedcb78a0a90efdfc0d9e91f464d",
          "50bb4591b9373323c609a27955b4ebd9ff032da4",
          "db75dbfacf2af9513b9cd91f3d8c296c2ad631a3",
          "e7287e8b5513906d6b3f1ea1e8122926c89786f3",
          "00bdffd5aac56fd5d46991030e91d103c45a045f",
          "d6c74fec7ab66126e678c95d694a43fed0726676",
          "02693c9a9d7fe86d871ee7c40a0c4e7f46ae1eec",
          "e9ede587b999696e67c67a4b5bf8df927c70bbe8",
          "01fe19f762f190df1cf6b1fdfb80f602c24deee3",
          "5bd3d5c8813f37261cfdd41bea14e572705c71f4",
          "ff3a30ea27ed0cbefeec472594171c8baea37d94",
          "ca0a73bced633bfa071c7146a0d6b4fd1f9697e7",
          "803ec8587099bdf0afae957bc5532565ed13fe25",
          "cb62c433af70bb300f0b583a5dc1c6ccc9be47bd",
          "1e4a6eac37ecbc8f55173725141c1ab80f871cc1",
          "801b2d0a4ad32538619e56a7624f9fa4091f52dd",
          "a1387d2b1b495a0595a42bbf84abeb468bc0759e",
          "af2bd3d66cec104779b437ffe3398cb16afcea51",
          "a294d12891302d012a827c459dfa1144fd731ba6",
          "c91cd7f731b613280aa46bdd537a53440d10110a",
          "c432bce9be47b202bc494e38d5c853ef75179000",
          "ee7d778ed6e11f7c066f5b06999efc58513b1c93",
          "39f4f27734a9fd5c6e976e0c1527e8c19acafd96",
          "fa8127c066b55d48d535fdd7c7cf2ff9faa5f2d9",
          "3e3b72fc060aa1908262ae32c2fd77260a4b5547",
          "ab2a6d238e2caf83a5b4cc23537033fdd0ed15d7",
          "3307ff1a749cf58fcbc3111f3c85cc482eccc256",
          "f2195dcd9a0f9f2ed7b9fc9f43307a41df158ccd",
          "971573ba3ece027437654bee068789f574c42740",
          "23bc7a2adfebbd75f0dd677399eef37fde8a9b5b",
          "a0d9f3e62d6645e9ca191f34110a2ae79f16cc62"
        ],
        "raw_margin": 0.0173608660697937,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.012743168149419531,
        "admission_positive_above_negative": true,
        "context_hash": "a0f80eb374f29f44",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|a0f80eb374f29f44",
        "delay_risk_margin": 0.008664131164550781,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 843,
        "negative_signature_ids": [
          "ff3a30ea27ed0cbefeec472594171c8baea37d94"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 19.688070999999923,
        "positive_row_index": 842,
        "positive_signature_ids": [
          "a70dbaa64524bf905fc51b945398aa779b1c7eb0"
        ],
        "raw_margin": 0.01790463924407959,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03117468955829225,
        "admission_positive_above_negative": true,
        "context_hash": "be33b2560df0147a",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_04_seed71306|be33b2560df0147a",
        "delay_risk_margin": 0.02847042679786682,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 848,
        "negative_signature_ids": [
          "a949e955098080b1bb592e9036f53b4686a950f5"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 11.920403999999962,
        "positive_row_index": 849,
        "positive_signature_ids": [
          "8e0d1a86c301c3394cb3a5df8b83d7b89385a953"
        ],
        "raw_margin": 0.03942537307739258,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.016803238695199396,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.010390788316726685,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 376,
        "negative_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "79a81ddeb102a733f3300e0ed0d04f17002ac4c9",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "7b46563f19a4ba2bc2739dba622b82f8b83a21db",
          "d683a437bea4020da6c195020e287cdb04e42702",
          "c410281c463756c0840f5e7d78c10c2a9f8f66f1",
          "ad39a056d43137e879031e5713f0dd8c4f0db0b3",
          "6a91a0e6224b8164f0556fd0d9d70e5bed11cce7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.028215408325195312,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04008143378603593,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.0379967987537384,
        "family": "sector-wave",
        "negative_roi": -1.9897776000000003,
        "negative_row_index": 377,
        "negative_signature_ids": [
          "4e652a888b0ae9b2bb9bf41d5503a1a4ec9bad8e",
          "e4103869ca379807e8ae5dcb9caf0a8690a31ae9",
          "a7a1cda9c064cdbc2c5bbbd3c6b1923e1701842c",
          "bfa93dc9f590902712e1de6b243615c5a3adae04",
          "9e3b6b64ee5dd65f00a7cea9c026ca69984721ea",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "a39671fe901a091d64e9745fb9b96a324d444f4c",
          "98d021049f6f330222aecd4dade4f9e31230f262"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.05107453465461731,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03545964211855954,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.031644731760025024,
        "family": "sector-wave",
        "negative_roi": -2.72311875,
        "negative_row_index": 378,
        "negative_signature_ids": [
          "a247df4c67f63e4d9156a52f7f5d3d9107efab5e",
          "473a19b7f445c74141fcea0fa54b73333d517b56",
          "14b4f04a9321d0cffae8af1a4f51ecc57d523da6",
          "dff85c2667854d10424ecbf8d6e94d3c4fcc0e03",
          "6b41a7792f0e333d46f37df42b0d16175096b3ae",
          "ac14ee4b06ed716038738034f837c86f87ab94a1",
          "19c95206050339d4afbca332abac669e726912a4",
          "c9469442c21b2c959cab23a81263f42e564082e7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.04745727777481079,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.010799319751015585,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.005499035120010376,
        "family": "sector-wave",
        "negative_roi": -1.9837796500000002,
        "negative_row_index": 379,
        "negative_signature_ids": [
          "3ac19578c7ea584e34a6d9c1c4284dc79288b9ec",
          "7087028b6674339e590b9debe36662eea447ba33",
          "0e3f2e7025d686b4f731e90ae308aedef6093f5b",
          "b05d66c3eeb29914a69d67d9b9b91ec03ae7e275",
          "c7669347754a2b509c1b5cb5c9725b86887f8bea",
          "4b16a1deb38190830844d95238b3fb60f357007c",
          "79b621108ae956cd6cf161c2776b8259fbfef2b9",
          "c01a851755c5ad392eb3e55ffa81ab7173cf19dd"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.019712746143341064,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02334649645006437,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.021134912967681885,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 381,
        "negative_signature_ids": [
          "4e652a888b0ae9b2bb9bf41d5503a1a4ec9bad8e"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.02962017059326172,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.010902026246548735,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.007883429527282715,
        "family": "sector-wave",
        "negative_roi": -1.9382478,
        "negative_row_index": 445,
        "negative_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.01635432243347168,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.033843112578834156,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.031376272439956665,
        "family": "sector-wave",
        "negative_roi": -1.9875231,
        "negative_row_index": 449,
        "negative_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.0432814359664917,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.020894409324772656,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.01856270432472229,
        "family": "sector-wave",
        "negative_roi": -1.9888643,
        "negative_row_index": 450,
        "negative_signature_ids": [
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.02684420347213745,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.01776497491146814,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.013109385967254639,
        "family": "sector-wave",
        "negative_roi": -2.7302804,
        "negative_row_index": 451,
        "negative_signature_ids": [
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.4709638750000096,
        "positive_row_index": 380,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "raw_margin": 0.026683449745178223,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.026978530105763676,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.022502273321151733,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 376,
        "negative_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "79a81ddeb102a733f3300e0ed0d04f17002ac4c9",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "7b46563f19a4ba2bc2739dba622b82f8b83a21db",
          "d683a437bea4020da6c195020e287cdb04e42702",
          "c410281c463756c0840f5e7d78c10c2a9f8f66f1",
          "ad39a056d43137e879031e5713f0dd8c4f0db0b3",
          "6a91a0e6224b8164f0556fd0d9d70e5bed11cce7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.035359084606170654,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05025672519660021,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.05010828375816345,
        "family": "sector-wave",
        "negative_roi": -1.9897776000000003,
        "negative_row_index": 377,
        "negative_signature_ids": [
          "4e652a888b0ae9b2bb9bf41d5503a1a4ec9bad8e",
          "e4103869ca379807e8ae5dcb9caf0a8690a31ae9",
          "a7a1cda9c064cdbc2c5bbbd3c6b1923e1701842c",
          "bfa93dc9f590902712e1de6b243615c5a3adae04",
          "9e3b6b64ee5dd65f00a7cea9c026ca69984721ea",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "a39671fe901a091d64e9745fb9b96a324d444f4c",
          "98d021049f6f330222aecd4dade4f9e31230f262"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.05821821093559265,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04563493352912382,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.04375621676445007,
        "family": "sector-wave",
        "negative_roi": -2.72311875,
        "negative_row_index": 378,
        "negative_signature_ids": [
          "a247df4c67f63e4d9156a52f7f5d3d9107efab5e",
          "473a19b7f445c74141fcea0fa54b73333d517b56",
          "14b4f04a9321d0cffae8af1a4f51ecc57d523da6",
          "dff85c2667854d10424ecbf8d6e94d3c4fcc0e03",
          "6b41a7792f0e333d46f37df42b0d16175096b3ae",
          "ac14ee4b06ed716038738034f837c86f87ab94a1",
          "19c95206050339d4afbca332abac669e726912a4",
          "c9469442c21b2c959cab23a81263f42e564082e7"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.05460095405578613,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.020974611161579865,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.017610520124435425,
        "family": "sector-wave",
        "negative_roi": -1.9837796500000002,
        "negative_row_index": 379,
        "negative_signature_ids": [
          "3ac19578c7ea584e34a6d9c1c4284dc79288b9ec",
          "7087028b6674339e590b9debe36662eea447ba33",
          "0e3f2e7025d686b4f731e90ae308aedef6093f5b",
          "b05d66c3eeb29914a69d67d9b9b91ec03ae7e275",
          "c7669347754a2b509c1b5cb5c9725b86887f8bea",
          "4b16a1deb38190830844d95238b3fb60f357007c",
          "79b621108ae956cd6cf161c2776b8259fbfef2b9",
          "c01a851755c5ad392eb3e55ffa81ab7173cf19dd"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.026856422424316406,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03352178786062865,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.033246397972106934,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 381,
        "negative_signature_ids": [
          "4e652a888b0ae9b2bb9bf41d5503a1a4ec9bad8e"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.03676384687423706,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.021077317657113015,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.019994914531707764,
        "family": "sector-wave",
        "negative_roi": -1.9382478,
        "negative_row_index": 445,
        "negative_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.02349799871444702,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.044018403989398436,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.043487757444381714,
        "family": "sector-wave",
        "negative_roi": -1.9875231,
        "negative_row_index": 449,
        "negative_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.05042511224746704,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.031069700735336936,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.03067418932914734,
        "family": "sector-wave",
        "negative_roi": -1.9888643,
        "negative_row_index": 450,
        "negative_signature_ids": [
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.03398787975311279,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02794026632203242,
        "admission_positive_above_negative": true,
        "context_hash": "ac056820151e9ad7",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002|ac056820151e9ad7",
        "delay_risk_margin": 0.025220870971679688,
        "family": "sector-wave",
        "negative_roi": -2.7302804,
        "negative_row_index": 451,
        "negative_signature_ids": [
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 4.941927750000019,
        "positive_row_index": 1125,
        "positive_signature_ids": [
          "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d",
          "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17",
          "6a756bf8a77a533b5f33aa9e86e87b2495171eb6",
          "4b16a1deb38190830844d95238b3fb60f357007c"
        ],
        "raw_margin": 0.033827126026153564,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02593351055890422,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.039994120597839355,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
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
        "raw_margin": 0.0011963844299316406,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03033405454157173,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.041077226400375366,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
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
        "raw_margin": 0.010701298713684082,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03162884106941305,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.04433262348175049,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
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
        "raw_margin": 0.008906424045562744,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02593351055890422,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.039994120597839355,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
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
        "raw_margin": 0.0011963844299316406,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03033405454157173,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.041077226400375366,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
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
        "raw_margin": 0.010701298713684082,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 3.547838862091868e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0008023977279663086,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 385,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0011809468269348145,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.004436022371288428,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0018855035305023193,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 385,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.008323967456817627,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.005730808899129747,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.005140900611877441,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 385,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.006529092788696289,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 3.547838862091868e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0008023977279663086,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 385,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0011809468269348145,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.004436022371288428,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0018855035305023193,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8244333499999998,
        "positive_row_index": 385,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.008323967456817627,
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
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 436,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.00440054398266751,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0010831058025360107,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 436,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.009504914283752441,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.005695330510508828,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.004338502883911133,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 436,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0077100396156311035,
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
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 436,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.00440054398266751,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0010831058025360107,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 436,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.009504914283752441,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 3.547838862091868e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0008023977279663086,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 437,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0011809468269348145,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.004436022371288428,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0018855035305023193,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 437,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.008323967456817627,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.005730808899129747,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.005140900611877441,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 437,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.006529092788696289,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 3.547838862091868e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0008023977279663086,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 437,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0011809468269348145,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.004436022371288428,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0018855035305023193,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 437,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.008323967456817627,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.00440054398266751,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0010831058025360107,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 438,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.009504914283752441,
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
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 438,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0012947865278413184,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.003255397081375122,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 438,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.0017948746681213379,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.00440054398266751,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0010831058025360107,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 438,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.009504914283752441,
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
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 438,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 3.547838862091868e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0008023977279663086,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 456,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0011809468269348145,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.004436022371288428,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0018855035305023193,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 456,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.008323967456817627,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.005730808899129747,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.005140900611877441,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 456,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.006529092788696289,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 3.547838862091868e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0008023977279663086,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 456,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0011809468269348145,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.004436022371288428,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0018855035305023193,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8384176999999997,
        "positive_row_index": 456,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.008323967456817627,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.003522128171372013,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.001455456018447876,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 460,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": -0.006678581237792969,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0008784158112954965,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.00037235021591186523,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 460,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": 0.0028263330459594727,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.002173202339136815,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.002883046865463257,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 460,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": 0.0010314583778381348,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.003522128171372013,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.001455456018447876,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 460,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": -0.006678581237792969,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0008784158112954965,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.00037235021591186523,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 460,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": 0.0028263330459594727,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02593351055890422,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.039994120597839355,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 483,
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
        "raw_margin": 0.0011963844299316406,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03033405454157173,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.041077226400375366,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 483,
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
        "raw_margin": 0.010701298713684082,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03162884106941305,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.04433262348175049,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 483,
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
        "raw_margin": 0.008906424045562744,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02593351055890422,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.039994120597839355,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 483,
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
        "raw_margin": 0.0011963844299316406,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03033405454157173,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.041077226400375366,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 483,
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
        "raw_margin": 0.010701298713684082,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02593351055890422,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.039994120597839355,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 553,
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
        "raw_margin": 0.0011963844299316406,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03033405454157173,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.041077226400375366,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 553,
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
        "raw_margin": 0.010701298713684082,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03162884106941305,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.04433262348175049,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 553,
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
        "raw_margin": 0.008906424045562744,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.02593351055890422,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.039994120597839355,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 553,
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
        "raw_margin": 0.0011963844299316406,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03033405454157173,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.041077226400375366,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.8094513673469376,
        "positive_row_index": 553,
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
        "raw_margin": 0.010701298713684082,
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
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 752,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.00440054398266751,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0010831058025360107,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 752,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.009504914283752441,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.005695330510508828,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.004338502883911133,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 752,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0077100396156311035,
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
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 752,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.00440054398266751,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0010831058025360107,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 31.935651000000007,
        "positive_row_index": 752,
        "positive_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "raw_margin": 0.009504914283752441,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 3.547838862091868e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0008023977279663086,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 753,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0011809468269348145,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.004436022371288428,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0018855035305023193,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 753,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.008323967456817627,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.005730808899129747,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.005140900611877441,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 753,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.006529092788696289,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 3.547838862091868e-05,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0008023977279663086,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 753,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": -0.0011809468269348145,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.004436022371288428,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.0018855035305023193,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 26.543082000000027,
        "positive_row_index": 753,
        "positive_signature_ids": [
          "42986411c95f970de8b1b1ace7b24b017b0bd949"
        ],
        "raw_margin": 0.008323967456817627,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.00440054398266751,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0010831058025360107,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 754,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.009504914283752441,
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
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 754,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0012947865278413184,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.003255397081375122,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": true,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 754,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.0017948746681213379,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.00440054398266751,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.0010831058025360107,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 754,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": -0.009504914283752441,
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
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 15.12042299999996,
        "positive_row_index": 754,
        "positive_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.003522128171372013,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.001455456018447876,
        "family": "sector-wave",
        "negative_roi": -1.7641903999999922,
        "negative_row_index": 384,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 755,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": -0.006678581237792969,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0008784158112954965,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.00037235021591186523,
        "family": "sector-wave",
        "negative_roi": -2.7614056499999826,
        "negative_row_index": 386,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 755,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": 0.0028263330459594727,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.002173202339136815,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": 0.002883046865463257,
        "family": "sector-wave",
        "negative_roi": -0.30568100000001097,
        "negative_row_index": 448,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb",
          "42986411c95f970de8b1b1ace7b24b017b0bd949",
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 755,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": 0.0010314583778381348,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.003522128171372013,
        "admission_positive_above_negative": false,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.001455456018447876,
        "family": "sector-wave",
        "negative_roi": -1.9046695499999917,
        "negative_row_index": 455,
        "negative_signature_ids": [
          "dd971e12856314e2fe9648723acb6729e7aa96fb"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 755,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": -0.006678581237792969,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0008784158112954965,
        "admission_positive_above_negative": true,
        "context_hash": "ac15bc4e7e3d6fff",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104|ac15bc4e7e3d6fff",
        "delay_risk_margin": -0.00037235021591186523,
        "family": "sector-wave",
        "negative_roi": -2.7588620499999825,
        "negative_row_index": 457,
        "negative_signature_ids": [
          "439b7b8900988aa08d459904417c872be5dcb16f"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 21.827696999999944,
        "positive_row_index": 755,
        "positive_signature_ids": [
          "215b9f05c6d6ae390aa47ed01835f6bef30a9868"
        ],
        "raw_margin": 0.0028263330459594727,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04452054009594414,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.05154317617416382,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 412,
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
        "raw_margin": 0.027941763401031494,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05732279439029331,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.06057542562484741,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 413,
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
        "raw_margin": 0.04725193977355957,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06868561273914103,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.0731968879699707,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 430,
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
        "raw_margin": 0.05838209390640259,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04452054009594414,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.05154317617416382,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 412,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 326,
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
        "raw_margin": 0.027941763401031494,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05732279439029331,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.06057542562484741,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 413,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 326,
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
        "raw_margin": 0.04725193977355957,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06868561273914103,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.0731968879699707,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 430,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 326,
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
        "raw_margin": 0.05838209390640259,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.024165072643196894,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": -0.021653711795806885,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 412,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 411,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "raw_margin": -0.030440330505371094,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.011362818348847725,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": -0.012621462345123291,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 413,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 411,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "raw_margin": -0.011130154132843018,
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
        "negative_row_index": 430,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.0,
        "positive_row_index": 411,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
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
        "negative_roi": -71.0984261500001,
        "negative_row_index": 412,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 7.900282999999945,
        "positive_row_index": 431,
        "positive_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.012802254294349169,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.009032249450683594,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 413,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 7.900282999999945,
        "positive_row_index": 431,
        "positive_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "raw_margin": 0.019310176372528076,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.024165072643196894,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.021653711795806885,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 430,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 7.900282999999945,
        "positive_row_index": 431,
        "positive_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "raw_margin": 0.030440330505371094,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.012802254294349169,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": -0.009032249450683594,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 412,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 2.1534749999999576,
        "positive_row_index": 432,
        "positive_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": -0.019310176372528076,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 413,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 2.1534749999999576,
        "positive_row_index": 432,
        "positive_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.011362818348847725,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.012621462345123291,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 430,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 2.1534749999999576,
        "positive_row_index": 432,
        "positive_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": 0.011130154132843018,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04452054009594414,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.05154317617416382,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 412,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 509,
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
        "raw_margin": 0.027941763401031494,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05732279439029331,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.06057542562484741,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 413,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 509,
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
        "raw_margin": 0.04725193977355957,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06868561273914103,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.0731968879699707,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 430,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.004419020833332,
        "positive_row_index": 509,
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
        "raw_margin": 0.05838209390640259,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.01855722224252923,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.01722395420074463,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 412,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 8.362749749999978,
        "positive_row_index": 1104,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d",
          "e92756f39247cf7a0abeb6c6c67a11df2eb656da",
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba",
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": 0.019610822200775146,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0313594765368784,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.026256203651428223,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 413,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 8.362749749999978,
        "positive_row_index": 1104,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d",
          "e92756f39247cf7a0abeb6c6c67a11df2eb656da",
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba",
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": 0.03892099857330322,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.042722294885726125,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.038877665996551514,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 430,
        "negative_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 8.362749749999978,
        "positive_row_index": 1104,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d",
          "e92756f39247cf7a0abeb6c6c67a11df2eb656da",
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba",
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "raw_margin": 0.05005115270614624,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -3.6452848,
        "negative_row_index": 390,
        "negative_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 13.436328000000003,
        "positive_row_index": 463,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.02616119793919769,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.030217647552490234,
        "family": "sector-wave",
        "negative_roi": -7.4290636999999995,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "20fdd4b4d638d08cd21bc466cba236faf2b07360"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.436328000000003,
        "positive_row_index": 463,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "raw_margin": 0.029749423265457153,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0030022631438589853,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.0015031099319458008,
        "family": "sector-wave",
        "negative_roi": -2.5419104,
        "negative_row_index": 392,
        "negative_signature_ids": [
          "10f81606d859bf88c1a08bfaab80e229131db94c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.436328000000003,
        "positive_row_index": 463,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "raw_margin": 0.006084620952606201,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.014051204470998752,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.01636791229248047,
        "family": "sector-wave",
        "negative_roi": -3.6452848,
        "negative_row_index": 390,
        "negative_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.359082000000001,
        "positive_row_index": 1123,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965",
          "005456aa3459dbf2c766c921cb57a48637bd92c2",
          "20fdd4b4d638d08cd21bc466cba236faf2b07360",
          "10f81606d859bf88c1a08bfaab80e229131db94c"
        ],
        "raw_margin": 0.01312875747680664,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04021240241019644,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.0465855598449707,
        "family": "sector-wave",
        "negative_roi": -7.4290636999999995,
        "negative_row_index": 391,
        "negative_signature_ids": [
          "20fdd4b4d638d08cd21bc466cba236faf2b07360"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.359082000000001,
        "positive_row_index": 1123,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965",
          "005456aa3459dbf2c766c921cb57a48637bd92c2",
          "20fdd4b4d638d08cd21bc466cba236faf2b07360",
          "10f81606d859bf88c1a08bfaab80e229131db94c"
        ],
        "raw_margin": 0.042878180742263794,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.017053467614857737,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.01787102222442627,
        "family": "sector-wave",
        "negative_roi": -2.5419104,
        "negative_row_index": 392,
        "negative_signature_ids": [
          "10f81606d859bf88c1a08bfaab80e229131db94c"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.359082000000001,
        "positive_row_index": 1123,
        "positive_signature_ids": [
          "db31a9f9d33fb7d0311f522bee48c5f8de5af965",
          "005456aa3459dbf2c766c921cb57a48637bd92c2",
          "20fdd4b4d638d08cd21bc466cba236faf2b07360",
          "10f81606d859bf88c1a08bfaab80e229131db94c"
        ],
        "raw_margin": 0.019213378429412842,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.052611591525176804,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.05820751190185547,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 387,
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
        "raw_margin": 0.039361655712127686,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0812385474988877,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08667537569999695,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 388,
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
        "raw_margin": 0.07404708862304688,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0812385474988877,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08667537569999695,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 443,
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
        "raw_margin": 0.07404708862304688,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0786061739824041,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08389583230018616,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 444,
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
        "raw_margin": 0.07080256938934326,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.056946392015428005,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.06168872117996216,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 447,
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
        "raw_margin": 0.045446038246154785,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.052611591525176804,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.05820751190185547,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 452,
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
        "raw_margin": 0.039361655712127686,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0812385474988877,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08667537569999695,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 453,
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
        "raw_margin": 0.07404708862304688,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0812385474988877,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08667537569999695,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 749,
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
        "raw_margin": 0.07404708862304688,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0786061739824041,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08389583230018616,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 750,
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
        "raw_margin": 0.07080256938934326,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0259945824572273,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.02568832039833069,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.031440913677215576,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0026323735164835993,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.002779543399810791,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 388,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0032445192337036133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0026323735164835993,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.002779543399810791,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 443,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0032445192337036133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 444,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0216597819669761,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.022207111120224,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 447,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.025356531143188477,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0259945824572273,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.02568832039833069,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 452,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.031440913677215576,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0026323735164835993,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.002779543399810791,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 453,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0032445192337036133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0026323735164835993,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.002779543399810791,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 749,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0032445192337036133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 750,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.2127802500000058,
        "positive_row_index": 389,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0286269559737109,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02846786379814148,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 388,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.03468543291091919,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0286269559737109,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02846786379814148,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 443,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.03468543291091919,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0259945824572273,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02568832039833069,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 444,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.031440913677215576,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0043348004902512005,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0034812092781066895,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 447,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.0060843825340271,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 452,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0286269559737109,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02846786379814148,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 453,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.03468543291091919,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0286269559737109,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02846786379814148,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 749,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.03468543291091919,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0259945824572273,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02568832039833069,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 750,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 442,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.031440913677215576,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0259945824572273,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.02568832039833069,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.031440913677215576,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0026323735164835993,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.002779543399810791,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 388,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0032445192337036133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0026323735164835993,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.002779543399810791,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 443,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0032445192337036133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 444,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0216597819669761,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.022207111120224,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 447,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.025356531143188477,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": -0.0259945824572273,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": -0.02568832039833069,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 452,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": -0.031440913677215576,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0026323735164835993,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.002779543399810791,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 453,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0032445192337036133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0026323735164835993,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.002779543399810791,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 749,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0032445192337036133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 750,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 1.202311850000006,
        "positive_row_index": 454,
        "positive_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.00806691295817119,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.007184863090515137,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.00986868143081665,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03669386893188209,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.035652726888656616,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 388,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04455411434173584,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03669386893188209,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.035652726888656616,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 443,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04455411434173584,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03406149541539849,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.032873183488845825,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 444,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04130959510803223,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.012401713448422391,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.010666072368621826,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 447,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.01595306396484375,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.00806691295817119,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.007184863090515137,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 452,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.00986868143081665,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03669386893188209,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.035652726888656616,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 453,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04455411434173584,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03669386893188209,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.035652726888656616,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 749,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04455411434173584,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03406149541539849,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.032873183488845825,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 750,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 461,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04130959510803223,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.052611591525176804,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.05820751190185547,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.039361655712127686,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0812385474988877,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08667537569999695,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 388,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.07404708862304688,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0812385474988877,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08667537569999695,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 443,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.07404708862304688,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0786061739824041,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08389583230018616,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 444,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.07080256938934326,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.056946392015428005,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.06168872117996216,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 447,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.045446038246154785,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.052611591525176804,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.05820751190185547,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 452,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.039361655712127686,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0812385474988877,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08667537569999695,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 453,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.07404708862304688,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0812385474988877,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08667537569999695,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 749,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.07404708862304688,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0786061739824041,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.08389583230018616,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 750,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.7734083750000001,
        "positive_row_index": 527,
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
        "raw_margin": 0.07080256938934326,
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
        "negative_row_index": 387,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0286269559737109,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02846786379814148,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 388,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.03468543291091919,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0286269559737109,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02846786379814148,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 443,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.03468543291091919,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0259945824572273,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02568832039833069,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 444,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.031440913677215576,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0043348004902512005,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0034812092781066895,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 447,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.0060843825340271,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0,
        "admission_positive_above_negative": false,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.0,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 452,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.0,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0286269559737109,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02846786379814148,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 453,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.03468543291091919,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0286269559737109,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02846786379814148,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 749,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.03468543291091919,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0259945824572273,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.02568832039833069,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 750,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 14.96982300000002,
        "positive_row_index": 748,
        "positive_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "raw_margin": 0.031440913677215576,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.00806691295817119,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.007184863090515137,
        "family": "sector-wave",
        "negative_roi": -25.979907549999943,
        "negative_row_index": 387,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.00986868143081665,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03669386893188209,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.035652726888656616,
        "family": "sector-wave",
        "negative_roi": -26.660240199999944,
        "negative_row_index": 388,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04455411434173584,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03669386893188209,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.035652726888656616,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 443,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04455411434173584,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03406149541539849,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.032873183488845825,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 444,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04130959510803223,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.012401713448422391,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.010666072368621826,
        "family": "sector-wave",
        "negative_roi": -25.923193099999946,
        "negative_row_index": 447,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc",
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f",
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.01595306396484375,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.00806691295817119,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.007184863090515137,
        "family": "sector-wave",
        "negative_roi": -25.997795649999947,
        "negative_row_index": 452,
        "negative_signature_ids": [
          "5740a41c212c3216fe3755c7f1a904fdcba404fc"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.00986868143081665,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03669386893188209,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.035652726888656616,
        "family": "sector-wave",
        "negative_roi": -26.658945749999944,
        "negative_row_index": 453,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04455411434173584,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03669386893188209,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.035652726888656616,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 749,
        "negative_signature_ids": [
          "f6bf8ec83cac493b7c970d1d0fe79f248286666f"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04455411434173584,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03406149541539849,
        "admission_positive_above_negative": true,
        "context_hash": "79fde658840fe2b8",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718|79fde658840fe2b8",
        "delay_risk_margin": 0.032873183488845825,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 750,
        "negative_signature_ids": [
          "f64dfd0b2fabfb21e60e84b4354825f8f04bec64"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 13.56820700000003,
        "positive_row_index": 751,
        "positive_signature_ids": [
          "f650bc8e326572acfebbd6ba3a548058f1e6b2fa"
        ],
        "raw_margin": 0.04130959510803223,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0008916197818731875,
        "admission_positive_above_negative": true,
        "context_hash": "5a812898b6327d87",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks030_01_seed71001|5a812898b6327d87",
        "delay_risk_margin": 0.0014365315437316895,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 918,
        "negative_signature_ids": [
          "5084bb924b869db277689578e5da1f6055704b9a"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.6034570000000485,
        "positive_row_index": 919,
        "positive_signature_ids": [
          "5b5f7de7f10530def29043f24a64e343e0e93a31"
        ],
        "raw_margin": 0.0005076825618743896,
        "raw_positive_above_negative": true
      }
    ],
    "production_ready": false,
    "runs_bpc_or_pricing": false,
    "summary": {
      "admission_pair_pass_count": 297,
      "admission_pair_pass_rate": 0.7734375,
      "ambiguous_row_count": 0,
      "context_count": 37,
      "contexts_with_positive_and_negative": 37,
      "delay_risk_pair_pass_count": 285,
      "delay_risk_pair_pass_rate": 0.7421875,
      "family_counts": {
        "greedy-anchor": 33,
        "random-wave": 75,
        "sector-wave": 99
      },
      "focused_row_count": 207,
      "label_counts": {
        "delay_or_hard_negative": 90,
        "positive_high_priority": 117
      },
      "negative_row_count": 90,
      "pair_count": 384,
      "positive_row_count": 117,
      "primary": "candidate_head_context_ranking_failure",
      "raw_pair_pass_count": 278,
      "raw_pair_pass_rate": 0.7239583333333334,
      "strict_pair_pass_count": 266,
      "strict_pair_pass_rate": 0.6927083333333334
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
    "train_context_count": 411,
    "train_family_counts": {
      "greedy-anchor": 234,
      "random-wave": 317,
      "sector-wave": 344
    },
    "train_instances": [
      "BPC_future/logical_graph/tasks_005/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks005_02_seed46105_logical_graph.json",
      "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_01_seed146007_logical_graph.json",
      "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_02_seed146110_logical_graph.json",
      "BPC_future/logical_graph/tasks_005/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks005_03_seed1046207_logical_graph.json",
      "BPC_future/logical_graph/tasks_005/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_03_seed1146204_logical_graph.json",
      "BPC_future/logical_graph/tasks_005/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks005_01_seed2146011_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_02_seed51106_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks010_03_seed51209_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_01_seed51000_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_03_seed51213_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks010_01_seed51001_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks010_02_seed51106_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks010_03_seed51209_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_02_seed51111_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_03_seed51213_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_08_seed61716_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_09_seed61818_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_10_seed61921_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_02_seed61103_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_03_seed61206_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_04_seed61311_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_01_seed61001_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_02_seed61103_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_04_seed61309_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_05_seed61411_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_02_seed61102_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_03_seed61204_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_04_seed61306_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_09_seed61817_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_10_seed61919_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_01_seed61002_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_02_seed61104_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_03_seed61206_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_04_seed61308_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_08_seed61718_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_10_seed61923_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks030_01_seed71000_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks030_01_seed71010_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_01_seed71000_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_02_seed71102_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_04_seed71306_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_05_seed71408_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_01_seed71000_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_03_seed71204_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks030_01_seed71000_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks030_02_seed71102_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks030_01_seed71001_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks030_02_seed71104_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks050_04_seed91307_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks050_05_seed91409_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks050_06_seed91511_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks050_01_seed91004_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks050_02_seed91109_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_03_seed91204_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks050_04_seed91307_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_04_seed91307_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks050_03_seed91204_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks050_04_seed91307_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks050_05_seed91409_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks050_04_seed91307_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks050_05_seed91410_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_01_seed141000_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_03_seed141207_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_04_seed141309_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_05_seed141411_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_08_seed141718_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_09_seed141820_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_03_seed141207_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_04_seed141309_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_05_seed141411_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_07_seed141615_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_08_seed141718_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_09_seed141820_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks100_01_seed141000_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_01_seed141000_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_04_seed141309_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_05_seed141411_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_06_seed141513_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_07_seed141615_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_08_seed141718_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_09_seed141820_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_10_seed141922_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks100_01_seed141000_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks100_02_seed141102_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks100_04_seed141306_logical_graph.json"
    ],
    "validation_context_count": 135,
    "validation_family_counts": {
      "greedy-anchor": 124,
      "random-wave": 132,
      "sector-wave": 70
    },
    "validation_instances": [
      "BPC_future/logical_graph/tasks_005/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks005_03_seed46207_logical_graph.json",
      "BPC_future/logical_graph/tasks_005/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks005_03_seed146214_logical_graph.json",
      "BPC_future/logical_graph/tasks_005/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks005_01_seed1146000_logical_graph.json",
      "BPC_future/logical_graph/tasks_005/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks005_01_seed2046000_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks010_02_seed51111_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks010_01_seed51000_logical_graph.json",
      "BPC_future/logical_graph/tasks_010/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks010_01_seed51001_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_08_seed61744_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_09_seed61846_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_10_seed61948_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_05_seed61408_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_07_seed61615_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_06_seed61510_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_06_seed61513_logical_graph.json",
      "BPC_future/logical_graph/tasks_020/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_09_seed61821_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks030_02_seed71102_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks030_02_seed71115_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks030_03_seed71204_logical_graph.json",
      "BPC_future/logical_graph/tasks_030/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_04_seed71306_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_02_seed91102_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/random-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks050_03_seed91204_logical_graph.json",
      "BPC_future/logical_graph/tasks_050/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks050_01_seed91000_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_02_seed141104_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_06_seed141513_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks100_07_seed141615_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_02_seed141104_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_06_seed141513_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/random-wave/apollo15_20km/apollo15_20km_random-wave_randomtw_tasks100_10_seed141922_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_02_seed141104_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks100_03_seed141207_logical_graph.json",
      "BPC_future/logical_graph/tasks_100/sector-wave/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks100_03_seed141204_logical_graph.json"
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
      "accepted_batch_count": 22,
      "accepted_batch_precision": 1.0,
      "accepted_batch_rate": 0.06748466257668712,
      "accepted_batch_roi": 12.614279048009353,
      "accepted_batch_roi_ci_low": 5.023888300128747,
      "accepted_batch_roi_over_baseline": 12.614279048009353,
      "accepted_batch_roi_over_baseline_ci_low": 5.023888300128747,
      "accepted_batch_roi_over_best_rc_baseline": 12.614279048009353,
      "accepted_batch_roi_over_best_rc_baseline_ci_low": 5.023888300128747,
      "accepted_batch_roi_over_old_gat_baseline": 12.614279048009353,
      "accepted_batch_roi_over_old_gat_baseline_ci_low": 5.023888300128747,
      "accepted_batch_roi_over_random_baseline": 12.614279048009353,
      "accepted_batch_roi_over_random_baseline_ci_low": 5.023888300128747,
      "baseline_roi_ci_high": 0.0,
      "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
      "baseline_selection_roi": 0.0,
      "batch_threshold": 0.5478627681732178,
      "batch_thresholds_by_family": {},
      "best_rc_baseline_accepted_batch_roi": 0.0,
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_blocked_count": 0,
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.55,
      "candidate_delay_score_penalty": 1.5,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_rescue_window_eligible_count": 0,
      "candidate_rescue_window_promoted_count": 0,
      "candidate_risk_adjusted_suppressed_count": 2735,
      "candidate_score_threshold_blocked_count": 2735,
      "candidate_threshold": 0.2552189121665872,
      "checkpoint_gate_pass": false,
      "checkpoint_gate_reject_reasons": [
        "safe_precision_ci_low_below_threshold_or_not_measurable",
        "knn_ood_audit_missing"
      ],
      "context_delay_fallback_contexts": [],
      "coverage_non_ood": 1.0,
      "delay_label_count": 286,
      "delay_rate": 0.9325153374233128,
      "evaluated_candidate_count": 3260,
      "expected_trajectory_utility": 12.637006320736624,
      "false_high_priority_on_delay": 0.0,
      "false_high_priority_on_delay_count": 0,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 0.0,
      "family_delay_fallback_families": [],
      "family_holdout_min_accepted_high_roi_count": 5,
      "family_holdout_min_accepted_roi": 6.602623319625854,
      "family_holdout_min_high_roi_capture_rate": 0.21428571428571427,
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
          "accepted_batch_count": 5,
          "accepted_batch_roi": 6.602623319625854,
          "accepted_high_roi_count": 5,
          "high_roi_capture_rate": 0.25,
          "max_accepted_batch_roi_label": 106.158935546875,
          "oracle_high_roi_count": 20,
          "safe_precision": 1.0,
          "total_batches": 124
        },
        "random-wave": {
          "accepted_batch_count": 8,
          "accepted_batch_roi": 21.57581076025963,
          "accepted_high_roi_count": 8,
          "high_roi_capture_rate": 0.23529411764705882,
          "max_accepted_batch_roi_label": 79.51943969726562,
          "oracle_high_roi_count": 34,
          "safe_precision": 1.0,
          "total_batches": 132
        },
        "sector-wave": {
          "accepted_batch_count": 9,
          "accepted_batch_roi": 7.988281819555494,
          "accepted_high_roi_count": 6,
          "high_roi_capture_rate": 0.21428571428571427,
          "max_accepted_batch_roi_label": 41.31852722167969,
          "oracle_high_roi_count": 28,
          "safe_precision": 1.0,
          "total_batches": 70
        }
      },
      "family_specific_delay_fallback_families": [],
      "hard_reject_reason_categories": [
        "knn_ood_audit_missing",
        "precision_ci_below_gate"
      ],
      "high_priority_precision": 1.0,
      "high_priority_precision_ci_low": 0.9927358210851793,
      "high_priority_prediction_count": 525,
      "high_priority_true_positive_count": 525,
      "max_accepted_bad_mode_count": 0,
      "min_family_accepted_high_roi_count": 0,
      "min_family_high_roi_capture_rate": 0.0,
      "old_gat_baseline_accepted_batch_roi": 0.0,
      "random_baseline_accepted_batch_roi": 0.0,
      "safe_precision": 1.0,
      "safe_precision_ci_low": 0.8513404742740388,
      "threshold": 0.5478627681732178,
      "threshold_local_gate_pass": false,
      "threshold_local_hard_reject_reason_categories": [
        "precision_ci_below_gate"
      ],
      "threshold_local_reject_reasons": [
        "safe_precision_ci_low_below_threshold_or_not_measurable"
      ],
      "threshold_mode": "separate_batch_candidate",
      "total_batches": 326
    }
  },
  "train_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 51,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.05698324022346369,
    "accepted_batch_roi": 8.855635017156601,
    "accepted_batch_roi_ci_low": 6.032210041024795,
    "accepted_batch_roi_over_baseline": 8.855635017156601,
    "accepted_batch_roi_over_baseline_ci_low": 6.032210041024795,
    "accepted_batch_roi_over_best_rc_baseline": 8.855635017156601,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 6.032210041024795,
    "accepted_batch_roi_over_old_gat_baseline": 8.855635017156601,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 6.032210041024795,
    "accepted_batch_roi_over_random_baseline": 8.855635017156601,
    "accepted_batch_roi_over_random_baseline_ci_low": 6.032210041024795,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.5478627681732178,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_blocked_count": 0,
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.55,
    "candidate_delay_score_penalty": 1.5,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 8800,
    "candidate_score_threshold_blocked_count": 8800,
    "candidate_threshold": 0.2552189121665872,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 1053,
    "delay_rate": 0.9430167597765363,
    "evaluated_candidate_count": 10092,
    "expected_trajectory_utility": 8.87622325245072,
    "false_high_priority_on_delay": 0.000949667616334283,
    "false_high_priority_on_delay_count": 1,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.000949667616334283,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 9,
    "family_holdout_min_accepted_roi": 8.018012222490812,
    "family_holdout_min_high_roi_capture_rate": 0.1792452830188679,
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
        "accepted_batch_count": 9,
        "accepted_batch_roi": 8.717266930474175,
        "accepted_high_roi_count": 9,
        "high_roi_capture_rate": 0.23076923076923078,
        "max_accepted_batch_roi_label": 18.683509826660156,
        "oracle_high_roi_count": 39,
        "safe_precision": 1.0,
        "total_batches": 234
      },
      "random-wave": {
        "accepted_batch_count": 23,
        "accepted_batch_roi": 9.601728316234505,
        "accepted_high_roi_count": 21,
        "high_roi_capture_rate": 0.25609756097560976,
        "max_accepted_batch_roi_label": 77.04981231689453,
        "oracle_high_roi_count": 82,
        "safe_precision": 1.0,
        "total_batches": 317
      },
      "sector-wave": {
        "accepted_batch_count": 19,
        "accepted_batch_roi": 8.018012222490812,
        "accepted_high_roi_count": 19,
        "high_roi_capture_rate": 0.1792452830188679,
        "max_accepted_batch_roi_label": 31.935651779174805,
        "oracle_high_roi_count": 106,
        "safe_precision": 1.0,
        "total_batches": 344
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "knn_ood_audit_missing"
    ],
    "high_priority_precision": 0.9992260061919505,
    "high_priority_precision_ci_low": 0.9956286800857106,
    "high_priority_prediction_count": 1292,
    "high_priority_true_positive_count": 1291,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9299509861127317,
    "threshold": 0.5478627681732178,
    "threshold_local_gate_pass": true,
    "threshold_local_hard_reject_reason_categories": [],
    "threshold_local_reject_reasons": [],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 895
  },
  "validation_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 22,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.06748466257668712,
    "accepted_batch_roi": 12.614279048009353,
    "accepted_batch_roi_ci_low": 5.023888300128747,
    "accepted_batch_roi_over_baseline": 12.614279048009353,
    "accepted_batch_roi_over_baseline_ci_low": 5.023888300128747,
    "accepted_batch_roi_over_best_rc_baseline": 12.614279048009353,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 5.023888300128747,
    "accepted_batch_roi_over_old_gat_baseline": 12.614279048009353,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 5.023888300128747,
    "accepted_batch_roi_over_random_baseline": 12.614279048009353,
    "accepted_batch_roi_over_random_baseline_ci_low": 5.023888300128747,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.5478627681732178,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_blocked_count": 0,
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.55,
    "candidate_delay_score_penalty": 1.5,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 2735,
    "candidate_score_threshold_blocked_count": 2735,
    "candidate_threshold": 0.2552189121665872,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable",
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 286,
    "delay_rate": 0.9325153374233128,
    "evaluated_candidate_count": 3260,
    "expected_trajectory_utility": 12.637006320736624,
    "false_high_priority_on_delay": 0.0,
    "false_high_priority_on_delay_count": 0,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.0,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 5,
    "family_holdout_min_accepted_roi": 6.602623319625854,
    "family_holdout_min_high_roi_capture_rate": 0.21428571428571427,
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
        "accepted_batch_count": 5,
        "accepted_batch_roi": 6.602623319625854,
        "accepted_high_roi_count": 5,
        "high_roi_capture_rate": 0.25,
        "max_accepted_batch_roi_label": 106.158935546875,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "total_batches": 124
      },
      "random-wave": {
        "accepted_batch_count": 8,
        "accepted_batch_roi": 21.57581076025963,
        "accepted_high_roi_count": 8,
        "high_roi_capture_rate": 0.23529411764705882,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "oracle_high_roi_count": 34,
        "safe_precision": 1.0,
        "total_batches": 132
      },
      "sector-wave": {
        "accepted_batch_count": 9,
        "accepted_batch_roi": 7.988281819555494,
        "accepted_high_roi_count": 6,
        "high_roi_capture_rate": 0.21428571428571427,
        "max_accepted_batch_roi_label": 41.31852722167969,
        "oracle_high_roi_count": 28,
        "safe_precision": 1.0,
        "total_batches": 70
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "knn_ood_audit_missing",
      "precision_ci_below_gate"
    ],
    "high_priority_precision": 1.0,
    "high_priority_precision_ci_low": 0.9927358210851793,
    "high_priority_prediction_count": 525,
    "high_priority_true_positive_count": 525,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.8513404742740388,
    "threshold": 0.5478627681732178,
    "threshold_local_gate_pass": false,
    "threshold_local_hard_reject_reason_categories": [
      "precision_ci_below_gate"
    ],
    "threshold_local_reject_reasons": [
      "safe_precision_ci_low_below_threshold_or_not_measurable"
    ],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 326
  }
}
```

## 边界

- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；
- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；
- 当前 checkpoint 仍 `production_ready=false`；
- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；
- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。
