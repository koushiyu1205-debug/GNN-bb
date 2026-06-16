# GAT Target Mode Stage 3 v24 Delay-Suppression Synthesis

日期：2026-06-16

## 目的

本报告不是新的 production admission 结论，而是读完五阶段计划、v15 Stage 3/4
证据、v23 合成报告以及最新 Stage 5 目标后，对 v24 delay-risk suppression
诊断实验的收敛判断。核心问题是：missed high-ROI 是阈值差一点，还是模型/数据
结构性分不开。

## 已读上下文

- Stage 1/2：batch-impact GAT 仍是 offline/audit-only；数据只允许来自
  same-context target intervention 与 true trajectory ROI，不能用 true-RC
  negative 直接替代 trajectory label。
- Stage 3：训练目标已经硬化为 `precision-constrained ROI maximization`；
  loss/F1/recall 只能做 surrogate，checkpoint 是否可进入 Stage 4 必须看
  precision、ROI、false-safe、coverage 和置信下界。
- v15 Stage 3：candidate threshold 高达 `0.9019626379013062`，validation
  high-ROI capture 为 `12/28`，missed `16`，其中 random-wave missed `5`、
  sector-wave missed `11`。
- v15 margin：missed 没有 near-threshold，`deep_candidate_score_gap=11`、
  `moderate_candidate_score_gap=5`；random-wave missed margin mean
  `-0.5054`，sector-wave mean `-0.3272`。
- v15 Stage 4：first-tranche top3 A/B 执行 `20/20`，reachability `9/9`，
  certificate violation `0`，但 9 个 target-worker 候选只有 2 个正 ROI，
  7 个应回流为 hard-negative / delay；更关键的是新增 rows 全在 validation
  split，不能改善 train split 可学习证据。
- 最新 Stage 5：20-task 目标是在 5/10 no-regression 和 exactness 不变的前提下
  `OPTIMAL within 200s`，official dual bound 和最终 certificate 只能来自 exact
  pricing full closure。

## v24 诊断设置

v24 只做训练/审计，不改 solver/pricing，不生成 certificate：

```text
dataset =
  BPC_future/data/gat_batch_impact/v23_mixed_v21_plus_train_split_remaining_contrast_first_tranche_ab_roi_20260616
checkpoint =
  BPC_future/data/gat_batch_impact/v24_delay_suppression_v23_data_20260616/gat_batch_impact.pt

false_high_priority_loss_multiplier = 12.0
hard_roi_candidate_loss_multiplier = 1.5
hard_roi_positive_candidate_loss_multiplier = 1.0
pairwise_candidate_ranking_loss_multiplier = 0.75
```

目的不是“再调一个好看的阈值”，而是验证 v23 的主要 blocker
`false_safe_rate_union=0.4255` 能否被 delay-risk 抑制项压下来。

## v24 结果

Training / threshold frontier 的最佳诊断点：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
accepted_batch_count = 17
accepted_batch_roi = 13.208018599187627
accepted_batch_roi_ci_low = 6.259074425581186
false_high_priority_on_delay = 0.00847457627118644
false_safe_rate_union = 0.00847457627118644
high_priority_precision_ci_low = 0.9770614106050519
safe_precision_ci_low = 0.8156763396284354
feasible_threshold_count = 0
family_holdout_missing_accepted_opportunity_families = ['random-wave']
```

Global kNN/OOD 后：

```text
accepted_batch_count = 12
accepted_batch_roi = 10.982604684929052
accepted_batch_roi_ci_low = 2.282549698834341
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
safe_precision_ci_low = 0.7574992425007574
production_ready = false
production_block_reasons =
  ['validation_safe_precision_ci_low_below_min',
   'family_holdout_accepted_batch_missing',
   'validation_candidate_not_ready']
