# GAT Branch/Action Sanity Training

日期：2026-06-26

## 目的

用 V244 branch/action sanity dataset 做一次离线小规模训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不导出 score map，不接入 solver 默认行为。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v427_v421_plus_v426_walltime_gain_20260625
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v427_v421_plus_v426_walltime_gain_20260625/gat_branch_action_v428_walltime_gain.pt
sample_count = 40
train_sample_count = 36
validation_sample_count = 4
branch_priority_label_counts = {'not_walltime_gain': 11, 'walltime_gain_positive': 29}
row_kind_counts = {'budget_dominant_improvement': 1, 'hard_negative_regression': 11, 'local_only_hard_negative': 8, 'regression': 2, 'unknown_right_censored': 2, 'walltime_gain_positive': 16, 'walltime_gain_target_wall_crossing': 13}
epochs = 20
train_branch_priority_metrics = {'weighted_row_count': 36.0, 'positive_count': 26.0, 'negative_count': 10.0, 'tp': 26.0, 'fp': 10.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.7222222222222222, 'recall': 1.0, 'f1': 0.8387096774193548, 'mean_score': 0.6537915882137086}
validation_branch_priority_metrics = {'weighted_row_count': 4.0, 'positive_count': 3.0, 'negative_count': 1.0, 'tp': 3.0, 'fp': 1.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.75, 'recall': 1.0, 'f1': 0.8571428571428571, 'mean_score': 0.6680015176534653}
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
