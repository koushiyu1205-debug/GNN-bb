# BPC_future GAT target-mode Stage 3 v133 审计综合报告

日期：2026-06-23

## 结论

v133 是一次负结果，但方向有信息量：在严格 train-only focused 训练约束下，增强
focused delay-risk loss 后，本地 deployment threshold gate 已经通过；但是 focused
pair gate 仍未达到 78/78，因此不进入 kNN/OOD，也不能作为 Stage 4 candidate。

本次运行不调用 BPC / pricing / RMP，不生成 certificate 或 official lower bound。
GAT 仍只作为 admission scheduling 诊断候选。

## 运行对象

- dataset:
  `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622`
- checkpoint:
  `BPC_future/results/gat_batch_impact_training_v133_focused_delay_risk_trainonly_seed13_20260623/model.pt`
- metrics:
  `BPC_future/results/gat_batch_impact_training_v133_focused_delay_risk_trainonly_seed13_20260623/metrics.json`
- machine report:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v133_focused_delay_risk_trainonly_seed13_zh.md`

## 关键指标

selected epoch = 2；best validation-loss epoch = 5。选择 epoch 2 的原因不是
loss 最低，而是 `deployment_gate_first_then_roi_ci_baseline_utility_loss`：先看本地
deployment gate，再按 ROI / CI / utility 排序。

epoch 2 validation deployment metrics：

- `threshold_local_gate_pass = true`
- `accepted_batch_count = 36`
- `accepted_batch_roi = 18.801208721732515`
- `accepted_batch_roi_ci_low = 9.878776762449476`
- `high_priority_precision = 0.9967637540453075`
- `high_priority_precision_ci_low = 0.9882776405504577`
- `safe_precision = 1.0`
- `safe_precision_ci_low = 0.9035781695514236`
- `false_high_priority_on_delay = 0.007220216606498195`
- `false_safe_rate_union = 0.007220216606498195`

focused pair gate：

- `pair_count = 78`
- `raw_pair_pass_rate = 0.9615384615384616`，即 75/78
- `admission_pair_pass_rate = 0.9871794871794872`，即 77/78
- `delay_risk_pair_pass_rate = 0.9871794871794872`，即 77/78
- `strict_pair_pass_rate = 0.9615384615384616`，即 75/78
- blocking primary = `candidate_head_context_ranking_failure`

Stage 4 blockers：

- `raw_pair_pass_rate_below_threshold`
- `admission_pair_pass_rate_below_threshold`
- `delay_risk_pair_pass_rate_below_threshold`
- `strict_pair_pass_rate_below_threshold`
- `knn_ood_audit_missing`
- `knn_ood_holdout_audit_not_run`
- `online_shadow_and_opt_in_ab_not_run`

## 与近邻实验对比

同口径 focused strict：

- v125 selected epoch 2：74/78，validation ROI 19.450745，false-delay 0.007220
- v128 train-only focused early stop：最好 71/78，后续 false-delay 越界
- v130 context comparator cached early stop：最好 74/78，ROI/CI 未超过 v125
- v133 focused delay-risk train-only：最好 76/78 出现在 epoch 3/5，但 selected
  epoch 2 为 75/78；admission/delay-risk 分项提升到 77/78

因此，v133 相比 v125 在 focused admission / delay-risk ordering 上有局部改善，
但没有解决 raw/candidate-head 排序错误；同时 selected epoch 的 ROI 略低于 v125。

## 为什么不跑 kNN/OOD

kNN/OOD 是 Stage 3 进入 Stage 4 前的安全壳审计，不是用来修复 focused gate 的。
当前 focused strict 仍低于 78/78，且 raw ranking 只有 75/78。即使 kNN/OOD 通过，
仍会被 focused pair gate 拦住；因此这次跳过 kNN/OOD，避免消耗时间在已知不可通过的
candidate 上。

## 下一步建议

当前 blocker 不再是普通本地 threshold gate，而是同上下文 action-consequence 可见性：
增强 delay-risk loss 可以改善 admission/delay-risk 分项，但 raw candidate head 仍会把
少数同上下文正负样本排反。下一步应优先做 model-visible action-consequence / context-pair
contrast，而不是继续单纯放大 delay-risk loss 或放松 gate。
