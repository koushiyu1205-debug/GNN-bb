# GAT random-wave ord5 ROI 采样与 v9 数据更新报告

日期：2026-06-15

## 目标

上一轮 ord4 采样显示：

- `random-wave / Tranq` 正 ROI 为 0；
- HIGH_PRIORITY 和 DELAY_QUEUE 候选即使 target reachable，也多数没有 ROI；
- v8 GAT 因正样本不足而变得极保守。

本轮换到 `random-wave` ord5，继续采集 20-task hard-tail 的 same-context target ROI 标签。

## 安全边界

本轮仍保持：

- 不启用 production 默认；
- 不启用 certificate；
- 不产生 official lower bound；
- worker 只在显式 opt-in target-priority A/B 中启用；
- `max_workers=1`；
- DELAY_QUEUE 只表示延迟，不表示永久丢弃；
- GAT 只作为 trajectory-impact embedding，不是 pricing oracle。

## ord5 capture

runbook：

`BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615`

执行了前 8 步：

1. 5-task baseline/capture；
2. 10-task baseline/capture；
3. 20-task random-wave ord5 Apollo/Tranq baseline/capture；
4. same-run batch-impact rows；
5. same-run graph dataset。

结果摘要：

| 项目 | 数值 |
|---|---:|
| raw row_count | 14 |
| positive objective-improvement rows | 12 |
| non-improving rows | 2 |
| objective positive rate | 0.8571 |
| graph sample_count | 14 |
| graph candidate_count | 232 |
| graph add labels | 225 |
| graph abstain labels | 7 |

5/10 baseline 均为 `OPTIMAL`。

20-task baseline/capture 均为 `TIME_LIMIT`，适合 hard-tail 采样。

## ord5 same-run GAT + kNN/OOD

使用 ord5 局部 graph dataset 训练 audit-only GAT：

`BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/same_run_batch_impact_training`

该模型只用于本轮候选筛选，不具备 production 条件。

kNN/OOD 审计：

`BPC_future/results/gat_same_run_random_wave_ord5_capture_runbook_20260615/same_run_gat_knn_ood_audit`

结果：

| 指标 | 数值 |
|---|---:|
| decision records | 14 |
| predicted HIGH_PRIORITY | 6 |
| actual HIGH_PRIORITY | 12 |
| high priority precision | 1.0 |
| high priority recall | 0.5 |
| negative recall delay queue | 1.0 |

解释：

安全壳没有把 delay 样本误放为 high，但 recall 偏低，仍然保守。

## ord5 HIGH_PRIORITY target A/B

从 6 个 task20 HIGH_PRIORITY 中做最小分层 A/B：

- Apollo 1 条：`rc=-32.4695918`
- Tranq 1 条：`rc=-64.402114`

候选：

`BPC_future/results/gat_same_run_random_wave_ord5_high_stratified_candidates_20260615/candidates.json`

A/B 目录：

`BPC_future/results/gat_same_run_random_wave_ord5_high_stratified_worker_ab_20260615`

ROI 审计：

`BPC_future/results/gat_same_run_random_wave_ord5_high_stratified_worker_ab_analysis_20260615/summary.json`

reachability 审计：

`BPC_future/results/gat_same_run_random_wave_ord5_high_stratified_reachability_20260615/summary.json`

结果：

| region | rc | reachability | ROI |
|---|---:|---|---|
| Apollo | -32.4695918 | target reachable | negative_primal_roi |
| Tranq | -64.402114 | target reachable | positive_primal_roi |

Tranq 候选：

- baseline primal: `646.349246`
- worker primal: `641.659225`
- primal improvement: `4.690021`

这是当前最重要的新证据：`random-wave / Tranq` 终于获得一个 same-context target reachable 的正 ROI 样本。

Apollo 同批候选则是负 ROI，说明即使同 family、同 ordinal、同 HIGH_PRIORITY，region/context 差异仍然很强。

## v9 ROI 数据集

组合数据集：

`BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v9_worker_roi_dataset_20260615`

摘要：

| 指标 | 数值 |
|---|---:|
| row_count | 47 |
| positive_primal_roi | 18 |
| negative_primal_roi | 12 |
| no_observed_roi | 15 |
| columns_only_roi | 2 |

按 family/region：

| family / region | positive | non-positive | unsupported |
|---|---:|---:|---:|
| greedy-anchor / Apollo | 4 | 4 | 0 |
| greedy-anchor / Tranq | 6 | 1 | 0 |
| random-wave / Apollo | 1 | 7 | 0 |
| random-wave / Tranq | 1 | 6 | 1 |
| sector-wave / Apollo | 3 | 4 | 1 |
| sector-wave / Tranq | 3 | 5 | 0 |

random-wave 缺口仍然存在，但已经不再是完全没有正样本：

- `random-wave / Apollo`: 1 positive, 7 non-positive
- `random-wave / Tranq`: 1 positive, 6 non-positive, 1 unsupported

## v9 GAT 训练

图数据：

`BPC_future/results/gat_worker_roi_graph_dataset_v9_20260615`

训练：

`BPC_future/results/gat_worker_roi_training_v9_20260615`

结果：

| 指标 | 数值 |
|---|---:|
| graph sample_count | 45 |
| add labels | 18 |
| abstain labels | 27 |
| validation accuracy | 0.7273 |
| validation add recall | 0.0 |
| best validation loss | 0.5966 |

解释：

v9 仍然不是 production-ready。模型仍倾向于全部 abstain，说明单个新增正样本不足以让 GAT 稳定学到 `random-wave` 的可泛化正 ROI 区域。

## 当前判断

1. 正样本稀疏不是采集错误，而是定义更严格后暴露出来的真实现象；
2. `rc < 0`、`new_support_changing`、`HIGH_PRIORITY` 都不是充分条件；
3. ord5 证明 random-wave/tranq 确实存在正 ROI，但需要更多 ordinal/context 才能训练稳定；
4. 继续扩大 worker 时间或默认启用 worker都不合适；
5. 下一步应继续采 `random-wave` 新 ordinal 的 same-context target ROI，优先补 random-wave 两个 region 的正样本。

## 下一步

建议继续跑 `random-wave` ord6 或 ord7 的同样流程：

1. capture hard-tail context；
2. 本地 audit-only GAT + kNN/OOD；
3. 只抽少量 HIGH_PRIORITY 分层候选；
4. max_workers=1 做 target A/B；
5. 只把 target reachable 且 A/B 有 ROI 的样本作为正标签。

在此之前，v9 GAT 仍只能作为诊断模型，不能进入 production gate。

