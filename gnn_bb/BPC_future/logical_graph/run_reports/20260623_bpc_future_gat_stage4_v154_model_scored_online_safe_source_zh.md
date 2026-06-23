# 2026-06-16 BPC_future GAT Stage 4 Model-scored Online Safe-source Audit 报告

## 结论

本报告只读 Stage 3 safe-source、decision records 和 Stage 4 shadow 日志；
不运行 BPC / pricing / RMP，不改变 admission，也不产生 certificate。

核心结果：

- online sampled candidates = 630
- exact safe-id hit count = 113
- diagnostic priority hint count = 2
- admission ready count = 0

这些 diagnostic hints 只能说明 coarse key 上存在离线 high-ROI / high-priority 证据；
审计已要求 online family / task scale 与 offline evidence 兼容，以避免跨 family/scale 误迁移。
它们还没有 online trajectory ROI、tail-risk 或 family/context holdout 证明，不能作为 mutating admission rule。

## Top Diagnostic Candidates

```text
{"admission_blocker": "coarse_key_hint_but_online_trajectory_roi_unverified", "admission_ready": false, "best_key_level": "task_set", "candidate_id": "ddf1264ee8bc91c593d17ef092c9d350e6ff1af6", "cg_iter": 4, "context_compatible": true, "diagnostic_priority_hint": true, "evidence_score": 2.035139322280884, "exact_safe_id_hit": false, "offline_batch_score_mean": 0.7835869193077087, "offline_batch_score_min": 0.7835869193077087, "offline_context_count": 1, "offline_delay_conflict_count": 0, "offline_families": ["sector-wave"], "offline_high_count": 1, "offline_high_roi_count": 1, "offline_high_roi_max": 1.017569661140442, "offline_high_roi_mean": 1.017569661140442, "offline_task_counts": ["20"], "offline_unsafe_count": 0, "online_family": "sector-wave", "online_task_count": "20", "pricing_kind": "exact", "shadow_decision": "DELAY_QUEUE", "shadow_reason": "true_rc_negative_delayed_not_rejected", "task_set": [3, 4, 6, 18], "true_reduced_cost": -3.253824}
{"admission_blocker": "coarse_key_hint_but_online_trajectory_roi_unverified", "admission_ready": false, "best_key_level": "task_set", "candidate_id": "248da019a9711562239c39a8eb5c620f9132a0cf", "cg_iter": 1, "context_compatible": true, "diagnostic_priority_hint": true, "evidence_score": 2.035139322280884, "exact_safe_id_hit": false, "offline_batch_score_mean": 0.7835869193077087, "offline_batch_score_min": 0.7835869193077087, "offline_context_count": 1, "offline_delay_conflict_count": 0, "offline_families": ["sector-wave"], "offline_high_count": 1, "offline_high_roi_count": 1, "offline_high_roi_max": 1.017569661140442, "offline_high_roi_mean": 1.017569661140442, "offline_task_counts": ["20"], "offline_unsafe_count": 0, "online_family": "sector-wave", "online_task_count": "20", "pricing_kind": "exact", "shadow_decision": "DELAY_QUEUE", "shadow_reason": "true_rc_negative_delayed_not_rejected", "task_set": [1, 20], "true_reduced_cost": -0.803368}
```

## 判定

```text
stage4_model_scored_online_safe_source_ready = false
stage4_mutating_admission_ready = false
stage4_next_direction = collect_online_trajectory_roi_for_diagnostic_hints
```

## Exactness Boundary

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```
