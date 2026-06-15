# GAT Worker ROI v35 Hard-Negative Training Audit 报告

日期：2026-06-15

## 目标

本轮只做离线 GAT worker-ROI 训练与 OOD/kNN 安全壳审计，不接 production driver，不运行 BPC / pricing / RMP / worker，不产生 certificate 或 official lower bound。

目标是验证：把 post-injection hard negative 加入 v34 后，是否能在不增加采样的情况下得到满足生产门槛的 trajectory ROI gate。

## 数据集

合并数据集：

```text
dataset = BPC_future/data/gat_worker_roi/v35_v34_plus_post_injection_hard_negative_20260615
sample_count = 205
candidate_label_counts = {'abstain': 145, 'add': 60}
instance_count = 57
family_count = 3
region_count = 2
all_checks_pass = true
```

新增 hard negative 来源：

```text
source = post_injection_batch_k4_hard_negative_v1
added_samples = 8
added_label = abstain / DELAY_QUEUE
target_returned_journeys = 32
target_active_changed_task_set_sum = 0
```

这批样本原本是 true-RC negative，可被 worker 注入，但没有进入 active support，因此不能作为正 ROI 标签。

## 训练结果

### focal hard

```text
checkpoint = gat_worker_roi_focal_hard.pt
validation_precision = 0.4333
validation_recall = 0.8125
validation_f1 = 0.5652
```

裸模型 recall 足够，但 precision 远低于 0.95。

严格 OOD/kNN 壳：

```text
validation_high_priority = 0
validation_false_safe_rate_union = 0.0
validation_harmful_batch_recall = 1.0
decision_scope_high_priority = 7 / 205
decision_scope_precision = 1.0
decision_scope_recall = 0.1167
```

安全但几乎不接受，无法带来加速。

### focal pairwise

```text
checkpoint = gat_worker_roi_focal_pairwise.pt
validation_precision = 0.4545
validation_recall = 0.5
validation_f1 = 0.4762
```

pairwise/focal 没有改善可分性。

严格 OOD/kNN 壳：

```text
validation_high_priority = 0
validation_false_safe_rate_union = 0.0
validation_harmful_batch_recall = 1.0
decision_scope_high_priority = 3 / 205
decision_scope_precision = 1.0
decision_scope_recall = 0.05
```

同样安全但不可用。

## kNN 阈值扫描

### focal hard

| max_neighbor_delay_fraction | val HP | val precision | val recall | val false-safe | harmful recall |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0 | - | 0.0000 | 0.0000 | 1.0000 |
| 0.2 | 0 | - | 0.0000 | 0.0000 | 1.0000 |
| 0.5 | 6 | 0.6667 | 0.2500 | 0.0500 | 0.9286 |
| 0.8 | 17 | 0.3529 | 0.3750 | 0.3056 | 0.6071 |
| 1.0 | 30 | 0.4333 | 0.8125 | 0.6071 | 0.3929 |

### focal pairwise

| max_neighbor_delay_fraction | val HP | val precision | val recall | val false-safe | harmful recall |
|---:|---:|---:|---:|---:|---:|
| 0.0 | 0 | - | 0.0000 | 0.0000 | 1.0000 |
| 0.2 | 0 | - | 0.0000 | 0.0000 | 1.0000 |
| 0.5 | 1 | 0.0000 | 0.0000 | 0.0263 | 0.9643 |
| 0.8 | 7 | 0.2857 | 0.2000 | 0.1563 | 0.8214 |
| 1.0 | 11 | 0.4545 | 0.5000 | 0.2143 | 0.7857 |

## 结论

v35 已达到样本数量下限：

```text
total >= 150-200: yes, 205
positive >= 50-80: yes, 60
```

但它没有达到生产指标：

```text
precision >= 0.95: no
recall >= 0.65: only naked focal passes recall, but precision fails
OOD false-safe <= 1-2%: only strict shell passes, but accepted count is zero on validation
harmful batch recall >= 95%: strict shell passes; useful shell fails
```

核心原因不是样本总数不足，而是 positive ROI 的可分性不足。当前 GAT 仍容易把“true-RC negative / 可加列”与“真正改善 RMP 轨迹的列”混在一起。加入 8 个 post-injection hard negative 后，安全壳更保守，但模型没有学出足够稳定的 HIGH_PRIORITY 区域。

## 当前生产判定

```text
production_ready = false
default_enabled = false
selector_can_certificate = false
gate_can_permanently_discard_negative_columns = false
```

该 GAT 不能用于生产默认启用，也不应进入 20-task active worker A/B。

## 下一步

继续采样不应再围绕 true-RC negative 数量，而应专门采集真正 positive trajectory ROI：

- target columns 进入 active support；
- worker next objective 不差于 baseline same-iteration；
- follow-up exact / retry pressure 下降；
- wall time 或 gap 有实际改善；
- 保留本轮 inactive-only / worse-than-baseline 样本作为 hard negative。

在新增真实正 ROI 前，继续调 loss 或放宽 OOD 壳只会在 false-safe 和 harmful recall 之间摇摆，不能满足生产门槛。
