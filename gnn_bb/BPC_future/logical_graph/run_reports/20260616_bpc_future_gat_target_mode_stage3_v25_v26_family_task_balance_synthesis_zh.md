# 2026-06-16 BPC_future GAT Target Mode Stage 3 v25/v26 Family-task Balance 综合报告

日期：2026-06-16

## 结论

本轮目标不是继续盲目调 threshold，而是回答一个具体问题：v15 以来 missed
high-ROI 到底是“分数差一点”，还是当前模型结构性分不开。

结论是：

1. 不是纯结构性分不开。v25 用 family-task balanced hard-ROI positive
   candidate boost 后，accepted high-ROI 从 v24 的 `13 / 30` 提升到 `24 / 30`，
   missed random-wave task50 全部变成 near-threshold。
2. 但当前单一 HIGH_PRIORITY candidate head 仍然过载。v25 同时接受了 34 个
   low-ROI / bad batch，false-high-priority-on-delay 和 false-safe union 都爆到
   `0.7033898305084746`，不能进 Stage 4。
3. v26 把 safety 拉回来了，false-high-priority-on-delay 和 false-safe union
   都是 `0.00847457627118644`，checkpoint 只剩 safe precision CI 与 kNN/OOD
   类阻塞；但 high-ROI capture 掉到 `10 / 30`，random-wave 又出现 deep /
   moderate candidate gap。

所以下一步不应该再做纯全局 multiplier / threshold 扫描。应把 admission 目标拆成
两个可学习判断：

```text
roi_opportunity_score  高：这批列可能改善 RMP trajectory
delay_risk_score       低：这批列不太可能触发拖尾 / low-ROI admission

admit HIGH_PRIORITY only if:
  roi_opportunity_score passes
  and delay_risk_score fails the risk gate
```

同时增加 same-context high-ROI vs low-ROI / delay 的 candidate-level contrast，
让模型学会“同一 context 内哪个候选该上，哪个该 delay”，而不是只把正样本分数整体抬高。

## 对齐 Stage 3 / Stage 4 / Stage 5 目标

已重读 v15 Stage 3、最新 Stage 4 报告和主计划 Stage 5 目标。当前硬约束保持不变：

- Stage 3 训练验收不是 F1 / recall 优先，而是 precision、CI、false-safe、ROI、
  ROI CI、coverage、family/context holdout 先过；
- Stage 4 只能是 shadow / opt-in / guarded A/B，必须有 5/10 no-regression、
  online coverage、trajectory ROI、certificate audit；
- Stage 5 目标仍是 20-task `OPTIMAL <= 200s`，official dual bound 可用，并且
  certificate 只来自 exact pricing full closure；
- GAT/CBF/kNN/OOD 只能做 ordering / scheduling，不能生成 official bound、
  certificate 或 no-negative conclusion。

v15 Stage 4 first-tranche 的教训仍然成立：9 个 reachable target intervention 中
只有 2 个正 ROI，7 个应回流为 hard-negative / delay 证据；并且这些 rows 当时来自
validation split，不能当作训练 split 的可学习证据。后续必须优先补 train-split /
same-context 对照。

## 本轮改动

只改 offline trainer 和对应 unittest，没有改 solver、pricing、RMP、certificate 路径。

新增 default-off 训练选项：

```text
--hard-roi-positive-group-balance {none,family,task_count,family_task}
--hard-roi-positive-group-weight-power
--max-hard-roi-positive-group-weight
```

含义：只对达到 hard ROI gate 且非 bad-mode 的正样本候选 boost loss 做 group
balance。默认 `none`，保持旧行为。

v25 使用 full inverse-frequency family_task balance；v26 使用 mild sqrt balance
并提高 delay / low-ROI suppression。

## v25 结果

训练配置摘要：

```text
false_high_priority_loss_multiplier = 12.0
hard_roi_candidate_loss_multiplier = 1.5
hard_roi_positive_candidate_loss_multiplier = 1.5
hard_roi_positive_group_balance = family_task
hard_roi_positive_group_weight_power = 1.0
max_hard_roi_positive_group_weight = 4.0
```

训练 split hard-ROI positive group counts：

```text
greedy-anchor|10 = 1
random-wave|20 = 14
random-wave|30 = 6
random-wave|50 = 3
sector-wave|20 = 9
```

对应 weights：

```text
greedy-anchor|10 = 4.0
random-wave|20 = 1.0
random-wave|30 = 1.1
random-wave|50 = 2.2
sector-wave|20 = 1.0
```

关键结果：

```text
checkpoint_gate_pass = false
accepted_batch_count = 36
accepted_batch_roi = 7.854044479864772
accepted_batch_roi_ci_low = 4.004213317424325
high_priority_precision_ci_low = 0.9195970653083465
safe_precision_ci_low = 0.9035781695514236
false_high_priority_on_delay = 0.2542372881355932
false_safe_rate_union = 0.2542372881355932
rejected = false_high_priority_on_delay_too_high,
           false_safe_rate_union_too_high,
           family_holdout_accepted_roi_below_threshold,
           knn_ood_audit_missing
```

threshold frontier 最优候选：

```text
accepted_batch_count = 58
accepted_batch_roi = 5.255281713873673
accepted_batch_roi_ci_low = 2.689249384486058
safe_precision_ci_low = 0.9378800031047062
false_safe_rate_union = 0.7033898305084746
feasible_threshold_count = 0
```

