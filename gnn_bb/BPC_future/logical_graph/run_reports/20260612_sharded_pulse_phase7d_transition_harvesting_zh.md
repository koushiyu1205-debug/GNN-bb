# Sharded Pulse Phase 7D Transition-state Harvesting 报告

日期：2026-06-12

## 目标

本轮只实现 Phase 7D：把 `transition_root_only_pulse()` 发现的 true-RC negative leaves 接入现有 support-aware harvesting。

本轮不做：

- resume；
- parallel；
- adaptive hierarchical sharding；
- prefix RC lower-bound pruning；
- legacy fallback 扩展；
- production benchmark 默认启用。

## 实现摘要

### 1. Transition core 接入 harvest-after-negative

`transition_root_only_pulse()` 新增 opt-in 参数：

- `harvest_after_negative_enabled`
- `support_aware_harvesting_enabled`
- `negative_harvest_limit`
- `active_masks`
- `pool_masks`
- `forbidden_signatures`

发现 true-RC negative 后，如果启用 harvest mode，返回强制退出 proof mode：

- `exhausted=False`
- `status="FOUND_NEGATIVE_HARVESTED"` 或 `FOUND_NEGATIVE`
- `reason="harvest_after_negative"`

即使局部搜索后来已经枚举完，也不能形成 certificate。

### 2. 复用现有 support-aware selector

harvest 逻辑复用：

```python
harvest_support_aware_negative_journeys(...)
```

所有 harvested journeys 仍由 `manual_journey_reduced_cost()` 做 true-RC 过滤。

`forbidden_signatures` 保守处理：

- forbidden negative 仍保留在 `negative_leaves` 中，用于 duplicate-only 判定；
- forbidden negative 不进入 returned harvested columns；
- empty harvest 不表示 no-negative。

### 3. Guarded sharded path 透传 harvest config

`_price_journeys_by_sharded_pulse_guarded()` 现在向每个 first-task shard 传入：

- support-aware harvest 开关；
- harvest limit；
- active support task sets；
- pool task sets；
- forbidden signatures。

archive 与 harvest 保持隔离：当前 guarded path 仍在存在 forbidden signatures 时禁用 archive，避免 dominance 隐藏 duplicate-only 语义。

### 4. 新增诊断字段

`ToyPulseExhaustiveResult`、`JourneyPricingResult` 和 driver JSONL 增加：

- `pulse_negative_pool_size`
- `pulse_harvested_count`
- `pulse_harvested_new_task_set_count`
- `pulse_harvested_support_changing_count`
- `pulse_harvested_replacement_count`

既有字段继续保留：

- `pulse_negative_found`
- `pulse_best_true_rc`

## 新增测试

新增 Phase 7D focused tests：

- `test_transition_pulse_harvest_after_negative_exits_proof_mode`
- `test_transition_pulse_harvest_returns_only_true_rc_negatives`
- `test_transition_pulse_empty_harvest_not_certificate`
- `test_transition_pulse_archive_harvest_matches_unarchived_best_and_negative`
- `test_sharded_pulse_guarded_harvest_diagnostics_surface`
- `test_sharded_pulse_guarded_harvest_duplicate_only_not_certificate`
- `test_sharded_pulse_driver_smoke_harvest_counters_surface`

覆盖语义：

- found-negative 后退出 proof mode；
- harvested columns 全部 true-RC negative；
- empty harvest 不证书；
- duplicate-only 不证书；
- archive + harvest 与 unarchived 在 best true RC / found-negative 语义上一致；
- guarded path 与 driver JSONL 能观测 harvest counters。

## 验证命令

Phase 7D focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_harvest_after_negative_exits_proof_mode \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_harvest_returns_only_true_rc_negatives \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_empty_harvest_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_archive_harvest_matches_unarchived_best_and_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_harvest_diagnostics_surface \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_harvest_duplicate_only_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_harvest_counters_surface
```

结果：

```text
Ran 7 tests in 0.626s
OK
```

Phase 7A-7D focused regression：

```text
Ran 31 tests in 0.223s
OK
```

语法与 diff 检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py

git diff --check
```

结果：通过。

完整回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_bpc_future
```

结果：

```text
Ran 401 tests in 47.612s
OK (skipped=1)
```

## 当前边界

- transition harvest 仍是 opt-in；
- guarded sharded engine 仍不默认启用 production benchmark；
- harvest-after-negative 只影响返回列，不参与 proof closure；
- prefix RC lower-bound pruning 仍未实现，相关 pruning 继续 fail-open；
- resume / parallel / adaptive refinement 仍未实现。

## 结论

Phase 7D 已完成：transition-level root-only Pulse 的 true-RC negative leaves 可以进入 support-aware harvesting，同时保持 proof-search 与 harvest-after-negative 的证书边界。

当前最重要的语义结果是：

1. 发现 negative 后不会 certificate；
2. duplicate-only / empty harvest 不会 certificate；
3. harvested columns 继续由 true-RC 过滤；
4. guarded path 和 driver JSONL 能观测 harvest pool 与 selection 诊断。

下一步建议 Phase 7E：实现 safe prefix RC lower-bound ledger，但只允许已证明安全的 row/cut/fleet contribution 参与 bound pruning；不安全的 contribution 继续 fail-open。
