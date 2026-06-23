# 2026-06-23 BPC_future GAT Stage 3 v148 Context-conditioned Path Gate 综合报告

## 结论

v148 是一次正向但未过门的 Stage 3 诊断实验。

本轮在 v146 之后新增默认关闭的 context-conditioned path gate：

```text
path_token_vocab_size = 4096
path_feature_scale = 1.0
path_feature_dropout = 0.2
path_context_gate_hidden_dim = 16
```

它验证了 v145/v146 的核心判断：path token 不能全删，也不能全局缩放。按当前 RMP
context 给 path embedding 加 gate 后：

- v146 中失败的 greedy `b361 / 813>815`、`84ae / 998>1001` 被修复；
- validation ROI / ROI CI-low 基本保持在 v140/v146 水平；
- focused strict 从 v146 的 `74/78` 回到 `75/78`；
- 但剩余 3 个 random-wave pair 仍失败，且 2 个是 deep structural score gap；
- 因此 v148 仍不能进入 Stage 4。

## Artifact

```text
v148_metrics =
  BPC_future/results/gat_batch_impact_training_v148_path_context_gate_seed13_20260623/metrics.json

v148_model =
  BPC_future/results/gat_batch_impact_training_v148_path_context_gate_seed13_20260623/model.pt

v148_training_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v148_path_context_gate_seed13_zh.md

v148_failure_audit =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v148_path_context_gate_20260623/summary.json

v148_failure_audit_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v148_path_context_gate_pair_failure_audit_zh.md

v149_top_context_feature_contrast =
  BPC_future/results/gat_batch_impact_top_context_feature_contrast_v149_v148_failures_20260623/summary.json

v149_top_context_feature_contrast_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v149_v148_failure_top_context_feature_contrast_zh.md
```

## 实现变化

新增默认关闭参数：

```text
GATBatchImpactModel.path_context_gate_hidden_dim
train_gat_batch_impact.py --path-context-gate-hidden-dim
```

默认值为 `0`，不创建 gate，不改变旧模型/旧命令行为。启用后，模型在 path-token
embedding 拼入 candidate encoder 前，用当前 context embedding 生成逐维 sigmoid gate。
这只影响 offline GAT 训练/诊断，不触碰 BPC、pricing、RMP、final judge 或 benchmark 默认配置。

## v140 / v146 / v148 对比

| 指标 | v140 path full | v146 path scale/dropout | v148 context path gate |
|---|---:|---:|---:|
| path_token_vocab_size | 4096 | 4096 | 4096 |
| path_feature_scale | 1.0 legacy | 0.5 | 1.0 |
| path_feature_dropout | 0.0 legacy | 0.5 | 0.2 |
| path_context_gate_hidden_dim | 0 legacy | 0 | 16 |
| best_epoch | 5 | 4 | 4 |
| validation accepted_batch_count | 35 | 35 | 35 |
| validation precision | 1.0000 | 1.0000 | 1.0000 |
| validation ROI | 19.6656 | 19.5444 | 19.5406 |
| validation ROI CI low | 10.6192 | 10.4725 | 10.4679 |
| validation safe_precision_ci_low | 0.9011 | 0.9011 | 0.9011 |
| validation false_safe_rate_union | 0.00722 | 0.00722 | 0.00722 |
| focused raw pass | 75/78 | 74/78 | 75/78 |
| focused admission pass | 76/78 | 75/78 | 75/78 |
| focused delay-risk pass | 76/78 | 76/78 | 75/78 |
| focused strict pass | 75/78 | 74/78 | 75/78 |
| checkpoint_gate_pass | false | false | false |
| stage4_candidate_ready | false | false | false |

v148 的收益不是总 pass count 大幅提升，而是失败类型发生了有意义转移：

- greedy path-token 误导 pair 被修复；
- 剩余失败集中到 random-wave task20/task30；
- 下一步可以更窄地针对 random-wave deep misranking，而不是继续泛化地调 path 分支。

## v148 Focused Failure

```text
pair_count = 78
pair_pass_count = 75
raw_fail_count = 3
admission_fail_count = 3
delay_risk_fail_count = 3
strict_pair_pass_rate = 0.961538
diagnosis_counts = {
  deep_structural_score_gap: 2,
  mixed_margin_failure: 1,
  pair_passes: 75
}
```

失败 pair：

| context | family | task | pair | raw | admission | delay | diagnosis |
|---|---|---:|---|---:|---:|---:|---|
| `62c86745ed2b3aaa` | random-wave | 20 | `768>767` | -0.042223 | -0.002428 | -0.104074 | deep_structural_score_gap |
| `9f80ae35ea87da5b` | random-wave | 30 | `183>845` | -0.060492 | -0.076350 | -0.059923 | deep_structural_score_gap |
| `9f80ae35ea87da5b` | random-wave | 30 | `844>845` | -0.042733 | -0.038630 | -0.014343 | mixed_margin_failure |

其中 `9f80` 仍是关键 blocker：同一 negative row `845` 同时压过两个 positive row，
包括一个 ROI 极高的 `844`。这不再像单纯 path 信号误导，而是 random-wave context-local
action consequence 仍没被当前 candidate/admission heads 学稳。

## v149 Feature Contrast

v149 对 v148 剩余失败做 top-context feature contrast：

```text
failed_pair_count = 3
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
deep_failed_pair_count = 2
primary = visible_inputs_differ_but_model_still_misranks
recommended_next_step = tighten_context_local_pairwise_ranking_head
```

解释：

- 剩余失败不是正负样本在当前输入中完全碰撞；
- path token、trace scalar、slack scalar 都存在；
- 模型仍把可见差异排错，尤其 random-wave deep failures；
- 下一步应针对 random-wave context-local ranking 做训练/结构修复，而不是再扩大 path gate。

## Stage 4 状态

v148 仍不是 Stage 4 candidate：

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

focused gate 未达到 `78/78` 前，不应运行或绑定 kNN/OOD safe source；即使 kNN/OOD 通过，
也不能覆盖 focused context-local ranking failure。

## 下一步建议

1. 保留 `path_context_gate_hidden_dim` 作为正向结构开关；
2. 不再继续全局 path scale/dropout sweep；
3. 针对 `62c` 和 `9f80` 做 train-only random-wave hard-context analog mining；
4. 或将 focused pair 的 raw/admission/delay 三个头共享一个更直接的 context-local
   pair-delta ranking target；
5. 若继续训练，应记录 per-epoch focused gate 明细，避免只看到 selected checkpoint。

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
