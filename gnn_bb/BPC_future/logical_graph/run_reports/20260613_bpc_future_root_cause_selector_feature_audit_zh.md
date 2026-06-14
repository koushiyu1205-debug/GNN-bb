# BPC_future 根因审计补充：selector feature audit

日期：2026-06-13

## 目标

上一轮 returned-boundary calibration 已经证明：

- baseline 会截断 rank1+ strong negative candidates；
- early quota return8 能把 rank1-rank7 带入 pool；
- Apollo20 dp1000 单点从 `921.640296` 改到 `793.914380`。

本轮继续只读检查：

**rank、rough RC、future-active-hit 这些 candidate-level 特征，能不能直接作为 selector？**

如果这些特征能解释 outcome，下一步可以设计 selector。  
如果不能，说明 root cause 还在更复杂的 batch-level trajectory interaction。

## 输入

只读输入：

- `BPC_future/results/root_cause_returned_boundary_apollo20_dp1000_20260613/logs/*.jsonl`
- `BPC_future/results/root_cause_returned_boundary_apollo20_dp1000_20260613/summary.csv`

只使用：

- `diagnostic_returned_boundary_candidate_samples`
- `diagnostic_truncated_boundary_candidate_samples`
- `journey_column_addition`
- `journey_pool_structure_diagnostics.pool_active_top_task_set_value_samples`

注意：`pool_active_top_task_set_value_samples` 是 capped sample，不是完整 active set。因此 `future_active=Y` 是强证据，`future_active=N` 只能表示未出现在 sample 中。

## 发现 1：rough RC / rank 不是 selector

Apollo20 dp1000 return8，cg1：

| rank | task-set | rough RC | future active top sample |
|---:|---|---:|---|
| 0 | `[5,8,15]` | -139.913748 | N |
| 1 | `[4,5,8]` | -137.150710 | N |
| 2 | `[5,8,18]` | -136.660461 | N |
| 3 | `[4,5,15]` | -136.347326 | N |
| 4 | `[4,8,15]` | -136.011232 | Y, cg4 value 0.333333333 |
| 5 | `[4,5,18]` | -134.743366 | Y, cg2 value 1.0 |
| 6 | `[8,15,16]` | -132.930824 | Y, cg2 value 1.0 |
| 7 | `[8,15,18]` | -132.886574 | Y, cg3 value 0.333333333 |

结论：

- rank0-rank3 更负，但未出现在后续 active top sample；
- rank4-rank7 较弱，却进入后续 active top sample；
- 因此 `rough RC 越负越好` 不是 selector。

cg2：

| rank | task-set | rough RC | future active top sample |
|---:|---|---:|---|
| 0 | `[12,16,17]` | -123.681417 | Y, cg3 value 1.0 |
| 1 | `[4,12,17]` | -121.654710 | N |
| 2 | `[12,14,16]` | -74.761131 | N |
| 3 | `[12,14,17]` | -74.197467 | N |
| 4 | `[4,12,14]` | -73.864202 | N |
| 5 | `[14,16,17]` | -72.262031 | N |
| 6 | `[11,16,17]` | -71.648997 | N |
| 7 | `[11,12,17]` | -70.814616 | N |

cg2 又是 rank0 active，说明连“较弱 rank 更好”也不是规则。

## 发现 2：future-active-hit 是后验解释，不是前置 selector

同一个 `[5,8,15]` 在不同 batch context 下作用不同。

baseline：

```text
cg1 returned rank0 [5,8,15]
future active hits: cg2 value 1.0, cg3 value 1.0
final primal: 921.640296
```

return8：

```text
cg1 returned rank0 [5,8,15]，同时返回 rank1-rank7
[5,8,15] 未出现在后续 active top sample
final primal: 793.914380
```

解释：

- `[5,8,15]` 本身不是“好/坏”的独立标签；
- 它在 baseline 中 active，但 baseline 仍差；
- return8 加入一批其它候选后，active basis 选择转向 `[4,5,18]`、`[8,15,16]`、`[8,15,18]`、`[4,8,15]` 等；
- 改善来自 batch-level interaction，而不是单个 candidate 的孤立质量。

因此：

