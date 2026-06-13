# Sharded Pulse Phase 7P Follow-up Active-support Attribution 报告

日期：2026-06-13

## 目标

本轮不继续加 worker budget，也不放开 certificate gate。

目标是补一个后效诊断：Pulse worker 加入的 task-set 在下一轮 RMP 中是否真的进入 active support。

上一轮结果显示：

- worker 能加入 true-RC negative new task-set；
- under-budget primal 有改善；
- 但 follow-up exact pricing tail 仍然存在；
- 因此必须区分两种可能：
  - worker 列没有进入 RMP active support；
  - worker 列进入了 active support，但仍不足以消除 tail。

## 实现摘要

### 1. Driver RMP 后效日志

在 `journey_rmp_dual_diagnostics` 中新增字段：

- `worker_followup_changed_task_set_count`
- `worker_followup_active_changed_task_set_count`
- `worker_followup_inactive_changed_task_set_count`
- `worker_followup_changed_task_set_hash`
- `worker_followup_active_changed_task_set_hash`

语义：

- 只归因上一轮 Pulse hidden-negative worker 成功加入的 changed task-sets；
- 下一轮 RMP solve 后，统计这些 task-set 与当前 active support 的交集；
- 记录后立即清空 pending worker task-set；
- 不改变 pricing、RMP、certificate 或 add-column 行为。

### 2. ROI calibration summary 字段

新增 summary / CSV 字段：

- `followup_worker_changed_task_set_count`
- `followup_worker_active_task_set_count`
- `followup_worker_inactive_task_set_count`
- `followup_worker_active_task_set_ratio`
- `pulse_worker_followup_changed_task_set_count`
- `pulse_worker_followup_active_task_set_count`
- `pulse_worker_followup_inactive_task_set_count`
- `pulse_worker_followup_active_task_set_ratio`

## Focused 测试

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 2 tests in 0.005s
OK
```

## 单例 smoke

输出：

- `BPC_future/results/sharded_pulse_phase7p_followup_active_attribution_single_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_followup_active_attribution_single_20260613/summary.csv`

实例：`mt20_greedy_apollo_01`

Profile：`strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate`

结果：

- worker events：`1`
- worker added journeys：`1`
- worker added new task-set：`1`
- worker addition productivity class：`changed_inactive_only`
- next RMP objective delta：`-31.551683`
- follow-up changed task-set count：`1`
- follow-up active changed task-set count：`1`
- follow-up active task-set ratio：`1.0`
- follow-up pricing calls：`2`
- follow-up generated / evaluated：`404 / 1535`
- follow-up last pricing state：`INCOMPLETE_LIMIT`
- critical disagreement：`0`

解释：

worker 加入的 new task-set 在下一轮 RMP 中确实进入 active support，但后续 exact pricing tail 仍然发生。

## Gate 矩阵

输出：

- `BPC_future/results/sharded_pulse_phase7p_followup_active_attribution_gate_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7p_followup_active_attribution_gate_20260613/summary.csv`

矩阵：

- 5-task balanced 全量 20 个；
- 10-task 指定 7 个；
- 20-task smoke 3 个；
- profiles：`baseline` vs `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate`。

结果摘要：

| scale | profile | n | avg wall | worker events | added | follow-up active / changed | follow-up pricing | critical |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 5 | baseline | 20 | 0.025222 | 0 | 0 | 0 / 0 | 0 | 0 |
| 5 | active attribution | 20 | 0.024956 | 0 | 0 | 0 / 0 | 0 | 0 |
| 10 | baseline | 7 | 0.117479 | 0 | 0 | 0 / 0 | 0 | 0 |
| 10 | active attribution | 7 | 0.117581 | 0 | 0 | 0 / 0 | 0 | 0 |
| 20 | baseline | 3 | 0.209234 | 0 | 0 | 0 / 0 | 0 | 0 |
| 20 | active attribution | 3 | 0.224759 | 1 | 1 | 1 / 1 | 2 | 0 |

20-task active row：

- `tranq20_01`：未触发 worker；
- `mt20_greedy_apollo_01`：worker events `1`，added `1`，follow-up active ratio `1.0`，primal `1061.554044 -> 1030.002361`；
- `mt20_greedy_tranq_01`：未触发 worker。

## 结论

本轮诊断把问题进一步缩小：

- Pulse worker 的 true-RC negative new task-set 可以进入下一轮 RMP active support；
- 它能产生明显 next-RMP objective movement；
- 但它仍没有消除后续 exact pricing tail；
- 因此当前 ROI 不足不是简单的“worker 列没进 active support”问题。

当前判断：

- 不默认启用 worker；
- 不进入 official certificate gate；
- 不扩大 worker budget；
- active-support continuation gate 保留为更安全的实验 profile；
- 下一步应分析 tail pricing 中残留负列/near-zero RC 结构，或转向 RMP stabilization / pool compression / legacy final judge optimization，而不是继续只增加 Pulse worker 调用。
