# Selector Holdout Priority Collection Runbook 报告

日期：2026-06-14

## 目的

本报告把未覆盖 priority contexts 转成补采 runbook。它只生成命令，不运行 BPC / pricing / RMP / Pulse。

## 机器字段

```text
selector_holdout_priority_collection_runbook = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_priority_collection_runbook_ready
target_context_count = 6
commandable_context_count = 3
unsupported_context_count = 3
command_count = 1
all_checks_pass = true
```

## 结论

未覆盖 priority contexts 中，一部分可以直接用现有 profile/config 生成 no-certificate-effect active-basis/forbidden capture 命令；其余 context 被显式列为 unsupported，不能当作已补采。该 runbook 只是补采入口，不是 production selector 或求解加速证据。

## Commandable contexts

```json
[
  "46e7a2883459d4fb",
  "794ecbd6fefaa1d7",
  "c27d904416342f6b"
]
```

## Unsupported contexts

```json
[
  "1b95888aae8dd7c2",
  "7b9a35f8f7c6581a",
  "988c728382b4a376"
]
```

## Commands

```json
[
  {
    "command": "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/run_sharded_pulse_roi_calibration.py --output-dir BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8 --instances BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json --profiles experimental_early_new_task_set_quota_3_20_only --repeat-count 3 --time-limit 8 --max-cg-iterations 4 --pricing-time-limit 0.3 --pricing-max-dp-states 1000 --counterfactual-replay-capture --counterfactual-replay-capture-active-basis --counterfactual-replay-capture-active-basis-max-rows 0 --counterfactual-replay-capture-max-journeys 0 --counterfactual-replay-capture-pool-max-journeys 0 --counterfactual-replay-capture-forbidden-signatures --counterfactual-replay-capture-forbidden-signature-max-count 0 --counterfactual-replay-capture-log-empty --quiet",
    "command_id": "selector_priority_capture_001",
    "diagnostic_only": true,
    "expected_context_hashes": [
      "46e7a2883459d4fb",
      "794ecbd6fefaa1d7",
      "c27d904416342f6b"
    ],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "instance_path": "BPC_future/logical_graph/tasks_020/greedy-anchor/apollo15_20km/apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000_logical_graph.json",
    "max_cg_iterations": 4,
    "output_dir": "BPC_future/results/root_cause_selector_holdout_priority_collection_capture_20260614/001_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8",
    "pricing_max_dp_states": 1000,
    "pricing_time_limit": 0.3,
    "profile": "experimental_early_new_task_set_quota_3_20_only",
    "repeat_count": 3,
    "requires_post_run_context_hit_audit": true,
    "runbook_generation_runs_bpc_or_pricing": false,
    "source_config_class": "target002_pt03_dp1000_cg4_tl8",
    "source_files": [
      "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl",
      "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl"
    ],
    "time_limit": 8.0
  }
]
```

## Target rows

