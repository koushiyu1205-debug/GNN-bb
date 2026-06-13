# Sharded Pulse Phase 7P Follow-up Profile-DP Incomplete Attribution 报告

日期：2026-06-13

## 目标

本轮不继续扩大 Pulse worker，也不做 official certificate gate。

目标是解释 Phase 7P tail outcome 中的后续 exact tail：

- worker 加列后，follow-up pricing 为什么仍然 `INCOMPLETE_LIMIT`；
- `profile_dp_incomplete` 是 DP 状态上限、还是 best-RC 仍有负值、还是未知；
- 所有新增内容只作为日志和 ROI 汇总诊断，不改变求解行为、不影响证书语义。

## 实现摘要

### 1. Journey pricing 日志补配置上下文

`journey_pricing` JSONL 新增：

- `pricing_max_dp_states`
- `pricing_profile_generation_time_fraction`

这两个字段来自当前 `JourneyPricingConfig`，只用于后处理判断 profile-DP incomplete 是否触及 state cap。

### 2. Calibration CLI 补 DP cap override

`run_sharded_pulse_roi_calibration.py` 新增：

- `--pricing-max-dp-states`

默认仍为 `1`，保持既有快速 gate 行为不变。只有显式传参时才提高 DP cap，用于 sensitivity smoke。

### 3. ROI 汇总新增 follow-up profile-DP 字段

`run_sharded_pulse_roi_calibration.py` 新增 worker 后续诊断字段：

- `followup_profile_dp_incomplete_count`
- `followup_profile_dp_incomplete_class`
- `followup_profile_dp_state_count_max`
- `followup_profile_dp_processed_labels_max`
- `followup_profile_dp_extension_attempts`
- `followup_profile_dp_time`
- `followup_profile_dp_state_cap_hit`
- `followup_profile_dp_min_best_rc`

并提供对应 `pulse_worker_followup_*` 别名，便于 CSV/JSONL 后处理。

### 4. 归因分类

新增分类逻辑：

- `no_worker_add`
- `no_profile_dp_incomplete`
- `profile_dp_state_cap_hit`
- `profile_dp_negative_best_rc_incomplete`
- `profile_dp_near_zero_best_rc_incomplete`
- `profile_dp_positive_best_rc_incomplete`
- `profile_dp_unknown_best_rc_incomplete`

分类只读取 worker 加列后的 `journey_pricing` 事件。

注意：`profile_dp_incomplete_class` 只使用 `profile_dp_incomplete` 记录自身的 `best_reduced_cost`，不会被同一 follow-up 窗口里更早的 `FOUND_NEGATIVE` 事件污染。

## Single Smoke 结果

命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7p_profile_dp_incomplete_single_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate \
  --time-limit 0.3 \
  --pricing-time-limit 0.12
```

关键观测：

| profile | worker added | follow-up pricing | tail outcome | profile-DP class | min best RC |
|---|---:|---:|---|---|---:|
| baseline | 0 | 0 | `no_worker_add` | `no_worker_add` | - |
| active-gate | 1 | 2 | `followup_incomplete_positive_best_rc` | `profile_dp_state_cap_hit` | `0.034526` |

active-gate 额外字段：

- `followup_profile_dp_incomplete_count=2`
- `followup_profile_dp_state_count_max=2`
- `followup_profile_dp_processed_labels_max=1`
- `followup_profile_dp_extension_attempts=2`
- `followup_profile_dp_time=0.002141`
- `followup_profile_dp_state_cap_hit=True`
- `followup_profile_dp_min_best_rc=0.034526`
- `critical_disagreement_count=0`

解释：默认 calibration gate 的 `journey_pricing_max_dp_states=1`，因此这里的 state-cap 命中是超短 smoke 配置导致的，不应直接解释为生产求解器固有瓶颈。

## DP Cap Sensitivity

追加运行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
  --output-dir BPC_future/results/sharded_pulse_phase7p_profile_dp_incomplete_dp1000_single_20260613 \
  --instances mt20_greedy_apollo_01 \
  --profiles baseline strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_reserve_active_gate \
  --time-limit 0.3 \
  --pricing-time-limit 0.12 \
  --pricing-max-dp-states 1000
```

关键观测：

| profile | official pricing | worker added | follow-up tail | profile-DP class | profile-DP min best RC |
|---|---|---:|---|---|---:|
| baseline | `FOUND_NEGATIVE` | 0 | `no_worker_add` | `no_worker_add` | - |
| active-gate | `INCOMPLETE_LIMIT` | 1 | `followup_found_negative` | `profile_dp_unknown_best_rc_incomplete` | - |

解释：提高 DP cap 后，baseline 在同一短预算下能找到负列；active-gate 仍加 1 列，follow-up 中也观察到负列，但最终 official pricing 仍以 `INCOMPLETE_LIMIT` 结束。这说明下一步应分析 worker 后列加入与 legacy/heuristic tail 调度的交互，而不是简单继续提高 Pulse worker 预算。

## 验证

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 2 tests in 0.006s
OK
```

语法与 diff 检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py

git diff --check
```

结果：通过。

完整回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future
```

结果：

```text
Ran 459 tests in 1.401s
OK (skipped=1)
```

## 当前边界

- 未改变 solver 决策；
- 未改变 worker 触发；
- 未改变 official certificate / dual bound 规则；
- 未默认启用 Pulse worker；
- 未做 resume / parallel / official certificate gate；
- 未把 `profile_dp_state_cap_hit` 当作数学证明，只作为后处理归因。
- `--pricing-max-dp-states` 只影响 calibration 脚本配置，不改变默认 solver 配置。

## 结论

本轮把 worker 后 `profile_dp_incomplete` 从一个泛化 reason 拆成可观测归因。`mt20_greedy_apollo_01` single smoke 显示：

- 默认超短 gate 下，后续 incomplete 是人为 DP cap 命中；
- 提高 DP cap 后，baseline 可找到负列，active-gate 仍最终 incomplete；
- Pulse worker 能加列，但当前证据仍不支持扩大 worker 或开启 official certificate。

下一步不建议继续提高 worker time limit。更合理的方向是：

1. 分析 worker 加列后为什么会改变后续 heuristic/exact tail 的闭合轨迹；
2. 或转向 legacy final judge / RMP degeneracy 路线，判断 worker 加列后为什么仍不能稳定减少 tail。
