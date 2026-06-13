# Sharded Pulse Phase 7V Residual Tail Attribution 报告

日期：2026-06-13

## 目标

Phase 7V 只做 residual pricing / legacy tail attribution，不改算法。

背景是 Phase 7U 已经显示：Pulse worker 加入的新列能进入 pool、改变 active support 和 RMP objective，但 follow-up 仍可能出现 ordinary / exact pricing negative tail。因此本轮目标是让日志能回答：

1. worker 加入的 task-set 是什么；
2. follow-up 首个非 worker negative task-set 是什么；
3. 两者是同一 task-set、重叠 task-set，还是完全不同 task-set。

## 实现摘要

### 1. `journey_pricing` 负列 task-set summary

`journey_pricing` 事件新增只读字段：

- `negative_journey_task_set_count`
- `negative_journey_task_set_hash`
- `negative_journey_task_set_samples`
- `negative_journey_task_set_sample_count`
- `negative_journey_task_set_samples_truncated`

样本是排序后的 `list[list[int]]`，有固定上限，只用于诊断。

### 2. `journey_column_addition` task-set samples

`journey_column_addition` 事件新增：

- `requested_task_set_samples`
- `changed_task_set_samples`
- `new_task_set_samples`
- `replacement_task_set_samples`
- `active_changed_task_set_samples`
- `inactive_changed_task_set_samples`

这些字段只辅助重建 worker add-column 后的 task-set 影响，不参与列筛选或 RMP。

### 3. ROI summary follow-up attribution

`run_sharded_pulse_roi_calibration.py` 新增 summary 字段：

- `followup_first_negative_task_set_hash`
- `followup_first_negative_task_set`
- `followup_first_negative_task_count`
- `followup_first_negative_overlap_to_worker`
- `followup_first_negative_jaccard_to_worker`
- `followup_first_negative_relation_to_worker`

并提供对应 `pulse_worker_followup_*` 别名。

relation 分类：

- `same_task_set`
- `overlapping_task_set`
- `disjoint_task_set`
- `unknown`
- `no_worker_add`

## Exactness 边界

- 不改变 pricing / worker / certificate / RMP 逻辑；
- 不改变 worker trigger；
- 不启用 production certificate；
- 不把 Pulse no-column / incomplete / duplicate-only 变成 official lower bound；
- 新字段全部是 JSONL / CSV 诊断字段。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_addition_log_reports_active_support_overlap \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_pricing_log_reports_negative_task_set_samples \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 4 tests in 0.003s
OK
```

全量 `BPCFutureTests`：

```text
Ran 469 tests in 1.417s
OK (skipped=1)
```

`git diff --check`：通过。

## Smoke

运行短时 opt-in diagnostic smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7v_residual_attribution_smoke_20260613 \
--instances mt20_greedy_apollo_01 \
--profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown \
--time-limit 1.2 \
--audit-time-limit 0.15 \
--worker-time-limit 0.15 \
--current-probe-time-limit 0.15 \
--pricing-time-limit 0.12 \
--pricing-max-dp-states 1 \
--max-cg-iterations 2 \
--audit-max-recursions 20000 \
--worker-max-recursions 20000 \
--current-probe-max-recursions 12000 \
--current-probe-min-tasks 20 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7v_residual_attribution_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase7v_residual_attribution_smoke_20260613/summary.csv`

观测：

- baseline official status：`TIME_LIMIT`;
- worker profile official status：`TIME_LIMIT`;
- `official_result_changed_vs_baseline=False`;
- worker added journeys：`1`;
- JSONL 中出现：
  - `negative_journey_task_set_samples=[[6, 19]]`;
  - `changed_task_set_samples=[[6, 19]]`;
  - `new_task_set_samples=[[6, 19]]`;
  - `inactive_changed_task_set_samples=[[6, 19]]`;
- 本次短 smoke 没有后续非 worker pricing，`followup_tail_outcome=no_followup_pricing`，overlap relation 为 `unknown`。

## 结论

Phase 7V 完成了只读 attribution 层：后续 ROI 矩阵可以直接从 JSONL / CSV 判断 worker 后 residual negative 与 worker 加入列的 task-set 关系。

当前不应因此放开 worker 或 certificate。下一步应复跑最强 20-only worker profiles，用 Phase 7V 字段分类 residual tail：

1. 如果 residual negatives 多为 disjoint/new task-set，说明 worker 没覆盖 ordinary negative tail；
2. 如果 residual negatives 多与 worker task-set 重叠，优先查 replacement quality、start-time variants 和 column impact filter；
3. 如果仍无稳定 ROI，应继续按负结果路线转向 RMP stabilization / pool compression / legacy final-judge optimization。
