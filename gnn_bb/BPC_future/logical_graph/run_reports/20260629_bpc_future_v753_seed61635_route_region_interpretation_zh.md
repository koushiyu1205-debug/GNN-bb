# V753 Seed61635 Route-Region Audit Interpretation

日期：2026-06-29

## 目的

V752 已经把 dynamic SRC 的 route-region 诊断字段落到日志中。V753 用 seed61635 做一次短预算验证，目标不是求最优，而是回答：

1. 普通 SRC violation 是否围绕稳定 task/pair hub；
2. seed61635 的 lower bound 是否仍不动；
3. 下一步是否值得进入 route-aware / rank-1-like cut 原型。

## 配置

实例：

```text
BPC_future/logical_graph/tasks_020/greedy-anchor/tranquillitatis_balmer_like_20km/
tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_07_seed61635_logical_graph.json
```

运行：

```text
time_limit = 180s
journey_branch_candidate_priority = routeopt_bkf_staged
journey_branch_candidate_phased_testing_preset = routeopt_bkf_v736
dynamic SRC = audit + gated cut-on
journey_dynamic_subset_row_route_region_audit_enabled = True
```

输出：

```text
BPC_future/results/20260629_v753_route_region_audit_seed61635_180/
BPC_future/results/journey_dynamic_src_route_region_v753_seed61635_20260629/
```

自动 summary：

```text
BPC_future/logical_graph/run_reports/20260629_bpc_future_v753_dynamic_src_route_region_seed61635_zh.md
```

## 结果

180 秒结束：

```text
status = TIME_LIMIT
primal = 560.618366
dual = 526.651393
gap = 0.060588
nodes = 15
pricing = 104
exact_pricing = 43
subset_row_cuts_added = 9
```

这和 V736/V750 的 seed61635 长跑结果保持同一个 primal/dual/gap：

```text
best_primal = 560.618366
best_dual   = 526.651393
gap         = 0.060588
```

因此，当前 RouteOpt/BKF preset + gated ordinary SRC 仍没有推动 seed61635 的 lower bound。

## Route-Region 发现

dynamic SRC separation：

```text
separation_count = 6
violated = 18
added = 9
gate pass/block = 2/4
depth0: violated=1, added=1, max_best_violation=0.5
depth1: violated=17, added=8, max_best_violation=0.25
```

全局 route-region task hubs：

```text
task 2  : weighted_violation = 1.727272728
task 19 : weighted_violation = 1.5
task 1  : weighted_violation = 1.006493507
task 10 : weighted_violation = 1.0
task 13 : weighted_violation = 1.0
```

全局 route-region pair hubs：

```text
(10,19): 0.75
(13,19): 0.75
(2,16) : 0.5
(2,18) : 0.5
(16,18): 0.5
(1,19) : 0.5
(2,19) : 0.5
(3,5)  : 0.5
```

典型 root violated candidate：

```text
tasks = [2,16,18]
violation = 0.5
activity = 1.5
active overlap task sets:
  [2,4,18]          mass=0.5
  [2,6,8,14,16]     mass=0.5
  [16,18]           mass=0.5
```

典型 depth-1 violated candidate：

```text
tasks = [2,10,19]
violation = 0.25
activity = 1.25
active overlap task sets include:
  [2,5,10,12,13,20]
  [1,2,4,9,19]
  [1,2,4,10,12,13,20]
  [3,10,13,19]
```

## 判断

V753 说明 seed61635 的 ordinary SRC violation 不是完全随机分散的。

它有明显的两个 hub 族：

1. `task 2` 相关区域：`(2,16)`, `(2,18)`, `(2,19)`, `(2,10)`, `(2,12)`；
2. `task 19` 相关区域：`(10,19)`, `(13,19)`, `(1,19)`, `(2,19)`。

但这些普通 SRC 即使被加入 9 条，dual 仍未移动。这说明下一步不应只是降低 gate 阈值、加更多同类 SRC。更合理的是：

- 围绕 `task 2 / task 19` 的 route-region 做更强 cut family；
- 把 active task-set overlap 和 branch state 绑定；
- 设计 rank-1-like / route-aware cut diagnostic prototype；
- 同时检查这些 hub 是否在 600s full run 的后续节点持续出现。

## Exact-Safe

V753 的 route-region audit 不提供：

- official bound；
- certificate；
- prune/fathom 条件；
- learned cut；
- learned branching proof。

这次唯一会影响求解的仍是原有 valid gated SRC；route-region 字段只是日志诊断。

## 下一步

1. 用同一 summarizer 对 V736/V737/V738/V740/V750 的旧日志做兼容汇总，确认旧日志缺 route-region 字段时只保留 task hub。
2. 对 seed61635 再跑一个短预算 variant：`route_region_audit + higher audit_top_n`，不增加 cut，专门采集更多 blocked low-violation regions。
3. 如果 `task 2/19` hub 在更多节点持续出现，进入 route-aware/rank-1-like cut prototype：
   - 先 diagnostic-only；
   - 再实现 coefficient / reduced-cost updater；
   - 最后小规模 exact-safe A/B。
4. 不建议继续只调普通 SRC gate 阈值。V753 与 V736/V750 一致，ordinary SRC 对 seed61635 的 lower bound 没有实质推动。
