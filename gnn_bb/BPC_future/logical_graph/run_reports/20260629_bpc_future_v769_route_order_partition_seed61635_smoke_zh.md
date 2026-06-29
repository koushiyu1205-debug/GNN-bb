# V769 Route-Order Partition Audit Smoke - seed61635

日期：2026-06-29

## 目的

V768 新增了 `journey_route_order_partition_audit`。本轮在 hard case `tasks020_07_seed61635` 上跑 45s smoke，检查：

- route/order conflict 是否能被三路 partition 捕获；
- child width 是否合理；
- partition contract 是否完整；
- 是否值得马上接 live order branch。

## 运行口径

实例：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
```

输出：

```text
BPC_future/results/20260629_v768_route_order_partition_audit_seed61635_45/results.csv
```

启用：

```text
journey_route_order_region_audit_enabled=True
journey_route_resource_cut_audit_enabled=True
journey_route_order_partition_audit_enabled=True
journey_branch_candidate_priority=routeopt_bkf_staged
journey_branch_candidate_phased_testing_preset=routeopt_bkf_v762
```

## 求解结果

```text
status = TIME_LIMIT
time = 44.015889s
primal = 561.030445
dual = 526.651393
gap = 0.061278
nodes = 3
columns = 355
cuts_added = 1
subset_row_cuts_added = 0
```

和 V765 的 45s audit 结果相比，目标值和 gap 没有改善；这是预期，因为本轮 audit-only。

## Audit 结果

事件数量：

```text
journey_route_order_partition_audit = 14
journey_route_order_region_audit = 26
journey_route_resource_cut_audit = 26
```

最大 conflict 数：

```text
max_conflict_pair_count = 1
```

典型强 conflict：

```text
node = 0
depth = 0
cg_iter = 3
tasks = [14, 16]
total_mass = 1.0
balance_ratio = 0.5
parent_allowed_count = 282
child_widths:
  not_same_route = 279
  same_route_order_after_strict = 244
  same_route_order_before_strict = 243
child_branch_relevant_widths:
  not_same_route = 37
  same_route_order_after_strict = 2
  same_route_order_before_strict = 1
exact_safe_partition_contract_holds = True
```

出现过的 pair：

```text
[12,13]: count = 11, max_mass = 1.0
[14,16]: count = 2,  max_mass = 1.0
[12,20]: count = 1,  max_mass = 0.25
```

所有记录的 `exact_safe_partition_contract_holds` 都为 true。

## 解释

这个结果说明两件事。

第一，route/order conflict 确实可以被 state-scoped 三路 partition 准确表达：

```text
涉及 pair 的 column 唯一归属；
不涉及 pair 的中性 column 三路共享。
```

第二，直接把它接成 live branch 不一定立刻有效：

```text
child_widths 仍然很宽。
```

例如 `[14,16]` 的三个 child 总体宽度分别是 `279/244/243`，相对 parent `282` 并没有大幅收窄；只是 branch-relevant 子集很小。这说明它更适合先做 targeted replay，而不是作为全局自动 branch 主线。

## 当前判断

seed61635 的 bottleneck 仍不是“一个 root order branch 立刻闭环”。

更准确的判断是：

```text
route/order partition 是可行的 exact-safe 表达；
但当前 pool/formulation 过宽，单个 order branch 可能不足以提升 dual/gap。
```

因此下一步不应裸接 live branch，而应：

1. 对 `[14,16]`、`[12,13]`、`[12,20]` 做 opt-in child replay；
2. 比较三个 child 的 LP bound、exact pricing events、proof CPU、gap 改善；
3. 如果 child replay 没有明显提升，再继续攻 pricing-compatible route-resource cut / stronger master formulation。

## 对主线的影响

这进一步支持当前主线判断：

- branch score 仍有用，但不是唯一瓶颈；
- route/order branch 已经有 exact-safe contract；
- cuts/formulation 仍必须并行推进，因为 child width 宽说明 LP 松弛和 column region 仍过大。

