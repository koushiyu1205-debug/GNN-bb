# Sharded Pulse Phase 11A Profile-DP Pricing-time Sensitivity 报告

日期：2026-06-13

## 目标

Phase 10I 审计后，Pulse active-worker、profile-DP cap / label-cap、early-column quota 都没有形成稳定 ROI。本轮转向 legacy/profile-DP proof-tail 的一个最小问题：

增加 pricing time limit 是否能减少 20-task `profile_dp_incomplete_tail`，还是只增加耗时并扰动列轨迹？

本轮不做：

- Sharded Pulse worker；
- Pulse audit；
- dual stabilization；
- official certificate gate；
- production default；
- resume / parallel；
- unsafe bound 或 cut contribution 改动。

## 实现摘要

新增 20-only calibration profiles：

- `experimental_pricing_time_0_6_20_only`
- `experimental_pricing_time_1_0_20_only`

新增 profile group：

- `phase11a_profile_pricing_time_sensitivity`

profile 行为：

- 只在 `task_count >= 20` 生效；
- 分别设置 `journey_pricing_time_limit=0.6` / `1.0`；
- 显式关闭：
  - `journey_sharded_pulse_audit_enabled`
  - `journey_sharded_pulse_hidden_negative_worker_enabled`
  - `journey_dual_stabilization_enabled`

默认 benchmark 行为不变。

## Focused Tests

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

结果：通过。

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_profile_configs_are_opt_in
```

结果：

```text
Ran 2 tests in 0.002s
OK
```

## Full Regression

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 483 tests in 1.448s
OK (skipped=1)
```

```bash
git diff --check
```

结果：通过。

## Smoke 矩阵

### 20-task pricing-time sensitivity

输出目录：

- `BPC_future/results/sharded_pulse_phase11a_profile_pricing_time_sensitivity_smoke_20260613`

矩阵：

- instances：
  - `tranq20_01`
  - `mt20_greedy_apollo_01`
  - `mt20_greedy_tranq_01`
- profiles：
  - baseline (`journey_pricing_time_limit=0.3`)
  - `experimental_pricing_time_0_6_20_only`
  - `experimental_pricing_time_1_0_20_only`
- repeat-count：2
- rows：18

### 5/10 no-op guard

输出目录：

- `BPC_future/results/sharded_pulse_phase11a_profile_pricing_time_sensitivity_5_10_guard_20260613`

矩阵：

- instances：
  - `apollo5`
  - `tranq5`
  - `apollo10`
  - `tranq10_09`
  - `tranq10_04`
- profiles：
  - baseline
  - `experimental_pricing_time_0_6_20_only`
  - `experimental_pricing_time_1_0_20_only`
- repeat-count：1
- rows：15

## 5/10 Guard 结果

两个 experimental profiles 均为 no-op：

- `official_result_changed_vs_baseline=False`
- `critical_disagreement_count=0`
- status / pricing_state 与 baseline 一致
- primal 与 baseline 完全一致

| instance | baseline | 0.6s profile | 1.0s profile |
|---|---:|---:|---:|
| `apollo5` | 165.623455 | 165.623455 | 165.623455 |
| `tranq5` | 180.521929 | 180.521929 | 180.521929 |
| `apollo10` | 405.125490 | 405.125490 | 405.125490 |
| `tranq10_09` | 391.751577 | 391.751577 | 391.751577 |
| `tranq10_04` | 361.939751 | 361.939751 | 361.939751 |

## 20-task 结果

整体分布：

| profile | pricing state | improvement class | profile-DP incomplete sum | state-cap hits | profile-DP time |
|---|---|---|---:|---:|---:|
| baseline | 4 `INCOMPLETE_LIMIT`, 2 `FOUND_NEGATIVE` | baseline | 4 | 29 | 0.391099 |
| 0.6s | 6 `INCOMPLETE_LIMIT` | 4 improved, 2 worsened | 6 | 30 | 0.581605 |
| 1.0s | 6 `INCOMPLETE_LIMIT` | 1 improved, 5 worsened | 6 | 20 | 0.498347 |

关键结论：

- 增加 pricing time 没有减少 incomplete；
- baseline 的 2 行 `FOUND_NEGATIVE` 在 0.6s / 1.0s profiles 中都变成 `INCOMPLETE_LIMIT`；
- 0.6s 有 4 行 incumbent 改善，但 wall time 全部接近 3s time limit；
- 1.0s 大多回退；
- 没有 critical disagreement；
- 没有 certificate / lower-bound 语义变化。

## 20-task 明细

### `tranq20_01`

- baseline：两次 `781.101309`
- 0.6s：两次 `676.808421`，incumbent 改善但仍 `INCOMPLETE_LIMIT`
- 1.0s：两次 `781.398505`，回退

### `mt20_greedy_apollo_01`

- baseline：`921.640296`, `847.812231`
- 0.6s：两次 `837.187019`，一行从 921 改善、一行相对 847 回退
- 1.0s：两次 `849.288754`，一行改善、一行回退

### `mt20_greedy_tranq_01`

- baseline：两次 `761.814403`，均 `FOUND_NEGATIVE`
- 0.6s：两次 `761.814403`，但 pricing 变为 `INCOMPLETE_LIMIT`
- 1.0s：两次 `829.395319`，明显回退且 pricing 变为 `INCOMPLETE_LIMIT`

## 判断

Phase 11A 不支持“简单增加 `journey_pricing_time_limit`”作为 legacy/profile-DP proof-tail 优化。

证据：

1. 5/10 profile guard 有效，未污染小实例；
2. 20-task incomplete 数量没有下降，反而从 4/6 增至 6/6；
3. `FOUND_NEGATIVE` 行被更多 pricing 时间扰动成 `INCOMPLETE_LIMIT`；
4. 0.6s 的部分 incumbent 改善不是 proof-tail 改善，且伴随 wall time 触顶；
5. 1.0s 大多回退。

这条结果进一步支持：

- 不继续扩大 Pulse worker；
- 不继续扩大 profile-DP cap / label-cap；
- 不简单增加 pricing time；
- 下一步若继续追求条件 A，应关注更结构化的 legacy/profile-DP candidate ordering 或 RMP/column trajectory，而不是粗粒度预算扩张。

## Exactness 边界

- calibration-only；
- 20-only；
- no Sharded Pulse worker；
- no audit/certificate effect；
- no dual stabilization；
- no production default change；
- no official lower-bound rule change。

## 下一步建议

当前又多了一条负证据：

- proof-tail 不是单纯 pricing time 不够；
- 增加 pricing time 会改变列进入顺序，并可能把 negative-returning path 变成 incomplete path。

下一步建议：

1. 若继续 legacy/profile-DP：
   - 做 candidate ordering / returned-column selection 的结构化实验；
   - 不增加全局 time/state cap。
2. 若继续完成最终条件 B：
   - 将 Phase 10I + 11A 作为 proof-tail / worker / budget 扩张无 ROI 的证据；
   - 仍需处理 proof-closed resume 未实现/未验证的缺口。
