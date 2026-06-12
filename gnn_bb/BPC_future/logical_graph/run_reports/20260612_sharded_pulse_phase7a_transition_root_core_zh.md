# Sharded Pulse Phase 7A Transition-level Root-only Core 报告

日期：2026-06-12

## 目标

本轮只实现 Phase 7A：`Transition-level root-only Pulse core`。

目标不是跑 10/20 性能 benchmark，而是验证下一代 Pulse core 不再依赖“先枚举完整 trace、再 materialize、再发现不可行”的方向。

Phase 7A 的验收点：

1. transition-level pruning counters > 0；
2. transition-level Pulse 与旧 completed-trace toy exhaustive / brute-force 在 `very_small` focused tests 上结果一致；
3. 在 no-wait infeasible toy case 中，生成完整 trace 的数量相对旧 toy engine 明显下降。

## 实现摘要

### 1. 新增 transition core

在 `BPC_future/pricing/pulse_toy_exhaustive.py` 新增：

- `_TransitionPulseState`
- `transition_root_only_pulse()`

该 core 仍是 test-only，不接默认 production driver。

### 2. State 与 counters

当前 transition state 显式维护：

- `phase`
- `last_node`
- `visited_task_mask`
- `current_sortie_task_mask`
- `sorties_used`
- `current_time`
- `travel_energy`
- `service_energy`
- `load_used`
- `partial_exact_prefix_rc`
- `partial_lb_prefix_rc`
- `pending_same_mask`
- `partial trace`

`partial_exact_prefix_rc / partial_lb_prefix_rc` 目前只维护，不用于 bound pruning。因为 cut / fleet / branch row 的安全 prefix lower bound 还没有完整实现，剪枝必须继续 fail-open。

transition-level pruning counters：

- `transition_time_window_pruned`
- `transition_energy_pruned`
- `transition_return_pruned`
- `pulse_capacity_pruned`
- 兼容旧日志的 `pulse_resource_pruned`

### 3. Transition 前检查

每次扩展 task 前检查：

- no-wait ready time；
- due time；
- capacity；
- partial energy；
- optimistic safe return lower bound；
- Ryan-Foster `separate_vehicle`；
- Ryan-Foster `same_vehicle` pending obligations。

return action 仍通过 Phase 3A materialization helper：

- completed sortie -> `materialize_pulse_sortie()` -> `evaluate_timed_trip()`；
- completed journey -> `materialize_pulse_leaf_candidate()` -> `make_journey()` + `manual_journey_reduced_cost()`。

这样 transition core 不手搓 `TimedTrip` / `JourneyColumn`。

### 4. Branch obligations

`same_vehicle(i,j)`：

- partial 包含一侧后，另一侧进入 `pending_same_mask`；
- journey 结束前必须清空 obligations；
- 若 pending partner 已不在 remaining tasks 中，transition branch prune。

`separate_vehicle(i,j)`：

- transition 一旦会让 visited mask 同时包含两侧，立即 prune。

## 新增测试

新增/更新 7 个 Phase 7A focused tests：

- `test_transition_pulse_matches_toy_exhaustive_on_very_small`
- `test_transition_pulse_best_rc_and_negative_flag_match_bruteforce`
- `test_transition_pulse_no_negative_exhaustive_iff_bruteforce_no_negative`
- `test_transition_pulse_prunes_before_completed_trace_materialization`
- `test_transition_pulse_resource_and_return_pruning_counters`
- `test_transition_pulse_first_task_shards_partition_toy`
- `test_transition_pulse_branch_obligations_match_filtered_bruteforce`

并复用既有 malformed trace guard：

- `test_pulse_materialization_rejects_arc_option_count_mismatch`

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_matches_toy_exhaustive_on_very_small \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_best_rc_and_negative_flag_match_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_no_negative_exhaustive_iff_bruteforce_no_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_prunes_before_completed_trace_materialization \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_resource_and_return_pruning_counters \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_first_task_shards_partition_toy \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_transition_pulse_branch_obligations_match_filtered_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_arc_option_count_mismatch
```

结果：

```text
Ran 8 tests in 0.051s
OK
```

同时回归 Phase 3B/3C/4/5 相关 focused tests：

```text
Ran 38 tests in 0.103s
OK
```

## 当前边界

- 未接 production driver；
- 未替换 guarded sharded engine 中的旧 completed-trace toy path；
- 未做 resume；
- 未做 parallel；
- 未做 adaptive hierarchical sharding；
- 未做 prefix RC bound pruning；
- 未把 dominance archive / harvesting 接入 transition state；
- 未跑 5/10/20 性能抽样。

## 结论

Phase 7A 已完成最小可验证版本：transition-level root-only Pulse core 能在扩展 task 前做 time/resource/return/branch 检查，并且仍通过 Phase 3A helper 物化 leaf。

当前最重要的结果是：

1. 在 no-wait infeasible toy case 中，transition core 在生成完整 sortie trace 前剪掉不可行扩展，`generated_sortie_traces` 从旧 toy 的正数降为 0；
2. `best_true_rc`、`found_negative iff brute-force found negative`、`no-negative exhaustive iff brute-force no-negative` 都有直接 brute-force 测试；
3. time-window / energy / return pruning 都有 `>0` focused toy case；
4. malformed trace 仍由 Phase 3A materialization helper fail-fast 抛 `ValueError`，不会被解释成 no-negative。

下一步建议只做 Phase 7B：把 `transition_root_only_pulse()` 接到 guarded sharded final judge 的 opt-in test path，替换旧 completed-trace toy engine，但仍不默认启用 production benchmark。
