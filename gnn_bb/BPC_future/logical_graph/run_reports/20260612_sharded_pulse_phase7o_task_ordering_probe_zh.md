# Sharded Pulse Phase 7O Task-ordering Probe 报告

日期：2026-06-12

## 目标

上一轮 Phase 7O full-profile gate 显示：

- 普通 current-probe profiles 在 5/10 上明显拖慢；
- 当前唯一可保留的候选是 `20-only + pre-heuristic + cooldown + leaf-stop`；
- 该候选能在 `mt20_greedy_apollo_01` 加 1 个 new task-set，但仍没有 wall-time ROI。

本轮尝试一个低风险方向：只改变 transition Pulse 的任务扩展顺序，配合 `stop_after_first_negative` 更早遇到 true-RC negative leaf。

该改动不改变 pricing universe，不改变 materialization，不改变 certificate 语义；只改变 DFS 遍历顺序。

## 实现摘要

### 1. Transition task ordering

`transition_root_only_pulse()` 新增参数：

- `task_ordering="natural" | "cover_dual_desc" | "reduced_cost_proxy"`

默认值是 `natural`。

`reduced_cost_proxy` 的排序依据为：

```text
min transition cost
+ service cost
+ min direct return cost
- cover dual
```

并在非 natural 模式下按 option cost / energy / time 对 arc options 做稳定排序。

### 2. Sharded Pulse config

`JourneyPricingConfig` 新增：

- `pulse_task_ordering`

driver config 新增 opt-in 透传：

- `journey_pulse_task_ordering`
- `journey_sharded_pulse_audit_task_ordering`
- `journey_sharded_pulse_hidden_negative_worker_task_ordering`

日志新增：

- `pulse_task_ordering`
- `pulse_worker_task_ordering`

### 3. 独立 ordered 实验 profile

保留当前候选 profile 不变：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown`

新增实验 profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered`

只有 ordered 实验 profile 开启：

```text
journey_sharded_pulse_hidden_negative_worker_task_ordering = reduced_cost_proxy
```

这样不会污染当前候选，也不会影响 5/10 gate。

## Focused Tests

新增/更新测试：

- `test_transition_pulse_task_ordering_preserves_exhaustive_surface`
- `test_transition_pulse_task_ordering_reduces_early_stop_search`
- `test_sharded_pulse_task_ordering_passes_to_transition_core`
- `test_sharded_pulse_roi_calibration_profile_configs_are_opt_in`

其中 toy early-stop case 证明 ordering 机制本身有效：

- natural：`generated_sortie_traces = 10`，`recursions = 5`
- reduced_cost_proxy：`generated_sortie_traces = 1`，`recursions = 2`

同时 exhaustive surface 测试证明：

- full exhaustive candidate signatures 不变；
- best true RC 不变；
- found-negative 判断不变。

## 20-task Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_task_ordering_compare_20_smoke_20260612 \
--instances phase7o_20_smoke \
--profiles baseline \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered \
--time-limit 4.0 \
--audit-time-limit 0.15 \
--worker-time-limit 0.15 \
--current-probe-time-limit 0.15 \
--pricing-time-limit 0.08 \
--max-cg-iterations 3 \
--audit-max-recursions 30000 \
--worker-max-recursions 30000 \
--current-probe-max-recursions 15000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_task_ordering_compare_20_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_task_ordering_compare_20_smoke_20260612/summary.csv`

## Smoke 结果

| profile | avg wall | median wall | worker events | added | new task-set | critical |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.200246 | 0.170179 | 0 | 0 | 0 | 0 |
| natural candidate | 0.215122 | 0.206844 | 1 | 1 | 1 | 0 |
| ordered experiment | 0.210997 | 0.208796 | 1 | 1 | 1 | 0 |

Active row：

| profile | instance | worker ordering | wall | primal | added | worker time | recursions | pruned |
|---|---|---|---:|---:|---:|---:|---:|---:|
| natural candidate | mt20_greedy_apollo_01 | natural | 0.206844 | 1030.002361 | 1 | 0.033576 | 115 | 6056 |
| ordered experiment | mt20_greedy_apollo_01 | reduced_cost_proxy | 0.208796 | 1030.002361 | 1 | 0.035687 | 115 | 6038 |

## 判断

`reduced_cost_proxy` ordering 在 toy early-stop case 中有效，但在当前 20-task active shard 上没有降低 recursions，也没有降低 worker time。

因此：

- 保留 `pulse_task_ordering` 作为 opt-in 实验机制；
- 不把 ordering 打开到当前候选 profile；
- 不进入 Phase 7P production tuning；
- 不默认启用 worker；
- 不开启 official certificate gate。

这个负结果说明当前 20-task overhead 不主要来自 task 扩展顺序，而是来自 worker 后 follow-up exact tail / RMP 退化路径。下一步更应聚焦：

1. worker 后 follow-up exact tail 的触发与耗时诊断；
2. active-support / productivity gate；
3. RMP degeneracy / column pool impact；
4. 或 hidden-negative add-column 后的后续 pricing path，而不是继续调 task ordering。

## 验证

```text
py_compile: OK
focused tests: Ran 7 tests in 0.074s OK
20-task smoke: completed, summary/logs written
```