```

Family 层面：

```text
sector-wave: accepted_batch_count = 12 after kNN/OOD
random-wave: oracle_high_roi_count = 6, accepted_batch_count = 0
greedy-anchor: oracle_high_roi_count = 0, accepted_batch_count = 0
```

## Missed High-ROI 诊断

v24 opportunity / margin：

```text
high_roi_opportunities = 30
accepted_high_roi_opportunities = 13
accepted_high_roi_capture_rate = 0.43333333333333335
missed_high_roi_opportunities = 17
accepted_low_roi_or_bad = 4
missed_reason_counts = {'no_candidate_above_threshold': 17}

candidate_margin_bucket_counts =
  {'deep_candidate_score_gap': 6,
   'moderate_candidate_score_gap': 3,
   'near_candidate_threshold': 8}
```

按 family 拆开：

```text
random-wave:
  missed_high_roi_opportunities = 6
  bucket = {'deep_candidate_score_gap': 5, 'near_candidate_threshold': 1}
  missed_candidate_score_margin_mean = -0.1990807776649793
  missed_candidate_score_margin_min = -0.25070591270923615
  missed_without_same_context_contrast_count = 3

sector-wave:
  missed_high_roi_opportunities = 11
  bucket = {'deep_candidate_score_gap': 1,
            'moderate_candidate_score_gap': 3,
            'near_candidate_threshold': 7}
  missed_candidate_score_margin_mean = -0.055926450274207375
  missed_candidate_score_margin_min = -0.3923274278640747
  missed_without_same_context_contrast_count = 3
```

解释：

- sector-wave 的 missed high-ROI 已经有 7 个落在 near-threshold，另有 3 个
  moderate gap；这部分可以通过校准、family-local threshold、或更细的
  candidate ranking 继续追。
- random-wave 不是简单阈值差一点：6 个 missed 中 5 个是 deep gap，平均 margin
  约 `-0.199`；v24 即使把全局 threshold 从 v15 的 `0.902` 降到 `0.496`，
  random-wave 仍没有 accepted high-ROI。
- random-wave 的若干 missed context 缺 same-context positive/negative 对照，
  因此当前证据更像“训练/表示结构性压分 + 对照样本不足”，不是单纯阈值问题。

## 结论

v24 相对 v23 的进步是真实的：false-safe / delay-risk 已从 v23 的大面积误放行
压到接近 Stage 4 诊断门槛，kNN/OOD 后 observed false-safe 为 `0`。但 v24 不能
进入 Stage 4，因为：

1. `safe_precision_ci_low` 仍低于门槛，主要受 accepted batch count / confidence
   lower bound 限制。
2. family holdout 失败：random-wave 有 6 个 oracle high-ROI，但 accepted 为 0。
3. accepted low-ROI/bad 仍有 4 个，说明 v23 的低 ROI / delay-risk 问题只是被
   大幅缓解，没有被完全解决。
4. 现有 family-local frontier 没有给出可行解，说明继续盲目全局阈值搜索收益低。

因此下一步不应继续“调参赌阈值”。正确方向是：

- 对 random-wave missed contexts 补 same-context positive/negative A/B rows，尤其
  `9f80ae35ea87da5b`、`a67f331bdb819d7d`、`e6b17bbf825984ae`；
- 在训练目标或 checkpoint selection 中加入 family high-ROI capture / family
  coverage 约束，避免 sector-wave 高 ROI 把 random-wave 全部压成 delay；
- 对 sector-wave near-threshold missed 单独做 calibration / candidate margin
  ranking，而不要用同一个全局放宽去污染 random-wave safety；
- 继续把 negative true-RC 但 trajectory ROI 为负的候选作为 DELAY/hard-negative，
  不能当 HIGH_PRIORITY 正样本。

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- `DELAY_QUEUE` 是有限延迟，不是永久 reject；
- final OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下完整
  configured universe 的 exact pricing full closure。

## Artifacts

```text
training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v24_delay_suppression_training_zh.md
threshold_frontier_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v24_delay_suppression_threshold_frontier_zh.md
knn_ood_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v24_delay_suppression_knn_ood_global_zh.md
opportunity_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v24_delay_suppression_opportunity_mining_zh.md
score_margin_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v24_delay_suppression_score_margin_audit_zh.md
```
