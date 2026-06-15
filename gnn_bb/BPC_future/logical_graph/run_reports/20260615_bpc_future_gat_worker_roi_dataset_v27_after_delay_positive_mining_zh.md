# GAT Worker ROI Dataset v27 合并报告

日期：2026-06-15

## 标签原则

- 训练目标是候选列对后续 RMP trajectory objective / retry / pricing tail 的 ROI。
- `rc`、GAT 分数、kNN/OOD 决策、same-run improvement 都不是最终训练标签。
- 只有 worker A/B audit 后的 `positive_*_roi` / `negative_*_roi` / `no_observed_roi` 进入主标签。
- `columns_only_roi` 不进入主训练标签。

## 机器字段

```json
{
  "cell_counts": {
    "(20, 'greedy-anchor', 'apollo15_20km')": {
      "negative": 15,
      "positive": 10,
      "positive_rate": 0.4,
      "total": 25
    },
    "(20, 'greedy-anchor', 'tranquillitatis_balmer_like_20km')": {
      "negative": 14,
      "positive": 8,
      "positive_rate": 0.36363636363636365,
      "total": 22
    },
    "(20, 'random-wave', 'apollo15_20km')": {
      "negative": 11,
      "positive": 1,
      "positive_rate": 0.08333333333333333,
      "total": 12
    },
    "(20, 'random-wave', 'tranquillitatis_balmer_like_20km')": {
      "negative": 15,
      "positive": 1,
      "positive_rate": 0.0625,
      "total": 16
    },
    "(20, 'sector-wave', 'apollo15_20km')": {
      "negative": 13,
      "positive": 6,
      "positive_rate": 0.3157894736842105,
      "total": 19
    },
    "(20, 'sector-wave', 'tranquillitatis_balmer_like_20km')": {
      "negative": 8,
      "positive": 9,
      "positive_rate": 0.5294117647058824,
      "total": 17
    }
  },
  "certificate_ready": false,
  "jsonl_path": "BPC_future/results/gat_worker_roi_dataset_v27_after_delay_positive_mining_20260615/gat_worker_roi_rows.jsonl",
  "label_counts": {
    "0": 76,
    "1": 35
  },
  "negative_trajectory_roi_count": 76,
  "positive_trajectory_roi_count": 35,
  "production_ready": false,
  "roi_class_counts": {
    "columns_only_roi": 9,
    "negative_primal_roi": 27,
    "negative_retry_roi": 22,
    "no_observed_roi": 40,
    "positive_primal_roi": 31,
    "positive_retry_roi": 5
  },
  "row_count": 134,
  "sample_gap": {
    "positive_to_50": 15,
    "training_rows_to_150": 39
  },
  "sample_target": {
    "positive_min": 50,
    "positive_target": 80,
    "total_min": 150,
    "total_target": 200
  },
  "schema_version": "gat_worker_roi_all_unique_trajectory_v27",
  "source_file_count": 2,
  "source_files": [
    "BPC_future/results/gat_worker_roi_dataset_v26_after_parallel4_20260615/gat_worker_roi_rows.jsonl",
    "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/worker_roi_dataset/gat_worker_roi_rows.jsonl"
  ],
  "source_row_counts": {
    "BPC_future/results/gat_delay_positive_mining_worker_ab_top8_20260615/worker_roi_dataset/gat_worker_roi_rows.jsonl": 8,
    "BPC_future/results/gat_worker_roi_dataset_v26_after_parallel4_20260615/gat_worker_roi_rows.jsonl": 126
  },
  "task_count_distribution": {
    "20": 111
  },
  "training_row_count": 111
}
```

## 结论

- 合并后可训练样本 111 条，其中正 ROI 35 条、负 ROI 76 条。
- 距离最低采样线还缺正 ROI 15 条、总训练样本 39 条。
- 当前仍是 audit/training 数据准备阶段，不可 production 默认启用，也不可参与证书。
