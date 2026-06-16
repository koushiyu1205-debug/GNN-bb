# 2026-06-15 BPC_future GAT Target Mode Stage 3 v2 多规模刷新报告

> 2026-06-16 更新：本报告的离线 gate 结论已被
> `20260616_bpc_future_gat_target_mode_stage3_confidence_gate_fix_zh.md`
> 进一步加硬。当前结论以 confidence lower-bound gate 为准：
> `stage4_candidate_ready=false`，`validation_candidate_ready=false`。

## 2026-06-15 硬门槛与 family fallback 修正

本报告原结论中的“batch-impact checkpoint 通过 kNN/OOD validation candidate gate”
已被后续 Stage 3 hardening 重新解释。原因是计划文件把训练目标进一步加硬后，
checkpoint 不能只看总体 validation ROI / precision，还必须同时满足：

- 存在 high-ROI oracle opportunity 的 family 必须有 accepted HIGH_PRIORITY；
- 不存在 high-ROI oracle opportunity 的 family 必须进入 family-specific delay fallback；
- accepted ROI / precision / false-safe / coverage 仍保持硬门槛。

重新运行 `train_gat_batch_impact.py` 后，默认 gate 已改为：

```text
min_family_holdout_accepted_roi
  = max(min_accepted_batch_roi,
        baseline_accepted_batch_roi + min_roi_margin_over_baseline)
```

第一次硬门槛重跑后发现 greedy-anchor / sector-wave missing accepted；继续审计标签后发现：

```text
greedy-anchor validation max accepted ROI label = 0.4039181172847748 < 0.65
sector-wave validation has high-ROI opportunity
random-wave validation has high-ROI opportunity
```

因此 greedy-anchor 应作为 delay fallback，而不是强行要求 accepted batch。修正 trainer
和 kNN/OOD audit 后，新的 v2 multiscale 结果为：

```text
validation local deployment gate = true
knn_ood validation_candidate_ready = true
stage4_candidate_ready = false
selected_checkpoint_reason =
  local_deployment_gate_passed_and_best_validation_loss
accepted_batch_count = 2
accepted_batch_rate = 0.02564102564102564
accepted_batch_roi = 0.9396930038928986
family_specific_delay_fallback_families = ['greedy-anchor']
family_holdout_missing_accepted_opportunity_families = []
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
production_block_reasons = []
```

因此，本报告下方的旧数值只能作为历史诊断记录；当前 Stage 3 状态按最新 hardening
报告和 kNN/OOD audit 报告判断：

```text
production_ready = false
stage4_candidate_ready = false
offline_stage3_candidate_ready = true
仍需 Stage 4 default-off shadow / 5-10 no-regression / 20-task ROI A/B
```

## 结论

本轮继续推进 Stage 3，并把离线 validation gate 从“greedy-anchor holdout
缺失”推进到“batch-impact checkpoint 通过 kNN/OOD validation candidate gate”。

仍未进入 Stage 4 online shadow / opt-in A/B；也不声明 production ready、
wall-time ROI、5/10 no-regression 或 20-task exact proof 改善。

核心变化：

1. 修复 std pooling 零方差反向传播问题，v2 训练
   `nonfinite_skipped_update_rate = 0.0`。
2. 将 admission calibration 从单阈值升级为：
   `family_local_batch_candidate`。
3. 训练 deployment metrics 与 kNN/OOD audit 的 accepted 口径对齐：
   batch 必须过 batch threshold，且 batch 内至少一个 candidate 过
   candidate threshold，并且没有 delay-candidate false positive。
4. kNN/OOD validation audit 通过：
   三个 major family 都有 accepted batch，false-safe 为 0。

## 复读依据

本轮重新阅读并对齐：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 / Stage 2 / Stage 3 既有报告
- v2 多规模 batch-impact dataset / training / kNN-OOD audit report
- `20260610_balanced60_vs_old_baseline_comparison.md`

主线仍是：

```text
Learning-guided discovery, exact-certified closure
```

GAT 只能排序、调度和延迟 true-RC negative；最终 optimality proof 必须由
exact pricing 在当前 branch/cut/dual 下对完整配置宇宙重新确认。

## 本次修改

- `BPC_future/scripts/train_gat_batch_impact.py`
  - 增加 family-local batch threshold 校准；
  - 保留 shared candidate threshold；
  - accepted metrics 加入 candidate sanity gate；
  - summary / checkpoint 输出 `batch_thresholds_by_family`。

- `BPC_future/scripts/audit_gat_batch_impact_knn_ood.py`
  - 读取 `batch_thresholds_by_family`；
  - 每条 decision record 记录实际 batch threshold；
  - kNN/OOD shell 仍只产生 `HIGH_PRIORITY` / `DELAY_QUEUE`，不运行 BPC/pricing/RMP。

- `BPC_future/tests/test_gat_batch_impact_training.py`
  - 增加 family-local batch threshold metrics 单测。

