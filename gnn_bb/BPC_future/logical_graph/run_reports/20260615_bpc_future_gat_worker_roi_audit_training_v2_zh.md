# GAT Worker ROI Audit Training v2 报告

日期：2026-06-15

## 目的

在补跑剩余 4 个 cross-family high-priority target-intervention A/B 后，
重新合并 worker ROI 标签，并训练 audit-only GAT ROI gate。

本轮仍然只做离线验证：

- 不接 production driver；
- 不默认启用；
- 不参与 pricing oracle；
- 不产生 certificate；
- 不产生 official lower bound；
- 不永久丢弃任何 true-RC negative 候选。

## 新增 A/B 结果

剩余 4 个 cross-family high-priority 候选均完成 target intervention：

```text
reachable_target_intervention_count = 4
reachability_class_counts = {'target_intervention_reachable': 4}
roi_class_counts = {'no_observed_roi': 2, 'positive_primal_roi': 2}
certificate_ready = false
official_bound_effect = false
```

其中两个正向 ROI：

```text
apollo15_20km_greedy-anchor tasks020_09 context=301df9ab59b370e5
primal: 551.221675 -> 550.022370
improvement = 1.199305

tranquillitatis_balmer_like_20km greedy-anchor tasks020_01 context=1bb852f9988a595e
primal: 649.843765 -> 581.276964
improvement = 68.566801
```

## 合并 ROI Dataset v2

```text
dataset = BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v2_worker_roi_dataset_20260615
row_count = 24
training_row_count = 22
unique_training_row_count = 22
label_counts = {'0': 12, '1': 10}
positive_training_label_count = 10
negative_training_label_count = 12
positive_family_count = 3
negative_family_count = 3
positive_region_count = 2
negative_region_count = 2
sample_collection_gaps = []
training_ready = true
production_ready = false
```

## GAT 图数据集 v2

```text
graph_dataset = BPC_future/results/gat_worker_roi_graph_dataset_v2_20260615
sample_count = 22
candidate_count = 22
candidate_label_counts = {'abstain': 12, 'add': 10}
family_count = 3
region_count = 2
production_ready = false
certificate_ready = false
```

标签语义：

- `add`：同 context target intervention 后 positive primal ROI；
- `abstain`：同 context target intervention 后 no/negative primal ROI，进入 DELAY_QUEUE；
- `skip`：本数据集不使用，不能用于永久丢弃负列。

## 训练结果

```text
checkpoint = BPC_future/results/gat_worker_roi_training_v2_20260615/context_aware_worker_roi_gat_audit_only.pt
sample_count = 22
train_count = 15
validation_count = 7
best_validation_loss = 0.7123677815709796

train_accuracy = 0.8
train_add_precision = 0.8
train_add_recall = 0.6666666666666666
train_confusion = [[0, 0, 0], [0, 4, 2], [0, 1, 8]]

validation_accuracy = 0.42857142857142855
validation_add_precision = 0.5
validation_add_recall = 0.5
validation_confusion = [[0, 0, 0], [0, 2, 2], [0, 2, 1]]
```

## 判断

v2 相比上一版有实质改善：模型不再退化成全量 `abstain`。

但它仍然不能生产化：

```text
validation_count = 7
validation_add_precision = 0.5
validation_add_recall = 0.5
```

这意味着当前模型会把一半正向 ROI 延迟，也会把一半 delay 样本误判成
HIGH_PRIORITY。作为 audit signal 有价值，但作为 worker gate 仍不够稳。

## 下一步

- 继续扩充 target-intervention ROI 标签，优先补充 random-wave / greedy-anchor 的负样本和 Tranquillitatis/Apollo 均衡样本；
- 在样本量扩大后重新训练 GAT，并用 kNN/OOD safety shell 做 validation-only 审计；
- 在 `validation_add_precision` 和 `validation_add_recall` 稳定前，不接 production driver；
- 所有未通过 gate 的 true-RC negative 仍进入 DELAY_QUEUE，不允许永久丢弃；
- GAT / kNN / ROI gate 仍不能参与 certificate 或 official lower bound。
