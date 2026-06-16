# BPC_future GAT Target Mode Stage 3 v8 硬门槛状态报告

日期：2026-06-16

## 结论

本轮把 Stage 3 训练目标从普通 classification / loss selection 明确推进到
`precision-constrained ROI maximization`：

- checkpoint selection 先过 precision / ROI / safety / coverage gate，再比较 utility / ROI / loss；
- pairwise ranking loss 已在同 context ROI 可比 pair 上启用；
- accepted batch ROI、precision confidence lower bound、false-safe、family fallback 都进入 reject reason；
- GAT 仍为 diagnostic-only，不能作为 pricing oracle、certificate source 或 official bound source。

v8 的训练与 threshold frontier 已经出现强 sector-wave 候选，但还不能进入 Stage 4
production candidate：random-wave 在 validation 中存在 oracle high-ROI opportunity，却被当前
family fallback 全部延迟；KNN/OOD 变体即使数值硬指标可过，也必须保留
`production_ready=false`。

## 本轮输入与改动

### 1. validation-only worker rows

从 v7 opportunity mining 中选出 task20 validation contexts，并用
`--require-opportunity-context` 限制 multibatch intervention plan 只能选真实出现在
opportunity rows 的 context，避免 fallback 到 train split context。

新增 6 条 validation worker rows：

```text
row_count = 6
positive_objective_improvement_count = 6
context_count = 6
worker_target_causal_match = true for all rows
```

这些 rows 单独构不成 same-context pair，所以 worker row builder 的 standalone
`all_checks_pass=false` 只表示“单独训练不够”；合并进 v8 mixed dataset 后训练检查通过。

### 2. mixed v8 dataset

`build_gat_batch_impact_dataset.py` 支持重复 `--input-jsonl`，v8 合并三类来源：

- v14 same-run combined rows；
- v3 worker validation full rows；
- v8 validation-only target-worker rows。

v8 dataset 摘要：

```text
sample_count = 320
candidate_count = 4595
batch_label_counts = {'non_improving': 67, 'roi_positive': 253}
candidate_label_counts = {'delay_queue': 322, 'high_priority': 4273}
family_counts = {'greedy-anchor': 54, 'random-wave': 193, 'sector-wave': 73}
task_count_counts = {'5': 2, '10': 8, '20': 144, '30': 76, '50': 89, '100': 1}
ranking_ready = true
training_ready = true
```

## v8 Training

训练命令使用硬门槛：

```text
--min-validation-high-priority-precision 0.90
--min-validation-high-priority-precision-ci-low 0.90
--min-validation-safe-precision 0.90
--min-validation-safe-precision-ci-low 0.90
--max-false-high-priority-on-delay 0.01
--max-false-safe-union-rate 0.02
--min-accepted-batch-roi 0.65
--min-accepted-batch-roi-ci-low 0.65
--baseline-accepted-batch-roi 0.45
--min-roi-margin-over-baseline 0.20
```

训练结果：

```text
training_objective = precision_constrained_roi_maximization
checkpoint_selection = deployment_gate_first_then_utility_roi_loss
best_epoch = 4
best_loss_epoch = 7
selected_checkpoint_reason = local_deployment_gate_passed_then_ranked_by_utility_roi_loss
pairwise_ranking_loss_active = true
nonfinite_skipped_update_rate = 0.0
checkpoint_gate_pass = false
stage4_candidate_ready = false
rejected_checkpoint_reasons = ['knn_ood_audit_missing']
```

关键 deployment metrics：

```text
accepted_batch_count = 35
accepted_batch_rate = 0.35714285714285715
accepted_batch_roi = 8.824355633769716
accepted_batch_roi_ci_low = 4.923453034500176
accepted_batch_roi_over_baseline_ci_low = 4.473453034500176
expected_trajectory_utility = 8.848641348055432
high_priority_precision = 1.0
high_priority_precision_ci_low = 0.9928440716963813
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
family_delay_fallback_families = ['greedy-anchor', 'random-wave']
```

这说明训练阶段已经把 ROI 和精准率纳入 checkpoint selection，而不是训练后再报告。
`best_epoch=4` 覆盖了 `best_loss_epoch=7`，正是 hard gate first 的预期行为。

## Threshold Frontier

frontier 审计展开所有候选 threshold：

```text
feasible_threshold_count = 282
checkpoint_feasible_threshold_count = 0
best.threshold_mode = family_delay_fallback
best.accepted_batch_count = 35
best.safe_precision_ci_low = 0.9010957324106112
best.accepted_batch_roi_ci_low = 4.923453034500176
best.false_high_priority_on_delay = 0.0
best.false_safe_rate_union = 0.0
best.family_delay_fallback_families = ['greedy-anchor', 'random-wave']
```

`checkpoint_feasible_threshold_count=0` 的原因不是本地 hard gate 失败，而是 frontier
运行时尚未完成 KNN/OOD 审计，所有 checkpoint-level candidate 都带
`knn_ood_audit_missing`。

## KNN/OOD 审计

### strict global shell

```text
knn_k = 3
max_neighbor_delay_fraction = 0.0
accepted_batch_count = 19
safe_precision_ci_low = 0.8318156346315495
accepted_batch_roi_ci_low = 0.3377305496827247
production_ready = false
```

strict global kNN/OOD 太保守，挡掉了部分高 ROI sector-wave batch，导致 precision CI
和 ROI CI 都不过硬门槛。

### family shell

```text
knn_k = 3
threshold_grouping = family
accepted_batch_count = 18
safe_precision_ci_low = 0.8241154494176252
accepted_batch_roi_ci_low = 0.30512991782027354
production_ready = false
```

family grouping 没有改善，仍然过保守。

### global shell with one-delay-neighbor tolerance

```text
knn_k = 3
max_neighbor_delay_fraction = 0.34
accepted_batch_count = 35
accepted_batch_rate = 0.35714285714285715
accepted_batch_roi = 8.824355633769716
accepted_batch_roi_ci_low = 4.923453034500176
safe_precision = 1.0
safe_precision_ci_low = 0.9010957324106112
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
coverage = 1.0
production_ready = false
production_block_reasons = ['family_holdout_accepted_batch_missing', 'validation_candidate_not_ready']
```

这个变体在数值硬指标上过线，但仍不能称为 Stage 4 candidate。原因是
validation family audit 显示：

```text
oracle_high_roi_families = ['random-wave', 'sector-wave']
missing_accepted_opportunity_families = ['random-wave']
```

也就是说，当前策略实质上是 sector-wave-only 放行；random-wave 的 high-ROI opportunity
还没有被模型/阈值安全覆盖。

## Exactness Boundary

本轮所有脚本和报告保持：

```text
diagnostic_only = true
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
official_bound_effect = false
```

GAT/CBF/kNN/OOD 只能影响 true-RC verified negative column 的 admission scheduling。
最终 certificate 仍只能来自当前 branch/cut/dual 下 exact pricing 对完整配置宇宙的
no-negative closure。

## 下一步

1. 补 random-wave same-context / target-worker intervention rows，优先覆盖 validation 中已知
   oracle high-ROI but delayed 的 contexts。
2. 重新训练 v9，并保持当前 hard gate：precision / ROI / CI / false-safe 不降标。
3. 如果先做 Stage 4 shadow，只能把 safe source 明确限制为 sector-wave-only，并把
   `production_ready=false`、coverage 限制和 family fallback 写入 safe-source artifact。
4. Stage 4 仍需 5/10 no-regression、20-task wall-time/tail retry ROI，以及 final certificate
   safety audit；Stage 3 离线通过不能替代这些在线证据。
