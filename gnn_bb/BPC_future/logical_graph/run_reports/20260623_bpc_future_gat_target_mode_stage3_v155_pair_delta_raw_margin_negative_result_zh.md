# BPC_future GAT target-mode Stage 3 v155 pair-delta raw-margin 负结果报告

日期：2026-06-23

## 目的

v154 已将 focused gate 从 v152 的 `75/78` 提升到 `77/78`，只剩
`apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b`
中的 row `844 > 845` raw near-margin failure。

v155 的目标是做一个窄幅训练侧修复：不改 exact solver、不放宽 gate、不改 kNN/OOD 语义，只把
focused raw candidate-head 排序压力提高，检查能否把 raw/strict 从 `77/78` 推到 `78/78`。

## 配置

```text
run_id = v155_pair_delta_raw_margin_v154_seed13
dataset_dir = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
sample_count = 1117
seed = 13
epochs = 8
context_pair_delta_hidden_dim = 16
context_pair_hidden_dim = 0
context_pair_delta_loss_multiplier = 0.5
focused_pair_delta_loss_multiplier = 2.0
focused_pair_raw_all_candidate_loss_multiplier = 10.0
v154_focused_pair_raw_all_candidate_loss_multiplier = 6.0
focused_gate_threshold = 78/78 for raw/admission/delay_risk/strict
checkpoint = BPC_future/results/gat_batch_impact_training_v155_pair_delta_raw_margin_v154_seed13_20260623/model.pt
metrics = BPC_future/results/gat_batch_impact_training_v155_pair_delta_raw_margin_v154_seed13_20260623/metrics.json
training_report = BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v155_pair_delta_raw_margin_seed13_zh.md
focused_pair_failure_audit = BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v155_pair_delta_raw_margin_pair_failure_audit_zh.md
knn_scale_strict_audit = BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v155_pair_delta_raw_margin_knn_ood_scale_strict_zh.md
```

## 结论

v155 是负结果，不能进入 Stage 4。

单纯把 focused raw loss 从 `6.0` 提到 `10.0` 确实修复了 v154 的 `9f80` near-margin raw failure，
但同时把已修复的其他 context 拉坏，focused gate 从 v154 的 `77/78` 回退到 `75/78`。

这说明当前问题不是“raw loss 权重再大一点”就能稳定闭合，而是仍存在 context/family 之间的迁移循环。
继续做盲目的 multiplier sweep 大概率会在 `9f80`、`b361`、`ddcb` 等 context 之间反复摆动。

## Epoch 选择

```text
best_epoch = 2
best_loss_epoch = 5
best_validation_loss = 4.726817035766184
selected_validation_loss = 5.692044305685021
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
checkpoint_gate_pass = false
stage4_candidate_ready = false
```

这里再次验证：本线不会因为 epoch 5 loss 最低就选 epoch 5。checkpoint selection 先看 deployment gate、
ROI CI / baseline utility，再用 loss 做 tie-breaker。v155 的 best-loss epoch 仍不能抵消 focused gate 失败。

## 与 v154 对比

```text
v154:
  focused pair_count = 78
  raw_pair_pass_rate = 0.9871794872
  admission_pair_pass_rate = 1.0
  delay_risk_pair_pass_rate = 1.0
  strict_pair_pass_rate = 0.9871794872
  context_pair_delta_pair_pass_rate = 0.9743589744
  failed_pair_count = 1
  failed_context = 9f80

v155:
  focused pair_count = 78
  raw_pair_pass_rate = 0.9615384615
  admission_pair_pass_rate = 0.9615384615
  delay_risk_pair_pass_rate = 0.9615384615
  strict_pair_pass_rate = 0.9615384615
  context_pair_delta_pair_pass_rate = 0.9615384615
  failed_pair_count = 3
  failed_contexts = b361, ddcb
```

Validation deployment metrics:

```text
v154:
  accepted_batch_count = 36
  accepted_batch_roi = 18.939204781833624
  accepted_batch_roi_ci_low = 10.046815201854097
  high_priority_precision = 0.9966499162479062
  high_priority_precision_ci_low = 0.9878681487216135
  safe_precision_ci_low = 0.9035781695514236
  false_high_priority_on_delay_count = 2
  false_safe_rate_union = 0.007220216606498195

v155:
  accepted_batch_count = 35
  accepted_batch_roi = 17.192218843102456
  accepted_batch_roi_ci_low = 8.253735197457987
  high_priority_precision = 1.0
  high_priority_precision_ci_low = 0.9939771880667552
  safe_precision_ci_low = 0.9010957324106112
  false_high_priority_on_delay_count = 0
  false_safe_rate_union = 0.0
```

