# Sharded Pulse Phase 10G Early-column / Active-pool Attribution 报告

日期：2026-06-13

## 目标

Phase 10G 继续 Phase 10F 的 active-pool 归因，但进一步追踪 early column addition。

本轮只回答一个问题：

早期加列是否会先以 inactive column 进入 pool，然后在下一轮或后续 RMP 中改变 active basis trajectory，从而导致 20-task short-time incumbent 分叉？

本轮不做：

- Pulse worker default；
- official certificate gate；
- profile-DP / Pulse pruning 改动；
- RMP 求解逻辑改动；
- 5/10/20 production A/B；
- 任何 lower-bound 或 certificate 语义变化。

## 实现摘要

### 1. 新增 early-column trajectory summary

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中新增 `_early_column_trajectory_metrics()`，只从已有 JSONL 事件还原：

- `journey_column_addition`
- `journey_pool_structure_diagnostics`

新增 summary 字段：

- `early_column_addition_events`
- `early_column_addition_kind_sequence`
- `early_column_primary_task_set_sequence`
- `early_column_changed_task_set_hash_sequence`
- `early_column_new_task_set_hash_sequence`
- `early_column_productivity_class_sequence`
- `early_column_active_hash_before_sequence`
- `early_column_active_hash_after_sequence`
- `early_column_active_hash_transition_count`
- `early_column_changed_active_relation_before_sequence`
- `early_column_changed_active_relation_after_sequence`
- `early_column_active_changed_task_set_count`
- `early_column_trajectory_class`
- `early_column_trajectory_reason`

这些字段只读汇总，不参与任何求解决策。

### 2. Trajectory 分类

新增 `_classify_early_column_trajectory()`：

- `no_early_additions`
- `active_support_changing_additions`
- `inactive_addition_enters_active_basis`
- `inactive_additions_with_active_basis_transition`
- `inactive_additions_no_active_basis_transition`

当前重点是区分：

- 加列时就改变 active support；
- 加列时 inactive，但后续 active basis 中出现该 task-set；
- 加列后 active basis hash 改变但样本中未看到 exact task-set；
- 加列后 active basis 未变。

### 3. 测试覆盖

新增 focused test：

- `test_sharded_pulse_roi_calibration_early_column_trajectory_metrics_are_summarized`

覆盖：

- 无加列时分类为 `no_early_additions`；
- 手工 records 中 inactive 加列 `[3,4]`；
- 加列前 active samples 与 `[3,4]` disjoint；
- 加列后 active samples exact 包含 `[3,4]`；
- 分类为 `inactive_addition_enters_active_basis`。

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase10g_early_column_active_pool_attribution_smoke_20260613 \
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

- `BPC_future/results/sharded_pulse_phase10g_early_column_active_pool_attribution_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase10g_early_column_active_pool_attribution_smoke_20260613/summary.csv`

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

- 27 行全部无 critical disagreement；
- baseline:
  - 6 `INCOMPLETE_LIMIT`
  - 3 `FOUND_NEGATIVE`
- label-cap16:
  - 6 `INCOMPLETE_LIMIT`
  - 3 `FOUND_NEGATIVE`
  - official result changed vs same-repeat baseline: 0
- label-cap32:
  - 6 `INCOMPLETE_LIMIT`
  - 3 `FOUND_NEGATIVE`
  - official result changed vs same-repeat baseline: 2

### Early-column trajectory

全部 27 行的 `early_column_trajectory_class` 都是：

```text
inactive_addition_enters_active_basis
```

含义：

- early `journey_column_addition` 记录中 `active_changed_task_set_count=0`；
- 加列当下主要是 inactive changed/new task-set；
- 但后续 `journey_pool_structure_diagnostics` 的 active top samples 中出现了该 task-set；
- 因此 active-basis 分叉不是“加列立即 active”，而是“inactive column 进入 pool 后，在后续 RMP 中成为 active basis 的一部分”。

### 实例观察

#### `tranq20_01`

- 三个 profiles、三次 repeat 的 incumbent 都是 `781.101309`；
- early task-set sequence 稳定：
  - `[5,15,20]`
  - `[4,13,18]`
  - `[4,6,13]`
