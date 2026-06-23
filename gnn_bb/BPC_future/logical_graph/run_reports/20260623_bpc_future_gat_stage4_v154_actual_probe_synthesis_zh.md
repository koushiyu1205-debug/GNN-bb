# BPC Future GAT Target Mode v154 Stage 4 实测诊断汇总

日期：2026-06-23

## 结论

当前 v154 不应该进入 Stage 4 默认启用或生产 safe-source。

正式 safe-source export 仍是 `safe_source_blocked`：`safe_source_ready=false`，
`safe_candidate_id_count=0`。非 kNN 可修复 blocker 仍是
`raw_pair_pass_rate_below_threshold` 和 `strict_pair_pass_rate_below_threshold`。
本轮后续 Stage 4 运行使用的是 forced diagnostic safe-source，只用于回答
“当前理论最好的 v154 候选放进实际流程表现如何”，不能视为修复 77/78 后的
正式 admission 结果。

实测结果也不支持 opt-in worker 扩大：5/10 no-regression sentinel 通过；
20-task online shadow 有覆盖和 exact-safe-id overlap；但 top8 exact-safe-hit
opt-in A/B 中 `positive_trajectory_roi_count=0`，`negative_primal_roi=2`，
`no_observed_roi=1`。也就是说，v154 的理论安全候选能被实际 worker
物化，但当前没有带来 Stage 4 wall-time / trajectory ROI。

## 机器字段

```text
stage4_v154_actual_probe = current
formal_safe_source_status = safe_source_blocked
formal_safe_source_ready = false
formal_safe_candidate_id_count = 0
forced_diagnostic_safe_source_ready = true
forced_diagnostic_safe_candidate_id_count = 515
forced_diagnostic_override = true
no_regression_5_10_pass = true
online_shadow_events = 92
online_sampled_candidate_journeys = 630
online_unique_signature_ids = 630
exact_safe_id_overlap_count = 113
exact_safe_id_overlap_rate_online = 0.17936507936507937
stage4_model_scored_online_safe_source_ready = false
stage4_mutating_admission_ready = false
optin_ab_command_count = 6
optin_ab_failed_command_count = 0
optin_ab_record_count = 3
optin_ab_roi_class_counts = {'negative_primal_roi': 2, 'no_observed_roi': 1}
optin_ab_positive_trajectory_roi_count = 0
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
```

## Formal 与 Diagnostic 边界

正式导出：

- 输出：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/formal_safe_source_export/safe_source.json`
- 结果：`safe_source_ready=false`，`safe_candidate_id_count=0`
- blocker：`training_validation_non_knn_repairable_reject_reasons`
- 非 kNN blocker：`raw_pair_pass_rate_below_threshold`、`strict_pair_pass_rate_below_threshold`
- 仍然不能 certificate、不能 official bound、不能永久丢弃 true-RC negative。

强制诊断导出：

- 输出：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/forced_diagnostic_safe_source/safe_source.json`
- 结果：`safe_candidate_id_count=515`
- 作用：只作为本轮 Stage 4 shadow / opt-in probe 的候选集合。
- 边界：`forced_diagnostic_override=true`，`production_ready=false`，`default_enabled=false`。

## 5/10 No-Regression

主线 GAT/learning 保持开启，没有启用新 worker。

| scale | instance | status | solving_time | primal=dual | columns | pricing/exact/rmp |
|---|---|---:|---:|---:|---:|---:|
| 5 | apollo15 sector seed2046000 | OPTIMAL | 1.015313 | 284.084294 | 14 | 6 / 4 / 2 |
| 5 | tranquillitatis sector seed2146011 | OPTIMAL | 1.031405 | 179.982081 | 18 | 6 / 4 / 2 |
| 10 | apollo15 sector seed51001 | OPTIMAL | 2.925391 | 456.756326 | 42 | 16 / 11 / 5 |
| 10 | tranquillitatis sector seed51001 | OPTIMAL | 1.698650 | 330.363821 | 71 | 6 / 4 / 2 |

判定：sentinel 通过。这里的 `wall_time` 约 32.6s 主要包含 external-timeout
harness 固定开销，判断 solver 轨迹时看 `solving_time`。

## 20-Task Online Shadow

forced diagnostic safe-source 下，5 个 task020 shadow capture 的结果如下：

| instance | status | solving_time | wall_time | primal | columns | pricing/exact/rmp |
|---|---:|---:|---:|---:|---:|---:|
| sector/apollo seed61715 | TIME_LIMIT | 52.318019 | 54.700280 | 744.848595 | 218 | 13 / 7 / 6 |
| sector/tranq seed61513 | TIME_LIMIT | 59.051556 | 61.427438 | 639.119548 | 252 | 16 / 7 / 9 |
| greedy/apollo seed61308 | EXTERNAL_TIME_LIMIT | - | 85.026279 | - | - | - |
| random/tranq seed61615 | TIME_LIMIT | 68.299230 | 70.499091 | 548.335796 | 470 | 23 / 9 / 14 |
| random/apollo seed61715 | TIME_LIMIT | 67.765529 | 70.024597 | 619.142683 | 240 | 23 / 11 / 12 |

