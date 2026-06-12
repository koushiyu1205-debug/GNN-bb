# Sharded Pulse Phase 3B Root-only Toy Exhaustive DFS 报告

日期：2026-06-11

## 目标

本轮只实现测试专用的 root-only toy exhaustive Pulse DFS，不接 production driver。

Phase 3B 的目标是确认：

1. toy Pulse 枚举空间与独立 brute-force enumerator 完全一致；
2. 每个 Pulse leaf 必须调用 Phase 3A materialization helper；
3. true reduced cost 必须通过 `manual_journey_reduced_cost()`；
4. first-task shard 是严格 partition；
5. deadline / max_recursions 命中时 fail-open 返回 incomplete；
6. 不引入 pruning、dominance、resume、parallel、branch compiler 或 production final judge 接入。

## Toy Universe 定义

本轮不是连续时间 production search，而是一个有限、可测试的 root-only search universe：

- 第一条 sortie 从 `root_start_time=0` 开始；
- 后续 sortie 立刻从上一条 sortie 的 `end_time` 开始；
- 枚举 elementary task sequence；
- 枚举 sortie partition；
- 枚举所有 path option combinations；
- 每个 completed leaf 用 Phase 3A helper 物化；
- infeasible sortie / journey 只由 `evaluate_timed_trip()` / `make_journey()` 判定。

这个 toy universe 用来验证搜索空间和 true-RC 语义，不作为 official certificate。

## 实现摘要

新增模块：

- `BPC_future/pricing/pulse_toy_exhaustive.py`

新增类型：

- `ToyPulseExhaustiveResult`

新增入口：

- `toy_root_exhaustive_pulse()`

该入口只做：

- root-only DFS；
- first-task shard filter；
- elementary remaining-task expansion；
- path option product enumeration；
- 调用 `materialize_pulse_sortie()`；
- 调用 `materialize_pulse_leaf_candidate()`；
- 汇总 `status`、`reason`、`best_true_reduced_cost`、`negative_leaves`、`found_negative`、`exhausted`；
- `deadline` 命中时返回 `status=TIME_LIMIT`、`exhausted=False`；
- `max_recursions` 命中时返回 `status=RECURSION_LIMIT`、`exhausted=False`。

## 明确未做

本轮没有实现：

- return feasibility pruning；
- completion-bound pruning；
- dominance archive；
- depot-ready memo；
- branch compiler；
- support-aware harvesting；
- diversity backtracking；
- resume/cache；
- parallel shard workers；
- production driver 接入。

## Brute-force 对照

测试中新增独立 brute-force enumerator，枚举方式不同于 Pulse DFS：

- 先枚举全局 ordered task tuple；
- 再枚举 sortie size partitions；
- 再直接调用 `evaluate_timed_trip()`、`make_journey()`、`manual_journey_reduced_cost()`。

它不调用 Phase 3A helper，因此可以作为 Phase 3B toy Pulse 的独立语义对照。

## 测试覆盖

新增 focused tests：

- `test_toy_exhaustive_pulse_matches_bruteforce_feasible_journeys`
- `test_toy_exhaustive_pulse_best_rc_and_negative_flag_match_bruteforce`
- `test_toy_exhaustive_pulse_no_negative_exhausts_toy_universe`
- `test_toy_exhaustive_pulse_first_task_shards_partition_bruteforce`
- `test_toy_exhaustive_pulse_keeps_tasks_elementary_and_cover_once`
- `test_toy_exhaustive_pulse_no_wait_matches_bruteforce`
- `test_toy_exhaustive_pulse_budget_hits_return_incomplete`

覆盖内容：

- Pulse feasible journey signatures 等于 brute-force；
- Pulse true RC map 等于 brute-force；
- Pulse `best_true_reduced_cost` 等于 brute-force best；
- Pulse `found_negative` iff brute-force 存在 true negative；
- no-negative toy universe 下 `exhausted=True` 且没有 negative leaves；
- first-task shard 结果等于 brute-force 中 `first(J)=task` 的子集；
- 所有 first-task shards 并集等于全量非空 journeys；
- shards 之间不重叠；
- 每个 journey 不重复访问 task；
- cover dual 只按 unique `journey.task_set` 领取一次；
- no-wait toy case 下 Pulse 与 brute-force 可行性一致；
- deadline / recursion-limit 命中返回 incomplete，不产生 no-negative 证明。

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/pulse_materialization.py \
BPC_future/pricing/pulse_toy_exhaustive.py \
BPC_future/pricing/sharded_pulse_final_judge.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

Phase 3B focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_matches_bruteforce_feasible_journeys \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_best_rc_and_negative_flag_match_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_no_negative_exhausts_toy_universe \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_first_task_shards_partition_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_keeps_tasks_elementary_and_cover_once \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_no_wait_matches_bruteforce \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_toy_exhaustive_pulse_budget_hits_return_incomplete
```

结果：

```text
Ran 7 tests in 0.014s
OK
```

Phase 2.5 guard 回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_enabled_without_dummy_engine_is_incomplete \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_default_off \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_all_certified_sets_official_bound \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_rejects_missing_test_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_rejects_missing_env_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_without_dummy_is_incomplete \
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
Ran 35 tests in 0.753s
OK
```

## 当前边界

- Phase 3B toy exhaustive result 不是 official certificate；
- 连续时间 waiting / no-wait interval search 尚未实现；
- branch constraints 尚未实现；
- hierarchical shard refine 尚未实现；
- production driver 仍不调用该 toy engine。

## 结论

Phase 3B 已完成：root-only toy Pulse 在受控有限搜索空间中与 brute-force enumerator 逐项一致，first-task sharding 是严格 partition，negative 判断与 true-RC 一致，并且仍然强制复用 Phase 3A 的 `TimedTrip` / `JourneyColumn` 物化合同。
