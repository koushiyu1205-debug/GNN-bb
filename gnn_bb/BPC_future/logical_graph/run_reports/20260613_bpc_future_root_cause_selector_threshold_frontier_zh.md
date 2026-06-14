# Root Cause Selector Threshold Frontier 报告

日期：2026-06-13

## 目标

本报告只读分析 true-RC 阈值前沿，验证是否存在另一个阈值可以同时消除
false positive 和 false negative。不运行 BPC，不修改 solver。

## 关键结果

```text
row_count = 280
threshold_count = 115
perfect_threshold_count = 0
strict_gate_threshold_count = 69
recommended_threshold_metrics = {'threshold': -12.430587, 'total': 280, 'predicted_positive': 200, 'tp': 178, 'fp': 22, 'tn': 49, 'fn': 31, 'precision': 0.89, 'recall': 0.851674641148, 'accuracy': 0.810714285714, 'f1': 0.870415647922}
best_f1_threshold_metrics = {'threshold': -9.939229917, 'total': 280, 'predicted_positive': 229, 'tp': 198, 'fp': 31, 'tn': 40, 'fn': 11, 'precision': 0.864628820961, 'recall': 0.947368421053, 'accuracy': 0.85, 'f1': 0.904109589041}
best_zero_false_positive_threshold_metrics = {'threshold': -129.163058, 'total': 280, 'predicted_positive': 56, 'tp': 56, 'fp': 0, 'tn': 71, 'fn': 153, 'precision': 1.0, 'recall': 0.267942583732, 'accuracy': 0.453571428571, 'f1': 0.422641509434}
best_zero_false_negative_threshold_metrics = {'threshold': -3.826192, 'total': 280, 'predicted_positive': 271, 'tp': 209, 'fp': 62, 'tn': 9, 'fn': 0, 'precision': 0.771217712177, 'recall': 1.0, 'accuracy': 0.778571428571, 'f1': 0.870833333333}
```

## 解释

没有任何 true-RC 阈值能把 improved 与 noop replay candidates 完美分开。零 false-positive 阈值会损失太多 recall；零 false-negative 阈值会放入大量 no-op columns。

因此，当前问题不是简单调 true-RC 阈值即可解决；仍需要更强的
addition-before selector，并通过 context / instance / dataset holdout。
