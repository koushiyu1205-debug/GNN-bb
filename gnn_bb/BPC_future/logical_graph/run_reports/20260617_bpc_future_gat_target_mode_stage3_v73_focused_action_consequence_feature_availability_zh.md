# GAT Batch Impact Action-consequence Feature Availability 审计报告

日期：2026-06-17

## 目的

审计 v72 之后建议补入的 action-consequence 特征是否能从现有 batch-impact rows 和 replay capture 中稳定恢复。该脚本只读已有 dataset / capture / logical graph，不运行 BPC、pricing、RMP、worker 或 certificate。

## 机器字段

```text
gat_batch_impact_action_consequence_feature_availability = current
status = gat_batch_impact_action_consequence_feature_availability_audited
audited_sample_count = 9
audited_candidate_count = 9
arc_token_sequence_coverage = 1.0
parseable_arc_token_coverage = 1.0
time_window_slack_coverage = 1.0
resource_slack_coverage = 1.0
pool_overlap_proxy_coverage = 1.0
active_basis_direct_payload_coverage = 1.0
branch_payload_coverage = 1.0
cut_payload_coverage = 0.0
unique_arc_option_token_count = 37
unique_arc_option_pair_count = 34
unique_arc_option_type_values = ['low_energy', 'low_risk', 'low_time']
primary = per_candidate_cut_interaction_payload_missing
recommended_next_step = add_arc_token_sequence_and_slack_features_then_retrain
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## Recommended Next Step

```json
{
  "primary": "add_arc_token_sequence_and_slack_features_then_retrain",
  "reason": "path_token_and_time_window_slack_payloads_are_available"
}
```

## Summary

```json
{
  "active_basis_direct_payload_candidate_count": 9,
  "active_basis_direct_payload_coverage": 1.0,
  "arc_token_sequence_candidate_count": 9,
  "arc_token_sequence_coverage": 1.0,
  "branch_payload_candidate_count": 9,
  "branch_payload_coverage": 1.0,
  "candidate_count": 9,
  "candidate_cut_coefficients_count": 0,
  "cut_payload_candidate_count": 0,
  "cut_payload_coverage": 0.0,
  "min_survival_energy_min": 1.62811,
  "min_time_window_late_slack_min": 20.004786976562514,
  "occupancy_payload_candidate_count": 9,
  "occupancy_payload_coverage": 1.0,
  "parseable_arc_token_candidate_count": 9,
  "parseable_arc_token_coverage": 1.0,
  "pool_overlap_proxy_candidate_count": 9,
  "pool_overlap_proxy_coverage": 1.0,
  "primary": "per_candidate_cut_interaction_payload_missing",
  "resource_slack_candidate_count": 9,
  "resource_slack_coverage": 1.0,
  "sample_count": 9,
  "signature_in_pool_count": 0,
  "task_set_in_pool_count": 1,
  "time_window_slack_candidate_count": 9,
  "time_window_slack_coverage": 1.0,
  "unique_arc_option_pair_count": 34,
  "unique_arc_option_token_count": 37,
  "unique_arc_option_type_count": 3,
  "unique_arc_option_type_values": [
    "low_energy",
    "low_risk",
    "low_time"
  ]
}
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_action_consequence_feature_availability_v73_focus_v66_20260617/summary.json
candidate_rows = BPC_future/results/gat_batch_impact_action_consequence_feature_availability_v73_focus_v66_20260617/candidate_action_consequence_rows.jsonl
sample_rows = BPC_future/results/gat_batch_impact_action_consequence_feature_availability_v73_focus_v66_20260617/sample_action_consequence_rows.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
