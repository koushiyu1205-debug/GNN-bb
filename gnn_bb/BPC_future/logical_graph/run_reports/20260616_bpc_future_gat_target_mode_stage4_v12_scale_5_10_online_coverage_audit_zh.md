# 2026-06-16 BPC_future GAT Stage 4 v12 Scale 5/10 Online Coverage Audit 报告

## 结论

本报告复用已有 5/10 guarded full run 的 online shadow logs，只读 Stage 3 v12
scale safe-source 和 kNN/OOD decision records；不运行 BPC / pricing / RMP，
不改变 admission，也不产生 certificate。

核心结论：

```text
tasks5.exact_safe_id_overlap_count = 0
tasks10.exact_safe_id_overlap_count = 0
tasks5.online_sampled_candidate_journeys = 75
tasks10.online_sampled_candidate_journeys = 254
tasks5.task_set_online_candidate_hit_count = 9
tasks10.task_set_online_candidate_hit_count = 14
tasks5.model_scored_diagnostic_hint_count = 0
tasks10.model_scored_diagnostic_hint_count = 0
tasks5.coverage_gate_pass = false
tasks10.coverage_gate_pass = false
```

这说明 v12 scale safe-source 虽然通过了 Stage 3 offline precision / ROI /
accepted-bad-mode gate，但 exact signature id 白名单在 5/10 online candidate
上仍没有命中。进一步做 context-aware model-scored 审计后，5/10 balanced
online candidates 也没有任何可升级的 diagnostic priority hint。如果直接进入
guarded full no-regression，它大概率仍是 `no_online_safe_hit` / pass-through，
不会产生真实 HIGH_PRIORITY ROI。

## 输入

```text
safe_source =
  BPC_future/results/gat_batch_impact_safe_source_v12_coverage_aware_scale_20260616/safe_source.json

decision_records =
  BPC_future/results/gat_batch_impact_knn_ood_audit_v12_coverage_aware_scale_20260616/decision_records.jsonl

tasks5 logs =
  BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/logs_tasks5

tasks10 logs =
  BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/logs_tasks10
```

输出 artifact：

```text
BPC_future/results/gat_safe_source_online_coverage_v12_scale_tasks5_guarded_full_20260616/summary.json
BPC_future/results/gat_safe_source_online_coverage_v12_scale_tasks10_guarded_full_20260616/summary.json
BPC_future/results/gat_model_scored_online_safe_source_v12_scale_tasks5_guarded_full_20260616/summary.json
BPC_future/results/gat_model_scored_online_safe_source_v12_scale_tasks10_guarded_full_20260616/summary.json
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v12_scale_tasks5_online_coverage_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v12_scale_tasks10_online_coverage_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v12_scale_tasks5_model_scored_online_safe_source_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v12_scale_tasks10_model_scored_online_safe_source_audit_zh.md
```

## tasks5

```text
online_shadow_events = 24
online_declared_candidate_journeys = 82
online_sampled_candidate_journeys = 75
online_sample_coverage_complete = false
online_unique_signature_ids = 75
safe_candidate_id_count = 142
exact_safe_id_overlap_count = 0
exact_safe_id_overlap_rate_online = 0.0

route_no_start.online_candidate_hit_count = 0
sequence.online_candidate_hit_count = 0
task_set.overlap_key_count = 3
task_set.online_candidate_hit_count = 9
task_set.offline_conflict_key_count = 0
```

重叠 task-set 样本：

```text
[1,4], [1,5], [2,5]
```

## tasks10

```text
online_shadow_events = 89
online_declared_candidate_journeys = 494
online_sampled_candidate_journeys = 254
online_sample_coverage_complete = false
online_unique_signature_ids = 254
safe_candidate_id_count = 142
exact_safe_id_overlap_count = 0
exact_safe_id_overlap_rate_online = 0.0

route_no_start.online_candidate_hit_count = 0
sequence.online_candidate_hit_count = 1
task_set.overlap_key_count = 8
task_set.online_candidate_hit_count = 14
task_set.offline_conflict_key_count = 0
```

重叠 task-set 样本：

```text
[1,3,5,7], [1,4,7], [1,4,7,10], [1,5], [2,5], [2,8], [4,9], [6,9]
```

## Context-aware Model-scored 补充审计

对上述 5/10 guarded full logs 继续运行 audit-only model-scored online
safe-source 审计。该审计把 coarse-key evidence 作为候选线索，但要求 online
family / task scale 与 offline evidence 兼容；因此 20-task sector/random 的
high-ROI 证据不能迁移到 balanced 5/10。

```text
tasks5:
  online_sampled_candidate_journeys = 75
  exact_safe_id_hit_count = 0
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0
  observed_online_context = balanced:5

tasks10:
  online_sampled_candidate_journeys = 254
  exact_safe_id_hit_count = 0
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0
  observed_online_context = balanced:10
```

输出 evidence 中仍能看到部分 5/10 online candidates 命中 sector-wave:20 的
offline high-ROI task-set / sequence evidence，但 `context_compatible=false`。
因此这些命中只能解释为跨 family/scale 的相似形状，不能作为 5/10
HIGH_PRIORITY admission。

## 判定

```text
stage4_v12_scale_5_10_exact_safe_id_coverage_gate = failed
stage4_v12_scale_5_10_model_scored_context_gate = failed
stage4_v12_scale_guarded_full_expected_behavior = pass_through_no_online_safe_hit
stage4_v12_scale_mutating_admission_ready = false
stage4_v12_scale_high_priority_roi_ready = false
```

下一步不应把 exact safe-id 白名单直接当成 5/10 或 20-task 的 mutating
admission source。更合理的方向是把这些 task-set / sequence 粗键命中作为
diagnostic candidate-mining signal，再通过 same-context target-materialization
或 online trajectory ROI 标签验证；只有 exact current true-RC、precision、ROI、
accepted bad-mode 和 coverage 都过 gate 的规则，才允许进入 guarded mutating A/B。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```
