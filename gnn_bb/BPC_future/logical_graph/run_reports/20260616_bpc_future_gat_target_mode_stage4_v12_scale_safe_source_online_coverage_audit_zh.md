# 2026-06-16 BPC_future GAT Target Mode Stage 4 v12 scale safe-source Online Coverage Audit 报告

## 结论

本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。
它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结论：

- exact safe id online overlap = 0;
- online sampled candidates = 75;
- online sample coverage complete = true;
- task-set 层有 5 个 key 重叠，覆盖 5 个 online candidates；
- task-set 层 offline conflict key count = 0。

因此 v12 scale safe-source 当前失败不是因为 20-task sector-wave 完全没有相似列族，
而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。
task-set 级放宽虽然本次没有离线冲突，但 coverage 仍很低，不能直接作为 HIGH_PRIORITY admission rule。

## 输入

```text
safe_source = BPC_future/results/gat_batch_impact_safe_source_v12_coverage_aware_scale_20260616/safe_source.json
decision_records = BPC_future/results/gat_batch_impact_knn_ood_audit_v12_coverage_aware_scale_20260616/decision_records.jsonl
shadow_log_dir = BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_fullsamples_20260616/logs_sector_tranq20_01_shadow_fullsamples
```

## Exact-id Coverage

```text
safe_candidate_id_count = 142
offline_high_priority_unique_signature_ids = 142
online_unique_signature_ids = 75
exact_safe_id_overlap_count = 0
exact_safe_id_overlap_rate_online = 0.0
coverage_gate_pass = false
```

## Coarse-key Coverage Diagnostic

```text
route_no_start.overlap_key_count = 0
route_no_start.online_candidate_hit_count = 0
route_no_start.offline_conflict_key_count = 0

sequence.overlap_key_count = 0
sequence.online_candidate_hit_count = 0
sequence.offline_conflict_key_count = 0

task_set.overlap_key_count = 5
task_set.online_candidate_hit_count = 5
task_set.offline_conflict_key_count = 0
task_set.online_conflict_candidate_hit_count = 0
```

重叠 task-set 样本：

```text
[1, 5]
[4, 15, 17]
[6, 9]
[9, 15, 17]
[9, 17]
```

命中 online candidate 样本：

```text
{"candidate_id": "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -19.76771125}
{"candidate_id": "bfa93dc9f590902712e1de6b243615c5a3adae04", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [9, 15, 17], "true_reduced_cost": -5.350065}
{"candidate_id": "9e3b6b64ee5dd65f00a7cea9c026ca69984721ea", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [4, 15, 17], "true_reduced_cost": -5.0754}
{"candidate_id": "4d0f056a3c77a40f742321dd09be0c9b020628db", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [6, 9], "true_reduced_cost": -1.397984}
{"candidate_id": "9f76ef17461812cf5cb0ef885e4736e842ca17b0", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [9, 17], "true_reduced_cost": -1.397984}
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
