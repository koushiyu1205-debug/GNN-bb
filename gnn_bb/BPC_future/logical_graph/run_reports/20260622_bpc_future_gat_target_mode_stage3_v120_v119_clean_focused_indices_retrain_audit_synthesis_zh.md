# 2026-06-22 BPC_future GAT Target Mode Stage 3 v120 v119-clean focused indices 重训与审计综合报告

## 结论

v120 是一次有效的 Stage 3 收敛推进，但仍不是 Stage 4 candidate。

- v119-clean focused tranche mining 生成了更干净的显式 row-index selector：`102` 个 focused rows、`78` 个 same-context positive/negative pairs，避免继续使用旧 v110 selector 带入大量非 focused rows。
- v120 local deployment metrics 相对 v119 继续改善：validation accepted ROI 从 `18.4524762773` 提高到 `19.3365859772`，ROI CI-low 从 `9.3015235175` 提高到 `10.2191974778`。
- focused pair gate 明显改善但未过线：strict pair pass rate 从 v119 的 `0.8717948718` 提高到 v120 的 `0.9230769231`，failed pair 从 `10` 个降到 `6` 个，但 Stage 3 hard gate 仍要求 `1.0`。
- strict kNN/OOD shell 继续保持 false-safe union 为 `0`，但 accepted all-success count 仍不足：global strict `33` 个，scale strict `32` 个，Wilson safe precision CI-low 分别为 `0.8957265700` 和 `0.8928172849`，都低于 `0.9`。

因此当前状态是：

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
selector_can_certificate = false
```

下一步不应降低 focused/kNN/OOD gate，也不应继续盲目调 loss multiplier。当前 blocker 已缩小到：

1. 三个 focused failure contexts 的 context-local ranking 误排序；
2. kNN/OOD strict shell 在 false-safe 仍为 0 的前提下，需要再多接受约 2-3 个安全 high-ROI batch，才能让 safe precision CI-low 过 `0.9`。

## 对计划的对齐

本轮仍处于 Stage 3。根据 `gat_bpc_future_target_mode_optimization_plan_zh.md`：

- Stage 3 的 primary objective 是 `precision_constrained_roi_maximization`；
- checkpoint selection 必须先看 precision / ROI / safety / coverage / holdout gates，validation loss 只能做可行 checkpoint 之间的 tie-breaker；
- focused pair gate、kNN/OOD false-safe gate 和 CI lower bound 未过线时，checkpoint 只能是 diagnostic；
- GAT/kNN/OOD 不产生 official lower bound、不能生成 `CERTIFIED_NO_NEGATIVE`、不能永久丢弃 true-RC negative columns。

v120 继续遵守这些边界：所有 artifact 都是 offline / diagnostic-only，不运行 BPC / pricing / RMP / worker / certificate。

## 输入数据与 focused tranche

数据集：

```text
dataset_dir = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
sample_count = 1117
candidate_count = 12684
context_count = 546
```

v120 先在 v119 clean dataset 上重新挖 focused tranche，而不是沿用旧 v110 row-index selector：

```text
focused_tranche_summary =
  output_dir = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622
  trainable_context_count = 30
  focused_pair_count = 78
  focused_row_count = 102
  focused_positive_row_count = 56
  focused_hard_negative_row_count = 46
  focused_family_counts = {'greedy-anchor': 33, 'random-wave': 47, 'sector-wave': 22}
  focused_task_count_counts = {'20': 83, '30': 17, '50': 2}
  recommended_selector = explicit_row_indices
  stage3_focused_tranche_ready = true
```

关键意义：v119 clean mining 保留了相同规模的 hard same-context pair signal，但 selector 更窄、更干净，避免 row-index-min 方案把大量非 focused rows 混入 focused loss。

## v120 训练结果

训练 artifact：

```text
checkpoint = BPC_future/results/gat_batch_impact_training_v120_v119_clean_focused_indices_seed13_20260622/model.pt
metrics = BPC_future/results/gat_batch_impact_training_v120_v119_clean_focused_indices_seed13_20260622/metrics.json
report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v120_v119_clean_focused_indices_retrain_seed13_zh.md
```

训练设置：

```text
seed = 13
epochs = 8
device = cuda
candidate_admission_score_mode = risk_adjusted_product
candidate_delay_score_penalty = 1.5
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.55
focused_pair_row_indices_file = BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/focused_row_indices.json
focused_pair_row_indices_count = 102
```

checkpoint selection：

```text
best_epoch = 6
best_loss_epoch = 3
best_loss_epoch_gate_pass = true
checkpoint_gate_pass = false
stage4_candidate_ready = false
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
rejected_checkpoint_reasons =
  - admission_pair_pass_rate_below_threshold
  - delay_risk_pair_pass_rate_below_threshold
  - knn_ood_audit_missing
  - raw_pair_pass_rate_below_threshold
  - strict_pair_pass_rate_below_threshold
