# GAT Same-Run Target-Priority Candidates 报告

日期：2026-06-15

## 目的

从 same-run GAT+kNN/OOD 决策中抽取 target-priority worker 候选。
该脚本只读 decision_records 与 capture JSONL，不运行 BPC / pricing / RMP / worker，
不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_same_run_target_priority_candidates = current
status = ready
candidate_count = 24
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## 关键约束

- 默认候选来自 same-context batch-impact 的 HIGH_PRIORITY 决策；
- 显式 `include_delay_queue` 时可纳入 DELAY_QUEUE 候选做离线探索采样；
- `best_true_reduced_cost < 0` 才能成为 worker target；
- 当前仍不能直接作为训练标签，必须先通过 worker reachability / target causal match 审计；
- 不通过的 true-RC negative 只能进入 DELAY_QUEUE，不能永久丢弃。

## 摘要

```json
{
  "candidate_count": 24,
  "candidate_family_region_counts": {
    "random-wave|apollo15_20km": 15,
    "random-wave|tranquillitatis_balmer_like_20km": 9
  },
  "candidate_impact_bucket_counts": {
    "new_support_changing": 13,
    "new_task_set": 1,
    "replacement_like": 10
  },
  "candidate_new_task_set_count": 14,
  "candidate_policy": {
    "permanent_negative_filter_allowed": false,
    "safe_negative_decision": "HIGH_PRIORITY",
    "training_label_requires_worker_target_causal_match": true,
    "unsafe_negative_decision": "DELAY_QUEUE"
  },
  "candidate_ranking": "active_replacement",
  "candidate_replacement_like_proxy_count": 10,
  "candidate_support_changing_proxy_count": 13,
  "candidate_task_count_counts": {
    "20": 24
  },
  "checks": {
    "all_candidate_instances_exist": true,
    "all_candidates_have_arc_targets": true,
    "all_candidates_have_full_capture_context": true,
    "all_candidates_have_full_sortie_traces": true,
    "all_candidates_true_rc_negative": true,
    "candidate_decision_scope_valid": true,
    "diagnostic_only": true,
    "has_candidate": true,
    "labels_blocked_until_worker_reachability": true,
    "no_certificate_effect": true,
    "runs_bpc_or_pricing_false": true
  },
  "delay_queue_only": false,
  "exclude_existing_roi_jsonl": "BPC_future/results/gat_worker_roi_dataset_v34_after_v33_sampling_20260615/gat_worker_roi_rows.jsonl",
  "existing_roi_target_count": 229,
  "include_delay_queue": true,
  "include_families": [],
  "include_ordinals": [],
  "include_regions": [],
  "include_task_counts": [
    20
  ],
  "max_targets_per_context": 4,
  "skipped_counts": {
    "existing_roi_target": 11,
    "task_count_not_selected": 10
  }
}
```
