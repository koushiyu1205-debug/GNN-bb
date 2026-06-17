# 2026-06-16 BPC_future GAT Stage 3 v45 False-Delay Contrast 综合报告

## 读取范围

本轮重新读取 `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`、Stage 1/2 基础报告、Stage 3 v43/v44、Stage 4 v38/v40 和 Stage 5 20/30/50/100 目标。

边界保持不变：GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling；进入 RMP 的列仍必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 full exact pricing no-negative closure。

## 背景结论

v43 说明 v15 missed high-ROI 不是阈值差一点：

```text
primary = candidate_head_score_gap_plus_embedding_structural_gap
near_threshold_miss_count = 0
non_near_threshold_miss_count = 16
recommended_next_step = collect_train_split_same_context_positive_negative_pairs_and_delay_hard_negatives
```

v44 进一步说明严格 delay-safe 壳层存在，但 coverage 坍缩：

```text
delay_safe_threshold_count = 1309
delay_safe_with_accepted_batch_count = 335
delay_safe_accepted_batch_count_max = 2
recommended_primary = delay_safe_shell_exists_but_coverage_too_small
```

因此这轮不再继续单纯调 threshold，而是把 Stage 3 训练目标加硬到同一 context 内的 false-delay hard-negative 对比。

## 代码改动

`BPC_future/scripts/train_gat_batch_impact.py` 新增：

- `--pairwise-false-delay-contrast-loss-multiplier`，默认 `0.5`；
- same-context ROI pair 中的 false-delay contrast loss：
  - 高 ROI batch 的 labeled safe candidate 在 candidate-head 上必须高于低 ROI / delay batch 的 delay candidate；
  - 低 ROI / delay batch 的 delay candidate 在 delay-risk head 上必须高于高 ROI batch 的 safe candidate；
- checkpoint metadata、metrics 和 report 中写出 `pairwise_false_delay_contrast_loss_multiplier`；
- pairwise loss 内 better/worse sample 各只前向一次，避免 batch score、candidate ranking 和 false-delay contrast 重复前向。

`BPC_future/tests/test_gat_batch_impact_training.py` 新增：

- loss option 字段检查；
- fake-model 单测，验证 false-delay hard-negative contrast 对未分开的 safe/delay candidate 产生正损失。

## v45 Smoke

使用 v39 数据集做 1 epoch diagnostic smoke：

```text
dataset =
  BPC_future/data/gat_batch_impact/v39_mixed_v23_plus_neighbor_roi_b6d808_ab_roi_20260616

metrics =
  BPC_future/results/gat_batch_impact_training_v45_false_delay_contrast_v39_smoke_20260616/metrics.json

training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v45_false_delay_contrast_training_smoke_zh.md
```

关键结果：

```text
pairwise_false_delay_contrast_loss_multiplier = 0.5
checkpoint_gate_pass = false
stage4_candidate_ready = false
accepted_batch_count = 3
accepted_batch_roi = 1.0162206888198853
accepted_batch_roi_ci_low = 0.8130007701208048
safe_precision = 1.0
safe_precision_ci_low = 0.4384939195509822
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9914410785453043
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
candidate_threshold = 0.272533852408138
candidate_score_threshold_blocked_count = 770
rejected_checkpoint_reasons =
  ['safe_precision_ci_low_below_threshold_or_not_measurable', 'knn_ood_audit_missing']
```

解释：

1. false-delay suppression 方向有效，`false_high_priority_on_delay` 从 v39 的 `0.4489795918367347` 降到 `0.0`。
2. 但 accepted coverage 太小，validation 只接受 `3 / 123`，`safe_precision_ci_low = 0.4384939195509822`，仍未达到 Stage 3 hard gate。
3. 这与 v44 的结论一致：当前模型可以形成 delay-safe 壳层，但壳层太窄，不足以作为 Stage 4 candidate。
4. 这只是 1 epoch smoke，不能证明 full training 后的最终 frontier；但它证明新增训练目标和 artifact 字段可运行。

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `default_enabled=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。

## 下一步

下一步应做正式 v45 训练，而不是降低 Stage 3 gate：

1. 用相同 v39 数据集跑完整 8 epoch v45；
2. 对比 v39 / v45 的 threshold frontier：
   - false-delay 是否保持接近 0；
   - accepted coverage 是否能从 `3` 恢复到可过 CI 的样本量；
   - high-ROI capture 是否继续覆盖 random-wave / sector-wave；
3. 如果 full v45 仍停在 low-coverage delay-safe 壳层，就继续做模型结构修复：candidate head / delay-risk head 需要更强的 context-local 表示，而不是继续扫阈值。

当前结论：

```text
stage3_completed = false
stage4_candidate_ready = false
next_step = run_full_v45_false_delay_contrast_then_threshold_frontier_and_gate_shortfall
```
