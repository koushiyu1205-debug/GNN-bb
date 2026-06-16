# GAT Batch Impact Dataset 构建报告

日期：2026-06-16

## 目的

把 same-context intervention rows 转换成 `GATBatchImpactModel` 可直接读取的
batch-impact 图样本。该脚本只做离线数据转换，不运行 BPC / pricing / RMP / worker，
不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_batch_impact_dataset = current
status = gat_batch_impact_dataset_built
sample_count = 2
candidate_count = 2
context_match_rate = 1.0
batch_label_counts = {'non_improving': 1, 'roi_positive': 1}
candidate_label_counts = {'delay_queue': 1, 'high_priority': 1}
batch_type_counts = {'new_task_set': 1, 'replacement_heavy': 1}
pairwise_context_stats = {'context_count': 1, 'multi_context_count': 1, 'same_context_pair_count': 1, 'largest_context_size': 2, 'sample_count': 2, 'same_context_comparable_pair_count': 1, 'roi_diverse_context_count': 1, 'positive_negative_label_pair_count': 1, 'by_family': {'sector-wave': {'sample_count': 2, 'context_count': 1, 'multi_context_count': 1, 'same_context_pair_count': 1, 'largest_context_size': 2}}, 'by_task_count': {'20': {'sample_count': 2, 'context_count': 1, 'multi_context_count': 1, 'same_context_pair_count': 1, 'largest_context_size': 2}}}
ranking_ready = true
ranking_blockers = []
family_counts = {'sector-wave': 2}
task_count_counts = {'20': 2}
instance_count = 1
region_count = 1
training_ready = false
training_blockers = ['need_more_instances_for_holdout', 'need_more_regions_for_holdout']
production_ready = false
default_enabled = false
all_checks_pass = true
```

## 标签语义

- `y_candidate_high_priority`：true-RC negative 且 same-context 加入后 objective 改善；
- `y_candidate_delay_risk`：true-RC negative 但 same-context 加入后 objective 未改善；
- `y_batch_roi_positive` / `y_accepted_batch_roi`：batch-level ROI 标签；
- `y_delta_v` / `y_barrier_slack`：trajectory/CBF head 的离线监督占位；
- 所有标签都只允许训练 admission scheduling，不能作为 pricing certificate。

## Pairwise Ranking Readiness

`training_ready=true` 只表示可以做离线 diagnostic classification / regression；
`ranking_ready=true` 才表示同一 RMP context 下至少存在多个 batch 样本，
可以合法训练 pairwise ranking loss。没有 same-context batch pair 时，
不能跨 context 伪造 `score(high-ROI) > score(low-ROI)` 监督。
