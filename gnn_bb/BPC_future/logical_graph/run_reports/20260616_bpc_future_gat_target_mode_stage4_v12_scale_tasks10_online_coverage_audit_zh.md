# 2026-06-16 BPC_future GAT Target Mode Stage 4 v12 scale safe-source Online Coverage Audit 报告

## 结论

本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。
它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结论：

- exact safe id online overlap = 0;
- online sampled candidates = 254;
- online sample coverage complete = false;
- task-set 层有 8 个 key 重叠，覆盖 14 个 online candidates；
- task-set 层 offline conflict key count = 0。

因此 v12 scale safe-source 当前失败不是因为当前 online logs 完全没有相似列族，
而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。
task-set 级放宽虽然本次没有离线冲突，但 coverage 仍很低，不能直接作为 HIGH_PRIORITY admission rule。

## 输入

```text
safe_source = BPC_future/results/gat_batch_impact_safe_source_v12_coverage_aware_scale_20260616/safe_source.json
decision_records = BPC_future/results/gat_batch_impact_knn_ood_audit_v12_coverage_aware_scale_20260616/decision_records.jsonl
shadow_log_dir = BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/logs_tasks10
```

## Exact-id Coverage

```text
safe_candidate_id_count = 142
offline_high_priority_unique_signature_ids = 142
online_unique_signature_ids = 254
exact_safe_id_overlap_count = 0
exact_safe_id_overlap_rate_online = 0.0
coverage_gate_pass = false
```

## Coarse-key Coverage Diagnostic

```text
route_no_start.overlap_key_count = 0
route_no_start.online_candidate_hit_count = 0
route_no_start.offline_conflict_key_count = 0

sequence.overlap_key_count = 1
sequence.online_candidate_hit_count = 1
sequence.offline_conflict_key_count = 0

task_set.overlap_key_count = 8
task_set.online_candidate_hit_count = 14
task_set.offline_conflict_key_count = 0
task_set.online_conflict_candidate_hit_count = 0
```

重叠 task-set 样本：

```text
[1, 3, 5, 7]
[1, 4, 7]
[1, 4, 7, 10]
[1, 5]
[2, 5]
[2, 8]
[4, 9]
[6, 9]
```

命中 online candidate 样本：

```text
{"candidate_id": "e982352226bf4fa1a188115c1b62764dee14bd23", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 8], "true_reduced_cost": -0.756379}
{"candidate_id": "13c657e0e1e204bea5825d79f215f935d3984245", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -2.592736}
{"candidate_id": "abaffa1b6a7277c75a1864ae3fbf19ef243e91d9", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 8], "true_reduced_cost": -0.476052}
{"candidate_id": "547f8ccf1015e8ad1b0a3ac52fd43e6e31483788", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 8], "true_reduced_cost": -0.636169}
{"candidate_id": "f152bd1f06fbf455ecea97fb13e6023aca87fca4", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 4, 7], "true_reduced_cost": -0.543809}
{"candidate_id": "48524c2255f5389ab75eccfd47ae00ac2187d8a9", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [4, 9], "true_reduced_cost": -1.542911}
{"candidate_id": "7bfb0f35c214923f0b5318d481c1a990217b7f53", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5], "true_reduced_cost": -0.0714}
{"candidate_id": "0c53140affb772463c60ce1a98d3a1b1e57a1834", "cg_iter": 2, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [6, 9], "true_reduced_cost": -1.259105}
{"candidate_id": "5d6caa0a1c36df6370d84ba7da9928d4fd824e5d", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 4, 7, 10], "true_reduced_cost": -3.967583}
{"candidate_id": "e42d85cd4cb7b2dd1f02406afd344b3645b93b82", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5], "true_reduced_cost": -2.530025}
{"candidate_id": "f6ad60289171849153014f8c307ef79bd466bf02", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -2.094478}
{"candidate_id": "4edddcb21599b7b0a215a0b550545609c148e3e6", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 3, 5, 7], "true_reduced_cost": -14.087768333}
{"candidate_id": "04349af7103f8ac587ebd17c65e60577a36430b2", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [6, 9], "true_reduced_cost": -0.117178}
{"candidate_id": "4743decd16b187dff35dde7d1fdf94d8cbaa2f78", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 8], "true_reduced_cost": -2.082141}
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
