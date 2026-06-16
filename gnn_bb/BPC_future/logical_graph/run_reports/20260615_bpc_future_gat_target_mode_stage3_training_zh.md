# 2026-06-15 BPC_future GAT Target Mode Stage 3 训练报告

## 结论

Stage 3 的 offline batch-impact trainer 已实现，并已在当前 `gat_batch_impact/v1` 数据集上完成一次 diagnostic training。

本阶段没有通过 Stage 3 acceptance gate，不能进入 Stage 4 shadow / opt-in A/B。主要原因：

- batch sample 数量 `68 < 200`，不满足计划中的 Stage 3 有效样本量下限；
- family 覆盖只有 `sector-wave`，缺少 `random-wave` 和 `greedy-anchor`；
- validation `safe_precision = 0.8125`，低于第一版 offline gate 的 `0.85`；
- validation `accepted_batch_roi = 0.3550`，低于目标 `>= 0.65`；
- 尚未做 kNN/OOD holdout；
- 尚未做 5/10 no-regression 或 20-task wall-time ROI A/B。

因此当前 checkpoint 只能作为 diagnostic artifact，不能用于 production gate、pricing certificate、official bound 或 benchmark 默认配置。

## 复读依据

本轮开始前已重新阅读：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- `BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_target_mode_stage1_model_structure_zh.md`
- `BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_target_mode_stage2_data_collection_zh.md`
- `BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_dataset_zh.md`
- `BPC_future/logical_graph/run_reports/20260610_balanced60_vs_old_baseline_comparison.md`

重新确认的主线仍是：

```text
Learning-guided discovery, exact-certified closure
```

GAT 只能改善列搜索和 admission scheduling；最终 proof 仍必须由 exact pricing 对当前 branch/cut/dual 下的完整配置宇宙做 no-negative closure。

## 新增/修改文件

- `BPC_future/scripts/train_gat_batch_impact.py`
  新增 offline batch-impact trainer。

- `BPC_future/tests/test_gat_batch_impact_training.py`
  覆盖训练 checkpoint contract、deployment metrics、hard gate blocker、非 production metadata。

- `BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_training_zh.md`
  训练脚本自动生成的 metrics report。

- `BPC_future/results/gat_batch_impact_training_20260615/summary.json`
  训练 summary。

- `BPC_future/data/gat_batch_impact/v1/gat_batch_impact.pt`
  diagnostic checkpoint，本地 artifact，仍 `production_ready=false`。

## Trainer 设计

训练目标不是 F1 或 recall，而是 deployment-facing admission scheduling：

- candidate-level `HIGH_PRIORITY`；
- candidate-level `DELAY_QUEUE risk`；
- batch-level ROI positive；
- objective progress；
- tail improved；
- bad mode switch；
- support changed good；
- `predicted_delta_v`；
- `predicted_barrier_slack`；
- `predicted_accepted_batch_roi`。

checkpoint selection 规则：

```text
先满足 deployment gate，再比较 expected utility / accepted ROI / validation loss。
```

deployment gate 包括：

- `high_priority_precision`
- `safe_precision`
- `accepted_batch_count`
- `accepted_batch_roi`
- `expected_trajectory_utility`
- `false_high_priority_on_delay`
- `false_safe_rate_union`
- `family_holdout_min_precision`
- `family_holdout_min_accepted_roi`
- Stage 3 sample count 下限
- kNN/OOD audit requirement

## 真实训练命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/train_gat_batch_impact.py --dataset-dir BPC_future/data/gat_batch_impact/v1 --checkpoint-out BPC_future/data/gat_batch_impact/v1/gat_batch_impact.pt --metrics-out BPC_future/results/gat_batch_impact_training_20260615/summary.json --report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_training_zh.md --epochs 3 --lr 1.0e-4 --device cpu --hidden-dim 32 --option-hidden-dim 32 --pair-edge-dim 32 --candidate-hidden-dim 32 --context-hidden-dim 24 --batch-hidden-dim 32 --impact-hidden-dim 32 --min-samples 1 --stage3-min-samples 200 --min-roi-positive-batches 1 --min-delay-candidates 1 --max-grad-norm 5.0
```

## 训练结果

```text
sample_count = 68
candidate_count = 1410
train_count = 52
validation_count = 16
family_counts = {'sector-wave': 68}
task_count_counts = {'20': 68}
checkpoint_selection = deployment_gate_first_then_utility_roi_loss
checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
all_checks_pass = true
```

Validation metrics：

```text
high_priority_precision = 1.0
safe_precision = 0.8125
accepted_batch_count = 16
accepted_batch_rate = 1.0
accepted_batch_roi = 0.3550373798934743
expected_trajectory_utility = 0.3925373798934743
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
family_holdout_min_precision = 0.8125
family_holdout_min_accepted_roi = 0.3550373798934743
```

Gate blockers：

```text
safe_precision_below_threshold_or_no_accepted_batches
accepted_batch_roi_below_baseline_margin
major_family_coverage_incomplete
stage3_effective_sample_count_below_200
knn_ood_audit_missing
knn_ood_holdout_audit_not_run
stage2_family_coverage_missing_random_wave_or_greedy_anchor
online_shadow_and_opt_in_ab_not_run
```

## 重大发现

真实训练首次运行时，GAT 参数在若干 optimizer step 后出现 non-finite。定位结果：

- graph tensors、candidate/context/batch tensors 本身是 finite；
- 单样本 forward 正常；
- 问题出现在小样本 GAT 多头训练的梯度/optimizer step 稳定性；
- trainer 已增加 `max_grad_norm` 和 non-finite gradient skip；
- 本次 diagnostic training 仍记录 `nonfinite_skipped_update_count = 6`。

这说明后续训练不能只看 validation metric，还必须把 numerical stability 写入 checkpoint readiness；若跳过 update 过多，checkpoint 不应进入 online A/B。

## Exactness Boundary

checkpoint metadata 仍保持：

```text
production_ready=false
default_enabled=false
pricing_oracle=false
certificate_source=false
official_bound_effect=false
can_permanently_discard_true_rc_negative=false
delay_queue_replaces_exact_pricing=false
```

因此：

- 模型不能替代 true reduced-cost；
- 模型不能产生 official lower bound；
- 模型不能参与 `CERTIFIED_NO_NEGATIVE`；
- 模型不能永久丢弃 true-RC negative；
- DELAY_QUEUE 只能延迟，最终仍必须 exact pricing closure。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_training BPC_future.tests.test_gat_batch_impact_dataset BPC_future.tests.test_gat_batch_impact_model
```

结果：

```text
Ran 7 tests in 0.130s
OK
```

`git diff --check` 已通过。

## 下一步

不要进入 Stage 4。下一步应回到 Stage 2/3 的数据和训练门槛：

1. 补 task20 `random-wave` 和 `greedy-anchor` same-context intervention rows；
2. 把 batch sample 数提升到 `>= 200`；
3. 增加 kNN/OOD holdout audit；
4. 调整 threshold/loss，使 `safe_precision >= 0.85`、`accepted_batch_roi >= 0.65`；
5. numerical stability 指标必须纳入 checkpoint reject reason；
6. 只有上述 gate 通过后，才允许做 Stage 4 shadow / opt-in A/B。
