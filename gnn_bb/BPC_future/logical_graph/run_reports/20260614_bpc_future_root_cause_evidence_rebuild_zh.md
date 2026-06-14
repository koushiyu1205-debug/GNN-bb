# Root Cause Evidence Rebuild 报告

日期：2026-06-14

## 目的

本报告记录根因证据包 rebuild 结果。该 rebuild 只运行诊断聚合脚本和
verifier，不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
root_cause_evidence_rebuild = current
diagnostic_only = true
runs_bpc_or_pricing = false
command_count = 108
all_commands_pass = true
final_ledger_all_checks_pass = true
final_goal_complete = false
final_completion_decision = keep_goal_active
all_checks_pass = true
```

## 命令

### 1

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_counterexample_catalog.py
returncode = 0
```

### 2

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_production_selector_blocker_catalog.py
returncode = 0
```

### 3

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_failure_mechanism_audit.py
returncode = 0
```

### 4

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_context_feature_gap_audit.py
returncode = 0
```

### 5

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_feature_availability_audit.py
returncode = 0
```

### 6

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_capture_schema_feasibility_audit.py
returncode = 0
```

### 7

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_remaining_rmp_trajectory_field_recovery.py
returncode = 0
```

### 8

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_active_basis_observability_gap.py
returncode = 0
```

### 9

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_active_basis_capture_schema_feasibility.py
returncode = 0
```

### 10

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_enriched_rmp_feature_holdout.py
returncode = 0
```

### 11

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_enriched_multifeature_model_holdout.py
returncode = 0
```

### 12

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_production_ab_entry_gate_catalog.py
returncode = 0
```

### 13

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_objective_completion_audit.py
returncode = 0
```

### 14

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_next_evidence_protocol_catalog.py
returncode = 0
```

### 15

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_root_cause_failure_matrix.py
returncode = 0
```

### 16

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_optimization_direction_candidate_registry.py
returncode = 0
```

### 17

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_component_feature_readiness.py
returncode = 0
```

### 18

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_component_capture_schema_contract.py
returncode = 0
```

### 19

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_component_payload_addition_before_rows.py
returncode = 0
```

### 20

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_component_payload_selector_holdout_extension.py
returncode = 0
```

### 21

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_context_sufficiency_gap.py
returncode = 0
```

### 22

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_pool_overlap_feature_probe.py
returncode = 0
```

### 23

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_next_feature_gate.py
returncode = 0
```

### 24

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_context_schema_gap.py
returncode = 0
```

### 25

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_snapshot_sample_coverage.py
returncode = 0
```

### 26

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_gap_matrix.py
returncode = 0
```

### 27

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target_priority_matrix.py
returncode = 0
```

### 28

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_priority_collection_runbook.py
returncode = 0
```

### 29

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_priority_collection_capture.py
returncode = 0
```

### 30

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_priority_capture_miss.py
returncode = 0
```

### 31

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_context_trajectory_capture_protocol.py
returncode = 0
```

### 32

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_context_worklist.py
returncode = 0
```

### 33

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_context_action_plan.py
returncode = 0
```

### 34

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_selector_collection_plan.py
returncode = 0
```

### 35

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_collection_schema_coverage.py
returncode = 0
```

### 36

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_collection_manifest.py
returncode = 0
```

### 37

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_collection_runbook.py
returncode = 0
```

### 38

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_collection_capture.py
returncode = 0
```

### 39

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_blocker_status.py
returncode = 0
```

### 40

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_worker_negative_column_roi_blocker.py
returncode = 0
```

### 41

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_why_many_attempts_failed_report.py
returncode = 0
```

### 42

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_causal_chain_audit.py
returncode = 0
```

### 43

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_current_answer.py
returncode = 0
```

### 44

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_next_action_plan.py
returncode = 0
```

### 45

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_root_cause_document_consistency.py
returncode = 0
```

### 46

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_direction_readiness_matrix.py
returncode = 0
```

### 47

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target002_drift.py
returncode = 0
```

### 48

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target002_probe_matrix.py
returncode = 0
```

### 49

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target002_trajectory_branch.py
returncode = 0
```

### 50

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_missing_context_diagnosis.py
returncode = 0
```

### 51

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target002_component_drift.py
returncode = 0
```

