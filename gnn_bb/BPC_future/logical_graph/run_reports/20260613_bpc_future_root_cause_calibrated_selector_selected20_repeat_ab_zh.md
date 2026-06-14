# BPC_future Root Cause calibrated selector selected-20 repeat A/B 报告

日期：2026-06-13

## 目标

本轮把 delayed/pre-heuristic calibrated selector 放进更接近 production gate 的 selected 20-task repeat A/B。

和前一轮 repeat gate 相比，本轮只跑 20-task，并把 CG 深度从 `max_cg_iterations=3` 提高到 `8`：

```text
instances = mt20_greedy_apollo_01, tranq20_01, mt20_greedy_tranq_01
profiles = baseline, strict_worker_delayed_current_probe_calibrated_true_rc_20_only_pre_heuristic_coverage_scan
repeat_count = 2
time_limit = 20
pricing_time_limit = 0.3
pricing_max_dp_states = 1000
max_cg_iterations = 8
```

目标是检查：Apollo20 的局部 RMP movement 是否能转化成 selected 20 hard-repeat 的 wall-time / primal / status / tail 改善。

## 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_calibrated_selector_selected20_repeat_ab_20260613 \
--instances mt20_greedy_apollo_01 tranq20_01 mt20_greedy_tranq_01 \
--profiles root_cause_calibrated_selector_hardtail_ab \
--repeat-count 2 \
--time-limit 20 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 8 \
--current-probe-min-tasks 20 \
--current-probe-time-limit 0.8 \
--worker-time-limit 0.5 \
--audit-time-limit 0.2 \
--quiet
```

输出：

```text
BPC_future/results/root_cause_calibrated_selector_selected20_repeat_ab_20260613/summary.json
BPC_future/results/root_cause_calibrated_selector_selected20_repeat_ab_20260613/summary.csv
```

## 结果摘要

profile rows 共 6 行：

```text
all status = TIME_LIMIT
objective_mismatch_count = 0
worker_triggered_count = 2
worker_added_journeys = [2, 2, 0, 0, 0, 0]
```

按 worker 是否触发聚合：

| group | rows | avg wall delta | min wall delta | max wall delta | avg primal delta |
|---|---:|---:|---:|---:|---:|
| all | 6 | -0.010644 | -0.059809 | 0.037777 | 1.398338 |
| worker triggered | 2 | -0.050702 | -0.059809 | -0.041594 | 4.195013 |
| no worker | 4 | 0.009384 | -0.012232 | 0.037777 | 0.0 |

## Apollo20 结果

`mt20_greedy_apollo_01` 两次 repeat 都触发 worker：

```text
worker_added_journeys = 2
worker_added_new_task_set_count = 2
pulse_worker_next_rmp_objective_delta = -38.978656
pulse_worker_next_dual_l1_delta = 43.80801
followup_first_negative_task_set = 5,8,15
followup_first_negative_relation_to_worker = disjoint_task_set
```

但 selected 20 A/B 结果不是稳定改善：

```text
repeat 0:
  wall_delta = -0.041594
  primal_delta = -41.372067
  status = TIME_LIMIT -> TIME_LIMIT
  pricing_state = INCOMPLETE_LIMIT -> INCOMPLETE_LIMIT

repeat 1:
  wall_delta = -0.059809
  primal_delta = +49.762092
  status = TIME_LIMIT -> TIME_LIMIT
  pricing_state = INCOMPLETE_LIMIT -> INCOMPLETE_LIMIT
```

即：wall time 在短 run 中略低，但 primal 一次改善、一次恶化，status 和 pricing_state 没有改善，residual tail 仍存在。

## Tranq20 / MT Tranq20 结果

`tranq20_01` 两次 repeat：

```text
worker_events = 0
worker_triggered = False
status = TIME_LIMIT -> TIME_LIMIT
pricing_state = INCOMPLETE_LIMIT -> INCOMPLETE_LIMIT
primal_delta = 0.0
```

`mt20_greedy_tranq_01` 两次 repeat：

```text
worker_events = 0
worker_triggered = False
status = TIME_LIMIT -> TIME_LIMIT
pricing_state = FOUND_NEGATIVE -> FOUND_NEGATIVE
primal_delta = 0.0
```

## 结论

本轮 selected 20 repeat A/B 不支持把 calibrated selector 视为生产优化方向：

1. Apollo20 的局部 RMP movement 可重复；
2. 但 residual disjoint negative `[5,8,15]` 仍保留；
3. status / pricing_state 没有改善；
4. primal 结果在 worker-triggered repeats 中一好一坏；
5. 另外两个 20-task 样本不触发 worker。

因此当前状态仍是：

```text
has_replay_calibrated_selector_candidate = true
has_production_validated_selector = false
has_20_walltime_speedup_evidence = false
production_direction_proven = false
```

这条证据进一步说明：根因不是“是否能找到并加入 true-RC negative columns”，而是 returned batch / selector 与后续 RMP trajectory 的耦合还没有被稳定控制。
