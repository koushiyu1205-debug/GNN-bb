# GAT Branch/Action Sanity Dataset

日期：2026-06-29

## 目的

把已完成 branch counterfactual replay 转成小规模 GAT branch/action sanity dataset。该数据集只用于离线试训模型管线，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
output_dir = BPC_future/data/gat_branch_action_sanity/v792_pressure_coverage_with_delta_reason_counts
target_wall = 200.0
wall_cap = 600.0
min_wall_improvement = 30.0
min_wall_regression = 30.0
raw_row_count = 7
sample_count = 1
row_kind_counts = {'paired_probe_neutral_proxy': 6, 'paired_probe_positive_proxy': 1}
branch_priority_label_counts = {'aux_only_weak_positive': 1}
target_wall_crossing_label_counts = {'not_target_wall_crossing': 1}
tail_improved_aux_label_counts = {'tail_improved': 1}
skipped_counts = {'not_training_sample:paired_probe_neutral_proxy': 6}
instance_count = 1
family_count = 1
phase2_pressure_observed_counts = {'phase2_same_child_negative_severity': 1, 'phase2_separate_child_negative_severity': 1, 'phase2_negative_severity_sum': 1, 'phase2_negative_severity_gap': 1, 'phase2_negative_severity_balance_ratio': 1, 'phase2_negative_child_presence_balance_gap': 1}
phase2_pressure_nonzero_counts = {'phase2_same_child_negative_severity': 1, 'phase2_separate_child_negative_severity': 0, 'phase2_negative_severity_sum': 1, 'phase2_negative_severity_gap': 1, 'phase2_negative_severity_balance_ratio': 0, 'phase2_negative_child_presence_balance_gap': 1}
phase2_pressure_nonzero_sample_count = 1
phase2_pressure_coverage_ready = true
sanity_training_dataset_ready = false
serious_training_dataset_ready = false
pressure_aware_training_dataset_ready = false
optin_training_dataset_ready = false
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## 标签边界

- 主 `branch_priority` 标签使用 capped wall-time gain，不把 200 秒作为训练硬断点。
- `target_wall_crossing_positive` 只作为验收/报告字段；`199s -> 201s` 这类小变化不会成为强负例，`500s -> 300s` 会成为高权重正例。
- `weak_positive_not_target` 样本保留在数据集中；只要有足够 wall-time gain，也会进入主标签，否则仅作为 `tail_improved` 辅助标签。
- `local_only_hard_negative` 和未校准右删失 proxy 不进入主训练样本；`paired_probe_hard_negative_proxy` 只作为 proof-risk hard-negative calibration 进入，不能当 full-run 反例。
- `paired_probe_positive_proxy` 只进入 auxiliary weak-positive / proof-cost 训练头，主 wall-time gain loss 权重保持 0，不能当 full-run 正例或 production score 依据。

## Schema

```json
{
  "branch_feature_schema": [
    "depth",
    "candidate_count",
    "eligible_count",
    "has_candidate_log",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "same_mass",
    "fractionality",
    "support_count",
    "incumbent_relation_known",
    "incumbent_relation_same",
    "incumbent_disagreement",
    "pool_same_allowed",
    "pool_separate_allowed",
    "pool_max_child_width",
    "pool_total_child_width",
    "pool_balance_gap"
  ],
  "context_feature_schema": [
    "node_id",
    "depth",
    "branch_time",
    "candidate_count",
    "eligible_count",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "phased_testing_stage_code",
    "phased_testing_decision_code",
    "phased_testing_elimination_reason_code",
    "phased_testing_phase0_passed",
    "phased_testing_phase1_lp_complete",
    "phased_testing_phase2_heuristic_complete",
    "baseline_task_i",
    "baseline_task_j",
    "alternative_task_i",
    "alternative_task_j",
    "phase1_min_child_lp_gain",
    "phase1_child_lp_gain_product",
    "phase1_child_lp_gain_gap",
    "phase1_child_lp_gain_balance_ratio",
    "phase1_child_width_balance",
    "phase1_wall_time",
    "phase1_dynamic_k_probe_count",
    "phase1_cut_snapshot_complete",
    "phase1_cut_snapshot_added_total",
    "phase1_cut_snapshot_min_child_lp_gain",
    "phase1_cut_snapshot_child_lp_gain_product",
    "phase1_cut_snapshot_child_lp_gain_gap",
    "phase1_cut_snapshot_child_lp_gain_balance_ratio",
    "phase1_cut_snapshot_wall_time",
    "phase1_diagnostic_wall_time",
    "phase2_negative_child_count",
    "phase2_negative_journey_count",
    "phase2_negative_journey_balance_gap",
    "phase2_best_reduced_cost",
    "phase2_worst_negative_severity",
    "phase2_same_child_negative_severity",
    "phase2_separate_child_negative_severity",
    "phase2_negative_severity_sum",
    "phase2_negative_severity_gap",
    "phase2_negative_severity_balance_ratio",
    "phase2_negative_child_presence_balance_gap",
    "phase2_child_wall_time_balance_gap",
    "phase2_child_status_mismatch",
    "phase2_wall_time",
    "phase2_dynamic_k_probe_count",
    "cut_context_active_count",
    "cut_context_subset_row_count",
    "cut_context_fleet_lb_count",
    "cut_context_dynamic_subset_row_regime_code",
    "cut_context_dynamic_subset_row_cuts_enabled",
    "cut_context_dynamic_subset_row_cut_gate_enabled",
    "cut_context_dynamic_subset_row_min_add_depth",
    "cut_context_dynamic_subset_row_max_depth",
    "cut_context_dynamic_subset_row_gate_min_best_violation",
    "route_order_active_journey_count",
    "route_order_active_task_set_count",
    "route_order_active_route_signature_count",
    "route_order_multi_route_task_set_count",
    "route_order_conflict_count",
    "route_order_conflict_mass",
    "route_order_top_conflict_balance_ratio",
    "route_order_top_transition_count",
    "route_order_top_arc_option_count",
    "route_order_candidate_same_route_mass",
    "route_order_candidate_i_before_j_mass",
    "route_order_candidate_j_before_i_mass",
    "route_order_candidate_direction_conflict_mass",
    "route_order_candidate_direction_balance_ratio",
    "route_order_candidate_adjacent_conflict_mass",
    "route_order_candidate_adjacent_balance_ratio"
  ],
  "label_schema": [
    "y_branch_priority_walltime_gain",
    "branch_priority_loss_weight",
    "capped_wall_time_delta",
    "capped_wall_time_delta_ratio",
    "y_target_wall_crossing_positive",
    "y_strict_full_replay_positive",
    "y_weak_positive_not_target",
    "y_counterfactual_regression",
    "y_timeout_regression",
    "y_timeout_resolved",
    "y_tail_improved_aux",
    "tail_improved_loss_weight",
    "y_walltime_gain",
    "walltime_gain_loss_weight",
    "y_child_proof_cpu",
    "child_proof_cpu_loss_weight",
    "y_time_to_certificate",
    "time_to_certificate_loss_weight",
    "y_gap_improvement",
    "gap_improvement_loss_weight",
    "y_primal_improvement",
    "primal_improvement_loss_weight",
    "y_dual_bound_gain",
    "dual_bound_gain_loss_weight",
    "y_fathom_gain",
    "fathom_gain_loss_weight",
    "y_branch_count_delta",
    "branch_count_delta_loss_weight",
    "y_completion_bound_retry_gain",
    "completion_bound_retry_gain_loss_weight"
  ]
}
```
