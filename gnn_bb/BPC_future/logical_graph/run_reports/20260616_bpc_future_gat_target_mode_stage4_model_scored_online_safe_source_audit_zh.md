# 2026-06-16 BPC_future GAT Stage 4 Model-scored Online Safe-source Audit 报告

## 结论

本报告只读 Stage 3 safe-source、decision records 和 Stage 4 shadow 日志；
不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结果：

- online sampled candidates = 75
- exact safe-id hit count = 0
- diagnostic priority hint count = 2
- admission ready count = 0

这些 diagnostic hints 只能说明 coarse key 上存在离线 high-ROI / high-priority 证据；
审计已要求 online family / task scale 与 offline evidence 兼容，以避免跨 family/scale 误迁移。
它们还没有 online trajectory ROI、tail-risk 或 family/context holdout 证明，不能作为 mutating admission rule。

## Top Diagnostic Candidates

```text
{"admission_blocker": "exact_safe_id_missing_and_online_trajectory_roi_unverified", "admission_ready": false, "best_key_level": "task_set", "candidate_id": "897bf7a82d86b9b3ab2d639d9306c3f7d043ff17", "cg_iter": 7, "context_compatible": true, "diagnostic_priority_hint": true, "evidence_score": 5.175938129425049, "exact_safe_id_hit": false, "offline_batch_score_mean": 0.8212968707084656, "offline_batch_score_min": 0.8212968707084656, "offline_context_count": 1, "offline_delay_conflict_count": 0, "offline_families": ["sector-wave"], "offline_high_count": 1, "offline_high_roi_count": 1, "offline_high_roi_max": 2.5879690647125244, "offline_high_roi_mean": 2.5879690647125244, "offline_task_counts": ["20"], "offline_unsafe_count": 0, "online_family": "sector-wave", "online_task_count": "20", "pricing_kind": "exact", "shadow_decision": "DELAY_QUEUE", "shadow_reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 5], "true_reduced_cost": -19.76771125}
{"admission_blocker": "exact_safe_id_missing_and_online_trajectory_roi_unverified", "admission_ready": false, "best_key_level": "task_set", "candidate_id": "9e3b6b64ee5dd65f00a7cea9c026ca69984721ea", "cg_iter": 7, "context_compatible": true, "diagnostic_priority_hint": true, "evidence_score": 1.6189026832580566, "exact_safe_id_hit": false, "offline_batch_score_mean": 0.6064697504043579, "offline_batch_score_min": 0.6064697504043579, "offline_context_count": 1, "offline_delay_conflict_count": 0, "offline_families": ["sector-wave"], "offline_high_count": 1, "offline_high_roi_count": 1, "offline_high_roi_max": 0.8094513416290283, "offline_high_roi_mean": 0.8094513416290283, "offline_task_counts": ["20"], "offline_unsafe_count": 0, "online_family": "sector-wave", "online_task_count": "20", "pricing_kind": "exact", "shadow_decision": "DELAY_QUEUE", "shadow_reason": "true_rc_negative_delayed_not_rejected", "task_set": [4, 15, 17], "true_reduced_cost": -5.0754}
```

## 判定

```text
stage4_model_scored_online_safe_source_ready = false
stage4_mutating_admission_ready = false
stage4_next_direction = collect_online_trajectory_roi_for_diagnostic_hints
```

## 与 Target-materialization A/B 对齐

两个 diagnostic hints 都能在 online shadow target candidates 里找到完整
same-context target payload：

```text
[1,5]
  expected_context_hash = ac056820151e9ad7
  true_dual_hash = af26c5fef326d91a
  target_sequence = [5,1]
  true_rc = -19.76771125

[4,15,17]
  expected_context_hash = ac056820151e9ad7
  true_dual_hash = af26c5fef326d91a
  target_sequence = [15,17,4]
  true_rc = -5.0754
```

但已有 same-context target-materialization A/B 已经说明：`true-RC negative`
不是训练正样本的充分条件。

```text
single [1,5]:
  returned_journeys = 1
  next_rmp_objective = 635.508935
  rmp/pricing/exact = 10/16/6
  generated/evaluated = 32443/53274
  label_implication = hard_negative_or_delay

batch5 includes [1,5] and [4,15,17]:
  returned_journeys = 5
  next_rmp_objective = 635.508935
  rmp/pricing/exact = 9/14/5
  generated/evaluated = 30302/48610
  active_changed_task_set_count = 0
  label_implication = weak_batch_signal_not_stage4_positive
```

因此当前训练含义必须更硬：

- `[1,5]` 不能作为 HIGH_PRIORITY 正例；它是同 context 已验证的 hard
  negative / delay candidate；
- `[4,15,17]` 也不能因 batch5 弱 workload 下降而单独升级为正例；
- Stage 3 正样本必须同时满足 true-RC、same-context materialization、
  trajectory ROI、precision/CI、coverage 和 tail-risk gate；
- 没有 active-support / replacement-aware 改善的负列，即使模型分数高，也只能
  作为 diagnostic hint 或 DELAY_QUEUE 训练样本。

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```
