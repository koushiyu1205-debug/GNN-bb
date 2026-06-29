# GAT Branch/Action Sanity Training

日期：2026-06-27

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v471_v466_plus_v470_hard_negative_20260627
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v471_v466_plus_v470_hard_negative_20260627/gat_branch_action_v471_weighted.pt
sample_count = 198
train_sample_count = 167
validation_sample_count = 31
branch_priority_label_counts = {'aux_only_weak_positive': 12, 'not_walltime_gain': 135, 'walltime_gain_positive': 51}
row_kind_counts = {'budget_dominant_improvement': 2, 'changed_timeout_no_effect_hard_negative': 79, 'hard_negative_regression': 54, 'local_only_hard_negative': 18, 'regression': 2, 'target_wall_crossing_positive': 5, 'unknown_right_censored': 5, 'unsupported': 53, 'walltime_gain_positive': 23, 'walltime_gain_target_wall_crossing': 28, 'weak_positive_not_target': 11}
epochs = 80
loss_multipliers = {'branch_priority': 1.0, 'branch_positive': 1.0, 'tail_aux': 0.25, 'walltime_gain': 2.0, 'child_proof_cpu': 0.1, 'time_to_certificate': 0.1}
train_branch_priority_metrics = {'weighted_row_count': 155.0, 'positive_count': 46.0, 'negative_count': 109.0, 'tp': 27.0, 'fp': 0.0, 'fn': 19.0, 'tn': 109.0, 'precision': 1.0, 'recall': 0.5869565217391305, 'f1': 0.7397260273972603, 'mean_score': 0.3734643238446405}
validation_branch_priority_metrics = {'weighted_row_count': 31.0, 'positive_count': 5.0, 'negative_count': 26.0, 'tp': 1.0, 'fp': 1.0, 'fn': 4.0, 'tn': 25.0, 'precision': 0.5, 'recall': 0.2, 'f1': 0.28571428571428575, 'mean_score': 0.27576930580600617}
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
