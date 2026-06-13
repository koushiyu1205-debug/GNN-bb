# Sharded Pulse Phase 7O Leaf-level Stop-after-first-negative Gate 报告

日期：2026-06-12

## 目标

上一轮 `stop-after-first-negative` 只停止后续 first-task / child shards。它能让 `mt20_greedy_apollo_01` 的 worker 只跑 2 个 required shards，但 active shard 内部仍要枚举到完整 shard 结束，worker time 仍约 `0.05s`。

本轮进一步把 early stop 下沉到 transition core 的 leaf 层：

> 在 hidden-negative worker 的 opt-in path 中，transition Pulse 一旦 materialize 出一个非 forbidden、非已有 task-set 的 true-RC negative leaf，就停止当前 shard 的后续枚举。

这不是 proof/certificate 功能，只用于 bounded hidden-negative worker 找列。

## 实现摘要

### 1. Transition core leaf-level early stop

`transition_root_only_pulse()` 新增参数：

- `stop_after_first_negative`

触发条件：

- 显式开启 `stop_after_first_negative=True`；
- leaf 已通过 Phase 3A materialization：
  - sortie 通过 `evaluate_timed_trip()`；
  - journey 通过 `make_journey()`；
  - true RC 通过 `materialize_pulse_leaf_candidate()` / `manual_journey_reduced_cost()`；
- `candidate.true_reduced_cost < -eps`；
- candidate signature 不在 forbidden set；
- 如果传入 pool task sets，则 candidate task set 必须不在已有 pool task sets 中。

触发后：

- 当前 transition shard 返回 `FOUND_NEGATIVE`；
- `exhausted=False`；
- reason = `stop_after_first_negative`；
- 不可能进入 `CERTIFIED_NO_NEGATIVE` path。

### 2. Sharded worker 传参

`_price_journeys_by_sharded_pulse_guarded()` 将：

- `JourneyPricingConfig.pulse_stop_after_first_negative`

传给：

- `transition_root_only_pulse(stop_after_first_negative=...)`

因此现有 opt-in worker profile 同时具备：

- leaf-level stop；
- outer shard-level stop；
- pre-heuristic add-column path；
- impact filter；
- 20-only gate。

## Focused Correctness Tests

新增 focused tests：

- `test_transition_pulse_stop_after_first_negative_exits_current_shard`
- `test_sharded_pulse_stop_after_first_negative_passes_to_transition_core`

覆盖：

- leaf-level early stop 后 transition result 为 `FOUND_NEGATIVE` 且 `exhausted=False`；
- early stop 明显减少 generated traces / recursions；
- sharded pricing 会把 config 传进 transition core；
- result 不被 driver 识别为 global certificate。

## 20-task Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_20_smoke_20260612 \
--instances phase7o_20_smoke \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown \
--time-limit 4.0 \
--audit-time-limit 0.15 \
--worker-time-limit 0.15 \
--current-probe-time-limit 0.15 \
--pricing-time-limit 0.08 \
--max-cg-iterations 3 \
--audit-max-recursions 30000 \
--worker-max-recursions 30000 \
--current-probe-max-recursions 15000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_20_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_20_smoke_20260612/summary.csv`

与上一轮 outer-shard-only stop 对比：

| instance | worker time | recursions | added | primal |
|---|---:|---:|---:|---:|
| `mt20_greedy_apollo_01` outer stop | 0.051013 | 186 | 1 | 1030.002361 |
| `mt20_greedy_apollo_01` leaf stop | 0.032457 | 115 | 1 | 1030.002361 |

关键观察：

- worker time 降低约 `36%`；
- recursions 降低约 `38%`；
- 保留 1 个 new task-set；
- primal 改善保持 `1061.554044 -> 1030.002361`；
- `pulse_worker_impact_filter_candidate_count=1`，`selected_count=1`。

## Full Gate

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_gate_20260612 \
--instances phase7o_gate \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown \
--time-limit 4.0 \
--audit-time-limit 0.15 \
--worker-time-limit 0.15 \
--current-probe-time-limit 0.15 \
--pricing-time-limit 0.08 \
--max-cg-iterations 3 \
--audit-max-recursions 30000 \
--worker-max-recursions 30000 \
--current-probe-max-recursions 15000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_leaf_stop_first_gate_20260612/summary.csv`

### 5-task full balanced gate

| metric | baseline | leaf-stop profile |
|---|---:|---:|
| instances | 20 | 20 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| critical disagreement | 0 | 0 |
| avg wall time | 0.026935 | 0.024900 |
| class | baseline | 3 improved, 17 no_regression |

### 10-task specified gate

| metric | baseline | leaf-stop profile |
|---|---:|---:|
| instances | 7 | 7 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| critical disagreement | 0 | 0 |
| median wall time | 0.103232 | 0.100569 |
| class | baseline | 7 no_regression |

### 20-task smoke

| metric | baseline | leaf-stop profile |
|---|---:|---:|
| instances | 3 | 3 |
| worker events | 0 | 1 |
| added columns | 0 | 1 |
| new task-set | 0 | 1 |
| critical disagreement | 0 | 0 |
| avg wall time | 0.189502 | 0.207028 |
| class | baseline | 1 improved, 2 no_regression |

Active 20-task row：

| instance | baseline wall | candidate wall | baseline primal | candidate primal | worker time | recursions | next RMP objective delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| `mt20_greedy_apollo_01` | 0.153759 | 0.202673 | 1061.554044 | 1030.002361 | 0.031975 | 115 | -31.551683 |

## 当前判断

这是一个真实的 overhead reduction：

- 20-task active worker time 从约 `0.05s` 降到约 `0.032s`；
- 同一 new task-set / primal improvement signal 保留；
- 5-task / 10-task 仍由 20-only gate 完全禁止 worker；
- no certificate / official lower-bound side effect。

但最终目标仍未完成：

- active 20-task wall time 仍慢于 baseline；
- final judge / retry tail 仍未证明下降；
- 还不能默认启用；
- 还不能进入 official certificate gate。

下一步建议继续沿 active shard 内部降本：

- high-yield first-task / second-action ordering；
- current-context probe 的 task-set target fingerprint；
- per-shard productivity gate；
- 或针对当前 active shard 的 transition child ordering。

不建议：

- 增加 worker time limit；
- 默认启用 worker；
- official certificate gate；
- 20/100 A/B；
- resume / parallel。

## 验证

语法检查通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests 通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_stop_after_first_negative_exits_current_shard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_stop_after_first_negative_passes_to_transition_core \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 4 tests in 0.069s
OK
```

完整 `BPCFutureTests` 通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 452 tests in 54.996s
OK (skipped=1)
```

diff whitespace 检查通过：

```bash
git diff --check
```
