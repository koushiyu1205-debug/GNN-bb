# Sharded Pulse Phase 9F RMP Stabilization / Pool-compression Diagnostics 报告

日期：2026-06-13

## 目标

Phase 9F 继续只做只读诊断，不改变 solver / pricing / RMP / driver 语义。

本轮目标是把 Phase 9E 的两个 Apollo20 tail 类型转成更明确的下一步方向：

1. 是否存在 pool compression candidate；
2. 是否存在 active-family stabilization candidate；
3. 是否存在 stable-basis dual stabilization candidate；
4. 是否继续支持停止扩张 Pulse active worker。

## 实现摘要

### 1. 新增 summary 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中新增：

- `followup_post_first_negative_dual_objective_abs_ratio`
- `followup_post_first_negative_dual_move_class`
- `followup_pool_compression_candidate_class`
- `followup_pool_compression_candidate_reason`
- `followup_rmp_stabilization_candidate_class`
- `followup_rmp_stabilization_candidate_reason`
- 以及对应的 `pulse_worker_followup_*` alias。

### 2. 新增只读 helper / classifier

- `_dual_objective_abs_ratio()`
- `_classify_dual_move()`
- `_classify_pool_compression_candidate()`
- `_classify_rmp_stabilization_candidate()`

这些 helper 只解析已有 JSONL summary 信号，不做任何求解决策。

### 3. 新增 profile group

新增：

- `phase9f_rmp_stabilization_pool_compression_diagnostics`

包含：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9f_rmp_stabilization_pool_compression_diagnostics_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9f_rmp_stabilization_pool_compression_diagnostics \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9f_rmp_stabilization_pool_compression_diagnostics_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9f_rmp_stabilization_pool_compression_diagnostics_smoke_20260613/summary.csv`

## 关键结果

### 5/10 Guard

- `apollo5`、`tranq5`、`apollo10`、`tranq10_09`：两个 opt-in worker profile 均未触发 worker；
- 5/10 official result 与 baseline 一致；
- critical disagreement count 均为 0。

### Tranq20

`tranq20_01` 在本轮两个 opt-in worker profile 中均未触发 worker，official result 与 baseline 一致，critical disagreement count 为 0。

### Apollo20 coverage-target profile

实例：`mt20_greedy_apollo_01`

- worker added journeys: `8`
- worker added new task sets: `8`
- worker added support-changing count: `0`
- follow-up negative sequence:
  - `4,12,18`
- RMP degeneracy pressure class:
  - `active_fractional_pressure`
- active fractional ratio:
  - `0.583333333`
- active fractional value sum:
  - `3.5`
- post-first-negative objective delta:
  - `-40.33852`
- post-first-negative dual L1 delta:
  - `400.061096`
- dual/objective abs ratio:
  - `9.917594795`
- dual move class:
  - `large_dual_move_relative_to_objective`
- pool compression candidate class:
  - `no_pool_compression_signal`
- RMP stabilization candidate class:
  - `active_family_stabilization_candidate`

### Apollo20 auto-active validation profile

实例：`mt20_greedy_apollo_01`

- worker added journeys: `1`
- worker added new task sets: `0`
- worker added support-changing count: `1`
- follow-up negative sequence:
  - `5,8,15|5,12,18|4,8,12`
- RMP degeneracy pressure class:
  - `stable_basis_overlapping_family_with_dual_move`
- post-first-negative objective delta:
  - `-139.913748`
- post-first-negative dual L1 delta:
  - `139.913748`
- dual/objective abs ratio:
  - `1.0`
- dual move class:
  - `proportional_dual_objective_move`
- pool compression candidate class:
  - `no_pool_compression_signal`
- RMP stabilization candidate class:
  - `stable_basis_dual_stabilization_candidate`

## 解释

Phase 9F 给出两个清晰分流：

1. coverage-target row：
   - 没有 duplicate / pool-compression 信号；
   - 有 active fractional pressure；
   - dual movement 明显大于 objective movement；
   - 更像 active-family stabilization candidate。

2. auto-active validation row：
   - 没有 duplicate / pool-compression 信号；
   - 没有 active fractional pressure；
   - active basis 稳定，但仍有 overlapping negative family；
   - 更像 stable-basis dual stabilization candidate。

因此当前证据不支持把下一步设成 pool compression policy，也不支持继续扩大 Pulse worker。更合理的最小下一步是 RMP stabilization / dual stabilization 的诊断或轻量 opt-in 实验，但仍不能影响 official certificate。

## Exactness 边界

- 本轮只新增 JSONL/summary 归因字段；
- 不改变 pricing / RMP / driver official decision；
- 不新增 official certificate；
- 不启用 production default；
- 不做 resume；
- 不做 parallel；
- 不改变 prefix RC bound；
- 不扩大 active worker 触发范围。

## 当前结论

Phase 9F 继续支持 Phase 8R 的主结论：Pulse active-worker 路线没有稳定 ROI。

当前下一步建议：

- Phase 9G：RMP/dual stabilization opt-in diagnostic design；
- 先只设计或实现极窄 opt-in diagnostic，不改变 official bounds；
- 重点比较 active-family stabilization candidate 与 stable-basis dual stabilization candidate；
- 若仍无改善，则把 Pulse worker/proof 路线的无 ROI 证据整理为最终 B 类交付的一部分。

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
Ran 480 tests in 1.429s
OK (skipped=1)
```
