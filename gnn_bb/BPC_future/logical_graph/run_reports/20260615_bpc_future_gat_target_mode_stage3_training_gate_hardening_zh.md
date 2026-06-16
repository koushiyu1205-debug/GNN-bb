# 2026-06-15 BPC_future GAT Target Mode Stage 3 训练硬门槛修正报告

> 2026-06-16 更新：本报告中的 `offline_stage3_candidate_ready=true` 已被
> `20260616_bpc_future_gat_target_mode_stage3_confidence_gate_fix_zh.md`
> 覆盖。新的硬口径要求 precision / ROI confidence lower bound 同时过线；
> 当前 v2 multiscale checkpoint 因 `safe_precision_ci_low` 和
> `accepted_batch_roi_ci_low` 不足，仍只能作为 diagnostic checkpoint，
> 不能作为 Stage 4 safe source。

## 结论

本轮根据目标计划中加硬后的训练要求，修正了 offline batch-impact trainer 的
checkpoint / threshold gate。训练阶段现在把 ROI 和精准率作为 admission policy 的硬约束，
而不是训练后附带报告项。

关键结论：

- 经过后续 family-specific delay fallback 修正和 kNN/OOD 重审计，Stage 3 offline
  candidate gate 已通过；
- 当前 v2 multiscale checkpoint 仍只能作为 diagnostic / shadow candidate artifact；
- 可以准备 Stage 4 default-off shadow / no-regression，但不能直接 opt-in production；
- 不声明 production ready、5/10 no-regression、20-task wall-time ROI 或 exact proof 改善。

## 2026-06-15 family fallback 与 kNN/OOD 更新

本报告初版把所有 missing accepted family 都视为 Stage 3 blocker。重新审计后发现这会误伤
一种合法情况：某个 family 在 validation holdout 中本来没有任何 ROI 达到硬门槛的 batch。
这种 family 不应被强行 high-priority，而应进入 family-specific delay fallback。

本轮新增区分：

```text
family_holdout_oracle_high_roi_families
family_holdout_missing_accepted_opportunity_families
family_specific_delay_fallback_families
```

在 v2 validation split 中：

```text
greedy-anchor max accepted ROI label = 0.4039181172847748
min accepted ROI hard threshold = 0.65
```

因此 greedy-anchor 没有 high-ROI oracle opportunity，被正确标记为：

```text
family_specific_delay_fallback_families = ['greedy-anchor']
```

random-wave 和 sector-wave 都存在 high-ROI oracle opportunity，并且当前 checkpoint 各接受一个
safe / high-ROI batch：

```text
random-wave accepted_batch_count = 1
random-wave accepted_batch_roi = 1.1059776544570923
sector-wave accepted_batch_count = 1
sector-wave accepted_batch_roi = 0.7734083533287048
```

重新运行 kNN/OOD audit 后：

```text
validation_candidate_ready = true
accepted_batch_count = 2
accepted_batch_rate = 0.02564102564102564
accepted_batch_roi = 0.9396930038928986
safe_precision = 1.0
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
production_block_reasons = []
```

注意：这只说明 Stage 3 offline gate 通过，不是 production ready。Stage 4 仍必须完成
default-off shadow、5/10 no-regression、certificate safety audit 和 20-task ROI A/B。

## 复读依据

本轮重新阅读并对齐：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 3 初版训练报告
- Stage 3 v2 多规模刷新报告
- Stage 4 scheduler preflight 报告
- `20260610_balanced60_vs_old_baseline_comparison.md`

主线仍是：

```text
Learning-guided discovery, exact-certified closure
```

GAT 只能排序、调度和有限延迟 true-RC negative；最终 certificate 仍必须来自当前
branch/cut/dual 下的 exact pricing full closure。

## 本次修改

- `BPC_future/scripts/train_gat_batch_impact.py`
  - `--min-family-holdout-accepted-roi` 默认不再是 `0.0`；
  - 默认值改为与总体 ROI 硬门槛一致：

```text
max(min_accepted_batch_roi,
    baseline_accepted_batch_roi + min_roi_margin_over_baseline)
```

  - epoch selection 先看本地 deployment gate，再比较 expected utility、accepted ROI、validation loss；
  - 新增 `best_loss_epoch`、`selected_validation_loss`、`selected_checkpoint_reason`、
    `rejected_checkpoint_reasons`，避免低 loss checkpoint 绕过 ROI / precision gate。

