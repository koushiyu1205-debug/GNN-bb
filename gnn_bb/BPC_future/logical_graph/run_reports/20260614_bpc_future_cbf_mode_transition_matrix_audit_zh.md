# CBF Mode Transition Audit 报告

日期：2026-06-14

## 目的

本报告只从已有 JSONL 中重建 `state_t, action_t, state_{t+1}` transition，
计算 Lyapunov surrogate 与 CBF barrier slack。它不运行 BPC / pricing / RMP / Pulse，
也不改变 worker、certificate 或 official lower bound。

## 机器字段

```text
cbf_mode_transition_audit = current
diagnostic_only = true
runs_bpc_or_pricing = false
status = cbf_mode_transition_audited_no_transition_evidence
all_checks_pass = true
production_ready = false
goal_complete = false
```

## 摘要

```json
{
  "bad_capture_event_count": 0,
  "bad_mode_transition_count": 0,
  "capture_event_count": 0,
  "cbf_feasible_observed_count": 0,
  "cbf_infeasible_observed_count": 0,
  "has_transition_evidence": false,
  "input_file_count": 4,
  "mode_switch_count": 0,
  "negative_action_transition_count": 0,
  "training_ready": false,
  "transition_count": 0,
  "transition_task_count_histogram": {}
}
```

## 检查项

```json
{
  "all_capture_events_no_certificate_effect": true,
  "barrier_values_are_present": true,
  "diagnostic_only": true,
  "no_decode_errors": true,
  "runs_bpc_or_pricing_false": true,
  "transitions_have_state_action_next": true
}
```

## 解释

- `cbf_feasible_observed_count` 只表示相邻 capture 事件在该 surrogate 下满足离散 CBF slack；
- `cbf_infeasible_observed_count` 表示当前 observed action 后 energy 没有满足该安全约束；
- 本报告不能证明 production speedup，也不能作为 certificate；
- 下一步应扩大 no-certificate-effect capture，覆盖 5/10/20 多实例和 mixed/noop/improved contexts。
