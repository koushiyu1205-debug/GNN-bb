# Sharded Pulse Phase 7O Stop-after-first-negative Gate 报告

日期：2026-06-12

## 目标

上一轮 `pre-heuristic` profile 证明了一个有价值但仍不够便宜的信号：

- 5-task / 10-task 通过 20-only gate 完全 no-op；
- 20-task `mt20_greedy_apollo_01` 可由 Pulse worker 找到并加入 1 个 new task-set；
- primal 从 `1061.554044` 改善到 `1030.002361`；
- 但 active row wall time 仍慢于 baseline。

本轮只加一个非常窄的 worker guard：

> hidden-negative worker 一旦找到第一批 true-RC negative column，就停止继续扫描后续 first-task shards。

目标是减少已找到可加列后的额外 shard 扫描。该 guard 不改变列的 true-RC 检查、不产生 certificate，也不改变默认配置。

## 实现摘要

新增 `JourneyPricingConfig` / `JourneyPricingResult` 字段：

- `pulse_stop_after_first_negative`

新增 solver opt-in 配置：

- `journey_sharded_pulse_hidden_negative_worker_stop_after_first_negative`

行为：

- 仅在显式配置开启时生效；
- guarded sharded Pulse 发现 `all_candidates` 后，停止后续 parent/child shard 调度；
- 已发现候选仍按原路径执行：
  - `manual_journey_reduced_cost()` true-RC sanitize；
  - impact filter；
  - normal add-column path；
- `INCOMPLETE` / no-column / duplicate-only 仍不 certificate。

`strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown` profile 现在开启：

- `journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=True`
- `journey_sharded_pulse_hidden_negative_worker_stop_after_first_negative=True`

## 20-task Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_20_smoke_20260612 \
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

- `BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_20_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_20_smoke_20260612/summary.csv`

Active worker row：

| instance | status | worker shards total | returned / added | worker time | recursions | primal |
|---|---|---:|---:|---:|---:|---:|
| `mt20_greedy_apollo_01` | `FOUND_NEGATIVE` | 2 | 1 / 1 | 0.051013 | 186 | 1030.002361 |

关键观察：

- `pulse_worker_stop_after_first_negative=True`；
- worker 只跑到 2 个 required shards 就停止；
- `transition_time_window_pruned=9726`，`transition_return_pruned=180`；
- 仍加入 1 个 new task-set；
- worker time 仍约 `0.05s`，说明瓶颈主要在找到该负列的 active shard 内部，而不是后续 shard 扫描。

## Full Gate

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_gate_20260612 \
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

- `BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_pre_heuristic_stop_first_gate_20260612/summary.csv`

### 5-task full balanced gate

| metric | baseline | stop-first profile |
|---|---:|---:|
| instances | 20 | 20 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| critical disagreement | 0 | 0 |
| avg wall time | 0.024901 | 0.025398 |
| class | baseline | 20 no_regression |

### 10-task specified gate

| metric | baseline | stop-first profile |
|---|---:|---:|
| instances | 7 | 7 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| critical disagreement | 0 | 0 |
| median wall time | 0.103681 | 0.101363 |
| class | baseline | 7 no_regression |

### 20-task smoke

| metric | baseline | stop-first profile |
|---|---:|---:|
| instances | 3 | 3 |
| worker events | 0 | 1 |
| added columns | 0 | 1 |
| new task-set | 0 | 1 |
| critical disagreement | 0 | 0 |
| avg wall time | 0.192527 | 0.213643 |
| class | baseline | 1 improved, 2 no_regression |

Active 20-task row：

| instance | baseline wall | candidate wall | baseline primal | candidate primal | worker time | recursions | next RMP objective delta |
|---|---:|---:|---:|---:|---:|---:|---:|
| `mt20_greedy_apollo_01` | 0.155130 | 0.222483 | 1061.554044 | 1030.002361 | 0.050740 | 190 | -31.551683 |

## 当前判断

`stop-after-first-negative` 是一个正确的 exact-safe guard：

- 只在 opt-in worker 中生效；
- 不改变 default benchmark；
- 不产生 certificate / official lower-bound side effect；
- 5-task / 10-task gate 仍不触发 worker；
- 20-task 保留 1 个 new task-set / primal improvement signal。

但它没有解决当前主要瓶颈：

- active 20-task worker time 仍约 `0.05s`；
- wall time 仍慢于 baseline；
- final judge / retry tail 没有明显下降；
- 单纯停止后续 shards 不足以形成 wall-time ROI。

下一步如果继续 Phase 7O/7P，应优先优化 active shard 内部：

- high-yield shard ordering；
- cheaper current-context probe fingerprint；
- active-shard early productivity gate；
- 或更强的 transition-level ordering。

不建议做：

- 默认启用 worker；
- official certificate gate；
- 继续加 worker time limit；
- 20/100 A/B；
- resume / parallel。

## 验证

语法检查通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests 通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 2 tests in 0.001s
OK
```

完整 `BPCFutureTests` 通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 450 tests in 1.277s
OK (skipped=1)
```

diff whitespace 检查通过：

```bash
git diff --check
```
