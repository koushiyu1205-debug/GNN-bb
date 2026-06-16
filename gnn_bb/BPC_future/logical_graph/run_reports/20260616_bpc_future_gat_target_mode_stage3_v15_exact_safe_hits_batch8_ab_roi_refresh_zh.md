# 2026-06-16 BPC_future GAT Stage 3 v15 Exact Safe-hit Batch8 A/B ROI 刷新报告

## 结论

本轮把 Stage 4 v14 exact safe-hit batch8 A/B 的真实结果回流到 Stage 3 训练数据。
核心修正是：不再让即时 RMP objective delta 决定训练正负例，而是用最终 A/B
trajectory ROI 覆盖标签。

结果：

```text
v15_dataset_built = true
v15_training_completed = true
v15_threshold_frontier_completed = true
v15_global_knn_ood_completed = true
v15_scale_knn_ood_completed = true
stage4_candidate_ready = false
production_ready = false
default_enabled = false
```

v15 的正向变化是 false-safe 被压到 0：

```text
v14 selected false_safe_rate_union = 0.02531645569620253
v15 selected false_safe_rate_union = 0.0
v15 selected false_high_priority_on_delay = 0.0
v15 accepted_bad_mode_count = 0
```

但 v15 仍不能进入 Stage 4：accepted batch 从 v14 的 34 降到 13，导致
`safe_precision_ci_low=0.7718981569447084`，低于硬门槛。因此当前 blocker 从
“false-safe 过高”转为“安全覆盖太窄 / confidence lower bound 不足”。

## 代码改动

新增/修改：

```text
BPC_future/scripts/build_gat_batch_impact_dataset.py
BPC_future/scripts/build_gat_multibatch_worker_batch_impact_rows.py
BPC_future/tests/test_gat_multibatch_worker_batch_impact_rows.py
```

关键语义：

- `build_gat_multibatch_worker_batch_impact_rows.py` 新增 `--ab-audit-summary`；
- 如果提供 A/B audit summary，`label_batch_roi_positive`、`label_bad_mode_switch`、
  `accepted_batch_roi_label`、`delta_v_label`、`barrier_slack_label` 使用最终
  trajectory ROI，而不是只看 worker 后下一次 RMP objective；
- row 中写入 `target_signature_samples` / `worker_returned_candidate_signature_samples`；
- `build_gat_batch_impact_dataset.py` 支持按 signature samples 过滤 capture
  returned journeys，避免 batch8 退化成单列样本。

## Batch8 hard-negative rows

输入：

```text
runbook =
  BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_20260616/summary.json
ab_audit =
  BPC_future/results/gat_target_priority_worker_ab_v14_exact_safe_hits_batch8_tranq20_01_audit_20260616/summary.json
rows =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v14_exact_safe_hits_batch8_ab_roi_20260616/same_context_target_worker_batch_impact_rows.jsonl
summary =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v14_exact_safe_hits_batch8_ab_roi_20260616/summary.json
```

机器结果：

```text
row_count = 4
ab_audit_matched_row_count = 4
signature_sample_row_count = 4
positive_objective_improvement_count = 3
positive_trajectory_roi_count = 0
nonpositive_trajectory_roi_count = 4
roi_class_counts = {'negative_retry_roi': 3, 'no_observed_roi': 1}
all_checks_pass = true
```

解释：这 4 个 row 里有 3 个在 worker 后下一次 RMP objective 下降，但最终
A/B 没有正 ROI，甚至增加 exact/pricing/RMP retry。因此它们必须作为
`DELAY_QUEUE` / hard-negative 训练信号，而不是 `HIGH_PRIORITY` 正例。

## v15 Dataset

v15 在 v14 的 6 个 source JSONL 基础上追加 batch8 hard-negative rows：

```text
dataset =
  BPC_future/data/gat_batch_impact/v15_mixed_v14_plus_exact_safe_hits_batch8_ab_roi_20260616
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_dataset_v15_exact_safe_hits_batch8_ab_roi_zh.md

sample_count = 332
candidate_count = 4635
batch_label_counts = {'non_improving': 73, 'roi_positive': 259}
candidate_label_counts = {'delay_queue': 356, 'high_priority': 4279}
family_counts = {'greedy-anchor': 54, 'random-wave': 199, 'sector-wave': 79}
task_count_counts = {'10': 8, '100': 1, '20': 150, '30': 76, '5': 2, '50': 95}
training_ready = true
ranking_ready = true
all_checks_pass = true
```

