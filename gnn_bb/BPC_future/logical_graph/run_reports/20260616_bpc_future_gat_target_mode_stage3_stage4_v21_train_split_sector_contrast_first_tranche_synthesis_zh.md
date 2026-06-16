# v21 Train-Split Sector Contrast First-Tranche Synthesis

日期：2026-06-16

## 目的

本报告汇总 v21 train-split `sector-wave` task20 first-tranche 的 Stage 3/4
结果。目标不是上线 GAT，也不是放宽 admission gate，而是判断新增同 context
contrast 是否能让 batch-impact GAT 更好地区分 high-ROI 与拖尾/低 ROI 列族。

所有学习相关产物仍是 diagnostic-only：不能作为 pricing oracle、不能生成 official
bound、不能作为 certificate。最终无负 reduced-cost certificate 仍只能来自当前
branch/cut/dual 下的 exact pricing full closure。

## 执行与 Exact Boundary

```text
runbook =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/summary.json
execution_summary =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v21_train_split_sector_contrast_first_tranche_20260616/worker_ab_runbook/runbook_execution_summary.json

command_count = 20
executed_count = 20
failed_command_count = 0
elapsed_s = 604.1773736650066
runs_bpc_or_pricing = true
all_checks_pass = true
```

5/10 sentinel 均为 `OPTIMAL`。task20 A/B 仍是 `TIME_LIMIT` 诊断，不提供 official
bound 或 certificate。

certificate audit：

```text
certificate_audit =
  BPC_future/results/gat_target_mode_certificate_audit_v21_train_split_sector_contrast_first_tranche_20260616/summary.json

violation_count = 0
finish_events = 22
optimal_finish_events = 4
global_certificate_pricing_events = 6
gat_events = 0
admission_events = 0
shadow_events = 0
```

结论：v21 first-tranche 没有污染 exact certificate 边界。

## A/B 与 Reachability

```text
ab_audit =
  BPC_future/results/gat_target_priority_worker_ab_v21_train_split_sector_contrast_first_tranche_audit_20260616/summary.json
reachability_audit =
  BPC_future/results/gat_target_intervention_reachability_v21_train_split_sector_contrast_first_tranche_20260616/summary.json

record_count = 9
positive_trajectory_roi_count = 4
nonpositive_roi_count = 5
roi_class_counts =
  {'negative_primal_roi': 2,
   'negative_retry_roi': 2,
   'no_observed_roi': 1,
   'positive_primal_roi': 1,
   'positive_retry_roi': 3}

reachable_target_intervention_count = 9
training_label_allowed = 9 / 9
```

关键结构：

- `0df8d5cea7864e69`：3 条偏负/无效，包含 2 条 `negative_retry_roi`；
- `b9550ffc9a42531a`：3 条 `positive_retry_roi`，主要减少 exact/pricing retry；
- `4e481a6307fca228`：1 条 `positive_primal_roi`，2 条强 `negative_primal_roi`。

这批数据的价值是同 context 正负对照干净，不是直接证明 online 加速。

## Rows 与 Dataset

```text
rows =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v21_train_split_sector_contrast_first_tranche_20260616/summary.json

row_count = 9
context_count = 3
positive_trajectory_roi_count = 4
nonpositive_trajectory_roi_count = 5
all_checks_pass = true
```

v21 dataset 在 v18 基础上追加这 9 条 reachability-valid rows：

```text
dataset =
  BPC_future/data/gat_batch_impact/v21_mixed_v18_plus_train_split_sector_contrast_first_tranche_ab_roi_20260616
dataset_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v21_train_split_sector_contrast_first_tranche_zh.md

sample_count = 363
candidate_count = 4666
family_counts = {'greedy-anchor': 54, 'random-wave': 209, 'sector-wave': 100}
task_count_counts = {'5': 2, '10': 8, '20': 180, '30': 76, '50': 96, '100': 1}
same_context_pair_count = 208
same_context_comparable_pair_count = 203
positive_negative_label_pair_count = 72
training_ready = true
ranking_ready = true
```

相对 v18：sample `354 -> 363`，sector-wave `91 -> 100`，same-context comparable
pairs `168 -> 203`，positive/negative label pairs `60 -> 72`。

## v21 Data-Only Training

为了隔离“新增数据”的效果，本轮显式关闭 v19/v20 的 candidate-pairwise loss：

