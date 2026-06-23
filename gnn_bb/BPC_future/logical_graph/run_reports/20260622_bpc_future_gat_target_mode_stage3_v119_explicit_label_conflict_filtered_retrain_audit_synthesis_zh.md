# 2026-06-22 BPC_future GAT Target Mode Stage 3 v119 数据修复、重训与 kNN/OOD 综合报告

## 结论

v119 是一次有效的数据修复和离线重训推进，但还不是 Stage 4 candidate。

分开看：

- 数据层面变好：v119 过滤 explicit long-horizon 同输入冲突后，
  model-visible label conflict 已降为 0，可以继续作为 Stage 3 重训输入。
- GAT local deployment metrics 变好：相对 v116/v118，v119 的 validation accepted
  ROI 和 ROI CI-low 明显提高，且 local gate 通过。
- focused pair gate 没变好：v119 的 focused strict pair pass rate 只有
  `0.8717948718`，低于 Stage 3 对 hard same-context pair 的 1.0 要求。
- kNN/OOD safety shell 有进展但未过线：global/scale strict shell 都把
  false-safe union 压到 0，但 accepted batch count 只有 32，Wilson
  `safe_precision_ci_low=0.8928172849 < 0.9`。
- 因此：

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
selector_can_certificate = false
```

下一步不应继续盲目调 loss multiplier，也不应降低 gate；应在 v119 clean
dataset 上重新挖掘 focused hard pairs，并加强 context-local pairwise ranking
head / loss，使 kNN/OOD 后 accepted all-success batch 从 32 提到至少足够支撑
`safe_precision_ci_low >= 0.9`，同时保持 false-safe union 为 0。

## Plan 对齐

本报告按 `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
的 Stage 3 合同解释结果：

- Stage 3 不是普通分类训练；
- checkpoint 选择必须先看 precision / ROI / safety / coverage / kNN-OOD gate；
- validation loss、F1、recall 不能覆盖 hard gate；
- 任何未通过 focused pair、kNN/OOD、holdout、Stage 4 shadow/opt-in 的 checkpoint
  都只能叫 diagnostic checkpoint；
- GAT/kNN/OOD 只能影响 admission scheduling 或优先级，不能生成 official lower
  bound、certificate 或 no-negative conclusion。

## v119 数据修复

输入数据集：

```text
BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
```

构建结果：

```text
sample_count = 1117
candidate_count = 12684
training_ready = true
ranking_ready = true
family_counts = {'greedy-anchor': 358, 'random-wave': 421, 'sector-wave': 338}
task_count_counts = {'5': 32, '10': 74, '20': 688, '30': 168, '50': 119, '100': 36}
explicit_long_horizon_candidate_key_count = 65
conflicting_explicit_long_horizon_candidate_key_count = 19
skipped_counts = {
  'conflicting_explicit_long_horizon_label': 89,
  'shadowed_by_explicit_long_horizon_label': 15
}
```

冲突审计：

```text
audited_sample_count = 1117
model_visible_label_conflict_group_count = 0
model_visible_label_conflict_sample_count = 0
explicit_long_horizon_conflict_group_count = 0
mixed_provenance_conflict_group_count = 0
stage3_retrain_safe_without_repair = true
recommended_next_step = no_model_visible_label_conflict_found_continue_focused_pair_gap_audit
```

解释：

- v116 中 row400/row418 一类“同一模型可见输入、不同 long-horizon 标签”的冲突已被清掉。
- v119 的 1117 样本少于 v116 的 1177，是因为 builder 按 explicit long-horizon
  candidate key 过滤冲突和 shadowed rows；这比只删除 30 个直接冲突样本更保守。
- 该修复只处理标签来源冲突，不改变 solver、pricing、RMP 或 certificate path。

## v119 GAT 重训结果

训练输出：

```text
BPC_future/results/gat_batch_impact_training_v119_explicit_label_conflict_filtered_seed13_20260622/model.pt
BPC_future/results/gat_batch_impact_training_v119_explicit_label_conflict_filtered_seed13_20260622/metrics.json
```

核心字段：

```text
best_epoch = 5
best_loss_epoch = 3
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_roi_ci_baseline_utility_loss
checkpoint_gate_pass = false
stage4_candidate_ready = false
```

Validation local deployment metrics：

