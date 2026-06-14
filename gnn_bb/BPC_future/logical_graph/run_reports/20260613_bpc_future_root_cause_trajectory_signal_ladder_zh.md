# BPC_future 根因审计补充：trajectory signal ladder

日期：2026-06-13

## 目标

本轮继续只读分析，不运行 solver，不修改 pricing / RMP / Pulse 主线。

目标是按时间顺序拆解 improved / worsened 信号到底出现在哪一层：

1. pre-batch：加列前可观测；
2. immediate addition：加列后立刻可见；
3. next-RMP movement：下一次 RMP movement；
4. hindsight trajectory：后续 incumbent / zero-fractional / incomplete 轨迹。

这样可以避免把后验信号误当作 addition-before selector 证据。

## 输入与脚本

输入：

```text
BPC_future/results/root_cause_returned_batch_trajectory_dataset_20260613/stage_rows.csv
```

脚本：

```text
BPC_future/scripts/analyze_trajectory_signal_ladder.py
```

复跑：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/analyze_trajectory_signal_ladder.py \
--output-dir BPC_future/results/root_cause_trajectory_signal_ladder_20260613
```

输出：

```text
BPC_future/results/root_cause_trajectory_signal_ladder_20260613/summary.json
```

## 样本

20-task strict stage rows：

- rows：`288`
- improved：`136`
- worsened：`152`

## Layer 1：pre-batch

最强特征：

```text
feature = returned_union_size
auc_positive_higher = 0.6897977941176471
positive_mean = 6.147058823529412
negative_mean = 3.7697368421052633
```

leave-one-dataset：

```text
accuracy = 0.4201388888888889
precision = 0.4392156862745098
recall = 0.8235294117647058
tp/fp/tn/fn = 112 / 143 / 9 / 24
```

leave-one-instance：

```text
accuracy = 0.4618055555555556
precision = 0.46619217081850534
recall = 0.9632352941176471
tp/fp/tn/fn = 131 / 150 / 2 / 5
```

结论：pre-batch 信号高召回、低精度，主要是 batch size / returned coverage。

## Layer 2：immediate addition

最强特征：

```text
feature = addition_new_count
auc_positive_higher = 0.6849119582043344
positive_mean = 4.727941176470588
negative_mean = 1.868421052631579
```

leave-one-dataset：

```text
accuracy = 0.5069444444444444
precision = 0.4855769230769231
recall = 0.7426470588235294
tp/fp/tn/fn = 101 / 107 / 45 / 35
```

leave-one-instance：

```text
accuracy = 0.5173611111111112
precision = 0.4944237918215613
recall = 0.9779411764705882
tp/fp/tn/fn = 133 / 136 / 16 / 3
```

结论：即使知道加进去多少 new columns，仍然 precision 不足。也就是说“加了新列”不是充分条件。

## Layer 3：next-RMP movement

特征：

```text
feature = next_rmp_objective_delta
auc_positive_higher = 0.46812113003095973
positive_mean = -33.66625352205883
negative_mean = -37.05029234868421
```

leave-one-dataset：

```text
accuracy = 0.4895833333333333
precision = 0.4794007490636704
recall = 0.9411764705882353
tp/fp/tn/fn = 128 / 139 / 13 / 8
```

结论：单独的下一轮 RMP objective delta 不能稳定解释 improved / worsened。

## Layer 4：hindsight trajectory

最强特征：

```text
feature = incumbent_within2
auc_positive_higher = 0.718266253869969
positive_mean = 0.6470588235294118
negative_mean = 0.21052631578947367
```

leave-one-dataset：

```text
accuracy = 0.6909722222222222
precision = 0.6821705426356589
recall = 0.6470588235294118
tp/fp/tn/fn = 88 / 41 / 111 / 48
```

leave-one-instance：

```text
accuracy = 0.6805555555555556
precision = 0.6617647058823529
recall = 0.6617647058823529
tp/fp/tn/fn = 90 / 46 / 106 / 46
```

结论：真正更接近 improved / worsened 的信号出现在后续 incumbent / zero-fractional / incomplete trajectory，而不是 pre-batch 或 immediate addition。

## 对根因判断的影响

这轮把因果链进一步收紧：

1. pre-batch 能看到 returned coverage / batch size，但 precision 低；
2. immediate addition 能看到 new columns，但仍 precision 低；
3. next-RMP objective delta 单独不够；
4. hindsight trajectory 明显更接近 outcome。

因此当前缺口不是：

- 找不到负列；
- 加不进新列；
- returned batch 太少；
- next-RMP objective delta 不够大。

更准确地说，缺口是：

> 还没有一个 addition-before proxy 能稳定预测后续 incumbent-producing / low-incomplete trajectory。

## 当前不能得出的结论

不能用 hindsight 直接做 production selector。

也不能因为 immediate addition 的 `addition_new_count` 有相关性，就把 worker 目标改成“尽量多加 new columns”。它的 leave-one precision 仍低于 `0.5`。

## 结论

当前 20-task hard-tail 的主因进一步确认：

> 系统能生成和加入负列，但缺少能提前判断这批列是否会推动后续 RMP active-basis / incumbent trajectory 的 selector。

这解释了为什么前面很多机制都“看起来有信号”，但不能稳定优化 20，也不能保护 5/10。
