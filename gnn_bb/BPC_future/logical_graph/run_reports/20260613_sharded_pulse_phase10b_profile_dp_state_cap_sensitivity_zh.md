# Sharded Pulse Phase 10B Profile-DP State-Cap Sensitivity 报告

日期：2026-06-13

## 目标

本轮只做 profile-DP state-cap 的受控 sensitivity A/B。

目标不是放开 Sharded Pulse worker，也不是做 official certificate gate，而是回答：

1. 将 20-task profile-DP cap 从 1000 提高到 2000/3000，是否能降低 incomplete tail；
2. 是否会带来 5/10 小实例回退；
3. 是否会改变 official result、incumbent 或 pricing tail 结构。

## 实现摘要

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 增加：

- instance group：
  - `phase10b_profile_dp_state_cap_gate`
- profiles：
  - `experimental_profile_dp_cap_2000_20_only`
  - `experimental_profile_dp_cap_3000_20_only`
- profile group：
  - `phase10b_profile_dp_state_cap_sensitivity`

cap profile 只在 `task_count >= 20` 时生效；5/10 直接 no-op。

20-task cap profile 只修改：

- `journey_pricing_max_dp_states=2000/3000`

并显式关闭：

- `journey_sharded_pulse_audit_enabled`
- `journey_sharded_pulse_hidden_negative_worker_enabled`
- `journey_dual_stabilization_enabled`

