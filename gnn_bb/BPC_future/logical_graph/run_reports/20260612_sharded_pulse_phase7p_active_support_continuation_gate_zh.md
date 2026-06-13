# Sharded Pulse Phase 7P Active-support Continuation Gate 报告

日期：2026-06-12

## 目标

本轮沿着 Phase 7P-alt / productivity gate 方向继续收紧 worker：

- 不扩大 worker budget；
- 不放开 official certificate；
- 不做 resume / parallel / 20/100 A/B；
- 只新增一个默认关闭的 continuation gate，避免连续 worker 成功但只产生 inactive-only 列时持续消耗预算。

核心判断来自上一轮 reserve gate：

- worker 能在 `mt20_greedy_apollo_01` 加 true-RC negative columns；
- 但连续 follow-up probe 仍没有 wall-time ROI；
- 因此下一步应减少低 productivity continuation，而不是增加预算。

## 实现摘要

### 1. 新增 continuation gate

新增配置：

- `journey_sharded_pulse_hidden_negative_worker_continue_only_on_active_support`
- `journey_sharded_pulse_hidden_negative_worker_inactive_success_cooldown_rounds`

默认：

- `continue_only_on_active_support=False`
- `inactive_success_cooldown_rounds=0`

默认 benchmark 行为不变。

启用后：

- worker 成功加列后，若 changed task-set 与当前 active support 无交集，则设置 inactive-success cooldown；
- 若 changed task-set 命中 active support，则不额外 cooldown；
- 该 gate 只控制后续 worker 是否继续抢预算，不影响 true-RC sanitize、impact filter、RMP add-column path；
- worker no-column / incomplete / filtered-empty 仍不能 certificate。

### 2. 新增 profile

新增 ROI calibration profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate`

它继承：

- 20-task only；
- pre-heuristic worker；
- current-context probe；
- impact filter；
- low-budget；
- stop-after-first-negative；
- post-call reserve `0.08s`。

并新增：

- `continue_only_on_active_support=True`
- `inactive_success_cooldown_rounds=2`

5-task / 10-task 下该 profile 仍为空配置。

## Focused 测试

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_worker_success_cooldown_uses_active_support_gate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 3 tests in 0.006s
OK
```

## 单例 smoke

输出：

- `BPC_future/results/sharded_pulse_phase7p_active_gate_single_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_active_gate_single_20260612/summary.csv`

实例：`mt20_greedy_apollo_01`

| profile | wall | primal | worker events | added | new task-set | support-changing | follow-up pricing |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 0.179556 | 1061.554044 | 0 | 0 | 0 | 0 | 0 |
| reserve | 0.290116 | 1022.575388 | 3 | 2 | 2 | 0 | 2 |
| reserve + active gate | 0.224746 | 1030.002361 | 1 | 1 | 1 | 0 | 2 |

观察：

- active gate 将 worker events 从 `3` 降到 `1`；
- wall 从 reserve profile 的 `0.290116s` 降到 `0.224746s`；
- 由于后续 inactive-only worker 被 cooldown，primal 改善从 `1022.575388` 回到单列水平 `1030.002361`；
- follow-up exact tail 仍存在。

## Gate 矩阵

输出：

- `BPC_future/results/sharded_pulse_phase7p_active_gate_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_active_gate_gate_20260612/summary.csv`

矩阵：

- 5-task balanced 全量 20 个；
- 10-task 指定 7 个；
- 20-task smoke 3 个；
- profiles：`baseline` vs `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate`。

结果摘要：

| scale | profile | n | avg wall | worker events | added | new task-set | critical |
|---:|---|---:|---:|---:|---:|---:|---:|
| 5 | baseline | 20 | 0.025458 | 0 | 0 | 0 | 0 |
| 5 | active gate | 20 | 0.024506 | 0 | 0 | 0 | 0 |
| 10 | baseline | 7 | 0.117733 | 0 | 0 | 0 | 0 |
| 10 | active gate | 7 | 0.117807 | 0 | 0 | 0 | 0 |
| 20 | baseline | 3 | 0.209673 | 0 | 0 | 0 | 0 |
| 20 | active gate | 3 | 0.228497 | 1 | 1 | 1 | 0 |

20-task active row：

- `tranq20_01`：未触发 worker；
- `mt20_greedy_apollo_01`：worker events `1`，added `1`，new task-set `1`，primal `1061.554044 -> 1030.002361`；
- `mt20_greedy_tranq_01`：未触发 worker。

## 结论

active-support continuation gate 符合设计意图：

- 保持 5/10 不触发 worker；
- 在 20-task active case 中减少连续 inactive-only worker；
- 保留一个 true-RC negative new task-set；
- 不产生 critical disagreement；
- 不产生 certificate side effect。

但它仍没有达成最终目标：

- 20-task 平均 wall 仍从 `0.209673s` 增到 `0.228497s`；
- follow-up exact tail 没有消失；
- 额外 primal 改善依赖被 gate 抑制的 inactive-only continuation。

因此当前判断：

- active gate 是比 reserve profile 更安全的实验候选；
- 仍不能默认启用；
- 仍不能进入 official certificate gate；
- 下一步若继续 worker 路线，应分析为什么 new task-set / inactive-only 列没有减少 follow-up exact tail，或进一步把 continuation gate 绑定到可观测 next-RMP objective / active-support movement。
