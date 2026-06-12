# Sharded Pulse Phase 7H Audit-only Legacy-equivalence Smoke 报告

日期：2026-06-12

## 目标

本轮只实现 Phase 7H：`audit-only small-instance legacy-equivalence smoke` 链路。

Phase 7H 不做：

- cut / subset-row / fleet-cut prefix bound；
- resume；
- parallel；
- direct official certificate；
- production default enable；
- 20/100 A/B。

核心边界：Pulse audit 只能写日志，不得改变 official `pricing_state`、`dual_bound`、node fathoming 或 lower-bound 行为。

## 实现摘要

### 1. 新增 audit-only driver 链路

在根节点 legacy final pricing 结果之后新增 `journey_sharded_pulse_audit` 事件。

新增配置默认关闭：

- `journey_sharded_pulse_audit_enabled=False`
- `journey_sharded_pulse_audit_after_legacy_final_judge=True`
- `journey_sharded_pulse_audit_time_limit=5.0`
- `journey_sharded_pulse_audit_max_recursions=100000`
- `journey_sharded_pulse_audit_log_disagreements=True`
- `journey_sharded_pulse_audit_allow_certificate_effect=False`

audit 内部调用 guarded sharded Pulse path，但结果只用于日志。

### 2. Legacy/Pulse comparison

新增 comparison helper：

- legacy certified + pulse certified：agreement；
- legacy certified + pulse found negative：`legacy_certified_pulse_negative`，`critical`；
- legacy found negative + pulse certified：`legacy_negative_pulse_certified`，`critical`；
- legacy certified + pulse incomplete：`legacy_certified_pulse_incomplete`；
- legacy incomplete + pulse certified：`legacy_incomplete_pulse_certified`；
- legacy found negative + pulse incomplete：`legacy_negative_pulse_incomplete`。

同时新增 `pulse_audit_comparison_type`，完整覆盖：

- `legacy_certified_pulse_certified`
- `legacy_certified_pulse_incomplete`
- `legacy_certified_pulse_negative`
- `legacy_negative_pulse_negative`
- `legacy_negative_pulse_incomplete`
- `legacy_negative_pulse_certified`
- `legacy_incomplete_pulse_negative`
- `legacy_incomplete_pulse_incomplete`
- `legacy_incomplete_pulse_certified`

### 3. Audit 日志字段

`journey_sharded_pulse_audit` 记录：

- `pulse_audit_enabled`
- `pulse_audit_status`
- `pulse_audit_reason`
- `pulse_audit_global_certificate_capable`
- `pulse_audit_agrees_with_legacy`
- `pulse_audit_comparison_type`
- `pulse_audit_disagreement_type`
- `pulse_audit_disagreement_severity`
- `pulse_audit_legacy_state`
- `pulse_audit_legacy_best_rc`
- `pulse_audit_pulse_best_rc`
- `pulse_audit_time`
- `pulse_audit_recursions`
- `pulse_audit_shards_total`
- `pulse_audit_shards_certified`
- `pulse_audit_shards_incomplete`
- `pulse_audit_shards_negative`
- `pulse_audit_bound_pruned`
- `pulse_audit_archive_pruned`
- `pulse_audit_time_window_pruned`
- `pulse_audit_return_pruned`
- `pulse_audit_harvested_count`
- `pulse_audit_context_hash`
- `pulse_audit_true_dual_hash`
- `pulse_audit_cut_hash`
- `pulse_audit_branch_hash`
- `pulse_audit_forbidden_signature_hash`

### 4. Guarded dummy audit support

为 focused tests 增加 audit dummy path，但它只作用于 `journey_sharded_pulse_audit` 事件，不进入 official `journey_pricing` certificate path。

## 新增测试

新增 4 个 focused tests：

- `test_sharded_pulse_audit_payload_agreement_and_disagreements`
- `test_sharded_pulse_audit_certified_log_does_not_change_official_bound`
- `test_sharded_pulse_audit_timeout_is_log_only`
- `test_sharded_pulse_audit_logs_transition_counters`

覆盖：

