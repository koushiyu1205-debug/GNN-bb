# Sharded Pulse Phase 9D Residual-family Chain Attribution 报告

日期：2026-06-13

## 目标

Phase 9D 继续沿 Phase 9C 的只读诊断路线，目标是回答：

1. 首个 follow-up residual 加入并进入 active support 后，active value 是否持续；
2. 后续 negative family 与首个 residual 是同一族、重叠族还是无关族；
3. active basis hash 是否发生 churn；
4. 当前 tail 更像 active-basis churn，还是同一 active basis 下的 residual-family regeneration。

本轮不做 worker 扩张，不做 official certificate gate，不改变求解语义。

## 实现摘要

### 1. 新增 summary 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中新增：

- `followup_first_negative_active_persistence_count`
- `followup_first_negative_active_value_sequence`
- `followup_first_negative_active_last_value`
- `followup_active_basis_hash_sequence_after_first_negative`
- `followup_active_basis_unique_count_after_first_negative`
- `followup_active_basis_churn_count_after_first_negative`
- `followup_negative_family_after_first_count`
- `followup_negative_family_after_first_relation_sequence`
- `followup_negative_family_after_first_disjoint_count`
- `followup_negative_family_after_first_overlapping_count`
- `followup_negative_family_after_first_same_count`
- `followup_negative_family_after_first_max_overlap`
- `followup_negative_family_after_first_max_jaccard`
- `followup_residual_family_chain_class`
- `followup_residual_family_chain_reason`
- 以及对应的 `pulse_worker_followup_*` alias。

### 2. 新增只读 helper

- `_pool_records_after_index()`
- `_active_residual_persistence_summary()`
- `_negative_family_after_first_summary()`
- `_classify_residual_family_chain()`

这些 helper 只解析已有 JSONL 事件，不影响 pricing / RMP / driver。

### 3. 新增 profile group

新增：

- `phase9d_residual_family_chain_attribution`

包含：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9d_residual_family_chain_attribution_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9d_residual_family_chain_attribution \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9d_residual_family_chain_attribution_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9d_residual_family_chain_attribution_smoke_20260613/summary.csv`

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
- first residual active persistence count:
  - `1`
- active value sequence:
  - `[1.0]`
- active basis hash sequence:
  - `["910b061f81d9d041"]`
- active basis unique count:
  - `1`
- active basis churn count:
  - `0`
- negative family after first count:
  - `0`
- residual family chain class:
  - `active_residual_no_observed_new_family`

### Apollo20 auto-active validation profile

实例：`mt20_greedy_apollo_01`

- worker added journeys: `1`
- worker added new task sets: `0`
- worker added support-changing count: `1`
- follow-up negative sequence:
  - `5,8,15|5,12,18|4,8,12`
- first residual active persistence count:
  - `2`
- active value sequence:
  - `[1.0,1.0]`
- active last value:
  - `1.0`
- active basis hash sequence:
  - `["12fab00b36e47734","12fab00b36e47734"]`
- active basis unique count:
  - `1`
- active basis churn count:
  - `0`
- negative family after first count:
  - `2`
- negative family after first relation sequence:
  - `overlapping_task_set|overlapping_task_set`
- max overlap to first residual:
  - `1`
- max Jaccard to first residual:
  - `0.2`
- residual family chain class:
  - `persistent_active_residual_with_overlapping_new_family`

## 解释

Phase 9D 把 Phase 9C 的结论再收紧了一层：

- 首个 residual 不只是短暂进入 active support；
- 在 auto-active validation profile 中，它跨两个后续 pool diagnostics 仍保持 active value `1.0`；
- 同时 active basis hash 没有变化；
- 但后续仍出现两个新的 negative task-set family，且都只与首个 residual 弱重叠。

因此本轮 evidence 更像：

- 同一 active basis 下仍有后续负列族；
- residual-family regeneration 不是由 active basis hash churn 直接解释；
- 当前 active worker 即使命中并保持 residual active，也不能稳定消除 tail。

这继续支持 Phase 8R 的结论：不要继续扩大 Pulse active worker，也不要进入 official certificate gate。

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

当前最有价值的下一步不是再调 Pulse worker，而是 Phase 9E：

- RMP degeneracy / pool compression / active-family stabilization 诊断；
- 检查后续 negative family 是否来自 pool 重复压力、active fractional pressure、或 dual oscillation；
- 比较 active basis hash 稳定时仍出现负列族的模式；
- 再决定是否转向 RMP stabilization / pool compression / legacy final judge optimization。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_proof_tail_bridge_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

当前结果：

```text
Ran 3 tests in 0.002s
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
Ran 480 tests in 1.421s
OK (skipped=1)
```
