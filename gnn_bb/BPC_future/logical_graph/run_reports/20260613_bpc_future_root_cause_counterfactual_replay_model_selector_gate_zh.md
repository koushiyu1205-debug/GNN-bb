# BPC_future 根因：Exact-context Replay Model Selector Gate 审计

日期：2026-06-13

## 目的

single-feature 和 pair-feature gate 都失败后，本轮继续检查更强一点的简单多特征模型：

- `nearest_centroid`
- `linear_mean_diff`
- `shallow_tree_depth3`

目标不是上线模型，而是回答：

> 当前 exact replay impact rows 是否已经足够支持一个简单 production selector？

结论：仍然不够。

## 数据范围

输入与前两轮 selector gate 一致：

```text
row_count = 207
label_counts = improved:147, noop:60
context_count = 22
instance_count = 4
impact_dataset_count = 4
```

只使用 addition-before 可见字段：

- `true_reduced_cost`
- `cost`
- `task_count`
- `vehicle_count`
- `new_task_set`
- `duplicate_signature`
- `active_support_changing`
- `strict_replacement_by_cost`
- `weak_replacement_or_duplicate`

排除后验字段：

- `single_objective_delta`
- `single_dual_l1_delta`
- `single_changed_journey_count`

## 结果摘要

### Context holdout

有模型能过 strict gate：

```text
passing_models = nearest_centroid, shallow_tree_depth3

nearest_centroid:
  precision = 0.7655172413793103
  recall = 0.7551020408163265

shallow_tree_depth3:
  precision = 0.7637362637362637
  recall = 0.9455782312925171
```

### Instance holdout

也有模型能过 strict gate：

```text
passing_models = nearest_centroid, shallow_tree_depth3

nearest_centroid:
  precision = 0.7986577181208053
  recall = 0.8095238095238095

shallow_tree_depth3:
  precision = 0.75
  recall = 1.0
```

### Dataset holdout

dataset holdout 仍然没有任何模型通过：

```text
passing_models = []

linear_mean_diff:
  precision = 0.6907216494845361
  recall = 0.9115646258503401

nearest_centroid:
  precision = 0.6907216494845361
  recall = 0.9115646258503401

shallow_tree_depth3:
  precision = 0.7101449275362319
  recall = 1.0
```

## 关键解释

这不是“完全没有 selector 信号”。

相反，context / instance holdout 里已经出现了能过最低 precision/recall gate 的简单模型。但 dataset holdout 仍然失败，说明当前信号对数据集分布敏感：在已见数据集内可以拟合，但跨 replay dataset / target source 后 false positives 仍过多。

这正是 production 风险：

- 如果只看 context / instance，会误以为 selector 已经可用；
- 一旦换到新的 capture source / replay dataset，precision 低于 `0.75`；
- 这会把 no-op / replacement negative candidates 当作 high-impact candidates 加入，继续污染 RMP trajectory。

## 审计结论

```text
context_models_have_passing_candidates = true
instance_models_have_passing_candidates = true
dataset_models_fail_strict_gate = true
no_model_passes_all_holdout_gates = true
all_checks_pass = true
```

所以当前状态仍是：

```text
has_stable_addition_before_selector = false
production_direction_proven = false
```

下一步如果继续 selector 路线，必须扩大 exact replay dataset 并引入更结构化的 batch / trajectory 特征。不能把当前 shallow tree 或 nearest-centroid 直接写进 solver。
