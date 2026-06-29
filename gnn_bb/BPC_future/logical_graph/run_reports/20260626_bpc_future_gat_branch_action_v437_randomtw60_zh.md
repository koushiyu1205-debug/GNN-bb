# GAT Branch/Action Sanity Training

日期：2026-06-26

## 目的

用 v430 random-TW branch/action dataset 做一次离线训练，验证 GAT branch/action head 的数据、loss 和 checkpoint 链路。该 checkpoint 不接入 solver 默认行为，score map 只能显式 opt-in 导出和使用。

## 机器字段

```text
dataset_dir = BPC_future/data/gat_branch_action_sanity/v437_randomtw60_branch_replay_20260626
checkpoint_out = BPC_future/data/gat_branch_action_sanity/v437_randomtw60_branch_replay_20260626/gat_branch_action_v437.pt
sample_count = 122
train_sample_count = 103
validation_sample_count = 19
branch_priority_label_counts = {'aux_only_weak_positive': 9, 'not_walltime_gain': 60, 'walltime_gain_positive': 53}
row_kind_counts = {'budget_dominant_improvement': 2, 'changed_timeout_no_effect_hard_negative': 6, 'hard_negative_regression': 54, 'local_only_hard_negative': 18, 'regression': 2, 'unknown_right_censored': 5, 'unsupported': 52, 'walltime_gain_positive': 21, 'walltime_gain_target_wall_crossing': 32, 'weak_positive_not_target': 9}
epochs = 16
loss_multipliers = {'tail_aux': 0.25, 'walltime_gain': 1.0, 'child_proof_cpu': 0.25, 'time_to_certificate': 0.25}
train_branch_priority_metrics = {'weighted_row_count': 98.0, 'positive_count': 48.0, 'negative_count': 50.0, 'tp': 31.0, 'fp': 6.0, 'fn': 17.0, 'tn': 44.0, 'precision': 0.8378378378378378, 'recall': 0.6458333333333334, 'f1': 0.7294117647058824, 'mean_score': 0.6065250340164924}
validation_branch_priority_metrics = {'weighted_row_count': 15.0, 'positive_count': 5.0, 'negative_count': 10.0, 'tp': 0.0, 'fp': 1.0, 'fn': 5.0, 'tn': 9.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'mean_score': 0.4671374003092448}
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
