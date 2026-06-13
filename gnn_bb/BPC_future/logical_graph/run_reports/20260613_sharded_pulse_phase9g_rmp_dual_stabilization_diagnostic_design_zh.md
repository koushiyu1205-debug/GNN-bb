# Sharded Pulse Phase 9G RMP/Dual Stabilization Diagnostic Design 报告

日期：2026-06-13

## 目标

Phase 9G 只做 opt-in diagnostic design，不启用新的求解策略。

本轮目标是把 Phase 9F 的两个候选方向落成可回归的 summary 设计字段：

1. active-family stabilization diagnostic；
2. stable-basis dual stabilization diagnostic；
3. 明确 guarded config keys；
4. 明确 certificate / official lower-bound effect 永远为 `False`。

## 实现摘要

### 1. 新增 summary 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中新增：

- `followup_stabilization_diagnostic_design_class`
- `followup_stabilization_diagnostic_design_reason`
- `followup_stabilization_diagnostic_recommended_profile`
- `followup_stabilization_diagnostic_guarded_config_keys`
- `followup_stabilization_diagnostic_certificate_effect_allowed`
- 以及对应的 `pulse_worker_followup_*` alias。

### 2. 新增只读 design helper

新增：

- `_stabilization_diagnostic_design()`

该 helper 只把 Phase 9F 的 candidate class 转换成建议的 diagnostic profile 和 guarded config keys，不修改配置，不调用 solver，不影响 official result。

### 3. 新增 profile group

新增：

- `phase9g_rmp_dual_stabilization_diagnostic_design`

包含：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9g_rmp_dual_stabilization_diagnostic_design_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9g_rmp_dual_stabilization_diagnostic_design \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9g_rmp_dual_stabilization_diagnostic_design_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9g_rmp_dual_stabilization_diagnostic_design_smoke_20260613/summary.csv`

## 关键结果

### 5/10 Guard

- `apollo5`、`tranq5`、`apollo10`、`tranq10_09`：两个 opt-in worker profile 均未触发 worker；
- 5/10 official result 与 baseline 一致；
- critical disagreement count 均为 0；
- design class 为 `no_worker_add`。

### Tranq20

`tranq20_01` 在本轮两个 opt-in worker profile 中均未触发 worker，official result 与 baseline 一致，critical disagreement count 为 0。

### Apollo20 coverage-target profile

实例：`mt20_greedy_apollo_01`

- RMP stabilization candidate class:
  - `active_family_stabilization_candidate`
- design class:
  - `active_family_stabilization_diagnostic`
- recommended profile:
  - `diagnostic_active_family_dual_anchor_audit_only`
- certificate effect allowed:
  - `False`
- guarded config keys:
  - `journey_rmp_stabilization_diagnostic_enabled`
  - `journey_rmp_stabilization_diagnostic_mode`
  - `journey_rmp_stabilization_diagnostic_allow_certificate_effect`
  - `journey_rmp_stabilization_diagnostic_context_hash_required`
  - `journey_rmp_stabilization_active_family_fractional_threshold`
  - `journey_rmp_stabilization_active_family_dual_anchor_weight`

### Apollo20 auto-active validation profile

实例：`mt20_greedy_apollo_01`

- RMP stabilization candidate class:
  - `stable_basis_dual_stabilization_candidate`
- design class:
  - `stable_basis_dual_stabilization_diagnostic`
- recommended profile:
  - `diagnostic_stable_basis_dual_anchor_audit_only`
- certificate effect allowed:
  - `False`
- guarded config keys:
  - `journey_rmp_stabilization_diagnostic_enabled`
  - `journey_rmp_stabilization_diagnostic_mode`
  - `journey_rmp_stabilization_diagnostic_allow_certificate_effect`
  - `journey_rmp_stabilization_diagnostic_context_hash_required`
  - `journey_rmp_stabilization_stable_basis_dual_anchor_weight`
  - `journey_rmp_stabilization_stable_basis_required_hash_repeats`

## 解释

Phase 9G 没有证明 RMP/dual stabilization 有 ROI。它只把下一步实验边界写清楚：

- 只能 opt-in；
- 必须 context-hash guarded；
- 必须 audit-only / diagnostic-only；
- `certificate_effect_allowed=False`；
- 不允许影响 official lower bound；
- 不能替代 true-dual exact pricing certificate。

当前更适合下一步做 Phase 9H：实现一个极窄的 audit-only stabilization probe，先验证日志链路和 no-official-effect，而不是直接做生产调参。

## Exactness 边界

- 本轮只新增 summary design 字段；
- 不改变 solver / pricing / RMP / driver official decision；
- 不新增 official certificate；
- 不启用 production default；
- 不做 resume；
- 不做 parallel；
- 不改变 prefix RC bound；
- 不扩大 active worker 触发范围。

## 当前结论

Phase 9G 继续支持 Phase 8R 的主结论：Pulse active-worker 路线没有稳定 ROI。

当前下一步建议：

- Phase 9H：audit-only RMP/dual stabilization probe skeleton；
- 只验证配置 guard、context hash、日志字段和 official no-effect；
- 不改变 official certificate / lower bound；
- 若 9H 无正向信号，则准备把 worker/proof 路线的无 ROI 证据补全到最终 B 类交付。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_proof_tail_bridge_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

当前结果：

```text
Ran 4 tests in 0.002s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

Whitespace 检查：

```bash
git diff --check
```

结果：通过。

全量 `BPCFutureTests`：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 480 tests in 1.446s
OK (skipped=1)
```
