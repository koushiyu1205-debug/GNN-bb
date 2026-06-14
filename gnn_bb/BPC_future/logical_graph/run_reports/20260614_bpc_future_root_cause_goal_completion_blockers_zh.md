# BPC_future 根因目标完成阻塞报告

日期：2026-06-14

## 目的

本报告只回答一个问题：

```text
为什么当前不能把“根因目标”标记为完成？
```

它不提出新的主线 solver 改动，也不把 calibration / replay / worker smoke
解释成生产优化成功。权威机器证据仍以：

```text
BPC_future/results/root_cause_evidence_ledger_20260613/summary.json
BPC_future/scripts/verify_root_cause_evidence.py
```

为准。

## 当前完成状态

```text
goal_complete = false
completion_decision = keep_goal_active
why_many_attempts_failed = current
why_many_attempts_failed_status = supported_but_optimization_direction_unproven
missing_requirements = five_ten_full_no_regression_ab,production_validated_selector,twenty_walltime_speedup
```

含义是：

- 根因解释已有证据；
- 但生产优化方向仍未证明；
- 不能声明已经满足“5/10 不退化且 20 大幅加速”的最终目标。

## 用户目标逐项审计

```text
objective_completion_audit = current
root_cause_explanation_has_evidence = proved
not_limited_to_pulse = proved
no_unvalidated_mainline_change_before_proof = proved
unproven_experiments_not_counted_as_completion = proved
five_ten_no_regression_is_noop_guard_not_worker_success = proved
stable_production_optimization_direction = not_proved
exact_5_10_no_regression_and_20_speedup = not_proved
```

| 用户要求 | 当前状态 | 依据 |
|---|---:|---|
| 查出根因，不能猜测 | 已有证据 | `why_many_attempts_failed` 三主因、失败矩阵、selector 反例目录、production selector blocker catalog 均纳入 verifier |
| 不局限于 Pulse | 已证明 | evidence 覆盖 small-scale overhead、JourneyColumn batch、RMP trajectory、selector holdout、profile-DP / ordinary pricing / replay |
| 明确前不要做主线大修改 | 已证明边界 | code boundary 显示 capture diagnostic-only、profile priority default empty、mainline unvalidated effect default disabled |
| 失败实验不能算根因完成 | 已证明 | worker 能加负列、exact replay 有 local RMP impact，但仍缺 production selector 和 20 wall-time speedup |
| 5/10 不退化 | 未证明生产候选 | 当前只有 no-op / gate 不触发安全证据；triggered 10-task 有回退风险 |
| 20 大幅加速最优解 | 未证明 | hard-tail worker / add-column smoke 未显示稳定 wall-time / status 改善 |
| 找到可上线优化方向 | 未证明 | `production_validated_selector=false`，production A/B entry gate 仍 blocked |

## 为什么做了很多仍不行

当前机器 ledger 把主因收敛为三条：

```text
why_many_attempts_failed_primary_causes = small_scale_fixed_overhead_sensitivity,twenty_returned_batch_rmp_trajectory_coupling,addition_before_selector_not_production_validated
```

### 1. 5/10：固定开销敏感

5/10 baseline 太短，worker / audit / probe 只要真实触发，就可能把收益吃掉。

当前关键证据：

```text
triggered_worse_count = 220
triggered_better_count = 0
task10_triggered_official_changed = 61
```

所以现在能证明的是：

```text
no-op / gate 不触发时安全
```

还不能证明：

```text
production worker / selector 在 5/10 全量默认启用时无回退
```

这就是 `five_ten_full_no_regression_ab` 仍缺失的原因。

### 2. 20：负列存在，但 batch impact 不稳定

Pulse / worker 已经能返回 true-RC negative columns，这条路线不是接线失败。
问题是这些列是否改变后续 RMP active basis / dual trajectory / final judge tail。

当前关键证据：

```text
phase8q_added_journeys = 10
phase8q_all_time_limit = true
replay_high_impact_candidate_count = 4
replay_noop_candidate_count = 1
```

所以当前不能把“找到更多负列”当成根本解决方案。

正确问题已经变成：

```text
在加列之前，如何判断这个 returned batch 会推动后续 RMP / dual / pricing trajectory？
```

这就是 returned-batch / RMP trajectory selector 问题。

### 3. selector：已有 calibration 候选，但未 production-validated

当前 replay 数据中已有 addition-before selector 候选，但没有通过生产要求的
context / instance / dataset holdout。

当前关键证据：

```text
recommended_selector_candidate = true_reduced_cost_<=_-12.430587
exact_false_positive_count = 22
exact_false_negative_count = 31
robust_all_fold_selector_available = false
production_validated_selector = false
```

所以它只能是 calibration signal，不能直接进入 production BPC A/B，更不能打开
official certificate gate。

## 已排除的充分解释

当前不是说这些路线完全没有信号，而是它们不足以成为 production-safe 根因解法：

```text
pulse_wiring_or_certificate_semantics_is_the_main_cause = ruled_out_as_primary_root_cause
finding_more_true_rc_negative_columns_is_sufficient = ruled_out
expanding_worker_budget_or_default_worker_is_safe_for_5_10 = ruled_out
true_rc_threshold_or_simple_selector_is_production_ready = ruled_out
hindsight_or_post_addition_signals_can_be_used_online = forbidden_shortcut
```

这也是为什么不能继续简单加 worker 时间、加返回列数量、调 true-RC 阈值，或用
post-addition / hindsight 轨迹特征。

## 三个阻塞门槛

### `five_ten_full_no_regression_ab`

缺口：

```text
当前只有 no-op / gate 证据，没有生产候选默认启用后的 5/10 全量 A/B 证据。
```

必须补的证据：

```text
生产候选 full BPC A/B 覆盖 5-task 和 10-task；
official result 不变；
wall time / TIME_LIMIT / objective / dual_bound 不回退。
```

### `production_validated_selector`

缺口：

```text
没有 selector 同时通过 context / instance / dataset holdout。
```

必须补的证据：

```text
selector 只使用 addition-before features；
在 no-certificate-effect exact-context replay 数据上通过 context / instance / dataset holdout；
之后才允许进入 full BPC A/B。
```

### `twenty_walltime_speedup`

缺口：

```text
现有 hard-tail worker / add-column smoke 没有稳定产生 20-task wall-time / status 改善。
```

必须补的证据：

```text
selected 20-task hard repeat A/B 显示 wall time、gap、status 或 final-judge tail 明确改善；
同时 official exactness 不变。
```

## 下一步协议

当前下一步不是主线大改，而是继续 calibration-only：

```text
next_evidence_protocol_status = calibration_only_until_selector_passes
next_evidence_protocol_gates = exact_context_capture_and_replay_dataset,addition_before_selector,production_candidate_ab
```

顺序必须保持：

1. 扩展 no-certificate-effect exact-context capture / replay；
2. 证明 addition-before selector 通过 context / instance / dataset holdout；
3. 再做 full BPC A/B，先过 5/10 no-regression，再看 selected 20 hard repeats。

## 结论

当前可以回答“为什么做了很多仍不行”：

```text
5/10 卡在固定开销；
20 卡在 returned-batch 与 RMP trajectory 的上下文耦合；
当前缺少 production-validated addition-before selector。
```

但当前不能回答：

```text
哪个生产优化方向已经百分百确定，并且已证明能在 exactness 和 5/10 不退化前提下大幅加速 20。
```

因此目标必须保持 active。
