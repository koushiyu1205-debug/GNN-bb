# BPC_future GAT target-mode Stage 3 v130 focused context-pair comparator 早停报告

日期：2026-06-23

## 结论

v130 是负结果，已在 epoch `4` 后早停。

本轮基于 v127/v128 诊断做两个改动：

1. 在 `GATBatchImpactModel` 中加入默认关闭的 same-context pair comparator head；
2. 在训练脚本中加入 focused-only comparator loss，并给 threshold search 增加 candidate decision 缓存。

实际训练结果没有超过 v125：

- epoch `4` focused strict 达到 `74/78=0.9487`，只追平 v125 selected epoch2；
- v125 selected epoch2 的 accepted ROI / ROI CI low 是 `19.451 / 10.358`，v130 epoch4 只有 `13.702 / 5.402`；
- v130 epoch3 ROI 最高，为 `16.912 / 7.936`，但 focused strict 只有 `73/78`；
- 没有任何 epoch 通过 focused gate 的 `78/78` 硬线。

因此 v130 不能作为 Stage 4 candidate，也不值得继续同配置跑 epoch 5-8。

## 输入与产物

```text
dataset = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
output = BPC_future/results/gat_batch_impact_training_v130_focused_context_pair_comparator_cached_seed13_20260623
epoch checkpoints = .../epoch_checkpoints/epoch_001.pt ... epoch_004.pt
early_stop_summary = .../early_stop_summary.json
```

由于本轮按指标早停中断，未生成最终 `model.pt` / `metrics.json`。可审计产物是 4 个 per-epoch checkpoint 和 `early_stop_summary.json`。

## 代码侧改动

`BPC_future/learning/batch_impact_model.py`：

- 新增 `context_pair_hidden_dim`，默认 `0`；
- 默认不创建 comparator head，旧 checkpoint 配置不变；
- 显式开启后增加 `context_pair_preference_logit(left_output, right_output)`；
- forward 输出新增 `batch_decision_embedding`，供同 context pair comparator 使用。

`BPC_future/scripts/train_gat_batch_impact.py`：

- 新增 `--context-pair-hidden-dim`；
- 新增全量 pair 开关 `--context-pair-comparator-loss-multiplier`；
- 新增 focused-only 开关 `--focused-pair-context-comparator-loss-multiplier`；
- focused-only comparator 只作用于 focused / boost pair，避免全量 same-context pair 成本过高；
- `_record_candidate_prediction_indices()` 增加按 record + candidate threshold + gate config 的缓存，不改变 threshold 候选集合和 gate 语义。

## 训练配置

```text
base_config = v128 leak-free focused training
context_pair_hidden_dim = 32
context_pair_comparator_loss_multiplier = 0.0
focused_pair_context_comparator_loss_multiplier = 2.5
focused_pair_row_indices_file = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json
focused_pair_training_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_training_row_indices.json
focused_pair_boost_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/focused_boost_train_row_indices.json
targeted_safe_positive_row_indices_file = BPC_future/results/gat_batch_impact_v123_leakfree_focused_selectors_20260622/optional_v121_train_targeted_safe_positive_row_indices.json
```

先尝试过全量 comparator：

```text
context_pair_comparator_loss_multiplier = 1.0
focused_pair_context_comparator_loss_multiplier = 0.0
```

该实验在 epoch 后 threshold search 之前没有及时给出完整可审计结果，计算反馈太慢，因此改成 focused-only comparator。

## 前 4 个 epoch

| epoch | local gate | accepted | ROI | ROI CI low | safe CI low | false-delay | false-safe | focused strict |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | true | 35 | 11.676 | 3.394 | 0.9011 | 0.00000 | 0.00000 | 61/78 = 0.7821 |
| 2 | true | 42 | 12.623 | 5.218 | 0.9162 | 0.00722 | 0.00722 | 73/78 = 0.9359 |
| 3 | true | 35 | 16.912 | 7.936 | 0.9011 | 0.00361 | 0.00361 | 73/78 = 0.9359 |
| 4 | true | 35 | 13.702 | 5.402 | 0.9011 | 0.00000 | 0.00000 | 74/78 = 0.9487 |

对比参考：

| run | focused strict | 说明 |
|---|---:|---|
| v125 selected epoch2 | 74/78 | local + global/scale kNN pass，ROI CI low 10.358 |
| v125 diagnostic epoch3 | 76/78 | focused 更好，但 false-delay 1.083% 超 1% |
| v128 isolated train-only focused | 71/78 | 负结果 |
| v130 focused comparator best | 74/78 | 只追平 v125 selected，ROI CI low 更低 |

## 判断

v130 说明：直接给 focused rows 增加 pair-context comparator BCE，不足以解决 focused gate。它能从 epoch1 的 61/78 拉到 74/78，但没有超过 v125，也没有接近 78/78。

当前更像是训练信号还没有把 comparator 的输出接入最终 focused gate 所依赖的 raw / admission / delay-risk 三个评分面。focused gate 仍由原 head 决定，comparator 只是训练辅助，不直接影响 admission score。下一步不应继续调大 comparator multiplier，而应考虑：

1. 让 comparator 表示通过 shared projection 回流到 candidate/batch heads；
2. 或新增一个 offline fused admission score 审计，但必须先证明它不改变 exact-safe boundary；
3. 同时保留 v130 的 threshold search 缓存，因为它不改变语义且改善训练反馈速度。

## Stage 状态

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
checkpoint_gate_pass = false
```

当前 blocker 不变：

- focused same-context pair gate 未达到 `78/78`；
- Stage 4 shadow / opt-in 未运行；
- 5/10 no-regression 与 20-task ROI 未绑定当前 checkpoint；
- GAT/kNN/OOD 不能提供 official lower bound 或 exact certificate。

## Exactness Boundary

本轮只运行离线训练和 per-epoch diagnostic checkpoint：

- 不运行 BPC / pricing / RMP；
- 不改变 pricing universe；
- 不改变 lower bound、certificate 或 exact closure；
- 不启用 production/default config；
- true-RC negative columns 必须保持 eventually reachable；
- final optimality proof 仍只能来自 exact pricing full closure。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m py_compile \
  BPC_future/learning/batch_impact_model.py \
  BPC_future/scripts/train_gat_batch_impact.py \
  BPC_future/tests/test_gat_batch_impact_model.py \
  BPC_future/tests/test_gat_batch_impact_training.py
```

通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/bin/python -m unittest \
  BPC_future.tests.test_gat_batch_impact_model \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_batch_impact_focused_pair_failures
```

结果：

```text
Ran 51 tests in 0.331s
OK
```