v155 的 safety point estimate 更保守，false delay 错放变为 0，但 focused context ranking 更差，ROI 也低于 v154。
按计划合同，不能用 false-safe 改善抵消 focused gate 回退。

## Focused Failure Audit

v155 focused pair failure audit:

```text
pair_count = 78
pair_pass_count = 75
failed_pair_count = 3
contexts_with_failure_count = 2
raw_fail_count = 3
admission_fail_count = 3
delay_risk_fail_count = 3
strict_pair_pass_rate = 0.9615384615384616
diagnosis_counts = {'mixed_margin_failure': 3, 'pair_passes': 75}
recommended_next_step.primary = add_or_repair_context_action_consequence_features_before_more_sweeps
recommended_next_step.avoid = do_not_continue_blind_multiplier_sweeps
```

失败 context:

```text
b36178f6655c5f75:
  family = greedy-anchor
  task_count = 20
  failed_pair_count = 2
  min_raw_margin = -0.0441451073
  min_admission_margin = -0.0397137184
  min_delay_risk_margin = -0.0361275673

ddcb5387bef3bf63:
  family = random-wave
  task_count = 20
  failed_pair_count = 1
  min_raw_margin = -0.0272822976
  min_admission_margin = -0.0339921127
  min_delay_risk_margin = -0.0407848060
```

v154 的 `9f80` 已经修复：

```text
9f80ae35ea87da5b:
  pair_count = 2
  pair_pass_count = 2
  min_raw_margin = 0.0004899502
```

但这是以 `b361` / `ddcb` 回归为代价，不是稳定改进。

## kNN/OOD scale strict

v155 scale strict kNN/OOD:

```text
validation_candidate_ready = false
accepted_batch_count = 33
accepted_batch_roi = 16.95264626407262
accepted_batch_roi_ci_low = 7.627326629356332
coverage = 0.9657534246575342
ood_count = 10
false_high_priority_on_delay_count = 0
false_safe_rate_union = 0.0
safe_precision = 1.0
safe_precision_ci_low = 0.8957265699643882
blocker = validation_safe_precision_ci_low_below_min
```

kNN/OOD 也没有比 v154 scale strict 更好。v154 scale strict 的 safe precision CI low 是 `0.9035781696`，
而 v155 降到 `0.8957265700`，低于 `0.9`。因此即使忽略 focused gate，v155 的 scale strict safety
也没有达到 v154 的正结果。

## 判断

v155 证明了一个负结论：

```text
仅靠提高 focused raw multiplier 不能闭合 Stage 3 focused gate。
```

具体原因：

- raw loss 加大后，目标 `9f80` 修复；
- 但 `b361` 和 `ddcb` 出现混合 margin failure；
- admission、delay-risk 和 pair-delta 也一起回退；
- kNN/OOD scale strict 也从 v154 的 candidate-ready 回退到 not-ready。

这比 v154 更差，不能作为下一阶段候选。

## 下一步

不要继续做盲目 multiplier sweep。下一步应转到更结构化的稳定机制：

1. 在 focused loss 中显式做 frontier context balanced replay，使 `9f80`、`b361`、`ddcb`、`84ae` 这类已知 frontier
   contexts 同时受约束，而不是只靠全局 raw 权重；
2. 或者把 pair-delta / admission / delay-risk 已经排对的信号蒸馏回 raw logit，但要以所有 frontier context
   的联合 pass 为目标；
3. 如果仍不能稳定达到 `78/78`，应回到 action consequence feature，而不是继续调 loss 倍数；
4. 在 focused gate 达到 `78/78` 前，不进入 Stage 4。

## Exactness Boundary

本轮只运行 offline GAT training 和 offline audits：

```text
runs_bpc_or_pricing = false
runs_rmp = false
production_ready = false
default_enabled = false
stage3_completed = false
stage4_candidate_ready = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
official_bound_effect = false
```

GAT / kNN / OOD 仍只能影响 discovery / ordering / finite-delay scheduling。official lower bound、no-negative
conclusion 和 final certificate 仍只能来自 exact pricing full closure。
