# GAT Branch/Action Sanity Training

日期：2026-06-26

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v431_v430_plus_score_gated_smoke20_20260626
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v431_v430_plus_score_gated_smoke20_20260626/gat_branch_action_v431.pt
sample_count = 116
train_sample_count = 87
validation_sample_count = 29
branch_priority_label_counts = {'aux_only_weak_positive': 9, 'not_walltime_gain': 55, 'walltime_gain_positive': 52}
row_kind_counts = {'budget_dominant_improvement': 2, 'hard_negative_regression': 55, 'local_only_hard_negative': 18, 'regression': 2, 'unknown_right_censored': 15, 'unsupported': 52, 'walltime_gain_positive': 20, 'walltime_gain_target_wall_crossing': 32, 'weak_positive_not_target': 9}
epochs = 12
loss_multipliers = {'tail_aux': 0.25, 'walltime_gain': 1.0, 'child_proof_cpu': 0.1, 'time_to_certificate': 0.1}
train_branch_priority_metrics = {'weighted_row_count': 79.0, 'positive_count': 44.0, 'negative_count': 35.0, 'tp': 44.0, 'fp': 35.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.5569620253164557, 'recall': 1.0, 'f1': 0.7154471544715447, 'mean_score': 0.8323836507676523}
validation_branch_priority_metrics = {'weighted_row_count': 28.0, 'positive_count': 8.0, 'negative_count': 20.0, 'tp': 8.0, 'fp': 20.0, 'fn': 0.0, 'tn': 0.0, 'precision': 0.2857142857142857, 'recall': 1.0, 'f1': 0.4444444444444445, 'mean_score': 0.8802371514695031}
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
