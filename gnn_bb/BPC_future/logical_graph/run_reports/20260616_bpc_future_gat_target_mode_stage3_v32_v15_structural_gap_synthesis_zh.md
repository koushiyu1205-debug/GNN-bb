# BPC Future GAT Target Mode Stage 3 v32 v15 Structural Gap 综合报告

日期：2026-06-16

## 结论

v15 missed high-ROI 不是简单“分数差一点”，而是 candidate head 与 embedding 表示同时暴露结构性缺口。

已有 score-margin 审计显示：16 个 missed high-ROI 全部是 `no_candidate_above_threshold`，candidate margin 平均 `-0.3829`，最深 `-0.8569`，最大也只有 `-0.0723`；其中 `11` 个是 deep gap，`5` 个是 moderate gap，没有 near-threshold 正 margin。

v32 embedding separation 审计进一步确认：16 个 missed high-ROI 中 `10` 个在训练 embedding 空间里最近 low-ROI/bad 邻居比最近 high-ROI 邻居更近；missed 的 5-NN high-ROI fraction 均值只有 `0.1625`，而 accepted high-ROI 的均值为 `0.5`。这说明 v15 不是靠调低 threshold 或 rescue window 就能修好的问题。

```text
stage = Stage 3
variant = v32_v15_embedding_separation
diagnostic_only = true
runs_bpc_or_pricing = false
selector_can_certificate = false
official_bound_effect = false
candidate_threshold = 0.9019626379013062
missed_high_roi_opportunities = 16
missed_candidate_score_margin_mean = -0.3829170756507665
missed_candidate_score_margin_min = -0.8569196499884129
missed_candidate_score_margin_max = -0.07226938009262085
missed_nearest_negative_closer_count = 10
missed_knn_positive_fraction_mean = 0.1625
accepted_high_roi_knn_positive_fraction_mean = 0.5
```

## 证据

### Score Margin

```text
high_roi_opportunities = 28
accepted_high_roi_opportunities = 12
missed_high_roi_opportunities = 16
missed_reason_counts = {'no_candidate_above_threshold': 16}
candidate_margin_bucket_counts = {'deep_candidate_score_gap': 11, 'moderate_candidate_score_gap': 5}
missed_without_same_context_contrast_count = 7
```

Family breakdown：

```text
random-wave missed = 5, all task50, all deep gap, mean margin = -0.5054
sector-wave missed = 11, all task20, 6 deep + 5 moderate, mean margin = -0.3272
```

### Embedding Separation

```text
train_record_count = 222
validation_record_count = 110
knn_k = 5
missed_nearest_negative_closer_count = 10 / 16
random-wave missed_nearest_negative_closer_count = 5 / 5
sector-wave missed_nearest_negative_closer_count = 5 / 11
missed_nearest_positive_distance_mean = 0.820577759166009
missed_nearest_negative_distance_mean = 0.7116149044142464
```

解释：

- `random-wave` 的 5 个 missed 全部更靠近 negative 邻域，是最明确的结构性不可分区域。
- `sector-wave` 有 5/11 更靠近 negative；剩余部分虽然最近 positive 更近，但 candidate score 仍大幅低于 threshold，说明 head/embedding 对 high-ROI safe candidate 的排序仍不稳定。
- accepted high-ROI 的 kNN positive fraction 明显高于 missed high-ROI，表示模型对“能接受的 high-ROI”和“漏掉的 high-ROI”在表示空间内已经形成不同区域。

## 对 v31 的影响

v31 rescue window 主要解释 v28/v29 的 risk-adjusted suppression；它不适合修 v15。v15 没有 risk suppression blocker，主要是 raw candidate score gap 和 embedding 邻域混杂。

因此不能把 v15 下一步定义为：

- 降低 `candidate_threshold`；
- 放宽 rescue window；
- 把 true-RC negative / exact-id hit 当作 positive admission 标签；
- 放宽 Stage 3 precision / ROI / CI / false-safe gate。

## 下一步

1. 针对 `random-wave task50` missed context 补 same-context 正负对照，优先让 high-ROI 和 low-ROI/bad 在 embedding 空间可分。
2. 针对 `sector-wave task20` 的 moderate gap 样本，加 context-local margin / candidate-head contrast，让 high-ROI safe candidate 的 score 排到同 context negative 前面。
3. 训练目标继续保持 `precision_constrained_roi_maximization`，不要用 recall 或 true-RC 命中率替代 ROI/safety gate。
4. 下一版训练应报告两个新增诊断：missed high-ROI embedding neighbor mix、candidate score margin bucket。只有这两项同时改善，才值得进入 Stage 4 shadow。

## 产物

```text
embedding_separation_summary =
  BPC_future/results/gat_batch_impact_embedding_separation_v15_exact_safe_hits_batch8_ab_roi_20260616/summary.json
embedding_separation_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v32_v15_embedding_separation_audit_zh.md
score_margin_summary =
  BPC_future/results/gat_batch_impact_score_margin_audit_v15_exact_safe_hits_batch8_ab_roi_20260616/summary.json
score_margin_report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_batch_impact_score_margin_audit_v15_exact_safe_hits_batch8_ab_roi_zh.md
```

## 验证

```text
python -m py_compile audit_gat_batch_impact_embedding_separation.py = pass
python -m unittest BPC_future.tests.test_gat_batch_impact_embedding_separation = 2 tests OK
v15 embedding separation audit = pass
```
