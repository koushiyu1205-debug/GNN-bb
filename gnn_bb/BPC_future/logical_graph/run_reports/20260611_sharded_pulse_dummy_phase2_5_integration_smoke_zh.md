# Sharded Pulse Dummy Phase 2.5 Driver Integration Smoke 报告

日期：2026-06-11

## 目标

本轮只验证 `Sharded Pulse Final Judge` 的 driver 链路，不实现真实 Pulse DFS。

Phase 2.5 的目标是确认：

1. 默认关闭 sharded dummy；
2. test-only opt-in 后 dummy `all-certified` 能被 driver 识别为 official certificate；
3. opt-in 后 dummy `incomplete` 不产生 official lower bound；
4. opt-in 后 dummy `negative` 不进入 certificate path；
5. 生产 sharding / pulse opt-in 在真实 Pulse 未实现时只返回 `INCOMPLETE`，不能调用 dummy all-certified；
6. `journey_pricing` 日志中能区分真实 `final_judge_engine=sharded_pulse` 与测试 `final_judge_engine=sharded_pulse_dummy`，并观测 dummy guard 及 shard 诊断字段。

## 实现摘要

### 1. Driver smoke 覆盖

新增 driver 级 integration smoke，直接调用 `solve_bpc_future_journey()` 跑 `very_small`，并从 JSONL 日志读取 `journey_pricing` 事件。

覆盖场景：

- 默认关闭：即使配置了 dummy shard statuses，也不进入 sharded dummy engine；
- test-only `CERTIFIED_NO_NEGATIVE`：driver 接受为 global certificate，并设置 `dual_bound`；
- dummy 缺少 `allow_test_dummy_certificate`：driver 返回 incomplete，不设置 `dual_bound`；
- dummy 缺少 `BPC_FUTURE_ALLOW_DUMMY_CERTIFICATE=1`：driver 返回 incomplete，不设置 `dual_bound`；
- 生产 sharding enabled 但 dummy disabled：driver 可运行 guarded real Pulse；若找到 true negative，则返回 `sharded_pulse_found_negative`，不设置 `dual_bound`；
- `INCOMPLETE_TIME_LIMIT`：driver 记录 sharded final judge incomplete，但 `dual_bound=None`；
- `FOUND_NEGATIVE`：driver 记录 sharded final judge found-negative，但 `global_certificate=False` 且 `dual_bound=None`。

### 2. 证书 reason guard 收紧

`JourneyPricingResult` 和 driver 的显式 `CERTIFIED_NO_NEGATIVE` 现在都要通过 certificate reason 白名单。

允许的证书 reason：

- `direct_label_no_negative_journey`
- `sharded_pulse_no_negative_journey`
- 保留既有 `ng_dssr_relaxed_no_negative_journey` relaxed certificate 语义

这避免了只靠 `pricing_state=CERTIFIED_NO_NEGATIVE` 和 `global_certificate_capable=True` 误接收不明来源证书。

`ng_dssr_relaxed_no_negative_journey` 额外 fail-closed：

- `ng_relaxation_superset` 必须显式为 `True`；
- `ng_certificate_limit_hit=True` 时不证书；
- `ng_probe_limit_hit=True` 时不证书；
- `ng_relaxation_superset=None` / 缺省 / `False` 均不证书。

### 3. Cache key skeleton 加 schema / proof version

`ShardCacheKey` 增加：

- `schema_version="sharded_pulse_ledger_v1"`
- `proof_version="pulse_proof_rules_v1"`

测试覆盖：

- true dual 变化会改变 key；
- cut 变化会改变 key；
- forbidden signature 变化会改变 key；
- branch constraint 变化会改变 key；
- pricing config 变化会改变 key；
- schema version 变化会改变 key；
- proof version 变化会改变 key。

### 4. Opt-in 开关

driver 接入仍然默认关闭。

生产 sharded path 可显式启用：

- `journey_final_judge_sharding_enabled=True`
- 或 `journey_pulse_final_judge_enabled=True`

但这只会选择 `final_judge_engine=sharded_pulse`。在真实 Pulse DFS 尚未实现时，生产 sharded path 返回 `INCOMPLETE` / fallback，不会调用 dummy engine。

dummy engine 只允许测试显式启用：

- `journey_sharded_pulse_dummy_engine_enabled=True`
- `allow_test_dummy_certificate=True` 或 `journey_sharded_pulse_allow_test_dummy_certificate=True`
- 环境变量 `BPC_FUTURE_ALLOW_DUMMY_CERTIFICATE=1`
- instance 名称必须是 `very_small` 或以 `test` 开头

缺少任一 guard 时，dummy 请求返回 `sharded_pulse_dummy_engine_not_allowed`，不得产生 official lower bound。

dummy 结果日志使用：

- `final_judge_engine=sharded_pulse_dummy`
- `final_judge_dummy_certificate=True/False`
- `final_judge_test_only=True`

未来真实 Pulse 证书应使用 `final_judge_engine=sharded_pulse`，且 `final_judge_dummy_certificate=False`。

## Driver Smoke 结论

| 场景 | sharded dummy | driver 证书 | official lower bound | 日志观测 |
|---|---:|---:|---:|---|
| 默认关闭 | 否 | 否 | 否 | 无 `final_judge_engine=sharded_pulse` |
| test-only all-certified | 是 | 是 | 是，`dual_bound` 非空 | `final_judge_engine=sharded_pulse_dummy`, `global_certificate=True` |
| dummy guard 缺失 | 是 | 否 | 否，`dual_bound=None` | `reason=sharded_pulse_dummy_engine_not_allowed` |
| dummy env guard 缺失 | 是 | 否 | 否，`dual_bound=None` | `reason=sharded_pulse_dummy_engine_not_allowed` |
| sharding enabled 但 dummy disabled | real guarded | 否 | 否，`dual_bound=None` | `reason=sharded_pulse_found_negative` |
| incomplete | 是 | 否 | 否，`dual_bound=None` | `pricing_state=INCOMPLETE_LIMIT` |
| negative | 是 | 否 | 否，`dual_bound=None` | `pricing_state=FOUND_NEGATIVE` |

## 验证命令

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
Ran 35 tests in 0.676s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/sharded_pulse_final_judge.py \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

## 当前边界

- 仍未实现真实 Pulse DFS；
- dummy `FOUND_NEGATIVE` 只用于验证 driver 不误走 certificate path，不返回真实 JourneyColumn；
- dummy `CERTIFIED_NO_NEGATIVE` 现在是 test-only 语义，不能由生产 sharding / pulse opt-in 直接触发；
- dummy certificate 需要配置 guard、instance guard 和环境变量 guard 同时满足，并在日志中标记为 `sharded_pulse_dummy`；
- Phase 3 前建议继续保持真实 DFS 与 certificate ledger 解耦，先补 toy exactness tests 后再接入叶子 materialization。

## 结论

Phase 2.5 已完成并补强 guard：sharded dummy final judge 的 driver 链路可观测、可回归，并且不会在默认或生产 sharding benchmark 路径中启用。当前证书状态机能区分 all-certified、incomplete、negative、duplicate-only、frontier-not-proof、dummy-not-allowed、dummy-env-not-allowed 与 engine-not-implemented；dummy 证书日志使用 `sharded_pulse_dummy`，不会与未来真实 `sharded_pulse` 证书混淆。
