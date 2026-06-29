# Journey Branch Training Readiness Audit

日期：2026-06-28

## 目的

汇总已完成 branch counterfactual replay，区分 strict full-replay positive 和真正进入 200 秒目标的 target-200 positive。该脚本只读既有 JSONL，不运行 BPC / pricing / RMP，不改变 official bound 或 certificate。

## 机器字段

```text
target_wall = 200.0
row_count = 2
usable_counterfactual_training_count = 0
strict_full_replay_positive_count = 0
strict_full_replay_positive_context_count = 0
strict_full_replay_positive_instance_count = 0
strict_full_replay_positive_time_window_family_count = 0
target_200_positive_count = 0
target_200_positive_context_count = 0
target_200_positive_instance_count = 0
target_200_positive_time_window_family_count = 0
weak_positive_not_target_count = 0
weak_gap_aux_positive_count = 2
weak_gap_fathom_aux_positive_count = 1
weak_gap_aux_regression_count = 0
weak_gap_aux_positive_context_count = 1
weak_gap_aux_positive_instance_count = 1
regression_count = 0
local_only_hard_negative_count = 0
hard_negative_count = 0
right_censored_counterfactual_count = 2
timeout_resolved_count = 0
timeout_regression_count = 0
target_200_positive_holdout_context_count = 0
counterfactual_label_type_counts = {'weak_gap_fathom_positive': 1, 'weak_gap_positive': 1}
status_pair_counts = {'EXTERNAL_TIME_LIMIT->EXTERNAL_TIME_LIMIT': 2}
pipeline_debug_training_ready = false
sanity_training_ready = false
serious_training_ready = false
optin_training_ready = false
serious_training_requirements = {'target_200_positive_min': 20, 'hard_negative_min': 30, 'target_200_context_min': 8, 'target_200_instance_min': 8, 'target_200_time_window_family_min': 3, 'holdout_context_min': 2}
optin_training_requirements = {'target_200_positive_min': 40, 'hard_negative_min': 60, 'target_200_context_min': 15, 'target_200_instance_min': 15, 'target_200_time_window_family_min': 3, 'holdout_context_min': 3}
remaining_for_pipeline_debug_training = {'strict_full_replay_positive_min': 5, 'positive_context_min': 2, 'positive_instance_min': 2, 'positive_time_window_family_min': 2}
remaining_for_sanity_training = {'strict_full_replay_positive_min': 10, 'hard_negative_min': 5, 'positive_context_min': 3, 'positive_instance_min': 3, 'positive_time_window_family_min': 2}
remaining_for_serious_training = {'target_200_positive_min': 20, 'hard_negative_min': 30, 'target_200_context_min': 8, 'target_200_instance_min': 8, 'target_200_time_window_family_min': 3, 'holdout_context_min': 2}
remaining_for_optin_training = {'target_200_positive_min': 40, 'hard_negative_min': 60, 'target_200_context_min': 15, 'target_200_instance_min': 15, 'target_200_time_window_family_min': 3, 'holdout_context_min': 3}
missing_for_pipeline_debug_training = {'strict_full_replay_positive_min': 5, 'positive_context_min': 2, 'positive_instance_min': 2, 'positive_time_window_family_min': 2}
missing_for_sanity_training = {'strict_full_replay_positive_min': 10, 'hard_negative_min': 5, 'positive_context_min': 3, 'positive_instance_min': 3, 'positive_time_window_family_min': 2}
missing_for_serious_training = {'target_200_positive_min': 20, 'hard_negative_min': 30, 'target_200_context_min': 8, 'target_200_instance_min': 8, 'target_200_time_window_family_min': 3, 'holdout_context_min': 2}
missing_for_optin_training = {'target_200_positive_min': 40, 'hard_negative_min': 60, 'target_200_context_min': 15, 'target_200_instance_min': 15, 'target_200_time_window_family_min': 3, 'holdout_context_min': 3}
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## 解释

- `strict_full_replay_positive` 表示 forced branch 闭环跑完且相对 baseline 改善；它可以用于试训练和排序信号，但不等价于 20 规模达标。
- `target_200_positive` 表示 baseline 超过目标墙钟、alternative 在目标墙钟内 OPTIMAL；这是 20 规模 200 秒目标的高权重标签。
- `hard_negative_count` 当前只计入 full-run regression；`local_only_hard_negative` 作为弱负例单列，避免把右删失局部 proxy 当成严格反例。
- `weak_gap_aux_positive` 表示 600 秒右删失下 gap/incumbent/fathom 结构变好；它不是 strict 正例，只能作为 gap/proof-cost/ranking 辅助信号。
- `pipeline_debug_training_ready=true` 只表示可以调通数据加载、图构造、loss 和 checkpoint，不表示模型已有足够跨 context 泛化证据。
- `sanity_training_ready=true` 只说明可以试训模型管线；`serious_training_ready=true` 才表示数据量接近可以认真训练 branch/action head；`optin_training_ready=true` 才接近上线 opt-in 评估门槛。
- `remaining_for_*` 是距离对应 requirements 还差多少；`missing_for_*` 是保留给旧下游的同义字段，不是最低门槛本身。

## 当前判断

当前 strict/full-replay 信号连 pipeline/debug 训练都偏薄，应先补最小闭环正例。
当前 strict/full-replay 信号还不足以支撑试训练，应继续补最小正负例。
当前还不适合把 branch/action GAT 当作正式训练目标；主要缺口见 remaining_for_serious_training。
存在右删失 gap/fathom 弱正例，适合用于诊断 branch pair 对 proof tree 的结构影响，但不能作为完整求解正例。
