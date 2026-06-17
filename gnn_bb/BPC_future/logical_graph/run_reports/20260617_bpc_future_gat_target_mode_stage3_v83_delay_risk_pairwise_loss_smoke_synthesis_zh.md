# 2026-06-17 BPC_future GAT Stage 3 v83 Delay-risk Pairwise Loss Smoke 综合报告

## 结论

本轮按 v78 的结论实现了独立的同 context delay-risk pairwise loss，并跑了两个隔离 smoke：

- v79：`pairwise_delay_risk_contrast_loss_multiplier = 1.0`
- v81：`pairwise_delay_risk_contrast_loss_multiplier = 3.0`

新 loss 方向有效，但单纯加权不能解决 Stage 3 blocker。

v79 把 v77 的 focused `delay_risk_pair_pass_rate` 从 `0.0` 提到 `0.5`，说明 delay-risk head 可以被同 context 监督拉动；但 focused gate 仍失败。v81 进一步加权后，validation false-delay 压到 `0.0`，但 accepted coverage 和 family coverage 坍缩，focused raw/admission ranking 也从 `1.0` 回退到 `0.75`。这说明下一步不能继续盲目增加 delay-risk 权重，而要把 focused hard-negative pair 作为固定 regression tranche / model-selection hard gate，并补更明确的 risk head 监督或结构。

## 代码改动

`BPC_future/scripts/train_gat_batch_impact.py` 新增：

- CLI / dataclass 参数：
  `--pairwise-delay-risk-contrast-loss-multiplier`
- `loss_options` 字段：
  `pairwise_delay_risk_contrast_loss_multiplier`
- `_pairwise_loss_enabled()` 启用条件；
- `_pairwise_delay_risk_contrast_loss()`：
  要求 higher-ROI safe candidate 的 delay-risk logit 低于 lower-ROI delay / hard-negative candidate；
- checkpoint `training_contract` 和训练报告机器字段写出该 multiplier。

`BPC_future/tests/test_gat_batch_impact_training.py` 新增：

- loss option 字段检查；
- fake-model 单测：candidate head 已分开但 delay-risk 方向错时，新 loss 必须产生正损失；
- checkpoint contract 中该字段存在性检查。

## v79 结果

```text
checkpoint = BPC_future/results/gat_batch_impact_training_v79_v75_delay_risk_pairwise_smoke_20260617/gat_batch_impact.pt
metrics = BPC_future/results/gat_batch_impact_training_v79_v75_delay_risk_pairwise_smoke_20260617/metrics.json
training_report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v79_v75_delay_risk_pairwise_training_smoke_zh.md
focused_report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v80_v79_delay_risk_pairwise_focused_pair_gate_zh.md
pairwise_delay_risk_contrast_loss_multiplier = 1.0
checkpoint_gate_pass = false
stage4_candidate_ready = false
```

validation selected metrics：

```text
accepted_batch_count = 37
accepted_batch_roi = 1.5677298062254448
accepted_batch_roi_ci_low = 0.03792591292409453
safe_precision = 1.0
safe_precision_ci_low = 0.9059390425448562
high_priority_precision = 0.998914223669924
false_high_priority_on_delay = 0.0070921985815602835
false_safe_rate_union = 0.0070921985815602835
family_holdout_min_accepted_roi = 0.09050442464649677
rejected_checkpoint_reasons =
  ['accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable',
   'family_holdout_accepted_roi_below_threshold',
   'knn_ood_audit_missing']
```

focused pair gate：

```text
raw_pair_pass_rate = 1.0
admission_pair_pass_rate = 1.0
delay_risk_pair_pass_rate = 0.5
strict_pair_pass_rate = 0.5
primary = delay_risk_head_context_ranking_failure
focused_pair_gate_pass = false
```

对比 v77，v79 是真实进步：candidate ranking 没丢，delay-risk 从 0/4 变成 2/4。但剩余两个 pair 仍失败，不能进入 Stage 4。

## v81 结果

```text
checkpoint = BPC_future/results/gat_batch_impact_training_v81_v75_delay_risk_pairwise_w3_smoke_20260617/gat_batch_impact.pt
metrics = BPC_future/results/gat_batch_impact_training_v81_v75_delay_risk_pairwise_w3_smoke_20260617/metrics.json
training_report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v81_v75_delay_risk_pairwise_w3_training_smoke_zh.md
focused_report = BPC_future/logical_graph/run_reports/20260617_bpc_future_gat_target_mode_stage3_v82_v81_delay_risk_pairwise_w3_focused_pair_gate_zh.md
pairwise_delay_risk_contrast_loss_multiplier = 3.0
checkpoint_gate_pass = false
stage4_candidate_ready = false
```

