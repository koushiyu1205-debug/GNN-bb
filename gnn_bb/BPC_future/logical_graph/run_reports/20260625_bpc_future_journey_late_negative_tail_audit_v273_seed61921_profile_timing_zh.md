# Journey Late Negative Tail Audit

日期：2026-06-24

## 目的

统一解析 solver JSONL 中的 true-negative pricing、column addition 和 weak false-negative filtered 事件，区分 active-support-changing、inactive-only 与 weak/noise tail。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_late_negative_tail_audit = current
output_dir = BPC_future/results/journey_late_negative_tail_audit_v273_seed61921_profile_timing_20260625
log_count = 1
tail_event_count = 15
min_cg_iter = 0
min_time = 80.0
true_negative_event_count = 15
weak_filtered_event_count = 4
weak_false_negative_event_count = 0
total_active_changed_task_sets = 0
total_inactive_changed_task_sets = 38
runs_bpc_or_pricing = false
certificate_effect = false
official_bound_effect = false
```

## 分类

```json
{
  "true_negative_inactive_only": 7,
  "true_negative_no_addition_observed": 8
}
```

## 定价类型

```json
{
  "exact": 5,
  "exact_completion_bound_retry": 3,
  "heuristic": 7
}
```

## 解释

True negative rows require exact true-RC verification before addition; weak false-negative rows are materialized and then filtered. This audit is suitable for support-aware admission and weak-delay diagnostics, but is not a pruning or certificate source.
