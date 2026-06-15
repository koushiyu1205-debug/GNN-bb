# GAT Worker ROI Graph Dataset Merge 报告

日期：2026-06-15

## 目的

合并离线 GAT worker-ROI 图数据集。该流程只复制已有样本，不运行 BPC / pricing / RMP / worker，也不产生 certificate 或 official lower bound。

## 机器字段

```text
gat_worker_roi_graph_dataset_merge = current
status = gat_worker_roi_graph_datasets_merged
sample_count = 205
candidate_label_counts = {'abstain': 145, 'add': 60}
roi_class_counts = {'negative_exact_roi': 5, 'negative_primal_roi': 39, 'negative_retry_roi': 60, 'negative_walltime_roi': 1, 'no_observed_roi': 38, 'positive_exact_roi': 1, 'positive_pricing_roi': 1, 'positive_primal_roi': 46, 'positive_retry_roi': 14}
delay_queue_label_count = 145
source_datasets = ['BPC_future/data/gat_worker_roi/v34_after_v33_sampling_20260615', 'BPC_future/data/gat_worker_roi/post_injection_batch_k4_hard_negative_v1']
skipped_counts = {}
production_ready = false
certificate_ready = false
all_checks_pass = true
```

## 结论

- 合并数据仍为离线诊断数据；
- `abstain` 表示 DELAY_QUEUE，不是永久丢弃；
- 该合并不改变默认求解路径和证书逻辑。
