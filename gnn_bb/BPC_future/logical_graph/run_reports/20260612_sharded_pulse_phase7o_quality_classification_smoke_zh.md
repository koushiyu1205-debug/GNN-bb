# Sharded Pulse Phase 7O Quality Classification Smoke 报告

日期：2026-06-12

## 目标

本轮不改 solver 求解语义，只修正 Phase 7O 校准报告层的两个问题：

1. `目标.md` 要求的 worker summary 字段缺少若干短名别名；
2. 20-task TIME_LIMIT 场景下，current-context worker 让 primal 明显改善，但旧 `improvement_class` 只按 wall time 将其归为 `worsened`，无法表达 20-task 的 column-quality / primal-quality signal。

本轮不做：

- 不默认启用 worker；
- 不放开 official certificate gate；
- 不改变 pricing / RMP / final judge 语义；
- 不把 Pulse incomplete / no-column / duplicate-only 证书化。

## 实现摘要

### 1. Summary 字段补齐

`run_sharded_pulse_roi_calibration.py` 增加 `目标.md` 要求的 worker 字段别名：

- `worker_added_new_task_set_count`
- `worker_added_replacement_count`
- `worker_addition_productivity_class`

这些字段均从 existing JSONL `journey_column_addition` 记录重建，不改变 solver 行为。

### 2. 20-task quality classification

`improvement_class` 仍保留：

- `no_regression`
- `improved`
- `worsened`
- `unsafe`
- `inconclusive`

调整规则：

- 5/10 regression gate 仍按原来的 wall-time/no-regression 逻辑；
- `OPTIMAL` vs `OPTIMAL` 的 objective / dual mismatch 仍是 `unsafe`；
- 只有在 `scale >= 20`、同为 non-OPTIMAL 状态、无 critical disagreement、无 objective mismatch，且 primal 明显优于 baseline 时，才允许归类为 `improved`。

注意：这里的 `improved` 表示 20-task under-budget primal / column-quality 改善，不表示 wall-time speedup。

## Smoke 命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_quality_classification_smoke_20260612 \
--instances phase7o_20_smoke \
--profiles baseline strict_worker_delayed_current_probe_impact_low_budget strict_worker_delayed_current_probe_impact_low_budget_cooldown \
--time-limit 12.0 \
--audit-time-limit 0.2 \
--worker-time-limit 0.2 \
--current-probe-time-limit 0.2 \
--pricing-time-limit 0.2 \
--max-cg-iterations 10 \
--audit-max-recursions 50000 \
--worker-max-recursions 50000 \
--current-probe-max-recursions 25000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_quality_classification_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_quality_classification_smoke_20260612/summary.csv`

## 结果摘要

| instance | profile | primal | wall time | added | new task-set | class |
|---|---|---:|---:|---:|---:|---|
| mt20_greedy_apollo_01 | baseline | 1061.554044 | 0.251541 | 0 | 0 | baseline |
| mt20_greedy_apollo_01 | low-budget | 1022.575388 | 0.866560 | 2 | 2 | improved |
| mt20_greedy_apollo_01 | low-budget + cooldown | 1030.002361 | 0.512412 | 1 | 1 | improved |

关键解释：

- low-budget profile 的 primal 明显改善，但 wall time 明显变差；
- cooldown profile 降低了 overhead，但 wall time 仍慢于 baseline；
- 因此这只是 20-task primal / column-quality improvement signal，不是最终 wall-time ROI；
- 当前仍不能默认启用 worker，也不能进入 official certificate gate。

## Exactness 边界

- worker returned journeys 仍走 true-RC sanitize；
- `objective_mismatch_vs_baseline=False`；
- 无 critical disagreement；
- Pulse no-column / incomplete / duplicate-only 仍不影响 official lower bound；
- 本轮只调整校准解释层与 summary 字段。

## 验证

语法检查通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

focused tests 通过：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_baseline_comparison_is_conservative
```

结果：

```text
Ran 2 tests in 0.001s
OK
```

## 当前判断

Phase 7O 的状态现在更清楚：

- 5-task / 10-task gate 仍以 no-regression 为硬约束；
- 20-task 已有可记录的 primal / column-quality improvement signal；
- 但 wall-time ROI 仍未成立；
- 最终目标尚未完成。

下一步若继续 Sharded Pulse worker 主线，应做更严格的 productivity / ROI gate，让 20-task 的 primal-quality signal 尽量少付 wall-time overhead，而不是继续增加 worker budget。