### 52

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_root_cause_stale_claims.py
returncode = 0
```

### 53

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_root_cause_missing_requirement_evidence_scan.py
returncode = 0
```

### 54

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_evidence_bundle_manifest.py
returncode = 0
```

### 55

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/verify_root_cause_evidence.py --output-dir BPC_future/results/root_cause_evidence_ledger_20260613
returncode = 0
```

### 56

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_failure_mechanism_audit.py
returncode = 0
```

### 57

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_context_feature_gap_audit.py
returncode = 0
```

### 58

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_feature_availability_audit.py
returncode = 0
```

### 59

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_capture_schema_feasibility_audit.py
returncode = 0
```

### 60

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_remaining_rmp_trajectory_field_recovery.py
returncode = 0
```

### 61

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_active_basis_observability_gap.py
returncode = 0
```

### 62

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_active_basis_capture_schema_feasibility.py
returncode = 0
```

### 63

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_enriched_rmp_feature_holdout.py
returncode = 0
```

### 64

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_enriched_multifeature_model_holdout.py
returncode = 0
```

### 65

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_production_ab_entry_gate_catalog.py
returncode = 0
```

### 66

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_objective_completion_audit.py
returncode = 0
```

### 67

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_next_evidence_protocol_catalog.py
returncode = 0
```

### 68

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_root_cause_failure_matrix.py
returncode = 0
```

### 69

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_optimization_direction_candidate_registry.py
returncode = 0
```

### 70

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_component_feature_readiness.py
returncode = 0
```

### 71

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_component_capture_schema_contract.py
returncode = 0
```

### 72

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_component_payload_addition_before_rows.py
returncode = 0
```

### 73

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_component_payload_selector_holdout_extension.py
returncode = 0
```

### 74

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_context_sufficiency_gap.py
returncode = 0
```

### 75

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_pool_overlap_feature_probe.py
returncode = 0
```

### 76

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_next_feature_gate.py
returncode = 0
```

### 77

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_context_schema_gap.py
returncode = 0
```

### 78

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_snapshot_sample_coverage.py
returncode = 0
```

### 79

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_gap_matrix.py
returncode = 0
```

### 80

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target_priority_matrix.py
returncode = 0
```

### 81

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_priority_collection_runbook.py
returncode = 0
```

### 82

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_priority_collection_capture.py
returncode = 0
```

### 83

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_priority_capture_miss.py
returncode = 0
```

### 84

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_context_trajectory_capture_protocol.py
returncode = 0
```

### 85

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_context_worklist.py
returncode = 0
```

### 86

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_context_action_plan.py
returncode = 0
```

### 87

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_selector_collection_plan.py
returncode = 0
```

### 88

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_collection_schema_coverage.py
returncode = 0
```

### 89

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_collection_manifest.py
returncode = 0
```

### 90

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_selector_holdout_collection_runbook.py
returncode = 0
```

### 91

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_collection_capture.py
returncode = 0
```

### 92

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_blocker_status.py
returncode = 0
```

### 93

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_worker_negative_column_roi_blocker.py
returncode = 0
```

### 94

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_why_many_attempts_failed_report.py
returncode = 0
```

### 95

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_causal_chain_audit.py
returncode = 0
```

### 96

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_current_answer.py
returncode = 0
```

### 97

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_next_action_plan.py
returncode = 0
```

### 98

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_root_cause_document_consistency.py
returncode = 0
```

### 99

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_direction_readiness_matrix.py
returncode = 0
```

### 100

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target002_drift.py
returncode = 0
```

### 101

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target002_probe_matrix.py
returncode = 0
```

### 102

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target002_trajectory_branch.py
returncode = 0
```

### 103

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_missing_context_diagnosis.py
returncode = 0
```

### 104

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_selector_holdout_target002_component_drift.py
returncode = 0
```

### 105

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_root_cause_stale_claims.py
returncode = 0
```

### 106

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_root_cause_missing_requirement_evidence_scan.py
returncode = 0
```

### 107

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/build_root_cause_evidence_bundle_manifest.py
returncode = 0
```

### 108

```text
/home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/verify_root_cause_evidence.py --output-dir BPC_future/results/root_cause_evidence_ledger_20260613
returncode = 0
```
