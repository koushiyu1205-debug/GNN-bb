# Sharded Pulse Phase 7B Guarded Transition Engine 接入报告

日期：2026-06-12

## 目标

Phase 7B 只做一件事：把 `transition_root_only_pulse()` 接到 guarded sharded final judge 的 opt-in test path，替换旧 completed-trace toy engine。

本轮不做：

- 默认 benchmark 启用；
- resume；
- parallel；
- adaptive hierarchical refinement；
- prefix RC bound pruning；
- dominance archive；
- harvesting；
- production full certificate。

## 实现摘要

### 1. Shard executor 替换

`BPC_future/pricing/journey_pricing.py` 中 guarded sharded engine 的 first-task shard executor 已改为：

```python
transition_root_only_pulse(...)
```

旧 `toy_root_exhaustive_pulse()` 仍保留，用作 brute-force / completed-trace 对照测试，不再作为 guarded sharded path 的 shard executor。

### 2. Certificate guard 不变

保持原有边界：

- 仍需显式 opt-in；
- 仍只允许 `very_small` / `test*` 在 `sharded_final_judge_toy_certificate_enabled=True` 下 certificate；
- non-test instance 即使开启 toy certificate config，也只能返回 incomplete，不能闭合；
- `FOUND_NEGATIVE` / `INCOMPLETE_LIMIT` / `DUPLICATE_ONLY` 仍不产生 official lower bound。

### 3. Transition counters 透传

`JourneyPricingResult` 和 driver `journey_pricing` JSONL 日志新增：

- `transition_time_window_pruned`
- `transition_energy_pruned`
- `transition_return_pruned`
- `pulse_capacity_pruned`
- `pulse_energy_pruned`

原有兼容字段仍保留：

- `pulse_resource_pruned`
- `pulse_return_pruned`
- `pulse_time_window_pruned`

## 验证覆盖

Phase 7B focused tests 覆盖：

1. guarded sharded engine 使用 `transition_root_only_pulse()`；
2. very_small all shards certified -> `sharded_pulse_no_negative_journey`；
3. very_small negative shard -> `FOUND_NEGATIVE`，不证书；
4. incomplete shard -> `INCOMPLETE_LIMIT`，不证书；
5. transition pruning counters 在 `price_journeys` result 中可观测；
6. transition pruning counters 在 driver `journey_pricing` JSONL 中可观测；
7. production non-test instance 不能由 test-only toy certificate 直接闭合；
8. default config 行为不变。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_certifies_very_small_no_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_incomplete_no_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_transition_pruning_counters_surface \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_non_test_instance_never_toy_certifies \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_duplicate_only_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_unsupported_branch_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_separate_branch_filters_pair_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_same_branch_filters_one_sided_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_without_dummy_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_default_off
```

结果：

```text
Ran 11 tests in 0.064s
OK
```

## 当前边界

- driver all-certified official lower bound 仍主要由 dummy smoke 覆盖；真实 `solve_bpc_future_journey()` 的 RMP dual 由求解过程决定，不在本轮强行伪造；
- transition engine 已进入 guarded opt-in sharded path，但 certificate guard 仍限制在 `very_small` / `test*`；
- archive / harvesting 暂未接入 transition state；
- 5/10/20 benchmark 默认不启用该 path。

## 结论

Phase 7B 已完成：guarded sharded final judge 的 shard engine 已从 completed-trace toy enumerator 替换为 transition-level root-only Pulse core。证书边界保持不变，transition pruning counters 可以从 `JourneyPricingResult` 和 driver JSONL 日志观测到。

下一步建议 Phase 7C：只接入 transition-state `StructuralKeyDominanceArchive`，要求 archive-enabled 与 archive-disabled 在 toy 上结果一致，并验证 `archive_pruned > 0`、archive cap fail-open、no-wait dominance 不误剪。
