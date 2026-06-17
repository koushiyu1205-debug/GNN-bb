# 2026-06-16 BPC_future GAT Target Mode Stage 3 v28 Risk-adjusted Delay Calibrated Synthesis

## 结论

本轮先重读五阶段计划、v15 Stage 3 missed high-ROI 诊断、最新 Stage 4 v23
A/B / certificate 审计和 Stage 5 目标，再推进 v28。结论是：

```text
v28_training_completed = true
v28_threshold_frontier_completed = true
v28_knn_ood_completed = true
v28_opportunity_mining_completed = true
v28_score_margin_audit_completed = true
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
```

v28 的正向变化是：v27 的 hard delay gate 没有真正参与 admission
(`candidate_delay_gate_blocked_count=0`)，v28 改为 risk-adjusted candidate
admission score 后，delay-risk head 开始真实影响候选准入。

```text
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.0
validation_candidate_risk_adjusted_suppressed_count = 662
train_candidate_risk_adjusted_suppressed_count = 2476
```

但是 v28 仍不能进入 Stage 4。当前 blocker 不是 exactness，而是 Stage 3/4
deployment gate 没过：

```text
frontier_safe_precision_ci_low = 0.8513404742740388 < 0.90
knn_safe_precision_ci_low = 0.8063865817272801 < 0.90
knn_accepted_batch_roi_ci_low = 0.3155012164995732 < 0.65
```

因此 v28 只能作为 offline diagnostic checkpoint。下一步不能盲目调参，应围绕
missed high-ROI 的两类原因分别处理：risk penalty 过重的 near-threshold
candidate，以及候选分数本身仍分不开的 context。

## 本轮先读的阶段目标

Stage 3 训练目标已写硬：

```text
primary_objective = precision_constrained_roi_maximization
```

训练不是先做分类器再事后看 ROI / precision。checkpoint 是否合格必须先过
precision、safe precision、ROI、ROI-CI、false-safe、coverage、family/context
holdout gate；loss、F1、AUC、recall 只能作为 surrogate 或 tie-breaker。

Stage 4 的目标是先证明不退化，再证明有 ROI：

- 5/10 official no-regression；
- certificate safety audit 无 violation；
- online shadow / opt-in A/B 必须 default-off；
- 20-task A/B 要证明 wall-time、tail retry 或 pricing workload ROI；
- GAT/CBF/kNN/OOD 仍不能产生 lower bound 或 certificate。

Stage 5 的目标更硬：

- 5-task no regression；
- 10-task no regression；
- 20-task `OPTIMAL` within 200s；
- official dual bound available；
- certificate only from exact pricing full closure；
- 30/50/100 只在 exact-safe fallback 下报告 heuristic acceleration，除非 exact
  closure 成功。

## v15 对照

v15 把 Stage 4 v14 exact safe-hit batch8 A/B 的真实 trajectory ROI 回流训练后，
把 false-safe 压到 0，但 accepted coverage 太窄：

```text
accepted_batch_count = 13
accepted_batch_roi = 16.316478240948456
accepted_batch_roi_ci_low = 8.0292472538527
false_safe_rate_union = 0.0
safe_precision_ci_low = 0.7718981569447084
stage4_candidate_ready = false
```

v15 missed high-ROI score margin 审计显示：

```text
high_roi_opportunities = 28
accepted_high_roi_opportunities = 12
missed_high_roi_opportunities = 16
candidate_margin_bucket_counts = {
  "deep_candidate_score_gap": 11,
  "moderate_candidate_score_gap": 5
}
missed_without_same_context_contrast_count = 7
```

也就是说 v15 missed high-ROI 主要不是“分数差一点”，而是模型结构/训练数据
还没有把相关 context 分开。因此 v15 后续方向是补 same-context positive /
negative pairs，而不是降 threshold。

## v28 改动

本轮只改 offline Stage 3 training / audit 工具，不改 solver、pricing、RMP、
worker 或 certificate path。

新增默认关闭的训练/审计能力：

- 可配置 `candidate_delay_loss_multiplier`；
- hard-ROI negative / bad-mode batch 上，把 candidate delay-risk head 校准到 1；
- hard-ROI safe high-priority candidate 上，把 delay-risk head 校准到 0；
- 新增 `candidate_admission_score_mode=risk_adjusted_product`；
- risk-adjusted admission score 使用 `high_priority_score * (1 - delay_risk_score)^penalty`；
- threshold frontier、kNN/OOD、opportunity mining、score margin audit 统一使用同一套
  admission score，避免训练和审计阈值不一致。

