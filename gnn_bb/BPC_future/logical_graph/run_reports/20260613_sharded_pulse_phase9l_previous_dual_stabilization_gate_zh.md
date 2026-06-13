# Sharded Pulse Phase 9L Previous-anchor Dual Stabilization Gate 报告

日期：2026-06-13

## 目标

Phase 9L 只保留 Phase 9K 中唯一还有验证价值的 previous-anchor dual stabilization，扩大 5/10 regression gate，并继续用 selected 20-task hard smoke 判断 ROI 是否稳定。

本轮不再测试 zero-anchor，因为 Phase 9K 中 zero-anchor 在 20-task 上 `improved=0`、`worsened=5`。

本轮仍不做：

- production default；
- official certificate gate；
- Sharded Pulse worker / proof path；
- resume / parallel；
- 20/100 大矩阵。

## 实现摘要

### 1. 新增 Phase 9L aliases

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增：

- `INSTANCE_GROUPS["phase9l_previous_dual_stabilization_gate"]`
- `PROFILE_GROUPS["phase9l_previous_dual_stabilization_gate_ab"]`

实例组包含：

- `balanced5_all` 全量 20 个 5-task；
- `balanced10_all` 全量 20 个 10-task；
- `phase7o_20_smoke` 的 3 个可跑 20-task hard smoke：
  - `tranq20_01`
  - `mt20_greedy_apollo_01`
  - `mt20_greedy_tranq_01`

profile group 只包含：

- `baseline`
- `experimental_l1_previous_dual_stabilization_20_only`

说明：旧 `apollo20_01` 之前已有 single-task feasibility preflight 失败记录，本轮仍不纳入默认 hardset，避免把实例/grid 问题误判为算法问题。

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9l_previous_dual_stabilization_gate_ab_smoke_20260613 \
--instances phase9l_previous_dual_stabilization_gate \
--profiles phase9l_previous_dual_stabilization_gate_ab \
--repeat-count 2 \
--time-limit 3.0 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 8 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9l_previous_dual_stabilization_gate_ab_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9l_previous_dual_stabilization_gate_ab_smoke_20260613/summary.csv`

矩阵规模：

- 43 个实例；
- 2 个 profiles；
- repeat count = 2；
- 共 172 行 summary。

## 5-task Regression Gate

聚合：

| profile | rows | avg wall | max wall | changed | accepted |
|---|---:|---:|---:|---:|---:|
| baseline | 40 | `0.042747` | `0.057458` | 0 | 0 |
| previous-anchor | 40 | `0.042789` | `0.057629` | 0 | 0 |

结果：

- experimental profile 在 5-task 下 no-op；
- `dual_stabilization_events=0`；
- official result 与 baseline 一致；
- no critical disagreement；
- 平均 wall 只增加约 `0.000042s`。

说明：该 smoke 的 5-task 由于短 time limit 显示为 `TIME_LIMIT`，因此这里只能证明 profile no-op / no-regression，不能作为最终 5-task OPTIMAL gate。

## 10-task Regression Gate

聚合：

| profile | rows | avg wall | max wall | changed | accepted |
|---|---:|---:|---:|---:|---:|
| baseline | 40 | `1.937340` | `2.003631` | 0 | 0 |
| previous-anchor | 40 | `1.938006` | `2.006113` | 0 | 0 |

结果：

- experimental profile 在 10-task 下 no-op；
- `dual_stabilization_events=0`；
- official result 与 baseline 一致；
- pricing state 分布一致：
  - baseline: `FOUND_NEGATIVE=38`、`INCOMPLETE_LIMIT=2`
  - previous-anchor: `FOUND_NEGATIVE=38`、`INCOMPLETE_LIMIT=2`
- no critical disagreement；
- 平均 wall 增加约 `0.000665s`。

说明：该 smoke 的 10-task 仍是短 time limit gate，不是最终 full optimality benchmark。

## 20-task Hard Smoke

聚合：

| profile | rows | avg wall | changed | improved | worsened | accepted |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 6 | `1.829656` | 0 | 0 | 0 | 0 |
| previous-anchor | 6 | `1.763805` | 4 | 4 | 2 | 24 |

所有 20-task accepted stabilized dual event 均满足：

- `dual_stabilization_current_pool_negative_count_max=0`
- `dual_stabilization_objective_mismatch_count=0`
- `dual_stabilization_current_pool_infeasible_count=0`
- `critical_disagreement_count=0`

### tranq20_01

- repeat 0：
  - baseline primal `781.101309`
  - previous-anchor primal `760.460385`
  - `improvement_class=improved`
  - wall 从 `1.434847` 增至 `1.836596`
- repeat 1：
  - primal 不变 `781.101309`
  - wall 从 `1.429264` 增至 `1.807657`
  - `improvement_class=worsened`

结论：混合信号。

### mt20_greedy_apollo_01

- repeat 0：
  - baseline primal `847.812231`
  - previous-anchor primal `921.640296`
  - `improvement_class=worsened`
- repeat 1：
  - primal 不变 `921.640296`
  - wall 从 `1.315609` 降至 `0.983060`
  - `improvement_class=improved`

结论：混合信号。

### mt20_greedy_tranq_01

- repeat 0 / 1 均稳定改善：
  - baseline primal `761.814403`
  - previous-anchor primal `721.502279`
  - `improvement_class=improved`
- wall 略增：
  - repeat 0: `2.416887 -> 2.484304`
  - repeat 1: `2.415111 -> 2.488317`

结论：这是当前 previous-anchor 最稳定的正向 hard case。

## ROI 判断

Phase 9L 结论：

- previous-anchor 在 full 5/10 smoke gate 下保持 no-op / no-regression；
- previous-anchor 在 20-task selected hard smoke 中仍有真实正向信号；
- 但 20-task 结果仍然 mixed：
  - `mt20_greedy_tranq_01` 稳定改善；
  - `tranq20_01` 一次 improved、一次 worsened；
  - `mt20_greedy_apollo_01` 一次 improved、一次 worsened。

因此 previous-anchor 仍不能进入 production tuning，也不能满足最终目标 A。

按照 `目标.md` 的 Phase 9K 后续判断：

- previous-anchor 仍只在单个 hard case 上稳定改善；
- selected 20-task hard smoke 仍有 worsened；
- 应停止 dual-stabilization production 推进；
- 下一步应转向 legacy final judge / profile-DP proof-tail optimization。

## Exactness 边界

- 不改变 default config；
- 不启用 Pulse worker；
- 不启用 certificate gate；
- stabilized dual 禁用于 certificate candidate；
- accepted stabilized dual 必须通过 current-pool feasibility / objective-match guard；
- no critical disagreement；
- no official lower-bound rule relaxed。

## 下一步建议

建议 Phase 10A：

- 停止继续扩大 dual-stabilization production profiles；
- 保留 previous-anchor 作为 diagnostic / research knob；
- 转向 legacy final judge / profile-DP proof-tail optimization；
- 优先目标：
  - 分析 `FOUND_NEGATIVE` / `INCOMPLETE_LIMIT` tail 下 profile-DP 与 direct final judge 的切换；
  - 降低 final judge tail time 或 retry；
  - 保持 5/10 full gate；
  - 不引入任何非 true-dual certificate。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_dual_stabilization_metrics_are_summarized
```

结果：

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

全量 `BPCFutureTests`：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 481 tests in 1.432s
OK (skipped=1)
```

Whitespace 检查：

```bash
git diff --check
```

结果：通过。
