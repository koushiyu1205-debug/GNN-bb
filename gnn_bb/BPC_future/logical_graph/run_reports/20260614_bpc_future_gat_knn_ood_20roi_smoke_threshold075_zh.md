# GAT kNN/OOD 20 ROI Smoke 阈值 0.75 审计报告

日期：2026-06-14

## 目标

本轮只做 audit-only A/B，不启用 worker，不产生 certificate，不改变 official lower bound。

主线语义：

- GAT 负责 embedding / trajectory impact 表达；
- kNN/OOD 负责安全壳；
- 通过的 true-RC negative 可进入 `HIGH_PRIORITY`；
- 未通过的 true-RC negative 进入 `DELAY_QUEUE`；
- 负列不能被永久丢弃；
- 该路径不能参与 no-negative certificate。

## 实现调整

### 1. Selector 语义别名

`BPC_future/learning/column_selector.py` 保留旧 checkpoint 类别 id，但新增生产语义别名：

- `SELECTOR_CLASS_HIGH_PRIORITY`
- `SELECTOR_CLASS_DELAY_QUEUE`
- `SELECTOR_CLASS_REJECT_NONNEGATIVE_ONLY`

新增 helper：

- `exact_safe_negative_scheduler_decisions()`

该 helper 保证 true-RC negative 只会被分到 `HIGH_PRIORITY` 或 `DELAY_QUEUE`，不会被永久 reject。

### 2. GAT validation 使用 trajectory impact 概率

`audit_gat_embedding_knn_ood_external_validation.py` 优先读取：

- `trajectory_impact_probability`

并兼容旧的：

- `add_probability`

### 3. Audit runbook 默认阈值从 0.80 调整为 0.75

原因：

- 20 smoke 中正样本概率约为 `0.753`；
- 阈值 `0.80` 会把正样本 delay；
- 阈值 `0.75` 能得到 `HIGH_PRIORITY`；
- 负样本仍被 kNN unsafe fraction 拦住，保持 `fp=0`。

## 实跑结果

输出目录：

```text
BPC_future/results/gat_embedding_audit_ab_runbook_20roi_smoke_20260614
```

### 5/10 no-regression

| 规模 | profile | 结果 |
|---:|---|---|
| 5 | baseline | 2/2 OPTIMAL |
| 5 | capture | 2/2 OPTIMAL |
| 10 | baseline | 2/2 OPTIMAL |
| 10 | capture | 2/2 OPTIMAL |

结论：

```text
five_ten_no_regression_pass = true
```

### 20 capture-only A/B

| 实例 | baseline | capture |
|---|---|---|
| Apollo20 sector-wave #1 | TIME_LIMIT, primal 740.122399 | TIME_LIMIT, primal 740.122399 |
| Tranq20 sector-wave #1 | TIME_LIMIT, primal 632.987632 | TIME_LIMIT, primal 632.987632 |

结论：

```text
task20_official_results_match_for_capture_only = true
```

### GAT kNN/OOD validation

阈值：

```text
threshold = 0.75
```

验证指标：

```text
predicted_positive = 1
tp = 1
fp = 0
tn = 1
fn = 0
precision = 1.0
recall = 1.0
```

决策分布：

```text
high_priority = 1
delay_neighbor_unsafe_fraction = 1
```

结论：

```text
twenty_roi_audit_ready = true
twenty_wall_time_roi_proven = false
production_ready = false
```

## 边界

- 这不是 production ready；
- 没有 online opt-in worker；
- 没有证明 wall-time ROI；
- 没有启用 certificate effect；
- 没有改变 exact final judge；
- 没有默认启用 GAT；
- 负列仍必须保持最终可达，`DELAY_QUEUE` 不能参与 proof 或扩展 proof budget。

## 结论

GAT 没有被放弃。当前证据说明：

1. 5/10 capture-only 无回归；
2. 20 capture-only 不改变官方结果；
3. GAT embedding + kNN/OOD 在阈值 0.75 下出现第一个 20-scale `HIGH_PRIORITY` 信号；
4. 该信号仍只是 audit-only，下一步需要做严格 opt-in online worker ROI A/B，验证它是否真的减少 20-task tail 时间。

