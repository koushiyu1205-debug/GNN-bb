# GAT Branch/Action Sanity Training

日期：2026-06-28

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v682_v679_plus_v681_strict_full_replay_20260628
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v682_v679_plus_v681_strict_full_replay_20260628/gat_branch_action_v682_seed29.pt
sample_count = 210
train_sample_count = 157
validation_sample_count = 53
branch_priority_label_counts = {'aux_only_weak_positive': 13, 'not_walltime_gain': 142, 'walltime_gain_positive': 55}
row_kind_counts = {'budget_dominant_improvement': 2, 'changed_timeout_no_effect_hard_negative': 82, 'hard_negative_regression': 56, 'local_only_hard_negative': 18, 'paired_probe_hard_negative_proxy': 2, 'paired_probe_positive_proxy': 1, 'regression': 2, 'right_censored_neutral': 1, 'target_wall_crossing_positive': 5, 'unknown_right_censored': 15, 'unsupported': 53, 'walltime_gain_positive': 23, 'walltime_gain_target_wall_crossing': 32, 'weak_gap_fathom_positive': 1, 'weak_gap_positive': 1, 'weak_positive_not_target': 11}
epochs = 12
loss_multipliers = {'branch_priority': 1.0, 'branch_positive': 1.0, 'tail_aux': 0.25, 'walltime_gain': 1.0, 'child_proof_cpu': 0.1, 'time_to_certificate': 0.1, 'tree_policy': 0.25, 'tree_policy_pairwise': 0.25, 'tree_policy_pairwise_margin': 0.5}
train_branch_priority_metrics = {'weighted_row_count': 150.0, 'positive_count': 40.0, 'negative_count': 110.0, 'tp': 10.0, 'fp': 6.0, 'fn': 30.0, 'tn': 104.0, 'precision': 0.625, 'recall': 0.25, 'f1': 0.35714285714285715, 'mean_score': 0.28948255176655946}
validation_branch_priority_metrics = {'weighted_row_count': 47.0, 'positive_count': 15.0, 'negative_count': 32.0, 'tp': 6.0, 'fp': 14.0, 'fn': 9.0, 'tn': 18.0, 'precision': 0.3, 'recall': 0.4, 'f1': 0.34285714285714286, 'mean_score': 0.37981800271317046}
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
