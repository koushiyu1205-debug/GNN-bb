# 2026-06-23 BPC_future GAT Stage 3 v146 Path-feature Scale/Dropout 综合报告

## 结论

v146 在不删除 path token 的前提下，新增并启用了 path 分支弱化/正则化：

```text
path_token_vocab_size = 4096
path_feature_scale = 0.5
path_feature_dropout = 0.5
```

结果是一个 negative diagnostic：

- validation ROI 基本保住，接近 v140；
- 但 focused gate 没有关闭；
- focused strict pass 为 `74/78 = 0.9487`，低于 v140 的 `75/78 = 0.9615`；
- v145 no-path 修复的 3 个 v140 失败中，v146 又重新失败了同样的 3 个；
- 另新增一个 task50 random-wave shared-signature confounder 失败。

因此下一步不应继续做单纯 path 强度 sweep。当前主要 blocker 更像
context-action consequence / shared-signature confounder，而不是 path token 是否存在。

## Artifact

```text
v146_metrics =
  BPC_future/results/gat_batch_impact_training_v146_path_feature_dropout_scale_seed13_20260623/metrics.json

v146_model =
  BPC_future/results/gat_batch_impact_training_v146_path_feature_dropout_scale_seed13_20260623/model.pt

v146_training_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v146_path_feature_dropout_scale_seed13_zh.md

v146_failure_audit =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v146_path_feature_dropout_scale_20260623/summary.json

v146_failure_audit_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v146_path_feature_dropout_scale_pair_failure_audit_zh.md

v147_top_context_feature_contrast =
  BPC_future/results/gat_batch_impact_top_context_feature_contrast_v147_v146_failures_20260623/summary.json

v147_top_context_feature_contrast_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v147_v146_failure_top_context_feature_contrast_zh.md
```

## 实现变化

新增默认关闭的模型/训练参数：

```text
GATBatchImpactModel.path_feature_scale
GATBatchImpactModel.path_feature_dropout
train_gat_batch_impact.py --path-feature-scale
train_gat_batch_impact.py --path-feature-dropout
```

默认值：

```text
path_feature_scale = 1.0
path_feature_dropout = 0.0
```

因此旧 checkpoint / 旧训练命令行为不变。v146 只是 offline diagnostic ablation，不改变
solver、pricing、RMP、benchmark config 或 certificate path。

## v140 / v145 / v146 对比

| 指标 | v140 path full | v145 no path | v146 path scale/dropout |
|---|---:|---:|---:|
| path_token_vocab_size | 4096 | 0 | 4096 |
| path_feature_scale | 1.0 legacy | n/a | 0.5 |
| path_feature_dropout | 0.0 legacy | n/a | 0.5 |
| best_epoch | 5 | 3 | 4 |
| best_loss_epoch | 3 | 5 | 4 |
| validation accepted_batch_count | 35 | 35 | 35 |
| validation precision | 1.0000 | 1.0000 | 1.0000 |
| validation ROI | 19.6656 | 17.2735 | 19.5444 |
| validation ROI CI low | 10.6192 | 8.2428 | 10.4725 |
| validation safe_precision_ci_low | 0.9011 | 0.9011 | 0.9011 |
| validation false_safe_rate_union | 0.00722 | 0.00000 | 0.00722 |
| focused raw pass | 75/78 | 76/78 | 74/78 |
| focused admission pass | 76/78 | 73/78 | 75/78 |
| focused delay-risk pass | 76/78 | 73/78 | 76/78 |
| focused strict pass | 75/78 | 73/78 | 74/78 |
| checkpoint_gate_pass | false | false | false |
| stage4_candidate_ready | false | false | false |

v146 说明：弱化 path 可以保住全局 ROI，但不能解决 focused context-local ranking。
v145 说明：完全删除 path 可以修复 v140 的 3 个旧失败，但会引入更多新失败并降低 ROI。

## v146 Focused Failure

v146 focused gate：

```text
pair_count = 78
pair_pass_count = 74
raw_fail_count = 4
admission_fail_count = 3
delay_risk_fail_count = 2
strict_pair_pass_rate = 0.9487179487
diagnosis_counts = {
  mixed_margin_failure: 2,
  shared_signature_confounder: 2,
  pair_passes: 74
}
```

失败 pair：

| context | family | task | pair | raw | admission | delay | diagnosis |
|---|---|---:|---|---:|---:|---:|---|
| `b36178f6655c5f75` | greedy-anchor | 20 | `813>815` | -0.040962 | -0.045138 | -0.040267 | mixed_margin_failure |
| `84ae11479ed592d4` | greedy-anchor | 20 | `998>1001` | -0.019136 | -0.013289 | -0.007313 | mixed_margin_failure |
| `9f80ae35ea87da5b` | random-wave | 30 | `183>845` | -0.011394 | 0.053451 | 0.046111 | shared_signature_confounder |
| `9a2ca522ff49991c` | random-wave | 50 | `133>402` | -0.044089 | -0.000843 | 0.021232 | shared_signature_confounder |

与 v145 对比：

- v145 修复了 `813>815`、`998>1001`、`183>845`；
- v146 又失败了这三对；
- v146 同时修复了 v145 的 sector-wave / random-wave near-margin 新失败；
- 说明 path 分支不是纯坏信号，也不是纯好信号，它的作用取决于 context-local
  action consequence。

## Stage 4 状态

v146 不能进入 Stage 4：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
rejected_checkpoint_reasons = [
  admission_pair_pass_rate_below_threshold,
  delay_risk_pair_pass_rate_below_threshold,
  knn_ood_audit_missing,
  raw_pair_pass_rate_below_threshold,
  strict_pair_pass_rate_below_threshold
]
```

validation local deployment gate 通过不够。focused pair gate 未全过时，不能用高 ROI 或
高 precision 覆盖 context-local ranking failure。

## 下一步判断

继续调 `path_feature_scale` / `path_feature_dropout` 的收益有限。更合理的下一步：

1. 优先强化 context-local pairwise comparator / ranking head；
2. 不再把下一步主因归结为 tensor schema 完全缺失；
3. 若要继续 path 分支实验，应改成 context-conditioned path comparator，而不是全局 scale；
4. 只有 comparator/ranking 仍失败时，再回头补更细的 action-consequence feature。

v147 top-context feature contrast 对 v146 失败做了复审：

```text
failed_pair_count = 4
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
primary = visible_inputs_differ_but_model_still_misranks
recommended_next_step = tighten_context_local_pairwise_ranking_head
```

这说明 v146 的 4 个失败 pair 并不是正负样本在当前模型输入中完全不可分；更像是当前
candidate head 没有把已可见差异稳定转成同 context 排序优势。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
runs_rmp = false
production_ready = false
default_enabled = false
stage3_completed = false
stage4_candidate_ready = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

GAT/path-token/kNN/OOD 仍只能做 discovery ordering 或有限延迟 admission scheduling；
不能产生 official bound / certificate，也不能永久丢弃 true reduced-cost negative columns。
