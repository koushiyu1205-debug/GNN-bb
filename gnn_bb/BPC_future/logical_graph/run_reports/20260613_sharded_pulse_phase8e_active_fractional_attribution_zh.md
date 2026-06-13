# Sharded Pulse Phase 8E Active Fractional Attribution 报告

日期：2026-06-13

## 目标

Phase 8E 从 Phase 8A/8D 后的 pivot 方向继续推进，检查 RMP active fractional degeneracy / column-pool pressure 是否解释当前 hard-tail。

本轮只加只读诊断和窄 probe，不改变：

- RMP 建模；
- pricing / Pulse worker；
- column selection；
- certificate / official lower-bound 逻辑。

## 实现摘要

### 1. Active support 结构诊断

`_journey_pool_structure_diagnostics()` 新增只读字段：

- `pool_active_duplicate_task_set_ratio`
- `pool_active_avg_journeys_per_task_set`
- `pool_active_fractional_value_sum`
- `pool_active_fractional_value_max`
- `pool_active_fractional_value_min`
- `pool_active_fractional_small_value_count`
- `pool_active_top_task_set_value_samples`

`pool_active_top_task_set_value_samples` 格式为：

```text
[active_value_sum, active_journey_count, task_set]
```

这些字段只描述当前 RMP active support，不参与求解决策。

### 2. ROI summary 透传

`run_sharded_pulse_roi_calibration.py` 新增 summary 字段：

- `pool_active_duplicate_task_set_ratio_last`
- `pool_active_duplicate_task_set_ratio_max`
- `pool_active_avg_journeys_per_task_set_last`
- `pool_active_fractional_value_sum_last`
- `pool_active_fractional_value_max_last`
- `pool_active_fractional_value_min_last`
- `pool_active_fractional_small_value_count_last`
- `pool_active_top_task_set_value_samples_last`

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pool_structure_diagnostics_tracks_pool_and_active_support \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pool_structure_metrics_are_summarized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier
```

结果：

```text
Ran 4 tests in 0.001s
OK
```

## Probe 输出

输出目录：

- `BPC_future/results/sharded_pulse_phase8e_active_fractional_attribution_probe_20260613`
- `BPC_future/results/sharded_pulse_phase8e_active_fractional_short_probe_20260613`

### 1. Greedy Apollo20 / Tranq20，1.5s probe

`mt20_greedy_apollo_01` baseline：

- active journeys: `10`
- active task sets: `10`
- active duplicate ratio: `0.0`
- active avg journeys/task-set: `1.0`
- fractional journeys: `0`
- fractional ratio: `0.0`
- top active task sets all have value `1.0`

`mt20_greedy_apollo_01` worker profile：

- active journeys: `10`
- active task sets: `10`
- active duplicate ratio: `0.0`
- fractional ratio: `0.0`
- worker added journeys: `1`
- follow-up negative remains disjoint `5,8,15`

`mt20_greedy_tranq_01` baseline / worker：

- active journeys: `8`
- active task sets: `8`
- active duplicate ratio: `0.0`
- active avg journeys/task-set: `1.0`
- fractional ratio: `0.0`
- worker added journeys: `0`

### 2. Short-budget Tranq20 probe

`tranq20_01` baseline / worker：

- active journeys: `11`
- active task sets: `11`
- active duplicate ratio: `0.0`
- active avg journeys/task-set: `1.0`
- fractional journeys: `3`
- fractional ratio: `0.272727273`
- fractional value sum: `1.5`
- fractional value min/max: `0.5 / 0.5`
- small fractional count (`<=0.25`): `0`

`mt20_greedy_tranq_01` short-budget rerun：

- active journeys: `8`
- active task sets: `8`
- active duplicate ratio: `0.0`
- fractional ratio: `0.0`

## 解释

当前 probe 不支持“column-pool duplicate / active replacement degeneracy 是主因”：

1. active duplicate task-set ratio 均为 `0.0`；
2. active avg journeys/task-set 均为 `1.0`；
3. top active samples 也都是单 journey per task-set；
4. 出现 fractional 的 `tranq20_01` 只有 3 个 `0.5` 权重列，不是大量小权重 fractional columns。

因此，当前 hard-tail 更像：

- residual pricing / profile-DP / proof-tail 仍在找负列；
- 或 RMP primal route 仍未形成足够强的 final basis；
- 但不是 active support 内大量重复 task-set 或大量 tiny fractional columns 导致的明显退化。

## Exactness 边界

本轮没有改变：

- objective；
- RMP 约束；
- pricing；
- worker；
- add-column path；
- certificate / official lower-bound。

新增字段只进入 JSONL / ROI summary。

## 结论

Phase 8E 给出一个排除性结论：在本轮 Apollo/Tranq 20-task probes 中，active support duplicate pressure 不是主因，active fractional pressure 也不是“大量小权重列”形态。

下一步不建议做 column-pool compression 作为主线，除非后续更大矩阵显示 active duplicate ratio 或 tiny fractional count 明显升高。

更合理的下一步仍是：

1. residual pricing / legacy final-judge proof-tail 优化；
2. profile-DP structural control；
3. 或真正的 RMP stabilization 诊断，但不要把它等同于 column-pool duplicate compression。
