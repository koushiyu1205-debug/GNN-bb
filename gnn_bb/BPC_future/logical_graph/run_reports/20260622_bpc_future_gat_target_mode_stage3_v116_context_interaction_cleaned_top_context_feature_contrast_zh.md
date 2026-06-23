# 2026-06-22 BPC_future GAT Target Mode Stage 3 v114 Top Context Feature Contrast 审计报告

## 目的

本报告只审计 v112/v113 focused same-context pair failure 的 top contexts 在 `BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622` 数据集中的模型可见输入。它不运行 BPC、pricing、RMP、worker 或 certificate。

## 机器字段

```text
status = gat_batch_impact_top_context_feature_contrast_audited
dataset_dir = BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622
selected_context_hashes = ['b6d808ebac2a6dd8', '79fde658840fe2b8', 'ac15bc4e7e3d6fff', 'd519291840dd7000', 'ddcb5387bef3bf63', '4e481a6307fca228', 'b36178f6655c5f75', 'ac056820151e9ad7']
audited_row_count = 66
audited_pair_count = 242
failed_pair_count = 50
failed_pair_count_by_checkpoint = {'v112': 25, 'v113': 25}
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
failed_context_feature_drift_pair_count = 0
deep_failed_pair_count = 7
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
  "row_count": 66,
  "slack_scalar_field_count": 3,
  "slack_scalar_row_coverage": 1.0,
  "trace_scalar_field_count": 23,
  "trace_scalar_row_coverage": 1.0
}
```

## Top Contexts

| checkpoint | context | family | task | failed/pairs | deep_failed | input_collision | context_drift | primary |
|---|---|---|---:|---:|---:|---:|---:|---|
| v112 | 79fde658840fe2b8 | sector-wave | 20 | 6/30 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v112 | d519291840dd7000 | random-wave | 20 | 6/12 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v112 | ac15bc4e7e3d6fff | sector-wave | 20 | 4/35 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v112 | b36178f6655c5f75 | greedy-anchor | 20 | 4/4 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v112 | ddcb5387bef3bf63 | random-wave | 20 | 3/15 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v112 | 4e481a6307fca228 | sector-wave | 20 | 2/10 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v112 | b6d808ebac2a6dd8 | sector-wave | 20 | 0/15 | 0 | 0 | 0 | pair_passes |
| v113 | 79fde658840fe2b8 | sector-wave | 20 | 6/30 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v113 | d519291840dd7000 | random-wave | 20 | 6/12 | 4 | 0 | 0 | deep_misranking_despite_visible_inputs |
| v113 | ac15bc4e7e3d6fff | sector-wave | 20 | 4/35 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v113 | b36178f6655c5f75 | greedy-anchor | 20 | 4/4 | 0 | 0 | 0 | near_margin_misranking_despite_visible_inputs |
| v113 | ddcb5387bef3bf63 | random-wave | 20 | 3/15 | 1 | 0 | 0 | deep_misranking_despite_visible_inputs |

## 结论

- `BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622` tensor 已包含 candidate path token、trace scalar 和 slack scalar；旧 feature-structure 审计里“path/timing/slack 全缺失”的结论对当前数据集需要收窄。
- top failed contexts 中，正负 pair 通常存在模型可见差异；继续单纯调 threshold 或放大 focused loss 已由 v113 证明风险较高。
- 仍缺少 per-candidate branch/cut 或 active-basis interaction；当前只有 context aggregate 的 `branch_constraint_count` / `cut_dual_l1_norm`。
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
summary = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v116_context_interaction_cleaned_v112_v113_20260622/summary.json
rows = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v116_context_interaction_cleaned_v112_v113_20260622/top_context_row_feature_records.jsonl
pairs = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v116_context_interaction_cleaned_v112_v113_20260622/top_context_pair_feature_contrast_rows.jsonl
contexts = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v116_context_interaction_cleaned_v112_v113_20260622/top_context_feature_contrast_contexts.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
