# Root Cause Selector Collection Schema Coverage 报告

日期：2026-06-14

## 目的

本报告检查 selector 补采计划要求的字段，在当前 active-basis snapshot
反例行和源 JSONL capture event 中是否可得。它只读已有 CSV/JSONL/summary，
不运行 BPC / pricing / RMP / Pulse，也不改变 worker、certificate 或 solver
默认行为。

## 机器字段

```text
root_cause_selector_collection_schema_coverage = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_collection_schema_covered_for_current_rows
current_stage = calibration_only_selector_holdout
production_direction_proven = false
input_path_count = 5
row_count = 14
csv_missing_count = 0
event_missing_count = 0
journey_missing_count = 0
incomplete_journey_count = 0
official_effect_event_bad_count = 0
all_checks_pass = true
```

## 覆盖结论

当前 active-basis snapshot 反例行已经覆盖 selector 补采计划所需的行内字段；returned_journeys、signature 和 TimedTrip/JourneyColumn materialization payload 可从同一 context 的 no-certificate-effect JSONL capture event 中恢复。该结论只支持 calibration-only selector 数据准备，不证明 production selector、5/10 no-regression 或 20-task speedup。

## 字段来源

### CSV 行内字段

- `context_hash`
- `instance`
- `task_count`
- `cg_iter`
- `task_set`
- `sequence`
- `true_reduced_cost`
- `active_basis_churn_count_before`
- `rmp_degeneracy_pressure_before`
- `control_objective`
- `column_pool_size_before`
- `single_impact_class`
- `single_objective_delta`
- `source_file`

### JSONL capture event 字段

- `true_dual_hash`
- `returned_journeys`

### returned JourneyColumn payload 字段

- `signature`
- `task_set`
- `sequence`
- `true_reduced_cost`
- `trips`

### TimedTrip payload 字段

- `tasks`
- `start_time`
- `end_time`
- `arc_option_ids`
- `service_start`
- `occupancy`

## Dataset summary no-certificate-effect 检查

```json
[
  {
    "all_checks_pass": true,
    "audit_summary_path": "BPC_future/results/root_cause_active_basis_snapshot_smoke_audit_20260614/summary.json",
    "exists": true,
    "impact_candidate_row_count": 2,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_smoke_20260614/impact/candidate_impact_rows.csv",
    "official_effect_count": 0
  },
  {
    "all_checks_pass": true,
    "audit_summary_path": "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_audit_20260614/summary.json",
    "exists": true,
    "impact_candidate_row_count": 2,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_20260614/impact/candidate_impact_rows.csv",
    "official_effect_count": 0
  },
  {
    "all_checks_pass": true,
    "audit_summary_path": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_audit_20260614/summary.json",
    "exists": true,
    "impact_candidate_row_count": 4,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/impact/candidate_impact_rows.csv",
    "official_effect_count": 0
  },
  {
    "all_checks_pass": true,
    "audit_summary_path": "BPC_future/results/root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_audit_20260614/summary.json",
    "exists": true,
    "impact_candidate_row_count": 2,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_greedy_apollo20_02_smoke_20260614/impact/candidate_impact_rows.csv",
    "official_effect_count": 0
  },
  {
    "all_checks_pass": true,
    "audit_summary_path": "BPC_future/results/root_cause_active_basis_snapshot_greedy20_pair_smoke_audit_20260614/summary.json",
    "exists": true,
    "impact_candidate_row_count": 4,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_greedy20_pair_smoke_20260614/impact/candidate_impact_rows.csv",
    "official_effect_count": 0
  }
]
```

## 行级样例

