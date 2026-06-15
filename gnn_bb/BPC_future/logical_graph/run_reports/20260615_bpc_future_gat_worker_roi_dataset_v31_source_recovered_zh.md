# GAT Worker ROI Dataset v31 Source Recovered 报告

日期：2026-06-15

## 目的

恢复 v30 全局 ROI 数据集中缺失的 `source_file`，用于构建 GAT 图样本。恢复只补 capture provenance，不修改 ROI 标签。

## 结果

| 指标 | 数量 |
|---|---:|
| 总行数 | 180 |
| 可训练行数 | 156 |
| 正 trajectory ROI | 51 |
| 负 trajectory ROI | 105 |
| source_file recovered | 38 |
| source_file unrecovered | 0 |

## 边界

- 标签仍只来自 paired worker A/B 的 trajectory ROI；
- 恢复 `source_file` 只用于图构建，不改变 label；
- `production_ready=false`，`certificate_ready=false`。

## 输出

- JSONL：`BPC_future/results/gat_worker_roi_dataset_v31_source_recovered_20260615/gat_worker_roi_rows.jsonl`
- CSV：`BPC_future/results/gat_worker_roi_dataset_v31_source_recovered_20260615/gat_worker_roi_rows.csv`
- Summary：`BPC_future/results/gat_worker_roi_dataset_v31_source_recovered_20260615/summary.json`
