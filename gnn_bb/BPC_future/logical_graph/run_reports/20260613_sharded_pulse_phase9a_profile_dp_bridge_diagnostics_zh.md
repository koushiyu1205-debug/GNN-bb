# Sharded Pulse Phase 9A Profile-DP Proof-tail Bridge Diagnostics 报告

日期：2026-06-13

## 目标

Phase 8R 已正式关闭 Pulse active-worker 扩张子路线。Phase 9A 转向 non-worker proof-tail structural control。

本轮目标很窄：只在 ROI calibration summary 中增加 ordinary follow-up residual negative 与 profile-DP pipeline 的桥接分类，回答：

- ordinary / follow-up residual negative 是否已经出现在 profile-DP reachable / negative / selected / materialized / returned 层；
- residual tail 是 profile-DP candidate bridge 缺口，还是 profile-DP 已返回 residual 后 RMP / tail 仍未收敛；
- 是否应该继续补 selected/materialization bridge。

本轮不改 pricing 转移，不改 final judge，不改 Pulse worker gate，不打开 production worker，不打开 official certificate gate。

## 实现摘要

### 1. 新增 summary 字段

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增：

- `followup_proof_tail_bridge_class`
- `followup_proof_tail_bridge_reason`
- `pulse_worker_followup_proof_tail_bridge_class`
- `pulse_worker_followup_proof_tail_bridge_reason`

分类函数：

- `_classify_followup_proof_tail_bridge()`

分类顺序按 profile-DP pipeline：

1. `profile_returned_residual_exact`
2. `profile_materialized_residual_not_returned`
3. `profile_selected_unmaterialized_residual`
4. `profile_weak_filtered_residual`
5. `profile_filtered_residual`
6. `profile_selected_residual_not_materialized`
7. `profile_negative_residual_not_selected`
8. `profile_reachable_residual_not_negative`
9. `profile_topmask_residual_not_reached`
10. `profile_dp_state_cap_missing_residual`
11. `profile_dp_incomplete_missing_residual`
12. `profile_overlap_without_exact_residual`
13. `profile_no_residual_signal`

这些字段只解释日志，不参与 solver 决策。

### 2. 新增 profile group

新增：

- `phase9a_profile_dp_bridge_diagnostics`

展开为：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`

该 group 只用于 opt-in calibration，不改变默认 benchmark。

## Smoke Matrix

输出目录：

```text
BPC_future/results/sharded_pulse_phase9a_profile_dp_bridge_diagnostics_smoke_20260613
```

运行实例：

- `apollo5`
- `tranq5`
- `apollo10`
- `tranq10_09`
- `mt20_greedy_apollo_01`
- `tranq20_01`

运行参数：

```text
time_limit=1.8
pricing_time_limit=0.2
pricing_max_dp_states=1000
max_cg_iterations=4
current_probe_time_limit=0.8
```

规模汇总：

| scale | rows | official changed | critical disagreement | worker triggers | bridge classes |
|---:|---:|---:|---:|---:|---|
| 5 | 6 | 0 | 0 | 0 | `no_worker_add=6` |
| 10 | 6 | 0 | 0 | 0 | `no_worker_add=6` |
| 20 | 6 | 2 opt-in worker rows | 0 | 2 | `no_worker_add=4`, `profile_returned_residual_exact=2` |

## 关键结果

### Apollo20 greedy-anchor

`coverage_target_priority`：

- worker added journeys = `8`
- support-changing = `0`
- addition class = `changed_inactive_only`
- follow-up residual = `4,12,18`
- profile-DP reachable exact = `True`
- profile-DP negative exact = `True`
- profile-DP selected exact = `True`
- profile-DP materialized exact = `True`
- profile-DP returned exact = `True`
- bridge class = `profile_returned_residual_exact`

`auto_active_residual_target_validation_diagnostic`：

- worker added journeys = `1`
- support-changing = `1`
- addition class = `active_replacement_task_set`
- follow-up residual = `5,8,15`
- profile-DP reachable exact = `True`
- profile-DP negative exact = `True`
- profile-DP selected exact = `True`
- profile-DP materialized exact = `True`
- profile-DP returned exact = `True`
- bridge class = `profile_returned_residual_exact`

### Tranq20

- worker 未触发；
- bridge class = `no_worker_add`；
- pivot signal 仍是 active fractional pressure；
- 本轮没有产生新的 profile-DP bridge 证据。

## 判断

Phase 9A 证伪了一个重要假设：

> Apollo residual tail 主要不是 profile-DP selected/materialization/returned bridge 丢失导致的。

在本轮可观测的 Apollo20 residual rows 中，follow-up residual task set 已经被 profile-DP 精确返回。也就是说：

- profile-DP 能看到 residual；
- profile-DP 能把它作为 negative；
- profile-DP 能 selected；
- materialization 成功；
- returned 也成功；
- tail 仍未稳定改善。

因此下一步不应优先补 selected-candidate materialization bridge，也不应继续做 Pulse worker target-specific ordering。

更合理的后续问题是：

- profile-DP 返回 residual 后，RMP 为什么仍不能消除后续 tail；
- residual negative sequence 是否在 RMP 中反复再生；
- returned negative 的 rough-vs-true RC 排序和 active fractional / dual movement 是否导致弱 replacement；
- legacy final judge / completion-bound tail 是否主要来自连续 residual return 后的证明阶段，而不是候选不可见。

## Exactness 边界

- 只新增 summary classifier；
- 不改变 pricing / final judge / RMP；
- 不改变 worker trigger；
- 不改变 official lower bound；
- 不打开 certificate gate；
- 默认 benchmark 不变；
- Pulse incomplete / no-column / duplicate-only 仍不能 certificate。

## 验证命令

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_proof_tail_bridge_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 4 tests in 0.002s
OK
```

完整回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 480 tests in 1.427s
OK (skipped=1)
```

diff whitespace 检查：

```bash
git diff --check
```

结果：通过。

Smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9a_profile_dp_bridge_diagnostics_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9a_profile_dp_bridge_diagnostics \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

结果：

- `summary.json` 已生成；
- `summary.csv` 已生成。

## 下一步建议

进入 Phase 9B：profile-DP returned residual tail sequence attribution。

建议回答：

- profile-DP returned residual 后，下一轮 RMP objective / dual movement 是否足够；
- residual task-set 是否在后续 CG 中反复换形再生；
- returned residual 是否是 active-support-changing，还是弱 replacement；
- rough RC 与 true RC 排序是否让 stronger residual 被延后；
- final judge tail 是否发生在 residual returned 后的证明阶段。

仍然不要做：

- Pulse worker 重新 production tuning；
- official certificate gate；
- resume / parallel；
- 20/100 A/B；
- 简单加大 pricing cap 或 worker time limit。
