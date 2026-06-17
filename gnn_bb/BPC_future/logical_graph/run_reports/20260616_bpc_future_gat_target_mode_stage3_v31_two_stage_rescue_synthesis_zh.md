# BPC Future GAT Target Mode Stage 3 v31 Two-Stage Rescue 综合报告

日期：2026-06-16

## 结论

v31 只做 audit-only admission 规则验证：在现有 risk-adjusted score 外，加一个 `risk_adjusted_rescue_window`，允许 raw HIGH_PRIORITY 分数足够高、delay-risk 低于宽松上限的候选，用较弱 delay penalty 重新计算 admission score，并在该窗口内绕过 strict delay gate。

结果说明：two-stage rescue 能捞回一部分被 risk penalty 压低的候选，但直接放宽 window 不是 Stage 4 方案。v28 上提升很有限且仍卡 CI；v29_p075 上 high-ROI capture 几乎满了，但 false delay 风险爆炸。下一步不能继续盲调阈值，应转向“rescue 必须受 CBF/kNN/OOD 或更强 delay-risk 判别约束”。

```text
stage = Stage 3
variant = v31_two_stage_rescue_window
diagnostic_only = true
runs_bpc_or_pricing = false
selector_can_certificate = false
official_bound_effect = false
candidate_admission_score_mode = risk_adjusted_rescue_window
candidate_rescue_raw_score_threshold = 0.30
candidate_rescue_delay_risk_threshold = 0.75
candidate_rescue_delay_score_penalty = 0.25
```

## 实现范围

- `train_gat_batch_impact.py` 增加 `risk_adjusted_rescue_window`、rescue raw/delay/penalty 配置、eligible/promoted 计数；默认仍是原 `high_priority`，不改变旧训练/审计行为。
- `audit_gat_batch_impact_threshold_frontier.py` 增加 admission 规则 override，可以复用同一 checkpoint 做 audit-only 对照，不混入重新训练影响。
- `audit_gat_batch_impact_opportunity_mining.py` 和 `audit_gat_batch_impact_knn_ood.py` 同步本地 scoring 口径。
- 修正 opportunity mining：现在会应用 frontier 选出的 family/context delay fallback，避免 opportunity accepted 数和 frontier accepted 数不一致。

## v28 对照

checkpoint：`v28_risk_adjusted_delay_calibrated_v23_data_20260616`

```text
frontier_accepted_batch_count = 25
frontier_accepted_batch_roi = 9.159044431447983
frontier_safe_precision = 1.0
frontier_safe_precision_ci_low = 0.8668035060468212
frontier_high_priority_precision = 0.997867803837953
frontier_false_high_priority_on_delay = 0.00847457627118644
frontier_candidate_rescue_window_promoted_count = 469
frontier_reject_reasons = ['safe_precision_ci_low_below_threshold_or_not_measurable']
opportunity_high_roi = 30
opportunity_accepted_high_roi = 15
opportunity_missed_high_roi = 15
opportunity_accepted_low_roi_or_bad = 10
```

解读：v28 rescue 比原 v28 selected 的 accepted=22 多接收 3 个 batch，但 safe CI low 仍只有 0.867，达不到 0.9。top missed high-ROI 里有多个候选只差极小 margin，例如 `-4.3e-05`、`-0.00073`、`-0.00131`，说明一部分 missed 是 admission margin/校准问题，不是 batch score 问题；但仍有 raw 分明显不足的 missed，不能靠 rescue window 全部解决。

## v29_p075 对照

checkpoint：`v29_p075_n200_risk_penalty_matrix_v23_data_20260616`

```text
frontier_accepted_batch_count = 62
frontier_accepted_batch_roi = 5.107854291511279
frontier_safe_precision = 1.0
frontier_safe_precision_ci_low = 0.9416539087749994
frontier_high_priority_precision = 0.9485834207764953
frontier_false_high_priority_on_delay = 0.5212765957446809
frontier_candidate_rescue_window_promoted_count = 435
frontier_reject_reasons = ['false_high_priority_on_delay_too_high', 'false_safe_rate_union_too_high']
opportunity_high_roi = 30
opportunity_accepted_high_roi = 29
opportunity_missed_high_roi = 1
opportunity_accepted_low_roi_or_bad = 33
```

解读：v29_p075 证明 rescue window 能把 high-ROI capture 拉到 29/30，但代价是 false_high_priority_on_delay=0.521，远超 Stage 3 safety gate 的 0.01。这个结果支持“risk-suppressed 里面确实有高 ROI”，但也证明不能用简单 window 直接 admission。

## 对 v15 missed high-ROI 的判断

结合 v30 raw-vs-risk 审计：v15 的 missed high-ROI 主要是 raw candidate score gap，不是 risk suppression。v31 rescue window 是针对 v28/v29 这类 risk-adjusted 压制的诊断工具；它不能直接解释或修复 v15 的结构性 raw 分不开问题。v15 下一步应看 candidate raw score 分布、上下文/候选族 embedding 是否把 high-ROI 和低 ROI 混在一起，而不是只调 admission rule。

## 下一步

1. 不把 v31 作为 Stage 4 candidate。它是 audit-only evidence。
2. 对 v28 的 near-miss 样本做 margin-band 分析：只针对 `0 < raw_margin` 且 `adjusted_margin` 接近 0 的候选，训练/校准 delay penalty 或 rescue penalty。
3. 对 v29_p075 的 promoted false-delay 样本做 CBF/kNN/OOD 分层：rescue 必须先过局部邻域安全壳，不能只看 raw/delay 两个标量。
4. v15 继续单独判断 raw 分数差一点还是模型结构分不开；如果 raw margin 大面积为负，优先改候选表示/positive sampling，而不是继续调 admission threshold。

## 验证

```text
python -m py_compile train/frontier/opportunity/knn scripts = pass
python -m unittest gat_batch_impact_training/opportunity_mining/threshold_frontier/knn_ood/score_margins = 36 tests OK
git diff --check = pass
v31_v28_frontier = pass
v31_v28_opportunity_mining = pass
v31_v29_p075_frontier = pass
v31_v29_p075_opportunity_mining = pass
```
