# Root Cause Selector Holdout Priority Collection Capture Audit 报告

日期：2026-06-14

## 目的

本报告审计 selector holdout collection runbook 的实际采集输出。它只读
 JSONL/summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker、
certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_holdout_priority_collection_capture_audit = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_collection_capture_audited
command_count = 1
capture_event_count = 12
expected_context_hash_count = 3
expected_context_hit_count = 0
all_expected_contexts_hit = false
all_expected_contexts_have_complete_snapshot = false
ready_for_selector_holdout = false
no_certificate_bad_count = 0
active_basis_bad_count = 0
all_checks_pass = true
```

## 结论

该审计只检查已执行 runbook 的 capture 输出是否满足 no-certificate-effect active-basis snapshot 采集契约。如果 expected context 未全部命中，则还不能进入 selector holdout，但这不是 official solver 结果变化。

## Command summaries

```json
[
  {
    "active_basis_bad_count": 0,
    "capture_event_count": 12,
    "command_id": "selector_priority_capture_001",
    "complete_hit_context_hashes": [],
    "expected_context_hashes": [
      "46e7a2883459d4fb",
      "794ecbd6fefaa1d7",
      "c27d904416342f6b"
    ],
    "hit_context_hashes": [],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "log_count": 3,
    "missing_complete_context_hashes": [
      "46e7a2883459d4fb",
      "794ecbd6fefaa1d7",
      "c27d904416342f6b"
    ],
    "missing_context_hashes": [
      "46e7a2883459d4fb",
      "794ecbd6fefaa1d7",
      "c27d904416342f6b"
    ],
    "no_certificate_bad_count": 0,
    "output_dir": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8",
    "output_exists": true,
    "profile": "experimental_early_new_task_set_quota_3_20_only",
    "sample_events": [
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 12,
        "active_basis_payload_count": 12,
        "active_basis_snapshot_hash": "67447f73c5ffce83",
        "captured_journey_count": 8,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "080a188d2484ee3e",
        "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      },
      {
        "active_basis_fractional_journey_count": 4,
        "active_basis_journey_count": 11,
        "active_basis_payload_count": 11,
        "active_basis_snapshot_hash": "35b8c9e8311f125c",
        "captured_journey_count": 8,
        "cg_iter": 2,
        "complete_active_basis": true,
        "context_hash": "a9831c8a34a4a2f4",
        "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      },
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "d9588027fa5a7ee3",
        "captured_journey_count": 0,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "c0259858cde05f02",
        "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "INCOMPLETE_LIMIT",
        "returned_journey_count": 0
      },
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "d9588027fa5a7ee3",
        "captured_journey_count": 0,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "c0259858cde05f02",
        "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "exact",
        "pricing_state": "INCOMPLETE_LIMIT",
        "returned_journey_count": 0
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 12,
        "active_basis_payload_count": 12,
        "active_basis_snapshot_hash": "67447f73c5ffce83",
        "captured_journey_count": 8,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "080a188d2484ee3e",
        "log_path": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      }
    ]
  }
]
```

## 检查项

```json
{
  "all_capture_events_have_complete_active_basis": true,
  "all_capture_events_no_certificate_effect": true,
  "all_command_outputs_exist": true,
  "all_commands_have_logs": true,
  "audit_generation_does_not_run_bpc_or_pricing": true,
  "has_capture_events": true,
  "has_commands": true,
  "runbook_passed": true
}
```
