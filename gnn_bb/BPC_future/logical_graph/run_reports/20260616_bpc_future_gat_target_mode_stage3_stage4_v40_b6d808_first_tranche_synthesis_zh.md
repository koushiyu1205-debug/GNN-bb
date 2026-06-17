# 2026-06-16 BPC_future GAT Stage 3/4 v40 b6d808 First-tranche 综合报告

## 读取范围

本轮继续复读 `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`、Stage 1/2 报告、v15 missed high-ROI / hard-negative 结论、v38 neighbor-ROI runbook 桥接报告、Stage 4 v14 A/B 与 certificate audit、以及 Stage 5 20/30/50/100 scale acceleration 目标。

结论边界不变：GAT / CBF / kNN / OOD 只能做 discovery / ordering / finite-delay admission scheduling；进入 RMP 的列必须 true-RC verified；最终 OPTIMAL certificate 只能来自当前 branch/cut/dual 下的 full exact pricing no-negative closure。

## 本轮执行

从 v38 runbook 中选择最高 opportunity context：

```text
context = b6d808ebac2a6dd8
instance = BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_08_seed61715_logical_graph.json
candidate_count = 4
opportunity_score = 41.318527
```

执行命令为 first-tranche 小批：

```text
execution_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v37_neighbor_roi_task20_contrast_20260616/worker_ab_runbook/first_tranche_b6d808_execution_summary.json

command_count = 7
executed_count = 7
failed_command_count = 0
elapsed_s = 302.790953
runs_bpc_or_pricing = true
official_bound_effect = false
certificate_ready = false
```

其中 2 条是 5/10 sentinel，5 条是 task20 baseline + 4 个 target-materialization worker。为了避免重复 baseline 成本，只执行了 `mb1` baseline；后续 A/B audit 对同 instance 的其余 3 个 worker 使用 baseline fallback。

## 5/10 No-regression

5/10 sentinel 均成功写出结果，4 个小规模实例均为 `OPTIMAL`：

```text
task005_mainline_no_regression_gat_kept = 2 / 2 OPTIMAL
task010_mainline_no_regression_gat_kept = 2 / 2 OPTIMAL
```

这只说明本轮显式 opt-in 小批没有破坏 5/10 sentinel；它不是 production no-regression matrix 的完整替代。

## Task20 A/B 结果

A/B audit：

```text
audit_summary =
  BPC_future/results/gat_target_priority_worker_ab_v38_first_tranche_b6d808_audit_20260616/summary.json
audit_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v38_first_tranche_b6d808_ab_audit_zh.md

record_count = 4
positive_trajectory_roi_count = 0
nonpositive_roi_count = 3
roi_class_counts = {'columns_only_roi': 1, 'negative_retry_roi': 1, 'no_observed_roi': 2}
all_checks_pass = false
next_decision = collect_more_ab_evidence
official_bound_effect = false
certificate_ready = false
```

四个 worker 与 baseline 一样都是 `TIME_LIMIT`，都没有 official dual bound，primal 都停在 `744.848595`。差异只体现在 workload：

| target | ROI class | primal improvement | exact delta | pricing delta | rmp delta | generated delta | columns delta |
|---|---|---:|---:|---:|---:|---:|---:|
| `[16, 19]` | `columns_only_roi` | 0.0 | 0 | +1 | +1 | +2812 | +10 |
| `[1, 2, 8]` | `no_observed_roi` | 0.0 | 0 | 0 | 0 | -101 | -23 |
| `[5, 19]` | `no_observed_roi` | 0.0 | 0 | 0 | 0 | -21 | -21 |
| `[5, 13, 20]` | `negative_retry_roi` | 0.0 | +1 | +2 | +1 | +2774 | +22 |

因此，最高 opportunity context 的 4 个 target-materialization 候选没有产生正 trajectory ROI；其中 1 个还明确增加 retry / pricing / RMP 负担。

## Certificate Audit

certificate audit 只读 v38 first-tranche 日志：

```text
certificate_audit_summary =
  BPC_future/results/gat_target_mode_certificate_audit_v38_first_tranche_b6d808_20260616/summary.json
certificate_audit_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage4_v38_first_tranche_b6d808_certificate_audit_zh.md

all_checks_pass = true
violation_count = 0
log_files = 11
events = 731
finish_events = 9
optimal_finish_events = 4
global_certificate_pricing_events = 6
```

这说明本轮 worker/GAT 没有产生 certificate、official lower bound 或 no-negative conclusion。非 OPTIMAL task20 runs 仍无 official dual bound。