这些机制只改变 offline checkpoint selection / diagnostic audit；不产生 official
bound，不参与 no-negative certificate。

## v28 Training / Frontier

训练命令使用 v23 mixed dataset：

```text
dataset =
  BPC_future/data/gat_batch_impact/v23_mixed_v21_plus_train_split_remaining_contrast_first_tranche_ab_roi_20260616
checkpoint =
  BPC_future/data/gat_batch_impact/v28_risk_adjusted_delay_calibrated_v23_data_20260616/gat_batch_impact.pt
```

selected checkpoint：

```text
best_epoch = 6
best_loss_epoch = 3
checkpoint_gate_pass = false
checkpoint_gate_reject_reasons =
  ['knn_ood_audit_missing', 'safe_precision_ci_low_below_threshold_or_not_measurable']
```

threshold frontier best candidate：

```text
accepted_batch_count = 22
accepted_batch_roi = 10.363879138773138
accepted_batch_roi_ci_low = 4.579148638670199
safe_precision = 1.0
safe_precision_ci_low = 0.8513404742740388
high_priority_precision = 0.9974093264248705
high_priority_precision_ci_low = 0.9854729046367267
false_high_priority_on_delay = 0.00847457627118644
false_safe_rate_union = 0.00847457627118644
candidate_delay_gate_blocked_count = 0
candidate_risk_adjusted_suppressed_count = 662
stage4_candidate_ready = false
```

对比 v27：

| metric | v27 | v28 |
| --- | ---: | ---: |
| accepted_batch_count | 24 | 22 |
| accepted_batch_roi | 9.514876774822673 | 10.363879138773138 |
| accepted_batch_roi_ci_low | 4.099000909759836 | 4.579148638670199 |
| safe_precision_ci_low | 0.8620194241710247 | 0.8513404742740388 |
| false_safe_rate_union | 0.00847457627118644 | 0.00847457627118644 |
| hard delay blocked | 0 | 0 |
| risk-adjusted suppressed | n/a | 662 |

解释：v28 用更窄的 accepted set 换来更高 ROI point / lower bound，但 accepted
count 下降使 safe precision CI lower bound 没有变好。

## v28 kNN/OOD

global kNN/OOD：

```text
production_ready = false
accepted_batch_count = 16
accepted_batch_roi = 6.688791900873184
accepted_batch_roi_ci_low = 0.3155012164995732
safe_precision = 1.0
safe_precision_ci_low = 0.8063865817272801
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
production_block_reasons =
  ['validation_safe_precision_ci_low_below_min',
   'validation_accepted_batch_roi_ci_low_below_min',
   'validation_candidate_not_ready']
```

对比 v27：

| metric | v27 kNN/OOD | v28 kNN/OOD |
| --- | ---: | ---: |
| accepted_batch_count | 16 | 16 |
| accepted_batch_roi | 3.0489296121522784 | 6.688791900873184 |
| accepted_batch_roi_ci_low | -0.4091389147994051 | 0.3155012164995732 |
| safe_precision_ci_low | 0.8063865817272801 | 0.8063865817272801 |
| false_safe_rate_union | 0.0 | 0.0 |

v28 明显修复了 kNN/OOD 后 ROI-CI 为负的问题，但仍没达到 `0.65` hard gate，
safe CI 也仍低于 `0.90`。

## Missed High-ROI 诊断

v28 opportunity mining：

```text
high_roi_opportunities = 30
accepted_high_roi_opportunities = 15
missed_high_roi_opportunities = 15
accepted_low_roi_or_bad = 8
missed_reason_counts = {
  "candidate_delay_risk_above_threshold": 1,
  "candidate_risk_adjusted_below_threshold": 12,
  "no_candidate_above_threshold": 15
}
```

v28 score margin：

```text
candidate_margin_bucket_counts = {
  "near_candidate_threshold": 6,
  "moderate_candidate_score_gap": 7,
  "deep_candidate_score_gap": 2
}
missed_without_same_context_contrast_count = 4
missed_candidate_score_margin_mean = -0.10886818499237977
missed_candidate_score_margin_min = -0.33159111128664875
```

这和 v15 不同：

