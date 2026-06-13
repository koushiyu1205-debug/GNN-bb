# Sharded Pulse Phase 8A ROI Pivot Classifier 报告

日期：2026-06-13

## 目标

Phase 7AH 已关闭 active Pulse worker gate-stacking 子路线。Phase 8A 的目标是给 ROI summary 增加一个只读 pivot classifier，让后续 A/B 结果能自动指向更合理的优化入口：

- correctness blocker；
- profile-DP state cap；
- residual disjoint negative；
- pool duplicate pressure；
- RMP fractional active pressure；
- worker column impact unclear；
- no clear signal。

本轮不改变求解路径，不改变 worker gate，不改变 certificate / official lower-bound 语义。

## 实现摘要

`BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增：

- `pivot_recommendation_class`
- `pivot_recommendation_reason`
- `_classify_pivot_recommendation()`
- `_apply_pivot_recommendation()`

分类优先级：

1. `correctness_blocker`
   - critical disagreement；
   - residual replay RC mismatch；
   - residual replay signature mismatch。
2. `profile_dp_state_cap`
   - follow-up profile-DP hit state cap。
3. `profile_dp_incomplete`
   - 其他 profile-DP incomplete class。
4. `residual_disjoint_negative`
   - worker 后首个 follow-up negative 与 worker task set disjoint。
5. `residual_overlapping_negative`
   - worker 后首个 follow-up negative 与 worker task set overlap / same。
6. `pool_duplicate_pressure`
   - duplicate task-set ratio >= 0.2 或 duplicate count > 0。
7. `rmp_fractional_active_pressure`
   - active fractional ratio >= 0.5。
8. `worker_column_impact_unclear`
   - worker 加列但没有分类出 follow-up / pool / profile-DP 瓶颈。
9. `no_clear_pivot_signal`
   - 无明确信号。

分类只写入 `summary.json` / `summary.csv`，不参与 solver 决策。

## 验证

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier
```

结果：

```text
Ran 2 tests in 0.016s
OK
```

very_small smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase8a_pivot_classifier_smoke_20260613 \
  --instances very_small \
  --profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
  --time-limit 0.5 \
  --audit-time-limit 0.05 \
  --worker-time-limit 0.05 \
  --current-probe-time-limit 0.05 \
  --pricing-time-limit 0.1 \
  --pricing-max-dp-states 200 \
  --max-cg-iterations 1 \
  --current-probe-min-tasks 20 \
  --quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase8a_pivot_classifier_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase8a_pivot_classifier_smoke_20260613/summary.csv`

smoke 字段：

```text
very_small baseline -> no_clear_pivot_signal
very_small strict_worker...failure_cooldown -> no_clear_pivot_signal
```

## Existing Summary Reclassification

把新 classifier 离线套到已有 7U / 7W / 7Z / 7AG summary 上：

| source | class counts |
|---|---|
| `phase7u_pool_diagnostics_matrix` | `no_clear_pivot_signal=9`, `rmp_fractional_active_pressure=4`, `worker_column_impact_unclear=1` |
| `phase7w_residual_tail_matrix` | `rmp_fractional_active_pressure=4`, `profile_dp_state_cap=1`, `no_clear_pivot_signal=1` |
| `phase7w_residual_tail_apollo_probe` | `residual_disjoint_negative=1`, `no_clear_pivot_signal=1` |
| `phase7z_worker_no_roi_gate_coverage` | `residual_disjoint_negative=3`, `no_clear_pivot_signal=1` |
| `phase7ag_target_arc_option_priority` | `residual_overlapping_negative=1`, `no_clear_pivot_signal=2` |

关键观察：

- pool duplicate pressure 没有成为当前主要信号；
- 20-task `tranq20_01` / `mt20_greedy_tranq_01` 更像 RMP active fractional pressure；
- `mt20_greedy_apollo_01` worker 后仍出现 residual disjoint negative；
- 部分 follow-up exact retry 命中 profile-DP state cap；
- target diagnostics 说明 active worker coverage 的局部修补已经进入过度特化。

## Pivot 判断

Phase 8A 不建议继续写 Pulse active-worker gate。

更合理的下一入口是：

1. `legacy/profile-DP proof-tail`：
   - 因为 7W matrix 中出现 `profile_dp_state_cap`；
   - 该问题比继续 target-specific Pulse ordering 更接近 final judge tail。

2. `RMP stabilization / active fractional degeneracy`：
   - 因为 20-task Tranq cases 有 `pool_active_fractional_ratio >= 0.5`；
   - pool duplicate 不是主因，不能优先做简单 duplicate compression。

3. `residual negative coverage analysis`：
   - 仅作为诊断保留，不继续做 active worker gate；
   - worker 后 residual negative 与 worker task set disjoint，说明“找更多同类 worker 列”不能解决 tail。

## Exactness 边界

- classifier 只读 JSONL-derived summary fields；
- 不影响 pricing；
- 不影响 RMP；
- 不影响 worker trigger；
- 不影响 official certificate；
- 不影响 default benchmark。

## 结论

Phase 8A 完成：ROI summary 现在能直接输出 pivot recommendation。

当前分类结果支持 Phase 7AH 的关闭结论：active Pulse worker 不应继续扩张。下一步若继续求解性能目标，应进入 `legacy/profile-DP proof-tail` 或 `RMP stabilization / active fractional degeneracy`，而不是继续为 Pulse worker 增加 budget 或 target-specific ordering。
