# 2026-06-23 BPC_future GAT Stage 3 v141 Feature/Structure Gap 审计报告

## 目的

量化当前 candidate input 的可分性和欠指定问题：固定本轮 focused pair rows，比较同一 context 内 positive target 和 hard-negative target 在当前模型可见输入上的差异，并检查哪些 action-consequence 信息仍只有粗粒度标量或 metadata。

该脚本只读 batch-impact dataset 和 focused pair rows，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
status = gat_batch_impact_feature_structure_gap_audited
focused_row_count = 1116
context_count = 546
positive_row_count = 824
negative_row_count = 292
pair_count = 249
ranking_pair_available_count = 78
raw_ranking_failure_pair_count = 3
model_visible_difference_pair_count = 200
model_input_collision_pair_count = 49
constant_candidate_feature_count = 13
critical_missing_feature_category_count = 1
primary = candidate_input_under_specified_for_action_consequence
recommended_next_step = add_selected_arc_option_sequence_or_targeted_context_pair_comparator_then_retrain
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- 当前 candidate feature dim = `59`，context dim = `26`，batch dim = `18`。
- focused rows 中常数 candidate features：`strict_replacement_by_cost, duplicate_signature, duplicate_signature_pool_count_before, order_observed, best_position, active_basis_signature_duplicate_count_before, forbidden_signature_duplicate_count_before, branch_constraint_touch_count, branch_constraint_violation_count, branch_same_vehicle_pair_partial_count, branch_separate_vehicle_pair_violation_count, candidate_cut_fleet_coeff_count, candidate_cut_dual_abs_weighted_coeff_sum`。
- critical missing / under-specified categories：`selected_arc_option_sequence`。
- pair gap class counts：`{"coarse_input_visibility_without_model_score_pair": 124, "coarse_input_visible_and_raw_ranking_passes": 73, "coarse_input_visible_but_candidate_head_misranks": 3, "model_input_collision": 49}`。

解释：focused 正负 target 在 task set / sequence position / scalar features 上通常不是完全碰撞；当前 raw ranking 仍有失败，说明问题已经从“完全不可见”转为“可见标量不足以稳定排序”。selected arc-option identity/sequence 仍是粗粒度计数，下一步不应继续只调 threshold / delay penalty。

## Feature Category Coverage

```json
[
  {
    "category": "reduced_cost_and_cost",
    "evidence_fields": [
      "cost",
      "true_reduced_cost"
    ],
    "model_input": true,
    "note": "Candidate input includes true RC and cost scalars.",
    "status": "present"
  },
  {
    "category": "task_set_and_coarse_order",
    "evidence_fields": [
      "candidate_task_membership",
      "candidate_sequence_positions",
      "sequence_length",
      "sortie_count"
    ],
    "model_input": true,
    "note": "Model input sees covered tasks and coarse task order positions.",
    "status": "present"
  },
  {
    "category": "signature_identity",
    "evidence_fields": [
      "candidate_signature_ids"
    ],
    "model_input": false,
    "note": "Signature ids are stored in sample metadata but are not a model input.",
    "status": "metadata_only"
  },
  {
    "category": "selected_arc_option_sequence",
    "evidence_fields": [
      "trace_arc_option_count",
      "trace_unique_arc_option_count",
      "trace_low_time_arc_count",
      "trace_low_energy_arc_count",
      "trace_low_risk_arc_count"
    ],
    "model_input": true,
    "note": "Candidate input has arc/path aggregate counts, but not the selected arc-option identity sequence.",
    "status": "aggregate_counts_only"
  },
  {
    "category": "start_time_and_sortie_timing",
    "evidence_fields": [
      "trace_low_time_arc_count",
      "trace_journey_start_time",
      "trace_journey_end_time",
      "trace_journey_duration",
      "trace_total_travel_time",
      "trace_total_recharge_time",
      "trace_service_start_min",
      "trace_service_start_max",
      "trace_service_start_span",
      "trace_inter_sortie_gap_sum",
      "trace_inter_sortie_gap_max",
      "trace_idle_time_proxy",
      "slack_min_late_time",
      "slack_mean_late_time",
      "slack_min_early_time"
    ],
    "model_input": true,
    "note": "Candidate input has scalar timing summaries; it still lacks per-sortie timing sequence structure.",
    "status": "scalar_present"
  },
  {
    "category": "resource_and_window_slack",
    "evidence_fields": [
      "trace_low_energy_arc_count",
      "trace_total_energy",
      "trace_max_load",
      "trace_min_survival_energy",
      "slack_min_late_time",
      "slack_mean_late_time",
      "slack_min_early_time"
    ],
    "model_input": true,
    "note": "Candidate input has scalar energy/load/slack summaries; it still lacks per-arc slack structure.",
    "status": "scalar_present"
  },
  {
    "category": "active_basis_overlap_detail",
    "evidence_fields": [
      "new_task_set",
      "task_set_pool_count_before",
      "weak_replacement_or_duplicate"
    ],
    "model_input": true,
    "note": "Only task-set pool overlap proxies are present; active basis coefficient overlap is absent.",
    "status": "coarse_only"
  },
  {
    "category": "branch_cut_per_candidate_interaction",
    "evidence_fields": [
      "branch_constraint_touch_count",
      "branch_constraint_violation_count",
      "branch_same_vehicle_pair_partial_count",
      "branch_separate_vehicle_pair_violation_count",
      "candidate_cut_coeff_l1_sum",
      "candidate_cut_dual_abs_weighted_coeff_sum",
      "candidate_cut_fleet_coeff_count",
      "candidate_cut_subset_row_coeff_sum"
    ],
    "model_input": true,
    "note": "Candidate input has branch/cut scalar interaction features when listed; coefficient sequence/detail remains absent.",
    "status": "candidate_scalar_present"
  },
  {
    "category": "trajectory_tail_proxy",
    "evidence_fields": [
      "final_judge_retry_count",
      "hidden_negative_count",
      "pricing_tail_retry_count_before"
    ],
    "model_input": true,
    "note": "Tail state is present only as context aggregate, not as a candidate consequence feature.",
    "status": "aggregate_context_only"
  },
  {
    "category": "batch_composition",
    "evidence_fields": [
      "best_true_reduced_cost",
      "negative_candidate_count",
      "returned_journey_count"
    ],
    "model_input": true,
    "note": "Batch-level composition scalars are present.",
    "status": "present"
  }
]
```

