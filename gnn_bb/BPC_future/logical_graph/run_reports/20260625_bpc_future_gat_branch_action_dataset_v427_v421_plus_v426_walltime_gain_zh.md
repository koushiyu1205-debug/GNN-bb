# GAT Branch/Action Sanity Dataset

日期：2026-06-26

## 目的

把已完成 branch counterfactual replay 转成小规模 GAT branch/action sanity dataset。该数据集只用于离线试训模型管线，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
output_dir = BPC_future/data/gat_branch_action_sanity/v427_v421_plus_v426_walltime_gain_20260625
target_wall = 200.0
wall_cap = 600.0
min_wall_improvement = 5.0
min_wall_regression = 5.0
raw_row_count = 53
sample_count = 40
row_kind_counts = {'budget_dominant_improvement': 1, 'hard_negative_regression': 11, 'local_only_hard_negative': 8, 'regression': 2, 'unknown_right_censored': 2, 'walltime_gain_positive': 16, 'walltime_gain_target_wall_crossing': 13}
branch_priority_label_counts = {'not_walltime_gain': 11, 'walltime_gain_positive': 29}
target_wall_crossing_label_counts = {'not_target_wall_crossing': 27, 'target_wall_crossing_positive': 13}
tail_improved_aux_label_counts = {'tail_improved': 29, 'tail_not_improved': 11}
skipped_counts = {'not_training_sample:budget_dominant_improvement': 1, 'not_training_sample:local_only_hard_negative': 8, 'not_training_sample:regression': 2, 'not_training_sample:unknown_right_censored': 2}
instance_count = 14
family_count = 3
sanity_training_dataset_ready = true
serious_training_dataset_ready = false
optin_training_dataset_ready = false
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## 标签边界

- 主 `branch_priority` 标签使用 capped wall-time gain，不把 200 秒作为训练硬断点。
- `target_wall_crossing_positive` 只作为验收/报告字段；`199s -> 201s` 这类小变化不会成为强负例，`500s -> 300s` 会成为高权重正例。
- `weak_positive_not_target` 样本保留在数据集中；只要有足够 wall-time gain，也会进入主标签，否则仅作为 `tail_improved` 辅助标签。
- `local_only_hard_negative` 和右删失 proxy 不进入主训练样本，避免把局部证据当 full-run 反例。

## Schema

```json
{
  "branch_feature_schema": [
    "depth",
    "candidate_count",
    "eligible_count",
    "has_candidate_log",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "same_mass",
    "fractionality",
    "support_count",
    "incumbent_relation_known",
    "incumbent_relation_same",
    "incumbent_disagreement",
    "pool_same_allowed",
    "pool_separate_allowed",
    "pool_max_child_width",
    "pool_total_child_width",
    "pool_balance_gap"
  ],
  "context_feature_schema": [
    "node_id",
    "depth",
    "branch_time",
    "candidate_count",
    "eligible_count",
    "branch_rank_in_top",
    "branch_rank_in_priority_top",
    "baseline_task_i",
    "baseline_task_j",
    "alternative_task_i",
    "alternative_task_j"
  ],
  "label_schema": [
    "y_branch_priority_walltime_gain",
    "branch_priority_loss_weight",
    "capped_wall_time_delta",
    "capped_wall_time_delta_ratio",
    "y_target_wall_crossing_positive",
    "y_strict_full_replay_positive",
    "y_weak_positive_not_target",
    "y_counterfactual_regression",
    "y_timeout_regression",
    "y_timeout_resolved",
    "y_tail_improved_aux",
    "tail_improved_loss_weight"
  ]
}
```
