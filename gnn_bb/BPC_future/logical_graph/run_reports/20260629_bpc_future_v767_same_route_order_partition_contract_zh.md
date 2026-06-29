# V767 Same-Route Order Partition Contract

日期：2026-06-29

## 背景

V766 已经能表达同一 sortie 内的 order branch 过滤，但 `before/after` 的弱语义不能直接作为 B&B child：

```text
before 和 after 都允许不同 sortie / 不相关列，
因此二者不是 disjoint partition。
```

本轮补的是更接近 live branching 的 partition contract。

## 本轮新增语义

新增三路 same-route order partition：

```text
same_route_order_before_strict(i, j)
same_route_order_after_strict(i, j)
not_same_route(i, j)
```

含义：

- `same_route_order_before_strict(i,j)`
  - 允许不含 `i/j` 的中性列；
  - 允许同一 sortie 内 `i before j`；
  - 禁止单侧列、不同 sortie 同含列、反向同 sortie 列。
- `same_route_order_after_strict(i,j)`
  - 对称地允许同一 sortie 内 `j before i`；
  - 同样允许中性列。
- `not_same_route(i,j)`
  - 禁止同一 sortie 内同时包含 `i/j`；
  - 允许单侧列、不同 sortie 同含列、中性列。

新增 helper：

```text
_journey_same_route_order_partition_constraints(i, j)
```

返回上述三路 constraints。

## 为什么中性列可以共享

不含 `i/j` 的 journey column 必须在三个 child 中都可用，否则其他任务的覆盖会被无故破坏。

因此正确要求不是：

```text
每个 column 只属于一个 child
```

而是：

```text
所有涉及 i/j 的 column 只属于一个 child；
不涉及 i/j 的中性 column 可以被所有 child 共享。
```

在 set-partitioning master 中，最终整数解必须覆盖 `i` 和 `j`，所以三路 child 对整数解空间仍然可以形成互斥划分。

## Exact-Safe 边界

本轮仍不是 live B&B：

- pricing direct-label / profile / pulse 路径还没有完整携带 route-order state；
- mask-level branch pruning 仍不能表达 sortie 内顺序；
- direct NG certificate 对这些 branch 继续 fail-closed；
- task-set dominance 在这些 branch 下继续判为不安全。

因此本轮不改变：

- official bound；
- certificate；
- fathom/prune；
- branch candidate 默认排序；
- full60 结果。

## 验证

静态编译：

```text
python -m py_compile \
  BPC_future/core/branching.py \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py
```

通过。

聚焦测试：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_same_route_order_branch_filter_is_exact_safe_prototype \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_same_route_order_partition_is_disjoint_for_branch_relevant_columns \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_core_trip_order_branch_filters_single_sortie_sequence \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_helpers_filter_and_choose_pair \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_forbidden_signatures_are_scoped_to_branch_node_pool
```

结果：

```text
Ran 5 tests
OK
```

## 当前判断

这一步让 formulation/branching 方向从“能看见 route/order conflict”推进到：

```text
能定义一个可验证的 state-scoped same-route order branch family。
```

它还不是加速结果，但它是后续把 seed61635 这类 order/resource conflict 接入 exact-safe B&B 的必要前置条件。

## 下一步

1. 给 pricing materialization 加 route-order support flag：
   - supported 时按 strict partition 过滤；
   - unsupported 时禁止 certificate / fail-closed。
2. 在 child replay 中只对 diagnostic node 手动施加三路 constraints，统计 child LP/gap/proof cost。
3. 如果三路 order branch 在 seed61635 的 `[14,16]` / `[12,20]` 上改善 dual/gap，再设计 live branching controller。
4. 如果 child dual 仍不动，则继续转向 pricing-compatible route-resource cut 或 stronger master formulation。

