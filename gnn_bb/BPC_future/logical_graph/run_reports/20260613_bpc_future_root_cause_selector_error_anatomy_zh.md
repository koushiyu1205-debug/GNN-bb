# Root Cause Selector Error Anatomy 报告

日期：2026-06-13

## 目标

本报告只读分析当前 replay-calibrated addition-before selector 的错误分布，
不运行 BPC、不修改 solver、不产生 certificate 或 lower-bound effect。

## 当前推荐规则

```text
recommended_selector_candidate = true_reduced_cost_<=_-12.430587
recommended_selector_rule = {'feature': 'true_reduced_cost', 'operator': '<=', 'threshold': -12.430587, 'type': 'numeric'}
```

## 错误总览

```text
row_count = 280
selected_count = 200
positive_count = 209
false_positive_count = 22
false_negative_count = 31
false_positive_new_task_set_noop_count = 21
false_negative_new_task_set_improved_count = 23
```

## 数据集分布

```json
{
  "false_negative_by_dataset": {
    "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613": 21,
    "root_cause_target002_capture_pt03_r3_20260613": 10
  },
  "false_positive_by_dataset": {
    "duplicate_noop_smoke": 1,
    "root_cause_counterfactual_target_capture_dp1000_targets001_002_20260613": 21
  }
}
```

## 解释

当前 true-RC 阈值规则同时存在 false positive 和 false negative：
一部分 false positive 是 new task-set 负列，但 replay impact 为 0；
一部分 false negative 是 new task-set 列，却有正向 replay impact。
因此 true-RC 和 new-task-set 信号不足以作为 production addition-before selector。

这说明当前规则只能作为 calibration signal，不能作为 production selector。
下一步仍必须要求 context / instance / dataset holdout 与 full BPC A/B。
