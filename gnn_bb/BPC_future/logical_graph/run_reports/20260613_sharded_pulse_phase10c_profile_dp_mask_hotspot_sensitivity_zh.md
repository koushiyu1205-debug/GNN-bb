# Sharded Pulse Phase 10C Profile-DP Mask-Hotspot Sensitivity 报告

日期：2026-06-13

## 目标

Phase 10B 已经排除了“简单提高 `journey_pricing_max_dp_states`”作为主线优化。本轮只做 Phase 10C：profile-DP mask-hotspot / selected-materialization diagnostics。

目标：

1. 增强 ROI summary 对 profile-DP hotspot 的可见性；
2. 做 20-task-only mask-label-cap calibration；
3. 观察热点 mask 限流是否能改善 short CG tail；
4. 继续确认 5/10 no-op guard、official result safety 和 certificate 边界。

不做：

- 不启用 Sharded Pulse worker；
- 不启用 Pulse audit；
- 不启用 dual stabilization；
- 不放开 official certificate gate；
- 不改变 final judge / lower-bound 语义。

## 实现摘要

### 1. 新增 profile-DP hotspot summary 字段

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 的 `_profile_dp_tail_metrics()` 增加：

- `profile_dp_tail_label_cap_pruned`
- `profile_dp_tail_selected_candidate_input_count`
- `profile_dp_tail_selected_candidate_scanned_count`
- `profile_dp_tail_selected_candidate_materialized_count`
- `profile_dp_tail_selected_candidate_returned_count`
- `profile_dp_tail_selected_candidate_filtered_count`
- `profile_dp_tail_selected_unmaterialized_candidate_count`
- `profile_dp_tail_materialization_candidate_count`
- `profile_dp_tail_materialization_selected_candidate_count`
- `profile_dp_tail_materialization_infeasible_filtered_count`
- `profile_dp_tail_hotspot_class`
- `profile_dp_tail_hotspot_reason`

这些字段只汇总 official pricing path 的 `journey_pricing` 日志，排除 Sharded Pulse worker 和 dummy/pulse final judge 记录。

### 2. 新增 20-task-only calibration profiles

新增：

- `experimental_profile_dp_mask_label_cap_16_20_only`
- `experimental_profile_dp_mask_label_cap_32_20_only`
- `phase10c_profile_dp_mask_hotspot_gate`
- `phase10c_profile_dp_mask_hotspot_sensitivity`

profile 行为：

- 5/10-task：no-op；
- 20-task：
  - 设置 `journey_pricing_profile_dp_max_labels_per_mask=16/32`；
  - 显式关闭 Pulse audit、Pulse hidden-negative worker、dual stabilization。

