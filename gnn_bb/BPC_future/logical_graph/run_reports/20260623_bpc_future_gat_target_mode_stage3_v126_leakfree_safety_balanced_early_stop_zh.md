# BPC_future GAT target-mode Stage 3 v126 leak-free safety-balanced 早停报告

日期：2026-06-23

## 结论

v126 是负结果，已在 epoch `4` 后早停。

本轮尝试把 v125 的 full focused-row training 收紧为 leak-free focused training：

- focused gate 仍使用 full `102` focused rows；
- focused training loss 只使用 seed13 train split 内的 `81` focused rows；
- v121 focused boost 只使用 train-only `7` rows；
- targeted safe-positive 仍使用 train split `24` rows；
- 额外加强 false-delay / candidate-delay / focused delay-risk 惩罚，目标是保留 v125 epoch3 的 near-margin 排序信号，同时压住 false-delay。

实际结果没有改善：

- 前 4 个 epoch focused strict 最高只有 `73/78=0.9359`；
- 低于 v125 epoch3 的 `76/78=0.9744`；
- 也低于 v121/v123 的 `75/78` / `74/78` 边界；
- 因此无需继续消耗后 4 个 epoch。

本轮没有运行 BPC、pricing、RMP、worker 或 certificate。

## 输入与配置

```text
dataset = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
output = BPC_future/results/gat_batch_impact_training_v126_leakfree_safety_balanced_epoch_checkpoints_seed13_20260623
epoch checkpoints = .../epoch_checkpoints/epoch_001.pt ... epoch_004.pt
```

关键训练配置：

```text
focused_pair_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_gate_row_indices.json
focused_pair_training_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_training_row_indices.json
focused_pair_boost_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_boost_train_row_indices.json
targeted_safe_positive_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/optional_v121_train_targeted_safe_positive_row_indices.json
false_high_priority_loss_multiplier = 10.0
candidate_delay_loss_multiplier = 1.5
hard_roi_negative_delay_loss_multiplier = 1.5
candidate_delay_score_penalty = 1.75
focused_pair_loss_multiplier = 1.5
focused_pair_candidate_loss_multiplier = 2.0
focused_pair_admission_loss_multiplier = 3.0
focused_pair_delay_risk_loss_multiplier = 3.5
focused_pair_boost_loss_multiplier = 2.0
targeted_safe_positive_loss_multiplier = 0.5
```

## 前 4 个 epoch

| epoch | local gate | accepted | ROI | ROI CI low | safe CI low | false-delay | focused strict | 结论 |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | true | 35 | 10.630 | 3.078 | 0.9011 | 0.00000 | 58/78 = 0.7436 | focused 大幅退化 |
| 2 | false | 28 | 21.790 | 11.087 | 0.8794 | 0.00000 | 71/78 = 0.9103 | safe CI 不过，focused 仍弱 |
| 3 | true | 35 | 19.384 | 10.278 | 0.9011 | 0.00722 | 73/78 = 0.9359 | local 可行，但 focused 低于 v125/v121 |
| 4 | true | 35 | 19.463 | 10.373 | 0.9011 | 0.00722 | 72/78 = 0.9231 | focused 回落 |

与 v125 对比：

| run | 最好 focused strict | local/safety 说明 |
|---|---:|---|
| v125 epoch2 selected | 74/78 = 0.9487 | local + global/scale kNN pass |
| v125 epoch3 diagnostic | 76/78 = 0.9744 | false-delay 1.083%，local 不过 |
| v126 early-stop best | 73/78 = 0.9359 | local 可行但 focused 更差 |

因此 v126 的调整方向不值得继续。

## 判断

这次负结果说明：单纯把 full focused rows 改成 train-only，并同时增强 delay/safety 惩罚，
会把模型推向更保守，但没有提高 focused same-context 排序能力。它也没有复制 v125 epoch3
的 near-margin 优势。

下一步不应继续在同一组 multiplier 上扩大搜索。更合理的方向是：

1. 保留 v125 的 per-epoch checkpoint 审计工具；
2. 回到 feature/action-consequence 诊断，重点看 `9f80ae35ea87da5b`、`ddcb5387bef3bf63`、`84ae11479ed592d4`；
3. 若继续训练，使用更小的单变量实验，例如只调整 focused delay-risk loss 或只调整 candidate-delay penalty，避免多个惩罚同时改变导致不可解释；
4. 每个候选仍必须同时过 full focused gate 与 v124 global/scale one-unsafe-neighbor kNN/OOD。

## Stage 状态

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
```

当前主 blocker 不变：

- focused same-context pair gate 未达到 `78/78`；
- Stage 4 shadow / opt-in 未运行；
- 5/10 no-regression 与 20-task ROI 未绑定当前 checkpoint；
- GAT/kNN/OOD 不能提供 official lower bound 或 exact certificate。

## Exactness Boundary

本轮只运行离线训练前 4 个 epoch，并保存 per-epoch diagnostic checkpoints：

- 不运行 BPC/pricing/RMP；
- 不改变 pricing universe；
- 不改变 lower bound、certificate 或 exact closure；
- 不启用 production/default config；
- true-RC negative columns 必须保持 eventually reachable；
- final optimality proof 仍只能来自 exact pricing full closure。
