# CBF Gate Holdout 稳健性审计报告

日期：2026-06-14

## 目的

按 instance 与 task_count 做 leave-one holdout，审计离线 CBF/RMP-impact gate
是否在留出上下文中保持低误放。该脚本只读已构建数据，不运行 BPC / pricing / RMP，
不生成列，不产生 certificate 或 official lower bound。

## 机器字段

```text
cbf_gate_holdout_audit = current
status = cbf_gate_holdout_audited
diagnostic_only = true
runs_bpc_or_pricing = false
holdout_safety_pass = false
production_gate_ready = false
production_ready = false
all_checks_pass = true
```

## 摘要

```json
{
  "feature_count": 30,
  "holdout_safety_pass": false,
  "instance_holdout_summary": {
    "all_evaluated_folds_no_false_positive": false,
    "all_folds_evaluated": false,
    "evaluated_count": 13,
    "false_positive_fold_count": 2,
    "fold_count": 16,
    "productive_fold_count": 3,
    "skipped_count": 3,
    "skipped_status_counts": {
      "skipped_too_few_holdout_rows": 3
    }
  },
  "label_counts": {
    "0": 152,
    "1": 33
  },
  "production_gate_ready": false,
  "row_count": 185,
  "task_count_holdout_summary": {
    "all_evaluated_folds_no_false_positive": false,
    "all_folds_evaluated": true,
    "evaluated_count": 3,
    "false_positive_fold_count": 2,
    "fold_count": 3,
    "productive_fold_count": 2,
    "skipped_count": 0,
    "skipped_status_counts": {}
  }
}
```

## 解释

- `holdout_safety_pass=true` 只表示已评估 folds 没有 false positive；
- `production_gate_ready=false` 表示仍不能接 production worker；
- skipped fold 通常意味着该 instance/task_count 样本太少或训练侧单标签；
- 下一步必须补齐留出覆盖和做 5/10 no-regression + 20-task A/B。
