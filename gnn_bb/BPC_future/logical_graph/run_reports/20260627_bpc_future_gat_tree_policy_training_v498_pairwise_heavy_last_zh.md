# GAT Branch/Action Sanity Training

日期：2026-06-27

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v496_tree_policy_pairwise_event_dataset_20260627
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v496_tree_policy_pairwise_event_dataset_20260627/gat_tree_policy_v498_pairwise_heavy_last.pt
sample_count = 81
train_sample_count = 76
validation_sample_count = 5
branch_priority_label_counts = {'not_walltime_gain': 0, 'walltime_gain_positive': 0}
row_kind_counts = {'tree_policy_hard_negative': 52, 'tree_policy_positive': 29}
epochs = 20
loss_multipliers = {'branch_priority': 0.0, 'branch_positive': 1.0, 'tail_aux': 0.0, 'walltime_gain': 0.0, 'child_proof_cpu': 0.0, 'time_to_certificate': 0.0, 'tree_policy': 0.2, 'tree_policy_pairwise': 5.0, 'tree_policy_pairwise_margin': 1.0}
train_branch_priority_metrics = {'weighted_row_count': 0.0, 'positive_count': 0.0, 'negative_count': 0.0, 'tp': 0.0, 'fp': 0.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'mean_score': 0.0}
validation_branch_priority_metrics = {'weighted_row_count': 0.0, 'positive_count': 0.0, 'negative_count': 0.0, 'tp': 0.0, 'fp': 0.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'mean_score': 0.0}
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

这次训练只证明链路能跑通，不证明模型可泛化，也不证明能加速 20 规模。当前 wall-time gain 正例和 hard negative 数量仍未达到正式训练门槛。