相对 v14：

| metric | v14 | v15 |
| --- | ---: | ---: |
| sample_count | 328 | 332 |
| candidate_count | 4603 | 4635 |
| non_improving batches | 69 | 73 |
| delay_queue candidates | 324 | 356 |
| sector-wave samples | 75 | 79 |
| task20 samples | 146 | 150 |
| same_context_pair_count | 79 | 93 |
| same_context_comparable_pair_count | 76 | 90 |
| positive_negative_label_pair_count | 12 | 16 |

## v15 Training

训练产物：

```text
training =
  BPC_future/results/gat_batch_impact_training_v15_exact_safe_hits_batch8_ab_roi_20260616/metrics.json
checkpoint =
  BPC_future/results/gat_batch_impact_training_v15_exact_safe_hits_batch8_ab_roi_20260616/gat_batch_impact.pt
report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v15_exact_safe_hits_batch8_ab_roi_training_zh.md

training_objective = precision_constrained_roi_maximization
checkpoint_gate_pass = false
stage4_candidate_ready = false
best_epoch = 8
rejected_checkpoint_reasons =
  ['knn_ood_audit_missing', 'safe_precision_ci_low_below_threshold_or_not_measurable']
```

关键 validation metrics：

| metric | v14 | v15 |
| --- | ---: | ---: |
| accepted_batch_count | 34 | 13 |
| accepted_batch_roi | 9.270531552487656 | 16.316478240948456 |
| accepted_batch_roi_ci_low | 5.325235030723549 | 8.0292472538527 |
| false_high_priority_on_delay | 0.02531645569620253 | 0.0 |
| false_safe_rate_union | 0.02531645569620253 | 0.0 |
| safe_precision | 1.0 | 1.0 |
| safe_precision_ci_low | 0.8984820937803899 | 0.7718981569447084 |
| high_priority_precision | 0.9980601357904947 | 1.0 |
| high_priority_precision_ci_low | 0.9929545460660191 | 0.9782766045998227 |
| delay_rate | 0.679245283018868 | 0.8818181818181818 |

v15 正确学到了“batch8 exact-id hit 负例应 delay”，但当前阈值过窄，accepted
batch count 不足以支撑 safe precision CI lower bound。

## Threshold / kNN-OOD

Threshold frontier：

```text
frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v15_exact_safe_hits_batch8_ab_roi_20260616/summary.json
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = confidence_lower_bound_sample_size_or_acceptance_count_blocker
best_accepted_batch_count = 13
best_safe_precision_ci_low = 0.7718981569447084
best_accepted_batch_roi_ci_low = 8.0292472538527
```

Strict global / scale kNN-OOD 均未通过：

```text
global_knn_ood:
  accepted_batch_count = 10
  accepted_batch_roi = 12.392746290564537
  accepted_batch_roi_ci_low = 2.8979448716411866
  false_safe_rate_union = 0.0
  safe_precision_ci_low = 0.7224598312333834
  validation_safety_ready = false

scale_knn_ood:
  accepted_batch_count = 10
  accepted_batch_roi = 12.392746290564537
  accepted_batch_roi_ci_low = 2.8979448716411866
  false_safe_rate_union = 0.0
  safe_precision_ci_low = 0.7224598312333834
  validation_safety_ready = false
```

因此本轮不导出 v15 safe-source，也不进入 Stage 4 online coverage。

## Exactness Boundary

本轮全部是 offline / diagnostic-only：

```text
runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
selector_is_pricing_oracle = false
selector_can_certificate = false
official_bound_effect = false
gate_can_permanently_discard_negative_columns = false
```

GAT / kNN / OOD 仍只能训练 admission scheduling。最终 certificate 仍必须来自
当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的 exhaustive no-negative
closure。

## 下一步

v15 说明方向正确但数据不够：硬负例能消掉 false-safe，但同时暴露 accepted
coverage / CI 不足。下一轮应补 same-context high-ROI positives，而不是降低
precision / ROI 门槛：

1. 对 `sector_tranq20_01` 同一 context 继续采样强正 batch，与这 4 个 hard-negative
   batch 形成更多 positive/negative 对照；
2. 优先补 random-wave 和 sector-wave 中 missed high-ROI 的 same-context rows，
   目标是把 accepted batch count 提到 `>=35` 的 all-success CI 区间；
3. 在模型结构上增加 context-local candidate score margin / batch diversity head，
   防止 hard-negative refresh 后模型只学会保守 delay。
