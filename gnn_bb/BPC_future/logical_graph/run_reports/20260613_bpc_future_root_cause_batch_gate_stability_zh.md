# BPC_future 根因审计补充：batch gate stability

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

目标是检查一个更接近可优化方向的问题：

> 是否存在简单、保守的 batch-level gate，可以决定“值得触发 worker / batch 扩张”或“应该 no-op 跳过”？

如果这样的 gate 稳定存在，它可能成为下一步优化方向。若不存在，就不能把简单 gate 当生产方案。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_batch_gate_stability.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_batch_gate_stability.py \
--output-dir BPC_future/results/root_cause_batch_gate_stability_20260613
```

输出：

```text
BPC_future/results/root_cause_batch_gate_stability_20260613/summary.json
```

## 样本

20-task strict stage rows：

- rows：`288`
- improved：`136`
- worsened：`152`

规则搜索只用 pre-batch features，不使用后验字段。

## 正向 trigger gate

目标：预测 improved，也就是“这类 batch 值得触发”。

全量 aggregate 最强规则：

```text
returned_union_size >= 11.0
precision = 0.8695652173913043
recall = 0.14705882352941177
tp/fp/tn/fn = 20 / 3 / 149 / 116
```

表面上这是一个高 precision trigger。

但 leave-one-dataset 后：

```text
precision = 0.0
recall = 0.0
predicted_positive = 3
tp/fp/tn/fn = 0 / 3 / 149 / 136
```

leave-one-instance 后：

```text
precision = 0.2
recall = 0.022058823529411766
predicted_positive = 15
tp/fp/tn/fn = 3 / 12 / 140 / 133
```

结论：aggregate 高 precision 是过拟合，不是可上线 trigger gate。

## 负向 no-op gate

目标：预测 worsened，也就是“这类 batch 应该跳过 / no-op”。

全量 aggregate 最强规则：

```text
returned_union_size <= 2.0
precision = 0.8125
recall = 0.17105263157894737
tp/fp/tn/fn = 26 / 6 / 130 / 126
```

表面上这是一个高 precision no-op gate。

但 leave-one-dataset 后：

```text
precision = 0.41025641025641024
recall = 0.10526315789473684
predicted_positive = 39
tp/fp/tn/fn = 16 / 23 / 113 / 136
```

leave-one-instance 后：

```text
precision = 1.0
recall = 0.03289473684210526
predicted_positive = 5
tp/fp/tn/fn = 5 / 0 / 136 / 147
```

结论：no-op gate 也不稳定。leave-one-instance 虽然 precision 高，但几乎不触发；leave-one-dataset precision 又不够。

## 对根因判断的影响

本轮说明：

- 不能用简单 batch-level threshold 做 production trigger；
- 也不能用简单 batch-level threshold 做 production no-op；
- aggregate 上的高 precision 主要是 dataset-specific pattern；
- leave-one-dataset / leave-one-instance 后要么不触发，要么 false positive 太多。

这进一步排除了一个看似简单的优化方向：

> “先做一个保守 gate，只在 returned_union_size 很大/很小时触发或跳过。”

当前证据不支持它。

## 当前可信结论

当前最可信结论仍是：

> 20-task 需要的不是简单 pre-batch trigger/no-op gate，而是更强的 addition-before trajectory predictor，或者更直接的 counterfactual / replay 证据来判断 batch 是否会推动后续 active-basis / incumbent trajectory。

在没有这类证据前，不应默认启用 worker、扩大 return count、扩大 profile-DP cap，或把 aggregate threshold 当成生产策略。
