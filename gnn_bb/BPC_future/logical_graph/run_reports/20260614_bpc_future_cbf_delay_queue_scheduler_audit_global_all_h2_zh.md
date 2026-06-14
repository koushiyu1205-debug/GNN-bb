# CBF Delay-Queue Scheduler 审计报告

日期：2026-06-14

## 目的

审计 trajectory gate 是否能作为稳定性调度层使用：安全负列进入
`HIGH_PRIORITY`，不安全负列进入 `DELAY_QUEUE`。该脚本只读 H=2
trajectory dataset，不运行 BPC / pricing / RMP，不生成列，不产生
certificate 或 official lower bound。

## 机器字段

```text
cbf_delay_queue_scheduler_audit = current
status = cbf_delay_queue_scheduler_audited
diagnostic_only = true
runs_bpc_or_pricing = false
scheduler_ready = false
production_ready = false
min_high_priority_threshold = 0.8
gate_can_permanently_discard_negative_columns = false
finite_delay_required = true
delay_queue_can_extend_proof_budget = false
delay_queue_runs_proof_sweep = false
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
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 1,
        "fold_count": 8,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 3,
        "scheduler_no_unsafe_high_priority": false,
        "skipped_count": 3,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 1,
          "skipped_too_few_train_rows": 2
        },
        "total_delay_queue_count": 9,
        "total_high_priority_count": 3,
        "unsafe_high_priority_fold_count": 1
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
        "false_positive_fold_count": 2,
        "fold_count": 10,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 6,
        "scheduler_no_unsafe_high_priority": false,
        "skipped_count": 4,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 1,
          "skipped_too_few_train_rows": 3
        },
        "total_delay_queue_count": 3,
        "total_high_priority_count": 9,
        "unsafe_high_priority_fold_count": 2
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
  "min_high_priority_threshold": 0.8,
  "ready_families": [],
  "ready_task_counts": [],
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
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 2,
        "fold_count": 22,
        "productive_fold_count": 0,
        "productive_high_priority_fold_count": 12,
        "scheduler_no_unsafe_high_priority": false,
        "skipped_count": 4,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 4
        },
        "total_delay_queue_count": 109,
        "total_high_priority_count": 20,
        "unsafe_high_priority_fold_count": 2
      },
      "row_count": 133,
      "status": "scale_scheduler_not_ready",
      "task_count": 20
    }
  ],
  "scale_scheduler_ready": false
}
```

## 解释

- 训练侧阈值必须满足 train zero-FP；留出侧若有 unsafe high priority，则不 ready；
- `DELAY_QUEUE` 不是丢弃，必须满足有限延迟并保持 exact reachable；
- `DELAY_QUEUE` 不能扩展 final judge / proof 阶段预算，也不能触发额外 proof sweep；
- 小规模默认延迟/abstain，以保护 5/10 不退化；
- `production_ready=false` 表示仍不能接 worker 或 certificate。
