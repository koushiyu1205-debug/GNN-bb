# BPC_future 根因审计补充：batch selector audit

日期：2026-06-13

## 目标

上一轮 selector feature audit 证明：

- 单个 candidate 的 rank / rough RC 不能解释后续 usefulness；
- 同一 candidate 在不同 batch context 中作用会变化；
- 根因更像 early returned batch composition 的非线性 trajectory effect。

本轮继续只读检查：

**batch-level 前置特征是否已经足以区分 Phase 10H 的 improved / worsened rows？**

本轮不改 solver，不跑新 benchmark，不做 production selector。

## 输入

只读输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/*.jsonl`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/summary.csv`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/logs/*.jsonl`

对每个 run：

- 用同 instance / repeat 的 baseline primal 分类 `improved / worsened`；
- 只看前三个 `journey_column_addition` batch；
- 从 `changed_task_set_samples` 计算 batch 特征；
- 用后续 `pool_active_top_task_set_value_samples` 计算 conservative future-active hit。

注意：

`pool_active_top_task_set_value_samples` 是 capped sample，因此 future hit 是保守信号。

## 特征定义

对前三个 addition batch 合并后的 task-set samples 计算：

- `first3_added`：前三轮加入的 JourneyColumn 数；
- `first3_changed_sets`：前三轮 changed task-set sample 数；
- `first3_future_hits`：这些 sample 后续出现在 active top samples 的个数；
- `future_hit_ratio = future_hits / unique_changed_task_sets`；
- `union_size`：batch task-set 并集任务数；
- `avg_size`：平均 task-set size；
- `pair_jacc`：batch 内 pairwise Jaccard 平均；
- `pair_overlap`：batch 内 pairwise overlap 平均；
- `max_task_freq`：同一个 task 在 batch 中出现的最大次数。

## 汇总结果

### Phase 10H

| outcome | rows | avg primal delta | avg first3 added | avg future hits | avg future-hit ratio | avg union | avg pair jacc |
|---|---:|---:|---:|---:|---:|---:|---:|
| improved | 10 | -141.927485 | 28.7 | 6.2 | 0.278 | 15.0 | 0.173 |
| worsened | 8 | +131.245952 | 23.5 | 4.375 | 0.203 | 13.0 | 0.197 |

### RC-C / return12 ablation

| outcome | rows | avg primal delta | avg first3 added | avg future hits | avg future-hit ratio | avg union | avg pair jacc |
|---|---:|---:|---:|---:|---:|---:|---:|
| improved | 6 | -161.108463 | 36.0 | 7.333 | 0.306 | 17.5 | 0.139 |

## 正向信号

batch-level 特征确实比单列 rank / rough RC 更接近机制：

1. improved rows 的 average future-hit ratio 更高：
   - Phase 10H improved `0.278`
   - Phase 10H worsened `0.203`
   - RC-C / return12 improved `0.306`
2. improved rows 的 task union 更大：
   - Phase 10H improved `15.0`
   - Phase 10H worsened `13.0`
   - RC-C / return12 improved `17.5`
3. improved rows 的 pairwise Jaccard 更低：
   - Phase 10H improved `0.173`
   - Phase 10H worsened `0.197`
   - RC-C / return12 improved `0.139`

这说明“更宽、更分散、后续更多进入 active top sample 的 batch”是合理候选方向。

## 关键反例

这些 batch-level 特征仍不足以直接成为 selector。

### 反例 1：future-hit ratio 高也能 worsened

`mt20_greedy_tranq_01` return8 三次 worsened：

```text
first3_added = 24
first3_future_hits = 8
future_hit_ratio = 0.348
union_size = 15
pair_jacc = 0.192
primal delta = +67.580916
```

这个 future-hit ratio 高于很多 improved rows。例如：

- `tranq20_01` return12 improved 的 aggregate future-hit ratio 为 `0.167`；
- `mt20_greedy_apollo_01` return8 improved row 的 aggregate future-hit ratio 为 `0.250`。

因此 future-active-hit 不能作为充分 selector。

### 反例 2：同一 instance 中 return8/return12 改变很小，但 outcome 反转

`mt20_greedy_tranq_01`：

| profile | outcome | first3 added | future-hit ratio | union | pair jacc |
|---|---|---:|---:|---:|---:|
| return8 | worsened | 24 | 0.348 | 15 | 0.192 |
| return12 | improved | 27-28 | 0.350-0.368 | 14 | 0.155-0.169 |

return12 的 pairwise Jaccard 更低，可能是正向信号；但 future-hit ratio 和 union 并不能单独解释。

### 反例 3：Apollo20 return12 低 overlap 仍 worsened

`mt20_greedy_apollo_01` return12 三次 worsened：

```text
first3_added = 24 / 24 / 28
future_hit_ratio = 0.062 / 0.062 / 0.100
union_size = 11 / 11 / 14
pair_jacc = 0.225 / 0.225 / 0.169
```

第三次 pair_jacc 已降到 `0.169`，接近 improved rows，但仍 worsened。

说明 overlap/diversity 也不是充分规则。

## 当前判断

batch-level 特征是目前最有希望的方向，但仍只是 calibration signal：

- 它比 single candidate rank / rough RC 更接近 trajectory mechanism；
- 它能解释一部分 improved vs worsened 的平均差异；
- 但它还不能稳定区分所有 hard rows；
- 尤其不能处理 `mt20_greedy_tranq_01` return8 这种 high future-hit but worsened 的反例。

所以当前不能做 production selector，也不能宣称目标完成。

## 根因进一步表述

当前根因不是：

- Pulse 不够强；
- profile-DP cap 太小；
- return count 太小；
- best-RC 排序错；
- future-active-hit 不够多；
- batch diversity 不够高。

更准确是：

> 20-task hard tail 的早期列加入存在 batch-level trajectory sensitivity。一个 batch 是否有利，取决于具体 JourneyColumn task-set / timing / signature composition 与当前 RMP active basis、后续 dual movement、后续 pricing residual tail 的相互作用。当前已有的前置特征只能提供弱相关，尚不能构成 exact-safe、可泛化、能保护 5/10 的 selector。

## 对下一步的约束

下一步仍不能：

- 默认 return12；
- 默认扩大 returned batch；
- 默认开启 Pulse worker；
- 根据 rough RC / rank 选列；
- 根据 future-active-hit 这种后验信号在线选列；
- 打开 official certificate gate。

如果继续，应只做 calibration-only 的 batch selector modeling：

1. 使用已存在日志构造 per-batch dataset；
2. 标签只用后验 outcome / next-RMP objective delta / incumbent update；
3. 特征只能使用 addition 前可见字段；
4. 先做解释能力评估，不改求解器；
5. 只有当模型/规则能解释 Phase 10H 的反例，再做 opt-in A/B。

## 目标状态

目标仍未完成。

当前已经有证据说明根因所在层级，但还没有证明一个优化方向能：

1. 保证 exactness；
2. 保证 5/10 不退化；
3. 在 selected 20-task hard set 上稳定大幅加速。

