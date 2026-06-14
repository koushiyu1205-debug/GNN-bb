# BPC_future Selector Holdout Status 审计

日期：2026-06-13

## 目标

本报告只审计 selector 是否已经具备 production 资格。它不运行 BPC，不改变求解路径，
不更新 certificate，也不把任何 selector 上线。

## 结论

```text
exact_replay_candidate = available_with_errors
selector_holdout = not_production_validated
production_candidate_ab = blocked
```

解释：

- exact replay 中已有 calibrated selector candidate；
- 该 candidate 仍有 false positive / false negative；
- broader candidate / trajectory holdout 仍不足以 production；
- selected 20 repeat A/B 没有证明 wall-time / status / pricing-state 改善。

## Exact Replay Selector

```text
row_count = 280
label_counts = {'improved': 209, 'noop': 71}
recommended_selector_candidate = true_reduced_cost_<=_-12.430587
false_positive_count = 22
false_negative_count = 31
passing_features_all_holdouts = ['true_reduced_cost', 'cost', 'new_task_set', 'strict_replacement_by_cost']
production_validated_selector = False
```

## Broader Candidate Selector

```text
row_count = 848
label_counts = {'improved': 553, 'worsened': 295}
dataset_holdout_pass_count = 0
instance_holdout_pass_count = 0
best_dataset_model = linear_mean_diff
best_dataset_precision = 0.6633165829145728
best_dataset_recall = 0.7160940325497287
```

## Column-local Selector Blockers

```text
task_set_mixed_group_count = 6
task_sequence_mixed_group_count = 5
online_flags_mixed_row_count = 278
task_set_true_rc_direction_counts = {'improved_lower_mean': 2, 'noop_lower_mean': 4}
task_sequence_true_rc_direction_counts = {'improved_lower_mean': 2, 'noop_lower_mean': 3}
```

这些 blockers 表示：同一 task-set / sequence / 在线 flags 在不同 context 下会混合
improved 与 noop；在 mixed groups 内，true-RC 更负的方向也会反转。因此不能用
列局部形态或简单单调 true-RC/cost 规则作为 production selector。

## Trajectory Signal Ladder

```text
pre_batch_lod_precision = 0.4392156862745098
immediate_addition_lod_precision = 0.4855769230769231
next_rmp_movement_lod_precision = 0.4794007490636704
hindsight_trajectory_lod_precision = 0.6821705426356589
```

## Selected 20 Repeat A/B

```text
profile_row_count = 6
profile_statuses = ['TIME_LIMIT']
profile_pricing_states = ['FOUND_NEGATIVE', 'INCOMPLETE_LIMIT']
worker_added_journeys = [2, 2, 0, 0, 0, 0]
primal_deltas_vs_baseline = [-41.372067, 49.762092, 0.0, 0.0, 0.0, 0.0]
```

## 当前边界

```text
production_validated_selector = false
has_20_walltime_speedup_evidence = false
```

下一步仍只能是 calibration-only：selector 必须只使用 addition-before features，
并同时通过 context / instance / dataset holdout，之后才允许 full BPC A/B。
