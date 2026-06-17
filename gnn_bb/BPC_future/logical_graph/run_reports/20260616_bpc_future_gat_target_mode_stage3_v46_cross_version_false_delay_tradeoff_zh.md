# 2026-06-16 BPC_future GAT Stage 3 v46 Cross-version False-delay Tradeoff 综合报告

## 读取范围

本报告横向复读以下材料，不运行 BPC、pricing、RMP 或 certificate：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1/2/3/4/5 相关报告，尤其 v15 missed high-ROI、v23/v24/v28/v39/v41/v44/v45
- v45 full training、threshold frontier、gate shortfall 新结果

目标模式不变：

```text
Learning-guided discovery, exact-certified closure
```

GAT/CBF/kNN/OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；所有进入 RMP 的列仍必须 true-RC verified；最终 optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 no-negative closure。

## Cross-version 对比

| version | 主变化 | accepted | ROI CI-low | HP precision CI-low | false-delay | frontier / gate 结论 |
|---|---|---:|---:|---:|---:|---|
| v15 | exact-safe hits batch8 A/B ROI 回流 | 13 | 8.029247 | 0.978277 | 0.0 | 安全但样本/coverage 不足，`safe_precision_ci_low=0.771898` |
| v23 | positive candidate boost | 56/59 | 2.703147 / 2.819947 | 0.941651 / 0.934709 | 0.425532 / 0.521277 | high-ROI 覆盖改善，但 false-safe/false-delay 失控 |
| v24 | delay suppression | 17 | 6.259074 | 0.977061 | 0.008475 | false-delay 基本压住，但 coverage / family holdout 不足 |
| v28 | risk-adjusted delay calibrated | 22 | 4.579149 | 0.985473 | 0.008475 | 比 v24 覆盖略好，仍卡在 sample / safe CI / kNN-OOD |
| v39 | neighbor-ROI + b6d808 hard-negative | 46 | 3.321518 | 0.920802 | 0.448980 | ROI 和 coverage 回升，但 `model_ranking_false_delay_blocker` |
| v44 | v39 delay-safe shell shortfall | 46 | 3.321518 | 0.920802 | 0.448980 | delay-safe shell 存在，但最多只接受 2 个 batch |
| v45 smoke | false-delay contrast smoke | 3 | 0.813001 | 0.991441 | 0.0 | false-delay 被压住，但 coverage 太小，CI 不可信 |
| v45 full | false-delay contrast full | 35 | 4.462123 | 0.805696 | 0.448980 | ROI/coverage 回升后 false-delay 复发，0 feasible threshold |

注：v23 的第一组数字来自 selected validation metrics，第二组来自 threshold frontier best candidate；v39/v45 的 gate 判断以 frontier / shortfall 为准。

## 旧版本给出的新理解

### 1. v15 missed high-ROI 不是阈值差一点

v15 missed high-ROI diagnosis 的关键字段：

```text
accepted_high_roi_opportunities = 12
missed_high_roi_opportunities = 16
near_threshold_miss_count = 0
non_near_threshold_miss_count = 16
missed_candidate_score_margin_mean = -0.382917
missed_nearest_negative_closer_count = 10
missed_without_same_context_contrast_count = 7
primary = candidate_head_score_gap_plus_embedding_structural_gap
```

这说明 v15 的主要问题不是把 threshold 从 0.90 降到 0.85 就能修好，而是 candidate head / embedding 在 random-wave、sector-wave high-ROI 上结构性分不开。后续 v23 的 positive boost 确实把 high-ROI recall 拉起来，但代价是 false-delay 暴涨。

### 2. v23/v24/v28 证明了安全和覆盖之间存在 Pareto 张力

v23 用 positive candidate boost 让覆盖上去：

```text
accepted_batch_count = 56
accepted_batch_roi_ci_low = 2.703147
false_high_priority_on_delay = 0.425532
```

v24/v28 用 delay suppression / risk-adjusted scoring 把 false-delay 压低：

```text
v24 false_high_priority_on_delay = 0.008475, accepted_batch_count = 17
v28 false_high_priority_on_delay = 0.008475, accepted_batch_count = 22
```

但它们没有进入 Stage 4 candidate，因为 accepted 样本数、safe precision CI、family/context holdout、kNN/OOD 仍不过硬。也就是说，单纯调 loss 权重会在两端摇摆：

- boost high-ROI candidate -> 覆盖变好，delay false positive 爆；
- suppress delay risk -> false-delay 变好，覆盖和 CI 变差。

### 3. v39/v41 把 blocker 定位到 context-concentrated false positive

v39 training / v42 frontier：

```text
accepted_batch_count = 46
accepted_batch_roi_ci_low = 3.321518
safe_precision_ci_low = 0.922924
high_priority_precision_ci_low = 0.920802
false_high_priority_on_delay = 0.448980
false_high_priority_on_delay_count = 44
primary_blocker = model_ranking_false_delay_blocker
```

v41 false-positive catalog 进一步说明：

```text
family_counts = {'sector-wave': 44}
family_task_counts = {'sector-wave|20': 44}
context_false_positive_count = 5
candidate_threshold_zero = true
candidate_threshold_zero_effect = candidate_head_threshold_disabled_delay_gate_is_only_filter
```

所以 v39 的问题不是全局噪声，而是少数 `sector-wave|20` context 中，candidate head 没能先过滤，delay gate 独自承担过滤，最终把 true-RC negative 但 trajectory-delay 的候选列也打成 high-priority。

