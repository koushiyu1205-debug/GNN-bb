# GAT Worker ROI v34 无增量训练变体 A/B 报告

日期：2026-06-15

## 目标

不继续采样，不改变标签语义，只使用同一份 v34 `paired_worker_ab_trajectory_roi` 数据集训练若干无增量数据变体，并固定同一套 5/10 no-regression + selected 20 worker A/B 协议比较。

本轮新增训练能力：

- weighted BCE / hard-positive / hard-negative 权重；
- focal loss；
- family-level pairwise ranking loss。

边界不变：

- GAT 只做 trajectory ROI priority scheduler；
- kNN/OOD 仍是 safety shell；
- 不产生 certificate；
- 不产生 official lower bound；
- 不通过的 true-RC negative 只能进 DELAY_QUEUE，不能永久丢弃。

## 代码改动

更新 `BPC_future/scripts/train_gat_worker_roi.py`：

- 新增 `--loss-mode bce|focal|pairwise|focal_pairwise`；
- 新增 `--focal-gamma`；
- 新增 hard-positive / hard-negative score threshold 与 loss multiplier；
- 新增 `--pairwise-loss-multiplier` 与 `--pairwise-group-key instance|family|all`；
- checkpoint 与 summary 记录 loss 配置。

说明：当前 v34 graph dataset 是一行一个候选，因此 pairwise 无法严格做到“同一 context 内多候选排序”。本轮使用 `family` 作为近似分组，只作为诊断实验。

## 训练变体

使用同一数据集：

```text
BPC_future/data/gat_worker_roi/v34_after_v33_sampling_20260615
```

样本不变：

```text
training_row_count = 197
positive_trajectory_roi_count = 61
negative_trajectory_roi_count = 137
duplicate_candidate_count = 0
```

训练三组：

| 变体 | loss | 目的 |
|---|---|---|
| `v34_weighted_hard_20260615` | BCE + hard weights | 提高 hard positive / hard negative 权重 |
| `v34_focal_hard_20260615` | focal + hard weights | 提高难例关注，降低 easy negative 主导 |
| `v34_focal_pairwise_family_20260615` | focal + family pairwise | 在同 family 内学习正 ROI 排序 |

## kNN/OOD 离线结果

与原 v34 对比：

| 模型 | shell | HP数 | precision | recall | false HP rate | ready |
|---|---|---:|---:|---:|---:|---|
| 原 v34 | strict | 5 | 0.800 | 0.235 | 0.028 | false |
| weighted_hard | strict | 5 | 0.400 | 0.118 | 0.083 | false |
| focal_hard | strict | 3 | 1.000 | 0.176 | 0.000 | false |
| pairwise_family | strict | 1 | 1.000 | 0.059 | 0.000 | false |
| focal_hard | neighbor frac 0.5 | 13 | 0.385 | 0.294 | 0.222 | true |
| pairwise_family | neighbor frac 0.5 | 11 | 0.455 | 0.294 | 0.167 | true |

解释：

- weighted_hard 变差，不进入 20 A/B；
- focal_hard / pairwise_family 在 relaxed shell 下召回略升，但整体 precision 明显低于原 strict；
- 两个 relaxed 变体只适合作为 top-k 候选实验，不适合放开全部 HIGH_PRIORITY。

## 20规模 Solver A/B

固定 runbook 协议：

- 5-task sector-wave 双实例 no-regression；
- 10-task sector-wave 双实例 no-regression；
- selected 20 top-5 HIGH_PRIORITY baseline vs worker paired A/B；
- max workers = 4；
- task20 time limit = 200s；
- worker 仍为 explicit opt-in。

汇总：

| 模型 | 20 top-k | solver正ROI | solver负ROI | primal改善合计 | wall-time delta合计 | 5/10 |
|---|---:|---:|---:|---:|---:|---|
| 原 v34 strict | 5 | 4 | 1 | +5.6874 | -39.3852s | OPTIMAL |
| focal_hard frac0.5 | 5 | 5 | 0 | +5.6874 | -46.1079s | OPTIMAL |
| pairwise_family frac0.5 | 5 | 5 | 0 | +4.0520 | -19.3842s | OPTIMAL |

所有 run 均无 certificate / official-bound 副作用。

### focal_hard frac0.5

top-5 全部是正 ROI：

- 2 个 `positive_primal_roi`；
- 3 个 `positive_retry_roi`。

它相对原 v34 的主要改善：

- 去掉了原 v34 top-5 里的一个 false HIGH_PRIORITY；
- 新增的 retry ROI 候选没有改善 primal，但也没有明显拖慢；
- 总 wall-time delta 从 `-39.39s` 改为 `-46.11s`。

但要注意：

- source OOD validation precision 只有 `0.385`；
- HP 总数是 13，不是所有 HP 都安全；
- 这说明“只取 top-k”有效，不能直接放开全部 HIGH_PRIORITY。

### pairwise_family frac0.5

top-5 也是 5/5 正 ROI，但效果弱于 focal_hard：

- primal 改善合计 `+4.0520`；
- wall-time delta 合计 `-19.38s`；
- 新增 Apollo greedy-anchor 候选有 primal 改善，但 wall time 变慢约 11s；
- 说明 pairwise 排序当前未稳定优于 focal_hard。

## 判断

这次无增量训练变体有正向结果，但不是生产化结论。

可以确认：

1. 不增加训练集数量，确实能通过 loss/权重改变 top-k 候选质量；
2. `focal_hard + relaxed shell + top-5` 当前比原 strict v34 更好；
3. 但召回提升很小：`0.235 -> 0.294`；
4. precision/recall tradeoff 仍然明显；
5. 所有 20 规模仍是 `TIME_LIMIT`，未达到 exact optimal。

所以当前原因不是“训练完全不够”，也不是“模型完全没用”。

更准确地说：

```text
GAT embedding 已有 trajectory ROI 信号；
focal/hard mining 能改善 top-k；
但当前表示和 safety shell 仍不足以稳定放大到生产级召回。
```

## 下一步建议

短期：

1. 保留 `focal_hard frac0.5 top-k` 作为当前最优非生产候选策略；
2. 不默认启用；
3. 不扩大所有 HIGH_PRIORITY，只允许 top-k；
4. 增加一个 `top_k_high_priority` 生产前 guard；
5. 再做 hard-repeat 复测，确认 `5/5` 不是 validation split 偶然。

中期：

1. 不急着继续采样；
2. 先改 GAT 表示：加入 active support similarity、dual movement、support churn、retry-history 特征；
3. 构造真正同 context 多候选 pairwise dataset，否则 pairwise loss 只能做 family 近似；
4. kNN/OOD shell 改成 family/scale 分层阈值，而不是全局阈值。

