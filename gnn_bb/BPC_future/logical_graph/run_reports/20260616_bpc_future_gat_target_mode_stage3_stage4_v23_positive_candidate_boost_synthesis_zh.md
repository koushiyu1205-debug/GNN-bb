# 2026-06-16 GAT Target Mode Stage 3/4 v23 Positive Candidate Boost Synthesis

## 结论

v23 train first-tranche 已完成执行、reachability / ROI / certificate 审计、rows
回流、mixed dataset 重建、v22-style positive-candidate boost 训练与离线审计。

核心结论：v23 不是 Stage 4 ready，但它把问题从“missed high-ROI 太多”推进到
“召回过宽导致 low-ROI / delay-risk 误收太多”。因此下一步不应继续加大
positive boost 或降低 threshold，而应做 delay-risk / low-ROI suppression，或在
kNN/OOD 后专门修 ROI CI。

所有产物仍是 diagnostic-only：GAT 不能做 pricing oracle，不能产生 official
bound，不能作为 certificate。最终 certificate 仍必须由当前 branch/cut/dual 下的
exact pricing full closure 给出。

## 产物

```text
runbook_execution =
  BPC_future/results/gat_batch_impact_multibatch_intervention_plan_v23_train_split_remaining_contrast_first_tranche_20260616/worker_ab_runbook/runbook_execution_summary.json
ab_audit =
  BPC_future/results/gat_target_priority_worker_ab_v23_train_split_remaining_contrast_first_tranche_audit_20260616/summary.json
reachability =
  BPC_future/results/gat_target_intervention_reachability_v23_train_split_remaining_contrast_first_tranche_20260616/summary.json
certificate_audit =
  BPC_future/results/gat_target_mode_certificate_audit_v23_train_split_remaining_contrast_first_tranche_20260616/summary.json
rows =
  BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/summary.json
dataset =
  BPC_future/data/gat_batch_impact/v23_mixed_v21_plus_train_split_remaining_contrast_first_tranche_ab_roi_20260616
training =
  BPC_future/results/gat_batch_impact_training_v23_positive_candidate_boost_v23_data_20260616/metrics.json
knn_ood =
  BPC_future/results/gat_batch_impact_knn_ood_v23_positive_candidate_boost_global_20260616/summary.json
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v23_positive_candidate_boost_20260616/summary.json
opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v23_positive_candidate_boost_20260616/summary.json
score_margin =
  BPC_future/results/gat_batch_impact_score_margin_audit_v23_positive_candidate_boost_20260616/summary.json
```

## A/B / Reachability / Certificate

```text
runbook_command_count = 26
executed_count = 26
failed_command_count = 0
5/10 sentinels = OPTIMAL

ab_record_count = 12
roi_class_counts =
  {'negative_primal_roi': 1,
   'negative_retry_roi': 4,
   'no_observed_roi': 2,
   'positive_retry_roi': 5}
positive_trajectory_roi_count = 5
nonpositive_roi_count = 7

reachable_target_intervention_count = 12 / 12
training_label_allowed = 12 / 12
certificate_violation_count = 0
```

这批 rows 是有效训练证据，不是 online safety proof。它们说明同 context 内确实同时
存在 useful retry ROI 与拖尾/低 ROI 负例。

## Dataset

v23 dataset 在 v21 的 11 个 source JSONL 基础上追加 v23 12 条 rows：

```text
sample_count = 375        # v21: 363
candidate_count = 4678    # v21: 4666
family_counts = {'greedy-anchor': 54, 'random-wave': 218, 'sector-wave': 103}
task_count_counts = {'5': 2, '10': 8, '20': 192, '30': 76, '50': 96, '100': 1}
same_context_pair_count = 286
same_context_comparable_pair_count = 268
positive_negative_label_pair_count = 88
training_ready = true
ranking_ready = true
```

对比 v21，same-context comparable pairs 从 `203` 增至 `268`，positive/negative
label pairs 从 `72` 增至 `88`。这说明 v23 的数据闭环确实补到了 candidate head
所需的对照。

## Training / Frontier

训练只复用 v22 的目标强化：

```text
hard_roi_positive_candidate_loss_multiplier = 2.0
pairwise_candidate_ranking_loss_multiplier = 0.0
training_objective = precision_constrained_roi_maximization
```

