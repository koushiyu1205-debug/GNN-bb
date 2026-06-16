# BPC_future GAT Target Mode Stage 3 v11 ROI-CI Gate Hardening 报告

日期：2026-06-16

## 结论

本轮把训练阶段的目标从“文档写硬”推进到 trainer 实现层：

- checkpoint / threshold selection 现在先按 ROI confidence lower bound 和 baseline margin 排序；
- validation loss / F1 / recall 只能做 diagnostic 或 tie-breaker；
- trainer 默认 high-priority / safe precision gate 提高到 `0.90`；
- metrics 增加 random / best-RC / old-GAT baseline margin 字段；
- metrics 增加 hard reject reason taxonomy。

v11 使用 v10 dataset 重训后，validation local gate 过线，但 kNN/OOD safe shell 没过。
因此 v11 是 diagnostic hardening result，不是新的 Stage 4 safe-source。当前 Stage 4
仍应优先使用 v10 safe-source 做 A/B；v11 暴露的新问题是 ROI-CI 优先会让 safe shell
过窄，random-wave 覆盖不足。

## 修改文件

- `BPC_future/scripts/train_gat_batch_impact.py`
  - 新增 `CHECKPOINT_SELECTION_POLICY = deployment_gate_first_then_roi_ci_baseline_utility_loss`；
  - threshold feasible selection 改为优先 `accepted_batch_roi_ci_low`、
    `accepted_batch_roi_over_baseline_ci_low`、baseline margin；
  - checkpoint epoch selection 复用同一 ROI-CI key，validation loss 只做最后 tie-breaker；
  - 支持 `random_baseline_accepted_batch_roi`、`best_rc_baseline_accepted_batch_roi`、
    `old_gat_baseline_accepted_batch_roi`；
  - 输出 `baseline_roi_ci_high` 和 per-baseline ROI margin；
  - 输出 `hard_reject_reason_categories`。

- `BPC_future/tests/test_gat_batch_impact_training.py`
  - 新增 ROI-CI selection 单测；
  - 更新 checkpoint selection policy 断言；
  - 检查新 baseline margin / reject taxonomy 字段。

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
  - 记录 v11 hardening 结果和新 blocker。

## v11 Training

命令输出目录：

```text
BPC_future/results/gat_batch_impact_training_v11_roi_ci_gate_20260616
```

核心结果：

```text
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
best_epoch = 8
best_loss_epoch = 7
best_loss_epoch_gate_pass = true
checkpoint_gate_pass = false
stage4_candidate_ready = false
rejected_checkpoint_reasons = ['knn_ood_audit_missing']
```

validation deployment metrics：

```text
accepted_batch_count = 22
accepted_batch_rate = 0.215686
accepted_batch_roi = 13.735747
accepted_batch_roi_ci_low = 8.516215
accepted_batch_roi_over_baseline_ci_low = 8.066215
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.996177
safe_precision = 1.0
safe_precision_ci_low = 0.851340
false_high_priority_on_delay = 0
false_safe_rate_union = 0
```

family holdout：

```text
greedy-anchor accepted_batch_count = 0
greedy-anchor oracle_high_roi_count = 0
random-wave accepted_batch_count = 1
random-wave accepted_batch_roi = 1.105978
random-wave oracle_high_roi_count = 5
sector-wave accepted_batch_count = 21
sector-wave accepted_batch_roi = 14.337165
sector-wave oracle_high_roi_count = 22
```

## v11 KNN/OOD

输出目录：

```text
BPC_future/results/gat_batch_impact_knn_ood_audit_v11_roi_ci_gate_knn34_20260616
```

配置：

```text
knn_k = 3
max_neighbor_delay_fraction = 0.34
min_safe_precision = 0.90
min_safe_precision_ci_low = 0.85
min_accepted_batch_roi = 0.65
min_accepted_batch_roi_ci_low = 0.65
```

结果：

```text
validation_candidate_ready = false
validation_safety_ready = false
production_block_reasons =
  ['validation_safe_precision_ci_low_below_min', 'validation_candidate_not_ready']

accepted_batch_count = 21
accepted_batch_rate = 0.205882
accepted_batch_roi = 13.836773
accepted_batch_roi_ci_low = 8.366423
safe_precision = 1.0
safe_precision_ci_low = 0.845356
false_safe_rate_union = 0
```

