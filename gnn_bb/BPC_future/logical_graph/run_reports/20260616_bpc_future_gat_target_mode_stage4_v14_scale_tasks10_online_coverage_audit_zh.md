# 2026-06-16 BPC_future GAT Target Mode Stage 4 gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616 Online Coverage Audit 报告

## 结论

本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。
它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结论：

- exact safe id online overlap = 0;
- online sampled candidates = 254;
- online sample coverage complete = false;
- task-set 层有 40 个 key 重叠，覆盖 84 个 online candidates；
- task-set 层 offline conflict key count = 48。

因此 gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616 当前失败不是因为当前 online logs 完全没有相似列族，
而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。
而且 task-set / sequence 级放宽存在离线冲突，不能直接作为 HIGH_PRIORITY admission rule。

## 输入

```text
safe_source = BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616/safe_source.json
decision_records = BPC_future/results/gat_batch_impact_knn_ood_audit_v14_random_wave_task50_margin_tl130_scale_20260616/decision_records.jsonl
shadow_log_dir = BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/logs_tasks10
```

## Exact-id Coverage

```text
safe_candidate_id_count = 1198
offline_high_priority_unique_signature_ids = 1198
online_unique_signature_ids = 254
exact_safe_id_overlap_count = 0
exact_safe_id_overlap_rate_online = 0.0
coverage_gate_pass = false
```

## Coarse-key Coverage Diagnostic

```text
route_no_start.overlap_key_count = 0
route_no_start.online_candidate_hit_count = 0
route_no_start.offline_conflict_key_count = 4

sequence.overlap_key_count = 2
sequence.online_candidate_hit_count = 3
sequence.offline_conflict_key_count = 13

task_set.overlap_key_count = 40
task_set.online_candidate_hit_count = 84
task_set.offline_conflict_key_count = 48
task_set.online_conflict_candidate_hit_count = 12
```

重叠 task-set 样本：

```text
[1, 2, 10]
[1, 3, 10]
[1, 3, 5, 7]
[1, 3, 7, 10]
[1, 4, 10]
[1, 4, 5, 8]
[1, 4, 7]
[1, 4, 7, 10]
[1, 5]
[1, 8, 9]
[1, 9, 10]
[2, 3, 5]
[2, 3, 8]
[2, 3, 8, 9]
[2, 4, 7]
[2, 5]
[2, 5, 10]
[2, 6, 9]
[2, 8]
[2, 8, 10]
```

命中 online candidate 样本：

```text
{"candidate_id": "e982352226bf4fa1a188115c1b62764dee14bd23", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 8], "true_reduced_cost": -0.756379}
{"candidate_id": "b2d48e382d624f0f2cb3be068c6aa33f81815620", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [4, 6], "true_reduced_cost": -0.723053}
{"candidate_id": "a1519972ee3034f889eca412fe2c8ceabede36f1", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 4, 7], "true_reduced_cost": -0.538666}
{"candidate_id": "5d245b848f31ab350287905447da47b04bad0c51", "cg_iter": 2, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 10], "true_reduced_cost": -0.06528}
{"candidate_id": "993c97fd35dc14de2e3e6dcac57d296741c595f9", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 8, 10], "true_reduced_cost": -17.853779}
{"candidate_id": "6ebbaa5487c0d29f245f35e7ac1afe9f8bab2e55", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [6, 8, 10], "true_reduced_cost": -5.508889}
{"candidate_id": "13c657e0e1e204bea5825d79f215f935d3984245", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -2.592736}
{"candidate_id": "abaffa1b6a7277c75a1864ae3fbf19ef243e91d9", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 8], "true_reduced_cost": -0.476052}
{"candidate_id": "f297723d2ada8cc551f638f495efdf2d748a6045", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [4, 7], "true_reduced_cost": -3.706599}
{"candidate_id": "c154c35ca48c3067d78721f4afe9ca200a81cff4", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [4, 6], "true_reduced_cost": -1.371179}
{"candidate_id": "1536f940e8c414abf4b3822c15d257473ed74e28", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 5], "true_reduced_cost": -1.079036}
{"candidate_id": "f1d40453895481e8117c3aadd9d5196e1c2d83bd", "cg_iter": 2, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [4, 10], "true_reduced_cost": -0.353132}
{"candidate_id": "2db47b2ad3a40f925b48117a86ca417a9c6004a7", "cg_iter": 2, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 6, 9], "true_reduced_cost": -0.148077}
{"candidate_id": "3ab9f71037093c351ed5f92a81a9f22b6d12cd6c", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 9, 10], "true_reduced_cost": -37.74468125}
{"candidate_id": "2deef6fe9046800e7c62b77085b7485f467fc705", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 8], "true_reduced_cost": -2.062187}
{"candidate_id": "547f8ccf1015e8ad1b0a3ac52fd43e6e31483788", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 8], "true_reduced_cost": -0.636169}
{"candidate_id": "f152bd1f06fbf455ecea97fb13e6023aca87fca4", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 4, 7], "true_reduced_cost": -0.543809}
{"candidate_id": "10f85f5e966839736a5d24138acc42a489d1df06", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3, 8], "true_reduced_cost": -6.831981}
{"candidate_id": "cff9d1826eb44ea00bae6d76e58013079560568f", "cg_iter": 2, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5, 10], "true_reduced_cost": -0.393827}
{"candidate_id": "f700d23e57ecb4e557efe7b6b7f3c87ddc3ab989", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3, 5], "true_reduced_cost": -0.869075}
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
