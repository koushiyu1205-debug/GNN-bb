# BPC_future 根因审计补充：selector failure anatomy

日期：2026-06-13

## 目标

本轮只做只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

目标是解释：为什么已经有 returned negative candidates、也已经有 candidate + batch-context features，但仍然不能形成可上线的 addition-before selector。

## 输入

输入文件：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/candidate_rows.csv
```

分析脚本：

```text
BPC_future/scripts/analyze_selector_failure_anatomy.py
```

复跑命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_selector_failure_anatomy.py \
--output-dir BPC_future/results/root_cause_selector_failure_anatomy_20260613
```

输出：

```text
BPC_future/results/root_cause_selector_failure_anatomy_20260613/summary.json
```

## 样本范围

只看 20-task strict candidates：

- rows：`848`
- improved：`553`
- worsened：`295`

这些 rows 来自已有 result-set 的 returned JourneyColumn candidates，只用于离线解释，不作为生产 selector。

## 关键发现 1：正例高度集中在一个 result-set

`sharded_pulse_phase10h_early_new_task_set_quota_smoke_20260613` 包含：

- rows：`648`
- improved：`481`
- worsened：`167`
- positive share：`0.8698010849909584`

也就是说，全部 improved candidate 中约 `87%` 来自同一个 result-set。

这解释了为什么 leave-one-dataset 结果很差：

- 在 phase10h 上训练/验证容易看到正例；
- 一旦 held-out 到其他 result-set，很多规则几乎不召回正例；
- 这个数据分布不能支撑 production selector。

## 关键发现 2：全局最强特征不是稳健 selector

全局 effect 最大的几个 addition-before 特征：

| feature | auc_positive_higher | standardized_effect | dataset mixed sign | instance mixed sign |
|---|---:|---:|---:|---:|
| `batch_pair_overlap` | `0.6995310632298403` | `0.7938734929385808` | false | true |
| `batch_pair_jaccard` | `0.6963925583106017` | `0.7899393726930406` | false | true |
| `batch_returned_count` | `0.6541759892113893` | `0.7007170663686664` | false | true |
| `candidate_low_risk_arc_frac` | `0.6747601679590524` | `0.6164674488889889` | true | false |
| `candidate_low_time_arc_frac` | `0.34172924265179144` | `-0.5834846473911613` | true | false |

含义：

- batch overlap / jaccard / returned count 在全局有信号；
- 但这些信号在 instance 维度方向翻转；
- low-risk / low-time arc fraction 在 dataset 维度方向翻转；
- 因此这些特征可以解释部分历史结果，但不能直接作为 production gate。

## 关键发现 3：没有 robust single-feature candidate

脚本的保守 robust 条件：

- aggregate AUC 距离 `0.5` 至少 `0.15`；
- dataset 方向不翻转；
- instance 方向不翻转；
- dataset / instance 组内 AUC margin 均保持同方向。

结果：

```text
robust_single_feature_candidates = []
```

这说明当前不是“找一个阈值就能解决”的问题。

## 关键发现 4：方向不稳定是系统性的

dataset 方向翻转的 addition-before features：

```text
candidate_sequence_len
candidate_start_time
candidate_arc_count
candidate_low_time_arc_frac
candidate_low_risk_arc_frac
candidate_low_energy_arc_frac
candidate_active_overlap
candidate_active_jaccard
batch_active_avg_overlap
batch_active_bridge_frac
```

instance 方向翻转的 addition-before features：

```text
candidate_position_frac
candidate_sequence_len
candidate_start_time
candidate_arc_count
candidate_active_overlap
candidate_active_jaccard
batch_returned_count
batch_pair_overlap
batch_pair_jaccard
batch_active_avg_overlap
```

这进一步说明问题不是某个单独 feature 写错，而是 returned-batch trajectory effect 本身存在强上下文依赖。

## 对根因判断的影响

本轮把根因进一步收紧为：

> 20-task 的瓶颈不是缺少 negative columns，也不是简单缺少更多 returned columns，而是缺少能跨 result-set / instance 泛化的 addition-before returned-batch trajectory selector。

更具体地说：

- 当前 features 能解释局部结果；
- 但 improved labels 高度集中在一个 result-set；
- 全局强特征在 instance 或 dataset 间方向翻转；
- 简单阈值、二特征规则、nearest centroid、linear mean-diff、shallow tree 都未形成可上线 gate；
- 因此继续扩大 Pulse worker、profile-DP cap、return count 或 pricing time，仍然只是生成更多候选，不保证选择正确 batch。

## 当前不能得出的结论

不能说：

- Pulse 已经没价值；
- profile-DP 没价值；
- negative columns 没价值；
- batch overlap 完全没用。

只能说：

- 这些机制能提供候选或局部信号；
- 但目前没有证据证明它们能形成 exact-safe、5/10 no-regression、20-task 大幅加速的生产策略。

## 下一步边界

如果继续寻找优化方向，应优先做更强的 addition-before selector 证据，而不是继续加大搜索预算。

候选方向必须先通过：

1. leave-one-dataset；
2. leave-one-instance；
3. 5/10 no-op / no-regression；
4. no certificate effect；
5. 20-task hard set repeat validation。

在通过这些 gate 前，不应默认启用 worker / probe / profile-DP cap / return count 扩张。