- `BPC_future/tests/test_gat_batch_impact_training.py`
  - 增加默认 family ROI gate 单测；
  - 增加 family ROI collapse 单测，证明总体 ROI 过线但某个 family 坍塌时不能通过本地 gate。

## 重新训练命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python BPC_future/scripts/train_gat_batch_impact.py --dataset-dir BPC_future/data/gat_batch_impact/v2_multiscale_20260615 --checkpoint-out BPC_future/data/gat_batch_impact/v2_multiscale_20260615/gat_batch_impact.pt --metrics-out BPC_future/results/gat_batch_impact_training_v2_multiscale_20260615/summary.json --report BPC_future/logical_graph/run_reports/20260615_bpc_future_gat_batch_impact_training_v2_multiscale_zh.md --epochs 2 --lr 1.0e-4 --device cpu --hidden-dim 24 --option-hidden-dim 24 --pair-edge-dim 24 --candidate-hidden-dim 24 --context-hidden-dim 16 --batch-hidden-dim 24 --impact-hidden-dim 24 --min-samples 200 --stage3-min-samples 200 --min-roi-positive-batches 20 --min-delay-candidates 20 --max-grad-norm 5.0
```

## 重新训练结果

```text
sample_count = 294
candidate_count = 4569
family_counts = {'greedy-anchor': 54, 'random-wave': 190, 'sector-wave': 50}
best_epoch = 1
best_loss_epoch = 2
best_loss_epoch_gate_pass = false
selected_validation_loss = 6.207449161089384
best_validation_loss = 5.05897759168576
nonfinite_skipped_update_rate = 0.0
checkpoint_gate_pass = false
stage4_candidate_ready = false
all_checks_pass = true
```

Validation deployment metrics：

```text
accepted_batch_count = 1
accepted_batch_rate = 0.01282051282051282
accepted_batch_roi = 1.1059776544570923
high_priority_precision = 1.0
safe_precision = 1.0
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
family_holdout_missing_accepted_families = ['greedy-anchor', 'sector-wave']
threshold_local_gate_pass = false
threshold_local_reject_reasons = [
  accepted_batch_rate_too_low,
  family_holdout_accepted_batch_missing
]
```

旧 Stage 4 blockers：

```text
accepted_batch_rate_too_low
family_holdout_accepted_batch_missing
knn_ood_audit_missing
knn_ood_holdout_audit_not_run
online_shadow_and_opt_in_ab_not_run
```

更新后，训练 summary 的本地 deployment gate 通过，剩余外部 blocker 是：

```text
knn_ood_audit_missing
```

但后续 `audit_gat_batch_impact_knn_ood.py` 已重跑并通过，因此 Stage 3 当前状态应按
kNN/OOD audit 报告判断为 offline candidate-ready。

## 判断

旧 v2 报告中的 kNN/OOD candidate-ready 结论曾经不够，因为它没有区分 family fallback
和真正漏放 high-ROI opportunity。本轮修正后，checkpoint 只在存在 high-ROI oracle
opportunity 的 family 上要求接受；无 high-ROI opportunity 的 family 必须 delay fallback。

这比之前更符合目标：

- high precision 不能掩盖 accepted coverage 太低；
- high ROI 不能掩盖某些存在 high-ROI opportunity 的 family 完全没有 accepted batch；
- 无 high-ROI opportunity 的 family 不能被硬推 HIGH_PRIORITY，必须 fallback 到 DELAY_QUEUE；
- low validation loss 不能替代 ROI / precision / family holdout；
- zero-FP / conservative checkpoint 没有足够放行量时仍然不能上线。

## Exactness Boundary

本次只修改 offline trainer、offline tests 和报告。

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
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_training
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile BPC_future/scripts/train_gat_batch_impact.py BPC_future/tests/test_gat_batch_impact_training.py
```

结果：

```text
Ran 4 tests in 0.112s
OK
py_compile: pass
```

## 下一步

进入 Stage 4 前置，但仍保持 default-off：

1. 保留 greedy-anchor 的 family-specific delay fallback 语义；
2. 实现/复核 default-off shadow logging，不改变 solver decision；
3. 跑 5/10 shadow no-regression；
4. 通过后才允许指定 20-task opt-in A/B；
5. final certificate 仍必须由 exact pricing full closure 产生。