family KNN/OOD 后：

```text
random-wave accepted_batch_count = 1
random-wave safe_precision_ci_low = 0.206543
sector-wave accepted_batch_count = 20
sector-wave safe_precision_ci_low = 0.838870
```

## 解释

v11 的 ROI-CI gate 符合“先证明回报率和精准率”的训练合同，但它牺牲了覆盖：

- v10 accepted `35` 个 batch，random-wave accepted `11` 个；
- v11 accepted `22` 个 batch，random-wave accepted `1` 个；
- KNN/OOD 后 v11 accepted `21` 个 batch，safe precision point estimate 仍为 `1.0`，
  但 CI lower bound 只有 `0.845356`，低于本轮 `0.85` gate。

因此不能为了更高 ROI point / CI 就直接替换 v10 safe-source。下一步应做
Pareto-aware / coverage-aware selection：在 precision / ROI / false-safe 不降级的前提下，
加入 accepted coverage、family opportunity capture、random-wave minimum accepted support，
避免 safe shell 过窄。

## Exactness Boundary

本轮只改 offline trainer 和测试，不运行 BPC / pricing / RMP，不改变 solver 默认配置。

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```

最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的
no-negative closure。

## Verification

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -m unittest \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_batch_impact_threshold_frontier \
  BPC_future.tests.test_gat_batch_impact_gate_shortfall \
  BPC_future.tests.test_gat_batch_impact_knn_ood \
  BPC_future.tests.test_gat_safe_source_export
```

结果：

```text
Ran 22 tests in 0.249s
OK
```

实跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python BPC_future/scripts/train_gat_batch_impact.py \
  --dataset-dir BPC_future/data/gat_batch_impact/v10_mixed_v8_plus_random_wave_task50_5751_20260616 \
  --checkpoint-out BPC_future/results/gat_batch_impact_training_v11_roi_ci_gate_20260616/model.pt \
  --metrics-out BPC_future/results/gat_batch_impact_training_v11_roi_ci_gate_20260616/metrics.json \
  --report BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v11_roi_ci_training_gate_zh.md \
  --epochs 8 \
  --seed 41 \
  --baseline-accepted-batch-roi 0.45 \
  --random-baseline-accepted-batch-roi 0.45 \
  --best-rc-baseline-accepted-batch-roi 0.45 \
  --old-gat-baseline-accepted-batch-roi 0.45 \
  --min-validation-high-priority-precision 0.90 \
  --min-validation-high-priority-precision-ci-low 0.85 \
  --min-validation-safe-precision 0.90 \
  --min-validation-safe-precision-ci-low 0.85 \
  --min-accepted-batch-roi 0.65 \
  --min-accepted-batch-roi-ci-low 0.65
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python BPC_future/scripts/audit_gat_batch_impact_knn_ood.py \
  --dataset-dir BPC_future/data/gat_batch_impact/v10_mixed_v8_plus_random_wave_task50_5751_20260616 \
  --checkpoint BPC_future/results/gat_batch_impact_training_v11_roi_ci_gate_20260616/model.pt \
  --training-summary BPC_future/results/gat_batch_impact_training_v11_roi_ci_gate_20260616/metrics.json \
  --output-dir BPC_future/results/gat_batch_impact_knn_ood_audit_v11_roi_ci_gate_knn34_20260616 \
  --report BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v11_roi_ci_knn_ood_zh.md \
  --knn-k 3 \
  --max-neighbor-delay-fraction 0.34 \
  --min-safe-precision 0.90 \
  --min-safe-precision-ci-low 0.85 \
  --min-accepted-batch-count 1 \
  --min-accepted-batch-rate 0.02 \
  --min-accepted-batch-roi 0.65 \
  --min-accepted-batch-roi-ci-low 0.65
```

## 下一步

1. 不降低 v11 的 precision / ROI / CI / false-safe gate。
2. 在 threshold / checkpoint selection 中加入 coverage-aware Pareto 约束，例如
   `family_high_roi_capture_rate_floor` 或 `random_wave_min_accepted_high_roi_count`。
3. 继续使用 v10 safe-source 做 Stage 4 opt-in A/B；v11 只作为 hard-gate 诊断和下一轮选择器改进依据。
