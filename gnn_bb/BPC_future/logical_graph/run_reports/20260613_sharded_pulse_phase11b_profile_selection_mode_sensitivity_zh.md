# Sharded Pulse Phase 11B Profile Selection-mode Sensitivity 报告

日期：2026-06-13

## 目标

Phase 11A 说明粗粒度增加 `journey_pricing_time_limit` 不能稳定改善 profile-DP / legacy proof tail。本轮只测试更窄的 returned-column selection 方向：

- `integer_diverse`
- `orthogonal`

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

- `experimental_profile_selection_integer_diverse_20_only`
- `experimental_profile_selection_orthogonal_20_only`

新增 profile group：

- `phase11b_profile_selection_mode_sensitivity`

profile 行为：

- 只在 `task_count >= 20` 生效；
- 分别设置：
  - `journey_pricing_selection_mode`
  - `journey_heuristic_selection_mode`
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
Ran 483 tests in 1.422s
OK (skipped=1)
```

```bash
git diff --check
```

结果：通过。

## Smoke 矩阵

### 20-task state-cap smoke

输出目录：

- `BPC_future/results/sharded_pulse_phase11b_profile_selection_mode_sensitivity_smoke_20260613`

配置：

- `--pricing-max-dp-states 1`
- `--pricing-time-limit 0.2`
- `--time-limit 3.0`
- `--max-cg-iterations 3`
- repeat-count：2

实例：

- `tranq20_01`
- `mt20_greedy_apollo_01`
- `mt20_greedy_tranq_01`

### 20-task activation smoke

输出目录：

- `BPC_future/results/sharded_pulse_phase11b_profile_selection_mode_sensitivity_state1000_smoke_20260613`

配置：

- `--pricing-max-dp-states 1000`
- `--pricing-time-limit 0.2`
- `--time-limit 3.0`
- `--max-cg-iterations 3`
- repeat-count：2

实例同上。

### 5/10 no-op guard

输出目录：

- `BPC_future/results/sharded_pulse_phase11b_profile_selection_mode_sensitivity_5_10_guard_20260613`

实例：

- `apollo5`
- `tranq5`
- `apollo10`
- `tranq10_09`
- `tranq10_04`

profiles：

- baseline
- `experimental_profile_selection_integer_diverse_20_only`
- `experimental_profile_selection_orthogonal_20_only`

## 5/10 Guard 结果

两个 experimental profiles 均为 no-op：

- rows：15
- `critical_disagreement_count=0`
- `official_result_changed_vs_baseline=False`
- status / pricing_state 与 baseline 一致
- primal 与 baseline 一致

| instance | baseline | integer_diverse | orthogonal |
|---|---:|---:|---:|
| `apollo5` | 183.481234 | 183.481234 | 183.481234 |
| `tranq5` | 199.628855 | 199.628855 | 199.628855 |
| `apollo10` | 470.192861 | 470.192861 | 470.192861 |
| `tranq10_09` | 391.751577 | 391.751577 | 391.751577 |
| `tranq10_04` | 430.098840 | 430.098840 | 430.098840 |

## 20-task State-cap Smoke 结果

这个 smoke 使用 `pricing_max_dp_states=1`，用于确认当前 hard-tail 是否在 selection 前就被 state cap 截断。

结果：

| profile | pricing state | profile-DP tail | selected input/materialized/returned | state-cap hits | critical |
|---|---|---|---:|---:|---:|
| baseline | 6 `INCOMPLETE_LIMIT` | `profile_dp_state_cap_tail` | 0 / 0 / 0 | 18 | 0 |
| integer_diverse | 6 `INCOMPLETE_LIMIT` | `profile_dp_state_cap_tail` | 0 / 0 / 0 | 18 | 0 |
| orthogonal | 6 `INCOMPLETE_LIMIT` | `profile_dp_state_cap_tail` | 0 / 0 / 0 | 18 | 0 |

解释：

- selection mode 没有机会介入；
- tail 在产生可选 negative candidates 前已经撞到 profile-DP state cap；
- 因此这一组不能证明 selection mode 好坏，只说明当前最硬配置的 blocker 早于 returned-column selection。

## 20-task Activation Smoke 结果

这个 smoke 使用 `pricing_max_dp_states=1000`，让 profile-DP 有机会产生候选并进入 selection mode。

整体结果：

| profile | pricing state | improvement class | selected input/materialized/returned | profile-DP time | critical |
|---|---|---|---:|---:|---:|
| baseline | 6 `FOUND_NEGATIVE` | baseline | 72 / 18 / 18 | 0.140670 | 0 |
| integer_diverse | 6 `FOUND_NEGATIVE` | 6 no_regression | 72 / 18 / 18 | 0.146238 | 0 |
| orthogonal | 6 `FOUND_NEGATIVE` | 6 no_regression | 72 / 18 / 18 | 0.139587 | 0 |

关键观察：

- 两个 selection modes 都没有改变 official outcome；
- 仍然全部 `TIME_LIMIT`，没有形成求解加速；
- selected-candidate 计数与 baseline 一致；
- `tranq20_01` 与 `mt20_greedy_apollo_01` 的 returned task-set hash 与 baseline 一致；
- `mt20_greedy_tranq_01` 的一个 orthogonal repeat 返回了不同 task set，从 `[[2,7,10,17]]` 变为 `[[3,4]]`，best RC 也从约 `-35.797866` 变为 `-29.040689`，但 official primal/status 未改善。

## 判断

Phase 11B 不支持把 `integer_diverse` / `orthogonal` selection mode 作为稳定优化主线。

证据：

1. 5/10 guard 有效，未污染小实例；
2. state-cap smoke 中 selection mode 完全没有机会介入；
3. activation smoke 中 selection mode 能运行，但没有减少 tail、没有改善 status、没有改变 official result；
4. orthogonal 在一个 repeat 中确实改变了返回列结构，但没有转化为求解收益；
5. 没有 critical disagreement，也没有 certificate / lower-bound 副作用。

这进一步收窄了 legacy/profile-DP 主线：

- 当前 hard-tail 的主要 blocker 不是简单 returned-column selection；
- 也不是简单 pricing time / state cap / label cap / early quota；
- 后续若继续条件 A，应转向 RMP 退化、列池压缩、或 legacy final judge proof-tail 本身，而不是继续调 selection mode。

## Exactness 边界

- calibration-only；
- 20-only；
- no Sharded Pulse worker；
- no Pulse audit/certificate effect；
- no dual stabilization；
- no production default change；
- no official lower-bound rule change。

## 下一步建议

Phase 11B 又补了一条负证据：

- selection mode 可以改变个别返回列，但没有稳定 ROI；
- 在最硬 cap 下，selection mode 甚至还没机会执行。

建议下一步不要继续扩大 Pulse worker、pricing time、state cap、label cap、early quota 或 selection-mode 调参。更合理的方向是二选一：

1. 若完成最终条件 B：
   - 补 proof-closed resume / refinement-resume 的负证据；
   - 然后输出完整 negative-result / pivot report。
2. 若继续性能路线：
   - 转向 RMP stabilization / pool compression / legacy final judge proof-tail optimization；
   - 不再把 Sharded Pulse worker 作为默认 active path。