```text
pairwise_candidate_ranking_loss_multiplier = 0.0
training =
  BPC_future/results/gat_batch_impact_training_v21_train_split_sector_contrast_first_tranche_20260616/metrics.json
training_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v21_train_split_sector_contrast_first_tranche_training_zh.md

best_epoch = 1
best_loss_epoch = 8
checkpoint_gate_pass = false
stage4_candidate_ready = false
rejected_checkpoint_reasons =
  ['knn_ood_audit_missing',
   'safe_precision_ci_low_below_threshold_or_not_measurable']

validation accepted_batch_count = 4
validation accepted_batch_roi = 0.9555176049470901
validation accepted_batch_roi_ci_low = 0.7689567764619533
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.5100999795960008
validation false_high_priority_on_delay = 0.0
validation false_safe_rate_union = 0.0
validation high_priority_precision_ci_low = 0.9958774109247752
```

结论：v21-data-only checkpoint 很安全但过保守。它没有 low-ROI/bad admission，
但 accepted batch 太少，导致 safe precision CI 下界不足。

## kNN/OOD 与 Threshold Frontier

```text
knn_ood =
  BPC_future/results/gat_batch_impact_knn_ood_v21_train_split_sector_contrast_first_tranche_global_20260616/summary.json

validation_candidate_ready = false
validation_safety_ready = false
production_block_reasons =
  ['validation_safe_precision_ci_low_below_min',
   'validation_candidate_not_ready']

accepted_batch_count = 4
accepted_batch_roi = 0.9555176049470901
accepted_batch_roi_ci_low = 0.7689567764619533
safe_precision_ci_low = 0.5100999795960008
false_safe_rate_union = 0.0
knn_unsafe_count = 71
```

```text
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v21_train_split_sector_contrast_first_tranche_20260616/summary.json

feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker

best_global:
  accepted_batch_count = 4
  accepted_batch_roi_ci_low = 0.7689567764619533
  safe_precision_ci_low = 0.5100999795960008

best_family_delay_fallback:
  accepted_batch_count = 14
  accepted_batch_roi_ci_low = 0.3550365321616284
  safe_precision_ci_low = 0.7846829880728186
```

结论：不存在可用阈值组合。降低阈值不是正确方向；family fallback 也只是把
accepted 从 4 提到 14，仍不过 safe precision CI 和 ROI-CI。

## Opportunity 与 Score Margin

```text
opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v21_train_split_sector_contrast_first_tranche_20260616/summary.json

high_roi_opportunities = 30
accepted_high_roi_opportunities = 4
missed_high_roi_opportunities = 26
accepted_high_roi_capture_rate = 0.13333333333333333
accepted_low_roi_or_bad = 0
missed_reason_counts =
  {'batch_score_below_family_threshold': 25,
   'no_candidate_above_threshold': 26}

random-wave: accepted_high_roi = 1 / 6
sector-wave: accepted_high_roi = 3 / 24
```

```text
score_margin =
  BPC_future/results/gat_batch_impact_score_margin_audit_v21_train_split_sector_contrast_first_tranche_20260616/summary.json

candidate_margin_bucket_counts =
  {'deep_candidate_score_gap': 25,
   'near_candidate_threshold': 1}

missed_candidate_score_margin_mean = -0.2779155373573303
missed_candidate_score_margin_median = -0.2899966686964035
missed_candidate_score_margin_min = -0.3004484474658966
missed_candidate_score_margin_max = -0.0018556714057922363
missed_without_same_context_contrast_count = 11
```

主要 missed contexts：

```text
9fadf4f7b39742a2  sector-wave task20  missed = 4
b6d808ebac2a6dd8  sector-wave task20  missed = 5
a67f331bdb819d7d  random-wave task50  missed = 1
e6b17bbf825984ae  random-wave task50  missed = 1
```

结论：不是分数差一点。26 个 missed high-ROI 里只有 1 个 near-threshold，其余
25 个是 deep candidate score gap。v21 first-tranche 新数据增强了 train-side
对照，但 data-only 训练仍没有把 validation high-ROI candidate score 拉上来。

## 当前结论

v21 first-tranche 的正确结论是：

```text
v21_status = first_tranche_executed_trained_audited
stage3_checkpoint_gate_pass = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
certificate_ready = false
primary_blocker = candidate_head_deep_score_gap_and_low_acceptance_ci
```

下一步不应继续盲调 threshold。可选方向只有两类：

1. 数据侧：继续补 reachability-valid same-context positive/negative contrast，尤其要给
   `9fadf4f7b39742a2` / `b6d808ebac2a6dd8` 找 train-side analog，random-wave task50
   仍需先修复 target replay reachability；
2. 模型侧：改 candidate head / batch-candidate interaction / context-local margin，训练目标必须
   显式保持 coverage 约束，例如 `accepted_batch_count >= 35`、safe precision CI、
   false-safe gate 不放松，同时最大化 ROI 并压低 low-ROI/bad admission。

Exact-safe boundary 保持不变：GAT 只能影响 ordering/admission scheduling；
最终 certificate 必须由 exact pricing under current true duals 完整确认。
