# GAT Gap-Focused ROI 采样 v5 报告

日期：2026-06-15

## 目标

继续沿用 v4 的结论：有效 GAT 标签必须来自可达、因果匹配的 target intervention，而不是普通 `rc < 0`。

本轮只做一件事：

- 用 ordinal=3 的 gap-focused 采样补充 v4 中仍偏弱的 `random-wave / Apollo` 单元；
- 继续保持 5/10 no-regression；
- 不启用生产 GAT；
- 不让 GAT / worker / DELAY_QUEUE 参与 certificate 或 official lower bound。

## ordinal=3 capture

路径：

- `BPC_future/results/gat_same_run_gap_focused_ord3_capture_runbook_20260615`

选择：

- family：`greedy-anchor`, `random-wave`
- ordinal：`3`
- region：Apollo + Tranquillitatis
- 20-task 实例数：4
- `max_workers=1`

结果：

```text
5-task baseline/capture: 4/4 OPTIMAL
10-task baseline/capture: 4/4 OPTIMAL
20-task baseline/capture: 4/4 TIME_LIMIT / EXTERNAL_TIME_LIMIT
same-run impact rows: 35
graph candidates: 376
```

说明：

- 5/10 仍未观察到退化；
- 20-task 仍是 hard-tail；
- 本地 batch GAT 只用于生成同批 decision records，不用于生产。

## ordinal=3 候选

路径：

- `BPC_future/results/gat_same_run_gap_focused_ord3_impact_candidates_20260615`

结果：

```text
candidate_count = 1
candidate_family_region_counts = {"random-wave|apollo15_20km": 1}
candidate_impact_bucket_counts = {"new_support_changing": 1}
```

该候选为：

- true-RC negative；
- `new_support_changing`；
- target context 完整；
- 进入 worker A/B 前仍不是训练标签。

## ordinal=3 worker A/B

路径：

- runbook：`BPC_future/results/gat_same_run_gap_focused_ord3_worker_ab_20260615`
- reachability：`BPC_future/results/gat_same_run_gap_focused_ord3_worker_ab_20260615/target_intervention_reachability`
- ROI audit：`BPC_future/results/gat_same_run_gap_focused_ord3_worker_ab_analysis_20260615`

5/10 no-regression：

```text
5-task: 2/2 OPTIMAL
10-task: 2/2 OPTIMAL
```

Reachability：

```text
record_count = 1
reachable_target_intervention_count = 1
target_causal_match = 1 / 1
certificate_effect = false
official_bound_effect = false
```

ROI：

```text
roi_class_counts = {"no_observed_roi": 1}
```

单独 ROI audit 的 `all_checks_pass=false` 不是运行失败，而是因为单样本 runbook 没有同时包含正向与非正向证据。该样本并入 combined 数据集后可作为非正标签使用。

## v5 ROI 数据集

路径：

- `BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v5_worker_roi_dataset_20260615`

结果：

```text
row_count = 37
training_row_count = 35
positive_training_label_count = 17
negative_training_label_count = 18
roi_class_counts =
  positive_primal_roi: 17
  negative_primal_roi: 6
  no_observed_roi: 12
  columns_only_roi: 2
target_causal_match_count = 37
worker_context_match_count = 37
training_ready = true
production_ready = false
```

`columns_only_roi=2` 仍被排除，不作为训练标签。

## v5 Graph Dataset 与训练

Graph dataset：

- `BPC_future/results/gat_worker_roi_graph_dataset_v5_20260615`

```text
sample_count = 35
candidate_label_counts = {"add": 17, "abstain": 18}
family_count = 3
region_count = 2
production_ready = false
```

Audit-only GAT：

- `BPC_future/results/gat_worker_roi_training_v5_20260615/context_aware_worker_roi_gat_audit_only.pt`

```text
train_count = 25
validation_count = 10
train_accuracy = 0.8000
train_add_precision = 0.7333
train_add_recall = 0.9167
validation_accuracy = 0.8000
validation_add_precision = 0.7143
validation_add_recall = 1.0000
```

判断：

- v5 比 v4 多 1 个可达、因果匹配的非正样本；
- 验证集仍只有 10 个样本，不能生产启用；
- 当前 checkpoint 只能 audit-only。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m unittest \
BPC_future.tests.test_gat_same_run_target_priority_candidates \
BPC_future.tests.test_gat_target_priority_worker_ab_runbook \
BPC_future.tests.test_gat_target_priority_worker_ab_results \
BPC_future.tests.test_gat_worker_roi_dataset \
BPC_future.tests.test_gat_worker_roi_graph_dataset \
BPC_future.tests.test_gat_same_run_batch_impact_graph_dataset \
BPC_future.tests.test_gat_same_run_batch_impact_knn_ood
```

结果：

```text
Ran 23 tests in 0.139s
OK
```

语法检查：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python -m py_compile \
BPC_future/scripts/build_gat_same_run_target_priority_candidates.py \
BPC_future/tests/test_gat_same_run_target_priority_candidates.py
```

结果：通过。

`git diff --check`：通过。

## 当前判断

1. 正样本稀疏不是因为没有负列，而是因为“负列能改变 RMP 轨迹”的条件很苛刻；
2. `new_support_changing` 是比最负 RC 更好的采样优先级；
3. kNN/OOD 壳会显著减少 HIGH_PRIORITY 数量，但能避免把明显不安全样本直接加入；
4. `no_observed_roi` 样本也有价值，因为它告诉 GAT：即使目标可达且 true-RC negative，也可能对 trajectory 没帮助；
5. 当前仍不能生产启用，需要继续扩充 gap-focused target-intervention 样本。

## 下一步建议

继续补：

- `greedy-anchor / Tranquillitatis` 的非正样本；
- `random-wave / Tranquillitatis` 的正样本；
- `random-wave / Apollo` 的正样本。

优先方式：

- 不扩大生产 worker；
- 不默认启用 GAT；
- 继续用 gap-focused capture -> target candidate -> worker A/B -> reachability / ROI audit 的闭环；
- 每批保持 `max_workers=1`，避免内存风险。

