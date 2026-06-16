# GAT Target Mode Stage 3 v6 验证扩样与 Family Fallback 报告

日期：2026-06-16

## 结论

Stage 3 的训练目标已按 deployment-facing 口径硬化：训练不是追求 validation loss、F1 或 recall，而是 `precision_constrained_roi_maximization`。checkpoint 选择必须先过 precision / safe precision / ROI / confidence lower bound / coverage / family holdout gate，再比较 utility 和 loss。

v6 数据和训练比 v4/v5 更接近可用：同 context 可比较 pair 增多，pairwise ranking loss 已激活，selected validation batch 的 point estimate ROI 很高，false-safe 为 0。但当前仍不是 Stage 4 safe source，主要原因是 accepted batch 支撑数不足，safe precision 的 Wilson lower bound 不达 0.90；kNN/OOD shell 也过于保守。

```text
stage3_candidate_ready = false
production_ready = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

## 本轮新增数据

worker validation 扩样输出：

```text
rows_dir = BPC_future/results/gat_multibatch_worker_batch_impact_rows_v3_signature_hard_roi_validation_expanded_20260616
row_count = 14
context_count = 5
pairwise_context_count = 5
positive_objective_improvement_count = 12
non_improving_objective_count = 2
skipped_counts = {'missing_worker_logs': 21}
```

v6 mixed dataset：

```text
dataset_dir = BPC_future/data/gat_batch_impact/v6_mixed_v3_plus_worker_validation_expanded_20260616
sample_count = 308
candidate_count = 4583
family_counts = {'greedy-anchor': 54, 'random-wave': 193, 'sector-wave': 61}
task_count_counts = {'10': 8, '100': 1, '20': 132, '30': 76, '5': 2, '50': 89}
same_context_comparable_pair_count = 27
ranking_ready = true
training_ready = true
```

## 训练结果

训练输出：

```text
training_dir = BPC_future/results/gat_batch_impact_training_v6_mixed_worker_validation_expanded_fallback_20260616
training_objective = precision_constrained_roi_maximization
checkpoint_selection = deployment_gate_first_then_utility_roi_loss
pairwise_ranking_status = active_same_context_roi_margin_ranking
checkpoint_gate_pass = false
stage4_candidate_ready = false
stage4_blockers = ['knn_ood_audit_missing', 'knn_ood_holdout_audit_not_run', 'online_shadow_and_opt_in_ab_not_run', 'safe_precision_ci_low_below_threshold_or_not_measurable']
```

selected validation metrics：

```text
threshold_mode = family_local_batch_candidate
accepted_batch_count = 7
safe_precision = 1.0
safe_precision_ci_low = 0.6456611570247934
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9959384319742334
accepted_batch_roi = 18.980578677994863
accepted_batch_roi_ci_low = 6.450565547872774
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
family_specific_delay_fallback_families = ['greedy-anchor']
family_delay_fallback_families = []
```

解释：ROI 和 high-priority precision 已经不是主要 blocker；当前 blocker 是 accepted batch count 太少，导致 safe precision lower bound 只有 0.646，达不到 Stage 4 的 0.90。

## Threshold Frontier 与 Fallback

本轮补齐了 threshold frontier 审计口径：除了 global 和 family-local threshold，也把 trainer 中的 family-delay fallback 候选纳入 frontier，并在 train metrics 回算时使用同一套 fallback families。

```text
frontier_dir = BPC_future/results/gat_batch_impact_threshold_frontier_v6_mixed_worker_validation_expanded_fallback_20260616
global_frontier_count = 13015
family_local_frontier_count = 1250
family_delay_fallback_frontier_count = 4791
feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
```

best global candidate：

```text
accepted_batch_count = 44
safe_precision_ci_low = 0.919701682217986
accepted_batch_roi = 3.601989853854899
accepted_batch_roi_ci_low = 0.787639392741144
family_holdout_min_accepted_roi = 0.11975858719658088
reject = ['family_holdout_accepted_roi_below_threshold']
```

best family-local candidate：

```text
accepted_batch_count = 15
safe_precision_ci_low = 0.7961107336956521
accepted_batch_roi = 10.158267388741175
accepted_batch_roi_ci_low = 2.847036888034962
reject = ['safe_precision_ci_low_below_threshold_or_not_measurable']
```

best family-delay fallback candidate：

```text
accepted_batch_count = 25
safe_precision_ci_low = 0.8668035060468212
accepted_batch_roi = 6.174587808847427
accepted_batch_roi_ci_low = 1.42949258589271
family_delay_fallback_families = ['greedy-anchor', 'random-wave']
reject = ['safe_precision_ci_low_below_threshold_or_not_measurable']
```

解释：global threshold 有足够 safe CI，但 family ROI 坍塌；family-local 和 family-delay fallback 的 ROI 很强，但 safe CI lower bound 不足。fallback 方向有价值，但当前不能作为 Stage 4 admission safe source。

## kNN/OOD Audit

```text
knn_ood_dir = BPC_future/results/gat_batch_impact_knn_ood_audit_v6_mixed_worker_validation_expanded_fallback_20260616
validation_candidate_ready = false
production_ready = false
accepted_batch_count = 2
safe_precision = 1.0
safe_precision_ci_low = 0.3423719528896193
accepted_batch_roi = 1.1196053624153137
accepted_batch_roi_ci_low = 1.0928950548171996
false_safe_rate_union = 0.0
production_block_reasons = ['validation_safe_precision_ci_low_below_min', 'validation_candidate_not_ready']
```

解释：kNN/OOD shell 没有 false-safe，但 accepted 太少，safe CI lower bound 只有 0.342；它只能作为 diagnostic，不是 online admission gate。

## 当前判断

- 训练阶段确实必须考虑回报率和精准率；现在主计划、loss、threshold search、checkpoint selection、frontier 审计都按这个方向收紧。
- v6 的正向变化是 ROI gate 明显不再是主要问题；真正的问题变成 lower-bound sample support 和 family/context 泛化。
- 不能把 zero-FP、低 coverage 的壳包装成可用模型；accepted count 不足时必须继续标记 `stage4_candidate_ready=false`。
- 不能让 GAT/CBF/kNN/OOD 参与证明；它们只能做 search priority 和 admission scheduling。最终 certificate 仍必须由当前 branch/cut/dual 下 exact pricing full closure 给出。

## 下一步

1. 继续扩 same-context validation intervention，优先补能增加 accepted count 且覆盖 `random-wave` / `sector-wave` 的 hard-tail context。
2. 针对 family fallback 做更细粒度规则，避免因为某个 family 内低 ROI 子群导致整个高 ROI family 被 delay。
3. kNN/OOD audit 要从 accepted=2 提高到足够支撑 Wilson lower bound 的数量级；按当前 0 false-safe 且目标 CI low 0.90，safe all-success count 需要约 35。
4. 在进入 Stage 4 前，必须同时得到：threshold/frontier feasible、kNN/OOD validation candidate ready、5/10 no-regression shadow、20-task ROI A/B。
