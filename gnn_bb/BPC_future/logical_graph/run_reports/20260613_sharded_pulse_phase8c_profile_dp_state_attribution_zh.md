# Sharded Pulse Phase 8C Profile-DP State Attribution 报告

日期：2026-06-13

## 目标

Phase 8C 只做 `profile-DP state explosion` 的只读归因。

本轮不改变求解行为，不调 worker gate，不提高 `journey_pricing_max_dp_states`，也不打开 official certificate gate。

目标是让后续 ROI / proof-tail 诊断能回答：

1. profile-DP state cap 是少数 task-mask 的 label bucket 爆炸；
2. 还是整体 reachable mask 面太大；
3. 爆炸发生在哪个 sortie count 层；
4. top mask 对应哪些任务集合。

## 实现摘要

### 1. Profile-DP 内部结构统计

在 `_solve_best_journey_profile_dp()` 的 `record_dp_stats()` 中新增只读派生字段：

- `nonempty_mask_count`
- `max_labels_per_mask_observed`
- `labels_by_sortie_count`
- `top_mask_label_counts`

这些字段只扫描 `labels_by_count` 当前内容，不参与：

- DP 转移；
- dominance；
- pruning；
- candidate selection；
- certificate 判断。

`top_mask_label_counts` 记录格式为：

```text
(sortie_count, label_count, task_tuple)
```

根空 mask 不计入这些结构字段。

### 2. JourneyPricingResult / JSONL 透传

`JourneyPricingResult` 新增诊断字段：

- `dp_nonempty_mask_count`
- `dp_max_labels_per_mask_observed`
- `dp_labels_by_sortie_count`
- `dp_top_mask_label_counts`

`journey_pricing` JSONL 事件同步输出这些字段。

`_journey_pricing_audit_stats()` 也加入同一组字段，便于 audit / worker 事件保留结构归因。

### 3. ROI summary 归因字段

`run_sharded_pulse_roi_calibration.py` 新增 summary 字段：

- `followup_profile_dp_max_labels_per_mask_observed`
- `followup_profile_dp_nonempty_mask_count`
- `followup_profile_dp_labels_by_sortie_count`
- `followup_profile_dp_top_mask_label_counts`
- `pulse_worker_followup_profile_dp_max_labels_per_mask_observed`
- `pulse_worker_followup_profile_dp_nonempty_mask_count`
- `pulse_worker_followup_profile_dp_labels_by_sortie_count`
- `pulse_worker_followup_profile_dp_top_mask_label_counts`

汇总逻辑从 worker 后所有 follow-up profile-DP pricing records 中提取结构字段，不只依赖 `profile_dp_incomplete` records。这样即使 state cap 未复现，也能保留 mask / label 分布信号。

## 验证

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_profile_dp_early_return_records_stats \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields
```

结果：

```text
Ran 3 tests in 0.002s
OK
```

补充 ROI focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pool_structure_metrics_are_summarized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_baseline_comparison_is_conservative
```

结果：

```text
Ran 3 tests in 0.001s
OK
```

very_small summary smoke：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase8c_profile_dp_attribution_smoke_20260613 \
--instances very_small \
--profiles baseline \
--time-limit 1 \
--pricing-time-limit 0.05 \
--pricing-max-dp-states 20 \
--max-cg-iterations 1 \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase8c_profile_dp_attribution_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase8c_profile_dp_attribution_smoke_20260613/summary.csv`

summary CSV / JSON 已包含新增字段。

## 当前边界

- 没有改变 pricing search；
- 没有改变 worker trigger；
- 没有改变 Pulse audit / worker 预算；
- 没有改变 certificate / official lower-bound 逻辑；
- 没有跑 20-task A/B；
- 该 phase 只提供归因观测，不构成性能收益证据。

## 结论

Phase 8C 完成了 profile-DP state explosion 的结构化观测链路。

下一次遇到 `profile_dp_state_cap` 或 follow-up profile-DP tail 时，summary 可以直接看到：

- reachable nonempty mask 面；
- 单个 mask bucket 最大 label 数；
- 各 sortie 层 label 分布；
- label 最多的 task-mask 样本。

这支持下一步区分：

1. 少数 mask bucket 爆炸，适合做更局部的 dominance / cap / materialization 策略；
2. mask 面整体扩张，适合做 RMP dual / pool / proof-tail 策略；
3. cap 只是预算症状，提高 cap 不是稳定 ROI 修复。
