# BPC_future GAT target-mode Stage 3 v109 epoch selection and kNN/OOD audit

日期：2026-06-22

## 结论

这次 5000 行样本重训后，`epoch 1` 被选中不是因为 validation loss 最低，也不是因为 accepted 数最多；它是当前 checkpoint selector 在“部署门槛优先”规则下能找到的最安全诊断点。`epoch 7/8` 覆盖更高，但 false high-priority on delay 明确越过 1% 硬线，因此不能作为 Stage 3/4 候选。

当前还没有 Stage 4 candidate。GAT 和 kNN/OOD 都仍然只能 diagnostic-only，不能进入默认启用或 exact 证明路径。

## v108 原始 5000 行重训

训练输出：

- checkpoint: `BPC_future/results/gat_batch_impact_training_v108_5000_stage4_biased_seed13_20260622/model.pt`
- metrics: `BPC_future/results/gat_batch_impact_training_v108_5000_stage4_biased_seed13_20260622/metrics.json`
- report: `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v108_5000_retrain_seed13_zh.md`

关键 epoch：

| epoch | accepted | ROI | false-delay | precision | validation loss | selector judgement |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 13 | 33.164 | 0.0000 | 1.0000 | 4.466 | false-delay safe, low coverage |
| 7 | 158 | 7.170 | 0.0350 | 0.9948 | 3.170 | coverage ready, false-delay unsafe |
| 8 | 182 | 6.290 | 0.1469 | 0.9815 | 3.544 | coverage ready, false-delay unsafe |

因此 `best_loss_epoch=7` 不能选；它的 false-delay 是 3.50%，超过 `max_false_high_priority_on_delay=1%`。`epoch 8` 更差，false-delay 14.69%。

## v108 阈值前沿

阈值前沿改善了 selected checkpoint 的默认 accepted 覆盖，但仍未过 Stage 3 gate：

- best accepted: 22
- accepted ROI: 35.760
- ROI CI low: 23.365
- false-delay: 0.00350
- false safe union: 0.00350
- high-priority precision CI low: 0.9749
- safe precision CI low: 0.8513
- blocker: `safe_precision_ci_low_below_threshold_or_not_measurable`
- shortfall: 还缺 13 个 accepted 全成功验证样本，才能把 safe precision CI low 推到 0.9

这说明 v108 不是 ROI 不够，而是安全 accepted 样本数不够支撑置信下界。

## v108 kNN/OOD strict audit

global strict:

- accepted: 9
- ROI: 14.004
- ROI CI low: 8.753
- false-delay: 0.0000
- false safe union: 0.0000
- safe precision: 1.000
- safe precision CI low: 0.7008
- validation candidate ready: false

scale strict:

- accepted: 10
- ROI: 23.220
- ROI CI low: 4.557
- false-delay: 0.0000
- false safe union: 0.0000
- safe precision: 1.000
- safe precision CI low: 0.7225
- OOD rate: 0.0153
- validation candidate ready: false

kNN/OOD shell 没有发现新的安全问题，但它进一步压低 accepted 覆盖，因此仍然不能让 checkpoint 进入 Stage 4。

## v109 safety-biased repair training

训练输出：

- checkpoint: `BPC_future/results/gat_batch_impact_training_v109_5000_stage4_biased_delay_suppression_seed13_20260622/model.pt`
- metrics: `BPC_future/results/gat_batch_impact_training_v109_5000_stage4_biased_delay_suppression_seed13_20260622/metrics.json`
- report: `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v109_5000_delay_suppression_retrain_seed13_zh.md`

配置变化：

- `candidate_delay_risk_threshold=0.5`
- `candidate_delay_score_penalty=2.0`
- `candidate_delay_loss_multiplier=2.0`
- `false_high_priority_loss_multiplier=12.0`
- `hard_roi_negative_delay_loss_multiplier=2.0`
- `hard_roi_safe_delay_loss_multiplier=0.5`

结果：没有变好。

| epoch | accepted | ROI | false-delay | precision | validation loss | selector judgement |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 18 | 31.300 | 0.0000 | 1.0000 | 5.789 | false-delay safe, low coverage |
| 5 | 37 | 12.804 | 0.0175 | 0.9882 | 4.559 | coverage ready, false-delay unsafe |
| 6 | 73 | 14.828 | 0.0280 | 0.9888 | 4.407 | coverage ready, false-delay unsafe |
| 7 | 111 | 9.964 | 0.0420 | 0.9832 | 4.418 | coverage ready, false-delay unsafe |
| 8 | 87 | 12.664 | 0.0664 | 0.9760 | 4.828 | coverage ready, false-delay unsafe |

v109 的第 5 轮 accepted=37，已经够置信样本量，但 false-delay=1.75%，超过 1% 硬线，所以仍不能选。selector 继续选择 epoch 1 是正确的。

v109 阈值前沿：

- best accepted: 18
- accepted ROI: 31.300
- ROI CI low: 16.216
- false-delay: 0.0000
- false safe union: 0.0000
- safe precision CI low: 0.8241
- shortfall: 还缺 17 个 accepted 全成功验证样本

这比 v108 的 22 accepted / safe CI 0.851 更差。更强 delay suppression 把模型变保守了，但没有产生更多可证明安全的 accepted。

## 为什么不是 epoch 7 或 8

Stage 3 的选择目标不是 validation loss 最低，也不是 accepted 数最多，而是：

1. 先过安全门槛，尤其是 false high-priority on delay。
2. 再看 precision / safe precision 的置信下界。
3. 再看 ROI CI / ROI。
4. accepted coverage 是在安全可行后的次级目标。

所以：

- v108 `epoch 7`: loss 最低、accepted=158，但 false-delay=3.50%，直接硬 veto。
- v108 `epoch 8`: accepted=182，但 false-delay=14.69%，更不能选。
- v109 `epoch 5`: accepted=37，但 false-delay=1.75%，仍超过 1%。
- 当前可安全点只有低覆盖 epoch 1/2/3 类点，因此 selected checkpoint 仍是 epoch 1。

## 当前瓶颈

当前不是 checkpoint selection bug，也不是简单调阈值能解决的问题。审计结果一致指向：

- 安全高覆盖区域不足。
- 高覆盖 epoch 会引入 delay false-positive。
- 低 false-delay threshold 下 accepted 数不足，safe precision CI low 过不了 0.9。
- kNN/OOD shell 进一步降低 accepted 覆盖，不能弥补 Stage 3 gate。

## 下一步建议

继续训练同一批 5000 行数据、只调 loss 权重，收益不高。下一步应优先收集或构造 context-local hard negatives / near-boundary validation accepts：

- 针对 v108 frontier 中低 false-delay 但 accepted 不足的区域补样。
- 保留同一 context 下 positive/negative 成对样本，提升模型区分后期高覆盖 false-delay 的能力。
- 目标不是总样本数继续盲目增加，而是让验证集中 delay-safe accepted 从 22 提升到至少 35 个全成功样本。

## 验证

- `python -m unittest BPC_future.tests.test_gat_batch_impact_knn_ood`
- 结果：5 tests OK

## exactness boundary

本轮只运行离线训练、阈值审计、kNN/OOD safety shell 审计和报告生成：

- 不运行 BPC/pricing。
- 不修改 pricing oracle、lower/upper bound、certificate 或 exact closure。
- GAT/kNN/OOD 仍为 diagnostic-only。
- `selector_is_pricing_oracle=false`
- `selector_can_certificate=false`
- `gate_can_permanently_discard_negative_columns=false`
