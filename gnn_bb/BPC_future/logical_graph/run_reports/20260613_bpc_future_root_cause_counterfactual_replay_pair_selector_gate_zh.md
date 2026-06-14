# BPC_future 根因：Exact-context Replay Pair Selector Gate 审计

日期：2026-06-13

## 目的

上一轮 single-feature selector gate 已经排除了单一 addition-before 特征。  
本轮继续检查一个更强但仍简单的假设：

> 两个 addition-before 规则的 AND / OR 组合，是否已经足够形成 production selector？

结论：仍然不能。

## 数据范围

数据与 single-feature selector gate 完全一致：

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

明确排除后验字段：

- `single_objective_delta`
- `single_dual_l1_delta`
- `single_changed_journey_count`

## 全样本最优 pair rule

全样本最优二规则组合：

```text
logic = OR
rule_1 = true_reduced_cost <= -123.681417
rule_2 = cost >= 85.394781

precision = 0.9512195121951219
recall = 0.5306122448979592
tp = 78
fp = 4
fn = 69
total = 207
```

这比单特征全样本 precision 更高，看起来更像一个高精度 selector。

但仍然只是同样本结果。

## Holdout 结果

### Context holdout

```text
precision = 0.7547169811320755
recall = 0.272108843537415
tp = 40
fp = 13
fn = 107
total = 207
passes_strict_gate = false
```

recall 极低，说明 context 变化后大量 improved rows 被漏掉。

### Instance holdout

```text
precision = 0.6907216494845361
recall = 0.9115646258503401
tp = 134
fp = 60
fn = 13
total = 207
passes_strict_gate = false
```

recall 高，但 false positives 太多，precision 不达标。

### Dataset holdout

```text
precision = 0.6875
recall = 0.8979591836734694
tp = 132
fp = 60
fn = 15
total = 207
passes_strict_gate = false
```

dataset holdout 同样 precision 不达标。

## 审计结论

```text
context_holdout_pair_rule_fails = true
instance_holdout_pair_rule_fails = true
dataset_holdout_pair_rule_fails = true
no_pair_rule_passes_all_holdout_gates = true
all_checks_pass = true
```

因此当前不能上线：

- `true_reduced_cost OR cost` 组合；
- 任意本轮枚举得到的简单二特征 AND / OR gate；
- 用全样本 pair precision `0.951` 作为 production selector 证据。

## 对根因判断的影响

这条证据进一步收紧当前结论：

> 现在缺的不是“再加一个简单阈值”或“再加一个二特征组合”。当前 addition-before 可见字段中确实有信号，但简单 selector 不能跨 context / instance / dataset 稳定泛化。

所以当前状态仍是：

```text
has_stable_addition_before_selector = false
production_direction_proven = false
```

下一步如果继续，必须进入更结构化的 returned-batch trajectory 建模；在新的 selector 通过跨 instance / dataset gate 之前，不能做 production path 修改。
