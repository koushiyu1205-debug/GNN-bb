# Sharded Pulse Phase 9C RMP Residual Active-Support Attribution 报告

日期：2026-06-13

## 目标

Phase 9C 只做 RMP residual impact / active-support attribution。

本轮不继续扩大 Pulse active worker，也不做 production certificate gate。目标是回答 Phase 9B 留下的问题：

1. follow-up returned residual column 加入后，下一轮是否进入 active support；
2. 如果进入 active support，是否还能继续出现新的 negative task-set family；
3. 当前 tail 更像 inactive-new-column tail，还是 active residual 后的新负列族 / RMP-dual degeneracy。

## 实现摘要

### 1. 新增 summary 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中新增只读归因字段：

- `followup_first_negative_active_after_addition`
- `followup_first_negative_active_value_after_addition`
- `followup_first_negative_active_journey_count_after_addition`
- `followup_first_negative_active_relation_after_addition`
- `followup_active_fractional_ratio_after_first_negative`
- `followup_active_total_value_after_first_negative`
- `followup_active_task_set_hash_after_first_negative`
- `followup_rmp_residual_impact_class`
- `followup_rmp_residual_impact_reason`
- 以及对应的 `pulse_worker_followup_*` alias。

### 2. 新增只读 helper

- `_first_pool_after_index()`
- `_active_task_set_value_from_pool_record()`
- `_classify_rmp_residual_impact()`

这些 helper 只读取 JSONL 事件，不改变 solver / pricing / pool 语义。

### 3. 新增 profile group

新增：

- `phase9c_rmp_residual_active_support_attribution`

包含：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9c_rmp_residual_active_support_attribution_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9c_rmp_residual_active_support_attribution \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9c_rmp_residual_active_support_attribution_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9c_rmp_residual_active_support_attribution_smoke_20260613/summary.csv`

## 关键结果

### 5/10 Guard

- `apollo5`、`tranq5`、`apollo10`、`tranq10_09`：两个 opt-in worker profile 均未触发 worker；
- 5/10 official result 与 baseline 一致；
- critical disagreement count 均为 0。

### Apollo20 coverage-target profile

实例：`mt20_greedy_apollo_01`

- worker triggered: `True`
- worker signal source: `current_context_probe`
- worker added journeys: `8`
- worker added new task sets: `8`
- worker added support-changing count: `0`
- follow-up negative sequence:
  - `4,12,18|5,12,16|12,16,17`
- first follow-up residual addition productivity:
  - `changed_inactive_only`
- first follow-up residual active after addition:
  - `True`
- first follow-up residual active value after addition:
  - `1.0`
- active relation:
  - `same_task_set`
- active fractional ratio after first negative:
  - `0.583333333`
- active total value after first negative:
  - `8.5`
- RMP residual impact class:
  - `active_residual_then_new_negative_family`

### Apollo20 auto-active validation profile

实例：`mt20_greedy_apollo_01`

- worker triggered: `True`
- worker signal source: `current_context_probe`
- worker added journeys: `1`
- worker added new task sets: `0`
- worker added support-changing count: `1`
- follow-up negative sequence:
  - `5,8,15|5,12,18|4,8,12`
- first follow-up residual addition productivity:
  - `changed_inactive_only`
- first follow-up residual active after addition:
  - `True`
- first follow-up residual active value after addition:
  - `1.0`
- active relation:
  - `same_task_set`
- active fractional ratio after first negative:
  - `0.0`
- active total value after first negative:
  - `10.0`
- RMP residual impact class:
  - `active_residual_then_new_negative_family`

### Tranq20

`tranq20_01` 在本轮两个 opt-in worker profile 中均未触发 worker，official result 与 baseline 一致，critical disagreement count 为 0。

## 解释

Phase 9C 排除了一个过强的假设：首个 follow-up returned residual 并非总是“加了但后续完全不活跃”。

在 Apollo20 两个触发 profile 中，首个 follow-up residual task-set 在下一轮 pool diagnostics 中都能作为 same task-set active，并且 active value 都是 `1.0`。但之后仍出现 3 个 unique follow-up negative task sets。

因此当前更准确的归因是：

- 不是 profile-DP 看不到 residual；
- 不是 residual 无法返回；
- 不是首个 residual 加列后一定无法进入 active support；
- 而是 active residual 后仍会继续生成新的 negative family，伴随明显 RMP/dual movement。

这更像：

- residual-family regeneration；
- RMP dual degeneracy / active-basis churn；
- active residual 已吸收但 pricing universe 中仍有其他负列族；
- 或者当前 worker 选列目标没有直接压住后续 hard-tail family。

## Exactness 边界

- 本轮只新增 JSONL/summary 归因；
- 不改变 pricing / RMP / driver official decision；
- 不新增 official certificate；
- 不启用 production default；
- 不做 resume；
- 不做 parallel；
- 不改变 prefix RC bound；
- 不扩大 active worker 触发范围。

## 当前结论

Phase 9C 进一步说明，Phase 7N-8R 的 active-worker negative result 仍然成立：Pulse worker 可以加 true-RC negative columns，但目前没有稳定证据说明这些列能消除 hard-tail。

当前 Apollo20 tail 的新定位是：

首个 follow-up residual 可以进入 active support，但 active 后仍继续出现新的 negative task-set family。

这意味着下一步不应继续增加 worker budget，也不应进入 certificate gate。更合适的下一步是 Phase 9D：

- residual-family chain / active-value persistence；
- follow-up negative family 是否由同一 active-basis churn 触发；
- RMP stabilization / pool compression 方向的最小诊断；
- 或者用只读方式比较 active dual movement 与后续 negative family 的关系。

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
Ran 480 tests in 1.439s
OK (skipped=1)
```
