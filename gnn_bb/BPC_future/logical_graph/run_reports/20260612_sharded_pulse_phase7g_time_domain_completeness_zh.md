# Sharded Pulse Phase 7G Time-domain Completeness 报告

日期：2026-06-12

## 目标

本轮只做 Phase 7G：`Time-domain completeness / no-wait start-interval Pulse`。

目标是让 transition Pulse 在 no-wait 时间域上与现有 `candidate_start_times_for_trip()` / `evaluate_timed_trip()` 语义对齐，避免继续证明一个固定 `root_start_time` 子空间。

本轮不做：

- resume；
- parallel；
- adaptive sharding；
- cut / subset-row / fleet prefix bound；
- production default enable；
- 20/100 A/B。

## 实现摘要

### 1. no-wait start interval state

`_TransitionPulseState` 新增：

- `start_interval_lb`
- `start_interval_ub`
- `current_offset`

no-wait 下，每次扩展 task 时用 arrival offset 更新 start interval：

```text
start_lb = max(start_lb, r_i - arrival_offset_i)
start_ub = min(start_ub, D_i - sigma_i - arrival_offset_i)
```

如果 interval 为空，直接 `transition_time_window_pruned`，不生成 completed trace。

waiting-allowed 暂不做 interval proof，保持 fail-safe：guarded toy Pulse 不允许 waiting-allowed no-negative certificate。

### 2. return / horizon / survival energy

no-wait 下 return action 使用 offset 语义：

- `return_offset = current_offset + return_tau`
- `survival_energy = survival_energy_rate * return_offset`
- `end_offset = return_offset + total_energy / rho`
- horizon 约束转成 `start <= horizon - end_offset`

若 return / recharge 约束使 interval 为空，返回剪枝。

### 3. completed sortie materialization

completed sortie 不再只取 `root_start_time`。

no-wait 下：

1. 调用 `candidate_start_times_for_trip(data, sequence, arc_options, start_step)`；
2. 用当前 interval 过滤 fixed starts；
3. 每个 fixed start 都构造 `PulseSortieTrace`；
4. 每个 trace 继续通过 Phase 3A helper：
   - `materialize_pulse_sortie()`
   - `evaluate_timed_trip()`
   - `materialize_pulse_leaf_candidate()`
   - `manual_journey_reduced_cost()`

这保证 leaf 物化仍然复用现有列语义。

### 4. archive no-wait time semantics

no-wait open-sortie archive record 现在使用 `start_interval`。

支配仍要求 interval containment：

```text
old.left <= new.left
old.right >= new.right
```

不使用“更早时间自动支配”。

depot-ready phase 仍使用 actual next-start time，因为它来自已物化上一 sortie 的 `trip.end_time`。

### 5. certificate guard 收紧

guarded toy Pulse certificate 现在要求 no-wait scheduling。

如果 `task_waiting_allowed=True`，即使 `sharded_final_judge_toy_certificate_enabled=True`，no-negative 结果也只返回 `INCOMPLETE_LIMIT / sharded_pulse_toy_certificate_guard_failed`。

这是因为 waiting-allowed 的完整 start-domain proof logic 尚未实现。

## 新增/更新测试

新增：

- `test_transition_pulse_no_wait_interval_recovers_nonzero_start_candidate`
- `test_pulse_no_wait_start_candidates_match_candidate_start_times`
- `test_transition_pulse_interval_matches_candidate_start_bruteforce`
- `test_sharded_pulse_guarded_waiting_allowed_not_certificate`

更新：

- fixed-start no-wait pruning tests 改成真正 interval 为空的 `D < r` 场景；
- guarded no-negative certificate tests 显式使用 no-wait data；
- no-wait archive tests 继续验证 earlier-time-alone 不支配。

## Focused 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_prunes_before_completed_trace_materialization \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_no_wait_interval_recovers_nonzero_start_candidate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_no_wait_start_candidates_match_candidate_start_times \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_interval_matches_candidate_start_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_transition_pruning_counters_surface \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_certifies_very_small_no_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_harvest_diagnostics_surface \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_engine_incomplete_no_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_archive_counter_surfaces \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_bound_counter_surfaces \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_waiting_allowed_not_certificate
```

结果：

```text
Ran 12 tests in 0.061s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

完整 `BPCFutureTests` 回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 412 tests in 48.931s
OK (skipped=1)
```

## 当前边界

- no-wait start-domain 已按 `candidate_start_times_for_trip()` 对齐；
- waiting-allowed 仍未完整 proof 化，不得 certificate；
- 没有放开 production benchmark 默认配置；
- 没有接 resume / parallel / adaptive refinement；
- 没有加入 cut / subset-row / fleet prefix bound。

## 结论

Phase 7G 完成了 no-wait 时间域完整性主缺口：transition Pulse 不再只证明 fixed `root_start_time` 子空间，而是在 completed sortie 处枚举现有 candidate start-time 域，并继续通过 Phase 3A helper 物化 leaf。

下一步建议做 Phase 7H：small-instance opt-in certificate smoke。7H 应继续区分 observation path 与 experimental certificate path，并保持 waiting-allowed / unsupported cuts-branch fail-open。
