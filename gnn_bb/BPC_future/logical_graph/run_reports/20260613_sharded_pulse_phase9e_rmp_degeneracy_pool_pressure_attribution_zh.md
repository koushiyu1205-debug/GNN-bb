# Sharded Pulse Phase 9E RMP Degeneracy / Pool-pressure Attribution 报告

日期：2026-06-13

## 目标

Phase 9E 继续只做 summary / JSONL 归因，不改变 solver 语义。

本轮目标是回答 Phase 9D 后留下的问题：

1. 后续 negative family 是否与 pool duplicate pressure 相关；
2. 后续 negative family 是否与 active fractional pressure 相关；
3. active basis hash 稳定时，dual movement 和 new negative family 是否仍同步出现；
4. 当前是否更应转向 RMP stabilization / pool compression / legacy final judge optimization。

## 实现摘要

### 1. 新增 summary 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中新增：

- `followup_post_first_negative_pool_duplicate_task_sets`
- `followup_post_first_negative_pool_duplicate_task_set_ratio`
- `followup_post_first_negative_pool_active_duplicate_task_sets`
- `followup_post_first_negative_pool_active_duplicate_task_set_ratio`
- `followup_post_first_negative_pool_avg_journeys_per_task_set`
- `followup_post_first_negative_pool_max_journeys_per_task_set`
- `followup_post_first_negative_pool_active_avg_journeys_per_task_set`
- `followup_post_first_negative_pool_active_fractional_value_sum`
- `followup_post_first_negative_pool_active_fractional_value_max`
- `followup_post_first_negative_pool_active_fractional_value_min`
- `followup_post_first_negative_pool_active_fractional_small_value_count`
- `followup_rmp_degeneracy_pressure_class`
- `followup_rmp_degeneracy_pressure_reason`
- 以及对应的 `pulse_worker_followup_*` alias。

### 2. 新增只读 classifier

新增：

- `_classify_rmp_degeneracy_pressure()`

该 classifier 只读取已有 post-first-negative pool / RMP / family-chain 指标，用于区分：

- active / global duplicate pressure；
- active fractional pressure；
- stable basis 下的 overlapping/disjoint new family；
- active basis churn；
- dual move without objective progress；
- no clear degeneracy signal。

### 3. 新增 profile group

新增：

- `phase9e_rmp_degeneracy_pool_pressure_attribution`

包含：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9e_rmp_degeneracy_pool_pressure_attribution_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9e_rmp_degeneracy_pool_pressure_attribution \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9e_rmp_degeneracy_pool_pressure_attribution_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9e_rmp_degeneracy_pool_pressure_attribution_smoke_20260613/summary.csv`

## 关键结果

### 5/10 Guard

- `apollo5`、`tranq5`、`apollo10`、`tranq10_09`：两个 opt-in worker profile 均未触发 worker；
- 5/10 official result 与 baseline 一致；
- critical disagreement count 均为 0。

### Tranq20

`tranq20_01` 在本轮两个 opt-in worker profile 中均未触发 worker，official result 与 baseline 一致，critical disagreement count 为 0。

### Apollo20 coverage-target profile

实例：`mt20_greedy_apollo_01`

- worker added journeys: `8`
- worker added new task sets: `8`
- worker added support-changing count: `0`
- follow-up negative sequence:
  - `4,12,18|5,12,16`
- residual family chain class:
  - `persistent_active_residual_with_overlapping_new_family`
- post-first-negative objective delta:
  - `-40.33852`
- post-first-negative dual L1 delta:
  - `400.061096`
- pool duplicate ratio:
  - `0.0`
- active duplicate ratio:
  - `0.0`
- active fractional ratio after first negative:
  - `0.583333333`
- active fractional value sum:
  - `3.5`
- active basis unique count:
  - `1`
- active basis churn count:
  - `0`
- RMP degeneracy pressure class:
  - `active_fractional_pressure`

### Apollo20 auto-active validation profile

实例：`mt20_greedy_apollo_01`

- worker added journeys: `1`
- worker added new task sets: `0`
- worker added support-changing count: `1`
- follow-up negative sequence:
  - `5,8,15|5,12,18`
- residual family chain class:
  - `persistent_active_residual_with_overlapping_new_family`
- post-first-negative objective delta:
  - `-139.913748`
- post-first-negative dual L1 delta:
  - `139.913748`
- pool duplicate ratio:
  - `0.0`
- active duplicate ratio:
  - `0.0`
- active fractional ratio after first negative:
  - `0.0`
- active fractional value sum:
  - `0.0`
- active basis unique count:
  - `1`
- active basis churn count:
  - `0`
- RMP degeneracy pressure class:
  - `stable_basis_overlapping_family_with_dual_move`

## 解释

Phase 9E 把 Apollo20 两类 tail 分开了：

1. coverage-target profile 有明显 active fractional pressure：
   - active fractional ratio = `0.583333333`；
   - active fractional value sum = `3.5`；
   - pool duplicate pressure 不明显。

2. auto-active validation profile 没有 duplicate / fractional pressure：
   - duplicate ratio = `0.0`；
   - active duplicate ratio = `0.0`；
   - active fractional ratio = `0.0`；
   - 但 active basis 稳定、dual 明显移动，且仍有 overlapping negative family。

因此当前不能把 residual tail 简化成“列池重复过多”。

更准确的判断是：

- 一部分 row 显示 active fractional pressure；
- 另一部分 row 显示 stable active basis + dual movement + overlapping new family；
- 两者都不支持继续扩大 Pulse active worker；
- 下一步更适合转向 RMP degeneracy / active-family stabilization / legacy final judge optimization 的更小诊断。

## Exactness 边界

- 本轮只新增 JSONL/summary 归因字段；
- 不改变 pricing / RMP / driver official decision；
- 不新增 official certificate；
- 不启用 production default；
- 不做 resume；
- 不做 parallel；
- 不改变 prefix RC bound；
- 不扩大 active worker 触发范围。

## 当前结论

Phase 9E 继续支持 Phase 8R 的主结论：当前 Pulse active-worker 路线没有稳定 ROI，继续加预算或加触发器不合理。

下一步建议 Phase 9F：

- 做 RMP stabilization / pool compression 的只读前置诊断；
- 按 active fractional pressure 和 stable-basis overlapping-family 两类 tail 分别归因；
- 检查是否存在可安全减少 replacement/duplicate pressure 的 pool policy；
- 或者直接转向 legacy/profile-DP final judge tail 优化，而不是继续 worker。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_proof_tail_bridge_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

当前结果：

```text
Ran 4 tests in 0.002s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

Whitespace 检查：

```bash
git diff --check
```

结果：通过。

全量 `BPCFutureTests`：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 480 tests in 1.440s
OK (skipped=1)
```
