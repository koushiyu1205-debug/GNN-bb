# CBF Mode Transition Capture Smoke 报告

日期：2026-06-14

## 目的

本轮只验证 `CBF-1 mode transition audit` 的最小采集链路：

```text
run_bpc_future journey smoke
  -> journey_counterfactual_replay_capture JSONL
  -> audit_cbf_mode_transition.py
  -> state_t/action_t/state_next + V/barrier_slack
```

该 smoke 不训练 GNN，不启用 controller，不产生 certificate，不证明 5/10
no-regression，也不证明 20-task speedup。

## 运行配置

实例：`very_small`，显式启用 `master_mode=journey`。

capture 组开启：

```text
journey_counterfactual_replay_capture_enabled=true
journey_counterfactual_replay_capture_active_basis_enabled=true
journey_counterfactual_replay_capture_active_basis_max_rows=0
journey_counterfactual_replay_capture_max_journeys=0
journey_counterfactual_replay_capture_pool_max_journeys=0
journey_counterfactual_replay_capture_forbidden_signatures_enabled=true
journey_counterfactual_replay_capture_forbidden_signature_max_count=0
journey_counterfactual_replay_capture_log_empty=true
```

baseline 组使用同一 `very_small + master_mode=journey`，但关闭 capture。

## Solver 对照

| 组别 | status | primal | dual | rmp_solves | pricing_calls | exact_pricing_calls | columns |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline no capture | `TIME_LIMIT` | `132.270984` | `None` | 5 | 6 | 1 | 11 |
| capture on | `TIME_LIMIT` | `132.270984` | `None` | 5 | 6 | 1 | 11 |

解释：

- 该 smoke 中 capture 没有改变求解状态、列数、RMP solve 数或 pricing call 数；
- capture 组 wall time 更高，因为 full pool / active-basis payload 写入 JSONL，有观测开销；
- 因此该 smoke 只能证明采集链路工作，不能证明 production no-regression。

## CBF audit 结果

审计命令读取：

```text
BPC_future/results/cbf_mode_transition_capture_smoke_20260614/logs
```

输出：

```text
summary = BPC_future/results/cbf_mode_transition_audit_smoke_20260614/summary.json
report = BPC_future/logical_graph/run_reports/20260614_bpc_future_cbf_mode_transition_smoke_zh.md
```

关键字段：

```text
capture_event_count = 6
transition_count = 4
mode_switch_count = 4
bad_mode_transition_count = 1
cbf_feasible_observed_count = 3
cbf_infeasible_observed_count = 1
negative_action_transition_count = 4
has_transition_evidence = true
training_ready = false
production_ready = false
goal_complete = false
```

这说明 CBF audit 已能从真实日志恢复 transition，并计算 observed
barrier slack。当前仍是 very_small / task_count=4 的 smoke，不是训练集。

## 结论

CBF-1 的最小链路已经打通：

1. no-certificate-effect capture 可以产生完整 context payload；
2. 离线审计可以构造 `state_t, action_t, state_next`；
3. 离线审计可以识别 mode switch、bad mode transition 和 CBF slack；
4. 当前不具备 training-ready 或 production-ready 资格。

下一步应该用同一 capture 协议采集 5/10/20 多实例、多 context 的连续
transition 数据，再构建 barrier dataset。不能把 very_small smoke 当作
5/10 no-regression 或 20-task speedup 证据。
