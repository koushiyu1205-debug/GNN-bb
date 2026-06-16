# 2026-06-16 BPC_future GAT Target Mode Stage 4 gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616 Online Coverage Audit 报告

## 结论

本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。
它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结论：

- exact safe id online overlap = 32;
- online sampled candidates = 75;
- online sample coverage complete = true;
- task-set 层有 39 个 key 重叠，覆盖 39 个 online candidates；
- task-set 层 offline conflict key count = 48。

因此 gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616 当前失败不是因为当前 online logs 完全没有相似列族，
而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。
而且 task-set / sequence 级放宽存在离线冲突，不能直接作为 HIGH_PRIORITY admission rule。

## 输入

```text
safe_source = BPC_future/results/gat_batch_impact_safe_source_v14_random_wave_task50_margin_tl130_scale_20260616/safe_source.json
decision_records = BPC_future/results/gat_batch_impact_knn_ood_audit_v14_random_wave_task50_margin_tl130_scale_20260616/decision_records.jsonl
shadow_log_dir = BPC_future/results/gat_target_mode_stage4_v10_safe_source_20_shadow_hit_probe_fullsamples_20260616/logs_sector_tranq20_01_shadow_fullsamples
```

## Exact-id Coverage

```text
safe_candidate_id_count = 1198
offline_high_priority_unique_signature_ids = 1198
online_unique_signature_ids = 75
exact_safe_id_overlap_count = 32
exact_safe_id_overlap_rate_online = 0.4266666666666667
coverage_gate_pass = true
```

## Coarse-key Coverage Diagnostic

```text
route_no_start.overlap_key_count = 32
route_no_start.online_candidate_hit_count = 32
route_no_start.offline_conflict_key_count = 4

sequence.overlap_key_count = 32
sequence.online_candidate_hit_count = 32
sequence.offline_conflict_key_count = 13

task_set.overlap_key_count = 39
task_set.online_candidate_hit_count = 39
task_set.offline_conflict_key_count = 48
task_set.online_conflict_candidate_hit_count = 5
```

重叠 task-set 样本：

```text
[1, 15]
[1, 5]
[10, 17]
[11, 15, 17]
[12, 17]
[15, 17]
[15, 20]
[16, 17]
[16, 18]
[16, 20]
[2, 10, 11]
[2, 10, 14]
[2, 10, 15, 16]
[2, 3, 7, 15, 16]
[2, 5, 10]
[2, 5, 10, 12, 15]
[2, 5, 12, 13, 15]
[2, 5, 16]
[3, 11, 14, 20]
[3, 11, 15, 17]
```

命中 online candidate 样本：

```text
{"candidate_id": "6ad2d0b7ba49fa70ab106775aef2dc51b0880b9d", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [16, 20], "true_reduced_cost": -25.4432665}
{"candidate_id": "79a81ddeb102a733f3300e0ed0d04f17002ac4c9", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [16, 17], "true_reduced_cost": -20.7411045}
{"candidate_id": "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -19.76771125}
{"candidate_id": "7b46563f19a4ba2bc2739dba622b82f8b83a21db", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 7, 15, 17], "true_reduced_cost": -15.846047}
{"candidate_id": "d683a437bea4020da6c195020e287cdb04e42702", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 11, 15, 17], "true_reduced_cost": -12.459543}
{"candidate_id": "c410281c463756c0840f5e7d78c10c2a9f8f66f1", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 6, 7], "true_reduced_cost": -11.893966}
{"candidate_id": "ad39a056d43137e879031e5713f0dd8c4f0db0b3", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 7, 8], "true_reduced_cost": -11.893966}
{"candidate_id": "6a91a0e6224b8164f0556fd0d9d70e5bed11cce7", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 7, 17], "true_reduced_cost": -11.893966}
{"candidate_id": "4e652a888b0ae9b2bb9bf41d5503a1a4ec9bad8e", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 6, 11], "true_reduced_cost": -8.507462}
{"candidate_id": "e4103869ca379807e8ae5dcb9caf0a8690a31ae9", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 8, 11], "true_reduced_cost": -8.507462}
{"candidate_id": "a7a1cda9c064cdbc2c5bbbd3c6b1923e1701842c", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 11, 17], "true_reduced_cost": -8.507462}
{"candidate_id": "bfa93dc9f590902712e1de6b243615c5a3adae04", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [9, 15, 17], "true_reduced_cost": -5.350065}
{"candidate_id": "9e3b6b64ee5dd65f00a7cea9c026ca69984721ea", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [4, 15, 17], "true_reduced_cost": -5.0754}
{"candidate_id": "6a756bf8a77a533b5f33aa9e86e87b2495171eb6", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 5, 7, 15, 16], "true_reduced_cost": -4.97015675}
{"candidate_id": "a39671fe901a091d64e9745fb9b96a324d444f4c", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 7, 14, 17], "true_reduced_cost": -4.896076}
{"candidate_id": "98d021049f6f330222aecd4dade4f9e31230f262", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5, 16], "true_reduced_cost": -4.853055}
{"candidate_id": "a247df4c67f63e4d9156a52f7f5d3d9107efab5e", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 15], "true_reduced_cost": -4.767096}
{"candidate_id": "473a19b7f445c74141fcea0fa54b73333d517b56", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 7, 14, 20], "true_reduced_cost": -4.646775}
{"candidate_id": "14b4f04a9321d0cffae8af1a4f51ecc57d523da6", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 3, 7, 15, 16], "true_reduced_cost": -4.64105675}
{"candidate_id": "dff85c2667854d10424ecbf8d6e94d3c4fcc0e03", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [2, 5, 12, 13, 15], "true_reduced_cost": -4.433239}
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
