# Sharded Pulse Phase 8I Worker-vs-Ordinary Candidate Family Contrast 报告

日期：2026-06-13

## 目标

Phase 8I 只做 worker 与 ordinary follow-up 的候选族对比诊断。

本轮不改变：

- production worker 默认开关；
- Pulse worker trigger；
- profile-DP / Pulse transition；
- materialization / true-RC filter；
- RMP insertion；
- official certificate / lower-bound 语义。

## 实现摘要

在 `BPC_future/scripts/run_sharded_pulse_roi_calibration.py` 新增只读 summary 字段：

- `worker_vs_ordinary_first_worker_task_set`
- `worker_vs_ordinary_first_followup_task_set`
- `worker_vs_ordinary_task_set_overlap`
- `worker_vs_ordinary_task_set_jaccard`
- `worker_vs_ordinary_task_set_relation`
- `worker_vs_ordinary_disjoint`
- `worker_vs_ordinary_worker_task_count`
- `worker_vs_ordinary_followup_task_count`
- `worker_vs_ordinary_task_count_delta`
- `worker_vs_ordinary_worker_added_before_followup`
- `worker_vs_ordinary_followup_returned_after_worker`
- `worker_vs_ordinary_contrast_class`

并提供对应 `pulse_worker_vs_ordinary_*` alias，便于从 CSV 直接筛选。

`contrast_class` 当前只做分类：

- `no_worker_add`
- `no_followup_negative`
- `same_task_set`
- `overlapping_task_set`
- `disjoint_residual_after_worker`
- `unknown_worker_task_set`
- `unknown`

## Probe

输出目录：

- `BPC_future/results/sharded_pulse_phase8i_worker_vs_ordinary_contrast_probe_20260613`

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

| 字段 | 值 |
|---|---:|
| worker_added_journeys | `1` |
| worker_vs_ordinary_first_worker_task_set | `6,19` |
| worker_vs_ordinary_first_followup_task_set | `5,8,15` |
| worker_vs_ordinary_task_set_overlap | `0` |
| worker_vs_ordinary_task_set_jaccard | `0.0` |
| worker_vs_ordinary_task_set_relation | `disjoint_task_set` |
| worker_vs_ordinary_contrast_class | `disjoint_residual_after_worker` |
| followup_first_negative_sequence | `8,15,5` |
| followup_first_negative_best_rc | `-139.913748` |
| followup_first_negative_profile_selected_exact | `True` |
| followup_first_negative_profile_materialized_exact | `True` |
| followup_first_negative_profile_returned_exact | `True` |
| followup_profile_selected_candidate_input_count | `12` |
| followup_profile_selected_candidate_scanned_count | `3` |
| followup_profile_selected_candidate_materialized_count | `3` |
| followup_profile_selected_candidate_returned_count | `3` |
| followup_profile_selected_candidate_return_limit_truncated_count | `9` |
| pulse_worker_next_rmp_objective_delta | `-171.465431` |
| critical_disagreement_count | `0` |

## 结论

Phase 8I 把 8H 的人工判断转成了 summary 字段：

- Pulse worker 首个加入的 task-set 是 `[6,19]`；
- worker 后 ordinary follow-up 首个 negative 是 `[5,8,15]`；
- 两者 task-set 完全 disjoint；
- ordinary follow-up 的 `[5,8,15]` 已经被 selected、materialized、returned，后续通过正常 add-column path 加入；
- 因此当前 ROI 缺口不是 ordinary materialization path 丢列，而是 worker 首列没有覆盖 / 消除 residual negative family。

这仍不是 production ROI 正信号，也不是 certificate 信号。

## 下一步建议

下一步应做 Phase 8J：worker 内部候选族覆盖 / 停止条件诊断。

只回答：

- 同一 worker context 中，除了 `[6,19]`，是否也存在 `[5,8,15]` 或相近 residual family；
- 当前 `stop_after_first_negative` / impact filter / task ordering 是否让 worker 过早停在 inactive disjoint column；
- 如果 worker 多返回少量候选，是否能覆盖 residual family。

仍然不要做：

- production worker 默认开启；
- official certificate gate；
- resume / parallel；
- 20/100 A/B；
- 单纯扩大 worker time limit。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/run_sharded_pulse_roi_calibration.py \
BPC_future/tests/test_bpc_future.py
```

Focused tests：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_phase7o_profiles_and_fields \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_worker_followup_metrics_are_attributed \
BPC_future.tests.test_bpc_future.BPCFutureTests.test_sharded_pulse_roi_calibration_pivot_classifier
```

结果：

```text
Ran 3 tests in 0.001s
OK
```
