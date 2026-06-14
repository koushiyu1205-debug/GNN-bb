# BPC_future 根因审计补充：candidate label granularity

日期：2026-06-13

## 目标

本轮继续只做只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

目标是检查：

> `candidate_rows.csv` 里的 improved / worsened 是否是单个 JourneyColumn 的因果标签，还是 batch / run 级标签复制到每个 returned candidate 上。

这个问题很重要。若标签是 batch / run 级展开，就不能把 candidate-level 模型误解为“单列因果 selector”。

## 输入与脚本

输入目录：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613
```

脚本：

```text
BPC_future/scripts/analyze_candidate_label_granularity.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_candidate_label_granularity.py \
--output-dir BPC_future/results/root_cause_candidate_label_granularity_20260613
```

输出：

```text
BPC_future/results/root_cause_candidate_label_granularity_20260613/summary.json
```

## Batch key

用于对齐 stage 与 candidate 的 key：

```text
dataset, instance, profile, repeat_index, cg_iter
```

## 核心结果

20-task strict stage / candidate：

| 指标 | 数值 |
|---|---:|
| stage rows | `288` |
| candidate rows | `848` |
| candidate batches | `288` |
| label-mixed candidate batches | `0` |
| stage/candidate batch key missing | `0 / 0` |

含义：

- 每个 stage batch 对应若干 returned candidates；
- 同一个 batch 内所有 candidate 共享同一个 `run_improvement_class`；
- 没有 batch 内 mixed label；
- candidate rows 不是单列因果标签，而是 batch/run label 展开。

## Label balance 被 candidate expansion 改变

Batch / stage 级标签：

```text
improved = 136
worsened = 152
positive_rate = 0.4722222222222222
```

Candidate row 级标签：

```text
improved = 553
worsened = 295
positive_rate = 0.652122641509434
```

正例比例被 candidate 展开提高了：

```text
positive_rate_shift_candidate_minus_batch = 0.1799004192872118
```

## Improved batch 返回更多 candidates

按 batch label 统计 candidate expansion：

| label | batches | candidate rows | avg candidates / batch | max |
|---|---:|---:|---:|---:|
| improved | `136` | `553` | `4.0661764705882355` | `8` |
| worsened | `152` | `295` | `1.9407894736842106` | `8` |

扩张比：

```text
improved_vs_worsened_avg_candidate_expansion_ratio = 2.0951146560319045
```

这解释了为什么一些 candidate-level selector 会偏好 `batch_returned_count`、`batch_pair_overlap`、`batch_pair_jaccard`：

- 它们确实有相关性；
- 但部分相关性来自 improved batch 返回更多 candidates 后的标签复制；
- 这不是单个 JourneyColumn 的因果贡献证明。

## 字段粒度

所有 288 个 candidate batch 中，以下 stage-level / batch-level 字段在 batch 内恒定：

```text
run_improvement_class
run_status
run_primal
run_wall_time
batch_returned_count
batch_pair_overlap
batch_pair_jaccard
batch_active_avg_overlap
batch_active_redundant_frac
batch_active_bridge_frac
incumbent_within2
zero_fractional_within2
next_negative_count
next_incomplete_count
```

一些 candidate-level 字段确实在 batch 内变化，例如：

```text
candidate_sequence
candidate_task_set
candidate_start_time
candidate_active_overlap
candidate_future_active_within2
candidate_future_active_value
```

因此当前数据适合做：

- batch trajectory root-cause audit；
- returned batch composition analysis；
- candidate-level feature 与 batch outcome 的相关性检查。

但它不适合直接做：

- 单列因果 selector；
- “这个 candidate 必然导致 improvement”的 production gate；
- 只按 candidate-level label 训练的 active worker 策略。

## 对根因判断的影响

本轮把根因边界进一步收紧：

> 当前最可信的缺口不是“找一个 candidate-level 分类器”，而是“构造能在 batch/run 级预测后续 RMP active-basis / incumbent trajectory 的 selector，并最终需要更强的候选级或 batch级因果证据”。

这也解释了为什么前面的模型审计没有通过 strict gate：

- candidate rows 的正例被 returned-count expansion 放大；
- stage-level outcome 被复制到 batch 内所有 candidates；
- 简单 candidate-level 模型会把 batch-size / overlap 相关性误读为单列因果；
- 跨 dataset / instance 时这种相关性方向会翻转。

## 结论

当前数据已经足够支持 root-cause 判断：

- 5/10 是固定开销敏感；
- 20 有负列和候选，但 returned batch 的后续 trajectory 选择不稳；
- candidate-level 简单 selector 不可靠。

但当前数据还不足以直接产出 production selector。

下一步若继续，应补更强的 action-level / batch-level causal evidence，例如：

1. 同一 context 下候选 batch A/B 或 replay；
2. returned batch subset / reorder 的 counterfactual replay；
3. 单列进入 active basis 与 incumbent movement 的更精确因果归因；
4. 仍保持 5/10 no-op 和 no certificate effect。
