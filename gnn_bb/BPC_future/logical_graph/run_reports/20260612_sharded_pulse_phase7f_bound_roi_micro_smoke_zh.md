# Sharded Pulse Phase 7F Bound ROI Micro-smoke 报告

日期：2026-06-12

## 目标

本轮只做 Phase 7F：`Bound / Archive / Harvest micro-smoke 与 ROI gate`。

目标不是增强 prefix reduced-cost bound，也不是跑 20/100 benchmark，而是先确认：

1. bound pruning 的启用、支持、fail-open 原因可以在 `JourneyPricingResult` 与 JSONL 中观测；
2. archive off/on 与 bound off/on 组合在 toy 上不改变 exactness surface；
3. very_small / 5-task / 10-task opt-in micro-smoke 中，weak safe LB 是否真的有剪枝信号；
4. archive + bound + harvest 不互相污染证书语义。

## 实现摘要

### 1. Bound ROI diagnostics

`JourneyPricingResult` 新增并透传到 driver JSONL：

- `pulse_bound_prune_enabled`
- `pulse_bound_prune_supported`
- `pulse_bound_prune_fail_open_reason`
- `pulse_bound_prune_query_count`
- `pulse_bound_prune_winner_count`
- `pulse_bound_prune_time`

已有的 `pulse_bound_pruned` 保持作为 winner counter。

当前 fail-open reason：

- `disabled`
- `cuts_present`
- `negative_arc_cost`
- `negative_service_cost`
- `missing_return_lb`
- `missing_outbound_lb`

`remaining_tasks` 为空不是 fail-open 原因，不写入 diagnostics。

### 2. Guarded sharded 聚合

`_price_journeys_by_sharded_pulse_guarded()` 现在聚合所有 first-task shard 的：

- bound query count；
- bound winner count；
- bound query time；
- supported flag；
- fail-open reason。

若配置未启用 bound pruning，则 `pulse_bound_prune_fail_open_reason="disabled"`。

### 3. Archive / bound 组合回归

新增 toy regression 覆盖：

- archive off + bound off
- archive on + bound off
- archive off + bound on
- archive on + bound on

要求：

- `best_true_reduced_cost` 一致；
- `found_negative` 一致；
- negative signatures 一致；
- bound on 时 query count 可观测。

### 4. Driver JSONL smoke

新增 driver smoke，确认 opt-in guarded sharded path 的 `journey_pricing` 事件中包含 bound diagnostics 字段。

## Micro-smoke 设置

实例：

- `very_small`
- Apollo 5：`apollo15_20km_greedy-anchor_randomtw_tasks005_01_seed46001`
- Tranquillitatis 5：`tranquillitatis_balmer_like_20km_balanced_tasks05_01_seed136000`
- Apollo 10：`apollo15_20km_greedy-anchor_randomtw_tasks010_01_seed51001`

配置矩阵：

| 配置 | 含义 |
|---|---|
| A | default baseline |
| B | sharded transition, archive off, bound off |
| C | sharded transition, archive on, bound off |
| D | sharded transition, archive on, bound on |
| E | archive + bound + harvest |

约束：

- 只调用 `price_journeys()`；
- 不接 production default；
- 5-task cap 为 `time_limit=0.35s`、`pulse_max_recursions=25000`；
- 10-task cap 为 `time_limit=0.55s`、`pulse_max_recursions=45000`；
- 非 test instance 即使 opt-in，也不能由 toy certificate guard 形成 official certificate。

## Micro-smoke 结果摘要

### very_small

| 配置 | pricing_state | recursions | expanded | materialized journeys | archive pruned | bound pruned | wall_s |
|---|---|---:|---:|---:|---:|---:|---:|
| A | LOCAL_NO_COLUMN_UNCERTIFIED | 0 | 0 | 0 | 0 | 0 | 0.000229 |
| B | CERTIFIED_NO_NEGATIVE | 113 | 113 | 93 | 0 | 0 | 0.005976 |
| C | CERTIFIED_NO_NEGATIVE | 113 | 113 | 93 | 0 | 0 | 0.005964 |
| D | CERTIFIED_NO_NEGATIVE | 12 | 8 | 4 | 0 | 8 | 0.000421 |
| E | CERTIFIED_NO_NEGATIVE | 12 | 8 | 4 | 0 | 8 | 0.000864 |

### Apollo 5

