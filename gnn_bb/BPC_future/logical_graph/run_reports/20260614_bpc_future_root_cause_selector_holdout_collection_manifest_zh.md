# Root Cause Selector Holdout Collection Manifest 报告

日期：2026-06-14

## 目的

本报告把 selector 补采计划转成具体 context manifest。它只读已有
summary/CSV，不运行 BPC / pricing / RMP / Pulse，也不改变 worker、
certificate 或 solver 默认行为。

## 机器字段

```text
root_cause_selector_holdout_collection_manifest = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_collection_manifest_ready
current_stage = calibration_only_selector_holdout
production_direction_proven = false
priority_context_count = 10
collection_target_count = 10
collection_target_candidate_row_count = 97
targets_needing_active_basis_snapshot_count = 10
existing_active_basis_snapshot_anchor_count = 1
all_checks_pass = true
```

## 结论

当前 priority selector failure contexts 都能映射回已有 candidate rows，但大多数还缺 full active-basis snapshot 版本。下一步应只做 no-certificate-effect / calibration-only 补采；该 manifest 不证明 production selector、5/10 no-regression 或 20-task speedup。

## 失败类型覆盖

```json
{
  "false_positive_no_positive_context": 4,
  "missed_positive_context": 3,
  "mixed_low_precision_or_recall_context": 3
}
```

## 补采配置要求

```json
{
  "journey_counterfactual_replay_capture_active_basis_enabled": true,
  "journey_counterfactual_replay_capture_active_basis_max_rows": 0,
  "journey_counterfactual_replay_capture_enabled": true,
  "journey_counterfactual_replay_capture_forbidden_signature_max_count": 0,
  "journey_counterfactual_replay_capture_forbidden_signatures_enabled": true,
  "journey_counterfactual_replay_capture_log_empty": true,
  "journey_counterfactual_replay_capture_max_journeys": 0,
  "journey_counterfactual_replay_capture_pool_max_journeys": 0
}
```

## 仍然禁止

- official certificate gate
- worker default enable
- production BPC A/B before selector holdout
- post-addition or hindsight features in online selector

## Context targets

```json
[
  {
    "candidate_label_counts": {
      "noop": 5
    },
    "candidate_row_count": 5,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_001",
    "context_hash": "3f914a0d2b97fd27",
    "failure_kind": "false_positive_no_positive_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "3",
    "representative_instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "representative_source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl"
  },
  {
    "candidate_label_counts": {
      "noop": 3
    },
    "candidate_row_count": 3,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_002",
    "context_hash": "c5a59a95c2c9971a",
    "failure_kind": "false_positive_no_positive_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "4",
    "representative_instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl"
  },
  {
    "candidate_label_counts": {
      "noop": 3
    },
    "candidate_row_count": 3,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_003",
    "context_hash": "d60fcf4b919b7d22",
    "failure_kind": "false_positive_no_positive_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "2",
    "representative_instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_pricing_time_0_6_20_only__r0.jsonl"
  },
  {
    "candidate_label_counts": {
      "noop": 3
    },
    "candidate_row_count": 3,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_004",
    "context_hash": "e55ea3e7d277b6d1",
    "failure_kind": "false_positive_no_positive_context",
    "has_current_active_basis_snapshot_context": true,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "2",
    "representative_instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_l1_previous_dual_stabilization_20_only__r0.jsonl"
  },
  {
    "candidate_label_counts": {
      "improved": 3
    },
    "candidate_row_count": 3,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_005",
    "context_hash": "05695ab419abfb4b",
    "failure_kind": "missed_positive_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "4",
    "representative_instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl"
  },
  {
    "candidate_label_counts": {
      "improved": 1,
      "noop": 5
    },
    "candidate_row_count": 6,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_006",
    "context_hash": "1db815e33b9ea471",
    "failure_kind": "missed_positive_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "3",
    "representative_instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl"
  },
  {
    "candidate_label_counts": {
      "improved": 2,
      "noop": 9
    },
    "candidate_row_count": 11,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_007",
    "context_hash": "7f2e531534d18ad2",
    "failure_kind": "missed_positive_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "3",
    "representative_instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl"
  },
  {
    "candidate_label_counts": {
      "improved": 12,
      "noop": 12
    },
    "candidate_row_count": 24,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_008",
    "context_hash": "3c36c602289637b4",
    "failure_kind": "mixed_low_precision_or_recall_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "2",
    "representative_instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl"
  },
  {
    "candidate_label_counts": {
      "improved": 12,
      "noop": 12
    },
    "candidate_row_count": 24,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_009",
    "context_hash": "774573a2964cb1c5",
    "failure_kind": "mixed_low_precision_or_recall_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "2",
    "representative_instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl"
  },
  {
    "candidate_label_counts": {
      "improved": 3,
      "noop": 12
    },
    "candidate_row_count": 15,
    "capture_command_template": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_bpc_future.py --config <same-profile-config-as-source> --instances tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001 --log-dir BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/logs --results-csv BPC_future/results/root_cause_selector_holdout_collection_capture_20260614/summary.csv --set journey_counterfactual_replay_capture_enabled=true --set journey_counterfactual_replay_capture_active_basis_enabled=true --set journey_counterfactual_replay_capture_active_basis_max_rows=0 --set journey_counterfactual_replay_capture_max_journeys=0 --set journey_counterfactual_replay_capture_pool_max_journeys=0 --set journey_counterfactual_replay_capture_forbidden_signatures_enabled=true --set journey_counterfactual_replay_capture_forbidden_signature_max_count=0 --set journey_counterfactual_replay_capture_log_empty=true --quiet",
    "collection_target_id": "selector_holdout_context_010",
    "context_hash": "79de1ece885a7f67",
    "failure_kind": "mixed_low_precision_or_recall_context",
    "has_current_active_basis_snapshot_context": false,
    "needs_active_basis_snapshot_capture": true,
    "representative_cg_iter": "3",
    "representative_instance": "tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001",
    "representative_source_file": "BPC_future/results/root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613/logs/mt20_greedy_tranq_01__experimental_early_new_task_set_quota_3_20_only__r0.jsonl"
  }
]
```

## 检查项

```json
{
  "all_priority_contexts_mapped_to_rows": true,
  "all_targets_no_certificate_effect": true,
  "collection_plan_passed": true,
  "covers_all_failure_kinds": true,
  "feature_availability_passed": true,
  "has_at_least_one_existing_snapshot_anchor": true,
  "has_priority_contexts": true,
  "has_snapshot_gap_targets": true,
  "schema_coverage_passed": true,
  "still_calibration_only": true
}
```
