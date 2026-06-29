# V736 Dynamic SRC Gated Hard2

日期：2026-06-28

## 目的

V734 dynamic SRC cut-on 对 seed61311 有强收益，但 seed61635 仍 timeout。V735 因此实现 cut gate。本轮验证：

```text
journey_dynamic_subset_row_cut_gate_enabled=True
journey_dynamic_subset_row_cut_gate_min_violated=1
journey_dynamic_subset_row_cut_gate_min_best_violation=0.25
```

是否能保留 seed61311 的收益，同时减少 seed61635 的弱 SRC。

## 结果

| seed | V733 audit-only | V734 cut-on | V736 gated | V736 wall | V736 gap | V736 SRC added |
|---|---|---|---|---:|---:|---:|
| 61311 | EXTERNAL_TIME_LIMIT | OPTIMAL | OPTIMAL | 110.914 | 0.000000 | 20 |
| 61635 | EXTERNAL_TIME_LIMIT | EXTERNAL_TIME_LIMIT | EXTERNAL_TIME_LIMIT | 600.019 | 0.060588 | 9 |

V736 seed61311：

```text
primal = dual = 570.891015
node_count = 7
rmp_solves = 33
pricing_calls = 59
exact_pricing_calls = 30
branch = 5
fathom = 6
CB retry = 7
```

V736 seed61635：

```text
primal = 560.618366
dual = 526.651393
gap = 0.060588
branch = 26
fathom = 12
CB retry = 40
```

## Gate 行为

seed61311：

```text
root iter1: violated=0 -> blocked
root iter2: violated=8, best=0.333333333 -> added 8
depth1 node1 iter1: violated=4, best=0.5 -> added 4
depth1 node1 iter2: violated=0 -> blocked
depth1 node2 iter1: violated=2, best=0.5 -> added 2
depth1 node2 iter2: violated=6, best=0.428571429 -> added 6
total SRC added = 20
```

seed61635：

```text
root iter1: violated=0 -> blocked
root iter2: violated=1, best=0.5 -> added 1
depth1 node1 iter1: violated=8, best=0.25 -> added 8
depth1 node1 iter2: violated=1, best=0.142857143 -> blocked
depth1 node2 iter1: violated=4, best=0.090909091 -> blocked
depth1 node2 iter2: violated=4, best=0.090909091 -> blocked
total SRC added = 9
```

## 判断

V736 说明 gate 是有用的：

- seed61311 的 `EXTERNAL_TIME_LIMIT -> OPTIMAL` 收益被完整保留；
- seed61635 的 weak SRC 从 V734 的 22 条减少到 9 条；
- 低 best-violation 节点被正确挡住。

但 gate 不能解决 seed61635：

- primal/dual/gap 与 V733/V734 一样；
- CB retry 仍高；
- 说明 seed61635 需要更强 cuts/formulation 或 branch-cuts 联动，不是普通 dynamic SRC 数量问题。

## 下一步

1. 对 seed61635 单独做 stronger cut probe：
   - `max_rounds=3/4`
   - `cut_budget=1000`
   - route-compact / repeated-hub selection
   - 观察 dual/gap 是否动
2. 同时做 seed61311 no-regression repeat：
   - 重跑 2-3 次或不同 worker 排序，确认 110s OPTIMAL 不是偶然调度。
3. 进入 greedy-anchor family 小批量：
   - 只用 gated SRC；
   - 指标看 OPTIMAL 数、dual/gap、CB retry；
   - 不直接扩 full60。
4. 之后再与 RouteOpt/BKF branch controller 合并成新的 candidate config。

## Exact-Safe

V736 的 OPTIMAL 由 solver finish event 给出，`primal=dual`。SRC 通过已有 cut coefficient 和 pricing reduced-cost 逻辑进入求解，不作为 learned/audit bound。`journey_corrected_node_bound_fathom_enabled=False`，没有用 corrected-bound shortcut 剪枝。
