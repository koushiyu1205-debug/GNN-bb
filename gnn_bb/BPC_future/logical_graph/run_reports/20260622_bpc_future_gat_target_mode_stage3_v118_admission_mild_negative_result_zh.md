# BPC_future GAT Target Mode Stage 3 v118 Admission Mild 负结果报告

日期：2026-06-22

## 结论

v118 不替代 v116，也不能作为 Stage 4 candidate。

本轮在 v116 数据集上只做温和的 focused admission loss 上调，目的是验证：
不整体加强 focused candidate/delay head，只把 admission 从 v116 的 2.0 调到
2.75，能否把 focused strict pair pass rate 从 0.93548 推近 1.0，同时保持
v116 已有的 local / kNN 安全边界。

结果没有变好。v118 的 validation accepted 从 v116 的 36 增到 54，safe precision
CI low 也高于 0.9，但 false high-priority on delay 升到 0.0174825，超过 Stage 3
硬线 0.01；focused strict pair pass rate 退化到 0.880184。该结果说明问题不再像
v116 那样只是 near-margin focused head tuning，继续做盲目 multiplier sweep 会把
coverage / safety 和 focused ranking 同时推坏。

## Exactness 边界

- 只运行 offline training 和 offline audit；
- 不运行 BPC / pricing / RMP / worker；
- 不生成 official bound 或 certificate；
- GAT/kNN/OOD 不能永久丢弃 true-RC negative；
- final certificate 仍只能来自 exact pricing full closure。

## v118 配置

数据集：

```text
BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622
```

输出：

```text
checkpoint = BPC_future/results/gat_batch_impact_training_v118_context_interaction_cleaned_admission_mild_seed13_20260622/model.pt
metrics = BPC_future/results/gat_batch_impact_training_v118_context_interaction_cleaned_admission_mild_seed13_20260622/metrics.json
training_report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v118_context_interaction_cleaned_admission_mild_retrain_seed13_zh.md
epoch_selector = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v118_context_interaction_cleaned_admission_mild_epoch_selector_audit_zh.md
focused_failure_audit = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v118_context_interaction_cleaned_admission_mild_pair_failure_audit_zh.md
```

相对 v116 的 focused loss 变化：

```text
focused_pair_loss_multiplier: 1.0 -> 1.0
focused_pair_candidate_loss_multiplier: 1.5 -> 1.5
focused_pair_admission_loss_multiplier: 2.0 -> 2.75
focused_pair_delay_risk_loss_multiplier: 2.0 -> 2.0
focused_pair_batch_loss_multiplier: 0.5 -> 0.5
```

相对 v117，v118 撤回了过强的 candidate/admission/delay 整体加权，只保留 admission
轻微上调。

## 训练结果

```text
best_epoch = 2
best_loss_epoch = 4
checkpoint_gate_pass = false
stage4_candidate_ready = false
selected_checkpoint_reason = no_local_deployment_gate_passed_selected_best_diagnostic_by_reject_reasons_precision_ci_safe_ci_coverage
rejected_checkpoint_reasons = [
  admission_pair_pass_rate_below_threshold,
  delay_risk_pair_pass_rate_below_threshold,
  false_high_priority_on_delay_too_high,
  knn_ood_audit_missing,
  raw_pair_pass_rate_below_threshold,
  strict_pair_pass_rate_below_threshold
]
```

selected validation metrics：

```text
accepted_batch_count = 54
accepted_batch_roi = 3.795431596088141
accepted_batch_roi_ci_low = 2.1841855273511417
high_priority_precision = 0.9938725490196079
high_priority_precision_ci_low = 0.9857367369279972
safe_precision = 1.0
safe_precision_ci_low = 0.9335841332189981
false_high_priority_on_delay = 0.017482517482517484
false_high_priority_on_delay_count = 5
false_safe_rate_union = 0.017482517482517484
threshold_local_gate_pass = false
```

注意：metrics 中的 train split `accepted_batch_count=157`、`false_high_priority_on_delay=0.000956`
不能作为 Stage 3 通过证据。Stage 3 gate 必须看 frozen threshold 在 validation /
holdout 上的 safety、ROI、coverage 和 focused-pair 结果。

## Epoch Selector

epoch selector 结论：

```text
epoch_count = 8
false_delay_safe_epoch_count = 1
coverage_confidence_ready_epoch_count = 7
coverage_and_false_delay_safe_epoch_count = 0
primary = no_epoch_satisfies_coverage_and_false_delay_constraints
checkpoint_selection_is_primary_blocker = false
recommended_next_step = not_a_checkpoint_selection_problem_collect_context_local_hard_negatives
```

关键 epoch：

| epoch | accepted | ROI | false-delay | validation loss | class |
|---:|---:|---:|---:|---:|---|
| 1 | 9 | 4.253915 | 0.000000 | 5.345574 | false-delay safe, low coverage |
| 2 | 54 | 3.795432 | 0.017483 | 5.326231 | coverage ready, false-delay unsafe |
| 4 | 74 | 4.125824 | 0.066434 | 5.079018 | best loss, false-delay unsafe |
| 5 | 121 | 4.129276 | 0.048951 | 5.929727 | best coverage-ready diagnostic |