```text
threshold_local_gate_pass = true
accepted_batch_count = 35
accepted_batch_roi = 18.452476277308804
accepted_batch_roi_ci_low = 9.301523517522549
high_priority_precision = 0.9983443708609272
high_priority_precision_ci_low = 0.990681912987217
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0036101083032490976
false_safe_rate_union = 0.0036101083032490976
expected_trajectory_utility = 18.473904848737376
```

Checkpoint hard blockers：

```text
rejected_checkpoint_reasons = [
  'admission_pair_pass_rate_below_threshold',
  'delay_risk_pair_pass_rate_below_threshold',
  'knn_ood_audit_missing',
  'raw_pair_pass_rate_below_threshold',
  'strict_pair_pass_rate_below_threshold'
]

stage4_blockers = [
  'admission_pair_pass_rate_below_threshold',
  'delay_risk_pair_pass_rate_below_threshold',
  'knn_ood_audit_missing',
  'knn_ood_holdout_audit_not_run',
  'online_shadow_and_opt_in_ab_not_run',
  'raw_pair_pass_rate_below_threshold',
  'strict_pair_pass_rate_below_threshold'
]
```

解释：

- v119 的 local gate 通过，说明数据修复后 GAT 可以学到更高 ROI 的保守 admission
  policy。
- 但 local gate 不是 Stage 3 完成定义；focused pair gate、kNN/OOD holdout 和
  Stage 4 shadow/opt-in 仍必须全部通过。

## v116/v118/v119 对比

| 版本 | accepted | ROI | ROI CI-low | safe CI-low | false-delay | false-safe union | Stage 4 candidate |
|---|---:|---:|---:|---:|---:|---:|---|
| v116 | 36 | 4.602683 | 2.355012 | 0.903578 | 0.000000 | 0.000000 | false |
| v118 | 54 | 3.795432 | 2.184186 | 0.933584 | 0.017483 | 0.017483 | false |
| v119 | 35 | 18.452476 | 9.301524 | 0.901096 | 0.003610 | 0.003610 | false |

结论：

- v119 在 local ROI 上显著优于 v116/v118；
- v119 比 v118 安全，false-delay 从 `0.017483` 降到 `0.003610`；
- v119 的 accepted count 比 v118 低，但足够让 local safe CI 刚过 `0.9`；
- 这些改进仍不足以关闭 focused pair 和 kNN/OOD hard gate。

## Focused Pair Failure 审计

审计输出：

```text
BPC_future/results/gat_batch_impact_focused_pair_failure_audit_v119_explicit_label_conflict_filtered_20260622
```

结果：

```text
pair_count = 78
failed_pair_count = 10
pair_pass_count = 68
raw_fail_count = 8
admission_fail_count = 8
delay_risk_fail_count = 9
strict_pair_pass_rate = 0.8717948717948718
all_failed_heads_near_count = 5
any_failed_head_deep_count = 3
diagnosis_counts = {
  'deep_structural_score_gap': 3,
  'mixed_margin_failure': 2,
  'near_margin_loss_tuning_candidate': 3,
  'near_margin_with_shared_signature': 2,
  'pair_passes': 68
}
```

原始审计建议：

```text
primary = add_or_repair_context_action_consequence_features_before_more_sweeps
avoid = do_not_continue_blind_multiplier_sweeps
```

结合后续 top-context contrast，当前更精确的解释是：

- v119 已经修掉模型可见输入冲突；
- 剩余失败不是“同输入不同标签”的数据冲突；
- 失败集中在 context-local ranking 的可见输入误排序；
- 应重新在 v119 clean rows 上挖掘 focused hard pairs，并加强 context-local pairwise ranking。

## Top-context Feature Contrast

审计输出：

```text
BPC_future/results/gat_batch_impact_top_context_feature_contrast_v119_explicit_label_conflict_filtered_20260622
```

结果：

```text
audited_pair_count = 28
audited_row_count = 31
failed_pair_count = 10
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
deep_failed_pair_count = 3
mean_failed_candidate_feature_l1 = 599.7410425478432
mean_failed_path_token_jaccard = 0.08418803418803418
primary = visible_inputs_differ_but_model_still_misranks
recommended_next_step = tighten_context_local_pairwise_ranking_head
```

Tensor 可见性：

```text
candidate_feature_dim = 59
context_feature_dim = 26
batch_feature_dim = 18
candidate_path_token_row_coverage = 1.0
trace_scalar_row_coverage = 1.0
slack_scalar_row_coverage = 1.0
per_candidate_branch_cut_interaction_present = true
```

解释：

