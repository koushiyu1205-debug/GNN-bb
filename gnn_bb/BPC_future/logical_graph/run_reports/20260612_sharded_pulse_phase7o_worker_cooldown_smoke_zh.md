# Sharded Pulse Phase 7O Worker Success Cooldown Smoke 报告

日期：2026-06-12

## 目标

本轮只验证一个很窄的 Phase 7O 变体：

在 hidden-negative worker 成功加入列后，跳过后续若干轮可选 Pulse worker probe，观察是否能降低“加了列但 wall time 变差”的副作用。

这不是 production 默认开关，也不是 official certificate gate。

## 实现摘要

新增 opt-in 配置：

- `journey_sharded_pulse_hidden_negative_worker_success_cooldown_rounds`

语义：

- 默认值为 `0`，默认行为不变；
- 当 Sharded Pulse hidden-negative worker 通过正常 add-column path 成功加入列后，设置 cooldown；
- cooldown 期间只跳过可选 hidden-negative worker；
- exact pricing / legacy final judge 仍照常运行；
- skip 会写出 `success_cooldown` worker skip 日志；
- cooldown 不产生 certificate，不影响 official lower bound。

校准脚本新增 profile：

- `strict_worker_delayed_current_probe_impact_low_budget_cooldown`

该 profile 复用 low-budget delayed current-probe impact 配置，并设置：

- `journey_sharded_pulse_hidden_negative_worker_success_cooldown_rounds=2`

## Smoke 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_worker_cooldown_smoke_20260612 \
--instances phase7o_20_smoke \
--profiles baseline strict_worker_delayed_current_probe_impact_low_budget strict_worker_delayed_current_probe_impact_low_budget_cooldown \
--time-limit 12.0 \
--audit-time-limit 0.2 \
--worker-time-limit 0.2 \
--current-probe-time-limit 0.2 \
--pricing-time-limit 0.2 \
--max-cg-iterations 10 \
--audit-max-recursions 50000 \
--worker-max-recursions 50000 \
--current-probe-max-recursions 25000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_worker_cooldown_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_worker_cooldown_smoke_20260612/summary.csv`

## 结果摘要

| instance | profile | primal | wall time | worker returned / added | new task-set | worker time | class |
|---|---|---:|---:|---:|---:|---:|---|
| tranq20_01 | baseline | 860.912211 | 0.357206 | 0 / 0 | 0 | 0 | baseline |
| tranq20_01 | low-budget | 860.912211 | 0.351880 | 0 / 0 | 0 | 0 | no_regression |
| tranq20_01 | low-budget + cooldown | 860.912211 | 0.358129 | 0 / 0 | 0 | 0 | no_regression |
| mt20_greedy_apollo_01 | baseline | 1061.554044 | 0.254094 | 0 / 0 | 0 | 0 | baseline |
| mt20_greedy_apollo_01 | low-budget | 1022.575388 | 0.865410 | 2 / 2 | 2 | 0.212501 | worsened |
| mt20_greedy_apollo_01 | low-budget + cooldown | 1030.002361 | 0.513372 | 1 / 1 | 1 | 0.070875 | worsened |
| mt20_greedy_tranq_01 | baseline | 829.395319 | 0.268177 | 0 / 0 | 0 | 0 | baseline |
| mt20_greedy_tranq_01 | low-budget | 829.395319 | 0.268417 | 0 / 0 | 0 | 0 | no_regression |
| mt20_greedy_tranq_01 | low-budget + cooldown | 829.395319 | 0.267797 | 0 / 0 | 0 | 0 | no_regression |

## 关键观察

1. cooldown 对 Apollo greedy 20 的 overhead 有明显缓解：
   - worker time 从 `0.212501` 降到 `0.070875`；
   - wall time 从 `0.865410` 降到 `0.513372`。

2. cooldown 仍没有达到 wall-time ROI：
   - baseline wall time 为 `0.254094`；
   - cooldown profile 仍为 `0.513372`；
   - 仍被 classified 为 `worsened`。

3. cooldown 会减少列返回数量：
   - low-budget 返回并加入 2 个 new task-set；
   - cooldown 返回并加入 1 个 new task-set；
   - primal 从 `1022.575388` 退到 `1030.002361`，但仍优于 baseline 的 `1061.554044`。

4. official certificate 边界不变：
   - 没有 official lower-bound side effect；
   - 没有 certificate path；
   - worker no-column / skipped 不会被解释成 no-negative。

## 当前判断

cooldown 是有价值的开销控制 guard，但它没有把 Phase 7O worker profile 变成达标方案。

当前 20-task 结论仍是：

- 有 column-quality / primal-quality signal；
- 没有 wall-time ROI；
- 不能作为 20-task improvement success；
- 不应默认启用 worker；
- 不应进入 official certificate gate。

后续如果继续 worker 主线，应优先做更严格的 ROI / productivity gate，而不是单纯增加 worker 预算。

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_delayed_profiles_are_certificate_candidate_only
```

结果：

```text
Ran 2 tests in 0.001s
OK
```
