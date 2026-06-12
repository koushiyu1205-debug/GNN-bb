# Sharded Pulse Final Judge 计划

日期：2026-06-11

## 目标

`Sharded Pulse Final Judge` 的目标是把原本单体、不可中断的 true-dual final judge 重构为：

- first-task shard；
- 可中断、可诊断；
- 只在完整 proof-search 穷尽时给出 `CERTIFIED_NO_NEGATIVE`；
- `INCOMPLETE` / `DUPLICATE_ONLY` / `FOUND_NEGATIVE` 永远不产生 official lower bound；
- 默认关闭，通过 opt-in config 启用。

当前实现重点是证书状态机、Phase 3A leaf materialization contract、Phase 3B toy exhaustive Pulse、Phase 3C cheap exact-safe pruning、Phase 4 structural archive / harvesting、Phase 5 guarded first-task sharded engine。

## Exactness 边界

证书成立条件：

1. 当前 true dual / cuts / branch / forbidden signatures / config 下所有 required shards 完整穷尽；
2. 每个 certified shard 必须 `proof_closed=True` 或等价完整 proof-search；
3. `JourneyPricingResult.reason == "sharded_pulse_no_negative_journey"`；
4. `final_judge_engine == "sharded_pulse"` 或 test-only `sharded_pulse_dummy`；
5. `global_certificate_capable=True` 且 `final_judge_certificate_capable=True`；
6. `status == "OPTIMAL"` 且无返回负列。

非证书状态：

- `FOUND_NEGATIVE`：只表示发现 true-RC negative column；
- `DUPLICATE_ONLY`：只表示没有新可返回列，不表示无负列；
- `INCOMPLETE` / timeout / recursion limit / unsupported branch：不得更新 official lower bound；
- harvest-after-negative：已退出 proof mode，不得 certificate；
- dummy all-certified：仅 test-only，必须配置 guard、instance guard 和环境变量 guard 同时满足。

## 当前模块

- `BPC_future/pricing/sharded_pulse_final_judge.py`
  - `ShardProofStatus`
  - `ShardProofRecord`
  - `ShardLedger`
  - `ShardCacheKey`
  - dummy shard ledger

- `BPC_future/pricing/pulse_materialization.py`
  - `PulseSortieTrace`
  - `PulseLeafCandidate`
  - `materialize_pulse_sortie()`
  - `materialize_pulse_journey()`
  - `materialize_pulse_leaf_candidate()`
  - `materialize_negative_pulse_leaf()`

- `BPC_future/pricing/pulse_toy_exhaustive.py`
  - root-only toy exhaustive Pulse
  - first-task shard
  - optional second-action child shard
  - exact-safe resource/time/return pruning
  - optional archive
  - optional harvest-after-negative

- `BPC_future/pricing/pulse_archive.py`
  - `PulseStructuralKey`
  - `PulseArchiveRecord`
  - `StructuralKeyDominanceArchive`

## Phase 状态

### Phase 1-2.5

已完成：

- ledger skeleton；
- cache key builder；
- dummy shard engine；
- driver smoke；
- certificate reason guard；
- dummy test-only guard。

### Phase 3A

已完成：

- Pulse leaf 不手搓 `JourneyColumn`；
- sortie 通过 `evaluate_timed_trip()` 回放；
- journey 通过 `make_journey()`；
- true RC 通过 `manual_journey_reduced_cost()`；
- arc option 数量不匹配是内部 trace 错误，测试中抛 `ValueError`。

### Phase 3B

已完成：

- root-only toy exhaustive Pulse；
- 与独立 brute-force enumerator 对齐；
- first-task shard partition；
- no-wait toy case；
- deadline / max_recursions fail-open。

### Phase 3C

已完成的 cheap exact-safe pruning：

- resource / capacity；
- time-window transition；
- return feasibility；
- bound pruning 目前 fail-open。

未实现：

- 完整 prefix reduced-cost lower-bound pruning；
- cut/fleet/branch row contribution 的通用安全下界。

### Phase 4

已完成：

- structural-key dominance archive；
- archive cap fail-open；
- waiting/no-wait dominance 边界；
- support-aware harvesting 接入；
- harvest-after-negative 退出 proof mode。

### Phase 5

已完成：

- first-task sharded production entry；
- opt-in driver path；
- true negative 返回 `FOUND_NEGATIVE`；
- all-certified toy/very_small guard 下返回 `CERTIFIED_NO_NEGATIVE`；
- same/separate branch 通过 leaf feasibility 过滤；
- unsupported branch 不证书；
- dummy 不进入 production path。

当前限制：

- production certificate guard 只允许 `very_small` / `test*`；
- 真实 5/10/20 大实例默认不会由 toy Pulse 证书化；
- Phase 5 仍是 root-only toy Pulse，不是完整连续时间 Pulse proof engine。

### Phase 6

已完成：

- cache key 包含 true dual / cut / branch / forbidden / config / schema / proof version；
- frontier snapshot 非 proof 的 ledger 语义；
- second-action child shard toy partition；
- parallel/resume config skeleton 默认关闭。

未实现：

- 持久化 frontier resume；
- proof-closed prefix cache；
- adaptive hierarchical refinement；
- parallel worker merge。

## 默认行为

默认 benchmark 行为不变：

- `journey_final_judge_sharding_enabled=False`
- `journey_pulse_final_judge_enabled=False`
- dummy engine 默认关闭；
- production sharded Pulse 只有 opt-in 才进入。

## 风险

1. 当前 production sharded Pulse 是 guarded toy root-only engine，不应当解释为完整 20/100 规模 proof engine。
2. `pulse_max_recursions` 必须在大实例上设置上限；否则 exhaustive toy search 会非常慢。
3. bound pruning 当前故意 fail-open；这意味着优化效果有限，但避免 unsafe pruning。
4. harvest-after-negative 能返回更多 true-RC negative columns，但不会产生 certificate。
5. second-action sharding 目前是 toy partition 支持，未接自适应 refine 调度。

## 后续建议

1. 实现真正 open-sortie incremental Pulse，而不是 completed-sortie trace 枚举。
2. 为 prefix RC 建立可证明的 lower-bound ledger，先支持 cover/fleet，再支持 cuts。
3. 把 same_vehicle obligations 编译到 search state，而不是只在 leaf 过滤。
4. 实现 proof-closed prefix cache，并严格区分 frontier snapshot。
5. 大实例上只使用 bounded shard slices，配合 resume 和 hierarchical refine。
