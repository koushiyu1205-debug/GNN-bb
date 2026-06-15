# GAT random-wave ord4 ROI 采样与 v8 训练报告

日期：2026-06-15

## 目标

本轮继续围绕 `GAT = trajectory impact embedding`、`kNN/OOD = safety shell` 的主线推进。

重点不是启用 production，也不是放开 certificate，而是回答一个具体问题：

`random-wave` 20-task 中，之前通过或延迟的负列候选，是否真的能带来 RMP / primal / tail ROI？

## 运行边界

- 5/10 no-regression 保持默认 mainline GAT/learning；
- 20-task worker 只在显式 opt-in target-priority 命令中启用；
- `max_workers=1`，避免并行放大内存；
- 所有 worker 只允许走普通 add-column path；
- 不产生 certificate；
- 不产生 official lower bound；
- DELAY_QUEUE 候选只被延迟，不被永久丢弃。

## HIGH_PRIORITY A/B

候选来源：

`BPC_future/results/gat_same_run_random_wave_ord4_high_candidates_task020_20260615/candidates.json`

候选数：2

两条候选均为：

- family: `random-wave`
- region: `tranquillitatis_balmer_like_20km`
- task_count: 20
- decision: `HIGH_PRIORITY`
- impact bucket: `new_support_changing`

执行目录：

`BPC_future/results/gat_same_run_random_wave_ord4_high_worker_ab_20260615`

审计结果：

`BPC_future/results/gat_same_run_random_wave_ord4_high_worker_ab_analysis_20260615/summary.json`

结论：

| 指标 | 数值 |
|---|---:|
| record_count | 2 |
| positive_primal_roi | 0 |
| negative_primal_roi | 2 |
| no_observed_roi | 0 |
| reachable target intervention | 2 |
| certificate effect | 0 |
| official bound effect | 0 |

两个 HIGH_PRIORITY 候选都在目标上下文真实触发，且 worker 返回 `FOUND_NEGATIVE`，但 worker 组 primal 都更差。

这说明：

`HIGH_PRIORITY + true-RC negative + new_support_changing` 仍然不等于有效 ROI。

## DELAY_QUEUE 分层 A/B

为了检查安全壳是否误压潜在正样本，从 DELAY_QUEUE 中抽取 2 条：

- Apollo: 最强负 RC，`rc=-42.2934852`
- Tranq: 最强负 RC，`rc=-3.14282`

候选文件：

`BPC_future/results/gat_same_run_random_wave_ord4_delay_stratified_candidates_20260615/candidates.json`

执行目录：

`BPC_future/results/gat_same_run_random_wave_ord4_delay_stratified_worker_ab_20260615`

审计结果：

`BPC_future/results/gat_same_run_random_wave_ord4_delay_stratified_worker_ab_analysis_20260615/summary.json`

结论：

| 指标 | 数值 |
|---|---:|
| record_count | 2 |
| positive_primal_roi | 0 |
| negative_primal_roi | 1 |
| no_observed_roi | 1 |
| reachable target intervention | 2 |
| certificate effect | 0 |
| official bound effect | 0 |

两条 DELAY 候选也都 target reachable，但没有正 ROI。

这说明本轮 DELAY_QUEUE 没有明显误杀正样本；至少在 ord4 random-wave 的这两个分层样本上，安全壳偏保守是合理的。

## 5/10 no-regression

DELAY 分层 runbook 的 5/10 结果：

| 规模 | region | status | elapsed |
|---:|---|---|---:|
| 5 | Apollo | OPTIMAL | 2.2825s |
| 5 | Tranq | OPTIMAL | 2.1653s |
| 10 | Apollo | OPTIMAL | 4.9299s |
| 10 | Tranq | OPTIMAL | 3.5170s |

当前没有观察到 5/10 退化。

## v8 ROI 数据集

组合数据集：

`BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v8_worker_roi_dataset_20260615`

摘要：

| 指标 | 数值 |
|---|---:|
| row_count | 45 |
| positive_primal_roi | 17 |
| negative_primal_roi | 11 |
| no_observed_roi | 15 |
| columns_only_roi | 2 |

按 family/region 的标签分布：

| family / region | positive | non-positive | unsupported |
|---|---:|---:|---:|
| greedy-anchor / Apollo | 4 | 4 | 0 |
| greedy-anchor / Tranq | 6 | 1 | 0 |
| random-wave / Apollo | 1 | 6 | 0 |
| random-wave / Tranq | 0 | 6 | 1 |
| sector-wave / Apollo | 3 | 4 | 1 |
| sector-wave / Tranq | 3 | 5 | 0 |

核心缺口仍然非常明确：

`random-wave / Tranq` 没有正 ROI 样本，`random-wave / Apollo` 只有 1 个正 ROI 样本。

## v8 图数据与 GAT 训练

图数据：

`BPC_future/results/gat_worker_roi_graph_dataset_v8_20260615`

训练：

`BPC_future/results/gat_worker_roi_training_v8_20260615`

结果：

| 指标 | 数值 |
|---|---:|
| graph sample_count | 43 |
| add labels | 17 |
| abstain labels | 26 |
| validation accuracy | 0.8182 |
| validation add precision | null |
| validation add recall | 0.0 |
| best validation loss | 0.5252 |

解释：

v8 GAT 变得非常保守，验证集上没有预测 add。这不是 production-ready 模型，但在当前样本稀疏、random-wave 正样本不足的阶段，比误放不稳定候选更安全。

## 为什么无效样本这么多

本轮进一步验证了前面的判断：

1. `rc < 0` 只是必要条件，不是有效条件；
2. `new_support_changing` 也不是充分条件；
3. very negative RC 也可能没有 primal / tail ROI；
4. 目标列即使 same-context reachable，也可能让 worker 组更差；
5. 真正有效样本必须通过 worker A/B 的 trajectory ROI 验证。

所以“无效样本多”不是采集失败，而是现在标签定义更严格：

有效正样本不是“负列”，而是“能改善 RMP/trajectory/tail 的负列”。

## 下一步建议

不要把 v8 GAT 用作 production gate。

下一步应继续采集 20-task hard-tail 的有效正样本，优先补：

1. `random-wave / Tranq` 正 ROI；
2. `random-wave / Apollo` 正 ROI；
3. 只用 same-context target causal match；
4. 继续保留 5/10 no-regression；
5. 继续禁止 certificate / official bound side effect。

更具体地说，下一轮应该换新的 random-wave ordinal 或 hard-tail context，而不是继续在 ord4 这批候选中硬挑。当前 ord4 的 HIGH 和 DELAY 分层样本已经给出了比较一致的负证据。

