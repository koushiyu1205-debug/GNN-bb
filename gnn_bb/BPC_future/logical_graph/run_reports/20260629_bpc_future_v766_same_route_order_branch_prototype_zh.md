# V766 Same-Route Order Branch Prototype

日期：2026-06-29

## 背景

V765 的 route/resource cut audit 已经说明：

```text
seed61635 存在 route/order disjunction，
但这些 row 不是当前可以直接加入 RMP 的全局有效 cut。
```

因此后续不能只继续调 branch score，也不能把 order conflict 直接当 cut 加。更合理的路线是先把它表达成 state-scoped branch/formulation，再检查 pricing 和 certificate 是否能完整支持。

## 本轮改动

本轮新增两个原型 branch constraint：

```text
same_route_order_before(i, j)
same_route_order_after(i, j)
```

语义：

- 如果一个 journey 的同一 sortie 内同时包含 `i` 和 `j`：
  - `same_route_order_before(i,j)` 要求 `i` 在 `j` 之前；
  - `same_route_order_after(i,j)` 要求 `j` 在 `i` 之前。
- 如果 `i` 和 `j` 不在同一 sortie，或者其中一个任务不存在，该 order row 不限制这个 journey。

新增支持点：

1. `BranchConstraint.name()` 可稳定序列化：

```text
route_order(i,j)=before
route_order(i,j)=after
```

2. `trip_allowed_by_branch` / `partial_sequence_allowed` 支持单 sortie 顺序过滤。

3. `_journey_allowed_by_branch` / `_filter_journeys_by_branch` 支持完整 journey pool 的同一 sortie 顺序过滤。

## Exact-Safe 边界

本轮不是 live branching。

原因是当前 pricing/certificate 侧仍然主要基于 task mask 或 task-set 判断，无法完整表达同一 sortie 内顺序：

- `_journey_mask_branch_allowed` 对未知/非 Ryan-Foster 约束 fail-closed；
- `_direct_ng_branch_certificate_safe` 对 order branch 返回 false；
- `_journey_task_set_dominance_safe` 对 order branch 返回 false；
- task-set dominance 不能在 order branch 下继续使用，因为同一 task-set 的不同顺序可能代表不同合法性。

所以本轮不会改变：

- official lower bound；
- pricing certificate；
- fathom/prune；
- early branch 触发；
- branch candidate 默认排序。

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
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_core_trip_order_branch_filters_single_sortie_sequence \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_branch_helpers_filter_and_choose_pair \
  BPC_future.tests.test_bpc_future.BPCFutureTests.test_forbidden_signatures_are_scoped_to_branch_node_pool
```

结果：

```text
Ran 4 tests
OK
```

## 当前判断

这一步把 V765 的结论往前推进了一格：

```text
route/order conflict 不能直接当 cut；
但可以被表达成 state-scoped branch constraint 的过滤语义。
```

不过它还不能用于正式 B&B，因为二叉 child partition 和 pricing support 尚未完成。

关键未完成项：

1. 需要设计 disjoint/exhaustive child partition。
   当前 before/after 都允许不同 sortie 情况，直接二分会重叠。

2. pricing direct-label/profile/pulse 路径需要支持 route-order 状态，而不能只看 task mask。

3. 需要禁用或改造 order branch 下的 task-set dominance，保留 route signature/order variant。

4. completion-bound 和 final-judge 必须知道 order branch 是否支持；不支持时只能 fail-closed。

## 下一步

1. 设计 `order_before / order_after / not_same_route` 的三路 partition，或等价的二叉层级 partition。
2. 在 pricing candidate materialization 里保留 route signature，先只支持 exact direct-label 路径。
3. 给 order branch 增加 coverage 测试：所有可行 journey 必须落入某个 child，且 child 间不重叠。
4. 在 seed61635 上只做 opt-in diagnostic branch replay，确认 `[14,16]` / `[12,20]` 这类 order disjunction 是否真正降低 proof tail。

