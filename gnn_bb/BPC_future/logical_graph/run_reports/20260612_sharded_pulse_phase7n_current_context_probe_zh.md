# Sharded Pulse Phase 7N Current-context Signal Probe 报告

日期：2026-06-12

## 目标

Phase 7N 解决 Phase 7M 暴露的调度问题：Pulse audit 能看到 hidden-negative signal，但 strict worker 在 legacy final judge 前运行时往往没有 previous audit signal，因此保守跳过。

本轮新增 current-context signal probe。它只在 hard-tail 条件满足且显式 opt-in 时运行，用当前 true dual / cuts / branch / forbidden-signature context 做短预算 Pulse probe。probe 只能返回 true-RC negative columns，不能产生 certificate 或 official lower bound。

## 实现摘要

### 1. 新 trigger

新增：

```text
journey_sharded_pulse_hidden_negative_worker_trigger="audit_signal_or_current_probe"
```

该 trigger 仍要求：

- `certificate_candidate=True`
- task 数量满足 hidden-worker min-task gate
- remaining time 满足 hidden-worker min-remaining gate

如果 previous audit negative signal 存在且 context hash 匹配，按 strict previous-audit worker path 运行。

如果没有 previous audit signal，但 current probe 显式启用，则运行 current-context probe。

如果 previous audit signal 存在但 context mismatch，则 fail-closed 跳过 worker，不用 current probe 绕过 mismatch。

### 2. Current-context probe 配置

新增配置：

- `journey_sharded_pulse_worker_current_probe_enabled=False`
- `journey_sharded_pulse_worker_current_probe_time_limit=1.0`
- `journey_sharded_pulse_worker_current_probe_max_recursions=50000`
- `journey_sharded_pulse_worker_current_probe_min_tasks=10`
- `journey_sharded_pulse_worker_current_probe_min_remaining_time=8.0`
- `journey_sharded_pulse_worker_current_probe_harvesting_enabled=True`
- `journey_sharded_pulse_worker_current_probe_max_columns=16`
- `journey_sharded_pulse_worker_current_probe_negative_harvest_limit`

默认仍关闭。

### 3. Signal source 日志

worker 日志新增：

- `pulse_worker_signal_source`
  - `none`
  - `previous_audit`
  - `current_context_probe`
  - `ungated`
- `pulse_worker_current_probe_signal`
- `pulse_worker_previous_audit_signal`

skip 日志也写出 signal source / previous signal / current probe signal，便于区分是没有信号、context mismatch、小实例 gate，还是 probe 自身运行后无列。

### 4. Exactness 边界

保持 Phase 7M 边界：

- current probe found negative -> 只可走正常 add-column path；
- current probe incomplete -> 不证书；
- current probe duplicate-only -> 不证书；
- current probe empty found-negative -> 降级为 non-certificate incomplete；
- current probe certified-like no-negative -> 降级为 non-certificate incomplete；
- 所有 returned journeys 继续由 `manual_journey_reduced_cost()` true-RC 过滤；
- `global_certificate_capable=False`；
- `final_judge_certificate_capable=False`；
- 不产生 official lower bound。

### 5. Calibration 脚本

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增显式 opt-in profiles：

- `strict_worker_previous_signal_only`
- `strict_worker_current_probe`

summary 新增/聚合：

- `pulse_worker_signal_source`
- `pulse_worker_current_probe_signal`
- `pulse_worker_returned_journeys`
- `pulse_worker_added_journeys`
- `pulse_worker_time`
- `pulse_worker_recursions`
- `pulse_worker_shards_negative`

其中 returned / added / probe signal 会跨 worker events 聚合，避免同一 run 后续 incomplete event 遮住前面已加列的 signal。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py
```

结果：通过。

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_negative_runs_without_previous_signal \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_incomplete_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_duplicate_only_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_empty_negative_result_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_certified_like_result_is_downgraded \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_current_probe_small_fast_gate_skips \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_matching_audit_signal_triggers \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_context_mismatch_invalidates_signal \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_negative_signal_helper_is_strict
```

结果：

```text
Ran 9 tests in 0.030s
OK
```

小矩阵短 smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir /tmp/sharded_pulse_phase7n_matrix_smoke \
--instances apollo5 tranq5 apollo10 tranq10_09 \
--profiles baseline audit_only strict_worker_previous_signal_only strict_worker_current_probe \
--time-limit 2.0 \
--audit-time-limit 0.1 \
--worker-time-limit 0.1 \
--current-probe-time-limit 0.1 \
--pricing-time-limit 0.05 \
--max-cg-iterations 2 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

结果摘要：

| instance | previous-signal-only | current-probe |
|---|---|---|
| Apollo5 | skip: `no_previous_audit_negative_signal` | skip: `current_probe_instance_too_small` |
| Tranquillitatis5 | skip: `no_previous_audit_negative_signal` | skip: `current_probe_instance_too_small` |
| Apollo10 | skip: `no_previous_audit_negative_signal` | returned 2, added 2 |
| tranq10_09 | skip: `no_previous_audit_negative_signal` | returned 3, added 3 |

关键观察：

- Apollo5 / Tranquillitatis5 被 current-probe min-task gate 拦住；
- Apollo10 / tranq10_09 的 current-context probe 能返回 true-RC negative columns，并通过正常 add-column path 加入；
- 这些变化不是 certificate effect，也不是 official lower-bound effect；
- strict previous-signal-only profile 仍按 Phase 7M 逻辑保守跳过；
- 未出现 critical disagreement。

## 当前边界

- current probe 默认关闭；
- current probe 不是 certificate oracle；
- 当前未做 20/100 A/B；
- 当前未接 resume / parallel；
- 当前没有放开 official certificate gate；
- 后续若继续 worker 路线，应先评估 current probe 是否减少 legacy final judge / retry 成本，而不是直接提高预算。

## 结论

Phase 7N 已完成：strict worker 现在可以在没有 previous audit signal 时，通过同一 context 下的短预算 current probe 获得找列机会。小矩阵短 smoke 显示，5-task 小实例被 gate 拦住，10-task 样本可以通过 current probe 加到 true-RC negative columns。该路径仍只影响正常列生成，不产生 certificate 或 official lower bound。
