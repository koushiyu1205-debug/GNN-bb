# BPC_future GAT Target Mode Stage 3 v119 显式标签冲突过滤综合报告

日期：2026-06-22

## 结论

v119 完成了一次 Stage 3 数据合同修复：在 batch-impact dataset builder 中过滤
explicit long-horizon 同输入冲突组，并重建了冲突清零的数据集。

这不是 Stage 3 完成，也不是 Stage 4 candidate。它只证明 v118 暴露出的一个关键
blocker 已被移出训练数据：同一个模型可见输入不再同时对应互相矛盾的 trajectory
标签。下一步可以在 v119 数据集上重训 GAT，然后重新跑 epoch selector、focused
pair audit；只有 local gate 和 focused pair gate 都过线后，才值得继续跑 kNN/OOD。

## Exactness 边界

- 只修改 offline dataset builder 与 offline audit 脚本；
- 不运行 BPC / pricing / RMP / worker；
- 不生成 official lower bound 或 certificate；
- GAT/kNN/OOD 仍不能永久丢弃 true-RC negative；
- final certificate 仍只能来自 exact pricing full closure。

## 背景

v118 top-context feature contrast 发现至少 1 个失败 pair 的模型输入完全不可区分：

```text
context_hash = 67c11b5ec80925ec
negative_row_index = 400
positive_row_index = 418
candidate_feature_l1 = 0
batch_feature_l1 = 0
context_feature_l1 = 0
sequence_position_l1 = 0
model_visible_difference = false
```

回溯 source provenance 后确认：两个样本来自不同 worker / A-B 路径，action/context
对模型完全相同，但 long-horizon 标签不同。继续调 loss multiplier 无法解决这种
监督矛盾。

## v116 冲突审计

新增脚本：

```text
BPC_future/scripts/audit_gat_batch_impact_label_provenance_conflicts.py
```

v116 审计结果：

```text
dataset = BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622
audited_sample_count = 1177
model_visible_duplicate_group_count = 128
model_visible_duplicate_sample_count = 363
model_visible_label_conflict_group_count = 14
model_visible_label_conflict_sample_count = 30
explicit_long_horizon_conflict_group_count = 14
mixed_provenance_conflict_group_count = 14
stage3_retrain_safe_without_repair = false
```

其中 1 组是二元正负标签冲突：

```text
row_indices = [400, 418]
context_hash = 67c11b5ec80925ec
conflict_fields =
  manifest_label_batch_roi_positive,
  y_batch_roi_positive,
  y_candidate_high_priority,
  y_candidate_delay_risk,
  y_bad_mode_switch,
  y_tail_improved,
  y_accepted_batch_roi,
  y_delta_v,
  y_barrier_slack
provenance_source_paths =
  v16_train_split_top3_task20
  v23_train_split_remaining_contrast_first_tranche
provenance_roi_classes = [no_observed_roi, positive_retry_roi]
```

其余 13 组主要是同一模型输入对应不同 ROI / delta-v / barrier-slack 回归标签。

## Builder 修复

修改文件：

```text
BPC_future/scripts/build_gat_batch_impact_dataset.py
```

新增逻辑：

- 先用现有 `_long_horizon_candidate_key` 聚合 explicit long-horizon candidate；
- 对同一 key 的 explicit 标签签名做一致性检查；
- 如果同一 key 有多个不同标签签名，则整组 candidate key 进入
  `conflicting_explicit_long_horizon_candidate_keys`；
- 构建样本时只要 row 的 candidate key 命中该集合，就跳过并计入
  `skipped_counts["conflicting_explicit_long_horizon_label"]`；
- 不把 `v107_unique_source_path`、`worker_source_files`、`ab_audit_roi_class`
  等 offline provenance 注入模型特征，避免线上不可用字段造成 leakage。

manifest / summary 新增字段：

```text
explicit_long_horizon_candidate_key_count
conflicting_explicit_long_horizon_candidate_key_count
```

## v119 数据集

输出：

```text
dataset = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
dataset_report = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_dataset_zh.md
conflict_audit = BPC_future/logical_graph/run_reports/20260622_bpc_future_gat_target_mode_stage3_v119_explicit_label_conflict_filtered_conflict_audit_zh.md
```

构建结果：

```text
sample_count = 1117
candidate_count = 12684
training_ready = true
ranking_ready = true
family_counts = {'greedy-anchor': 358, 'random-wave': 421, 'sector-wave': 338}
task_count_counts = {'5': 32, '10': 74, '20': 688, '30': 168, '50': 119, '100': 36}
explicit_long_horizon_candidate_key_count = 65
conflicting_explicit_long_horizon_candidate_key_count = 19
skipped_counts = {
  'conflicting_explicit_long_horizon_label': 89,
  'shadowed_by_explicit_long_horizon_label': 15
}
```

相对 v116，v119 样本数从 1177 降到 1117。跳过数大于 v116 审计中的
30 条直接冲突样本，是因为 builder 以 candidate key 为单位保守过滤，同时会过滤
命中冲突 key 的后续重复/影子样本。

## v119 冲突复审

v119 复审结果：

```text
audited_sample_count = 1117
model_visible_duplicate_group_count = 107
model_visible_duplicate_sample_count = 316
model_visible_label_conflict_group_count = 0
model_visible_label_conflict_sample_count = 0
explicit_long_horizon_conflict_group_count = 0
mixed_provenance_conflict_group_count = 0
stage3_retrain_safe_without_repair = true
```

因此 v119 已清除本轮要修的 label-provenance blocker。剩余 duplicate group
不是标签冲突：它们是模型可见输入重复但标签一致的样本。

## Stage 3 状态

```text
stage3_completed = false
stage4_candidate_ready = false
production_ready = false
default_enabled = false
v119_training_input_ready = true
v119_model_visible_label_conflict_cleared = true
```

## 下一步

1. 用 v119 数据集重训 GAT，保持 `precision_constrained_roi_maximization` 和现有
   Stage 3 hard gate，不降低 precision / safe precision / false-delay / ROI / OOD 阈值。
2. 重训后先跑 epoch selector 与 focused pair audit，重点检查 v118 的
   `67c11b5ec80925ec` collision blocker 是否消失。
3. 只有 local gate 和 focused pair gate 同时过线后，再跑 kNN/OOD；如果仍不过线，
   继续做 context-local visible feature / ranking gap 审计，而不是进入 Stage 4。
