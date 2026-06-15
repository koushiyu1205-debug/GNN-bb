# GAT random-wave ord6 ROI 采样与 v10 数据更新报告

日期：2026-06-15

## 目标

延续 ord5 的流程，继续采集 `random-wave` 20-task hard-tail 的 same-context target ROI 标签。

核心目标不是启用 worker，也不是让 GAT 生产化，而是补充 `random-wave` family 的有效正/负样本，避免 GAT 标签歪。

## 安全边界

本轮保持：

- `max_workers=1`；
- 5/10 no-regression 必跑；
- 20-task worker 只在 explicit target-priority A/B 中启用；
- 不启用 production 默认；
- 不产生 certificate；
- 不产生 official lower bound；
- GAT 只作为 trajectory-impact embedding；
- kNN/OOD 只作为安全壳；
- DELAY_QUEUE 只表示延迟，不表示永久丢弃。

## ord6 capture

runbook：

`BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615`

结果：

| 指标 | 数值 |
|---|---:|
| raw row_count | 10 |
| positive objective-improvement rows | 7 |
| non-improving rows | 3 |
| objective positive rate | 0.7000 |
| graph sample_count | 10 |
| graph candidate_count | 99 |
| graph add labels | 86 |
| graph abstain labels | 13 |

5/10 baseline 均为 `OPTIMAL`。

20-task baseline/capture：

| instance | status | primal |
|---|---|---:|
| random-wave Apollo ord6 | TIME_LIMIT | 615.605876 |
| random-wave Tranq ord6 | TIME_LIMIT | 675.557123 |

## ord6 same-run GAT + kNN/OOD

本地 audit-only GAT：

`BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615/same_run_batch_impact_training`

kNN/OOD：

`BPC_future/results/gat_same_run_random_wave_ord6_capture_runbook_20260615/same_run_gat_knn_ood_audit`

结果：

| 指标 | 数值 |
|---|---:|
| decision records | 10 |
| predicted HIGH_PRIORITY | 4 |
| actual HIGH_PRIORITY | 7 |
| high priority precision | 1.0 |
| high priority recall | 0.5714 |
| negative recall delay queue | 1.0 |

安全壳没有误放 delay 样本，但仍偏保守。

## ord6 HIGH_PRIORITY target A/B

从 3 个 task20 HIGH_PRIORITY 中做最小分层 A/B：

- Apollo 1 条；
- Tranq 1 条。

候选：

`BPC_future/results/gat_same_run_random_wave_ord6_high_stratified_candidates_20260615/candidates.json`

A/B：

`BPC_future/results/gat_same_run_random_wave_ord6_high_stratified_worker_ab_20260615`

审计：

`BPC_future/results/gat_same_run_random_wave_ord6_high_stratified_worker_ab_analysis_20260615/summary.json`

reachability：

`BPC_future/results/gat_same_run_random_wave_ord6_high_stratified_reachability_20260615/summary.json`

结果：

| region | rc | reachability | ROI |
|---|---:|---|---|
| Apollo | -1.895862 | target reachable | columns_only_roi |
| Tranq | -4.779376333 | target reachable | no_observed_roi |

两条候选都在目标上下文真实触发并返回 `FOUND_NEGATIVE`，但没有正 primal ROI。

## v10 ROI 数据集

组合数据集：

`BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v10_worker_roi_dataset_20260615`

摘要：

| 指标 | 数值 |
|---|---:|
| row_count | 49 |
| positive_primal_roi | 18 |
| negative_primal_roi | 12 |
| no_observed_roi | 16 |
| columns_only_roi | 3 |

按 family/region：

| family / region | positive | non-positive | unsupported |
|---|---:|---:|---:|
| greedy-anchor / Apollo | 4 | 4 | 0 |
| greedy-anchor / Tranq | 6 | 1 | 0 |
| random-wave / Apollo | 1 | 7 | 1 |
| random-wave / Tranq | 1 | 7 | 1 |
| sector-wave / Apollo | 3 | 4 | 1 |
| sector-wave / Tranq | 3 | 5 | 0 |

ord6 没有新增正 ROI，但补充了 random-wave 的非正证据。

## v10 GAT 训练

图数据：

`BPC_future/results/gat_worker_roi_graph_dataset_v10_20260615`

训练：

`BPC_future/results/gat_worker_roi_training_v10_20260615`

结果：

| 指标 | 数值 |
|---|---:|
| graph sample_count | 46 |
| add labels | 18 |
| abstain labels | 28 |
| validation accuracy | 0.7500 |
| validation add recall | 0.0 |
| best validation loss | 0.5678 |

v10 仍然不是 production-ready。模型继续偏向 abstain，说明当前正 ROI 覆盖仍不够。

## 当前判断

ord6 说明：

1. random-wave 仍有大量 true-RC negative / HIGH_PRIORITY 候选没有直接 ROI；
2. target reachable 不等于有 primal improvement；
3. `columns_only_roi` 应继续排除出训练标签；
4. 当前 GAT 的生产化短板仍是正样本覆盖不足，尤其 random-wave 两个 region 都只有 1 个正 ROI；
5. 继续采样应该换新 ordinal，而不是扩大 ord6 的 worker 时间。

## 下一步

继续采 `random-wave` ord7 或 ord8：

1. capture hard-tail context；
2. 本地 audit-only GAT + kNN/OOD；
3. 每个 region 只抽 1 条 HIGH_PRIORITY 做 target A/B；
4. 只把 target reachable 且 A/B 正 ROI 的样本作为正标签；
5. 保持 5/10 no-regression 与无 certificate/official-bound side effect。

