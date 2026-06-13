# Sharded Pulse Phase 7AA Residual Sequence Diagnostics 报告

日期：2026-06-13

## 目标

Phase 7AA 只做 residual negative 的 sequence / signature 诊断。

Phase 7W-7Z 已经证明：

- worker 能返回 true-RC negative；
- worker 返回的 task-set 与 ordinary follow-up residual negative 是 disjoint；
- 关闭 `stop_after_first_negative` 与关闭 shard ROI gate 都不能找回 `[5,8,15]` residual family。

本轮目标是把 `[5,8,15]` 从 unordered task-set 进一步定位到具体 sequence / signature，给下一步同 context targeted replay 提供精确输入。

## 实现摘要

### 1. journey_pricing 日志新增 capped negative journey samples

`journey_pricing` 事件现在记录：

- `negative_journey_signature_count`
- `negative_journey_signature_hash`
- `negative_journey_signature_samples`
- `negative_journey_sequence_samples`
- sample count / truncated flags

这些字段只来自 `pricing.journeys`，不改变 pricing、pool、certificate 或 worker trigger 语义。

### 2. ROI summary 新增 sequence/signature 字段

`run_sharded_pulse_roi_calibration.py` 新增：

- `worker_negative_journey_sequence_samples`
- `worker_negative_journey_signature_samples`
- `followup_first_negative_sequence`
- `followup_first_negative_signature_sample`
- 对应 `pulse_worker_followup_*` aliases

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_log_reports_negative_task_set_samples \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 4 tests in 0.002s
OK
```

## Probe 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7aa_residual_sequence_diagnostics_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_scan \
    strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate \
  --time-limit 4.0 \
  --audit-time-limit 0.2 \
  --worker-time-limit 0.2 \
  --current-probe-time-limit 0.2 \
  --pricing-time-limit 0.4 \
  --pricing-max-dp-states 1000 \
  --max-cg-iterations 3 \
  --audit-max-recursions 30000 \
  --worker-max-recursions 30000 \
  --current-probe-max-recursions 20000 \
  --current-probe-min-tasks 20 \
  --quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7aa_residual_sequence_diagnostics_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7aa_residual_sequence_diagnostics_20260613/summary.csv`

## 结果

| profile | worker sequence | worker signature start | follow-up first task-set | follow-up first sequence | follow-up start | relation |
|---|---|---:|---|---|---:|---|
| coverage-scan | `[6,19]` | `241.411702` | `[5,8,15]` | `[8,15,5]` | `0.0` | disjoint_task_set |
| coverage no-ROI-gate | `[6,19]` | `241.411702` | `[5,8,15]` | `[8,15,5]` | `0.0` | disjoint_task_set |

JSONL 中第二个 ordinary follow-up residual negative：

- task-set `[5,12,18]`
- sequence `[12,18,5]`
- signature start `3.086313`

## 结论

Phase 7AA 把 coverage gap 从 unordered task-set 层面推进到具体 sequence/signature 层面：

- worker 找到的是 late-start `[6,19]` family；
- ordinary heuristic 后续找到的是 early-start `[8,15,5]` 和 `[12,18,5]` family；
- 这些 family 与 worker family disjoint；
- 关闭 early stop 与关闭 shard ROI gate 都没有覆盖 `[8,15,5]`。

因此下一步不应继续调 worker gate 或放大预算。更直接的诊断是：

1. 在 ordinary heuristic 找到 `[8,15,5]` 的同一 true dual / cuts / forbidden context 下做 targeted replay；
2. 强制 transition Pulse 进入 first-task shard `8` / sequence `[8,15,5]`，检查是否能物化该 journey 并得到同一 true RC；
3. 若 replay 可行但 worker 未找到，问题是搜索预算 / shard scheduling；
4. 若 replay 不可行，问题可能是 start-time domain、path-option enumeration、no-wait/waiting 语义或 Pulse materialization/context mismatch；
5. 若 replay 可行但 true RC 不一致，优先检查 dual/cut/forbidden context 或 manual RC 分解。

## 边界

- 本轮只增加 capped 诊断日志与 summary 字段；
- default benchmark 行为不变；
- 没有 certificate effect；
- 没有 official lower-bound effect；
- Pulse incomplete / duplicate-only / empty-harvest 仍不能产生 certificate。
