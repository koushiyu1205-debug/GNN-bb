# Sharded Pulse Phase 9J RMP/Dual Stabilization Repeat A/B 报告

日期：2026-06-13

## 目标

Phase 9J 只验证 Phase 9I 的 dual-stabilization 短 smoke 信号是否能在重复、稍长 A/B 中复现。

本轮目标不是 production tuning，也不是 official certificate gate。核心问题是：

1. `experimental_l1_previous_dual_stabilization_20_only` / `experimental_l1_zero_dual_stabilization_20_only` 是否继续通过 current-pool dual feasibility 与 objective-match guard；
2. 5/10 是否仍然 no-op / no-regression；
3. 20-task 的 primal / pricing-state 改善是否稳定，而不是单次短 smoke 偶然结果。

## 实现摘要

### 1. Calibration repeat 支持

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增：

- `--repeat-count`
- `repeat_index` summary 字段
- repeat-aware log path：
  - 单次时保持旧格式：`instance__profile.jsonl`
  - 多次时写成：`instance__profile__r<repeat_index>.jsonl`

baseline 对比按 `(instance, repeat_index)` 隔离，避免 repeat 之间互相污染。

### 2. Phase 9J profile group

新增 profile group：

- `phase9j_rmp_dual_stabilization_repeat_ab`

展开为：

- `baseline`
- `experimental_l1_previous_dual_stabilization_20_only`
- `experimental_l1_zero_dual_stabilization_20_only`

两个实验 profile 仍然是 20-task only，5/10 下 no-op。

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_smoke_20260613 \
--instances apollo5 tranq5 apollo10 tranq10_09 mt20_greedy_apollo_01 tranq20_01 \
--profiles phase9j_rmp_dual_stabilization_repeat_ab \
--repeat-count 2 \
--time-limit 2.4 \
--pricing-time-limit 0.25 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 6 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9j_rmp_dual_stabilization_repeat_ab_smoke_20260613/summary.csv`

矩阵规模：

- 6 个实例；
- 3 个 profiles；
- repeat count = 2；
- 共 36 行 summary。

## 关键结果

### 5/10 Guard

`apollo5`、`tranq5`、`apollo10`、`tranq10_09`：

- experimental profiles 下 `dual_stabilization_events=0`；
- official result 与同 repeat baseline 一致；
- critical disagreement = `0`；
- improvement class = `no_regression`。

聚合平均 wall time：

| scale | baseline | previous-anchor | zero-anchor |
|---:|---:|---:|---:|
| 5 | `0.049453` | `0.047097` | `0.050620` |
| 10 | `1.258583` | `1.256167` | `1.256209` |

解释：本轮 5/10 仍符合 no-op guard，没有因为 20-only profile 触发 stabilization。

### Apollo20 greedy-anchor

实例：`mt20_greedy_apollo_01`

previous-anchor：

- 两次 repeat 均 accepted stabilized dual `1` 次；
- 两次 repeat official result 都与 baseline 一致；
- 未观察到求解改善。

zero-anchor：

- repeat 0：
  - accepted `2` 次；
  - primal 从 `921.640296` 改善到 `848.242536`；
  - `improvement_class=improved`。
- repeat 1：
  - accepted `1` 次；
  - primal 仍为 `921.640296`；
  - `improvement_class=no_regression`。

解释：zero-anchor 在 Apollo20 上出现一次明显改善，但未在第二次 repeat 稳定复现。

### Tranq20

实例：`tranq20_01`

previous-anchor：

- repeat 0：
  - accepted `4` 次；
  - primal 与 baseline 一致：`781.398505`；
  - `improvement_class=no_regression`。
- repeat 1：
  - accepted `3` 次；
  - primal 从 `781.398505` 改善到 `781.101309`；
  - `improvement_class=improved`。

zero-anchor：

- repeat 0：
  - accepted `6` 次；
  - official pricing state 从 `INCOMPLETE_LIMIT` 变为 `FOUND_NEGATIVE`；
  - primal 与 baseline 一致；
  - wall time 增加，`improvement_class=worsened`。
- repeat 1：
  - accepted `5` 次；
  - primal 从 `781.398505` 改善到 `781.101309`；
  - `improvement_class=improved`。

解释：Tranq20 上 stabilized dual 能稳定 accepted，但 zero-anchor 的效果不稳定：一次改善，一次因 wall/pricing path 判为 worsened。

### Exactness Guards

所有 20-task accepted stabilized dual event 均满足：

- `dual_stabilization_current_pool_negative_count_max=0`；
- `dual_stabilization_objective_mismatch_count=0`；
- `dual_stabilization_current_pool_infeasible_count=0`；
- `critical_disagreement_count=0`。

## ROI 判断

Phase 9J 结论是：

- dual stabilization 机制安全边界仍成立；
- 5/10 no-regression guard 仍成立；
- 20-task 有真实正向信号，但不稳定；
- zero-anchor 不能直接进入 production tuning；
- previous-anchor 更稳定但改善较弱。

因此当前还不能满足最终目标 A 的 20-task 明显稳定改善，也不能宣称性能已提升。

## 当前边界

- 不改变 production default；
- 不启用 Sharded Pulse worker / certificate；
- 不新增 official certificate gate；
- stabilized dual 仍禁用于 certificate candidate；
- accepted stabilized dual 必须通过 objective-match 和 current-pool feasibility guard；
- 本轮只是 repeat A/B，不是 20-task selected hard set 的正式结论。

## 下一步建议

下一步不应回到扩大 Pulse worker。

建议 Phase 9K：

- 保留 previous-anchor / zero-anchor；
- 增加 longer time-limit / max-CG 对照；
- 扩大 20-task selected hard set；
- 加入更多 repeat；
- 用稳定性标准筛选：
  - 5/10 no-regression；
  - 20-task 至少两个 hard cases 重复改善；
  - accepted stabilized dual 无 exactness guard failure；
  - wall time / primal / pricing-state 改善方向一致。

如果 Phase 9K 仍然是偶发改善、平均 wall 变差或只改变 pricing path，则应停止 dual-stabilization production 推进，转向 legacy final judge / profile-DP proof-tail optimization。

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
Ran 481 tests in 1.436s
OK (skipped=1)
```

Whitespace 检查：

```bash
git diff --check
```

结果：通过。
