# Sharded Pulse Phase 8B Profile-DP State-cap Sensitivity 报告

日期：2026-06-13

## 目标

Phase 8A 的 pivot classifier 指出，后续优化入口之一可能是 `legacy/profile-DP proof-tail`，尤其是已有 7W matrix 中出现过 `profile_dp_state_cap`。

Phase 8B 只做一个窄 probe：在 `mt20_greedy_apollo_01` 上比较 `journey_pricing_max_dp_states=1000` 与 `5000`，判断提高 profile-DP state cap 是否能直接缓解 tail 或改善 ROI。

本轮不改算法，不改 worker gate，不改 certificate / official lower-bound 语义。

## 运行矩阵

实例：

- `mt20_greedy_apollo_01`

profiles：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`

两组预算：

1. short cap：
   - `time_limit=0.3`
   - `pricing_max_dp_states=1000 / 5000`
2. 1.5s cap：
   - `time_limit=1.5`
   - `pricing_max_dp_states=1000 / 5000`

输出目录：

- `BPC_future/results/sharded_pulse_phase8b_profile_dp_cap1000_short_probe_20260613`
- `BPC_future/results/sharded_pulse_phase8b_profile_dp_cap5000_short_probe_20260613`
- `BPC_future/results/sharded_pulse_phase8b_profile_dp_cap1000_probe_20260613`
- `BPC_future/results/sharded_pulse_phase8b_profile_dp_cap5000_probe_20260613`

## Commands

代表命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase8b_profile_dp_cap1000_probe_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
  --time-limit 1.5 \
  --audit-time-limit 0.2 \
  --worker-time-limit 0.2 \
  --current-probe-time-limit 0.2 \
  --pricing-time-limit 0.4 \
  --pricing-max-dp-states 1000 \
  --max-cg-iterations 3 \
  --audit-max-recursions 30000 \
  --worker-max-recursions 30000 \
  --current-probe-max-recursions 20000 \
  --current-probe-min-tasks 20 \
  --quiet
```

其他三组只改 `output-dir`、`time-limit` 与 `pricing-max-dp-states`。

## 结果

### 1. short cap 0.3s

| cap | profile | pricing_state | wall | primal | worker added | pivot |
|---:|---|---|---:|---:|---:|---|
| 1000 | baseline | `INCOMPLETE_LIMIT` | 0.302005 | 921.640296 | 0 | `no_clear_pivot_signal` |
| 1000 | worker | `INCOMPLETE_LIMIT` | 0.304138 | 921.640296 | 0 | `no_clear_pivot_signal` |
| 5000 | baseline | `FOUND_NEGATIVE` | 0.306511 | 1061.554044 | 0 | `no_clear_pivot_signal` |
| 5000 | worker | `FOUND_NEGATIVE` | 0.300729 | 1061.554044 | 0 | `no_clear_pivot_signal` |

观察：

- 提高 cap 能让短预算下的 pricing path 从 `INCOMPLETE_LIMIT` 变成 `FOUND_NEGATIVE`；
- 但 primal / wall 并不形成可用 ROI；
- worker 没触发 / 没加列；
- 这不能证明 state cap 是稳定可优化瓶颈。

### 2. 1.5s cap

| cap | profile | wall | primal | worker added | follow-up first negative | follow-up relation | pivot |
|---:|---|---:|---:|---:|---|---|---|
| 1000 | baseline | 1.266867 | 923.116819 | 0 | none | `no_worker_add` | `no_clear_pivot_signal` |
| 1000 | worker | 1.289411 | 891.565136 | 1 | `5,8,15` | `disjoint_task_set` | `residual_disjoint_negative` |
| 5000 | baseline | 1.311125 | 921.640296 | 0 | none | `no_worker_add` | `no_clear_pivot_signal` |
| 5000 | worker | 1.341132 | 890.088613 | 1 | `5,8,15` | `disjoint_task_set` | `residual_disjoint_negative` |

profile-DP fields:

- cap 1000 worker:
  - `followup_last_pricing_kind=heuristic`
  - `followup_last_pricing_state=FOUND_NEGATIVE`
  - `followup_last_pricing_reason=partial_dp_negative_journey`
  - `followup_last_pricing_dp_state_count=1001`
  - `followup_profile_dp_incomplete_count=0`
  - `followup_profile_dp_state_cap_hit=False`
- cap 5000 worker:
  - `followup_last_pricing_kind=heuristic`
  - `followup_last_pricing_state=FOUND_NEGATIVE`
  - `followup_last_pricing_reason=partial_dp_negative_journey`
  - `followup_last_pricing_dp_state_count=5001`
  - `followup_profile_dp_incomplete_count=0`
  - `followup_profile_dp_state_cap_hit=False`

观察：

- 1.5s 下没有复现 `profile_dp_state_cap` incomplete；
- follow-up 仍是 worker 后 residual disjoint negative；
- 提高 cap 从 1000 到 5000 让 best RC / primal 有变化，但 wall time 也上升；
- 这不是稳定 proof-tail ROI。

## 判断

Phase 8B 不支持“简单提高 profile-DP state cap”作为下一步主线。

原因：

1. 短 cap 下提高 cap 改变了 pricing state，但没有稳定改善 primal / wall；
2. 1.5s 下 state-cap incomplete 没复现，follow-up bottleneck 仍是 `residual_disjoint_negative`；
3. cap 从 1000 到 5000 增加了搜索量，wall 也随之增加；
4. 这更像预算路径敏感性，而不是可直接生产化的 proof-tail 修复。

## Exactness 边界

- 只运行现有 ROI calibration；
- 不改 pricing / RMP / worker；
- 不改变 certificate；
- Pulse incomplete / no-column 仍不影响 official lower bound；
- 所有结果只作为诊断。

## 结论

Phase 8B 完成：profile-DP cap sensitivity 没有给出稳定 ROI。

下一步不应简单提高 `journey_pricing_max_dp_states`。更合理的方向是：

1. 做 profile-DP state-cap 的结构化归因，而不是直接放大 cap：
   - 哪些 mask / prefix / transition 导致 state explosion；
   - 是 label fanout、time bucket、arc option fanout，还是 replacement-tail。
2. 或转入 RMP stabilization / active fractional degeneracy：
   - 7U / 8A 已显示 20-task Tranq cases 有高 active fractional ratio；
   - 这可能比继续扩大 profile-DP cap 更接近真实 tail。
