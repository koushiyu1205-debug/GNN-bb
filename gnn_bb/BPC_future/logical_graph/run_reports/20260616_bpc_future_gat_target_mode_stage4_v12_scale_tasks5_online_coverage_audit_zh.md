# 2026-06-16 BPC_future GAT Target Mode Stage 4 v12 scale safe-source Online Coverage Audit 报告

## 结论

本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。
它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结论：

- exact safe id online overlap = 0;
- online sampled candidates = 75;
- online sample coverage complete = false;
- task-set 层有 3 个 key 重叠，覆盖 9 个 online candidates；
- task-set 层 offline conflict key count = 0。

因此 v12 scale safe-source 当前失败不是因为当前 online logs 完全没有相似列族，
而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。
task-set 级放宽虽然本次没有离线冲突，但 coverage 仍很低，不能直接作为 HIGH_PRIORITY admission rule。

## 输入

```text
safe_source = BPC_future/results/gat_batch_impact_safe_source_v12_coverage_aware_scale_20260616/safe_source.json
decision_records = BPC_future/results/gat_batch_impact_knn_ood_audit_v12_coverage_aware_scale_20260616/decision_records.jsonl
shadow_log_dir = BPC_future/results/gat_target_mode_stage4_v10_safe_source_guarded_full_20260616/logs_tasks5
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

task_set.overlap_key_count = 3
task_set.online_candidate_hit_count = 9
task_set.offline_conflict_key_count = 0
task_set.online_conflict_candidate_hit_count = 0
```

重叠 task-set 样本：

```text
[1, 4]
[1, 5]
[2, 5]
```

命中 online candidate 样本：

```text
{"candidate_id": "a7ea52e07ec6548b93ad94006682f1308ee4e3f5", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 4], "true_reduced_cost": -1.662824}
{"candidate_id": "eabc331d2eb979fb768d0c32ad3f44f98c5cc733", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -1.037756}
{"candidate_id": "f2d5ed4c5de6dd78f8de83ecbf4ed1d896b8c0bb", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5], "true_reduced_cost": -1.037756}
{"candidate_id": "1dc8ca438c48e6abbde27a8a494536cfa2b4636f", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 4], "true_reduced_cost": -0.114641}
{"candidate_id": "93c253c804939ebbe912ab0f34d15f7955293546", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5], "true_reduced_cost": -0.073206}
{"candidate_id": "72c684d85341b4c64aa851fbe6f103897da24550", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -1.413124}
{"candidate_id": "1c109278e9c4c333187a1672e8d7890ecce6b7af", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -0.784913}
{"candidate_id": "db096540c6b6e046a36832f0c28bf35b624c1767", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5], "true_reduced_cost": -3.986846}
{"candidate_id": "ae39058486b4d7a72c0df0c57d49533db33e4ab5", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5], "true_reduced_cost": -3.000138}
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
