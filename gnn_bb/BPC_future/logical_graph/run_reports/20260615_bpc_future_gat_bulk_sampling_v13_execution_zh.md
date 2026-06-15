# GAT Bulk Sampling v13 执行报告

日期：2026-06-15

## 目标

本轮执行 `gat_bulk_sampling_runbook_v13`，目标是把 GAT/CBF gate 的样本采集从单候选 worker A/B 改为批量 same-run capture：

1. 保持 5/10 规模 no-regression；
2. 20-task 只做 capture-only 批量采样；
3. 不启用 worker、不启用 certificate、不产生 official lower bound；
4. 尽量把正样本推进到 80-100，并评估总样本离 250-300 还有多少缺口。

## 执行摘要

### 5/10 sentinel

已执行：

- `task005_baseline_sentinel`
- `task005_capture_sentinel`
- `task010_baseline_sentinel`
- `task010_capture_sentinel`

结果：

| 规模 | baseline | capture | 结论 |
|---:|---|---|---|
| 5 | 2/2 OPTIMAL, gap=0 | 2/2 OPTIMAL, gap=0 | 无退化 |
| 10 | 2/2 OPTIMAL, gap=0 | 2/2 OPTIMAL, gap=0 | 无退化 |

capture 只增加日志，不改变 official result。

### 20-task bulk capture

已执行全部 9 个 capture waves：

| wave | 返回码 | 用时 |
|---:|---:|---:|
| 01 | 0 | 319.0s |
| 02 | 0 | 428.2s |
| 03 | 0 | 424.0s |
| 04 | 0 | 404.7s |
| 05 | 0 | 313.9s |
| 06 | 0 | 301.7s |
| 07 | 0 | 310.8s |
| 08 | 0 | 283.9s |
| 09 | 0 | 89.4s |

总计执行 33 个 20-task capture-only 实例，`max_workers=1`。

## 样本产出

从 5/10 sentinel capture 与 20-task bulk capture 构建 same-run batch-impact rows：

```text
row_count = 128
positive_objective_improvement_count = 97
non_improving_objective_count = 31
objective_positive_rate = 0.757812
instance_count = 36
instance_region_count = 2
training_ready = true
```

按 region：

| region | rows | positive | non-improving |
|---|---:|---:|---:|
| Apollo | 64 | 53 | 11 |
| Tranquillitatis | 64 | 44 | 20 |

结论：

- 正样本已达到 `80-100` 目标区间；
- 总样本仍低于 `250-300`；
- 非改善样本偏少，后续不能再只追正样本，需要补边界/非改善样本。

## Graph Dataset 与 GAT

本地 graph dataset：

```text
sample_count = 128
candidate_count = 2211
candidate_label_counts = {"add": 2046, "abstain": 165}
```

本地离线训练：

```text
train_count = 91
validation_count = 37
validation_accuracy = 0.9490
validation_add_precision = 0.9723
validation_add_recall = 0.9751
```

但 `abstain/delay` 候选仍偏少，validation 混淆矩阵中 delay 召回不足。因此该 GAT checkpoint 仍只能用于 audit，不可生产默认启用。

## kNN/OOD Safety Shell

离线 kNN/OOD 审计：

```text
decision_record_count = 128
predicted_high_priority = 49
actual_high_priority = 97
actual_delay_queue = 31
high_priority_precision = 1.0
high_priority_recall = 0.505154639
negative_recall_delay_queue = 1.0
fp_high_priority_on_delay = 0
validation_safety_ready = true
production_ready = false
```

解释：

- safety shell 没有把 DELAY 样本误判成 HIGH；
- HIGH 很保守，只覆盖约一半正样本；
- 这符合当前阶段要求：宁可 delay，不永久丢负列；
- 仍不能作为 production gate。

## 候选产出

已抽取：

- HIGH_PRIORITY target candidates: 24
- DELAY_QUEUE target candidates: 24

这些候选只允许进入后续 top-K target worker A/B，不允许直接改变求解默认路径。

## 当前缺口

对用户设定的样本目标：

| 指标 | 当前 same-run v13 | 目标 | 状态 |
|---|---:|---:|---|
| 总样本 | 128 | 250-300 | 不足 |
| 正样本 | 97 | 80-100 | 已达标 |
| 非改善样本 | 31 | 建议 >=100 | 不足 |

因此下一步不应继续盲目追正样本，而应采集更多：

- DELAY / near-boundary；
- no-observed / non-improving；
- 30/50/100 更大规模；
- 或通过 targeted worker A/B 采集真实 ROI negative。

## 精确性边界

本轮所有步骤均满足：

- 不启用 worker；
- 不启用 sharded pulse certificate；
- 不产生 official lower bound；
- GAT 不是 pricing oracle；
- kNN/OOD 只是安全壳；
- HIGH_PRIORITY 只是优先级；
- DELAY_QUEUE 不是丢弃；
- true-RC negative 不允许永久过滤。

## 下一步建议

1. 做 v14 采样计划，重点补非改善/边界样本，而不是继续追正样本；
2. 扩到 `tasks_030/050/100` 的 capture-only smoke，先每个规模少量实例；
3. 对 v13 的 24 个 HIGH 和 24 个 DELAY 候选做分层 top-K worker A/B；
4. 只有 worker A/B 证明 5/10 不退化且 20-task ROI 有改善，才允许考虑 opt-in worker；
5. 仍然不能默认启用，也不能进入 certificate path。
