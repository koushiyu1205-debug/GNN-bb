# Journey Branch Training Readiness Audit

日期：2026-06-25

## 目的

汇总已完成 branch counterfactual replay，区分 strict full-replay positive 和真正进入 200 秒目标的 target-200 positive。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不改变 official bound 或 certificate。

## 机器字段

```text
target_wall = 200.0
row_count = 25
usable_counterfactual_training_count = 17
strict_full_replay_positive_count = 11
strict_full_replay_positive_context_count = 5
strict_full_replay_positive_instance_count = 4
strict_full_replay_positive_time_window_family_count = 2
target_200_positive_count = 6
target_200_positive_context_count = 3
target_200_positive_instance_count = 3
target_200_positive_time_window_family_count = 2
weak_positive_not_target_count = 5
regression_count = 6
local_only_hard_negative_count = 7
hard_negative_count = 6
right_censored_counterfactual_count = 8
timeout_resolved_count = 4
timeout_regression_count = 6
target_200_positive_holdout_context_count = 0
counterfactual_label_type_counts = {'budget_dominant_improvement': 1, 'local_only_hard_negative': 7, 'regression': 6, 'strong_positive': 11}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 1, 'EXTERNAL_TIME_LIMIT->OPTIMAL': 4, 'EXTERNAL_TIME_LIMIT->TIME_LIMIT': 1, 'OPTIMAL->EXTERNAL_TIME_LIMIT': 5, 'OPTIMAL->OPTIMAL': 7, 'OPTIMAL->TIME_LIMIT': 1, 'TIME_LIMIT->EXTERNAL_TIME_LIMIT': 4, 'TIME_LIMIT->TIME_LIMIT': 2}
pipeline_debug_training_ready = true
sanity_training_ready = true
serious_training_ready = false
optin_training_ready = false
serious_training_requirements = {'target_200_positive_min': 20, 'hard_negative_min': 30, 'target_200_context_min': 8, 'target_200_instance_min': 8, 'target_200_time_window_family_min': 3, 'holdout_context_min': 2}
optin_training_requirements = {'target_200_positive_min': 40, 'hard_negative_min': 60, 'target_200_context_min': 15, 'target_200_instance_min': 15, 'target_200_time_window_family_min': 3, 'holdout_context_min': 3}
remaining_for_pipeline_debug_training = {}
remaining_for_sanity_training = {}
remaining_for_serious_training = {'target_200_positive_min': 14, 'hard_negative_min': 24, 'target_200_context_min': 5, 'target_200_instance_min': 5, 'target_200_time_window_family_min': 1, 'holdout_context_min': 2}
remaining_for_optin_training = {'target_200_positive_min': 34, 'hard_negative_min': 54, 'target_200_context_min': 12, 'target_200_instance_min': 12, 'target_200_time_window_family_min': 1, 'holdout_context_min': 3}
missing_for_pipeline_debug_training = {}
missing_for_sanity_training = {}
missing_for_serious_training = {'target_200_positive_min': 14, 'hard_negative_min': 24, 'target_200_context_min': 5, 'target_200_instance_min': 5, 'target_200_time_window_family_min': 1, 'holdout_context_min': 2}
missing_for_optin_training = {'target_200_positive_min': 34, 'hard_negative_min': 54, 'target_200_context_min': 12, 'target_200_instance_min': 12, 'target_200_time_window_family_min': 1, 'holdout_context_min': 3}
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## 解释

- `strict_full_replay_positive` 表示 forced branch 闭环跑完且相对 baseline 改善；它可以用于试训练和排序信号，但不等价于 20 规模达标。
- `target_200_positive` 表示 baseline 超过目标墙钟、alternative 在目标墙钟内 OPTIMAL；这是 20 规模 200 秒目标的高权重标签。
- `hard_negative_count` 当前只计入 full-run regression；`local_only_hard_negative` 作为弱负例单列，避免把右删失局部 proxy 当成严格反例。
- `pipeline_debug_training_ready=true` 只表示可以调通数据加载、图构造、loss 和 checkpoint，不表示模型已有足够跨 context 泛化证据。
- `sanity_training_ready=true` 只说明可以试训模型管线；`serious_training_ready=true` 才表示数据量接近可以认真训练 branch/action head；`optin_training_ready=true` 才接近上线 opt-in 评估门槛。
- `remaining_for_*` 是距离对应 requirements 还差多少；`missing_for_*` 是保留给旧下游的同义字段，不是最低门槛本身。

## 当前判断

当前 strict/full-replay 信号已经足够跑一次 pipeline/debug 训练。
当前 strict/full-replay 信号已经足够做一次小规模试训练。
当前还不适合把 branch/action GAT 当作正式训练目标；主要缺口见 remaining_for_serious_training。
存在相对变快但仍未进入 200 秒的弱正例，训练时应降权或单独作为 proof-cost/ranking 辅助标签。
