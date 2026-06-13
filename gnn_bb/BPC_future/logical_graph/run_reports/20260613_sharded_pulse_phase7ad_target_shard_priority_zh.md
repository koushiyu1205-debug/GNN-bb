# Sharded Pulse Phase 7AD Target First-task Shard Priority 报告

日期：2026-06-13

## 目标

本轮只做 Phase 7AD：诊断性 target first-task shard priority。

背景来自 Phase 7AC：Apollo20 coverage probe 中，worker 目标 sequence `[8,15,5]` 在目标 first-task shard 作用域内 `reached_prefix_len=0`、`transition_attempts=0`、`blocked_reason=deadline`。这说明当时不是 time/resource/bound/archive 剪掉目标 sequence，而是 deadline 前没有进入 first-task shard `8` 的目标 transition。

本轮目标：

1. 只在 opt-in diagnostic profile 中把 target first-task shard 提前；
2. 不过滤任何 shard；
3. 不改变 certificate / official lower-bound 语义；
4. 验证 shard `8` 是否能在小预算内进入 transition 搜索。

## 实现摘要

### 1. Pricing config

`JourneyPricingConfig` 增加：

- `pulse_target_first_task_priority_enabled`
- `pulse_target_first_task_priority_sequence`

新增 helper：

- `_prioritize_target_first_task_shard()`

语义：

- 默认关闭时顺序完全不变；
- 开启且 target first task 存在时，只把该 first-task shard 移到最前；
- 其余 first-task shards 仍然保留；
- 这只是调度顺序，不是剪枝，不参与证书。

### 2. Driver config / logs

driver 支持：

- generic `journey_pulse_target_first_task_priority_*`
- audit override `journey_sharded_pulse_audit_target_first_task_priority_*`
- worker override `journey_sharded_pulse_hidden_negative_worker_target_first_task_priority_*`

新增日志字段：

- `pulse_target_first_task_priority_enabled`
- `pulse_target_first_task_priority_sequence`
- `pulse_worker_target_first_task_priority_enabled`
- `pulse_worker_target_first_task_priority_sequence`

### 3. ROI diagnostic profile

新增 profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`

该 profile：

- 仅 20-task 生效；
- 继承 coverage diagnostics；
- target sequence diagnostics = `8,15,5`；
- target first-task priority sequence = `8,15,5`；
- `stop_after_first_negative=False`；
- 不开启 production default；
- 不产生 official certificate effect。

### 4. ROI summary

summary 增加：

- `worker_target_first_task_priority_enabled`
- `worker_target_first_task_priority_sequence`

## Focused Tests

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_target_first_task_priority_reorders_only_target \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_target_sequence_diagnostics_surface_in_pricing_log \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 4 tests in 0.013s
OK
```

## Apollo20 Narrow Probe

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7ad_target_shard_priority_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority \
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

- `BPC_future/results/sharded_pulse_phase7ad_target_shard_priority_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7ad_target_shard_priority_20260613/summary.csv`

## 关键结果

| profile | priority | worker returned | worker sequences | follow-up first negative | target prefix | target attempts | target accepted | target blocked |
|---|---:|---:|---|---|---:|---:|---:|---|
| coverage_scan | False | 1 | `[6,19]` | `[8,15,5]` | 0 | 0 | 0 | deadline |
| coverage_target_priority | True | 2 | `[8,4,18]`; `[8,4]` | `[15,5,4]` | 1 | 1 | 1 | deadline |

解释：

- target first-task priority 生效后，worker 确实进入 shard `8`；
- `[8,15,5]` 从完全未开始变成已接受第一个 transition；
- worker 返回了两个以 `8` 开头的新列；
- 但目标 sequence `[8,15,5]` 仍未 completed/materialized，blocked reason 仍为 `deadline`。

## 当前结论

Phase 7AD 修正了 Phase 7AC 中“deadline 前完全没进入 first-task shard 8”的调度问题，但没有完全覆盖 residual target sequence `[8,15,5]`。

当前 coverage 缺口进一步收窄为：

- shard `8` 内部 task / transition ordering；
- 或 shard `8` 内 per-shard budget allocation；
- 而不是 leaf materialization、true-RC context、first-task shard scheduling、time/resource/bound/archive 误剪。

## 边界

- opt-in diagnostic profile only；
- 不默认启用 worker；
- 不开启 official certificate gate；
- 不改变 official lower bound；
- 不做 resume / parallel / 20-task full A/B。

## 下一步建议

下一步应做 Phase 7AE：target-shard internal ordering diagnostic。

建议只在 diagnostic profile 中验证：

1. 当 first-task shard 已固定为 `8` 时，是否可把 target second action `15` 提前；
2. target sequence `[8,15,5]` 是否能从 prefix length `1` 推进到 `2` 或 materialized；
3. 若仍 deadline，则记录 shard `8` 内 transition ordering / expanded prefixes 的 capped samples。

仍不要扩大 worker budget，不要开启 production default，也不要让 Pulse certificate 生效。
