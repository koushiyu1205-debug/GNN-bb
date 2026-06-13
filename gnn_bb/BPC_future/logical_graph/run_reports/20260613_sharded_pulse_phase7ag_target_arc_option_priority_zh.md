# Sharded Pulse Phase 7AG Target Arc-option Priority 报告

日期：2026-06-13

## 目标

本轮只做 Phase 7AG：target arc-option priority diagnostic。

Phase 7AF 已经定位到：Apollo20 worker 能到达 target prefix `[8,15]`，但该 prefix 实际使用 `0->8:low_risk:2`，而 Phase 7AB residual replay 证明可行 signature 使用 `0->8:low_time:0`。本轮目标是验证能否在 target prefix 中优先探索 replay 对应的 arc option family。

本轮不是 worker ROI 实验，不开启 production default，不开启 official certificate gate。

## 实现摘要

### 1. Transition core

`transition_root_only_pulse()` 新增：

- `target_arc_option_priority_enabled`
- `target_arc_option_priority_sequence`

返回字段新增：

- `pulse_target_arc_option_priority_enabled`
- `pulse_target_arc_option_priority_sequence`

语义：

- 仅当当前 sortie sequence 是 target sequence 的前缀时生效；
- 仅把该层目标边对应的 option id 移到候选 option 最前；
- 不丢弃任何 option；
- 不改变剪枝规则；
- 不改变 candidate / certificate / official lower-bound 语义。

### 2. Pricing / Driver / ROI

`JourneyPricingConfig` 新增：

- `pulse_target_arc_option_priority_enabled`
- `pulse_target_arc_option_priority_sequence`

driver 支持：

- generic `journey_pulse_target_arc_option_priority_*`
- audit override `journey_sharded_pulse_audit_target_arc_option_priority_*`
- worker override `journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_*`

日志 / summary 新增：

- `pulse_target_arc_option_priority_enabled`
- `pulse_target_arc_option_priority_sequence`
- `pulse_worker_target_arc_option_priority_enabled`
- `pulse_worker_target_arc_option_priority_sequence`
- `worker_target_arc_option_priority_enabled`
- `worker_target_arc_option_priority_sequence`

### 3. ROI diagnostic profile

新增 profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority`

该 profile：

- 仅 20-task 生效；
- 继承 target first-task priority；
- 继承 target transition priority；
- target sequence = `8,15,5`；
- target arc-option priority sequence =
  - `0->8:low_time:0`
  - `8->15:low_risk:2`
  - `15->5:low_risk:2`
  - `5->0:low_time:0`
- 保留 target path diagnostics，sample cap = `12`。

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_target_arc_option_priority_moves_preferred_option_first \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_target_sequence_diagnostics_surface_in_pricing_log \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 4 tests in 0.003s
OK
```

全量回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 476 tests in 1.440s
OK (skipped=1)
```

`git diff --check`：通过。

## Apollo20 Narrow Probe

运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_path_diagnostic \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority \
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

- `BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_20260613/summary.csv`

关键结果：

| profile | target arc priority | target prefix | blocked | worker returned / added |
|---|---:|---:|---|---:|
| baseline | False | 0 | none | 0 / 0 |
| target_path_diagnostic | False | 2 | `time_window` at `[8,15] -> 5` | 4 / 4 |
| target_arc_option_priority | True | 1 | `deadline` | 0 / 0 |

7AF path diagnostic prefix sample：

```text
prefix=8;arc_ids=0->8:low_risk:2;start_lb=0.000000;start_ub=11.880447;offset=260.843506
```

7AG target arc-option priority prefix sample：

```text
prefix=8;arc_ids=0->8:low_time:0;start_lb=0.000000;start_ub=107.447026;offset=165.276927
```

这说明 target arc-option priority 生效：同一 target first task `8` 的首条边已从 `low_risk:2` 改为 residual replay 对应的 `low_time:0`。

但在相同 0.2s current-probe 预算下，7AG 只达到 prefix length `1`，随后以 `deadline` 停止，没有返回或加入列。

## Diagnostic Budget Probe

为确认不是单纯 0.2s 预算过低，额外跑单 profile 1.0s 诊断预算：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_budget_probe_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_arc_option_priority \
  --time-limit 6.0 \
  --audit-time-limit 0.2 \
  --worker-time-limit 1.0 \
  --current-probe-time-limit 1.0 \
  --pricing-time-limit 0.4 \
  --pricing-max-dp-states 1000 \
  --max-cg-iterations 3 \
  --audit-max-recursions 30000 \
  --worker-max-recursions 80000 \
  --current-probe-max-recursions 80000 \
  --current-probe-min-tasks 20 \
  --quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_budget_probe_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7ag_target_arc_option_priority_budget_probe_20260613/summary.csv`

结果仍为：

- target prefix length = `1`
- blocked reason = `deadline`
- worker returned / added = `0 / 0`

## Exactness 边界

- 7AG 只改变 target diagnostic profile 下的 option 遍历顺序；
- 所有 path options 仍保留；
- 不改变 leaf materialization；
- 不改变 true-RC 复算；
- 不改变 duplicate / incomplete / certificate 状态机；
- 不更新 official lower bound；
- 不默认启用 worker；
- 不打开 5/10/20 production certificate gate。

## 结论

Phase 7AG 完成了目标 arc-option priority 的 opt-in 接线与可观测性验证。它证明我们可以把 target prefix 的 `0->8` 首选 option 从 `low_risk:2` 改成 residual replay 中可行的 `low_time:0`。

但它没有改善 `[8,15,5]` coverage：Apollo20 窄 probe 和 1.0s 诊断预算 probe 都只达到 prefix length `1`，以 `deadline` 停止，且没有返回可加列。因此 7AG 不是 ROI 正信号，不能据此继续放大 worker、打开 official certificate gate，或默认启用 Pulse。

下一步若继续诊断，应做更局部的 target path/start-time replay 与 transition ordering 对照；若目标是求解性能，则应回到 Phase 7O/7P 的 ROI 决策框架，暂停继续叠 active-worker gate。
