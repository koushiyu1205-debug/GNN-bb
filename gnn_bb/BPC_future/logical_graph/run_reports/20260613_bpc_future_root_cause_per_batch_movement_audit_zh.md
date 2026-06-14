# BPC_future 根因审计补充：per-batch movement audit

日期：2026-06-13

## 目标

上一轮 stage-aware audit 说明：

- aggregate low-overlap 不够；
- `cg1_active_avg_overlap <= 0.5` 是强 negative filter，但不是完整 positive selector；
- Apollo20 return8 r2 的正向分叉发生在 cg3；
- Apollo20 return12 r2 的 cg3 `[2,20]` family 是 active-redundant no-op batch。

本轮继续只读分析：

**把每一次 heuristic returned batch 作为一行，用 post-addition RMP objective / active hash / fractional movement 做 immediate label，检查前置 batch 特征是否能解释 movement 与 final outcome。**

本轮不改 solver、不改 pricing、不改 RMP、不改 Pulse、不跑新 benchmark。

## 数据构造

输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- 对应 `logs/*.jsonl`

分析集：

- Phase 10H 非 baseline 20-task rows；
- 18 runs；
- 逐 run 读取前 4 个 heuristic `journey_pricing` returned batch；
- 形成 64 个 per-stage batch rows。

每行包含：

- instance / profile / repeat / final outcome；
- CG stage；
- returned count / truncated count / best RC；
- returned task-set batch pair overlap / Jaccard / union / max task freq；
- batch 与当前 active top samples 的 relation：
  - avg max Jaccard；
  - avg max overlap；
  - active-redundant fraction；
  - active-bridge fraction；
- post-addition labels：
  - `objective_delta = next_rmp_objective - current_rmp_objective`；
  - `active_hash_changed`；
  - `fractional_sum_delta`；
  - `strong_moved = objective_delta < 0 and active_hash_changed`；
  - `integerizing = fractional_sum_delta < -0.5`。

注意：

- post-addition labels 是诊断标签，不是线上可用 selector 输入；
- 这一步用于判断哪些前置特征接近可训练/可解释的 selector。

## 总体结果

64 个 per-stage batch rows：

```text
stage rows = 64
moved = 63
strong_moved = 63
integerizing = 26
```

唯一没有 immediate movement 的 batch：

```text
instance = mt20_greedy_apollo_01
profile = experimental_early_new_task_set_quota_3_return12_20_only
repeat = 2
cg = 3
final outcome = worsened
returned = 4
best_rc = -6.110727
sets = [[2,13,20], [2,10,20], [2,3,20], [2,20]]
objective_delta = 0.0
active_hash_changed = False
```

这说明：

- Apollo return12 r2 的 cg3 no-op 是真实异常点；
- 但 `immediate movement` 这个标签整体太宽，因为绝大多数 batch 都会改变 RMP objective 或 active hash；
- 不能把“加入后 RMP objective 下降”当作最终好轨迹的充分条件。

## Final outcome vs stage movement

### Improved runs

```text
stage rows = 40
moved = 40
strong_moved = 40
integerizing = 19
```

### Worsened runs

```text
stage rows = 24
moved = 23
strong_moved = 23
integerizing = 7
```

也就是说，worsened runs 里的大多数 batches 也会 immediate move。

这解释了为什么之前很多局部指标失败：

- best RC 更负不能保证最终改善；
- immediate objective drop 不能保证最终改善；
- active hash changed 不能保证最终改善；
- returned count 更大不能保证最终改善。

## Stage aggregate 对照

### CG1

| outcome | rows | active_avg_overlap | active_redundant_frac | active_bridge_frac | objective_delta |
|---|---:|---:|---:|---:|---:|
| improved | 10 | 0.550 | 0.125 | 0.875 | -81.378 |
| worsened | 8 | 0.820 | 0.672 | 0.328 | -171.272 |

CG1 里 worsened rows 的 objective drop 更大，但 active redundancy 更高。

这说明：

> 前期强 RMP objective drop 可能只是 active-redundant replacement 的局部改善，不等价于好 tail。

### CG2

| outcome | rows | active_avg_overlap | active_redundant_frac | active_bridge_frac | objective_delta |
|---|---:|---:|---:|---:|---:|
| improved | 10 | 0.569 | 0.338 | 0.662 | -41.816 |
| worsened | 8 | 0.658 | 0.615 | 0.385 | -45.174 |

CG2 同样显示 worsened rows 更 active-redundant。

### CG3

| outcome | rows | active_avg_overlap | active_redundant_frac | active_bridge_frac | objective_delta |
|---|---:|---:|---:|---:|---:|
| improved | 10 | 0.566 | 0.317 | 0.683 | -29.207 |
| worsened | 5 | 0.621 | 0.525 | 0.475 | -10.859 |

CG3 开始体现 late-stage bridge 的重要性：

- improved rows 更 bridge-like；
- worsened rows 更 redundant；
- 但这个 aggregate 仍不能单独给出 production rule。

## Per-stage row label 的 separability

把 64 个 stage rows 全部作为样本，并用 final outcome 做标签。

最好的单特征阈值之一：

```text
active_avg_overlap <= 0.5555555555555556
accuracy = 0.765625
tp = 32
fp = 7
tn = 17
fn = 8
```

