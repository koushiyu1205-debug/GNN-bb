# Journey Weak Negative Tail Audit

日期：2026-06-23

## 目的

读取 solver JSONL 日志，提取 rough reduced-cost 为负、但 true-RC 复算后被过滤的 weak negative tail 事件。该脚本只读日志，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
journey_weak_negative_tail_audit = current
output_dir = BPC_future/results/journey_weak_negative_tail_audit_greedy_selectedlog_20260623
log_count = 2
weak_event_count = 14
weak_training_row_count = 14
total_weak_negative_journeys_filtered = 446
total_profile_weak_filtered_materialized_count = 446
total_profile_generation_time = 32.396167
total_profile_dp_time = 55.20569
max_true_minus_rough = 29.129438
best_rough_rc = -11.774451333
best_true_rc_after_materialization = -0.0
pricing_kind_counts = {'exact': 13, 'exact_retry': 1}
reason_counts = {'streaming_partial_negative_journey': 9, 'weak_negative_journeys_filtered': 5}
repeated_weak_mask_count = 4
repeated_weak_task_set_sample_count = 45
production_ready = false
certificate_effect = false
official_bound_effect = false
```

## 解释

这些 row 表示当前 profile/rough objective 的负列信号在 true-RC materialization 后失效。它们可以作为 GAT branch-impact / proof-tail 模型的负样本，或作为未来 worker priority / finite-delay 的训练依据；但不能作为 pruning、no-negative certificate 或 official lower bound。

## Top Weak Masks

```json
{
  "3136": 1,
  "4230": 4,
  "69824": 1,
  "75872": 2,
  "86050": 2,
  "86146": 4
}
```

## Top Weak Task-Set Samples

```json
{
  "2,12,13,15,17": 10,
  "2,3,6,7,13": 10,
  "2,4,6,11,12": 10,
  "2,4,6,12,14,17": 10,
  "2,6,12,13,15,17": 8,
  "2,6,7,13,14,17": 10,
  "2,6,7,13,17": 10,
  "2,6,8,12,17": 10,
  "2,6,8,13,17": 10,
  "2,6,8,15,17": 10,
  "2,7,8,13,17": 10,
  "2,8,12,13,17": 10,
  "2,8,12,15,17": 10,
  "2,8,13,14,17": 10,
  "2,8,13,15,17": 10,
  "3,7,13,20": 10,
  "6,11,12,16,18": 10,
  "6,12,16,17,18": 10,
  "6,7,12,13,17": 10,
  "6,7,16,17,18": 10
}
```
