# V733/V734 Dynamic SRC Hard2 A/B

日期：2026-06-28

## 目的

V729 的 paired replay 说明 greedy-anchor hard cases 不是单靠 depth1/depth2 branch pair 替换就能闭环。V731/V732 短预算 smoke 发现 seed61311 存在 violated dynamic subset-row cuts，且 cut-on 能早期抬高 RMP objective。

本轮把对照扩大到 greedy-anchor hard2、600s：

- V733: RouteOpt/BKF + dynamic SRC audit-only；
- V734: RouteOpt/BKF + dynamic SRC cut-on；
- 两个实例并行，外部 `600s`。

## 配置边界

共同配置：

```text
config = BPC_future/configs/moon_trek_20_smoke.yaml
instances = seed61311, seed61635
time_limit = 600
max_workers = 2
journey_branch_candidate_priority = routeopt_bkf_staged
journey_branch_candidate_phased_testing_phase1_lp_enabled = True
journey_branch_candidate_phased_testing_phase2_heuristic_enabled = True
journey_branch_candidate_phased_testing_dynamic_k_enabled = True
journey_branch_candidate_phased_testing_bkf_score_order_enabled = True
journey_dynamic_subset_row_cut_budget = 600
journey_dynamic_subset_row_max_depth = 1
journey_dynamic_subset_row_max_rounds = 2
journey_dynamic_subset_row_max_subset_size = 6
```

V733:

```text
journey_dynamic_subset_row_audit_enabled = True
journey_dynamic_subset_row_cuts_enabled = False
```

V734:

```text
journey_dynamic_subset_row_audit_enabled = True
journey_dynamic_subset_row_cuts_enabled = True
journey_dynamic_subset_row_max_added = 20
```

## 总表

| seed | V733 status | V733 wall | V733 primal | V733 dual | V733 gap | V734 status | V734 wall | V734 primal | V734 dual | V734 gap | SRC added |
|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 61311 | EXTERNAL_TIME_LIMIT | 600.024 | 570.891016 | 547.186422 | 0.041522 | OPTIMAL | 110.711 | 570.891015 | 570.891015 | 0.000000 | 20 |
| 61635 | EXTERNAL_TIME_LIMIT | 600.034 | 560.618366 | 526.651393 | 0.060588 | EXTERNAL_TIME_LIMIT | 600.017 | 560.618366 | 526.651393 | 0.060588 | 22 |

## seed61311

V734 是严格正信号：

```text
EXTERNAL_TIME_LIMIT -> OPTIMAL
wall = 110.710595s
node_count = 7
rmp_solves = 33
pricing_calls = 59
exact_pricing_calls = 30
fathom = 6
CB retry = 7
```

SRC 分离：

```text
root cg_iter=2: violated=8, added=8, best_violation=0.333333333
depth1 node1 cg_iter=1: violated=4, added=4, best_violation=0.5
depth1 node2 cg_iter=1: violated=2, added=2, best_violation=0.5
depth1 node2 cg_iter=2: violated=6, added=6, best_violation=0.428571429
total subset_row_added = 20
```

解释：

- root 最终 RMP lower trajectory 仍会回到 `547.186422`，所以不是单纯 root bound 被永久抬高；
- 但 depth1 的 SRC 明显改变了 child proof landscape，使 branch tree 能在 7 个节点内闭环；
- 这说明 greedy-anchor 至少有一类 hard case 需要 branch + cuts 联动，而不是只优化 branch pair。

## seed61635

V734 没有改善：

```text
status = EXTERNAL_TIME_LIMIT
primal = 560.618366
dual = 526.651393
gap = 0.060588
branch = 29
fathom = 9
CB retry = 38
subset_row_added = 22
```

SRC 分离存在，但不够：

```text
root cg_iter=2: violated=1, added=1, best_violation=0.5
depth1 node1: added=9
depth1 node2: added=12
total subset_row_added = 22
```

解释：

- seed61635 有 SRC violation，但这些 cut 没有推动 final closure；
- gap/dual 和 V733 完全一致，说明这类实例还需要更强 cut family、branch-cuts 联动，或 incumbent/formulation 进一步强化；
- 不能把 dynamic SRC 直接全局视为充分解法。

## 结论

这轮是 Branch Score 主线之外的关键进展：

```text
RouteOpt/BKF branch controller + dynamic SRC cut-on
在 greedy-anchor hard2 中得到 1/2 timeout -> optimal。
```

这推翻了“greedy-anchor 只能靠更多 branch replay 找正例”的假设。至少 seed61311 的瓶颈是 branch 与 subset-row cuts 的组合，而不是单个 Ryan-Foster pair。

但当前还没达到 20-scale 全部 600s OPTIMAL：

- seed61311 已经闭环；
- seed61635 仍 timeout；
- full60 未跑；
- 小规模 5/10 no-regression 未验证。

## 下一步

1. 做 V735 hard2 cut-gate：
   - cut-on 只在 `violated > 0` 且 `best_violation >= threshold` 的 node 启用；
   - 记录 cut density、RMP solve time、pricing calls，防止 full60 上 cut 过多。
2. 对 seed61635 增强 cut/search：
   - 增加 dynamic SRC max rounds 到 3/4；
   - 测试更高 budget 或 route-compact selection；
   - 检查 root/depth1 repeated task hubs，如 `[2,16,18]`、`[2,8,19]`、`[2,6,19]`。
3. 再跑 random-TW 20 greedy-anchor family，而不是直接 full60：
   - 先确认 SRC 对哪些 family 有效；
   - 避免 sector-wave 已由 branch controller 解决时被多余 cuts 拖慢。
4. 最后做 5/10 no-regression：
   - dynamic SRC 默认仍应 opt-in；
   - 小规模必须验证不会破坏 60/60 OPTIMAL 和平均时间。

## 验证边界

本轮 V734 的 `OPTIMAL` 来自 solver finish event，`primal=dual=570.891015`，不是 learned score、audit bound 或 corrected-bound shortcut。

V733/V734 的 logs 仍显示：

```text
journey_dynamic_subset_row_audit_enabled=True
journey_dynamic_subset_row_cuts_enabled=True/False
journey_corrected_node_bound_fathom_enabled=False
```

因此当前结论是 exact-safe 的实验结论，但还不是最终验收。
