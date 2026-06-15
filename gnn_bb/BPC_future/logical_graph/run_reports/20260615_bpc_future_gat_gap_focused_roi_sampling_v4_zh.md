# GAT Gap-Focused ROI 采样与 v4 Audit-only 训练报告

日期：2026-06-15

## 目标

本轮目标是减少 GAT ROI 训练中的无效样本，而不是启用生产 GAT。

核心策略：

1. 不再只按最负 reduced cost 采样；
2. 优先采 `new_support_changing` / `new_task_set` 目标；
3. 按 family / region 标签缺口采样；
4. 所有候选必须经过 target reachability 与 ROI 审计后才可作为训练标签；
5. GAT 仍只作为 embedding / trajectory impact 表达，kNN/OOD 仍是安全壳；
6. 负列不允许永久丢弃，未通过安全壳只能进入 DELAY_QUEUE；
7. 任何 GAT / worker / DELAY_QUEUE 结果都不能参与 certificate 或 official lower bound。

## 代码改动

### `build_gat_same_run_target_priority_candidates.py`

新增：

- `instance_task_count`
- `instance_family`
- `instance_region`
- `instance_ordinal`
- `candidate_family_region_counts`
- `--include-families`
- `--include-regions`
- `--include-ordinals`

目的：

- 候选提取阶段可直接面向标签缺口采样；
- 避免继续过采已有 family / region；
- 报告能直接显示候选分布；
- 修正 `target_task_set_new` 重复字段。

### 测试

新增测试覆盖：

- candidate 元数据提取；
- family / region / ordinal 过滤；
- 非目标 family 不会混入 gap-focused 候选。

## 本轮采样

### Gap-focused capture runbook

路径：

- `BPC_future/results/gat_same_run_gap_focused_ord2_capture_runbook_20260615`

选择：

- family：`greedy-anchor`, `random-wave`
- ordinal：`2`
- region：Apollo + Tranquillitatis
- 20-task 实例数：4
- `max_workers=1`

5/10 no-regression：

- 5-task：4/4 `OPTIMAL`
- 10-task：4/4 `OPTIMAL`

20-task capture：

- 4/4 为 `TIME_LIMIT` / `EXTERNAL_TIME_LIMIT`
- 产生 same-run impact rows：26
- graph candidate 数：297
- 本地 audit-only GAT 用于该 gap dataset，不用于生产。

### Gap-focused 候选提取

路径：

- `BPC_future/results/gat_same_run_gap_focused_ord2_impact_candidates_20260615`

结果：

```text
candidate_count = 6
candidate_impact_bucket_counts = {"new_support_changing": 6}
candidate_family_region_counts =
  greedy-anchor|apollo15_20km: 2
  greedy-anchor|tranquillitatis_balmer_like_20km: 2
  random-wave|apollo15_20km: 1
  random-wave|tranquillitatis_balmer_like_20km: 1
```

这些候选均为 true-RC negative，且在进入训练标签前仍需 worker A/B。

## Worker A/B 审计

路径：

- runbook：`BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615`
- reachability：`BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_20260615/target_intervention_reachability`
- ROI audit：`BPC_future/results/gat_same_run_gap_focused_ord2_worker_ab_analysis_20260615`

5/10 no-regression：

- 5-task：2/2 `OPTIMAL`
- 10-task：2/2 `OPTIMAL`

Target reachability：

```text
record_count = 6
reachable_target_intervention_count = 6
target_causal_match = 6 / 6
certificate_effect = false
official_bound_effect = false
```

ROI：

```text
positive_primal_roi = 4
negative_primal_roi = 2
no_observed_roi = 0
columns_only_roi = 0
```

这批样本质量明显高于普通负列采样，因为 6/6 都是可达且因果匹配的目标干预样本。

## v4 ROI 数据集

路径：

- `BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v4_worker_roi_dataset_20260615`

结果：

```text
row_count = 36
training_row_count = 34
positive_training_label_count = 17
negative_training_label_count = 17
positive_family_count = 3
negative_family_count = 3
positive_region_count = 2
negative_region_count = 2
target_causal_match_count = 36
worker_context_match_count = 36
training_ready = true
production_ready = false
```

`columns_only_roi=2` 被排除，未作为训练标签。

## v4 Graph Dataset 与训练

Graph dataset：

- `BPC_future/results/gat_worker_roi_graph_dataset_v4_20260615`

```text
sample_count = 34
candidate_label_counts = {"add": 17, "abstain": 17}
family_count = 3
region_count = 2
production_ready = false
```

Audit-only GAT：

- `BPC_future/results/gat_worker_roi_training_v4_20260615/context_aware_worker_roi_gat_audit_only.pt`

```text
train_count = 24
validation_count = 10
train_accuracy = 0.7917
train_add_precision = 0.7333
train_add_recall = 0.9167
validation_accuracy = 0.7000
validation_add_precision = 0.6667
validation_add_recall = 0.8000
```

判断：

- v4 比 v3 样本分布更健康；
- 但 validation_count 仍只有 10，不能生产启用；
- 当前模型只能作为 audit-only checkpoint。

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
Ran 23 tests in 0.143s
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

## 当前结论

无效样本多的主要原因不是负列少，而是有效训练标签必须同时满足：

- true-RC negative；
- current-context 可达；
- target causal match；
- 非 replacement-like；
- 对后续 RMP / primal / dual 轨迹有可观察影响。

本轮证明：

- gap-focused + impact-ranking 采样能显著提高有效样本率；
- 6 个候选全部可达且因果匹配；
- 4 正 2 负，且没有 columns-only / no-observed；
- 这是比“按最负 RC 抓候选”更适合 GAT ROI 训练的采样方式。

## 当前边界

- v4 GAT 仍不是 production-ready；
- 不默认启用任何 GAT worker；
- 不允许 GAT 参与 certificate / official lower bound；
- 5/10 只作为 no-regression guard；
- 20-task 仍未达到 200 秒精确解目标；
- 下一步应继续补充 gap-focused target-intervention 样本，而不是扩大生产 worker。

