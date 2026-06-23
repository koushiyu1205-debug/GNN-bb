# BPC_future GAT target-mode Stage 3 v134 审计综合报告

日期：2026-06-23

## 结论

v134 是负结果。它把 v133 的 train-only delay-risk 设置继续推进，并额外加入
context-pair comparator、focused context comparator loss、以及 train-only raw-action
boost rows；本地 deployment threshold gate 仍然可以通过，ROI 和 precision 也比
v133 selected checkpoint 略好，但 focused pair gate 退回到 `74/78`，低于必须
`78/78` 的硬线，因此不进入 kNN/OOD，也不能作为 Stage 4 candidate。

本次运行不调用 BPC / pricing / RMP，不生成 certificate 或 official lower bound。
GAT 仍只作为 admission scheduling 的离线诊断候选。

## 运行对象

- dataset:
  `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622`
- checkpoint:
  `BPC_future/results/gat_batch_impact_training_v134_raw_action_context_pair_seed13_20260623/model.pt`
- metrics:
  `BPC_future/results/gat_batch_impact_training_v134_raw_action_context_pair_seed13_20260623/metrics.json`
- training report:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v134_raw_action_context_pair_seed13_zh.md`
- focused failure audit:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v134_focused_pair_failure_audit_zh.md`

## 本轮改动意图

v133 的主要 blocker 是同上下文 action-consequence / raw candidate-head 排序：

- selected epoch 2 的 local gate 已通过；
- focused raw / strict 只有 `75/78`；
- admission / delay-risk 提升到 `77/78`，但仍未到硬线；
- validation rows `183/844/845` 不能泄漏进训练。

v134 因此只加入 train split 可用的 raw-action boost rows：

```text
[176, 398, 779, 780, 781, 782, 783, 846, 847]
```

其中 `398/779` 是 v133 里唯一可用于 train-only replay 的 raw-head 失败对；validation
rows `183/844/845` 继续排除。

## 关键指标

checkpoint selection 仍是：

```text
deployment_gate_first_then_roi_ci_baseline_utility_loss
```

selected epoch = `5`；best validation-loss epoch = `1`。选择 epoch 5 的原因不是
loss 最低，而是它在通过本地 deployment gate 的候选中 ROI-CI / baseline utility
排序最好。

epoch 5 validation deployment metrics：

- `threshold_local_gate_pass = true`
- `accepted_batch_count = 35`
- `accepted_batch_rate = 0.11986301369863013`
- `accepted_batch_roi = 19.517712778460034`
- `accepted_batch_roi_ci_low = 10.438985380200847`
- `high_priority_precision = 0.9965277777777778`
- `high_priority_precision_ci_low = 0.9874290122708577`
- `safe_precision = 1.0`
- `safe_precision_ci_low = 0.9010957324106112`
- `false_high_priority_on_delay = 0.007220216606498195`
- `false_safe_rate_union = 0.007220216606498195`

focused pair gate：

- `pair_count = 78`
- `raw_pair_pass_rate = 0.9487179487179487`，即 `74/78`
- `admission_pair_pass_rate = 0.9487179487179487`，即 `74/78`
- `delay_risk_pair_pass_rate = 0.9487179487179487`，即 `74/78`
- `strict_pair_pass_rate = 0.9487179487179487`，即 `74/78`
- blocking primary = `candidate_head_context_ranking_failure`

Stage 4 blockers：

- `raw_pair_pass_rate_below_threshold`
- `admission_pair_pass_rate_below_threshold`
- `delay_risk_pair_pass_rate_below_threshold`
- `strict_pair_pass_rate_below_threshold`
- `knn_ood_audit_missing`
- `knn_ood_holdout_audit_not_run`
- `online_shadow_and_opt_in_ab_not_run`

## Epoch 轨迹

| epoch | local gate | accepted | ROI | ROI CI low | false-delay | safe CI low | raw | admission | delay-risk | strict |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | true | 35 | 17.505 | 8.502 | 0.0072 | 0.901 | 59/78 | 64/78 | 66/78 | 59/78 |
| 2 | true | 35 | 18.528 | 9.388 | 0.0036 | 0.901 | 71/78 | 71/78 | 71/78 | 71/78 |
| 3 | true | 36 | 19.149 | 10.299 | 0.0072 | 0.904 | 71/78 | 72/78 | 72/78 | 71/78 |
| 4 | false | 9 | 14.004 | 8.753 | 0.0000 | 0.701 | 70/78 | 71/78 | 71/78 | 70/78 |
| 5 | true | 35 | 19.518 | 10.439 | 0.0072 | 0.901 | 74/78 | 74/78 | 74/78 | 74/78 |

这说明 v134 的 local ROI/precision frontier 并不差，但 focused action-consequence
排序没有改善到可用水平。

## 与 v133 对比

| run | selected epoch | local gate | accepted | ROI | ROI CI low | false-delay | focused raw | focused admission | focused delay-risk | focused strict |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v133 | 2 | true | 36 | 18.801 | 9.879 | 0.0072 | 75/78 | 77/78 | 77/78 | 75/78 |
| v134 | 5 | true | 35 | 19.518 | 10.439 | 0.0072 | 74/78 | 74/78 | 74/78 | 74/78 |

v134 的 ROI / ROI-CI 比 v133 略高，但 focused gate 全面变差，尤其 admission /
delay-risk 从 `77/78` 退到 `74/78`。因此 v134 不能替代 v133，也不值得进入
kNN/OOD。

