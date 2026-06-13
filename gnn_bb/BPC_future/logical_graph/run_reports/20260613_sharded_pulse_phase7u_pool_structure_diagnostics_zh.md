# Sharded Pulse Phase 7U RMP / Column-pool Structure Diagnostics 报告

日期：2026-06-13

## 目标

Phase 7O/7P 的 synthesis 显示：active Pulse worker 能安全加 true-RC negative columns，但没有稳定 wall-time / proof-tail ROI。

本轮不继续扩大 worker，不开启 official certificate gate，也不跑大矩阵。

目标是补一层只读诊断，帮助后续判断 worker 列没有转化为稳定 ROI 的原因是否来自：

- column pool task-set 多样性不足；
- replacement / duplicate pressure；
- active support 高度集中；
- fractional active support；
- worker 后 RMP 已变动但 proof-tail 仍卡住。

## 实现摘要

### 1. Driver 增加只读 RMP/列池结构日志

在 `BPC_future/solver/journey_driver.py` 中新增：

- `_journey_pool_structure_diagnostics(...)`

并在 root / branch 的每次 `solve_journey_rmp()` 后记录 JSONL 事件：

- `event="journey_pool_structure_diagnostics"`

字段包括：

- `pool_journey_count`
- `pool_unique_task_set_count`
- `pool_duplicate_task_set_count`
- `pool_duplicate_task_set_ratio`
- `pool_avg_journeys_per_task_set`
- `pool_max_journeys_per_task_set`
- `pool_singleton_task_set_count`
- `pool_multi_task_set_count`
- `pool_task_set_size_hist`
- `pool_task_set_dominance_enabled`
- `pool_active_journey_count`
- `pool_active_task_set_count`
- `pool_active_duplicate_task_set_count`
- `pool_active_fractional_journey_count`
- `pool_active_fractional_ratio`
- `pool_active_total_value`
- `pool_active_max_value`
- `pool_active_singleton_task_set_count`
- `pool_active_multi_task_set_count`
- `pool_active_task_count_union`
- `pool_active_task_set_hash`

该日志只读取 `journey_pool` 和 `solution.journey_values`，不影响 RMP、pricing、worker、branch、cuts、certificate。

### 2. ROI calibration summary 增加 pool structure 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 中新增：

- `_pool_structure_metrics(records)`

并把以下字段写入 `summary.json / summary.csv`：

- `pool_diag_events`
- `pool_journeys_last`
- `pool_unique_task_sets_last`
- `pool_duplicate_task_sets_last`
- `pool_duplicate_task_set_ratio_last`
- `pool_duplicate_task_set_ratio_max`
- `pool_avg_journeys_per_task_set_last`
- `pool_max_journeys_per_task_set_last`
- `pool_active_journeys_last`
- `pool_active_task_sets_last`
- `pool_active_duplicate_task_sets_last`
- `pool_active_fractional_journeys_last`
- `pool_active_fractional_ratio_last`
- `pool_active_fractional_ratio_max`
- `pool_active_total_value_last`
- `pool_active_max_value_last`
- `pool_active_singleton_task_sets_last`
- `pool_active_multi_task_sets_last`
- `pool_active_task_count_union_last`
- `pool_active_task_set_hash_last`

## Exactness 边界

本轮是 diagnostic-only：

- 不改变 RMP 模型；
- 不改变 pricing dual；
- 不改变 worker trigger；
- 不改变 add-column path；
- 不改变 certificate inference；
- 不改变 official lower bound；
- 不启用任何默认 Pulse worker / certificate profile。

## 测试

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pool_structure_diagnostics_tracks_pool_and_active_support \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pool_structure_metrics_are_summarized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 4 tests in 0.002s
OK
```

Full focused suite：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 468 tests in 1.428s
OK (skipped=1)
```

## Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_very_small_smoke_20260613 \
--instances very_small \
--profiles baseline \
--time-limit 0.4 \
--pricing-time-limit 0.05 \
--max-cg-iterations 2 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_very_small_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7u_pool_diagnostics_very_small_smoke_20260613/summary.csv`

关键观测：

- `pool_diag_events=1`
- `pool_journeys_last=10`
- `pool_unique_task_sets_last=10`
- `pool_duplicate_task_sets_last=0`
- `pool_active_journeys_last=2`
- `pool_active_task_sets_last=2`
- `pool_active_fractional_ratio_last=0.0`
- `pool_active_multi_task_sets_last=2`
- `pool_active_task_count_union_last=4`

## 当前结论

Phase 7U 只补观测能力，不声称性能提升。

它让后续 RMP / pool / proof-tail 转向可以直接回答：

- worker 加入的列是否只是 replacement；
- active support 是否真的吸收 worker 任务集；
- 列池是否在 task-set 维度重复或过窄；
- RMP 是否高度 fractional；
- follow-up proof-tail 是否与列池结构相关。

## 下一步建议

下一步不应继续 active worker gate-stacking。

建议做：

1. 用 Phase 7U 字段重跑一个小型 5/10/20 diagnostic-only matrix；
2. 重点比较 baseline 与已有最有信号的 20-only worker profile：
   - `pool_active_task_set_hash_last`
   - `pool_active_fractional_ratio_last`
   - `pool_unique_task_sets_last`
   - `pool_duplicate_task_set_ratio_last`
   - `followup_tail_outcome`
3. 若 worker 后 active support 和 pool diversity 改善但 proof-tail 仍卡住，优先进入 legacy final-judge proof-tail profiling；
4. 若 pool diversity 差、replacement pressure 高，再进入 column pool compression / RMP stabilization。

本阶段不满足最终交付条件 A 或 B，只是为 worker 负结果后的 exact-safe 转向补齐观测基础。
