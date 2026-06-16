# BPC_future GAT Target Mode Stage 3 v10 Random-wave Safe-source Candidate 报告

日期：2026-06-16

## 结论

本轮继续推进 Stage 3 hard gate。v9 的 blocker 是 `random-wave` validation 存在
high-ROI opportunity，但模型 / threshold / kNN-OOD safe source 将 random-wave
整体 fallback delay。

v10 已经打破这个 blocker：`random-wave` 不再整体 fallback，并且导出了一个
offline safe-source candidate，可进入 Stage 4 shadow / opt-in A/B。它仍不是
production-ready，也不改变 exact pricing / certificate 语义。

## 本轮补样

继续使用 v9 random-wave task50 runbook，但只跑可复现的
`5751b1799b606ad1` context 剩余 targets：

```text
mb1 [4, 40, 3]                 objective_improvement = 4.385625   best_true_rc = -11.539468769
mb2 [4, 8, 25, 32, 45, 9]      objective_improvement = 0.024858   best_true_rc = -2.633324538
mb3 [33, 41, 16, 32, 45, 9]    objective_improvement = 0.007822   best_true_rc = -0.088008
mb4 [33, 16, 2, 43, 7]         objective_improvement = 1.201441   best_true_rc = -4.622862264
```

worker rows：

```text
row_count = 4
context_count = 1
largest_context_size = 4
pairwise_context_count = 1
positive_objective_improvement_count = 4
all_checks_pass = true
```

这给 random-wave 同一 RMP context 提供了强正 / 中强正 / 弱正 / 极弱正四档
ROI 排序信号。

## v10 Dataset

```text
sample_count = 324
candidate_count = 4599
family_counts = {'greedy-anchor': 54, 'random-wave': 197, 'sector-wave': 73}
task_count_counts = {'5': 2, '10': 8, '20': 144, '30': 76, '50': 93, '100': 1}
random-wave same_context_pair_count = 16
task50 same_context_pair_count = 10
ranking_ready = true
training_ready = true
all_checks_pass = true
```

## v10 Training

训练目标保持硬化：

```text
training_objective = precision_constrained_roi_maximization
checkpoint_selection = deployment_gate_first_then_utility_roi_loss
pairwise_ranking_loss_active = true
best_epoch = 7
best_loss_epoch = 7
selected_checkpoint_reason = local_deployment_gate_passed_and_best_validation_loss
```

validation deployment metrics：

```text
accepted_batch_count = 35
accepted_batch_rate = 0.343137
accepted_batch_roi = 8.949960742571525
accepted_batch_roi_ci_low = 5.073187796362916
accepted_batch_roi_over_baseline_ci_low = 4.623187796362916
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.995823628763909
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
family_delay_fallback_families = ['greedy-anchor']
```

family holdout：

```text
random-wave accepted_batch_count = 11
random-wave accepted_batch_roi = 0.733351525596597
random-wave max_accepted_batch_roi_label = 4.385624885559082
random-wave oracle_high_roi_count = 5
random-wave safe_precision = 1.0

sector-wave accepted_batch_count = 24
sector-wave accepted_batch_roi = 12.715906633685032
sector-wave safe_precision = 1.0

greedy-anchor accepted_batch_count = 0
greedy-anchor oracle_high_roi_count = 0
```

`greedy-anchor` fallback 目前可接受，因为 validation 中没有 greedy high-ROI
opportunity；后续若采到 greedy high-ROI opportunity，必须重新审计 family fallback。

## Threshold / kNN-OOD / Safe-source

threshold frontier：

```text
feasible_threshold_count = 324
best accepted_batch_count = 42
best accepted_batch_roi = 7.455028318689161
best accepted_batch_roi_ci_low = 4.076867756237288
best safe_precision_ci_low = 0.916198387490838
best family_delay_fallback_families = ['greedy-anchor']
```

kNN/OOD (`k=3`, `max_neighbor_delay_fraction=0.34`)：

```text
validation_candidate_ready = true
validation_safety_ready = true
accepted_batch_count = 35
accepted_batch_roi = 8.949960742571525
accepted_batch_roi_ci_low = 5.073187796362916
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_safe_rate_union = 0.0
production_block_reasons = []
production_ready = false
```

safe-source export：

```text
safe_source_ready = true
safe_ids_exportable = true
safe_candidate_id_count = 408
blockers = []
all_checks_pass = true
production_ready = false
selector_can_certificate = false
official_bound_effect = false
```

## Opportunity Mining

v10 opportunity summary：

```text
records = 102
accepted = 45
high_roi_opportunities = 27
accepted_high_roi_opportunities = 22
accepted_high_roi_capture_rate = 0.8148148148148148
missed_high_roi_opportunities = 5
```

family summary：

```text
random-wave:
  records = 42
  accepted = 12
  high_roi_opportunities = 5
  accepted_high_roi_opportunities = 3
  missed_high_roi_opportunities = 2

sector-wave:
  records = 46
  accepted = 30
  high_roi_opportunities = 22
  accepted_high_roi_opportunities = 19
  missed_high_roi_opportunities = 3
```

剩余主要问题不是安全壳失败，而是部分 high-ROI batch 的 candidate score 仍低于
selected threshold：

```text
recommended_next_step.primary = improve_candidate_high_priority_scores_for_high_roi_batches
missed_family_counts = {'random-wave': 2, 'sector-wave': 3}
```

## Exactness Boundary

本轮所有新增 artifact 均保持：

```text
diagnostic_only = true
runs_bpc_or_pricing = false  # dataset/training/audit/export scripts
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
negative_columns_must_remain_eventually_reachable = true
```

safe-source ids 只能用于已经 true-RC verified 的 negative journey admission
scheduling。最终 certificate 仍必须由当前 branch/cut/dual 下 exact pricing 对完整
configured universe 做 no-negative closure。

## 下一步

1. 用 v10 safe-source 做 Stage 4 shadow / opt-in A/B，先重跑 5/10 no-regression。
2. 若 5/10 no-regression 通过，再做 20-task targeted ROI A/B；不能直接进 production。
3. 同时继续补 `random-wave` / `sector-wave` missed high-ROI rows，提高 candidate high-priority scores。
4. 不降低 precision / ROI / false-safe 门槛，不让 GAT 参与 certificate。
