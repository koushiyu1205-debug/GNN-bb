# Sharded Pulse Phase 3A Leaf Materialization Contract 报告

日期：2026-06-11

## 目标

本轮只实现 Pulse 叶子物化契约，不实现真实 Pulse DFS。

Phase 3A 的目标是确认：

1. Pulse completed sortie trace 必须回放现有 `evaluate_timed_trip()`；
2. completed journey 必须调用现有 `make_journey()`；
3. negative candidate 必须调用 `manual_journey_reduced_cost()` 做 true-RC 复算；
4. infeasible sortie / infeasible journey 必须返回 `None`；
5. `signature`、`arc_option_ids`、`start_time`、`service_start`、`occupancy`、`physical_paths` 与现有系统列完全一致。

## 实现摘要

新增模块：

- `BPC_future/pricing/pulse_materialization.py`

新增类型：

- `PulseSortieTrace`
- `PulseLeafCandidate`

新增 helper：

- `materialize_pulse_sortie()`
- `materialize_pulse_journey()`
- `materialize_pulse_leaf_candidate()`
- `materialize_negative_pulse_leaf()`

这些 helper 只做叶子回放和过滤：

- `materialize_pulse_sortie()` 内部直接调用 `evaluate_timed_trip()`；
- `materialize_pulse_journey()` 内部直接调用 `make_journey()`；
- `materialize_pulse_leaf_candidate()` 先物化所有 sorties，再构造 journey，最后调用 `manual_journey_reduced_cost()`；
- `materialize_negative_pulse_leaf()` 只返回 `true_reduced_cost < -eps` 的候选。

## Exactness 边界

本轮没有新增任何搜索、剪枝、dominance、resume、parallel 或 branch 逻辑。

Pulse 后续 DFS 只能把 completed trace 交给本 helper 物化，不应手工拼：

- `TimedTrip.cost`
- `TimedTrip.signature`
- `TimedTrip.occupancy`
- `TimedTrip.end_time`
- `JourneyColumn.cost`
- `JourneyColumn.signature`

## 测试覆盖

新增 focused tests：

- `test_pulse_materialization_replays_evaluate_timed_trip_fields`
- `test_pulse_materialization_builds_journey_and_true_rc_filter`
- `test_pulse_materialization_rejects_infeasible_leaves`
- `test_pulse_materialization_rejects_arc_option_count_mismatch`
- `test_pulse_materialization_rejects_overlapping_sorties`
- `test_pulse_materialization_true_rc_includes_cut_duals`
- `test_pulse_materialization_no_wait_ready_time_boundary`
- `test_pulse_materialization_rejects_duplicate_task_across_sorties`

覆盖内容：

- Pulse sortie replay 与 `evaluate_timed_trip()` 完全相等；
- `signature` / `arc_option_ids` / `start_time` / `service_start` / `occupancy` / `physical_paths` 保持一致；
- Pulse journey 与 `make_journey()` 完全相等；
- true RC 与 `manual_journey_reduced_cost()` 一致；
- negative filter 只接受 true negative；
- energy infeasible sortie 返回 `None`；
- time-window infeasible sortie 返回 `None`；
- arc option 数量少于 / 多于 `len(sequence)+1` 时抛出明确 `ValueError`；
- 多 sortie 时间重叠时 journey 返回 `None`；
- true RC 复算包含 cut dual contribution；
- no-wait 场景下 `arrival == ready_time` 可行，`arrival < ready_time` 不可行；
- 同一 task 出现在不同 sorties 中时 journey 返回 `None`。

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_materialization.py \
BPC_future/pricing/sharded_pulse_final_judge.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

Phase 3A focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_replays_evaluate_timed_trip_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_builds_journey_and_true_rc_filter \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_infeasible_leaves \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_arc_option_count_mismatch \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_overlapping_sorties \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_true_rc_includes_cut_duals \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_no_wait_ready_time_boundary \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_duplicate_task_across_sorties
```

结果：

```text
Ran 8 tests in 0.024s
OK
```

Phase 3A + Phase 2.5 guard 回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_replays_evaluate_timed_trip_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_builds_journey_and_true_rc_filter \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_infeasible_leaves \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_arc_option_count_mismatch \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_overlapping_sorties \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_true_rc_includes_cut_duals \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_no_wait_ready_time_boundary \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_pulse_materialization_rejects_duplicate_task_across_sorties \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_direct_journey_label_completion_bound_uses_ng_certificate_preprobe \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_can_close_profile_pricing \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_flag_alone_starts_profile_probe \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_can_close_ryan_foster_branch_pricing \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_preprobe_certificate_rejects_non_ryan_foster_branch_pricing \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_only_final_judge_no_column_results_are_global_certificates \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_state_uses_explicit_certificate_semantics \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_certificate_state_and_driver_guard_are_consistent \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_ng_relaxed_certificate_reason_requires_safe_relaxation_flags \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_ledger_aggregates_root_shards \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_ledger_refined_parent_uses_children \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_frontier_snapshot_is_not_proof_closed \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_cache_key_tracks_context \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_engine_all_certified \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_engine_duplicate_only_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_engine_incomplete_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_engine_is_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_engine_requires_test_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_engine_requires_environment_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_engine_rejects_non_test_instance \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_enabled_without_real_engine_is_incomplete \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_default_off \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_all_certified_sets_official_bound \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_rejects_missing_test_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_rejects_missing_env_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_without_dummy_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_incomplete_has_no_official_bound \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_certificate_config_sets_dummy_engine \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_duplicate_only_final_judge_never_promotes_to_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_duplicate_only_final_judge_noops_without_rmp_audit \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_completion_bound_final_probe_verifies_profile_no_column_certificates \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_retry_budget_completion_reserve_is_opt_in_and_bounded \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_final_judge_config_with_call_deadline_sets_absolute_deadline \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_expired_absolute_deadline_returns_incomplete_not_certificate
```

结果：

```text
Ran 43 tests in 0.595s
OK
```

## 当前边界

- 未实现 Pulse DFS；
- 未实现 dominance archive；
- 未实现 resume / parallel；
- 未实现 branch compiler；
- 未接入 driver final judge；
- 只建立叶子物化契约。

## 结论

Phase 3A 已完成：未来 Pulse DFS 找到 completed leaf 后，可以通过统一 helper 复用现有 `TimedTrip` / `JourneyColumn` / true-RC 语义，避免手工构造列导致 RMP cost、signature、occupancy 或 reduced cost 不一致。
