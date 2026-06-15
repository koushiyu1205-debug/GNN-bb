# GAT Bulk Sampling v14 Multiscale 执行报告

日期：2026-06-15

## 目标

本轮目标是回答一个具体问题：

能否用批量采样把 GAT / CBF gate 的 same-run impact 样本从少量手工样本扩到可训练规模，同时保持：

- 5/10 默认求解不退化；
- GAT 只做 embedding / trajectory-impact 表达；
- kNN/OOD 只做安全壳；
- 负列不被永久丢弃；
- 不产生 certificate / official lower-bound side effect；
- 不默认启用 worker / probe。

## 采样执行

使用 runbook：

`BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/summary.json`

本轮顺序执行了 v14 multiscale capture waves，`max_workers=1`，覆盖 30/50/100 的 random-wave Apollo / Tranquillitatis 实例。采样日志：

`BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/sequential_execution_log_waves02_13.jsonl`

所有 wave 返回码均为 0。多数 50/100 实例达到 200 秒外部上限，这是预期的 hard-tail 采样行为，不代表采样框架失败。

## 样本结果

v14 单独 row build：

- row_count: 166
- positive_objective_improvement_count: 134
- non_improving_objective_count: 32
- instance_count: 18
- instance_region_count: 2
- production_ready: false

合并 v13 + v14 same-run rows 后：

- sample_count: 294
- objective_improved: 231
- non_improving: 63
- candidate_count: 4569
- candidate add: 4251
- candidate abstain / delay: 318

结论：总样本量已经达到 250-300 的目标区间，正样本数量也超过 80-100 的下限。但标签仍偏正，delay / non-improving 样本只有约 21.4%，生产化前还需要继续补边界样本。

## Combined GAT 训练

训练输入：

`BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_graph_dataset`

训练输出：

`BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_same_run_batch_impact_training/context_aware_bulk_sampling_gat.pt`

训练摘要：

- sample_count: 294
- validation accuracy: 0.9577
- validation add precision: 0.9683
- validation add recall: 0.9884

但 validation confusion 显示 delay/abstain 仍被 GAT 单模型明显误判为 add：49 个 abstain 中 39 个被预测成 add。因此 GAT 不能单独作为 gate，必须继续套 kNN/OOD 安全壳。

## kNN/OOD 安全审计

审计输出：

`BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_same_run_gat_knn_ood_audit/summary.json`

全量 decision-scope：

- predicted_high_priority: 134
- actual_high_priority: 231
- actual_delay_queue: 63
- high_priority_precision: 1.0
- high_priority_recall: 0.5801
- fp_high_priority_on_delay: 0
- negative_recall_delay_queue: 1.0
- validation_safety_ready: true
- production_ready: false

解释：安全壳把所有 delay 样本拦住了，没有把 delay 错放到 HIGH_PRIORITY；代价是保守，约 42% 的实际 high priority 被延迟。这符合当前策略：宁可 delay，不永久 discard，也不让 gate 破坏 completeness。

## 候选抽取

HIGH_PRIORITY candidates：

`BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_target_priority_candidates/candidates.json`

- candidate_count: 32
- new_support_changing: 29
- new_task_set: 3
- task20: 31
- task10: 1

DELAY_QUEUE candidates：

`BPC_future/results/gat_bulk_sampling_runbook_v14_multiscale_20260615/combined_delay_queue_target_candidates/candidates.json`

- candidate_count: 32
- new_support_changing: 24
- new_task_set: 4
- support_changing: 4
- task20: 23
- task10: 7
- task5: 2

所有候选仍是 diagnostic-only，不能参与 certificate，也不能默认接入 production worker。

## 当前判断

批量采样是可行的，并且已经把 same-run impact 样本扩到可训练规模：

- 总样本已经够第一版训练；
- 正样本已经够；
- delay / non-improving 仍偏少，是下一轮采样重点；
- GAT 单模型偏向 add，不能单独使用；
- GAT + kNN/OOD 安全壳当前可用于 audit-only 和小规模 target intervention A/B；
- 仍不具备 production_ready 条件。

## 下一步建议

1. 不要默认启用 GAT / worker。
2. 用 32 条 HIGH_PRIORITY 和 32 条 DELAY_QUEUE 做小规模 target intervention A/B。
3. 采样继续偏向 hard-tail / boundary / delay-producing contexts，而不是继续堆 positive。
4. 继续保持规则：HIGH_PRIORITY 只是优先级，DELAY_QUEUE 是延迟队列，负列不能永久丢弃。

