# GAT Worker ROI Graph Dataset 报告

日期：2026-06-15

## 目的

把 same-context target-intervention ROI rows 转换为现有 GAT
`ContextAwareColumnSelector` 可训练的图样本。该数据只用于离线 ROI gate
校准，不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_worker_roi_graph_dataset = current
status = gat_worker_roi_graph_dataset_built
sample_count = 156
candidate_count = 156
candidate_label_counts = {'abstain': 105, 'add': 51}
roi_class_counts = {'negative_primal_roi': 34, 'negative_retry_roi': 39, 'no_observed_roi': 32, 'positive_primal_roi': 42, 'positive_retry_roi': 9}
delay_queue_label_count = 105
instance_count = 52
family_count = 3
region_count = 2
skipped_counts = {'not_training_eligible:no_worker_target_intervention_observed': 10, 'not_training_eligible:positive_roi_without_target_causal_match': 1, 'not_training_eligible:unsupported_roi_class:columns_only_roi': 10, 'not_training_eligible:worker_context_mismatch': 3}
has_high_priority_and_delay_labels = true
production_ready = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## 标签语义

- `add`：同 context target intervention 后出现 positive primal ROI，作为 HIGH_PRIORITY；
- `abstain`：同 context target intervention 后 no/negative primal ROI，进入 DELAY_QUEUE；
- `skip`：仅保留给非负 reduced-cost 候选，本数据集不使用，不能用于永久丢弃负列。
