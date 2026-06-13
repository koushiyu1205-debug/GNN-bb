# Sharded Pulse Phase 8P Active Source Seed Matrix 报告

日期：2026-06-13

## 目标

本轮做 Phase 8P：expanded active source seed matrix。

目标不是打开 production worker，也不是让 Pulse 参与 official certificate。目标是扩大但仍受控地搜索 active residual source，确认是否存在 `same_task_set` / `overlapping_task_set` 的 source，并判断它是否有继续做 worker ROI 的价值。

## 实现摘要

### 1. 新增 instance group

新增：

- `phase8p_20_source_seed_matrix`

当前包含：

- `mt20_greedy_apollo_01`
- `mt20_greedy_tranq_01`
- `tranq20_01`

旧 `apollo20_01` 未放入默认 group。第一次 smoke 触发：

```text
ValueError: task 17 has no feasible single-task timed trip on the configured grid
```

这属于 instance/grid feasibility preflight 问题，不计为算法失败。

### 2. 新增 profile group

新增：

- `phase8p_active_source_seed_matrix`

展开为：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown_ordered`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate`

### 3. 新增 outcome 字段

`summary.json/csv` 新增：

- `active_residual_source_search_outcome_class`
- `active_residual_source_search_recommendation`

分类包括：

- `passed_source_available`
- `no_source_candidate`
- `disjoint_only_no_passed_source`
- `no_active_signal_only`
- `blocked_mixed_no_passed_source`

这些字段只读，不参与 solver 决策。

## Smoke Matrix

输出目录：

```text
BPC_future/results/sharded_pulse_phase8p_active_source_seed_matrix_smoke_v2_20260613
```

运行实例：

- `apollo5`
- `tranq5`
- `apollo10`
- `tranq10_09`
- `mt20_greedy_apollo_01`
- `mt20_greedy_tranq_01`
- `tranq20_01`

运行 profile：

- `phase8p_active_source_seed_matrix`

规模汇总：

| scale | rows | official changed | critical disagreement | worker triggers | passed source |
|---:|---:|---:|---:|---:|---:|
| 5 | 14 | 0 | 0 | 0 | 0 |
| 10 | 14 | 0 | 0 | 0 | 0 |
| 20 | 21 | 6 seed rows | 0 | 7 | 1 |

## 关键观测

Apollo20 greedy-anchor 找到一个 passed source：

- source profile：`coverage_target_priority`
- residual candidate：`12,4,18`
- relation：`overlapping_task_set`
- source-search outcome：`passed_source_available`

随后 auto-active diagnostic 使用该 target：

- `auto_residual_target_applied=True`
- `auto_residual_target_sequence=12,4,18`
- worker triggered
- worker added journeys = `1`
- `worker_added_support_changing_count=1`
- addition class = `active_replacement_task_set`

但 follow-up tail 仍没有消失：

- follow-up residual negative = `8,15,5`
- relation = `disjoint_task_set`

strict auto-active ROI profile 也提取到 `12,4,18`，但 worker 未触发：

- skip reason = `max_cg_iter_exceeded`

Tranq greedy 与 `tranq20_01` 在同一短预算下没有产生 passed active source。

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
--output-dir BPC_future/results/sharded_pulse_phase8p_active_source_seed_matrix_smoke_v2_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 phase8p_20_source_seed_matrix \
--profiles phase8p_active_source_seed_matrix \
--time-limit 1.2 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 3 \
--current-probe-time-limit 0.5 \
--profile-mask-diagnostics \
--quiet
```

结果：`summary.json` / `summary.csv` 已生成。

## Exactness 边界

- 只新增 calibration groups 与 summary diagnostics；
- 不改变默认 benchmark；
- 不改变 production worker 默认；
- 不打开 official certificate gate；
- 不允许 incomplete / no-column / duplicate-only 更新 official lower bound；
- 所有 worker-added columns 仍走既有 true-RC add-column path；
- source-search 统计只读，不参与证明。

## 结论

Phase 8P 说明 8O 的 “no passed source” 不是最终负结论：扩大 seed matrix 后确实能找到一个 overlapping active residual source。

但 ROI 仍不足：

- active auto diagnostic 只加入 1 个 active-replacement 列；
- follow-up residual negative 没消失；
- residual family 切回 disjoint `8,15,5`；
- strict ROI gate 下仍不触发。

当前仍不能打开 production worker 或 official certificate gate。下一步应做 Phase 8Q：passed-source ROI validation / negative-result decision。如果 passed source 不能稳定降低 tail，应停止继续扩大 Pulse active-worker 主线，转向 non-worker 路线。
