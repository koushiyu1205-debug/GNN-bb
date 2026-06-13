# Sharded Pulse Phase 9B Returned-residual Tail Attribution 报告

日期：2026-06-13

## 目标

Phase 9A 证明 Apollo20 的 observed residual task set 已经被 profile-DP 精确 returned，不是 selected / materialization bridge 丢失。

Phase 9B 继续沿 non-worker proof-tail structural control，回答：

- profile-DP returned residual 后，tail 是同一 task-set 重复，还是新 residual family 继续出现；
- first follow-up residual 加入 RMP 后，objective / dual 是否明显移动；
- first follow-up residual 是 active-support-changing 还是 inactive/new replacement；
- tail 是否更像 RMP/dual 退化或 continuous residual family，而不是候选不可见。

本轮仍不改 pricing / final judge / RMP 语义，不启用 production worker，不打开 certificate gate。

## 实现摘要

### 1. 新增 returned-residual tail 字段

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增：

- `followup_returned_residual_tail_class`
- `followup_returned_residual_tail_reason`
- `followup_negative_task_set_sequence`
- `followup_negative_task_set_unique_count`
- `followup_negative_task_set_repeat_count`
- `followup_first_negative_addition_productivity_class`
- `followup_first_negative_added_journeys`
- `followup_first_negative_added_new_task_set_count`
- `followup_first_negative_added_replacement_count`
- `followup_first_negative_added_support_changing_count`
- `followup_post_first_negative_rmp_objective_delta`
- `followup_post_first_negative_dual_l1_delta`

并增加 `pulse_worker_followup_*` 对应字段。

### 2. 新增 helper

- `_first_matching_column_addition_after()`
- `_first_rmp_after_index()`
- `_classify_returned_residual_tail()`

分类只读，不参与 solver 决策。

### 3. 新增 profile group

新增：

- `phase9b_returned_residual_tail_attribution`

展开与 Phase 9A 相同：

- `baseline`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_coverage_target_priority`
- `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_auto_active_residual_target_validation_diagnostic`

## Smoke Matrix

输出目录：

```text
BPC_future/results/sharded_pulse_phase9b_returned_residual_tail_attribution_smoke_20260613
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

| scale | rows | official changed | critical disagreement | worker triggers | tail classes |
|---:|---:|---:|---:|---:|---|
| 5 | 6 | 0 | 0 | 0 | `no_worker_add=6` |
| 10 | 6 | 0 | 0 | 0 | `no_worker_add=6` |
| 20 | 6 | 2 opt-in worker rows | 0 | 2 | `no_worker_add=4`, `returned_residual_then_new_negative_family=2` |

## 关键结果

### Apollo20 coverage-target row

- worker added journeys = `8`
- worker addition class = `changed_inactive_only`
- first follow-up residual = `4,12,18`
- bridge class = `profile_returned_residual_exact`
- tail class = `returned_residual_then_new_negative_family`
- follow-up negative sequence = `4,12,18|5,12,16`
- unique follow-up negative task sets = `2`
- first follow-up residual addition class = `changed_inactive_only`
- first follow-up residual added new task-set count = `1`
- first follow-up residual active-support-changing count = `0`
- post-first-negative RMP objective delta = `-40.33852`
- post-first-negative dual L1 delta = `400.061096`
- terminal class includes profile-DP incomplete signal.

### Apollo20 auto-active validation row

- worker added journeys = `1`
- worker support-changing = `1`
- worker addition class = `active_replacement_task_set`
- first follow-up residual = `5,8,15`
- bridge class = `profile_returned_residual_exact`
- tail class = `returned_residual_then_new_negative_family`
- follow-up negative sequence = `5,8,15|5,12,18|4,8,12`
- unique follow-up negative task sets = `3`
- first follow-up residual addition class = `changed_inactive_only`
- first follow-up residual added new task-set count = `1`
- first follow-up residual active-support-changing count = `0`
- post-first-negative RMP objective delta = `-139.913748`
- post-first-negative dual L1 delta = `139.913748`

### Tranq20

- worker 未触发；
- tail class = `no_worker_add`；
- pivot signal 仍为 `rmp_fractional_active_pressure`。

## 判断

Phase 9B 进一步收窄了问题：

- profile-DP 已经 returned residual；
- first follow-up residual 能加入 RMP；
- first follow-up residual 是 new task-set，但不是 active-support-changing；
- 加入后 objective / dual 会移动；
- 但后续会继续出现新的 negative task-set family。

这说明当前 hard-tail 更像：

- residual family 连续再生；
- new task-set columns 多为 inactive / weak impact；
- RMP / dual movement 未能稳定消除后续 negative families；
- final judge / profile-DP proof tail 不是因为 first residual 看不见或 materialize 失败。

因此下一步不应做：

- profile-DP selected/materialization bridge 修补；
- Pulse worker target-specific tuning；
- 简单加 worker / pricing time limit。

## Exactness 边界

- 只新增 summary 归因字段；
- 不改变 pricing；
- 不改变 RMP；
- 不改变 worker trigger；
- 不改变 official lower bound；
- 不改变 certificate path；
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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_proof_tail_bridge_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 3 tests in 0.002s
OK
```

完整回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 480 tests in 1.448s
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
--output-dir BPC_future/results/sharded_pulse_phase9b_returned_residual_tail_attribution_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9b_returned_residual_tail_attribution \
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

进入 Phase 9C：RMP residual impact / active-support attribution。

Phase 9C 应只做只读诊断：

- 对每个 follow-up returned residual column，记录是否进入 active support；
- 记录加入后下一轮 active value、task-set value、fractional status；
- 统计 residual family 加列后 objective delta 与后续 new negative family 的关系；
- 判断是否是 inactive-new-column tail / active fractional tail / dual degeneracy tail。

仍然不要做：

- production worker 默认开启；
- official certificate gate；
- resume / parallel；
- 20/100 A/B；
- 简单增大 worker 或 pricing time limit。
