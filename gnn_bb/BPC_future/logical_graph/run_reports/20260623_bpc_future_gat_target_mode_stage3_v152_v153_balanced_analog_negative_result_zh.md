# 2026-06-23 BPC_future GAT Stage 3 v152/v153 balanced analog boost 负结果报告

## 结论

v152 证明了一个重要负结果：继续用 train-only failure analog boost 做逐点修补，会在
focused gate 上形成 family/context 间的循环，而不是稳定收敛到 `78/78`。

本轮输入是 v150 剩余的 greedy-anchor `b361` failed pairs。v152 成功挖到
train-only greedy analog，并且没有 validation leakage：

```text
failed_pair_count = 2
failure_split_counts = {'validation_gate_only': 2}
analog_pair_count = 24
analog_row_index_count = 20
existing_boost_row_index_count = 48
combined_boost_row_index_count = 52
new_row_indices_beyond_existing_boost = [982, 1010, 1011, 1053]
excluded_validation_row_indices = [813, 814, 815]
validation_leakage_row_indices = []
combined_boost_validation_leakage_row_indices = []
all_combined_boost_rows_train = true
```

训练后：

- v150 回归的 `b361` 已修复；
- 但 v148/v150 中已修过的 `9f80` random-wave deep failures 又回来；
- `84ae` greedy-anchor 也重新失败；
- focused strict 回到 `75/78`，低于 v150 的 `76/78`；
- Stage 4 仍 blocked。

因此 v152 不是候选 checkpoint；它是一个“analog boost 不足以闭合 focused gate”的证据点。

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
diagnostic_only = true
selector_can_certificate = false
```

## Artifact

```text
v152_analog_summary =
  BPC_future/results/gat_batch_impact_v152_v150_train_only_failure_analogs_20260623/summary.json

v152_boost_selector =
  BPC_future/results/gat_batch_impact_v152_v150_train_only_failure_analogs_20260623/train_only_combined_boost_row_indices.json

v152_metrics =
  BPC_future/results/gat_batch_impact_training_v152_v150_balanced_trainonly_analog_boost_path_context_gate_seed13_20260623/metrics.json

v152_training_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v152_v150_balanced_trainonly_analog_boost_path_context_gate_seed13_zh.md

v152_failure_audit =
  BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v152_v150_balanced_trainonly_analog_boost_path_context_gate_20260623/summary.json

v152_failure_audit_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v152_v150_balanced_trainonly_analog_boost_path_context_gate_pair_failure_audit_zh.md

v153_top_context_feature_contrast =
  BPC_future/results/gat_batch_impact_top_context_feature_contrast_v153_v152_failures_20260623/summary.json

v153_top_context_feature_contrast_report =
  BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v153_v152_failure_top_context_feature_contrast_zh.md
