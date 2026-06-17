# 2026-06-16 BPC_future GAT Target Mode Stage 3 v29 Risk-penalty Matrix Synthesis

## 结论

本轮按计划先复读 `gat_bpc_future_target_mode_optimization_plan_zh`、Stage 1/2
报告、Stage 3 v28 synthesis、Stage 4 v23 A/B / certificate audit，以及 Stage 5
20/30/50/100 目标。随后只做 Stage 3 offline risk-penalty matrix，不改 solver、
pricing、RMP、worker 或 certificate path。

v29 结论：

```text
v29_stage3_matrix_completed = partial_targeted
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
```

v28 的问题是 missed high-ROI 有相当一部分被 risk-adjusted delay penalty 压到阈值下；
本轮检验“单值 penalty 放松”能否恢复这些 near-miss。结果证明：可以恢复 high-ROI
capture，但 false-safe / false high-priority on delay 会快速失控。因此下一步不应
继续盲扫 scalar penalty，而应改成 context/family-aware 或 two-stage safety-aware
admission calibration。

## 本轮矩阵

固定条件：

```text
dataset =
  BPC_future/data/gat_batch_impact/v23_mixed_v21_plus_train_split_remaining_contrast_first_tranche_ab_roi_20260616
epochs = 8
seed = 41
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_loss_multiplier = 2.0
hard_roi_safe_delay_loss_multiplier = 1.0
pairwise_candidate_ranking_loss_multiplier = 0.75
```

实际完成两个最有信息量的点：

| variant | candidate_delay_score_penalty | hard_roi_negative_delay_loss_multiplier | 目的 |
| --- | ---: | ---: | --- |
| v29_p050_n100 | 0.50 | 1.00 | 同时放松 penalty 和 hard-negative delay 校准，测试上界 coverage |
| v29_p075_n200 | 0.75 | 2.00 | 只放松 penalty，保留 v28 hard-negative delay 校准 |

未继续跑完整 2x2 的原因：前两个点已经给出单调清晰结论。`p050/n100` false-safe
直接崩塌；`p075/n200` 虽然恢复 high-ROI capture，但仍远超 false-safe 硬上限。
继续跑更松点没有 Stage 3 意义；继续跑接近 v28 的点只会回到 v28 blocker。

## Frontier 对比

| metric | v28 | v29_p050_n100 | v29_p075_n200 |
| --- | ---: | ---: | ---: |
| accepted_batch_count | 22 | 60 | 31 |
| accepted_batch_roi | 10.363879138773138 | 5.259393584790329 | 9.578097760196655 |
| accepted_batch_roi_ci_low | 4.579148638670199 | 2.783378241123864 | 5.30637039762128 |
| safe_precision_ci_low | 0.8513404742740388 | 0.939826069522067 | 0.889740999265246 |
| high_priority_precision | 0.9974093264248705 | 0.9488752556237219 | 0.9294871794871795 |
| high_priority_precision_ci_low | 0.9854729046367267 | 0.9332304440465666 | 0.9026271643369088 |
| false_high_priority_on_delay | 0.00847457627118644 | 0.5319148936170213 | 0.35106382978723405 |
| false_safe_rate_union | 0.00847457627118644 | 0.5319148936170213 | 0.35106382978723405 |
| candidate_delay_gate_blocked_count | 0 | 0 | 87 |
| candidate_risk_adjusted_suppressed_count | 662 | 48 | 420 |
| candidate_threshold | 0.3353747177982669 | 0.22914484647085312 | 0.2425465249523217 |

读法：

- `p050/n100` accepted count 和 safe CI 看起来好，但 false-safe = 53.19%，完全不可用；
- `p075/n200` ROI CI-low 比 v28 高，accepted count 也高，但 false-safe = 35.11%，仍不可用；
- v28 的 false-safe 合格来自强 risk penalty / suppression；一旦单值 penalty 放松，
  low-ROI / delay-risk batch 会重新进入 HIGH_PRIORITY。

