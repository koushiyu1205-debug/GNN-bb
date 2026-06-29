# V750 RouteOpt/BKF v736 Preset Hard2 600s

日期：2026-06-29

## 目的

V749 已证明：

```text
journey_branch_candidate_phased_testing_preset=routeopt_bkf_v736
```

可以复现 seed61311 的 V736 好路径。V750 把这个 preset 放回 greedy-anchor hard2，验证：

- seed61311 是否 no-regression；
- seed61635 是否仍是 dual/gap 不动的 hard case；
- diagnostic-only cut snapshot 是否能安全保留为训练/诊断字段。

## 配置

共同配置：

```text
config = BPC_future/configs/moon_trek_20_smoke.yaml
time_limit = 600
max_workers = 2
journey_branch_candidate_priority = routeopt_bkf_staged
journey_branch_candidate_phased_testing_preset = routeopt_bkf_v736
journey_branch_candidate_phased_testing_phase1_lp_enabled = True
journey_branch_candidate_phased_testing_phase2_heuristic_enabled = True
journey_branch_candidate_phased_testing_dynamic_k_enabled = True
journey_branch_candidate_phased_testing_bkf_score_order_enabled = True
```

cut/snapshot 配置：

```text
journey_branch_candidate_phased_testing_phase1_cut_snapshot_enabled = True
journey_branch_candidate_phased_testing_bkf_phase1_cut_snapshot_min_gain_weight = 0.0
journey_branch_candidate_phased_testing_bkf_phase1_cut_snapshot_product_weight = 0.0

journey_dynamic_subset_row_audit_enabled = True
journey_dynamic_subset_row_cuts_enabled = True
journey_dynamic_subset_row_cut_gate_enabled = True
journey_dynamic_subset_row_cut_gate_min_violated = 1
journey_dynamic_subset_row_cut_gate_min_best_violation = 0.25
journey_dynamic_subset_row_cut_budget = 600
journey_dynamic_subset_row_max_depth = 1
journey_dynamic_subset_row_max_rounds = 2
journey_dynamic_subset_row_max_subset_size = 6
journey_dynamic_subset_row_max_added = 20
```

## 结果

输出：

```text
BPC_future/results/20260629_v750_routeopt_v736_preset_snapshot_diag_hard2_600/results.csv
```

| seed | status | wall | primal | dual | gap | node_count | pricing | exact pricing | subset_row_added |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 61311 | OPTIMAL | 113.795881 | 570.891015 | 570.891015 | 0.000000 | 7 | 59 | 30 | 20 |
| 61635 | EXTERNAL_TIME_LIMIT | 600.020446 | 560.618366 | 526.651393 | 0.060588 | - | - | - | - |

对比 V736：

| seed | V736 | V750 | 判断 |
|---|---:|---:|---|
| 61311 | OPTIMAL, 110.913642s | OPTIMAL, 113.795881s | no-regression，轻微 snapshot/环境开销 |
| 61635 | EXTERNAL_TIME_LIMIT, gap 0.060588 | EXTERNAL_TIME_LIMIT, gap 0.060588 | 完全未改善 |

## seed61311

V750 分支路径：

```text
node0 depth0: RF(2,16)
node1 depth1: RF(5,13)
node2 depth1: RF(5,14)
node5 depth2: RF(5,13)
node6 depth2: RF(13,14)
```

这与 V736 好路径一致。最终：

```text
status = OPTIMAL
primal = dual = 570.891015
branch = 5
fathom = 6
CB retry = 7
```

cut 行为：

```text
root cg1: best=0.0, added=0, blocked
root cg2: best=0.333333333, added=8
depth1 node1 cg1: best=0.5, added=4
depth1 node1 cg2: best=0.0, added=0, blocked
depth1 node2 cg1: best=0.5, added=2
depth1 node2 cg2: best=0.428571429, added=6
```

