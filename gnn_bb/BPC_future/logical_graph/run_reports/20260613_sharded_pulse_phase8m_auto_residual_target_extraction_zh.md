# Sharded Pulse Phase 8M Automatic Residual Target Extraction 报告

日期：2026-06-13

## 目标

本轮只做 Phase 8M：从同一 calibration 矩阵中的前序 diagnostic row 自动提取 residual target，并在 context hash 匹配时把 target first-task priority 注入 worker。

不做：

- production worker 默认开启；
- official certificate gate；
- resume；
- parallel；
- 20/100 A/B；
- 扩大 worker time limit；
- 把 `8,15,5` 继续作为通用硬编码策略。

## 实现摘要

### 1. 新增 auto residual profiles

新增两个 calibration profile：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate`

二者均为 20-task only，5/10 task 下 no-op。

diagnostic profile：

- 从前序 row 自动抽取 target；
- 启用 target first-task priority；
- 不启用 hard-tail fingerprint；
- 用于验证 residual-aware scheduling 是否能触达候选。

ROI gate profile：

- 同样自动抽取 target；
- 启用 context hash guard；
- 保留 hard-tail fingerprint、follow-up reserve、true-RC gate、same-iteration / active-support guard；
- 用于 strict gate 安全性检查。

### 2. 自动 target 提取

新增 helper：

- `_derive_auto_residual_target()`
- `_apply_auto_residual_target_to_config()`

提取规则：

- 只消费同一实例的前序 rows；
- 只从 20-task row 提取；
- source row 必须有非空 `worker_context_hash`；
- 优先使用 `followup_first_negative_sequence`；
- 若没有 sequence，则退回 `followup_first_negative_task_set`；
- target 长度必须至少 2；
- 不再硬编码 `8,15,5`。

### 3. Context hash guard

driver 新增：

- `_journey_sharded_pulse_expected_context_allows()`

若 config 带：

- `journey_sharded_pulse_hidden_negative_worker_expected_context_hash`

则 worker 当前 context hash 必须完全一致，否则直接 skip：

- `residual_target_context_mismatch`

该 guard 只影响 opt-in worker，不影响默认 benchmark / official certificate。

### 4. Summary 字段

新增 summary 字段：

- `auto_residual_target_applied`
- `auto_residual_target_sequence`
- `auto_residual_target_source_profile`
- `auto_residual_target_source_context_hash`
- `auto_residual_target_context_match`

同时修正 `worker_context_hash` 提取逻辑：从 worker events 中取最后一个非空 context hash，避免后续 `max_cg_iter_exceeded` skip 事件覆盖真实 context。

## Smoke 矩阵

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase8m_auto_residual_target_diagnostic_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 \
--profiles baseline \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_diagnostic \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_residual_target_roi_gate \
--time-limit 1.5 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 3 \
--current-probe-time-limit 0.5 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase8m_auto_residual_target_diagnostic_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase8m_auto_residual_target_diagnostic_20260613/summary.csv`

## Smoke 结果

### 5/10 guard

Apollo5 / Tranq5 / Apollo10 / Tranq10_09：

- auto residual target 未应用；
- worker 未触发；
- official result unchanged；
- no critical disagreement。

### Apollo20 diagnostic auto

前序 seed profile：

- `coverage_no_roi_gate`
- worker triggered；
- returned / added = `3 / 3`；
- worker returned task sets：`[7,19]`, `[6,19]`, `[11,12]`；
- follow-up residual negative：`[5,8,15]`；
- source context hash：`080a188d2484ee3e`。

auto diagnostic profile：

- 自动抽取 target sequence：`8,15,5`；
- source profile：`coverage_no_roi_gate`；
- context match：`True`；
- worker target first-task priority enabled；
- worker returned / added = `8 / 8`；
- returned candidates 包含 exact `[5,8,15]`；
- returned task-set samples：
  - `[4,5,8,15]`
  - `[4,5,8,18]`
  - `[5,8,15]`
  - `[4,5,8]`
  - `[5,8,18]`
  - `[4,8,18]`
  - `[5,8]`
  - `[4,8]`
- short-run primal 从 baseline `921.640296` 到 `857.401315`；
- addition class = `changed_inactive_only`；
- active-support-changing count = `0`；
- follow-up residual negative 仍存在，变成 `[4,12,18]`；
- follow-up RMP objective delta = `-204.152729`；
- follow-up dual L1 delta = `204.497989`；
- no critical disagreement。

### Apollo20 strict ROI auto

strict ROI profile 从 auto diagnostic row 继续抽取：

- auto target sequence：`12,4,18`；
- context match：`True`；
- 但 worker 未触发；
- skip reason = `max_cg_iter_exceeded`；
- official result unchanged。

该结果说明 strict gate 安全，但在当前短预算 smoke 下仍然太保守，不能提供 ROI 证据。

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/solver/journey_driver.py \
BPC_future/tests/test_bpc_future.py
```

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_auto_residual_target_uses_prior_context \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_worker_expected_context_guard \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 4 tests in 0.002s
OK
```

完整 focused suite：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 479 tests in 1.432s
OK (skipped=1)
```

## Exactness Boundary

- auto residual target 只改变 opt-in worker shard scheduling；
- 不改变 official certificate；
- 不产生 official lower bound；
- worker no-column / incomplete / skip 不会证书化；
- context mismatch 会直接 skip worker；
- 5/10 benchmark profile 保持 no-op；
- default production path 不变。

## 结论

Phase 8M 的机制目标成立：

1. residual target 不再需要硬编码；
2. 可以从前序 ordinary follow-up residual negative 自动抽取；
3. context hash guard 能防止 target 在错上下文生效；
4. Apollo20 diagnostic auto 能复现 manual target-priority 的局部正信号。

但 ROI 仍未成立：

1. auto diagnostic 加入的 8 列仍是 `changed_inactive_only`；
2. active-support-changing count 仍为 0；
3. follow-up residual negative 没消失，只从 `[5,8,15]` 转为 `[4,12,18]`；
4. strict ROI gate 在短预算下仍不触发。

下一步不应放开 worker 或 certificate。建议 Phase 8N 做 residual-chain source selection / active-support-aware target gate：限制自动 target 只在 source residual 与 active support / pool active fractional set 有交集或能预测 support-changing 时生效，避免继续产生 inactive-only residual chasing。