```

local validation deployment metrics：

```text
threshold_local_gate_pass = true
accepted_batch_count = 35
accepted_batch_rate = 0.1198630137
accepted_batch_roi = 19.3365859772
accepted_batch_roi_ci_low = 10.2191974778
high_priority_precision = 0.9972714870
high_priority_precision_ci_low = 0.9901063814
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324
false_high_priority_on_delay = 0.0072202166
false_high_priority_on_delay_count = 2
false_safe_rate_union = 0.0072202166
expected_trajectory_utility = 19.3551574058
```

与 v119 local validation 对比：

| 指标 | v119 | v120 | 判断 |
|---|---:|---:|---|
| accepted batch count | 35 | 35 | 持平 |
| accepted ROI | 18.452476 | 19.336586 | 改善 |
| accepted ROI CI-low | 9.301524 | 10.219197 | 改善 |
| false high-priority on delay | 0.003610 | 0.007220 | 变差但仍低于 0.01 |
| false high-priority count | 1 | 2 | 变差 |
| safe precision CI-low | 0.901096 | 0.901096 | 持平 |

解读：v120 的 local ROI 更好，说明 v119-clean focused rows 和更强 focused loss 方向有效；但 false-delay margin 被吃掉一部分，后续修复不能继续牺牲 safety。

## Focused Pair Gate

v120 focused pair gate：

```text
focused_row_count = 102
context_count = 30
pair_count = 78
raw_pair_pass_rate = 0.9358974359
admission_pair_pass_rate = 0.9358974359
delay_risk_pair_pass_rate = 0.9487179487
strict_pair_pass_rate = 0.9230769231
primary = candidate_head_context_ranking_failure
```

与 v119 focused pair gate 对比：

| 指标 | v119 | v120 | 判断 |
|---|---:|---:|---|
| focused rows | 113 | 102 | 更窄 |
| pair count | 78 | 78 | 持平 |
| raw pass rate | 0.897436 | 0.935897 | 改善 |
| admission pass rate | 0.897436 | 0.935897 | 改善 |
| delay-risk pass rate | 0.884615 | 0.948718 | 改善 |
| strict pass rate | 0.871795 | 0.923077 | 改善但未过 1.0 |

focused failure anatomy：

```text
failure_audit =
  pair_count = 78
  failed_pair_count = 6
  pair_pass_count = 72
  strict_pair_pass_rate = 0.9230769231
  raw_fail_count = 5
  admission_fail_count = 5
  delay_risk_fail_count = 4
  all_failed_heads_near_count = 4
  any_failed_head_deep_count = 1
  diagnosis_counts = {
    'deep_structural_score_gap': 1,
    'mixed_margin_failure': 1,
    'near_margin_loss_tuning_candidate': 4,
    'pair_passes': 72
  }
```

剩余失败集中在 3 个 context：

| context | family | task | failed pairs | 诊断 |
|---|---|---:|---:|---|
| `5c522ff2995f86be` | random-wave | 20 | 3 | near-margin + mixed |
| `84ae11479ed592d4` | greedy-anchor | 20 | 2 | 1 个 deep structural score gap |
| `5368cf35ed6f06cb` | random-wave | 30 | 1 | near-margin |

top-context feature contrast 进一步确认：

```text
primary = visible_inputs_differ_but_model_still_misranks
failed_pair_count = 6
failed_model_input_collision_pair_count = 0
failed_context_feature_drift_pair_count = 0
deep_failed_pair_count = 1
recommended_next_step = tighten_context_local_pairwise_ranking_head
```

这说明当前不是模型输入 schema 缺失或样本完全不可分，而是 context-local ranking head / pairwise margin 仍不够稳。下一轮应围绕这 3 个 context 做 targeted repair，而不是扩大无关训练样本。

## kNN/OOD Strict Shell

global strict：

```text
output_dir = BPC_future/results/gat_batch_impact_knn_ood_audit_v120_v119_clean_focused_indices_global_strict_20260622
threshold_grouping = global
accepted_batch_count = 33
accepted_batch_rate = 0.1130136986
accepted_batch_roi = 16.0403406322
accepted_batch_roi_ci_low = 8.0908387790
safe_precision = 1.0
safe_precision_ci_low = 0.8957265700
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
coverage = 1.0
ood_count = 0
validation_candidate_ready = false
production_block_reasons =
  - validation_safe_precision_ci_low_below_min
  - validation_candidate_not_ready