因此 v29 没有 Stage 4 candidate。

## Opportunity / Margin

只对较有信息量的 `v29_p075_n200` 追加 opportunity 和 score-margin 审计。

```text
high_roi_opportunities = 30
accepted_high_roi_opportunities = 22
missed_high_roi_opportunities = 8
accepted_low_roi_or_bad = 10
missed_reason_counts =
  {'candidate_delay_risk_above_threshold': 7,
   'candidate_risk_adjusted_below_threshold': 7,
   'no_candidate_above_threshold': 8}
candidate_margin_bucket_counts =
  {'near_candidate_threshold': 6,
   'moderate_candidate_score_gap': 1,
   'deep_candidate_score_gap': 1}
missed_without_same_context_contrast_count = 2
```

对比 v28：

| metric | v28 | v29_p075_n200 |
| --- | ---: | ---: |
| accepted high-ROI | 15 / 30 | 22 / 30 |
| missed high-ROI | 15 | 8 |
| accepted low/bad | 8 | 10 |
| near misses | 6 | 6 |
| moderate misses | 7 | 1 |
| deep misses | 2 | 1 |
| missed without same-context contrast | 4 | 2 |

这说明 penalty 放松确实恢复了 high-ROI capture，并且把 moderate/deep miss 显著减少。
但它同时打开了大量 false-safe：frontier best 的 `false_safe_rate_union=0.3511`，
远高于 Stage 3/4 的 `<=0.02` 上限。这个 tradeoff 不允许靠 ROI 抵消。

## 关键发现

1. v28 missed high-ROI 不是单纯结构性分不开。
   v29_p075_n200 能把 accepted high-ROI 从 15/30 提升到 22/30，说明分数空间里有可恢复信号。

2. scalar penalty 不是足够精细的控制旋钮。
   penalty 从 1.0 降到 0.75 后，高 ROI 恢复，但 false-safe 从 0.0085 飙到 0.3511。
   这说明当前 delay-risk 分数同时覆盖了两类样本：
   - true high-ROI 但被过度惩罚的 near-miss；
   - 真实 low-ROI / delay-risk batch。

3. hard delay gate 本身仍不是主要解法。
   v29_p075_n200 的 `candidate_delay_gate_blocked_count=87`，但 false-safe 仍然过高。
   仅靠 fixed delay-risk threshold 不能替代 admission score 校准。

4. 下一步应从“全局 penalty”转到“条件化 admission”。
   需要让 penalty 或阈值依赖 family/context/OOD/kNN/CBF safety，而不是用一个全局
   exponent 同时处理 random-wave task50 near-miss 和 sector-wave low/bad batch。

## Exactness Boundary

本轮所有 artifact 都是 offline / diagnostic-only：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```

GAT/CBF/kNN/OOD 仍只能做 ordering、priority 或 finite-delay scheduling。最终
optimality certificate 只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙
的 exhaustive no-negative closure。

## 下一步

不要继续盲扫单值 penalty。建议下一步做最小结构改造：

1. 新增 `context_family_risk_penalty` audit mode：
   - 对 `random-wave:task50` 和缺 same-context contrast 的 context 使用较低 penalty；
   - 对已有 low/bad contrast 的 context 保持 v28 penalty=1.0；
   - 仍然用同一套 Stage 3 frontier / opportunity / margin gate 验收。
2. 或者新增 two-stage candidate admission score：
   - stage A 用 v28 strict score 控 false-safe；
   - stage B 只对 kNN/OOD-safe 且 raw high-priority margin 足够高的 near-miss 追加 rescue window；
   - rescue window 必须单独报告 false-safe 和 accepted low/bad。
3. 对 v29_p075_n200 的 remaining missed context 继续补 contrast：
   - `random-wave:a67f331bdb819d7d`
   - `random-wave:e6b17bbf825984ae`

只有上述结构化校准同时满足 false-safe、safe CI、ROI-CI 和 kNN/OOD gate 后，才允许重新进入 Stage 4 shadow / opt-in no-regression。
