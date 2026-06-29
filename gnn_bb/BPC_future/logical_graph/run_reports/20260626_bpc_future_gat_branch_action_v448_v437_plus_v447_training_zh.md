# GAT Branch/Action Sanity Training

日期：2026-06-27

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v448_v437_plus_v447_walltime_20260626
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v448_v437_plus_v447_walltime_20260626/gat_branch_action_v448.pt
sample_count = 122
train_sample_count = 83
validation_sample_count = 39
branch_priority_label_counts = {'aux_only_weak_positive': 12, 'not_walltime_gain': 64, 'walltime_gain_positive': 46}
row_kind_counts = {'budget_dominant_improvement': 2, 'changed_timeout_no_effect_hard_negative': 8, 'hard_negative_regression': 54, 'local_only_hard_negative': 18, 'regression': 2, 'target_wall_crossing_positive': 5, 'unknown_right_censored': 5, 'unsupported': 53, 'walltime_gain_positive': 19, 'walltime_gain_target_wall_crossing': 27, 'weak_positive_not_target': 11}
epochs = 5
loss_multipliers = {'tail_aux': 0.25, 'walltime_gain': 1.0, 'child_proof_cpu': 0.1, 'time_to_certificate': 0.1}
train_branch_priority_metrics = {'weighted_row_count': 71.0, 'positive_count': 37.0, 'negative_count': 34.0, 'tp': 3.0, 'fp': 2.0, 'fn': 34.0, 'tn': 32.0, 'precision': 0.6, 'recall': 0.08108108108108109, 'f1': 0.14285714285714288, 'mean_score': 0.3646420863732486}
validation_branch_priority_metrics = {'weighted_row_count': 39.0, 'positive_count': 9.0, 'negative_count': 30.0, 'tp': 0.0, 'fp': 1.0, 'fn': 9.0, 'tn': 29.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'mean_score': 0.33730195195246965}
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
