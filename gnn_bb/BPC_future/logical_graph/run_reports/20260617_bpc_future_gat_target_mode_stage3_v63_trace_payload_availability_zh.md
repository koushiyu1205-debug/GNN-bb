# 2026-06-17 BPC_future GAT Stage 3 v63 Trace Payload Availability 审计报告

## 目的

承接 v62 的 feature/schema gap 结论，检查 focused v53/v60 target 的 source capture 中是否已经存在 trace、timing、resource payload。该脚本只读 dataset manifest 和 capture JSONL，不运行 BPC / pricing / RMP / worker / certificate。

## 机器字段

```text
status = gat_batch_impact_trace_payload_availability_audited
focused_row_count = 9
source_event_found_count = 9
target_journey_found_count = 9
matched_rate = 1.0
arc_option_payload_full_count = 9
timing_payload_full_count = 9
resource_payload_full_count = 9
trace_numeric_feature_count = 22
branch_cut_event_available_count = 9
per_candidate_branch_cut_coefficients_count = 0
task_time_window_slack_count = 0
primary = trace_timing_resource_payload_available_but_not_in_model_schema
recommended_next_step = extend_batch_impact_candidate_schema_with_trace_payload_features
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## 关键结论

- focused target 匹配率：`9 / 9`。
- arc-option / timing / resource payload full counts：`9 / 9 / 9`。
- 可直接候选的 scalar trace features 数量：`22`。
- `task_time_window_slack` 和 per-candidate branch/cut coefficient 仍没有直接 payload，需要后续从 logical graph / cut evaluator 另行提取或补采集。

## Availability Rates

```json
{
  "event_branch_constraints": 0.0,
  "event_cuts": 1.0,
  "journey_end_time": 1.0,
  "journey_start_time": 1.0,
  "per_candidate_branch_cut_coefficients": 0.0,
  "sequence": 1.0,
  "signature": 1.0,
  "task_set": 1.0,
  "task_time_window_slack": 0.0,
  "trip_arc_option_ids": 1.0,
  "trip_distance": 1.0,
  "trip_end_time": 1.0,
  "trip_energy": 1.0,
  "trip_load": 1.0,
  "trip_occupancy": 1.0,
  "trip_recharge_time": 1.0,
  "trip_risk": 1.0,
  "trip_service_start": 1.0,
  "trip_start_time": 1.0,
  "trip_survival_energy": 1.0,
  "trip_travel_time": 1.0,
  "trips": 1.0
}
```

## Feature Schema Proposal

```json
{
  "available_now": {
    "arc_option_sequence": 9,
    "resource": 9,
    "timing": 9
  },
  "recommended_scalar_features": [
    "trace_arc_option_count",
    "trace_idle_time_proxy",
    "trace_inter_sortie_gap_max",
    "trace_inter_sortie_gap_sum",
    "trace_journey_duration",
    "trace_journey_end_time",
    "trace_journey_start_time",
    "trace_low_energy_arc_count",
    "trace_low_risk_arc_count",
    "trace_low_time_arc_count",
    "trace_max_load",
    "trace_min_survival_energy",
    "trace_service_start_max",
    "trace_service_start_min",
    "trace_service_start_span",
    "trace_total_distance",
    "trace_total_energy",
    "trace_total_recharge_time",
    "trace_total_risk",
    "trace_total_travel_time",
    "trace_trip_count",
    "trace_unique_arc_option_count"
  ],
  "recommended_token_features": [
    "trace_arc_option_path_type_sequence",
    "trace_arc_option_from_to_sequence"
  ],
  "requires_additional_extraction_or_instrumentation": [
    "task_time_window_slack",
    "per_candidate_branch_cut_coefficients",
    "active_basis_overlap_coefficients"
  ]
}
```

## Recommended Next Step

```json
{
  "primary": "extend_batch_impact_candidate_schema_with_trace_payload_features",
  "reason": "arc-option, timing, and resource payloads are recoverable for focused targets"
}
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_trace_payload_availability_v63_v62_individual_followup_20260617/summary.json
rows = BPC_future/results/gat_batch_impact_trace_payload_availability_v63_v62_individual_followup_20260617/trace_payload_rows.jsonl
proposal = BPC_future/results/gat_batch_impact_trace_payload_availability_v63_v62_individual_followup_20260617/candidate_trace_feature_schema_proposal.json
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
