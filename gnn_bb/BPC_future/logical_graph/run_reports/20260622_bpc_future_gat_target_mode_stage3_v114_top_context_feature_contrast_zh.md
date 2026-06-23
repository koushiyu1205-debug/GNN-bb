# 2026-06-22 BPC_future GAT Target Mode Stage 3 v114 Top Context Feature Contrast 审计报告

## 目的

本报告只审计 v112/v113 focused same-context pair failure 的 top contexts 在当前 v107 5000-row 数据集中的模型可见输入。它不运行 BPC、pricing、RMP、worker 或 certificate。

## 机器字段

```text
status = gat_batch_impact_top_context_feature_contrast_audited
selected_context_hashes = ['b6d808ebac2a6dd8', '79fde658840fe2b8', 'ac15bc4e7e3d6fff', 'd519291840dd7000', 'ddcb5387bef3bf63', '4e481a6307fca228', 'b36178f6655c5f75', 'ac056820151e9ad7']
audited_row_count = 98
audited_pair_count = 566
failed_pair_count = 192
failed_pair_count_by_checkpoint = {'v112': 96, 'v113': 96}
model_input_collision_pair_count = 64
failed_model_input_collision_pair_count = 64
context_feature_drift_pair_count = 474
failed_context_feature_drift_pair_count = 128
deep_failed_pair_count = 18
primary = same_context_feature_drift_blocks_pair_gate_interpretability
recommended_next_step = audit_context_hash_and_context_feature_binding_before_retraining
production_ready = false
selector_can_certificate = false
all_checks_pass = true
```

## Tensor Availability

```json
{
  "batch_feature_dim": 18,
  "candidate_feature_dim": 40,
  "candidate_path_token_row_coverage": 1.0,
  "candidate_path_token_tensor_present": true,
  "candidate_signature_source_coverage": 1.0,
  "context_branch_cut_aggregate_fields": [
    "branch_constraint_count",
    "cut_dual_l1_norm"
  ],
  "context_feature_dim": 26,
  "per_candidate_branch_cut_interaction_present": false,
  "row_count": 98,
  "slack_scalar_field_count": 3,
  "slack_scalar_row_coverage": 1.0,
  "trace_scalar_field_count": 23,
  "trace_scalar_row_coverage": 1.0
}
```

## Top Contexts

| checkpoint | context | family | task | failed/pairs | deep_failed | input_collision | context_drift | primary |
|---|---|---|---:|---:|---:|---:|---:|---|
| v112 | b6d808ebac2a6dd8 | sector-wave | 20 | 36/55 | 0 | 8 | 47 | same_context_feature_drift_present |
| v112 | ac15bc4e7e3d6fff | sector-wave | 20 | 16/65 | 0 | 8 | 55 | same_context_feature_drift_present |
| v112 | 79fde658840fe2b8 | sector-wave | 20 | 14/72 | 0 | 8 | 54 | same_context_feature_drift_present |
| v112 | d519291840dd7000 | random-wave | 20 | 10/18 | 0 | 2 | 16 | same_context_feature_drift_present |
| v112 | ddcb5387bef3bf63 | random-wave | 20 | 7/30 | 0 | 3 | 27 | same_context_feature_drift_present |
| v112 | 4e481a6307fca228 | sector-wave | 20 | 6/21 | 0 | 3 | 18 | same_context_feature_drift_present |
| v112 | b36178f6655c5f75 | greedy-anchor | 20 | 4/4 | 0 | 0 | 4 | same_context_feature_drift_present |
| v112 | ac056820151e9ad7 | sector-wave | 20 | 3/18 | 0 | 0 | 16 | same_context_feature_drift_present |
| v113 | b6d808ebac2a6dd8 | sector-wave | 20 | 32/55 | 8 | 8 | 47 | same_context_feature_drift_present |
| v113 | 79fde658840fe2b8 | sector-wave | 20 | 18/72 | 0 | 8 | 54 | same_context_feature_drift_present |
| v113 | ac15bc4e7e3d6fff | sector-wave | 20 | 16/65 | 0 | 8 | 55 | same_context_feature_drift_present |
| v113 | d519291840dd7000 | random-wave | 20 | 10/18 | 6 | 2 | 16 | same_context_feature_drift_present |

## 结论

- 当前 v107 tensor 已包含 candidate path token、trace scalar 和 slack scalar；旧 feature-structure 审计里“path/timing/slack 全缺失”的结论对当前数据集需要收窄。
- top failed contexts 中，正负 pair 通常存在模型可见差异；继续单纯调 threshold 或放大 focused loss 已由 v113 证明风险较高。
- 仍缺少 per-candidate branch/cut 或 active-basis interaction；当前只有 context aggregate 的 `branch_constraint_count` / `cut_dual_l1_norm`。
- 该结论只用于 Stage 3 模型/特征修复，不是 Stage 4 readiness，也不能产生 certificate。

## Recommended Next Step

```json
{
  "primary": "audit_context_hash_and_context_feature_binding_before_retraining",
  "reason": "same context pairs have different context feature tensors"
}
```

## Output Artifacts

```text
summary = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v114_v112_v113_20260622/summary.json
rows = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v114_v112_v113_20260622/top_context_row_feature_records.jsonl
pairs = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v114_v112_v113_20260622/top_context_pair_feature_contrast_rows.jsonl
contexts = BPC_future/results/gat_batch_impact_top_context_feature_contrast_v114_v112_v113_20260622/top_context_feature_contrast_contexts.jsonl
```

## Exactness Boundary

- `diagnostic_only=true`；
- `runs_bpc_or_pricing=false`；
- `production_ready=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final certificate 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
