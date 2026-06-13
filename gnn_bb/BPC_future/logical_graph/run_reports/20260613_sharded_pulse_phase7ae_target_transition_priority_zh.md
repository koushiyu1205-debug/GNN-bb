# Sharded Pulse Phase 7AE Target Transition Priority 报告

日期：2026-06-13

## 目标

本轮只做 Phase 7AE：target-shard internal ordering diagnostic。

Phase 7AD 已证明 target first-task shard priority 能让 worker 在小预算内进入 shard `8`，但目标 sequence `[8,15,5]` 只推进到 prefix length `1`。本轮目标是验证：

1. 在 prefix 匹配 target sequence 时，把下一目标 task 提前是否能继续推进 target reachability；
2. 不过滤任何其他 transition；
3. 不改变 certificate / official lower-bound 语义；
4. 不扩大 worker budget。

## 实现摘要

### 1. Transition core

`transition_root_only_pulse()` 增加：

- `target_transition_priority_enabled`
- `target_transition_priority_sequence`

语义：

- 如果当前 `current_sequence` 是 target sequence 前缀，则把下一目标 task 移到当前 transition 候选列表最前；
- 其余候选 task 仍保留；
- 只改变搜索顺序，不改变 feasibility / pruning / certificate 语义。

### 2. Pricing config

`JourneyPricingConfig` 增加：

- `pulse_target_transition_priority_enabled`
- `pulse_target_transition_priority_sequence`

guarded sharded Pulse 会把该配置传入 transition core。

### 3. Driver config / logs

driver 支持：

- generic `journey_pulse_target_transition_priority_*`
- audit override `journey_sharded_pulse_audit_target_transition_priority_*`
- worker override `journey_sharded_pulse_hidden_negative_worker_target_transition_priority_*`

新增日志字段：

- `pulse_target_transition_priority_enabled`
- `pulse_target_transition_priority_sequence`
- `pulse_worker_target_transition_priority_enabled`
- `pulse_worker_target_transition_priority_sequence`

### 4. ROI diagnostic profile

新增 profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority`

该 profile：

- 仅 20-task 生效；
- 继承 coverage diagnostics；
- target sequence diagnostics = `8,15,5`；
- target first-task priority sequence = `8,15,5`；
- target transition priority sequence = `8,15,5`；
- `stop_after_first_negative=False`；
- 不开启 production default；
- 不产生 official certificate effect。

### 5. ROI summary

summary 增加：

- `worker_target_transition_priority_enabled`
- `worker_target_transition_priority_sequence`

## Focused Tests

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_target_transition_priority_reaches_next_target_earlier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_target_sequence_diagnostics_surface_in_pricing_log \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 4 tests in 0.007s
OK
```

## Apollo20 Narrow Probe

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7ae_target_transition_priority_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority \
  --time-limit 4.0 \
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

输出：

- `BPC_future/results/sharded_pulse_phase7ae_target_transition_priority_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7ae_target_transition_priority_20260613/summary.csv`

## 关键结果

| profile | first-task priority | transition priority | worker returned | worker sequences | follow-up first negative | target prefix | attempts / accepted | blocked |
|---|---:|---:|---:|---|---|---:|---:|---|
| coverage_scan | False | False | 1 | `[6,19]` | `[8,15,5]` | 0 | 0 / 0 | deadline |
| coverage_target_priority | True | False | 3 | `[8,4,18]`; `[8,5]`; `[8,4]` | `[15,5,4]` | 1 | 1 / 1 | deadline |
| coverage_target_transition_priority | True | True | 4 | `[8,15,18,4]`; `[8,15,18]`; `[8,15,4]`; `[8,15]` | `[12,5,4]` | 2 | 9 / 3 | time_window at `[8,15] -> 5` |

target-transition profile 的 target diagnostics：

- `worker_target_sequence = [8, 15, 5]`
- `worker_target_sequence_reached_prefix_len = 2`
- `worker_target_sequence_completed = False`
- `worker_target_sequence_materialized = False`
- `worker_target_sequence_blocked_reason = time_window`
- `worker_target_sequence_blocked_prefix = [8,15]`
- `worker_target_sequence_blocked_next_task = 5`
- `worker_target_sequence_prune_reason_counts = [['time_window', 6]]`

## 当前结论

Phase 7AE 证明 target transition priority 能把 worker 推进到 residual target family 的 prefix `[8,15]`，并返回多条以 `[8,15]` 开头的新列。

但目标 `[8,15,5]` 仍未 materialized。由于 Phase 7AB 已证明同 context 下 `[8,15,5]` 可通过 Phase 3A materialization replay 且 true RC 一致，当前缺口进一步定位为：

- target prefix `[8,15]` 下的 arc-option ordering；
- no-wait start interval / start candidate 选择；
- path-specific transition state 没有在 budget 内走到 residual replay 使用的 feasible option family。

这不是 first-task shard scheduling 问题，也不是 next-task ordering 问题。

## 边界

- opt-in diagnostic profile only；
- 不默认启用 worker；
- 不开启 official certificate gate；
- 不改变 official lower bound；
- 不做 resume / parallel / 20-task full A/B；
- target priority 只重排候选，不丢弃候选。

## 下一步建议

下一步应做 Phase 7AF：target path-option / start-time ordering diagnostic。

建议只在 diagnostic profile 中：

1. 记录 target prefix `[8,15]` 达到时的 capped arc option ids / start interval samples；
2. 对照 7AB replay 的 signature：`0->8:low_time:0`, `8->15:low_risk:2`, `15->5:low_risk:2`, `5->0:low_time:0`, start `0.0`；
3. 若当前 transition state 到 `[8,15]` 使用了不同 `0->8` option 或 start interval 导致 `15->5` time-window prune，则优先做 target option priority；
4. 仍不扩大 worker budget，不开启 production default，不让 Pulse certificate 生效。
