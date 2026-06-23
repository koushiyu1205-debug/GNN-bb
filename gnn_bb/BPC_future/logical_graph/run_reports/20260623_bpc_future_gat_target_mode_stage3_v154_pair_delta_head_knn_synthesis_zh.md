# BPC_future GAT target-mode Stage 3 v154 pair-delta head 与 kNN/OOD 复训审计总结

日期：2026-06-23

## 目的

在 v152/v153 已确认 train-only analog boost 仍会陷入同族同上下文排序失败后，本轮实现并训练一个默认关闭的
`context_pair_delta` 辅助排序头，检验它是否能改善 focused same-context positive-vs-hard-negative gate。

本轮仍是离线诊断：不运行 BPC、pricing、RMP，不生成 certificate 或 official lower bound；kNN/OOD 只能作为延迟
true-RC negative 的 safety shell，不能永久丢弃列。

## 机器字段

```text
run_id = v154_pair_delta_head_v152_balanced_trainonly_analog_boost_path_context_gate_seed13
dataset_dir = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
effective_sample_count_after_conflict_filter = 1117
candidate_count = 12684
seed = 13
epochs = 5
context_pair_hidden_dim = 0
context_pair_delta_hidden_dim = 16
context_pair_delta_loss_multiplier = 0.5
focused_pair_delta_loss_multiplier = 2.0
checkpoint = BPC_future/results/gat_batch_impact_training_v154_pair_delta_head_v152_balanced_trainonly_analog_boost_path_context_gate_seed13_20260623/model.pt
metrics = BPC_future/results/gat_batch_impact_training_v154_pair_delta_head_v152_balanced_trainonly_analog_boost_path_context_gate_seed13_20260623/metrics.json
training_report = BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v154_pair_delta_head_seed13_zh.md
focused_pair_audit_report = BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v154_pair_delta_head_pair_failure_audit_zh.md
knn_global_strict_report = BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v154_pair_delta_head_knn_ood_global_strict_zh.md
knn_scale_strict_report = BPC_future/logical_graph/run_reports/20260623_bpc_future_gat_target_mode_stage3_v154_pair_delta_head_knn_ood_scale_strict_zh.md
stage3_completed = false
stage4_candidate_ready = false
default_enabled = false
```

## 结论

v154 比 v152 明显变好，但还不能进入 Stage 4。

GAT focused gate 从 v152 的四项失败收窄为两项失败：admission 和 delay-risk 已经达到 78/78；raw/strict 从
75/78 提升到 77/78，但 Stage 3 focused gate 要求 78/78，所以仍失败。

kNN/OOD 的 scale strict 审计已经通过 validation safety 条件：accepted=36，ROI CI low=10.0468，
false-high-priority-on-delay=0，false-safe-union=0，safe precision CI low=0.9036。但是 kNN/OOD 不能覆盖
GAT 本体 focused raw/strict gate 的失败，因此不能把该 checkpoint 升为 Stage 4 candidate。

## 与 v152 对比

```text
v152 focused observed:
  pair_count = 78
  raw_pair_pass_rate = 0.9615384615
  admission_pair_pass_rate = 0.9615384615
  delay_risk_pair_pass_rate = 0.9615384615
  strict_pair_pass_rate = 0.9615384615
  reject = raw/admission/delay_risk/strict all below threshold

v154 focused observed:
  pair_count = 78
  raw_pair_pass_rate = 0.9871794872
  admission_pair_pass_rate = 1.0
  delay_risk_pair_pass_rate = 1.0
  strict_pair_pass_rate = 0.9871794872
  context_pair_delta_pair_pass_rate = 0.9743589744
  reject = raw/strict below threshold
```

validation deployment metrics:

```text
v152:
  accepted_batch_count = 35
  accepted_batch_roi = 19.2210
  accepted_batch_roi_ci_low = 10.0960
  high_priority_precision = 0.996161
  safe_precision_ci_low = 0.901096
  false_high_priority_on_delay_count = 2

v154:
  accepted_batch_count = 36
  accepted_batch_roi = 18.9392
  accepted_batch_roi_ci_low = 10.0468
  high_priority_precision = 0.996650
  safe_precision_ci_low = 0.903578
  false_high_priority_on_delay_count = 2
```

v154 的 GAT 本体 ROI 变化不大，主要收益来自 focused context ranking：失败面从 3 个 pair 降到 1 个 pair。

## 失败 pair

focused pair failure audit 显示剩余失败只有 1 个 pair：

```text
context_key = apollo15_20km_random-wave_randomtw_tasks030_03_seed71204|9f80ae35ea87da5b
positive_row_index = 844
negative_row_index = 845
positive_roi = 53.71779400000014
negative_roi = 0.0
raw_margin = -0.0040836930
admission_margin = 0.0026177732
delay_risk_margin = 0.0051024556
context_pair_delta_margin = 0.0166664720
```

这不是深结构缺口，而是 raw head 的近零负 margin。新增 pair-delta 头、admission、delay-risk 都已经把该 pair
排对，只有 raw high-priority 分数仍差 0.00408。

## kNN/OOD 结果

global strict:

```text
validation_candidate_ready = false
accepted_batch_count = 33
accepted_batch_roi = 15.2928
accepted_batch_roi_ci_low = 7.3656
coverage = 1.0
false_high_priority_on_delay_count = 0
false_safe_rate_union = 0.0
safe_precision = 1.0
safe_precision_ci_low = 0.8957265699
blocker = validation_safe_precision_ci_low_below_min
```

scale strict:

```text
validation_candidate_ready = true
accepted_batch_count = 36
accepted_batch_roi = 18.9392
accepted_batch_roi_ci_low = 10.0468
coverage = 0.9691780822
ood_count = 9
false_high_priority_on_delay_count = 0
false_safe_rate_union = 0.0
safe_precision = 1.0
safe_precision_ci_low = 0.9035781696
validation_safety_checks = all true
```

scale strict kNN/OOD 是本轮安全壳的正结果，但它仍是 diagnostic-only，不能替代 GAT focused raw/strict gate。

## Epoch 选择说明

本线的 checkpoint selection 不是按 validation loss 直接选，也不是按单项 precision 直接选。顺序是先看本地部署
gate、ROI CI / baseline utility，再用 loss 做 tie-breaker。v154 的 best epoch 与 best loss epoch 都是 5，但
checkpoint_gate_pass 仍为 false，因为 focused raw/strict 和正式 kNN/OOD/online shadow 条件没有全部满足。

这也解释了先前为什么不能因为 epoch 7/8 loss 更低就选它们：低 loss 不能覆盖 delay false-positive 或 focused
pair gate 失败。

## 代码边界

本轮新增的 `context_pair_delta` 是默认关闭的辅助头：

- `context_pair_delta_hidden_dim=0` 时输出零张量，不影响既有 admission / delay / high-priority 决策；
- 开启后只参与训练和诊断字段，不放松 focused gate，不生成 certificate；
- 旧的 `context_pair_comparator` 保持关闭，避免复用 v130/v131/v134 已验证为负结果的融合路径。

## 下一步

优先做 v155 的窄幅近 margin 修复，而不是继续扩大采样：

- 保持 `context_pair_delta` 为辅助诊断头；
- 对剩余 row 844 vs 845 的 raw near-margin 失败加更强 focused raw 约束，或把 pair-delta 的正确排序蒸馏回 raw high-priority logit；
- 不用 kNN/OOD 放宽 GAT focused gate；
- v155 目标是把 raw/strict 从 77/78 推到 78/78，同时保持 scale strict kNN/OOD validation safety 通过。
