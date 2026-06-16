# 2026-06-16 BPC_future GAT Target Mode Stage 4 gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616 Online Coverage Audit 报告

## 结论

本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。
它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结论：

- exact safe id online overlap = 0;
- online sampled candidates = 75;
- online sample coverage complete = false;
- task-set 层有 12 个 key 重叠，覆盖 41 个 online candidates；
- task-set 层 offline conflict key count = 48。

因此 gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616 当前失败不是因为当前 online logs 完全没有相似列族，
而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。
而且 task-set / sequence 级放宽存在离线冲突，不能直接作为 HIGH_PRIORITY admission rule。

## 输入

```text
safe_source = BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616/safe_source.json
decision_records = BPC_future/results/gat_batch_impact_knn_ood_audit_v14_random_wave_task50_margin_tl130_scale_20260616/decision_records.jsonl
shadow_log_dir = BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/logs_tasks5
```

## Exact-id Coverage

```text
safe_candidate_id_count = 1198
offline_high_priority_unique_signature_ids = 1198
online_unique_signature_ids = 75
exact_safe_id_overlap_count = 0
exact_safe_id_overlap_rate_online = 0.0
coverage_gate_pass = false
```

## Coarse-key Coverage Diagnostic

```text
route_no_start.overlap_key_count = 0
route_no_start.online_candidate_hit_count = 0
route_no_start.offline_conflict_key_count = 4

sequence.overlap_key_count = 0
sequence.online_candidate_hit_count = 0
sequence.offline_conflict_key_count = 13

task_set.overlap_key_count = 12
task_set.online_candidate_hit_count = 41
task_set.offline_conflict_key_count = 48
task_set.online_conflict_candidate_hit_count = 20
```

重叠 task-set 样本：

```text
[1, 2, 3, 5]
[1, 2, 4, 5]
[1, 4]
[1, 5]
[2, 3]
[2, 3, 5]
[2, 4]
[2, 4, 5]
[2, 5]
[3, 4]
[3, 5]
[4, 5]
```

命中 online candidate 样本：

```text
{"candidate_id": "348432b1bf2044f503689791432975a82b020cf7", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3, 5], "true_reduced_cost": -0.026864}
{"candidate_id": "a57271eec9bf85a158d2fd5c0485a59c10e1bf8f", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 2, 3, 5], "true_reduced_cost": -0.009904}
{"candidate_id": "a7ea52e07ec6548b93ad94006682f1308ee4e3f5", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 4], "true_reduced_cost": -1.662824}
{"candidate_id": "fa771a1cfcc448453ec18042474aef3052c04ea8", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 4], "true_reduced_cost": -1.662824}
{"candidate_id": "eabc331d2eb979fb768d0c32ad3f44f98c5cc733", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -1.037756}
{"candidate_id": "f2d5ed4c5de6dd78f8de83ecbf4ed1d896b8c0bb", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5], "true_reduced_cost": -1.037756}
{"candidate_id": "ca024f612c76e69f579cd5e1a7cd196a725a031e", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3], "true_reduced_cost": -1.193155}
{"candidate_id": "d31dfec8db33ea35f4a77181366ba6b1633e48f5", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 5], "true_reduced_cost": -1.193155}
{"candidate_id": "216a8c3dc136d34d5da3deea21ea8954c8d5ed74", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 4], "true_reduced_cost": -0.85992}
{"candidate_id": "878b8ba85826bdebf831a2122c5df2a971cc3df2", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3], "true_reduced_cost": -0.583913}
{"candidate_id": "818abf6847a4e3b216ddce4fa43ee4e0792916d8", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 4, 5], "true_reduced_cost": -0.428911}
{"candidate_id": "654ac71dc8d07ea728a9825f3f0f978cfda1f209", "cg_iter": 3, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3, 5], "true_reduced_cost": -9.277007333}
{"candidate_id": "8d8adfd28d9a9bd1051b67e420e821df2a56cce7", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 4], "true_reduced_cost": -0.229281}
{"candidate_id": "1dc8ca438c48e6abbde27a8a494536cfa2b4636f", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 4], "true_reduced_cost": -0.114641}
{"candidate_id": "93c253c804939ebbe912ab0f34d15f7955293546", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5], "true_reduced_cost": -0.073206}
{"candidate_id": "3e94f8edeaa6da417acf1ab43404cb058a658a5a", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 4], "true_reduced_cost": -0.018889}
{"candidate_id": "72c684d85341b4c64aa851fbe6f103897da24550", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -1.413124}
{"candidate_id": "94ca14514eebc525ca9ce09f7c0d89e5948a0d23", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 4], "true_reduced_cost": -0.349006}
{"candidate_id": "6bc50c2b44be0d742d7bfa80e26e312f29c96db8", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3], "true_reduced_cost": -0.207835}
{"candidate_id": "0410640b329857d61e06388cc15395cd3107cfb2", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3], "true_reduced_cost": -1.01246}
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
