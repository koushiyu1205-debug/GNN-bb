# Sharded Pulse Phase 7J Adaptive Second-action Shard Refinement 报告

日期：2026-06-12

## 目标

本轮实现 Phase 7J：`Adaptive second-action shard refinement`。

目标不是继续推进 active worker，也不是放开 official certificate，而是把 hard first-task shard exact-safely 细分为 second-action child shards：

```text
Omega_j
  -> Omega_{j,k}, k != j
  -> Omega_{j,return}
```

本轮不做：

- resume；
- parallel；
- adaptive multi-level refinement；
- production default enable；
- official certificate gate；
- 20/100 A/B；
- cut / subset-row / fleet prefix bound。

## 实现摘要

### 1. JourneyPricingConfig 增加 refinement 开关

新增字段，默认关闭：

- `pulse_adaptive_sharding_enabled=False`
- `pulse_refine_incomplete_first_task_shards=False`
- `pulse_refinement_min_recursions=1000`
- `pulse_refinement_min_expanded=0`
- `pulse_refinement_max_children=32`

对应 driver config 已接入：

- `journey_pulse_*`
- `journey_sharded_pulse_audit_*`
- `journey_sharded_pulse_hidden_negative_worker_*`

hidden worker 仍默认关闭，不建议作为当前主线继续放大。

### 2. Guarded sharded engine 调度

`_price_journeys_by_sharded_pulse_guarded()` 现在先运行 parent first-task shard。

若 parent shard：

- 未 exhausted；
- 没有 found negative；
- 达到 recursion / expanded threshold；
- 完整 second-action children 数量不超过 cap；
- 且 adaptive refinement 显式开启；

则 parent 进入 refined runtime 语义：

- parent 只累计运行 counters；
- `final_judge_shards_refined += 1`；
- parent 不直接参与 required proof shard 计数；
- required proof shards 改为完整 child 集合。

child 规则：

- any child negative -> global found negative；
- any child incomplete and no negative -> global incomplete；
- all children certified -> parent 可视为 certified；
- `DUPLICATE_ONLY` 仍不证书。

如果 `pulse_refinement_max_children` 不能覆盖完整 child partition，则不 refine，保持旧 first-task 行为。

### 3. Child 顺序

second-action child 调度顺序为：

1. `next-task k`，按高 cover dual、低 transition cost、task id 排序；
2. `return-after-first-task`。

排序只影响运行效率，不影响 exactness。

### 4. Audit 日志字段

`journey_sharded_pulse_audit` payload 新增：

- `pulse_audit_shards_refined`

driver 的 normal `journey_pricing` 日志已通过既有字段记录：

- `final_judge_shards_refined`

## 新增测试

新增 4 个 focused tests：

- `test_sharded_pulse_adaptive_refinement_all_children_certify_parent`
- `test_sharded_pulse_adaptive_refinement_child_incomplete_blocks_certificate`
- `test_sharded_pulse_adaptive_refinement_child_negative_propagates`
- `test_sharded_pulse_adaptive_refinement_threshold_and_cap_guard`

覆盖：

- all children certified -> global `CERTIFIED_NO_NEGATIVE`；
- child incomplete -> global `INCOMPLETE_LIMIT`；
- child negative -> global `FOUND_NEGATIVE`；
- parent refined 后不直接计入 required proof shard；
- threshold 不满足时不 refine；
- child cap 无法覆盖完整 partition 时不 refine；
- refined parent 只记录 `final_judge_shards_refined`，不把 parent frontier 当 proof。

同时回归既有：