- active hash transition count = 2；
- label-cap 不改变 outcome。

#### `mt20_greedy_tranq_01`

- 三个 profiles、三次 repeat 的 incumbent 都是 `761.814403`；
- early task-set sequence 完全一致：
  - `[8,10,13]`
  - `[2,7,10,17]`
  - `[2,7,9,17]`
  - `[3,4]`
  - `[8,12]`
  - `[13,16]`
  - `[2,7,9]`
  - `[1,6,15]`
- active hash transition count = 5；
- label-cap 不改变 outcome。

#### `mt20_greedy_apollo_01`

- short-time trajectory 仍然高度敏感；
- baseline 本轮已有 1 个 repeat 到 `847.812231`；
- label-cap32 有 2 行 changed vs baseline：
  - repeat 1: `921.640296 -> 847.812231`
  - repeat 2: `921.640296 -> 773.85915`
- 改善行的 early sequence 包含更长的 inactive-to-active 链：
  - `[5,8,15]`
  - `[5,12,18]`
  - `[12,16,17]`
  - `[4,5,8]`
  - `[4,8,15]`
  - repeat 2 进一步出现 `[5,14,18]`
- active hash path 从 `c6ea96127d7c5d7b -> 12fab00b36e47734` 继续分叉到：
  - `c36666e846435b59`
  - `98e14b42b7f3753c`
  - `c9dd1125cc1bf8fa`

## 解释

Phase 10G 支持以下判断：

1. 当前 20-task short-time 分叉不是“active-support-changing column 立即生效”；
2. 更像 inactive new/changed column 进入 pool 后，在后续 RMP 中改变 active basis；
3. label-cap32 能扰动 Apollo early trajectory，但不稳定，也没有降低 `INCOMPLETE_LIMIT`；
4. `tranq20_01` 与 `mt20_greedy_tranq_01` 的 early sequence 在本轮 profiles 下稳定，因此 label-cap 对它们没有 ROI；
5. 继续调 label-cap 不值得作为主线。

## 5/10 No-regression

本轮 smoke 仍只运行 `phase7o_20_smoke`。

边界说明：

- 本轮是只读 summary 字段；
- profiles 是 20-only calibration；
- 没改默认 benchmark 配置；
- 没改求解路径；
- 没改 driver official result；
- 因此本轮不能作为新的 5/10 no-regression 证据。

## Exactness 边界

本轮没有改变：

- pricing universe；
- profile-DP transition / pruning；
- Pulse worker；
- RMP insertion；
- branch / cut / forbidden context；
- official lower bound；
- certificate inference；
- completion-bound final judge。

所有新增字段均为离线 summary / report attribution。

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_early_column_trajectory_metrics_are_summarized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
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
Ran 483 tests in 1.430s
OK (skipped=1)
```

diff whitespace 检查：

```bash
git diff --check
```

结果：通过。

## 结论

Phase 10G 进一步收紧了 Phase 10F 的判断：

- label-cap 不是稳定 proof-tail 优化；
- Apollo 的改善来自 early inactive column 后续进入 active basis 的轨迹分叉；
- 这仍然只是 short-time trajectory effect，不是稳定求解加速；
- 不应打开 Pulse worker default；
- 不应打开 official certificate gate；
- 不应继续扩大 label-cap。

## 下一步建议

进入 Phase 10H：early-column controlled intervention / negative-result split。

候选路线：

1. 只读路线：
   - 继续记录每个 early addition 的 true RC、pricing kind、task-set size、后续 active persistence；
   - 判断好路径是否由少数 recurring early task-set family 触发。
2. 极窄 experimental 路线：
   - 只在 20-only calibration profile 中把 Apollo 改善路径中的 early task-set family 提前加入或提高排序；
   - 不允许 certificate effect；
   - 必须跑 5/10 no-op gate 后才能评价。
3. negative-result 路线：
   - 若 early intervention 仍不稳定，停止 profile-DP / worker / label-cap 主线；
   - 输出 negative-result synthesis，转向 legacy final judge proof-tail 或 RMP degeneracy/column-pool stabilization。
