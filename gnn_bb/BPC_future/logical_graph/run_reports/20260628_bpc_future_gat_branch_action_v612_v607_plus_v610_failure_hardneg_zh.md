# GAT Branch/Action Sanity Training

日期：2026-06-28

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v612_v607_plus_v610_failure_hardneg_20260628
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v612_v607_plus_v610_failure_hardneg_20260628/gat_branch_action_v612.pt
sample_count = 1147
train_sample_count = 589
validation_sample_count = 558
branch_priority_label_counts = {'aux_only_tree_policy': 1112, 'not_walltime_gain': 4, 'walltime_gain_positive': 31}
row_kind_counts = {'tree_policy_hard_negative': 936, 'tree_policy_positive': 31, 'tree_policy_proof_tail_hard_negative': 180}
epochs = 8
loss_multipliers = {'branch_priority': 1.0, 'branch_positive': 1.0, 'tail_aux': 0.25, 'walltime_gain': 1.0, 'child_proof_cpu': 0.1, 'time_to_certificate': 0.1, 'tree_policy': 0.5, 'tree_policy_pairwise': 0.5, 'tree_policy_pairwise_margin': 0.5}
train_branch_priority_metrics = {'weighted_row_count': 12.0, 'positive_count': 12.0, 'negative_count': 0.0, 'tp': 12.0, 'fp': 0.0, 'fn': 0.0, 'tn': 0.0, 'precision': 1.0, 'recall': 1.0, 'f1': 1.0, 'mean_score': 1.0}
validation_branch_priority_metrics = {'weighted_row_count': 23.0, 'positive_count': 19.0, 'negative_count': 4.0, 'tp': 19.0, 'fp': 4.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.8260869565217391, 'recall': 1.0, 'f1': 0.9047619047619047, 'mean_score': 1.0}
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
