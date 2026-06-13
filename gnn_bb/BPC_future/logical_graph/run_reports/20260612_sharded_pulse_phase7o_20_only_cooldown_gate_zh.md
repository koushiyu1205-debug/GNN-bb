# Sharded Pulse Phase 7O 20-only Cooldown Gate 报告

日期：2026-06-12

## 目标

上一轮 `low_budget_cooldown` 在 20-task 上保留 primal / column-quality signal，但 10-task median wall time 明显增加，不能作为 `目标.md` 的候选 profile。

本轮目标是验证一个更严格的 scale gate：

- 5-task：完全 no-op；
- 10-task：完全 no-op；
- 20-task：才启用 delayed current-context Pulse worker；
- worker 仍使用 impact filter、low-budget probe、success cooldown；
- 不改变默认 solver 配置；
- 不放开 official certificate gate。

## 实现摘要

新增 calibration profile：

- `strict_worker_delayed_current_probe_impact_20_only_cooldown`

语义：

- `task_count < 20` 时 `_apply_profile()` 返回空配置；
- `task_count >= 20` 时复用：
  - delayed `on_certificate_candidate` audit trigger；
  - current-context probe；
  - `require_new_or_active_support` impact filter；
  - low-budget probe factor；
  - `journey_sharded_pulse_hidden_negative_worker_success_cooldown_rounds=2`。

该 profile 只在 calibration script 中显式 opt-in，不影响默认 benchmark。

## Gate 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_20_only_cooldown_gate_20260612 \
--instances phase7o_gate \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_cooldown \
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

- `BPC_future/results/sharded_pulse_phase7o_20_only_cooldown_gate_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_20_only_cooldown_gate_20260612/summary.csv`

## Gate 结果

### 5-task full balanced gate

| metric | baseline | 20-only cooldown |
|---|---:|---:|
| instances | 20 | 20 |
| status | 20 TIME_LIMIT | 20 TIME_LIMIT |
| avg wall time | 0.025658 | 0.025209 |
| median wall time | 0.025541 | 0.025385 |
| max wall time | 0.039156 | 0.028867 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 1 improved, 19 no_regression |

结论：5-task 全量 gate 无回退；Pulse worker 完全没有启动。

### 10-task specified gate

| metric | baseline | 20-only cooldown |
|---|---:|---:|
| instances | 7 | 7 |
| status | 7 TIME_LIMIT | 7 TIME_LIMIT |
| avg wall time | 0.104169 | 0.102878 |
| median wall time | 0.103810 | 0.101739 |
| max wall time | 0.111284 | 0.110636 |
| worker events | 0 | 0 |
| added columns | 0 | 0 |
| official changed | 0 | 0 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 7 no_regression |

结论：10-task 指定 gate 无回退；该 profile 通过 scale gate 完全不触发 worker，因此不会为了 20-task 改善牺牲 10-task。

### 20-task smoke

| metric | baseline | 20-only cooldown |
|---|---:|---:|
| instances | 3 | 3 |
| status | 3 TIME_LIMIT | 3 TIME_LIMIT |
| avg wall time | 0.192052 | 0.239239 |
| median wall time | 0.171330 | 0.252797 |
| max wall time | 0.250302 | 0.293946 |
| worker events | 0 | 1 |
| added columns | 0 | 1 |
| new task-set | 0 | 1 |
| official changed | 0 | 1 |
| objective mismatch | 0 | 0 |
| critical disagreement | 0 | 0 |
| class | baseline | 1 improved, 2 no_regression |

Active 20-task row：

| instance | primal baseline | primal candidate | added | composition | next RMP objective delta | class |
|---|---:|---:|---:|---|---:|---|
| mt20_greedy_apollo_01 | 1061.554044 | 1030.002361 | 1 | 1 new task-set | -31.551683 | improved |

结论：

- 20-task 有 primal / column-quality improvement signal；
- 该 signal 仍伴随 wall-time 增加；
- 当前不能解释为 wall-time ROI 或 production-ready speedup。

## Exactness 边界

- 该 profile 只在 calibration script 中 opt-in；
- default solver 配置不变；
- worker returned journeys 仍走 true-RC sanitize；
- Pulse no-column / incomplete / duplicate-only 不更新 official lower bound；
- 无 critical disagreement；
- 无 `OPTIMAL` objective / dual mismatch；
- 所有影响都来自正常 add-column path。

## 当前判断

`strict_worker_delayed_current_probe_impact_20_only_cooldown` 是当前最干净的 Phase 7O 候选：

- 5-task full balanced gate：无回退；
- 10-task specified gate：无回退；
- 20-task selected smoke：有 1 个 primal / new-task-set improvement signal。

它仍未满足最终目标的强版本：

- 20-task wall time 没有下降；
- final judge / retry tail 尚未下降；
- 还不能默认启用；
- 还不能进入 official certificate gate。

下一步应继续做 20-task productivity / ROI gate，把同一类 new-task-set signal 的 wall-time overhead 压低，而不是放大 worker budget。

## 验证

语法检查通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
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
