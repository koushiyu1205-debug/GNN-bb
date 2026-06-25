# GAT Branch/Action Sanity Training

日期：2026-06-24

## 目的

用 V244 branch/action sanity dataset 做一次离线小规模训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不导出 score map，不接入 solver 默认行为。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v244_v192_v204_v205_v210_v243_20260624
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v244_v192_v204_v205_v210_v243_20260624/gat_branch_action_sanity_v244.pt
sample_count = 17
train_sample_count = 13
validation_sample_count = 4
branch_priority_label_counts = {'aux_only_weak_positive': 5, 'not_target_200': 6, 'target_200_positive': 6}
row_kind_counts = {'budget_dominant_improvement': 1, 'hard_negative_regression': 6, 'local_only_hard_negative': 7, 'target_200_positive': 6, 'weak_positive_not_target': 5}
epochs = 8
train_branch_priority_metrics = {'weighted_row_count': 8.0, 'positive_count': 5.0, 'negative_count': 3.0, 'tp': 5.0, 'fp': 3.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.625, 'recall': 1.0, 'f1': 0.7692307692307693, 'mean_score': 0.7137462273240089}
validation_branch_priority_metrics = {'weighted_row_count': 4.0, 'positive_count': 1.0, 'negative_count': 3.0, 'tp': 1.0, 'fp': 3.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.25, 'recall': 1.0, 'f1': 0.4, 'mean_score': 0.7870848923921585}
sanity_training_completed = true
serious_training_ready = false
optin_training_ready = false
score_map_exported = false
solver_default_effect = false
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## 边界

这次训练只证明链路能跑通，不证明模型可泛化，也不证明能加速 20 规模。当前 target-200 正例和 hard negative 数量仍未达到正式训练门槛。
