# 2026-06-16 BPC_future GAT Stage 4 v14 Online Coverage Audit 报告

## 结论

v14 global / scale safe-source 已完成 5/10/20 online shadow coverage
审计和 model-scored online safe-source 审计。本轮是只读审计：不运行
BPC / pricing / RMP，不改变 admission，不产生 lower bound 或 certificate。

核心变化是：相比 v10/v12 在 20-task shadow 上 exact safe-id hit 为 0，v14
在 `sector_tranq20_01` full-sample shadow 上已经出现 exact-id 覆盖信号：

```text
global 20-task exact_safe_id_overlap_count = 32 / 75
scale  20-task exact_safe_id_overlap_count = 32 / 75
```

但这仍不是 mutating admission 通过。exact-id 命中只能说明 offline safe-source
能识别当前 online shadow 中的一部分 true-RC negative journey；它还没有证明这些
列加入 RMP 后会改善 objective、dual、basis、tail retry 或 final proof tail。
因此：

```text
stage4_model_scored_online_safe_source_ready = false
stage4_mutating_admission_ready = false
admission_ready_count = 0
```

## Coverage 结果

| source | shadow | safe ids | online sampled | exact safe-id hits | route hits | sequence hits | task-set hits | task-set conflict hits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| global | tasks5 guarded full | 1226 | 75 | 0 | 0 | 0 | 41 | 20 |
| global | tasks10 guarded full | 1226 | 254 | 0 | 0 | 3 | 84 | 12 |
| global | tasks20 sector_tranq20 full | 1226 | 75 | 32 | 32 | 32 | 39 | 5 |
| scale | tasks5 guarded full | 1198 | 75 | 0 | 0 | 0 | 41 | 20 |
| scale | tasks10 guarded full | 1198 | 254 | 0 | 0 | 3 | 84 | 12 |
| scale | tasks20 sector_tranq20 full | 1198 | 75 | 32 | 32 | 32 | 39 | 5 |

5/10 的 exact safe-id coverage gate 仍失败。task-set 粗键虽然有 overlap，但
conflict 明显，不能作为 safe-source 或 admission rule。

20-task 的 exact safe-id coverage gate 在这个 `sector_tranq20_01` full-sample
shadow 上通过，且 sample coverage complete：

```text
online_declared_candidate_journeys = 75
online_sampled_candidate_journeys = 75
exact_safe_id_overlap_rate_online = 0.4266666666666667
online_by_pricing_kind = {'exact': 60, 'heuristic': 15}
```

这个信号足以把下一步从“找不到 online exact id”推进为“对这 32 个 exact-id hit
采集 online trajectory ROI / tail-risk”。但不能跨 benchmark、跨 family 或跨
task scale 推广。

## Model-scored 审计

model-scored online safe-source 对六个组合的结论一致：

```text
tasks5 global/scale:
  exact_safe_id_hit_count = 0
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0

tasks10 global/scale:
  exact_safe_id_hit_count = 0
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0

tasks20 global/scale:
  exact_safe_id_hit_count = 32
  diagnostic_priority_hint_count = 0
  admission_ready_count = 0
```

20-task blocker 已从 `exact_safe_id_overlap_missing` 变成：

```text
exact_safe_id_overlap_is_not_trajectory_roi_proof
online_trajectory_roi_unverified
```

也就是说，本轮找到的是 candidate coverage，不是 trajectory ROI proof。

## Exactness Boundary

本轮所有结果都保持以下边界：

```text
diagnostic_only = true
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
negative_columns_must_remain_eventually_reachable = true
```

GAT / CBF / kNN / OOD 仍只能帮助 column generation 更聪明地排序和调度候选。
最终 optimality certificate 仍必须由当前 branch/cut/dual 下 exact pricing 对完整
配置宇宙执行 no-negative closure。

## 产物

Coverage summaries:

```text
BPC_future/results/gat_safe_source_online_coverage_v14_global_tasks5_guarded_full_20260616/summary.json
BPC_future/results/gat_safe_source_online_coverage_v14_global_tasks10_guarded_full_20260616/summary.json
BPC_future/results/gat_safe_source_online_coverage_v14_global_tranq20_01_20260616/summary.json
BPC_future/results/gat_safe_source_online_coverage_v14_scale_tasks5_guarded_full_20260616/summary.json
BPC_future/results/gat_safe_source_online_coverage_v14_scale_tasks10_guarded_full_20260616/summary.json
BPC_future/results/gat_safe_source_online_coverage_v14_scale_tranq20_01_20260616/summary.json
```

Model-scored summaries:

```text
BPC_future/results/gat_model_scored_online_safe_source_v14_global_tasks5_guarded_full_20260616/summary.json
BPC_future/results/gat_model_scored_online_safe_source_v14_global_tasks10_guarded_full_20260616/summary.json
BPC_future/results/gat_model_scored_online_safe_source_v14_global_tranq20_01_20260616/summary.json
BPC_future/results/gat_model_scored_online_safe_source_v14_scale_tasks5_guarded_full_20260616/summary.json
BPC_future/results/gat_model_scored_online_safe_source_v14_scale_tasks10_guarded_full_20260616/summary.json
BPC_future/results/gat_model_scored_online_safe_source_v14_scale_tranq20_01_20260616/summary.json
```

Individual reports:

```text
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_global_tasks5_online_coverage_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_global_tasks10_online_coverage_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_global_20_online_coverage_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_scale_tasks5_online_coverage_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_scale_tasks10_online_coverage_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_scale_20_online_coverage_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_global_tasks5_model_scored_online_safe_source_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_global_tasks10_model_scored_online_safe_source_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_global_20_model_scored_online_safe_source_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_scale_tasks5_model_scored_online_safe_source_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_scale_tasks10_model_scored_online_safe_source_audit_zh.md
BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_scale_20_model_scored_online_safe_source_audit_zh.md
```

## 下一步

已把 20-task `sector_tranq20_01` 的 32 个 exact-id hit 导出为
target-materialization candidates，并生成 batch8 A/B runbook：

```text
candidates =
  BPC_future/results/gat_exact_safe_hit_target_candidates_v14_global_tranq20_01_20260616/candidates.json
runbook =
  BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/summary.json
runbook_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v14_exact_safe_hits_batch8_runbook_zh.md

input_candidate_count = 32
worker_batch_size = 8
candidate_group_count = 4
candidate_batch_counts = [8, 8, 8, 8]
```

后续只允许执行这个 explicit opt-in runbook 采集 online trajectory ROI：
记录加入前后 RMP objective、dual movement、basis churn、pricing/exact calls、
tail retry 和 certificate tail。采样结论必须回写成 trajectory utility label，
再进入 Stage 3 训练和 Stage 4 admission gate。

5/10 当前没有 exact-id hit，不能启用 safe-source admission；若要继续推进 5/10，
需要 same-context 的 trajectory ROI rows，而不是把 task-set overlap 当作准入证据。
