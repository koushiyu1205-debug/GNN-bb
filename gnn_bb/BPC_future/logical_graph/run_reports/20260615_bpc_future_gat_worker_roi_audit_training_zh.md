# GAT Worker ROI Audit Training 报告

日期：2026-06-15

## 目的

用 `gat_same_run_combined_plus_seed_cross_family_worker_roi_dataset_20260615`
构建的 ROI 图样本，验证现有 `ContextAwareColumnSelector` 是否已经能学习
“target-intervention 后是否有真实 ROI”。

本轮只做 audit-only 训练：

- 不接 production driver；
- 不默认启用；
- 不参与 pricing oracle；
- 不产生 certificate；
- 不产生 official lower bound；
- 不永久丢弃任何 true-RC negative 候选。

## 数据集

```text
graph_dataset = BPC_future/results/gat_worker_roi_graph_dataset_20260615
sample_count = 18
candidate_count = 18
candidate_label_counts = {'abstain': 10, 'add': 8}
roi_class_counts = {'negative_primal_roi': 3, 'no_observed_roi': 7, 'positive_primal_roi': 8}
family_count = 3
region_count = 2
production_ready = false
certificate_ready = false
```

标签语义：

- `add`：同 context target intervention 后出现 positive primal ROI；
- `abstain`：同 context target intervention 后 no/negative primal ROI，进入 DELAY_QUEUE；
- `skip`：本数据集不使用，不能用于永久丢弃负列。

## 训练命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /home/kai/miniconda3/envs/ecole/bin/python \
BPC_future/scripts/train_gnn_column_selector.py \
  --dataset-dir BPC_future/results/gat_worker_roi_graph_dataset_20260615 \
  --checkpoint-out BPC_future/results/gat_worker_roi_training_20260615/context_aware_worker_roi_gat_audit_only.pt \
  --metrics-out BPC_future/results/gat_worker_roi_training_20260615/summary.json \
  --device cpu \
  --epochs 30 \
  --hidden-dim 32 \
  --option-hidden-dim 32 \
  --pair-edge-dim 32 \
  --selector-hidden-dim 32 \
  --num-gnn-layers 1 \
  --heads 4 \
  --dropout 0.05 \
  --validation-fraction 0.3 \
  --seed 31
```

## 结果

```text
sample_count = 18
train_count = 13
validation_count = 5
best_validation_loss = 0.7124589383602142
train_accuracy = 0.5384615384615384
validation_accuracy = 0.6
train_add_precision = None
train_add_recall = 0.0
validation_add_precision = None
validation_add_recall = 0.0
train_confusion = [[0, 0, 0], [0, 0, 6], [0, 0, 7]]
validation_confusion = [[0, 0, 0], [0, 0, 2], [0, 0, 3]]
selector_is_pricing_oracle = false
selector_can_certificate = false
```

## 判断

这次训练不是成功的 production gate。

虽然 ROI dataset 已经达到最低 `training_ready=true` 门槛，但 18 条样本对
GAT 仍然太小。模型在 train 和 validation 上都退化为全量 `abstain`：

```text
有效正样本也被延迟，add_recall = 0
```

这说明当前样本只够验证数据管线和标签语义，不够训练一个可用的
GAT ROI gate。直接上线会把本应 HIGH_PRIORITY 的正样本也压进
DELAY_QUEUE，无法改善 20-task hard tail。

## 下一步

继续采集 target-intervention ROI 样本，而不是调阈值硬上：

- 保持 5/10 只做 no-regression，不从小快实例采主标签；
- 在 20-task hard-tail 上扩充 same-context target-intervention A/B；
- 每个 family/region 至少补充更多 positive 和 negative ROI；
- 继续要求 `worker_context_match=true` 和 `worker_target_causal_match=true`；
- `columns_only_roi` 暂不作为主训练标签；
- 训练出的 GAT 必须先通过 OOD/kNN safety shell 和 20-task ROI A/B；
- 未通过前不能默认启用，不能参与 certificate / official lower bound。
