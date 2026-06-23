# GAT Batch Impact Dataset 构建报告

日期：2026-06-18

## 目的

把 same-context intervention rows 转换成 `GATBatchImpactModel` 可直接读取的
batch-impact 图样本。该脚本只做离线数据转换，不运行 BPC / pricing / RMP / worker，
不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_batch_impact_dataset = current
status = gat_batch_impact_dataset_built
sample_count = 1064
candidate_count = 12100
context_match_rate = 1.0
batch_label_counts = {'non_improving': 320, 'roi_positive': 744}
candidate_label_counts = {'delay_queue': 1279, 'high_priority': 10821}
batch_type_counts = {'new_task_set': 870, 'replacement_heavy': 194}
pairwise_context_stats = {'context_count': 514, 'multi_context_count': 162, 'same_context_pair_count': 1793, 'largest_context_size': 18, 'sample_count': 1064, 'same_context_comparable_pair_count': 1316, 'roi_diverse_context_count': 83, 'positive_negative_label_pair_count': 569, 'by_family': {'greedy-anchor': {'sample_count': 321, 'context_count': 138, 'multi_context_count': 59, 'same_context_pair_count': 408, 'largest_context_size': 7}, 'random-wave': {'sample_count': 401, 'context_count': 264, 'multi_context_count': 34, 'same_context_pair_count': 449, 'largest_context_size': 13}, 'sector-wave': {'sample_count': 342, 'context_count': 112, 'multi_context_count': 69, 'same_context_pair_count': 936, 'largest_context_size': 18}}, 'by_task_count': {'5': {'sample_count': 32, 'context_count': 16, 'multi_context_count': 4, 'same_context_pair_count': 42, 'largest_context_size': 6}, '10': {'sample_count': 74, 'context_count': 35, 'multi_context_count': 11, 'same_context_pair_count': 93, 'largest_context_size': 6}, '20': {'sample_count': 668, 'context_count': 227, 'multi_context_count': 120, 'same_context_pair_count': 1574, 'largest_context_size': 18}, '30': {'sample_count': 168, 'context_count': 120, 'multi_context_count': 24, 'same_context_pair_count': 72, 'largest_context_size': 3}, '50': {'sample_count': 119, 'context_count': 114, 'multi_context_count': 2, 'same_context_pair_count': 11, 'largest_context_size': 5}, '100': {'sample_count': 3, 'context_count': 2, 'multi_context_count': 1, 'same_context_pair_count': 1, 'largest_context_size': 2}}}
ranking_ready = true
ranking_blockers = []
family_counts = {'greedy-anchor': 321, 'random-wave': 401, 'sector-wave': 342}
task_count_counts = {'10': 74, '100': 3, '20': 668, '30': 168, '5': 32, '50': 119}
instance_count = 126
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
