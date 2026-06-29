# V765 Route/Resource Cut Audit - seed61635

日期：2026-06-29

## 目的

前面 V762/V764 已经说明：

```text
route/order conflict 存在，
但 root RF candidate 集合里没有可直接惩罚的 conflict pair。
```

因此本轮不再继续调 branch score，而是转向 formulation/cuts：先新增一个 exact-safe 的 route/resource cut audit，判断这些 route/order 信号能不能变成合法 row。

## 本轮代码变化

新增 audit-only 事件：

```text
journey_route_resource_cut_audit
```

配置：

```text
journey_route_resource_cut_audit_enabled = False
journey_route_resource_cut_audit_max_depth = 0
journey_route_resource_cut_audit_top_n = 8
journey_route_resource_cut_audit_mass_tol = 1e-9
journey_route_resource_cut_audit_min_conflict_mass = mass_tol
```

记录三类候选 row 形态：

1. `order_direction_disjunction`
   - active journeys 中同一 pair 同时出现 `i before j` 和 `j before i`；
2. `adjacent_direction_disjunction`
   - 上述方向冲突进一步要求两个任务相邻；
3. `same_task_set_multi_route_region`
   - 同一 task-set 下多个 route signature 同时活跃。

每个候选明确标记：

```text
global_valid_candidate
requires_branch_state
pricing_supported
recommended_next
```

当前所有 route/order row 都只 audit，不加到 RMP。

## Exact-Safe 边界

事件固定输出：

```text
audit_only = true
add_enabled = false
production_ready = false
official_bound_effect = false
certificate_effect = false
exact_pricing_supported = false
completion_bound_fail_closed = true
```

也就是说：

- 不改变 RMP；
- 不改变 pricing；
- 不改变 official bound；
- 不改变 fathom/prune；
- 不把 route/order conflict 当作有效 cut。

## 验证

编译通过：

```text
python -m py_compile \
  BPC_future/solver/journey_driver.py \
  BPC_future/tests/test_bpc_future.py
```

focused tests 通过：

```text
MPLCONFIGDIR=/tmp/bpc_future_mpl python -m unittest \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_resource_cut_audit_classifies_order_rows_as_not_live_cuts \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_route_order_region_audit_logs_direction_conflicts_without_bound_effect \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_weighted_subset_row_live_pricing_is_rc_consistent_and_fail_closed_for_bounds
```

结果：

```text
Ran 3 tests
OK
```

## seed61635 45s audit

实例：

```text
tasks020_07_seed61635
```

输出：

```text
BPC_future/results/20260629_v765_route_resource_cut_audit_seed61635_45/results.csv
```

结果：

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

和 V761/V764 一致，符合 audit-only 预期。

## Audit 结果

日志统计：

```text
journey_route_resource_cut_audit events = 31
max order_direction_candidate_count = 1
max adjacent_direction_candidate_count = 1
max same_task_set_multi_route_candidate_count = 0
route_resource_global_valid_candidate_count = 0
route_resource_pricing_supported_candidate_count = 0
```

典型候选：

```text
row_type = order_direction_disjunction
tasks = [14, 16]
ascending_mass = 0.666666667
descending_mass = 0.333333333
total_mass = 1.0
balance_ratio = 0.5
global_valid_candidate = false
requires_branch_state = true
pricing_supported = false
reason = direction_disjunction_not_global_cut
recommended_next = branch_state_scoped_order_branch_or_route_resource_formulation
```

另一个候选：

```text
tasks = [12, 20]
ascending_mass = 0.125
descending_mass = 0.125
total_mass = 0.25
balance_ratio = 1.0
```

## 解释

这次把 formulation/cuts 方向说清楚了：

1. seed61635 确实出现 route/order disjunction 信号；
2. 但它不是可以直接作为全局有效 cut 加进 RMP 的 row；
3. 当前 pricing 也没有支持 route-order coefficient；
4. 同一 task-set 多 route 活跃数量为 0，所以不是简单“保留多个 route variant”即可解决；
5. root RF candidate 也没有承接这些 conflict，因此只调 root branch score 无效。

## 当前判断

seed61635 的下一步不应是：

```text
继续加大普通 SRC
继续加大 weighted task-set row
继续调 root route/order branch penalty
直接把 order conflict 当 cut 加入 RMP
```

更合理的是：

```text
branch-state scoped order/resource formulation
或 order/resource branching
或能被 pricing 精确支持的 route-resource row
```

其中 live cut 的最低契约是：

1. row 对当前 node 的所有整数解有效；
2. `_journey_cut_coefficient(cut, journey)` 可精确计算；
3. pricing 里的 reduced-cost updater 与 RMP coefficient 一致；
4. completion-bound / profile pruning 对非支持 cut dual fail-closed；
5. 先通过 RC 一致性测试，再 opt-in live。

## 下一步

1. 设计 `OrderDirectionBranchConstraint` 或等价的 state-scoped order branch，而不是全局 cut；
2. 或设计真正 pricing-compatible 的 route-resource row，先只支持 exact direct-label pricing；
3. 在 seed61635 的 child nodes 上看 `[14,16]` / `[12,20]` order disjunction 是否持续出现并影响 proof tail；
4. 若要 live cut，先加 coefficient + pricing updater + fail-closed tests，再跑 45s/120s hard-case smoke。
