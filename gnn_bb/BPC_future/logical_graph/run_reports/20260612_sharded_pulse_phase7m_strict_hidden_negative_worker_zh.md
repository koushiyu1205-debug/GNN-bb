# Sharded Pulse Phase 7M Strict Hidden-negative Worker 报告

日期：2026-06-12

## 目标

本轮实现 Phase 7M：把 Sharded Pulse hidden-negative worker 收紧为严格的 hard-tail worker。

目标不是放开 official certificate，也不是把 Pulse 变成默认 active worker。Phase 7M 只允许 Pulse 在已有 audit negative signal 的 hard-tail 场景中作为 hidden-negative column finder 运行。

## 实现摘要

### 1. Previous audit negative signal gate

driver 层新增轻量 audit-signal cache。它只记录上一轮 audit 是否出现 Pulse negative signal，并绑定：

- node id；
- depth；
- CG iteration；
- true dual hash；
- cuts hash；
- branch hash；
- forbidden signature hash；
- aggregate context hash。

该 cache 不是 proof cache，也不是 certificate cache。它只用于 hard-tail worker 触发判断。

当前只接受 strongest signal：

- audit status 为 `FOUND_NEGATIVE`；
- 或 comparison type 为 `legacy_incomplete_pulse_negative`；
- 或 comparison type 为 `legacy_negative_pulse_negative`；
- 或 `pulse_audit_shards_negative > 0`。

prune-only signal 不触发 worker。

### 2. Strict hard-tail worker gate

`journey_sharded_pulse_hidden_negative_worker_trigger="hard_tail_only"` 时必须同时满足：

- hidden worker 显式启用；
- 当前是 certificate candidate；
- task 数量达到 min-task gate；
- remaining time 达到 min-remaining gate；
- previous audit negative signal 有效；
- previous audit context 与当前 true dual / cuts / branch / forbidden context 一致。

否则 worker 不运行，并在开启 skip logging 时写出稳定 skip reason。

### 3. Worker 仍不产生证书

hidden-negative worker 仍然只能作为找列器：

- `FOUND_NEGATIVE` / `FOUND_NEGATIVE_HARVESTED` 可走正常 add-column path；
- `INCOMPLETE_LIMIT` 不设置 official lower bound；
- `DUPLICATE_ONLY` 不证书；
- no-negative / certified-like 结果会被降级为 non-certificate incomplete；
- 所有返回 journey 进入 RMP 前继续由 `manual_journey_reduced_cost()` 逐条复算。

### 4. Calibration summary 扩展

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 增加：

- profile：`audit_plus_strict_worker`；
- profile alias：`audit_only`；
- worker summary 字段：
  - `worker_events`
  - `pulse_worker_skipped`
  - `pulse_worker_skip_reason`
  - `pulse_worker_trigger`
  - `pulse_worker_previous_audit_signal`
  - `pulse_worker_status`
  - `pulse_worker_returned_journeys`
  - `pulse_worker_added_journeys`
  - `pulse_worker_true_rc_filtered`
  - `pulse_worker_time`
  - `pulse_worker_recursions`
  - `pulse_worker_shards_negative`
  - `pulse_worker_context_hash`

该 profile 仍是 opt-in smoke/calibration 用，不改变默认 benchmark 行为，也不进入脚本默认 profile 顺序。

## 文档同步

`BPC_future/docs/sharded_pulse_final_judge_plan.md` 已补 Phase 7M，并确认 disagreement severity 分类为：

- critical：
  - `legacy_certified_pulse_negative`
  - `legacy_negative_pulse_certified`
- warning：
  - `legacy_certified_pulse_incomplete`
  - `legacy_incomplete_pulse_certified`
  - `legacy_negative_pulse_incomplete`
  - `legacy_incomplete_pulse_negative`
  - 其他非一致状态

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py
```

结果：通过。

Focused regression：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_payload_agreement_and_disagreements \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_certified_log_does_not_change_official_bound \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_timeout_is_log_only \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_logs_transition_counters \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_negative_signal_helper_is_strict \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_hard_tail_skips_without_audit_signal \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_context_mismatch_invalidates_signal \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_matching_audit_signal_triggers \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_hard_tail_gate_skips_small_fast_instance \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_hard_tail_gate_triggers_with_signal \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_returns_true_rc_negative_only \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_driver_adds_negative_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_duplicate_only_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_no_negative_not_certificate
```

结果：

```text
Ran 14 tests in 0.118s
OK
```

全量回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 437 tests in 61.828s
OK (skipped=1)
```

极小脚本 smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir /tmp/sharded_pulse_phase7m_smoke \
--instances very_small \
--profiles baseline audit_plus_strict_worker \
--time-limit 2.0 \
--audit-time-limit 0.1 \
--worker-time-limit 0.1 \
--pricing-time-limit 0.05 \
--max-cg-iterations 2 \
--quiet
```

结果：

- summary/json 和 summary/csv 成功生成；
- baseline official result 不变；
- `audit_plus_strict_worker` 在 `very_small` 上因 `instance_too_small` 跳过 worker；
- worker skip reason / worker fields 可观测。

小矩阵短 smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir /tmp/sharded_pulse_phase7m_matrix_smoke \
--instances apollo5 tranq5 apollo10 tranq10_09 \
--profiles baseline audit_only audit_plus_strict_worker \
--time-limit 2.0 \
--audit-time-limit 0.1 \
--worker-time-limit 0.1 \
--pricing-time-limit 0.05 \
--max-cg-iterations 2 \
--quiet
```

结果：

- 4 instances x 3 profiles 成功生成 summary；
- `official_unchanged_vs_baseline=True` for all non-baseline rows；
- 没有 critical disagreement；
- `audit_only` 和 `audit_plus_strict_worker` 都观测到 `legacy_incomplete_pulse_negative` warning；
- `audit_plus_strict_worker` 均记录 worker event；
- strict worker 在该短时限 smoke 下均因 `no_previous_audit_negative_signal` 跳过，没有返回列，也没有改变 official result。

## 当前边界

- 没有放开 official certificate gate；
- 没有默认启用 hidden-negative worker；
- 没有做 resume / parallel；
- 没有做 20/100 A/B；
- small matrix 的 `audit_plus_strict_worker` real smoke 仍需单独运行和记录。

## 结论

Phase 7M 已完成：hidden-negative worker 现在可以作为严格门控的 hard-tail 找列器使用，且触发条件依赖真实 audit negative signal。prune-only 信号不会触发 worker，context mismatch 会 fail-closed，worker incomplete / duplicate-only / no-negative 不会污染 official lower bound。
