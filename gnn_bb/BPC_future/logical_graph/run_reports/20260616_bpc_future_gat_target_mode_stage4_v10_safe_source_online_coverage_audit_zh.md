# 2026-06-16 BPC_future GAT Target Mode Stage 4 v10 Safe-source Online Coverage Audit 报告

## 结论

本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。
它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结论：

- exact safe id online overlap = 0;
- online sampled candidates = 75;
- online sample coverage complete = true;
- task-set 层有 10 个 key 重叠，覆盖 10 个 online candidates；
- task-set 层 offline conflict key count = 7。

因此 v10 safe-source 当前失败不是因为 20-task sector-wave 完全没有相似列族，
而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。
但 task-set/sequence 级放宽存在离线冲突，不能直接作为 HIGH_PRIORITY admission rule。

## 输入

```text
safe_source = BPC_future/results/gat_batch_impact_safe_source_v10_random_wave_task50_5751_20260616/safe_source.json
decision_records = BPC_future/results/gat_batch_impact_knn_ood_audit_v10_mixed_random_wave_task50_5751_knn34_20260616/decision_records.jsonl
shadow_log_dir = BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_fullsamples_20260616/logs_sector_tranq20_01_shadow_fullsamples
```

## Exact-id Coverage

```text
safe_candidate_id_count = 408
offline_high_priority_unique_signature_ids = 408
online_unique_signature_ids = 75
exact_safe_id_overlap_count = 0
exact_safe_id_overlap_rate_online = 0.0
coverage_gate_pass = false
```

## Coarse-key Coverage Diagnostic

```text
route_no_start.overlap_key_count = 0
route_no_start.online_candidate_hit_count = 0
route_no_start.offline_conflict_key_count = 2

sequence.overlap_key_count = 0
sequence.online_candidate_hit_count = 0
sequence.offline_conflict_key_count = 5

task_set.overlap_key_count = 10
task_set.online_candidate_hit_count = 10
task_set.offline_conflict_key_count = 7
task_set.online_conflict_candidate_hit_count = 1
```

重叠 task-set 样本：

```text
[1, 5]
[10, 17]
[12, 17]
[15, 17]
[2, 10, 14]
[3, 8, 11]
[4, 15, 17]
[6, 9]
[9, 15, 17]
[9, 17]
```

## 判定

```text
stage4_exact_safe_id_coverage_gate = failed
stage4_coarse_key_direct_admission_ready = false
stage4_next_direction = train_or_audit_context_aware_online_safe_source
```

下一步应做 context-aware / model-scored online safe-source，而不是把 exact id 改成
task-set 白名单直接上线。更宽的 key 只能作为 pricing priority / candidate mining hint，
进入 admission 前仍必须 true-RC verified，并且必须通过 precision / ROI / conflict gate。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```
