# GAT Same-Run Batch Impact Graph Dataset 报告

日期：2026-06-15

## 目的

把 same-run batch-impact rows 转换为 GAT `ContextAwareColumnSelector`
可读取的图样本。该数据只用于离线 trajectory-impact 诊断训练，不运行
BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_same_run_batch_impact_graph_dataset = current
status = gat_same_run_batch_impact_graph_dataset_built
sample_count = 68
candidate_count = 1410
batch_label_counts = {'non_improving': 12, 'objective_improved': 56}
candidate_label_counts = {'abstain': 91, 'add': 1319}
delay_queue_label_count = 91
instance_count = 20
region_count = 2
has_high_priority_and_delay_labels = true
production_ready = false
certificate_ready = false
official_bound_effect = false
all_checks_pass = true
```

## 标签语义

- `add`：true-RC negative 且该 batch 真实加入后 RMP objective 改善，作为 HIGH_PRIORITY；
- `abstain`：true-RC negative 但该 batch 加入后 objective 未改善，进入 DELAY_QUEUE；
- `skip`：仅允许用于非负 reduced-cost 候选，不能用于永久丢弃负列。
