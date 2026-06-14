# BPC_future 根因审计补充：batch feature separability

日期：2026-06-13

## 目标

上一轮综合报告把根因收紧为：

> returned JourneyColumn batch 的 candidate/signature/timing composition 会非线性改变 RMP active-basis trajectory，但当前还没有 addition 前可见、可泛化、能保护 5/10 的 selector。

本轮继续做只读离线分析：

**用现有 Phase 10H / RC-C 日志重新计算 early returned batch 特征，检查这些特征能否区分 20-task improved / worsened rows。**

本轮不改 solver、不改 pricing、不改 RMP、不改 Pulse、不跑新 benchmark。

## 数据来源

只读输入：

- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/summary.csv`
- `BPC_future/results/sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613/logs/*.jsonl`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/summary.csv`
- `BPC_future/results/root_cause_rcc_context_replay_return12_ablation_20260613/logs/*.jsonl`

标签：

- 对每个非 baseline row，用同 instance / repeat 的 baseline primal 计算 delta；
- `delta < 0` 标为 improved；
- `delta > 0` 标为 worsened。

主分析集：

- Phase 10H 非 baseline 20-task rows；
- 共 18 行；
- improved 10 行；
- worsened 8 行。

外部参照：

- RC-C / return12 ablation 中 6 个非 baseline 20-task rows；
- 6 行均 improved；
- 只作为 sanity reference，不参与阈值拟合。

## 特征定义

对每个 run 的前三个 `journey_column_addition` 事件，抽取 `changed_task_set_samples`，计算：

- `first3_added`：前三次 addition 的 added journeys 总数；
- `first3_changed_sets`：前三次 addition 的 unique changed task-set 数；
- `union_size`：这些 task-set 的任务并集大小；
- `avg_size`：平均 task-set size；
- `pair_jacc`：unique task-set 两两 Jaccard 平均；
- `pair_overlap`：unique task-set 两两 overlap coefficient 平均，即 `|A cap B| / min(|A|, |B|)`；
- `max_task_freq`：单个 task 在 batch task-sets 中出现的最大次数；
- `active_changed_first3` / `replacement_first3` / `new_task_sets_first3`；
- `first3_future_hits` / `future_hit_ratio`：后续 active top sample 中出现的数量和比例。

注意：

- `future_hit_ratio` 是后验信号，不能在线作为 selector；
- 本轮主要看 returned batch composition 对 outcome 的 separability；
- 这些特征是 outcome 前可见，但不一定都能在“决定 returned cut 之前”完整可见，后续若做 selector 仍需改成 candidate-list 前置特征。

## Aggregate 复核

### Phase 10H

| outcome | rows | avg delta | avg union | avg pair_jacc | avg pair_overlap | avg future_hit_ratio |
|---|---:|---:|---:|---:|---:|---:|
| improved | 10 | -141.927485 | 15.0 | 0.172764 | 0.258754 | 0.277675 |
| worsened | 8 | +131.245952 | 13.0 | 0.191303 | 0.285967 | 0.202831 |

### RC-C / return12 reference

| outcome | rows | avg delta | avg union | avg pair_jacc | avg pair_overlap | avg future_hit_ratio |
|---|---:|---:|---:|---:|---:|---:|
| improved | 6 | -161.108463 | 17.5 | 0.139181 | 0.224537 | 0.305556 |

方向上，improved rows 更像：

- task union 更大；
- pairwise Jaccard 更低；
- pairwise overlap 更低；
- future-hit ratio 更高。

这继续支持上一轮判断：batch-level composition 比单个 candidate rank / rough RC 更接近真实机制。

## 单阈值 separability

只用 Phase 10H 18 行，在 outcome 上直接拟合单特征阈值。

### 最强前置特征

`pair_overlap <= 0.26992753623188404`

结果：

```text
accuracy = 17 / 18 = 0.944444
tp = 10
fp = 1
tn = 7
fn = 0
```

也就是说，这个阈值在当前 18 行上能覆盖所有 improved rows，只误判 1 个 worsened row。

### 其他前置特征

| rule | accuracy | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|
| `pair_overlap <= 0.26811594202898553` | 0.888889 | 9 | 1 | 7 | 1 |
| `pair_jacc <= 0.17500000000000002` | 0.833333 | 8 | 1 | 7 | 2 |
| `union_size >= 16` | 0.777778 | 6 | 0 | 8 | 4 |
| `max_task_freq >= 12` | 0.777778 | 6 | 0 | 8 | 4 |

### 后验 future-hit 特征

`first3_future_hits >= 4`

```text
accuracy = 14 / 18 = 0.777778
tp = 10
fp = 4
tn = 4
fn = 0
```

`future_hit_ratio >= 1/6`

```text
accuracy = 13 / 18 = 0.722222
tp = 10
fp = 5
tn = 3
fn = 0
```

后验 future-hit 反而不如 `pair_overlap`，也不能在线使用。这说明“后续进入 active top sample”不是充分解释。

## 最关键误判

`pair_overlap <= 0.26992753623188404` 唯一误判：

```text
instance = mt20_greedy_apollo_01
profile = experimental_early_new_task_set_quota_3_return12_20_only
repeat = 2
outcome = worsened
delta = +139.913748
first3_added = 28
first3_changed_sets = 20
union_size = 14
avg_size = 2.9
pair_jacc = 0.168772
pair_overlap = 0.247368
max_task_freq = 10
first3_future_hits = 2
future_hit_ratio = 0.100000
```

这个误判非常重要：

- 它满足低 overlap / 低 Jaccard 的“好 batch”形态；
- 但最终仍 worsened；
- 它正是 Apollo20 return12 的关键坏轨迹之一。

因此，即使当前单阈值在同样本上达到 17/18，也不能直接作为 production selector。

## Row-level 对照

| instance | profile | repeat | outcome | delta | union | pair_jacc | pair_overlap | future_hit_ratio |
|---|---|---:|---|---:|---:|---:|---:|---:|
| tranq20_01 | return8 | 0 | improved | -183.982696 | 16 | 0.181 | 0.268 | 0.292 |
| tranq20_01 | return12 | 0 | improved | -175.974351 | 16 | 0.174 | 0.260 | 0.167 |
| tranq20_01 | return8 | 1 | improved | -184.924818 | 16 | 0.175 | 0.258 | 0.333 |
| tranq20_01 | return12 | 1 | improved | -187.176358 | 16 | 0.174 | 0.260 | 0.167 |
| tranq20_01 | return8 | 2 | improved | -187.055474 | 16 | 0.175 | 0.258 | 0.333 |
| tranq20_01 | return12 | 2 | improved | -175.974351 | 16 | 0.174 | 0.260 | 0.167 |
| mt20_greedy_apollo_01 | return8 | 0 | worsened | +213.741813 | 12 | 0.186 | 0.277 | 0.167 |
| mt20_greedy_apollo_01 | return12 | 0 | worsened | +213.741813 | 11 | 0.225 | 0.331 | 0.062 |
| mt20_greedy_apollo_01 | return8 | 1 | worsened | +139.913748 | 11 | 0.193 | 0.281 | 0.188 |
| mt20_greedy_apollo_01 | return12 | 1 | worsened | +139.913748 | 11 | 0.225 | 0.331 | 0.062 |
| mt20_greedy_apollo_01 | return8 | 2 | improved | -151.428979 | 12 | 0.181 | 0.270 | 0.250 |
| mt20_greedy_apollo_01 | return12 | 2 | worsened | +139.913748 | 14 | 0.169 | 0.247 | 0.100 |
| mt20_greedy_tranq_01 | return8 | 0 | worsened | +67.580916 | 15 | 0.178 | 0.274 | 0.348 |
| mt20_greedy_tranq_01 | return12 | 0 | improved | -57.585940 | 14 | 0.155 | 0.238 | 0.368 |
| mt20_greedy_tranq_01 | return8 | 1 | worsened | +67.580916 | 15 | 0.178 | 0.274 | 0.348 |
| mt20_greedy_tranq_01 | return12 | 1 | improved | -57.585940 | 14 | 0.169 | 0.258 | 0.350 |
| mt20_greedy_tranq_01 | return8 | 2 | worsened | +67.580916 | 15 | 0.178 | 0.274 | 0.348 |
| mt20_greedy_tranq_01 | return12 | 2 | improved | -57.585940 | 14 | 0.169 | 0.258 | 0.350 |

## 判断

这轮给出一个比上一轮更强的信号：

> returned batch 的 pairwise overlap 是目前最强的可观测 separability 特征之一。低 overlap / 更分散的 early batch 在 Phase 10H 上高度对应 improved rows。

但它仍然不是可上线规则：

1. 样本只有 18 行，阈值在同一数据上拟合，存在明显过拟合风险；
2. 唯一 false positive 是关键 Apollo20 return12 r2 worsened row，不是无关边角；
3. `pair_overlap` 是 returned batch 后的 composition 特征，若要作为 selector，必须能在 candidate-list 选择阶段预测并控制；
4. 它只解释 Phase 10H 的 returned batch 干预，不证明 5/10 no-regression；
5. 它没有证明能大幅加速 20-task exact optimal solving，只是解释 short-time incumbent trajectory。

## 对根因的更新

当前根因可以进一步写成：

> 20-task hard-tail 的不稳定性主要来自 early returned batch 的 overlap / diversity / signature composition 对 RMP active-basis trajectory 的影响。较低 overlap 的 batch 往往更容易带来好轨迹，但低 overlap 不是充分条件；仍需要 signature/timing/context 特征来排除 Apollo20 return12 r2 这类低 overlap 但 worsened 的反例。

这比“返回更多列”更精确：

- return8 / return12 是否有效，取决于它们形成的 batch overlap 和具体 signature；
- 单纯扩大 returned count 不控制 overlap；
- 单纯按 rough RC 排序不控制 overlap；
- 单纯 future-active-hit 也不能排除高 future-hit worsened。

## 下一步

若继续，应保持 calibration-only：

1. 把 `pair_overlap` / `pair_jacc` 加入 returned-boundary candidate diagnostics；
2. 在 candidate-list 层模拟“低 overlap batch selection”，但先不改 solver；
3. 专门解释 false positive：
   - `mt20_greedy_apollo_01 / return12 / r2` 为什么低 overlap 仍 worsened；
   - 需要看 signature、start-time、arc-option family、relation to active top samples、post-addition dual movement；
4. 只有当低-overlap selector 能排除这个反例，并在 5/10 guard 与 20 hard repeat 上通过，才允许做 opt-in A/B。

## 目标状态

目标仍未完成。

本轮找到了一个很强的 root-cause feature candidate，但没有证明它是 production-safe selector，更没有证明它能在 exactness、5/10 no-regression 的前提下大幅加速 20-task 最优求解。

