# GAT Target Mode Stage 3 v7 Validation Full 与 Context Fallback 报告

日期：2026-06-16

## 结论

本轮继续推进 Stage 3 safe-source 训练。新增跑完两个 validation split 中缺失的 sector-wave context，共 6 个 target-materialization worker。worker rows 从 14 增加到 20，mixed dataset 从 v6 的 308 samples 增加到 v7 的 314 samples。

同时把 fallback 从 family-only 扩展为 context-level：当某个 family 内只有局部 context ROI 坍塌时，优先 delay 这些 context，而不是 delay 整个 family。该逻辑只存在于 offline trainer / frontier / kNN-OOD audit，仍是 diagnostic admission scheduling，不参与 certificate。

当前仍不是 Stage 4 safe source：

```text
stage4_candidate_ready = false
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 新增 Worker 数据

运行的新增 validation context：

```text
9fadf4f7b39742a2  tranquillitatis sector-wave tasks020 seed61206  3 worker batches
79fde658840fe2b8  tranquillitatis sector-wave tasks020 seed61718  3 worker batches
```

6 个 worker 均返回 `0` 并写出 CSV；它们用于离线训练 row，不代表 exact proof。

重建 worker rows：

```text
rows_dir = BPC_future/results/gat_multibatch_worker_batch_impact_rows_v3_signature_hard_roi_validation_full_20260616
row_count = 20
positive_objective_improvement_count = 16
non_improving_objective_count = 4
context_count = 7
pairwise_context_count = 7
largest_context_size = 3
skipped_counts = {'missing_worker_logs': 15}
```

## v7 Dataset

worker-only v7：

```text
dataset_dir = BPC_future/data/gat_batch_impact/v7_multibatch_worker_validation_full_20260616
sample_count = 20
candidate_count = 20
family_counts = {'random-wave': 3, 'sector-wave': 17}
same_context_comparable_pair_count = 18
positive_negative_label_pair_count = 5
ranking_ready = true
training_ready = false
```

mixed v7：

```text
dataset_dir = BPC_future/data/gat_batch_impact/v7_mixed_v3_plus_worker_validation_full_20260616
sample_count = 314
candidate_count = 4589
family_counts = {'greedy-anchor': 54, 'random-wave': 193, 'sector-wave': 67}
task_count_counts = {'10': 8, '100': 1, '20': 138, '30': 76, '5': 2, '50': 89}
same_context_comparable_pair_count = 38
positive_negative_label_pair_count = 9
roi_diverse_context_count = 7
ranking_ready = true
training_ready = true
```

## Context Fallback 代码口径

新增/同步口径：

- `context_delay_fallback_contexts` 写入 deployment metrics；
- threshold search 会生成 context fallback 候选；
- frontier 会把 context fallback 纳入 `frontier_family_delay_fallback.jsonl`；
- kNN/OOD audit 会把 context fallback record 直接判为 `DELAY_QUEUE`；
- 同等收益下，selection tie-break 优先少用 broad family fallback。

这仍然不改变 proof 语义：

```text
runs_bpc_or_pricing = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
```

## v7 Training

训练输出：

```text
training_dir = BPC_future/results/gat_batch_impact_training_v7_mixed_worker_validation_full_context_fallback_20260616
training_objective = precision_constrained_roi_maximization
pairwise_ranking_status = active_same_context_roi_margin_ranking
best_epoch = 7
selected_validation_loss = 2.890295338327602
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run', 'safe_precision_ci_low_below_threshold_or_not_measurable']
```

selected validation metrics：

```text
accepted_batch_count = 7
safe_precision_ci_low = 0.6456611570247934
high_priority_precision_ci_low = 0.9962805526036131
accepted_batch_roi = 18.980578677994863
accepted_batch_roi_ci_low = 6.450565547872774
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
threshold_mode = separate_batch_candidate
context_delay_fallback_contexts = []
family_delay_fallback_families = []
```

训练选中的 checkpoint 仍偏保守，accepted count 没有随新增 rows 增加，因此 safe precision lower bound 仍不达 0.90。

## v7 Frontier

frontier 输出：

```text
frontier_dir = BPC_future/results/gat_batch_impact_threshold_frontier_v7_mixed_worker_validation_full_context_fallback_20260616
global_frontier_count = 13837
family_local_frontier_count = 1609
family_delay_fallback_frontier_count = 19320
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
```

best global candidate：

```text
accepted_batch_count = 54
safe_precision_ci_low = 0.9335841332189981
accepted_batch_roi = 3.5975349268002765
accepted_batch_roi_ci_low = 1.227382412845194
family_holdout_min_accepted_roi = 0.11975858719658088
reject = ['family_holdout_accepted_roi_below_threshold']
```

best context fallback candidate：

```text
accepted_batch_count = 38
safe_precision_ci_low = 0.90818706741616
accepted_batch_roi = 5.043548252412381
accepted_batch_roi_ci_low = 1.7721734847088793
family_holdout_min_accepted_roi = 0.11975858719658088
reject = ['family_holdout_accepted_roi_below_threshold']
```

best candidate with family ROI not rejected and false-HP not rejected：

```text
threshold_mode = family_delay_fallback
accepted_batch_count = 29
safe_precision_ci_low = 0.8830264055344442
accepted_batch_roi_ci_low = 2.461242560367527
family_holdout_min_accepted_roi = 6.603846111174287
reject = ['safe_precision_ci_low_below_threshold_or_not_measurable']
```

解释：context fallback 让 coverage/ROI tradeoff 更好，但还不能同时满足 family ROI、false-HP 和 safe CI。当前离可行 gate 最近的是 accepted=29、0 false-HP、family ROI 通过，但 safe CI low 只有 0.883，离 0.90 还差验证支撑。

## kNN/OOD

```text
knn_ood_dir = BPC_future/results/gat_batch_impact_knn_ood_audit_v7_mixed_worker_validation_full_context_fallback_20260616
validation_candidate_ready = false
production_ready = false
accepted_batch_count = 1
accepted_batch_rate = 0.010869565217391304
safe_precision_ci_low = 0.20654329147389294
accepted_batch_roi = 1.1059776544570923
accepted_batch_roi_ci_low = None
false_safe_rate_union = 0.0
```

kNN/OOD shell 仍过于保守，只接受 1 个 batch；这不能作为 Stage 4 safe source。

## 当前判断

- 继续扩样是有效的：same-context comparable pairs 从 v6 的 27 提升到 v7 的 38。
- context fallback 是必要方向，但当前实现只能部分缓解 family ROI collapse。
- 主要 blocker 已经更清楚：不是 ROI point estimate，而是 `safe_precision_ci_low`、candidate-level false-high-priority-on-delay 和 kNN/OOD accepted coverage。
- 不能进入 Stage 4 mutating admission；no-safe-source pass-through 仍是唯一安全 online 行为。

## 下一步

1. 继续补 validation same-context worker，目标是让 no-family/no-falseHP 候选的 accepted count 从 29 提到至少 35 左右，先跨过 Wilson 0.90 lower bound。
2. 训练 loss 继续加强 candidate-level delay suppression，降低 frontier 中的 `false_high_priority_on_delay_too_high`。
3. kNN/OOD 需要调 radius/grouping 或训练 embedding，使 accepted batch 不再只有 1-2 个，但 false-safe 仍保持 0。
4. 只有 threshold/frontier feasible、kNN/OOD candidate ready、5/10 no-regression、20-task ROI A/B 都通过后，才允许 Stage 4 opt-in mutation。