validation selected metrics：

```text
accepted_batch_count = 14
accepted_batch_roi = 0.6534084230661392
accepted_batch_roi_ci_low = 0.33242751911858426
safe_precision = 1.0
safe_precision_ci_low = 0.7846829880728186
high_priority_precision = 1.0
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
family_holdout_missing_accepted_families = ['greedy-anchor', 'random-wave']
```

focused pair gate：

```text
raw_pair_pass_rate = 0.75
admission_pair_pass_rate = 0.75
delay_risk_pair_pass_rate = 0.25
strict_pair_pass_rate = 0.25
primary = candidate_head_context_ranking_failure
focused_pair_gate_pass = false
```

v81 是负结果：更大的 delay-risk 权重让 false-delay 点估计归零，但把模型推回低 coverage / narrow shell，并破坏了 v76/v79 已经修复的部分 candidate ranking。

## 横向对比

| version | delay-risk pair weight | accepted | false-delay | raw/admission pair | delay-risk pair | strict pair | 判断 |
|---|---:|---:|---:|---:|---:|---:|---|
| v77 / v76 | 0.0 | 18 | 0.0 | 1.0 / 1.0 | 0.0 | 0.0 | path-token 修 candidate head，但 risk head 错 |
| v80 / v79 | 1.0 | 37 | 0.0071 | 1.0 / 1.0 | 0.5 | 0.5 | 方向有效，但不过 gate |
| v82 / v81 | 3.0 | 14 | 0.0 | 0.75 / 0.75 | 0.25 | 0.25 | 权重过强，coverage 与 candidate ranking 回退 |

## 新理解

1. v75 path-token/slack 表示仍应保留。它让 focused raw/admission ranking 能到 `1.0`，这个信号没有被推翻。
2. delay-risk pairwise 监督方向正确，但必须谨慎。weight=1.0 有局部改善；weight=3.0 变成窄安全壳。
3. 当前 failure 不是单一 loss multiplier 能解。模型需要更明确地区分：
   - candidate head 的 high-ROI action score；
   - delay-risk head 的 tail / retry / bad-mode risk；
   - batch head 的 ROI / family coverage。
4. Stage 3 checkpoint selection 应把 focused strict pair gate 纳入硬 gate。否则 global metrics 可能掩盖 v77/v80/v82 这种 context-local 失败。

## 下一步

1. 保留 `pairwise_delay_risk_contrast_loss_multiplier`，但不要简单继续增大权重；
2. 用 v79 的 w=1.0 作为当前 delay-risk loss smoke baseline；
3. 把 v77/v80/v82 的 4 个 focused pair 固化成 regression tranche，并在训练后自动运行 focused gate；
4. 下一版训练优先尝试：
   - delay-risk pair loss weight 约束在 `0.5 - 1.5`；
   - 开启 `hard_roi_safe_delay_loss_multiplier` 和 `hard_roi_negative_delay_loss_multiplier` 做样本内 head 校准；
   - 保持 candidate pair loss，不让 delay-risk 权重压坏 raw/admission ranking；
   - 对 batch ROI head 增加同 context positive > negative 约束或更强 ROI regression；
5. 只有 focused strict gate、threshold frontier、family holdout、kNN/OOD 都过后，才允许重新考虑 Stage 4 shadow / opt-in A/B。

## Exactness Boundary

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
stage5_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

本轮只改离线训练 loss 和 diagnostic audit，不改 solver、pricing、RMP、benchmark config 或 certificate path。GAT 仍只能做 discovery / ordering / finite-delay admission scheduling；最终 proof 仍必须由当前 branch/cut/dual 下 exact pricing 对完整配置宇宙做 exhaustive no-negative closure。

## Verification

```text
py_compile train_gat_batch_impact.py + test_gat_batch_impact_training.py = pass
unittest BPC_future.tests.test_gat_batch_impact_training = 24 tests OK
v79 delay-risk pairwise smoke training = pass
v80 focused pair gate audit = pass, gate failed as diagnostic
v81 w=3 delay-risk pairwise smoke training = pass
v82 focused pair gate audit = pass, gate failed as diagnostic
```
