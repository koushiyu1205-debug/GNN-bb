# Root Cause Selector Holdout Missing Context Diagnosis 报告

日期：2026-06-14

## 目的

本报告解释 selector holdout 采集链当前为什么还不能进入 selector holdout。
它只读 capture audit / target002 probe / trajectory branch summary，
不运行 BPC / pricing / RMP / Pulse，也不改变 solver 行为。

## 机器字段

```text
selector_holdout_missing_context_diagnosis = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = selector_holdout_missing_context_diagnosed
ready_for_selector_holdout = false
expected_context_hash_count = 10
expected_context_hit_count = 9
missing_expected_context_count = 1
target002_context_hash = 3f914a0d2b97fd27
target002_target_recovered_probe_count = 0
all_checks_pass = true
```

## 结论

当前 selector holdout 不是缺少 runbook，而是 target002 context 在当前 config-matched active-basis capture 中没有复现。probe matrix 显示当前重放 probe 对该 target 的 recovery 为 0；trajectory branch 显示同一 active hash 附近会按 pool / forbidden / returned-batch composition 分叉。

因此下一步不是直接 production A/B，也不是默认开启 worker，而是先解决
这个 missing context / context-trajectory 分叉问题，再重新做 addition-before
selector holdout。

## Missing Commands

```json
[
  {
    "capture_event_count": 12,
    "command_id": "selector_holdout_capture_002",
    "expected_context_hashes": [
      "3f914a0d2b97fd27"
    ],
    "hit_context_hashes": [],
    "instance": "apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000",
    "log_count": 3,
    "missing_context_hashes": [
      "3f914a0d2b97fd27"
    ],
    "output_dir": "BPC_future/results/root_cause_selector_holdout_collection_capture_config_matched_20260614/002_apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000__experimental_early_new_task_set_quota_3_20_only__target002_pt03_dp1000_cg4_tl8",
    "profile": "experimental_early_new_task_set_quota_3_20_only",
    "sample_context_hash_count": 3,
    "sample_context_hashes": [
      "080a188d2484ee3e",
      "71cf005b699054ed",
      "827ddca748a70f26"
    ]
  }
]
```

## Checks

```json
{
  "capture_audit_not_ready_contract_observed": true,
  "missing_command_identified": true,
  "missing_context_exists": true,
  "same_active_hash_splits_context": true,
  "target002_missing_context_identified": true,
  "target002_not_recovered_by_current_probes": true,
  "target002_probe_matrix_passed": true,
  "target002_trajectory_branch_passed": true
}
```
