# GAT Branch/Action Sanity Training

日期：2026-06-25

## 目的

用 V244 branch/action sanity dataset 做一次离线小规模训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不导出 score map，不接入 solver 默认行为。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v421_v417_plus_v418_failclosed_20260625
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v421_v417_plus_v418_failclosed_20260625/gat_branch_action_v421.pt
sample_count = 28
train_sample_count = 23
validation_sample_count = 5
branch_priority_label_counts = {'aux_only_weak_positive': 9, 'not_target_200': 8, 'target_200_positive': 11}
row_kind_counts = {'budget_dominant_improvement': 1, 'hard_negative_regression': 8, 'local_only_hard_negative': 8, 'target_200_positive': 11, 'weak_positive_not_target': 9}
epochs = 24
train_branch_priority_metrics = {'weighted_row_count': 14.0, 'positive_count': 9.0, 'negative_count': 5.0, 'tp': 8.0, 'fp': 0.0, 'fn': 1.0, 'tn': 5.0, 'precision': 1.0, 'recall': 0.8888888888888888, 'f1': 0.9411764705882353, 'mean_score': 0.6046802529266903}
validation_branch_priority_metrics = {'weighted_row_count': 5.0, 'positive_count': 2.0, 'negative_count': 3.0, 'tp': 2.0, 'fp': 3.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.4, 'recall': 1.0, 'f1': 0.5714285714285715, 'mean_score': 0.70673166513443}
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
