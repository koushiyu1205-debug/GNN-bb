# Sharded Pulse Phase 7AF Target Path-option Diagnostics 报告

日期：2026-06-13

## 目标

本轮只做 Phase 7AF：target path-option / start-time diagnostics。

Phase 7AE 已经把 target sequence `[8,15,5]` 推进到 prefix `[8,15]`，但下一步 `5` 被 time-window 剪掉。由于 Phase 7AB 已证明同 context 下 residual replay 的 `[8,15,5]` 可以用 Phase 3A materialization 成功回放，本轮目标是记录 target prefix 下实际进入 Pulse 的 path option / start interval，判断是否走到了 replay 中可行的 option family。

## 实现摘要

### 1. Transition core

`transition_root_only_pulse()` 新增：

- `target_path_diagnostics_enabled`
- `target_path_diagnostics_max_samples`

返回字段新增：

- `pulse_target_path_diagnostics_enabled`
- `pulse_target_path_prefix_samples`
- `pulse_target_path_blocked_samples`

记录内容：

- prefix sample：
  - `prefix`
  - `arc_ids`
  - `start_lb`
  - `start_ub`
  - `offset`
  - `current_time`
- blocked transition sample：
  - `reason`
  - `prefix`
  - `next`
  - `arc_ids`
  - `option`
  - 当前 start interval / offset
  - time-window 分支的 `arrival_offset / next_start_lb / next_start_ub / ready / due / service`

这些 diagnostics capped、只读，不改变搜索顺序、不改变剪枝、不改变候选返回。

### 2. Pricing / driver / ROI

`JourneyPricingConfig` 新增：

- `pulse_target_path_diagnostics_enabled`
- `pulse_target_path_diagnostics_max_samples`

driver 支持：

- generic `journey_pulse_target_path_diagnostics_*`
- audit override `journey_sharded_pulse_audit_target_path_diagnostics_*`
- worker override `journey_sharded_pulse_hidden_negative_worker_target_path_diagnostics_*`

日志 / summary 新增：

- `pulse_target_path_diagnostics_enabled`
- `pulse_target_path_prefix_samples`
- `pulse_target_path_blocked_samples`
- `pulse_worker_target_path_diagnostics_enabled`
- `pulse_worker_target_path_prefix_samples`
- `pulse_worker_target_path_blocked_samples`
- `worker_target_path_diagnostics_enabled`
- `worker_target_path_prefix_samples`
- `worker_target_path_blocked_samples`

### 3. ROI diagnostic profile

新增 profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic`

该 profile：

- 仅 20-task 生效；
- 继承 target first-task priority；
- 继承 target transition priority；
- target sequence = `8,15,5`；
- `target_path_diagnostics_enabled=True`；
- `target_path_diagnostics_max_samples=12`；
- 不开启 production default；
- 不产生 official certificate effect。

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_target_path_diagnostics_record_time_window_sample \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_target_sequence_diagnostics_surface_in_pricing_log \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 4 tests in 0.005s
OK
```

## Apollo20 Narrow Probe

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7af_target_path_diagnostics_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_transition_priority \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic \
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

- `BPC_future/results/sharded_pulse_phase7af_target_path_diagnostics_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7af_target_path_diagnostics_20260613/summary.csv`

## 关键结果

| profile | path diag | target prefix | blocked | worker sequences |
|---|---:|---:|---|---|
| target_transition_priority | False | 2 | `time_window` at `[8,15] -> 5` | `[8,15,18,4]`; `[8,15,18]`; `[8,15,4]`; `[8,15]` |
| target_path_diagnostic | True | 2 | `time_window` at `[8,15] -> 5` | `[8,15,18,4]`; `[8,15,18]`; `[8,15,4]`; `[8,15]` |

prefix samples：

```text
prefix=8;arc_ids=0->8:low_risk:2;start_lb=0.000000;start_ub=11.880447;offset=260.843506;current_time=260.843506
prefix=8,15;arc_ids=0->8:low_risk:2|8->15:low_risk:2;start_lb=0.000000;start_ub=11.880447;offset=296.942537;current_time=296.942537
prefix=8,15;arc_ids=0->8:low_risk:2|8->15:low_time:0;start_lb=0.000000;start_ub=11.880447;offset=296.068747;current_time=296.068747
```

blocked samples 摘要：

```text
prefix=8,15; next=5; arc_ids=0->8:low_risk:2|8->15:low_risk:2|15->5:low_risk:2; next_start_ub=-18.212969
prefix=8,15; next=5; arc_ids=0->8:low_risk:2|8->15:low_risk:2|15->5:low_time:0; next_start_ub=-17.821765
prefix=8,15; next=5; arc_ids=0->8:low_risk:2|8->15:low_risk:2|15->5:low_energy:1; next_start_ub=-17.864000
prefix=8,15; next=5; arc_ids=0->8:low_risk:2|8->15:low_time:0|15->5:low_risk:2; next_start_ub=-17.339179
prefix=8,15; next=5; arc_ids=0->8:low_risk:2|8->15:low_time:0|15->5:low_time:0; next_start_ub=-16.947975
prefix=8,15; next=5; arc_ids=0->8:low_risk:2|8->15:low_time:0|15->5:low_energy:1; next_start_ub=-16.990210
```

7AB residual replay 的可行 signature 是：

```text
0->8:low_time:0
8->15:low_risk:2
15->5:low_risk:2
5->0:low_time:0
start=0.0
```

## 当前结论

Phase 7AF 把 coverage gap 从 task ordering 进一步定位到 arc-option ordering。

当前 worker 在 target prefix `[8,15]` 下先进入的是：

```text
0->8:low_risk:2
```

这条 first arc 导致 offset 已经约 `260.84`，到 `[8,15]` 后 offset 约 `296`，因此对 `15 -> 5` 的所有 sampled options 都出现负 `next_start_ub`，被 time-window 剪掉。

而 7AB replay 已证明可行 residual column 使用的是：

```text
0->8:low_time:0
```

所以现在最直接的下一步不是继续调 first-task shard 或 target next-task ordering，而是做 Phase 7AG：target arc-option priority diagnostic，让 target prefix 优先尝试 replay signature 对应的 path option family。

## 边界

- opt-in diagnostic profile only；
- 不默认启用 worker；
- 不开启 official certificate gate；
- 不改变 official lower bound；
- 不做 resume / parallel / 20-task full A/B；
- path diagnostics 只记录 capped samples，不参与剪枝。

## 下一步建议

Phase 7AG：target arc-option priority diagnostic。

建议只在 diagnostic profile 中：

1. 对 target sequence `[8,15,5]` 指定 replay option id sequence：
   - `0->8:low_time:0`
   - `8->15:low_risk:2`
   - `15->5:low_risk:2`
   - `5->0:low_time:0`
2. 当 current prefix 匹配 target prefix 时，把对应 arc option 移到该 edge options 的最前；
3. 不删除其他 arc options；
4. 观察 target prefix 是否能从 `2` 推到 `3`，以及是否 materialized；
5. 仍不扩大 worker budget，不开启 production default，不让 Pulse certificate 生效。