结论：`routeopt_bkf_v736` preset 成功保留 seed61311 的 branch-cut 联动收益。

## seed61635

V750 分支路径前段：

```text
node0 depth0: RF(12,20)
node1 depth1: RF(11,15)
node2 depth1: RF(14,16)
node5 depth2: RF(4,9)
node6 depth2: RF(17,18)
...
```

600s 结束时：

```text
status = EXTERNAL_TIME_LIMIT
best_primal = 560.618366
best_dual = 526.651393
gap = 0.060588
branch = 26
fathom = 12
CB retry = 40
```

这与 V736 的 seed61635 结果一致：

```text
best_primal = 560.618366
best_dual = 526.651393
gap = 0.060588
```

cut 行为：

```text
root cg1: best=0.0, added=0, blocked
root cg2: best=0.5, added=1
depth1 node1 cg1: best=0.25, added=8
depth1 node1 cg2: best=0.142857143, added=0, blocked
depth1 node2 cg1: best=0.090909091, added=0, blocked
depth1 node2 cg2: best=0.090909091, added=0, blocked
```

这说明普通 dynamic SRC 即使配合稳定 RouteOpt/BKF branch preset，也没有推动 seed61635 的 lower bound。

## Tail 诊断

seed61635 的 tail-action audit：

```text
EARLY_BRANCH = 56
CONTINUE_COLUMN_GENERATION = 31
BROAD_PLATEAU_FALLBACK = 25
```

这很重要：

- 大量节点已经被诊断为 D 类/early-branch 机会；
- 但当前 V750 没有把 audit 建议转成行为；
- 即使转成行为，也不能把当前 RMP objective 当 exact bound，child 仍必须靠 exact pricing closure。

因此 seed61635 后续有两条并行方向：

1. exact-safe score-gated early branch / child ordering，减少无效 final-probe 和 CB retry；
2. stronger pricing-compatible cuts / formulation，让 best dual 真正上升。

## Cut Snapshot

V750 开启：

```text
phase1_cut_snapshot_enabled=True
snapshot weights = 0
```

统计：

seed61311：

```text
candidate_events = 5
phase1_base_wall = 0.576331
phase1_snapshot_wall = 0.115715
phase2_wall = 1.480927
```

seed61635：

```text
candidate_events = 26
phase1_base_wall = 2.437046
phase1_snapshot_wall = 0.129134
phase2_wall = 8.416854
```

snapshot 本身开销很小，且权重为 0 时没有破坏 seed61311 好路径。因此它可以保留为诊断/训练特征，但仍不应直接给正权重进入 live BKF。

## 判断

V750 证明：

1. `routeopt_bkf_v736` preset 是必要的，不能裸开 `routeopt_bkf_staged`。
2. seed61311 属于 branch-cut 联动可解决的 hard case。
3. seed61635 不属于当前普通 dynamic SRC + branch preset 可解决的 hard case。
4. seed61635 的核心仍是 lower-bound/formulation/cuts 不够强，伴随大量 proof-tail retry。

## 下一步

对 seed61635，不建议继续只调 branch pair 权重。下一步应优先做：

```text
V751 stronger cut/formulation probe
```

建议先做只读/小批量 probe：

- dynamic SRC max_rounds 提高到 `3/4`；
- cut_budget 提高到 `1000`；
- max_added 提高到 `60/80`；
- gate 分层：root 保守、child 更宽；
- 记录 dual/gap 是否移动，而不是只看 cut 数量。

如果 dual/gap 仍不动，就应进入 route-aware / rank-1-like cut 设计，而不是继续扩普通 subset-row cuts。

## Exact-Safe

V750 的学习/RouteOpt/BKF/snapshot 部分只影响 branch candidate ordering 和日志特征。

不改变：

- official lower bound；
- no-negative certificate；
- fathom/prune 条件；
- child lower bound exactness。

seed61311 的 OPTIMAL 来自 solver finish event，`primal=dual=570.891015`。
