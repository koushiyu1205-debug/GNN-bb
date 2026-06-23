# BPC_future GAT target-mode Stage 3 v125 per-epoch checkpoint 综合审计

日期：2026-06-23

## 结论

v125 不是 Stage 4 candidate。

本轮目标是给 v121-like 训练配置增加 diagnostic-only per-epoch checkpoint，
从而能直接审计“如果选择 epoch 1/2/.../8，会不会更接近 Stage 3 gate”。结果显示：

- selected epoch 为 `2`，不是 validation loss 最低的 epoch `4`；
- epoch `2` 的 local deployment gate 和 v124 one-unsafe-neighbor kNN/OOD global/scale 壳都通过；
- 但 epoch `2` focused strict pair 只有 `74/78=0.9487`，低于 Stage 3 hard gate 的 `1.0`；
- epoch `3` focused 最好，为 `76/78=0.9744`，但 local false-delay 为 `1.083%`，超过 `1%` 上限；
- epoch `7/8` ROI 点估计更高，但 safe precision CI low 分别只有 `0.8754/0.8318`，不能选。

因此当前主 blocker 仍是 focused same-context pair gate，不是 kNN/OOD shell。
本轮没有运行 BPC、pricing、RMP、worker 或 certificate。

## 输入与产物

训练输入：

```text
dataset = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
```

说明：该 dataset 来自 5000 selected target rows 重建和显式 label conflict filtering；
训练 summary 里的 `sample_count=1117` 是 batch samples 数，不是 selected target rows 数。

本轮主要产物：

```text
training = BPC_future/results/gat_batch_impact_training_v125_v121_epoch_checkpoints_seed13_20260623
epoch checkpoints = .../epoch_checkpoints/epoch_001.pt ... epoch_008.pt
global kNN = BPC_future/results/gat_batch_impact_knn_ood_audit_v125_epoch002_global_one_unsafe_neighbor_20260623/summary.json
scale kNN = BPC_future/results/gat_batch_impact_knn_ood_audit_v125_epoch002_scale_one_unsafe_neighbor_20260623/summary.json
focused epoch2 = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v125_epoch002_20260623/summary.json
focused epoch3 = BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v125_epoch003_20260623/summary.json
```

## 代码侧改动

`train_gat_batch_impact.py` 新增了 `--epoch-checkpoint-dir`：

- 默认关闭，保留旧的 selected-checkpoint-only 输出；
- 每个 epoch 写出可被现有 kNN/OOD audit 读取的 `epoch_XXX.pt`；
- 同步写出 `epoch_XXX_metrics.json`，包含 deployment metrics、threshold search、focused pair gate 和 exact-safe contract；
- checkpoint 中仍写死 `production_ready=false`、`selector_is_pricing_oracle=false`、`selector_can_certificate=false`。

本轮还修正了 `_prediction_records()`：离线预测前记录 `model.training`，
结束后恢复原 train/eval 状态，避免 diagnostic evaluation 留下隐式状态副作用。

## Epoch 轨迹

| epoch | local gate | accepted | ROI | ROI CI low | safe CI low | false-delay | focused strict | 结论 |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | true | 35 | 14.832 | 6.112 | 0.9011 | 0.00361 | 0.9359 | local 可行但 ROI 低、focused 失败 |
| 2 | true | 35 | 19.451 | 10.358 | 0.9011 | 0.00722 | 0.9487 | 当前 selected diagnostic |
| 3 | false | 67 | 10.646 | 5.428 | 0.9458 | 0.01083 | 0.9744 | focused 最好，但 false-delay 超 1% |
| 4 | true | 36 | 18.200 | 9.285 | 0.9036 | 0.00722 | 0.9615 | validation loss 最低，但 ROI/CI 弱于 epoch2，focused 失败 |
| 5 | true | 35 | 18.666 | 9.559 | 0.9011 | 0.00722 | 0.9615 | local 可行但 focused 失败 |
| 6 | false | 50 | 13.102 | 6.327 | 0.9286 | 0.01805 | 0.9487 | false-delay 超限 |
| 7 | false | 27 | 23.648 | 12.493 | 0.8754 | 0.00722 | 0.9615 | ROI 高但 safe CI 不过 |
| 8 | false | 19 | 25.507 | 12.226 | 0.8318 | 0.00361 | 0.9615 | ROI 高但 safe CI 不过 |

`best_loss_epoch=4`，且 local gate 可行；但 checkpoint selection policy 是
`deployment_gate_first_then_roi_ci_baseline_utility_loss`。在可行 local checkpoint
之间，epoch `2` 的 ROI CI lower bound 更高，因此被选中。无论 epoch `2` 还是 epoch `4/5/7/8`，
focused strict 都未达到 `1.0`，不能升级 Stage 4。