> future-active-hit 可以解释后验 trajectory，但不能直接作为前置 selector。一个 candidate 是否 active 取决于同批其它 columns 与后续 dual/RMP 轨迹。

## 发现 3：returned cut 的真实问题是 batch composition

baseline 每轮只返回 rank0：

| cg | returned rank0 | first truncated examples |
|---:|---|---|
| 1 | `[5,8,15]` | `[4,5,8]`, `[5,8,18]`, `[4,5,15]` |
| 2 | `[5,12,18]` | `[4,5,12]`, `[4,12,18]`, `[4,12,17]` |
| 3 | `[4,8,12]` | `[12,16,17]`, `[8,12,17]`, `[4,12,17]` |

return8 改变的是 batch composition：

- cg1 从 1 条变成 8 条；
- 被 baseline 截断的 `[4,5,8]`、`[5,8,18]`、`[4,5,15]`、`[4,8,15]`、`[4,5,18]`、`[8,15,16]`、`[8,15,18]` 被一起加入；
- 后续 active top sample 中实际出现的是其中一部分，不是全部；
- final primal 改善到 `793.914380`。

这说明：

> 根因不是单列选择，而是 early returned batch 的 composition 改变了后续 active-basis path。

## 对“为什么做了这么多仍然不行”的解释

前面很多尝试失败，是因为它们都只控制了 batch composition 的某个粗维度：

- `return8 / return12` 控制 batch size，但不控制 batch quality；
- `best RC` 控制排序，但 active-hit 反例证明更负不一定更有用；
- `task-set priority` 控制粗 family，但不能控制 signature/timing 和同批相互作用；
- `Pulse worker` 找 hidden negative，但不保证这些 negative 能构成有利 batch；
- `future active hit` 是后验结果，不是 addition 前可安全使用的 feature；
- `final fractional pressure` 更是后验状态，且跨日志已经被证伪为充分指标。

所以当前没有稳定优化，不是因为局部机制没写够，而是因为：

**我们还没有一个 addition 前可见、可泛化、能预测 batch-level RMP trajectory 的 selector。**

## 当前最精确根因表述

综合到这一步，根因应表述为：

> 5/10 不能不退化，是因为小规模没有足够收益空间承受额外 worker/probe/search 固定开销，必须 20-only no-op guard。  
> 20 不能稳定优化，是因为 pricing 已能产生 true-RC negative candidates，但 early returned batch 的 candidate/signature/timing composition 会非线性改变后续 active-basis trajectory；现有规则只能粗暴扰动 batch size/order，不能在 addition 前稳定预测哪组 batch 会带来 incumbent/tail 改善。

这个判断有直接证据：

- baseline rank1+ strong negative candidates 被截断；
- return8 带入 rank1-rank7 后 Apollo20 单点改善；
- 更负 rank0-rank3 未必 active，较弱 rank4-rank7 反而 active；
- 同一 `[5,8,15]` 在 baseline active 但结果差，在 return8 batch 中不 active但结果好；
- 跨日志中 return12 在 `tranq20_01` / `mt20_greedy_tranq_01` 可改善，在 Apollo20 可变差。

## 仍未完成的证明

这还不是最终优化方向证明。

缺口：

1. 还没有 selector feature 能在 addition 前稳定预测 batch-level trajectory；
2. 还没有在 5/10 gate 下证明 selector no-regression；
3. 还没有在 selected 20 hard set 上证明 selector 稳定大幅加速；
4. 当前 `future_active` 依赖 capped active top sample，不是完整 active set；
5. 当前 calibration 只覆盖 Apollo20 dp1000 单点。

## 下一步

下一步不应继续扩大 return count 或 Pulse worker。

应做 calibration-only batch selector audit：

1. 对 returned batch 整体提特征，而不是只看单个 candidate：
   - batch task union；
   - pairwise overlap / diversity；
   - rough RC distribution；
   - new vs replacement composition；
   - relation to current active top samples；
   - timing/start profile spread；
   - signature family diversity；
2. 离线拟合或规则化解释 improved/worsened batch；
3. 只有当这些 batch-level 前置信号能区分 Phase 10H 的 improved/worsened rows，才进入 opt-in selector A/B。