```

## v150 / v152 对比

| 指标 | v150 | v152 | 变化 |
|---|---:|---:|---:|
| best_epoch | 5 | 5 | 0 |
| best_loss_epoch | 3 | 3 | 0 |
| validation accepted | 35 | 35 | 0 |
| accepted ROI | 18.789281 | 19.221042 | +0.431761 |
| accepted ROI CI-low | 9.691910 | 10.095954 | +0.404044 |
| high-priority precision | 0.996988 | 0.996161 | -0.000827 |
| high-priority CI-low | 0.989085 | 0.986112 | -0.002972 |
| safe precision | 1.000000 | 1.000000 | 0 |
| safe precision CI-low | 0.901096 | 0.901096 | 0 |
| false high-priority on delay | 0.007220 | 0.007220 | 0 |
| false-safe union | 0.007220 | 0.007220 | 0 |
| focused strict pass | 76/78 | 75/78 | -1 pair |
| checkpoint_gate_pass | false | false | unchanged |
| stage4_candidate_ready | false | false | unchanged |

v152 的 validation ROI point estimate 比 v150 略高，但 focused gate 更差。按计划合同，
ROI 不能抵消 focused context-local ranking failure。

## Focused Failure 转移

v150 failed pairs：

| context | family | task | pair | raw | admission | delay-risk | diagnosis |
|---|---|---:|---|---:|---:|---:|---|
| `b36178f6655c5f75` | greedy-anchor | 20 | `813>814` | -0.036538 | -0.024236 | -0.015176 | mixed_margin_failure |
| `b36178f6655c5f75` | greedy-anchor | 20 | `813>815` | -0.010646 | -0.004198 | -0.000282 | mixed_margin_failure |

v152 failed pairs：

| context | family | task | pair | raw | admission | delay-risk | diagnosis |
|---|---|---:|---|---:|---:|---:|---|
| `84ae11479ed592d4` | greedy-anchor | 20 | `998>1001` | -0.065697 | -0.060587 | -0.044057 | deep_structural_score_gap |
| `9f80ae35ea87da5b` | random-wave | 30 | `183>845` | -0.078300 | -0.057772 | -0.050017 | deep_structural_score_gap |
| `9f80ae35ea87da5b` | random-wave | 30 | `844>845` | -0.055217 | -0.067707 | -0.048152 | deep_structural_score_gap |

这不是简单 “v152 比 v150 少一个” 或 “多一个” 的问题，而是错误 context 在不同
family 之间迁移：

- v148: `62c` + `9f80` 失败；
- v150: `62c` / `9f80` 修复，`b361` 失败；
- v152: `b361` 修复，`9f80` + `84ae` 失败。

## v153 Feature Contrast

v153 对 v152 failure contexts 做 feature contrast：

```text
failed_pair_count = 3
deep_failed_pair_count = 3
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
failed_context_feature_drift_pair_count = 0
primary = visible_inputs_differ_but_model_still_misranks
recommended_next_step = tighten_context_local_pairwise_ranking_head
```

Tensor availability 仍然完整：

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

因此，当前 blocker 不是“再加几条 analog row”能稳定解决的样本数量问题，也不是
输入完全不可见的问题，而是模型缺少一个足够强、足够稳定的 context-local pairwise
ordering mechanism。

## 判断

1. `train-only analog boost` 作为诊断工具有效。
   它能验证某个 failure 是否可被相似 train pair 拉动。

2. `train-only analog boost` 作为闭合 Stage 3 focused gate 的主方法失败。
   v150/v152 已经形成循环：修一个 context，另一个 context/family 掉下去。

3. 下一步不应继续做 v154 = v152 failure analog boost。
   那会很可能继续在 `9f80`、`84ae`、`b361`、`62c` 之间摆动。

4. kNN/OOD 仍不能作为遮盖手段。
   focused gate 未达 `78/78` 前，不应把 kNN/OOD 绑定成 Stage 4 safety shell。

## 下一步

下一步应从“重复采样修补”转到“结构/目标函数稳定化”：

1. 增加默认关闭的 context-local pair-delta ranking head：
   输入同一 context 的 positive/negative candidate-batch 表示差值，直接优化
   `score(context, positive) > score(context, negative)`。

2. 训练时同时报告旧 raw/admission/delay heads 与新 pair-delta head 的 focused gate，
   但 Stage 4 gate 仍按旧 admission policy 不放宽。

3. 如果先不改模型结构，至少要实现 cross-family stability loss：
   在同一 mini-batch 或 accumulated focused loss 中对 `9f80`、`84ae`、`b361`、
   `62c` 这类已知 frontier contexts 做 balanced weighting，而不是按当前 failure
   单向加 boost。

4. 暂停继续做“当前失败 -> analog boost -> 训练”的线性循环，除非新增机制能证明不会
   牺牲已修复 contexts。

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

GAT / kNN / OOD 仍只能影响 discovery / ordering / finite-delay scheduling；official
lower bound、no-negative conclusion 和 final certificate 仍只能来自 exact pricing
full closure。
