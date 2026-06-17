# 2026-06-16 BPC_future GAT Stage 3 v57-v60 v55 Individual Follow-up Ranking 综合报告

## 读取范围

本轮继续复读：

- `BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md`
- Stage 1 模型结构报告
- Stage 2 数据采集报告
- Stage 4 v53 individual follow-up 执行综合报告
- Stage 3/4 v54-v56 individual follow-up 综合报告

目标边界保持不变：GAT / CBF / kNN / OOD 只能做 discovery、ordering 和 finite-delay admission scheduling。所有进入 RMP 的列必须 true-RC verified；最终 certificate 只能来自当前 branch/cut/dual 下 exact pricing full closure。

## 本轮产物

### v57 threshold frontier

```text
summary =
  BPC_future/results/gat_batch_impact_threshold_frontier_v57_v55_individual_followup_20260616/summary.json

report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v57_v55_individual_followup_threshold_frontier_zh.md

feasible_threshold_count = 0
checkpoint_feasible_threshold_count = 0
primary_blocker = model_ranking_false_delay_blocker
best_accepted_batch_count = 3
best_accepted_batch_roi_ci_low = 23.902832583252618
best_safe_precision_ci_low = 0.4384939195509822
```

best threshold 的 reject reasons：

```text
high_priority_precision_below_threshold_or_no_predictions
high_priority_precision_ci_low_below_threshold_or_not_measurable
safe_precision_ci_low_below_threshold_or_not_measurable
false_high_priority_on_delay_too_high
false_safe_rate_union_too_high
family_holdout_accepted_batch_missing
```

解释：v55 selected checkpoint 的高 ROI 点很高，但 accepted 只有 3，HP precision 只有 `0.333333`，false-delay 仍超 gate。完整 frontier 没有找到可行 threshold。

### v58 opportunity mining

```text
summary =
  BPC_future/results/gat_batch_impact_opportunity_mining_v58_v55_individual_followup_20260616/summary.json

report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v58_v55_individual_followup_opportunity_mining_zh.md

validation_records = 136
high_roi_opportunities = 32
accepted_high_roi_opportunities = 3
missed_high_roi_opportunities = 29
accepted_high_roi_capture_rate = 0.09375
```

family split：

```text
random-wave: high_roi = 6, accepted = 0, missed = 6
sector-wave: high_roi = 26, accepted = 3, missed = 23
```

miss reasons：

```text
batch_score_below_family_threshold = 28
candidate_delay_risk_above_threshold = 27
candidate_risk_adjusted_below_threshold = 27
no_candidate_above_threshold = 29
```

解释：v55 对 random-wave 仍是 0 capture；sector-wave 的 high-ROI 也大多被 delay/risk-adjusted gate 压掉。

### v59 score-margin audit

```text
summary =
  BPC_future/results/gat_batch_impact_score_margin_audit_v59_v55_individual_followup_20260616/summary.json

report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v59_v55_individual_followup_score_margin_audit_zh.md

missed_high_roi_opportunities = 29
risk_adjusted_suppressed_miss_count = 27
missed_without_same_context_contrast_count = 8
candidate_margin_bucket_counts = {
  'moderate_candidate_score_gap': 13,
  'near_candidate_threshold': 16
}
raw_candidate_margin_bucket_counts = {
  'moderate_candidate_score_gap': 1,
  'near_candidate_threshold': 28
}
```

解释：和 v15 的 deep candidate/embedding gap 不同，v55 的 missed high-ROI 在 raw candidate score 上大多已经接近阈值；问题主要在 risk-adjusted admission 之后被 delay-risk 抑制，以及 batch threshold 小幅不过线。

### v60 individual context ranking

新增脚本：

```text
script =
  BPC_future/scripts/audit_gat_batch_impact_individual_context_ranking.py

test =
  BPC_future/tests/test_gat_batch_impact_individual_context_ranking.py
```

运行聚焦 v53 individual rows：

```text
summary =
  BPC_future/results/gat_batch_impact_individual_context_ranking_v60_v55_individual_followup_20260616/summary.json

report =
  BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v60_v55_individual_followup_individual_context_ranking_zh.md

focus_row_index_min = 383
focused_row_count = 9
context_count = 3
contexts_with_positive_and_negative = 2
positive_row_count = 2
negative_row_count = 7
pair_count = 4
raw_pair_pass_rate = 0.25
admission_pair_pass_rate = 0.5
delay_risk_pair_pass_rate = 0.5
strict_pair_pass_rate = 0.25
primary = candidate_head_context_ranking_failure
```

逐 context 结果：

