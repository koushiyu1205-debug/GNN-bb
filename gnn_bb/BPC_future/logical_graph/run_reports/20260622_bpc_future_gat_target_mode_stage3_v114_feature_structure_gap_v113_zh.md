# 2026-06-17 BPC_future GAT Stage 3 v62 Feature/Structure Gap 审计报告

## 目的

量化 v61 提出的 candidate input 欠指定问题：固定 v53/v60 focused rows，比较同一 context 内 positive target 和 hard-negative target 在当前模型可见输入上的差异，并检查哪些 action-consequence 信息只在 metadata/log 或完全缺失。

该脚本只读 batch-impact dataset 和 v60 pair rows，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
status = gat_batch_impact_feature_structure_gap_audited
focused_row_count = 838
context_count = 384
positive_row_count = 600
negative_row_count = 238
pair_count = 421
ranking_pair_available_count = 317
raw_ranking_failure_pair_count = 85
model_visible_difference_pair_count = 330
model_input_collision_pair_count = 91
constant_candidate_feature_count = 5
critical_missing_feature_category_count = 4
primary = candidate_input_under_specified_for_action_consequence
recommended_next_step = add_trace_timing_slack_and_candidate_interaction_features_then_retrain
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- 当前 candidate feature dim = `40`，context dim = `26`，batch dim = `18`。
- focused rows 中常数 candidate features：`strict_replacement_by_cost, duplicate_signature, duplicate_signature_pool_count_before, order_observed, best_position`。
- critical missing / under-specified categories：`selected_arc_option_sequence, start_time_and_sortie_timing, resource_and_window_slack, branch_cut_per_candidate_interaction`。
- pair gap class counts：`{"coarse_input_visibility_without_model_score_pair": 80, "coarse_input_visible_and_raw_ranking_passes": 201, "coarse_input_visible_but_candidate_head_misranks": 49, "model_input_collision": 91}`。

解释：focused 正负 target 在 task set / sequence position / scalar features 上通常不是完全碰撞；但 v60 raw ranking 仍有失败，同时 path-option、timing、slack、branch/cut per-candidate interaction 等 action-consequence 特征缺失。因此下一步不应继续只调 threshold / delay penalty。

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
    "model_input": false,
    "note": "No selected path-option / arc-option sequence feature is present per candidate.",
    "status": "missing"
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
    "model_input": false,
    "note": "No start-time, per-sortie timing, or inter-sortie gap feature is present.",
    "status": "missing"
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
    "model_input": false,
    "note": "No energy, load, or time-window slack feature is present.",
    "status": "missing"
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
      "branch_constraint_count",
      "cut_dual_l1_norm"
    ],
    "model_input": true,
    "note": "Branch/cut counts are context aggregates; per-candidate cut coefficients are absent.",
    "status": "aggregate_context_only"
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
  "best_position": {
    "constant": true,
    "count": 838,
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
    "count": 838,
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
    "count": 838,
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
    "count": 838,
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
    "count": 838,
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
  "primary": "add_trace_timing_slack_and_candidate_interaction_features_then_retrain",
  "reason": "focused positive-negative pairs differ in coarse inputs but raw ranking still fails while critical action-consequence categories are absent"
}
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_feature_structure_gap_v114_v113_5000_20260622/summary.json
rows = BPC_future/results/gat_batch_impact_feature_structure_gap_v114_v113_5000_20260622/focused_candidate_input_rows.jsonl
pairs = BPC_future/results/gat_batch_impact_feature_structure_gap_v114_v113_5000_20260622/pair_feature_gap_rows.jsonl
candidate_feature_summary = BPC_future/results/gat_batch_impact_feature_structure_gap_v114_v113_5000_20260622/candidate_feature_summary.json
feature_category_coverage = BPC_future/results/gat_batch_impact_feature_structure_gap_v114_v113_5000_20260622/feature_category_coverage.json
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
