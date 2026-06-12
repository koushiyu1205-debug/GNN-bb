# Sharded Pulse Final Judge Phase 3B-6 抽样验证报告

日期：2026-06-11

## 目标

本轮实现并验证 `Sharded Pulse Final Judge` 在 Phase 3B 之后的安全主线：

1. Phase 3B：root-only toy exhaustive Pulse DFS，只用于测试，不接 production driver；
2. Phase 3C：加入 exact-safe toy pruning 计数与 fail-open bound pruning；
3. Phase 4：加入保守 dominance archive 与 harvest-after-negative 隔离语义；
4. Phase 5/6：接入 guarded sharded final judge，保持 opt-in、guarded certificate、branch 过滤和 shard 诊断；
5. 用 5/10/20 抽样 run 验证默认路径不变、opt-in 路径不会误证书，并观察当前优化效果。

本轮仍不实现 production-grade Pulse DFS，不启用 resume，不启用 parallel，不把 toy engine 当作正式 20/100 规模证明器。

## 代码改动

### 新增模块

- `BPC_future/pricing/pulse_materialization.py`
  - Phase 3A leaf materialization contract；
  - Pulse sortie 必须回放 `evaluate_timed_trip()`；
  - journey 必须通过 `make_journey()`；
  - 候选负列必须用 `manual_journey_reduced_cost()` 复算 true RC。

- `BPC_future/pricing/pulse_toy_exhaustive.py`
  - root-only toy exhaustive enumerator；
  - 默认无 pruning、无 archive、无 resume、无 parallel；
  - 每个 leaf 调 Phase 3A materialization helper；
  - 返回 feasible candidates、negative leaves、best true RC、exhausted/incomplete 状态与 shard 统计；
  - 支持测试用 first-task shard 与 second-action child shard partition。

- `BPC_future/pricing/pulse_archive.py`
  - `StructuralKeyDominanceArchive`；
  - 只实现保守 dominance；
  - no-wait 下不允许用“更早时间”单独支配；
  - cap 只丢弃旧记录，不把当前状态当作 proof-closed。

- `BPC_future/pricing/sharded_pulse_final_judge.py`
  - `ShardProofStatus` / `ShardProofRecord` / `ShardLedger` / `ShardCacheKey`；
  - 支持 `REFINED` parent aggregation；
  - `DUPLICATE_ONLY` 永远不 promotion；
  - frontier snapshot 与 proof-closed record 明确分离。

### 修改模块

- `BPC_future/pricing/journey_pricing.py`
  - 新增 sharded final judge 诊断字段；
  - 支持 `final_judge_engine=sharded_pulse` / `sharded_pulse_dummy`；
  - `sharded_pulse_no_negative_journey` 可被证书推断识别；
  - Pulse certificate 不依赖 `completion_bound_enabled=True`；
  - `ng_dssr_relaxed_no_negative_journey` 必须显式 `ng_relaxation_superset is True`；
  - guarded engine 只在 opt-in 下运行，真实实例无 toy certificate guard 时返回 `INCOMPLETE_LIMIT`，不产生 official lower bound。

- `BPC_future/solver/journey_driver.py`
  - final-probe path 接入 sharded config；
  - 默认关闭；
  - dummy certificate 需要 test flag、环境变量和 tiny/test instance guard；
  - journey pricing JSONL 日志增加 shard 与 pulse counters。

- `BPC_future/tests/test_bpc_future.py`
  - 增加 Phase 3A/3B/3C/4/5 focused tests；
  - 覆盖 brute-force equivalence、first-task partition、second-action partition、duplicate-only 非证书、frontier 非 proof、branch 过滤、guarded certificate、dummy opt-in。

## 当前算法结构

当前 production 可见路径分成三层：

1. 默认路径：不设置 sharded/pulse config 时，仍走原有 journey pricing / final judge 逻辑；
2. dummy sharded engine：只用于状态机和 driver smoke，日志标记 `final_judge_engine=sharded_pulse_dummy`；
3. guarded toy sharded engine：显式 opt-in 后调用 root-only toy exhaustive enumerator，按 first-task shards 聚合；只有 tiny/test 且启用 toy certificate guard 的场景允许 no-negative certificate。

当前 toy Pulse 的搜索方式是“枚举完成 trace 后再物化验证”，不是 production Pulse。它能验证 exactness contract，但不应该被期待在 20/100 规模上提速。

## 关键 exactness 边界