### 4. v44/v45 证明 false-delay safe shell 太窄

v44 shortfall：

```text
delay_safe_threshold_count = 1309
delay_safe_with_accepted_batch_count = 335
delay_safe_accepted_batch_count_max = 2
recommended_primary = delay_safe_shell_exists_but_coverage_too_small
```

v45 full shortfall：

```text
delay_safe_threshold_count = 1071
delay_safe_with_accepted_batch_count = 186
delay_safe_accepted_batch_count_max = 1
recommended_primary = delay_safe_shell_exists_but_coverage_too_small
```

这把问题从“没有安全阈值”细化为“安全阈值壳存在，但覆盖极窄”。一旦覆盖提升到 35-46 个 accepted batch，false-delay 重新回到 0.448980。

### 5. v45 false-delay contrast 没有解决结构性分不开

v45 smoke 的确把 false-delay 压到 0：

```text
accepted_batch_count = 3
false_high_priority_on_delay = 0.0
safe_precision_ci_low = 0.438494
```

但 full training 重新选择高覆盖/高 ROI 区域后：

```text
accepted_batch_count = 35
accepted_batch_roi_ci_low = 4.462123
high_priority_precision_ci_low = 0.805696
false_high_priority_on_delay = 0.448980
false_high_priority_on_delay_count = 44
feasible_threshold_count = 0
primary_blocker = model_ranking_false_delay_blocker
```

因此新增 pairwise false-delay contrast 只改善了极窄低覆盖壳，没有让模型在高覆盖区域内学会区分 high-ROI safe candidate 与 low-ROI / tail-delay hard negative。

## 当前问题判断

当前问题已经不应描述为“阈值没调好”或“训练还不够久”。更准确的判断是：

1. candidate head 目前缺少足够的 context-local ranking 能力，尤其是 `sector-wave|20`；
2. delay-risk head 可以产生安全壳，但安全壳不覆盖足够 high-ROI opportunity；
3. risk-adjusted product 把 candidate score 和 delay score 乘在一起后，仍无法表达“true-RC negative 但加入后拖累 RMP trajectory”的动作后果；
4. Stage 4 v40 已经证明即时 RMP objective improvement 会误导 label，训练目标必须继续绑定 A/B trajectory ROI、tail retry、pricing workload 和 RMP iteration 结果；
5. 现有 v45 loss 属于局部修补，还没有改变模型结构或数据覆盖上的分不开问题。

## 下一步建议

下一步不建议继续做普通 threshold sweep，也不建议放宽 precision / ROI / false-safe gate。更有价值的是直接验证下面几个假设。

1. 做 epoch-level constrained selector 审计。
   当前 v45 full 的训练过程早期有低 false-delay、后期有高 coverage/high ROI。需要把每个 epoch 的 frontier / shortfall 串起来，看是否存在一个满足 coverage 下限且 false-delay 不爆的 epoch。如果不存在，就能排除 checkpoint selection 问题。

2. 对 `sector-wave|20` 做 context-local hard-negative 数据补强。
   v41 已经证明 44 个 false-delay 全集中在 `sector-wave|20`。下一批 worker 不应泛泛采样，而应在这 5 个 false-positive context 内构造 same-context positive/negative/delay-hard-negative contrast，要求同一 context 内 high-ROI safe candidate 排到 delay negative 前面。

3. 把 candidate threshold 从“可为 0 的全局 fallback”改成可审计的 context/family-local candidate-head gate。
   v41 的 `candidate_threshold_zero_effect` 说明 candidate head 失效后，delay gate 被迫单独过滤。下一版要先证明 candidate head 本身在 context-local ranking 上有用，再叠 delay-risk。

4. 训练目标继续硬化为 constrained objective。
   checkpoint 选择不能只按 validation loss，也不能只按 ROI point。候选 checkpoint 必须先过：
   `HP precision CI`、`safe precision CI`、`false_high_priority_on_delay`、`false_safe_union`、coverage、family/context holdout、kNN/OOD；不过 gate 的 checkpoint 只能 diagnostic。

5. 保持 exact boundary。
   即使 GAT 能把前面的 column generation 变聪明，最终 proof 仍必须由 exact pricing 重跑确认：当前 branch/cut/dual 下，完整配置宇宙没有任何负 reduced-cost journey。GAT 不能产生 official lower bound，不能永久丢弃 true-RC negative，也不能把 delay queue 当 reject。

## 结论

跨版本对比后的新理解是：Stage 3 当前卡在“高 ROI 覆盖”和“false-delay 抑制”的结构性 tradeoff，而不是单点阈值或单个 loss multiplier。v23 证明 coverage 可上去，v24/v28 证明 false-delay 可压住，v39/v45 证明两者一合并就复发，v41/v44/v45 shortfall 说明复发集中且安全壳太窄。

下一步应从 `sector-wave|20` context-local hard-negative contrast、epoch-level constrained selector、candidate-head gate 可用性三件事入手；如果这些仍不能形成足够覆盖的 delay-safe shell，就需要回到模型结构，补 candidate order/timing/path-option/basis trajectory 表示，而不是继续调阈值。

## Exactness Boundary

- `diagnostic_only=true`
- `runs_bpc_or_pricing=false`
- `selector_is_pricing_oracle=false`
- `selector_can_certificate=false`
- `gate_can_permanently_discard_negative_columns=false`
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing exhaustive no-negative result
