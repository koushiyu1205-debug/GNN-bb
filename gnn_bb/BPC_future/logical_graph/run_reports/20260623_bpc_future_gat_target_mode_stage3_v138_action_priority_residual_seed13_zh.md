# GAT Batch Impact Training 报告

日期：2026-06-23

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
sample_count = 1117
candidate_count = 12684
family_counts = {'greedy-anchor': 358, 'random-wave': 421, 'sector-wave': 338}
task_count_counts = {'10': 74, '100': 36, '20': 688, '30': 168, '5': 32, '50': 119}
training_objective = precision_constrained_roi_maximization
training_run_config = {'seed': 13, 'validation_fraction': 0.25, 'epochs': 5, 'device': 'cuda', 'lr': 0.001, 'weight_decay': 1e-05, 'max_grad_norm': 5.0, 'model_config': {'node_dim': 9, 'option_dim': 10, 'candidate_feature_dim': 59, 'context_feature_dim': 26, 'batch_feature_dim': 18, 'path_token_vocab_size': 4096, 'path_pair_vocab_size': 4096, 'path_type_vocab_size': 3, 'path_token_dim': 16, 'path_hidden_dim': 32, 'hidden_dim': 32, 'option_hidden_dim': 32, 'pair_edge_dim': 32, 'num_gnn_layers': 1, 'heads': 4, 'dropout': 0.05, 'candidate_hidden_dim': 32, 'context_hidden_dim': 24, 'batch_hidden_dim': 32, 'impact_hidden_dim': 32, 'context_pair_hidden_dim': 0, 'candidate_context_interaction_dim': 0, 'candidate_batch_priority_residual_scale': 0.0, 'delay_risk_batch_priority_residual_scale': 0.0, 'candidate_action_priority_residual_scale': 0.5, 'delay_risk_action_priority_residual_scale': 0.5, 'use_layer_norm': True}, 'loss_options': {'false_high_priority_loss_multiplier': 8.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 1.25, 'hard_roi_negative_delay_loss_multiplier': 1.25, 'hard_roi_safe_delay_loss_multiplier': 0.35, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 1.5, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'context_pair_comparator_loss_multiplier': 0.0, 'focused_pair_loss_multiplier': 1.25, 'focused_pair_candidate_loss_multiplier': 0.0, 'focused_pair_raw_all_candidate_loss_multiplier': 6.0, 'focused_pair_admission_loss_multiplier': 2.5, 'focused_pair_delay_risk_loss_multiplier': 6.0, 'focused_pair_batch_loss_multiplier': 0.75, 'focused_pair_batch_priority_loss_multiplier': 0.0, 'focused_pair_action_priority_loss_multiplier': 4.0, 'focused_pair_context_comparator_loss_multiplier': 0.0, 'focused_pair_boost_row_indices_file': 'BPC_future/results/gat_batch_impact_v134_trainonly_raw_action_boost_20260623/focused_raw_action_boost_train_row_indices.json', 'focused_pair_boost_row_indices': [176, 398, 779, 780, 781, 782, 783, 846, 847], 'focused_pair_boost_loss_multiplier': 1.5, 'targeted_safe_positive_row_indices_file': 'BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/optional_v121_train_targeted_safe_positive_row_indices.json', 'targeted_safe_positive_row_indices': [5, 252, 408, 409, 461, 648, 751, 787, 791, 840, 841, 896, 897, 912, 913, 959, 963, 977, 1018, 1019, 1022, 1128, 1132, 1146], 'targeted_safe_positive_loss_multiplier': 0.75, 'focused_pair_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json', 'focused_pair_gate_row_indices': [106, 109, 133, 176, 177, 183, 326, 331, 362, 390, 391, 392, 398, 402, 411, 412, 413, 425, 426, 509, 514, 767, 768, 770, 779, 780, 781, 782, 783, 792, 793, 795, 796, 797, 798, 799, 808, 809, 810, 811, 812, 813, 814, 815, 842, 843, 844, 845, 846, 847, 848, 849, 888, 889, 918, 919, 922, 923, 956, 958, 959, 960, 961, 962, 963, 966, 967, 969, 978, 979, 980, 981, 982, 983, 985, 990, 991, 992, 993, 998, 999, 1001, 1010, 1011, 1012, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1040, 1041, 1042, 1050, 1051, 1053, 1097, 1104, 1123], 'focused_pair_training_row_indices_file': 'BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_training_row_indices.json', 'focused_pair_row_indices': [106, 109, 133, 176, 177, 326, 331, 362, 390, 391, 392, 398, 402, 411, 412, 413, 425, 426, 509, 514, 779, 780, 781, 782, 783, 792, 793, 795, 808, 809, 810, 811, 842, 843, 846, 847, 918, 919, 922, 923, 956, 958, 959, 960, 961, 962, 963, 966, 967, 969, 978, 979, 980, 981, 982, 983, 985, 990, 991, 992, 993, 1010, 1011, 1012, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1040, 1041, 1042, 1050, 1051, 1053, 1097, 1104, 1123], 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}, 'gate_config': {'min_high_priority_precision': 0.9, 'min_high_priority_precision_ci_low': 0.9, 'min_safe_precision': 0.9, 'min_safe_precision_ci_low': 0.9, 'confidence_z': 1.96, 'max_false_high_priority_on_delay': 0.01, 'max_false_safe_union_rate': 0.02, 'max_accepted_bad_mode_count': 0, 'min_accepted_batch_count': 1, 'min_accepted_batch_rate': 0.02, 'min_accepted_batch_roi': 0.65, 'min_accepted_batch_roi_ci_low': 0.65, 'baseline_accepted_batch_roi': 0.0, 'baseline_selection_roi': 0.0, 'baseline_roi_ci_high': 0.0, 'baseline_roi_ci_high_source': 'configured_point_estimate_no_baseline_distribution', 'random_baseline_accepted_batch_roi': 0.0, 'best_rc_baseline_accepted_batch_roi': 0.0, 'old_gat_baseline_accepted_batch_roi': 0.0, 'min_roi_margin_over_baseline': 0.2, 'min_family_holdout_precision': 0.8, 'min_family_holdout_accepted_roi': 0.65, 'min_family_accepted_high_roi_count': 0, 'min_family_high_roi_capture_rate': 0.0, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 1.5, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'min_major_families': 2, 'observed_family_count': 3, 'stage3_min_samples': 200, 'actual_sample_count': 1117, 'knn_ood_audit_completed': False, 'candidate_delay_gate_enabled': True, 'candidate_delay_risk_threshold': 0.6, 'require_positive_candidate_threshold': True}, 'focused_pair_gate_config': {'focused_pair_gate_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json', 'focused_pair_row_indices_count': 102, 'focused_pair_training_row_indices_file': 'BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_training_row_indices.json', 'focused_pair_training_row_indices_count': 81, 'focused_pair_selector': 'explicit_row_indices', 'min_focused_pair_count': 1, 'min_focused_raw_pair_pass_rate': 1.0, 'min_focused_admission_pair_pass_rate': 1.0, 'min_focused_delay_risk_pair_pass_rate': 1.0, 'min_focused_strict_pair_pass_rate': 1.0}, 'checkpoint_selection': 'deployment_gate_first_then_roi_ci_baseline_utility_loss'}
hard_roi_threshold = 0.65
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.6
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.5
candidate_rescue_raw_score_threshold = 1.0
candidate_rescue_delay_risk_threshold = 1.0
candidate_rescue_delay_score_penalty = 0.0
loss_options = {'false_high_priority_loss_multiplier': 8.0, 'bad_mode_loss_multiplier': 2.0, 'regression_loss_multiplier': 0.15, 'hard_roi_loss_multiplier': 1.0, 'hard_roi_candidate_loss_multiplier': 0.5, 'hard_roi_positive_candidate_loss_multiplier': 0.0, 'hard_roi_positive_group_balance': 'none', 'hard_roi_positive_group_weight_power': 0.5, 'max_hard_roi_positive_group_weight': 4.0, 'hard_roi_positive_group_counts': {}, 'hard_roi_positive_group_weights': {}, 'candidate_delay_loss_multiplier': 1.25, 'hard_roi_negative_delay_loss_multiplier': 1.25, 'hard_roi_safe_delay_loss_multiplier': 0.35, 'candidate_admission_score_mode': 'risk_adjusted_product', 'candidate_delay_score_penalty': 1.5, 'candidate_rescue_raw_score_threshold': 1.0, 'candidate_rescue_delay_risk_threshold': 1.0, 'candidate_rescue_delay_score_penalty': 0.0, 'hard_roi_threshold': 0.65, 'pairwise_ranking_loss_multiplier': 1.0, 'pairwise_candidate_ranking_loss_multiplier': 0.75, 'pairwise_false_delay_contrast_loss_multiplier': 0.5, 'pairwise_delay_risk_contrast_loss_multiplier': 1.0, 'context_pair_comparator_loss_multiplier': 0.0, 'focused_pair_loss_multiplier': 1.25, 'focused_pair_candidate_loss_multiplier': 0.0, 'focused_pair_raw_all_candidate_loss_multiplier': 6.0, 'focused_pair_admission_loss_multiplier': 2.5, 'focused_pair_delay_risk_loss_multiplier': 6.0, 'focused_pair_batch_loss_multiplier': 0.75, 'focused_pair_batch_priority_loss_multiplier': 0.0, 'focused_pair_action_priority_loss_multiplier': 4.0, 'focused_pair_context_comparator_loss_multiplier': 0.0, 'focused_pair_boost_row_indices_file': 'BPC_future/results/gat_batch_impact_v134_trainonly_raw_action_boost_20260623/focused_raw_action_boost_train_row_indices.json', 'focused_pair_boost_row_indices': [176, 398, 779, 780, 781, 782, 783, 846, 847], 'focused_pair_boost_loss_multiplier': 1.5, 'targeted_safe_positive_row_indices_file': 'BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/optional_v121_train_targeted_safe_positive_row_indices.json', 'targeted_safe_positive_row_indices': [5, 252, 408, 409, 461, 648, 751, 787, 791, 840, 841, 896, 897, 912, 913, 959, 963, 977, 1018, 1019, 1022, 1128, 1132, 1146], 'targeted_safe_positive_loss_multiplier': 0.75, 'focused_pair_row_index_min': None, 'focused_pair_row_indices_file': 'BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json', 'focused_pair_gate_row_indices': [106, 109, 133, 176, 177, 183, 326, 331, 362, 390, 391, 392, 398, 402, 411, 412, 413, 425, 426, 509, 514, 767, 768, 770, 779, 780, 781, 782, 783, 792, 793, 795, 796, 797, 798, 799, 808, 809, 810, 811, 812, 813, 814, 815, 842, 843, 844, 845, 846, 847, 848, 849, 888, 889, 918, 919, 922, 923, 956, 958, 959, 960, 961, 962, 963, 966, 967, 969, 978, 979, 980, 981, 982, 983, 985, 990, 991, 992, 993, 998, 999, 1001, 1010, 1011, 1012, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1040, 1041, 1042, 1050, 1051, 1053, 1097, 1104, 1123], 'focused_pair_training_row_indices_file': 'BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_training_row_indices.json', 'focused_pair_row_indices': [106, 109, 133, 176, 177, 326, 331, 362, 390, 391, 392, 398, 402, 411, 412, 413, 425, 426, 509, 514, 779, 780, 781, 782, 783, 792, 793, 795, 808, 809, 810, 811, 842, 843, 846, 847, 918, 919, 922, 923, 956, 958, 959, 960, 961, 962, 963, 966, 967, 969, 978, 979, 980, 981, 982, 983, 985, 990, 991, 992, 993, 1010, 1011, 1012, 1018, 1019, 1020, 1021, 1022, 1023, 1024, 1025, 1040, 1041, 1042, 1050, 1051, 1053, 1097, 1104, 1123], 'pairwise_roi_margin': 0.05, 'min_pairwise_roi_delta': 1e-06, 'max_grad_norm': 5.0}
pairwise_ranking_loss_active = true
pairwise_candidate_ranking_loss_multiplier = 0.75
pairwise_false_delay_contrast_loss_multiplier = 0.5
pairwise_delay_risk_contrast_loss_multiplier = 1.0
context_pair_hidden_dim = 0
candidate_context_interaction_dim = 0
candidate_batch_priority_residual_scale = 0.0
delay_risk_batch_priority_residual_scale = 0.0
candidate_action_priority_residual_scale = 0.5
delay_risk_action_priority_residual_scale = 0.5
context_pair_comparator_loss_multiplier = 0.0
focused_pair_loss_multiplier = 1.25
focused_pair_candidate_loss_multiplier = 0.0
focused_pair_raw_all_candidate_loss_multiplier = 6.0
focused_pair_admission_loss_multiplier = 2.5
focused_pair_delay_risk_loss_multiplier = 6.0
focused_pair_batch_loss_multiplier = 0.75
focused_pair_batch_priority_loss_multiplier = 0.0
focused_pair_action_priority_loss_multiplier = 4.0
focused_pair_context_comparator_loss_multiplier = 0.0
focused_pair_boost_row_indices_file = BPC_future/results/gat_batch_impact_v134_trainonly_raw_action_boost_20260623/focused_raw_action_boost_train_row_indices.json
focused_pair_boost_row_indices_count = 9
focused_pair_boost_loss_multiplier = 1.5
targeted_safe_positive_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/optional_v121_train_targeted_safe_positive_row_indices.json
targeted_safe_positive_row_indices_count = 24
targeted_safe_positive_loss_multiplier = 0.75
focused_pair_row_index_min = None
focused_pair_row_indices_file = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json
focused_pair_row_indices_count = 81
pairwise_ranking_status = active_same_context_roi_margin_ranking
context_pair_stats = {'all': {'sample_count': 1117, 'context_count': 546, 'multi_context_count': 232, 'same_context_pair_count': 1239, 'same_context_comparable_pair_count': 772, 'positive_negative_label_pair_count': 249, 'roi_diverse_context_count': 177, 'largest_context_size': 11}, 'train': {'sample_count': 825, 'context_count': 411, 'multi_context_count': 172, 'same_context_pair_count': 885, 'same_context_comparable_pair_count': 551, 'positive_negative_label_pair_count': 166, 'roi_diverse_context_count': 127, 'largest_context_size': 11}, 'validation': {'sample_count': 292, 'context_count': 135, 'multi_context_count': 60, 'same_context_pair_count': 354, 'same_context_comparable_pair_count': 221, 'positive_negative_label_pair_count': 83, 'roi_diverse_context_count': 50, 'largest_context_size': 7}}
focused_pair_gate_active = true
focused_pair_gate_summary = {'focused_row_count': 102, 'context_count': 30, 'contexts_with_positive_and_negative': 30, 'positive_row_count': 56, 'negative_row_count': 46, 'ambiguous_row_count': 0, 'pair_count': 78, 'raw_pair_pass_count': 75, 'admission_pair_pass_count': 74, 'delay_risk_pair_pass_count': 74, 'strict_pair_pass_count': 74, 'raw_pair_pass_rate': 0.9615384615384616, 'admission_pair_pass_rate': 0.9487179487179487, 'delay_risk_pair_pass_rate': 0.9487179487179487, 'strict_pair_pass_rate': 0.9487179487179487, 'label_counts': {'delay_or_hard_negative': 46, 'positive_high_priority': 56}, 'family_counts': {'greedy-anchor': 33, 'random-wave': 47, 'sector-wave': 22}, 'primary': 'candidate_head_context_ranking_failure'}
focused_pair_gate_reject_reasons = ['raw_pair_pass_rate_below_threshold', 'admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
rejected_checkpoint_reasons = ['admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'knn_ood_audit_missing', 'raw_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
rejected_checkpoint_reason_categories = ['focused_pair_gate_failed', 'knn_ood_audit_missing']
best_epoch = 2
selected_validation_loss = 5.7173495521119
best_loss_epoch = 4
best_validation_loss = 4.890735316319032
best_loss_epoch_gate_pass = true
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['admission_pair_pass_rate_below_threshold', 'delay_risk_pair_pass_rate_below_threshold', 'knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run', 'raw_pair_pass_rate_below_threshold', 'strict_pair_pass_rate_below_threshold']
attempted_update_count = 7630
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
    "family_holdout_min_accepted_high_roi_count": 7,
    "family_holdout_min_accepted_roi": 7.117968122164409,
    "family_holdout_min_high_roi_capture_rate": 0.4117647058823529,
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
        "accepted_batch_roi": 33.91330652766757,
        "accepted_high_roi_count": 9,
        "high_roi_capture_rate": 0.45,
        "max_accepted_batch_roi_label": 106.158935546875,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "total_batches": 124
      },
      "random-wave": {
        "accepted_batch_count": 14,
        "accepted_batch_roi": 21.08774014775242,
        "accepted_high_roi_count": 12,
        "high_roi_capture_rate": 0.5454545454545454,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "total_batches": 113
      },
      "sector-wave": {
        "accepted_batch_count": 12,
        "accepted_batch_roi": 7.117968122164409,
        "accepted_high_roi_count": 7,
        "high_roi_capture_rate": 0.4117647058823529,
        "max_accepted_batch_roi_label": 33.70098114013672,
        "oracle_high_roi_count": 17,
        "safe_precision": 1.0,
        "total_batches": 55
      }
    },
    "family_specific_delay_fallback_families": [],
    "per_family": {
      "greedy-anchor": {
        "accepted_batch_count": 9,
        "accepted_batch_roi": 33.91330652766757,
        "accepted_high_roi_count": 9,
        "high_roi_capture_rate": 0.45,
        "max_accepted_batch_roi_label": 106.158935546875,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "total_batches": 124
      },
      "random-wave": {
        "accepted_batch_count": 14,
        "accepted_batch_roi": 21.08774014775242,
        "accepted_high_roi_count": 12,
        "high_roi_capture_rate": 0.5454545454545454,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "total_batches": 113
      },
      "sector-wave": {
        "accepted_batch_count": 12,
        "accepted_batch_roi": 7.117968122164409,
        "accepted_high_roi_count": 7,
        "high_roi_capture_rate": 0.4117647058823529,
        "max_accepted_batch_roi_label": 33.70098114013672,
        "oracle_high_roi_count": 17,
        "safe_precision": 1.0,
        "total_batches": 55
      }
    }
  },
  "focused_pair_gate": {
    "active": true,
    "context_rows": [
      {
        "admission_pair_pass_rate": 0.5,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
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
        "context_hash": "7db256d4f7224cc6",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
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
        "raw_pair_pass_rate": 1.0,
        "row_count": 2,
        "strict_pair_pass_rate": 1.0
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
        "admission_pair_pass_rate": 1.0,
        "context_hash": "1b9dab1b2a407abd",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks030_02_seed71102|1b9dab1b2a407abd",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 1,
        "pair_count": 1,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 2,
        "strict_pair_pass_rate": 1.0
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
        "admission_pair_pass_rate": 1.0,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "greedy-anchor",
        "negative_count": 2,
        "pair_count": 4,
        "positive_count": 2,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 1.0
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
        "admission_pair_pass_rate": 0.0,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_pair_pass_rate": 0.0,
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
        "admission_pair_pass_rate": 0.6666666666666666,
        "context_hash": "7cb380a02e30e5a8",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
        "delay_risk_pair_pass_rate": 0.6666666666666666,
        "family": "random-wave",
        "negative_count": 3,
        "pair_count": 3,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 0.6666666666666666
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
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 2,
        "pair_count": 10,
        "positive_count": 5,
        "raw_pair_pass_rate": 1.0,
        "row_count": 7,
        "strict_pair_pass_rate": 1.0
      },
      {
        "admission_pair_pass_rate": 1.0,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_pair_pass_rate": 1.0,
        "family": "sector-wave",
        "negative_count": 3,
        "pair_count": 3,
        "positive_count": 1,
        "raw_pair_pass_rate": 1.0,
        "row_count": 4,
        "strict_pair_pass_rate": 1.0
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
    "focus_row_indices_count": 102,
    "focus_row_indices_file": "BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json",
    "focus_selector": "explicit_row_indices",
    "gate": {
      "blocking_primary": "candidate_head_context_ranking_failure",
      "diagnostic_only": true,
      "gate_name": "focused_same_context_positive_negative_pair_gate",
      "gate_pass": false,
      "observed": {
        "admission_pair_pass_rate": 0.9487179487179487,
        "delay_risk_pair_pass_rate": 0.9487179487179487,
        "pair_count": 78,
        "raw_pair_pass_rate": 0.9615384615384616,
        "strict_pair_pass_rate": 0.9487179487179487
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
        "admission_margin": 0.03439100045282065,
        "admission_positive_above_negative": true,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_margin": 0.026901811361312866,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 814,
        "negative_signature_ids": [
          "205a20d28e242d3d13b42954fc1ccae0302a39a4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 3.0676430000000323,
        "positive_row_index": 812,
        "positive_signature_ids": [
          "3fa5854924ac844a7e090bde70be0e205e2b3410"
        ],
        "raw_margin": 0.04279646277427673,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.031347909818833175,
        "admission_positive_above_negative": false,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_margin": -0.019684791564941406,
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
        "raw_margin": -0.04034256935119629,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.0377900818060522,
        "admission_positive_above_negative": true,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_margin": 0.029172271490097046,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 814,
        "negative_signature_ids": [
          "205a20d28e242d3d13b42954fc1ccae0302a39a4"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.3209439999999972,
        "positive_row_index": 813,
        "positive_signature_ids": [
          "f2813b715a37b431927f932dd1a75815eeb18ff5"
        ],
        "raw_margin": 0.04720166325569153,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.02794882846560162,
        "admission_positive_above_negative": false,
        "context_hash": "b36178f6655c5f75",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75",
        "delay_risk_margin": -0.017414331436157227,
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
        "raw_margin": -0.035937368869781494,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.053163347509841585,
        "admission_positive_above_negative": true,
        "context_hash": "7db256d4f7224cc6",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
        "delay_risk_margin": 0.04119214415550232,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 991,
        "negative_signature_ids": [
          "a9e74d78debdc9131ca24f9a86350c9e7dde56f9"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.9891109999999799,
        "positive_row_index": 990,
        "positive_signature_ids": [
          "5b29de0980e2376e6f56e7594a22af1af46500cf"
        ],
        "raw_margin": 0.0692690908908844,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.043067759580100784,
        "admission_positive_above_negative": true,
        "context_hash": "7db256d4f7224cc6",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
        "delay_risk_margin": 0.02557319402694702,
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
        "raw_margin": 0.06834015250205994,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.032342802824151695,
        "admission_positive_above_negative": true,
        "context_hash": "7db256d4f7224cc6",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|7db256d4f7224cc6",
        "delay_risk_margin": 0.024847179651260376,
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
        "raw_margin": 0.044454604387283325,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05784584953062158,
        "admission_positive_above_negative": true,
        "context_hash": "f9d0b6b18a0a28d3",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|f9d0b6b18a0a28d3",
        "delay_risk_margin": 0.04468294978141785,
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
        "raw_margin": 0.08071070909500122,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.047122895549808946,
        "admission_positive_above_negative": true,
        "context_hash": "f9d0b6b18a0a28d3",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_05_seed61410|f9d0b6b18a0a28d3",
        "delay_risk_margin": 0.035996317863464355,
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
        "raw_margin": 0.06456425786018372,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.017064754254020154,
        "admission_positive_above_negative": true,
        "context_hash": "84ae11479ed592d4",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
        "delay_risk_margin": 0.015563100576400757,
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
        "raw_margin": 0.0222511887550354,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.020989961975994592,
        "admission_positive_above_negative": true,
        "context_hash": "84ae11479ed592d4",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_06_seed61512|84ae11479ed592d4",
        "delay_risk_margin": 0.0220814049243927,
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
        "raw_margin": 0.023894190788269043,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.022861294248663233,
        "admission_positive_above_negative": true,
        "context_hash": "39d7643d5a478407",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614|39d7643d5a478407",
        "delay_risk_margin": 0.01999393105506897,
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
        "raw_margin": 0.030770033597946167,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04283967276333395,
        "admission_positive_above_negative": true,
        "context_hash": "39d7643d5a478407",
        "context_key": "apollo15_20km_greedy-anchor_randomtw_tasks020_07_seed61614|39d7643d5a478407",
        "delay_risk_margin": 0.029583722352981567,
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
        "raw_margin": 0.06543651223182678,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.13858330026040708,
        "admission_positive_above_negative": true,
        "context_hash": "62c86745ed2b3aaa",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
        "delay_risk_margin": 0.182342529296875,
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
        "raw_margin": 0.27698254585266113,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.17539315825397694,
        "admission_positive_above_negative": true,
        "context_hash": "62c86745ed2b3aaa",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa",
        "delay_risk_margin": 0.20311778783798218,
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
        "raw_margin": 0.3401724398136139,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.041426263128766544,
        "admission_positive_above_negative": true,
        "context_hash": "1b5a36a64a700b58",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
        "delay_risk_margin": 0.03530648350715637,
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
        "raw_margin": 0.05518442392349243,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.024844595135291497,
        "admission_positive_above_negative": true,
        "context_hash": "1b5a36a64a700b58",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
        "delay_risk_margin": 0.02257785201072693,
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
        "raw_margin": 0.03269067406654358,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.1280460529401483,
        "admission_positive_above_negative": true,
        "context_hash": "1b5a36a64a700b58",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|1b5a36a64a700b58",
        "delay_risk_margin": 0.09784653782844543,
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
        "raw_margin": 0.15446102619171143,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03885119384949032,
        "admission_positive_above_negative": true,
        "context_hash": "4575716b3939cb89",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|4575716b3939cb89",
        "delay_risk_margin": 0.033888816833496094,
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
        "raw_margin": 0.048819929361343384,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.044747682192974314,
        "admission_positive_above_negative": true,
        "context_hash": "4575716b3939cb89",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|4575716b3939cb89",
        "delay_risk_margin": 0.03757447004318237,
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
        "raw_margin": 0.05906456708908081,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08125410991469639,
        "admission_positive_above_negative": true,
        "context_hash": "ff6827bb236f4831",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|ff6827bb236f4831",
        "delay_risk_margin": 0.044067054986953735,
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
        "raw_margin": 0.1307780146598816,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07974502733509514,
        "admission_positive_above_negative": true,
        "context_hash": "ff6827bb236f4831",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks020_10_seed61919|ff6827bb236f4831",
        "delay_risk_margin": 0.051168203353881836,
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
        "raw_margin": 0.11752068996429443,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06983715903286208,
        "admission_positive_above_negative": true,
        "context_hash": "9f80ae35ea87da5b",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b",
        "delay_risk_margin": 0.0483396053314209,
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
        "raw_margin": 0.05756717920303345,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.010462621275666606,
        "admission_positive_above_negative": true,
        "context_hash": "9f80ae35ea87da5b",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b",
        "delay_risk_margin": 0.009106606245040894,
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
        "raw_margin": 0.00784599781036377,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08508064764438728,
        "admission_positive_above_negative": true,
        "context_hash": "9a2ca522ff49991c",
        "context_key": "apollo15_20km_random-wave_randomtw_tasks050_01_seed91000|9a2ca522ff49991c",
        "delay_risk_margin": 0.05027049779891968,
        "family": "random-wave",
        "negative_roi": -4.876676650000114,
        "negative_row_index": 402,
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
        "raw_margin": 0.05441129207611084,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07865771878832362,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.05428615212440491,
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
        "raw_margin": 0.10290998220443726,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07865771878832362,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.05428615212440491,
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
        "raw_margin": 0.10290998220443726,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07865771878832362,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.05428615212440491,
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
        "raw_margin": 0.10290998220443726,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.09503876609243844,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.07342138886451721,
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
        "raw_margin": 0.1176500916481018,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07865771878832362,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.05428615212440491,
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
        "raw_margin": 0.10290998220443726,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.07865771878832362,
        "admission_positive_above_negative": true,
        "context_hash": "ce3508e12ad69da7",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612|ce3508e12ad69da7",
        "delay_risk_margin": 0.05428615212440491,
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
        "raw_margin": 0.10290998220443726,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08949387600597772,
        "admission_positive_above_negative": true,
        "context_hash": "1b9dab1b2a407abd",
        "context_key": "apollo15_20km_sector-wave_randomtw_tasks030_02_seed71102|1b9dab1b2a407abd",
        "delay_risk_margin": 0.06558501720428467,
        "family": "sector-wave",
        "negative_roi": 0.0,
        "negative_row_index": 923,
        "negative_signature_ids": [
          "6cd52fe5346636609262c4972803573d4e776e12"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0419710000001032,
        "positive_row_index": 922,
        "positive_signature_ids": [
          "7925911ed9a6e62074766bd26509735eb63373d4"
        ],
        "raw_margin": 0.13505518436431885,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.13393662025889871,
        "admission_positive_above_negative": true,
        "context_hash": "77bc967e4038b08b",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414|77bc967e4038b08b",
        "delay_risk_margin": 0.09978604316711426,
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
        "raw_margin": 0.2036539912223816,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.13308104911532212,
        "admission_positive_above_negative": true,
        "context_hash": "77bc967e4038b08b",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_05_seed61414|77bc967e4038b08b",
        "delay_risk_margin": 0.09137400984764099,
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
        "raw_margin": 0.21371221542358398,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04225451212284992,
        "admission_positive_above_negative": true,
        "context_hash": "67925c0d2fd4abde",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
        "delay_risk_margin": 0.03295740485191345,
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
        "raw_margin": 0.057858556509017944,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04440799450635963,
        "admission_positive_above_negative": true,
        "context_hash": "67925c0d2fd4abde",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
        "delay_risk_margin": 0.03506326675415039,
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
        "raw_margin": 0.05994090437889099,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.05030886989853789,
        "admission_positive_above_negative": true,
        "context_hash": "67925c0d2fd4abde",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|67925c0d2fd4abde",
        "delay_risk_margin": 0.033020585775375366,
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
        "raw_margin": 0.07616057991981506,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.17921525494621804,
        "admission_positive_above_negative": true,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_margin": 0.15659642219543457,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1023,
        "negative_signature_ids": [
          "fcd09bbac25e9a1a3a18689df81a0a296df13a50"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.6925289999999222,
        "positive_row_index": 1022,
        "positive_signature_ids": [
          "9aaa3dd99445936514f4ca04ace40d7f80516104"
        ],
        "raw_margin": 0.2986312806606293,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.16596666124348042,
        "admission_positive_above_negative": true,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_margin": 0.13515466451644897,
        "family": "greedy-anchor",
        "negative_roi": 0.0,
        "negative_row_index": 1024,
        "negative_signature_ids": [
          "ad32ef0f1bec6d1378959e4aaeca26ff653c01a5"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 0.6925289999999222,
        "positive_row_index": 1022,
        "positive_signature_ids": [
          "9aaa3dd99445936514f4ca04ace40d7f80516104"
        ],
        "raw_margin": 0.27337974309921265,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.18672148156409962,
        "admission_positive_above_negative": true,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_margin": 0.16302144527435303,
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
        "raw_margin": 0.30596569180488586,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.173472887861362,
        "admission_positive_above_negative": true,
        "context_hash": "ddb0ce64af10976a",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_06_seed61520|ddb0ce64af10976a",
        "delay_risk_margin": 0.14157968759536743,
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
        "raw_margin": 0.28071415424346924,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.012236411706738615,
        "admission_positive_above_negative": true,
        "context_hash": "f4e732e2cfdeea6e",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635|f4e732e2cfdeea6e",
        "delay_risk_margin": 0.010365456342697144,
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
        "raw_margin": 0.016499996185302734,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.024343262663463178,
        "admission_positive_above_negative": true,
        "context_hash": "f4e732e2cfdeea6e",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635|f4e732e2cfdeea6e",
        "delay_risk_margin": 0.020997226238250732,
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
        "raw_margin": 0.033431023359298706,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04635127325641497,
        "admission_positive_above_negative": true,
        "context_hash": "3d4ab1c1e344186b",
        "context_key": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks030_02_seed71115|3d4ab1c1e344186b",
        "delay_risk_margin": 0.03180384635925293,
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
        "raw_margin": 0.05608856678009033,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.09834218247913679,
        "admission_positive_above_negative": true,
        "context_hash": "5c522ff2995f86be",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
        "delay_risk_margin": 0.055945366621017456,
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
        "raw_margin": 0.14409491419792175,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.09148519466990157,
        "admission_positive_above_negative": true,
        "context_hash": "5c522ff2995f86be",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
        "delay_risk_margin": 0.050855010747909546,
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
        "raw_margin": 0.1370987594127655,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.03793888640342438,
        "admission_positive_above_negative": true,
        "context_hash": "5c522ff2995f86be",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|5c522ff2995f86be",
        "delay_risk_margin": 0.011147111654281616,
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
        "raw_margin": 0.07471683621406555,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.14718233597530664,
        "admission_positive_above_negative": true,
        "context_hash": "9eb0dc7839bf91ec",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|9eb0dc7839bf91ec",
        "delay_risk_margin": 0.09036371111869812,
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
        "raw_margin": 0.23575523495674133,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06605988856872314,
        "admission_positive_above_negative": true,
        "context_hash": "9eb0dc7839bf91ec",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|9eb0dc7839bf91ec",
        "delay_risk_margin": 0.04191869497299194,
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
        "raw_margin": 0.08924901485443115,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.02146311756083666,
        "admission_positive_above_negative": false,
        "context_hash": "ddcb5387bef3bf63",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_03_seed61205|ddcb5387bef3bf63",
        "delay_risk_margin": -0.008261919021606445,
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
        "raw_margin": -0.03520697355270386,
        "raw_positive_above_negative": false
      },
      {
        "admission_margin": 0.10425715165544355,
        "admission_positive_above_negative": true,
        "context_hash": "a77e5457bde80b8e",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717|a77e5457bde80b8e",
        "delay_risk_margin": 0.06493675708770752,
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
        "raw_margin": 0.15846794843673706,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.0444835942565783,
        "admission_positive_above_negative": true,
        "context_hash": "a77e5457bde80b8e",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717|a77e5457bde80b8e",
        "delay_risk_margin": 0.024063050746917725,
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
        "raw_margin": 0.06534689664840698,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.17573221270123576,
        "admission_positive_above_negative": true,
        "context_hash": "a77e5457bde80b8e",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_08_seed61717|a77e5457bde80b8e",
        "delay_risk_margin": 0.126478910446167,
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
        "raw_margin": 0.2938252091407776,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": -0.0008424084020914047,
        "admission_positive_above_negative": false,
        "context_hash": "7cb380a02e30e5a8",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
        "delay_risk_margin": -0.007609456777572632,
        "family": "random-wave",
        "negative_roi": 0.0,
        "negative_row_index": 808,
        "negative_signature_ids": [
          "7a60d588833203ecd1a1332abe95da279c4748c0"
        ],
        "pair_pass": false,
        "positive_lower_delay_risk": false,
        "positive_roi": 0.6718080000000555,
        "positive_row_index": 810,
        "positive_signature_ids": [
          "23993e3fd17d5b9a3ef537cbb68b3da5321162ba"
        ],
        "raw_margin": 0.008551836013793945,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08717424041996691,
        "admission_positive_above_negative": true,
        "context_hash": "7cb380a02e30e5a8",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
        "delay_risk_margin": 0.04966038465499878,
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
        "raw_margin": 0.14762330055236816,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.04084669300324348,
        "admission_positive_above_negative": true,
        "context_hash": "7cb380a02e30e5a8",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_09_seed61820|7cb380a02e30e5a8",
        "delay_risk_margin": 0.022770434617996216,
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
        "raw_margin": 0.0645592212677002,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.15342414264768306,
        "admission_positive_above_negative": true,
        "context_hash": "03605a430acbd104",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923|03605a430acbd104",
        "delay_risk_margin": 0.10739678144454956,
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
        "raw_margin": 0.27485501766204834,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.16277874840278814,
        "admission_positive_above_negative": true,
        "context_hash": "03605a430acbd104",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923|03605a430acbd104",
        "delay_risk_margin": 0.1232711672782898,
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
        "raw_margin": 0.2909766733646393,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.031145820530115498,
        "admission_positive_above_negative": true,
        "context_hash": "03605a430acbd104",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks020_10_seed61923|03605a430acbd104",
        "delay_risk_margin": 0.011242985725402832,
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
        "raw_margin": 0.05606088042259216,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.15776433679099588,
        "admission_positive_above_negative": true,
        "context_hash": "5368cf35ed6f06cb",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|5368cf35ed6f06cb",
        "delay_risk_margin": 0.10271891951560974,
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
        "raw_margin": 0.11626917123794556,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.006847829695717456,
        "admission_positive_above_negative": true,
        "context_hash": "5368cf35ed6f06cb",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|5368cf35ed6f06cb",
        "delay_risk_margin": 0.008109062910079956,
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
        "raw_margin": 0.0017046332359313965,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.17084386395296342,
        "admission_positive_above_negative": true,
        "context_hash": "a0f80eb374f29f44",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|a0f80eb374f29f44",
        "delay_risk_margin": 0.11374914646148682,
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
        "raw_margin": 0.14446568489074707,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08425011059855042,
        "admission_positive_above_negative": true,
        "context_hash": "a0f80eb374f29f44",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_02_seed71102|a0f80eb374f29f44",
        "delay_risk_margin": 0.062077492475509644,
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
        "raw_margin": 0.0819212794303894,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.004381852907721473,
        "admission_positive_above_negative": true,
        "context_hash": "be33b2560df0147a",
        "context_key": "tranquillitatis_balmer_like_20km_random-wave_randomtw_tasks030_04_seed71306|be33b2560df0147a",
        "delay_risk_margin": 0.00419992208480835,
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
        "raw_margin": 0.0025097131729125977,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.1356747950223304,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.08593389391899109,
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
        "raw_margin": 0.1347060203552246,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.13006161399894378,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.08890712261199951,
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
        "raw_margin": 0.11786389350891113,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.1356747950223304,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.08593392372131348,
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
        "raw_margin": 0.1347060203552246,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.13006161399894378,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.0889071524143219,
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
        "raw_margin": 0.11786389350891113,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.057507890118904365,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.042495280504226685,
        "family": "sector-wave",
        "negative_roi": -71.0984261500001,
        "negative_row_index": 412,
        "negative_signature_ids": [
          "f1dcbe243e858990c1ad5d7a97b1fcbf3dec76ba"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 411,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "raw_margin": 0.06245613098144531,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.051894709095517744,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.04546850919723511,
        "family": "sector-wave",
        "negative_roi": -72.99262605000008,
        "negative_row_index": 413,
        "negative_signature_ids": [
          "c52c024812ef68aad39a25d86a29cce7e7829619"
        ],
        "pair_pass": true,
        "positive_lower_delay_risk": true,
        "positive_roi": 1.0,
        "positive_row_index": 411,
        "positive_signature_ids": [
          "fa1849e44e561b8c63c93a1c537f3399b34ec67d"
        ],
        "raw_margin": 0.045614004135131836,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.1356747950223304,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.08593389391899109,
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
        "raw_margin": 0.1347060203552246,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.13006161399894378,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.08890712261199951,
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
        "raw_margin": 0.11786389350891113,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.09371967779635851,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.05704954266548157,
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
        "raw_margin": 0.10408592224121094,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.08810649677297189,
        "admission_positive_above_negative": true,
        "context_hash": "4e481a6307fca228",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_05_seed61410|4e481a6307fca228",
        "delay_risk_margin": 0.06002277135848999,
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
        "raw_margin": 0.08724379539489746,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.06995167936297572,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.03696632385253906,
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
        "raw_margin": 0.08762657642364502,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.1478467152278016,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.08198532462120056,
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
        "raw_margin": 0.21578308939933777,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.038673733671835575,
        "admission_positive_above_negative": true,
        "context_hash": "45baa40751a0bf77",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks020_07_seed61615|45baa40751a0bf77",
        "delay_risk_margin": 0.022650688886642456,
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
        "raw_margin": 0.039272844791412354,
        "raw_positive_above_negative": true
      },
      {
        "admission_margin": 0.034935180548153255,
        "admission_positive_above_negative": true,
        "context_hash": "5a812898b6327d87",
        "context_key": "tranquillitatis_balmer_like_20km_sector-wave_randomtw_tasks030_01_seed71001|5a812898b6327d87",
        "delay_risk_margin": 0.02833995223045349,
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
        "raw_margin": 0.046590834856033325,
        "raw_positive_above_negative": true
      }
    ],
    "production_ready": false,
    "runs_bpc_or_pricing": false,
    "summary": {
      "admission_pair_pass_count": 74,
      "admission_pair_pass_rate": 0.9487179487179487,
      "ambiguous_row_count": 0,
      "context_count": 30,
      "contexts_with_positive_and_negative": 30,
      "delay_risk_pair_pass_count": 74,
      "delay_risk_pair_pass_rate": 0.9487179487179487,
      "family_counts": {
        "greedy-anchor": 33,
        "random-wave": 47,
        "sector-wave": 22
      },
      "focused_row_count": 102,
      "label_counts": {
        "delay_or_hard_negative": 46,
        "positive_high_priority": 56
      },
      "negative_row_count": 46,
      "pair_count": 78,
      "positive_row_count": 56,
      "primary": "candidate_head_context_ranking_failure",
      "raw_pair_pass_count": 75,
      "raw_pair_pass_rate": 0.9615384615384616,
      "strict_pair_pass_count": 74,
      "strict_pair_pass_rate": 0.9487179487179487
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
      "random-wave": 308,
      "sector-wave": 283
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
      "random-wave": 113,
      "sector-wave": 55
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
    "best_local_rejected_reasons": [],
    "best_rejected_reasons": [
      "knn_ood_audit_missing"
    ],
    "candidate_count": 1,
    "feasible_threshold_count": 1,
    "selected_metrics": {
      "accepted_bad_mode_count": 0,
      "accepted_batch_count": 35,
      "accepted_batch_precision": 1.0,
      "accepted_batch_rate": 0.11986301369863013,
      "accepted_batch_roi": 19.596106808100426,
      "accepted_batch_roi_ci_low": 10.534232724832064,
      "accepted_batch_roi_over_baseline": 19.596106808100426,
      "accepted_batch_roi_over_baseline_ci_low": 10.534232724832064,
      "accepted_batch_roi_over_best_rc_baseline": 19.596106808100426,
      "accepted_batch_roi_over_best_rc_baseline_ci_low": 10.534232724832064,
      "accepted_batch_roi_over_old_gat_baseline": 19.596106808100426,
      "accepted_batch_roi_over_old_gat_baseline_ci_low": 10.534232724832064,
      "accepted_batch_roi_over_random_baseline": 19.596106808100426,
      "accepted_batch_roi_over_random_baseline_ci_low": 10.534232724832064,
      "baseline_roi_ci_high": 0.0,
      "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
      "baseline_selection_roi": 0.0,
      "batch_threshold": 0.6380712389945984,
      "batch_thresholds_by_family": {},
      "best_rc_baseline_accepted_batch_roi": 0.0,
      "candidate_admission_score_mode": "risk_adjusted_product",
      "candidate_delay_gate_blocked_count": 0,
      "candidate_delay_gate_enabled": true,
      "candidate_delay_risk_threshold": 0.6,
      "candidate_delay_score_penalty": 1.5,
      "candidate_rescue_delay_risk_threshold": 1.0,
      "candidate_rescue_delay_score_penalty": 0.0,
      "candidate_rescue_raw_score_threshold": 1.0,
      "candidate_rescue_window_eligible_count": 0,
      "candidate_rescue_window_promoted_count": 0,
      "candidate_risk_adjusted_suppressed_count": 1978,
      "candidate_score_threshold_blocked_count": 2001,
      "candidate_threshold": 0.29696329766061574,
      "checkpoint_gate_pass": false,
      "checkpoint_gate_reject_reasons": [
        "knn_ood_audit_missing"
      ],
      "context_delay_fallback_contexts": [],
      "coverage_non_ood": 1.0,
      "delay_label_count": 277,
      "delay_rate": 0.8801369863013698,
      "evaluated_candidate_count": 3084,
      "expected_trajectory_utility": 19.61182109381471,
      "false_high_priority_on_delay": 0.0036101083032490976,
      "false_high_priority_on_delay_count": 1,
      "false_safe_rate_label_unsafe": 0.0,
      "false_safe_rate_union": 0.0036101083032490976,
      "family_delay_fallback_families": [],
      "family_holdout_min_accepted_high_roi_count": 7,
      "family_holdout_min_accepted_roi": 7.117968122164409,
      "family_holdout_min_high_roi_capture_rate": 0.4117647058823529,
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
          "accepted_batch_roi": 33.91330652766757,
          "accepted_high_roi_count": 9,
          "high_roi_capture_rate": 0.45,
          "max_accepted_batch_roi_label": 106.158935546875,
          "oracle_high_roi_count": 20,
          "safe_precision": 1.0,
          "total_batches": 124
        },
        "random-wave": {
          "accepted_batch_count": 14,
          "accepted_batch_roi": 21.08774014775242,
          "accepted_high_roi_count": 12,
          "high_roi_capture_rate": 0.5454545454545454,
          "max_accepted_batch_roi_label": 79.51943969726562,
          "oracle_high_roi_count": 22,
          "safe_precision": 1.0,
          "total_batches": 113
        },
        "sector-wave": {
          "accepted_batch_count": 12,
          "accepted_batch_roi": 7.117968122164409,
          "accepted_high_roi_count": 7,
          "high_roi_capture_rate": 0.4117647058823529,
          "max_accepted_batch_roi_label": 33.70098114013672,
          "oracle_high_roi_count": 17,
          "safe_precision": 1.0,
          "total_batches": 55
        }
      },
      "family_specific_delay_fallback_families": [],
      "hard_reject_reason_categories": [
        "knn_ood_audit_missing"
      ],
      "high_priority_precision": 0.9990766389658357,
      "high_priority_precision_ci_low": 0.9947881700306493,
      "high_priority_prediction_count": 1083,
      "high_priority_true_positive_count": 1082,
      "max_accepted_bad_mode_count": 0,
      "min_family_accepted_high_roi_count": 0,
      "min_family_high_roi_capture_rate": 0.0,
      "old_gat_baseline_accepted_batch_roi": 0.0,
      "random_baseline_accepted_batch_roi": 0.0,
      "safe_precision": 1.0,
      "safe_precision_ci_low": 0.9010957324106112,
      "threshold": 0.6380712389945984,
      "threshold_local_gate_pass": true,
      "threshold_local_hard_reject_reason_categories": [],
      "threshold_local_reject_reasons": [],
      "threshold_mode": "separate_batch_candidate",
      "total_batches": 292
    }
  },
  "train_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 101,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.12242424242424242,
    "accepted_batch_roi": 7.994258592993316,
    "accepted_batch_roi_ci_low": 5.752278134236011,
    "accepted_batch_roi_over_baseline": 7.994258592993316,
    "accepted_batch_roi_over_baseline_ci_low": 5.752278134236011,
    "accepted_batch_roi_over_best_rc_baseline": 7.994258592993316,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 5.752278134236011,
    "accepted_batch_roi_over_old_gat_baseline": 7.994258592993316,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 5.752278134236011,
    "accepted_batch_roi_over_random_baseline": 7.994258592993316,
    "accepted_batch_roi_over_random_baseline_ci_low": 5.752278134236011,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.6380712389945984,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_blocked_count": 0,
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.6,
    "candidate_delay_score_penalty": 1.5,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 5771,
    "candidate_score_threshold_blocked_count": 5855,
    "candidate_threshold": 0.29696329766061574,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 991,
    "delay_rate": 0.8775757575757576,
    "evaluated_candidate_count": 9600,
    "expected_trajectory_utility": 8.018020969230939,
    "false_high_priority_on_delay": 0.0020181634712411706,
    "false_high_priority_on_delay_count": 2,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.0020181634712411706,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 10,
    "family_holdout_min_accepted_roi": 6.61730662060947,
    "family_holdout_min_high_roi_capture_rate": 0.2564102564102564,
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
        "accepted_batch_count": 13,
        "accepted_batch_roi": 7.320417262613773,
        "accepted_high_roi_count": 10,
        "high_roi_capture_rate": 0.2564102564102564,
        "max_accepted_batch_roi_label": 18.683509826660156,
        "oracle_high_roi_count": 39,
        "safe_precision": 1.0,
        "total_batches": 234
      },
      "random-wave": {
        "accepted_batch_count": 47,
        "accepted_batch_roi": 9.381811107092716,
        "accepted_high_roi_count": 33,
        "high_roi_capture_rate": 0.4230769230769231,
        "max_accepted_batch_roi_label": 67.16388702392578,
        "oracle_high_roi_count": 78,
        "safe_precision": 1.0,
        "total_batches": 308
      },
      "sector-wave": {
        "accepted_batch_count": 41,
        "accepted_batch_roi": 6.61730662060947,
        "accepted_high_roi_count": 29,
        "high_roi_capture_rate": 0.3625,
        "max_accepted_batch_roi_label": 27.36725425720215,
        "oracle_high_roi_count": 80,
        "safe_precision": 1.0,
        "total_batches": 283
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "knn_ood_audit_missing"
    ],
    "high_priority_precision": 0.9994659546061415,
    "high_priority_precision_ci_low": 0.9980547241767377,
    "high_priority_prediction_count": 3745,
    "high_priority_true_positive_count": 3743,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9633580563440465,
    "threshold": 0.6380712389945984,
    "threshold_local_gate_pass": true,
    "threshold_local_hard_reject_reason_categories": [],
    "threshold_local_reject_reasons": [],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 825
  },
  "validation_deployment_metrics": {
    "accepted_bad_mode_count": 0,
    "accepted_batch_count": 35,
    "accepted_batch_precision": 1.0,
    "accepted_batch_rate": 0.11986301369863013,
    "accepted_batch_roi": 19.596106808100426,
    "accepted_batch_roi_ci_low": 10.534232724832064,
    "accepted_batch_roi_over_baseline": 19.596106808100426,
    "accepted_batch_roi_over_baseline_ci_low": 10.534232724832064,
    "accepted_batch_roi_over_best_rc_baseline": 19.596106808100426,
    "accepted_batch_roi_over_best_rc_baseline_ci_low": 10.534232724832064,
    "accepted_batch_roi_over_old_gat_baseline": 19.596106808100426,
    "accepted_batch_roi_over_old_gat_baseline_ci_low": 10.534232724832064,
    "accepted_batch_roi_over_random_baseline": 19.596106808100426,
    "accepted_batch_roi_over_random_baseline_ci_low": 10.534232724832064,
    "baseline_roi_ci_high": 0.0,
    "baseline_roi_ci_high_source": "configured_point_estimate_no_baseline_distribution",
    "baseline_selection_roi": 0.0,
    "batch_threshold": 0.6380712389945984,
    "batch_thresholds_by_family": {},
    "best_rc_baseline_accepted_batch_roi": 0.0,
    "candidate_admission_score_mode": "risk_adjusted_product",
    "candidate_delay_gate_blocked_count": 0,
    "candidate_delay_gate_enabled": true,
    "candidate_delay_risk_threshold": 0.6,
    "candidate_delay_score_penalty": 1.5,
    "candidate_rescue_delay_risk_threshold": 1.0,
    "candidate_rescue_delay_score_penalty": 0.0,
    "candidate_rescue_raw_score_threshold": 1.0,
    "candidate_rescue_window_eligible_count": 0,
    "candidate_rescue_window_promoted_count": 0,
    "candidate_risk_adjusted_suppressed_count": 1978,
    "candidate_score_threshold_blocked_count": 2001,
    "candidate_threshold": 0.29696329766061574,
    "checkpoint_gate_pass": false,
    "checkpoint_gate_reject_reasons": [
      "knn_ood_audit_missing"
    ],
    "context_delay_fallback_contexts": [],
    "coverage_non_ood": 1.0,
    "delay_label_count": 277,
    "delay_rate": 0.8801369863013698,
    "evaluated_candidate_count": 3084,
    "expected_trajectory_utility": 19.61182109381471,
    "false_high_priority_on_delay": 0.0036101083032490976,
    "false_high_priority_on_delay_count": 1,
    "false_safe_rate_label_unsafe": 0.0,
    "false_safe_rate_union": 0.0036101083032490976,
    "family_delay_fallback_families": [],
    "family_holdout_min_accepted_high_roi_count": 7,
    "family_holdout_min_accepted_roi": 7.117968122164409,
    "family_holdout_min_high_roi_capture_rate": 0.4117647058823529,
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
        "accepted_batch_roi": 33.91330652766757,
        "accepted_high_roi_count": 9,
        "high_roi_capture_rate": 0.45,
        "max_accepted_batch_roi_label": 106.158935546875,
        "oracle_high_roi_count": 20,
        "safe_precision": 1.0,
        "total_batches": 124
      },
      "random-wave": {
        "accepted_batch_count": 14,
        "accepted_batch_roi": 21.08774014775242,
        "accepted_high_roi_count": 12,
        "high_roi_capture_rate": 0.5454545454545454,
        "max_accepted_batch_roi_label": 79.51943969726562,
        "oracle_high_roi_count": 22,
        "safe_precision": 1.0,
        "total_batches": 113
      },
      "sector-wave": {
        "accepted_batch_count": 12,
        "accepted_batch_roi": 7.117968122164409,
        "accepted_high_roi_count": 7,
        "high_roi_capture_rate": 0.4117647058823529,
        "max_accepted_batch_roi_label": 33.70098114013672,
        "oracle_high_roi_count": 17,
        "safe_precision": 1.0,
        "total_batches": 55
      }
    },
    "family_specific_delay_fallback_families": [],
    "hard_reject_reason_categories": [
      "knn_ood_audit_missing"
    ],
    "high_priority_precision": 0.9990766389658357,
    "high_priority_precision_ci_low": 0.9947881700306493,
    "high_priority_prediction_count": 1083,
    "high_priority_true_positive_count": 1082,
    "max_accepted_bad_mode_count": 0,
    "min_family_accepted_high_roi_count": 0,
    "min_family_high_roi_capture_rate": 0.0,
    "old_gat_baseline_accepted_batch_roi": 0.0,
    "random_baseline_accepted_batch_roi": 0.0,
    "safe_precision": 1.0,
    "safe_precision_ci_low": 0.9010957324106112,
    "threshold": 0.6380712389945984,
    "threshold_local_gate_pass": true,
    "threshold_local_hard_reject_reason_categories": [],
    "threshold_local_reject_reasons": [],
    "threshold_mode": "separate_batch_candidate",
    "total_batches": 292
  }
}
```

## 边界

- checkpoint selection 先看 deployment gate，再看 utility / ROI / loss；
- HIGH_PRIORITY precision、safe precision、accepted batch ROI、false-safe、accepted count 都是硬门槛；
- 当前 checkpoint 仍 `production_ready=false`；
- kNN/OOD holdout、5/10 no-regression、20-task wall-time ROI、online opt-in A/B 通过前，不能进入 Stage 4；
- DELAY_QUEUE 只能延迟 true-RC negative，不能替代 final exact pricing certificate。