- `DUPLICATE_ONLY` 只表示没有产出新的可返回列，永远不表示没有负列；
- `INCOMPLETE_LIMIT`、timeout、unsupported branch、dummy guard failed 都不会形成 official lower bound；
- sharded certificate 必须满足 `status=OPTIMAL`、`global_certificate_capable=True`、`final_judge_certificate_capable=True`、reason 白名单；
- `frontier snapshot` 不是 proof，不能标记 shard certified；
- harvest-after-negative 退出 proof mode，不能产生 no-negative certificate；
- Phase 3B toy enumerator 不做 unsafe pruning；Phase 3C 的 bound pruning 没有安全 prefix lower-bound 时 fail-open。

## Focused 测试

### Phase 3B-5 focused tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_matches_bruteforce_feasible_journeys \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_best_rc_and_negative_flag_match_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_no_negative_exhausts_toy_universe \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_first_task_shards_partition_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_second_action_child_shards_partition_first_task_parent \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_keeps_tasks_elementary_and_cover_once \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_no_wait_matches_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_budget_hits_return_incomplete \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_resource_pruning_matches_unpruned \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_time_window_pruning_matches_unpruned \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_return_pruning_matches_unpruned \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_bound_pruning_fails_open_without_safe_row_bounds \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_archive_waiting_allowed_dominance_safe \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_archive_no_wait_earlier_time_alone_not_dominance \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_archive_no_wait_interval_containment_dominance_safe \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_archive_depot_ready_dominance_prunes_later_equivalent_state \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_archive_cap_drops_old_records_without_pruning_current \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_archive_dominance_matches_unpruned \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_harvest_after_negative_exits_proof_mode \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_harvest_returns_only_true_rc_negatives \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_duplicate_only_harvest_does_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_found_negative_status_is_not_global_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_certifies_very_small_no_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_incomplete_no_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_certificate_guard_default_incomplete \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_duplicate_only_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_unsupported_branch_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_separate_branch_filters_pair_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_same_branch_filters_one_sided_negative
```

结果：

```text
Ran 30 tests in 0.093s
OK
```

### Phase 2.5 / certificate regression

结果：

```text
Ran 35 tests in 1.643s
OK
```

### 合并 focused regression

结果：

```text
Ran 73 tests in 0.206s
OK
```

### 语法与 diff 检查

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_archive.py \
BPC_future/pricing/pulse_materialization.py \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/pricing/sharded_pulse_final_judge.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

已通过。

`git diff --check` 已通过。

## 5/10/20 抽样设置

抽样目标是比较：

1. 默认 no-GNN 路径；
2. opt-in sharded Pulse guarded toy 路径。

注意：`moon_trek_balanced_60_20260609` 目录当前只含 5/10 规模。为保证 5/10/20 都能跑，本轮 5/10 使用 `BPC_future/data/generated/moon_trek_60`，20 使用既有 baseline report 对应的 `BPC_future/logical_graph/tasks_020/random-wave/...` 实例。

另有一次 `moon_trek_60/tasks_20/...seed21000...` 尝试失败，错误为：

```text
ValueError: task 17 has no feasible single-task timed trip on the configured grid
```

该 run 是数据/配置可行性异常，不计入算法前后对比。

## 抽样结果

| 规模 | 路径 | 状态 | wall time(s) | primal | dual | pricing calls | exact calls | generated | evaluated | columns |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 默认 no-GNN | OPTIMAL | 3.264 | 102.041475 | 102.041475 | 4 | 3 | 9806 | 14160 | 31 |
| 5 | opt-in sharded Pulse | TIME_LIMIT | 2.344 | 102.041475 | - | 4 | 3 | 146783 | 14703 | 31 |
| 10 | 默认 no-GNN | OPTIMAL | 5.902 | 264.024007 | 264.024007 | 4 | 4 | 35393 | 24485 | 110 |
| 10 | opt-in sharded Pulse | TIME_LIMIT | 33.688 | 264.024007 | - | 4 | 4 | 11823639 | 24175 | 110 |
| 20 | 默认 no-GNN | TIME_LIMIT | 84.778 | 660.195529 | - | 12 | 4 | 90164 | 176509 | 295 |
| 20 | opt-in sharded Pulse | TIME_LIMIT | 84.723 | 660.195529 | - | 12 | 4 | 20713019 | 90413 | 295 |

## Sharded Pulse 日志摘要

| 规模 | sharded events | last pricing state | reason | shard 状态 | recursions | expanded | return pruned | time-window pruned | archive pruned | best true RC |
|---:|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 5 | 1 | INCOMPLETE_LIMIT | sharded_pulse_incomplete | total=5, certified=4, incomplete=1, negative=0 | 505 | 282 | 2172 | 135043 | 222 | 14.374812 |
| 10 | 1 | INCOMPLETE_LIMIT | sharded_pulse_incomplete | total=10, certified=0, incomplete=10, negative=0 | 3 | 3 | 0 | 11806833 | 0 | 1.697430 |
| 20 | 1 | INCOMPLETE_LIMIT | sharded_pulse_incomplete | total=20, certified=0, incomplete=20, negative=0 | 2 | 2 | 0 | 20670127 | 0 | 0.000000 |

这些 opt-in run 没有产生 `CERTIFIED_NO_NEGATIVE`，也没有设置 official lower bound。这符合当前 guard 设计。

## 前后效果判断

当前实现的主要收益不是速度，而是把证书状态机和 exactness 边界固定下来。

正向结果：

1. 默认 benchmark 路径不受影响；
2. sharded dummy / toy engine 都必须显式 opt-in；
3. `sharded_pulse_no_negative_journey` 可被 driver 正确认作证书，但只在 guarded 条件满足时；
4. incomplete、negative、duplicate-only、unsupported branch 都不会污染 official lower bound；
5. toy exhaustive Pulse 与 brute-force enumerator 已在单测中逐项对齐；
6. leaf materialization 与现有 `evaluate_timed_trip()` / `make_journey()` / `manual_journey_reduced_cost()` 语义绑定。

当前没有形成性能优化：

1. opt-in toy path 在 5/10 上反而丢失最终证书，因为真实实例默认不允许 toy certificate；
2. 10/20 的 generated sequences 暴涨，说明当前 toy engine 仍是“完成 trace 枚举后再验证”，不是 transition-level Pulse；
3. `time_window_pruned` 很大，但发生在 path-option/trace 枚举之后，不能有效降低生成成本；
4. prefix RC bound pruning 按设计 fail-open，因此不会带来 reduced-cost 层面的提前剪枝；
5. 没有 resume、parallel、adaptive hierarchical sharding，单个 incomplete shard 会阻断全局证书。

## 风险

1. 不能把当前 guarded toy engine 当成正式求解器；它只适合 very-small/test 和状态机验证；
2. 当前 opt-in 配置在真实 5/10 实例上可能把原本可由旧 judge 证明的节点变成 `INCOMPLETE_LIMIT`，因此不应默认开启；
3. `ValueError` 类型的 malformed trace 是内部 bug，不应在未来 production Pulse 中吞掉并解释成 no-negative；
4. archive / harvest 当前只在 focused toy tests 里验证，不能替代 production proof-closed resume；
5. second-action shard 目前是 toy partition 验证，尚未实现 adaptive refine / parent-child resume ledger。

## 后续优化方向

下一步应先做真正的 incremental open-sortie Pulse core，而不是继续扩展 completed-trace toy enumerator。

优先级建议：

1. 实现 transition-level root-only Pulse：在扩展任务/路径前做 time/resource/return feasibility 检查；
2. 把 first-task shard 和 second-action child shard 接入 proof ledger，但仍保持单线程、无 resume；
3. 建立安全的 `C_lb_prefix` reduced-cost lower-bound ledger，缺失 cut/fleet/branch row 下界时继续 fail-open；
4. 在 state 中显式维护 same/separate branch obligations，避免只靠 leaf 过滤；
5. 引入 proof-closed frontier cache，严格区分 resume frontier 与 certificate evidence；
6. 最后再加 parallel shard worker 和 legacy fallback cap。

## 结论

本轮完成了 Phase 3B 到 guarded Phase 5/6 的安全骨架：toy exhaustive Pulse 能和 brute-force 对齐，sharded final judge 能进入 driver 但不会默认启用，也不会把 incomplete / duplicate-only / negative 错误提升为证书。

5/10/20 抽样显示，当前 opt-in toy path 没有实际提速，且在 5/10 上会因为 certificate guard 丢失旧路径的最优证明；这符合预期，因为它仍是测试用 exhaustive skeleton。真正的性能收益要等下一步 transition-level Pulse core、safe prefix RC 和 adaptive sharding 实现后再评估。
