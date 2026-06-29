# V768 Route-Order Partition Audit

日期：2026-06-29

## 背景

V767 定义了 same-route order 的三路 partition：

```text
same_route_order_before_strict
same_route_order_after_strict
not_same_route
```

但在接入 live B&B 之前，还需要知道一个 active route/order conflict 在当前 node 上会产生什么 child width、覆盖是否完整、是否值得 replay。

因此本轮新增 audit-only 事件，不改变求解。

## 本轮新增

新增事件：

```text
journey_route_order_partition_audit
```

配置：

```text
journey_route_order_partition_audit_enabled = False
journey_route_order_partition_audit_max_depth = 0
journey_route_order_partition_audit_top_n = 8
journey_route_order_partition_audit_mass_tol = 1e-9
journey_route_order_partition_audit_min_conflict_mass = mass_tol
```

事件在 root 和 branch node 的 RMP optimal 后触发，但默认关闭。

## 记录字段

对 active support 中出现双向 order mass 的 pair，记录：

```text
parent_allowed_count
child_widths
child_branch_relevant_widths
branch_relevant_column_count
neutral_column_count
branch_relevant_partition_violation_count
neutral_shared_violation_count
branch_relevant_partition_complete
neutral_columns_shared
exact_safe_partition_contract_holds
```

其中：

- `branch_relevant_column_count`：column task-set 涉及 `i/j` 的数量；
- `neutral_column_count`：不涉及 `i/j` 的中性列数量；
- `child_widths`：三路 child 各自允许的 pool column 数；
- `child_branch_relevant_widths`：三路 child 中真正涉及 `i/j` 的 column 数；
- `exact_safe_partition_contract_holds`：涉及 `i/j` 的列唯一归属，且中性列三路共享。

## Exact-Safe 边界

事件固定标记：

```text
audit_only = true
production_ready = false
live_branch_enabled = false
official_bound_effect = false
certificate_effect = false
exact_pricing_supported = false
completion_bound_fail_closed = true
```

所以本轮不会改变：

- branch tree；
- pricing；
- official bound；
- fathom/prune；
- certificate；
- full60 benchmark 结果。

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
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_partition_audit_reports_child_width_and_coverage \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_resource_cut_audit_classifies_order_rows_as_not_live_cuts
```

结果：

```text
Ran 5 tests
OK
```

## 对主线的意义

这一步继续落实“不能只调 branch score，必须攻 formulation/branching/cuts”的方向。

现在我们可以在 seed61635 这类 hard node 上回答：

```text
如果对 [14,16] 或 [12,20] 做 same-route order partition，
三个 child 会有多宽？
涉及该 pair 的列是否唯一落入一个 child？
中性列是否被所有 child 保留？
```

这比直接接 live branch 更稳，因为先验证 partition contract 和 child width，再决定是否值得做 replay。

## 下一步

1. 在 seed61635 开启 `journey_route_order_partition_audit_enabled` 做 45s/120s hard-case smoke。
2. 如果 audit 显示 child width 合理且 partition contract holds，做 opt-in 三路 order branch replay。
3. 如果 replay 改善 gap/proof tail，再设计 live branch controller。
4. 如果 child width 过宽或 dual 仍不动，则继续转向 pricing-compatible route-resource cut / stronger master formulation。

