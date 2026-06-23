# BPC_future GAT target-mode Stage 3 v135 审计综合报告

日期：2026-06-23

## 结论

v135 是负结果。它在 v134/v133 的基础上加入可选的
`candidate_context_interaction_dim=16`，让 candidate embedding 与 batch/context
embedding 做显式交互投影，但最终 focused pair gate 从 v134 的 `74/78` 退化到
`68/78`。selected checkpoint 的 local deployment gate 虽然通过，precision 和
false-delay 也很干净，但同上下文 positive/negative 排序明显变差，因此不能进入
kNN/OOD，也不能作为 Stage 4 candidate。

本次运行不调用 BPC / pricing / RMP，不生成 certificate 或 official lower bound。
GAT 仍只作为 admission scheduling 的离线诊断候选。

## 运行对象

- dataset:
  `BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622`
- checkpoint:
  `BPC_future/results/gat_batch_impact_training_v135_candidate_context_interaction_seed13_20260623/model.pt`
- metrics:
  `BPC_future/results/gat_batch_impact_training_v135_candidate_context_interaction_seed13_20260623/metrics.json`
- training report:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v135_candidate_context_interaction_seed13_zh.md`
- focused failure audit:
  `BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v135_focused_pair_failure_audit_zh.md`

## 本轮改动意图

v134 的补充审计显示失败 pair 的模型输入并非完全相同，也不是 context feature drift；
当前更像是普通 raw/admission heads 没有把可见差异转成正确的 context-local ordering。
因此 v135 不继续叠加 comparator loss，而是做一个结构性试验：

- 新增可选 candidate/context/batch interaction projectors；
- 对每个 candidate 拼入 `candidate*batch`、`candidate*context`、
  `candidate-batch`、`candidate-context` 四类交互特征；
- 只在 `candidate_context_interaction_dim > 0` 时启用；
- 默认 `0`，保持旧 checkpoint / 旧配置兼容。

这次训练启用 `candidate_context_interaction_dim=16`，并关闭 context-pair comparator
loss，避免把 v134 已证明无效的 comparator 再混入。

## 关键指标

checkpoint selection 仍是：

```text
deployment_gate_first_then_roi_ci_baseline_utility_loss
```

selected epoch = `2`；best validation-loss epoch = `3`。epoch 3 的 validation loss
更低，且 local gate 也通过，但 checkpoint selection 不是按最低 loss 选，而是在通过
local deployment gate 的候选中按 ROI-CI / baseline utility 选择；epoch 2 的
`accepted_batch_roi_ci_low = 8.013` 高于 epoch 3 的训练轨迹记录口径，因此被选中。

epoch 2 validation deployment metrics：

- `threshold_local_gate_pass = true`
- `accepted_batch_count = 35`
- `accepted_batch_rate = 0.11986301369863013`
- `accepted_batch_roi = 17.145690649322102`
- `accepted_batch_roi_ci_low = 8.013031859074625`
- `high_priority_precision = 1.0`
- `high_priority_precision_ci_low = 0.9970100594501298`
- `safe_precision = 1.0`
- `safe_precision_ci_low = 0.9010957324106112`
- `false_high_priority_on_delay = 0.0`
- `false_safe_rate_union = 0.0`
- `nonfinite_skipped_update_rate = 0.0`

focused pair gate：

- `pair_count = 78`
- `raw_pair_pass_rate = 0.8717948717948718`，即 `68/78`
- `admission_pair_pass_rate = 0.9487179487179487`，即 `74/78`
- `delay_risk_pair_pass_rate = 0.9487179487179487`，即 `74/78`
- `strict_pair_pass_rate = 0.8717948717948718`，即 `68/78`
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

当前训练脚本在 `history` 中保存每个 epoch 的 deployment 摘要，focused gate 的完整明细
只保存 selected checkpoint。因此下表只列 `history` 可复核字段。

| epoch | local gate | accepted | ROI | false-delay | precision | safe precision | threshold | validation loss |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | false | 36 | 0.770 | 0.0000 | 1.0000 | 1.0000 | 0.603 | 6.504 |
| 2 | true | 35 | 17.146 | 0.0000 | 1.0000 | 1.0000 | 0.650 | 5.966 |
| 3 | true | 36 | 16.320 | 0.0072 | 0.9985 | 1.0000 | 0.568 | 5.477 |
| 4 | false | 24 | 1.599 | 0.0000 | 1.0000 | 1.0000 | 0.644 | 6.082 |
| 5 | true | 35 | 15.282 | 0.0072 | 0.9986 | 1.0000 | 0.632 | 5.776 |

这条轨迹说明 v135 的 local safety 指标可以被阈值调出来，但 ROI frontier 低于 v134，
并且 focused ranking 明显退化。

## 与 v133/v134 对比

| run | selected epoch | local gate | accepted | ROI | ROI CI low | false-delay | focused raw | focused admission | focused delay-risk | focused strict |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v133 | 2 | true | 36 | 18.801 | 9.879 | 0.0072 | 75/78 | 77/78 | 77/78 | 75/78 |
| v134 | 5 | true | 35 | 19.518 | 10.439 | 0.0072 | 74/78 | 74/78 | 74/78 | 74/78 |
| v135 | 2 | true | 35 | 17.146 | 8.013 | 0.0000 | 68/78 | 74/78 | 74/78 | 68/78 |

v135 唯一改善的是 selected checkpoint 的 false-delay 降到 `0.0`，但代价是 ROI-CI 和
focused raw/strict 大幅下降。这个 tradeoff 不符合 Stage 3 的
`precision_constrained_roi_maximization`，也不符合 Stage 4 前置 focused gate。

## Focused Failure Anatomy

v135 focused failure audit：

```text
pair_count = 78
failed_pair_count = 10
pair_pass_count = 68
strict_pair_pass_rate = 0.8717948717948718
raw_fail_count = 10
admission_fail_count = 4
delay_risk_fail_count = 4
all_failed_heads_near_rate_among_failed = 0.7
any_failed_head_deep_rate_among_failed = 0.1
diagnosis_counts = {
  deep_structural_score_gap: 1,
  mixed_margin_failure: 2,
  near_margin_loss_tuning_candidate: 3,
  near_margin_with_shared_signature: 4,
  pair_passes: 68
}
```

失败最集中的 context：

| context hash | family | task | failed pairs | pair count | diagnosis |
|---|---|---:|---:|---:|---|
| `4e481a6307fca228` | sector-wave | 20 | 4 | 10 | near-margin / shared-signature |
| `b36178f6655c5f75` | greedy-anchor | 20 | 1 | 4 | near-margin |
| `84ae11479ed592d4` | greedy-anchor | 20 | 1 | 2 | near-margin |
| `62c86745ed2b3aaa` | random-wave | 20 | 1 | 2 | mixed-margin |
| `5368cf35ed6f06cb` | random-wave | 30 | 1 | 2 | mixed-margin |
| `9a2ca522ff49991c` | random-wave | 50 | 1 | 1 | shared-signature |
| `ddcb5387bef3bf63` | random-wave | 20 | 1 | 1 | deep structural |

和 v134 不同，v135 的失败多数是 near-margin 或 shared-signature，而不是 v134 那种
以 deep structural score gap 为主。这说明显式交互投影并没有稳定修复原来的深层失败，
反而把更多 previously-pass 的 context-local raw ordering 推到边界附近。

## 为什么不跑 kNN/OOD

kNN/OOD 是 Stage 4 前的安全壳审计，不是修复 focused pair gate 的工具。v135 selected
checkpoint 已经被 focused gate 拦住：

```text
raw/strict = 68/78
admission/delay-risk = 74/78
required = 78/78
```

即使 kNN/OOD 通过，也不能覆盖 focused gate 失败。因此本轮跳过 kNN/OOD。

## 工程改动状态

已实现并验证的代码结构：

- `BatchImpactGAT` 新增 `candidate_context_interaction_dim`，默认 `0`；
- 默认关闭时保留旧 head 输入维度，兼容旧 checkpoint；
- 启用时新增 candidate/batch/context projectors，并把四类交互特征拼入
  high-priority / delay-risk candidate heads；
- 训练脚本新增 `--candidate-context-interaction-dim`；
- 单元测试覆盖默认关闭 shape、启用后 head 输入维度、以及 projector gradient。

该结构本身可以保留为实验开关，但 v135 结果说明它不应作为下一步主线。

## 下一步

v135 证明“简单显式 candidate x context/batch interaction”不是当前 blocker 的有效
修复，至少不能以这个形态继续推进。下一步不应继续扩大 interaction 维度，也不应因为
false-delay 变好就放松 focused gate。

更合理的方向是：

1. 把 focused gate 的 78 个同上下文 pair 直接作为 first-class ranking target，
   做显式 pair-delta / context-local ranking head，而不是让普通 candidate head 间接学习；
2. 在不泄漏 validation rows 的前提下，构造 train-only 的 context-local full-tranche
   replay，使 raw/admission/delay 三个头共享同一批正负对约束；
3. 给训练脚本增加 per-epoch focused gate 记录，避免后续只能看到 selected checkpoint
   的 focused 明细；
4. 继续保持 exactness 边界：学习模块只能决定 admission / scheduling，不能生成
   certificate，也不能永久丢弃 true-RC negative columns。
