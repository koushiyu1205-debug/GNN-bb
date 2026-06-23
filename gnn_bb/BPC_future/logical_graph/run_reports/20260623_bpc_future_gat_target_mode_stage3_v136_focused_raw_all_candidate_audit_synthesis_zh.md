# BPC_future GAT target-mode Stage 3 v136 审计综合报告

日期：2026-06-23

## 结论

v136 是部分正向但仍失败的结果。它没有沿用 v135 的
`candidate_context_interaction_dim=16`，而是修正 focused training 与 focused gate
之间的一个口径不一致：新增默认关闭的
`focused_pair_raw_all_candidate_loss_multiplier`，直接训练
“正样本 labeled safe candidate 的最大 raw logit 必须高于负样本所有 candidate 的最大
raw logit”。这与 focused gate 的 raw 检查完全一致。

结果上，v136 把 v135 的 focused strict `68/78` 修回到 `75/78`，并修复了 v135 最大的
sector-wave 失败簇；但仍低于 Stage 4 前置 focused gate 的硬线 `78/78`。因此本轮不进入
kNN/OOD，也不能作为 Stage 4 candidate。

本次运行不调用 BPC / pricing / RMP，不生成 certificate 或 official lower bound。
GAT 仍只作为 admission scheduling 的离线诊断候选。

## 运行对象

- dataset:
  `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622`
- checkpoint:
  `BPC_future/results/gat_batch_impact_training_v136_focused_raw_all_candidate_seed13_20260623/model.pt`
- metrics:
  `BPC_future/results/gat_batch_impact_training_v136_focused_raw_all_candidate_seed13_20260623/metrics.json`
