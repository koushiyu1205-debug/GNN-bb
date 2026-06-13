# Sharded Pulse Phase 8O Active Residual Source Search 报告

日期：2026-06-13

## 目标

本轮只做 Phase 8O：active residual source search / seed matrix。

目标是回答：

1. 在短矩阵中是否存在 `same_task_set` / `overlapping_task_set` 的 active residual source；
2. active auto target 是否能在这种 source 上应用；
3. 是否继续保持 5/10 no-regression、no critical disagreement、no certificate effect。

本轮不做 production worker 默认开启、official certificate gate、resume、parallel、20/100 A/B，也不扩大 worker time limit。

## 实现摘要

### 1. Profile group

新增 profile group：

- `phase8o_active_source_search`

展开为：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate`

该 group 只方便 seed matrix 调用；不改变任何默认 benchmark profile。

### 2. Row-level active source diagnostics

`summary.json/csv` 新增：

- `active_residual_source_candidate`
- `active_residual_source_candidate_sequence`
- `active_residual_source_context_hash`
- `active_residual_source_relation`
- `active_residual_source_active_signal_count`
- `active_residual_source_gate_reason`
- `active_residual_source_passed`

这些字段用于判断当前 row 自身是否可作为 active residual source。

### 3. Previous-row source-search diagnostics

auto-active rows 新增：

- `active_residual_source_search_candidate_count`
- `active_residual_source_search_passed_count`
- `active_residual_source_search_blocked_count`
- `active_residual_source_search_blocked_disjoint_count`
- `active_residual_source_search_blocked_no_active_count`
- `active_residual_source_search_blocked_relation_count`
- `active_residual_source_search_first_passed_*`
- `active_residual_source_search_first_blocked_*`

这些字段用于区分“没有 source”和“有 source 但被 active gate 阻断”。

## Smoke Matrix

输出目录：

```text
BPC_future/results/sharded_pulse_phase8o_active_source_search_smoke_20260613
```

运行实例：

- `apollo5`
- `tranq5`
- `apollo10`
- `tranq10_09`
- `mt20_greedy_apollo_01`
- `mt20_greedy_tranq_01`

关键结果：

| scale | rows | official changed | critical disagreement | worker triggers | passed source |
|---:|---:|---:|---:|---:|---:|
| 5 | 10 | 0 | 0 | 0 | 0 |
| 10 | 10 | 0 | 0 | 0 | 0 |
| 20 | 10 | 2 seed rows | 0 | 2 seed rows | 0 |

Apollo20 seed rows：

- worker added `3 / 3`；
- active-support-changing count = `1`；
- follow-up residual sequence = `8,15,5`；
- relation = `disjoint_task_set`；
- active source gate reason = `residual_disjoint_from_worker`。

Apollo20 auto-active rows：

- `active_residual_source_search_candidate_count = 2`
- `active_residual_source_search_passed_count = 0`
- `active_residual_source_search_blocked_disjoint_count = 2`
- active auto target 未应用；
- worker 未 fallback 成 untargeted worker。

Tranq20 在同一短预算下没有产生 candidate source。

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
Ran 3 tests in 0.001s
OK
```

Smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase8o_active_source_search_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 mt20_greedy_tranq_01 \
--profiles phase8o_active_source_search \
--time-limit 1.5 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 3 \
--current-probe-time-limit 0.5 \
--profile-mask-diagnostics \
--quiet
```

结果：`summary.json` / `summary.csv` 已生成。

## Exactness 边界

- 只新增 calibration profile group 和 summary diagnostics；
- 不改变默认 benchmark；
- 不改变 worker trigger 的 production 默认；
- 不允许 Pulse incomplete / no-column / duplicate-only 更新 official lower bound；
- 不打开 official certificate gate；
- 所有 worker-added columns 仍走既有 true-RC / add-column path；
- source-search 统计只读，不参与证明。

## 结论

Phase 8O 第一版完成：source-search 机制可以明确记录 candidate / passed / blocked-disjoint。当前短矩阵没有发现 same/overlapping active residual source；Apollo20 的 candidate 仍被判定为 disjoint residual，Tranq20 没有 candidate。

这不是 correctness blocker，也不是 worker ROI 证明。它说明继续追逐 8M/8N 的 disjoint residual target 没有依据。下一步应扩大但仍受控地搜索 source seeds，或准备转向 non-Pulse-worker 主线。
