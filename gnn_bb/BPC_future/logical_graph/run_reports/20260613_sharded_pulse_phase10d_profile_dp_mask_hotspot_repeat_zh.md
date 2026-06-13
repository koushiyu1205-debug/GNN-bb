# Sharded Pulse Phase 10D Profile-DP Mask-Hotspot Repeat Validation 报告

日期：2026-06-13

## 目标

Phase 10C 单次 smoke 中，`experimental_profile_dp_mask_label_cap_32_20_only` 在 `mt20_greedy_apollo_01` 出现一行 incumbent 改善，但证据不足。本轮只做 repeat validation。

目标：

1. 验证 label-cap32 的单次改善是否稳定；
2. 验证 label-cap16 的大量 label 剪枝是否转化成 ROI；
3. 继续检查 5/10 no-op guard；
4. 不改变 production/default/certificate 语义。

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613 \
--instances phase10c_profile_dp_mask_hotspot_gate \
--profiles phase10c_profile_dp_mask_hotspot_sensitivity \
--repeat-count 3 \
--time-limit 3.0 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase10d_profile_dp_mask_hotspot_repeat_smoke_20260613/summary.csv`

矩阵：

- instances：`apollo5`, `tranq5`, `apollo10`, `tranq10_09`, `tranq10_04`, `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`
- profiles：baseline, label-cap16, label-cap32
- repeat-count：3
- rows：72

## 结果摘要

### 5-task guard

| profile | rows | official changed | critical | pricing |
|---|---:|---:|---:|---|
| baseline | 6 | 0 | 0 | 6 INCOMPLETE_LIMIT |
| label-cap16 | 6 | 0 | 0 | 6 INCOMPLETE_LIMIT |
| label-cap32 | 6 | 0 | 0 | 6 INCOMPLETE_LIMIT |

5-task no-op guard 生效。

### 10-task guard

| profile | rows | official changed | critical | pricing |
|---|---:|---:|---:|---|
| baseline | 9 | 0 | 0 | 9 FOUND_NEGATIVE |
| label-cap16 | 9 | 0 | 0 | 9 FOUND_NEGATIVE |
| label-cap32 | 9 | 0 | 0 | 9 FOUND_NEGATIVE |

10-task no-op guard 生效。

### 20-task aggregate

| profile | rows | pricing | improvement class | official changed | critical | incomplete | label cap pruned | profile-DP time |
|---|---:|---|---|---:|---:|---:|---:|---:|
| baseline | 9 | 6 INCOMPLETE_LIMIT, 3 FOUND_NEGATIVE | baseline | 0 | 0 | 6 | 0 | 0.547s |
| label-cap16 | 9 | 6 INCOMPLETE_LIMIT, 3 FOUND_NEGATIVE | 7 no_regression, 1 improved, 1 worsened | 1 | 0 | 6 | 1729 | 0.489s |
| label-cap32 | 9 | 6 INCOMPLETE_LIMIT, 3 FOUND_NEGATIVE | 7 no_regression, 1 improved, 1 worsened | 2 | 0 | 6 | 0 | 0.546s |

关键结果：

- label-cap16 剪掉 1729 个 labels，但 20-task incomplete 数量没有下降；
- label-cap16 的 improved/worsened 各 1，整体不稳定；
- label-cap32 的 improved/worsened 各 1，复现了不稳定性；
- label-cap32 没有触发 label-cap pruning，本质上不是一个有效的 hotspot limiter；
- 20-task profile-DP time 没有形成稳定收益；
- 没有 critical disagreement。

## 20-task 明细

### `tranq20_01`

| profile | repeats | pricing | improvement | official changed |
|---|---:|---|---|---:|
| baseline | 3 | 3 INCOMPLETE_LIMIT | baseline | 0 |
| label-cap16 | 3 | 3 INCOMPLETE_LIMIT | 3 no_regression | 0 |
| label-cap32 | 3 | 3 INCOMPLETE_LIMIT | 3 no_regression | 0 |

`tranq20_01` 的 max labels/mask 约 16-18，label cap 不是有效 lever。

### `mt20_greedy_apollo_01`

| profile | repeats | pricing | improvement | official changed |
|---|---:|---|---|---:|
| baseline | 3 | 3 INCOMPLETE_LIMIT | baseline | 0 |
| label-cap16 | 3 | 3 INCOMPLETE_LIMIT | 1 improved, 1 worsened, 1 no_regression | 1 |
| label-cap32 | 3 | 3 INCOMPLETE_LIMIT | 1 improved, 1 worsened, 1 no_regression | 2 |

这是唯一有变化的实例，但方向混合，不支持作为优化主线。

### `mt20_greedy_tranq_01`

| profile | repeats | pricing | improvement | official changed |
|---|---:|---|---|---:|
| baseline | 3 | 3 FOUND_NEGATIVE | baseline | 0 |
| label-cap16 | 3 | 3 FOUND_NEGATIVE | 3 no_regression | 0 |
| label-cap32 | 3 | 3 FOUND_NEGATIVE | 3 no_regression | 0 |

label-cap16 在这里稳定剪大量 labels，但没有改变 short CG result。

## 结论

Phase 10D 证明：

1. label-cap16 有真实 hotspot 剪枝信号，但没有转化为 incomplete reduction 或 incumbent improvement；
2. label-cap32 的 Phase 10C 单次改善不稳定，repeat 中同时出现 improved 和 worsened；
3. selected/materialized/returned 链路仍不是 blocker；
4. profile-DP mask label cap 不应继续作为主线优化；
5. 当前更像 ordering / column trajectory / RMP degeneracy 问题，而不是 profile-DP bucket 太宽。

## Exactness 边界

- calibration-only；
- 5/10 no-op；
- no Sharded Pulse worker；
- no Pulse audit；
- no dual stabilization；
- no certificate / official lower-bound rule relaxed；
- profile-DP no-column 仍非 official certificate。

## 下一步建议

Phase 10E 应转向 profile-DP ordering attribution / RMP column trajectory：

- 比较 improved/worsened repeats 中 first returned negative task-set；
- 记录 profile-DP returned task-set 与 active pool / later negative family 的关系；
- 判断 short CG 变差是否来自列进入顺序、replacement 列、或 RMP degeneracy；
- 不再继续调 `profile_dp_max_labels_per_mask`。

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
Ran 3 tests in 0.002s
OK
```

全量回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 482 tests in 1.438s
OK (skipped=1)
```

whitespace check：

```bash
git diff --check
```

结果：通过。
