# 2026-06-23 BPC_future GAT Stage 3 v150/v151 train-only analog boost 综合报告

## 结论

v150 是一次有价值的 Stage 3 诊断推进，但还没有通过 Stage 3，不能进入
Stage 4。

本轮在 v148 context-conditioned path gate 的基础上，只用 validation focused
failure row 作为查询，挖掘 train split 中的相似正负对，并把 train-only analog
rows 加入 focused-pair boost selector。这个流程没有把 validation gate rows
写入训练：

```text
validation_failure_rows = [183, 767, 768, 844, 845]
validation_leakage_row_indices = []
combined_boost_validation_leakage_row_indices = []
all_analog_rows_train = true
all_combined_boost_rows_train = true
```

结果是一个明确的 tradeoff：

- v150 修复了 v148 的 3 个 random-wave focused failures；
- focused strict 从 `75/78` 提升到 `76/78`；
- 但 greedy-anchor `b36178f6655c5f75` 回归出 2 个 failed pair；
- validation ROI / safety 仍然强，但略低于 v148；
- focused gate 仍要求 `78/78`，因此 Stage 4 继续 blocked。

机器结论保持：

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
diagnostic_only = true
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 复读依据

本轮重新对齐：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 3 初版训练报告
- Stage 3 training gate hardening 报告
- Stage 4 v53 post-v51 individual follow-up 综合报告
- v148 path context gate synthesis
- v149 v148 failure top-context feature contrast

主线仍是：

```text
Learning-guided discovery, exact-certified closure
```

GAT / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission
scheduling；final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing
对完整配置宇宙的 exhaustive no-negative closure。

## Artifact

```text
v150_analog_summary =
  BPC_future/results/gat_batch_impact_v150_v148_train_only_failure_analogs_20260623/summary.json

v150_boost_selector =
  BPC_future/results/gat_batch_impact_v150_v148_train_only_failure_analogs_20260623/train_only_combined_boost_row_indices.json

v150_metrics =
  BPC_future/results/gat_batch_impact_training_v150_v148_trainonly_analog_boost_path_context_gate_seed13_20260623/metrics.json

v150_training_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v150_v148_trainonly_analog_boost_path_context_gate_seed13_zh.md

v150_failure_audit =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v150_v148_trainonly_analog_boost_path_context_gate_20260623/summary.json

v150_failure_audit_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v150_v148_trainonly_analog_boost_path_context_gate_pair_failure_audit_zh.md

v151_top_context_feature_contrast =
  BPC_future/results/gat_batch_impact_top_context_feature_contrast_v151_v150_failures_20260623/summary.json

v151_top_context_feature_contrast_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v151_v150_failure_top_context_feature_contrast_zh.md
```

## Train-only Analog Mining

v150 的 analog mining 输入来自 v148 focused failure rows：

| v148 failed pair | family | task | diagnosis |
|---|---|---:|---|
| `768>767` | random-wave | 20 | deep_structural_score_gap |
| `183>845` | random-wave | 30 | deep_structural_score_gap |
| `844>845` | random-wave | 30 | mixed_margin_failure |

挖掘结果：

```text
failed_pair_count = 3
failure_split_counts = {'validation_gate_only': 3}
train_pair_universe_count = 63
analog_pair_count = 36
analog_row_index_count = 26
existing_boost_row_index_count = 44
combined_boost_row_index_count = 48
new_analog_row_index_count = 4
new_row_indices_beyond_existing_boost = [133, 402, 810, 811]
```

这些新增行只用于 training-only focused-pair boost，不改变 validation / gate row。
因此 v150 的训练是合法的 diagnostic 训练，不是 validation leakage。

## v148 / v150 对比

| 指标 | v148 | v150 | 变化 |
|---|---:|---:|---:|
| best_epoch | 4 | 5 | - |
| best_loss_epoch | 4 | 3 | - |
| validation accepted | 35 | 35 | 0 |
| accepted ROI | 19.540643 | 18.789281 | -0.751362 |
| accepted ROI CI-low | 10.467926 | 9.691910 | -0.776016 |
| high-priority precision | 0.996176 | 0.996988 | +0.000812 |
| high-priority CI-low | 0.986165 | 0.989085 | +0.002920 |
| safe precision | 1.000000 | 1.000000 | 0 |
| safe precision CI-low | 0.901096 | 0.901096 | 0 |
| false high-priority on delay | 0.007220 | 0.007220 | 0 |
| false-safe union | 0.007220 | 0.007220 | 0 |
| focused strict pass | 75/78 | 76/78 | +1 pair |
| checkpoint_gate_pass | false | false | unchanged |
| stage4_candidate_ready | false | false | unchanged |

v150 的 selected checkpoint reason 仍是：

```text
local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
```