## v2 训练命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/train_gat_batch_impact.py --dataset-dir BPC_future/data/gat_batch_impact/v2_multiscale_20260615 --checkpoint-out BPC_future/data/gat_batch_impact/v2_multiscale_20260615/gat_batch_impact.pt --metrics-out BPC_future/results/gat_batch_impact_training_v2_multiscale_20260615/summary.json --report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_training_v2_multiscale_zh.md --epochs 2 --lr 1.0e-4 --device cpu --hidden-dim 24 --option-hidden-dim 24 --pair-edge-dim 24 --candidate-hidden-dim 24 --context-hidden-dim 16 --batch-hidden-dim 24 --impact-hidden-dim 24 --min-samples 200 --stage3-min-samples 200 --min-roi-positive-batches 20 --min-delay-candidates 20 --max-grad-norm 5.0
```

## 训练结果

```text
sample_count = 294
candidate_count = 4569
family_counts = {'greedy-anchor': 54, 'random-wave': 190, 'sector-wave': 50}
best_epoch = 1
nonfinite_skipped_update_rate = 0.0
checkpoint_gate_pass = false
stage4_candidate_ready = false
all_checks_pass = true
```

Selected thresholds：

```text
threshold_mode = family_local_batch_candidate
batch_threshold = 0.5396348834037781
candidate_threshold = 0.5431835651397705
batch_thresholds_by_family = {
  'greedy-anchor': 0.0,
  'random-wave': 0.5396348834037781,
  'sector-wave': 0.0
}
threshold_local_gate_pass = true
threshold_local_reject_reasons = []
```

Validation deployment metrics：

```text
accepted_batch_count = 14
accepted_batch_rate = 0.1794871794871795
accepted_batch_roi = 0.685879145216729
high_priority_precision = 1.0
safe_precision = 1.0
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
expected_trajectory_utility = 0.7323077166453004
family_holdout_missing_accepted_families = []
```

Family holdout：

```text
greedy-anchor accepted_batch_count = 1
greedy-anchor accepted_batch_roi = 0.024036092683672905
random-wave accepted_batch_count = 2
random-wave accepted_batch_roi = 0.6172637119889259
sector-wave accepted_batch_count = 11
sector-wave accepted_batch_roi = 0.7585222287611528
```

注意：训练集同一阈值的 accepted ROI 只有 `0.3842758924063099`，说明这仍是离线
validation candidate，不是 production readiness。下一阶段必须 shadow/opt-in A/B 验证。

## kNN/OOD Audit

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/audit_gat_batch_impact_knn_ood.py --dataset-dir BPC_future/data/gat_batch_impact/v2_multiscale_20260615 --checkpoint BPC_future/data/gat_batch_impact/v2_multiscale_20260615/gat_batch_impact.pt --training-summary BPC_future/results/gat_batch_impact_training_v2_multiscale_20260615/summary.json --output-dir BPC_future/results/gat_batch_impact_knn_ood_audit_v2_multiscale_20260615 --report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_knn_ood_audit_v2_multiscale_zh.md --device cpu --knn-k 3 --max-neighbor-delay-fraction 0.0 --safe-radius-quantile 1.0 --safe-radius-multiplier 1.0 --min-validation-high-priority 1 --min-safe-precision 0.85 --min-accepted-batch-count 1 --min-accepted-batch-rate 0.02 --min-accepted-batch-roi 0.65 --max-false-high-priority-on-delay 0.01 --max-validation-false-safe-rate 0.02 --min-coverage 0.0
```

结果：

```text
validation_candidate_ready = true
accepted_batch_count = 14
accepted_batch_rate = 0.1794871794871795
accepted_batch_roi = 0.685879145216729
safe_precision = 1.0
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
coverage = 1.0
production_block_reasons = []
```

Family result：

```text
greedy-anchor accepted_batch_count = 1
random-wave accepted_batch_count = 2
sector-wave accepted_batch_count = 11
missing_accepted_families = []
```

## 判断

Stage 3 的离线训练侧 blocker 已从：

```text
family_holdout_accepted_batch_missing
knn_ood_audit_missing
```

缩小为：

```text
online_shadow_and_opt_in_ab_not_run
```

也就是说，现在可以准备 Stage 4 shadow / opt-in A/B 的最小实现，但不能跳过
5/10 no-regression、20-task ROI 和 certificate safety audit。

## Exactness Boundary

本次只修改 learning / offline trainer / offline audit / report / tests。

```text
production_ready = false
default_enabled = false
pricing_oracle = false
certificate_source = false
official_bound_effect = false
can_permanently_discard_true_rc_negative = false
```

`DELAY_QUEUE` 仍只能有限延迟 true-RC negative；final certificate 仍必须来自 exact
pricing full closure。

## 验证

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_training BPC_future.tests.test_gat_batch_impact_knn_ood BPC_future.tests.test_gat_batch_impact_dataset BPC_future.tests.test_gat_batch_impact_model
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile BPC_future/scripts/train_gat_batch_impact.py BPC_future/scripts/audit_gat_batch_impact_knn_ood.py
```

结果：

```text
Ran 11 tests in 0.182s
OK
py_compile: pass
```

## 下一步

进入 Stage 4 前的最小任务：

1. 实现 default-off shadow-mode logging，不改变 solver decision；
2. 添加 certificate safety unit tests，确保 GAT/DELAY_QUEUE 不能产生 certificate；
3. 跑 5/10 no-regression shadow；
4. 只有 5/10 过后，再跑指定 20-task opt-in A/B。
