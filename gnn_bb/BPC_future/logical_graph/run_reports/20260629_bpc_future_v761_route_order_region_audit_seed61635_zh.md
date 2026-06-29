# V761 Route/Order Region Audit - seed61635

日期：2026-06-29

## 目的

V760 已经说明：

```text
weighted task-subset rank-1 rows 能加入 RMP、binding、产生 nonzero dual，
但 seed61635 的 best dual 仍停在 526.651393。
```

因此本轮不再继续扩大 task-set weighted rows，而是新增 route/order-aware 诊断，判断 hard case 是否需要超出 task-set 的 formulation。

## 代码变化

新增 diagnostic-only 事件：

```text
journey_route_order_region_audit
```

配置：

```text
journey_route_order_region_audit_enabled=False
journey_route_order_region_audit_max_depth=0
journey_route_order_region_audit_top_n=8
journey_route_order_region_audit_mass_tol=1e-9
```

记录内容：

- active route signature 数量；
- active task-set 数量；
- 同 task-set 下不同 route/order 的 multiplicity；
- ordered transition mass；
- arc-option mass；
- 正反方向 route-order conflict；
- sortie count / ordered task count histogram。

Exact-safe 边界：

```text
audit_only=True
production_ready=False
official_bound_effect=False
certificate_effect=False
```

该事件不加 row、不改 RMP、不改 pricing、不改 certificate、不改 fathom/prune。

## 验证

通过编译：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py
```

通过聚焦测试：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_region_audit_logs_direction_conflicts_without_bound_effect \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_weighted_subset_row_live_pricing_is_rc_consistent_and_fail_closed_for_bounds \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_weighted_rank1_separator_is_opt_in_and_deduplicates
```

结果：

```text
Ran 3 tests
OK
```

补充：route/order audit 标量也已接入 branch action sanity dataset context schema，字段包括：

```text
route_order_active_journey_count
route_order_active_task_set_count
route_order_active_route_signature_count
route_order_multi_route_task_set_count
route_order_conflict_count
route_order_conflict_mass
route_order_top_conflict_balance_ratio
route_order_top_transition_count
route_order_top_arc_option_count
```

新增/更新验证：

```text
python -m py_compile \
  BPC_future/scripts/build_gat_branch_action_sanity_dataset.py \
  BPC_future/tests/test_gat_branch_action_sanity_dataset.py

MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_gat_branch_action_sanity_dataset
```

结果：

```text
Ran 1 test
OK
```

## Seed61635 45s 诊断

实例：

```text
tasks020_07_seed61635
```

配置：

- RouteOpt/BKF staged preset：`routeopt_bkf_v736`
- dynamic SRC：on，gate best violation `0.25`
- route/order audit：on，max depth `2`
- time limit：45s

输出：

```text
BPC_future/results/20260629_v761_route_order_audit_seed61635_45/
```

求解结果：

```text
status = TIME_LIMIT
primal = 561.030445
dual = 526.651393
gap = 0.061278
nodes = 3
columns = 388
cuts_added = 10
subset_row_cuts_added = 9
```

该结果与 V759/V760 一致：诊断本身不改变求解行为，best dual 仍不动。

## Route/Order Audit 结果

汇总：

```text
route_order_events = 31
max_active_journey_count = 19
max_active_task_set_count = 19
max_active_route_signature_count = 19
max_multi_route_task_set_count = 0
max_route_order_conflict_count = 1
max_route_order_conflict_mass = 1.0
```

典型 direction conflict：

```text
node0 cg4:
tasks=[14,16]
ascending_mass=0.666666667
descending_mass=0.333333333
balance_ratio=0.5
total_mass=1.0

node0 cg7:
tasks=[12,20]
ascending_mass=0.125
descending_mass=0.125
balance_ratio=1.0
total_mass=0.25
```

典型 route transitions：

```text
8 -> 6  mass=1.0
2 -> 14 mass=0.5
10 -> 12 mass=0.5
12 -> 20 mass=0.5
14 -> 16 mass=0.5
```

## 解释

V761 给出两个判断：

1. 当前 active RMP 中没有同一 task-set 下多个 route/order 同时活跃：

```text
max_multi_route_task_set_count = 0
```

所以 seed61635 当前不是简单的“task-set dominance 把多 route variant 压没了”。

2. 仍存在少量 route-order direction conflict：

```text
[14,16], [12,20]
```

这说明 route/order 信号存在，但它很稀疏，不像 broad plateau 那样能靠一个全局 route-order cut 直接解决。

## 对下一步的含义

不建议：

- 继续盲目扩大 task-set SRC / weighted task-set rows；
- 直接关闭 task-set dominance；
- 把 route/order conflict 当成 live cut 直接加进 RMP。

更合理的下一步：

1. 在 hard nodes 上做 branch-state scoped route/order audit，尤其是 seed61635 的 node1/node2；
2. 把 route-order conflict 作为 branch candidate / child proof risk 特征，而不是先做 cut；
3. 若要做 cut，应优先考虑 branch-state scoped route/resource rows，而不是全局 task-set rows；
4. 继续推进 RouteOpt/BKF phased branch testing，让 exact-ish probe 只打到 route/order 风险高的少量候选。

## 当前结论

seed61635 的 lower-bound 瓶颈目前已经排除了两条“简单解释”：

```text
普通 SRC 不够但加更多普通 SRC即可
weighted task-set rank-1 不够但加少量 weighted rows即可
同 task-set 多 route 活跃导致 task-set dominance 掩盖 formulation
```

更可能的方向是：

```text
branch-state scoped route/resource proof cost
+ stronger formulation
+ 更好的 child ordering / retry gate
```

这也和 RouteOpt 的启发一致：branch testing 和 formulation 必须一起推进。