## kNN/OOD 审计

对 selected epoch `2` 使用 v124 的 one-unsafe-neighbor 壳：

```text
knn_k = 3
max_neighbor_delay_fraction = 0.3333333334
min_safe_precision_ci_low = 0.9
max_false_high_priority_on_delay = 0.01
max_validation_false_safe_rate = 0.02
```

global 结果：

```text
validation_candidate_ready = true
production_block_reasons = []
accepted = 35
accepted ROI = 19.450745
ROI CI low = 10.357920
safe precision = 1.0
safe precision CI low = 0.901096
false high-priority on delay = 0.0
false safe union = 0.0
OOD count = 0
coverage = 1.0
```

scale 结果：

```text
validation_candidate_ready = true
production_block_reasons = []
accepted = 35
accepted ROI = 19.450745
ROI CI low = 10.357920
safe precision = 1.0
safe precision CI low = 0.901096
false high-priority on delay = 0.0
false safe union = 0.0
OOD count = 11
coverage = 0.962329
```

这说明 v124 的 global/scale kNN safety shell 在 v125 selected epoch2 上仍能保持通过。
但 kNN/OOD 通过不能替代 focused pair gate，也不能替代 Stage 4 shadow / opt-in / no-regression。

## Focused Pair 审计

epoch `2` focused failure：

```text
pair_count = 78
failed_pair_count = 4
strict_pair_pass_rate = 0.9487179487
diagnosis_counts = {
  mixed_margin_failure: 2,
  near_margin_loss_tuning_candidate: 1,
  near_margin_with_shared_signature: 1,
  pair_passes: 74
}
recommended_next_step = add_or_repair_context_action_consequence_features_before_more_sweeps
```

失败 context 主要集中在：

- `9f80ae35ea87da5b`，random-wave task30，2 个失败；
- `b36178f6655c5f75`，greedy-anchor task20，1 个 near-margin 失败；
- `ddcb5387bef3bf63`，random-wave task20，1 个 mixed-margin 失败。

epoch `3` focused failure：

```text
pair_count = 78
failed_pair_count = 2
strict_pair_pass_rate = 0.9743589744
diagnosis_counts = {
  near_margin_loss_tuning_candidate: 1,
  near_margin_with_shared_signature: 1,
  pair_passes: 76
}
recommended_next_step = train_combined_focused_candidate_admission_delay_loss
```

epoch `3` 的失败全是 near-margin，但它违反 false-delay 上限，所以不能直接作为 checkpoint。
它的意义是指出一个可执行方向：在不突破 false-delay hard gate 的前提下，做更窄的
combined focused candidate/admission/delay loss 修复，而不是盲目继续加普通样本。

## Stage 状态

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
checkpoint_gate_pass = false
```

当前 blocker：

- focused same-context pair gate 未通过；
- online shadow / opt-in A/B 未运行；
- 5/10 no-regression 和 20-task wall-time ROI 未绑定当前 checkpoint；
- GAT/kNN/OOD 不能提供 official lower bound 或 exact certificate。

## 下一步

不建议继续盲目 multiplier sweep 或普通总量补样。下一步应围绕两个收敛方向做窄实验：

1. 以 epoch `3` 的 near-margin 诊断为参照，训练更窄的 combined focused candidate/admission/delay loss，
   但必须保持 `false_high_priority_on_delay <= 0.01`；
2. 针对 `9f80ae35ea87da5b`、`ddcb5387bef3bf63` 和 `84ae11479ed592d4`
   做 action-consequence / context interaction feature repair，检查模型是否真正看到同 context 下不同 batch 的后续 trajectory 差异。

每次修复后必须同时重跑：

- full focused pair gate；
- v124 one-unsafe-neighbor global kNN/OOD；
- v124 one-unsafe-neighbor scale kNN/OOD。

只有 focused strict 达到 `78/78` 且 global/scale kNN 继续通过后，才值得进入 Stage 4 shadow / opt-in gate。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/scripts/train_gat_batch_impact.py \
  BPC_future/scripts/audit_gat_batch_impact_knn_ood.py \
  BPC_future/scripts/audit_gat_batch_impact_focused_pair_failures.py
```

通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_batch_impact_focused_pair_failures
```

结果：

```text
Ran 39 tests in 0.688s
OK
```

## Exactness Boundary

本轮只运行离线训练、per-epoch checkpoint 导出、focused pair failure audit 和 kNN/OOD safety-shell audit：

- 不运行 BPC/pricing/RMP；
- 不改变 pricing universe；
- 不改变 RMP lower bound 或 certificate；
- 不启用 production/default config；
- GAT/kNN/OOD 仍只能做 admission scheduling 诊断；
- true-RC negative columns 必须保持 eventually reachable；
- final optimality proof 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
