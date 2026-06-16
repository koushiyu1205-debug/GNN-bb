# 2026-06-16 GAT Target Mode Stage 2/3 v23 Contrast Collection Plan Synthesis

## 结论

v22 之后的 blocker 不是 ROI 不够，而是：

```text
primary_blocker = safe_precision_ci_sample_count_and_remaining_deep_candidate_gap
```

因此 v23 不继续盲目调阈值或加大 loss，而是回到 Stage 2/3 数据闭环：

1. 生成 train-split same-context multi-batch contrast plan，用于下一轮可训练数据采集；
2. 生成 validation-missed diagnostic plan，只用于定位当前 v22 missed high-ROI context，不直接作为同一 validation gate 的训练证据；
3. 生成 train first-tranche guarded worker A/B runbook，但本报告不执行 BPC / pricing / RMP / worker。

所有 v23 artifact 仍保持 exact-safe 边界：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
certificate_ready = false
official_bound_effect = false
training_label_allowed_before_worker_reachability = false
```

## 产物

```text
train_full_plan =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_20260616/summary.json
train_full_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v23_train_split_remaining_contrast_plan_zh.md

train_first_tranche =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/summary.json
train_first_tranche_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v23_train_split_remaining_contrast_first_tranche_zh.md

train_first_tranche_runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/summary.json
train_first_tranche_runbook_report =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook.md

validation_missed_diagnostic_plan =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_validation_missed_diagnostic_20260616/summary.json
validation_missed_diagnostic_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v23_validation_missed_diagnostic_plan_zh.md
```

## Train-Split Plan

该计划限制在 v22 training summary 的 train split，避免把当前 validation missed
context 直接回流到同一 validation gate。

```text
status = ready
all_checks_pass = true
split_mode = train
include_task_counts = [20]
selected_context_count = 12
candidate_count = 35
pairwise_context_target_count = 12

candidate_task_count_counts = {'20': 35}
candidate_family_region_counts =
  {'greedy-anchor|tranquillitatis_balmer_like_20km': 3,
   'random-wave|apollo15_20km': 11,
   'random-wave|tranquillitatis_balmer_like_20km': 12,
   'sector-wave|apollo15_20km': 6,
   'sector-wave|tranquillitatis_balmer_like_20km': 3}
candidate_impact_bucket_counts =
  {'new_support_changing': 19,
   'new_task_set': 6,
   'replacement_like': 10}
```

首批裁剪：

```text
selected_context_count = 4
candidate_count = 12
candidate_family_counts = {'random-wave': 9, 'sector-wave': 3}
candidate_task_count_counts = {'20': 12}
selected_contexts =
  ['d519291840dd7000',
   'ddcb5387bef3bf63',
   '67c11b5ec80925ec',
   '0df8d5cea7864e69']
```

对应 guarded worker A/B runbook 已生成：

```text
status = ready
all_checks_pass = true
candidate_group_count = 12
worker_batch_size = 1
worker_method = target_materialization_fixed
```

## Validation-Missed Diagnostic Plan

该计划只用于定位 v22 剩余 missed high-ROI context 的 materialization / causal-match
可达性，不应直接并入同一 validation gate 的训练证据。

```text
status = ready
all_checks_pass = true
split_mode = validation
require_opportunity_context = true
selected_context_count = 8
candidate_count = 23
candidate_task_count_counts = {'20': 17, '50': 6}
candidate_family_region_counts =
  {'random-wave|tranquillitatis_balmer_like_20km': 6,
   'sector-wave|apollo15_20km': 2,
   'sector-wave|tranquillitatis_balmer_like_20km': 15}
candidate_impact_bucket_counts =
  {'new_support_changing': 17,
   'new_task_set': 4,
   'replacement_like': 1,
   'support_changing': 1}
selected_contexts =
  ['ac15bc4e7e3d6fff',
   '79fde658840fe2b8',
   '45baa40751a0bf77',
   '3d1bd8618099b573',
   '9fadf4f7b39742a2',
   '5751b1799b606ad1',
   'ce3508e12ad69da7',
   'a67f331bdb819d7d']
```

## 下一步

1. 若要继续采集训练证据，先执行 train first-tranche worker A/B runbook；
2. 跑完后必须做 reachability、target causal match、A/B ROI、certificate audit；
3. 只有通过 reachability 和 causal match 的 worker rows 才能回流 dataset；
4. validation diagnostic plan 的结果只能解释当前 v22 miss，不得直接宣称 Stage 3/4 gate 通过；
5. 任何上线或 Stage 5 加速仍需要 5/10 no-regression、20-task exact ROI、certificate safety，且最终 certificate 只能来自 current branch/cut/dual 下的 exact pricing full closure。

## 验证

本报告对应命令只生成 artifact，不运行 solver：

```text
train_full all_checks_pass = true
train_first_tranche all_checks_pass = true
train_first_tranche_runbook all_checks_pass = true
validation_missed_diagnostic all_checks_pass = true
```
