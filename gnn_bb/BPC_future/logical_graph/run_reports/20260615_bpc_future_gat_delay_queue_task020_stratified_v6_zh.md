# GAT DELAY_QUEUE 20-task 分层采样 v6 报告

日期：2026-06-15

## 目标

本轮目标是解释并减少“无效样本”来源：不再把 5/10 的容易闭合样本混入 20-task ROI 标签，而是只从 20-task DELAY_QUEUE true-RC negative 候选中抽样，做 same-context target intervention A/B。

所有实验仍为 audit-only / explicit opt-in：

- 不启用生产默认 worker；
- 不产生 certificate；
- 不产生 official lower bound；
- 不永久丢弃任何 `rc < 0` 候选；
- 5/10 只做 no-regression guard。

## 代码改动

`BPC_future/scripts/build_gat_same_run_target_priority_candidates.py` 增加：

- `--include-task-counts`
- `include_task_counts` summary 字段
- `candidate_task_count_counts` summary 字段
- `task_count_not_selected` skip 统计

对应测试：

- `BPC_future/tests/test_gat_same_run_target_priority_candidates.py`
- 覆盖同 family / region / ordinal 下混入 10-task 时，`include_task_counts=(20,)` 必须只保留 20-task。

## 20-task-only 候选抽取

从 ord2 / ord3 gap-focused decision records 中重抽 DELAY_QUEUE：

```text
ord2 task020 delay candidates = 8
ord3 task020 delay candidates = 8
candidate_task_count_counts = {"20": 8} for both
replacement_like = 0
```

分层挑选 4 个候选进入 A/B：

```text
random-wave | tranq  | ord2 | new_support_changing | rc=-0.006555667
random-wave | apollo | ord2 | new_support_changing | rc=-2.360002333
greedy-anchor | tranq | ord3 | new_support_changing | rc=-8.483300556
greedy-anchor | apollo | ord3 | new_support_changing | rc=-3.412270286
```

## 运行结果

Runbook：

```text
BPC_future/results/gat_same_run_delay_queue_task020_stratified_worker_ab_v6_20260615
```

顺序执行，`max_workers=1`。总耗时约 762 秒。

5/10 no-regression：

```text
task005 sector-wave apollo: OPTIMAL, ~2.15s
task005 sector-wave tranq: OPTIMAL, ~2.16s
task010 sector-wave apollo: OPTIMAL, ~4.95s
task010 sector-wave tranq: OPTIMAL, ~3.52s
```

20-task ROI：

```text
negative_primal_roi = 2
no_observed_roi = 2
positive_primal_roi = 0
official_bound_effect = false
certificate_effect = false
```

Reachability：

```text
target_intervention_reachable = 4 / 4
target_causal_match = 4 / 4
worker status at target context = FOUND_NEGATIVE for all 4
```

这说明这批不是“无效样本”，而是合法负类样本：候选确实同上下文触发、确实返回 true-RC negative，但短期 RMP / primal ROI 没有变好。

## 合并数据集

合并 v5 与本轮 v6-only 负类样本：

```text
BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v6_worker_roi_dataset_20260615
```

摘要：

```text
row_count = 41
training_row_count = 39
positive_training_label_count = 17
negative_training_label_count = 22
roi_class_counts = {
  "positive_primal_roi": 17,
  "negative_primal_roi": 8,
  "no_observed_roi": 14,
  "columns_only_roi": 2
}
```

Graph dataset：

```text
BPC_future/results/gat_worker_roi_graph_dataset_v6_20260615
sample_count = 39
candidate_label_counts = {"add": 17, "abstain": 22}
family_count = 3
region_count = 2
```

Audit-only GAT：

```text
BPC_future/results/gat_worker_roi_training_v6_20260615/context_aware_worker_roi_gat_audit_only.pt
validation_accuracy = 0.80
validation_add_precision = 0.75
validation_add_recall = 0.75
production_ready = false
```

## 判断

无效样本多的根因不是 true-RC negative 不够，而是：

1. `rc < 0` 不等于 RMP / primal / dual trajectory 有改善；
2. 5/10 太容易闭合，难以产生有效 ROI 标签；
3. DELAY_QUEUE 里有大量“看起来结构新、RC 也负，但短期轨迹无改善或变差”的候选；
4. 如果没有 same-context target intervention 审计，很容易把这些候选误标成好样本。

本轮新增证据说明：

- 20-task-only 过滤是必要的；
- DELAY_QUEUE 可以提供高质量负类样本；
- “new_support_changing + true-RC negative” 仍不足以作为正样本；
- GAT 标签必须继续以 reachable target causal match + observed ROI 为准。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_gat_same_run_target_priority_candidates \
BPC_future.tests.test_gat_target_priority_worker_ab_runbook \
BPC_future.tests.test_gat_target_priority_worker_ab_results \
BPC_future.tests.test_gat_target_intervention_reachability \
BPC_future.tests.test_gat_worker_roi_dataset \
BPC_future.tests.test_gat_worker_roi_graph_dataset \
BPC_future.tests.test_gat_same_run_batch_impact_graph_dataset \
BPC_future.tests.test_gat_same_run_batch_impact_knn_ood
```

结果：

```text
Ran 28 tests in 0.245s
OK
```

语法与 whitespace：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/build_gat_same_run_target_priority_candidates.py \
BPC_future/tests/test_gat_same_run_target_priority_candidates.py \
BPC_future/scripts/build_gat_worker_roi_graph_dataset.py \
BPC_future/scripts/train_gnn_column_selector.py

git diff --check -- \
BPC_future/scripts/build_gat_same_run_target_priority_candidates.py \
BPC_future/tests/test_gat_same_run_target_priority_candidates.py
```

结果：通过。

## 下一步

继续采有效正样本，不扩大生产开关：

1. 只从 20-task hard-tail same-context 候选采样；
2. 优先补 `random-wave/tranq` 正样本和 `greedy-anchor/tranq` 负样本；
3. 继续保留 5/10 no-regression guard；
4. GAT v6 只作为 audit-only checkpoint，不进入 production；
5. 不通过 kNN/OOD 的 true-RC negative 仍进入 DELAY_QUEUE，不能永久丢弃。