- v119 不再是 v116/v118 的“feature/input collision”问题。
- 模型已经看得到区分失败样本的主要输入，但 ranking head / loss 仍未稳定学到
  same-context positive-over-negative 顺序。
- 下一步应把 focused row indices 从 v110 旧索引迁移为 v119 clean dataset 上重新挖掘的
  hard pairs；当前 focused pair count 从旧语境缩到 78，说明旧索引在过滤后不再覆盖足够多的关键对。

## kNN/OOD strict shell

Global strict：

```text
accepted_batch_count = 32
accepted_batch_rate = 0.1095890410958904
accepted_batch_roi = 15.420070820255205
accepted_batch_roi_ci_low = 7.247021043893456
safe_precision = 1.0
safe_precision_ci_low = 0.8928172849426365
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
coverage = 1.0
ood_count = 0
validation_candidate_ready = false
production_block_reasons = [
  'validation_safe_precision_ci_low_below_min',
  'validation_candidate_not_ready'
]
```

Scale strict：

```text
accepted_batch_count = 32
accepted_batch_rate = 0.1095890410958904
accepted_batch_roi = 15.420070820255205
accepted_batch_roi_ci_low = 7.247021043893456
safe_precision = 1.0
safe_precision_ci_low = 0.8928172849426365
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
coverage = 0.9828767123287672
ood_count = 5
ood_rate = 0.017123287671232876
validation_candidate_ready = false
production_block_reasons = [
  'validation_safe_precision_ci_low_below_min',
  'validation_candidate_not_ready'
]
```

解释：

- kNN/OOD shell 的方向是对的：false-safe union 被压到 0。
- 失败原因不是 ROI，而是 accepted all-success count 不够，导致 Wilson lower bound
  `0.8928172849 < 0.9`。
- v119 local threshold 有 35 个 accepted 且 `safe_precision_ci_low=0.9010956324`；
  但 kNN/OOD shell 把 accepted 降到 32，因此刚好跌破 confidence gate。
- 下一步的目标不是放松 kNN/OOD，而是在保持 false-safe union 为 0 的情况下让 shell
  多接受几个同样安全的 high-ROI batch。

## Exactness Boundary

本轮所有 v119 工作均为 offline diagnostic / audit：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
pricing_oracle = false
certificate_source = false
official_bound_effect = false
can_permanently_discard_true_rc_negative = false
delay_queue_replaces_exact_pricing = false
```

因此：

- v119 GAT/kNN/OOD 不能生成 official lower bound；
- v119 GAT/kNN/OOD 不能生成 `CERTIFIED_NO_NEGATIVE`；
- true-RC negative 只能被有限延迟或重新暴露给 exact pricing，不能永久丢弃；
- 任何 Stage 4/5 声明仍必须由 current branch/cut/dual 下 exact pricing full closure
  和 official no-regression A/B 证明。

## 当前 Stage 判断

```text
data_repair_effective = true
local_deployment_gate_pass = true
focused_pair_gate_pass = false
knn_ood_global_strict_ready = false
knn_ood_scale_strict_ready = false
online_shadow_or_optin_ab_run = false
certificate_audit_for_v119_online_path = not_run
stage3_completed = false
stage4_candidate_ready = false
stage4_should_start = false
```

## 下一步

1. 在 v119 clean dataset 上重新运行 focused tranche mining，不再直接复用 v110
   旧 row-index 文件。
2. 用重新挖出的 v119 hard pairs 训练 context-local pairwise ranking head，目标是
   `strict_pair_pass_rate = 1.0`，而不是继续盲目加大 multiplier。
3. 保持 kNN/OOD strict shell，不降低 `safe_precision_ci_low >= 0.9` 和
   `false_safe_rate_union <= 0.02` gate。
4. 让 kNN/OOD 后 accepted all-success batch 从 32 提升到至少能支撑 Wilson lower
   bound 过 0.9；优先找当前被 shell 延迟但特征邻域安全的 high-ROI batch。
5. 只有 focused pair gate 和 kNN/OOD holdout 同时通过后，才允许生成新的 Stage 4
   default-off shadow / opt-in runbook；仍不得进入 Stage 5。

## 关联报告

- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_label_provenance_conflict_audit_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_dataset_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_conflict_audit_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_retrain_seed13_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_pair_failure_audit_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_top_context_feature_contrast_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_knn_ood_global_strict_zh.md`
- `BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_knn_ood_scale_strict_zh.md`