## Constant Candidate Features

```json
{
  "active_basis_signature_duplicate_count_before": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "best_position": {
    "constant": true,
    "count": 1116,
    "max": 1.0,
    "mean": 1.0,
    "min": 1.0,
    "unique_count": 1,
    "unique_values": [
      1.0
    ]
  },
  "branch_constraint_touch_count": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "branch_constraint_violation_count": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "branch_same_vehicle_pair_partial_count": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "branch_separate_vehicle_pair_violation_count": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "candidate_cut_dual_abs_weighted_coeff_sum": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "candidate_cut_fleet_coeff_count": {
    "constant": true,
    "count": 1116,
    "max": 1.0,
    "mean": 1.0,
    "min": 1.0,
    "unique_count": 1,
    "unique_values": [
      1.0
    ]
  },
  "duplicate_signature": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "duplicate_signature_pool_count_before": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "forbidden_signature_duplicate_count_before": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  },
  "order_observed": {
    "constant": true,
    "count": 1116,
    "max": 1.0,
    "mean": 1.0,
    "min": 1.0,
    "unique_count": 1,
    "unique_values": [
      1.0
    ]
  },
  "strict_replacement_by_cost": {
    "constant": true,
    "count": 1116,
    "max": 0.0,
    "mean": 0.0,
    "min": 0.0,
    "unique_count": 1,
    "unique_values": [
      0.0
    ]
  }
}
```

## Recommended Next Step

```json
{
  "primary": "add_selected_arc_option_sequence_or_targeted_context_pair_comparator_then_retrain",
  "reason": "focused positive-negative pairs differ in visible scalar inputs, but raw ranking still fails while selected arc-option identity/sequence remains only coarsely represented"
}
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_feature_structure_gap_v141_v140_remaining_20260623/summary.json
rows = BPC_future/results/gat_batch_impact_feature_structure_gap_v141_v140_remaining_20260623/focused_candidate_input_rows.jsonl
pairs = BPC_future/results/gat_batch_impact_feature_structure_gap_v141_v140_remaining_20260623/pair_feature_gap_rows.jsonl
candidate_feature_summary = BPC_future/results/gat_batch_impact_feature_structure_gap_v141_v140_remaining_20260623/candidate_feature_summary.json
feature_category_coverage = BPC_future/results/gat_batch_impact_feature_structure_gap_v141_v140_remaining_20260623/feature_category_coverage.json
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
