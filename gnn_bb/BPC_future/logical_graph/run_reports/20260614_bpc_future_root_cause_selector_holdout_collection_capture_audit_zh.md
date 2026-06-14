# Root Cause Selector Holdout Collection Capture Audit 报告

日期：2026-06-14

## 目的

本报告审计 selector holdout collection runbook 的实际采集输出。它只读
 JSONL/summary，不运行 BPC / pricing / RMP / Pulse，也不改变 worker、
certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_holdout_collection_capture_audit = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_collection_capture_audited
command_count = 6
capture_event_count = 78
expected_context_hash_count = 10
expected_context_hit_count = 9
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
    "capture_event_count": 15,
    "command_id": "selector_holdout_capture_001",
    "complete_hit_context_hashes": [
      "1db815e33b9ea471",
      "3c36c602289637b4",
      "7f2e531534d18ad2"
    ],
    "expected_context_hashes": [
      "1db815e33b9ea471",
      "3c36c602289637b4",
      "7f2e531534d18ad2"
    ],
    "hit_context_hashes": [
      "1db815e33b9ea471",
      "3c36c602289637b4",
      "7f2e531534d18ad2"
    ],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "log_count": 3,
    "missing_complete_context_hashes": [],
    "missing_context_hashes": [],
    "no_certificate_bad_count": 0,
    "output_dir": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8",
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
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 8,
        "active_basis_payload_count": 8,
        "active_basis_snapshot_hash": "743f721e93878a62",
        "captured_journey_count": 8,
        "cg_iter": 2,
        "complete_active_basis": true,
        "context_hash": "3c36c602289637b4",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      },
      {
        "active_basis_fractional_journey_count": 4,
        "active_basis_journey_count": 10,
        "active_basis_payload_count": 10,
        "active_basis_snapshot_hash": "0a46cfc63aa8a982",
        "captured_journey_count": 6,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "1db815e33b9ea471",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 6
      },
      {
        "active_basis_fractional_journey_count": 14,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "a80047d83d51fb89",
        "captured_journey_count": 0,
        "cg_iter": 4,
        "complete_active_basis": true,
        "context_hash": "90c6e86143b709e5",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "INCOMPLETE_LIMIT",
        "returned_journey_count": 0
      },
      {
        "active_basis_fractional_journey_count": 14,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "a80047d83d51fb89",
        "captured_journey_count": 0,
        "cg_iter": 4,
        "complete_active_basis": true,
        "context_hash": "90c6e86143b709e5",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "exact",
        "pricing_state": "INCOMPLETE_LIMIT",
        "returned_journey_count": 0
      }
    ]
  },
  {
    "active_basis_bad_count": 0,
    "capture_event_count": 12,
    "command_id": "selector_holdout_capture_002",
    "complete_hit_context_hashes": [],
    "expected_context_hashes": [
      "3f914a0d2b97fd27"
    ],
    "hit_context_hashes": [],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "log_count": 3,
    "missing_complete_context_hashes": [
      "3f914a0d2b97fd27"
    ],
    "missing_context_hashes": [
      "3f914a0d2b97fd27"
    ],
    "no_certificate_bad_count": 0,
    "output_dir": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8",
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
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      },
      {
        "active_basis_fractional_journey_count": 4,
        "active_basis_journey_count": 11,
        "active_basis_payload_count": 11,
        "active_basis_snapshot_hash": "f7a431ed4ee9fbe7",
        "captured_journey_count": 8,
        "cg_iter": 2,
        "complete_active_basis": true,
        "context_hash": "827ddca748a70f26",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      },
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "66dcb26c5a1f0411",
        "captured_journey_count": 0,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "71cf005b699054ed",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "INCOMPLETE_LIMIT",
        "returned_journey_count": 0
      },
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "66dcb26c5a1f0411",
        "captured_journey_count": 0,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "71cf005b699054ed",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
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
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      }
    ]
  },
  {
    "active_basis_bad_count": 0,
    "capture_event_count": 15,
    "command_id": "selector_holdout_capture_003",
    "complete_hit_context_hashes": [
      "e55ea3e7d277b6d1"
    ],
    "expected_context_hashes": [
      "e55ea3e7d277b6d1"
    ],
    "hit_context_hashes": [
      "e55ea3e7d277b6d1"
    ],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "log_count": 3,
    "missing_complete_context_hashes": [],
    "missing_context_hashes": [],
    "no_certificate_bad_count": 0,
    "output_dir": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/003_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8",
    "output_exists": true,
    "profile": "experimental_l1_previous_dual_stabilization_20_only",
    "sample_events": [
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 12,
        "active_basis_payload_count": 12,
        "active_basis_snapshot_hash": "67447f73c5ffce83",
        "captured_journey_count": 1,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "080a188d2484ee3e",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/003_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 10,
        "active_basis_payload_count": 10,
        "active_basis_snapshot_hash": "929509945f6249ea",
        "captured_journey_count": 1,
        "cg_iter": 2,
        "complete_active_basis": true,
        "context_hash": "e55ea3e7d277b6d1",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/003_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 10,
        "active_basis_payload_count": 10,
        "active_basis_snapshot_hash": "929509945f6249ea",
        "captured_journey_count": 1,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "862f8736f9f8b9b8",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/003_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 7,
        "active_basis_journey_count": 12,
        "active_basis_payload_count": 12,
        "active_basis_snapshot_hash": "a6388eae7d499fc9",
        "captured_journey_count": 0,
        "cg_iter": 4,
        "complete_active_basis": true,
        "context_hash": "2bde99fad71ad573",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/003_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "INCOMPLETE_LIMIT",
        "returned_journey_count": 0
      },
      {
        "active_basis_fractional_journey_count": 7,
        "active_basis_journey_count": 12,
        "active_basis_payload_count": 12,
        "active_basis_snapshot_hash": "a6388eae7d499fc9",
        "captured_journey_count": 0,
        "cg_iter": 4,
        "complete_active_basis": true,
        "context_hash": "2bde99fad71ad573",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/003_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "exact",
        "pricing_state": "INCOMPLETE_LIMIT",
        "returned_journey_count": 0
      }
    ]
  },
  {
    "active_basis_bad_count": 0,
    "capture_event_count": 12,
    "command_id": "selector_holdout_capture_004",
    "complete_hit_context_hashes": [
      "d60fcf4b919b7d22"
    ],
    "expected_context_hashes": [
      "d60fcf4b919b7d22"
    ],
    "hit_context_hashes": [
      "d60fcf4b919b7d22"
    ],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "log_count": 3,
    "missing_complete_context_hashes": [],
    "missing_context_hashes": [],
    "no_certificate_bad_count": 0,
    "output_dir": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/004_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__dp1000_pt02_cg4_tl8",
    "output_exists": true,
    "profile": "experimental_pricing_time_0_6_20_only",
    "sample_events": [
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 12,
        "active_basis_payload_count": 12,
        "active_basis_snapshot_hash": "67447f73c5ffce83",
        "captured_journey_count": 1,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "080a188d2484ee3e",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/004_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 10,
        "active_basis_payload_count": 10,
        "active_basis_snapshot_hash": "4ec55c69b2fe77cb",
        "captured_journey_count": 1,
        "cg_iter": 2,
        "complete_active_basis": true,
        "context_hash": "d60fcf4b919b7d22",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/004_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 10,
        "active_basis_payload_count": 10,
        "active_basis_snapshot_hash": "4ec55c69b2fe77cb",
        "captured_journey_count": 1,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "8a25921bbbe76f2f",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/004_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 9,
        "active_basis_payload_count": 9,
        "active_basis_snapshot_hash": "a58cc60d75e1b381",
        "captured_journey_count": 1,
        "cg_iter": 4,
        "complete_active_basis": true,
        "context_hash": "45f9ba26335328a1",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/004_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 12,
        "active_basis_payload_count": 12,
        "active_basis_snapshot_hash": "67447f73c5ffce83",
        "captured_journey_count": 1,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "080a188d2484ee3e",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/004_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__dp1000_pt02_cg4_tl8/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_pricing_time_0_6_20_only__r1.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      }
    ]
  },
  {
    "active_basis_bad_count": 0,
    "capture_event_count": 12,
    "command_id": "selector_holdout_capture_005",
    "complete_hit_context_hashes": [
      "05695ab419abfb4b",
      "774573a2964cb1c5",
      "79de1ece885a7f67"
    ],
    "expected_context_hashes": [
      "05695ab419abfb4b",
      "774573a2964cb1c5",
      "79de1ece885a7f67"
    ],
    "hit_context_hashes": [
      "05695ab419abfb4b",
      "774573a2964cb1c5",
      "79de1ece885a7f67"
    ],
    "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "log_count": 3,
    "missing_complete_context_hashes": [],
    "missing_context_hashes": [],
    "no_certificate_bad_count": 0,
    "output_dir": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8",
    "output_exists": true,
    "profile": "experimental_early_new_task_set_quota_3_20_only",
    "sample_events": [
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "70bb3b69a1c4d0bf",
        "captured_journey_count": 8,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "8c60fac6ce5f475f",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      },
      {
        "active_basis_fractional_journey_count": 6,
        "active_basis_journey_count": 11,
        "active_basis_payload_count": 11,
        "active_basis_snapshot_hash": "b0f3c6e7318ad421",
        "captured_journey_count": 8,
        "cg_iter": 2,
        "complete_active_basis": true,
        "context_hash": "774573a2964cb1c5",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      },
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "692d88bc082534a9",
        "captured_journey_count": 5,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "79de1ece885a7f67",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 5
      },
      {
        "active_basis_fractional_journey_count": 14,
        "active_basis_journey_count": 16,
        "active_basis_payload_count": 16,
        "active_basis_snapshot_hash": "bb3751fd0af7f66b",
        "captured_journey_count": 1,
        "cg_iter": 4,
        "complete_active_basis": true,
        "context_hash": "05695ab419abfb4b",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "70bb3b69a1c4d0bf",
        "captured_journey_count": 8,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "8c60fac6ce5f475f",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/005_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 8
      }
    ]
  },
  {
    "active_basis_bad_count": 0,
    "capture_event_count": 12,
    "command_id": "selector_holdout_capture_006",
    "complete_hit_context_hashes": [
      "c5a59a95c2c9971a"
    ],
    "expected_context_hashes": [
      "c5a59a95c2c9971a"
    ],
    "hit_context_hashes": [
      "c5a59a95c2c9971a"
    ],
    "instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "log_count": 3,
    "missing_complete_context_hashes": [],
    "missing_context_hashes": [],
    "no_certificate_bad_count": 0,
    "output_dir": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/006_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8",
    "output_exists": true,
    "profile": "experimental_l1_previous_dual_stabilization_20_only",
    "sample_events": [
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "70bb3b69a1c4d0bf",
        "captured_journey_count": 1,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "8c60fac6ce5f475f",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/006_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 8,
        "active_basis_payload_count": 8,
        "active_basis_snapshot_hash": "b4aa77712d449f56",
        "captured_journey_count": 1,
        "cg_iter": 2,
        "complete_active_basis": true,
        "context_hash": "f67cf0852ea7df8b",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/006_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 8,
        "active_basis_payload_count": 8,
        "active_basis_snapshot_hash": "a567b7f758690a01",
        "captured_journey_count": 1,
        "cg_iter": 3,
        "complete_active_basis": true,
        "context_hash": "0ce620bcfc56d562",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/006_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 0,
        "active_basis_journey_count": 8,
        "active_basis_payload_count": 8,
        "active_basis_snapshot_hash": "c2e1430c4c203770",
        "captured_journey_count": 1,
        "cg_iter": 4,
        "complete_active_basis": true,
        "context_hash": "c5a59a95c2c9971a",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/006_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
      },
      {
        "active_basis_fractional_journey_count": 13,
        "active_basis_journey_count": 15,
        "active_basis_payload_count": 15,
        "active_basis_snapshot_hash": "70bb3b69a1c4d0bf",
        "captured_journey_count": 1,
        "cg_iter": 1,
        "complete_active_basis": true,
        "context_hash": "8c60fac6ce5f475f",
        "log_path": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/006_tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__dp1000_pt02_cg4_tl8/logs/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001__experimental_l1_previous_dual_stabilization_20_only__r1.jsonl",
        "no_certificate_effect": true,
        "pricing_kind": "heuristic",
        "pricing_state": "FOUND_NEGATIVE",
        "returned_journey_count": 1
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
