# BPC_future Root Cause calibrated selector hard-tail worker smoke 报告

日期：2026-06-13

## 目标

本轮不是证明生产优化，而是检查 replay-calibrated selector candidate 是否能接入历史上确实触发 worker 的 hard-tail 路径。

新增 profile：

```text
strict_worker_delayed_current_probe_calibrated_true_rc_20_only_pre_heuristic_coverage_scan
```

该 profile 只在 20-task 启用，使用 delayed current-context probe + pre-heuristic coverage-scan 路径，并设置：

```text
impact_filter_mode = prefer_new_or_active_support
impact_filter_max_columns = 0
impact_filter_min_true_rc = -12.430587
```

它不启用 target-sequence priority / target-transition priority / target-arc-option priority，因此不是后验目标序列诊断。

## 配置 guard

直接审计 `_apply_profile()` 得到：

| task_count | worker_enabled | current_probe_enabled | min_true_rc |
|---:|---:|---:|---:|
| 5 | false | false | none |
| 10 | false | false | none |
| 20 | true | true | -12.430587 |

因此该 profile 仍是严格 opt-in，且不会在 5/10 上触发 worker。

## Smoke 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_calibrated_selector_hardtail_worker_smoke_20260613 \
--instances root_cause_calibrated_selector_hardtail \
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
BPC_future/results/root_cause_calibrated_selector_hardtail_worker_smoke_20260613/summary.json
BPC_future/results/root_cause_calibrated_selector_hardtail_worker_smoke_20260613/summary.csv
```

## 结果摘要

实例：`mt20_greedy_apollo_01`

| profile | status | pricing_state | worker_events | worker_added | next RMP delta | follow-up first negative |
|---|---|---|---:|---:|---:|---|
| baseline | TIME_LIMIT | FOUND_NEGATIVE | 0 | 0 | none | none |
| calibrated delayed hard-tail | TIME_LIMIT | FOUND_NEGATIVE | 1 | 2 | -38.978656 | `[5,8,15]` |

calibrated profile 观测到：

```text
worker_signal_source = current_context_probe
worker_returned_journeys = 2
worker_added_journeys = 2
worker_added_new_task_set_count = 2
pulse_worker_impact_filter_min_true_rc = -12.430587
pulse_worker_impact_filter_candidate_count = 3
pulse_worker_impact_filter_selected_count = 2
pulse_worker_impact_filter_dropped_count = 1
pulse_worker_impact_filter_rc_threshold_dropped_count = 1
pulse_worker_impact_filter_selected_best_true_rc = -39.760531
pulse_worker_next_rmp_objective_delta = -38.978656
pulse_worker_next_dual_l1_delta = 43.80801
```

这说明 replay-calibrated threshold 不是死配置：它在 hard-tail 路径中实际触发、筛掉了 1 个 candidate，并加入了 2 个 new task-set。

## 负面信号

worker 加列后，后续 ordinary/profile-DP pricing 仍返回 disjoint residual negative：

```text
pulse_worker_followup_first_negative_task_set = 5,8,15
pulse_worker_followup_first_negative_sequence = 8,15,5
pulse_worker_followup_first_negative_relation_to_worker = disjoint_task_set
pulse_worker_vs_ordinary_contrast_class = disjoint_residual_after_worker
```

并且后续仍有：

```text
pulse_worker_followup_tail_outcome = followup_found_negative
pulse_worker_followup_negative_task_set_sequence = 5,8,15|5,12,18
```

因此这次 smoke 不能证明 worker 已解决 hard tail。它只证明 calibrated delayed profile 能产生真实加列和局部 RMP movement。

## 结论

本轮新增证据修正了 calibrated selector profile 的接入状态：

```text
simple current-probe calibrated profile: worker 未触发，只是 wiring guard。
delayed/pre-heuristic calibrated profile: worker 可触发并加列，但仍有 residual disjoint negative tail。
```

所以当前判断保持不变：

```text
has_replay_calibrated_selector_candidate = true
has_production_validated_selector = false
has_20_walltime_speedup_evidence = false
production_direction_proven = false
```

下一步若继续验证 selector，必须跑更完整的 5/10 no-regression + selected 20 hard repeats A/B。单实例 hard-tail smoke 不能作为生产优化证明。