```json
[
  {
    "cg_iter": "1",
    "context_hash": "c3b3d298e984b9d9",
    "event_count_for_context": 1,
    "event_no_certificate_effect": true,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_smoke_20260614/impact/candidate_impact_rows.csv",
    "instance": "very_small",
    "journey_payload_complete": true,
    "matching_journey_found": true,
    "missing_csv_fields": [],
    "missing_event_fields": [],
    "sequence": "3-4",
    "signature_present": true,
    "single_impact_class": "improved",
    "source_exists": true,
    "source_file": "BPC_future/results/root_cause_active_basis_snapshot_smoke_20260614/logs/very_small__baseline.jsonl",
    "task_count": "4",
    "task_set": "3,4",
    "true_dual_hash_present": true,
    "true_reduced_cost": "-7.631622"
  },
  {
    "cg_iter": "2",
    "context_hash": "1b95888aae8dd7c2",
    "event_count_for_context": 1,
    "event_no_certificate_effect": true,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_smoke_20260614/impact/candidate_impact_rows.csv",
    "instance": "very_small",
    "journey_payload_complete": true,
    "matching_journey_found": true,
    "missing_csv_fields": [],
    "missing_event_fields": [],
    "sequence": "1-4",
    "signature_present": true,
    "single_impact_class": "noop",
    "source_exists": true,
    "source_file": "BPC_future/results/root_cause_active_basis_snapshot_smoke_20260614/logs/very_small__baseline.jsonl",
    "task_count": "4",
    "task_set": "1,4",
    "true_dual_hash_present": true,
    "true_reduced_cost": "-5.20414"
  },
  {
    "cg_iter": "1",
    "context_hash": "080a188d2484ee3e",
    "event_count_for_context": 1,
    "event_no_certificate_effect": true,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_20260614/impact/candidate_impact_rows.csv",
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "journey_payload_complete": true,
    "matching_journey_found": true,
    "missing_csv_fields": [],
    "missing_event_fields": [],
    "sequence": "8-15-5",
    "signature_present": true,
    "single_impact_class": "improved",
    "source_exists": true,
    "source_file": "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_20260614/logs/mt20_greedy_apollo_01__baseline.jsonl",
    "task_count": "20",
    "task_set": "5,8,15",
    "true_dual_hash_present": true,
    "true_reduced_cost": "-139.913748"
  },
  {
    "cg_iter": "2",
    "context_hash": "e55ea3e7d277b6d1",
    "event_count_for_context": 1,
    "event_no_certificate_effect": true,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_20260614/impact/candidate_impact_rows.csv",
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "journey_payload_complete": true,
    "matching_journey_found": true,
    "missing_csv_fields": [],
    "missing_event_fields": [],
    "sequence": "12-18-5",
    "signature_present": true,
    "single_impact_class": "noop",
    "source_exists": true,
    "source_file": "BPC_future/results/root_cause_active_basis_snapshot_mt20_smoke_20260614/logs/mt20_greedy_apollo_01__baseline.jsonl",
    "task_count": "20",
    "task_set": "5,12,18",
    "true_dual_hash_present": true,
    "true_reduced_cost": "-128.547499"
  },
  {
    "cg_iter": "1",
    "context_hash": "8c60fac6ce5f475f",
    "event_count_for_context": 1,
    "event_no_certificate_effect": true,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/impact/candidate_impact_rows.csv",
    "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "journey_payload_complete": true,
    "matching_journey_found": true,
    "missing_csv_fields": [],
    "missing_event_fields": [],
    "sequence": "10-13-8",
    "signature_present": true,
    "single_impact_class": "improved",
    "source_exists": true,
    "source_file": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/logs/mt20_greedy_tranq_01__baseline.jsonl",
    "task_count": "20",
    "task_set": "8,10,13",
    "true_dual_hash_present": true,
    "true_reduced_cost": "-38.7838905"
  },
  {
    "cg_iter": "2",
    "context_hash": "f67cf0852ea7df8b",
    "event_count_for_context": 1,
    "event_no_certificate_effect": true,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/impact/candidate_impact_rows.csv",
    "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "journey_payload_complete": true,
    "matching_journey_found": true,
    "missing_csv_fields": [],
    "missing_event_fields": [],
    "sequence": "2-7-9",
    "signature_present": true,
    "single_impact_class": "improved",
    "source_exists": true,
    "source_file": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/logs/mt20_greedy_tranq_01__baseline.jsonl",
    "task_count": "20",
    "task_set": "2,7,9",
    "true_dual_hash_present": true,
    "true_reduced_cost": "-32.5008455"
  },
  {
    "cg_iter": "1",
    "context_hash": "c30ee076e24e6460",
    "event_count_for_context": 1,
    "event_no_certificate_effect": true,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/impact/candidate_impact_rows.csv",
    "instance": "tranquillitatis_balmer_like_20km_tasks20_01_seed21000",
    "journey_payload_complete": true,
    "matching_journey_found": true,
    "missing_csv_fields": [],
    "missing_event_fields": [],
    "sequence": "20-15-5",
    "signature_present": true,
    "single_impact_class": "improved",
    "source_exists": true,
    "source_file": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/logs/tranq20_01__baseline.jsonl",
    "task_count": "20",
    "task_set": "5,15,20",
    "true_dual_hash_present": true,
    "true_reduced_cost": "-57.0891735"
  },
  {
    "cg_iter": "2",
    "context_hash": "8f9a20ae99268746",
    "event_count_for_context": 1,
    "event_no_certificate_effect": true,
    "input_path": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/impact/candidate_impact_rows.csv",
    "instance": "tranquillitatis_balmer_like_20km_tasks20_01_seed21000",
    "journey_payload_complete": true,
    "matching_journey_found": true,
    "missing_csv_fields": [],
    "missing_event_fields": [],
    "sequence": "18-13-4",
    "signature_present": true,
    "single_impact_class": "improved",
    "source_exists": true,
    "source_file": "BPC_future/results/root_cause_active_basis_snapshot_multi20_smoke_20260614/logs/tranq20_01__baseline.jsonl",
    "task_count": "20",
    "task_set": "4,13,18",
    "true_dual_hash_present": true,
    "true_reduced_cost": "-53.518311"
  }
]
```

## 检查项

```json
{
  "all_capture_events_have_required_fields": true,
  "all_capture_events_no_certificate_effect": true,
  "all_matching_journeys_have_complete_payload": true,
  "all_rows_have_context_capture_event": true,
  "all_rows_have_matching_returned_journey": true,
  "all_rows_have_returned_payload": true,
  "all_rows_have_signature_payload": true,
  "all_rows_have_true_dual_hash": true,
  "all_source_files_exist": true,
  "all_trip_payloads_have_materialization_fields": true,
  "audit_summaries_exist": true,
  "audit_summaries_official_effect_zero": true,
  "collection_plan_exists": true,
  "collection_plan_passed": true,
  "counterexamples_exists": true,
  "counterexamples_passed": true,
  "csv_required_fields_present": true,
  "has_input_paths": true,
  "has_rows": true,
  "planned_fields_match_expected": true
}
```
