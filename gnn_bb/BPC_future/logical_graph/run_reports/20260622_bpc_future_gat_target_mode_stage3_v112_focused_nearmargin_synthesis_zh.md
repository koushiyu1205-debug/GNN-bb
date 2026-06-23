# 2026-06-22 BPC_future GAT Target Mode Stage 3 v112 Focused Near-Margin 综合报告

## 结论

v112 是本轮 5000-row Stage 4-biased selected subset 上第一个同时满足 local Stage 3 hard gate、strict global kNN/OOD gate、strict scale kNN/OOD gate 和 threshold frontier local feasible gate 的 checkpoint 版本。

但 v112 仍不能进入 Stage 4 shadow / opt-in，也不能声明 `stage4_candidate_ready` 或 `production_ready`。当前主要 blocker 已从样本数量、safe precision CI、false-delay 和 kNN/OOD 转移到 focused same-context positive/negative pair gate：

```text
focused strict pair pass rate = 0.7421875
required strict pair pass rate = 1.0
stage4_candidate_ready = false
production_ready = false
```

因此当前正确状态是：

```text
stage3_local_threshold_gate = pass
knn_ood_validation_gate_global_strict = pass
knn_ood_validation_gate_scale_strict = pass
threshold_frontier_local_feasible = pass
focused_same_context_pair_gate = fail
stage4_online_shadow_or_optin_ab = not_run
stage4_candidate_ready = false
production_ready = false
```

## 计划边界复核

本轮复核了 `gat_bpc_future_target_mode_optimization_plan_zh.md` 中 Stage 3/4/5 的硬边界：

- Stage 3 的 primary objective 仍是 `precision_constrained_roi_maximization`；
- checkpoint selection 先看 deployment gate，再看 utility / ROI / validation loss tie-breaker；
- validation loss、F1、recall、AUC 不能抵消 precision / safe precision / ROI / false-delay / false-safe / coverage gate 失败；
- Stage 4 只能在 frozen threshold / OOD / fallback rule 绑定后进入 default-off shadow / opt-in；
- GAT、kNN、OOD、delay queue 都不能产生 official bound、pricing oracle 结论或 `CERTIFIED_NO_NEGATIVE`；
- Stage 5 仍要求 5/10 no-regression、20/30/50/100 exact-safe 加速，且 20-task 目标是 200s 内稳定 OPTIMAL。

因此 v112 的所有结论仍限制为离线 Stage 3 训练和审计证据，不改变 solver exactness 语义。

## 输入与 artifact

训练数据：

```text
BPC_future/data/gat_batch_impact/v107_optimized_5000_stage4_biased_first362_scale30first16_greedy30cap4_worker16_sector30cap4_worker16_scale50sgcap12_scale100open34_batch24_sectorcapfix_20context180new120batch4_followup40_20260619
```

主要 artifact：

```text
BPC_future/results/gat_batch_impact_training_v112_5000_stage4_biased_focused_nearmargin_seed13_20260622/model.pt
BPC_future/results/gat_batch_impact_training_v112_5000_stage4_biased_focused_nearmargin_seed13_20260622/metrics.json
BPC_future/results/gat_batch_impact_epoch_selector_v112_focused_nearmargin_5000_20260622/summary.json
BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v112_focused_nearmargin_5000_20260622/summary.json
BPC_future/results/gat_batch_impact_knn_ood_audit_v112_focused_nearmargin_global_strict_20260622/summary.json
BPC_future/results/gat_batch_impact_knn_ood_audit_v112_focused_nearmargin_scale_strict_20260622/summary.json
BPC_future/results/gat_batch_impact_threshold_frontier_v112_focused_nearmargin_5000_20260622/summary.json
```

## v112 训练结果

训练配置沿用 v111 的 focused-safety 方向，并显式加入 focused tranche near-margin losses：

```text
seed = 13
epochs = 8
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.55
candidate_delay_score_penalty = 1.5
focused_pair_loss_multiplier = 1.0
focused_pair_candidate_loss_multiplier = 1.5
focused_pair_admission_loss_multiplier = 2.0
focused_pair_delay_risk_loss_multiplier = 2.0
focused_pair_batch_loss_multiplier = 0.5
```

checkpoint selection:

```text
best_epoch = 1
best_loss_epoch = 4
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
checkpoint_gate_pass = false
stage4_candidate_ready = false
```

epoch 1 selected metrics:

```text
accepted_batch_count = 35
accepted_batch_roi = 4.921132917063577
accepted_batch_roi_ci_low = 2.6665812386647936
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9962733362720325
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
threshold_local_gate_pass = true
```

epoch 7/8 没有被选择的直接原因仍是 false-delay 过高：

| epoch | accepted | accepted ROI | false HIGH_PRIORITY on delay | local gate |
| --- | ---: | ---: | ---: | --- |
| 1 | 35 | 4.9211 | 0.000000 | pass |
| 7 | 130 | 7.9324 | 0.038462 | fail |
| 8 | 103 | 7.7019 | 0.034965 | fail |

这说明 v112 的训练不再是“只追求低 loss 或更大 accepted count”。epoch 7/8 的 accepted 更多、ROI 点估计也高，但 false-delay 超过 Stage 3 的 1% 上限，因此只能是 unsafe diagnostic signal。

## kNN/OOD 审计

### Global strict

配置：

```text
threshold_grouping = global
knn_k = 3
max_neighbor_delay_fraction = 0.0
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.55
candidate_delay_score_penalty = 1.5
```

结果：

