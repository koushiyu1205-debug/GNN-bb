# V487 Tree-Policy Event Dataset

日期：2026-06-27

## 目的

把 V481/V482 的成功 tree replay 和 V485 的失败聚合策略，转成 branch-event 级别的数据行，供后续 GAT tree-policy 头使用。

该数据集不是 single-pair counterfactual dataset。它表达的是：

```text
在某个 node/context 下，当前 tree-policy 选择这个 pair 是否属于成功/失败 tree policy 的一部分。
```

## 输入

正例来源：

```text
V481 seed61309 tree replay: TIME_LIMIT/EXTERNAL_TIME_LIMIT -> OPTIMAL
V482 seed61513 tree replay: TIME_LIMIT/EXTERNAL_TIME_LIMIT -> OPTIMAL
```

负例来源：

```text
V485 family-site-depth aggregate smoke:
6 个 holdout，0 个恢复 OPTIMAL
只取 selected_score_source 命中且 selected_pair_changed=True 的 branch events
```

## 输出

```text
BPC_future/data/gat_branch_action_sanity/v487_tree_policy_event_rows_20260627/tree_policy_event_rows.jsonl
```

汇总：

```text
row_count = 57
positive_event_count = 26
hard_negative_event_count = 31

policy_run_counts:
  v481_seed61309_tree_replay = 14
  v482_seed61513_tree_replay = 12
  v485_aggregate_family_site_depth = 31

production_ready = False
official_bound_effect = False
certificate_effect = False
```

## 字段语义

关键字段：

```text
instance
node_id
depth
baseline_pair
selected_pair
selected_pair_changed
candidate_count
eligible_count
selected_score
selected_score_source
selected_raw
priority_top
tree_policy_label_type
tree_policy_label_reason
full_replay_status
full_replay_wall_time
capped_wall_time_gain
event_loss_weight
y_tree_policy_positive
y_tree_policy_hard_negative
```

## 使用边界

这些 rows 可以用于训练/评估 GAT 的 tree-policy action head，但不能直接替代旧的 pair-level `branch_counterfactual_delta_rows`。

原因：

- V481/V482 的正例是整棵 tree policy 成功，不是每个单独 pair 独立因果成立。
- V485 的负例是聚合策略失败，不代表某个 pair 在所有上下文都坏。
- 因此训练时必须保留 node/context 特征和 tree-policy 标签，不应把它们降级成普通 single-pair positive/negative。

## 下一步

1. 给 `branch_impact_model` 增加 tree-policy action head，输入仍是 pair embedding + node/context feature。
2. 训练时把 V487 作为 tree-policy 辅助任务，不污染原 pair-level wall-time gain 头。
3. score map 导出时增加 `tree_policy_score` 来源，并要求 opt-in gate 看到足够 node/context coverage 才启用。
4. 继续通过 strict replay 收集更多 tree-policy positives；当前 26 个 positive events 来自 2 个完整成功实例，仍不足以 production-ready。

## V488 训练链路验证

已完成：

```text
BPC_future/scripts/build_gat_tree_policy_event_dataset.py
BPC_future/data/gat_branch_action_sanity/v488_tree_policy_event_dataset_20260627/
BPC_future/data/gat_branch_action_sanity/v488_tree_policy_event_dataset_20260627/gat_tree_policy_v488.pt
BPC_future/results/gat_tree_policy_v488_20260627/summary.json
BPC_future/results/gat_tree_policy_v488_score_map_on_v485_logs_20260627/
```

模型/训练改动：

```text
branch_impact_model 增加 tree_policy_head
train_gat_branch_action_sanity 增加 optional tree_policy BCE loss
export_gat_branch_action_score_map 增加 --score-mode tree_policy
```

V488 dataset：

```text
sample_count = 57
tree_policy_positive = 26
tree_policy_hard_negative = 31
legacy branch/walltime loss weight = 0
```

V488 training：

```text
epochs = 3
train_tree_policy_loss: 1.0735 -> 0.6966
validation_tree_policy_loss: 0.6505 -> 0.5637
production_ready = False
solver_default_effect = False
```

V488 export：

```text
score_mode = tree_policy
score_row_count = 392
has_tree_policy_head = True
production_ready = False
official_bound_effect = False
certificate_effect = False
```

这说明 tree-policy 辅助头的 dataset -> training -> checkpoint -> score rows 链路已经跑通，但当前正例仍只有 2 个完整实例，不能作为生产策略。
