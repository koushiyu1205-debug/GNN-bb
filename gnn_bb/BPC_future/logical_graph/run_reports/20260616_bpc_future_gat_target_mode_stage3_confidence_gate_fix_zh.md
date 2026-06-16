# 2026-06-16 BPC_future GAT Target Mode Stage 3 Confidence Gate 修正报告

## 结论

本轮按 `gat_bpc_future_target_mode_optimization_plan_zh.md` 中加硬后的训练目标，修正了 Stage 3 trainer 和 kNN/OOD audit 的 gate 语义：precision / ROI 不能只看 point estimate，必须同时报告并验收 confidence lower bound。

修正后，当前 v2 multiscale checkpoint 仍是 diagnostic-only，不能作为 Stage 4 safe source：

```text
stage4_candidate_ready = false
validation_candidate_ready = false
production_ready = false
default_enabled = false
```

关键原因是当前 validation 只接受了 2 个 batch。虽然 point estimate 看起来很好：

```text
high_priority_precision = 1.0
safe_precision = 1.0
accepted_batch_roi = 0.9396930038928986
false_safe_rate_union = 0.0
```

但 confidence lower bound 不足：

```text
safe_precision_ci_low = 0.3423719528896193
accepted_batch_roi_ci_low = 0.6137750887870789
min_safe_precision_ci_low = 0.85
min_accepted_batch_roi_ci_low = 0.65
```

因此不能把当前 checkpoint / kNN/OOD shell 标为可审计 safe source。Stage 4 admission scheduler 仍必须保持 safe-source gate：没有通过 Stage 3 confidence gate 的 safe source 时，只能 pass-through / audit，不能 mutating delay true-RC negative。

## 复读依据

本轮重新阅读并对齐：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 3 初版训练报告
- Stage 3 v2 多规模刷新报告
- Stage 3 训练硬门槛修正报告
- Stage 4 shadow no-regression 报告
- Stage 4 safe-source gate 修复报告

## 本次修改

### `BPC_future/scripts/train_gat_batch_impact.py`

新增训练 gate 字段：

- `high_priority_precision_ci_low`
- `safe_precision_ci_low`
- `accepted_batch_roi_ci_low`
- `accepted_batch_roi_over_baseline_ci_low`
- `confidence_z`

新增默认硬门槛：

- `min_validation_high_priority_precision_ci_low` 默认等于 `min_validation_high_priority_precision`
- `min_validation_safe_precision_ci_low` 默认等于 `min_validation_safe_precision`
- `min_accepted_batch_roi_ci_low` 默认等于 `max(min_accepted_batch_roi, baseline_accepted_batch_roi + min_roi_margin_over_baseline)`

新增 reject reasons：

- `high_priority_precision_ci_low_below_threshold_or_not_measurable`
- `safe_precision_ci_low_below_threshold_or_not_measurable`
- `accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable`

### `BPC_future/scripts/audit_gat_batch_impact_knn_ood.py`

kNN/OOD audit 同步输出并验收：

- `safe_precision_ci_low`
- `accepted_batch_roi_ci_low`
- `safe_precision_ci_low_met`
- `accepted_batch_roi_ci_low_met`

这保证 safe-source readiness 不再由小样本 point estimate 误判。

### 测试

新增/更新：

- 小样本 point precision = 1.0 但 Wilson lower bound 不过线时，threshold gate 必须 reject；
- training summary 必须包含 precision / ROI lower-bound 字段；
- kNN/OOD decision metrics 必须输出 lower-bound 字段。

## 重新训练与审计命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/train_gat_batch_impact.py \
  --dataset-dir BPC_future/data/gat_batch_impact/v2_multiscale_20260615 \
  --checkpoint-out BPC_future/data/gat_batch_impact/v2_multiscale_20260615/gat_batch_impact.pt \
  --metrics-out BPC_future/results/gat_batch_impact_training_v2_multiscale_20260615/summary.json \
  --report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_training_v2_multiscale_zh.md \
  --epochs 2 --lr 1.0e-4 --device cpu \
  --hidden-dim 24 --option-hidden-dim 24 --pair-edge-dim 24 \
  --candidate-hidden-dim 24 --context-hidden-dim 16 \
  --batch-hidden-dim 24 --impact-hidden-dim 24 \
  --min-samples 200 --stage3-min-samples 200 \
  --min-roi-positive-batches 20 --min-delay-candidates 20 \
  --max-grad-norm 5.0
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/audit_gat_batch_impact_knn_ood.py \
  --dataset-dir BPC_future/data/gat_batch_impact/v2_multiscale_20260615 \
  --checkpoint BPC_future/data/gat_batch_impact/v2_multiscale_20260615/gat_batch_impact.pt \
  --training-summary BPC_future/results/gat_batch_impact_training_v2_multiscale_20260615/summary.json \
  --output-dir BPC_future/results/gat_batch_impact_knn_ood_audit_v2_multiscale_20260615 \
  --report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_knn_ood_audit_v2_multiscale_zh.md \
  --device cpu --knn-k 3 \
  --max-neighbor-delay-fraction 0.0 \
  --safe-radius-quantile 1.0 \
  --safe-radius-multiplier 1.0 \
  --min-validation-high-priority 1 \
  --min-safe-precision 0.85 \
  --min-accepted-batch-count 1 \
  --min-accepted-batch-rate 0.02 \
  --min-accepted-batch-roi 0.65 \
  --max-false-high-priority-on-delay 0.01 \
  --max-validation-false-safe-rate 0.02 \
  --decision-scope validation \
  --threshold-grouping global
```

## 更新后结果

Training summary:

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
best_loss_epoch_gate_pass = false
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_utility_roi
rejected_checkpoint_reasons = [
  accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable,
  knn_ood_audit_missing,
  safe_precision_ci_low_below_threshold_or_not_measurable
]
```

kNN/OOD audit:

```text
validation_candidate_ready = false
validation_safety_ready = false
production_block_reasons = [
  validation_safe_precision_ci_low_below_min,
  validation_accepted_batch_roi_ci_low_below_min,
  validation_candidate_not_ready
]
```

## Exactness Boundary

本轮只修改 offline training / audit gate，不运行 BPC、pricing、RMP，也不改变 `manual_journey_reduced_cost()`、exact pricing universe、certificate 判定或 benchmark 默认配置。

GAT / kNN / OOD 仍然：

- 不是 pricing oracle；
- 不能产生 official lower bound；
- 不能产生 certificate；
- 不能永久丢弃 true-RC negative；
- 只能在通过 Stage 3 confidence gate 与 Stage 4 no-regression / ROI gate 后，作为 opt-in admission safe source。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_gat_batch_impact_training \
BPC_future.tests.test_gat_batch_impact_knn_ood
```

结果：

```text
Ran 9 tests in 1.172s
OK
```

## 下一步

当前 Stage 3/4 不应继续打开 mutating admission。下一步应补充更多 same-context intervention 样本，或者调整 threshold / family-specific policy，使 accepted batch count 和 confidence lower bound 同时过线。只有 training summary 与 kNN/OOD audit 都给出 `validation_candidate_ready=true`，才允许重新进入 Stage 4 safe-source opt-in no-regression。