coverage audit：

- `online_shadow_events=92`
- `online_declared_candidate_journeys=776`
- `online_sampled_candidate_journeys=630`
- `online_unique_signature_ids=630`
- `exact_safe_id_overlap_count=113`
- `exact_safe_id_overlap_rate_online=0.17936507936507937`
- `online_sample_coverage_complete=false`

model-scored online audit：

- `stage4_model_scored_online_safe_source_ready=false`
- `stage4_mutating_admission_ready=false`
- blocker：`exact_safe_id_overlap_is_not_trajectory_roi_proof`、
  `coarse_key_evidence_is_diagnostic_only`、`online_trajectory_roi_unverified`

## Opt-In A/B

候选来源：`v154_exact_safe_hit_target_candidates_top8/candidates.json`。
8 个 exact-safe-id hit 候选按同 context 合并成 3 组，`worker_batch_size=4`。
执行命令使用 `summary_python313.json`，只替换 Python 路径为
`/home/kai/miniconda3/bin/python`，未改 runbook 逻辑。

执行结果：

- command count：6
- failed command count：0
- all commands executed
- worker 日志均出现 `pricing_kind=sharded_pulse_hidden_negative_worker`
  和 `reason=target_materialized_negative_true_rc`
- 三组分别物化 2 / 4 / 2 条 target candidate，`pulse_target_sequence_materialized=true`

审计结果：

| group | roi_class | baseline primal | worker primal | primal improvement | baseline time | worker time | columns delta | pricing delta | exact delta | rmp delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ctxdd1c3812 tasks2_3_8_18 batch2 | negative_primal_roi | 639.119548 | 689.646995 | -50.527447 | 59.251771 | 58.372215 | +18 | 0 | +2 | -1 |
| ctxb095fbae tasks3_8_18_20 batch4 | no_observed_roi | 744.848595 | 744.848595 | 0.000000 | 52.325700 | 52.260580 | -36 | 0 | 0 | 0 |
| ctxea2f1344 tasks1_11 batch2 | negative_primal_roi | 639.119548 | 643.478120 | -4.358572 | 59.025268 | 59.987742 | -35 | +2 | 0 | +2 |

合计：

- `positive_trajectory_roi_count=0`
- `nonpositive_roi_count=3`
- total primal improvement = `-54.886019`
- total solving_time_delta = `+0.017798`
- total columns_delta = `-53`
- total pricing_calls_delta = `+2`
- total exact_pricing_calls_delta = `+2`
- total rmp_solves_delta = `+1`

解读：worker 确实能把 v154 候选物化成 true-RC negative columns，但当前
candidate priority 不等于实际 ROI。两组 primal 明显变差；一组 primal 持平且
columns 减少，但没有 pricing / exact / RMP 改善，审计只能判为 `no_observed_roi`。

## 当前判断

v154 当前的 Stage 4 实测表现是：

1. 小规模 5/10 sentinel 没看到 no-regression 问题。
2. 20-task shadow 有候选覆盖，且 forced safe ids 与 online candidates 有 113 个 overlap。
3. model-scored online safe-source 仍不能转成 mutating admission。
4. opt-in target materialization 确实触发，但 top8 exact-safe-hit A/B 没有正 ROI。

所以当前不应继续扩大 v154 Stage 4 worker，也不应把 forced diagnostic safe-source
改成默认安全源。下一步如果继续这条线，重点不是先把 77/78 补成 78/78 后直接上
Stage 4，而是要增加一个“trajectory ROI selector / context admission selector”：
同一个 exact-safe-id hit 必须再证明在当前 active basis、cut、branch、pool context 下
不会拖慢 primal trajectory，才允许 opt-in worker。

## 产物

- formal safe-source：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/formal_safe_source_export/safe_source.json`
- forced diagnostic safe-source：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/forced_diagnostic_safe_source/safe_source.json`
- 5/10 sentinel：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/task005_mainline_no_regression_gat_kept/results.csv`，`BPC_future/results/gat_stage4_v154_actual_probe_20260623/task010_mainline_no_regression_gat_kept/results.csv`
- 20 shadow capture：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/task020_v154_online_shadow_capture/results.csv`
- online coverage audit：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_online_coverage_audit/summary.json`
- model-scored online audit：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_model_scored_online_safe_source/summary.json`
- opt-in A/B runbook：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/summary_python313.json`
- opt-in A/B execution：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_runbook_top8/runbook_execution_summary_python313.json`
- opt-in A/B audit：`BPC_future/results/gat_stage4_v154_actual_probe_20260623/v154_exact_safe_hit_optin_ab_audit_top8/summary.json`
