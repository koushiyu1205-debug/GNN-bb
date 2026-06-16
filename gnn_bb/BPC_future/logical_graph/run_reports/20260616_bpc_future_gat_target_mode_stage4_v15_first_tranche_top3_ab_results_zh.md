# GAT Target Mode Stage 4 v15 First-Tranche Top3 A/B 结果汇总

日期：2026-06-16

## 结论

v15 missed high-ROI top3 first-tranche 已完成 20 条显式 runbook commands。
worker reachability 成功，certificate closure audit 无 violation，但真实
trajectory ROI 呈混合结果：9 个 target-worker 候选中只有 2 个为正 ROI，
其余 7 个应回流为 hard-negative / delay 证据。

更关键的是：这些 v15 intervention candidates 和回流 rows 全部来自 validation
split。它们能让 validation 对照更完整，但不能给训练 split 增加可学习证据。
因此 v16 未通过 Stage 4 gate 的主要解释不是阈值差一点，而是补样位置错误：
下一步必须执行 train-split same-context A/B。

## 机器字段

```text
stage4_v15_first_tranche_ab = current
execution_status = executed
command_count = 20
executed_count = 20
failed_command_count = 0
record_count = 9
reachable_target_intervention_count = 9
positive_trajectory_roi_count = 2
nonpositive_roi_count = 7
certificate_violation_count = 0
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## Artifacts

```text
execution_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v15_first_tranche_top3_20260616/worker_ab_runbook/runbook_execution_summary.json
ab_audit_summary =
  BPC_future/results/gat_target_priority_worker_ab_v15_first_tranche_top3_audit_20260616/summary.json
reachability_summary =
  BPC_future/results/gat_target_intervention_reachability_v15_first_tranche_top3_20260616/summary.json
certificate_audit_summary =
  BPC_future/results/gat_target_mode_certificate_audit_v15_first_tranche_top3_20260616/summary.json
worker_rows_summary =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/summary.json
v16_training_metrics =
  BPC_future/results/gat_batch_impact_training_v16_first_tranche_top3_ab_roi_20260616/metrics.json
```

## ROI Breakdown

```text
roi_class_counts =
  {'negative_primal_roi': 4,
   'negative_retry_roi': 3,
   'positive_primal_roi': 1,
   'positive_retry_roi': 1}

row_count = 9
positive_trajectory_roi_count = 2
nonpositive_trajectory_roi_count = 7
```

这些 rows 的标签语义：

- positive ROI 才能作为 `HIGH_PRIORITY` 训练证据；
- negative primal / retry ROI 虽然是 true-RC negative，但应作为 `DELAY_QUEUE`
  或 hard-negative 训练证据；
- 不能用 true-RC negative、exact safe-hit 或即时 objective improvement 替代
  trajectory ROI。

## v16 结果

```text
v16_dataset =
  BPC_future/data/gat_batch_impact/v16_mixed_v15_plus_first_tranche_top3_ab_roi_20260616

sample_count = 341
candidate_count = 4644
same_context_pair_count = 138
same_context_comparable_pair_count = 135
positive_negative_label_pair_count = 44
```

训练 / kNN-OOD：

```text
checkpoint_gate_pass = false
stage4_candidate_ready = false
accepted_batch_count = 12
accepted_batch_roi = 15.887507483363152
accepted_batch_roi_ci_low = 6.949653955866234
safe_precision = 1.0
safe_precision_ci_low = 0.7574992425007574
false_high_priority_on_delay = 0.00847457627118644
false_safe_rate_union = 0.00847457627118644

global_knn_ood:
  accepted_batch_count = 9
  accepted_batch_roi = 11.456397010220421
  accepted_batch_roi_ci_low = 1.0586008970415683
  safe_precision_ci_low = 0.7008472464490406
  validation_safety_ready = false
```

v16 的新增 rows 全部来自 validation split：

```text
v15_full_candidate_split = {'validation': 32}
v15_first_tranche_candidate_split = {'validation': 9}
v16_new_row_split = {'validation': 9}
```

这解释了为什么 v16 pairwise coverage 增加，但 checkpoint / kNN-OOD 没有通过。

## 下一步

已生成 train-split intervention plan 和 top3 task20 runbook：

```text
train_split_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_20260616/summary.json
top3_subset_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/summary.json
top3_worker_ab_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/summary.json
top3_dry_run_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v16_train_split_top3_task20_20260616/worker_ab_runbook/runbook_execution_dry_run_summary.json
```

下一轮先跑 train-split top3 task20 guarded A/B，再回流 v17 rows。完整 v15
validation runbook 不应继续扩跑为训练补样主线。

## 边界

- 本报告不是 production admission 结论；
- worker 只在显式 opt-in runbook 中生效；
- `DELAY_QUEUE` 不是 reject，不能永久丢弃 true-RC negative；
- final OPTIMAL / no-negative certificate 仍只能来自当前 branch/cut/dual 下完整
  configured universe 的 exact pricing closure。
