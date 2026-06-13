# Sharded Pulse Phase 10F Active-pool Trajectory Attribution 报告

日期：2026-06-13

## 目标

Phase 10F 只做 active-pool / early trajectory attribution。

本轮目标不是继续调 profile-DP label cap，也不是启用 Pulse worker 或 certificate gate，而是回答 Phase 10E 留下的问题：

- `mt20_greedy_apollo_01` 的 short-time incumbent 分叉是否更像 active-pool trajectory / early column ordering，而不是 profile-DP top-mask hotspot；
- label-cap16/32 是否有稳定 ROI；
- 20-task hard smoke 中的 active basis 是否能解释改善/扰动。

## 实现摘要

### 1. ROI summary 新增 active-pool trajectory 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中，`_pool_structure_metrics()` 现在额外汇总：

- `pool_active_task_set_hash_first`
- `pool_active_task_set_hash_sequence`
- `pool_active_task_set_hash_unique_count`
- `pool_active_task_set_hash_churn_count`
- `pool_active_top_task_set_value_samples_first`
- `pool_active_trajectory_class`
- `pool_active_trajectory_reason`

这些字段来自已有 `journey_pool_structure_diagnostics` 事件，只读归因，不改变 pricing、RMP、worker trigger、certificate 或 lower-bound 逻辑。

### 2. Active trajectory 分类

新增 `_classify_active_pool_trajectory()`：

- `no_pool_diagnostics`
- `no_active_basis`
- `stable_active_basis`
- `churn_active_basis`
- `high_churn_active_basis`

分类只用于报告，不参与任何求解决策。

### 3. 测试覆盖

补充 focused tests：

- `test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields`
  - 要求新 active trajectory summary 字段存在；