因此 v118 不是 checkpoint selector 漏选了好 epoch，而是没有 epoch 同时满足 coverage
confidence 和 false-delay safety。best loss epoch 4 也不能选，因为 false-delay 明确越线。

## Focused Pair 结果

focused same-context pair gate：

```text
pair_count = 217
pair_pass_count = 191
failed_pair_count = 26
raw_pair_pass_rate = 0.8894009216589862
admission_pair_pass_rate = 0.9032258064516129
delay_risk_pair_pass_rate = 0.9078341013824884
strict_pair_pass_rate = 0.880184331797235
raw_fail_count = 24
admission_fail_count = 21
delay_risk_fail_count = 20
all_failed_heads_near_rate_among_failed = 0.23076923076923078
any_failed_head_deep_count = 7
signature_overlap_pair_rate = 0.5023041474654378
```

主要失败上下文：

| context | family | failed pairs | primary |
|---|---|---:|---|
| `apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715|b6d808ebac2a6dd8` | sector-wave | 9 | shared_signature_confounder |
| `apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|d519291840dd7000` | random-wave | 8 | mixed/deep structural gap |
| `apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|67c11b5ec80925ec` | random-wave | 5 | near-margin with shared signature |

审计建议是：

```text
add_or_repair_context_action_consequence_features_before_more_sweeps
avoid = do_not_continue_blind_multiplier_sweeps
```

## Top-context Feature Contrast

进一步对 v118 top failed contexts 做模型可见输入审计：

```text
report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v118_top_context_feature_contrast_zh.md
summary = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v118_context_interaction_cleaned_admission_mild_20260622/summary.json
audited_pair_count = 103
failed_pair_count = 26
model_input_collision_pair_count = 1
failed_model_input_collision_pair_count = 1
context_feature_drift_pair_count = 0
deep_failed_pair_count = 7
primary = model_input_collision_still_exists_in_top_contexts
recommended_next_step = add_or_repair_candidate_action_consequence_features_before_more_sweeps
```

Tensor availability 本身不是空的：candidate path token、trace scalar、slack scalar、
per-candidate branch/cut/active-basis interaction 都存在。但在
`67c11b5ec80925ec` 这个 top failed context 中，仍有失败 pair 对模型输入不可区分。
这把下一步从“继续调 loss”收紧为：先审计 action-consequence 特征、signature 绑定、
long-horizon label provenance 和 batch-level consequence 是否缺失或被压缩掉。

## v116 / v117 / v118 对比

| run | best epoch | accepted | ROI | ROI CI low | safe CI low | false-delay | focused strict | local gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v116 | 1 | 36 | 4.602683 | 2.355012 | 0.903578 | 0.000000 | 0.935484 | pass |
| v117 | 3 | 20 | 5.435636 | 3.299236 | 0.838870 | 0.000000 | 0.870968 | fail |
| v118 | 2 | 54 | 3.795432 | 2.184186 | 0.933584 | 0.017483 | 0.880184 | fail |

v118 相比 v117，accepted coverage 和 safe CI 回升；但相比 v116，false-delay 从 0
变成越线，focused strict 也明显退化。因此 v118 不能替代 v116。

## kNN/OOD

未运行 v118 kNN/OOD。

理由：v118 已经在 validation local gate 上触发 `false_high_priority_on_delay_too_high`，
focused-pair gate 也低于 1.0。kNN/OOD safety shell 不能修复 focused same-context pair
ranking，也不能把一个 local false-delay 已越线的 checkpoint 升级成 Stage 4 candidate。

## Stage 3 状态

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
current_best_research_baseline = v116
primary_blocker = focused_pair_gate_below_1.0_and_context_action_consequence_gap
secondary_blocker = no_v118_epoch_satisfies_coverage_and_false_delay_constraints
```

## 下一步

1. 保留 v116 为当前最好研究基线。
2. 停止盲目 focused multiplier sweep；v117 和 v118 都把 v116 的 focused strict 推低。
3. 下一轮优先做 context/action-consequence feature repair：
   - 针对 `b6d808ebac2a6dd8`、`d519291840dd7000`、`67c11b5ec80925ec` 做样本级对照；
   - 检查 positive/negative batch 的 active-basis change、cut interaction、branch interaction、support change、tail retry consequence 是否在 candidate/batch/context feature 中可见；
   - 重点复核 `67c11b5ec80925ec` 的失败 pair，因为 top-context feature contrast 已发现至少 1 个 failed model-input collision；
   - 若特征已可见但排序仍错，再做 context-local margin shaping，而不是继续全局加大 loss multiplier。
4. 任何下一轮 checkpoint 仍必须先通过 Stage 3 deployment-facing gate，再谈 kNN/OOD 和 Stage 4 shadow。
