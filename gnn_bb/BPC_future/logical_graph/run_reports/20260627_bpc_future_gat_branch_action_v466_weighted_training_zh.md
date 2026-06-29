# GAT Branch/Action Sanity Training

日期：2026-06-27

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v466_v457_plus_v465_walltime_20260627
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v466_v457_plus_v465_walltime_20260627/gat_branch_action_v466_weighted.pt
sample_count = 188
train_sample_count = 144
validation_sample_count = 44
branch_priority_label_counts = {'aux_only_weak_positive': 12, 'not_walltime_gain': 125, 'walltime_gain_positive': 51}
row_kind_counts = {'budget_dominant_improvement': 2, 'changed_timeout_no_effect_hard_negative': 69, 'hard_negative_regression': 54, 'local_only_hard_negative': 18, 'regression': 2, 'target_wall_crossing_positive': 5, 'unknown_right_censored': 5, 'unsupported': 53, 'walltime_gain_positive': 23, 'walltime_gain_target_wall_crossing': 28, 'weak_positive_not_target': 11}
epochs = 12
loss_multipliers = {'branch_priority': 20.0, 'branch_positive': 3.0, 'tail_aux': 0.25, 'walltime_gain': 0.25, 'child_proof_cpu': 0.05, 'time_to_certificate': 0.05}
train_branch_priority_metrics = {'weighted_row_count': 135.0, 'positive_count': 42.0, 'negative_count': 93.0, 'tp': 32.0, 'fp': 14.0, 'fn': 10.0, 'tn': 79.0, 'precision': 0.6956521739130435, 'recall': 0.7619047619047619, 'f1': 0.7272727272727272, 'mean_score': 0.32703356700776903}
validation_branch_priority_metrics = {'weighted_row_count': 41.0, 'positive_count': 9.0, 'negative_count': 32.0, 'tp': 1.0, 'fp': 12.0, 'fn': 8.0, 'tn': 20.0, 'precision': 0.07692307692307693, 'recall': 0.1111111111111111, 'f1': 0.09090909090909093, 'mean_score': 0.37660528010711436}
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
