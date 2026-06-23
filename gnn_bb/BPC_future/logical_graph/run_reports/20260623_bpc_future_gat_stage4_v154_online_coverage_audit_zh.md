# 2026-06-16 BPC_future GAT Target Mode Stage 4 forced_diagnostic_safe_source Online Coverage Audit 报告

## 结论

本报告只读 Stage 3 safe-source、kNN/OOD decision records 和 Stage 4 online shadow 日志。
它不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结论：

- exact safe id online overlap = 113;
- online sampled candidates = 630;
- online sample coverage complete = false;
- task-set 层有 112 个 key 重叠，覆盖 135 个 online candidates；
- task-set 层 offline conflict key count = 10。

因此 forced_diagnostic_safe_source 当前失败不是因为当前 online logs 完全没有相似列族，
而是因为导出的是 exact signature id 白名单，跨 seed / context / timing 后在线命中为 0。
而且 task-set / sequence 级放宽存在离线冲突，不能直接作为 HIGH_PRIORITY admission rule。

## 输入

```text
safe_source = BPC_future/results/gat_stage4_v154_actual_probe_20260623/forced_diagnostic_safe_source/safe_source.json
decision_records = BPC_future/results/gat_batch_impact_v154_pair_delta_head_knn_ood_scale_strict_20260623/decision_records.jsonl
shadow_log_dir = BPC_future/results/gat_stage4_v154_actual_probe_20260623/task020_v154_online_shadow_capture/logs
```

## Exact-id Coverage

```text
safe_candidate_id_count = 515
offline_high_priority_unique_signature_ids = 515
online_unique_signature_ids = 630
exact_safe_id_overlap_count = 113
exact_safe_id_overlap_rate_online = 0.17936507936507937
coverage_gate_pass = true
```

## Coarse-key Coverage Diagnostic

```text
route_no_start.overlap_key_count = 113
route_no_start.online_candidate_hit_count = 113
route_no_start.offline_conflict_key_count = 3

sequence.overlap_key_count = 113
sequence.online_candidate_hit_count = 117
sequence.offline_conflict_key_count = 3

task_set.overlap_key_count = 112
task_set.online_candidate_hit_count = 135
task_set.offline_conflict_key_count = 10
task_set.online_conflict_candidate_hit_count = 9
```

重叠 task-set 样本：

```text
[1, 11]
[1, 11, 16]
[1, 2, 3, 8]
[1, 20]
[1, 3, 8]
[1, 3, 8, 18]
[1, 4, 11]
[1, 5]
[1, 5, 13]
[1, 5, 7]
[1, 5, 8, 18]
[1, 6]
[1, 6, 8]
[1, 9, 11]
[1, 9, 16, 20]
[13, 16, 19]
[16, 19]
[19, 20]
[2, 16, 19, 20]
[2, 3, 6]
```

命中 online candidate 样本：

