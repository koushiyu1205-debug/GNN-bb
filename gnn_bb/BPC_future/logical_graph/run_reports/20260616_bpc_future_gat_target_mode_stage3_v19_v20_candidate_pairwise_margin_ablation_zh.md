# GAT Target Mode Stage 3 v19/v20 Candidate Pairwise Margin Ablation 报告

日期：2026-06-16

## 目的

本轮不是上线实验，也不运行 BPC / pricing / RMP。目标是验证 v18 的核心 blocker：
batch score 经常足够，但 candidate head 对真正 high-ROI 的候选列打不到
HIGH_PRIORITY 阈值，导致 missed high-ROI；同时 greedy-anchor / random-wave
低 ROI 接收又稀释整体 ROI。

因此 v19/v20 在训练侧加入同 context 的 candidate-level pairwise margin：
高 ROI 样本用 labeled-safe candidate 的最大 admission logit，低 ROI / bad 样本用
所有 candidate 的最大 admission logit，要求前者至少高出 margin。该约束只影响
offline checkpoint 训练，不改变 exact pricing，也不提供 certificate。

## 代码变更

```text
script =
  BPC_future/scripts/train_gat_batch_impact.py
test =
  BPC_future/tests/test_gat_batch_impact_training.py

new_cli =
  --pairwise-candidate-ranking-loss-multiplier

new_training_contract_field =
  pairwise_candidate_ranking_loss_multiplier

new_internal_logic =
  _candidate_acceptance_logit(...)
  _pairwise_loss_enabled(...)
  _pairwise_ranking_loss(...) now combines batch-score margin and
    candidate-acceptance margin
```

测试新增覆盖点：同 context 下，better/high-ROI 样本只用 labeled-safe candidate
的最大 logit；worse/low-ROI 样本用任意 candidate 的最大 logit，因此如果 bad row
有更高 admission logit，pairwise loss 必须为正。

## v18 基线

```text
dataset =
  BPC_future/data/gat_batch_impact/v18_mixed_v17_plus_train_split_next3_hard_negative_20260616

training selected:
  accepted_batch_count = 39
  accepted_batch_roi = 4.3838918669516245
  accepted_batch_roi_ci_low = 1.0535803658133176
  safe_precision_ci_low = 0.910330146399761
  false_safe_rate_union = 0.00847457627118644
  checkpoint_gate_pass = false

kNN/OOD global:
  accepted_batch_count = 38
  accepted_batch_roi = 3.4119277786693076
  accepted_batch_roi_ci_low = 0.607449381373161
  safe_precision_ci_low = 0.90818706741616
  false_safe_rate_union = 0.0
  validation_candidate_ready = false

opportunity:
  accepted = 39
  high_roi_opportunities = 30
  accepted_high_roi_opportunities = 12
  missed_high_roi_opportunities = 18
  accepted_low_roi_or_bad = 27
  missed_reason_counts = {'no_candidate_above_threshold': 18}

score margins:
  candidate_margin_bucket_counts =
    {'deep_candidate_score_gap': 9,
     'moderate_candidate_score_gap': 8,
     'near_candidate_threshold': 1}
  missed_candidate_score_margin_mean = -0.231501843366358
  missed_candidate_score_margin_min = -0.6960250288248062
  missed_without_same_context_contrast_count = 6
```

v18 的问题不是安全门完全不够，而是 ROI 被 low-ROI / bad admission 稀释：
accepted count 和 selected safe CI 已接近 Stage 3 gate，但 `accepted_low_roi_or_bad`
高达 27。

## v19: candidate pairwise multiplier = 0.75

```text
checkpoint =
  BPC_future/data/gat_batch_impact/v19_candidate_pairwise_margin_v18_data_20260616/gat_batch_impact.pt
metrics =
  BPC_future/results/gat_batch_impact_training_v19_candidate_pairwise_margin_20260616/metrics.json

training selected:
  accepted_batch_count = 18
  accepted_batch_roi = 9.241468070281876
  accepted_batch_roi_ci_low = 2.623136213513141
  safe_precision_ci_low = 0.8241154494176252
  false_safe_rate_union = 0.00847457627118644
  checkpoint_gate_pass = false
  rejected_checkpoint_reasons =
    ['knn_ood_audit_missing', 'safe_precision_ci_low_below_threshold_or_not_measurable']

kNN/OOD global:
  accepted_batch_count = 12
  accepted_batch_roi = 0.7894691005349159
  accepted_batch_roi_ci_low = 0.4312704809602725
  safe_precision_ci_low = 0.7574992425007574
  false_safe_rate_union = 0.0
  validation_candidate_ready = false

opportunity:
  accepted = 20
  high_roi_opportunities = 30
  accepted_high_roi_opportunities = 11
  missed_high_roi_opportunities = 19
  accepted_low_roi_or_bad = 9
  missed_reason_counts =
    {'batch_score_below_family_threshold': 11,
     'no_candidate_above_threshold': 19}

score margins:
  candidate_margin_bucket_counts =
    {'deep_candidate_score_gap': 4,
     'moderate_candidate_score_gap': 10,
     'near_candidate_threshold': 5}
  missed_candidate_score_margin_mean = -0.1428575433398548
  missed_candidate_score_margin_min = -0.6304099783301353
  missed_without_same_context_contrast_count = 7
```

