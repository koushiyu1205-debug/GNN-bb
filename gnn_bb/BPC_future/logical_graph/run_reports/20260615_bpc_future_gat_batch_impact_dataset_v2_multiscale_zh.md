# GAT Batch Impact Dataset 构建报告

日期：2026-06-15

## 目的

把 same-context intervention rows 转换成 `GATBatchImpactModel` 可直接读取的
batch-impact 图样本。该脚本只做离线数据转换，不运行 BPC / pricing / RMP / worker，
不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_batch_impact_dataset = current
status = gat_batch_impact_dataset_built
sample_count = 294
candidate_count = 4569
context_match_rate = 1.0
batch_label_counts = {'non_improving': 63, 'roi_positive': 231}
candidate_label_counts = {'delay_queue': 318, 'high_priority': 4251}
batch_type_counts = {'new_task_set': 254, 'replacement_heavy': 40}
family_counts = {'greedy-anchor': 54, 'random-wave': 190, 'sector-wave': 50}
task_count_counts = {'10': 8, '100': 1, '20': 118, '30': 76, '5': 2, '50': 89}
instance_count = 54
region_count = 2
training_ready = true
training_blockers = []
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
