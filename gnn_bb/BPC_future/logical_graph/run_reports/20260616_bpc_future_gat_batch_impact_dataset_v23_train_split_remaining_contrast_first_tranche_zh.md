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
sample_count = 375
candidate_count = 4678
context_match_rate = 1.0
batch_label_counts = {'non_improving': 101, 'roi_positive': 274}
candidate_label_counts = {'delay_queue': 384, 'high_priority': 4294}
batch_type_counts = {'new_task_set': 319, 'replacement_heavy': 56}
pairwise_context_stats = {'context_count': 295, 'multi_context_count': 16, 'same_context_pair_count': 286, 'largest_context_size': 10, 'sample_count': 375, 'same_context_comparable_pair_count': 268, 'roi_diverse_context_count': 16, 'positive_negative_label_pair_count': 88, 'by_family': {'greedy-anchor': {'sample_count': 54, 'context_count': 54, 'multi_context_count': 0, 'same_context_pair_count': 0, 'largest_context_size': 1}, 'random-wave': {'sample_count': 218, 'context_count': 190, 'multi_context_count': 5, 'same_context_pair_count': 109, 'largest_context_size': 10}, 'sector-wave': {'sample_count': 103, 'context_count': 51, 'multi_context_count': 11, 'same_context_pair_count': 177, 'largest_context_size': 10}}, 'by_task_count': {'5': {'sample_count': 2, 'context_count': 2, 'multi_context_count': 0, 'same_context_pair_count': 0, 'largest_context_size': 1}, '10': {'sample_count': 8, 'context_count': 8, 'multi_context_count': 0, 'same_context_pair_count': 0, 'largest_context_size': 1}, '20': {'sample_count': 192, 'context_count': 119, 'multi_context_count': 14, 'same_context_pair_count': 264, 'largest_context_size': 10}, '30': {'sample_count': 76, 'context_count': 76, 'multi_context_count': 0, 'same_context_pair_count': 0, 'largest_context_size': 1}, '50': {'sample_count': 96, 'context_count': 89, 'multi_context_count': 2, 'same_context_pair_count': 22, 'largest_context_size': 7}, '100': {'sample_count': 1, 'context_count': 1, 'multi_context_count': 0, 'same_context_pair_count': 0, 'largest_context_size': 1}}}
ranking_ready = true
ranking_blockers = []
family_counts = {'greedy-anchor': 54, 'random-wave': 218, 'sector-wave': 103}
task_count_counts = {'10': 8, '100': 1, '20': 192, '30': 76, '5': 2, '50': 96}
instance_count = 55
region_count = 2
training_ready = true
training_blockers = []
production_ready = false
default_enabled = false
all_checks_pass = true
```

## 标签语义

- `y_candidate_high_priority`：true-RC negative 且显式 longer-horizon ROI 为正，
  并且不是 `label_bad_mode_switch`；
- `y_candidate_delay_risk`：true-RC negative 但 ROI 非正、bad-mode，
  或缺少可证明改善 RMP trajectory 的 admission 标签；
- `y_batch_roi_positive` / `y_accepted_batch_roi`：batch-level longer-horizon ROI 标签；
- `y_bad_mode_switch`：候选列虽然 true-RC negative，但会增加 RMP / pricing / exact workload
  或触发拖尾的硬负标签；
- `y_delta_v` / `y_barrier_slack`：trajectory/CBF head 的离线监督目标；
- 所有标签都只允许训练 admission scheduling，不能作为 pricing certificate。

## Pairwise Ranking Readiness

`training_ready=true` 只表示可以做离线 diagnostic classification / regression；
`ranking_ready=true` 才表示同一 RMP context 下至少存在多个 batch 样本，
可以合法训练 pairwise ranking loss。没有 same-context batch pair 时，
不能跨 context 伪造 `score(high-ROI) > score(low-ROI)` 监督。