| context | positive | negative | pair count | raw pass | admission pass | strict pass | action |
|---|---:|---:|---:|---:|---:|---:|---|
| `ac056820151e9ad7` | 0 | 3 | 0 | n/a | n/a | n/a | keep as retry hard-negative / collect positive counterpart |
| `79fde658840fe2b8` | 1 | 2 | 2 | 0/2 | 1/2 | 0/2 | candidate-head ranking failure |
| `ac15bc4e7e3d6fff` | 1 | 2 | 2 | 1/2 | 1/2 | 1/2 | candidate-head ranking failure |

关键解释：v59 从全局 missed high-ROI 看像“raw score 接近、risk-adjusted 被压”；但 v60 聚焦 v53 individual rows 后发现，两个有正负对照的 context 中，positive target 的 raw candidate score 并没有稳定排在 hard-negative 前面。也就是说不能只调 delay penalty 或 rescue window，candidate head 的 context-local 表示本身也不可靠。

## 与旧版本的关系

| version | 旧结论 | v57-v60 后的新理解 |
|---|---|---|
| v15/v43 | missed high-ROI 不是阈值差一点，存在 candidate-head/embedding structural gap | v55 的 raw margin 已比 v15 近很多，但 focused individual rows 仍证明同 context raw ranking 没过。 |
| v44/v45/v46 | delay-safe shell 存在但覆盖太窄，coverage 回来后 false-delay 复发 | v57 frontier 仍 0 feasible；v56/v57 互相确认不是 selector 或单一 threshold 问题。 |
| v50 | context-batch negative label 过粗，且即时 objective improvement 会误导 | v53/v60 证明 individual attribution 必须保留；同一个 context 中正负 target 的模型分数仍会错排。 |
| v51/v52 | safe epoch 与 coverage-ready epoch 分离，checkpoint selection 不是主 blocker | v57/v60 进一步说明 blocker 在候选表示和 context-local ranking，不在选哪个 epoch。 |
| v54-v56 | v53 rows 提高 pairwise 密度，但没有改变 coverage/safety tradeoff | v60 解释了原因：新增正负对照进入数据后，模型仍没学会在这些 context 内排序。 |

## 新判断

### 1. 不能把下一步简化为调 delay penalty

v58/v59 显示 `candidate_delay_risk_above_threshold` 和 `risk_adjusted_suppressed_miss_count` 很高，表面上像 delay-risk 过强。但 v60 显示 raw candidate head 在 v53 focused pairs 上也只有 `1/4` pair 排对。因此只降低 delay penalty 可能把 false-delay hard-negative 一起放回 HIGH_PRIORITY。

### 2. v55 和 v15 的问题形态不同

v15 是 missed high-ROI deep score gap / embedding mixture 更重；v55 已经把 raw candidate score 推到 near-threshold，但 risk-adjusted admission 和 batch score 没能形成高覆盖安全区。进步存在，但还没有转化成 Stage 4 readiness。

### 3. `ac056` 应继续作为 hard-negative source，但需要正对照

v53 focused rows 中 `ac056` 只有 3 个 negative retry targets，没有 positive counterpart。它能监督 delay queue，但不能单独训练“正 > 负”的排序。后续若继续围绕 `ac056`，必须找同 context positive counterpart，否则只会继续收窄安全壳。

### 4. `79fde` / `ac15` 是直接的模型结构反例

这两个 context 都有 positive 和 hard-negative individual targets；v60 显示 positive target 没有稳定排在 negative target 前。它们适合作为 candidate-head context-local representation 的最小回归用例。

## 下一步

1. 不把 v55/v57 推进 Stage 4；`stage4_candidate_ready=false` 仍成立。
2. 不直接降低 delay penalty；先修 candidate head 的 context-local 排序。
3. 建一个 v61 结构/特征审计：检查当前 candidate features 是否包含足够的 order、arc-option、timing、basis/dual trajectory、target signature 信息；尤其对 `79fde/ac15` 这两组反例。
4. 训练目标上增加 focused regression check：`79fde positive > 79fde hard-negative`、`ac15 positive > ac15 hard-negative` 必须成为 checkpoint diagnostic gate，而不是只看全局 validation loss。
5. 数据采集上补 random-wave same-context 正负对照；v58/v59 仍显示 random-wave 6/6 missed，并且 3 个 random-wave contexts 缺 same-context contrast。

## Exactness Boundary

```text
v57_frontier_runs_bpc_or_pricing = false
v58_opportunity_runs_bpc_or_pricing = false
v59_score_margin_runs_bpc_or_pricing = false
v60_individual_ranking_runs_bpc_or_pricing = false
production_ready = false
default_enabled = false
stage4_candidate_ready = false
certificate_ready = false
official_bound_effect = false
selector_is_pricing_oracle = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

最终证明仍必须由当前 branch/cut/dual 下 exact pricing exhaustive no-negative closure 产生；本轮所有产物只用于 Stage 3 diagnostic 和下一轮模型/数据修复。
