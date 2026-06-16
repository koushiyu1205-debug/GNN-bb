# GAT Target Mode Stage 3 Pairwise Training Activation

日期：2026-06-16

## 结论

本轮把 Stage 3 从“hard ROI / precision gate 已写入 trainer，但 pairwise ranking 仍未实际启用”
推进到“真实 same-context worker rows 已进入训练集，并且 trainer 在 train split 上实际启用
same-context ROI margin ranking loss”。

这仍是 offline diagnostic checkpoint，不是 Stage 4 safe source：

- 不运行 online pricing / RMP / certificate；
- 不产生 official lower bound；
- 不允许永久丢弃 true-RC negative；
- final certificate 仍只能来自当前 branch/cut/dual 下的 exact pricing full closure。

## Worker Rows

只执行了同一个 task20 context `ce3508e12ad69da7` 下的两个 target-materialization worker，
没有跑完整 35 个候选，也没有跑 5/10 no-regression。

```text
worker_row_status = built
candidate_count = 35
executed_worker_count = 2
row_count = 2
pairwise_context_count = 1
positive_objective_improvement_count = 1
non_improving_objective_count = 1
skipped_missing_worker_logs = 33
all_checks_pass = true
```

产物：

- `BPC_future/results/gat_multibatch_worker_batch_impact_rows_v3_signature_hard_roi_20260616/same_context_target_worker_batch_impact_rows.jsonl`
- `BPC_future/results/gat_multibatch_worker_batch_impact_rows_v3_signature_hard_roi_20260616/summary.json`

## Dataset

先建 smoke dataset，只包含真实 worker rows：

```text
v4_smoke_sample_count = 2
v4_smoke_candidate_count = 2
v4_smoke_training_ready = false
v4_smoke_ranking_ready = true
v4_smoke_same_context_pair_count = 1
v4_smoke_same_context_comparable_pair_count = 1
```

再把 worker rows 合并进 v3 signature 主数据，得到可训练 mixed dataset：

```text
v4_mixed_sample_count = 296
v4_mixed_candidate_count = 4571
v4_mixed_training_ready = true
v4_mixed_ranking_ready = true
v4_mixed_context_count = 294
v4_mixed_same_context_pair_count = 3
v4_mixed_same_context_comparable_pair_count = 3
v4_mixed_positive_negative_label_pair_count = 2
```

产物：

- `BPC_future/data/gat_batch_impact/v4_multibatch_worker_smoke_20260616/`
- `BPC_future/data/gat_batch_impact/v4_mixed_v3_plus_worker_smoke_20260616/`

## Trainer Hardening

`BPC_future/scripts/train_gat_batch_impact.py` 新增：

- `pairwise_ranking_loss_multiplier`；
- `pairwise_roi_margin`；
- `min_pairwise_roi_delta`；
- same-context ROI pair construction；
- pairwise-aware instance split：当存在可比 pair 但 train split 没有 pair 时，优先把一个 paired instance 保留到 train；
- checkpoint/report 中记录 `pairwise_ranking_loss_active`、`pairwise_ranking_status` 和 train/validation pair stats。

当前 v4 mixed smoke training：

```text
training_status = gat_batch_impact_trained
sample_count = 296
candidate_count = 4571
training_objective = precision_constrained_roi_maximization
hard_roi_threshold = 0.65
pairwise_ranking_loss_active = true
pairwise_ranking_status = active_same_context_roi_margin_ranking
pairwise_split_adjustment = moved_validation_pair_instance_to_train:BPC_future/logical_graph/tasks_020/sector-wave/apollo15_20km/apollo15_20km_sector-wave_randomtw_tasks020_07_seed61612_logical_graph.json
train_same_context_pair_count = 3
train_same_context_comparable_pair_count = 3
train_positive_negative_label_pair_count = 2
checkpoint_gate_pass = false
stage4_candidate_ready = false
```

validation gate 仍未过：

```text
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.936858991216536
safe_precision = 1.0
safe_precision_ci_low = 0.3423719528896193
accepted_batch_count = 2
accepted_batch_roi = 1.8469733595848083
accepted_batch_roi_ci_low = 0.3946217775344849
accepted_batch_roi_over_baseline_ci_low = -0.0553782224655151
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
```

拒绝原因：

```text
rejected_checkpoint_reasons =
  accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable
  knn_ood_audit_missing
  safe_precision_ci_low_below_threshold_or_not_measurable

stage4_blockers =
  accepted_batch_roi_ci_low_below_baseline_margin_or_not_measurable
  knn_ood_audit_missing
  knn_ood_holdout_audit_not_run
  online_shadow_and_opt_in_ab_not_run
  safe_precision_ci_low_below_threshold_or_not_measurable
```

结论：训练目标已经硬化到 precision / ROI / confidence / pairwise-ranking 约束，但样本量和
safe-source 证据仍不足以进入 Stage 4 mutating admission。

## 下一步

1. 扩大 task20 same-context worker execution，从 1 个 context 扩到更多 context/family。
2. 重新构建 mixed dataset，目标是让 `same_context_comparable_pair_count` 从 3 提高到可做 holdout 的规模。
3. 跑 kNN/OOD holdout audit，只有 safe_precision CI、accepted ROI CI、family fallback 都过线后，才允许导出 Stage 4 safe source。
4. Stage 4 仍先 shadow，再 5/10 no-regression，再 task20 opt-in ROI A/B；任何 certificate 仍必须由 exact pricing full closure 给出。
