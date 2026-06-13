# Sharded Pulse Phase 9I RMP/Dual Stabilization A/B Smoke 报告

日期：2026-06-13

## 目标

Phase 9I 只做极窄的 RMP/dual stabilization opt-in A/B smoke。

本轮目标不是开启 production stabilization，也不是 official certificate gate，而是验证：

1. 现有 `journey_dual_stabilization` 机制能否在 20-task 短 smoke 中实际 accepted；
2. accepted stabilized dual 是否通过 current-pool dual feasibility / objective-match guard；
3. 5/10 profile 是否保持 no-op / no-regression；
4. 20-task 是否出现值得继续调查的信号。

## 实现摘要

### 1. 新增 profile group

新增：

- `phase9i_rmp_dual_stabilization_ab`

展开为：

- `baseline`
- `experimental_l1_previous_dual_stabilization_20_only`
- `experimental_l1_zero_dual_stabilization_20_only`

两个实验 profile 都是 20-task only。5/10 下直接 no-op。

### 2. 新增 experimental dual stabilization profiles

新增 profile：

- `experimental_l1_previous_dual_stabilization_20_only`
- `experimental_l1_zero_dual_stabilization_20_only`

配置边界：

- `journey_dual_stabilization_enabled=True`
- `journey_dual_stabilization_mode=l1_reference`
- reference mode 分别为 `previous` / `zero`
- `journey_dual_stabilization_tail_only_enabled=False`
- `journey_dual_stabilization_certificate_candidate_enabled=False`
- `journey_dual_stabilization_disable_on_certificate_candidate=True`
- 不启用 Sharded Pulse audit / hidden-negative worker
- 不改变 production default

说明：第一次尝试时 tail-only gate 导致 20-task 全部 `all_skipped`，无法回答 stabilization 是否有运行信号。因此本轮最终 profile 改为 20-only 但非 tail-only，仍禁止 certificate-candidate 使用 stabilized dual。

### 3. 新增 summary 字段

新增：

- `dual_stabilization_events`
- `dual_stabilization_accepted_count`
- `dual_stabilization_skipped_count`
- `dual_stabilization_status_sequence`
- `dual_stabilization_source_sequence`
- `dual_stabilization_mode_sequence`
- `dual_stabilization_reference_sequence`
- `dual_stabilization_first_accepted_cg_iter`
- `dual_stabilization_current_pool_negative_count_max`
- `dual_stabilization_objective_mismatch_count`
- `dual_stabilization_current_pool_infeasible_count`
- `dual_stabilization_time`
- `dual_stabilization_effect_class`

并新增 helper：

- `_dual_stabilization_metrics()`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9i_rmp_dual_stabilization_ab_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9i_rmp_dual_stabilization_ab \
--time-limit 1.8 \
--pricing-time-limit 0.2 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 4 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9i_rmp_dual_stabilization_ab_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9i_rmp_dual_stabilization_ab_smoke_20260613/summary.csv`

## 关键结果

### 5/10 Guard

`apollo5`、`tranq5`、`apollo10`、`tranq10_09`：

- experimental profiles 下 `dual_stabilization_events=0`；
- official result 与 baseline 一致；
- critical disagreement = `False`；
- improvement class = `no_regression`。

### Apollo20 greedy-anchor

实例：`mt20_greedy_apollo_01`

baseline：

- official status = `TIME_LIMIT`
- official pricing state = `INCOMPLETE_LIMIT`
- primal = `921.640296`
- dual bound = `None`

`experimental_l1_previous_dual_stabilization_20_only`：

- `dual_stabilization_events=4`
- `dual_stabilization_accepted_count=2`
- `dual_stabilization_source_sequence=scip|stabilized|scip|stabilized`
- `current_pool_negative_count_max=0`
- `objective_mismatch_count=0`
- `current_pool_infeasible_count=0`
- official result 与 baseline 一致

`experimental_l1_zero_dual_stabilization_20_only`：

- `dual_stabilization_events=4`
- `dual_stabilization_accepted_count=2`
- `dual_stabilization_source_sequence=scip|stabilized|scip|stabilized`
- `current_pool_negative_count_max=0`
- `objective_mismatch_count=0`
- `current_pool_infeasible_count=0`
- official result 与 baseline 一致

解释：Apollo20 上 stabilization 能 accepted，但短 smoke 没看到求解状态改善。

### Tranq20

实例：`tranq20_01`

baseline：

- official status = `TIME_LIMIT`
- official pricing state = `INCOMPLETE_LIMIT`
- primal = `783.715884`
- dual bound = `None`

`experimental_l1_previous_dual_stabilization_20_only`：

- `dual_stabilization_events=4`
- `dual_stabilization_accepted_count=4`
- `dual_stabilization_source_sequence=stabilized|stabilized|stabilized|stabilized`
- `current_pool_negative_count_max=0`
- `objective_mismatch_count=0`
- `current_pool_infeasible_count=0`
- official pricing state = `FOUND_NEGATIVE`
- primal unchanged = `783.715884`

`experimental_l1_zero_dual_stabilization_20_only`：

- `dual_stabilization_events=4`
- `dual_stabilization_accepted_count=4`
- `dual_stabilization_source_sequence=stabilized|stabilized|stabilized|stabilized`
- `current_pool_negative_count_max=0`
- `objective_mismatch_count=0`
- `current_pool_infeasible_count=0`
- official pricing state = `FOUND_NEGATIVE`
- primal improved from `783.715884` to `781.398505`

解释：Tranq20 zero-anchor 在 1.8s 短 smoke 中出现一个正向信号，但这不是稳定 ROI 结论。还需要更长/重复 A/B 验证 wall time、gap、tail、5/10 no regression 和 selected hard set consistency。

## Exactness 边界

- 本轮只新增 calibration profile / summary fields；
- 不改变 production default；
- 不启用 Sharded Pulse worker / certificate；
- 不新增 official certificate gate；
- stabilized dual 只有在 solver 现有 guard 下 accepted：
  - dual objective matches RMP objective；
  - current pool has no negative reduced-cost column under selected dual；
- experimental profiles 禁止 certificate-candidate 使用 stabilized dual；
- 本轮 smoke 的正向信号不能外推为 20-task 生产性能提升。

## 当前结论

Phase 9I 说明：

- RMP/dual stabilization 方向比继续扩大 Pulse worker 更值得继续；
- 5/10 guard 在本轮 profile 下保持 no-op；
- 20-task 上 stabilized dual 能 accepted，且未出现 objective/current-pool feasibility mismatch；
- `tranq20_01` zero-anchor 有一个短 smoke primal 改善信号；
- 但当前证据仍不足以满足最终 A。

下一步建议：

- Phase 9J：对 `experimental_l1_zero_dual_stabilization_20_only` 做重复/稍长 A/B；
- 同时保留 `previous` anchor 作为对照；
- 继续报告 5/10 no-regression；
- 不做 production default；
- 不做 official certificate gate；
- 不回到扩大 Pulse worker 主线。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_dual_stabilization_metrics_are_summarized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 5 tests in 0.003s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

全量 `BPCFutureTests`：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 481 tests in 1.444s
OK (skipped=1)
```

Whitespace 检查：

```bash
git diff --check
```

结果：通过。
