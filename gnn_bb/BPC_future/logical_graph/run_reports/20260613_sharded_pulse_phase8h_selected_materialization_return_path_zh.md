# Sharded Pulse Phase 8H selected materialization / return path 诊断报告

日期：2026-06-13

## 目标

Phase 8G 显示 Apollo20 worker 后 follow-up first negative `5,8,15` 已经出现在 profile-DP 的 reachable / negative / selected task-set samples 中。

Phase 8H 只回答一个问题：

`5,8,15` 是 selected 后在 materialization / true-RC / duplicate / forbidden / dominated / return-limit path 中丢失，还是确实被 ordinary follow-up pricing 返回了？

本轮不改变求解语义。

## 实现摘要

### 1. Selected candidate return-path diagnostics

`JourneyPricingResult` 新增只读字段：

- `profile_selected_candidate_input_count`
- `profile_selected_candidate_scanned_count`
- `profile_selected_candidate_materialized_count`
- `profile_selected_candidate_returned_count`
- `profile_selected_candidate_branch_filtered_count`
- `profile_selected_candidate_duplicate_signature_filtered_count`
- `profile_selected_candidate_duplicate_task_set_filtered_count`
- `profile_selected_candidate_forbidden_signature_filtered_count`
- `profile_selected_candidate_dominated_task_set_filtered_count`
- `profile_selected_candidate_return_limit_truncated_count`

新增 sample 字段：

- `diagnostic_selected_materialized_task_set_samples`
- `diagnostic_selected_returned_task_set_samples`
- `diagnostic_selected_unmaterialized_task_set_samples`
- `diagnostic_selected_weak_filtered_task_set_samples`
- `diagnostic_selected_filtered_task_set_samples`

这些字段在 `_instantiate_profile_journey_candidates()` 的 selected-candidate loop 中记录。

### 2. Driver / ROI summary 接线

`journey_pricing` JSONL 事件现在输出上述字段。

ROI summary 新增：

- `followup_first_negative_profile_materialized_*`
- `followup_first_negative_profile_returned_*`
- `followup_first_negative_profile_unmaterialized_*`
- `followup_first_negative_profile_weak_filtered_*`
- `followup_first_negative_profile_filtered_*`
- `followup_profile_selected_candidate_*`

并提供对应 `pulse_worker_followup_*` 别名。

## Probe

输出目录：

- `BPC_future/results/sharded_pulse_phase8h_selected_materialization_cap1000_probe_20260613`

配置：

- instance: `mt20_greedy_apollo_01`
- profile: `strict_worker_delayed_current_probe_impact_20_only_pre_heuristic_followup_same_iter_rc_gate_failure_cooldown`
- `time_limit=1.5`
- `pricing_time_limit=0.2`
- `pricing_max_dp_states=1000`
- `max_cg_iterations=3`
- `current_probe_time_limit=0.5`
- `profile-mask-diagnostics=True`

## 关键结果

Summary 中 worker profile：

| 字段 | 值 |
|---|---:|
| worker_added_journeys | `1` |
| followup_first_negative_task_set | `5,8,15` |
| selected exact | `True` |
| materialized exact | `True` |
| returned exact | `True` |
| unmaterialized exact | `False` |
| weak-filtered exact | `False` |
| filtered exact | `False` |
| followup selected candidate input | `8` |
| scanned | `2` |
| materialized | `2` |
| returned | `2` |
| filtered | `0` |
| return-limit truncated | `6` |

JSONL 中 cg_iter=1 ordinary heuristic：

```text
negative_journey_task_set_samples = [[5, 8, 15]]
diagnostic_selected_materialized_task_set_samples = [[5, 8, 15]]
diagnostic_selected_returned_task_set_samples = [[5, 8, 15]]
profile_selected_candidate_input_count = 4
profile_selected_candidate_scanned_count = 1
profile_selected_candidate_materialized_count = 1
profile_selected_candidate_returned_count = 1
profile_selected_candidate_return_limit_truncated_count = 3
```

## 结论

`5,8,15` 没有在 ordinary follow-up materialization / return path 中丢失。

它在 ordinary heuristic follow-up 中完整经过：

1. selected；
2. materialized；
3. true-RC accepted；
4. returned；
5. 后续 `journey_column_addition` 加入 pool。

因此 Phase 8G 的下一步假设需要修正：

问题不是 ordinary follow-up selected negative 没有返回，而是 Pulse worker 当前加入 `[6,19]` 后，ordinary follow-up 仍能立即找到 residual negative `[5,8,15]`。这说明 worker 加列没有覆盖或消除该 residual family。

当前主因仍更接近：

- worker 子空间覆盖不足；
- worker candidate ordering 与 ordinary profile-DP negative family 不一致；
- worker 返回列对后续 RMP / dual context 影响不足；
- return-limit truncation 说明 ordinary follow-up 每轮只返回 selected negatives 中最前若干个，但首个 residual 本身已经返回，不是被 truncation 丢掉。

## Exactness 边界

- 只读诊断；
- 不改变 profile-DP transition；
- 不改变 selected candidate ordering；
- 不改变 materialization；
- 不改变 true-RC filter；
- 不改变 RMP insertion；
- 不改变 Pulse worker trigger；
- 不改变 official certificate / lower-bound 语义。

## 验证

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
BPC_future.tests.test_bpc_future.BPCFutureTests.test_journey_profile_instantiation_filters_existing_signature \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_profile_journey_instantiation_counts_true_rc_filtered_candidate_as_weak \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed
```

结果：

```text
Ran 4 tests in 0.003s
OK
```

完整回归：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests
```

结果：

```text
Ran 477 tests in 51.738s
OK (skipped=1)
```

`git diff --check`：通过。

## 下一步建议

不要继续查 ordinary selected materialization path。

下一步建议进入 Phase 8I：worker-vs-ordinary candidate family contrast。

目标是比较同一 context 下：

- Pulse worker returned `[6,19]`
- ordinary follow-up returned `[5,8,15]`

之间的差异来自：

1. task-set ordering；
2. start-time / arc-option domain；
3. Pulse transition DFS deadline；
4. profile-DP rough objective vs true-RC ranking；
5. RMP dual context after worker add-column 的变化。

仍不要开启 production worker、official certificate gate、resume、parallel 或 20/100 A/B。
