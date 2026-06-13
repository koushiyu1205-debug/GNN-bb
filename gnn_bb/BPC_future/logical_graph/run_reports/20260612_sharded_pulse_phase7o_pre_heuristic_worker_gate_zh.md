# Sharded Pulse Phase 7O Pre-heuristic Worker Gate 报告

日期：2026-06-12

## 目标

上一轮 `20-only cooldown` profile 已经满足：

- 5-task no-regression；
- 10-task no-regression；
- 20-task 有 primal / new-task-set signal。

但它仍在 20-task active row 上慢于 baseline。日志显示旧路径的 worker 位于 heuristic pricing 之后：

1. 先运行 heuristic；
2. 再运行 Sharded Pulse hidden-negative worker；
3. 如果 worker 加列，再进入下一轮 RMP。

本轮尝试一个更合理的 opt-in 顺序：

先用 bounded Sharded Pulse worker 试找 true-RC negative column；若找到并 add-column，则本轮像普通 pricing 找到负列一样直接进入下一轮 RMP，跳过本轮 heuristic / exact pricing。

若 worker 没找到列，则原 heuristic / exact path 照常运行。

## 实现摘要

新增 solver opt-in 配置：

- `journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled`

新增 calibration profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_cooldown`

profile 语义：

- `task_count < 20`：不注入任何 Pulse audit/worker 配置；
- `task_count >= 20`：
  - delayed current-context probe；
  - impact filter；
  - low-budget probe；
  - success cooldown；
  - worker before heuristic。

Exactness 边界：

- worker returned journeys 仍走 true-RC sanitize；
- worker incomplete / no-column / duplicate-only 不更新 official lower bound；
- 找到列只走正常 add-column path；
- 不产生 certificate；
- default solver 行为不变。

## Gate 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_gate_20260612 \
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

- `BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_gate_20260612/summary.csv`

## Gate 结果

### 5-task full balanced gate

| metric | baseline | pre-heuristic 20-only |
|---|---:|---:|
| instances | 20 | 20 |
| status | 20 TIME_LIMIT | 20 TIME_LIMIT |
| avg wall time | 0.025284 | 0.025203 |
| median wall time | 0.025465 | 0.025412 |
| max wall time | 0.033396 | 0.029156 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |

结论：5-task 完全 no-op，无回退。

### 10-task specified gate

| metric | baseline | pre-heuristic 20-only |
|---|---:|---:|
| instances | 7 | 7 |
| status | 7 TIME_LIMIT | 7 TIME_LIMIT |
| avg wall time | 0.102809 | 0.102915 |
| median wall time | 0.101716 | 0.102372 |
| max wall time | 0.110512 | 0.110097 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |

结论：10-task 完全 no-op，无回退。

### 20-task smoke

| metric | baseline | pre-heuristic 20-only |
|---|---:|---:|
| instances | 3 | 3 |
| status | 3 TIME_LIMIT | 3 TIME_LIMIT |
| avg wall time | 0.193201 | 0.215690 |
| median wall time | 0.169645 | 0.222174 |
| max wall time | 0.251777 | 0.252718 |
| worker events | 0 | 1 |
| added columns | 0 | 1 |
| new task-set | 0 | 1 |
| generated sequences | 735 | 734 |
| evaluated timed trips | 3698 | 3689 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 1 improved, 2 no_regression |

Active row：

| instance | baseline wall | candidate wall | baseline primal | candidate primal | added | next RMP objective delta |
|---|---:|---:|---:|---:|---:|---:|
| mt20_greedy_apollo_01 | 0.158182 | 0.222174 | 1061.554044 | 1030.002361 | 1 new task-set | -31.551683 |

## 额外 tighter-probe smoke

为了确认是否可以通过更小 current-probe cap 保留同一信号，额外运行：

- `current_probe_time_limit=0.09`
- low-budget factor 后实际 probe cap 约 `0.03s`

输出：

- `BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_tighter_probe_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_20_only_pre_heuristic_tighter_probe_smoke_20260612/summary.csv`

结果：

- `mt20_greedy_apollo_01` worker triggered；
- worker time `0.031007`；
- recursions `109`；
- returned / added = `0 / 0`；
- primal 未改善。

结论：当前 new-task-set signal 大约需要 `0.05s` / `180` recursion 级别的 Pulse 搜索，简单降低 probe cap 会丢掉信号。

## 当前判断

pre-heuristic worker 是正确方向：

- 它让 Pulse worker 在 costly heuristic 前先尝试；
- active row 上避免了第一轮 heuristic；
- 20-task generated/evaluated 总量略降；
- 5/10 完全 no-op；
- exactness 边界不变。

但它仍未达到最终目标：

- active 20-task wall time 仍慢于 baseline；
- final judge / retry tail 仍没有实质下降；
- 不能默认启用；
- 不能进入 official certificate gate。

下一步不应继续简单降低 worker cap；更可能需要：

- 更便宜的 current-context probe ordering；
- 更强的 first-task / second-action shard priority；
- 或只在已知 high-yield 20-task fingerprint 下触发 worker。

## 验证

语法检查通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
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