## Smoke Matrix

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
--output-dir BPC_future/results/sharded_pulse_phase10b_profile_dp_state_cap_sensitivity_smoke_20260613 \
--instances phase10b_profile_dp_state_cap_gate \
--profiles phase10b_profile_dp_state_cap_sensitivity \
--repeat-count 1 \
--time-limit 3.0 \
--pricing-time-limit 0.3 \
--pricing-max-dp-states 1000 \
--max-cg-iterations 8 \
--profile-mask-diagnostics \
--quiet
```

输出：

- `BPC_future/results/sharded_pulse_phase10b_profile_dp_state_cap_sensitivity_smoke_20260613/summary.json`
- `BPC_future/results/sharded_pulse_phase10b_profile_dp_state_cap_sensitivity_smoke_20260613/summary.csv`

矩阵：

- instances：`apollo5`, `tranq5`, `apollo10`, `tranq10_09`, `tranq10_04`, `tranq20_01`, `mt20_greedy_apollo_01`, `mt20_greedy_tranq_01`
- profiles：baseline, cap2000, cap3000
- rows：24

## 结果摘要

### 5-task

| profile | rows | official changed | critical | pricing | tail class |
|---|---:|---:|---:|---|---|
| baseline | 2 | 0 | 0 | 2 INCOMPLETE_LIMIT | 2 profile_dp_negative_tail |
| cap2000 | 2 | 0 | 0 | 2 INCOMPLETE_LIMIT | 2 profile_dp_negative_tail |
| cap3000 | 2 | 0 | 0 | 2 INCOMPLETE_LIMIT | 2 profile_dp_negative_tail |

5-task cap profiles 按设计 no-op，没有 official result change 或 critical disagreement。

### 10-task

| profile | rows | official changed | critical | pricing | tail class |
|---|---:|---:|---:|---|---|
| baseline | 3 | 0 | 0 | 3 FOUND_NEGATIVE | 3 profile_dp_negative_tail |
| cap2000 | 3 | 0 | 0 | 3 FOUND_NEGATIVE | 3 profile_dp_negative_tail |
| cap3000 | 3 | 0 | 0 | 3 FOUND_NEGATIVE | 3 profile_dp_negative_tail |

10-task cap profiles 同样 no-op。虽然 profile-DP 多次触达 state cap，但仍返回 negative，不是当前 smoke 的 no-negative proof blocker。

### 20-task

| profile | pricing | improvement class | official changed | profile-DP incomplete | state-cap hits | profile-DP time |
|---|---|---|---:|---:|---:|---:|
| baseline | 1 INCOMPLETE_LIMIT, 2 FOUND_NEGATIVE | baseline | 0 | 1 | 18 | 0.236s |
| cap2000 | 2 INCOMPLETE_LIMIT, 1 FOUND_NEGATIVE | 1 no_regression, 2 worsened | 2 | 2 | 14 | 0.272s |
| cap3000 | 1 INCOMPLETE_LIMIT, 2 FOUND_NEGATIVE | 1 improved, 2 worsened | 3 | 1 | 16 | 0.491s |

20-task 结论：

- cap2000 没有减少 incomplete，反而从 1 个 incomplete 变成 2 个 incomplete；
- cap3000 的 incomplete 数量回到 1，但 profile-DP time 约翻倍；
- cap2000/cap3000 都导致部分 20-task incumbent 变差；
- 没有 critical disagreement；
- 没有 certificate/lower-bound 语义放松。

## 20-task 明细

### `tranq20_01`

| profile | pricing | primal | tail class | incomplete | state max | labels/mask max | min best RC |
|---|---|---:|---|---:|---:|---:|---:|
| baseline | INCOMPLETE_LIMIT | 781.101309 | profile_dp_incomplete_tail | 1 | 1001 | 16 | -57.0891735 |
| cap2000 | INCOMPLETE_LIMIT | 781.101309 | profile_dp_incomplete_tail | 1 | 2001 | 20 | -57.0891735 |
| cap3000 | INCOMPLETE_LIMIT | 780.341965 | profile_dp_incomplete_tail | 1 | 3001 | 26 | -58.8722635 |

raising cap 没有消除 incomplete，只增加了状态规模。

### `mt20_greedy_apollo_01`

| profile | pricing | primal | tail class | incomplete | state max | labels/mask max | min best RC |
|---|---|---:|---|---:|---:|---:|---:|
| baseline | FOUND_NEGATIVE | 773.859150 | profile_dp_negative_tail | 0 | 1001 | 28 | -139.913748 |
| cap2000 | INCOMPLETE_LIMIT | 921.640296 | profile_dp_incomplete_tail | 1 | 2001 | 38 | -139.913748 |
| cap3000 | FOUND_NEGATIVE | 921.640296 | profile_dp_negative_tail | 0 | 3001 | 38 | -192.171101 |

这是本轮最强的反例：提高 cap 后 incumbent 明显变差，cap2000 还让 pricing tail 变成 incomplete。

### `mt20_greedy_tranq_01`

| profile | pricing | primal | tail class | incomplete | state max | labels/mask max | min best RC |
|---|---|---:|---|---:|---:|---:|---:|
| baseline | FOUND_NEGATIVE | 721.502279 | profile_dp_negative_tail | 0 | 1001 | 31 | -38.7838905 |
| cap2000 | FOUND_NEGATIVE | 766.373756 | profile_dp_negative_tail | 0 | 2001 | 55 | -57.515033 |
| cap3000 | FOUND_NEGATIVE | 767.053982 | profile_dp_negative_tail | 0 | 3001 | 57 | -59.664038333 |

cap 提高能找到更负的 profile-DP candidate，但没有改善 3s 内 incumbent，反而变差。这说明 cap 增强可能改变列进入顺序并加重 tail，而不是直接提高 ROI。

## 结论

Phase 10B 不支持“简单提高 profile-DP cap”作为主线优化。

证据：

1. 5/10 no-op guard 生效，无 official result change、无 critical disagreement；
2. 20-task cap2000/cap3000 没有稳定减少 incomplete tail；
3. cap3000 增加 profile-DP time；
4. `mt20_greedy_apollo_01` 和 `mt20_greedy_tranq_01` 出现 20-task incumbent 变差；
5. 更负 RC 不等于更好 CG tail，当前问题仍像列选择/状态热点/列池退化，而不是单纯 cap 不够。

## Exactness 边界

- 本轮没有启用 Sharded Pulse worker；
- 没有启用 Pulse audit；
- 没有启用 dual stabilization；
- 没有修改 certificate / official lower-bound 规则；
- cap profile 是 calibration-only、20-task opt-in；
- 5/10 cap profile 直接 no-op。

## 下一步建议

不要继续全局或粗粒度提高 `journey_pricing_max_dp_states`。

下一步应转向 Phase 10C：

- profile-DP mask-hotspot ordering / selected-mask materialization diagnostics；
- 对 top mask hotspots 做更细粒度 attribution；
- 区分“找到更负 RC 但 incumbent 变差”的列池/列顺序问题；
- 继续保持 5/10 no-regression gate 和 certificate 语义不变。

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

本轮最终 focused run：

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
Ran 482 tests in 1.440s
OK (skipped=1)
```

whitespace check：

```bash
git diff --check
```

结果：通过。
