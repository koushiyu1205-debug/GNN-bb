# 2026-06-16 BPC_future GAT Target Mode Stage 3 v27 Dual-gate 综合报告

日期：2026-06-16

## 结论

v27 不是 Stage 4 candidate。它是一次有价值的 Stage 3 诊断推进：

1. offline admission 决策已支持 `high_priority_score >= threshold` 且
   `delay_risk_score <= threshold` 的 dual gate；默认仍不开启，不影响 solver /
   pricing / RMP / certificate。
2. v27 相比 v25 明显压住了拖尾误接收风险，相比 v26 提高了 accepted count、
   validation ROI 和 ROI CI。
3. 但当前 delay-risk head 在 `0.5` gate 下没有实际过滤最优候选：
   `candidate_delay_gate_blocked_count = 0`。也就是说，这轮收益主要来自 checkpoint /
   threshold / context fallback 的变化，不是来自 delay head 已经学会区分拖尾候选。
4. missed high-ROI 不是纯阈值问题，也不是完全结构性不可分：15 个 missed high-ROI
   中 6 个 candidate near-threshold、8 个 moderate gap、1 个 deep gap；4 个 missed
   context 缺 same-context low-ROI / delay contrast。

下一步不应该再做普通全局 threshold / multiplier 扫描。应转向：

```text
roi_opportunity_score 高：候选列 / 候选批次有望改善 RMP trajectory
delay_risk_score       低：不会明显引入 low-ROI / tail retry 风险

HIGH_PRIORITY iff:
  roi_opportunity_score passes
  and calibrated delay_risk_score stays below risk gate
```

并补充 missed high-ROI context 的 same-context 正负对，让模型在同一 RMP / dual /
branch context 内学习“哪个候选该先入、哪个候选该 delay”。

## Exact-safe 边界

本轮只改 offline learning / audit / unit test 侧，不改 solver、pricing、RMP、final
judge 或 certificate 逻辑。

保持以下边界：

- GAT / CBF / kNN / OOD 只能做 discovery ordering 和 admission scheduling；
- GAT 不能 permanent discard negative columns；
- GAT 不能生成 official lower bound、certificate 或 no-negative reduced-cost 结论；
- 最终证明仍必须由当前 branch / cut / true RMP dual 下的 exhaustive exact pricing
  full closure 给出：整个配置宇宙不存在 negative reduced-cost journey。

## 本轮实现

新增 default-off offline candidate delay gate：

```text
--candidate-delay-gate-enabled
--candidate-delay-risk-threshold
```

接入范围：

- training checkpoint contract / report；
- threshold search / deployment metrics；
- family holdout 和 context/family delay fallback；
- kNN/OOD audit；
- opportunity mining；
- score-margin diagnostic 的输入链路；
- unit tests。

当前语义是：

```text
candidate predicted HIGH_PRIORITY iff
  high_priority_probability >= candidate_threshold
  and, if enabled, delay_risk_probability <= candidate_delay_risk_threshold
```

所有新增路径仍是 diagnostic-only；checkpoint `production_ready=false`。

## v25 / v26 / v27 对比

| 版本 | frontier accepted | frontier ROI | frontier ROI CI low | safe precision CI low | false-safe union | kNN accepted | kNN ROI CI low | high-ROI capture | accepted low/bad | missed high-ROI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v25 | 58 | 5.2553 | 2.6892 | 0.9379 | 0.7034 | 22 | -0.3231 | 24 / 30 | 34 | 6 |
| v26 | 21 | 7.9698 | 2.1237 | 0.8454 | 0.0085 | 13 | -1.0509 | 10 / 30 | 13 | 20 |
| v27 | 24 | 9.5149 | 4.0990 | 0.8620 | 0.0085 | 16 | -0.4091 | 15 / 30 | 10 | 15 |

读法：

- v25 证明 high-ROI 机会可被拉回来，但代价是 low-ROI / delay admission 爆炸；
- v26 证明安全性可恢复，但 high-ROI capture 掉太多；
- v27 在二者之间更均衡：ROI CI 最强，accepted low/bad 更低，但 safe precision
  CI 仍低于 0.9，kNN/OOD ROI CI 仍为负，所以不能进入 Stage 4。

## v27 关键审计结果

training / frontier 最优候选：

