# BPC_future GAT Target Mode Stage 3 v119 标签来源冲突审计

日期：2026-06-22

## 结论

本审计没有发现模型可见输入完全相同但标签冲突的样本组。

这意味着 v118 top-context collision 至少不是当前全数据集中的普遍 label-provenance 冲突；
下一步可以继续审计可见特征不足或 context-local ranking loss。

## Exactness 边界

- 只读取现有 manifest、sample tensor 和 source JSONL；
- 不运行 BPC / pricing / RMP / worker；
- 不生成 official bound 或 certificate；
- GAT/kNN/OOD 不能永久丢弃 true-RC negative；
- final certificate 仍只能来自 exact pricing full closure。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
audited_sample_count = 1117
source_row_count = 1221
model_visible_unique_group_count = 908
model_visible_duplicate_group_count = 107
model_visible_label_conflict_group_count = 0
model_visible_label_conflict_sample_count = 0
model_visible_label_conflict_sample_rate = 0.0
explicit_long_horizon_conflict_group_count = 0
mixed_provenance_conflict_group_count = 0
stage3_retrain_safe_without_repair = true
recommended_next_step = no_model_visible_label_conflict_found_continue_focused_pair_gap_audit
conflict_groups_path = BPC_future/results/gat_batch_impact_label_provenance_conflicts_v119_explicit_label_conflict_filtered_20260622/model_visible_label_conflict_groups.jsonl
duplicate_groups_path = BPC_future/results/gat_batch_impact_label_provenance_conflicts_v119_explicit_label_conflict_filtered_20260622/model_visible_duplicate_groups.jsonl
```

## 冲突字段统计

```json
{}
```

## 来源差异统计

```json
{}
```
## Stage 3 判断

本审计仍属于 Stage 3 offline diagnostic。即使模型可见标签冲突清零，后续 checkpoint
仍必须证明同一 frozen threshold/OOD/fallback 规则下 precision、safe precision、ROI、
coverage、focused pair 和 kNN/OOD gate 均通过，才能称为 Stage 4 candidate。

## 下一步

1. 用当前冲突清零的数据集重训 Stage 3 GAT。
2. 先跑 epoch selector / focused pair audit，确认 v118 的 collision blocker 是否消失。
3. 只有 local gate 与 focused pair gate 同时过线后，再运行 kNN/OOD；仍不得把 diagnostic checkpoint 升级成 Stage 4 candidate。
