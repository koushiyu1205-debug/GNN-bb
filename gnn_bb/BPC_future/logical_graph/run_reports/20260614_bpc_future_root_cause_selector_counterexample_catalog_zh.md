# Selector Counterexample Catalog 报告

日期：2026-06-14

## 目的

本报告只读现有 exact-context replay selector 输出，列出当前
addition-before selector 为什么不能作为 production selector 的具体反例。

## 当前候选

```text
selector_counterexample_catalog = current
recommended_selector_candidate = true_reduced_cost_<=_-12.430587
row_count = 280
false_positive_count = 22
false_negative_count = 31
false_positive_new_task_set_noop_count = 21
false_negative_new_task_set_improved_count = 23
production_validated_selector = false
all_checks_pass = true
```

## 关键反例

### new-task-set 但 replay no-op 的 false positive

`root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 / capture_case_0002 / journey_0001`: task_set=`4,12,17`, sequence=`17-12-4`, true_rc=-121.65471, delta=0.0, class=`noop`

这说明 `new_task_set=True` 和负 reduced cost 不能保证会推动当前 RMP。

### true-RC 较弱但 replay improved 的 false negative

`root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613 / capture_case_0003 / journey_0004`: task_set=`12,15,18`, sequence=`12-18-15`, true_rc=-3.826192, delta=-0.168249, class=`improved`

这说明简单 true-RC 阈值会漏掉确实改善 RMP 的列。

### duplicate / replacement no-op false positive

`duplicate_noop_smoke / capture_case_0001 / journey_0000`: task_set=`1`, sequence=`1`, true_rc=-91.914096, delta=0.0, class=`noop`

这说明 replacement / duplicate 类负列不能被直接当成有效优化信号。

## 解释

当前 replay-calibrated selector 有具体 false positive 和 false negative 反例。有些 new-task-set 负列在 exact replay 中是 no-op，同时也有 true-RC 较弱的 new-task-set 列能改善 RMP objective。因此 true-RC 与 new-task-set 信号不足以作为 production addition-before selector。

## 结论

当前 selector 只能作为 calibration signal。进入 production 前仍必须证明：

```text
selector_feature_scope = addition_before_only
required_selector_holdouts = context / instance / dataset
production_validated_selector = false
```

也就是说，下一步仍是 selector holdout，而不是打开 worker default 或
official certificate gate。