opportunity / margin：

```text
accepted_high_roi = 24 / 30
missed_high_roi = 6
accepted_low_roi_or_bad = 34
random-wave accepted_high_roi = 1 / 6
random-wave missed = 5, all near_candidate_threshold
random-wave missed_candidate_score_margin_mean = -0.038853573799133304
sector-wave missed = 1, moderate_candidate_score_gap
```

解释：v25 证明了 random-wave task50 的一部分 missed high-ROI 不是模型完全分不开，
因为它们已经被拉到 candidate threshold 附近。但它也证明了单纯抬正样本会把
low-ROI / delay 候选一起放进 HIGH_PRIORITY。

## v26 结果

训练配置摘要：

```text
false_high_priority_loss_multiplier = 16.0
hard_roi_candidate_loss_multiplier = 2.0
hard_roi_positive_candidate_loss_multiplier = 1.0
hard_roi_positive_group_balance = family_task
hard_roi_positive_group_weight_power = 0.5
max_hard_roi_positive_group_weight = 2.5
```

对应 weights：

```text
greedy-anchor|10 = 2.5
random-wave|20 = 1.0
random-wave|30 = 1.0488088481701514
random-wave|50 = 1.4832396974191324
sector-wave|20 = 1.0
```

关键结果：

```text
checkpoint_gate_pass = false
accepted_batch_count = 16
accepted_batch_roi = 10.365407323464751
accepted_batch_roi_ci_low = 3.04184528049667
high_priority_precision = 0.9986876640419947
high_priority_precision_ci_low = 0.9926040041563496
safe_precision = 1.0
safe_precision_ci_low = 0.8063865817272801
false_high_priority_on_delay = 0.00847457627118644
false_safe_rate_union = 0.00847457627118644
rejected = safe_precision_ci_low_below_threshold_or_not_measurable,
           knn_ood_audit_missing
```

threshold frontier 最优候选：

```text
accepted_batch_count = 21
accepted_batch_roi = 7.969781869933719
accepted_batch_roi_ci_low = 2.1236682014139197
safe_precision_ci_low = 0.8453561767357979
false_safe_rate_union = 0.00847457627118644
feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
```

kNN/OOD：

```text
accepted_batch_count = 13
accepted_batch_roi = 5.9738279191347265
accepted_batch_roi_ci_low = -1.050935970350018
safe_precision_ci_low = 0.7718981569447084
false_safe_rate_union = 0.0
production_ready = false
```

opportunity / margin：

```text
accepted_high_roi = 10 / 30
missed_high_roi = 20
accepted_low_roi_or_bad = 13
random-wave accepted_high_roi = 1 / 6
sector-wave accepted_high_roi = 9 / 24
missed_reason_counts =
  batch_score_below_family_threshold = 8
  no_candidate_above_threshold = 19
candidate_margin_buckets =
  deep = 5
  moderate = 7
  near = 8
```

推荐补样 context：

```text
sector-wave: 9fadf4f7b39742a2, b6d808ebac2a6dd8
random-wave: a67f331bdb819d7d, e6b17bbf825984ae
```

解释：v26 是安全性最接近 Stage 3 的点，但 recall / coverage 不够，且 kNN/OOD 后
accepted count 和 ROI CI 又不足。继续微调全局 loss 很可能在 v25 和 v26 两端摇摆。

## 下一步

1. 停止纯全局超参扫描。
   v25/v26 已经显示正样本 recall 与 delay suppression 在单头 admission 里冲突。

2. 拆 admission 头或拆决策函数。
   推荐新增或重构为 `roi_opportunity_score` 与 `delay_risk_score` 双门控：
   高 ROI 机会必须过，delay / low-ROI 风险必须不过。

3. 增加 same-context low-ROI / delay contrast loss。
   同一 context 内，训练 `score(high-ROI batch/candidate) >
   score(low-ROI-or-delay batch/candidate) + margin`，并把 candidate-level
   false-high-priority-on-delay 作为硬惩罚。

4. 定向补数据，而不是扩大随机采样。
   优先补 v26 margin audit 标出的 4 个 context，尤其 random-wave task50 的
   `a67f331bdb819d7d`、`e6b17bbf825984ae`，以及 sector-wave 的
   `9fadf4f7b39742a2`、`b6d808ebac2a6dd8`。

5. 每轮继续执行同一套 hard gate。
   训练报告、threshold frontier、kNN/OOD、opportunity mining、score margin audit
   必须同时看；任何一项失败都保持 `stage4_candidate_ready=false`。

## Exactness Boundary

本轮所有 artifact 均为 offline / audit-only：

- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- `production_ready=false`；
- `default_enabled=false`。

GAT 可以让前面的 column generation 更聪明，但最终 certificate 仍必须由当前
branch/cut/dual 下的 exact pricing 对完整配置宇宙重新确认 no negative reduced-cost
journey。任何 delay queue 中 current true-RC negative 未清理或未 re-expose 时，都不能
报告 exact optimality。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_threshold_frontier \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_batch_impact_opportunity_mining \
  BPC_future.tests.test_gat_batch_impact_score_margins

Ran 27 tests in 0.188s
OK
```
