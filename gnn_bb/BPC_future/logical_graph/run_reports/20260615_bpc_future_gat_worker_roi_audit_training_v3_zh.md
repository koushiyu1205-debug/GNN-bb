# GAT Worker ROI Audit Training v3 报告

日期：2026-06-15

## 目的

本轮在 v2 基础上补跑 `impact-unsampled` target-intervention A/B。

核心改动不是直接扩大 GAT 训练，而是先提高标签质量：

- 候选抽取新增 `candidate_ranking=impact`；
- 优先选择 `new_support_changing` target；
- 跳过已有 ROI 标签的 `(context_hash, target_sequence)`；
- 仍然只做 audit-only，不接 production driver；
- 不产生 certificate 或 official lower bound；
- 不永久丢弃任何 true-RC negative。

## 新增 A/B 结果

```text
runbook = BPC_future/results/gat_same_run_cross_family_impact_unsampled_worker_ab_runbook_20260615
candidate_count = 6
candidate_impact_bucket_counts = {'new_support_changing': 6}
candidate_new_task_set_count = 6
candidate_support_changing_proxy_count = 6
candidate_replacement_like_proxy_count = 0
existing_roi_target_skipped = 2
```

6 个 target 全部通过 reachability / target causal match：

```text
reachable_target_intervention_count = 6
reachability_class_counts = {'target_intervention_reachable': 6}
```

ROI 审计：

```text
roi_class_counts = {
  'positive_primal_roi': 3,
  'negative_primal_roi': 1,
  'no_observed_roi': 2
}
official_bound_effect = false
certificate_ready = false
```

这说明 `impact` 抽样没有继续制造大量无效样本：6 条均可作为因果标签，其中 3 条正样本、3 条非正样本。

## 合并 ROI Dataset v3

```text
dataset = BPC_future/results/gat_same_run_combined_plus_seed_cross_family_v3_worker_roi_dataset_20260615
row_count = 30
training_row_count = 28
unique_training_row_count = 28
label_counts = {'0': 15, '1': 13}
positive_training_label_count = 13
negative_training_label_count = 15
positive_family_count = 3
negative_family_count = 3
positive_region_count = 2
negative_region_count = 2
sample_collection_gaps = []
training_ready = true
production_ready = false
```

`columns_only_roi` 仍不进入训练，避免把“只多加列但没有轨迹改善”的样本误当正样本。

## GAT 图数据集 v3

```text
graph_dataset = BPC_future/results/gat_worker_roi_graph_dataset_v3_20260615
sample_count = 28
candidate_label_counts = {'abstain': 15, 'add': 13}
family_count = 3
region_count = 2
production_ready = false
certificate_ready = false
```

标签语义保持不变：

- `add`：同 context target intervention 后 positive primal ROI；
- `abstain`：同 context target intervention 后 no/negative primal ROI，进入 DELAY_QUEUE；
- 不使用 `skip`，不能永久丢弃 true-RC negative。

## 训练结果

```text
checkpoint = BPC_future/results/gat_worker_roi_training_v3_20260615/context_aware_worker_roi_gat_audit_only.pt
sample_count = 28
train_count = 20
validation_count = 8
best_validation_loss = 0.593926846398972

train_accuracy = 0.8
train_add_precision = 0.7
train_add_recall = 0.875
train_confusion = [[0, 0, 0], [0, 7, 1], [0, 3, 9]]

validation_accuracy = 0.75
validation_add_precision = 1.0
validation_add_recall = 0.6
validation_confusion = [[0, 0, 0], [0, 3, 2], [0, 0, 3]]
```

## 判断

v3 相比 v2 明显改善：

- v2 validation accuracy = 0.4286；
- v2 validation add precision = 0.5；
- v2 validation add recall = 0.5；
- v3 validation accuracy = 0.75；
- v3 validation add precision = 1.0；
- v3 validation add recall = 0.6。

但 v3 仍不能生产化：

```text
validation_count = 8
sample_count = 28
production_ready = false
```

当前结论只能是：`impact` 候选采样方向有效，GAT 开始学到有用信号；但样本量仍不足以默认启用 worker gate。

## 下一步

- 继续按 `candidate_ranking=impact` 采集 20-task hard-tail target-intervention 样本；
- 重点补 random-wave / greedy-anchor 的 Apollo 与 Tranquillitatis 均衡正负样本；
- 继续保持 5/10 no-regression 只做 guard，不作为主标签来源；
- GAT 继续保持 audit-only；
- 任何未通过 gate 的 true-RC negative 进入 DELAY_QUEUE，不能永久丢弃；
- GAT / kNN / ROI gate 不参与 certificate 或 official lower bound。
