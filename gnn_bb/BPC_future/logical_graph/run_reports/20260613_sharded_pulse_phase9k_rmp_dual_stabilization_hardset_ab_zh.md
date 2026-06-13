# Sharded Pulse Phase 9K RMP/Dual Stabilization Hardset A/B 报告

日期：2026-06-13

## 目标

Phase 9K 继续沿 Phase 9J 的结论推进：扩大 repeat、加入更多 selected 20-task hard smoke、稍加长 time limit，判断 dual stabilization 是否有稳定 ROI。

本轮仍然不做：

- production default；
- official certificate gate；
- Sharded Pulse worker / proof path；
- 20/100 大矩阵；
- resume / parallel。

## 实现摘要

### 1. 新增 Phase 9K aliases

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增：

- `INSTANCE_GROUPS["phase9k_dual_stabilization_gate"]`
- `PROFILE_GROUPS["phase9k_rmp_dual_stabilization_hardset_ab"]`

实例组：

- `apollo5`
- `tranq5`
- `apollo10`
- `tranq10_09`
- `tranq10_04`
- `mt20_greedy_apollo_01`
- `tranq20_01`
- `mt20_greedy_tranq_01`

profile group：

- `baseline`
- `experimental_l1_previous_dual_stabilization_20_only`
- `experimental_l1_zero_dual_stabilization_20_only`

两个实验 profile 仍然只在 20-task 生效，5/10 下 no-op。

### 2. 修正 ROI 分类口径

Phase 9K 解析时发现旧 `_classify_improvement()` 存在一个报告层风险：

- 20-task 非 OPTIMAL / TIME_LIMIT 下，如果 incumbent primal 变差但 wall time 更短，旧逻辑可能判为 `improved`。

这违反 `目标.md` 的要求：

- 不允许仅靠 timeout / 少算 final judge 制造“加速”假象。

本轮修正：

- 当 scale >= 20 且 baseline / row 同为非 OPTIMAL 状态时；
- 若 row primal 明显高于 baseline primal；
- 直接判为 `worsened`，即使 wall time 更短。

新增测试覆盖该回归。

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase9k_rmp_dual_stabilization_hardset_ab_smoke_20260613 \
--instances phase9k_dual_stabilization_gate \
--profiles phase9k_rmp_dual_stabilization_hardset_ab \
--repeat-count 3 \
--time-limit 3.0 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 8 \
--current-probe-time-limit 0.8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase9k_rmp_dual_stabilization_hardset_ab_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase9k_rmp_dual_stabilization_hardset_ab_smoke_20260613/summary.csv`

矩阵规模：

- 8 个实例；
- 3 个 profiles；
- repeat count = 3；
- 共 72 行 summary。

## 关键结果

### 5-task Regression Gate

聚合：

| profile | rows | avg wall | changed | accepted stabilized dual |
|---|---:|---:|---:|---:|
| baseline | 6 | `0.052978` | 0 | 0 |
| previous-anchor | 6 | `0.051824` | 0 | 0 |
| zero-anchor | 6 | `0.050409` | 0 | 0 |

结论：

- 5-task 下实验 profiles 仍然 no-op；
- no critical disagreement；
- no official result change。

### 10-task Regression Gate

聚合：

| profile | rows | avg wall | changed | accepted stabilized dual |
|---|---:|---:|---:|---:|
| baseline | 9 | `1.968252` | 0 | 0 |
| previous-anchor | 9 | `1.969527` | 0 | 0 |
| zero-anchor | 9 | `1.968997` | 0 | 0 |

结论：

- 10-task 下实验 profiles 仍然 no-op；
- no critical disagreement；
- no official result change；
- 平均 wall 变化约为 0.1% 以内。

### 20-task Hardset

聚合：

| profile | rows | avg wall | changed | improved | worsened | no-regression | accepted |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 9 | `1.708104` | 0 | 0 | 0 | 0 | 0 |
| previous-anchor | 9 | `1.746792` | 5 | 6 | 2 | 1 | 35 |
| zero-anchor | 9 | `1.997108` | 1 | 0 | 5 | 4 | 42 |

所有 20-task accepted stabilized dual event 均满足：

- `dual_stabilization_current_pool_negative_count_max=0`
- `dual_stabilization_objective_mismatch_count=0`
- `dual_stabilization_current_pool_infeasible_count=0`
- `critical_disagreement_count=0`

#### mt20_greedy_apollo_01

previous-anchor：

- repeat 0：no-regression；
- repeat 1：primal `921.640296 -> 848.203168`，improved；
- repeat 2：primal `847.812231 -> 909.373291`，worsened；
- 结论：不稳定。

zero-anchor：

- repeat 0：no-regression；
- repeat 1 / 2：worsened；
- 结论：不支持继续。

#### tranq20_01

previous-anchor：

- repeat 0：worsened；
- repeat 1 / 2：improved by wall without primal change；
- 结论：混合信号，不稳定。

zero-anchor：

- repeat 0 / 1 / 2：全部 worsened；
- 结论：应停止作为候选 profile。

#### mt20_greedy_tranq_01

previous-anchor：

- 3 次 repeat 全部 improved；
- primal 稳定从 `761.814403` 改善到 `721.502279`；
- accepted stabilized dual 每次 `7`；
- pricing state 保持 `FOUND_NEGATIVE`；
- wall time 略高于 baseline，但 incumbent 改善稳定。

zero-anchor：

- 3 次 repeat 全部 no-regression；
- primal 不变；
- wall time 略高；
- 结论：没有 ROI。

## ROI 判断

Phase 9K 比 Phase 9J 提供了更强证据：

- previous-anchor 在 `mt20_greedy_tranq_01` 上有重复稳定的 20-task incumbent 改善；
- previous-anchor 在其他 20-task 上仍混合；
- zero-anchor 在 hardset 上基本失败，应降级或停止；
- 5/10 no-regression gate 仍成立；
- exactness guard 未失败。

但当前仍不足以满足最终 A：

- 20-task 改善尚未覆盖 selected hard set；
- previous-anchor 不是所有 20-task 都稳定；
- 还没有证明 wall time / final judge tail / gap 在更大 hardset 上稳定改善；
- 5/10 仍只是代表性 no-op gate，不是全量 gate。

## 当前边界

- 不改变 default config；
- 不启用 Pulse worker；
- 不启用 certificate gate；
- stabilized dual 禁用于 certificate candidate；
- accepted stabilized dual 必须通过 current-pool feasibility / objective-match guard；
- non-OPTIMAL 下 incumbent 变差即使更快也不再判为 improved。

## 下一步建议

建议 Phase 9L：

1. 保留 `experimental_l1_previous_dual_stabilization_20_only`；
2. 暂停 `zero` anchor 作为候选；
3. 对 previous-anchor 做更严格 20-task selected hardset A/B：
   - repeat >= 5；
   - 加入更多 20-task；
   - 单独报告 wall / primal / pricing state / retry / final judge tail；
4. 同时跑更完整 5/10 no-regression gate；
5. 若 previous-anchor 仍只在单个 hard case 改善，应停止 production tuning，转向 legacy final judge / profile-DP proof-tail。

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
Ran 481 tests in 1.424s
OK (skipped=1)
```

Whitespace 检查：

```bash
git diff --check
```

结果：通过。
