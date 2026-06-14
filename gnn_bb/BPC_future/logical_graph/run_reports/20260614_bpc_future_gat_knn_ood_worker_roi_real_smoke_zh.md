# BPC_future GAT/kNN/OOD Worker ROI 真实 Smoke 报告

日期：2026-06-14

## 目标

本轮对齐主线口径：

- GAT 负责 embedding / trajectory impact / residual-family 表达；
- kNN/OOD 负责安全壳；
- true-RC negative 且通过安全壳的列可进入 `HIGH_PRIORITY`；
- true-RC negative 但未通过安全壳的列只能进入 `DELAY_QUEUE`；
- 负列不能永久丢弃；
- GAT/kNN/OOD、delay queue、Pulse worker 都不能参与 no-negative certificate 或 official lower bound；
- 默认 benchmark 不启用新 worker/gate。

## 代码改动

### 1. Auto residual target 支持 signature -> arc option

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 增加 signature 解析：

- 从 `followup_first_negative_signature_sample`
- 或 `pulse_worker_followup_first_negative_signature_sample`
- 或 `worker_negative_journey_signature_samples`
- 或 `official_negative_journey_signature_samples`

解析第一段 sortie 的：

- task sequence；
- transition sequence；
- arc option sequence。

这样 GAT/kNN/OOD 审计通过的 residual-family 候选，可以自动转换为 Pulse target-priority 配置，而不是只停留在报告或手工 `--set` 覆盖里。

### 2. Exact-safe scheduler 语义保持不变

`BPC_future/learning/column_selector.py` 的语义仍是：

- `HIGH_PRIORITY`：优先加 true-RC negative；
- `DELAY_QUEUE`：延迟 true-RC negative；
- `REJECT_NONNEGATIVE_ONLY`：只允许拒绝非负 reduced-cost 候选；
- selector 不是 pricing oracle，不能产生 certificate。

## Focused 回归

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_auto_residual_target_uses_prior_context \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_expected_context_current_probe_runs_without_certificate_candidate \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_expected_context_current_probe_requires_explicit_allow_flag \
BPC_future.tests.test_learning_components.ContextAwareColumnSelectorTests.test_exact_safe_negative_scheduler_delays_negative_columns_not_rejects
```

结果：

```text
Ran 5 tests in 0.027s
OK
```

语法与 whitespace 检查通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py \
BPC_future/learning/column_selector.py \
BPC_future/solver/journey_driver.py

git diff --check -- \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py \
BPC_future/learning/column_selector.py \
BPC_future/solver/journey_driver.py
```

## 5/10 No-regression

使用主线 journey config，保留现有主线 GAT/learning 配置，不启用新的 GAT/kNN/OOD worker gate。

### 5-task

命令输出：

```text
Apollo sector-wave #1: OPTIMAL, wall=2.099470s, primal=dual=284.084294
Tranq sector-wave #1: OPTIMAL, wall=2.089542s, primal=dual=179.982081
```

### 10-task

命令输出：

```text
Apollo sector-wave #1: OPTIMAL, wall=4.975686s, primal=dual=456.756326
Tranq sector-wave #1: OPTIMAL, wall=3.495703s, primal=dual=330.363821
```

结论：

- 5/10 主线仍然快速 OPTIMAL；
- 新 worker/gate 仍是 opt-in；
- 没有默认生产启用。

## 20-task 真实 ROI Smoke

实例：

```text
BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_01_seed61000_logical_graph.json
```

### A. 默认主线 baseline

```text
status=TIME_LIMIT
primal=740.299496
dual_bound=None
rmp_solves=20
pricing_calls=26
exact_pricing_calls=6
columns=157
generated_sequences=160250
evaluated_timed_trips=359491
```

### B. no-learning baseline

用于和 expected-context target-priority 对齐上下文。

```text
status=TIME_LIMIT
primal=740.122399
dual_bound=None
rmp_solves=12
pricing_calls=16
exact_pricing_calls=6
columns=257
generated_sequences=71378
evaluated_timed_trips=152186
```

### C. expected-context + target-priority worker

配置要点：

- `journey_learning_enabled=False`
- `journey_sharded_pulse_hidden_negative_worker_enabled=True`
- `journey_sharded_pulse_hidden_negative_worker_before_heuristic_enabled=True`
- `journey_sharded_pulse_hidden_negative_worker_trigger=audit_signal_or_current_probe`
- `journey_sharded_pulse_worker_current_probe_allow_expected_context_without_certificate_candidate=True`
- `journey_sharded_pulse_hidden_negative_worker_expected_context_hash=c488c428ee5822de`
- target sequence: `20,17,16`
- target arc options:
  - `0->20:low_risk:2`
  - `20->17:low_risk:2`
  - `17->16:low_risk:2`
  - `16->0:low_risk:2`

带引号命令复跑结果：

```text
cg=7 kind=sharded_pulse_hidden_negative_worker
best_rc=-1.85699125
journeys=1
reason=sharded_pulse_found_negative

status=TIME_LIMIT
primal=739.158736
dual_bound=None
rmp_solves=13
pricing_calls=16
exact_pricing_calls=7
columns=259
generated_sequences=73041
evaluated_timed_trips=153882
```

## 判断

target-priority worker 有真实正信号：

- 相对同配置 no-learning baseline，incumbent 从 `740.122399` 改善到 `739.158736`；
- columns 从 `257` 增至 `259`；
- 说明 GAT/kNN/OOD 识别出的 residual-family target 能帮助 Pulse 找到有用列。

但还不能生产启用：

- 两组 20-task 都是 `TIME_LIMIT`；
- `dual_bound=None`，没有 official lower bound；
- 没有证明 tail retry 被稳定减少；
- 当前只验证了一个 20-task Apollo sector-wave 实例；
- expected-context target-priority 依赖特定 capture context，不能泛化为默认策略。

## 重要纠偏

`run_sharded_pulse_roi_calibration.py` 使用很小的 `pricing_time_limit` 时，会在 0.2-6 秒内早停。这类输出只能验证配置门控和日志字段，不能作为真实 20-task ROI smoke。

本报告中的 20-task 真实 smoke 使用 `run_bpc_future.py` 直接跑，运行时间约 72-85 秒，才可作为当前阶段的 ROI 证据。

另外，包含 `->` 的 arc-option 配置必须整体加 shell 引号，例如：

```bash
--set 'journey_sharded_pulse_hidden_negative_worker_target_arc_option_priority_sequence=0->20:low_risk:2,20->17:low_risk:2,17->16:low_risk:2,16->0:low_risk:2'
```

未加引号时，bash 会把 `>` 当成重定向，导致 stdout 被写入临时文件，arc-option 参数本身也不可信。本报告采用带引号复跑后的证据。

## 下一步

继续做 audit-only A/B，但不能默认启用：

1. 扩展到更多 20-task sector-wave / random-wave / greedy-anchor 实例；
2. 自动从 GAT/kNN/OOD 审计结果生成 target-priority 配置；
3. 记录 worker added columns 的后续 RMP objective / dual trajectory 变化；
4. 若多个 20-task 实例均显示 primal 或 tail retry 改善，再考虑更严格的 hard-tail trigger；
5. official certificate gate 仍然禁止。
