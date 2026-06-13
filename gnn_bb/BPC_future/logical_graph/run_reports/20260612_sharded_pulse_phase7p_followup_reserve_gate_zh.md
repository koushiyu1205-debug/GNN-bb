# Sharded Pulse Phase 7P Follow-up Reserve Gate 报告

日期：2026-06-12

## 目标

本轮只补一个预算护栏：`hidden-negative worker` 在调用前保留一段后续求解时间，避免 current-context follow-up probe 连续成功后吃完整体 time limit。

这不是 production tuning，也不是 official certificate gate。

## 实现摘要

### 1. Worker post-call reserve

新增配置：

- `journey_sharded_pulse_hidden_negative_worker_post_call_time_reserve`

语义：

- 默认 `0.0`，默认行为不变；
- 若设置为正数，则 worker 可用时间为 `remaining_time - reserve`；
- 若剩余时间不足 reserve，worker 跳过并记录 `post_call_reserve_too_low`；
- current-context probe 和普通 hidden-negative worker 使用同一 hard deadline cap；
- 该配置只影响 worker call budget，不产生 certificate / official lower-bound side effect。

### 2. 新增 opt-in profile

新增 ROI calibration profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve`

该 profile 继承 follow-up probe 的严格边界：

- 只在 20-task 启用；
- pre-heuristic worker path；
- current-context probe；
- impact filter；
- low-budget；
- stop-after-first-negative；
- no success cooldown；
- post-call reserve `0.08s`。

5-task / 10-task 下该 profile 不注入 worker 配置。

## Focused 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_caps_call_time_by_remaining_time \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_reserves_post_call_time \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 4 tests in 0.003s
OK
```

同时通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py

git diff --check
```

## 单例对比

输出：

- `BPC_future/results/sharded_pulse_phase7p_followup_reserve_single_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_followup_reserve_single_20260612/summary.csv`

实例：`mt20_greedy_apollo_01`

| profile | wall | primal | worker events | added | new task-set | worker time | recursions | follow-up pricing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.178476 | 1061.554044 | 0 | 0 | 0 | 0.000000 | 0 | 0 |
| cooldown candidate | 0.220171 | 1030.002361 | 1 | 1 | 1 | 0.031803 | 115 | 2 |
| follow-up probe | 0.301354 | 1022.575388 | 3 | 3 | 2 | 0.181922 | 602 | 0 |
| follow-up reserve | 0.289048 | 1022.575388 | 3 | 2 | 2 | 0.103519 | 332 | 2 |

结论：

- reserve 将 worker time 从 `0.181922s` 降到 `0.103519s`；
- recursions 从 `602` 降到 `332`；
- wall 从 `0.301354s` 降到 `0.289048s`；
- primal 保持 `1022.575388`；
- 但仍慢于 baseline / cooldown candidate，且 follow-up exact tail 仍存在。

## Gate 矩阵

输出：

- `BPC_future/results/sharded_pulse_phase7p_followup_reserve_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_followup_reserve_gate_20260612/summary.csv`

矩阵：

- 5-task balanced 全量 20 个；
- 10-task 指定 7 个；
- 20-task smoke 3 个；
- profiles：`baseline` vs `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve`。

结果摘要：

| scale | profile | n | avg wall | worker events | added | new task-set | critical |
|---:|---|---:|---:|---:|---:|---:|---:|
| 5 | baseline | 20 | 0.025536 | 0 | 0 | 0 | 0 |
| 5 | reserve | 20 | 0.024793 | 0 | 0 | 0 | 0 |
| 10 | baseline | 7 | 0.117756 | 0 | 0 | 0 | 0 |
| 10 | reserve | 7 | 0.118310 | 0 | 0 | 0 | 0 |
| 20 | baseline | 3 | 0.209741 | 0 | 0 | 0 | 0 |
| 20 | reserve | 3 | 0.249095 | 3 | 2 | 2 | 0 |

20-task active row：

- `tranq20_01`：未触发 worker；
- `mt20_greedy_apollo_01`：worker events `3`，added `2`，new task-set `2`，primal `1061.554044 -> 1022.575388`；
- `mt20_greedy_tranq_01`：未触发 worker。

`mt20_greedy_apollo_01` follow-up：

- follow-up pricing calls：`2`
- follow-up generated / evaluated：`312 / 1306`
- follow-up legacy final judge calls：`1`

## 结论

reserve 是一个有效的预算护栏：它能减少连续 worker 成功后的 worker 时间和递归数，并保留 under-budget primal 改善信号。

但它仍没有证明 wall-time ROI：

- 5/10 gate 不触发 worker，默认安全；
- 20 smoke 中只在 `mt20_greedy_apollo_01` 有信号；
- 20 平均 wall 仍从 `0.209741s` 增到 `0.249095s`；
- follow-up exact tail 仍未消除。

因此当前判断不变：

- 不默认启用 worker；
- 不进入 official certificate gate；
- 不扩大 worker time limit；
- 不做 20/100 A/B；
- reserve profile 只保留为 opt-in 实验护栏。

下一步若继续 worker 路线，应优先做 active-support / objective-impact productivity gate，或分析 column-pool / RMP degeneracy；不要单纯增加 worker budget。
