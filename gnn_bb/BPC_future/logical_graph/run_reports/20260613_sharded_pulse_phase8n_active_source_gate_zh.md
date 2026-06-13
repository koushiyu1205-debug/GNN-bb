# Sharded Pulse Phase 8N Active-Support-Aware Residual Source Gate 报告

日期：2026-06-13

## 目标

Phase 8N 的目标是给 Phase 8M 的 automatic residual target extraction 加一道 active-support-aware source gate，避免继续追逐 inactive-only residual family。

本轮仍然不做：

- production worker 默认开启；
- official certificate gate；
- resume；
- parallel；
- 20/100 A/B；
- 简单扩大 worker time limit；
- 把 Apollo20 单点 diagnostic 改善当成 production ROI。

## 背景

Phase 8M 证明：

- automatic residual target extraction 能从前序 diagnostic row 自动抽出 residual target；
- Apollo20 diagnostic auto 能抽出 `8,15,5`，返回并加入 8 条列；
- returned candidates 包含 `[5,8,15]`；
- 但 addition class 仍是 `changed_inactive_only`；
- active-support-changing count = `0`；
- follow-up residual negative 只是从 `[5,8,15]` 转移到 `[4,12,18]`。

这说明 blind residual chasing 不足以证明 ROI。

## 实现摘要

### 1. 新增 active residual profiles

新增两个 20-task only calibration profiles：

- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate`

二者都要求：

- source row 来自同一实例；
- source row 是 20-task；
- source row 有非空 worker context hash；
- auto residual target 通过 active-support source gate；
- 否则禁用该 opt-in worker，不能退回普通 untargeted worker。

### 2. Active-source gate

新增：

- `_auto_residual_target_active_source_gate_reason()`

当前安全规则：

- source row 必须有 active-support-changing 信号：
  - `worker_added_support_changing_count > 0`，或
  - `pulse_worker_impact_filter_selected_active_support_changing_count > 0`，或
  - `followup_worker_active_task_set_count > 0`；
- residual target 与 worker-added family 的关系必须是：
  - `same_task_set`，或
  - `overlapping_task_set`；
- 若 relation 是 `disjoint_task_set`，则阻止 target；
- 若没有明确 active-support relation，也阻止 target。

被阻止时 summary 保留 candidate，但不会注入 worker config。

### 3. 新增 summary 字段

新增：

- `auto_residual_target_candidate_sequence`
- `auto_residual_target_source_gate`
- `auto_residual_target_source_gate_reason`

这样可以区分：

- 没有 candidate；
- 有 candidate 但被 gate 拦下；
- candidate 被应用。

## Smoke 矩阵

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase8n_active_source_gate_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 \
--profiles baseline \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_no_roi_gate \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_diagnostic \
strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_roi_gate \
--time-limit 1.5 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 3 \
--current-probe-time-limit 0.5 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase8n_active_source_gate_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase8n_active_source_gate_smoke_20260613/summary.csv`

## Smoke 结果

### 5/10 guard

Apollo5 / Tranq5 / Apollo10 / Tranq10_09：

- active auto target 未应用；
- worker 未触发；
- official result unchanged；
- no critical disagreement。

### Apollo20 seed profile

`coverage_no_roi_gate`：

- worker triggered；
- worker returned / added = `3 / 3`；
- worker added_support_changing_count = `1`；
- addition class = `active_replacement_task_set`；
- follow-up residual negative = `[5,8,15]`；
- worker-vs-ordinary relation = `disjoint_task_set`。

### Apollo20 active auto profiles

active diagnostic / active ROI profiles 均识别到 candidate：

- candidate sequence = `8,15,5`；
- source profile = `coverage_no_roi_gate`；
- source gate = `active_support`；
- source gate reason = `residual_disjoint_from_worker`；
- auto target applied = `False`；
- worker_triggered = `False`；
- official result unchanged；
- no critical disagreement。

这正是本轮预期：`[5,8,15]` 是 follow-up residual negative，但它与上一轮 worker family 是 disjoint。8M 已证明盲目追它会产生 inactive-only additions；8N 因此拒绝追这个 source。

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 3 tests in 0.002s
OK
```

完整 focused suite：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 479 tests in 1.441s
OK (skipped=1)
```

## Exactness Boundary

- active gate 只影响 opt-in calibration worker；
- 不改变 default benchmark；
- 不改变 official certificate；
- 不产生 official lower bound；
- blocked candidate 不会 fallback 成 ordinary worker；
- worker no-column / incomplete / skip 不会证书化；
- context mismatch guard 仍保留；
- 5/10 profile 保持 no-op。

## 结论

Phase 8N 达成当前目标：

1. 能识别 residual candidate；
2. 能解释为什么不追；
3. 能阻止 Phase 8M 中的 inactive-only residual chasing；
4. 不影响 official result；
5. 不产生 certificate side effect。

当前结论不是“worker ROI 成立”，而是：

- active-source gate 是必要的；
- `[5,8,15]` 这类 disjoint residual 不应自动进入 target priority；
- 下一步应寻找真正 overlapping / same-task-set 的 residual source，再评估是否能产生 active-support-changing additions。

建议下一步 Phase 8O：active residual source search / seed matrix。目标是构造或发现 source relation 为 `same_task_set` / `overlapping_task_set` 的 hard-tail row，再让 active auto profile 应用 target，并观察 added_support_changing_count 是否能大于 0。
