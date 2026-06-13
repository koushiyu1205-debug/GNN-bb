# Sharded Pulse Phase 8G residual profile-mask visibility 报告

日期：2026-06-13

## 目标

本轮只做 residual 候选可见性诊断。

Phase 8F 已证明 Apollo20 follow-up residual negative `5,8,15` 不是 profile-DP top overloaded mask 的 exact hit。Phase 8G 进一步确认它到底是：

1. 完全不在 profile universe；
2. 在 reachable mask 里但没有 negative；
3. negative 但未 selected；
4. 已 selected，但后续未被 materialize / 返回。

本轮不改变 pricing、worker、RMP、certificate 行为。

## 实现摘要

### 1. Profile mask sample diagnostics

`JourneyPricingResult` 新增 opt-in 诊断字段：

- `diagnostic_profile_task_set_samples`
- `diagnostic_reachable_task_set_samples`
- `diagnostic_negative_task_set_samples`
- `diagnostic_selected_task_set_samples`

这些字段由 `diagnostic_*_task_masks` 解码得到，使用 `data.tasks` 将 bitmask 转为 task tuple，并做有上限采样。

默认配置下这些字段为空，不扩大默认日志。

### 2. JSONL 与 ROI summary 接线

`journey_pricing` JSONL 事件现在在 diagnostics enabled 时带出 task-set samples。

ROI summary 新增 residual follow-up overlap 字段：

- `followup_first_negative_profile_reachable_*`
- `followup_first_negative_profile_negative_*`
- `followup_first_negative_profile_selected_*`
- 对应 `pulse_worker_followup_*` 别名

这些字段只用于报告归因，不参与求解决策。

### 3. 显式 CLI 开关

`run_sharded_pulse_roi_calibration.py` 新增：

```bash
--profile-mask-diagnostics
```

不传该开关时，不启用 `journey_pricing_profile_mask_diagnostics_enabled`。

## Probe 结果

运行目录：

- `BPC_future/results/sharded_pulse_phase8g_residual_profile_mask_cap1000_probe_20260613`
- `BPC_future/results/sharded_pulse_phase8g_residual_profile_mask_cap5000_probe_20260613`

实例与配置：

- `mt20_greedy_apollo_01`
- profile: `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`
- `time_limit=1.5`
- `pricing_time_limit=0.2`
- `max_cg_iterations=3`
- `current_probe_time_limit=0.5`
- `profile-mask-diagnostics=True`

### cap1000

| 指标 | 值 |
|---|---:|
| worker_added_journeys | 1 |
| follow-up first negative | `5,8,15` |
| top-mask exact | `False` |
| top-mask overlap / jaccard | `2 / 0.5` |
| reachable exact | `True` |
| negative exact | `True` |
| selected exact | `True` |
| dp_nonempty_mask_count | `132` |
| dp_max_labels_per_mask_observed | `24` |

### cap5000

| 指标 | 值 |
|---|---:|
| worker_added_journeys | 1 |
| follow-up first negative | `5,8,15` |
| top-mask exact | `False` |
| top-mask overlap / jaccard | `2 / 0.333333333` |
| reachable exact | `True` |
| negative exact | `True` |
| selected exact | `True` |
| dp_nonempty_mask_count | `414` |
| dp_max_labels_per_mask_observed | `63` |

## 结论

Residual `5,8,15` 不是 top overloaded mask，但它已经出现在 profile-DP 的 reachable、negative、selected task-set samples 中。

这说明当前 residual tail 不是简单的“DP 没看到该 task set”，也不是“只要 materialize top overloaded masks 就能解决”。更可能的问题在：

1. selected candidate 没有被最终 materialize / 返回；
2. ordinary pricing 返回策略或 materialization cap 没覆盖该 selected negative；
3. worker 加列后 active context 仍保留 residual true-RC negative，说明 worker 列对 tail 的影响不足。

## Exactness 边界

- 本轮只添加诊断字段；
- 不改变 DP transition；
- 不改变 pruning；
- 不改变 candidate selection；
- 不改变 RMP column insertion；
- 不改变 official certificate / lower-bound 语义；
- diagnostics 默认关闭，只有显式 `--profile-mask-diagnostics` 打开。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/pricing/journey_pricing.py \
BPC_future/solver/journey_driver.py \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_profile_mask_diagnostics_default_to_empty \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 3 tests in 0.001s
OK
```

完整回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 477 tests in 1.430s
OK (skipped=1)
```

`git diff --check`：通过。

## 下一步建议

不要继续沿 top-mask-only materialization 方向推进。下一步应做 Phase 8H：selected negative materialization / return path attribution。

建议只回答一个问题：

`5,8,15` 既然已经 selected，为什么 ordinary follow-up pricing 没把它作为 returned journey 加回 RMP？

优先检查：

1. selected candidate materialization cap；
2. true-RC materialization scan order；
3. duplicate / forbidden / dominated task-set filter；
4. weak true-RC filter；
5. selected profile 到 JourneyColumn 物化失败原因。

仍不要开启 production worker、official certificate gate、resume、parallel 或 20/100 A/B。
