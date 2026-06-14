# Production Selector Blocker Catalog 报告

日期：2026-06-14

## 目的

本报告汇总 selector 为什么还不能进入 production BPC A/B。它只读已有
exact-context replay 和 selector audit 结果，不改变 solver。

## 机器字段

```text
production_selector_blocker_catalog = current
production_selector_status = production_selector_not_validated
selector_feature_scope = addition_before_only
required_selector_holdouts = context / instance / dataset
all_checks_pass = true
```

## 阻塞点

### 1. 具体 false positive / false negative 反例仍存在

```text
false_positive_count = 22
false_negative_count = 31
false_positive_new_task_set_noop_count = 21
false_negative_new_task_set_improved_count = 23
```

### 2. micro-average 通过不等于每个 fold 通过

```text
micro_passing_features = ['true_reduced_cost', 'cost', 'new_task_set', 'strict_replacement_by_cost']
robust_all_fold_passing_features = []
```

### 3. 简单模型 aggregate 有信号，但没有 robust all-fold 模型

```text
aggregate_all_holdout_models = ['nearest_centroid', 'shallow_tree_depth3']
robust_all_fold_passing_models = []
```

### 4. 单条件 / 双条件 addition-before 规则族无全 fold 规则

```text
rule_count = 18887
material_all_fold_passing_rule_count = 0
rule_count_20only = 18901
material_all_fold_passing_rule_count_20only = 0
```

### 5. train-on-fold 重新选规则也不稳定

```text
rule_family_train_context_material_passing_folds = 17/28
rule_family_train_20only_context_material_passing_folds = 17/27
```

### 6. context fold 同时有相反失败形态

```text
context_fold_anatomy_twenty_false_positive_no_positive_context_count = 4
context_fold_anatomy_twenty_missed_positive_context_count = 3
context_feature_mixed_instance_group_count = 2
context_feature_mixed_dataset_group_count = 2
```

## 结论

当前 selector 证据已经有 calibration signal，但具体反例、fold gate、模型 gate、规则族搜索、train-holdout 和 context anatomy 都说明它还不是 production selector。下一步必须继续 selector holdout，而不是打开 worker default 或 certificate gate。

当前仍必须保持：

```text
production_validated_selector = false
production_candidate_ab = blocked
```
