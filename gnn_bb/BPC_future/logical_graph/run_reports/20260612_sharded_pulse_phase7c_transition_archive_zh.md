# Sharded Pulse Phase 7C Transition Archive 接入报告

日期：2026-06-12

## 目标

Phase 7C 只接入 `StructuralKeyDominanceArchive -> transition_root_only_pulse()`。

本轮不做：

- resume；
- parallel；
- adaptive sharding；
- prefix RC bound pruning；
- harvesting；
- production benchmark 默认开启。

## 实现摘要

### 1. Transition state archive

`transition_root_only_pulse()` 新增 opt-in 参数：

- `archive_dominance_enabled`
- `archive_max_records_per_key`

archive 只在当前 DFS 调用内生效，不写入 ledger，不作为 proof-closed record。

### 2. Exact-safe dominance 规则

waiting-allowed：

- same structural key；
- `partial_rc <=`；
- `energy <=`；
- `load <=`；
- `current_time <=`。

no-wait：

- structural key 额外包含 exact current time；
- record 使用 singleton interval；
- 不允许“更早时间”单独支配。

archive cap：

- 表满时只丢旧 record；
- 不丢当前 state；
- 不把当前 state 当 dominated。

### 3. Guarded path 接入

guarded sharded final judge 继续调用 `transition_root_only_pulse()`，并透传：

- `pulse_archive_dominance_enabled`
- `pulse_archive_max_records_per_key`

同时增加一个安全 guard：

- 若存在 `forbidden_journey_signatures`，guarded path 禁用 archive。

原因是 archive 可能用一个 forbidden duplicate signature 对另一个新 signature 做结构支配；在 forbidden context 下这会污染 duplicate-only 语义。

## 测试覆盖

新增/更新 focused tests：

- `test_transition_pulse_archive_matches_unarchived_best_and_negative`
- `test_transition_pulse_archive_cap_fail_open_matches_unarchived`
- `test_transition_pulse_archive_no_wait_matches_unarchived_without_time_dominance`
- `test_sharded_pulse_guarded_archive_counter_surfaces`
- `test_sharded_pulse_driver_smoke_archive_counter_surfaces`

复用既有 archive exactness tests：

- `test_pulse_archive_cap_drops_old_records_without_pruning_current`
- `test_pulse_archive_no_wait_earlier_time_alone_not_dominance`
- `test_pulse_archive_depot_ready_dominance_prunes_later_equivalent_state`

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_archive_matches_unarchived_best_and_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_archive_cap_fail_open_matches_unarchived \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_archive_no_wait_matches_unarchived_without_time_dominance \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_archive_counter_surfaces \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_archive_counter_surfaces \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_archive_cap_drops_old_records_without_pruning_current \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_archive_no_wait_earlier_time_alone_not_dominance \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_archive_depot_ready_dominance_prunes_later_equivalent_state
```

结果：

```text
Ran 8 tests in 0.619s
OK
```

## 当前边界

- archive-enabled transition Pulse 可能减少候选 signature 数；验收标准是 best true RC / found-negative / no-negative exhaustive 与 archive-disabled 一致；
- forbidden signature context 下 guarded path 禁用 archive；
- no-wait 下没有使用“更早时间”支配；
- archive 不是 proof-closed cache，不能用于 resume certificate。

## 结论

Phase 7C 已完成：`StructuralKeyDominanceArchive` 已接入 transition-level root-only Pulse，并保持 opt-in、fail-open、no-wait 保守、forbidden context 禁用的 exactness 边界。

下一步建议 Phase 7D：只接入 transition-state harvesting，继续要求 found-negative 后退出 proof mode、empty harvest 不证书、duplicate-only 不证书。
