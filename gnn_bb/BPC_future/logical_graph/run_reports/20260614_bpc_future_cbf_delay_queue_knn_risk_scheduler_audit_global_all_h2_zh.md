# CBF Delay-Queue kNN Risk Scheduler 审计报告

日期：2026-06-14

## 目的

在 conservative probability threshold 外叠加在线特征空间的 kNN unsafe
density guard。该脚本只读 H=2 dataset，不运行 BPC / pricing / RMP，
不生成列，不产生 certificate 或 official lower bound。

## 机器字段

```text
cbf_delay_queue_knn_risk_scheduler_audit = current
status = cbf_delay_queue_knn_risk_scheduler_audited
diagnostic_only = true
runs_bpc_or_pricing = false
scheduler_ready = true
production_candidate_ready = false
production_ready = false
knn_k = 5
max_neighbor_unsafe_fraction = 0.0
all_checks_pass = true
```

## 摘要

```json
{
  "family_results": [
    {
      "family": "very_small",
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 0,
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 0,
        "scheduler_no_unsafe_high_priority": false,
        "skipped_count": 0,
        "skipped_status_counts": {},
        "total_delay_queue_count": 0,
        "total_high_priority_count": 0,
        "unsafe_high_priority_fold_count": 0
      },
      "row_count": 3,
      "status": "guarded_delay_below_min_task_count",
      "task_count": 4
    },
    {
      "family": "moon_trek_tasks10",
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 0,
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 0,
        "scheduler_no_unsafe_high_priority": false,
        "skipped_count": 0,
        "skipped_status_counts": {},
        "total_delay_queue_count": 0,
        "total_high_priority_count": 0,
        "unsafe_high_priority_fold_count": 0
      },
      "row_count": 3,
      "status": "guarded_delay_below_min_task_count",
      "task_count": 10
    },
    {
      "family": "greedy-anchor",
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 2,
        "evaluated_no_false_positive": true,
        "false_positive_fold_count": 0,
        "fold_count": 4,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 0,
        "scheduler_no_unsafe_high_priority": true,
        "skipped_count": 2,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 2
        },
        "total_delay_queue_count": 86,
        "total_high_priority_count": 0,
        "unsafe_high_priority_fold_count": 0
      },
      "row_count": 88,
      "status": "family_scheduler_not_ready",
      "task_count": 20
    },
    {
      "family": "random-wave",
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 5,
        "evaluated_no_false_positive": true,
        "false_positive_fold_count": 0,
        "fold_count": 8,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 0,
        "scheduler_no_unsafe_high_priority": true,
        "skipped_count": 3,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 1,
          "skipped_too_few_train_rows": 2
        },
        "total_delay_queue_count": 12,
        "total_high_priority_count": 0,
        "unsafe_high_priority_fold_count": 0
      },
      "row_count": 23,
      "status": "family_scheduler_not_ready",
      "task_count": 20
    },
    {
      "family": "sector-wave",
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 6,
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 1,
        "fold_count": 10,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 6,
        "scheduler_no_unsafe_high_priority": false,
        "skipped_count": 4,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 1,
          "skipped_too_few_train_rows": 3
        },
        "total_delay_queue_count": 6,
        "total_high_priority_count": 6,
        "unsafe_high_priority_fold_count": 1
      },
      "row_count": 22,
      "status": "family_scheduler_not_ready",
      "task_count": 20
    }
  ],
  "family_scheduler_ready": false,
  "label_counts": {
    "0": 103,
    "1": 36
  },
  "production_candidate_ready": false,
  "ready_families": [],
  "ready_task_counts": [
    20
  ],
  "row_count": 139,
  "scale_results": [
    {
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 0,
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 0,
        "scheduler_no_unsafe_high_priority": false,
        "skipped_count": 0,
        "skipped_status_counts": {},
        "total_delay_queue_count": 0,
        "total_high_priority_count": 0,
        "unsafe_high_priority_fold_count": 0
      },
      "row_count": 3,
      "status": "guarded_delay_below_min_task_count",
      "task_count": 4
    },
    {
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 0,
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 0,
        "scheduler_no_unsafe_high_priority": false,
        "skipped_count": 0,
        "skipped_status_counts": {},
        "total_delay_queue_count": 0,
        "total_high_priority_count": 0,
        "unsafe_high_priority_fold_count": 0
      },
      "row_count": 3,
      "status": "guarded_delay_below_min_task_count",
      "task_count": 10
    },
    {
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 18,
        "evaluated_no_false_positive": true,
        "false_positive_fold_count": 0,
        "fold_count": 22,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 4,
        "scheduler_no_unsafe_high_priority": true,
        "skipped_count": 4,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 4
        },
        "total_delay_queue_count": 125,
        "total_high_priority_count": 4,
        "unsafe_high_priority_fold_count": 0
      },
      "row_count": 133,
      "status": "scale_scheduler_candidate_ready",
      "task_count": 20
    }
  ],
  "scale_scheduler_ready": true
}
```

## 解释

- kNN risk 只能让 true-RC negative 从 high priority 退回 delay queue；
- 它不能 discard 负列，也不能产生 no-negative certificate；
- 若 high-priority 全被压没，则只能说明当前策略没有 ROI，不能上线。
