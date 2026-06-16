# 2026-06-16 GAT Target Mode Stage 3/4 v22 Positive Candidate Boost Synthesis

## 结论

v22 在 v21 数据不变的前提下，只改变训练 surrogate：新增并显式开启
`hard_roi_positive_candidate_loss_multiplier = 2.0`，对“达到 hard ROI gate 且非
bad-mode 的 batch 内真实 HIGH_PRIORITY 候选”增加候选头召回压力。

该实验保持 exact-safe 边界：

```text
runs_bpc_or_pricing = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
production_ready = false
default_enabled = false
```

核心结果：v22 不是 Stage 4 ready，但证明 v21 的 blocker 可以被训练目标改善。
validation high-ROI capture 从 v21 的 `4 / 30` 提升到 v22 的 `10 / 30`，
accepted low-ROI/bad 仍为 `0`。当前硬 blocker 变成 accepted safe 样本数不足导致
safe precision CI-low 不达标，而不是 ROI 不够。

## 产物

```text
training =
  BPC_future/results/gat_batch_impact_training_v22_positive_candidate_boost_v21_data_20260616/metrics.json
checkpoint =
  BPC_future/data/gat_batch_impact/v22_positive_candidate_boost_v21_data_20260616/gat_batch_impact.pt
knn_ood =
  BPC_future/results/gat_batch_impact_knn_ood_v22_positive_candidate_boost_global_20260616/summary.json
threshold_frontier =
  BPC_future/results/gat_batch_impact_threshold_frontier_v22_positive_candidate_boost_20260616/summary.json
opportunity_mining =
  BPC_future/results/gat_batch_impact_opportunity_mining_v22_positive_candidate_boost_20260616/summary.json
score_margin =
  BPC_future/results/gat_batch_impact_score_margin_audit_v22_positive_candidate_boost_20260616/summary.json
```

## Training / Frontier

```text
best_epoch = 8
checkpoint_gate_pass = false
stage4_candidate_ready = false

validation accepted_batch_count = 10
validation accepted_batch_roi = 16.32825751900673
validation accepted_batch_roi_ci_low = 6.201525818837059
validation high_priority_precision_ci_low = 0.965238155466207
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.7224598312333834
validation false_high_priority_on_delay = 0.00847457627118644
validation false_safe_rate_union = 0.00847457627118644

best_local_reject_reasons =
  ['safe_precision_ci_low_below_threshold_or_not_measurable']
primary_blocker =
  confidence_lower_bound_sample_size_or_acceptance_count_blocker
safe_all_success_count_needed_for_ci_low_0.9 = 35
```

解释：threshold frontier 下没有可通过 Stage 3/4 gate 的点；best global 点 ROI
很强，但只 accepted 10 个 batch。Wilson 下界要求约 35 个全安全 accepted 样本才能
支撑 `safe_precision_ci_low >= 0.9`。

## kNN/OOD

```text
validation accepted_batch_count = 9
validation accepted_batch_roi = 13.5515608853764
validation accepted_batch_roi_ci_low = 4.003538240157702
validation safe_precision = 1.0
validation safe_precision_ci_low = 0.7008472464490406
validation false_high_priority_on_delay = 0.0
validation false_safe_rate_union = 0.0

production_block_reasons =
  ['validation_safe_precision_ci_low_below_min',
   'validation_candidate_not_ready']
```

kNN/OOD 把 false-safe 降为 0，但 accepted 从 10 降到 9，CI 下界更低。当前不是
发现明确 unsafe 漏进，而是 accepted safe evidence 太少。

## Opportunity / Margin

```text
high_roi_opportunities = 30
accepted_high_roi_opportunities = 10
missed_high_roi_opportunities = 20
accepted_high_roi_capture_rate = 0.3333333333333333
accepted_low_roi_or_bad = 0

missed_reason_counts =
  {'no_candidate_above_threshold': 20}

candidate_margin_bucket_counts =
  {'deep_candidate_score_gap': 12,
   'moderate_candidate_score_gap': 6,
   'near_candidate_threshold': 2}

missed_candidate_score_margin_mean = -0.3812758083455265
missed_candidate_score_margin_median = -0.4011151432991028
missed_candidate_score_margin_min = -0.8909112956374884
missed_candidate_score_margin_max = -0.01867809295654299
```

对比 v21：

```text
v21 accepted_high_roi_opportunities = 4
v21 missed_high_roi_opportunities = 26
v21 margin buckets =
  {'deep_candidate_score_gap': 25,
   'near_candidate_threshold': 1}

v22 accepted_high_roi_opportunities = 10
v22 missed_high_roi_opportunities = 20
v22 margin buckets =
  {'deep_candidate_score_gap': 12,
   'moderate_candidate_score_gap': 6,
   'near_candidate_threshold': 2}
```

结论：v22 让一部分 high-ROI candidate 从深低分区域移动到可 accepted 或接近阈值；
但剩余 missed 仍有 12 个 deep gap，不能靠降低 threshold 解决。

## 下一步

1. 不降低 Stage 3/4 hard gate，不把 v22 标成 production-ready。
2. 数据采集优先补同 context 正负对照，尤其：
   `9fadf4f7b39742a2`、`b6d808ebac2a6dd8`、`a67f331bdb819d7d`、
   `e6b17bbf825984ae`。
3. 模型训练下一轮应考虑 context-local margin / candidate calibration，而不是单纯继续加大正候选 boost。
4. 若进入 Stage 4 shadow，只能作为 diagnostic safe-source；最终 certificate 仍必须由 current branch/cut/dual 下的 exact pricing full scan 证明全宇宙无负 reduced-cost journey。

## 验证

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest BPC_future.tests.test_gat_batch_impact_training

Ran 14 tests in 0.240s
OK
```