结果：

```text
best_epoch = 8
checkpoint_gate_pass = false
stage4_candidate_ready = false
validation accepted_batch_count = 56
validation accepted_batch_roi = 5.331371024134569
validation accepted_batch_roi_ci_low = 2.703146826585392
validation high_priority_precision = 0.9567567567567568
validation high_priority_precision_ci_low = 0.9416508253091629
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.9358038555118847
validation false_high_priority_on_delay = 0.425531914893617
validation false_safe_rate_union = 0.425531914893617
rejected_checkpoint_reasons =
  ['false_high_priority_on_delay_too_high',
   'false_safe_rate_union_too_high',
   'knn_ood_audit_missing']
```

threshold frontier 没有可通过 Stage 3/4 gate 的点。best family-delay-fallback 点
accepted 59，ROI CI 与 safe CI 都够，但 false-safe 仍约 `0.521`。

硬结论：v23+positive boost 的召回太激进，不能上线，也不能作为 Stage 4 admission
candidate。现在的主要 blocker 不是 high-ROI capture，而是 delay-risk / low-ROI
抑制。

## kNN/OOD

global kNN/OOD 同口径审计：

```text
accepted_batch_count = 37
accepted_batch_roi = 2.7717488413374567
accepted_batch_roi_ci_low = 0.16378971779217766
safe_precision = 1.0
safe_precision_ci_low = 0.9059390425448562
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
production_block_reasons =
  ['validation_accepted_batch_roi_ci_low_below_min',
   'validation_candidate_not_ready']
```

kNN/OOD 能把 false-safe 压回 0，并让 safe CI 过同口径 `0.85`，但 ROI CI-low
掉到 `0.164`，低于 `0.65`。这说明 safety shell 方向有效，但当前会留下太多低 ROI
accepted，或把 high-ROI utility 稀释掉。

## Opportunity / Margin

在 threshold-frontier selected rule 下：

```text
high_roi_opportunities = 30
accepted_high_roi_opportunities = 27
missed_high_roi_opportunities = 3
accepted_high_roi_capture_rate = 0.9
accepted_low_roi_or_bad = 39

candidate_margin_bucket_counts =
  {'deep_candidate_score_gap': 1,
   'near_candidate_threshold': 2}
missed_reason_counts =
  {'batch_score_below_family_threshold': 3,
   'no_candidate_above_threshold': 1}
```

对比 v22：accepted high-ROI 从 `10 / 30` 增到 `27 / 30`，deep candidate gap 从
`12` 降到 `1`。因此 v15/v22 的 missed high-ROI 不是结构性完全分不开，v23 数据和
positive boost 已经基本解决 candidate recall。

但 `accepted_low_roi_or_bad = 39` 说明当前模型把太多拖尾/低 ROI 负列也抬成了
HIGH_PRIORITY。下一步应优先修 false-safe，而不是继续补普通 high-ROI recall。

剩余 missed：

```text
45baa40751a0bf77  sector-wave task20  deep candidate score gap
ce3508e12ad69da7  sector-wave task20  near batch threshold
e6b17bbf825984ae  random-wave task50  near batch threshold, lacks same-context contrast
```

## 下一步

1. 不把 v23 checkpoint 放入 Stage 4 online admission；保持 opt-in / diagnostic-only。
2. 训练目标下一轮应增加 hard negative / delay-risk suppression，而不是继续提高
   `hard_roi_positive_candidate_loss_multiplier`。
3. 尝试 candidate-level false-safe penalty、delay-risk calibration、或恢复
   candidate-pairwise margin，但必须用 false-safe / ROI CI 作为 checkpoint gate。
4. kNN/OOD 后的 ROI CI 是新的关键指标：需要让 false-safe=0 的同时把
   accepted_batch_roi_ci_low 拉回 `>= 0.65`。
5. 对剩余 3 个 missed high-ROI，只需要窄补：尤其 `e6b17bbf825984ae` 缺同 context
   contrast；`45baa40751a0bf77` 是唯一还深分数缺口的样本。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
  BPC_future.tests.test_gat_batch_impact_training \
  BPC_future.tests.test_gat_multibatch_worker_batch_impact_rows \
  BPC_future.tests.test_gat_target_priority_worker_ab_runbook

Ran 24 tests in 0.162s
OK
```