## Stage 3 Rows 回流

已把 A/B audit 覆盖即时 objective label 后回流为 worker batch-impact rows：

```text
rows_summary =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v38_first_tranche_b6d808_20260616/summary.json
rows_jsonl =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v38_first_tranche_b6d808_20260616/same_context_target_worker_batch_impact_rows.jsonl
rows_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v38_first_tranche_b6d808_worker_rows_zh.md

row_count = 4
context_count = 1
pairwise_context_count = 1
positive_objective_improvement_count = 4
positive_trajectory_roi_count = 0
nonpositive_trajectory_roi_count = 4
roi_class_counts = {'columns_only_roi': 1, 'negative_retry_roi': 1, 'no_observed_roi': 2}
all_checks_pass = true
```

关键发现：4/4 rows 都有即时 RMP objective improvement，但 4/4 的最终 trajectory ROI 非正。两个例子：

```text
[16, 19]: objective_improvement = 41.318527, trajectory_accepted_batch_roi = -0.806741
[5, 13, 20]: objective_improvement = 28.011492, trajectory_accepted_batch_roi = -2.049483, label_bad_mode_switch = 1
```

因此不能把即时 objective movement 当作 `HIGH_PRIORITY` 正例；训练标签必须继续使用 A/B trajectory ROI，并显式惩罚 tail retry / pricing workload 增加。

## v39 Dataset / Training

v39 dataset 在 v23 主线数据基础上追加 v38 b6d808 rows：

```text
dataset =
  BPC_future/data/gat_batch_impact/v39_mixed_v23_plus_neighbor_roi_b6d808_ab_roi_20260616
dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v39_neighbor_roi_b6d808_dataset_zh.md

sample_count = 379
candidate_count = 4682
batch_label_counts = {'non_improving': 105, 'roi_positive': 274}
candidate_label_counts = {'delay_queue': 388, 'high_priority': 4294}
same_context_pair_count = 312
same_context_comparable_pair_count = 293
positive_negative_label_pair_count = 108
training_ready = true
ranking_ready = true
all_checks_pass = true
```

v39 training 沿用 v28 风格的 hard objective：risk-adjusted product、delay gate、false-high-priority 加重、candidate delay loss、family-task positive balance、same-context pairwise candidate ranking。

```text
training =
  BPC_future/results/gat_batch_impact_training_v39_neighbor_roi_b6d808_20260616/metrics.json
training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v39_neighbor_roi_b6d808_training_zh.md

checkpoint_gate_pass = false
stage4_candidate_ready = false
accepted_batch_count = 46
accepted_batch_precision = 1.0
accepted_batch_roi = 6.435102
accepted_batch_roi_ci_low = 3.321518
high_priority_precision = 0.940299
high_priority_precision_ci_low = 0.920802
safe_precision = 1.0
safe_precision_ci_low = 0.922924
false_high_priority_on_delay = 0.448980
false_safe_rate_union = 0.448980
false_high_priority_on_delay_count = 44
```

v39 的结论是：新增 hard-negative 证据没有把模型推成 Stage 4 candidate。它仍然会把大量 delay label 打成 high-priority，blocker 是：

```text
['false_high_priority_on_delay_too_high',
 'false_safe_rate_union_too_high',
 'knn_ood_audit_missing',
 'knn_ood_holdout_audit_not_run',
 'online_shadow_and_opt_in_ab_not_run']
```

## 结论

本轮不是成功推进 Stage 4 的结果，而是一个很有价值的负样本结论：

1. 最高 opportunity 的 b6d808 context 在 target-materialization 下没有产生正 trajectory ROI；
2. 即时 RMP objective improvement 会系统性误导 admission label；
3. 单纯追加 hard-negative rows 并沿用当前 risk-adjusted delay gate，仍无法压住 validation delay false-positive；
4. v39 不能进入 Stage 4 shadow / opt-in mutating admission，更不能进入 Stage 5 加速矩阵；
5. exact-safe 边界保持完好，证书路径未被 GAT/worker 污染。

下一步不应继续盲跑更多同类 target worker，也不应降低 precision / ROI / CI 门槛。更直接的下一步是对 v39 的 44 个 validation false-high-priority-on-delay 做 false-positive catalog：按 family / task_count / context / target signature / delay-risk score / high-priority score / ROI class 聚类，判断是分数校准问题、candidate head 结构问题，还是缺少相邻 same-context 对照。只有定位这些 false-safe 来源后，再决定是调整 candidate head / delay-risk head、加入 context-specific fallback，还是继续采集更有区分度的 A/B rows。

