# V754-V756 SRC / Cut-Dual Diagnosis

日期：2026-06-29

## 目的

这组实验围绕 seed61635，回答一个关键问题：

```text
seed61635 的 lower bound 不动，是因为 ordinary SRC 没被真正用上，
还是因为 ordinary SRC 本身不够强？
```

所有实验都保持 exact-safe：

- 只加入已有 `SubsetRowCut`；
- RMP cut coefficient 与 pricing true reduced cost 使用同一套 cut dual；
- cut 诊断不产生 official bound / certificate / prune；
- 外部时限 180s，仅用于短诊断，不代表 600s 全量验收。

## 实现变化

### V754

新增 route-region guided SRC 候选生成。

默认关闭；打开后仍只生成标准 `SubsetRowCut`，只是候选来源从 task-mass enumeration 扩展到 active journey task-set / route-region hub。

### V755

新增 `journey_cut_dual_diagnostics`。

每次 RMP optimal 后记录：

```text
cuts_active
nonzero_cut_dual_count
binding_cut_count
binding_nonzero_cut_count
cut_dual_abs_sum
cut_dual_objective_contribution
subset_row_nonzero_dual_count
top_cuts
```

这用于判断 cut 是否真的进入 RMP 对偶结构。

### V756

新增 opt-in 参数：

```text
journey_dynamic_subset_row_route_region_guided_max_subset_size
```

未设置时保持旧行为；显式设置后，route-region guided SRC 可以枚举更大的标准 SRC 子集。本次设为 8。

## 结果对比

| 版本 | 配置差异 | status | primal | dual | gap | SRC added | guided violated | cut dual nonzero |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| V753 | route-region audit + gated ordinary SRC | TIME_LIMIT | 560.618366 | 526.651393 | 0.060588 | 9 | n/a | n/a |
| V754 | guided SRC, max subset 默认 | TIME_LIMIT | 561.030445 | 526.651393 | 0.061278 | 17 | 4 | n/a |
| V755 | V754 + cut-dual diagnostics | EXTERNAL_TIME_LIMIT | 561.008953 | 526.651393 | 0.061242 | 17 | 4 | 30/54 |
| V756 | guided SRC max subset = 8 | EXTERNAL_TIME_LIMIT | 561.030445 | 526.651393 | 0.061278 | 24 | 34 | 17/56 |

关键点：

```text
best dual 始终 = 526.651393
```

V756 已经显著增加了 ordinary SRC 的候选覆盖：

```text
guided generated / violated = 3016 / 34
added = 24
added sizes = {3: 12, 5: 9, 7: 3}
max_cut_dual_abs_sum = 21.2536988
```

但 root corrected dual bound / best dual 仍然没有移动。

## 解释

V755 证明普通 SRC 不是“没发挥作用”：

```text
cut_dual_nonzero_event_count = 30 / 54
max_nonzero_cut_dual_count = 5
max_binding_nonzero_cut_count = 5
max_cut_dual_abs_sum = 7.663069
```

也就是说，SRC cut 被 RMP 使用了，而且很多是 binding + nonzero dual。

V756 进一步证明，问题也不只是“候选太少”：

```text
SRC added 从 17 增加到 24
guided violated 从 4 增加到 34
出现 size 7 的 larger SRC
max_cut_dual_abs_sum 从 7.663 增加到 21.254
```

但是 dual 仍不动。

因此 seed61635 当前瓶颈更像是：

```text
ordinary SRC 能局部改变 RMP 对偶面，
但不能改变决定全局 corrected lower bound 的主瓶颈。
```

这与 V631/V636 观察一致：换 root pair / 加普通 SRC 都能改变局部路径、gap 轨迹或 cut dual，但 hard case 的 best dual 仍卡住。

## 当前结论

不建议继续沿着以下方向投入主力：

```text
继续加普通 SRC 数量
继续降低普通 SRC gate
继续只扩大 ordinary SRC candidate budget
```

这些操作已经被 V754-V756 弱证伪：它们能制造更多 active cut 和 nonzero dual，但没有推动 seed61635 的 lower bound。

下一步应该转向：

1. 更强 formulation / pricing-compatible cut family；
2. route-aware 或 rank-1-like cut 的 coefficient / pricing updater 设计；
3. branch + cut 联动标签：哪些 branch state 让 cut 真正提升 child safe LB；
4. retry gate 与 branch controller 协同，减少已知无效 proof-tail 重复。

## 下一步建议

### 1. 先做 route-aware cut contract，不直接加 live cut

必须先定义：

```text
cut coefficient on JourneyColumn
pricing true RC updater
profile/direct completion bound safety
cut dual sign / sense
small-scale exhaustive validity check
```

在这些没完成前，不能把新 cut 放进 live solve。

### 2. 保留 V755 cut-dual diagnostics

它应进入后续所有 cuts/formulation 实验的默认诊断字段。以后判断 cut family 是否有用，不能只看 cut added 数，而要看：

```text
nonzero cut dual count
binding nonzero cut count
cut dual objective contribution
corrected lower bound / best dual movement
```

### 3. Branch 主线仍保留

V756 没有解决 lower-bound bottleneck，不等于 branch score 无效。它说明：

```text
branch score 负责减少 proof-tail 搜索；
cuts/formulation 负责抬 node lower bound；
二者必须并行。
```

seed61635 需要后者；seed61311 这类实例已经证明 branch-cut 联动可以成功闭环。

## 产物

```text
BPC_future/results/20260629_v755_cut_dual_diag_seed61635_180/
BPC_future/results/20260629_v756_guided_src_max8_seed61635_180/
BPC_future/results/journey_dynamic_src_route_region_v755_seed61635_20260629/
BPC_future/results/journey_dynamic_src_route_region_v756_seed61635_20260629/
BPC_future/logical_graph/run_reports/20260629_bpc_future_v755_dynamic_src_route_region_cut_dual_seed61635_zh.md
BPC_future/logical_graph/run_reports/20260629_bpc_future_v756_dynamic_src_guided_max8_seed61635_zh.md
```

