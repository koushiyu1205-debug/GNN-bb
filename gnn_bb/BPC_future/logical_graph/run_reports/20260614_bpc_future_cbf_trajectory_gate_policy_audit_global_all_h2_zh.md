# CBF Trajectory Gate Policy 审计报告

日期：2026-06-14

## 目的

审计 H-step trajectory-level CBF/RMP-impact gate 是否能在 instance、scale
和 `(task_count, family)` 留出上保持安全。该脚本只读 trajectory dataset，
不运行 BPC / pricing / RMP，不生成列，不产生 certificate 或 official lower bound。

重要 exactness guard：trajectory gate 是稳定性调度层，不是硬过滤器。
它只能把 true-RC negative column batch 分成 HIGH_PRIORITY 或 DELAY_QUEUE。
它不能永久丢弃任何 true-RC negative column；被 gate 拦下的候选仍必须留给
现有 exact pricing / fallback / backlog 路径，且必须满足有限延迟：
对任意 true-RC negative column，存在有限 T_p 使其进入 RMP 或重新回到 exact 可达路径。

## 机器字段

```text
cbf_trajectory_gate_policy_audit = current
status = cbf_trajectory_gate_policy_audited
horizon_steps = ['2']
diagnostic_only = true
runs_bpc_or_pricing = false
holdout_safety_pass = false
scale_policy_ready = false
family_policy_ready = false
production_ready = false
gate_decision_model = rc_negative_safe_high_priority_rc_negative_unsafe_delay_queue_rc_nonnegative_reject
gate_can_permanently_discard_negative_columns = false
finite_delay_required = true
all_checks_pass = true
```

## 摘要

```json
{
  "family_policy_ready": false,
  "holdout_safety_pass": false,
  "instance_holdout_summary": {
    "all_folds_evaluated": false,
    "evaluated_count": 20,
    "evaluated_no_false_positive": false,
    "false_positive_fold_count": 8,
    "fold_count": 24,
    "productive_fold_count": 16,
    "skipped_count": 4,
    "skipped_status_counts": {
      "skipped_too_few_holdout_rows": 4
    }
  },
  "label_counts": {
    "0": 103,
    "1": 36
  },
  "ready_families": [],
  "ready_task_counts": [],
  "row_count": 139,
  "scale_policy_ready": false,
  "task_count_histogram": {
    "10": 3,
    "20": 133,
    "4": 3
  },
  "task_count_holdout_summary": {
    "all_folds_evaluated": true,
    "evaluated_count": 3,
    "evaluated_no_false_positive": false,
    "false_positive_fold_count": 2,
    "fold_count": 3,
    "productive_fold_count": 2,
    "skipped_count": 0,
    "skipped_status_counts": {}
  }
}
```

## 解释

- 本审计使用 `label_horizon_cbf_feasible`，不是 one-step `label_cbf_feasible`；
- 特征只允许当前状态与候选 batch 字段，排除 `horizon_*`、`state_next_*`、`delta_*`；
- 小规模 scale/family 默认 abstain，用于保护 5/10 不退化；
- unsafe true-RC negative batch 进入 DELAY_QUEUE，不是 REJECT；
- DELAY_QUEUE 必须满足有限延迟引理，不能让 proof 阶段被无限拖住；
- 只有 `rc >= 0` 的候选可以被 scheduler 视为非负列而不加入；
- `production_ready=false` 表示仍不能接 worker 或 certificate。
