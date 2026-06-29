# V770 Route-Order Pricing Filter Contract

日期：2026-06-29

## 背景

V767/V768 已经定义并审计了 same-route order 的三路 partition。但要进入 live B&B，仅靠 solver 里的 RMP pool 过滤不够：

```text
新 pricing 生成的 journey column 也必须按同一 branch 语义过滤。
```

否则 child RMP 可能排除了旧非法列，但 pricing 又把非法新列加回来，破坏 branch state。

## 本轮新增

### 1. shared full-journey branch filter

在 `core.branching` 增加完整 journey 级别过滤：

```text
journey_route_order_signature(journey)
journey_same_route_order_relation(journey, i, j)
journey_allowed_by_branch(journey, constraints)
```

支持：

```text
same_vehicle
separate_vehicle
same_route_order_before
same_route_order_after
same_route_order_before_strict
same_route_order_after_strict
not_same_route
```

solver 里的 `_journey_allowed_by_branch` 改成调用 shared helper，避免 solver/pricing 两套语义漂移。

### 2. pricing materialized journey filter

在 `journey_pricing.py` 增加：

```text
_journey_column_branch_allowed(journey, constraints)
```

并替换 materialized journey 返回前的 branch filter：

```text
sharded/pulse negative candidate
selection-DP selected journey
direct-NG completed journey
direct-label completed journey
profile-DP materialized journey
```

这些路径现在在 journey 已经 materialize 后，使用 route signature 判断 order branch。

### 3. mask-level helper 保守放行

`_journey_mask_branch_allowed` 对 route-order branch 改为：

- partial mask：不靠 mask 剪 route-order；
- strict before/after 的 final mask 单侧：可以安全判 infeasible；
- 双侧 final mask 或 `not_same_route`：放行到 materialized journey 再判断。

这避免了以前“未知 constraint 直接 false”导致 profile DP 在 order branch 下把所有扩展剪掉。

## Exact-Safe 边界

本轮仍然不启用 live order branch。

保留的边界：

- direct NG certificate 对 route-order branch 仍 fail-closed；
- task-set dominance 对 route-order branch 仍不安全；
- mask-level 不能给 route-order certificate；
- official bound / fathom / prune 不变；
- full60 结果不变。

本轮只补了 live order branch 必需的 pricing filter 基础。

## 验证

静态编译：

```text
python -m py_compile \
  BPC_future/core/branching.py \
  BPC_future/pricing/journey_pricing.py \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py
```

通过。

聚焦测试：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_task_set_branch_allowed \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_column_branch_allowed_supports_route_order_after_materialization \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_mask_branch_allowed_fail_open_for_route_order_until_materialized \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_same_route_order_branch_filter_is_exact_safe_prototype \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_same_route_order_partition_is_disjoint_for_branch_relevant_columns \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_core_trip_order_branch_filters_single_sortie_sequence \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_partition_audit_reports_child_width_and_coverage
```

结果：

```text
Ran 7 tests
OK
```

## 当前判断

相比 V769，现在 live order branch 少了一个关键 blocker：

```text
pricing materialization 已经能用 route signature 过滤 order branch column。
```

但仍不能直接打开 live branch，因为还缺：

1. branch controller 支持三路 child；
2. order branch 下禁用/改造 task-set dominance；
3. exact pricing certificate 对 order branch 的完整支持；
4. child replay 证明它确实能提升 dual/gap/proof cost。

## 下一步

1. 做 opt-in route-order child replay，不作为正式 B&B：
   - 对 seed61635 的 `[14,16]`、`[12,13]`、`[12,20]` 三路分别跑短预算；
   - 记录 child LP bound、negative events、retry、gap。
2. 如果 child replay 有收益，再实现三路 branch controller。
3. 如果 replay 仍然 dual 不动，继续转向 pricing-compatible route-resource cut / stronger formulation。

