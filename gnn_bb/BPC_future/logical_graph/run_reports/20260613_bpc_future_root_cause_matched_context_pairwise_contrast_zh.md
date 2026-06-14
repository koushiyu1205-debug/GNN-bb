# BPC_future 根因审计补充：matched-context pairwise contrast

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

上一轮 matched-context audit 已经说明：同 `instance + profile` 内样本仍然稀疏，且 top feature 方向混杂。本轮进一步做成对比较：

> 在同一 `instance + profile` 内，逐对比较 improved batch 与 worsened batch，检查 addition-before feature 是否能稳定把 improved 排在 worsened 前面。

这比 aggregate AUC 更接近 selector 真正要解决的问题。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_matched_context_pairwise_contrast.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_matched_context_pairwise_contrast.py \
--output-dir BPC_future/results/root_cause_matched_context_pairwise_contrast_20260613
```

输出：

```text
BPC_future/results/root_cause_matched_context_pairwise_contrast_20260613/summary.json
```

## 样本

20-task strict stage rows：

- rows：`288`
- improved：`136`
- worsened：`152`

strict matched key：

```text
instance + profile
```

matched context：

```text
mixed_group_count = 8
mixed_rows = 94
pair_count = 244
```

## Pairwise Gate

本轮只定义一个保守 production 前置门槛，用于判断某个 addition-before feature 是否值得进入下一步 opt-in selector：

```text
best_orientation_auc >= 0.75
non_tie_share >= 0.20
group_consistency >= 0.75
```

其中：

- `best_orientation_auc`：允许 feature 正向或反向排序，取更好方向；
- `non_tie_share`：避免大量 tie 造成虚假稳定；
- `group_consistency`：dominant direction 在 matched groups 中必须一致。

结果：

```text
passing_strict_pairwise_gate = []
```

没有任何 pre-batch feature 通过。

## Top Feature

最好的 feature 是：

```text
feature = returned_union_size
best_orientation_auc = 0.5450819672131147
dominant_direction = positive
non_tie_share = 0.13114754098360656
group_consistency = 0.5
group_direction_counts = {flat: 4, positive: 4}
```

解释：

- 成对排序只比随机略好；
- 非 tie 的 pair 只有约 `13.1%`；
- 8 个 mixed groups 中只有 4 个是 positive，另外 4 个是 flat；
- 不满足 production selector 的稳定性要求。

## 其他靠前特征

```text
returned_low_time_arc_frac:
  best_orientation_auc = 0.5368852459016393
  dominant_direction = negative
  non_tie_share = 0.45081967213114754
  group_consistency = 0.5
  group_direction_counts = {flat: 2, negative: 4, positive: 2}

returned_low_risk_arc_frac:
  best_orientation_auc = 0.5327868852459017
  dominant_direction = positive
  non_tie_share = 0.45081967213114754
  group_consistency = 0.5
  group_direction_counts = {flat: 2, negative: 2, positive: 4}

returned_arc_count:
  best_orientation_auc = 0.5204918032786885
  dominant_direction = positive
  non_tie_share = 0.10655737704918032
  group_consistency = 0.375
```

这些都远低于可上线 selector 所需的稳定性。

## 对根因判断的影响

这轮把结论再收紧一层：

> 即使在同一 `instance + profile` 内做 improved-vs-worsened pairwise contrast，addition-before pre-batch features 仍然没有稳定排序信号。

因此问题不是简单的：

- 全局 threshold 没调好；
- context 分层还不够；
- `returned_union_size` / low-risk arc ratio 这类单特征可以直接做 gate；
- 只要用 pairwise ranking 就能得到 selector。

更准确的判断是：

> 当前可观测日志中的 addition-before features 不足以决定哪个 returned batch 会改善后续 RMP/dual/incumbent trajectory。下一步必须做同一 pricing/RMP context 下的 counterfactual / replay，对候选 batch 子集、顺序、signature/start-time composition 做因果级对照。

## 当前不能得出的结论

不能说：

- `returned_union_size` 可以作为 production gate；
- matched context 已经能稳定分开 improved / worsened；
- pairwise ranking 模型可以直接上线；
- 当前观测日志足够训练可靠 selector。

只能说：

- matched-context pairwise 也没有稳定 pre-batch selector；
- 这支持“需要 counterfactual/replay 证据”的根因判断；
- 目标仍未完成，因为还没有被证明的 exact-safe 优化方案。
