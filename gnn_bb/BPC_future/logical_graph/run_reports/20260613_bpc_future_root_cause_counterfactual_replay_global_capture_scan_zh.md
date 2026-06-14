# BPC_future Counterfactual Replay Global Capture Scan

日期：2026-06-13

## 目的

本轮不改 solver、不改 pricing、不加 worker。

目的只是扫描当前 `BPC_future/results` 下所有 JSONL，回答：

> 现有结果里到底有多少 no-certificate-effect exact-context replay capture，可用于 returned-batch selector calibration？

这直接关系到当前目标：如果 clean replay 样本不足，就不能宣称已经有可上线优化方向。

## 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_counterfactual_replay_capture.py \
BPC_future/results \
--output-dir BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/audit
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/build_counterfactual_replay_manifest.py \
BPC_future/results \
--output-dir BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/replay_manifest
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_counterfactual_replay_from_manifest.py \
BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/replay_manifest/replay_cases.json \
--output-dir BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/replay_result
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_impact_dataset.py \
--manifest BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/replay_manifest/replay_cases.json \
--replay-result BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/replay_result/replay_results.json \
--output-dir BPC_future/results/root_cause_counterfactual_replay_global_capture_scan_20260613/impact
```

## 全局 capture audit

```text
files_scanned = 8659
event_count = 4
complete_event_count = 4
returned_journey_count = 9
captured_journey_count = 9
pool_journey_count = 335
pool_journey_payload_count = 335
all_checks_pass = true
```

四个 capture event 来源：

| case | 来源 | task scale | candidates | context |
|---|---|---:|---:|---|
| `capture_case_0001` | `very_small_driver_capture.jsonl` | very small | 1 | smoke |
| `capture_case_0002` | `very_small_duplicate_noop_capture.jsonl` | very small | 1 | duplicate/no-op smoke |
| `capture_case_0003` | `capture_t10.jsonl` | 20 | 3 | Apollo20 same context |
| `capture_case_0004` | `capture_t10_v2.jsonl` | 20 | 4 | Apollo20 same context |

## Manifest readiness

```text
case_count = 4
ready_case_count = 1
candidate_count = 9
treatment_count = 21
all_checks_pass = true
```

non-ready 原因：

```text
capture_case_0001: missing_vehicle_count_for_replay
capture_case_0002: missing_vehicle_count_for_replay
capture_case_0003: missing_vehicle_count_for_replay
```

唯一 ready case：

```text
capture_case_0004
instance = apollo15_20km_greedy-anchor_randomtw_tasks020_01_seed61000
task_count = 20
context_hash = 080a188d2484ee3e
candidate_count = 4
```

## Replay result

```text
case_count = 4
ready_case_count = 1
all_checks_pass = false
control_rmp_solved = true
changed_treatment_count = 7
improving_treatment_count = 7
best_objective_delta = -137.116184
```

`control_rmp_solved=true` 只表示唯一 ready case 的 control RMP 为 `OPTIMAL`。全局 replay 仍 `all_checks_pass=false`，因为三个 non-ready case 被正确跳过并保留 issues。

## Impact dataset

```text
all_checks_pass = false
case_count = 4
candidate_row_count = 9
single_candidate_with_replay_count = 4
high_impact_candidate_count = 4
unknown_candidate_count = 0
control_solved_case_count = 1
control_unsolved_case_count = 3
full_batch_improved_count = 1
best_objective_delta = -137.116184
```

解释：

- 9 个 candidate rows 里，只有 4 个来自 ready case 并有 single-candidate replay；
- 这 4 个都来自同一个 Apollo20 context；
- 另外 5 个 candidate rows 不能作为 calibration 样本，因为对应 case 不满足 replay readiness；
- 当前仍没有多 context clean replay calibration set。

## 对根因判断的影响

这次全局扫描强化了两个判断：

1. high-impact returned batch 真实存在：Apollo20 v2 case 仍有 `-137.116184` local RMP delta；
2. 现有 clean replay 样本严重不足：全 results 里只有一个 ready 20-task context。

因此当前不能把任何 selector、worker 或 priority rule 推进 production。缺的不是一个更漂亮的解释，而是多个 clean exact-context treatment 样本。

## 当前 readiness 结论

全局扫描后，`optimization_direction_readiness` 中的关键状态仍是：

```text
has_local_rmp_impact = true
has_multi_context_clean_replay_calibration = false
has_stable_addition_before_selector = false
has_20_walltime_speedup_evidence = false
production_direction_proven = false
```

## 下一步门槛

如果继续推进，必须优先扩大 no-certificate-effect exact-context capture：

- 每个 event 必须有 `vehicle_count`；
- manifest case 必须 `ready_for_rmp_replay=true`；
- replay control RMP 必须 `OPTIMAL`；
- single candidate delta 必须 finite；
- 至少覆盖多个独立 20-task contexts；
- 在此之前，不能说已经找到能保证 exactness、5/10 不退化、20 大幅加速的优化方向。