另一个等价强信号：

```text
active_redundant_frac <= 0.25
accuracy = 0.765625
tp = 32
fp = 7
tn = 17
fn = 8
```

这比随机好，但远远不是 production selector。

含义：

- active relation 确实比 raw pair overlap / best RC 更接近 final outcome；
- 但 per-batch 层面的单阈值不够；
- final outcome 是跨多轮 trajectory 的结果，不能由单个 stage batch 简单决定。

## Immediate movement 标签的失败

如果用 `strong_moved = objective_delta < 0 and active_hash_changed` 做标签，几乎所有 batch 都是 positive：

```text
strong_moved = 63 / 64
```

因此任何 selector 很容易“预测 movement”，但这没有价值。

真正困难的问题不是：

> 这个 batch 加进去 RMP 会不会动？

而是：

> 这个 batch 加进去以后，后续 trajectory 是否走向更好 incumbent / 更少 tail / 更低 final gap？

这一步很重要，因为它排除了一个可能的错误方向：

- 不能用 immediate RMP objective delta 直接作为 optimization target；
- 不能把 active hash changed 当作 success；
- 必须使用 downstream trajectory label，例如 subsequent incumbent update、tail state、final primal/gap。

## Key rows

### Apollo return8 r2 improved

```text
cg1:
  active_avg_overlap = 1.000
  active_redundant_frac = 1.000
  active_bridge_frac = 0.000
  objective_delta = -202.197

cg2:
  active_avg_overlap = 0.688
  active_redundant_frac = 0.375
  active_bridge_frac = 0.625
  objective_delta = -78.771

cg3:
  active_avg_overlap = 0.479
  active_redundant_frac = 0.125
  active_bridge_frac = 0.875
  objective_delta = -10.375
  fractional_sum_delta = -7.0
```

Interpretation：

- cg1 是 active-redundant；
- cg3 才是 positive bridge；
- good trajectory 来自 late-stage bridge，而不是 cg1 immediate drop。

### Apollo return12 r2 worsened

```text
cg1:
  active_avg_overlap = 1.000
  active_redundant_frac = 1.000
  active_bridge_frac = 0.000
  objective_delta = -238.007

cg2:
  active_avg_overlap = 0.722
  active_redundant_frac = 0.583
  active_bridge_frac = 0.417
  objective_delta = -58.238

cg3:
  active_avg_overlap = 0.583
  active_redundant_frac = 0.500
  active_bridge_frac = 0.500
  objective_delta = 0.000
  active_hash_changed = False
  fractional_sum_delta = 0.0
```

Interpretation：

- cg1/cg2 虽然让 RMP objective 大幅下降，但把 trajectory 推到后续 no-op；
- cg3 `[2,20]` family 没有 marginal movement；
- final worsened。

### Tranq return8 vs return12

`mt20_greedy_tranq_01` return8 worsened：

```text
cg2 active_redundant_frac = 0.750
cg3 active_redundant_frac = 0.625
```

`mt20_greedy_tranq_01` return12 improved：

```text
cg2 active_redundant_frac = 0.583
cg3 active_redundant_frac = 0.667 / 0.750 depending repeat
```

Tranq case 说明：

- active redundancy 也不是完整解释；
- return12 的改善还与 sequence/signature/timing、后续 active path、incumbent update 相关；
- 需要 downstream trajectory label。

## 根因进一步收紧

当前根因不只是：

> batch overlap / diversity。

更准确是：

> returned batch 通过多轮 RMP active-basis trajectory 累积影响最终结果。单轮 RMP objective drop 和 active hash movement 几乎总会发生，但其中大量 movement 是短视或 redundant 的。真正有益的是在合适 stage 形成 active-family bridge，并把 trajectory 推向后续 incumbent / lower tail 的 concrete signature batch。

这解释了为什么：

- 5/10 不能承受 trial-and-error 式额外 batch 搜索；
- 20 中 return8/return12 只能随机扰动轨迹；
- low-overlap 是强信号但不是充分规则；
- immediate RMP movement 也不是充分规则；
- selector 必须用 downstream labels 做离线校准。

## 下一步

仍然不要改生产求解路径。

下一步最合理的是构造 stage-aware trajectory dataset：

每个 returned batch 一行，保留：

- addition 前特征：
  - batch overlap / Jaccard；
  - active relation；
  - active redundancy / bridge fraction；
  - RC distribution；
  - sequence / signature / start-time / arc-option diversity；
  - current fractional pressure；
  - current active hash family；
- addition 后标签：
  - immediate objective_delta；
  - active_hash_changed；
  - fractional_sum_delta；
  - next 1-2 CG incumbent update；
  - tail state；
  - final primal delta；

然后做两个层级的离线判断：

1. negative filter：
   - 找出哪些 batch 形态几乎从不通向 improved；
2. positive bridge selector：
   - 找出哪些 stage/context/signature 组合能稳定推动 downstream trajectory。

只有这两层都通过，再考虑 opt-in A/B。

## 目标状态

目标仍未完成。

本轮新增了一个关键证伪：

> immediate RMP movement 不是优化目标，几乎所有 batch 都会 immediate move；最终优化需要 downstream trajectory selector。