- training report:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v136_focused_raw_all_candidate_seed13_zh.md`
- focused failure audit:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v136_focused_pair_failure_audit_zh.md`
- top-context feature contrast:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v136_top_context_feature_contrast_zh.md`

## 本轮代码改动

新增训练开关：

```text
--focused-pair-raw-all-candidate-loss-multiplier
```

语义：

- 仅当 focused training rows 启用时生效；
- 正样本侧只取 `y_candidate_high_priority=1` 的 candidate raw logit max；
- 负样本侧取所有 candidate 的 raw logit max；
- 用同一个 margin ranking loss 训练；
- 默认值为 `0.0`，不改变旧训练命令和旧 checkpoint 兼容性。

这比旧 `focused_pair_candidate_loss_multiplier` 更贴近 focused gate。旧 raw loss 只拿
负样本里 delay-labeled candidate 比较，无法惩罚 hard-negative 行中把 raw max 顶高的其他
candidate。

## 关键指标

checkpoint selection 仍是：

```text
deployment_gate_first_then_roi_ci_baseline_utility_loss
```

selected epoch = `4`；best validation-loss epoch = `4`。

epoch 4 validation deployment metrics：

- `threshold_local_gate_pass = true`
- `accepted_batch_count = 35`
- `accepted_batch_rate = 0.11986301369863013`
- `accepted_batch_roi = 18.603320930685317`
- `accepted_batch_roi_ci_low = 9.467079478881129`
- `high_priority_precision = 0.9987745098039216`
- `high_priority_precision_ci_low = 0.9930910774764203`
- `safe_precision = 1.0`
- `safe_precision_ci_low = 0.9010957324106112`
- `false_high_priority_on_delay = 0.0036101083032490976`
- `false_safe_rate_union = 0.0036101083032490976`
- `nonfinite_skipped_update_rate = 0.0`

focused pair gate：

- `pair_count = 78`
- `raw_pair_pass_rate = 0.9615384615384616`，即 `75/78`
- `admission_pair_pass_rate = 0.9615384615384616`，即 `75/78`
- `delay_risk_pair_pass_rate = 0.9743589743589743`，即 `76/78`
- `strict_pair_pass_rate = 0.9615384615384616`，即 `75/78`
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

本轮启用了 `--epoch-checkpoint-dir`，因此每个 epoch 都有独立 checkpoint / metrics，
focused gate 不再只保留 selected checkpoint。

| epoch | local gate | accepted | ROI | ROI CI low | false-delay | raw | admission | delay-risk | strict |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | true | 35 | 13.653 | 5.210 | 0.0000 | 69/78 | 68/78 | 68/78 | 68/78 |
| 2 | true | 35 | 15.134 | 6.452 | 0.0000 | 73/78 | 74/78 | 74/78 | 73/78 |
| 3 | false | 91 | 8.024 | 4.081 | 0.0108 | 75/78 | 76/78 | 75/78 | 75/78 |
| 4 | true | 35 | 18.603 | 9.467 | 0.0036 | 75/78 | 75/78 | 76/78 | 75/78 |
| 5 | false | 22 | 25.415 | 12.583 | 0.0000 | 76/78 | 76/78 | 75/78 | 74/78 |

epoch 5 的 ROI-CI 最高，但 local gate 为 false，且 strict 反而降到 `74/78`；不能选。
epoch 4 是本轮合法 selected checkpoint。

## 与 v133-v135 对比

| run | selected epoch | local gate | accepted | ROI | ROI CI low | false-delay | focused raw | focused admission | focused delay-risk | focused strict |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v133 | 2 | true | 36 | 18.801 | 9.879 | 0.0072 | 75/78 | 77/78 | 77/78 | 75/78 |
| v134 | 5 | true | 35 | 19.518 | 10.439 | 0.0072 | 74/78 | 74/78 | 74/78 | 74/78 |
| v135 | 2 | true | 35 | 17.146 | 8.013 | 0.0000 | 68/78 | 74/78 | 74/78 | 68/78 |
| v136 | 4 | true | 35 | 18.603 | 9.467 | 0.0036 | 75/78 | 75/78 | 76/78 | 75/78 |

v136 证明 raw-all-candidate loss 是比 v135 interaction 更正确的方向：它恢复了 raw/strict，
并修复了 v135 中 `4e481a6307fca228` 的 4 个 sector-wave raw 失败。但它没有超过 v133
的 focused strict，也没有达到 78/78。

## Focused Failure Anatomy

v136 focused failure audit：

```text
pair_count = 78
failed_pair_count = 3
pair_pass_count = 75
strict_pair_pass_rate = 0.9615384615384616
raw_fail_count = 3
admission_fail_count = 3
delay_risk_fail_count = 2
all_failed_heads_near_rate_among_failed = 0.0
any_failed_head_deep_rate_among_failed = 0.3333333333333333
diagnosis_counts = {
  deep_structural_score_gap: 1,
  mixed_margin_failure: 1,
  shared_signature_confounder: 1,
  pair_passes: 75
}
```

失败 pair：

| context | family | positive row | negative row | positive ROI | raw margin | admission margin | delay-risk margin | diagnosis |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `b36178f6655c5f75` | greedy-anchor | 813 | 815 | 1.321 | -0.0311 | -0.0189 | -0.0091 | mixed margin |
| `84ae11479ed592d4` | greedy-anchor | 998 | 1001 | 1.464 | -0.0729 | -0.0449 | -0.0235 | deep structural |
| `9f80ae35ea87da5b` | random-wave | 183 | 845 | 1.106 | -0.0460 | -0.0047 | +0.0067 | shared signature confounder |

注意：`183/845` 属于 validation-side focused gate 行，不能直接泄漏进 train-only replay。

## 特征审计

top-context feature contrast 结论：

```text
primary = visible_inputs_differ_but_model_still_misranks
failed_pair_count = 3
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
failed_context_feature_drift_pair_count = 0
deep_failed_pair_count = 1
mean_failed_candidate_feature_l1 = 431.10931671724614
recommended_next_step = tighten_context_local_pairwise_ranking_head
```

这说明剩余失败不是输入完全相同，也不是 context feature drift。模型可见张量有差异，但
当前 head / loss 仍没有稳定学到这 3 个 context-local ordering。

## 为什么不跑 kNN/OOD

kNN/OOD 是 Stage 4 前的安全壳审计，不是修复 focused pair gate 的工具。v136 selected
checkpoint 已经被 focused gate 拦住：

```text
raw/admission/strict = 75/78
delay-risk = 76/78
required = 78/78
```

即使 kNN/OOD 通过，也不能覆盖 focused gate 失败。因此本轮跳过 kNN/OOD。

## 下一步

v136 的主要价值是定位：旧 raw loss 的训练口径确实不匹配 focused gate，修正后能修复一大批
near/shared-signature raw 失败；但剩余 3 对已经不是“盲目加 multiplier”能可靠解决的
near-margin 问题。

下一步不建议继续调高 `focused_pair_raw_all_candidate_loss_multiplier`。更合理的是：

1. 对剩余 `b36178`、`84ae`、`9f80` 做 action-consequence 级别的可解释特征/标签审计，
   尤其区分 greedy-anchor 小 ROI 正例和 hard-negative 的真实轨迹差异；
2. 设计真正的 context-local pair-delta ranking head，并明确是否能把该 head 的信息融合回
   raw/admission score；只训练一个不参与 admission score 的 auxiliary comparator 不够；
3. 对 validation-only 失败行保持严格隔离，不能为了修复 `183/845` 把 validation 行加入训练；
4. 继续保持 exactness 边界：学习模块只能决定 admission / scheduling，不能生成 certificate，
   也不能永久丢弃 true-RC negative columns。
