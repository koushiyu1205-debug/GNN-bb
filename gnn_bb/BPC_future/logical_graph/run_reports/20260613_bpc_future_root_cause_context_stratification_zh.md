# BPC_future 根因审计补充：context stratification

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

目标是解释为什么 aggregate batch gate 会失效：

> 是因为特征完全没信号，还是因为 dataset / instance / profile 上下文基准率差异太大，导致 aggregate 规则被混杂？

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_context_stratification.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_context_stratification.py \
--output-dir BPC_future/results/root_cause_context_stratification_20260613
```

输出：

```text
BPC_future/results/root_cause_context_stratification_20260613/summary.json
```

## 样本

20-task strict stage rows：

- rows：`288`
- improved：`136`
- worsened：`152`

## 基准率差异

不同上下文的 improved rate range：

| group key | improved-rate range |
|---|---:|
| dataset | `0.7272727272727273` |
| instance | `0.32667047401484867` |
| profile | `0.8372093023255814` |

这说明 improved / worsened 并不是从同一个平稳分布里抽样。不同 result-set / instance / profile 的 base rate 差异已经足以污染 aggregate threshold。

## Feature direction 翻转

出现方向翻转的 top pre-batch features：

```text
dataset:
  returned_union_size
  returned_arc_count

instance:
  returned_union_size
  returned_arc_count
  returned_count
  materialized_count
  returned_pair_overlap
  returned_pair_jaccard
  selected_count

profile:
  returned_union_size
  returned_arc_count
  returned_count
  materialized_count
  returned_pair_overlap
  returned_pair_jaccard
  selected_count
```

其中最重要的是：

```text
returned_union_size mixed by profile = true
```

也就是说，前面 aggregate 上最强的 trigger/no-op 特征，在 profile 内部方向并不稳定。

## 对根因判断的影响

这解释了为什么：

- aggregate 上 `returned_union_size >= 11` 看起来是 high precision trigger；
- aggregate 上 `returned_union_size <= 2` 看起来是 high precision no-op；
- 但 leave-one-dataset / leave-one-instance 后全部失效。

根本原因不是阈值没调好，而是：

> returned-batch outcome 强依赖 dataset / instance / profile context，且关键 pre-batch features 的方向会跨上下文翻转。

因此任何不显式建模 context 的简单 selector 都会被混杂。

## 当前不能得出的结论

不能说：

- `returned_union_size` 没有信息；
- batch coverage 完全无用；
- profile 调整完全无效。

只能说：

- 这些信号高度依赖上下文；
- aggregate 规则不能直接上线；
- 下一步若继续找优化方向，需要 context-aware 或 counterfactual evidence，而不是单一全局阈值。

## 结论

当前 20-task hard-tail 的根因进一步明确为：

> BPC_future 缺少能处理 dataset / instance / profile context heterogeneity 的 addition-before returned-batch trajectory selector。

这也是为什么同一个方向在某些 20-task profile 上偶发改善，在另一些 profile / instance 上退化或无效。