```text
accepted_batch_count = 24
accepted_batch_roi = 9.514876774822673
accepted_batch_roi_ci_low = 4.099000909759836
high_priority_precision = 0.9983221476510067
high_priority_precision_ci_low = 0.990557664961028
safe_precision = 1.0
safe_precision_ci_low = 0.8620194241710247
false_high_priority_on_delay = 0.00847457627118644
false_safe_rate_union = 0.00847457627118644
candidate_delay_gate_enabled = true
candidate_delay_risk_threshold = 0.5
candidate_delay_gate_blocked_count = 0
threshold_mode = context_delay_fallback
threshold_local_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
```

kNN/OOD：

```text
accepted_batch_count = 16
accepted_batch_roi = 3.0489296121522784
accepted_batch_roi_ci_low = -0.4091389147994051
safe_precision = 1.0
safe_precision_ci_low = 0.8063865817272801
false_high_priority_on_delay = 0.0
false_safe_rate_union = 0.0
production_ready = false
production_block_reasons =
  validation_safe_precision_ci_low_below_min
  validation_accepted_batch_roi_ci_low_below_min
  validation_candidate_not_ready
```

opportunity mining：

```text
high_roi_opportunities = 30
accepted_high_roi_opportunities = 15
missed_high_roi_opportunities = 15
accepted_low_roi_or_bad = 10
missed_reason_counts =
  batch_score_below_family_threshold: 15
  no_candidate_above_threshold: 15
```

score margin：

```text
candidate_margin_bucket_counts =
  near_candidate_threshold: 6
  moderate_candidate_score_gap: 8
  deep_candidate_score_gap: 1
missed_batch_score_margin_median = -0.017939746379852295
missed_candidate_score_margin_median = -0.10494878888130188
missed_without_same_context_contrast_count = 4
contexts_needing_contrast =
  9fadf4f7b39742a2 sector-wave task20
  a67f331bdb819d7d random-wave task50
  e6b17bbf825984ae random-wave task50
```

## 解释

v27 的核心信息不是“delay gate 成功”，而是“decision plumbing 准备好了，但
delay-risk signal 还没有校准到可用”。

如果 delay-risk head 已经有效，frontier 最优候选应该出现非零
`candidate_delay_gate_blocked_count`，并且 false-safe / accepted low-bad 会随之下降。
实际结果是 blocked count 为 0，说明 0.5 风险阈值对当前 score 分布过松，或者
delay-risk head 与 true delay / low-ROI admission 的排序关系还不够强。

missed high-ROI 的 margin 分布也说明不能简单放宽阈值：

- 6 个 near-threshold 可以通过校准、局部阈值或 margin loss 拉回；
- 8 个 moderate gap 需要更强的同上下文候选排序信号；
- 1 个 deep gap 说明存在模型/特征或标签覆盖问题；
- 4 个 missed context 没有 same-context contrast，继续训练会缺反例。

## 下一步

建议做 v28，而不是把 v27 直接送 Stage 4：

1. 加 delay-risk calibration / contrast：让 delay-risk head 明确学习 true delay、
   low-ROI accepted、tail retry risk，而不只是旁路输出。
2. 增加 `roi_opportunity_score - delay_risk_score` 或等价 combined admission logit，
   训练目标直接对齐 HIGH_PRIORITY admission。
3. 针对 margin 报告列出的三个 context 补 same-context positive/negative pairs，
   优先补 random-wave task50 与 sector-wave task20。
4. 可做小范围 delay threshold diagnostic，例如 `0.1 / 0.2 / 0.3`，但只作为校准诊断，
   不作为主线盲扫。
5. 继续保持 Stage 3 hard gate：precision / precision CI / false-safe / ROI /
   ROI CI / family-context holdout / kNN-OOD 全部先于 loss、F1、recall。

## 产物

- training:
  `BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v27_dual_gate_family_task_balanced_training_zh.md`
- threshold frontier:
  `BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v27_dual_gate_family_task_balanced_threshold_frontier_zh.md`
- kNN/OOD:
  `BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v27_dual_gate_family_task_balanced_knn_ood_global_zh.md`
- opportunity mining:
  `BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v27_dual_gate_family_task_balanced_opportunity_mining_zh.md`
- score margin:
  `BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v27_dual_gate_family_task_balanced_score_margin_audit_zh.md`