- refined ledger aggregation；
- second-action child partition；
- dummy / audit / worker sharded Pulse tests。

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_adaptive_refinement_all_children_certify_parent \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_adaptive_refinement_child_incomplete_blocks_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_adaptive_refinement_child_negative_propagates \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_adaptive_refinement_threshold_and_cap_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_pulse_second_action_child_shards_partition_first_task_parent \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_ledger_refined_parent_uses_children
```

结果：

```text
Ran 6 tests in 0.009s
OK
```

Sharded Pulse 相关回归：

```text
Ran 26 tests in 0.411s
OK
```

全量 `BPCFutureTests` 回归：

```text
Ran 425 tests in 2.069s
OK (skipped=1)
```

`git diff --check`：通过。

## Smoke

运行目录：

```text
BPC_future/results/sharded_pulse_phase7j_adaptive_refinement_smoke_20260612/
```

### Driver-level audit smoke

用 mainline 配置加 audit no-refine / audit refine 对照跑：

- Apollo 5；
- Tranquillitatis 5；
- Apollo 10。

结果：

- official `status` / `dual_bound` / `pricing_state` 在 no-refine 与 refine 间保持一致；
- 本组短时限没有触发 `journey_sharded_pulse_audit` 事件，因此不能作为 refinement 效果证据；
- 结论：driver official result 未被 refinement 配置污染，但还需要更合适的 legacy final-judge 触发场景观察 audit refinement。

### Guarded-engine normal smoke

直接调用 guarded sharded Pulse pricing path，普通 cap 下 first-task parents 都能穷尽，因此 refinement 未触发：

| case | mode | shards_total | certified | incomplete | refined |
|---|---|---:|---:|---:|---:|
| Apollo 5 | no-refine | 5 | 5 | 0 | 0 |
| Apollo 5 | refine | 5 | 5 | 0 | 0 |
| Tranquillitatis 5 | no-refine | 5 | 5 | 0 | 0 |
| Tranquillitatis 5 | refine | 5 | 5 | 0 | 0 |
| Apollo 10 | no-refine | 10 | 10 | 0 | 0 |
| Apollo 10 | refine | 10 | 10 | 0 | 0 |

### Guarded-engine stress smoke

用低 recursion cap 构造 hard parent，验证 refinement runtime 真实触发：

| case | mode | shards_total | certified | incomplete | refined | bound_pruned | archive_pruned |
|---|---|---:|---:|---:|---:|---:|---:|
| Apollo 5 | no-refine | 5 | 0 | 5 | 0 | 10 | 35 |
| Apollo 5 | refine | 25 | 20 | 5 | 5 | 76 | 70 |
| Tranquillitatis 5 | no-refine | 5 | 0 | 5 | 0 | 10 | 35 |
| Tranquillitatis 5 | refine | 25 | 20 | 5 | 5 | 80 | 70 |
| Apollo 10 | no-refine | 10 | 0 | 10 | 0 | 20 | 70 |
| Apollo 10 | refine | 100 | 90 | 10 | 10 | 301 | 140 |

关键观察：

- refinement 把 hard parent 分解为完整 second-action child set；
- parent 不再直接计入 required proof shard；
- child certified 数量显著上升；
- 仍有 child incomplete 时 global 仍为 `INCOMPLETE_LIMIT`；
- `global_certificate_capable=False`，没有放开 official certificate。

## 当前边界

- adaptive refinement 只是一层 second-action；
- 没有 resume / parallel；
- 没有 official certificate gate；
- hidden-negative worker 仍不建议继续放大预算；
- driver-level audit smoke 还需要更合适的 legacy final-judge 触发样本。

## 结论

Phase 7J 已完成：adaptive second-action refinement 已接入 guarded sharded engine，并有 focused tests 保护 parent/child exactness 语义。

当前最重要的结果是：

1. parent refined 后不会被当作 proof-closed；
2. child incomplete 会阻断 certificate；
3. child negative 会正确传播；
4. child cap 无法覆盖完整 partition 时不会 refine；
5. stress smoke 证明真实数据上 refinement 调度能把 hard parent 拆成更小 child proof units。

下一步不建议继续加 worker time limit。更合理的下一步是 Phase 7K：shard scheduling + ROI gate，用实时 prune/progress 信号决定是否继续 Pulse，避免小实例被额外审计/worker 开销拖慢。
