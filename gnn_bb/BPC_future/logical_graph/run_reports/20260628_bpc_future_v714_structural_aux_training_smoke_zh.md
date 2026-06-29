# GAT Branch/Action Sanity Training

日期：2026-06-28

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v714_mixed_walltime_gap_aux_smoke_20260628
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v714_mixed_walltime_gap_aux_smoke_20260628/gat_branch_action_v714_structural_aux_smoke.pt
sample_count = 8
train_sample_count = 6
validation_sample_count = 2
branch_priority_label_counts = {'aux_only_weak_positive': 2, 'not_walltime_gain': 4, 'walltime_gain_positive': 2}
row_kind_counts = {'changed_timeout_no_effect_hard_negative': 3, 'hard_negative_regression': 1, 'walltime_gain_target_wall_crossing': 2, 'weak_gap_fathom_positive': 1, 'weak_gap_positive': 1}
epochs = 1
loss_multipliers = {'branch_priority': 1.0, 'branch_positive': 1.0, 'tail_aux': 0.25, 'walltime_gain': 1.0, 'child_proof_cpu': 0.1, 'time_to_certificate': 0.1, 'gap_improvement': 0.1, 'primal_improvement': 0.05, 'dual_bound_gain': 0.05, 'fathom_gain': 0.05, 'branch_count_delta': 0.05, 'completion_bound_retry_gain': 0.05, 'tree_policy': 0.25, 'tree_policy_pairwise': 0.25, 'tree_policy_pairwise_margin': 0.5}
train_branch_priority_metrics = {'weighted_row_count': 4.0, 'positive_count': 0.0, 'negative_count': 4.0, 'tp': 0.0, 'fp': 2.0, 'fn': 0.0, 'tn': 2.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'mean_score': 0.48890311270952225}
validation_branch_priority_metrics = {'weighted_row_count': 2.0, 'positive_count': 2.0, 'negative_count': 0.0, 'tp': 1.0, 'fp': 0.0, 'fn': 1.0, 'tn': 0.0, 'precision': 1.0, 'recall': 0.5, 'f1': 0.6666666666666666, 'mean_score': 0.4812990576028824}
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