```json
[
  {
    "commandable_source_file_count": 0,
    "context_hash": "1b95888aae8dd7c2",
    "instance_counts": {
      "very_small": 1
    },
    "label_counts": {
      "noop": 1
    },
    "needs_active_basis_snapshot_capture": true,
    "needs_explicit_forbidden_payload": true,
    "profile_rows": [],
    "row_count": 1,
    "sample_source_files": [
      "BPC_future/results/root_cause_active_basis_snapshot_smoke_20260614/logs/very_small__baseline.jsonl"
    ],
    "source_file_count": 1,
    "unsupported_reason_counts": {
      "source_profile_not_encoded": 1
    }
  },
  {
    "commandable_source_file_count": 1,
    "context_hash": "46e7a2883459d4fb",
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 8
    },
    "label_counts": {
      "noop": 8
    },
    "needs_active_basis_snapshot_capture": true,
    "needs_explicit_forbidden_payload": true,
    "profile_rows": [
      {
        "context_hash": "46e7a2883459d4fb",
        "profile": "experimental_early_new_task_set_quota_3_20_only",
        "repeat": 1,
        "source_config_class": "target002_pt03_dp1000_cg4_tl8",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl"
      }
    ],
    "row_count": 8,
    "sample_source_files": [
      "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl"
    ],
    "source_file_count": 1,
    "unsupported_reason_counts": {}
  },
  {
    "commandable_source_file_count": 1,
    "context_hash": "794ecbd6fefaa1d7",
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 16
    },
    "label_counts": {
      "improved": 14,
      "noop": 2
    },
    "needs_active_basis_snapshot_capture": true,
    "needs_explicit_forbidden_payload": true,
    "profile_rows": [
      {
        "context_hash": "794ecbd6fefaa1d7",
        "profile": "experimental_early_new_task_set_quota_3_20_only",
        "repeat": 1,
        "source_config_class": "target002_pt03_dp1000_cg4_tl8",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl"
      }
    ],
    "row_count": 16,
    "sample_source_files": [
      "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r1.jsonl"
    ],
    "source_file_count": 1,
    "unsupported_reason_counts": {}
  },
  {
    "commandable_source_file_count": 0,
    "context_hash": "7b9a35f8f7c6581a",
    "instance_counts": {
      "very_small": 2
    },
    "label_counts": {
      "noop": 2
    },
    "needs_active_basis_snapshot_capture": true,
    "needs_explicit_forbidden_payload": true,
    "profile_rows": [],
    "row_count": 2,
    "sample_source_files": [
      "BPC_future/results/root_cause_counterfactual_replay_feasible_smoke_20260613/logs/very_small_duplicate_noop_capture.jsonl"
    ],
    "source_file_count": 1,
    "unsupported_reason_counts": {
      "source_profile_not_encoded": 1
    }
  },
  {
    "commandable_source_file_count": 0,
    "context_hash": "988c728382b4a376",
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205": 1
    },
    "label_counts": {
      "noop": 1
    },
    "needs_active_basis_snapshot_capture": true,
    "needs_explicit_forbidden_payload": true,
    "profile_rows": [],
    "row_count": 1,
    "sample_source_files": [
      "BPC_future/results/root_cause_active_basis_snapshot_greedy20_pair_smoke_20260614/logs/apollo15_20km_greedy-anchor_randomtw_tasks020_03_seed61205__baseline.jsonl"
    ],
    "source_file_count": 1,
    "unsupported_reason_counts": {
      "source_profile_not_encoded": 1
    }
  },
  {
    "commandable_source_file_count": 1,
    "context_hash": "c27d904416342f6b",
    "instance_counts": {
      "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000": 16
    },
    "label_counts": {
      "improved": 14,
      "noop": 2
    },
    "needs_active_basis_snapshot_capture": true,
    "needs_explicit_forbidden_payload": true,
    "profile_rows": [
      {
        "context_hash": "c27d904416342f6b",
        "profile": "experimental_early_new_task_set_quota_3_20_only",
        "repeat": 2,
        "source_config_class": "target002_pt03_dp1000_cg4_tl8",
        "source_file": "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl"
      }
    ],
    "row_count": 16,
    "sample_source_files": [
      "BPC_future/results/root_cause_target002_capture_pt03_r3_20260613/logs/mt20_greedy_apollo_01__experimental_early_new_task_set_quota_3_20_only__r2.jsonl"
    ],
    "source_file_count": 1,
    "unsupported_reason_counts": {}
  }
]
```

## Checks

```json
{
  "all_commands_have_active_basis_capture": true,
  "all_commands_have_forbidden_signature_capture": true,
  "all_commands_have_nondefault_pricing_context_args": true,
  "all_instances_resolved_for_commands": true,
  "diagnostic_not_solver_run": true,
  "has_commandable_contexts": true,
  "has_commands": true,
  "priority_matrix_passed": true,
  "uncovered_contexts_present": true,
  "unsupported_contexts_explicitly_listed": true
}
```