```text
{"candidate_id": "cd0a59a879515d62df9c4c92e75922862382c569", "cg_iter": 18, "decision": "DELAY_QUEUE", "pricing_kind": "heuristic", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -19.016345}
{"candidate_id": "3fa5854924ac844a7e090bde70be0e205e2b3410", "cg_iter": 41, "decision": "HIGH_PRIORITY", "pricing_kind": "exact", "reason": "true_rc_negative_safe_in_distribution", "task_set": [2, 3, 8, 12, 13, 15], "true_reduced_cost": -28.945943667}
{"candidate_id": "f2813b715a37b431927f932dd1a75815eeb18ff5", "cg_iter": 41, "decision": "HIGH_PRIORITY", "pricing_kind": "exact", "reason": "true_rc_negative_safe_in_distribution", "task_set": [2, 3, 6, 8, 13, 15], "true_reduced_cost": -28.875760667}
{"candidate_id": "2790b1a6fd6539333755651296d7389a9b4651ec", "cg_iter": 1, "decision": "HIGH_PRIORITY", "pricing_kind": "exact", "reason": "true_rc_negative_safe_in_distribution", "task_set": [19, 20], "true_reduced_cost": -60.691508}
{"candidate_id": "c1f4ab3caf4d0ab917bb251e1adcd55d21e06cb7", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [8, 20], "true_reduced_cost": -58.243405}
{"candidate_id": "c66fe0ce4b9d58d4e6450e227af52f3177549f9b", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 8], "true_reduced_cost": -54.898606}
{"candidate_id": "70528f366b9729f3372416ac2d3cf7fffc8fe0d2", "cg_iter": 1, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [5, 15], "true_reduced_cost": -0.392314}
{"candidate_id": "faa3e5eeea745d947ae4d0698ed0ab2d096fee55", "cg_iter": 6, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [16, 19], "true_reduced_cost": -37.8568215}
{"candidate_id": "2a84a4712e0bef1d384695125e3cd472b431bef9", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [8, 20], "true_reduced_cost": -1.716841}
{"candidate_id": "b9f7e1d0bd93171b93c3c8ccf2a9e84628597003", "cg_iter": 7, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [8, 13, 20], "true_reduced_cost": -0.791942}
{"candidate_id": "91003b127b9fd2df1568775252656000ce3032a9", "cg_iter": 8, "decision": "DELAY_QUEUE", "pricing_kind": "exact_retry", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 18, 20], "true_reduced_cost": -3.592138857}
{"candidate_id": "e1c81ab80566931bd3c56a27ddf60f34d0b961cc", "cg_iter": 9, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [13, 16, 19], "true_reduced_cost": -1.001421}
{"candidate_id": "b0b0e481085c7f79f6b965ae5a707ef81e050560", "cg_iter": 9, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [8, 15], "true_reduced_cost": -0.794421}
{"candidate_id": "73e97ca970cb41d5b7c47c584b32a1d7fd81348f", "cg_iter": 9, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [5, 9], "true_reduced_cost": -0.641005}
{"candidate_id": "8d3ab308f1d7eab6982e4bc0fc88fd6e4228ed7e", "cg_iter": 9, "decision": "DELAY_QUEUE", "pricing_kind": "exact", "reason": "true_rc_negative_delayed_not_rejected", "task_set": [8, 13, 20], "true_reduced_cost": -0.127459}
{"candidate_id": "975194bca91b34b2ab87292909715d21f52f82fe", "cg_iter": 6, "decision": "HIGH_PRIORITY", "pricing_kind": "exact", "reason": "true_rc_negative_safe_in_distribution", "task_set": [4, 12, 16, 19, 20], "true_reduced_cost": -21.353882}
{"candidate_id": "e5a3c3c4835f67d651c3ba8b3045d9b67c721307", "cg_iter": 6, "decision": "HIGH_PRIORITY", "pricing_kind": "exact", "reason": "true_rc_negative_safe_in_distribution", "task_set": [2, 16, 19, 20], "true_reduced_cost": -21.329195}
{"candidate_id": "088a2f809dc43eade49180040bb200018ddd8598", "cg_iter": 6, "decision": "HIGH_PRIORITY", "pricing_kind": "exact", "reason": "true_rc_negative_safe_in_distribution", "task_set": [4, 12, 15, 19, 20], "true_reduced_cost": -20.680593}
{"candidate_id": "f8d22b6ce84a43aace738940c490dd5c129ac81d", "cg_iter": 6, "decision": "HIGH_PRIORITY", "pricing_kind": "exact", "reason": "true_rc_negative_safe_in_distribution", "task_set": [4, 12, 15, 16, 20], "true_reduced_cost": -19.789638}
{"candidate_id": "5d908ceb8101b3aac1d39fd15ea08b4c9eda6a43", "cg_iter": 6, "decision": "HIGH_PRIORITY", "pricing_kind": "exact", "reason": "true_rc_negative_safe_in_distribution", "task_set": [4, 12, 16, 20], "true_reduced_cost": -15.912005}
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