| 配置 | pricing_state | recursions | expanded | materialized journeys | archive pruned | bound pruned | wall_s |
|---|---|---:|---:|---:|---:|---:|---:|
| A | LOCAL_NO_COLUMN_UNCERTIFIED | 0 | 0 | 0 | 0 | 0 | 0.000346 |
| B | INCOMPLETE_LIMIT | 121 | 121 | 84 | 0 | 0 | 0.021571 |
| C | INCOMPLETE_LIMIT | 109 | 103 | 75 | 6 | 0 | 0.021993 |
| D | INCOMPLETE_LIMIT | 23 | 10 | 13 | 3 | 15 | 0.002115 |
| E | INCOMPLETE_LIMIT | 23 | 10 | 13 | 3 | 15 | 0.001903 |

### Tranquillitatis 5

| 配置 | pricing_state | recursions | expanded | materialized journeys | archive pruned | bound pruned | wall_s |
|---|---|---:|---:|---:|---:|---:|---:|
| A | LOCAL_NO_COLUMN_UNCERTIFIED | 0 | 0 | 0 | 0 | 0 | 0.000327 |
| B | INCOMPLETE_LIMIT | 1036 | 1036 | 753 | 0 | 0 | 0.353365 |
| C | INCOMPLETE_LIMIT | 961 | 818 | 696 | 143 | 0 | 0.382618 |
| D | INCOMPLETE_LIMIT | 29 | 11 | 18 | 2 | 22 | 0.003810 |
| E | INCOMPLETE_LIMIT | 29 | 11 | 18 | 2 | 22 | 0.002955 |

### Apollo 10

| 配置 | pricing_state | recursions | expanded | materialized journeys | archive pruned | bound pruned | wall_s |
|---|---|---:|---:|---:|---:|---:|---:|
| A | LOCAL_NO_COLUMN_UNCERTIFIED | 0 | 0 | 0 | 0 | 0 | 0.002229 |
| B | INCOMPLETE_LIMIT | 1876 | 1876 | 928 | 0 | 0 | 0.553125 |
| C | INCOMPLETE_LIMIT | 1815 | 1775 | 898 | 40 | 0 | 0.553337 |
| D | INCOMPLETE_LIMIT | 47 | 21 | 26 | 3 | 34 | 0.004966 |
| E | INCOMPLETE_LIMIT | 47 | 21 | 26 | 3 | 34 | 0.004407 |

## ROI 判断

这轮 micro-smoke 给出正向信号：

- bound on 后，`pulse_bound_pruned > 0`；
- recursions / expanded / materialized journeys 在 5-task 与 10-task smoke 中明显下降；
- `pulse_bound_prune_supported=True`，fail-open reason 为空，说明该批无 cut / 非负成本场景确实进入了 bound path；
- archive 单独有剪枝信号，但在这批 smoke 中 weaker than bound；
- harvest 在零 dual negative 场景下没有新增返回列，符合预期；
- 非 test 实例仍由 toy certificate guard 返回 `INCOMPLETE_LIMIT`，没有产生 production certificate。

这说明 weak safe LB 框架值得保留，但还不能据此直接加入 cut / subset-row / fleet-cut prefix bound。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_bound_pruning_fails_open_with_cuts \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_bound_pruning_matches_unpruned_and_prunes \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_archive_bound_combinations_match \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_bound_counter_surfaces \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_bound_diagnostics_surface
```

结果：

```text
Ran 5 tests in 0.627s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

完整 `BPCFutureTests` 回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 408 tests in 50.291s
OK (skipped=1)
```

## 当前边界

- 未加入 cut / subset-row / fleet-cut prefix lower bound；
- 未做 resume；
- 未做 parallel；
- 未做 adaptive hierarchical sharding；
- 未做 20/100 A/B；
- 未默认开启 production benchmark；
- micro-smoke 只作为 ROI gate，不是性能结论。

## 结论

Phase 7F 完成：bound pruning 的 ROI diagnostics 已进入 result / JSONL，archive/bound 组合 exactness 有 focused regression，micro-smoke 显示 weak safe LB 在小实例上有明显剪枝信号。

下一步不应直接大改 production path。若继续做 7G，建议只选择一个可独立证明 exact-safe 的加强项；如果后续真实小实例 ROI 变弱，则优先转向 adaptive second-action shard refinement，而不是先加复杂 cut/subset-row prefix correction。
