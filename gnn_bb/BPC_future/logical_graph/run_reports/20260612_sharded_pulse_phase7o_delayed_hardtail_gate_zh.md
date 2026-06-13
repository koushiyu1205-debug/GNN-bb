# Sharded Pulse Phase 7O Delayed Hard-tail Gate 报告

日期：2026-06-12

## 目标

上一轮 expanded A/B 显示：

- current-context probe 可以加 true-RC negative columns；
- 但 `after_each_final_pricing + force_on_root` 带来固定 audit/skip overhead；
- 5-task small-fast 被明显拖慢；
- 10/20 active worker cases 仍缺 wall-time ROI。

本轮目标是新增更严格的 delayed hard-tail gate：

- 5-task 默认完全不注入 Pulse audit/worker 配置；
- 10/20 只在 certificate-candidate context 下运行 audit/worker；
- 不再每轮 exact pricing 都 audit；
- 不改变 solver 默认 benchmark；
- 不产生 certificate / official lower-bound side effect。

## 实现摘要

新增 calibration profiles：

- `strict_worker_delayed_hard_tail_only`
- `strict_worker_delayed_current_probe_impact`

实现边界：

- `strict_worker_delayed_*` 在 `task_count < current_probe_min_tasks` 时直接 no-op；
- 10/20 中 audit trigger 使用 `on_certificate_candidate`；
- `journey_sharded_pulse_audit_force_on_root=False`；
- audit / worker skip logging 关闭，避免 no-op log overhead；
- hard-tail-only profile 只消费 previous audit negative signal；
- delayed current-probe profile 在 certificate-candidate context 下允许 current probe，并启用 impact filter；
- 所有 worker returned journeys 仍由 driver 既有 true-RC sanitize 检查。

## Focused Tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_delayed_profiles_scale_gate_5_task \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_delayed_profiles_are_certificate_candidate_only
```

结果：

```text
Ran 4 tests in 0.001s
OK
```

## Expanded Delayed-gate Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_delayed_hardtail_gate_expanded_20260612 \
--instances apollo5 tranq5 apollo10 tranq10_09 tranq10_04 tranq10_01 tranq10_06 apollo10_04 apollo10_09 tranq20_01 mt20_greedy_apollo_01 mt20_greedy_tranq_01 \
--profiles baseline strict_worker_current_probe_support_aware_impact_filter strict_worker_delayed_hard_tail_only strict_worker_delayed_current_probe_impact \
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

- `BPC_future/results/sharded_pulse_phase7o_delayed_hardtail_gate_expanded_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_delayed_hardtail_gate_expanded_20260612/summary.csv`

### Expanded Smoke 结论

| profile | scale | avg time | worker added | class summary |
|---|---:|---:|---:|---|
| baseline | 5 | 0.0284 | 0 | baseline |
| old impact filter | 5 | 0.3454 | 0 | worsened |
| delayed hard-tail-only | 5 | 0.0254 | 0 | improved/no_regression |
| delayed current-probe impact | 5 | 0.0252 | 0 | improved/no_regression |
| baseline | 10 | 0.1042 | 0 | baseline |
| old impact filter | 10 | 0.6138 | 6 | worsened |
| delayed hard-tail-only | 10 | 0.1028 | 0 | no_regression |
| delayed current-probe impact | 10 | 0.3318 | 6 | mixed: 4 no_regression, 3 worsened |
| baseline | 20 | 0.1917 | 0 | baseline |
| old impact filter | 20 | 0.6799 | 3 | worsened |
| delayed hard-tail-only | 20 | 0.1938 | 0 | no_regression |
| delayed current-probe impact | 20 | 0.3313 | 3 | mixed: 2 no_regression, 1 worsened |

关键观察：

- delayed hard-tail-only 解决了固定 overhead，但本矩阵中不加列；
- delayed current-probe impact 完全消除了 5-task overhead；
- delayed current-probe impact 保留 10/20 加列能力；
- active current-probe cases 在 0.15s cap 下仍经常 worsened。

## Low-cap Current-probe Smoke

为了确认是否能用更小 worker budget 保留 10-task signal，本轮又跑了低 cap：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_delayed_current_probe_lowcap_smoke_20260612 \
--instances apollo5 tranq5 apollo10 tranq10_09 apollo10_04 mt20_greedy_apollo_01 \
--profiles baseline strict_worker_delayed_current_probe_impact \
--time-limit 4.0 \
--audit-time-limit 0.05 \
--worker-time-limit 0.05 \
--current-probe-time-limit 0.05 \
--pricing-time-limit 0.08 \
--max-cg-iterations 3 \
--audit-max-recursions 10000 \
--worker-max-recursions 10000 \
--current-probe-max-recursions 5000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_delayed_current_probe_lowcap_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_delayed_current_probe_lowcap_smoke_20260612/summary.csv`

### Low-cap 观察

| instance | scale | added | composition | objective delta | class |
|---|---:|---:|---|---:|---|
| Apollo5 | 5 | 0 | gated/no-op | - | improved |
| Tranquillitatis5 | 5 | 0 | gated/no-op | - | no_regression |
| Apollo10 | 10 | 1 | 1 support-changing replacement | -0.220167 | no_regression |
| tranq10_09 | 10 | 1 | 1 new task-set | -8.209058 | no_regression |
| apollo10_04 | 10 | 3 | 3 new task-set | -56.782044 | worsened |
| mt20_greedy_apollo_01 | 20 | 2 | 2 new task-set | -31.551683 | worsened |

## Exactness 边界

- delayed profiles 只是 calibration script opt-in；
- default benchmark 行为不变；
- 5-task no-op profile 不修改 solver config；
- current probe 仍不是 certificate oracle；
- worker empty / incomplete / duplicate-only 仍不会产生 official lower bound；
- `critical_disagreement_count=0` in both smoke runs。

## 当前判断

delayed gate 是明确正向：

- 解决了 5-task fixed overhead；
- non-triggered 10/20 cases 接近 baseline；
- low-cap current probe 在 Apollo10 / tranq10_09 保留 useful column signal，并被 classified as `no_regression`。

但仍未达成最终目标：

- 10-task hard set 未全量 no-regression；
- apollo10_04 仍 worsened；
- 20-task 仍未显示 improvement；
- 没有 evidence 证明 tail retry / final judge time 下降。

下一步建议：

1. 以 delayed current-probe impact + low cap 作为唯一候选 worker profile；
2. 跑完整 5/10 no-regression gate；
3. 对 apollo10_04 / 20-task active cases 加更严格 trigger 或 column-impact quota；
4. 如果 low-cap 扩展矩阵仍无 ROI，则停止 active-worker 扩张，转向 RMP stabilization / pool compression / legacy final judge optimization。
