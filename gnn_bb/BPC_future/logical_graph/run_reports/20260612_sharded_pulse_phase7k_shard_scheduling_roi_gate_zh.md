# Sharded Pulse Phase 7K Shard Scheduling + ROI Gate 报告

日期：2026-06-12

## 目标

本轮只做 Phase 7K：`Shard scheduling + ROI gate + audit trigger observability`。

不做：

- official certificate gate；
- production default enable；
- 20/100 A/B；
- parallel；
- persistent resume；
- cut / subset-row prefix bound。

## 实现摘要

### 1. Audit trigger 可观测

`journey_sharded_pulse_audit` 现在支持 trigger 字段：

- `after_legacy_final_judge`
- `after_each_final_pricing`
- `on_certificate_candidate`

新增日志字段：

- `pulse_audit_skipped`
- `pulse_audit_skip_reason`
- `pulse_audit_trigger`

当前 skip reason 覆盖：

- `audit_disabled`
- `not_after_legacy_final_judge`
- `base_pricing_is_sharded`
- `pricing_state_not_eligible`
- `trigger_mismatch:*`

`journey_sharded_pulse_audit_force_on_root=True` 可在 root 处强制执行 trigger 检查，便于小 smoke 中确认 audit 为什么运行或跳过。

### 2. Shard scheduling

guarded sharded Pulse 增加 opt-in shard scheduling：

- first-task shard 按 cover dual、depot round-trip cost proxy、可选 urgency 排序；
- second-action child shard 按 next-task cover dual 与 transition cost proxy 排序；
- `return-after-first-task` child 放在 next-task children 之后。

排序只影响运行顺序，不改变 partition、ledger 或 certificate 语义。

### 3. ROI gate

新增 opt-in low-ROI gate：

```text
time_spent >= min_time
expanded_states >= min_expanded
prune_rate < prune_rate_floor
no negative
not certified
```

满足时 shard 只记为 `low_roi_incomplete`，不会 certificate。

ROI gate 还会阻止 parent shard 继续 refine，避免把低收益 first-task shard 扩成大量 child shards。

### 4. Hidden worker hard-tail gate

hidden-negative worker 继续默认关闭。

新增 `hard_tail_only` trigger，必须满足：

- `certificate_candidate=True`
- task 数量不低于 `journey_sharded_pulse_hidden_negative_worker_min_tasks`
- remaining time 不低于 `journey_sharded_pulse_hidden_negative_worker_min_remaining_time`
- 若启用 `journey_sharded_pulse_hidden_negative_worker_require_previous_audit_signal`，还必须有 previous audit signal

这避免 Apollo5 这类小快实例默认启动 worker。

## 新增测试

新增 8 个 focused tests：

- `test_sharded_pulse_audit_skip_logs_reason`
- `test_sharded_pulse_audit_force_on_root_runs_after_each_pricing`
- `test_sharded_pulse_shard_priority_order_stable`
- `test_sharded_pulse_child_priority_order_stable`
- `test_sharded_pulse_low_roi_gate_blocks_refinement_not_certificate`
- `test_sharded_pulse_low_roi_gate_keeps_found_negative`
- `test_sharded_pulse_hidden_negative_worker_hard_tail_gate_skips_small_fast_instance`
- `test_sharded_pulse_hidden_negative_worker_hard_tail_gate_triggers_with_signal`

关键语义：

- low ROI 只能产生 incomplete，不能产生 certificate；
- low ROI gate 不吞 `FOUND_NEGATIVE`；
- scheduling 不改变结果语义；
- hard-tail worker gate 能跳过小实例，也能在显式 hard-tail 条件下触发。

## 验证命令

新增 focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_skip_logs_reason \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_audit_force_on_root_runs_after_each_pricing \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_shard_priority_order_stable \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_child_priority_order_stable \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_low_roi_gate_blocks_refinement_not_certificate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_low_roi_gate_keeps_found_negative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_hard_tail_gate_skips_small_fast_instance \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_hidden_negative_worker_hard_tail_gate_triggers_with_signal
```

结果：

```text
Ran 8 tests in 0.036s
OK
```

Phase 7J / 7H / 7I 周边回归：

```text
Ran 12 tests in 0.571s
OK
```

全量 `BPCFutureTests`：

```text
Ran 433 tests in 50.090s
OK (skipped=1)
```

## Guarded Engine Smoke

保存位置：

```text
BPC_future/results/sharded_pulse_phase7k_roi_gate_smoke_20260612/guarded_engine_summary.json
```

smoke 矩阵：

- `very_small`
- Apollo5 balanced seed 36000
- Tranquillitatis5 balanced seed 136000
- Apollo10 balanced seed 41002

profile：

- `no_refine`
- `refine`
- `refine_roi`

结论：

- 所有 profile 均保持 `global_certificate_capable=False`；
- Apollo5 / Tranq5 / Apollo10 上，`refine` 会把 first-task parent 拆为 second-action children，并显著增加 child certified 数；
- `refine_roi` 会减少 child 膨胀，并记录 `low_roi_shards`；
- Apollo10 stress 下：
  - `refine`: `10 parent -> 100 child shards`，`90 certified / 10 incomplete`
  - `refine_roi`: `1 refined parent / 19 required shards`，`9 certified / 10 incomplete / 9 low_roi`
- 这说明 ROI gate 能把低收益 shard fail-open 成 incomplete，而不是继续扩大 child 调度开销。

## 当前边界

- ROI gate 不是 proof，只能 fail-open 为 incomplete；
- scheduling priority 不是 reduced-cost bound；
- hidden worker 仍不能 certificate；
- audit skip event 只是 observability，不改变 official result；
- 仍未做 resume / parallel / production default enable。

## 结论

Phase 7K 已完成：Sharded Pulse 现在有 opt-in shard ordering、low-ROI fail-open gate、audit trigger skip logging，以及更严格的 hidden-worker hard-tail trigger。

当前最重要的工程结论是：

1. refinement 可以切小 hard shard，但会增加 child 调度成本；
2. ROI gate 可以阻止低收益 parent 继续膨胀为 child shards；
3. low ROI / audit / worker 机制都不会产生 official certificate；
4. 下一步如果继续推进，应先用 audit-only 小矩阵校准 ROI 阈值，再考虑 proof-closed resume 或更严格 hidden-negative worker 触发。
