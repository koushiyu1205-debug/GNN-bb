# CBF Gate Scale-aware Policy 审计报告

日期：2026-06-14

## 目的

审计一个分 scale 的 CBF/RMP-impact gate 策略：小于阈值的 task_count
必须 abstain，以保护 5/10 不退化；被允许的 scale 仍需通过本 scale
leave-one-instance 安全审计。该脚本只读离线数据，不运行 BPC / pricing / RMP。

## 机器字段

```text
cbf_gate_scale_policy_audit = current
status = cbf_gate_scale_policy_audited
diagnostic_only = true
runs_bpc_or_pricing = false
scale_policy_ready = false
ready_task_counts = 
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "label_counts": {
    "0": 151,
    "1": 30
  },
  "min_enabled_task_count": 20,
  "ready_task_counts": [],
  "row_count": 181,
  "scale_policy_ready": false,
  "scale_results": [
    {
      "fold_summary": {
        "evaluated_count": 0,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "skipped_count": 0
      },
      "must_abstain": true,
      "row_count": 5,
      "scale_gate_candidate_ready": false,
      "status": "guarded_abstain_below_min_task_count",
      "task_count": 4
    },
    {
      "fold_summary": {
        "evaluated_count": 0,
        "false_positive_fold_count": 0,
        "fold_count": 0,
        "productive_fold_count": 0,
        "skipped_count": 0
      },
      "must_abstain": true,
      "row_count": 4,
      "scale_gate_candidate_ready": false,
      "status": "guarded_abstain_below_min_task_count",
      "task_count": 10
    },
    {
      "fold_summary": {
        "all_folds_evaluated": false,
        "evaluated_count": 9,
        "evaluated_no_false_positive": false,
        "false_positive_fold_count": 4,
        "fold_count": 12,
        "productive_fold_count": 8,
        "skipped_count": 3,
        "skipped_status_counts": {
          "skipped_too_few_holdout_rows": 3
        }
      },
      "must_abstain": true,
      "row_count": 172,
      "scale_gate_candidate_ready": false,
      "status": "scale_gate_not_ready",
      "task_count": 20
    }
  ],
  "task_count_histogram": {
    "10": 4,
    "20": 172,
    "4": 5
  }
}
```

## 解释

- `task_count < min_enabled_task_count` 的 scale 会强制 abstain，避免 5/10 退化；
- `scale_policy_ready=false` 表示当前没有任何 scale 可以进入 production A/B；
- 即使某个 scale ready，也仍需 full BPC A/B 才能接 production worker；
- 该策略不影响 certificate，也不能证明 no-negative。
