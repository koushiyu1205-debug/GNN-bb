# Selector Context Scalar Holdout 审计

日期：2026-06-13

## 目标

`control_objective` 在当前 replay 样本中能消除 mixed labels；本审计检查它
是否能跨 dataset / instance / context_hash 留出稳定泛化。
本脚本只读 candidate replay rows，不运行 BPC，不改变 production path。

## 结论

all_checks_pass = true
selector_context_scalar_holdout = current
row_count = 280
label_counts = {'noop': 71, 'improved': 209}
strict_precision_min = 0.75
strict_recall_min = 0.5
control_objective_holdout_passing_model_count = 0
control_objective_holdout_production_validated_selector = false

核心判断：`control_objective` 有 calibration signal，但还不是 production selector。
激进 threshold 在 context holdout 下 precision 不稳；保守 100-bin majority
precision 高但 instance/context recall 太低，不足以支撑 20 大幅加速。

## Holdout 汇总

| Model | Dataset P/R | Dataset Pass | Instance P/R | Instance Pass | Context P/R | Context Pass | All Pass |
|---|---:|---:|---:|---:|---:|---:|---:|
| threshold_precision75 | 0.856436/0.827751 | true | 0.808889/0.870813 | true | 0.746377/0.985646 | false | false |
| bin100_majority75 | 1.000000/0.617225 | true | 1.000000/0.339713 | false | 1.000000/0.339713 | false | false |
| shape_bin100_majority75 | 1.000000/0.153110 | false | None/0.000000 | false | 1.000000/0.220096 | false | false |
| shape_majority75 | 0.796610/0.224880 | false | None/0.000000 | false | 0.815789/0.296651 | false | false |

## 关键失败模式

```text
threshold_context_precision = 0.746377
threshold_context_recall = 0.985646
bin100_instance_precision = 1.000000
bin100_instance_recall = 0.339713
bin100_context_precision = 1.000000
bin100_context_recall = 0.339713
control_objective_holdout_passing_model_count = 0
production_validated_selector = false
```

解释：当前样本中 `control_objective_bin_100_mixed_group_count = 0` 只能说明
它能分开已见 replay labels。留出后，简单规则不能同时满足 precision 和 recall。
因此它支持“RMP/context coupling 是根因”，但不能直接变成优化主线。

## 下一步含义

在没有 full BPC A/B 前，不应把该 selector 接入 production worker 或 certificate gate。
若继续推进，应先扩大 capture/replay 数据，或者寻找更稳定的 addition-before
RMP trajectory 特征，再重复 dataset / instance / context holdout。
