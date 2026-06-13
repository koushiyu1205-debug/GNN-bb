# Sharded Pulse Phase 8Q Passed-source ROI Validation 报告

日期：2026-06-13

## 目标

本轮做 Phase 8Q：passed-source ROI validation / negative-result decision。

Phase 8P 找到了一个 `overlapping_task_set` 的 passed source：`12,4,18`。Phase 8Q 的目标是验证它是否可重复产生有效 tail 改善，而不是只证明 worker 能加列。

本轮不做 production worker 默认开启，不做 official certificate gate，不做 resume / parallel / 20/100 A/B。

## 实现摘要

### 1. Validation profiles

新增：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate`

它们和 auto-active target profiles 共用 same active-source gate / context hash guard。新增 profile 只是为了在同一个 calibration run 中重复应用 passed source，避免 profile 去重导致无法复测。

### 2. Profile group

新增：

- `phase8q_passed_source_roi_validation`

展开为：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_roi_gate`

## Smoke Matrix

输出目录：

```text
BPC_future/results/sharded_pulse_phase8q_passed_source_roi_validation_smoke_20260613
```

运行实例：

- `apollo5`
- `tranq5`
- `apollo10`
- `tranq10_09`
- `mt20_greedy_apollo_01`
- `mt20_greedy_tranq_01`
- `tranq20_01`

运行参数：

```text
time_limit=1.8
pricing_time_limit=0.2
pricing_max_dp_states=1000
max_cg_iterations=4
current_probe_time_limit=0.8
```

规模汇总：

| scale | rows | official changed | critical disagreement | worker triggers | passed source |
|---:|---:|---:|---:|---:|---:|
| 5 | 10 | 0 | 0 | 0 | 0 |
| 10 | 10 | 0 | 0 | 0 | 0 |
| 20 | 15 | 5 seed/diagnostic rows | 0 | 3 | 1 |

## 关键结果

Apollo20 greedy-anchor：

1. `coverage_target_priority`
   - worker added journeys = `8`
   - support-changing = `0`
   - follow-up residual = `12,4,18`
   - relation = `overlapping_task_set`

2. `auto_active_residual_target_diagnostic`
   - auto target = `12,4,18`
   - worker added journeys = `1`
   - support-changing = `1`
   - addition class = `active_replacement_task_set`
   - follow-up residual = `8,15,5`
   - relation = `disjoint_task_set`
   - RMP objective delta = `-0.760334`

3. `auto_active_residual_target_validation_diagnostic`
   - auto target = `12,4,18`
   - worker added journeys = `1`
   - support-changing = `1`
   - addition class = `active_replacement_task_set`
   - follow-up residual = `8,15,5`
   - relation = `disjoint_task_set`
   - RMP objective delta = `-0.760334`

4. `auto_active_residual_target_validation_roi_gate`
   - auto target = `12,4,18`
   - worker not triggered
   - skip reason = `max_cg_iter_exceeded`

Tranq greedy / tranq20_01：

- 没有 passed source；
- worker 不触发；
- official result unchanged。

## 判断

Phase 8Q 证明：

- passed source `12,4,18` 可重复提取；
- auto-active diagnostic 可重复加 1 个 active-replacement column；
- 但该列没有消除 residual tail；
- residual negative 反复回到 disjoint `8,15,5`；
- strict ROI gate 下仍不触发 worker；
- 在该短预算下，Apollo20 validation rows 没有比 baseline 形成稳定 primal/tail 改善。

因此这不是 worker ROI 正信号。它支持停止继续扩大 Pulse active-worker 主线，准备 negative-result / pivot report。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_auto_residual_target_uses_prior_context \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 3 tests in 0.002s
OK
```

Smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase8q_passed_source_roi_validation_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 mt20_greedy_tranq_01 tranq20_01 \
--profiles phase8q_passed_source_roi_validation \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

结果：`summary.json` / `summary.csv` 已生成。

## Exactness 边界

- 只新增 opt-in calibration validation profiles；
- 不改变默认 benchmark；
- 不打开 production worker；
- 不打开 official certificate gate；
- 不允许 Pulse incomplete / no-column / duplicate-only 更新 official lower bound；
- 所有 worker-added columns 仍走既有 true-RC add-column path；
- source-search 与 validation 统计只读，不参与 proof。

## 结论

Phase 8Q 未发现 passed-source worker ROI。`12,4,18` 可以重复应用，但只产生 active-replacement column，不能消除 disjoint residual tail。

下一步建议 Phase 8R：Pulse active-worker negative-result / pivot report。重点是整理 7O-8Q 的连续证据，判断是否满足停止继续扩大 Pulse active-worker 的条件，并转向 legacy/profile-DP proof-tail structural control、RMP stabilization、active fractional degeneracy 或 proof-closed resume。
