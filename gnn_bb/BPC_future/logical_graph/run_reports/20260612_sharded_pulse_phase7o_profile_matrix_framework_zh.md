# Sharded Pulse Phase 7O Profile Matrix Calibration Framework 报告

日期：2026-06-12

## 目标

本轮继续 Phase 7O，但不写新 Pulse 搜索算法，也不改变 production 默认配置。

目标是把 `run_sharded_pulse_roi_calibration.py` 补齐为更接近正式 Phase 7O 的 A/B 校准框架，使后续能覆盖：

- 5-task no-regression gate；
- 10-task hard-tail gate；
- 20-task improvement gate；
- support-aware / low-budget / mid-budget / impact-filter / hard-tail-only worker profiles；
- summary 中可直接观察 official result、tail retry、worker 加列质量、follow-up RMP movement 和 conservative improvement class。

## 实现摘要

### 1. Instance presets

新增 10-task presets：

- `tranq10_06`
- `apollo10_04`
- `apollo10_09`

新增 20-task presets：

- `tranq20_01`
- `apollo20_01`
- `mt20_greedy_apollo_01`
- `mt20_greedy_tranq_01`

这些只是 calibration 脚本中的显式路径 preset，不改变 solver 默认数据集或 benchmark 行为。

### 2. Phase 7O profiles

新增显式 opt-in profiles：

- `strict_worker_current_probe_support_aware`
- `strict_worker_current_probe_support_aware_low_budget`
- `strict_worker_current_probe_support_aware_mid_budget`
- `strict_worker_current_probe_support_aware_impact_filter`
- `strict_worker_current_probe_hard_tail_only`

边界：

- 所有 worker profile 仍需显式在脚本命令行指定；
- current probe 不产生 certificate；
- worker no-column / incomplete / duplicate-only / empty result 不产生 official lower bound；
- hard-tail-only profile 不启用 current probe，只依赖 hard-tail/audit signal。

### 3. Summary / gate 字段

新增或补齐：

- `scale`
- `wall_time`
- `primal`
- `dual_bound`
- `gap`
- `pricing_state`
- `best_rc`
- `official_result_changed_vs_baseline`
- `objective_mismatch_vs_baseline`
- `root_rmp_rounds`
- `generated_sequences`
- `evaluated_timed_trips`
- `final_judge_max_single_call_time`
- `exact_completion_bound_retry_count`
- `exact_completion_bound_retry_time`
- `hidden_negative_audit_count`
- worker alias 字段：`worker_triggered`、`worker_skip_reason`、`worker_signal_source`、`worker_context_hash`、`worker_returned_journeys`、`worker_added_journeys`、`worker_pruned_total` 等；
- follow-up alias 字段：`followup_rmp_objective_delta`、`followup_dual_l1_delta`、`followup_legacy_final_judge_called`、`followup_completion_retry_called`；
- `critical_disagreement_count`
- `improvement_class`

`improvement_class` 只用于报告诊断：

- `unsafe`：critical disagreement，或两个 `OPTIMAL` 之间 objective / dual mismatch；
- `worsened`：状态回退或 wall time 超过 conservative overhead 阈值；
- `improved`：状态改善、wall time 明显下降、gap 明显下降或 retry 明显下降；
- `no_regression`：未满足 improved，但也没有 regression；
- `inconclusive`：缺 baseline 或证据不足。

worker 加列导致短时限 incumbent / gap 与 baseline 不同，不会自动被标成 correctness unsafe。

## Low-budget Profile Matrix Smoke

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase7o_profile_matrix_smoke_20260612 \
--instances apollo5 apollo10 tranq20_01 \
--profiles baseline strict_worker_current_probe_support_aware_low_budget strict_worker_current_probe_support_aware_impact_filter strict_worker_current_probe_hard_tail_only \
--time-limit 2.0 \
--audit-time-limit 0.1 \
--worker-time-limit 0.1 \
--current-probe-time-limit 0.1 \
--pricing-time-limit 0.05 \
--max-cg-iterations 2 \
--audit-max-recursions 10000 \
--worker-max-recursions 10000 \
--current-probe-max-recursions 5000 \
--current-probe-min-tasks 10 \
--current-probe-min-remaining-time 0.0 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase7o_profile_matrix_smoke_20260612/summary.json`
- `BPC_future/results/sharded_pulse_phase7o_profile_matrix_smoke_20260612/summary.csv`

## Smoke 观察

| instance | profile | worker | added | skip reason | improvement_class |
|---|---|---:|---:|---|---|
| Apollo5 | support-aware low / impact | no | 0 | `current_probe_instance_too_small` | `worsened` |
| Apollo5 | hard-tail-only | no | 0 | `instance_too_small` | `worsened` |
| Apollo10 | support-aware low | yes | 2 | - | `worsened` |
| Apollo10 | support-aware impact | yes | 1 | - | `worsened` |
| Apollo10 | hard-tail-only | no | 0 | `no_previous_audit_negative_signal` | `worsened` |
| tranq20_01 | all worker profiles | no | 0 | `not_certificate_candidate` | `worsened` |

解释：

- 这是极短 cap 的工具 smoke，不能作为正式性能结论；
- Apollo5 worker 被 gate 拦住，但 audit/skip logging 在极短 baseline 下仍带来 overhead，因此被 conservative classifier 标成 `worsened`；
- Apollo10 current probe 仍可加列，但低预算 profile-matrix 的总 wall time 未体现 ROI；
- tranq20_01 在该短 cap 下没有进入 worker add-column path；
- `critical_disagreement_count=0`；
- 没有 certificate / official lower-bound side effect。

## Exactness 边界

- 本轮只改 calibration script 和 tests；
- 没有默认启用 Sharded Pulse；
- 没有把 Pulse incomplete / no-column / duplicate-only 证书化；
- 所有 active worker 返回列仍经过 driver 中既有 true-RC sanitize；
- `improvement_class` 不参与 solver 决策，只用于报告和 gate 诊断。

## Tests

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_baseline_comparison_is_conservative \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 3 tests in 0.001s
OK
```

## 当前判断

本轮完成的是 Phase 7O 正式 A/B 前的工具补齐。它让后续可以更完整地跑 5/10/20 profile matrix，但本轮 smoke 本身仍显示：

- worker 路线不能默认启用；
- 小实例 overhead 仍需严格 gate；
- Apollo10 加列能力存在，但低预算 wall-time ROI 仍未成立；
- 20-task improvement 仍未证明。

下一步应跑更接近 `目标.md` 的正式 Phase 7O 矩阵，或者在时间预算受限时先跑 5/10 no-regression 扩展集，再选择 20-task hard smoke。
