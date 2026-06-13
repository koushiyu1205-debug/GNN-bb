# Sharded Pulse Phase 9H RMP/Dual Stabilization Probe Skeleton 报告

日期：2026-06-13

## 目标

Phase 9H 只做 `audit-only RMP/dual stabilization probe skeleton`。

本轮目标不是启用新的 RMP stabilization，也不是做 official certificate gate，而是验证：

1. Phase 9G 的 stabilization diagnostic design 能落成可观测的 probe plan；
2. summary 日志能记录 mode、context hash、anchor weight、candidate source；
3. probe plan 明确 `certificate_effect_allowed=False`、`official_effect_allowed=False`、`mutates_rmp=False`；
4. 5/10 小实例仍不触发该 probe；
5. 20-task smoke 能给出 active-family / stable-basis stabilization 信号。

## 实现摘要

### 1. 新增 profile group

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增：

- `phase9h_rmp_dual_stabilization_probe_skeleton`

该 group 仍只展开为既有 profile：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`

### 2. 新增 probe skeleton 字段

新增 top-level summary 字段：

- `followup_stabilization_probe_enabled`
- `followup_stabilization_probe_status`
- `followup_stabilization_probe_reason`
- `followup_stabilization_probe_mode`
- `followup_stabilization_probe_candidate_source`
- `followup_stabilization_probe_anchor_weight`
- `followup_stabilization_probe_context_hash_required`
- `followup_stabilization_probe_context_hash`
- `followup_stabilization_probe_certificate_effect_allowed`
- `followup_stabilization_probe_official_effect_allowed`
- `followup_stabilization_probe_mutates_rmp`
- `followup_stabilization_probe_design_profile`

并新增对应 `pulse_worker_followup_*` alias。

### 3. 新增只读 helper

新增：

- `_stabilization_probe_skeleton()`

该 helper 将 Phase 9G 的 design class 转成 audit-only probe plan：

- `active_family_stabilization_diagnostic` -> `active_family_dual_anchor`
- `stable_basis_dual_stabilization_diagnostic` -> `stable_basis_dual_anchor`
- `generic_dual_stabilization_diagnostic` -> `generic_dual_anchor`
- `pool_compression_precheck_diagnostic` -> `pool_compression_precheck`

如果缺少 context hash，则返回：

- `enabled=False`
- `status=blocked_missing_context_hash`

任何情况下都固定：

- `certificate_effect_allowed=False`
- `official_effect_allowed=False`
- `mutates_rmp=False`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9h_rmp_dual_stabilization_probe_skeleton_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9h_rmp_dual_stabilization_probe_skeleton \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9h_rmp_dual_stabilization_probe_skeleton_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9h_rmp_dual_stabilization_probe_skeleton_smoke_20260613/summary.csv`

## 关键结果

### 5/10 Guard

- `apollo5`、`tranq5`、`apollo10`、`tranq10_09`：
  - worker added journeys = 0；
  - stabilization design class = `no_worker_add`；
  - probe enabled = `False`；
  - probe mutates RMP = `False`；
  - probe official effect allowed = `False`；
  - probe certificate effect allowed = `False`；
  - official result 与 baseline 一致；
  - critical disagreement = `False`。

### Apollo20 coverage-target profile

实例：`mt20_greedy_apollo_01`

- stabilization design class:
  - `active_family_stabilization_diagnostic`
- probe status:
  - `audit_only_probe_planned`
- probe mode:
  - `active_family_dual_anchor`
- candidate source:
  - `active_family_stabilization_candidate`
- anchor weight:
  - `0.1`
- context hash:
  - `080a188d2484ee3e`
- certificate effect allowed:
  - `False`
- official effect allowed:
  - `False`
- mutates RMP:
  - `False`

### Apollo20 auto-active validation profile

实例：`mt20_greedy_apollo_01`

- stabilization design class:
  - `stable_basis_dual_stabilization_diagnostic`
- probe status:
  - `audit_only_probe_planned`
- probe mode:
  - `stable_basis_dual_anchor`
- candidate source:
  - `stable_basis_dual_stabilization_candidate`
- anchor weight:
  - `0.05`
- context hash:
  - `080a188d2484ee3e`
- certificate effect allowed:
  - `False`
- official effect allowed:
  - `False`
- mutates RMP:
  - `False`

### Tranq20

`tranq20_01` 在本轮两个 opt-in worker profile 中均未产生 worker-added journeys：

- probe enabled = `False`；
- official result 与 baseline 一致；
- critical disagreement = `False`。

## 解释

Phase 9H 没有证明 RMP/dual stabilization 有 ROI。它只把下一步实验的日志和 guard 骨架钉牢。

本轮 smoke 中 Apollo20 两条 opt-in profile 的 official result 与 baseline 不完全一致，这是既有 worker profile 本身造成的路径差异，不是 probe skeleton 的效果。probe skeleton 没有接入 solver，也不会修改 RMP、pricing decision、official certificate 或 official lower bound。

当前信号仍然是：

- active-family stabilization 和 stable-basis dual stabilization 是合理的下一步诊断对象；
- 但下一步若要真正尝试 stabilization，也必须继续 audit-only / opt-in / context-hash guarded；
- 不应回到扩大 Pulse active-worker、official certificate gate、resume 或 parallel 主线。

## Exactness 边界

- 本轮只新增 summary probe-plan 字段；
- 不改变 solver / pricing / RMP / driver official decision；
- 不新增 official certificate；
- 不启用 production default；
- 不做 resume；
- 不做 parallel；
- 不改变 prefix RC bound；
- 不扩大 active worker 触发范围；
- context hash 缺失时 probe skeleton fail-closed；
- probe skeleton 永远 `certificate_effect_allowed=False`、`official_effect_allowed=False`、`mutates_rmp=False`。

## 当前结论

Phase 9H 继续支持 Phase 8R 的主结论：Pulse active-worker 路线没有稳定 ROI。

当前下一步应转入更窄的 RMP/dual stabilization audit-only 实验，或准备把 Pulse worker/proof 路线的无 ROI 证据补全到最终 B 类交付。仍不应做 production worker 默认开启、official certificate gate、resume / parallel、20/100 A/B 或简单增大 worker/pricing time limit。

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
Ran 4 tests in 0.003s
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
Ran 480 tests in 1.436s
OK (skipped=1)
```