- `test_sharded_pulse_roi_calibration_pool_structure_metrics_are_summarized`
  - 验证 first/last active hash；
  - 验证 active hash sequence；
  - 验证 unique/churn count；
  - 验证 first/last active top task-set samples；
  - 验证 `churn_active_basis` 分类。

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase10f_active_pool_trajectory_attribution_smoke_20260613 \
  --instances phase7o_20_smoke \
  --profiles phase10c_profile_dp_mask_hotspot_sensitivity \
  --repeat-count 3 \
  --time-limit 3.0 \
  --pricing-time-limit 0.3 \
  --pricing-max-dp-states 1000 \
  --max-cg-iterations 8 \
  --profile-mask-diagnostics \
  --quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase10f_active_pool_trajectory_attribution_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase10f_active_pool_trajectory_attribution_smoke_20260613/summary.csv`

矩阵：

- instances:
  - `tranq20_01`
  - `mt20_greedy_apollo_01`
  - `mt20_greedy_tranq_01`
- profiles:
  - `baseline`
  - `experimental_profile_dp_mask_label_cap_16_20_only`
  - `experimental_profile_dp_mask_label_cap_32_20_only`
- repeat-count: 3
- rows: 27

## 结果

### 全局结果

| profile | rows | official pricing | critical disagreement | changed vs baseline |
|---|---:|---|---:|---:|
| baseline | 9 | 6 `INCOMPLETE_LIMIT`, 3 `FOUND_NEGATIVE` | 0 | 0 |
| label-cap16 | 9 | 6 `INCOMPLETE_LIMIT`, 3 `FOUND_NEGATIVE` | 0 | 1 |
| label-cap32 | 9 | 6 `INCOMPLETE_LIMIT`, 3 `FOUND_NEGATIVE` | 0 | 1 |

label-cap16/32 没有降低 `INCOMPLETE_LIMIT` 数量，也没有增加 `FOUND_NEGATIVE` 数量。

### Active-pool trajectory

active trajectory class：

- baseline:
  - `churn_active_basis`: 6
  - `high_churn_active_basis`: 3
- label-cap16:
  - `churn_active_basis`: 6
  - `high_churn_active_basis`: 3
- label-cap32:
  - `churn_active_basis`: 5
  - `high_churn_active_basis`: 4

实例级观察：

- `tranq20_01`
  - 三个 profiles 三次 repeat 的 incumbent 都是 `781.101309`；
  - active hash trajectory 稳定为同一条序列族；
  - label-cap16 只剪掉少量 labels，没有改变 outcome。
- `mt20_greedy_tranq_01`
  - 三个 profiles 三次 repeat 的 incumbent 都是 `761.814403`；
  - active hash trajectory 完全一致；
  - returned negative task-set 是 `[1,6,15]`，与 top-mask 只是 overlapping；
  - 本轮没有复现 Phase 10E 中 baseline repeat 2 的 `721.502279` 更好路径。
- `mt20_greedy_apollo_01`
  - baseline 三次都是 `921.640296`；
  - label-cap16/32 各有一次改善到 `847.812231`；
  - 改善行伴随 active hash trajectory 从 baseline 常见的 `12fab00b36e47734` 分叉到 `c36666e846435b59` 或 `98e14b42b7f3753c`；
  - 这些改善行没有形成 profile-DP incomplete reduction，也不是 label-cap pruning 本身稳定解释。

### Label-cap ROI

- label-cap16:
  - total `profile_dp_tail_label_cap_pruned` 在 20-task 上有明显计数；
  - 但 `INCOMPLETE_LIMIT` 没有下降；
  - 只在 `mt20_greedy_apollo_01` 一个 repeat 改善。
- label-cap32:
  - 多数行没有触发 label-cap pruning；
  - 也只在 `mt20_greedy_apollo_01` 一个 repeat 改善；
  - active basis churn 更高，不是稳定优化信号。

结论：label-cap 不是稳定主线；它更像扰动 early trajectory，而不是直接修复 profile-DP proof tail。

## 5/10 No-regression

本轮 smoke 只运行 `phase7o_20_smoke`，未重复 5/10 矩阵。

边界说明：

- 本轮 profiles 仍是 20-only calibration；
- 只新增 summary 字段与只读分类；
- 未改默认 benchmark 配置；
- 未改 driver official result 逻辑；
- 未启用 Pulse worker / certificate / lower-bound effect。

因此本轮不能作为新的 5/10 no-regression 证据，也不构成最终目标 A。

## Exactness 边界

本轮没有改变：

- pricing universe；
- profile-DP transition / pruning；
- TimedTrip / JourneyColumn materialization；
- RMP insertion；
- Pulse worker trigger；
- Sharded Pulse certificate；
- official dual bound；
- completion-bound certificate；
- cut / branch / forbidden context 语义。

所有新增字段均为 JSONL / summary 只读归因。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pool_structure_metrics_are_summarized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
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
Ran 482 tests in 1.456s
OK (skipped=1)
```

diff whitespace 检查：

```bash
git diff --check
```

结果：通过。

## 结论

Phase 10F 支持以下判断：

1. profile-DP top-mask / label-cap hotspot 不是当前最稳的优化主线；
2. label-cap 可以改变 early trajectory，但不能稳定降低 incomplete 或改善 hard-tail；
3. `mt20_greedy_apollo_01` 的改善更像 active-pool trajectory 分叉，而不是 profile-DP bucket width 被修好；
4. `mt20_greedy_tranq_01` 和 `tranq20_01` 的 active trajectory 在本轮 profiles 下基本稳定，因此 label-cap 对它们没有 ROI；
5. 不应打开 worker default 或 official certificate gate。

## 下一步建议

下一步应进入 Phase 10G：early-column / active-pool trajectory controlled intervention design。

建议不要再扩大 label-cap；而是做只读或极窄 experimental 的 early trajectory 对照：

- 记录 early added-column order 与 active hash transition；
- 比较改善行的 active task-set families 是否可由初始列池或 early profile-DP return order 复现；
- 若做 intervention，只允许 calibration profile，不允许 certificate effect；
- 继续保持 5/10 no-regression gate 和 20 selected hard set repeat 验证。
