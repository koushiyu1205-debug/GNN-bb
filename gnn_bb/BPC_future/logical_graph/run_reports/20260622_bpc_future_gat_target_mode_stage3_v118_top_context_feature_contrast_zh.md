# 2026-06-22 BPC_future GAT Target Mode Stage 3 v118 Top Context Feature Contrast 审计报告

## 目的

本报告只审计 v118 focused same-context pair failure 的 top contexts 在 `BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622` 数据集中的模型可见输入。它不运行 BPC、pricing、RMP、worker 或 certificate。

## 机器字段

```text
status = gat_batch_impact_top_context_feature_contrast_audited
dataset_dir = BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622
selected_context_hashes = ['b6d808ebac2a6dd8', 'd519291840dd7000', '67c11b5ec80925ec', '62c86745ed2b3aaa', '9f80ae35ea87da5b', '84ae11479ed592d4', 'ac15bc4e7e3d6fff', '79fde658840fe2b8']
audited_row_count = 54
audited_pair_count = 103
failed_pair_count = 26
failed_pair_count_by_checkpoint = {'v118': 26}
model_input_collision_pair_count = 1
failed_model_input_collision_pair_count = 1
context_feature_drift_pair_count = 0
failed_context_feature_drift_pair_count = 0
deep_failed_pair_count = 7
primary = model_input_collision_still_exists_in_top_contexts
recommended_next_step = add_or_repair_candidate_action_consequence_features_before_more_sweeps
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## Tensor Availability

```json
{
  "batch_feature_dim": 18,
  "candidate_feature_dim": 59,
  "candidate_path_token_row_coverage": 1.0,
  "candidate_path_token_tensor_present": true,
  "candidate_signature_source_coverage": 1.0,
  "context_branch_cut_aggregate_fields": [
    "branch_constraint_count",
    "cut_dual_l1_norm"
  ],
  "context_feature_dim": 26,
  "per_candidate_branch_cut_interaction_present": true,
  "row_count": 54,
  "slack_scalar_field_count": 3,
  "slack_scalar_row_coverage": 1.0,
  "trace_scalar_field_count": 23,
  "trace_scalar_row_coverage": 1.0
}
```

## Top Contexts

| checkpoint | context | family | task | failed/pairs | deep_failed | input_collision | context_drift | primary |
|---|---|---|---:|---:|---:|---:|---:|---|
| v118 | b6d808ebac2a6dd8 | sector-wave | 20 | 9/15 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v118 | d519291840dd7000 | random-wave | 20 | 8/12 | 4 | 0 | 0 | deep_misranking_despite_visible_inputs |
| v118 | 67c11b5ec80925ec | random-wave | 20 | 5/5 | 1 | 1 | 0 | model_input_collision_present |
| v118 | 62c86745ed2b3aaa | random-wave | 20 | 2/2 | 2 | 0 | 0 | deep_misranking_despite_visible_inputs |
| v118 | 84ae11479ed592d4 | greedy-anchor | 20 | 1/2 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v118 | 9f80ae35ea87da5b | random-wave | 30 | 1/2 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v118 | 79fde658840fe2b8 | sector-wave | 20 | 0/30 | 0 | 0 | 0 | pair_passes |
| v118 | ac15bc4e7e3d6fff | sector-wave | 20 | 0/35 | 0 | 0 | 0 | pair_passes |

## 结论

- `BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622` tensor 已包含 candidate path token、trace scalar 和 slack scalar；旧 feature-structure 审计里“path/timing/slack 全缺失”的结论对当前数据集需要收窄。
- top failed contexts 中，正负 pair 通常存在模型可见差异；继续单纯调 threshold 或放大 focused loss 的风险较高。
- tensor schema 已包含 per-candidate branch/cut 或 active-basis interaction；当前主要问题不是这些字段整体缺失。
- 该结论只用于 Stage 3 模型/特征修复，不是 Stage 4 readiness，也不能产生 certificate。

## Recommended Next Step

```json
{
  "primary": "add_or_repair_candidate_action_consequence_features_before_more_sweeps",
  "reason": "some failed positive/negative pairs are still indistinguishable to model inputs"
}
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v118_context_interaction_cleaned_admission_mild_20260622/summary.json
rows = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v118_context_interaction_cleaned_admission_mild_20260622/top_context_row_feature_records.jsonl
pairs = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v118_context_interaction_cleaned_admission_mild_20260622/top_context_pair_feature_contrast_rows.jsonl
contexts = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v118_context_interaction_cleaned_admission_mild_20260622/top_context_feature_contrast_contexts.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
