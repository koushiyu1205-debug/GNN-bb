# BPC_future Root Cause calibrated selector hard-tail repeat gate 报告

日期：2026-06-13

## 目标

上一轮 gate smoke 只跑了每个 instance/profile 一次。本轮增加 `--repeat-count 3`，检查 delayed/pre-heuristic calibrated selector 的局部信号是否稳定，还是一次性轨迹噪声。

这仍然不是 full benchmark：

- `max_cg_iterations=3`
- `time_limit=8`
- 只覆盖 2 个 5-task、2 个 10-task、2 个 20-task 样本

因此本轮只作为证据补强，不作为生产优化证明。

## 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/root_cause_calibrated_selector_hardtail_repeat_gate_20260613 \
--instances root_cause_calibrated_selector_gate \
--profiles root_cause_calibrated_selector_hardtail_ab \
--repeat-count 3 \
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
BPC_future/results/root_cause_calibrated_selector_hardtail_repeat_gate_20260613/summary.json
BPC_future/results/root_cause_calibrated_selector_hardtail_repeat_gate_20260613/summary.csv
```

## 聚合结果

| scale | profile rows | worker_events | worker_triggered | official_changed | objective_mismatch |
|---:|---:|---:|---:|---:|---:|
| 5 | 6 | 0 | 0 | 0 | 0 |
| 10 | 6 | 0 | 0 | 0 | 0 |
| 20 | 6 | 3 | 3 | 3 | 0 |

5/10 gate 在 3 次重复中保持不触发：

```text
apollo5: worker_events = 0 for all repeats
tranq5: worker_events = 0 for all repeats
apollo10: worker_events = 0 for all repeats
tranq10_09: worker_events = 0 for all repeats
```

## Apollo20 重复结果

`mt20_greedy_apollo_01` 三次 repeat 完全重复同一局部信号：

```text
worker_events = 1 each repeat
worker_added_journeys = 2 each repeat
worker_added_new_task_set_count = 2 each repeat
pulse_worker_next_rmp_objective_delta = -38.978656 each repeat
pulse_worker_next_dual_l1_delta = 43.80801 each repeat
pulse_worker_followup_first_negative_task_set = 5,8,15 each repeat
pulse_worker_followup_first_negative_relation_to_worker = disjoint_task_set each repeat
pulse_worker_vs_ordinary_contrast_class = disjoint_residual_after_worker each repeat
```

在这个短预算设置下，profile 的 primal 从 baseline 的 `921.640296` 变为 `882.66164`，说明 selector 确实能稳定改变 Apollo20 的早期 RMP 轨迹。

但每次 follow-up 仍返回 disjoint residual negative `[5,8,15]`，说明 worker 没覆盖 ordinary/profile-DP 后续 tail。

## Tranq20 重复结果

`tranq20_01` 三次 repeat 中 calibrated worker 都未触发：

```text
worker_events = 0
worker_triggered = False
```

因此当前 signal 不是跨 20-task 样本稳定触发的生产策略。

## 结论

本轮把判断推进了一步：

```text
calibrated selector 的 Apollo20 局部收益不是单次噪声；
5/10 gate wiring 在短 repeat 中稳定不触发；
但 20-task 上仍只是一部分 context 有信号，且 residual disjoint tail 稳定存在。
```

所以当前状态仍然是：

```text
has_replay_calibrated_selector_candidate = true
has_production_validated_selector = false
has_20_walltime_speedup_evidence = false
production_direction_proven = false
```

下一步如果继续，应把这个 profile 或更严格 selector 放进更完整的 5/10 no-regression + selected 20 hard-repeat A/B。现在还不能打开默认 worker，也不能声称根因优化方向已经被生产验证。
