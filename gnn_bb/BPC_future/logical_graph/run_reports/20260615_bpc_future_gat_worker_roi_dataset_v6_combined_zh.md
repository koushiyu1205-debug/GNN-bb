# GAT Worker ROI Dataset v6 Combined 报告

日期：2026-06-15

## 目的

合并 v5 ROI 数据集与本轮 20-task DELAY_QUEUE target-intervention 负/无改善样本。该数据集只用于离线 GAT ROI gate 训练，不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。

## 机器字段

```json
{
  "candidate_family_region_label_counts": {
    "greedy-anchor|apollo15_20km|0": 4,
    "greedy-anchor|apollo15_20km|1": 4,
    "greedy-anchor|tranquillitatis_balmer_like_20km|0": 1,
    "greedy-anchor|tranquillitatis_balmer_like_20km|1": 6,
    "random-wave|apollo15_20km|0": 5,
    "random-wave|apollo15_20km|1": 1,
    "random-wave|tranquillitatis_balmer_like_20km|0": 3,
    "sector-wave|apollo15_20km|0": 4,
    "sector-wave|apollo15_20km|1": 3,
    "sector-wave|tranquillitatis_balmer_like_20km|0": 5,
    "sector-wave|tranquillitatis_balmer_like_20km|1": 3
  },
  "certificate_ready": false,
  "jsonl_path": "BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v6_worker_roi_dataset_20260615/gat_worker_roi_rows.jsonl",
  "label_counts": {
    "0": 22,
    "1": 17
  },
  "negative_training_label_count": 22,
  "official_bound_effect": false,
  "positive_training_label_count": 17,
  "production_ready": false,
  "roi_class_counts": {
    "columns_only_roi": 2,
    "negative_primal_roi": 8,
    "no_observed_roi": 14,
    "positive_primal_roi": 17
  },
  "row_count": 41,
  "schema_version": "gat_worker_roi_dataset_combined_v6_summary",
  "source_jsonl_paths": [
    "BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v5_worker_roi_dataset_20260615/gat_worker_roi_rows.jsonl",
    "BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_roi_dataset_v6_only_20260615/gat_worker_roi_rows.jsonl"
  ],
  "training_row_count": 39
}
```