但最终 checkpoint gate 仍失败：

```text
rejected_checkpoint_reasons = [
  admission_pair_pass_rate_below_threshold,
  delay_risk_pair_pass_rate_below_threshold,
  knn_ood_audit_missing,
  raw_pair_pass_rate_below_threshold,
  strict_pair_pass_rate_below_threshold
]
```

## Focused Failure 转移

v148 剩余失败集中在 random-wave：

| context | family | task | pair | raw | admission | delay-risk | diagnosis |
|---|---|---:|---|---:|---:|---:|---|
| `62c86745ed2b3aaa` | random-wave | 20 | `768>767` | -0.042223 | -0.002428 | -0.104074 | deep_structural_score_gap |
| `9f80ae35ea87da5b` | random-wave | 30 | `183>845` | -0.060492 | -0.076350 | -0.059923 | deep_structural_score_gap |
| `9f80ae35ea87da5b` | random-wave | 30 | `844>845` | -0.042733 | -0.038630 | -0.014343 | mixed_margin_failure |

v150 后，这 3 个 random-wave pair 已通过，但 greedy-anchor `b361` 回归：

| context | family | task | pair | raw | admission | delay-risk | diagnosis |
|---|---|---:|---|---:|---:|---:|---|
| `b36178f6655c5f75` | greedy-anchor | 20 | `813>814` | -0.036538 | -0.024236 | -0.015176 | mixed_margin_failure |
| `b36178f6655c5f75` | greedy-anchor | 20 | `813>815` | -0.010646 | -0.004198 | -0.000282 | mixed_margin_failure |

这说明 v150 的 train-only analog boost 方向是有效但过于单向：它把 random-wave
deep failures 拉正了，却把之前已通过的 greedy `b361` 推回失败区。

## v151 Feature Contrast

v151 对 v150 failure contexts 做 top-context feature contrast：

```text
failed_pair_count = 2
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
failed_context_feature_drift_pair_count = 0
deep_failed_pair_count = 0
primary = visible_inputs_differ_but_model_still_misranks
recommended_next_step = tighten_context_local_pairwise_ranking_head
```

可见输入仍然存在：

```text
candidate_path_token_tensor_present = true
candidate_path_token_row_coverage = 1.0
candidate_feature_dim = 59
context_feature_dim = 26
batch_feature_dim = 18
trace_scalar_row_coverage = 1.0
slack_scalar_row_coverage = 1.0
per_candidate_branch_cut_interaction_present = true
```

因此当前主要 blocker 不是 schema 完全缺字段，也不是 validation 输入碰撞，而是
context-local pairwise ranking 在不同 family 之间不稳定。

## 判断

1. v150 是正向诊断，不是 Stage 4 checkpoint。
   它把 focused strict 从 `75/78` 提到 `76/78`，并修复 random-wave deep failures；
   但 `78/78` 硬门槛仍未通过。

2. 单纯继续扩大 random-wave analog boost 风险较高。
   现有结果已经显示 family 间跷跷板：random-wave 修复会牺牲 greedy `b361`。

3. 下一步不应 blind multiplier sweep。
   v151 说明输入可见且无 collision；继续只调 loss multiplier 可能继续在
   random-wave / greedy-anchor 之间摆动。

4. kNN/OOD 不能用来遮盖 focused gate failure。
   当前 focused gate 仍失败，kNN/OOD 即使补跑也只能审计 safety shell，不能让
   一个 context-local ranking 失败的 checkpoint 进入 Stage 4。

## 下一步

下一轮 Stage 3 修复应同时保护两个 frontier：

- 保留 v150 已修复的 random-wave `62c` / `9f80`；
- 重新保护 greedy `b361` 的 `813>814`、`813>815`。

更具体地，应优先做 cross-family stability repair：

1. 挖掘 v150 剩余失败的 train-only greedy analog；
2. 把 random-wave 修复 analog 与 greedy protection analog 合并为 balanced selector；
3. 在训练损失中避免单一 family analog 过度主导；
4. 或实现更直接的 context-local pair-delta ranking head，使同 context positive >
   negative 的约束不依赖单个 family 的重复采样权重。

不建议：

- 降低 focused pair gate；
- 降低 precision / ROI / CI / false-safe gate；
- 用 kNN/OOD 过滤掉 focused failures；
- 重新启用此前 v130/v131/v134 已证明无效的 context pair comparator 作为默认融合路径；
- 只因为 validation loss 更低而切换 epoch。

## Exactness Boundary

本轮只运行 offline mining、offline GAT training 和 offline audits：

```text
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

GAT 仍只能改变 discovery / ordering / finite-delay scheduling；所有进入 RMP 的列
仍必须 true-RC verified；final certificate 仍必须由 exact pricing full closure
产生。
