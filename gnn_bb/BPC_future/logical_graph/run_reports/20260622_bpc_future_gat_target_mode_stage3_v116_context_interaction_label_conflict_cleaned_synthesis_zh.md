# BPC_future GAT Target Mode Stage 3 v116 综合报告

日期：2026-06-22

## 结论

v116 是比 v112/v114 更好的 Stage 3 研究分支，但还不是 Stage 4 候选。

本轮真正修复的是 focused same-context positive/negative pair 中的不可学习冲突：
v115 加入 per-candidate branch/cut/active-basis interaction 特征后，top-context
model-input collision 仍为 64；v116 在离线数据构建中剔除了 44 条被 explicit
long-horizon label 覆盖的 default label 行后，top-context collision 降为 0。

训练和审计结果显示，v116 的 local deployment threshold、global kNN/OOD、scale
kNN/OOD 都已通过；主要剩余 blocker 是 focused-pair gate 尚未达到 100%。
focused strict pair pass rate 从 v112 的 0.7421875 提升到 v116 的
0.9354838709677419，但仍低于 Stage 3 当前硬门槛 1.0。

## Exactness 边界

- 本轮只改离线 dataset / feature / label 清理与诊断报告；
- 不运行 BPC、pricing、RMP、worker 或 certificate 生成；
- GAT/kNN/OOD 不能生成 official bound；
- GAT/kNN/OOD 不能永久丢弃 true-RC negative columns；
- final exact pricing full closure 仍是唯一 certificate 来源。

## 数据与模型变更

### v115：特征补强但冲突未消失

新增 candidate feature 维度从 40 增到 59，加入 active-basis、pool、forbidden
signature、branch constraint、cut coefficient 相关的 per-candidate interaction。

v115 top-context 审计：

```text
per_candidate_branch_cut_interaction_present = true
model_input_collision_pair_count = 64
failed_model_input_collision_pair_count = 64
context_feature_drift_pair_count = 0
primary = model_input_collision_still_exists_in_top_contexts
```

解释：冲突不是缺少 branch/cut/active-basis 可见性造成的，而是相同上下文、相同
candidate signature 的旧 default label 与新 explicit long-horizon label 互相矛盾。

### v116：label conflict cleanup

v116 在构建数据集时跳过被 explicit long-horizon label 覆盖的旧 default rows。

```text
sample_count = 1177
candidate_count = 13212
training_ready = true
ranking_ready = true
skipped.shadowed_by_explicit_long_horizon_label = 44
same_context_pair_count = 1549
same_context_comparable_pair_count = 1064
positive_negative_label_pair_count = 389
```

v116 top-context 审计：

```text
model_input_collision_pair_count = 0
failed_model_input_collision_pair_count = 0
context_feature_drift_pair_count = 0
per_candidate_branch_cut_interaction_present = true
primary = visible_inputs_differ_but_model_still_misranks
```

## 为什么 selector 选 epoch 1

v108 的问题是没有任何 epoch 真正通过 local deployment gate。epoch 7/8 的
validation loss 更低、accepted 数更多，但 false-high-priority-on-delay 超过
0.01，因此不应因为 loss 低而选它们。v108 epoch selector 中：

```text
epoch 1: accepted = 13, ROI = 33.163725, false-delay = 0.000000
epoch 7: accepted = 158, ROI = 7.169939, false-delay = 0.034965
epoch 8: accepted = 182, ROI = 6.289559, false-delay = 0.146853
```

v116 也选 epoch 1，但性质更好：epoch 1 是唯一 coverage confidence ready 且
false-delay safe 的 epoch；epoch 7/8 仍是 coverage ready but false-delay unsafe。

```text
epoch 1: accepted = 36, ROI = 4.602683, false-delay = 0.000000, threshold_local_gate_pass = true
epoch 7: accepted = 115, ROI = 1.604034, false-delay = 0.031469, threshold_local_gate_pass = false
epoch 8: accepted = 113, ROI = 2.737115, false-delay = 0.069930, threshold_local_gate_pass = false
```

因此这里不是 early stopping 偏好 epoch 1，也不是按 validation loss 选模型；选择规则是
deployment gate first，然后才看 ROI / utility / loss。后期 epoch 的 coverage 提高，
但安全指标掉线。

## v112 / v114 / v116 对比

| run | best epoch | validation accepted | validation ROI | safe precision CI low | focused strict | global kNN | scale kNN |
|---|---:|---:|---:|---:|---:|---|---|
| v112 | 1 | 35 | 4.921133 | 0.901096 | 0.742188 | pass | pass |
| v114 | 3 | 35 | 4.605858 | 0.901096 | 0.716146 | pass | pass |
| v116 | 1 | 36 | 4.602683 | 0.903578 | 0.935484 | pass | pass |

v116 相比 v112：

- focused strict 明显提升：0.7421875 -> 0.9354838709677419；
- accepted count 小幅提升：35 -> 36；
- safe precision CI low 小幅提升：0.9010957 -> 0.9035782；
- accepted ROI 小幅下降：4.9211329 -> 4.6026826；
- 仍未通过 focused-pair 100% gate。

## v116 focused-pair failure audit

```text
pair_count = 217
pair_pass_count = 203
failed_pair_count = 14
strict_pair_pass_rate = 0.9354838709677419
raw_fail_count = 7
admission_fail_count = 13
delay_risk_fail_count = 7
contexts_with_failure_count = 9
any_failed_head_deep_count = 0
all_failed_heads_near_rate_among_failed = 0.7142857142857143
recommended_next_step = train_combined_focused_candidate_admission_delay_loss
```

失败不再像 v115 那样是 identical model input contradictory label，而主要是 near-margin
head ranking 问题。下一步应优先调 focused candidate/admission/delay loss 或显式
tranche full training，不应先盲目继续采更多数据。

## v116 kNN/OOD

global strict：

```text
validation_safety_ready = true
accepted_batch_count = 36
accepted_batch_roi = 4.602682617492974
accepted_batch_roi_ci_low = 2.355012379080361
coverage = 1.0
false_safe_rate_union = 0.0
safe_precision_ci_low = 0.9035781695514236
production_block_reasons = []
```

scale strict：

```text
validation_safety_ready = true
accepted_batch_count = 36
accepted_batch_roi = 4.602682617492974
accepted_batch_roi_ci_low = 2.355012379080361
coverage = 0.9838187702265372
ood_count = 5
false_safe_rate_union = 0.0
safe_precision_ci_low = 0.9035781695514236
production_block_reasons = []
```

## Stage 3 状态

```text
stage3_completed = false
stage4_candidate_ready = false
remaining_primary_blocker = focused_pair_gate_below_1.0
secondary_blockers = knn_ood_holdout_audit_not_run, online_shadow_and_opt_in_ab_not_run
```

v116 可以替代 v112 作为下一轮 focused-pair 修复的基线，但不能进入 Stage 4。

## 建议下一步

1. 不要回到单纯扩样本；当前主要问题是 near-margin focused-pair ranking。
2. 在 v116 数据上做 focused candidate/admission/delay 联合 loss 小网格，目标是把
   strict pair pass rate 从 0.93548 推到 1.0，同时保持 global/scale kNN 通过。
3. 若仍卡在 1.0 门槛，再考虑对失败的 9 个 context 做 explicit tranche full training 或
   context-local margin shaping。