- audit-only Pulse certificate 不设置 official `dual_bound`；
- audit-only Pulse certificate 不改变 driver official `pricing_state`；
- legacy certified / Pulse certified agreement；
- critical disagreement payload；
- 3x3 comparison matrix；
- context hash 字段非空；
- legacy incomplete / Pulse certified 只写日志；
- audit timeout 记录 `AUDIT_INCOMPLETE`；
- waiting-allowed instance 下 audit 可运行，但无 official certificate effect；
- bound/archive/time-window/return/harvest counters 可观测。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_payload_agreement_and_disagreements \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_certified_log_does_not_change_official_bound \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_timeout_is_log_only \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_logs_transition_counters \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_waiting_allowed_has_no_official_certificate_effect \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_default_off \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_all_certified_sets_official_bound \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_incomplete_has_no_official_bound \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_dummy_driver_smoke_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_without_dummy_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_archive_counter_surfaces \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_bound_diagnostics_surface \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_driver_smoke_harvest_counters_surface \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_guarded_waiting_allowed_not_certificate
```

结果：

```text
Ran 14 tests in 0.798s
OK
```

补充 archive/bound focused regression：

```text
Ran 5 tests in 0.041s
OK
```

完整 `BPCFutureTests` 回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 417 tests in 51.955s
OK (skipped=1)
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

`git diff --check`：通过。

## 当前边界

- audit 当前只接根节点；
- audit 不会产生 official certificate effect；
- audit dummy 只用于 focused tests；
- sharded Pulse production 默认仍关闭；
- no-wait / test-only certificate guard 不放开到普通 5/10/20；
- 真实 Apollo / Tranquillitatis audit-only smoke 已完成，但仍只是小矩阵观测，不是 production certificate gate。

## Phase 7H-real 小矩阵 Smoke

运行目录：

```text
BPC_future/results/sharded_pulse_phase7h_real_smoke_20260612/
```

矩阵：

- `very_small`
- Apollo 5：`apollo15_20km_tasks05_01_seed6000`
- Tranquillitatis 5：`tranquillitatis_balmer_like_20km_tasks05_01_seed6000`
- Apollo 10：`apollo15_20km_tasks10_01_seed11000`

每个实例跑两组：

- baseline default；
- baseline + sharded Pulse audit-only。

audit 配置保持：

- `journey_sharded_pulse_audit_enabled=True`
- `journey_sharded_pulse_audit_after_legacy_final_judge=True`
- `journey_sharded_pulse_audit_time_limit=3.0`
- `journey_sharded_pulse_audit_max_recursions=100000`
- `journey_sharded_pulse_audit_allow_certificate_effect=False`
- `journey_sharded_pulse_audit_archive_enabled=True`
- `journey_sharded_pulse_audit_bound_pruning_enabled=True`
- `journey_sharded_pulse_audit_support_aware_harvesting_enabled=True`

结果摘要：

| 实例 | audit events | official status 是否一致 | official dual_bound 是否一致 | official pricing_state 是否一致 | critical | warning | comparison types | time-window pruned | return pruned |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|
| very_small | 0 | 是 | 是 | 是 | 0 | 0 | - | 0 | 0 |
| Apollo 5 | 1 | 是 | 是 | 是 | 0 | 0 | `legacy_incomplete_pulse_incomplete` | 51343 | 2922 |
| Tranquillitatis 5 | 1 | 是 | 是 | 是 | 0 | 0 | `legacy_incomplete_pulse_incomplete` | 42331 | 1946 |
| Apollo 10 | 2 | 是 | 是 | 是 | 0 | 1 | `legacy_incomplete_pulse_incomplete`, `legacy_negative_pulse_incomplete` | 219537 | 2610 |

结论：

- `journey_sharded_pulse_audit_allow_certificate_effect=False` 生效：audit 没有改写 official `status`、`dual_bound`、`pricing_state` 或 `best_rc`。
- 没有出现 `legacy_certified_pulse_negative` 或 `legacy_negative_pulse_certified`。
- Apollo 10 出现一次 `legacy_negative_pulse_incomplete`，按当前规则是 warning，不阻塞；含义是 legacy 找到负列，而 Pulse audit 在 3 秒预算内 incomplete。
- 触发 audit 的真实小实例均有 `pulse_audit_context_hash`，无 context hash 缺失。
- Apollo 5 / Tranquillitatis 5 / Apollo 10 均观测到真实 transition pruning 信号。
- very_small 在本轮短迭代配置中没有触发 legacy final-judge audit 事件，因此只作为“audit 不改变默认 official path”的 smoke 样本。

## 结论

Phase 7H 已完成最小可验证版本和真实小矩阵 smoke：legacy final pricing 后可以运行 sharded Pulse audit，并把 agreement / disagreement / counters 写入 JSONL；audit 结果不会污染 official lower bound、pricing state 或 fathoming 逻辑。
