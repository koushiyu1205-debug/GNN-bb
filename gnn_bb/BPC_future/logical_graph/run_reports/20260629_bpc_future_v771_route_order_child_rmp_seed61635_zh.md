# V771 Route-Order Child RMP Probe - seed61635

日期：2026-06-29

## 目的

V769 显示 same-route order partition 的 child width 很宽，因此不能直接假设 live order branch 会有效。

本轮在 `journey_route_order_partition_audit` 中新增可选 RMP-only child probe：

```text
journey_route_order_partition_audit_child_rmp_enabled=True
```

它只解三路 child 的当前 finite-pool RMP，记录 LP objective/gain，不加入列、不剪枝、不作为 official bound。

## 运行口径

实例：

```text
tasks020_07_seed61635
```

输出：

```text
BPC_future/results/20260629_v771_route_order_child_rmp_seed61635_45/results.csv
```

结果：

```text
status = TIME_LIMIT
time = 44.003467s
primal = 561.030445
dual = 526.651393
gap = 0.061278
nodes = 3
columns = 355
```

求解结果仍未改善，这是预期，因为 child RMP probe 是 audit-only。

## 关键发现

虽然 child width 宽，但 child RMP objective gain 很明显。

### [14,16] at root cg_iter=3

```text
parent_allowed = 282

same_route_order_before_strict:
  objective = 701.781815667
  gain = +2.551551
  allowed = 243

same_route_order_after_strict:
  objective = 699.297298
  gain = +0.067033333
  allowed = 244

not_same_route:
  objective = 737.54468775
  gain = +38.314423083
  allowed = 279
```

### [12,20] at root cg_iter=6

```text
parent_allowed = 294

same_route_order_before_strict:
  objective = 625.674183333
  gain = +27.370284708

same_route_order_after_strict:
  objective = 646.563682
  gain = +48.259783375

not_same_route:
  objective = 607.1883478
  gain = +8.884449175
```

### [12,13] later root tail

`[12,13]` 反复出现，child gain 稳定为正：

```text
same_route_order_before_strict gain ≈ +18 to +29
same_route_order_after_strict  gain ≈ +8 to +13
not_same_route                 gain ≈ +16 to +20
```

在 depth 1 也仍然有正 gain：

```text
node 1 depth 1 [12,13]:
  before gain = +27.20
  after  gain = +7.13
  not_same_route gain = +16.31

node 2 depth 1 [12,13]:
  before gain = +15.48
  after  gain = +21.90
  not_same_route gain = +18.30
```

## 解释

V769 的判断需要修正：

```text
child width 确实宽；
但 finite-pool child RMP gain 并不弱。
```

这说明 route/order branch 不是无效方向。它可能解决的是：

```text
当前 formulation 下 active support 的 order disjunction 造成 LP 松弛；
把 order region 分开后，有限 RMP 下界明显上升。
```

但这还不是完整证明，因为 child RMP gain 可能会被后续 pricing 负列吃掉。

因此下一步必须做：

```text
短预算 child pricing replay
```

而不是直接接 live branch，也不是放弃 order branch。

## Exact-Safe 边界

本轮所有 child RMP probe 均标记：

```text
official_bound_effect = false
certificate_effect = false
```

它们只是 diagnostic finite-pool LP，不用于：

- fathom；
- prune；
- official lower bound；
- incumbent；
- branch tree mutation。

## 当前判断

seed61635 的 bottleneck 现在更清楚：

1. 普通 Ryan-Foster root score 不能完全解决；
2. route/order disjunction 有明显 LP lift 信号；
3. 但必须验证 child pricing closure 后 gain 是否保留；
4. 如果 child pricing 后 gain 仍保留，same-route order branch 应进入 opt-in live controller；
5. 如果 gain 被 negative columns 快速吃掉，说明还需要 pricing-compatible route-resource cuts / stronger formulation。

## 下一步

1. 对 `[14,16]`、`[12,20]`、`[12,13]` 做三路 child pricing replay：
   - 每 child 短预算 CG；
   - 记录 objective gain 是否保持；
   - 记录 negative columns、retry、proof CPU。
2. 若某个 pair 的三个 child 都保持正 gain，优先做 live three-way order branch controller。
3. 若只有一侧 gain 强，进入 branch-score / child-ordering 学习，不直接作为全局规则。

