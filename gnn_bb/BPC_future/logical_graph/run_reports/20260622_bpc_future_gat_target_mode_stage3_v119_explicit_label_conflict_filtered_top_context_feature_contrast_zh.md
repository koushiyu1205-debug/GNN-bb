# 2026-06-22 BPC_future GAT Target Mode Stage 3 v119 Top Context Feature Contrast 审计报告

## 目的

本报告只审计 v119 focused same-context pair failure 的 top contexts 在 `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622` 数据集中的模型可见输入。它不运行 BPC、pricing、RMP、worker 或 certificate。

## 机器字段

```text
status = gat_batch_impact_top_context_feature_contrast_audited
dataset_dir = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
selected_context_hashes = ['b36178f6655c5f75', '9f80ae35ea87da5b', '62c86745ed2b3aaa', 'a0f80eb374f29f44', 'be33b2560df0147a', '9a2ca522ff49991c', '4e481a6307fca228', 'ce3508e12ad69da7']
audited_row_count = 31
audited_pair_count = 28
failed_pair_count = 10
failed_pair_count_by_checkpoint = {'v119': 10}
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
failed_context_feature_drift_pair_count = 0
deep_failed_pair_count = 3
primary = visible_inputs_differ_but_model_still_misranks
recommended_next_step = tighten_context_local_pairwise_ranking_head
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
  "row_count": 31,
  "slack_scalar_field_count": 3,
  "slack_scalar_row_coverage": 1.0,
  "trace_scalar_field_count": 23,
  "trace_scalar_row_coverage": 1.0
}
```

## Top Contexts

| checkpoint | context | family | task | failed/pairs | deep_failed | input_collision | context_drift | primary |
|---|---|---|---:|---:|---:|---:|---:|---|
| v119 | b36178f6655c5f75 | greedy-anchor | 20 | 3/4 | 2 | 0 | 0 | deep_misranking_despite_visible_inputs |
| v119 | 62c86745ed2b3aaa | random-wave | 20 | 2/2 | 1 | 0 | 0 | deep_misranking_despite_visible_inputs |
| v119 | 9f80ae35ea87da5b | random-wave | 30 | 2/2 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v119 | 9a2ca522ff49991c | random-wave | 50 | 1/1 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v119 | a0f80eb374f29f44 | random-wave | 30 | 1/2 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v119 | be33b2560df0147a | random-wave | 30 | 1/1 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v119 | 4e481a6307fca228 | sector-wave | 20 | 0/10 | 0 | 0 | 0 | pair_passes |
| v119 | ce3508e12ad69da7 | sector-wave | 20 | 0/6 | 0 | 0 | 0 | pair_passes |

## 结论

- `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622` tensor 已包含 candidate path token、trace scalar 和 slack scalar；旧 feature-structure 审计里“path/timing/slack 全缺失”的结论对当前数据集需要收窄。
- top failed contexts 中，正负 pair 通常存在模型可见差异；继续单纯调 threshold 或放大 focused loss 的风险较高。
- tensor schema 已包含 per-candidate branch/cut 或 active-basis interaction；当前主要问题不是这些字段整体缺失。
- 该结论只用于 Stage 3 模型/特征修复，不是 Stage 4 readiness，也不能产生 certificate。

## Recommended Next Step

```json
{
  "primary": "tighten_context_local_pairwise_ranking_head",
  "reason": "model-visible tensors differ and no direct schema blocker was detected"
}
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v119_explicit_label_conflict_filtered_20260622/summary.json
rows = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v119_explicit_label_conflict_filtered_20260622/top_context_row_feature_records.jsonl
pairs = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v119_explicit_label_conflict_filtered_20260622/top_context_pair_feature_contrast_rows.jsonl
contexts = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v119_explicit_label_conflict_filtered_20260622/top_context_feature_contrast_contexts.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