## Focused Failure Anatomy

v134 focused failure audit：

```text
pair_count = 78
failed_pair_count = 4
near_margin_failed_pair_count = 0
deep_or_mixed_failed_pair_count = 4
deep_structural_score_gap = 3
mixed_margin_failure = 1
recommended_next_step = add_or_repair_context_action_consequence_features_before_more_sweeps
```

失败 pair：

| context | family | task | positive row | negative row | positive ROI | raw margin | admission margin | delay-risk margin | diagnosis |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `apollo15_20km_greedy-anchor_randomtw_tasks020_04_seed61308|b36178f6655c5f75` | greedy-anchor | 20 | 813 | 815 | 1.321 | -0.0975 | -0.0488 | -0.0306 | deep structural |
| `apollo15_20km_random-wave_randomtw_tasks020_08_seed61715|62c86745ed2b3aaa` | random-wave | 20 | 768 | 767 | 4.427 | -0.0067 | -0.0001 | -0.0370 | mixed margin |
| `apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b` | random-wave | 30 | 183 | 845 | 1.106 | -0.0619 | -0.0929 | -0.0985 | deep structural |
| `apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b` | random-wave | 30 | 844 | 845 | 53.718 | -0.0484 | -0.0771 | -0.0376 | deep structural |

其中 `183/844/845` 仍属于 validation instance，不能直接加入 train-only replay。
`813/815` 和 `768/767` 虽是新增失败，但失败形态显示已经不是单纯继续放大
focused loss multiplier 就能稳妥解决的问题。

## 补充结构审计

本轮追加三项离线审计，均不运行 BPC / pricing / RMP：

- top-context feature contrast：
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v134_top_context_feature_contrast_zh.md`
- context-pair comparator audit：
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v134_context_pair_comparator_audit_zh.md`
- unresolved label/action audit：
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v134_unresolved_context_label_action_audit_zh.md`

top-context feature contrast 结论：

```text
primary = visible_inputs_differ_but_model_still_misranks
failed_pair_count = 4
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
failed_context_feature_drift_pair_count = 0
deep_failed_pair_count = 3
mean_failed_candidate_feature_l1 = 452.67460289508654
recommended_next_step = tighten_context_local_pairwise_ranking_head
```

这说明 v119 当前 tensor 已经有 candidate path token、trace scalar、slack scalar、
per-candidate branch/cut interaction 等字段。失败 pair 的模型输入不是完全相同，也
不是 context feature drift；当前更像是 head / ranking 结构没有把这些可见差异转成
正确的 context-local ordering。

context-pair comparator audit 结论：

```text
existing_strict_pair_pass = 74/78
comparator_pair_pass = 73/78
comparator_repaired_existing_failure_count = 0
comparator_unresolved_existing_failure_count = 4
comparator_conflicts_existing_pass_count = 1
primary = comparator_does_not_repair_focused_failures
```

因此不能把当前 comparator head 直接融合成 admission score；它既没有修复 v134 的
4 个失败 pair，还引入 1 个 existing-pass conflict。

unresolved label/action audit 结论：

```text
primary = no_unresolved_or_conflict_pairs_selected
selected_pair_count = 0
recommended_next_step = no_action_from_this_audit
```

这次没有新的标签 provenance 或 action-field 冲突证据；主要 blocker 仍是模型排序。

## 为什么不跑 kNN/OOD

kNN/OOD 是进入 Stage 4 前的安全壳审计，不是修复 focused pair gate 的工具。
v134 的 selected checkpoint 已经被 focused gate 拦住：

```text
raw/admission/delay-risk/strict = 74/78
required = 78/78
```

即使 kNN/OOD 通过，也无法覆盖 focused gate 失败。因此本轮跳过 kNN/OOD，避免在
已知不可成为 Stage 4 candidate 的 checkpoint 上消耗时间。

## 下一步

v134 证明了“在 v133 上叠加 context-pair comparator + train-only raw-action boost”
不足以解决问题，并且会损伤 admission / delay-risk focused ordering。下一步不应继续
盲目增加 multiplier，也不应放松 focused gate。

更合理的方向是：

1. 优先做 context-local pairwise ranking head / delta head，而不是继续盲目加
   multiplier；当前输入张量有可见差异，但普通 raw/admission heads 没学到正确排序；
2. 必要时补充更直接的 model-visible action-consequence 表示，尤其是同一 context 下
   batch action 对后续 workload / active support / replacement 的可见差异；
3. 对 validation 失败 context 做无泄漏的同族同尺度训练 analog 挖掘，而不是把
   `183/844/845` 这类 validation rows 直接训练；
4. 分离 raw candidate head 与 admission/delay-risk head 的梯度冲突，必要时做
   head-specific pairwise comparator 或 per-context delta head；
5. 保持 Stage 3 gate 不变：focused strict 未到 `78/78` 前，不跑 kNN/OOD，不进入
   Stage 4 shadow / opt-in。

## 验证

已完成：

- v134 GAT training 正常结束，`nonfinite_skipped_update_rate = 0.0`；
- v134 focused failure audit 正常结束，`all_checks_pass = true`；
- v134 top-context feature contrast 正常结束，`all_checks_pass = true`；
- v134 context-pair comparator audit 正常结束，`all_checks_pass = true`；
- v134 unresolved label/action audit 正常结束，`all_checks_pass = true`；
- 本轮不运行 BPC / pricing / RMP；
- 本轮不产生 certificate、official bound 或 production-ready artifact。
