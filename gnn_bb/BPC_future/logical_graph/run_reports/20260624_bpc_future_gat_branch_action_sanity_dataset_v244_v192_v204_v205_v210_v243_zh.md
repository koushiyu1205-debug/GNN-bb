# GAT Branch/Action Sanity Dataset

日期：2026-06-24

## 目的

把已完成 branch counterfactual replay 转成小规模 GAT branch/action sanity dataset。该数据集只用于离线试训模型管线，不运行 BPC / pricing / RMP，不产生 certificate 或 official bound。

## 机器字段

```text
output_dir = BPC_future/data/gat_branch_action_sanity/v244_v192_v204_v205_v210_v243_20260624
target_wall = 200.0
raw_row_count = 25
sample_count = 17
row_kind_counts = {'budget_dominant_improvement': 1, 'hard_negative_regression': 6, 'local_only_hard_negative': 7, 'target_200_positive': 6, 'weak_positive_not_target': 5}
branch_priority_label_counts = {'aux_only_weak_positive': 5, 'not_target_200': 6, 'target_200_positive': 6}
tail_improved_aux_label_counts = {'tail_improved': 11, 'tail_not_improved': 6}
skipped_counts = {'not_training_sample:budget_dominant_improvement': 1, 'not_training_sample:local_only_hard_negative': 7}
instance_count = 4
family_count = 2
sanity_training_dataset_ready = true
serious_training_dataset_ready = false
optin_training_dataset_ready = false
runs_bpc_or_pricing = false
official_bound_effect = false
certificate_effect = false
```

## 标签边界

- 主 `branch_priority` 标签只使用 `target_200_positive` 对 full-run regression；这对应 20 规模 200 秒目标。
- `weak_positive_not_target` 样本保留在数据集中，但主标签 loss weight 为 0，只作为 `tail_improved` 辅助标签。
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
    "y_branch_priority_target_200",
    "branch_priority_loss_weight",
    "y_strict_full_replay_positive",
    "y_weak_positive_not_target",
    "y_counterfactual_regression",
    "y_timeout_regression",
    "y_tail_improved_aux",
    "tail_improved_loss_weight"
  ]
}
```
