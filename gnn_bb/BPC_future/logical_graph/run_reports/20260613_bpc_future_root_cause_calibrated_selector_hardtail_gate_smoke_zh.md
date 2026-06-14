# BPC_future Root Cause calibrated selector hard-tail gate smoke 报告

日期：2026-06-13

## 目标

本轮把 delayed/pre-heuristic calibrated selector profile 放到一个小型 5/10/20 gate 矩阵中，验证两件事：

1. 5/10 gate 下 worker 不触发，official path 不被改动；
2. 20 hard-tail 下 selector 是否仍只表现为局部信号，而不是生产优化证明。

profile：

```text
strict_worker_delayed_current_probe_calibrated_true_rc_20_only_pre_heuristic_coverage_scan
```

关键配置：

```text
impact_filter_mode = prefer_new_or_active_support
impact_filter_min_true_rc = -12.430587
```

该 profile 仍是 opt-in，并且 `_apply_profile()` 在 `task_count < 20` 时直接返回。

## Smoke 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_calibrated_selector_hardtail_gate_smoke_20260613 \
--instances root_cause_calibrated_selector_gate \
--profiles root_cause_calibrated_selector_hardtail_ab \
--time-limit 8 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 3 \
--current-probe-min-tasks 20 \
--current-probe-time-limit 0.8 \
--worker-time-limit 0.5 \
--audit-time-limit 0.2 \
--quiet
```

输出：

```text
BPC_future/results/root_cause_calibrated_selector_hardtail_gate_smoke_20260613/summary.json
BPC_future/results/root_cause_calibrated_selector_hardtail_gate_smoke_20260613/summary.csv
```

## 结果摘要

| scale | instances | worker_events | worker_triggered | official_changed | objective_mismatch |
|---:|---:|---:|---:|---:|---:|
| 5 | 2 | 0 | 0 | 0 | 0 |
| 10 | 2 | 0 | 0 | 0 | 0 |
| 20 | 2 | 1 | 1 | 1 | 0 |

5/10 的 profile rows：

```text
apollo5: worker_events=0, worker_triggered=False
tranq5: worker_events=0, worker_triggered=False
apollo10: worker_events=0, worker_triggered=False
tranq10_09: worker_events=0, worker_triggered=False
```

这说明 gate wiring 是有效的。但本轮使用的是短 smoke 和 `max_cg_iterations=3`，不能把它当成完整 5/10 no-regression 证明。

20 rows：

```text
mt20_greedy_apollo_01:
  worker_events = 1
  worker_added_journeys = 2
  worker_added_new_task_set_count = 2
  pulse_worker_next_rmp_objective_delta = -38.978656
  pulse_worker_next_dual_l1_delta = 43.80801
  pulse_worker_followup_first_negative_task_set = 5,8,15
  pulse_worker_followup_first_negative_relation_to_worker = disjoint_task_set

tranq20_01:
  worker_events = 0
  worker_triggered = False
```

## 解释

这条矩阵证据加强了当前根因判断：

- calibrated selector 可以在某个 20 hard-tail context 中触发并产生局部 RMP movement；
- 但它没有在另一个 20 hard-tail context 中触发；
- 在触发的 Apollo20 中，worker 后仍存在 disjoint residual negative `[5,8,15]`；
- 5/10 当前只是“gate 不触发”的短 smoke，不是全量 no-regression 证明。

因此当前仍只能说：

```text
has_replay_calibrated_selector_candidate = true
has_production_validated_selector = false
has_20_walltime_speedup_evidence = false
production_direction_proven = false
```

## 结论

delayed/pre-heuristic calibrated selector 比 simple current-probe profile 更接近实际 hard-tail worker 路径，但它仍没有证明生产优化方向。下一步若继续，应做完整的 5/10 no-regression + selected 20 hard-repeat wall-time/gap/status/tail A/B，而不是打开默认 worker 或 certificate gate。
