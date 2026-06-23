# BPC_future GAT Target Mode Stage 3 v119 标签来源冲突审计

日期：2026-06-22

## 结论

当前 v116 数据集中仍存在模型可见输入完全相同、但 long-horizon / trajectory 标签互相矛盾的样本组。

这不是继续调 loss multiplier 能解决的问题：同一个 GAT 输入被要求同时学习正负 admission 结论时，
Stage 3 的 focused pair gate 和 false-delay gate 会互相拉扯。因此下一轮重训前应先在 dataset builder
层面对这些冲突组做 deterministic repair：保守做法是丢弃整个冲突组，或在有严格、在线可用的来源优先级时只保留最高可信标签。

## Exactness 边界

- 只读取现有 manifest、sample tensor 和 source JSONL；
- 不运行 BPC / pricing / RMP / worker；
- 不生成 official bound 或 certificate；
- GAT/kNN/OOD 不能永久丢弃 true-RC negative；
- final certificate 仍只能来自 exact pricing full closure。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_batch_impact/v116_context_interaction_label_conflict_cleaned_5000_stage4_biased_20260622
audited_sample_count = 1177
source_row_count = 1221
model_visible_unique_group_count = 942
model_visible_duplicate_group_count = 128
model_visible_label_conflict_group_count = 14
model_visible_label_conflict_sample_count = 30
model_visible_label_conflict_sample_rate = 0.025488530161427356
explicit_long_horizon_conflict_group_count = 14
mixed_provenance_conflict_group_count = 14
stage3_retrain_safe_without_repair = false
recommended_next_step = deduplicate_or_drop_conflicting_explicit_long_horizon_groups_before_retraining
conflict_groups_path = BPC_future/results/gat_batch_impact_label_provenance_conflicts_v116_current_20260622/model_visible_label_conflict_groups.jsonl
duplicate_groups_path = BPC_future/results/gat_batch_impact_label_provenance_conflicts_v116_current_20260622/model_visible_duplicate_groups.jsonl
```

## 冲突字段统计

```json
{
  "manifest_accepted_batch_roi": 14,
  "manifest_delay_candidate_count": 1,
  "manifest_high_priority_candidate_count": 1,
  "manifest_label_batch_roi_positive": 1,
  "y_accepted_batch_roi": 14,
  "y_bad_mode_switch": 1,
  "y_barrier_slack": 14,
  "y_batch_roi_positive": 1,
  "y_candidate_delay_risk": 1,
  "y_candidate_high_priority": 1,
  "y_delta_v": 14,
  "y_tail_improved": 1
}
```

## 来源差异统计

```json
{
  "ab_audit_roi_class": 2,
  "final_judge_retry_delta": 2,
  "generated_sequences_delta": 14,
  "pricing_calls_delta": 2,
  "pricing_tail_retry_delta": 2,
  "solving_time_delta": 14,
  "source_file": 1,
  "v107_unique_source_path": 14,
  "worker_source_files": 14
}
```

## Top 冲突组

### 组 1

```text
row_indices = [451, 738]
context_hashes = ['ac056820151e9ad7']
families = ['sector-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_sequential_target_materialization_utility_rows_tranq20_01_20260616/sequential_target_materialization_utility_rows.jsonl']
provenance_roi_classes = ['negative_retry_roi']
accepted_batch_roi_min = -4.1412
accepted_batch_roi_max = -2.7302804
```

- row 451: roi=-2.7302804, batch_positive=0, ab_class=negative_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 738: roi=-4.1412, batch_positive=0, ab_class=None, source=BPC_future/results/gat_sequential_target_materialization_utility_rows_tranq20_01_20260616/sequential_target_materialization_utility_rows.jsonl

### 组 2

```text
row_indices = [396, 416]
context_hashes = ['ddcb5387bef3bf63']
families = ['random-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v16_train_split_top3_task20_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['negative_retry_roi']
accepted_batch_roi_min = -4.6268153
accepted_batch_roi_max = -4.615673
```

- row 396: roi=-4.615673, batch_positive=0, ab_class=negative_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v16_train_split_top3_task20_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 416: roi=-4.6268153, batch_positive=0, ab_class=negative_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl

### 组 3

```text
row_indices = [388, 453]
context_hashes = ['79fde658840fe2b8']
families = ['sector-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['negative_primal_roi']
accepted_batch_roi_min = -26.6602402
accepted_batch_roi_max = -26.65894575
```

- row 388: roi=-26.6602402, batch_positive=0, ab_class=negative_primal_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 453: roi=-26.65894575, batch_positive=0, ab_class=negative_primal_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl

### 组 4

```text
row_indices = [385, 456]
context_hashes = ['ac15bc4e7e3d6fff']
families = ['sector-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['positive_retry_roi']
accepted_batch_roi_min = 0.82443335
accepted_batch_roi_max = 0.8384177
```

- row 385: roi=0.82443335, batch_positive=1, ab_class=positive_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 456: roi=0.8384177, batch_positive=1, ab_class=positive_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl

### 组 5

```text
row_indices = [389, 454]
context_hashes = ['79fde658840fe2b8']
families = ['sector-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['positive_primal_roi']
accepted_batch_roi_min = 1.20231185
accepted_batch_roi_max = 1.21278025
```

- row 389: roi=1.21278025, batch_positive=1, ab_class=positive_primal_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 454: roi=1.20231185, batch_positive=1, ab_class=positive_primal_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl

### 组 6

```text
row_indices = [384, 455]
context_hashes = ['ac15bc4e7e3d6fff']
families = ['sector-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['negative_primal_roi']
accepted_batch_roi_min = -1.90466955
accepted_batch_roi_max = -1.7641904
```

- row 384: roi=-1.7641904, batch_positive=0, ab_class=negative_primal_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 455: roi=-1.90466955, batch_positive=0, ab_class=negative_primal_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl

### 组 7

```text
row_indices = [397, 417]
context_hashes = ['ddcb5387bef3bf63']
families = ['random-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v16_train_split_top3_task20_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['negative_retry_roi']
accepted_batch_roi_min = -3.1229681
accepted_batch_roi_max = -3.1140998
```

- row 397: roi=-3.1229681, batch_positive=0, ab_class=negative_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v16_train_split_top3_task20_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 417: roi=-3.1140998, batch_positive=0, ab_class=negative_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl

### 组 8

```text
row_indices = [400, 418]
context_hashes = ['67c11b5ec80925ec']
families = ['random-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'manifest_delay_candidate_count', 'manifest_high_priority_candidate_count', 'manifest_label_batch_roi_positive', 'y_accepted_batch_roi', 'y_bad_mode_switch', 'y_barrier_slack', 'y_batch_roi_positive', 'y_candidate_delay_risk', 'y_candidate_high_priority', 'y_delta_v', 'y_tail_improved']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v16_train_split_top3_task20_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['no_observed_roi', 'positive_retry_roi']
accepted_batch_roi_min = 0.0
accepted_batch_roi_max = 1.0
```

- row 400: roi=0.0, batch_positive=0, ab_class=no_observed_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v16_train_split_top3_task20_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 418: roi=1.0, batch_positive=1, ab_class=positive_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl

### 组 9

```text
row_indices = [387, 452]
context_hashes = ['79fde658840fe2b8']
families = ['sector-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['negative_primal_roi']
accepted_batch_roi_min = -25.99779565
accepted_batch_roi_max = -25.97990755
```

- row 387: roi=-25.97990755, batch_positive=0, ab_class=negative_primal_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v15_first_tranche_top3_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 452: roi=-25.99779565, batch_positive=0, ab_class=negative_primal_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v53_post_v51_individual_followup_20260616/same_context_target_worker_batch_impact_rows.jsonl

### 组 10

```text
row_indices = [403, 406, 419]
context_hashes = ['0df8d5cea7864e69']
families = ['sector-wave']
task_counts = [20]
conflict_fields = ['manifest_accepted_batch_roi', 'y_accepted_batch_roi', 'y_barrier_slack', 'y_delta_v']
provenance_source_paths = ['BPC_future/results/gat_multibatch_worker_batch_impact_rows_v17_train_split_next3_mixed_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v21_train_split_sector_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl', 'BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl']
provenance_roi_classes = ['negative_retry_roi']
accepted_batch_roi_min = -14.0569863
accepted_batch_roi_max = -13.87521635
```

- row 403: roi=-13.87521635, batch_positive=0, ab_class=negative_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v17_train_split_next3_mixed_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 406: roi=-14.0434271, batch_positive=0, ab_class=negative_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v21_train_split_sector_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl
- row 419: roi=-14.0569863, batch_positive=0, ab_class=negative_retry_roi, source=BPC_future/results/gat_multibatch_worker_batch_impact_rows_v23_train_split_remaining_contrast_first_tranche_20260616/same_context_target_worker_batch_impact_rows.jsonl

## Stage 3 判断

本审计仍属于 Stage 3 offline diagnostic。若存在冲突组，不能把后续 checkpoint
称为 Stage 4 candidate，除非先重建数据并证明同一 frozen threshold/OOD/fallback
规则下 precision、safe precision、ROI、coverage、focused pair 和 kNN/OOD gate 均通过。

## 下一步

1. 在 `build_gat_batch_impact_dataset.py` 中增加 explicit long-horizon 同输入冲突组过滤或严格来源优先级。
2. 重建一个 v119 dataset，确认 `model_visible_label_conflict_group_count = 0`。
3. 只在 v119 冲突清零后再重训 GAT；不要把离线 provenance 字段直接加进模型，除非线上 admission scheduler 也能稳定获得同一字段。
