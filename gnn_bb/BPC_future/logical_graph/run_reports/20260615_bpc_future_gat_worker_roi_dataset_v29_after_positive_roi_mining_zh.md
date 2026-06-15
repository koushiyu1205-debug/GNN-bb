# GAT Worker ROI Dataset v29 合并报告

日期：2026-06-15

## 目标

本轮将 v28 全局 ROI 数据集与 v29 positive-mining worker A/B 数据集合并。标签口径保持不变：只使用 paired worker A/B 后的 trajectory ROI，判断候选列是否带来下一轮 objective / retry / tail 改善。`rc`、GAT 分数、kNN/OOD gate、HIGH_PRIORITY/DELAY_QUEUE 都不是标签。

## 合并结果

| 指标 | 数量 |
|---|---:|
| 总行数 | 172 |
| 可训练行数 | 148 |
| 正 trajectory ROI | 48 |
| 负 trajectory ROI | 100 |
| 去重命中 | 0 |

## v29 新增信号

- v29 worker A/B 单批提供 21 条可训练标签，其中 5 条正 ROI、16 条负 ROI；
- 合并后距离最小训练门槛还差：训练行 2 条，正 ROI 2 条；
- `production_ready=false`，`certificate_ready=false`，仍然不能默认启用。

## 标签边界

- 正标签：worker 目标候选通过真实 paired A/B 带来 objective 改善或 retry/tail 改善；
- 负标签：worker 没有改善，或导致 retry/trajectory 变差；
- `columns_only_roi` 不进入训练标签；
- 所有结果均为 diagnostic / audit-only，不影响 official bound 或 certificate。

## 输出

- JSONL：`BPC_future/results/gat_worker_roi_dataset_v29_after_positive_roi_mining_20260615/gat_worker_roi_rows.jsonl`
- CSV：`BPC_future/results/gat_worker_roi_dataset_v29_after_positive_roi_mining_20260615/gat_worker_roi_rows.csv`
- Summary：`BPC_future/results/gat_worker_roi_dataset_v29_after_positive_roi_mining_20260615/summary.json`
