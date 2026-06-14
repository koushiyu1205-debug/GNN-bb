# BPC_future 根因：Exact-context Replay Selector Gate 审计

日期：2026-06-13

## 目的

本轮只回答一个问题：

> 在已经有 exact-context replay impact rows 后，是否已经能用 addition-before 可见字段形成一个可上线 selector？

结论：不能。

这不是因为没有信号。相反，`true_reduced_cost` 的全样本阈值看起来很强；但一做 context / instance / dataset holdout，它就不稳定。因此不能把这个阈值写进 solver，也不能据此宣称已经找到生产优化方向。

## 数据范围

脚本：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_counterfactual_replay_selector_gate.py \
--output-dir BPC_future/results/root_cause_counterfactual_replay_selector_gate_20260613
```

输入是已有 exact replay impact 的 `candidate_impact_rows.csv`：

- `duplicate_noop_smoke`
- `real_capture_mt20_apollo`
- `root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613`
- `root_cause_counterfactual_target_capture_dp1000_tranq20_20260613`

只保留：

- `single_treatment_found=true`
- `single_impact_class in {improved, noop}`

汇总：

```text
row_count = 207
label_counts = improved:147, noop:60
context_count = 22
instance_count = 4
impact_dataset_count = 4
all_checks_pass = true
```

## 使用的线上可见特征

审计只允许 addition-before 可见字段：

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

这些后验字段只能用于打标签，不能作为线上 selector 输入。

## 表面上最强的规则

全样本最佳 `true_reduced_cost` 规则：

```text
rule = true_reduced_cost <= -12.430587
precision = 0.8513513513513513
recall = 0.8571428571428571
tp = 126
fp = 22
fn = 21
total = 207
```

这说明 exact replay impact rows 里确实有可解释信号。

但这只能说明“同样本可分”，不能证明生产可用。生产 selector 必须在未知 context / instance / dataset 上稳定。

## Holdout 结果

### Context holdout

`true_reduced_cost` rule：

```text
precision = 0.7933333333333333
recall = 0.8095238095238095
tp = 119
fp = 31
fn = 28
total = 207
```

这个结果仍有明显 false positive / false negative。它虽然过了最低 precision/recall 线，但不是零风险 gate，而且部分 held-out context recall 为 0。

### Instance holdout

`true_reduced_cost` rule：

```text
precision = 0.7816091954022989
recall = 0.46258503401360546
tp = 68
fp = 19
fn = 79
total = 207
```

recall 低于 `0.5`，不满足 strict gate。

关键反例：

held-out `tranquillitatis_balmer_like_20km_greedy-anchor_randomtw_tasks020_01_seed61001` 时，训练出的阈值过严，held-out 90 行里预测正例为 0，漏掉 63 个 improved rows。

### Dataset holdout

`true_reduced_cost` rule：

```text
precision = 0.664
recall = 0.564625850340136
tp = 83
fp = 42
fn = 64
total = 207
```

precision 低于 `0.75`，不满足 strict gate。

train-best 跨所有简单特征后，dataset holdout 仍失败：

```text
precision = 0.6907216494845361
recall = 0.9115646258503401
tp = 134
fp = 60
fn = 13
total = 207
feature_choices = true_reduced_cost:3, cost:1
```

这说明失败不是单个 `true_reduced_cost` 特征选得不好，而是当前这批 addition-before 简单特征还不足以形成泛化 gate。

## 审计结论

```text
passing_features_all_holdouts = []
```

没有任何单一 addition-before 特征同时通过：

- context holdout；
- instance holdout；
- dataset holdout。

因此不能上线：

- `true_reduced_cost <= threshold`
- `new_task_set`
- `duplicate_signature`
- `active_support_changing`
- `cost / task_count / vehicle_count`

作为 production returned-batch selector。

## 对根因判断的影响

这轮结果加强了当前根因判断：

1. 20-task 中确实存在 high-impact negative candidates；
2. duplicate/no-op negative candidates 也真实存在；
3. 全样本可以找到很诱人的规则；
4. 但这些规则跨 instance / dataset 不稳定；
5. 因此缺口仍是 addition-before、context-aware、低开销、可泛化 selector，而不是继续加 worker budget 或简单按 true-RC 阈值筛选。

所以当前状态仍是：

```text
production_direction_proven = false
has_stable_addition_before_selector = false
```

## 下一步边界

不能做：

- 把 `true_reduced_cost <= -12.430587` 写进 solver；
- 用全样本 precision/recall 宣称 selector 已成立；
- 打开 Pulse worker default；
- 打开 official certificate gate；
- 为追求 20-task 单点改善牺牲 5/10 no-regression。

有价值的下一步仍然是 calibration-only：

- 扩展 exact-context replay rows；
- 增加更结构化的 addition-before batch features；
- 做跨 instance / dataset selector gate；
- 通过后再跑 5/10 no-regression 和 20 hard repeat A/B。
