# 2026-06-23 BPC_future GAT Stage 3 v145 No-path-token 消融综合报告

## 结论

v145 关闭了 `PathTokenEncoder` 后重新训练同一批 v119/v140 训练数据。这个实验没有把
checkpoint 推到 Stage 4：`checkpoint_gate_pass=false`，
`stage4_candidate_ready=false`。

它的价值是定位失败机制，而不是替代当前模型：

- v140 剩余失败的 3 个 focused pair 在 v145 中全部修复；
- 但 v145 又产生了 5 个新的 focused pair 失败；
- focused strict pass 从 v140 的 `75/78 = 0.9615` 降到 v145 的
  `73/78 = 0.9359`；
- validation ROI 仍为正且很高，但低于 v140；
- 因此不能直接删除 path token，也不能盲目增强 path token。

当前判断：path-token 分支确实会误导部分 context-local ranking，但 path token 仍有全局
排序价值。下一步应做 path branch 的正则化、dropout 或 context-conditioned comparator，
而不是继续纯 multiplier sweep。

## Artifact

```text
v145_metrics =
  BPC_future/results/gat_batch_impact_training_v145_no_path_token_ablation_seed13_20260623/metrics.json

v145_model =
  BPC_future/results/gat_batch_impact_training_v145_no_path_token_ablation_seed13_20260623/model.pt

v145_train_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v145_no_path_token_ablation_seed13_zh.md

v145_failure_audit_summary =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v145_no_path_token_ablation_20260623/summary.json

v145_failure_audit_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v145_no_path_token_ablation_pair_failure_audit_zh.md
```

## Epoch 选择说明

v145 的训练配置仍使用：

```text
checkpoint_selection = deployment_gate_first_then_roi_ci_baseline_utility_loss
```

因此 checkpoint 不按 validation loss 单独选择。v145 中：

```text
best_epoch = 3
best_loss_epoch = 5
best_validation_loss = 4.704298
best_loss_epoch_gate_pass = false
```

第 5 个 epoch loss 最低，但没有通过 checkpoint gate，所以保存的诊断 checkpoint 是第 3
个 epoch。这个逻辑和 v108 中“为什么选 epoch 1 而不是 epoch 7/8”相同：epoch 7 是
loss 最低，但 gate 没过；当没有生产可用 checkpoint 时，脚本退回到诊断排序，优先看
deployment gate / reject reason / precision / ROI CI，再看 loss。

## v140 vs v145

| 指标 | v140 path-token enabled | v145 no-path-token |
|---|---:|---:|
| best_epoch | 5 | 3 |
| best_loss_epoch | 3 | 5 |
| path_token_vocab_size | 4096 | 0 |
| path_pair_vocab_size | 4096 | 0 |
| validation accepted_batch_count | 35 | 35 |
| validation precision | 1.0000 | 1.0000 |
| validation ROI | 19.6656 | 17.2735 |
| validation ROI CI low | 10.6192 | 8.2428 |
| validation safe_precision_ci_low | 0.9011 | 0.9011 |
| validation false_safe_rate_union | 0.00722 | 0.00000 |
| focused raw pass | 75/78 | 76/78 |
| focused admission pass | 76/78 | 73/78 |
| focused delay-risk pass | 76/78 | 73/78 |
| focused strict pass | 75/78 | 73/78 |
| checkpoint_gate_pass | false | false |
| stage4_candidate_ready | false | false |

v145 在 false-safe 方面更干净，但 focused strict gate 退步，ROI 也下降。因此它不能作为
Stage 4 起点。

## v142/v143 对 v145 的解释

v142 对 v140 剩余 3 个失败 pair 做 path-token 消融，结果：

```text
path_ablation_repairs_failure_count = 2 / 3
path_signal_helped_pair_count = 0
path_signal_hurt_pair_count = 3
primary = path_token_branch_hurts_this_pair
```

v143 再查 path-token 邻域标签，结果：

```text
negative_path_tokens_have_train_safe_conflict = 3 / 3 pairs
same_signature_cross_role_neighbor_count = 0
```

这解释了为什么 v145 能修复 v140 的 3 个剩余失败：原 path-token 分支确实把这些 pair
推错了。但 v145 又产生新失败，说明 path-token 不是纯噪声，不能整体删除。

## v145 Focused Failure Audit

v145 focused pair gate：

```text
pair_count = 78
pair_pass_count = 73
raw_fail_count = 2
admission_fail_count = 5
delay_risk_fail_count = 5
strict_pair_pass_rate = 0.935897
diagnosis_counts = {
  mixed_margin_failure: 2,
  near_margin_loss_tuning_candidate: 3,
  pair_passes: 73
}
```

失败 pair：

| context | family | task | pair | raw | admission | delay | diagnosis |
|---|---|---:|---|---:|---:|---:|---|
| `9eb0dc7839bf91ec` | random-wave | 20 | `795>792` | 0.000908 | -0.001503 | -0.003053 | near_margin_loss_tuning_candidate |
| `ddcb5387bef3bf63` | random-wave | 20 | `779>398` | -0.019545 | -0.011700 | -0.007227 | mixed_margin_failure |
| `be33b2560df0147a` | random-wave | 30 | `849>848` | 0.000315 | -0.000197 | -0.000510 | near_margin_loss_tuning_candidate |
| `4e481a6307fca228` | sector-wave | 20 | `411>412` | -0.010448 | -0.011309 | -0.011851 | mixed_margin_failure |
| `5a812898b6327d87` | sector-wave | 30 | `919>918` | 0.000147 | -0.000537 | -0.001013 | near_margin_loss_tuning_candidate |

3 个 near-margin 失败可以通过 loss/temperature/threshold 局部调参尝试修复；2 个
mixed-margin 失败说明只做 multiplier sweep 仍不可靠，需要补充 context-action
consequence 或改造 path branch。

## Stage 4 状态

v145 仍不是 Stage 4 candidate：

```text
rejected_checkpoint_reasons = [
  admission_pair_pass_rate_below_threshold,
  delay_risk_pair_pass_rate_below_threshold,
  knn_ood_audit_missing,
  raw_pair_pass_rate_below_threshold,
  strict_pair_pass_rate_below_threshold
]
```

其中 validation local deployment gate 是通过的：

```text
threshold_local_gate_pass = true
validation checkpoint_gate_reject_reasons = [knn_ood_audit_missing]
```

但总 checkpoint gate 必须同时满足 focused gate 和 kNN/OOD audit；不能用 validation
precision/ROI 掩盖 focused context-local ranking 失败。

## 下一步建议

1. 保留 path token，但不要直接增强其权重。
2. 做默认关闭的 path dropout / path branch regularization 训练实验。
3. 对 `negative_path_tokens_have_train_safe_conflict` 的 context 条件增加显式区分特征。
4. 对 v145 的 3 个 near-margin pair 可做小范围 loss/temperature 调整。
5. Stage 4 仍需等待 focused gate 全通过，再补 kNN/OOD audit。

## Exactness Boundary

```text
diagnostic_only = true
default_enabled = false
production_ready = false
stage3_completed = false
stage4_candidate_ready = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT/path-token/kNN/OOD 仍只能做 discovery ordering 或有限延迟 admission scheduling；
不能产生 official bound / certificate，也不能永久丢弃 true reduced-cost negative columns。