```

scale strict：

```text
output_dir = BPC_future/results/gat_batch_impact_knn_ood_audit_v120_v119_clean_focused_indices_scale_strict_20260622
threshold_grouping = scale
accepted_batch_count = 32
accepted_batch_rate = 0.1095890411
accepted_batch_roi = 18.5584336882
accepted_batch_roi_ci_low = 8.7020542294
safe_precision = 1.0
safe_precision_ci_low = 0.8928172849
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
coverage = 0.9691780822
ood_count = 9
ood_rate = 0.0308219178
validation_candidate_ready = false
production_block_reasons =
  - validation_safe_precision_ci_low_below_min
  - validation_candidate_not_ready
```

与 v119 strict shell 对比：

| shell | v119 accepted | v120 accepted | v119 CI-low | v120 CI-low | false-safe |
|---|---:|---:|---:|---:|---:|
| global strict | 32 | 33 | 0.892817 | 0.895727 | 0 |
| scale strict | 32 | 32 | 0.892817 | 0.892817 | 0 |

解读：

- safety 方向是正确的：两个 strict shell 都把 false-safe union 压到 `0`。
- 当前失败不是 ROI，global / scale 的 accepted ROI CI-low 都远高于 `0.65`。
- 当前失败也不是 point precision，而是 accepted all-success count 太少导致 Wilson lower bound 不够。
- 若保持 `safe_precision=1.0`，global strict 大约还差 2 个安全 accepted batch，scale strict 大约还差 3 个安全 accepted batch，才能把 `safe_precision_ci_low` 推过 `0.9`。

## Exactness Boundary

v120 所有新增 artifact 都保持：

```text
runs_bpc_or_pricing = false
runs_rmp = false
production_ready = false
default_enabled = false
pricing_oracle = false
certificate_source = false
official_bound_effect = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
delay_queue_replaces_exact_pricing = false
```

因此：

- v120 GAT/kNN/OOD 不能生成 official lower bound；
- v120 GAT/kNN/OOD 不能生成 `CERTIFIED_NO_NEGATIVE`；
- true-RC negative 只能被有限延迟或重新暴露给 exact pricing，不能永久丢弃；
- 后续 Stage 4/5 声明仍必须由当前 branch/cut/dual 下 exact pricing full closure、official no-regression A/B 和 certificate audit 证明。

## 当前 Stage 判断

```text
local_deployment_gate_pass = true
focused_pair_gate_pass = false
knn_ood_global_strict_ready = false
knn_ood_scale_strict_ready = false
online_shadow_or_optin_ab_run = false
certificate_audit_for_v120_online_path = not_run
stage3_completed = false
stage4_candidate_ready = false
stage4_should_start = false
```

v120 可以作为下一轮 Stage 3 targeted repair 的基线，但不能进入 Stage 4 shadow / opt-in。

## 下一步

建议下一轮只做窄修复：

1. 针对 `5c522ff2995f86be`、`84ae11479ed592d4`、`5368cf35ed6f06cb` 增加 context-local pairwise/ranking 修复，优先修复 admission/raw margin，不继续盲目放大全局 loss multiplier。
2. 对 kNN/OOD strict shell 的 delayed-but-safe high-ROI rows 做审计，目标是在 false-safe union 仍为 `0` 的前提下，让 global strict accepted 从 `33` 提到至少 `35`，或让 scale strict accepted 从 `32` 提到至少 `35`。
3. 保持 `safe_precision_ci_low >= 0.9`、`false_safe_rate_union <= 0.02`、focused strict pair pass rate `1.0` 的 hard gates，不为凑 Stage 4 candidate 降低阈值。
4. 只有 focused pair gate 和 kNN/OOD holdout 同时通过后，才生成新的 default-off Stage 4 shadow / opt-in runbook；仍不得进入 Stage 5。

## Artifact

- `BPC_future/results/gat_batch_impact_focused_tranche_mining_v120_v119_clean_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_training_v120_v119_clean_focused_indices_seed13_20260622/metrics.json`
- `BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v120_v119_clean_focused_indices_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_knn_ood_audit_v120_v119_clean_focused_indices_global_strict_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_knn_ood_audit_v120_v119_clean_focused_indices_scale_strict_20260622/summary.json`
- `BPC_future/results/gat_batch_impact_top_context_feature_contrast_v120_v119_clean_focused_indices_20260622/summary.json`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v120_v119_clean_focused_tranche_mining_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v120_v119_clean_focused_indices_retrain_seed13_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v120_v119_clean_focused_indices_pair_failure_audit_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v120_v119_clean_focused_indices_knn_ood_global_strict_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v120_v119_clean_focused_indices_knn_ood_scale_strict_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v120_v119_clean_focused_indices_top_context_feature_contrast_zh.md`
