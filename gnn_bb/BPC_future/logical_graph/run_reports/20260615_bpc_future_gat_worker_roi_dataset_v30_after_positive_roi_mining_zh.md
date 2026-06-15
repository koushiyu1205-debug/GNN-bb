# GAT Worker ROI Dataset v30 合并报告

日期：2026-06-15

## 目标

将 v30 小批量 positive-mining worker A/B 标签合并进全局 ROI 数据集。标签仍只来自 paired worker A/B 后的 trajectory objective / retry 改善，不使用 rc、GAT 分数或 kNN/OOD 判定作为标签。

## 合并结果

| 指标 | 数量 |
|---|---:|
| 总行数 | 180 |
| 可训练行数 | 156 |
| 正 trajectory ROI | 51 |
| 负 trajectory ROI | 105 |
| 去重命中 | 0 |

## 判断

- 最小训练门槛 `training>=150`、`positive>=50`、`negative>=50`：通过；
- `production_ready=false`，`certificate_ready=false`；
- 下一步只能进入 GAT ROI 训练/审计，不允许默认启用。

## 输出

- JSONL：`BPC_future/results/gat_worker_roi_dataset_v30_after_positive_roi_mining_20260615/gat_worker_roi_rows.jsonl`
- CSV：`BPC_future/results/gat_worker_roi_dataset_v30_after_positive_roi_mining_20260615/gat_worker_roi_rows.csv`
- Summary：`BPC_future/results/gat_worker_roi_dataset_v30_after_positive_roi_mining_20260615/summary.json`
