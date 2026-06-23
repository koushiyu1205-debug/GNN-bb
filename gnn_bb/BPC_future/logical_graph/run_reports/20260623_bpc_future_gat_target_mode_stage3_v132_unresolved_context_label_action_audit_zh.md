# BPC_future GAT target-mode Stage 3 v132 unresolved-context label/action 审计

日期：2026-06-23

## 结论

本轮只审计 v131 unresolved / comparator-conflict same-context pair，结论为 `supported_labels_but_delay_risk_head_orders_positive_as_riskier`。
推荐下一步：`add_focused_delay_risk_or_action_consequence_loss_without_relaxing_gate`。

该审计不运行 BPC、pricing、RMP、worker 或 certificate；只读取既有 dataset、source JSONL 和 sample tensor。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_batch_impact/v119_explicit_label_conflict_filtered_5000_stage4_biased_20260622
pair_rows_path = BPC_future/results/gat_batch_impact_context_pair_comparator_audit_v131_v130_epoch004_20260623/context_pair_comparator_pair_rows.jsonl
input_pair_count = 78
selected_pair_count = 5
audited_pair_count = 5
audited_row_count = 9
audited_context_count = 4
primary = supported_labels_but_delay_risk_head_orders_positive_as_riskier
causal_pair_supported_rate = 1.0
label_polarity_valid_pair_rate = 1.0
unresolved_existing_failure_pair_count = 4
comparator_conflict_pair_count = 1
recommended_next_step = add_focused_delay_risk_or_action_consequence_loss_without_relaxing_gate
row_records_path = BPC_future/results/gat_batch_impact_unresolved_context_label_action_audit_v132_v131_20260623/unresolved_context_label_action_rows.jsonl
pair_records_path = BPC_future/results/gat_batch_impact_unresolved_context_label_action_audit_v132_v131_20260623/unresolved_context_label_action_pairs.jsonl
context_records_path = BPC_future/results/gat_batch_impact_unresolved_context_label_action_audit_v132_v131_20260623/unresolved_context_label_action_contexts.jsonl
```

## 诊断分布

```json
{
  "comparator_conflicts_supported_existing_pass": 1,
  "delay_risk_order_contradicts_positive": 3,
  "supported_labels_same_action_type_needs_visible_contrast": 1
}
```

## Top Contexts

```text
context_hash = b36178f6655c5f75
families = ['greedy-anchor']
pair_count = 2
unresolved_existing_failure_pair_count = 2
comparator_conflict_pair_count = 0
diagnosis_counts = {'delay_risk_order_contradicts_positive': 1, 'supported_labels_same_action_type_needs_visible_contrast': 1}
positive_roi_min/max = 1.3209439999999972 / 3.0676430000000323
negative_roi_min/max = 0.0 / 0.0
row_indices = [812, 813, 815]
```

```text
context_hash = 9f80ae35ea87da5b
families = ['random-wave']
pair_count = 1
unresolved_existing_failure_pair_count = 1
comparator_conflict_pair_count = 0
diagnosis_counts = {'delay_risk_order_contradicts_positive': 1}
positive_roi_min/max = 53.71779400000014 / 53.71779400000014
negative_roi_min/max = 0.0 / 0.0
row_indices = [844, 845]
```

```text
context_hash = a77e5457bde80b8e
families = ['random-wave']
pair_count = 1
unresolved_existing_failure_pair_count = 1
comparator_conflict_pair_count = 0
diagnosis_counts = {'delay_risk_order_contradicts_positive': 1}
positive_roi_min/max = 3.813146999999958 / 3.813146999999958
negative_roi_min/max = 0.0 / 0.0
row_indices = [797, 798]
```

```text
context_hash = 84ae11479ed592d4
families = ['greedy-anchor']
pair_count = 1
unresolved_existing_failure_pair_count = 0
comparator_conflict_pair_count = 1
diagnosis_counts = {'comparator_conflicts_supported_existing_pass': 1}
positive_roi_min/max = 1.464020000000005 / 1.464020000000005
negative_roi_min/max = 0.0 / 0.0
row_indices = [998, 1001]
```

## Stage 3 判断

如果 causal provenance 和 label polarity 都是强的，则当前 blocker 不是简单标签缺失，
而是模型可见 action-consequence contrast 或 delay-risk ordering 不足。后续仍必须保持
focused strict pair gate = 1.0、global/scale kNN/OOD 通过、precision/ROI/CI gate 不放松。

## Exactness Boundary

- `runs_bpc_or_pricing=false`；
- `selector_is_pricing_oracle=false`；
- `selector_can_certificate=false`；
- `gate_can_permanently_discard_negative_columns=false`；
- final optimality proof 仍只能来自当前 branch/cut/dual 下 exact pricing full closure。