注意：`profile_dp_max_labels_per_mask` 是 calibration-only 的 label bucket truncation，不是 certificate-safe proof 剪枝；profile-DP no-column 仍不能形成 official certificate。

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase10c_profile_dp_mask_hotspot_sensitivity_smoke_20260613 \
--instances phase10c_profile_dp_mask_hotspot_gate \
--profiles phase10c_profile_dp_mask_hotspot_sensitivity \
--repeat-count 1 \
--time-limit 3.0 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase10c_profile_dp_mask_hotspot_sensitivity_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase10c_profile_dp_mask_hotspot_sensitivity_smoke_20260613/summary.csv`

矩阵：

- instances：`apollo5`, `tranq5`, `apollo10`, `tranq10_09`, `tranq10_04`, `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`
- profiles：baseline, label-cap16, label-cap32
- rows：24

## 结果摘要

### 5-task

| profile | rows | official changed | critical | pricing | label cap pruned |
|---|---:|---:|---:|---|---:|
| baseline | 2 | 0 | 0 | 2 INCOMPLETE_LIMIT | 0 |
| label-cap16 | 2 | 0 | 0 | 2 INCOMPLETE_LIMIT | 0 |
| label-cap32 | 2 | 0 | 0 | 2 INCOMPLETE_LIMIT | 0 |

5-task no-op guard 生效。

### 10-task

| profile | rows | official changed | critical | pricing | label cap pruned |
|---|---:|---:|---:|---|---:|
| baseline | 3 | 0 | 0 | 3 FOUND_NEGATIVE | 0 |
| label-cap16 | 3 | 0 | 0 | 3 FOUND_NEGATIVE | 0 |
| label-cap32 | 3 | 0 | 0 | 3 FOUND_NEGATIVE | 0 |

10-task no-op guard 生效。

### 20-task

| profile | pricing | improvement class | official changed | incomplete | label cap pruned | max labels/mask | profile-DP time |
|---|---|---|---:|---:|---:|---:|---:|
| baseline | 2 INCOMPLETE_LIMIT, 1 FOUND_NEGATIVE | baseline | 0 | 2 | 0 | 31 | 0.144s |
| label-cap16 | 2 INCOMPLETE_LIMIT, 1 FOUND_NEGATIVE | 3 no_regression | 0 | 2 | 574 | 16 | 0.160s |
| label-cap32 | 2 INCOMPLETE_LIMIT, 1 FOUND_NEGATIVE | 2 no_regression, 1 improved | 1 | 2 | 0 | 31 | 0.208s |

关键结果：

- label-cap16 确实将 20-task max labels/mask 限到 16，并剪掉 574 个 labels；
- label-cap16 没有减少 incomplete，也没有改善 20-task incumbent；
- label-cap32 在 `mt20_greedy_apollo_01` 单行改善 incumbent，但没有触发 label-cap pruning，且 profile-DP time 上升；
- selected candidate 全部 materialized 并 returned，没有 selected/materialization gap；
- materialization candidate count 为 0，当前 smoke 不是 selected-mask materialization failure 问题。

## 20-task 明细

### `tranq20_01`

| profile | pricing | primal | tail | hotspot | incomplete | label cap pruned | max labels/mask | selected/materialized/returned |
|---|---|---:|---|---|---:|---:|---:|---|
| baseline | INCOMPLETE_LIMIT | 781.101309 | profile_dp_incomplete_tail | no_mask_hotspot | 1 | 0 | 16 | 12 / 3 / 3 |
| label-cap16 | INCOMPLETE_LIMIT | 781.101309 | profile_dp_incomplete_tail | label_cap_active | 1 | 2 | 16 | 12 / 3 / 3 |
| label-cap32 | INCOMPLETE_LIMIT | 781.101309 | profile_dp_incomplete_tail | no_mask_hotspot | 1 | 0 | 16 | 12 / 3 / 3 |

`tranq20_01` 的热点不重，label cap 没有改善 incomplete。

### `mt20_greedy_apollo_01`

| profile | pricing | primal | tail | hotspot | incomplete | label cap pruned | max labels/mask | selected/materialized/returned |
|---|---|---:|---|---|---:|---:|---:|---|
| baseline | INCOMPLETE_LIMIT | 921.640296 | profile_dp_incomplete_tail | mask_hotspot | 1 | 0 | 24 | 8 / 2 / 2 |
| label-cap16 | INCOMPLETE_LIMIT | 921.640296 | profile_dp_incomplete_tail | label_cap_active | 1 | 31 | 16 | 8 / 2 / 2 |
| label-cap32 | INCOMPLETE_LIMIT | 847.812231 | profile_dp_incomplete_tail | mask_hotspot | 1 | 0 | 28 | 24 / 6 / 6 |

label-cap32 单行改善 incumbent，但不是由 label-cap pruning 直接造成；它更像搜索轨迹/列进入顺序变化。需要 repeat 才能判断是否有真实 ROI。

### `mt20_greedy_tranq_01`

| profile | pricing | primal | tail | hotspot | incomplete | label cap pruned | max labels/mask | selected/materialized/returned |
|---|---|---:|---|---|---:|---:|---:|---|
| baseline | FOUND_NEGATIVE | 761.814403 | profile_dp_negative_tail | mask_hotspot | 0 | 0 | 31 | 32 / 8 / 8 |
| label-cap16 | FOUND_NEGATIVE | 761.814403 | profile_dp_negative_tail | label_cap_active | 0 | 541 | 16 | 32 / 8 / 8 |
| label-cap32 | FOUND_NEGATIVE | 761.814403 | profile_dp_negative_tail | mask_hotspot | 0 | 0 | 31 | 32 / 8 / 8 |

label-cap16 在这个实例上大幅剪 label，但没有改变返回列或 incumbent。

## 结论

Phase 10C 结论：

1. selected/materialized/returned 链路不是当前 blocker：本轮全部 selected candidates 都 materialized 并 returned；
2. label-cap16 能削减 hotspot label 数，但没有改善 incomplete 或 incumbent；
3. label-cap32 的单行 20-task improvement 需要 repeat 验证，不能作为生产方向；
4. profile-DP tail 更像“状态/列顺序影响 short CG trajectory”，不是简单 materialization failure；
5. 不应把 label-cap 当成 proof-safe 或 production default。

## Exactness 边界

- calibration-only；
- 5/10 no-op；
- no Sharded Pulse worker；
- no Pulse audit；
- no dual stabilization；
- no certificate / official lower-bound rule relaxed；
- profile-DP no-column 仍非 official certificate。

## 下一步建议

Phase 10D 应做 repeat validation，而不是继续加新算法：

- 对 `phase10c_profile_dp_mask_hotspot_sensitivity` 做 repeat-count 3；
- 判断 `label-cap32` 在 `mt20_greedy_apollo_01` 的改善是否稳定；
- 同时观察 5/10 no-op、critical disagreement、profile-DP time；
- 如果 repeat 不稳定，转向 profile-DP ordering attribution / RMP column trajectory，而不是继续 label-cap。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_dp_tail_metrics_are_summarized \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 3 tests in 0.003s
OK
```

全量回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 482 tests in 1.432s
OK (skipped=1)
```

whitespace check：

```bash
git diff --check
```

结果：通过。