```text
all_checks_pass = true
validation_candidate_ready = true
validation_safety_ready = true
production_block_reasons = []
accepted_batch_count = 35
accepted_batch_roi = 4.921132917063577
accepted_batch_roi_ci_low = 2.6665812386647936
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
coverage = 1.0
ood_rate = 0.0
```

### Scale strict

配置同 global strict，但 `threshold_grouping = scale`。

结果：

```text
all_checks_pass = true
validation_candidate_ready = true
validation_safety_ready = true
production_block_reasons = []
accepted_batch_count = 35
accepted_batch_roi = 4.921132917063577
accepted_batch_roi_ci_low = 2.6665812386647936
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
coverage = 0.9877300613496932
ood_rate = 0.012269938650306749
```

scale strict 下有 4 条 validation row 被 OOD delay，但没有产生 false-safe 或 false-delay。该结果说明 v112 的 kNN/OOD blocker 在当前 validation split 上已经解除。

## Threshold frontier

frontier 审计重新枚举动态阈值，不依赖训练报告中固定的 selected threshold。

关键结果：

```text
feasible_threshold_count = 135
best_candidate.accepted_batch_count = 39
best_candidate.accepted_batch_roi = 4.458170121678939
best_candidate.accepted_batch_roi_ci_low = 2.3914200616349515
best_candidate.safe_precision = 1.0
best_candidate.safe_precision_ci_low = 0.910330146399761
best_candidate.false_high_priority_on_delay = 0.0
best_candidate.false_safe_rate_union = 0.0
best_candidate.threshold_local_gate_pass = true
best_candidate.batch_threshold = 0.5123559832572937
best_candidate.candidate_threshold = 0.2651715148785978
```

frontier 结论：

```text
diagnosis.primary_blocker = has_local_feasible_threshold
```

这说明 v112 不是靠单点偶然阈值过线，而是已经有一段可行 threshold frontier。由于存在 local-feasible thresholds，本轮不再需要 gate shortfall 审计；shortfall 的主要用途是解释无可行 frontier 时还差多少 all-success accepted samples。

## Focused pair gate

v112 的主要失败点是 focused same-context positive/negative pair gate。

训练摘要中的 gate rates：

```text
pair_count = 384
raw_pair_pass_rate = 0.7838541666666666
admission_pair_pass_rate = 0.7838541666666666
delay_risk_pair_pass_rate = 0.765625
strict_pair_pass_rate = 0.7421875
required raw/admission/delay/strict pass rate = 1.0
```

pair failure audit：

```text
pair_count = 384
pair_pass_count = 285
failed_pair_count = 99
strict_pair_pass_rate = 0.7421875
all_failed_heads_near_rate_among_failed = 0.7575757575757576
any_failed_head_deep_rate_among_failed = 0.0
```

top blocking context：

```text
context_hash = b6d808ebac2a6dd8
family = sector-wave
task_count = 20
pair_count = 55
failed_pair_count = 36
pair_pass_count = 19
primary = near_margin_loss_tuning_candidate
min_raw_margin = -0.0366939902305603
min_admission_margin = -0.03903736382072523
min_delay_risk_margin = -0.037512391805648804
```

诊断：

```text
recommended_next_step.primary = train_combined_focused_candidate_admission_delay_loss
recommended_next_step.reason = pair failures are mostly near-margin, not deep structural inversions
```

这点很重要：v112 的 pair failure 主要是 near-margin 排序不稳，不是 deep structural inversion。下一步应优先做 focused near-margin repair，而不是降低 Stage 3/4 hard gate。

## 与 v108/v111 的变化

v108/v111 的核心问题是 local gate 和 safe CI/coverage 还没有同时站稳，且 kNN/OOD 缺失。v112 的变化是：

- local Stage 3 gate 首次通过；
- strict global kNN/OOD 首次通过；
- strict scale kNN/OOD 首次通过；
- threshold frontier 找到 135 个 local-feasible thresholds；
- false-delay 和 false-safe 都压到 0；
- accepted all-success count 达到 safe precision CI 的最低样本量要求；
- remaining blocker 集中到 focused same-context pair ranking。

这说明 5000-row 数据扩充加 focused near-margin loss 是有效方向，但还没有完成 Stage 3 到 Stage 4 的交接。

## 下一步

不进入 Stage 4。下一步继续 Stage 3，目标是修复 focused pair gate，同时保持 v112 已经通过的 local/kNN/frontier 指标不退化。

优先方向：

1. 对 `b6d808ebac2a6dd8`、`ac15bc4e7e3d6fff`、`79fde658840fe2b8` 等 top blocking contexts 做 context-local near-margin repair。
2. 训练目标继续使用 combined focused candidate/admission/delay losses，但提高 pair-margin 明确性，而不是放松 gate。
3. 新版本必须复跑：
   - training hard gate；
   - epoch selector；
   - focused pair failure audit；
   - strict global kNN/OOD；
   - strict scale kNN/OOD；
   - threshold frontier。
4. 若 focused pair gate 通过且 kNN/OOD/frontier 不退化，再进入 Stage 4 default-off shadow / opt-in no-regression 证据采集。

继续禁止：

- 不降低 `safe_precision_ci_low >= 0.90`；
- 不放宽 `false_high_priority_on_delay <= 0.01`；
- 不把 kNN/OOD no-column 或 GAT delay 当成 certificate；
- 不在 5/10 no-regression、20-task A/B 和 certificate safety 通过前声明 production-ready。

## 本轮状态

```text
stage3_retraining_progress = improved
stage3_local_gate = pass
knn_ood_global_strict = pass
knn_ood_scale_strict = pass
threshold_frontier = pass
focused_pair_gate = fail
stage4_candidate_ready = false
production_ready = false
recommended_action = continue_stage3_focused_pair_repair
```
