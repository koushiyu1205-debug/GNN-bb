# GAT Worker ROI Dataset v28 合并报告

日期：2026-06-15

## 标签原则

- 训练目标是候选列对后续 RMP trajectory objective / retry / pricing tail 的 ROI。
- `rc`、GAT 分数、kNN/OOD 决策、same-run improvement 都不是最终训练标签。
- 只有 worker A/B audit 后的 `positive_*_roi` / `negative_*_roi` / `no_observed_roi` 进入主标签。
- 负列不能被永久丢弃；GAT/kNN 只控制优先级和延迟。

## 机器字段

```json
{
  "cell_counts": {
    "(20, 'greedy-anchor', 'apollo15_20km')": {
      "negative": 15,
      "positive": 14,
      "positive_rate": 0.4827586206896552,
      "total": 29
    },
    "(20, 'greedy-anchor', 'tranquillitatis_balmer_like_20km')": {
      "negative": 17,
      "positive": 9,
      "positive_rate": 0.34615384615384615,
      "total": 26
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
      "negative": 16,
      "positive": 7,
      "positive_rate": 0.30434782608695654,
      "total": 23
    },
    "(20, 'sector-wave', 'tranquillitatis_balmer_like_20km')": {
      "negative": 10,
      "positive": 11,
      "positive_rate": 0.5238095238095238,
      "total": 21
    }
  },
  "certificate_ready": false,
  "jsonl_path": "BPC_future/results/gat_worker_roi_dataset_v28_after_positive_roi_mining_20260615/gat_worker_roi_rows.jsonl",
  "label_counts": {
    "0": 84,
    "1": 43
  },
  "negative_trajectory_roi_count": 84,
  "positive_trajectory_roi_count": 43,
  "production_ready": false,
  "roi_class_counts": {
    "columns_only_roi": 9,
    "negative_primal_roi": 30,
    "negative_retry_roi": 26,
    "no_observed_roi": 41,
    "positive_primal_roi": 38,
    "positive_retry_roi": 6
  },
  "row_count": 150,
  "sample_gap": {
    "positive_to_50": 7,
    "training_rows_to_150": 23
  },
  "sample_target": {
    "positive_min": 50,
    "positive_target": 80,
    "total_min": 150,
    "total_target": 200
  },
  "schema_version": "gat_worker_roi_all_unique_trajectory_v28",
  "source_file_count": 2,
  "source_files": [
    "BPC_future/results/gat_worker_roi_dataset_v27_after_delay_positive_mining_20260615/gat_worker_roi_rows.jsonl",
    "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/worker_roi_dataset/gat_worker_roi_rows.jsonl"
  ],
  "source_row_counts": {
    "BPC_future/results/gat_positive_roi_mining_worker_ab_v28_20260615/worker_roi_dataset/gat_worker_roi_rows.jsonl": 16,
    "BPC_future/results/gat_worker_roi_dataset_v27_after_delay_positive_mining_20260615/gat_worker_roi_rows.jsonl": 134
  },
  "task_count_distribution": {
    "20": 127
  },
  "training_row_count": 127
}
```

## 结论

- 合并后可训练样本 127 条，其中正 ROI 43 条、负 ROI 84 条。
- 距离最低采样线还缺正 ROI 7 条、总训练样本 23 条。
- 当前仍是 audit/training 数据准备阶段，不可 production 默认启用，也不可参与证书。