v19 的方向是有效的：low-ROI / bad accepted 从 27 降到 9，deep candidate gap
从 9 降到 4，selected ROI 从 4.38 提升到 9.24。但它把 accepted count 压到
18，导致 safe precision CI 只有 0.824，达不到 Stage 3/4 的样本置信要求。
kNN/OOD 后只剩 12 个 accepted，ROI CI 和 safety CI 都失败。

## v20: candidate pairwise multiplier = 0.25

```text
checkpoint =
  BPC_future/data/gat_batch_impact/v20_candidate_pairwise_margin025_v18_data_20260616/gat_batch_impact.pt
metrics =
  BPC_future/results/gat_batch_impact_training_v20_candidate_pairwise_margin025_20260616/metrics.json

training selected:
  accepted_batch_count = 10
  accepted_batch_roi = 10.493025609850884
  accepted_batch_roi_ci_low = 0.8042559559050559
  safe_precision_ci_low = 0.7224598312333834
  false_safe_rate_union = 0.0
  checkpoint_gate_pass = false
  rejected_checkpoint_reasons =
    ['knn_ood_audit_missing', 'safe_precision_ci_low_below_threshold_or_not_measurable']

kNN/OOD global:
  accepted_batch_count = 10
  accepted_batch_roi = 10.493025609850884
  accepted_batch_roi_ci_low = 0.8042559559050559
  safe_precision_ci_low = 0.7224598312333834
  false_safe_rate_union = 0.0
  validation_candidate_ready = false

opportunity:
  accepted = 10
  high_roi_opportunities = 30
  accepted_high_roi_opportunities = 8
  missed_high_roi_opportunities = 22
  accepted_low_roi_or_bad = 2
  missed_reason_counts =
    {'batch_score_below_family_threshold': 7,
     'no_candidate_above_threshold': 22}

score margins:
  candidate_margin_bucket_counts =
    {'deep_candidate_score_gap': 5,
     'moderate_candidate_score_gap': 11,
     'near_candidate_threshold': 6}
  missed_candidate_score_margin_mean = -0.12939075990156693
  missed_candidate_score_margin_min = -0.47410809993743896
  missed_without_same_context_contrast_count = 7
```

v20 更干净但更窄：low/bad accepted 降到 2，但 accepted high-ROI 也降到 8，
missed high-ROI 上升到 22。降低 multiplier 没有恢复 coverage，说明当前 blocker
不是单一 loss 权重问题。

## 结论

1. candidate-level pairwise margin 是正确方向，但当前数据覆盖不足，不能作为
   production checkpoint。v19/v20 都没有通过 Stage 3/4 gate。
2. v19/v20 证明了 candidate head 可以被拉开一部分：deep gap 明显减少，低 ROI
   误收下降；但同时 admission 过保守，accepted all-success 样本数低于
   Stage 3 所需的 35，CI 不可用。
3. 下一步不应继续盲目调 threshold 或 multiplier。需要补 reachability-valid 的
   same-context positive/negative contrast，尤其：
   `sector-wave` task20 `9fadf4f7b39742a2`、
   `sector-wave` task20 `b6d808ebac2a6dd8`、
   以及修复 reachability 后再看 `random-wave` task50
   `a67f331bdb819d7d` / `e6b17bbf825984ae`。
4. 需要把训练目标从“提高 candidate margin”推进到“覆盖约束下的 ROI 排序”：
   保持 `accepted_batch_count >= 35` / safe precision CI，同时压低 low-ROI admission。
   可选方向包括 coverage-aware selector loss、family-local calibration、context-local
   margin 与 batch-candidate interaction，但 safety gate 不能放松。
5. exact 证明边界不变：GAT / CBF / kNN / OOD 只能排序和调度候选列，最终 certificate
   必须由当前 branch/cut/dual 下的 exact pricing full closure 重新确认。

## 验证

```text
unit_test =
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
    -m unittest \
      BPC_future.tests.test_gat_batch_impact_training \
      BPC_future.tests.test_gat_batch_impact_score_margins

result =
  Ran 14 tests in 0.084s
  OK

diff_check =
  git diff --check -- \
    BPC_future/scripts/train_gat_batch_impact.py \
    BPC_future/tests/test_gat_batch_impact_training.py \
    BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md \
    BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v19_v20_candidate_pairwise_margin_ablation_zh.md

diff_check_result =
  clean

format_note =
  these BPC_future paths are currently untracked in the /home/kai/work git index,
  so git diff --check is not sufficient by itself

trailing_whitespace_scan =
  rg -n "[ \t]$" \
    BPC_future/scripts/train_gat_batch_impact.py \
    BPC_future/tests/test_gat_batch_impact_training.py \
    BPC_future/docs/gat_bpc_future_target_mode_optimization_plan_zh.md \
    BPC_future/logical_graph/run_reports/20260616_bpc_future_gat_target_mode_stage3_v19_v20_candidate_pairwise_margin_ablation_zh.md

trailing_whitespace_scan_result =
  no matches
```