| metric | v15 | v28 |
| --- | ---: | ---: |
| high_roi_opportunities | 28 | 30 |
| accepted_high_roi_opportunities | 12 | 15 |
| missed_high_roi_opportunities | 16 | 15 |
| near_candidate_threshold | 0 | 6 |
| moderate_candidate_score_gap | 5 | 7 |
| deep_candidate_score_gap | 11 | 2 |
| missed_without_same_context_contrast_count | 7 | 4 |

结论：v15 是“模型/数据结构性分不开”为主；v28 已经把 deep misses 大幅减少，
但 risk-adjusted delay penalty 把一批 raw high-priority 过线的真实 high-ROI
候选压到了阈值下。

典型 missed high-ROI：

```text
raw candidate score margin = +0.2339
risk-adjusted candidate score margin = -0.0031
missed_reasons = ['no_candidate_above_threshold', 'candidate_risk_adjusted_below_threshold']
```

因此下一步不应继续简单提高 positive boost，也不应降低 safety gate。更合理的
方向是校准 delay-risk penalty：例如做 penalty / delay-loss 的小矩阵审计，或者
改成 context/family-aware penalty，再用 same threshold/frontier/kNN/OOD/opportunity
pipeline 验证。

## v25-v28 阶段对照

| version | frontier accepted | frontier ROI CI-low | safe CI-low | false-safe | kNN ROI CI-low | accepted high-ROI | accepted low/bad | missed high-ROI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v25 | 58 | 2.689249384486058 | 0.9378800031047062 | 0.7033898305084746 | -0.3230884780601899 | 24 / 30 | 34 | 6 |
| v26 | 21 | 2.1236682014139197 | 0.8453561767357979 | 0.00847457627118644 | -1.050935970350018 | 10 / 30 | 13 | 20 |
| v27 | 24 | 4.099000909759836 | 0.8620194241710247 | 0.00847457627118644 | -0.4091389147994051 | 15 / 30 | 10 | 15 |
| v28 | 22 | 4.579148638670199 | 0.8513404742740388 | 0.00847457627118644 | 0.3155012164995732 | 15 / 30 | 8 | 15 |

读法：

- v25 coverage 高，但 false-safe 完全不可接受；
- v26/v27 压住 false-safe，但 high-ROI recall 和 kNN ROI-CI 不足；
- v28 在不增加 false-safe 的情况下提高 ROI-CI，并减少 accepted low/bad；
- v28 的剩余瓶颈是 CI sample count、kNN/OOD ROI-CI 和 delay-risk penalty 误压
  high-ROI 候选。

## Exactness Boundary

本轮所有 v28 操作都是 offline / diagnostic-only：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```

GAT / CBF / kNN / OOD 只能做 ordering、priority 或有限延迟 admission
scheduling。最终 optimality certificate 仍必须来自当前 branch/cut/dual 下 exact
pricing 对完整配置宇宙的 exhaustive no-negative closure。

## 验证

```text
py_compile = passed
unit_tests = passed
unittest_count = 31
v28_training = completed
v28_threshold_frontier = completed
v28_knn_ood = completed
v28_opportunity_mining = completed
v28_score_margin_audit = completed
```

测试命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_opportunity_mining \
  BPC_future.tests.test_gat_batch_impact_threshold_frontier \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_batch_impact_score_margins
```

结果：

```text
Ran 31 tests in 0.304s
OK
```

## 下一步

不要直接盲扫所有超参。建议最小下一步：

1. 固定 v28 dataset / split / gate，只做 `candidate_delay_score_penalty` 和
   `hard_roi_negative_delay_loss_multiplier` 的小矩阵：
   - 重点比较 missed reason 中 `candidate_risk_adjusted_below_threshold` 是否下降；
   - 同时要求 false-safe、accepted low/bad、kNN ROI-CI 不回退。
2. 对 4 个 `missed_without_same_context_contrast` 的 context 补 same-context
   positive / negative pairs，尤其：
   - `sector-wave:9fadf4f7b39742a2`
   - `random-wave:a67f331bdb819d7d`
   - `random-wave:e6b17bbf825984ae`
3. 如果 penalty 小矩阵显示 near misses 可恢复且 false-safe 不升，再把 best variant
   跑完整 Stage 3 package：training、frontier、kNN/OOD、opportunity、margin。
4. 只有 Stage 3 gate 和 kNN/OOD gate 同时通过，才进入 Stage 4 shadow / opt-in
   no-regression；Stage 5 的 20-task 200s OPTIMAL 目标不能由当前 v28 直接支持。
