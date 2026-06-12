# Sharded Pulse Phase 3B-5 实施报告

日期：2026-06-11

## 实施范围

本轮从 Phase 3B 继续实现 `Sharded + Guarded Pulse Final Judge` 的剩余主线，但仍保持默认关闭。

已实现：

1. Phase 3B：root-only toy exhaustive Pulse DFS；
2. Phase 3C：cheap exact-safe pruning；
3. Phase 4.1：Structural-Key Dominance Archive；
4. Phase 4.2：Support-Aware Harvesting；
5. Phase 5：first-task sharded production entry 与 driver opt-in；
6. Phase 6 部分：second-action child shard toy partition、resume/parallel config skeleton。

## 文件改动

- `BPC_future/pricing/pulse_toy_exhaustive.py`
  - 新增/扩展 root-only toy Pulse；
  - 默认无剪枝；
  - 可选 exact-safe pruning、archive、harvest；
  - first-task shard 与 second-action child shard；
  - deadline / recursion limit fail-open。

- `BPC_future/pricing/pulse_archive.py`
  - 新增 structural-key dominance archive；
  - waiting/no-wait 不同 dominance 条件；
  - archive cap 只丢旧记录，不丢当前状态。

- `BPC_future/pricing/journey_pricing.py`
  - 接入 non-dummy sharded Pulse guarded engine；
  - 增加 Pulse diagnostics；
  - certificate guard 保持严格；
  - duplicate-only 不证书。

- `BPC_future/solver/journey_driver.py`
  - driver opt-in config 映射；
  - journey pricing 日志增加 Pulse counters；
  - dummy test-only guard 保持。

- `BPC_future/tests/test_bpc_future.py`
  - 增加 Phase 3B/3C/4/5 focused tests；
  - 增加 second-action child shard partition 测试；
  - 保留 Phase 2.5 dummy guard 回归。

## 当前算法结构

1. Driver 默认使用原有 pricing/final judge。
2. 若配置启用 sharded pulse：
   - dummy engine 只有 test-only guards 全部满足才运行；
   - 否则进入 real guarded sharded Pulse path。
3. Real guarded path：
   - 按 first-task 建 shard；
   - 每个 shard 调用 root-only toy Pulse；
   - leaf 通过 Phase 3A helper 物化；
   - true RC 用 `manual_journey_reduced_cost()`；
   - negative 立即按 true-RC 返回；
   - duplicate-only 返回 `DUPLICATE_ONLY`；
   - timeout / recursion / unsupported 返回 `INCOMPLETE`;
   - all shards certified 且 certificate guard 允许时，返回 `sharded_pulse_no_negative_journey`。

## Exactness 边界

- `DUPLICATE_ONLY` 永不 promotion；
- `FOUND_NEGATIVE` 永不 certificate；
- harvest-after-negative 永不 certificate；
- bound pruning 当前 fail-open；
- dummy certificate 必须 `sharded_pulse_dummy` 且 test-only guards 全满足；
- production certificate guard 只允许 `very_small` / `test*` toy case；
- 大实例如果没有完整 proof，不会产生 official lower bound。

## 测试摘要

已跑 focused tests：

- Phase 3B/3C/4/5 focused：30 tests，OK；
- Phase 2.5 guard / certificate regression：35 tests，OK；
- `py_compile`：通过；
- `git diff --check`：通过。

## 未完成项

1. 真正 incremental open-sortie Pulse core 尚未实现；
2. prefix RC safe lower-bound pruning 尚未实现；
3. same_vehicle obligation 尚未编译进中间状态，只在 leaf feasibility 过滤；
4. persistent resume / proof-closed prefix cache 尚未实现；
5. hierarchical refinement 尚未接 production 调度；
6. parallel worker merge 尚未实现。

## 风险

当前实现可以验证证书状态机、物化语义、toy exhaustive search、cheap pruning 和 guarded driver path，但不能解决 20/100 规模的 final judge proof tail。大实例启用时必须设置短 time limit / recursion cap，并预期大概率返回 `INCOMPLETE` 或只采到少量 true-RC negative columns。
